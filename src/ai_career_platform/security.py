from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class SecretScanner:
    PATTERNS = [
        re.compile(r"(?i)sk-[A-Za-z0-9]{16,}"),
        re.compile(r"(?i)ghp_[A-Za-z0-9]{36}"),
        re.compile(r"(?i)github_pat_[A-Za-z0-9_]{22,}"),
        re.compile(r"(?i)AWS_ACCESS_KEY_ID\s*[:=]\s*[A-Z0-9]{20}"),
        re.compile(r"(?i)AWS_SECRET_ACCESS_KEY\s*[:=]\s*[A-Za-z0-9+/]{40,}"),
        re.compile(r"(?i)-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+-----END [A-Z ]+PRIVATE KEY-----"),
        re.compile(r"(?i)AIza[0-9A-Za-z\-_]{35}"),
        re.compile(r"(?i)mongodb(\+srv)?:\/\/[^\s]+"),
        re.compile(r"(?i)postgres(ql)?:\/\/[^\s]+"),
        re.compile(r"(?i)mysql:\/\/[^\s]+"),
        re.compile(r"(?i)rediss?:\/\/[^\s]+"),
        re.compile(r"(?i)xox[baprs]-[0-9a-zA-Z-]+"),
        re.compile(r"(?i)password\s*[:=]\s*\S+"),
        re.compile(r"(?i)passwd\s*[:=]\s*\S+"),
        re.compile(r"(?i)api_key\s*[:=]\s*\S+"),
        re.compile(r"(?i)apikey\s*[:=]\s*\S+"),
    ]

    @classmethod
    def scan(cls, text: str) -> List[str]:
        findings: List[str] = []
        for pattern in cls.PATTERNS:
            if pattern.search(text):
                findings.append(pattern.pattern)
        return findings
