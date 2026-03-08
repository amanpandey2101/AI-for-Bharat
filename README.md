# 🧠 Memora.dev — AI-Powered Organizational Decision Memory

> **"Every decision your team makes, remembered forever."**

Memora.dev is an AI-powered platform that automatically captures, analyzes, and organizes technical decisions made across your development workflow — PRs, code reviews, Slack discussions, Jira tickets — building a living knowledge base that answers *"Why did we build it this way?"*

Built for the **AWS Hackathon 2026** using Amazon Bedrock Agents, Knowledge Base, DynamoDB, and more.

---

## 🎯 Problem Statement

Development teams make hundreds of architectural and design decisions daily across GitHub PRs, Slack threads, Jira tickets, and code reviews. These decisions are:

- **Scattered** across platforms with no unified view
- **Lost** when team members leave or channels are archived
- **Undiscoverable** — new devs can't find *why* something was built a certain way
- **Repeated** — teams re-debate decisions that were already settled

**Memora solves this** by using AI to passively observe your workflow and automatically extract, score, and organize decisions into a searchable knowledge graph.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📂 **Workspaces** | Organize projects — group repos, channels, and boards per workspace |
| 🔌 **Multi-Platform Ingestion** | GitHub, GitLab, Slack, Jira webhooks — unified event pipeline |
| 🤖 **AI Decision Inference** | Amazon Bedrock Agent analyzes events to detect technical decisions |
| 📊 **Confidence Scoring** | Each decision scored on evidence quality, quantity, authority, and consistency |
| 🔍 **Semantic Search (RAG)** | Ask "Why did we choose DynamoDB?" — agent searches Knowledge Base for answers |
| ✅ **Human-in-the-Loop** | Validate or dispute AI-inferred decisions |
| 📝 **ADR Automation** | Validated decisions automatically generate Pull Requests with standardized Markdown ADRs |
| 📈 **Decision Dashboard** | Stats, activity feed, and decision memory at a glance |
| 🧩 **Evidence Chains** | Each decision linked to source PRs, comments, commits, and messages |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│              Next.js 15 + shadcn/ui + TypeScript             │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │Dashboard │ │Activity  │ │Decision  │ │Integrations  │   │
│  │  Home    │ │  Feed    │ │ Memory   │ │  Manager     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────┴───────────────────────────────────┐
│                     FASTAPI BACKEND                          │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Auth    │ │ Webhooks │ │Decisions │ │Integrations  │   │
│  │ (JWT)   │ │ Handlers │ │  API     │ │  (OAuth)     │   │
│  └──────────┘ └────┬─────┘ └──────────┘ └──────────────┘   │
│                     │                                        │
│              ┌──────┴──────┐                                 │
│              │  AI Agent   │                                 │
│              │  Pipeline   │                                 │
│              └──────┬──────┘                                 │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                    AWS SERVICES                              │
│                                                              │
│  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │  Amazon Bedrock   │  │  Knowledge Base                │   │
│  │  Agent            │  │  (OpenSearch Serverless +      │   │
│  │  (Nova Lite /     │◄─┤   Titan Embeddings V2)        │   │
│  │   Claude Haiku)   │  │  ┌─────────┐                  │   │
│  └──────────────────┘  │  │ S3 Docs │                  │   │
│                         │  └─────────┘                  │   │
│  ┌──────────────────┐  └────────────────────────────────┘   │
│  │    DynamoDB       │                                       │
│  │  ┌─────────────┐ │  ┌────────────────────────────────┐   │
│  │  │ Users       │ │  │          SQS Queue             │   │
│  │  │ Events      │ │  │    (async event processing)    │   │
│  │  │ Decisions   │ │  └────────────────────────────────┘   │
│  │  │ Integrations│ │                                       │
│  │  │ Workspaces  │ │                                       │
│  │  └─────────────┘ │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Event Processing Flow

