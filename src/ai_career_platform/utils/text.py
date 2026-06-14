from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import List, Set

logger = logging.getLogger(__name__)


class Config:
    SESSION_TIMEOUT_MINUTES = 30
    MAX_INPUT_LENGTH = 50_000
    ALLOWED_FILE_EXTENSIONS = {".pdf", ".txt", ".md"}


SECRET_PATTERNS = [r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+", r"(?i)sk-[A-Za-z0-9]{16,}", r"(?i)ghp_[A-Za-z0-9]{36}", r"(?i)github_pat_[A-Za-z0-9_]{22,}", r"(?i)xox[baprs]-[0-9a-zA-Z-]+", r"(?i)-----BEGIN [A-Z ]+PRIVATE KEY-----[A-Za-z0-9/\s=+]+-----END [A-Z ]+PRIVATE KEY-----", r"(?i)AKIA[0-9A-Z]{16}", r"(?i)AIza[0-9A-Za-z\-_]{35}", r"(?i)xoxb-[A-Za-z0-9-]+", r"(?i)mongodb(\+srv)?:\/\/[^\s]+", r"(?i)postgres(ql)?:\/\/[^\s]+", r"(?i)mysql:\/\/[^\s]+", r"(?i)rediss?:\/\/[^\s]+"]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9+#./-]+", text.lower())
    return tokens


def compute_file_fingerprint(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_input_text(text: str, max_length: int = Config.MAX_INPUT_LENGTH) -> None:
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    if len(text) > max_length:
        raise ValueError(f"Input too long: {len(text)} chars (max {max_length})")


def validate_company_name(name: str) -> str:
    name = (name or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9 &.,'()\-]{2,}", name):
        raise ValueError("Invalid company_name format")
    return name


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, "[REDACTED]", redacted)
    return redacted
