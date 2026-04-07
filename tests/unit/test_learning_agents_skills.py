"""Tests for skill routing and CLI interface.

Validates requirements: LA-REQ-011, LA-REQ-011.1, LA-REQ-011.2, LA-REQ-011.3,
LA-REQ-011.4, LA-REQ-011.5, LA-REQ-011.6, LA-REQ-011.7, LA-REQ-011.8, LA-REQ-011.9,
LA-REQ-011.10, LA-REQ-011.11, LA-REQ-011.12, LA-REQ-011.13.

Each test class maps to a numbered requirement section in
specs/learning-agents/LA-REQ-011-skill-routing.md.

Only deterministic, boolean-verifiable requirements have tests here.
These tests inspect the SKILL.md files directly for correct routing
patterns, sub-command names, and structural properties.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

# Project root — navigate up from this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "learning_agents" / "skills"
DISPATCH_SKILL = SKILLS_DIR / "learning-agents" / "SKILL.md"


def _read_skill(name: str) -> str:
    """Read the SKILL.md content for a given skill directory name."""
    path = SKILLS_DIR / name / "SKILL.md"
    assert path.exists(), f"Skill {name} SKILL.md not found at {path}"
    return path.read_text()


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "No YAML frontmatter found"
    return yaml.safe_load(match.group(1))


# ---------------------------------------------------------------------------
# LA-REQ-011.1: Entry Point Skill
# ---------------------------------------------------------------------------


class TestEntryPointSkill:
    """The plugin provides a top-level dispatch skill (LA-REQ-011.1)."""

    def test_dispatch_skill_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.1).
        """LA-REQ-011.1: learning-agents skill directory and SKILL.md exist."""
        assert DISPATCH_SKILL.exists()

    def test_dispatch_skill_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.1).
        """LA-REQ-011.1: frontmatter name is 'learning-agents'."""
        fm = _parse_frontmatter(_read_skill("learning-agents"))
        assert fm["name"] == "learning-agents"

    def test_dispatch_skill_is_user_invocable(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.1).
        """LA-REQ-011.1: skill is user-invocable (no user-invocable: false)."""
        fm = _parse_frontmatter(_read_skill("learning-agents"))
        # If user-invocable is absent, it defaults to true.
        assert fm.get("user-invocable", True) is not False


# ---------------------------------------------------------------------------
# LA-REQ-011.2: Argument Parsing
# ---------------------------------------------------------------------------


class TestArgumentParsing:
    """The skill splits $ARGUMENTS on first whitespace (LA-REQ-011.2)."""

    def test_arguments_splitting_documented(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.2).
        """LA-REQ-011.2: SKILL.md describes splitting $ARGUMENTS on first whitespace."""
        content = _read_skill("learning-agents")
        assert "$ARGUMENTS" in content
        assert re.search(
            r"split.*\$ARGUMENTS.*first\s+whitespace", content, re.IGNORECASE
        ), "Must describe splitting $ARGUMENTS on first whitespace"

    def test_first_token_is_subcommand(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.2).
        """LA-REQ-011.2: first token is the sub-command (case-insensitive)."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"first token.*sub-command.*case-insensitive", content, re.IGNORECASE
        ), "Must identify first token as case-insensitive sub-command"


# ---------------------------------------------------------------------------
# LA-REQ-011.3: Underscore-Dash Equivalence
# ---------------------------------------------------------------------------


