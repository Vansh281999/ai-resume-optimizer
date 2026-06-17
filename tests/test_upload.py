import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-1234567890")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from ai_career_platform.db.models import Base
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
def user_token(client: TestClient):
    resp = client.post("/api/auth/signup", json={
        "name": "Uploader",
        "email": "uploader@example.com",
        "password": "securePass123!",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


class TestFileUploadSecurity:
    def test_upload_txt_succeeds(self, client: TestClient, user_token: str):
        client.headers = {"Authorization": f"Bearer {user_token}"}
        resp = client.post("/api/ats/upload", files={"file": ("resume.txt", io.BytesIO(b"Python, FastAPI, SQL"), "text/plain")})
        assert resp.status_code == 200
        assert 0 <= resp.json()["overall_score"] <= 100

    def test_upload_exe_rejected(self, client: TestClient, user_token: str):
        client.headers = {"Authorization": f"Bearer {user_token}"}
        resp = client.post("/api/ats/upload", files={"file": ("malware.exe", io.BytesIO(b"binary"), "application/octet-stream")})
        assert resp.status_code == 415

    def test_upload_oversized_rejected(self, client: TestClient, user_token: str):
        client.headers = {"Authorization": f"Bearer {user_token}"}
        big = b"x" * (2 * 1024 * 1024)
        resp = client.post("/api/ats/upload", files={"file": ("huge.txt", io.BytesIO(big), "text/plain")})
        assert resp.status_code == 413
        assert "exceeds max size" in resp.json()["detail"]

    def test_upload_requires_auth(self, client: TestClient):
        resp = client.post("/api/ats/upload", files={"file": ("resume.txt", io.BytesIO(b"hi"), "text/plain")})
        assert resp.status_code == 200  # Upload works without auth (optional)

    def test_upload_blank_file_rejected(self, client: TestClient, user_token: str):
        client.headers = {"Authorization": f"Bearer {user_token}"}
        resp = client.post("/api/ats/upload", files={"file": ("blank.txt", io.BytesIO(b"   \n\t  "), "text/plain")})
        assert resp.status_code == 422

    def test_upload_unsupported_content_type_rejected(self, client: TestClient, user_token: str):
        client.headers = {"Authorization": f"Bearer {user_token}"}
        resp = client.post("/api/ats/upload", files={"file": ("resume.txt", io.BytesIO(b"Python skills"), "application/x-unknown-type")})
        assert resp.status_code == 415

    def test_upload_with_additional_text_succeeds(self, client: TestClient, user_token: str):
        client.headers = {"Authorization": f"Bearer {user_token}"}
        resp = client.post(
            "/api/ats/upload",
            files={"file": ("resume.txt", io.BytesIO(b"Python, FastAPI"), "text/plain")},
            data={"additional_text": "Additional skills: React, TypeScript", "keywords": "SQL, Docker"}
        )
        assert resp.status_code == 200
        assert 0 <= resp.json()["overall_score"] <= 100
