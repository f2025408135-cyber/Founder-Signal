"""Hashing utilities — raw_payload_hash for Sources, dedupe pair keys."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def _stable_json(obj: Any) -> str:
    """JSON dump with sorted keys — stable across runs / machines."""
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def hash_json(obj: Any) -> str:
    """SHA-256 hex of a stable JSON serialization of obj.

    Used by all ingestion modules to populate Source.raw_payload_hash.
    """
    return hashlib.sha256(_stable_json(obj).encode("utf-8")).hexdigest()


def hash_text(text: str) -> str:
    """SHA-256 hex of a raw text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_text_truncated(text: str, length: int = 16) -> str:
    """First `length` chars of hash_text — used for dedupe pair keys."""
    return hash_text(text)[:length]
