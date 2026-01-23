"""Unit tests for techniques sync functionality."""

from pathlib import Path

import pytest

from deepwork.cli.sync import (
    TECHNIQUE_PREFIX,
    _convert_skill_md_to_toml,
    _copy_technique,
    sync_techniques_to_platform,
)
from deepwork.core.adapters import ClaudeAdapter, GeminiAdapter


class TestSyncTechniquesToPlatform:
    """Tests for sync_techniques_to_platform function."""

    def test_sync_single_technique_to_claude(self, temp_dir: Path) -> None:
        """Test syncing a single technique to Claude skills directory."""
        # Setup
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create a technique
        technique_dir = techniques_dir / "making_pdfs"
        technique_dir.mkdir()
        skill_content = """---
name: making_pdfs
description: "Convert documents to PDF format"
---

# Making PDFs

This technique uses pandoc to convert markdown to PDF.
"""
        (technique_dir / "SKILL.md").write_text(skill_content)

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify
        assert synced == 1
        assert removed == 0
        dest_dir = skills_dir / f"{TECHNIQUE_PREFIX}making_pdfs"
        assert dest_dir.exists()
        assert (dest_dir / "SKILL.md").exists()
        assert (dest_dir / "SKILL.md").read_text() == skill_content

    def test_sync_technique_with_assets(self, temp_dir: Path) -> None:
        """Test syncing a technique that includes asset files."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create a technique with assets
        technique_dir = techniques_dir / "chart_generation"
        technique_dir.mkdir()
        (technique_dir / "SKILL.md").write_text("---\nname: chart_generation\n---\n# Chart Gen")
        (technique_dir / "generate_chart.py").write_text("#!/usr/bin/env python\nprint('chart')")
        (technique_dir / "template.html").write_text("<html>template</html>")

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify all files are copied
        assert synced == 1
        dest_dir = skills_dir / f"{TECHNIQUE_PREFIX}chart_generation"
        assert (dest_dir / "SKILL.md").exists()
        assert (dest_dir / "generate_chart.py").exists()
        assert (dest_dir / "template.html").exists()

    def test_sync_multiple_techniques(self, temp_dir: Path) -> None:
        """Test syncing multiple techniques at once."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create multiple techniques
        for name in ["making_pdfs", "web_scraping", "image_processing"]:
            technique_dir = techniques_dir / name
            technique_dir.mkdir()
            (technique_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}")

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify
        assert synced == 3
        assert removed == 0
        for name in ["making_pdfs", "web_scraping", "image_processing"]:
            assert (skills_dir / f"{TECHNIQUE_PREFIX}{name}").exists()

    def test_removes_stale_techniques(self, temp_dir: Path) -> None:
        """Test that stale dw_ folders are removed."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create a technique
        technique_dir = techniques_dir / "making_pdfs"
        technique_dir.mkdir()
        (technique_dir / "SKILL.md").write_text("---\nname: making_pdfs\n---\n# PDF")

        # Create stale dw_ folders (no longer in techniques)
        stale_dir1 = skills_dir / f"{TECHNIQUE_PREFIX}old_technique"
        stale_dir1.mkdir()
        (stale_dir1 / "SKILL.md").write_text("stale")

        stale_dir2 = skills_dir / f"{TECHNIQUE_PREFIX}another_old"
        stale_dir2.mkdir()
        (stale_dir2 / "SKILL.md").write_text("also stale")

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify
        assert synced == 1
        assert removed == 2
        assert (skills_dir / f"{TECHNIQUE_PREFIX}making_pdfs").exists()
        assert not stale_dir1.exists()
        assert not stale_dir2.exists()

    def test_updates_existing_technique(self, temp_dir: Path) -> None:
        """Test that existing techniques are updated."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create existing dw_ folder with old content
        existing_dir = skills_dir / f"{TECHNIQUE_PREFIX}making_pdfs"
        existing_dir.mkdir()
        (existing_dir / "SKILL.md").write_text("old content")

        # Create updated technique
        technique_dir = techniques_dir / "making_pdfs"
        technique_dir.mkdir()
        new_content = "---\nname: making_pdfs\n---\n# Updated PDF technique"
        (technique_dir / "SKILL.md").write_text(new_content)

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify content was updated
        assert synced == 1
        assert removed == 0
        assert (skills_dir / f"{TECHNIQUE_PREFIX}making_pdfs" / "SKILL.md").read_text() == new_content

    def test_ignores_non_dw_folders(self, temp_dir: Path) -> None:
        """Test that non-dw_ prefixed folders are not touched."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create a technique
        technique_dir = techniques_dir / "making_pdfs"
        technique_dir.mkdir()
        (technique_dir / "SKILL.md").write_text("---\nname: making_pdfs\n---\n# PDF")

        # Create non-dw_ folder (should not be touched)
        other_dir = skills_dir / "my_custom_skill"
        other_dir.mkdir()
        (other_dir / "SKILL.md").write_text("custom skill")

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify other folder still exists
        assert synced == 1
        assert removed == 0
        assert other_dir.exists()
        assert (other_dir / "SKILL.md").read_text() == "custom skill"

    def test_skips_directories_without_skill_file(self, temp_dir: Path) -> None:
        """Test that directories without SKILL.md are not synced."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create valid technique
        valid_dir = techniques_dir / "valid_technique"
        valid_dir.mkdir()
        (valid_dir / "SKILL.md").write_text("---\nname: valid\n---\n# Valid")

        # Create invalid technique (no SKILL.md)
        invalid_dir = techniques_dir / "invalid_technique"
        invalid_dir.mkdir()
        (invalid_dir / "README.md").write_text("not a skill")

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify only valid technique was synced
        assert synced == 1
        assert (skills_dir / f"{TECHNIQUE_PREFIX}valid_technique").exists()
        assert not (skills_dir / f"{TECHNIQUE_PREFIX}invalid_technique").exists()

    def test_handles_empty_techniques_dir(self, temp_dir: Path) -> None:
        """Test handling when techniques directory is empty."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create a stale dw_ folder
        stale_dir = skills_dir / f"{TECHNIQUE_PREFIX}old"
        stale_dir.mkdir()
        (stale_dir / "SKILL.md").write_text("stale")

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify stale was removed
        assert synced == 0
        assert removed == 1
        assert not stale_dir.exists()

    def test_handles_nonexistent_techniques_dir(self, temp_dir: Path) -> None:
        """Test handling when techniques directory doesn't exist."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        # Create a stale dw_ folder
        stale_dir = skills_dir / f"{TECHNIQUE_PREFIX}old"
        stale_dir.mkdir()

        adapter = ClaudeAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify stale was removed even without techniques dir
        assert synced == 0
        assert removed == 1