class TestUnderscoreDashEquivalence:
    """Underscores and dashes are treated as equivalent (LA-REQ-011.3)."""

    def test_equivalence_documented(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.3).
        """LA-REQ-011.3: SKILL.md states underscore-dash equivalence."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"underscores?\s+and\s+dashes?", content, re.IGNORECASE
        ), "Must document underscore-dash equivalence"

    def test_report_issue_example_uses_underscore(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.3).
        """LA-REQ-011.3: report_issue (underscore form) appears as a sub-command."""
        content = _read_skill("learning-agents")
        assert "report_issue" in content


# ---------------------------------------------------------------------------
# LA-REQ-011.4: Create Sub-Command
# ---------------------------------------------------------------------------


class TestCreateSubCommand:
    """The create sub-command routes to create-agent (LA-REQ-011.4)."""

    def test_create_routes_to_create_agent_skill(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.4).
        """LA-REQ-011.4: create routes to Skill learning-agents:create-agent."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"Skill\s+learning-agents:create-agent", content
        ), "Must invoke Skill learning-agents:create-agent"

    def test_create_accepts_name_argument(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.4).
        """LA-REQ-011.4: create sub-command takes a <name> argument."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"###\s+`create\s+<name>", content
        ), "Must show create <name> heading"

    def test_create_accepts_optional_template_path(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.4).
        """LA-REQ-011.4: create sub-command accepts optional [template-path]."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"create\s+<name>\s+\[template-path\]", content
        ), "Must show optional [template-path] argument"

    def test_create_example_with_template(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.4).
        """LA-REQ-011.4: example shows template-path being passed through."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"create-agent\s+\S+\s+\.deepwork/learning-agents/", content
        ), "Must show example passing template path to create-agent skill"


# ---------------------------------------------------------------------------
# LA-REQ-011.5: Learn Sub-Command
# ---------------------------------------------------------------------------


class TestLearnSubCommand:
    """The learn sub-command routes to learn skill (LA-REQ-011.5)."""

    def test_learn_routes_to_learn_skill(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.5).
        """LA-REQ-011.5: learn routes to Skill learning-agents:learn."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"Skill\s+learning-agents:learn\b", content
        ), "Must invoke Skill learning-agents:learn"

    def test_learn_ignores_extra_arguments(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.5).
        """LA-REQ-011.5: arguments after learn are ignored."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"arguments?\s+after\s+`?learn`?\s+(are\s+)?ignored",
            content,
            re.IGNORECASE,
        ), "Must state that arguments after learn are ignored"


# ---------------------------------------------------------------------------
# LA-REQ-011.6: Report Issue Sub-Command
# ---------------------------------------------------------------------------


class TestReportIssueSubCommand:
    """The report_issue sub-command routes to report-issue (LA-REQ-011.6)."""

    def test_report_issue_routes_to_report_issue_skill(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.6).
        """LA-REQ-011.6: report_issue routes to Skill learning-agents:report-issue."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"Skill\s+learning-agents:report-issue", content
        ), "Must invoke Skill learning-agents:report-issue"

    def test_report_issue_searches_agent_sessions(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.6).
        """LA-REQ-011.6: searches .deepwork/tmp/agent_sessions/ for agentId."""
        content = _read_skill("learning-agents")
        assert ".deepwork/tmp/agent_sessions/" in content

    def test_report_issue_handles_no_match(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.6).
        """LA-REQ-011.6: if no match found, inform the user."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"no\s+match.*inform", content, re.IGNORECASE
        ), "Must describe informing user when no match found"

    def test_report_issue_uses_most_recent_on_multiple(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.6).
        """LA-REQ-011.6: if multiple matches, use most recently modified."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"multiple\s+matches.*most\s+recently\s+modified",
            content,
            re.IGNORECASE,
        ), "Must describe using most recently modified on multiple matches"


# ---------------------------------------------------------------------------
# LA-REQ-011.7: Help Text
# ---------------------------------------------------------------------------


