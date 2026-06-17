import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 50_000
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}

SECRET_PATTERNS = [
    r"(?i)sk-[A-Za-z0-9]{16,}",
    r"(?i)ghp_[A-Za-z0-9]{36}",
    r"(?i)github_pat_[A-Za-z0-9_]{22,}",
    r"(?i)AIza[0-9A-Za-z\-_]{35}",
    r"(?i)xox[baprs]-[0-9a-zA-Z-]+",
    r"(?i)password\s*[:=]\s*\S+",
    r"(?i)secret\s*[:=]\s*\S+",
    r"(?i)passwd\s*[:=]\s*\S+",
    r"(?i)api_key\s*[:=]\s*\S+",
    r"(?i)apikey\s*[:=]\s*\S+",
    r"(?i)-----BEGIN [A-Z ]+PRIVATE KEY-----[A-Za-z0-9/\s=+]+-----END [A-Z ]+PRIVATE KEY-----",
    r"(?i)AKIA[0-9A-Z]{16}",
    r"(?i)mongodb(\+srv)?:\/\/[^\s]+",
    r"(?i)postgres(ql)?:\/\/[^\s]+",
    r"(?i)mysql:\/\/[^\s]+",
    r"(?i)rediss?:\/\/[^\s]+",
]


def validate_input(name: str, value: Optional[str]) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} cannot be empty")
    if len(value) > MAX_INPUT_LENGTH:
        raise ValueError(f"{name} exceeds max length ({len(value)})")
    return value


def validate_input_text(text: str, max_length: int = MAX_INPUT_LENGTH) -> None:
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    if len(text) > max_length:
        raise ValueError(f"Input too long: {len(text)} chars (max {max_length})")


def validate_company(name: str) -> str:
    name = validate_input("company", name)
    if not re.fullmatch(r"[A-Za-z0-9 &.,'()\-]{2,}", name):
        raise ValueError("Invalid company name format")
    return name


def validate_company_name(name: str) -> str:
    name = (name or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9 &.,'()\-]{2,}", name):
        raise ValueError("Invalid company_name format")
    return name


def validate_file_path(path: str) -> str:
    if not path or not isinstance(path, str):
        raise ValueError("Invalid file path")
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    return path


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")


def redact(text: str) -> str:
    return redact_secrets(text)


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, "[REDACTED]", redacted)
    return redacted
