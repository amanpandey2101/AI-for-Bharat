import uuid
from ..extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    
    password_hash = db.Column(db.String(255), nullable=True)
    github_id = db.Column(db.String(120), nullable=True)
    provider = db.Column(db.String(50), nullable=False)

    avatar_url = db.Column(db.String(500), nullable=True)

    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    is_inactive = db.Column(db.Boolean, default=False, nullable=False)

    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(255), nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
