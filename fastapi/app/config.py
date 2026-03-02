from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Core
    SECRET_KEY: str = "secret"
    JWT_SECRET_KEY: str = "jwt-secret"
    JWT_COOKIE_SECURE: bool = False
    JWT_COOKIE_SAMESITE: str = "lax"
    JWT_ACCESS_COOKIE_PATH: str = "/"
    JWT_ACCESS_COOKIE_NAME: str = "access_token_cookie"

    # AWS / DynamoDB
    AWS_REGION: str = "us-west-2"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    DYNAMODB_ENDPOINT_URL: Optional[str] = None  # e.g. http://localhost:8000 for local DynamoDB
    DYNAMODB_TABLE_PREFIX: str = "memora"

    # Mail Configuration
    MAIL_SERVER: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_DEFAULT_SENDER: Optional[str] = None

    # Github OAuth  
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # GitLab OAuth
    GITLAB_CLIENT_ID: Optional[str] = None
    GITLAB_CLIENT_SECRET: Optional[str] = None

    # Slack OAuth
    SLACK_CLIENT_ID: Optional[str] = None
    SLACK_CLIENT_SECRET: Optional[str] = None

    # Jira / Atlassian OAuth
    JIRA_CLIENT_ID: Optional[str] = None
    JIRA_CLIENT_SECRET: Optional[str] = None

    # Webhook Secrets (fallback — per-user secrets are auto-generated)
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITLAB_WEBHOOK_SECRET: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None
    JIRA_WEBHOOK_SECRET: Optional[str] = None
    JIRA_BASE_URL: Optional[str] = None

    # Application URLs
    API_BASE_URL: str = "http://localhost:5000"       # Backend URL (used for OAuth redirects)
    FRONTEND_URL: str = "http://localhost:3000"        # Frontend URL (redirect after OAuth)

    # Amazon Bedrock Agent + Knowledge Base
    BEDROCK_MODEL_ID: str = "amazon.nova-lite-v1:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    BEDROCK_AGENT_ID: str = ""
    BEDROCK_AGENT_ALIAS_ID: str = ""
    BEDROCK_KB_ID: str = ""
    BEDROCK_KB_S3_BUCKET: str = ""

    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )


settings = Settings()
