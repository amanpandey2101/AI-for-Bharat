from datetime import datetime, timedelta
import jwt
import secrets
import bcrypt
from app.config import settings

def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    # bcrypt.hashpw expects bytes
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(identity: str):
    expire = datetime.utcnow() + timedelta(minutes=settings.DEBUG and 60*24 or 15) # Longer expiration in debug
    to_encode = {"sub": str(identity), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def generate_verification_token():
    return secrets.token_urlsafe(32)