```
 GitHub PR Created
       │
       ▼
 Webhook received at POST /webhooks/github
       │
       ▼
 ┌─────────────────────────────────┐
 │ 1. Validate signature           │
 │ 2. Parse → IngestionEvent       │
 │ 3. Store in DynamoDB            │
 │ 4. Queue in SQS                 │
 │ 5. Return 202 Accepted          │
 └───────────────┬─────────────────┘
                 │ (background thread)
                 ▼
 ┌─────────────────────────────────┐
 │ Bedrock Agent (invoke_agent)    │
 │                                 │
 │ Input: Event data (PR title,    │
 │        description, author)     │
 │                                 │
 │ Agent searches Knowledge Base   │
 │ for related past decisions      │
 │                                 │
 │ Output: Structured JSON         │
 │  {                              │
 │    is_decision: true,           │
 │    title: "Migrate to DynamoDB",│
 │    confidence: 0.95,            │
 │    rationale: "...",            │
 │    tags: ["architecture"]       │
 │  }                              │
 └───────────────┬─────────────────┘
                 │
                 ▼
 ┌─────────────────────────────────┐
 │ Store Decision in DynamoDB      │
 │ Upload to S3 → Sync KB          │
 │ Decision visible in dashboard   │
 └───────────────┬─────────────────┘
                 │
                 ▼
 ┌─────────────────────────────────┐
 │ 🔄 ADR Automation (on Validate) │
 │                                 │
 │ 1. Create new Git branch        │
 │ 2. Generate Markdown ADR        │
 │ 3. Commit to repository          │
 │ 4. Open Pull Request            │
 └─────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, TypeScript, shadcn/ui, Tailwind CSS | Dashboard, integrations, decision viewer |
| **Backend** | FastAPI, Python 3.11, Pydantic V2, Uvicorn | REST API, webhook handlers, auth |
| **AI** | Amazon Bedrock Agent + Knowledge Base | Decision inference, semantic search (RAG) |
| **Models** | Amazon Nova Lite / Claude 3 Haiku (configurable) | LLM for structured extraction |
| **Embeddings** | Amazon Titan Text Embeddings V2 | Vector embeddings for Knowledge Base |
| **Database** | Amazon DynamoDB | Users, events, decisions, integrations |
| **Vector Store** | OpenSearch Serverless | Knowledge Base vector storage |
| **Storage** | Amazon S3 | Decision documents for KB indexing |
| **Queue** | Amazon SQS | Async event processing |
| **Auth** | JWT + OAuth 2.0 (GitHub, GitLab, Slack, Jira) | User authentication, platform connections |

---

## 📁 Project Structure

```
AI-for-Bharat/
├── client/                         # Frontend (Next.js 15)
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx        # Dashboard home — stats, quick actions
│   │   │   │   ├── activity/       # Activity feed — real-time events
│   │   │   │   ├── decisions/      # Decision memory — AI-inferred decisions
│   │   │   │   ├── integrations/   # Platform connections manager
│   │   │   │   └── layout.tsx      # Sidebar + workspace provider
│   │   │   └── (auth)/             # Login, signup pages
│   │   ├── components/
│   │   │   ├── app-sidebar.tsx     # Sidebar with workspace switcher
│   │   │   ├── IntegrationCard.tsx # Platform connection card
│   │   │   └── ResourceSelector.tsx# Repo/channel/project picker
│   │   ├── context/
│   │   │   ├── AuthContext.tsx     # JWT auth state
│   │   │   └── WorkspaceContext.tsx# Active workspace state
│   │   └── services/
│   │       ├── decisions.ts        # Decision API client
│   │       ├── events.ts           # Events API client
│   │       ├── integrations.ts     # Integrations API client
│   │       └── workspaces.ts       # Workspace API client
│   └── package.json
│
├── fastapi/                        # Backend (FastAPI)
│   ├── main.py                     # App entry point, router registration
│   ├── run.py                      # Uvicorn launcher
│   ├── app/
│   │   ├── config.py               # Settings (Pydantic, env vars)
│   │   ├── database.py             # DynamoDB client + table creation
│   │   ├── auth/                   # JWT authentication
│   │   ├── agents/
│   │   │   └── bedrock_agent.py    # Bedrock Agent + KB integration
│   │   ├── decisions/
│   │   │   ├── __init__.py         # DecisionEntity model + DynamoDB repo
│   │   │   └── routes.py           # Decision API (CRUD, search, stats)
│   │   ├── integrations/           # OAuth flows (GitHub, GitLab, Slack, Jira)
│   │   ├── workspaces/
│   │   │   ├── __init__.py         # Workspace model + DynamoDB repo
│   │   │   └── routes.py           # Workspace CRUD + resource management
│   │   └── webhooks/
│   │       ├── models.py           # IngestionEvent unified schema
│   │       ├── routes.py           # Webhook endpoints + agent trigger
│   │       ├── github_adapter.py   # GitHub payload parser
│   │       ├── gitlab_adapter.py   # GitLab payload parser
│   │       ├── slack_adapter.py    # Slack payload parser
│   │       └── jira_adapter.py     # Jira payload parser
│   ├── .env                        # Environment variables
│   └── requirements.txt
│
├── design.md                       # Detailed design document
├── requirements.md                 # Product requirements
└── README.md                       # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **AWS Account** with Bedrock, DynamoDB, S3, SQS access
- **GitHub OAuth App** (for GitHub integration)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/AI-for-Bharat.git
cd AI-for-Bharat

