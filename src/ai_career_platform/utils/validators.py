import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 50_000
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


def validate_input(name: str, value: Optional[str]) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} cannot be empty")
    if len(value) > MAX_INPUT_LENGTH:
        raise ValueError(f"{name} exceeds max length ({len(value)})")
    return value


def validate_company(name: str) -> str:
    name = validate_input("company", name)
    if not re.fullmatch(r"[A-Za-z0-9 &.,'()\-]{2,}", name):
        raise ValueError("Invalid company name format")
    return name


def validate_file_path(path: str) -> str:
    if not path or not isinstance(path, str):
        raise ValueError("Invalid file path")
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    return path


def redact(text: str) -> str:
    redacted = text
    patterns = [
        r"(?i)sk-[A-Za-z0-9]{16,}",
        r"(?i)ghp_[A-Za-z0-9]{36}",
        r"(?i)github_pat_[A-Za-z0-9_]{22,}",
        r"(?i)AIza[0-9A-Za-z\-_]{35}",
        r"(?i)xox[baprs]-[0-9a-zA-Z-]+",
        r"(?i)password\s*[:=]\s*\S+",
        r"(?i)secret\s*[:=]\s*\S+",
    ]
    for pattern in patterns:
        redacted = re.sub(pattern, "[REDACTED]", redacted)
    return redacted
