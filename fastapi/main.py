from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.auth.routes import auth_router
from app.webhooks.routes import webhook_router
from app.integrations.routes import integration_router
from app.decisions.routes import decision_router
from app.workspaces.routes import workspace_router
from app.adrs.routes import adr_router
from app.chat.routes import chat_router
from app.database import ensure_tables_exist

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure DynamoDB tables exist. Shutdown: nothing to clean up."""
    logger.info("Starting up — ensuring DynamoDB tables exist…")
    ensure_tables_exist()
    from app.workspaces import create_workspaces_table
    from app.adrs import create_adrs_table
    create_workspaces_table()
    create_adrs_table()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Memora.dev — AI-Powered Organizational Memory",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(integration_router, prefix="/integrations", tags=["Integrations"])
app.include_router(decision_router, prefix="/decisions", tags=["Decisions"])
app.include_router(workspace_router, prefix="/workspaces", tags=["Workspaces"])
app.include_router(adr_router, tags=["ADRs"])  # paths are /workspaces/{id}/adrs
app.include_router(chat_router, prefix="/chat/workspaces", tags=["Chat"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Memora.dev API"}


@app.get("/health")
def health_check():
    """Health check endpoint (Requirement 11.3)."""
    return {"status": "healthy"}