# Backend
cd fastapi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../client
npm install
```

### 2. Configure Environment

Copy and edit the environment file:

```bash
cd fastapi
cp .env.example .env  # or edit .env directly
```

Key variables to set:

```env
# AWS credentials
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# OAuth (GitHub)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Bedrock Agent (after AWS setup)
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
BEDROCK_KB_ID=your-kb-id
BEDROCK_KB_S3_BUCKET=your-bucket-name
```

### 3. Set Up AWS Resources

Follow these steps in the AWS Console:

1. **S3 Bucket** — Create `memora-kb-{account-id}` with a `decisions/` folder
2. **Knowledge Base** — Create with vector store, S3 data source, Titan Embeddings V2
3. **Bedrock Agent** — Create with Nova Lite model, associate KB, create `prod` alias
4. **IAM** — Ensure your IAM user has `AmazonBedrockFullAccess` + `AmazonDynamoDBFullAccess`

> See [Bedrock Setup Guide](bedrock_setup_guide.md) for detailed instructions.

### 4. Run

```bash
# Terminal 1: Backend (port 5000)
cd fastapi
source venv/bin/activate
python run.py

# Terminal 2: Frontend (port 3000)
cd client
npm run dev
```

Open **http://localhost:3000** in your browser.

### 5. Test the Agent

```bash
cd fastapi
python test_agent.py
```

This sends a mock PR event through the full pipeline and verifies:
- ✅ Bedrock Agent invocation
- ✅ Decision extraction with confidence scoring
- ✅ DynamoDB storage
- ✅ S3 upload for KB indexing

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login (returns JWT) |
| GET | `/auth/me` | Current user profile |

### Integrations (OAuth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/integrations/` | List user integrations |
| GET | `/integrations/github/connect` | Start GitHub OAuth flow |
| GET | `/integrations/github/callback` | OAuth callback |
| POST | `/integrations/{platform}/resources` | Save selected repos/channels |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/github` | Receive GitHub events |
| POST | `/webhooks/gitlab` | Receive GitLab events |
| POST | `/webhooks/slack` | Receive Slack events |
| POST | `/webhooks/jira` | Receive Jira events |
| GET | `/webhooks/events` | List recent events |

### Workspaces
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/` | List user workspaces |
| POST | `/workspaces/` | Create workspace |
| GET | `/workspaces/{id}` | Get workspace details |
| PATCH | `/workspaces/{id}` | Update name/description |
| DELETE | `/workspaces/{id}` | Delete workspace |
| POST | `/workspaces/{id}/resources` | Add resource to workspace |
| DELETE | `/workspaces/{id}/resources` | Remove resource |
| GET | `/workspaces/{id}/resources` | List workspace resources |
| GET | `/workspaces/{id}/decisions` | List workspace-scoped decisions |

