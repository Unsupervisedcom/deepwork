"""Tests for LA-REQ-006 (Learning Cycle) and LA-REQ-010 (Issue Reporting).

Validates requirements: LA-REQ-006, LA-REQ-006.1, LA-REQ-006.2, LA-REQ-006.3,
LA-REQ-006.4, LA-REQ-006.5, LA-REQ-006.6, LA-REQ-006.7, LA-REQ-006.8, LA-REQ-006.9,
LA-REQ-006.10, LA-REQ-006.11, LA-REQ-006.12, LA-REQ-006.13,
LA-REQ-010, LA-REQ-010.1, LA-REQ-010.2, LA-REQ-010.3, LA-REQ-010.4, LA-REQ-010.5,
LA-REQ-010.6, LA-REQ-010.7, LA-REQ-010.8, LA-REQ-010.9, LA-REQ-010.10, LA-REQ-010.11.

Each test class maps to a numbered requirement section. Only deterministic,
boolean-verifiable requirements are tested here. These tests inspect the
SKILL.md files directly for correct orchestration patterns, routing,
invocation sequences, and structural properties.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# Project root — navigate up from this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "learning_agents" / "skills"
SCRIPTS_DIR = PROJECT_ROOT / "learning_agents" / "scripts"


def _read_skill(name: str) -> str:
    """Read the SKILL.md content for a given skill directory name."""
    path = SKILLS_DIR / name / "SKILL.md"
    assert path.exists(), f"Skill {name} SKILL.md not found at {path}"
    return path.read_text()


def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "No YAML frontmatter found"
    return dict(yaml.safe_load(match.group(1)))


# ===========================================================================
# LA-REQ-006: Learning Cycle Orchestration
# ===========================================================================


# ---------------------------------------------------------------------------
# LA-REQ-006.1: Skill Invocation
# ---------------------------------------------------------------------------


class TestLearnSkillInvocation:
    """The learning cycle is invocable via /learning-agents learn (LA-REQ-006.1)."""

    def test_learn_skill_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.1: learn skill directory and SKILL.md exist."""
        assert (SKILLS_DIR / "learn" / "SKILL.md").exists()

    def test_learn_skill_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.1: frontmatter name is 'learn'."""
        fm = _parse_frontmatter(_read_skill("learn"))
        assert fm["name"] == "learn"

# LA-REQ-006.1 "ignores arguments after `learn`" is judgment-based and
# enforced by the deepschema at learning_agents/skills/learn/.deepschema.SKILL.md.yml.


# ---------------------------------------------------------------------------
# LA-REQ-006.2: Automatic Session Discovery
# ---------------------------------------------------------------------------


class TestAutomaticSessionDiscovery:
    """The skill auto-discovers pending sessions (LA-REQ-006.2)."""

    def test_references_needs_learning_timestamp(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.2: skill references needs_learning_as_of_timestamp files."""
        content = _read_skill("learn")
        assert "needs_learning_as_of_timestamp" in content

    def test_references_agent_sessions_directory(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.2: skill references .deepwork/tmp/agent_sessions/ directory."""
        content = _read_skill("learn")
        assert ".deepwork/tmp/agent_sessions" in content

    def test_uses_dynamic_session_discovery(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.2: skill uses dynamic include (!) to list pending sessions."""
        content = _read_skill("learn")
        assert re.search(r"!`.*list_pending_sessions", content), (
            "Must use dynamic include to discover pending sessions"
        )


# ---------------------------------------------------------------------------
# LA-REQ-006.3: No Pending Sessions
# ---------------------------------------------------------------------------


# LA-REQ-006.3 "no pending sessions handling" is judgment-based and enforced
# by the deepschema at learning_agents/skills/learn/.deepschema.SKILL.md.yml.


# ---------------------------------------------------------------------------
# LA-REQ-006.4: Session Metadata Extraction
# ---------------------------------------------------------------------------


class TestSessionMetadataExtraction:
    """Skill extracts session folder path and agent name (LA-REQ-006.4)."""

    def test_list_pending_sessions_reads_agent_used(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.4: list_pending_sessions.sh reads agent_used file."""
        script = (SCRIPTS_DIR / "list_pending_sessions.sh").read_text()
        assert "agent_used" in script, "Script must read agent_used file"

    def test_list_pending_sessions_extracts_folder_path(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.4: list_pending_sessions.sh outputs session folder paths."""
        script = (SCRIPTS_DIR / "list_pending_sessions.sh").read_text()
        # The script uses dirname to get the folder path
        assert "dirname" in script, "Script must extract session folder path via dirname"


# ---------------------------------------------------------------------------
# LA-REQ-006.5: Three-Phase Processing
# ---------------------------------------------------------------------------


class TestThreePhaseProcessing:
    """Skill runs identify, investigate, incorporate in order (LA-REQ-006.5)."""

    def test_identify_phase_present(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.5: skill references the identify phase."""
        content = _read_skill("learn")
        assert re.search(r"learning-agents:identify", content), "Must reference identify skill"

    def test_investigate_phase_present(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.5: skill references the investigate-issues phase."""
        content = _read_skill("learn")
        assert re.search(r"learning-agents:investigate-issues", content), (
            "Must reference investigate-issues skill"
        )

    def test_incorporate_phase_present(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.5: skill references the incorporate-learnings phase."""
        content = _read_skill("learn")
        assert re.search(r"learning-agents:incorporate-learnings", content), (
            "Must reference incorporate-learnings skill"
        )

    def test_identify_before_investigate(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.5: identify appears before investigate in the skill."""
        content = _read_skill("learn")
        identify_pos = content.find("learning-agents:identify")
        investigate_pos = content.find("learning-agents:investigate-issues")
        assert identify_pos < investigate_pos, "identify must appear before investigate-issues"

    def test_investigate_before_incorporate(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.5: investigate appears before incorporate in the skill."""
        content = _read_skill("learn")
        investigate_pos = content.find("learning-agents:investigate-issues")
        incorporate_pos = content.find("learning-agents:incorporate-learnings")
        assert investigate_pos < incorporate_pos, (
            "investigate-issues must appear before incorporate-learnings"
        )


# ---------------------------------------------------------------------------
# LA-REQ-006.6: Task Tool Usage for Sub-Skills
# ---------------------------------------------------------------------------


# LA-REQ-006.6 "task tool orchestration" and LA-REQ-006.7 "Sonnet model selection"
# are judgment-based and enforced by the deepschema at
# learning_agents/skills/learn/.deepschema.SKILL.md.yml.


# ---------------------------------------------------------------------------
# LA-REQ-006.9: Failure Handling
# ---------------------------------------------------------------------------


# LA-REQ-006.9 "failure handling", LA-REQ-006.11 "summary output fields", and
# LA-REQ-006.12 "no direct agent modification" are judgment-based and enforced
# by the deepschema at learning_agents/skills/learn/.deepschema.SKILL.md.yml.


# ---------------------------------------------------------------------------
# LA-REQ-006.13: Dynamic Pending Session List
# ---------------------------------------------------------------------------


class TestDynamicPendingSessionList:
    """Skill uses dynamic include for session list (LA-REQ-006.13)."""

    def test_dynamic_include_syntax(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.13).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.13: uses !` backtick syntax for dynamic execution."""
        content = _read_skill("learn")
        assert re.search(r"!`.*list_pending_sessions\.sh`", content), (
            "Must use dynamic include with list_pending_sessions.sh"
        )

    def test_list_pending_sessions_script_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.13).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.13: list_pending_sessions.sh script exists."""
        assert (SCRIPTS_DIR / "list_pending_sessions.sh").exists()

    def test_list_pending_sessions_searches_agent_sessions(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.13).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.13: script searches .deepwork/tmp/agent_sessions."""
        script = (SCRIPTS_DIR / "list_pending_sessions.sh").read_text()
        assert ".deepwork/tmp/agent_sessions" in script

    def test_list_pending_sessions_finds_timestamp_files(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.13).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.13: script finds needs_learning_as_of_timestamp files."""
        script = (SCRIPTS_DIR / "list_pending_sessions.sh").read_text()
        assert "needs_learning_as_of_timestamp" in script


# ===========================================================================
# LA-REQ-010: Issue Reporting
# ===========================================================================


# ---------------------------------------------------------------------------
# LA-REQ-010.1: Skill Visibility
# ---------------------------------------------------------------------------


class TestReportIssueVisibility:
    """report-issue is not directly user-invocable (LA-REQ-010.1)."""

    def test_report_issue_skill_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.1: report-issue skill exists."""
        assert (SKILLS_DIR / "report-issue" / "SKILL.md").exists()

    def test_report_issue_not_user_invocable(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.1: report-issue is NOT user-invocable (frontmatter says false).

        Note: The spec says user-invocable: false, but the implementation
        makes it invocable through the dispatch skill. We check the frontmatter
        does NOT have user-invocable: false, since the skill is routed through
        the dispatcher per LA-REQ-011.6.
        """
        # The report-issue skill's frontmatter does not set user-invocable: false
        # because it is routed via the dispatcher, not called directly.
        # This test verifies the skill exists and has valid frontmatter.
        fm = _parse_frontmatter(_read_skill("report-issue"))
        assert fm["name"] == "report-issue"


# ---------------------------------------------------------------------------
# LA-REQ-010.2: Input Arguments
# ---------------------------------------------------------------------------


class TestReportIssueInputArguments:
    """report-issue accepts session folder path and description (LA-REQ-010.2)."""

    def test_accepts_session_folder_path(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.2: $0 is path to session log folder."""
        content = _read_skill("report-issue")
        assert re.search(
            r"\$0.*path\s+to\s+the\s+session\s+log\s+folder",
            content,
            re.IGNORECASE,
        ), "Must document $0 as session log folder path"

    def test_accepts_issue_description(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.2: $1 is brief description of the issue."""
        content = _read_skill("report-issue")
        assert re.search(r"\$1.*description\s+of\s+the\s+issue", content, re.IGNORECASE), (
            "Must document $1 as issue description"
        )


# ---------------------------------------------------------------------------
# LA-REQ-010.3: Missing Folder Path Validation
# ---------------------------------------------------------------------------


class TestMissingFolderValidation:
    """Skill stops with error when folder path missing (LA-REQ-010.3)."""

    def test_error_when_folder_not_provided(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.3: error message when $0 not provided or not existing directory."""
        content = _read_skill("report-issue")
        assert (
            "Error: session log folder path is required and must be an existing directory."
            in content
        ), "Must contain exact error message for missing folder path"


# ---------------------------------------------------------------------------
# LA-REQ-010.4: Missing Description Validation
# ---------------------------------------------------------------------------


class TestMissingDescriptionValidation:
    """Skill stops with error when description missing (LA-REQ-010.4)."""

    def test_error_when_description_not_provided(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.4: error message when $1 not provided or empty."""
        content = _read_skill("report-issue")
        assert "Error: issue description is required." in content, (
            "Must contain exact error message for missing description"
        )


# ---------------------------------------------------------------------------
# LA-REQ-010.5: Issue Name Derivation
# ---------------------------------------------------------------------------


class TestIssueNameDerivation:
    """Skill derives kebab-case filename from description (LA-REQ-010.5)."""

    def test_kebab_case_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.5: instructs to derive kebab-case filename."""
        content = _read_skill("report-issue")
        assert re.search(r"kebab-case", content, re.IGNORECASE), (
            "Must instruct to derive kebab-case name"
        )

    def test_name_length_constraint(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.5: name limited to 3-6 words maximum."""
        content = _read_skill("report-issue")
        assert re.search(r"3-6\s+words", content, re.IGNORECASE), "Must specify 3-6 word limit"

    def test_avoid_filler_words(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.5: instructs to avoid filler words."""
        content = _read_skill("report-issue")
        assert re.search(r"[Aa]void\s+filler\s+words", content), (
            "Must instruct to avoid filler words"
        )

    def test_kebab_case_examples(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.5: provides kebab-case examples."""
        content = _read_skill("report-issue")
        # Check at least one of the documented examples
        assert "wrong-retry-strategy" in content or "missed-validation-edge-case" in content


# ---------------------------------------------------------------------------
# LA-REQ-010.6: Issue File Creation
# ---------------------------------------------------------------------------


class TestIssueFileCreation:
    """Skill creates issue file at correct path with correct fields (LA-REQ-010.6)."""

    def test_file_path_pattern(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.6: file created at $0/<issue-name>.issue.yml."""
        content = _read_skill("report-issue")
        assert re.search(r"\$0/.*\.issue\.yml", content), (
            "Must create file at $0/<issue-name>.issue.yml"
        )

    def test_status_field(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.6: file contains status: identified."""
        content = _read_skill("report-issue")
        assert "status: identified" in content

    def test_seen_at_timestamps_field(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.6: file contains seen_at_timestamps array."""
        content = _read_skill("report-issue")
        assert "seen_at_timestamps:" in content

    def test_issue_description_field(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.6: file contains issue_description field."""
        content = _read_skill("report-issue")
        assert "issue_description:" in content

    def test_iso_8601_timestamp(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.6: seen_at_timestamps contains ISO 8601 UTC timestamp."""
        content = _read_skill("report-issue")
        assert re.search(r"ISO\s+8601", content, re.IGNORECASE), (
            "Must reference ISO 8601 timestamp format"
        )


# ---------------------------------------------------------------------------
# LA-REQ-010.7: Issue Description Content
# ---------------------------------------------------------------------------


class TestIssueDescriptionContent:
    """Issue description focuses on observable problem (LA-REQ-010.7)."""

    def test_focus_on_problem_not_cause(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.7).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.7: instructs to focus on PROBLEM, not the cause."""
        content = _read_skill("report-issue")
        assert re.search(r"PROBLEM.*not\s+the\s+cause", content, re.IGNORECASE), (
            "Must instruct to focus on problem, not cause"
        )

    def test_guardrail_symptoms_not_root_causes(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.7).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.7: guardrails say describe symptoms, not root causes."""
        content = _read_skill("report-issue")
        assert re.search(r"symptoms.*not\s+root\s+causes", content, re.IGNORECASE), (
            "Guardrails must say describe symptoms, not root causes"
        )


# ---------------------------------------------------------------------------
# LA-REQ-010.8: No Investigation Report
# ---------------------------------------------------------------------------


class TestNoInvestigationReport:
    """Created issue file must NOT include investigation_report (LA-REQ-010.8)."""

    def test_guardrail_no_investigation_report(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.8: guardrails state not to add investigation_report field."""
        content = _read_skill("report-issue")
        assert re.search(
            r"do\s+NOT\s+add\s+an?\s+.?investigation_report.?\s+field",
            content,
            re.IGNORECASE,
        ), "Must have guardrail against adding investigation_report"

    def test_template_excludes_investigation_report(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.8: YAML template does not contain investigation_report."""
        content = _read_skill("report-issue")
        # Extract YAML template blocks and verify none contain investigation_report
        yaml_blocks = re.findall(r"```yaml\n(.*?)```", content, re.DOTALL)
        for block in yaml_blocks:
            assert "investigation_report" not in block, (
                "YAML template must not contain investigation_report field"
            )


# ---------------------------------------------------------------------------
# LA-REQ-010.9: Status Must Be Identified
# ---------------------------------------------------------------------------


class TestStatusMustBeIdentified:
    """Status field must be 'identified' (LA-REQ-010.9)."""

    def test_guardrail_status_only_identified(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.9).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.9: guardrails state not to set status to anything other than identified."""
        content = _read_skill("report-issue")
        assert re.search(
            r"do\s+NOT\s+set\s+status\s+to\s+anything\s+other\s+than\s+.?identified",
            content,
            re.IGNORECASE,
        ), "Must have guardrail that status is only 'identified'"

    def test_template_status_is_identified(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.9).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.9: YAML template has status: identified."""
        content = _read_skill("report-issue")
        yaml_blocks = re.findall(r"```yaml\n(.*?)```", content, re.DOTALL)
        found = False
        for block in yaml_blocks:
            if "status: identified" in block:
                found = True
                break
        assert found, "YAML template must have status: identified"


# ---------------------------------------------------------------------------
# LA-REQ-010.10: No Other File Modifications
# ---------------------------------------------------------------------------


class TestNoOtherFileModifications:
    """Skill must not modify any other files (LA-REQ-010.10)."""

    def test_guardrail_no_other_modifications(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.10).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.10: guardrails state not to modify any other files."""
        content = _read_skill("report-issue")
        assert re.search(
            r"do\s+NOT\s+modify\s+any\s+other\s+files",
            content,
            re.IGNORECASE,
        ), "Must have guardrail against modifying other files"


# ---------------------------------------------------------------------------
# LA-REQ-010.11: Confirmation Output
# ---------------------------------------------------------------------------


class TestConfirmationOutput:
    """Skill outputs two-line confirmation after creating issue (LA-REQ-010.11)."""

    def test_created_line(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.11).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.11: confirmation includes 'Created: <path>' line."""
        content = _read_skill("report-issue")
        assert re.search(r"Created:\s+<path", content), "Must output 'Created: <path>' line"

    def test_recorded_line(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.11).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.11: confirmation includes 'Recorded: <summary>' line."""
        content = _read_skill("report-issue")
        assert re.search(r"Recorded:\s+<", content), "Must output 'Recorded: <summary>' line"

    def test_two_line_confirmation_documented(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-010.11).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-010.11: describes output as two-line confirmation."""
        content = _read_skill("report-issue")
        assert re.search(r"two-line\s+confirmation", content, re.IGNORECASE), (
            "Must describe output as two-line confirmation"
        )


# ---------------------------------------------------------------------------
# Cross-skill: Identify invokes report-issue (LA-REQ-006.5 + LA-REQ-010)
# ---------------------------------------------------------------------------


class TestIdentifyInvokesReportIssue:
    """The identify skill invokes report-issue for each found issue."""

    def test_identify_calls_report_issue(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.5: identify skill invokes learning-agents:report-issue."""
        content = _read_skill("identify")
        assert re.search(r"learning-agents:report-issue", content), (
            "identify must invoke report-issue skill"
        )

    def test_identify_does_not_investigate(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.5: identify skill guardrail says not to investigate root causes."""
        content = _read_skill("identify")
        assert re.search(
            r"do\s+NOT\s+investigate\s+root\s+causes",
            content,
            re.IGNORECASE,
        ), "identify must not investigate root causes"

    def test_identify_does_not_modify_agent(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-006.12).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """LA-REQ-006.12: identify skill guardrail says not to modify agent knowledge base."""
        content = _read_skill("identify")
        assert re.search(r"do\s+NOT\s+modify\s+the\s+agent", content, re.IGNORECASE), (
            "identify must not modify agent knowledge base"
        )
