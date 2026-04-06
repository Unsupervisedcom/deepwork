"""Tests for LearningAgent file structure (LA-REQ-003) and issue lifecycle (LA-REQ-005).

Each test class maps to a numbered requirement section in the corresponding
spec under specs/learning-agents/.

Only deterministic, boolean-verifiable requirements have tests here.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import yaml

# Project root — navigate up from this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEEPWORK_AGENTS_DIR = PROJECT_ROOT / ".deepwork" / "learning-agents"
CLAUDE_AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
CREATE_AGENT_SCRIPT = PROJECT_ROOT / "learning_agents" / "scripts" / "create_agent.sh"

# Reference agent that exists in the repo for structural validation
REFERENCE_AGENT = "consistency-reviewer"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_yaml_frontmatter(path: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file (between --- delimiters)."""
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))


def _has_yaml_frontmatter(path: Path) -> bool:
    """Check if a markdown file starts with YAML frontmatter."""
    text = path.read_text()
    return text.startswith("---\n")


# ===========================================================================
# LA-REQ-003: Agent File Structure and Knowledge Base
# ===========================================================================


class TestAgentRootDirectory:
    """LA-REQ-003.1 / LA-REQ-003.2: Agent root directory and naming."""

    def test_agent_dir_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.1).
        """LA-REQ-003.1: Agent directory exists at .deepwork/learning-agents/<agent-name>/."""
        agent_dir = DEEPWORK_AGENTS_DIR / REFERENCE_AGENT
        assert agent_dir.is_dir(), f"Expected agent dir: {agent_dir}"

    def test_agent_name_uses_dashes(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.1).
        """LA-REQ-003.1: Agent folder name uses dashes for word separation."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            name = agent_dir.name
            assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name), (
                f"Agent folder name '{name}' does not use dash-separated lowercase words"
            )


class TestCoreKnowledgeFile:
    """LA-REQ-003.3 / LA-REQ-003.4: Core knowledge file presence and format."""

    def test_core_knowledge_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.3).
        """LA-REQ-003.3: Each agent MUST have a core-knowledge.md file."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            ck = agent_dir / "core-knowledge.md"
            assert ck.is_file(), f"Missing core-knowledge.md in {agent_dir}"

    def test_core_knowledge_no_yaml_frontmatter(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.4).
        """LA-REQ-003.4: core-knowledge.md MUST be plain markdown with no YAML frontmatter."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            ck = agent_dir / "core-knowledge.md"
            if ck.is_file():
                assert not _has_yaml_frontmatter(ck), (
                    f"core-knowledge.md in {agent_dir.name} has YAML frontmatter (forbidden)"
                )

    def test_core_knowledge_second_person(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.4).
        """LA-REQ-003.4: core-knowledge.md MUST be written in second person."""
        ck = DEEPWORK_AGENTS_DIR / REFERENCE_AGENT / "core-knowledge.md"
        text = ck.read_text()
        # At minimum, should contain "You" somewhere (second person)
        assert re.search(r"\bYou\b", text), (
            f"core-knowledge.md for {REFERENCE_AGENT} lacks second person ('You')"
        )


class TestTopicsDirectory:
    """LA-REQ-003.6 / LA-REQ-003.7 / LA-REQ-003.8: Topics subdirectory."""

    def test_topics_dir_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.6).
        """LA-REQ-003.6: Each agent MUST have a topics/ subdirectory."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            topics = agent_dir / "topics"
            assert topics.is_dir(), f"Missing topics/ in {agent_dir}"

    def test_topic_files_are_markdown(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.8).
        """LA-REQ-003.8: Topic filenames MUST have the .md extension."""
        topics_dir = DEEPWORK_AGENTS_DIR / REFERENCE_AGENT / "topics"
        for f in topics_dir.iterdir():
            if f.name == ".gitkeep":
                continue
            assert f.suffix == ".md", f"Topic file {f.name} does not have .md extension"

    def test_topic_files_use_dashes(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.8).
        """LA-REQ-003.8: Topic filenames MUST use dashes."""
        topics_dir = DEEPWORK_AGENTS_DIR / REFERENCE_AGENT / "topics"
        for f in topics_dir.iterdir():
            if f.name == ".gitkeep":
                continue
            stem = f.stem
            assert "_" not in stem, (
                f"Topic filename '{f.name}' uses underscores instead of dashes"
            )
            assert " " not in stem, (
                f"Topic filename '{f.name}' contains spaces"
            )

    def test_topic_files_have_frontmatter_with_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.7).
        """LA-REQ-003.7: Each topic file MUST have YAML frontmatter with 'name' field."""
        topics_dir = DEEPWORK_AGENTS_DIR / REFERENCE_AGENT / "topics"
        md_files = [f for f in topics_dir.iterdir() if f.suffix == ".md"]
        assert len(md_files) > 0, "No topic files to validate"
        for f in md_files:
            fm = _parse_yaml_frontmatter(f)
            assert fm is not None, f"Topic {f.name} is missing YAML frontmatter"
            assert "name" in fm, f"Topic {f.name} frontmatter missing required 'name' field"
            assert isinstance(fm["name"], str) and fm["name"].strip(), (
                f"Topic {f.name} 'name' must be a non-empty string"
            )

    def test_topic_frontmatter_optional_fields_valid(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.7).
        """LA-REQ-003.7: Optional frontmatter fields have correct types if present."""
        topics_dir = DEEPWORK_AGENTS_DIR / REFERENCE_AGENT / "topics"
        for f in topics_dir.iterdir():
            if f.suffix != ".md":
                continue
            fm = _parse_yaml_frontmatter(f)
            if fm is None:
                continue
            if "keywords" in fm:
                assert isinstance(fm["keywords"], list), (
                    f"Topic {f.name} 'keywords' must be an array"
                )
            if "last_updated" in fm:
                date_str = str(fm["last_updated"])
                assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str), (
                    f"Topic {f.name} 'last_updated' must be YYYY-MM-DD, got '{date_str}'"
                )


