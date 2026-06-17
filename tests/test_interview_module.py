import pytest

from ai_career_platform.interview.interview_module import InterviewPrepModule
from ai_career_platform.models import InterviewPrepReport, InterviewQuestion


@pytest.fixture
def module() -> InterviewPrepModule:
    return InterviewPrepModule(provider="openai")


def test_module_defaults(module: InterviewPrepModule) -> None:
    assert module.provider_name == "openai"
    assert module.model is None


def test_report_construction() -> None:
    report = InterviewPrepReport(
        company="Acme",
        role="Backend Engineer",
        technical_questions=[InterviewQuestion(question="Q1", category="tech", difficulty="easy")],
    )
    assert isinstance(report, InterviewPrepReport)
    assert report.company == "Acme"
    assert report.role == "Backend Engineer"
    assert len(report.technical_questions) == 1


def test_questions_parses_string_and_dict(module: InterviewPrepModule) -> None:
    items = [
        {"question": "Tell me about yourself", "category": "behavioral", "difficulty": "medium"},
        "Why do you want this role?",
    ]
    questions = module._questions(items)
    assert len(questions) == 2
    assert questions[0].question == "Tell me about yourself"
    assert questions[0].category == "behavioral"
    assert questions[1].question == "Why do you want this role?"
    assert questions[1].category == "general"


def test_parse_valid_json() -> None:
    module = InterviewPrepModule(provider="openai")
    text = '{"technical_questions": [], "behavioral_questions": [], "company_specific_questions": [], "preparation_tips": ["tip"]}'
    result = module._parse(text)
    assert result["preparation_tips"] == ["tip"]


def test_parse_json_code_block() -> None:
    module = InterviewPrepModule(provider="openai")
    text = "```json\n{ \"foo\": \"bar\" }\n```"
    result = module._parse(text)
    assert result == {"foo": "bar"}


def test_parse_invalid_returns_empty() -> None:
    module = InterviewPrepModule(provider="openai")
    assert module._parse("no json here") == {}