### Decisions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/decisions/` | List decisions (filter by status/repo) |
| GET | `/decisions/stats/overview` | Dashboard statistics |
| POST | `/decisions/search` | Semantic search via KB (RAG) |
| GET | `/decisions/search/kb` | Direct KB vector search |
| GET | `/decisions/{id}` | Get decision with evidence chain |
| POST | `/decisions/{id}/validate` | Validate or dispute decision (triggers ADR PR) |
| DELETE | `/decisions/{id}` | Delete decision |

---

## 📖 ADR Automation

Memora bridges the gap between informal discussion and formal documentation. When an engineer clicks **"Validate"** on an inferred decision, our ADR engine orchestrates the entire documentation lifecycle:

1. **Standardized Formatting:** Transforms the AI-extracted rationale, context, and alternatives into a clean Markdown ADR.
2. **Automated Git Flow:** 
   - Uses the GitHub API to create a unique branch (e.g., `adr/migrate-to-dynamodb`).
   - Commits the ADR file to the repository's documentation directory (`docs/architecture/decisions/`).
   - Opens a **Pull Request** back to the main branch for peer review.
3. **Closing the Loop:** Once merged, the ADR becomes the permanent source of truth for the project's architecture.

---

## 🤖 AI Agent Details

### Decision Inference Agent

The agent receives development events and determines if they contain technical decisions:

**Input:** Normalized event data (PR title, description, author, platform)

**Processing:**
1. Analyzes event content for decision indicators
2. Queries Knowledge Base for related past decisions
3. Extracts structured decision data with confidence scoring
4. Links evidence to source events

**Output:** Structured JSON with:
- Decision title, description, rationale
- Alternatives considered
- Confidence score (0.0–1.0) with factor breakdown
- Participant list and tags
- Related past decisions (from KB)

### Confidence Scoring

Each decision's confidence is calculated from 4 factors:

| Factor | Weight | What it measures |
|--------|--------|-----------------|
| **Evidence Quality** | 25% | Specificity and clarity of the evidence |
| **Evidence Quantity** | 25% | Number of supporting data points |
| **Participant Authority** | 25% | Seniority/role of decision makers |
| **Temporal Consistency** | 25% | Timeline coherence of the evidence |

### Model Options

| Model | Cost/Call | Best For |
|-------|----------|----------|
| Amazon Nova Micro | ~$0.0002 | Ultra-cheap, basic extraction |
| **Amazon Nova Lite** | ~$0.0003 | **Default — best value** |
| Claude 3 Haiku | ~$0.002 | High accuracy JSON extraction |
| Claude 3 Sonnet | ~$0.02 | Best reasoning, complex decisions |

---

## 🔐 Security

- **JWT authentication** for all API endpoints
- **OAuth 2.0** for platform connections (tokens stored encrypted in DynamoDB)
- **Webhook signature validation** for all platforms (HMAC-SHA256)
- **IAM-based** AWS resource access (no root credentials)
- **CORS** restricted to frontend origin

---

## 🗺️ Roadmap

- [x] Multi-platform webhook ingestion (GitHub, GitLab, Slack, Jira)
- [x] Bedrock Agent with Knowledge Base (RAG)
- [x] Decision inference with confidence scoring
- [x] Human-in-the-loop validation
- [x] Semantic search ("Why did we choose X?")
- [x] Dashboard with stats and activity feed
- [x] Workspaces (group repos, channels, projects per project)
- [x] Export decisions as ADR (Architecture Decision Records)
- [ ] Knowledge Graph visualization (D3.js/React Flow)
- [ ] Decision detail page with full evidence chain
- [ ] Team collaboration features
- [ ] Scheduled KB sync (CloudWatch Events)
- [ ] Slack bot for querying decisions inline

---

## 👥 Team

**Built for AI for Bharat — AWS Hackathon 2026**

---

## 📄 License

This project is built for the AWS Hackathon 2026. All rights reserved.