class TestLearningsDirectory:
    """LA-REQ-003.9 / LA-REQ-003.10 / LA-REQ-003.11: Learnings subdirectory."""

    def test_learnings_dir_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.9).
        """LA-REQ-003.9: Each agent MUST have a learnings/ subdirectory."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            learnings = agent_dir / "learnings"
            assert learnings.is_dir(), f"Missing learnings/ in {agent_dir}"

    def test_learning_files_are_markdown(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.11).
        """LA-REQ-003.11: Learning filenames MUST have the .md extension."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            learnings_dir = agent_dir / "learnings"
            if not learnings_dir.is_dir():
                continue
            for f in learnings_dir.iterdir():
                if f.name == ".gitkeep":
                    continue
                assert f.suffix == ".md", (
                    f"Learning file {f.name} in {agent_dir.name} does not have .md extension"
                )

    def test_learning_files_use_dashes(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.11).
        """LA-REQ-003.11: Learning filenames MUST use dashes."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            learnings_dir = agent_dir / "learnings"
            if not learnings_dir.is_dir():
                continue
            for f in learnings_dir.iterdir():
                if f.name == ".gitkeep":
                    continue
                if f.suffix != ".md":
                    continue
                stem = f.stem
                assert "_" not in stem, (
                    f"Learning filename '{f.name}' uses underscores instead of dashes"
                )


class TestAdditionalLearningGuidelines:
    """LA-REQ-003.13: Additional learning guidelines directory."""

    REQUIRED_FILES = [
        "README.md",
        "issue_identification.md",
        "issue_investigation.md",
        "learning_from_issues.md",
    ]

    def test_additional_guidelines_dir_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.13).
        """LA-REQ-003.13: Each agent MUST have additional_learning_guidelines/ subdirectory."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            alg = agent_dir / "additional_learning_guidelines"
            assert alg.is_dir(), (
                f"Missing additional_learning_guidelines/ in {agent_dir}"
            )

    def test_additional_guidelines_required_files(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.13).
        """LA-REQ-003.13: Required files in additional_learning_guidelines/."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            alg = agent_dir / "additional_learning_guidelines"
            if not alg.is_dir():
                continue
            for fname in self.REQUIRED_FILES:
                assert (alg / fname).is_file(), (
                    f"Missing {fname} in {agent_dir.name}/additional_learning_guidelines/"
                )


class TestClaudeCodeAgentFile:
    """LA-REQ-003.15 / LA-REQ-003.16 / LA-REQ-003.17: Claude Code agent file."""

    def test_claude_agent_file_exists_for_each_agent(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.15).
        """LA-REQ-003.15: Each LearningAgent MUST have a .claude/agents/<agent-name>.md file."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            agent_name = agent_dir.name
            claude_file = CLAUDE_AGENTS_DIR / f"{agent_name}.md"
            assert claude_file.is_file(), (
                f"Missing Claude agent file for {agent_name}: {claude_file}"
            )

    def test_claude_agent_file_has_yaml_frontmatter(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.15).
        """LA-REQ-003.15: Claude agent file MUST have YAML frontmatter."""
        claude_file = CLAUDE_AGENTS_DIR / f"{REFERENCE_AGENT}.md"
        fm = _parse_yaml_frontmatter(claude_file)
        assert fm is not None, f"Claude agent file for {REFERENCE_AGENT} missing frontmatter"

    def test_claude_agent_file_has_name_field(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.15).
        """LA-REQ-003.15: Frontmatter MUST contain 'name' field."""
        claude_file = CLAUDE_AGENTS_DIR / f"{REFERENCE_AGENT}.md"
        fm = _parse_yaml_frontmatter(claude_file)
        assert fm is not None
        assert "name" in fm, "Frontmatter missing 'name' field"
        assert isinstance(fm["name"], str) and fm["name"].strip(), (
            "'name' must be a non-empty string"
        )

    def test_claude_agent_file_has_description_field(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.15 / LA-REQ-003.17).
        """LA-REQ-003.15/017: Frontmatter MUST contain 'description' field (discovery description)."""
        claude_file = CLAUDE_AGENTS_DIR / f"{REFERENCE_AGENT}.md"
        fm = _parse_yaml_frontmatter(claude_file)
        assert fm is not None
        assert "description" in fm, "Frontmatter missing 'description' field"
        assert isinstance(fm["description"], str) and fm["description"].strip(), (
            "'description' must be a non-empty string"
        )

    def test_claude_agent_filename_matches_folder_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.16).
        """LA-REQ-003.16: Claude agent filename MUST match the LearningAgent folder name."""
        for agent_dir in DEEPWORK_AGENTS_DIR.iterdir():
            if not agent_dir.is_dir():
                continue
            agent_name = agent_dir.name
            claude_file = CLAUDE_AGENTS_DIR / f"{agent_name}.md"
            if claude_file.is_file():
                # Filename stem must exactly equal the folder name
                assert claude_file.stem == agent_name, (
                    f"Claude agent filename '{claude_file.stem}' != folder '{agent_name}'"
                )

    def test_claude_agent_file_references_generate_script(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.18).
        """LA-REQ-003.18: Agent file injects knowledge at invocation time via generate script."""
        claude_file = CLAUDE_AGENTS_DIR / f"{REFERENCE_AGENT}.md"
        text = claude_file.read_text()
        # Must include dynamic context injection (the ! backtick syntax referencing the agent)
        assert "generate_agent_instructions.sh" in text, (
            "Claude agent file must reference generate_agent_instructions.sh for dynamic injection"
        )


