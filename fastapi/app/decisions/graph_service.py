from typing import List, Dict, Any
import logging
from app.decisions import DecisionEntity

logger = logging.getLogger(__name__)

class GraphService:
    @staticmethod
    def build_graph(decisions: List[DecisionEntity]) -> Dict[str, Any]:
        """
        Transforms a list of DecisionEntity objects into a nodes/links graph format.
        Nodes: Decision, Author, Repository
        Links: (Author -> Decision), (Repository -> Decision), (Decision -> Decision)
        """
        nodes = []
        links = []
        node_ids = set()
        
        # Track counts for node sizing
        repo_impact_counts = {}
        author_contribution_counts = {}

        for d in decisions:
            # 1. Decision Node
            d_node_id = f"decision_{d.decision_id}"
            if d_node_id not in node_ids:
                nodes.append({
                    "id": d_node_id,
                    "name": d.title,
                    "type": "decision",
                    "status": d.status,
                    "confidence": d.confidence.overall,
                    "val": 12 + (d.confidence.overall * 8), # Size reflects confidence
                    "description": d.description,
                    "tags": d.tags,
                    "createdAt": d.created_at
                })
                node_ids.add(d_node_id)
            
            # 2. Repository Node
            if d.repository:
                repo_node_id = f"repo_{d.repository}"
                repo_impact_counts[repo_node_id] = repo_impact_counts.get(repo_node_id, 0) + 1
                if repo_node_id not in node_ids:
                    nodes.append({
                        "id": repo_node_id,
                        "name": d.repository,
                        "type": "repository",
                        "val": 18,
                        "platform": d.platform
                    })
                    node_ids.add(repo_node_id)
                links.append({
                    "source": repo_node_id, 
                    "target": d_node_id, 
                    "label": "impacted",
                    "value": 2
                })

            # 3. Author Nodes
            # Collect unique participants from metadata and evidence
            authors = set(d.participants)
            for evidence in d.intent + d.execution + d.authority + d.outcomes:
                if evidence.author and evidence.author != "unknown":
                    authors.add(evidence.author)
            
            for author in authors:
                author_node_id = f"author_{author}"
                author_contribution_counts[author_node_id] = author_contribution_counts.get(author_node_id, 0) + 1
                if author_node_id not in node_ids:
                    nodes.append({
                        "id": author_node_id,
                        "name": author,
                        "type": "author",
                        "val": 10
                    })
                    node_ids.add(author_node_id)
                links.append({
                    "source": author_node_id, 
                    "target": d_node_id, 
                    "label": "contributed",
                    "value": 1
                })

            # 4. Semantic Relationships (Relates)
            for related_id in d.related_decisions:
                related_node_id = f"decision_{related_id}"
                # We only create link if we have the target ID (to avoid broken links in visualization)
                links.append({
                    "source": d_node_id, 
                    "target": related_node_id, 
                    "label": "relates",
                    "value": 3
                })

        # Final pass: Adjust sizes based on connectivity
        for node in nodes:
            if node["type"] == "repository":
                node["val"] = 15 + (repo_impact_counts.get(node["id"], 0) * 2)
            elif node["type"] == "author":
                node["val"] = 8 + (author_contribution_counts.get(node["id"], 0) * 1.5)

        return {"nodes": nodes, "links": links}
