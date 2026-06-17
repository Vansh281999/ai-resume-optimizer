import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-1234567890")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import pytest

from ai_career_platform.db.models import Base, User
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


class TestAPIHealthEndpoints:
    def test_health_endpoint(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_ai_health_endpoint(self, client: TestClient):
        resp = client.get("/api/health/ai")
        assert resp.status_code == 200


class TestAPIProtectedEndpoints:
    def test_ats_score_unauthenticated(self, client: TestClient):
        resp = client.post("/api/ats/score", json={"resume_text": "test"})
        assert resp.status_code == 200

    def test_security_scan_unauthenticated(self, client: TestClient):
        resp = client.post("/api/security/scan", json={"text": "test"})
        assert resp.status_code == 401

    def test_analytics_trends_unauthenticated(self, client: TestClient):
        resp = client.get("/api/analytics/trends")
        assert resp.status_code == 401

    def test_job_match_unauthenticated(self, client: TestClient):
        resp = client.post("/api/jobs/match", json={
            "resume_text": "Python experience",
            "job_description": "Looking for Python developer"
        })
        assert resp.status_code == 200

    def test_interview_generate_unauthenticated(self, client: TestClient):
        resp = client.post("/api/interview/generate", json={
            "company": "TestCorp",
            "role": "Engineer"
        })
        assert resp.status_code == 200

    def test_career_roadmap_unauthenticated(self, client: TestClient):
        resp = client.post("/api/career/roadmap", json={
            "current_skills": ["Python"],
            "target_role": "Senior Engineer"
        })
        assert resp.status_code == 200


class TestAPIRequestIDs:
    def test_request_id_in_response(self, client: TestClient):
        resp = client.get("/api/health")
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) == 36

    def test_custom_request_id_preserved(self, client: TestClient):
        custom_id = "test-request-123"
        resp = client.get("/api/health", headers={"X-Request-ID": custom_id})
        assert resp.headers["X-Request-ID"] == custom_id