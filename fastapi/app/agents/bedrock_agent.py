"""
Bedrock Agent — Decision Inference Engine using Amazon Bedrock Agents + Knowledge Base.

Uses a managed Bedrock Agent with an associated Knowledge Base to:
1. Analyze development events for technical decisions
2. Query past decisions for context (RAG via Knowledge Base)
3. Answer semantic "Why?" questions about team decisions

Flow:
  Event → invoke_agent → Claude 3 + KB → Structured Decision JSON
  Decision → S3 upload → KB sync → searchable for future queries
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import boto3
from app.config import settings

logger = logging.getLogger(__name__)


# ── AWS Clients ────────────────────────────────────────────────────────────────

def _get_aws_kwargs() -> Dict[str, str]:
    kwargs: Dict[str, str] = {"region_name": settings.AWS_REGION}
    if settings.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return kwargs


def get_agent_runtime_client():
    """Bedrock Agent Runtime — for invoking agents."""
    return boto3.client("bedrock-agent-runtime", **_get_aws_kwargs())


def get_bedrock_runtime_client():
    """Bedrock Runtime — for direct model invocation (fallback)."""
    return boto3.client("bedrock-runtime", **_get_aws_kwargs())


def get_s3_client():
    """S3 client — for uploading decisions to Knowledge Base."""
    return boto3.client("s3", **_get_aws_kwargs())


def get_bedrock_agent_client():
    """Bedrock Agent client — for managing KB sync."""
    return boto3.client("bedrock-agent", **_get_aws_kwargs())


# ── PROMPTS ────────────────────────────────────────────────────────────────────

DECISION_ANALYSIS_PROMPT = """Analyze this development workflow event and determine if it contains a technical or architectural decision.

## Event Data
{event_data}

## Instructions
1. Determine if this event contains or implies a technical decision
2. If YES, extract the decision with full context
3. Search the knowledge base for any related past decisions
4. If NO decision is found, return is_decision: false

## Output (JSON only, no markdown fences)
{{
  "is_decision": true/false,
  "decision": {{
    "title": "Brief title of the decision",
    "description": "What was decided and its technical context",
    "rationale": "Why this approach was chosen",
    "alternatives_considered": ["Alt 1", "Alt 2"],
    "tags": ["architecture", "performance", "security"],
    "confidence_score": 0.0-1.0,
    "confidence_factors": {{
      "evidence_quality": 0.0-1.0,
      "evidence_quantity": 0.0-1.0,
      "participant_authority": 0.0-1.0,
      "temporal_consistency": 0.0-1.0
    }},
    "participants": ["username1"],
    "related_past_decisions": ["any related decisions found in KB"]
  }}
}}"""


SEMANTIC_SEARCH_PROMPT = """You are Memora's AI assistant. Answer the user's question about their team's development decisions.
Search the knowledge base for relevant past decisions and provide evidence-backed answers.

Question: {question}

