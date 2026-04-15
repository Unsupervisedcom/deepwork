"""Tests for tool requirements TTL cache."""

import time
from unittest.mock import patch

from deepwork.tool_requirements.cache import ToolRequirementsCache


class TestToolRequirementsCache:
    def test_make_key_deterministic(self) -> None:
        cache = ToolRequirementsCache()
        k1 = cache.make_key("shell", {"command": "ls"})
        k2 = cache.make_key("shell", {"command": "ls"})
        assert k1 == k2

    def test_make_key_different_for_different_input(self) -> None:
        cache = ToolRequirementsCache()
        k1 = cache.make_key("shell", {"command": "ls"})
        k2 = cache.make_key("shell", {"command": "rm"})
        assert k1 != k2

    def test_make_key_different_for_different_tool(self) -> None:
        cache = ToolRequirementsCache()
        k1 = cache.make_key("shell", {"command": "ls"})
        k2 = cache.make_key("write_file", {"command": "ls"})
        assert k1 != k2

    def test_approve_and_check(self) -> None:
        cache = ToolRequirementsCache()
        key = cache.make_key("shell", {"command": "ls"})
        assert not cache.is_approved(key)
        cache.approve(key)
        assert cache.is_approved(key)

    def test_ttl_expiry(self) -> None:
        cache = ToolRequirementsCache(ttl_seconds=1.0)
        key = cache.make_key("shell", {"command": "ls"})
        cache.approve(key)
        assert cache.is_approved(key)

        with patch("deepwork.tool_requirements.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2.0
            assert not cache.is_approved(key)

    def test_clear(self) -> None:
        cache = ToolRequirementsCache()
        cache.approve(cache.make_key("shell", {"command": "ls"}))
        assert len(cache) == 1
        cache.clear()
        assert len(cache) == 0

    def test_sorted_keys_for_consistency(self) -> None:
        cache = ToolRequirementsCache()
        k1 = cache.make_key("shell", {"b": "2", "a": "1"})
        k2 = cache.make_key("shell", {"a": "1", "b": "2"})
        assert k1 == k2
