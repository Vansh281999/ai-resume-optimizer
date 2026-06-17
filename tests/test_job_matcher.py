import pytest

from ai_career_platform.core.job_matcher import JobMatcher
from ai_career_platform.models import JobMatchReport


@pytest.fixture
def matcher() -> JobMatcher:
    return JobMatcher()


def test_match_returns_valid_report(matcher: JobMatcher) -> None:
    resume = "Python developer with FastAPI, Docker, Kubernetes, SQL, React"
    job = "Looking for Python, FastAPI, Docker, Kubernetes, SQL, React, AWS"
    out = matcher.match(resume, job)
    assert isinstance(out, JobMatchReport)
    assert 0 <= out.overall_match_score <= 100
    assert 0 <= out.skill_match_score <= 100
    assert 0 <= out.experience_match_score <= 100
    assert "aws" in [s.lower() for s in out.missing_skills]


def test_match_full_overlap_scores_high(matcher: JobMatcher) -> None:
    resume = "Python developer with FastAPI, Docker, Kubernetes, SQL, React, AWS"
    job = "Required: Python, FastAPI, Docker, Kubernetes, SQL, React, AWS"
    out = matcher.match(resume, job)
    assert out.overall_match_score >= 70
    assert not out.missing_skills