from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    email = Column(String(120), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    
    password_hash = Column(String(255), nullable=True)
    github_id = Column(String(120), nullable=True)
    provider = Column(String(50), nullable=False)

    avatar_url = Column(String(500), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    is_inactive = Column(Boolean, default=False, nullable=False)

    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
