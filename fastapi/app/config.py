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

    # Database
    DATABASE_URL: Optional[str] = "sqlite:///./app.db"

    # Mail Configuration
    MAIL_SERVER: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_DEFAULT_SENDER: Optional[str] = None

    # Github
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()
