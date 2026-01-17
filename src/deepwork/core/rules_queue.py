"""Queue system for tracking rule state in .deepwork/tmp/rules/queue/."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class QueueEntryStatus(Enum):
    """Status of a queue entry."""

    QUEUED = "queued"  # Detected, awaiting evaluation
    PASSED = "passed"  # Evaluated, rule satisfied (promise found or action succeeded)
    FAILED = "failed"  # Evaluated, rule not satisfied
    SKIPPED = "skipped"  # Safety pattern matched, skipped


@dataclass
class ActionResult:
    """Result of executing a rule action."""

    type: str  # "prompt" or "command"
    output: str | None = None  # Command stdout or prompt message shown
    exit_code: int | None = None  # Command exit code (None for prompt)


@dataclass
class QueueEntry:
    """A single entry in the rules queue."""

    # Identity
    rule_name: str  # Human-friendly name
    rule_file: str  # Filename (e.g., "source-test-pairing.md")
    trigger_hash: str  # Hash for deduplication

    # State
    status: QueueEntryStatus = QueueEntryStatus.QUEUED
    created_at: str = ""  # ISO8601 timestamp
    evaluated_at: str | None = None  # ISO8601 timestamp

    # Context
    baseline_ref: str = ""  # Commit hash or timestamp used as baseline
    trigger_files: list[str] = field(default_factory=list)
    expected_files: list[str] = field(default_factory=list)  # For set/pair modes
    matched_files: list[str] = field(default_factory=list)  # Files that also changed

    # Result
    action_result: ActionResult | None = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        if self.action_result:
            data["action_result"] = asdict(self.action_result)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueueEntry":
        """Create from dictionary."""
        action_result = None
        if data.get("action_result"):
            action_result = ActionResult(**data["action_result"])

        return cls(
            rule_name=data.get("rule_name", data.get("policy_name", "")),
            rule_file=data.get("rule_file", data.get("policy_file", "")),
            trigger_hash=data["trigger_hash"],
            status=QueueEntryStatus(data["status"]),
            created_at=data.get("created_at", ""),
            evaluated_at=data.get("evaluated_at"),
            baseline_ref=data.get("baseline_ref", ""),
            trigger_files=data.get("trigger_files", []),
            expected_files=data.get("expected_files", []),
            matched_files=data.get("matched_files", []),
            action_result=action_result,
        )


def compute_trigger_hash(
    rule_name: str,
    trigger_files: list[str],
    baseline_ref: str,
) -> str:
    """
    Compute a hash for deduplication.

    The hash is based on:
    - Rule name
    - Sorted list of trigger files
    - Baseline reference (commit hash or timestamp)

    Returns:
        12-character hex hash
    """
    hash_input = f"{rule_name}:{sorted(trigger_files)}:{baseline_ref}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:12]


class RulesQueue:
    """
    Manages the rules queue in .deepwork/tmp/rules/queue/.

    Queue entries are stored as JSON files named {hash}.{status}.json
    """

    def __init__(self, queue_dir: Path | None = None):
        """
        Initialize the queue.

        Args:
            queue_dir: Path to queue directory. Defaults to .deepwork/tmp/rules/queue/
        """
        if queue_dir is None:
            queue_dir = Path(".deepwork/tmp/rules/queue")
        self.queue_dir = queue_dir

    def _ensure_dir(self) -> None:
        """Ensure queue directory exists."""
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def _get_entry_path(self, trigger_hash: str, status: QueueEntryStatus) -> Path:
        """Get path for an entry file."""
        return self.queue_dir / f"{trigger_hash}.{status.value}.json"

    def _find_entry_path(self, trigger_hash: str) -> Path | None:
        """Find existing entry file for a hash (any status)."""
        for status in QueueEntryStatus:
            path = self._get_entry_path(trigger_hash, status)
            if path.exists():
                return path
        return None

    def has_entry(self, trigger_hash: str) -> bool:
        """Check if an entry exists for this hash."""
        return self._find_entry_path(trigger_hash) is not None

    def get_entry(self, trigger_hash: str) -> QueueEntry | None:
        """Get an entry by hash."""
        path = self._find_entry_path(trigger_hash)
        if path is None:
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return QueueEntry.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError):
            return None

    def create_entry(
        self,
        rule_name: str,
        rule_file: str,
        trigger_files: list[str],
        baseline_ref: str,
        expected_files: list[str] | None = None,
    ) -> QueueEntry | None:
        """
        Create a new queue entry if one doesn't already exist.

        Args:
            rule_name: Human-friendly rule name
            rule_file: Rule filename (e.g., "source-test-pairing.md")
            trigger_files: Files that triggered the rule
            baseline_ref: Baseline reference for change detection
            expected_files: Expected corresponding files (for set/pair)

        Returns:
            Created QueueEntry, or None if entry already exists
        """
        trigger_hash = compute_trigger_hash(rule_name, trigger_files, baseline_ref)

        # Check if already exists
        if self.has_entry(trigger_hash):
            return None

        self._ensure_dir()

        entry = QueueEntry(
            rule_name=rule_name,
            rule_file=rule_file,
            trigger_hash=trigger_hash,
            status=QueueEntryStatus.QUEUED,
            baseline_ref=baseline_ref,
            trigger_files=trigger_files,
            expected_files=expected_files or [],
        )

        path = self._get_entry_path(trigger_hash, QueueEntryStatus.QUEUED)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, indent=2)

        return entry

    def update_status(
        self,
        trigger_hash: str,
        new_status: QueueEntryStatus,
        action_result: ActionResult | None = None,
    ) -> bool:
        """
        Update the status of an entry.

        This renames the file to reflect the new status.

        Args:
            trigger_hash: Hash of the entry to update
            new_status: New status
            action_result: Optional result of action execution

        Returns:
            True if updated, False if entry not found
        """
        old_path = self._find_entry_path(trigger_hash)
        if old_path is None:
            return False

        # Load existing entry
        try:
            with open(old_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return False

        # Update fields
        data["status"] = new_status.value
        data["evaluated_at"] = datetime.now(UTC).isoformat()
        if action_result:
            data["action_result"] = asdict(action_result)

        # Write to new path
        new_path = self._get_entry_path(trigger_hash, new_status)

        # If status didn't change, just update in place
        if old_path == new_path:
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        else:
            # Write new file then delete old
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            old_path.unlink()

        return True

    def get_queued_entries(self) -> list[QueueEntry]:
        """Get all entries with QUEUED status."""
        if not self.queue_dir.exists():
            return []

        entries = []
        for path in self.queue_dir.glob("*.queued.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                entries.append(QueueEntry.from_dict(data))
            except (json.JSONDecodeError, OSError, KeyError):
                continue

        return entries

    def get_all_entries(self) -> list[QueueEntry]:
        """Get all entries regardless of status."""
        if not self.queue_dir.exists():
            return []

        entries = []
        for path in self.queue_dir.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                entries.append(QueueEntry.from_dict(data))
            except (json.JSONDecodeError, OSError, KeyError):
                continue

        return entries

    def clear(self) -> int:
        """
        Clear all entries from the queue.

        Returns:
            Number of entries removed
        """
        if not self.queue_dir.exists():
            return 0

        count = 0
        for path in self.queue_dir.glob("*.json"):
            try:
                path.unlink()
                count += 1
            except OSError:
                continue

        return count

    def remove_entry(self, trigger_hash: str) -> bool:
        """
        Remove an entry by hash.

        Returns:
            True if removed, False if not found
        """
        path = self._find_entry_path(trigger_hash)
        if path is None:
            return False

        try:
            path.unlink()
            return True
        except OSError:
            return False