Instructions:
- Search the knowledge base for relevant decisions
- Cite specific decisions and their evidence
- Include confidence scores where relevant
- If no relevant decisions found, say so clearly
"""


# ── BEDROCK AGENT CLASS ───────────────────────────────────────────────────────

class BedrockAgentService:
    """
    Manages interactions with Amazon Bedrock Agent + Knowledge Base.
    
    Primary: invoke_agent (agent + KB)
    Fallback: invoke_model (direct Claude call, no KB)
    """

    def __init__(self):
        self._agent_client = None
        self._runtime_client = None
        self._s3_client = None
        self._bedrock_agent_client = None

    @property
    def agent_client(self):
        if self._agent_client is None:
            self._agent_client = get_agent_runtime_client()
        return self._agent_client

    @property
    def runtime_client(self):
        if self._runtime_client is None:
            self._runtime_client = get_bedrock_runtime_client()
        return self._runtime_client

    @property
    def s3_client(self):
        if self._s3_client is None:
            self._s3_client = get_s3_client()
        return self._s3_client

    @property
    def bedrock_agent_client(self):
        if self._bedrock_agent_client is None:
            self._bedrock_agent_client = get_bedrock_agent_client()
        return self._bedrock_agent_client

    # ── Agent Invocation ───────────────────────────────────────────────────

    def invoke_agent(self, prompt: str, session_id: Optional[str] = None) -> Optional[str]:
        """
        Invoke the Bedrock Agent. The agent has access to the Knowledge Base
        and can search past decisions for context.
        """
        agent_id = getattr(settings, "BEDROCK_AGENT_ID", "")
        alias_id = getattr(settings, "BEDROCK_AGENT_ALIAS_ID", "")

        if not agent_id or not alias_id:
            logger.warning("BEDROCK_AGENT_ID or BEDROCK_AGENT_ALIAS_ID not set — falling back to direct model")
            return self._invoke_model_direct(prompt)

        try:
            response = self.agent_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId=session_id or str(uuid.uuid4()),
                inputText=prompt,
            )

            # Parse streaming response
            completion = ""
            for event in response.get("completion", []):
                chunk = event.get("chunk", {})
                if "bytes" in chunk:
                    completion += chunk["bytes"].decode("utf-8")

            return completion

        except Exception:
            logger.error("Bedrock Agent invocation failed, falling back to direct model", exc_info=True)
            return self._invoke_model_direct(prompt)

    def _invoke_model_direct(self, prompt: str) -> Optional[str]:
        """
        Fallback: invoke model directly using the Converse API.
        Works with ALL Bedrock models (Nova, Claude, Llama, Mistral, etc.)
        """
        try:
            model_id = getattr(settings, "BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

            response = self.runtime_client.converse(
                modelId=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": 4096,
                    "temperature": 0.1,
                },
            )

            output = response.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])
            if content and "text" in content[0]:
                return content[0]["text"]
            return None

        except Exception:
            logger.error("Direct model invocation failed", exc_info=True)
            return None

    def _invoke_model_direct_stream(self, prompt: str):
        """
        Fallback: invoke model directly using the Converse API with streaming.
        """
        try:
            model_id = getattr(settings, "BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

            response = self.runtime_client.converse_stream(
                modelId=model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": 4096,
                    "temperature": 0.1,
                },
            )

            for chunk in response.get("stream", []):
                if "contentBlockDelta" in chunk:
                    yield chunk["contentBlockDelta"]["delta"]["text"]

        except Exception as e:
            logger.error("Direct model stream invocation failed", exc_info=True)
            yield "Sorry, I encountered an error while streaming the response."

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from agent/model response, handling markdown fences."""
        if not text:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from agent response: {text[:200]}")
            return None

    # ── Decision Inference ─────────────────────────────────────────────────

    def infer_decision(self, event_data: Dict) -> Optional[Dict]:
        """
        Analyze an event for decision content using the Bedrock Agent.
        The agent will query the Knowledge Base for related past decisions.
        """
        prompt = DECISION_ANALYSIS_PROMPT.format(
            event_data=json.dumps(event_data, indent=2, default=str)
        )
        response = self.invoke_agent(prompt)
        return self._parse_json_response(response)

    # ── Semantic Search ────────────────────────────────────────────────────

    def search_decisions(self, question: str, session_id: Optional[str] = None) -> str:
        """
        Answer a natural language question about past decisions.
        Uses the Knowledge Base for retrieval-augmented generation.
        """
        prompt = SEMANTIC_SEARCH_PROMPT.format(question=question)
        response = self.invoke_agent(prompt, session_id=session_id)
        return response or "No relevant decisions found."

    def retrieve_from_kb(self, query: str, max_results: int = 5) -> list:
        """
        Direct Knowledge Base retrieval (without agent) for pure search.
        """
        kb_id = getattr(settings, "BEDROCK_KB_ID", "")
        if not kb_id:
            return []

        try:
            response = self.agent_client.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": max_results
                    }
                },
            )
            results = []
            for item in response.get("retrievalResults", []):
                results.append({
                    "content": item.get("content", {}).get("text", ""),
                    "score": item.get("score", 0),
                    "source": item.get("location", {}).get("s3Location", {}).get("uri", ""),
                })
            return results

        except Exception:
            logger.error("KB retrieval failed", exc_info=True)
            return []

    # ── Knowledge Base Sync ────────────────────────────────────────────────

    def upload_decision_to_kb(self, decision: Dict) -> bool:
        """
        Upload a decision document to S3 so the Knowledge Base can index it.
        """
        bucket = getattr(settings, "BEDROCK_KB_S3_BUCKET", "")
        if not bucket:
            logger.warning("BEDROCK_KB_S3_BUCKET not configured — skipping KB upload")
            return False

        try:
            decision_id = decision.get("decision_id", str(uuid.uuid4()))
            key = f"decisions/{decision_id}.json"

            # Build a rich document for the KB to index
            document = {
                "decision_id": decision_id,
                "title": decision.get("title", ""),
                "description": decision.get("description", ""),
                "rationale": decision.get("rationale", ""),
                "alternatives_considered": decision.get("alternatives_considered", []),
                "repository": decision.get("repository", ""),
                "platform": decision.get("platform", ""),
                "participants": decision.get("participants", []),
                "tags": decision.get("tags", []),
                "confidence_score": decision.get("confidence", {}).get("overall", 0.5)
                    if isinstance(decision.get("confidence"), dict)
                    else decision.get("confidence", 0.5),
                "status": decision.get("status", "inferred"),
                "created_at": decision.get("created_at", datetime.utcnow().isoformat()),
                "evidence_summary": self._summarize_evidence(decision),
            }

            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(document, indent=2, default=str),
                ContentType="application/json",
            )

            logger.info(f"Uploaded decision {decision_id} to KB S3: s3://{bucket}/{key}")
            return True

        except Exception:
            logger.error("Failed to upload decision to KB S3", exc_info=True)
            return False

    def sync_knowledge_base(self) -> bool:
        """
        Trigger a Knowledge Base sync to index new documents.
        Should be called periodically or after batch uploads.
        """
        kb_id = getattr(settings, "BEDROCK_KB_ID", "")
        if not kb_id:
            return False

        try:
            # List data sources for this KB
            ds_response = self.bedrock_agent_client.list_data_sources(
                knowledgeBaseId=kb_id
            )
            data_sources = ds_response.get("dataSourceSummaries", [])

            if not data_sources:
                logger.warning("No data sources found for KB")
                return False

            # Start ingestion job for the first data source
            ds_id = data_sources[0]["dataSourceId"]
            self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
            )
            logger.info(f"Started KB sync for {kb_id} / {ds_id}")
            return True

        except Exception:
            logger.error("KB sync failed", exc_info=True)
            return False

    @staticmethod
    def _summarize_evidence(decision: Dict) -> str:
        """Create a text summary of evidence for KB indexing."""
        parts = []
        for key in ["intent", "execution", "authority", "outcomes"]:
            evidence_list = decision.get(key, [])
            for e in evidence_list:
                if isinstance(e, dict):
                    parts.append(f"[{key}] {e.get('content', '')}")
                elif isinstance(e, str):
                    parts.append(f"[{key}] {e}")
        return " | ".join(parts) if parts else "No evidence captured."


