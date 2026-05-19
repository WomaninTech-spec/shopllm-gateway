"""API key generation and hashing."""
from __future__ import annotations

import hashlib
import secrets

from shopllm.config import get_settings

_PREFIX = get_settings().api_key_prefix


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, sha256_hash)."""
    full = _PREFIX + secrets.token_urlsafe(32)
    prefix = full[:12]
    h = hashlib.sha256(full.encode()).hexdigest()
    return full, prefix, h


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
