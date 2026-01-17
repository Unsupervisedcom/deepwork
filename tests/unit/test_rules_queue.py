"""Tests for rules queue system (QS-6.x from test_scenarios.md)."""

import json
from pathlib import Path

import pytest

from deepwork.core.rules_queue import (
    ActionResult,
    QueueEntry,
    QueueEntryStatus,
    RulesQueue,
    compute_trigger_hash,
)


class TestComputeTriggerHash:
    """Tests for hash calculation (QS-6.2.x)."""

    def test_same_everything_same_hash(self) -> None:
        """QS-6.2.1: Same rule, files, baseline - same hash."""
        hash1 = compute_trigger_hash("RuleA", ["a.py"], "commit1")
        hash2 = compute_trigger_hash("RuleA", ["a.py"], "commit1")
        assert hash1 == hash2

    def test_different_files_different_hash(self) -> None:
        """QS-6.2.2: Different files - different hash."""
        hash1 = compute_trigger_hash("RuleA", ["a.py"], "commit1")
        hash2 = compute_trigger_hash("RuleA", ["b.py"], "commit1")
        assert hash1 != hash2

    def test_different_baseline_different_hash(self) -> None:
        """QS-6.2.3: Different baseline - different hash."""
        hash1 = compute_trigger_hash("RuleA", ["a.py"], "commit1")
        hash2 = compute_trigger_hash("RuleA", ["a.py"], "commit2")
        assert hash1 != hash2

    def test_different_rule_different_hash(self) -> None:
        """QS-6.2.4: Different rule - different hash."""
        hash1 = compute_trigger_hash("RuleA", ["a.py"], "commit1")
        hash2 = compute_trigger_hash("RuleB", ["a.py"], "commit1")
        assert hash1 != hash2

    def test_file_order_independent(self) -> None:
        """File order should not affect hash (sorted internally)."""
        hash1 = compute_trigger_hash("RuleA", ["a.py", "b.py"], "commit1")
        hash2 = compute_trigger_hash("RuleA", ["b.py", "a.py"], "commit1")
        assert hash1 == hash2


class TestQueueEntry:
    """Tests for QueueEntry dataclass."""

    def test_to_dict_and_from_dict(self) -> None:
        """Round-trip serialization."""
        entry = QueueEntry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_hash="abc123",
            status=QueueEntryStatus.QUEUED,
            baseline_ref="commit1",
            trigger_files=["src/main.py"],
            expected_files=["tests/main_test.py"],
        )

        data = entry.to_dict()
        restored = QueueEntry.from_dict(data)

        assert restored.rule_name == entry.rule_name
        assert restored.rule_file == entry.rule_file
        assert restored.trigger_hash == entry.trigger_hash
        assert restored.status == entry.status
        assert restored.trigger_files == entry.trigger_files
        assert restored.expected_files == entry.expected_files

    def test_with_action_result(self) -> None:
        """Serialization with action result."""
        entry = QueueEntry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_hash="abc123",
            action_result=ActionResult(type="command", output="ok", exit_code=0),
        )

        data = entry.to_dict()
        restored = QueueEntry.from_dict(data)

        assert restored.action_result is not None
        assert restored.action_result.type == "command"
        assert restored.action_result.exit_code == 0


