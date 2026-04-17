"""In-memory TTL cache for tool requirements pass decisions.

Caches approved tool calls so that repeated identical calls
don't require re-evaluation within the TTL window.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _CacheEntry:
    """A cached approval decision."""

    approved_at: float
    ttl_seconds: float = 3600.0  # 1 hour

    @property
    def is_valid(self) -> bool:
        return (time.time() - self.approved_at) < self.ttl_seconds


class ToolRequirementsCache:
    """In-memory TTL cache for approved tool calls."""

    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        self._cache: dict[str, _CacheEntry] = {}
        self._ttl = ttl_seconds

    def make_key(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Create a deterministic cache key from tool name and input."""
        content = json.dumps({"tool": tool_name, "input": tool_input}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def is_approved(self, key: str) -> bool:
        """Check if a tool call has a valid cached approval."""
        entry = self._cache.get(key)
        if entry is not None and entry.is_valid:
            return True
        if entry is not None:
            del self._cache[key]
        return False

    def approve(self, key: str) -> None:
        """Cache an approval for a tool call."""
        self._cache[key] = _CacheEntry(approved_at=time.time(), ttl_seconds=self._ttl)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)
