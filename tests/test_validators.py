import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai_career_platform.utils.validators import validate_input, validate_company, redact, MAX_INPUT_LENGTH


def test_validate_input_accepts_good_value() -> None:
    assert validate_input("resume", "hello") == "hello"


def test_validate_input_rejects_empty() -> None:
    try:
        validate_input("resume", "   ")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty input")


def test_validate_input_rejects_too_long() -> None:
    try:
        validate_input("resume", "a" * (MAX_INPUT_LENGTH + 1))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for too-long input")


def test_validate_company_accepts_standard() -> None:
    assert validate_company("Acme Inc") == "Acme Inc"


def test_redact_removes_openai_key() -> None:
    text = "key sk-abcdefghijklmnopqrst"
    redacted = redact(text)
    assert "[REDACTED]" in redacted
