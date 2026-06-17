import pytest

from ai_career_platform.career.career_dashboard import CareerDashboard
from ai_career_platform.models import CareerRoadmap, SkillProgression


@pytest.fixture
def dashboard() -> CareerDashboard:
    return CareerDashboard(provider="openai")


def test_dashboard_defaults(dashboard: CareerDashboard) -> None:
    assert dashboard.provider_name == "openai"
    assert dashboard.model is None


def test_roadmap_construction() -> None:
    roadmap = CareerRoadmap(
        current_role="Junior Engineer",
        target_role="Data Engineer",
        skill_progressions=[SkillProgression(skill_name="Python", current_level=50.0, target_level=90.0)],
        estimated_timeline_months=12,
        salary_progression={},
    )
    assert isinstance(roadmap, CareerRoadmap)
    assert roadmap.target_role == "Data Engineer"
    assert roadmap.skill_progressions[0].skill_name == "Python"
    assert roadmap.skill_progressions[0].current_level == 50.0


def test_parse_valid_json() -> None:
    dashboard = CareerDashboard(provider="openai")
    text = '{"skill_progressions": [], "salary_progression": {}, "estimated_timeline_months": 6, "current_role": "DE"}'
    result = dashboard._parse(text)
    assert result["estimated_timeline_months"] == 6


def test_parse_json_code_block() -> None:
    dashboard = CareerDashboard(provider="openai")
    text = "```json\n{ \"foo\": \"bar\" }\n```"
    result = dashboard._parse(text)
    assert result == {"foo": "bar"}


def test_parse_invalid_returns_empty() -> None:
    dashboard = CareerDashboard(provider="openai")
    assert dashboard._parse("no json here") == {}