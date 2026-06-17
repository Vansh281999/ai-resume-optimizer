import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-1234567890")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session

import pytest

from ai_career_platform.db.models import Base, User, PasswordResetToken
from ai_career_platform.db.session import get_db
from ai_career_platform.config import Settings
from unittest.mock import patch


def _make_settings():
    return Settings(
        SECRET_KEY="test-secret-key-for-testing-only-1234567890",
        DATABASE_URL="sqlite://",
        MAX_UPLOAD_SIZE_BYTES=1 * 1024 * 1024,
    )


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    import api.server as server_module
    settings = _make_settings()

    with patch.object(server_module, "_global_settings", settings):
        app = server_module.create_app()

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient):
    resp = client.post("/api/auth/signup", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "securePass123!",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestSignupLogin:
    def test_signup_success(self, client: TestClient):
        resp = client.post("/api/auth/signup", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "securePass123!",
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "alice@example.com"

    def test_signup_duplicate_email(self, client: TestClient):
        client.post("/api/auth/signup", json={
            "name": "A", "email": "dup@example.com", "password": "securePass123!",
        })
        resp = client.post("/api/auth/signup", json={
            "name": "B", "email": "dup@example.com", "password": "securePass123!",
        })
        assert resp.status_code == 400

    def test_login_success(self, client: TestClient):
        client.post("/api/auth/signup", json={
            "name": "B", "email": "b@example.com", "password": "securePass123!",
        })
        resp = client.post("/api/auth/login", json={
            "email": "b@example.com", "password": "securePass123!",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client: TestClient):
        client.post("/api/auth/signup", json={
            "name": "C", "email": "c@example.com", "password": "securePass123!",
        })
        resp = client.post("/api/auth/login", json={
            "email": "c@example.com", "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_get_me(self, client: TestClient, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_me_unauthorized(self, client: TestClient):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_signup_rejects_short_password(self, client: TestClient):
        resp = client.post("/api/auth/signup", json={
            "name": "D", "email": "d@example.com", "password": "short",
        })
        assert resp.status_code == 422


class TestPasswordResetFlow:
    def test_forgot_password_returns_message(self, client: TestClient):
        client.post("/api/auth/signup", json={
            "name": "E", "email": "e@example.com", "password": "securePass123!",
        })
        resp = client.post("/api/auth/forgot-password", json={"email": "e@example.com"})
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_reset_password_success(self, client: TestClient, db_session: Session):
        signup_resp = client.post("/api/auth/signup", json={
            "name": "F", "email": "f@example.com", "password": "securePass123!",
        })
        assert signup_resp.status_code == 201
        forgot_resp = client.post("/api/auth/forgot-password", json={"email": "f@example.com"})
        assert forgot_resp.status_code == 200
        user = db_session.query(User).filter(User.email == "f@example.com").first()
        token_entry = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).first()
        assert token_entry is not None, "No reset token found for user"
        token = token_entry.token
        resp = client.post("/api/auth/reset-password", json={
            "token": token, "new_password": "newSecure456!",
        })
        assert resp.status_code == 200, resp.text
        login = client.post("/api/auth/login", json={
            "email": "f@example.com", "password": "newSecure456!",
        })
        assert login.status_code == 200

    def test_reset_password_used_token_rejected(self, client: TestClient, db_session: Session):
        client.post("/api/auth/signup", json={
            "name": "G", "email": "g@example.com", "password": "securePass123!",
        })
        client.post("/api/auth/forgot-password", json={"email": "g@example.com"})
        user = db_session.query(User).filter(User.email == "g@example.com").first()
        token_entry = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).first()
        token = token_entry.token
        client.post("/api/auth/reset-password", json={"token": token, "new_password": "newPass123!"})
        reuse = client.post("/api/auth/reset-password", json={"token": token, "new_password": "anotherPass456!"})
        assert reuse.status_code == 400
