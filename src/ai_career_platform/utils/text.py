from __future__ import annotations

import hashlib
import logging
import re
from typing import List, Set

from .validators import (
    MAX_INPUT_LENGTH,
    ALLOWED_EXTENSIONS,
    redact_secrets,
    validate_input_text,
    validate_company_name,
)

logger = logging.getLogger(__name__)


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


class Config:
    SESSION_TIMEOUT_MINUTES = 30
    MAX_INPUT_LENGTH = MAX_INPUT_LENGTH
    ALLOWED_FILE_EXTENSIONS = ALLOWED_EXTENSIONS
