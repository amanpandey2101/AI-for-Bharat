from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
import secrets
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(identity: str):
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"sub": str(identity), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def generate_verification_token():
    return secrets.token_urlsafe(32)
