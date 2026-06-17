import pytest

from ai_career_platform.core.ats_engine import ATSScoringEngine
from ai_career_platform.models import ATSScoreReport


@pytest.fixture
def engine() -> ATSScoringEngine:
    return ATSScoringEngine()


def test_score_returns_valid_report(engine: ATSScoringEngine) -> None:
    resume = "Email: user@example.com\nPhone: +1-555-0199\nExperience\nSkills: Python, SQL"
    report = engine.score(resume)
    assert isinstance(report, ATSScoreReport)
    assert 0 <= report.overall_score <= 100
    assert 0 <= report.keyword_density_score <= 100
    assert 0 <= report.formatting_risk_score <= 100
    assert "experience" in report.found_sections
    assert "skills" in report.found_sections


def test_score_empty_resume_returns_zero_and_missing_sections(engine: ATSScoringEngine) -> None:
    report = engine.score("")
    assert report.overall_score == 0
    assert "Resume text is empty" in report.critical_issues
    assert len(report.missing_sections) == len(report.found_sections) + len(report.missing_sections)