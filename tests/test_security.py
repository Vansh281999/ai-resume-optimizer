import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_career_platform.utils.validators import (
    MAX_INPUT_LENGTH,
    redact,
    validate_company,
    validate_file_path,
    validate_input,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("OpenAI key sk-abcdefghijklmnopqrst", "OpenAI key [REDACTED]"),
        ("GitHub token ghp_abcdefghijklmnopqrstuvwxyz1234567890", "GitHub token [REDACTED]"),
        ("Google key AIzaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Google key [REDACTED]"),
        ("Slack token xoxb-abc123def456", "Slack token [REDACTED]"),
        ("password: hunter2", "[REDACTED]"),
        ("secret = supersecret", "[REDACTED]"),
        ("github_pat_AAAAAAAAAAAAAAAAAAAAAA", "[REDACTED]"),
    ],
)
def test_redact_masks_various_secret_patterns(text, expected):
    assert redact(text) == expected


@pytest.mark.parametrize("value", ["", "   "])
def test_validate_input_rejects_empty_values(value):
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_input("company", value)


def test_validate_input_rejects_too_long_values():
    with pytest.raises(ValueError, match="exceeds max length"):
        validate_input("resume_text", "a" * (MAX_INPUT_LENGTH + 1))


@pytest.mark.parametrize("path", ["resume.docx", "resume.exe", "notes.rtf"])
def test_validate_file_path_rejects_bad_extensions(path):
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_file_path(path)


@pytest.mark.parametrize("name", ["Acme@Corp", "Acme_Corp", "Acme<Corp>", "A"])
def test_validate_company_rejects_invalid_characters_or_length(name):
    with pytest.raises(ValueError, match="Invalid company name format"):
        validate_company(name)
