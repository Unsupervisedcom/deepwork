"""Tests for DeepWork Reviews plugin skills and documentation — validates REQ-007."""

from pathlib import Path
from typing import Any

import yaml

# Project root — navigate up from this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "claude"
SKILLS_DIR = PLUGIN_DIR / "skills"


def _parse_frontmatter(skill_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file."""
    text = skill_path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{skill_path} must start with YAML frontmatter"
    end = text.index("---", 3)
    result: dict[str, Any] = yaml.safe_load(text[3:end])
    return result


class TestReviewSkill:
    """Tests for the review skill (REQ-007.1)."""

    skill_path = SKILLS_DIR / "review" / "SKILL.md"

    def test_skill_file_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.1: review skill exists at expected path."""
        assert self.skill_path.exists()

    def test_frontmatter_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.2: name field is 'review'."""
        fm = _parse_frontmatter(self.skill_path)
        assert fm["name"] == "review"

    def test_frontmatter_description(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.3: description field is present."""
        fm = _parse_frontmatter(self.skill_path)
        assert "description" in fm
        assert len(fm["description"]) > 0

    def test_instructs_to_call_review_mcp_tool(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.4: skill tells agent to call the review MCP tool."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "mcp__deepwork__get_review_instructions" in content

    def test_instructs_parallel_tasks(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.5: skill tells agent to launch tasks in parallel."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "parallel" in content.lower()

    def test_instructs_auto_apply_obvious_fixes(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.6: skill tells agent to auto-apply no-downside changes."""
        content = self.skill_path.read_text(encoding="utf-8")
        # Must mention making changes without asking for obvious fixes
        assert "without asking" in content.lower() or "immediately" in content.lower()

    def test_instructs_ask_user_for_tradeoffs(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.7).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.7: skill tells agent to use AskUserQuestion for trade-offs."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "AskUserQuestion" in content

    def test_instructs_iterate(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.8: skill tells agent to re-run after changes."""
        content = self.skill_path.read_text(encoding="utf-8")
        # Must mention running again / repeating
        assert "again" in content.lower() or "repeat" in content.lower()

    def test_routes_config_to_configure_reviews(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.1.9).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.1.9: skill routes configuration requests to configure_reviews."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "configure_reviews" in content


class TestConfigureReviewsSkill:
    """Tests for the configure_reviews skill (REQ-007.2)."""

    skill_path = SKILLS_DIR / "configure_reviews" / "SKILL.md"

    def test_skill_file_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.2.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.2.1: configure_reviews skill exists at expected path."""
        assert self.skill_path.exists()

    def test_frontmatter_name(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.2.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.2.2: name field is 'configure_reviews'."""
        fm = _parse_frontmatter(self.skill_path)
        assert fm["name"] == "configure_reviews"

    def test_frontmatter_description(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.2.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.2.3: description field is present."""
        fm = _parse_frontmatter(self.skill_path)
        assert "description" in fm
        assert len(fm["description"]) > 0

    def test_instructs_to_read_readme(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.2.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.2.4: skill tells agent to read README_REVIEWS.md."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "README_REVIEWS.md" in content

    def test_instructs_to_reuse_existing(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.2.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.2.5: skill tells agent to look at existing .deepreview files."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert ".deepreview" in content
        assert "reuse" in content.lower() or "existing" in content.lower()

    def test_instructs_to_test_changes(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.2.6).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.2.6: skill tells agent to test by calling the review MCP tool."""
        content = self.skill_path.read_text(encoding="utf-8")
        assert "mcp__deepwork__get_review_instructions" in content


class TestReferenceDocumentation:
    """Tests for README_REVIEWS.md in the plugin (REQ-007.3)."""

    symlink_path = PLUGIN_DIR / "README_REVIEWS.md"
    root_readme = PROJECT_ROOT / "README_REVIEWS.md"

    def test_symlink_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.1: README_REVIEWS.md exists in plugin directory."""
        assert self.symlink_path.exists()

    def test_is_symlink(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.2: plugin copy is a symlink."""
        assert self.symlink_path.is_symlink()

    def test_symlink_target(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.2: symlink points to ../../README_REVIEWS.md."""
        target = self.symlink_path.readlink()
        assert str(target) == "../../README_REVIEWS.md"

    def test_symlink_resolves(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.3: symlink target exists and is readable."""
        assert self.symlink_path.resolve().exists()
        content = self.symlink_path.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_root_readme_exists(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.3: root README_REVIEWS.md exists."""
        assert self.root_readme.exists()

    def test_documents_deepreview_format(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.4: documents .deepreview config format."""
        content = self.root_readme.read_text(encoding="utf-8")
        assert ".deepreview" in content
        assert "strategy" in content
        assert "individual" in content
        assert "matches_together" in content
        assert "all_changed_files" in content

    def test_documents_instruction_variants(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.4: documents both inline and file reference instructions."""
        content = self.root_readme.read_text(encoding="utf-8")
        assert "instructions:" in content
        assert "file:" in content

    def test_documents_agent_personas(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.4: documents agent personas."""
        content = self.root_readme.read_text(encoding="utf-8")
        assert "agent:" in content
        assert "claude:" in content

    def test_recommends_deepwork_review_dir(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.3.5).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.3.5: recommends .deepwork/review/ for instruction files."""
        content = self.root_readme.read_text(encoding="utf-8")
        assert ".deepwork/review/" in content


class TestSkillDirectoryConventions:
    """Tests for skill directory structure (REQ-007.4)."""

    def test_each_skill_has_own_directory(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.4.1).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.4.1: each skill is in its own directory."""
        skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 3  # deepwork, review, configure_reviews

    def test_each_skill_has_skill_md(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.4.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.4.2: each skill directory contains SKILL.md."""
        skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            assert (skill_dir / "SKILL.md").exists(), f"{skill_dir.name} is missing SKILL.md"

    def test_name_matches_directory(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (REQ-007.4.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """REQ-007.4.3: frontmatter name matches directory name."""
        skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                fm = _parse_frontmatter(skill_file)
                assert fm["name"] == skill_dir.name, (
                    f"Skill {skill_dir.name} has name={fm['name']} in frontmatter"
                )