class TestRulesQueue:
    """Tests for RulesQueue class (QS-6.1.x, QS-6.3.x)."""

    @pytest.fixture
    def queue(self, tmp_path: Path) -> RulesQueue:
        """Create a queue with temp directory."""
        return RulesQueue(tmp_path / "queue")

    def test_create_entry(self, queue: RulesQueue) -> None:
        """QS-6.1.1: Create new queue entry."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )

        assert entry is not None
        assert entry.status == QueueEntryStatus.QUEUED
        assert entry.rule_name == "Test Rule"

    def test_create_duplicate_returns_none(self, queue: RulesQueue) -> None:
        """QS-6.1.6: Re-trigger same files returns None."""
        entry1 = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        entry2 = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )

        assert entry1 is not None
        assert entry2 is None  # Duplicate

    def test_create_different_files_new_entry(self, queue: RulesQueue) -> None:
        """QS-6.1.7: Different files create new entry."""
        entry1 = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/a.py"],
            baseline_ref="commit1",
        )
        entry2 = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/b.py"],  # Different file
            baseline_ref="commit1",
        )

        assert entry1 is not None
        assert entry2 is not None

    def test_has_entry(self, queue: RulesQueue) -> None:
        """Check if entry exists."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        assert entry is not None

        assert queue.has_entry(entry.trigger_hash) is True
        assert queue.has_entry("nonexistent") is False

    def test_get_entry(self, queue: RulesQueue) -> None:
        """Retrieve entry by hash."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        assert entry is not None

        retrieved = queue.get_entry(entry.trigger_hash)
        assert retrieved is not None
        assert retrieved.rule_name == "Test Rule"

    def test_get_nonexistent_entry(self, queue: RulesQueue) -> None:
        """Get nonexistent entry returns None."""
        assert queue.get_entry("nonexistent") is None

    def test_update_status_to_passed(self, queue: RulesQueue) -> None:
        """QS-6.1.3: Update status to passed."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        assert entry is not None

        success = queue.update_status(entry.trigger_hash, QueueEntryStatus.PASSED)
        assert success is True

        updated = queue.get_entry(entry.trigger_hash)
        assert updated is not None
        assert updated.status == QueueEntryStatus.PASSED
        assert updated.evaluated_at is not None

    def test_update_status_to_failed(self, queue: RulesQueue) -> None:
        """QS-6.1.5: Update status to failed."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        assert entry is not None

        action_result = ActionResult(type="command", output="error", exit_code=1)
        success = queue.update_status(
            entry.trigger_hash, QueueEntryStatus.FAILED, action_result
        )
        assert success is True

        updated = queue.get_entry(entry.trigger_hash)
        assert updated is not None
        assert updated.status == QueueEntryStatus.FAILED
        assert updated.action_result is not None
        assert updated.action_result.exit_code == 1

    def test_update_status_to_skipped(self, queue: RulesQueue) -> None:
        """QS-6.1.2: Update status to skipped (safety suppression)."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        assert entry is not None

        success = queue.update_status(entry.trigger_hash, QueueEntryStatus.SKIPPED)
        assert success is True

        updated = queue.get_entry(entry.trigger_hash)
        assert updated is not None
        assert updated.status == QueueEntryStatus.SKIPPED

    def test_update_nonexistent_returns_false(self, queue: RulesQueue) -> None:
        """Update nonexistent entry returns False."""
        success = queue.update_status("nonexistent", QueueEntryStatus.PASSED)
        assert success is False

    def test_get_queued_entries(self, queue: RulesQueue) -> None:
        """Get only queued entries."""
        # Create multiple entries with different statuses
        entry1 = queue.create_entry(
            rule_name="Rule 1",
            rule_file="rule1.md",
            trigger_files=["a.py"],
            baseline_ref="commit1",
        )
        entry2 = queue.create_entry(
            rule_name="Rule 2",
            rule_file="rule2.md",
            trigger_files=["b.py"],
            baseline_ref="commit1",
        )
        assert entry1 is not None
        assert entry2 is not None

        # Update one to passed
        queue.update_status(entry1.trigger_hash, QueueEntryStatus.PASSED)

        # Get queued only
        queued = queue.get_queued_entries()
        assert len(queued) == 1
        assert queued[0].rule_name == "Rule 2"

    def test_get_all_entries(self, queue: RulesQueue) -> None:
        """Get all entries regardless of status."""
        entry1 = queue.create_entry(
            rule_name="Rule 1",
            rule_file="rule1.md",
            trigger_files=["a.py"],
            baseline_ref="commit1",
        )
        entry2 = queue.create_entry(
            rule_name="Rule 2",
            rule_file="rule2.md",
            trigger_files=["b.py"],
            baseline_ref="commit1",
        )
        assert entry1 is not None
        assert entry2 is not None

        queue.update_status(entry1.trigger_hash, QueueEntryStatus.PASSED)

        all_entries = queue.get_all_entries()
        assert len(all_entries) == 2

    def test_remove_entry(self, queue: RulesQueue) -> None:
        """Remove entry by hash."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        assert entry is not None

        removed = queue.remove_entry(entry.trigger_hash)
        assert removed is True
        assert queue.has_entry(entry.trigger_hash) is False

    def test_remove_nonexistent_returns_false(self, queue: RulesQueue) -> None:
        """Remove nonexistent entry returns False."""
        removed = queue.remove_entry("nonexistent")
        assert removed is False

    def test_clear(self, queue: RulesQueue) -> None:
        """Clear all entries."""
        queue.create_entry(
            rule_name="Rule 1",
            rule_file="rule1.md",
            trigger_files=["a.py"],
            baseline_ref="commit1",
        )
        queue.create_entry(
            rule_name="Rule 2",
            rule_file="rule2.md",
            trigger_files=["b.py"],
            baseline_ref="commit1",
        )

        count = queue.clear()
        assert count == 2
        assert len(queue.get_all_entries()) == 0

    def test_clear_empty_queue(self, queue: RulesQueue) -> None:
        """Clear empty queue returns 0."""
        count = queue.clear()
        assert count == 0

    def test_file_structure(self, queue: RulesQueue) -> None:
        """Verify queue files are named correctly."""
        entry = queue.create_entry(
            rule_name="Test Rule",
            rule_file="test-rule.md",
            trigger_files=["src/main.py"],
            baseline_ref="commit1",
        )
        assert entry is not None

        # Check file exists with correct naming
        expected_file = queue.queue_dir / f"{entry.trigger_hash}.queued.json"
        assert expected_file.exists()

        # Update status and check file renamed
        queue.update_status(entry.trigger_hash, QueueEntryStatus.PASSED)
        assert not expected_file.exists()
        passed_file = queue.queue_dir / f"{entry.trigger_hash}.passed.json"
        assert passed_file.exists()