class TestHelpText:
    """Help text shown when no args or unknown sub-command (LA-REQ-011.7)."""

    def test_help_section_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.7).
        """LA-REQ-011.7: skill has a section for no arguments / ambiguous input."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"no\s+arguments\s+or\s+ambiguous", content, re.IGNORECASE
        ), "Must have a section for no arguments or ambiguous input"

    def test_help_lists_all_subcommands(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.7).
        """LA-REQ-011.7: help text lists create, learn, report_issue."""
        content = _read_skill("learning-agents")
        # Check the help block contains all three sub-commands
        assert "/learning-agents create" in content
        assert "/learning-agents learn" in content
        assert "/learning-agents report_issue" in content

    def test_help_includes_examples(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.7).
        """LA-REQ-011.7: help text includes usage examples."""
        content = _read_skill("learning-agents")
        # The help block has an Examples section
        assert re.search(r"^Examples:", content, re.MULTILINE)


# ---------------------------------------------------------------------------
# LA-REQ-011.8: No Inline Implementation
# ---------------------------------------------------------------------------


class TestNoInlineImplementation:
    """The dispatch skill always routes — never implements inline (LA-REQ-011.8)."""

    def test_guardrail_no_inline(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.8).
        """LA-REQ-011.8: guardrails state never implement sub-command logic inline."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"do\s+NOT\s+implement\s+sub-command\s+logic\s+inline",
            content,
            re.IGNORECASE,
        ), "Must have guardrail against inline implementation"

    def test_always_routes_to_skill(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.8).
        """LA-REQ-011.8: guardrails state always route to the appropriate skill."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"always\s+route\s+to\s+the\s+appropriate\s+skill",
            content,
            re.IGNORECASE,
        ), "Must have guardrail to always route to skill"


# ---------------------------------------------------------------------------
# LA-REQ-011.9: Argument Pass-Through
# ---------------------------------------------------------------------------


class TestArgumentPassThrough:
    """Arguments are passed through to sub-skills exactly (LA-REQ-011.9)."""

    def test_passthrough_documented(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.9).
        """LA-REQ-011.9: documents passing arguments through exactly as provided."""
        content = _read_skill("learning-agents")
        assert re.search(
            r"pass\s+arguments?\s+through.*exactly\s+as\s+provided",
            content,
            re.IGNORECASE,
        ), "Must document argument pass-through"


# ---------------------------------------------------------------------------
# LA-REQ-011.10: Available Sub-Commands
# ---------------------------------------------------------------------------


class TestAvailableSubCommands:
    """Exactly three sub-commands are supported (LA-REQ-011.10)."""

    def test_exactly_three_routing_sections(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.10).
        """LA-REQ-011.10: exactly three sub-command routing sections (### headings under Routing)."""
        content = _read_skill("learning-agents")
        # Find routing section headings (### `command ...`)
        # Exclude the "No arguments" section which is not a sub-command
        routing_headings = re.findall(
            r"^###\s+`(\w+)", content, re.MULTILINE
        )
        assert routing_headings == ["create", "learn", "report_issue"], (
            f"Expected exactly [create, learn, report_issue], got {routing_headings}"
        )

    def test_create_subcommand_present(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.10).
        """LA-REQ-011.10: create sub-command is defined."""
        content = _read_skill("learning-agents")
        assert re.search(r"^###\s+`create\b", content, re.MULTILINE)

    def test_learn_subcommand_present(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.10).
        """LA-REQ-011.10: learn sub-command is defined."""
        content = _read_skill("learning-agents")
        assert re.search(r"^###\s+`learn\b", content, re.MULTILINE)

    def test_report_issue_subcommand_present(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.10).
        """LA-REQ-011.10: report_issue sub-command is defined."""
        content = _read_skill("learning-agents")
        assert re.search(r"^###\s+`report_issue\b", content, re.MULTILINE)


# ---------------------------------------------------------------------------
# LA-REQ-011.11: Sub-Skill Registry
# ---------------------------------------------------------------------------


REQUIRED_SKILLS = [
    "learning-agents",
    "create-agent",
    "learn",
    "identify",
    "investigate-issues",
    "incorporate-learnings",
    "report-issue",
    "prompt-review",
]


class TestSubSkillRegistry:
    """All required skills exist as directories with SKILL.md (LA-REQ-011.11)."""

    def test_all_required_skill_directories_exist(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.11).
        """LA-REQ-011.11: every required skill has a directory under skills/."""
        for skill_name in REQUIRED_SKILLS:
            skill_dir = SKILLS_DIR / skill_name
            assert skill_dir.is_dir(), (
                f"Required skill directory missing: {skill_name}"
            )

    def test_all_required_skills_have_skill_md(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.11).
        """LA-REQ-011.11: every required skill has a SKILL.md file."""
        for skill_name in REQUIRED_SKILLS:
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            assert skill_file.exists(), (
                f"Required SKILL.md missing: {skill_name}/SKILL.md"
            )

    def test_all_required_skills_have_valid_frontmatter(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.11).
        """LA-REQ-011.11: every required skill has YAML frontmatter with a name field."""
        for skill_name in REQUIRED_SKILLS:
            content = _read_skill(skill_name)
            fm = _parse_frontmatter(content)
            assert fm.get("name") == skill_name, (
                f"Skill {skill_name} frontmatter name mismatch: {fm.get('name')}"
            )

    def test_non_user_invocable_skills_marked(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.11).
        """LA-REQ-011.11: identify, investigate-issues, incorporate-learnings are non-user-invocable."""
        non_user_invocable = [
            "identify",
            "investigate-issues",
            "incorporate-learnings",
        ]
        for skill_name in non_user_invocable:
            fm = _parse_frontmatter(_read_skill(skill_name))
            assert fm.get("user-invocable") is False, (
                f"Skill {skill_name} must have user-invocable: false"
            )


# ---------------------------------------------------------------------------
# LA-REQ-011.12: Prompt Review Skill Independence
# ---------------------------------------------------------------------------


class TestPromptReviewIndependence:
    """prompt-review is independently invocable (LA-REQ-011.12)."""

    def test_prompt_review_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.12).
        """LA-REQ-011.12: prompt-review skill directory and SKILL.md exist."""
        assert (SKILLS_DIR / "prompt-review" / "SKILL.md").exists()

    def test_prompt_review_is_user_invocable(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.12).
        """LA-REQ-011.12: prompt-review is user-invocable (not marked false)."""
        fm = _parse_frontmatter(_read_skill("prompt-review"))
        assert fm.get("user-invocable", True) is not False

    def test_prompt_review_not_routed_through_dispatch(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.12).
        """LA-REQ-011.12: prompt-review is NOT listed as a routed sub-command in the dispatch skill."""
        content = _read_skill("learning-agents")
        # The dispatch skill routes to create-agent, learn, report-issue only.
        # prompt-review must NOT appear as a routing target.
        routing_targets = re.findall(
            r"Skill\s+learning-agents:(\S+)", content
        )
        assert "prompt-review" not in routing_targets, (
            "prompt-review must not be routed through the dispatch skill"
        )


# ---------------------------------------------------------------------------
# LA-REQ-011.13: Existing Agents Listing
# ---------------------------------------------------------------------------


class TestExistingAgentsListing:
    """Dispatch skill lists existing agents dynamically (LA-REQ-011.13)."""

    def test_lists_learning_agents_directory(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.13).
        """LA-REQ-011.13: skill references .deepwork/learning-agents/ for listing."""
        content = _read_skill("learning-agents")
        assert ".deepwork/learning-agents/" in content

    def test_dynamic_listing_command(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.13).
        """LA-REQ-011.13: uses a dynamic shell command (!) to list agents."""
        content = _read_skill("learning-agents")
        # The skill uses !`ls ...` syntax for dynamic execution
        assert re.search(
            r"!`ls\s+.*\.deepwork/learning-agents/", content
        ), "Must use dynamic shell command to list agents"

    def test_fallback_when_no_agents(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (LA-REQ-011.13).
        """LA-REQ-011.13: shows fallback (none) when no agents exist."""
        content = _read_skill("learning-agents")
        assert "(none)" in content, (
            "Must include (none) fallback for empty agent listing"
        )