# ── SINGLETON ──────────────────────────────────────────────────────────────────

agent_service = BedrockAgentService()


# ── EVENT PROCESSOR ────────────────────────────────────────────────────────────

def process_event_for_decisions(event: Dict) -> Optional[Dict]:
    """
    Process an ingested event through the Bedrock Agent pipeline.
    
    1. Send event to Bedrock Agent (which queries KB for context)
    2. Parse the structured decision response
    3. Save to DynamoDB
    4. Upload to S3 for KB indexing
    
    Returns the decision dict if one was found, None otherwise.
    """
    from app.decisions import (
        DecisionEntity,
        DecisionRepository,
        ConfidenceScore,
        Evidence,
        EvidenceType,
    )

    def _map_event_type(event_type: str) -> EvidenceType:
        mapping = {
            "pr_created": EvidenceType.PR_DESCRIPTION,
            "pr_merged": EvidenceType.PR_DESCRIPTION,
            "review_submitted": EvidenceType.CODE_REVIEW,
            "push": EvidenceType.COMMIT,
            "comment": EvidenceType.PR_COMMENT,
            "issue_created": EvidenceType.JIRA_ISSUE,
            "issue_updated": EvidenceType.JIRA_ISSUE,
            "message": EvidenceType.SLACK_MESSAGE,
        }
        return mapping.get(event_type, EvidenceType.PR_COMMENT)

    # 1. Invoke agent
    result = agent_service.infer_decision(event)
    if not result or not result.get("is_decision"):
        logger.info(f"No decision found in event {event.get('event_id', 'unknown')}")
        return None

    decision_data = result["decision"]
    confidence_factors = decision_data.get("confidence_factors", {})

    # 2. Build evidence
    author = event.get("author", {})
    if isinstance(author, dict):
        author_name = author.get("name", "unknown")
    else:
        author_name = event.get("author_name", str(author) if author else "unknown")

    evidence = Evidence(
        source_type=_map_event_type(event.get("event_type", "")),
        source_id=event.get("event_id", ""),
        content=event.get("content", event.get("title", "")),
        author=author_name,
        timestamp=event.get("timestamp", ""),
        confidence_contribution=decision_data.get("confidence_score", 0.5),
        url=event.get("url"),
    )

    # 3. Create decision entity
    decision = DecisionEntity(
        title=decision_data.get("title", "Untitled Decision"),
        description=decision_data.get("description", ""),
        rationale=decision_data.get("rationale", ""),
        alternatives_considered=decision_data.get("alternatives_considered", []),
        repository=event.get("repository", event.get("context", {}).get("repository", "") if isinstance(event.get("context"), dict) else ""),
        platform=event.get("platform", "github"),
        intent=[evidence],
        confidence=ConfidenceScore(
            overall=decision_data.get("confidence_score", 0.5),
            evidence_quality=confidence_factors.get("evidence_quality", 0.5),
            evidence_quantity=confidence_factors.get("evidence_quantity", 0.5),
            participant_authority=confidence_factors.get("participant_authority", 0.5),
            temporal_consistency=confidence_factors.get("temporal_consistency", 0.5),
        ),
        participants=decision_data.get("participants", []),
        tags=decision_data.get("tags", []),
        source_event_ids=[event.get("event_id", "")],
    )

    # 4. Save to DynamoDB
    DecisionRepository.save(decision)
    logger.info(f"Decision created: {decision.decision_id} — {decision.title} (confidence: {decision.confidence.overall})")

    # 5. Upload to S3 for Knowledge Base indexing
    decision_dict = decision.model_dump()
    agent_service.upload_decision_to_kb(decision_dict)

    return decision_dict