class TestGeminiTechniqueSync:
    """Tests for Gemini-specific technique syncing."""

    def test_converts_skill_md_to_toml(self, temp_dir: Path) -> None:
        """Test that SKILL.md is converted to index.toml for Gemini."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".gemini" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create a technique with SKILL.md
        technique_dir = techniques_dir / "making_pdfs"
        technique_dir.mkdir()
        skill_content = """---
name: making_pdfs
description: "Convert documents to PDF format"
---

# Making PDFs

This technique uses pandoc.
"""
        (technique_dir / "SKILL.md").write_text(skill_content)

        adapter = GeminiAdapter(project_root=temp_dir)

        # Execute
        synced, removed = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify
        assert synced == 1
        dest_dir = skills_dir / f"{TECHNIQUE_PREFIX}making_pdfs"
        assert dest_dir.exists()
        # SKILL.md should be replaced with index.toml
        assert not (dest_dir / "SKILL.md").exists()
        assert (dest_dir / "index.toml").exists()

        # Verify TOML content
        toml_content = (dest_dir / "index.toml").read_text()
        assert 'name = "making_pdfs"' in toml_content
        assert 'description = "Convert documents to PDF format"' in toml_content
        assert "# Making PDFs" in toml_content

    def test_preserves_assets_for_gemini(self, temp_dir: Path) -> None:
        """Test that asset files are preserved for Gemini."""
        techniques_dir = temp_dir / ".deepwork" / "techniques"
        skills_dir = temp_dir / ".gemini" / "skills"
        techniques_dir.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        # Create a technique with assets
        technique_dir = techniques_dir / "chart_generation"
        technique_dir.mkdir()
        (technique_dir / "SKILL.md").write_text("---\nname: charts\n---\n# Charts")
        (technique_dir / "helper.py").write_text("print('helper')")

        adapter = GeminiAdapter(project_root=temp_dir)

        # Execute
        synced, _ = sync_techniques_to_platform(techniques_dir, skills_dir, adapter)

        # Verify assets are preserved
        dest_dir = skills_dir / f"{TECHNIQUE_PREFIX}chart_generation"
        assert (dest_dir / "index.toml").exists()
        assert (dest_dir / "helper.py").exists()


class TestConvertSkillMdToToml:
    """Tests for _convert_skill_md_to_toml function."""

    def test_converts_complete_frontmatter(self, temp_dir: Path) -> None:
        """Test conversion with complete frontmatter."""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: my_technique
description: "A useful technique"
---

# My Technique

Content here.
""")
        toml_path = temp_dir / "index.toml"

        _convert_skill_md_to_toml(skill_md, toml_path)

        content = toml_path.read_text()
        assert 'name = "my_technique"' in content
        assert 'description = "A useful technique"' in content
        assert "# My Technique" in content
        assert "Content here." in content

    def test_handles_missing_frontmatter(self, temp_dir: Path) -> None:
        """Test conversion when frontmatter is missing."""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("# No Frontmatter\n\nJust content.")
        toml_path = temp_dir / "index.toml"

        _convert_skill_md_to_toml(skill_md, toml_path)

        content = toml_path.read_text()
        assert 'name = ""' in content
        assert "# No Frontmatter" in content

    def test_handles_quoted_values(self, temp_dir: Path) -> None:
        """Test conversion with quoted YAML values."""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: 'single_quoted'
description: "double_quoted"
---

Body
""")
        toml_path = temp_dir / "index.toml"

        _convert_skill_md_to_toml(skill_md, toml_path)

        content = toml_path.read_text()
        assert 'name = "single_quoted"' in content
        assert 'description = "double_quoted"' in content


class TestCopyTechnique:
    """Tests for _copy_technique function."""

    def test_copies_all_files(self, temp_dir: Path) -> None:
        """Test that all files are copied."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()

        (source_dir / "SKILL.md").write_text("skill")
        (source_dir / "helper.py").write_text("helper")
        subdir = source_dir / "templates"
        subdir.mkdir()
        (subdir / "template.html").write_text("template")

        adapter = ClaudeAdapter(project_root=temp_dir)
        _copy_technique(source_dir, dest_dir, adapter)

        assert (dest_dir / "SKILL.md").exists()
        assert (dest_dir / "helper.py").exists()
        assert (dest_dir / "templates" / "template.html").exists()

    def test_replaces_existing_destination(self, temp_dir: Path) -> None:
        """Test that existing destination is replaced."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Existing content that should be replaced
        (dest_dir / "old_file.txt").write_text("old")

        # New content
        (source_dir / "SKILL.md").write_text("new skill")

        adapter = ClaudeAdapter(project_root=temp_dir)
        _copy_technique(source_dir, dest_dir, adapter)

        assert not (dest_dir / "old_file.txt").exists()
        assert (dest_dir / "SKILL.md").exists()
