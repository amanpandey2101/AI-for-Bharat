"""
End-to-end auth flow test — DynamoDB version.

Prerequisites:
  1. Local DynamoDB must be running (docker run -p 8000:8000 amazon/dynamodb-local)
  2. FastAPI server must be running (python run.py)
"""

import requests
import time
from app.models.user import UserRepository


BASE_URL = "http://127.0.0.1:5000"


def get_db_token(email: str) -> str | None:
    """Retrieve the verification token directly from DynamoDB."""
    user = UserRepository.get_by_email(email)
    return user.verification_token if user else None


def test_auth_flow():
    email = f"test_{int(time.time())}@example.com"
    password = "testpassword123"
    name = "Test User"

    print(f"\n--- Testing Register for {email} ---")
    reg_data = {"email": email, "name": name, "password": password}
    r = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    assert r.status_code == 200
    assert r.json()["success"] is True

    print("\n--- Retrieving verification token from DynamoDB ---")
    token = get_db_token(email)
    print(f"Token: {token}")
    assert token is not None

    print("\n--- Testing Email Verification ---")
    r = requests.get(f"{BASE_URL}/auth/verify-email", params={"token": token})
    print(f"Status: {r.status_code}")
    print(f"Response Content: {r.text}")
    assert r.status_code == 200
    assert "Email verified successfully" in r.text

    print("\n--- Testing Login ---")
    login_data = {"email": email, "password": password}
    session = requests.Session()
    r = session.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    print(f"Cookies: {session.cookies.get_dict()}")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert "access_token_cookie" in session.cookies

    print("\n--- Testing /auth/me (Protected Route) ---")
    r = session.get(f"{BASE_URL}/auth/me")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert r.json()["name"] == name

    print("\n--- Testing /health ---")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

    print("\n✅ End-to-End Auth Flow Test Passed!")


if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"\n❌ Test Failed: {str(e)}")