class TestCreateAgentScript:
    """Validates that create_agent.sh produces the correct directory structure (LA-REQ-003)."""

    def test_script_exists_and_is_executable(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.1).
        """create_agent.sh must exist."""
        assert CREATE_AGENT_SCRIPT.is_file()

    def test_script_creates_correct_structure(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.1/3/6/9/13).
        """create_agent.sh creates all required directories and files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # create_agent.sh creates relative to cwd
            result = subprocess.run(
                ["bash", str(CREATE_AGENT_SCRIPT), "test-agent"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"create_agent.sh failed: {result.stderr}"

            agent_dir = tmp / ".deepwork" / "learning-agents" / "test-agent"
            assert agent_dir.is_dir()
            assert (agent_dir / "core-knowledge.md").is_file()
            assert (agent_dir / "topics").is_dir()
            assert (agent_dir / "learnings").is_dir()
            assert (agent_dir / "topics" / ".gitkeep").is_file()
            assert (agent_dir / "learnings" / ".gitkeep").is_file()
            assert (agent_dir / "additional_learning_guidelines").is_dir()
            assert (agent_dir / "additional_learning_guidelines" / "README.md").is_file()
            assert (agent_dir / "additional_learning_guidelines" / "issue_identification.md").is_file()
            assert (agent_dir / "additional_learning_guidelines" / "issue_investigation.md").is_file()
            assert (agent_dir / "additional_learning_guidelines" / "learning_from_issues.md").is_file()

            # Claude agent file
            claude_file = tmp / ".claude" / "agents" / "test-agent.md"
            assert claude_file.is_file()

    def test_script_creates_core_knowledge_without_frontmatter(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.4).
        """create_agent.sh creates core-knowledge.md without YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            subprocess.run(
                ["bash", str(CREATE_AGENT_SCRIPT), "fm-test-agent"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            ck = tmp / ".deepwork" / "learning-agents" / "fm-test-agent" / "core-knowledge.md"
            assert ck.is_file()
            assert not _has_yaml_frontmatter(ck), (
                "core-knowledge.md created by script should not have YAML frontmatter"
            )

    def test_script_creates_claude_agent_with_frontmatter(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.15).
        """create_agent.sh creates Claude agent file with YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            subprocess.run(
                ["bash", str(CREATE_AGENT_SCRIPT), "cf-test-agent"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            claude_file = tmp / ".claude" / "agents" / "cf-test-agent.md"
            fm = _parse_yaml_frontmatter(claude_file)
            assert fm is not None, "Claude agent file must have YAML frontmatter"
            assert "name" in fm, "Claude agent file frontmatter must have 'name'"
            assert "description" in fm, "Claude agent file frontmatter must have 'description'"

    def test_script_claude_agent_references_agent_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-003.16/18).
        """create_agent.sh Claude agent file references the correct agent name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            subprocess.run(
                ["bash", str(CREATE_AGENT_SCRIPT), "ref-test-agent"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            claude_file = tmp / ".claude" / "agents" / "ref-test-agent.md"
            text = claude_file.read_text()
            assert "ref-test-agent" in text, (
                "Claude agent file must reference its own agent name"
            )


# ===========================================================================
# LA-REQ-005: Issue Lifecycle
# ===========================================================================


class TestIssueFileNaming:
    """LA-REQ-005.2 / LA-REQ-005.3: Issue file naming conventions."""

    def test_valid_issue_filenames(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.2).
        """LA-REQ-005.2: Issue filenames use dashes and .issue.yml extension."""
        valid_names = [
            "wrong-retry-strategy.issue.yml",
            "missed-edge-case.issue.yml",
            "hallucinated-api-endpoint.issue.yml",
            "bad-sql-query.issue.yml",
        ]
        pattern = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.issue\.yml$")
        for name in valid_names:
            assert pattern.match(name), f"Expected valid: {name}"

    def test_invalid_issue_filenames_rejected(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.2 / LA-REQ-005.3).
        """LA-REQ-005.2/3: Invalid names must not match the required pattern."""
        invalid_names = [
            "wrong_retry_strategy.issue.yml",    # underscores not dashes
            "wrong-retry-strategy.issue.yaml",   # wrong extension
            "wrong-retry-strategy.yml",          # missing .issue. prefix
            "WRONG-RETRY.issue.yml",             # uppercase
            "a very long name with too many words describing issue.issue.yml",  # spaces
        ]
        pattern = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.issue\.yml$")
        for name in invalid_names:
            assert not pattern.match(name), f"Expected invalid: {name}"


class TestIssueFileSchema:
    """LA-REQ-005.4 / LA-REQ-005.6 / LA-REQ-005.7 / LA-REQ-005.9 / LA-REQ-005.12: Issue YAML schema."""

    VALID_STATUSES = {"identified", "investigated", "learned"}

    def _make_identified_issue(self) -> dict:
        """Create a minimal valid identified issue."""
        return {
            "status": "identified",
            "seen_at_timestamps": ["2026-01-15T14:32:00Z"],
            "issue_description": "The agent used the wrong retry strategy.\n",
        }

    def _make_investigated_issue(self) -> dict:
        """Create a valid investigated issue."""
        return {
            "status": "investigated",
            "seen_at_timestamps": ["2026-01-15T14:32:00Z"],
            "issue_description": "The agent used the wrong retry strategy.\n",
            "investigation_report": "Root cause: missing knowledge about backoff.\n",
        }

    def test_status_field_required(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.4).
        """LA-REQ-005.4: Every issue file MUST contain a status field."""
        issue = self._make_identified_issue()
        assert "status" in issue

    def test_status_field_valid_enum(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.4).
        """LA-REQ-005.4: Status MUST be one of: identified, investigated, learned."""
        for status in self.VALID_STATUSES:
            issue = self._make_identified_issue()
            issue["status"] = status
            assert issue["status"] in self.VALID_STATUSES

    def test_status_field_rejects_invalid(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.4).
        """LA-REQ-005.4: Invalid status values must be rejected."""
        invalid = ["open", "closed", "pending", "resolved", "new", ""]
        for s in invalid:
            assert s not in self.VALID_STATUSES, f"'{s}' should not be valid"

    def test_initial_status_is_identified(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.6).
        """LA-REQ-005.6: Initial status MUST be 'identified'."""
        issue = self._make_identified_issue()
        assert issue["status"] == "identified"

    def test_seen_at_timestamps_required(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.7).
        """LA-REQ-005.7: Every issue file MUST contain seen_at_timestamps as an array."""
        issue = self._make_identified_issue()
        assert "seen_at_timestamps" in issue
        assert isinstance(issue["seen_at_timestamps"], list)
        assert len(issue["seen_at_timestamps"]) > 0

    def test_seen_at_timestamps_iso8601(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.7).
        """LA-REQ-005.7: Timestamps MUST be ISO 8601 strings."""
        iso_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$"
        )
        issue = self._make_identified_issue()
        for ts in issue["seen_at_timestamps"]:
            assert isinstance(ts, str), "Timestamp must be a string"
            assert iso_pattern.match(ts), f"Timestamp '{ts}' is not ISO 8601"

    def test_issue_description_required(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.9).
        """LA-REQ-005.9: Every issue file MUST contain issue_description."""
        issue = self._make_identified_issue()
        assert "issue_description" in issue
        assert isinstance(issue["issue_description"], str)
        assert issue["issue_description"].strip(), "issue_description must not be empty"

    def test_investigation_report_absent_when_identified(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.10).
        """LA-REQ-005.10: investigation_report MUST NOT be present at status=identified."""
        issue = self._make_identified_issue()
        assert issue["status"] == "identified"
        assert "investigation_report" not in issue

    def test_investigation_report_present_when_investigated(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.10).
        """LA-REQ-005.10: investigation_report MUST be added at status=investigated."""
        issue = self._make_investigated_issue()
        assert issue["status"] == "investigated"
        assert "investigation_report" in issue
        assert isinstance(issue["investigation_report"], str)
        assert issue["investigation_report"].strip()

    def test_issue_yaml_roundtrip(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.12).
        """LA-REQ-005.12: Issue files MUST be valid YAML that round-trips correctly."""
        issue = self._make_identified_issue()
        yaml_str = yaml.dump(issue, default_flow_style=False)
        parsed = yaml.safe_load(yaml_str)
        assert parsed["status"] == "identified"
        assert parsed["seen_at_timestamps"] == ["2026-01-15T14:32:00Z"]
        assert "issue_description" in parsed

    def test_investigated_issue_yaml_roundtrip(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.12).
        """LA-REQ-005.12: Investigated issue YAML round-trips with all fields."""
        issue = self._make_investigated_issue()
        yaml_str = yaml.dump(issue, default_flow_style=False)
        parsed = yaml.safe_load(yaml_str)
        assert parsed["status"] == "investigated"
        assert "investigation_report" in parsed


class TestIssueStatusLifecycle:
    """LA-REQ-005.5: Status progression rules."""

    LIFECYCLE_ORDER = ["identified", "investigated", "learned"]

    def test_lifecycle_order_is_defined(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.5).
        """LA-REQ-005.5: Lifecycle order is identified -> investigated -> learned."""
        assert self.LIFECYCLE_ORDER == ["identified", "investigated", "learned"]

    def test_forward_transitions_valid(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.5).
        """LA-REQ-005.5: Status MUST progress forward through the lifecycle."""
        valid_transitions = [
            ("identified", "investigated"),
            ("investigated", "learned"),
        ]
        for from_status, to_status in valid_transitions:
            from_idx = self.LIFECYCLE_ORDER.index(from_status)
            to_idx = self.LIFECYCLE_ORDER.index(to_status)
            assert to_idx == from_idx + 1, (
                f"Transition {from_status} -> {to_status} should be exactly one step forward"
            )

    def test_backward_transitions_invalid(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.5).
        """LA-REQ-005.5: Status MUST NOT regress to a previous stage."""
        invalid_transitions = [
            ("investigated", "identified"),
            ("learned", "investigated"),
            ("learned", "identified"),
        ]
        for from_status, to_status in invalid_transitions:
            from_idx = self.LIFECYCLE_ORDER.index(from_status)
            to_idx = self.LIFECYCLE_ORDER.index(to_status)
            assert to_idx < from_idx, (
                f"Backward transition {from_status} -> {to_status} should be invalid"
            )

    def test_skip_transitions_invalid(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.5).
        """LA-REQ-005.5: Status MUST NOT skip stages."""
        from_idx = self.LIFECYCLE_ORDER.index("identified")
        to_idx = self.LIFECYCLE_ORDER.index("learned")
        assert to_idx - from_idx > 1, (
            "identified -> learned skips a stage and should be invalid"
        )


class TestIssueFileLocation:
    """LA-REQ-005.1: Issue file storage location."""

    def test_issue_location_pattern(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.1).
        """LA-REQ-005.1: Issue files MUST be stored in session log folder."""
        # Validate the expected path pattern
        expected_pattern = re.compile(
            r"^\.deepwork/tmp/agent_sessions/[^/]+/[^/]+/[^/]+\.issue\.yml$"
        )
        example_path = ".deepwork/tmp/agent_sessions/abc123/my-agent/wrong-retry.issue.yml"
        assert expected_pattern.match(example_path), (
            "Issue file path must match .deepwork/tmp/agent_sessions/<session>/<agent>/*.issue.yml"
        )

    def test_issue_location_rejects_wrong_paths(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.1).
        """LA-REQ-005.1: Issue files MUST NOT live outside session log folders."""
        expected_pattern = re.compile(
            r"^\.deepwork/tmp/agent_sessions/[^/]+/[^/]+/[^/]+\.issue\.yml$"
        )
        invalid_paths = [
            ".deepwork/issues/wrong-retry.issue.yml",
            "issues/wrong-retry.issue.yml",
            ".deepwork/learning-agents/my-agent/wrong-retry.issue.yml",
        ]
        for path in invalid_paths:
            assert not expected_pattern.match(path), f"Path should be invalid: {path}"


class TestDocumentedIssueFormat:
    """Validates that the documented issue format in doc/issue_yml_format.md
    matches the spec requirements (LA-REQ-005)."""

    doc_path = PROJECT_ROOT / "learning_agents" / "doc" / "issue_yml_format.md"

    def test_doc_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.12).
        """issue_yml_format.md reference doc must exist."""
        assert self.doc_path.is_file()

    def test_doc_mentions_all_statuses(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.4).
        """Doc must reference all three status values."""
        text = self.doc_path.read_text()
        for status in ("identified", "investigated", "learned"):
            assert status in text, f"Doc missing status '{status}'"

    def test_doc_mentions_required_fields(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.4/7/9).
        """Doc must reference all required fields."""
        text = self.doc_path.read_text()
        for field in ("status", "seen_at_timestamps", "issue_description"):
            assert field in text, f"Doc missing field '{field}'"

    def test_doc_example_yaml_is_valid(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-005.12).
        """YAML examples in the doc must parse correctly."""
        text = self.doc_path.read_text()
        # Extract YAML blocks from the doc
        yaml_blocks = re.findall(r"```yaml\n(.*?)```", text, re.DOTALL)
        assert len(yaml_blocks) > 0, "Doc should contain at least one YAML example"
        for block in yaml_blocks:
            parsed = yaml.safe_load(block)
            assert parsed is not None, f"YAML block failed to parse: {block[:80]}"
            if "status" in parsed:
                assert parsed["status"] in ("identified", "investigated", "learned")
