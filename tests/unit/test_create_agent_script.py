"""Tests for create_agent.sh -- validates learning-agents REQ-002.

These tests validate the scaffold script behavior for agent creation,
including template-based agent seeding (REQ-002.16 through REQ-002.22).
"""

import subprocess
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "learning_agents"
    / "scripts"
    / "create_agent.sh"
)


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    """Create a working directory simulating a project root."""
    (tmp_path / ".deepwork" / "learning-agents").mkdir(parents=True)
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def template_agent(tmp_path: Path) -> Path:
    """Create a template agent with core-knowledge, topics, and learnings."""
    template = tmp_path / "template-agent"
    template.mkdir()
    (template / "core-knowledge.md").write_text(
        "You are an expert on template domain.\n"
    )

    topics = template / "topics"
    topics.mkdir()
    (topics / ".gitkeep").touch()
    (topics / "topic-one.md").write_text("---\nname: Topic One\n---\nContent.\n")
    (topics / "topic-two.md").write_text("---\nname: Topic Two\n---\nContent.\n")

    learnings = template / "learnings"
    learnings.mkdir()
    (learnings / ".gitkeep").touch()
    (learnings / "learning-one.md").write_text(
        "---\nname: Learning One\n---\nContent.\n"
    )

    return template


def run_script(
    work_dir: Path, agent_name: str, template_path: str | None = None
) -> subprocess.CompletedProcess[str]:
    cmd = [str(SCRIPT_PATH), agent_name]
    if template_path is not None:
        cmd.append(template_path)
    return subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, timeout=30)


class TestBaselineCreation:
    """Non-template agent creation (REQ-002.6, REQ-002.8, REQ-002.10, REQ-002.11)."""

    # REQ-002.11
    def test_no_args_exits_with_error(self, work_dir: Path) -> None:
        result = subprocess.run(
            [str(SCRIPT_PATH)], cwd=work_dir, capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "Usage:" in result.stderr

    # REQ-002.6
    def test_creates_directory_structure(self, work_dir: Path) -> None:
        result = run_script(work_dir, "test-agent")
        assert result.returncode == 0

        agent_dir = work_dir / ".deepwork" / "learning-agents" / "test-agent"
        assert (agent_dir / "core-knowledge.md").is_file()
        assert (agent_dir / "topics" / ".gitkeep").is_file()
        assert (agent_dir / "learnings" / ".gitkeep").is_file()
        assert (agent_dir / "additional_learning_guidelines" / "README.md").is_file()

    # REQ-002.6
    def test_creates_todo_placeholder_without_template(self, work_dir: Path) -> None:
        run_script(work_dir, "test-agent")
        content = (
            work_dir / ".deepwork" / "learning-agents" / "test-agent" / "core-knowledge.md"
        ).read_text()
        assert "TODO" in content

    # REQ-002.8
    def test_creates_claude_agent_file(self, work_dir: Path) -> None:
        result = run_script(work_dir, "test-agent")
        assert result.returncode == 0

        agent_file = work_dir / ".claude" / "agents" / "test-agent.md"
        assert agent_file.is_file()
        content = agent_file.read_text()
        assert "name: TODO" in content

    # REQ-002.10
    def test_idempotent_does_not_overwrite(self, work_dir: Path) -> None:
        run_script(work_dir, "test-agent")
        ck = work_dir / ".deepwork" / "learning-agents" / "test-agent" / "core-knowledge.md"
        ck.write_text("Custom content\n")

        result = run_script(work_dir, "test-agent")
        assert result.returncode == 0
        assert "already exists" in result.stderr
        assert ck.read_text() == "Custom content\n"


class TestTemplateCreation:
    """Template-based agent creation (REQ-002.16 through REQ-002.22)."""

    # REQ-002.16
    def test_accepts_optional_template_argument(
        self, work_dir: Path, template_agent: Path
    ) -> None:
        result = run_script(work_dir, "new-agent", str(template_agent))
        assert result.returncode == 0

    # REQ-002.16
    def test_without_template_creates_todo(self, work_dir: Path) -> None:
        run_script(work_dir, "new-agent")
        content = (
            work_dir / ".deepwork" / "learning-agents" / "new-agent" / "core-knowledge.md"
        ).read_text()
        assert "TODO" in content

    # REQ-002.17
    def test_nonexistent_template_directory_exits_1(self, work_dir: Path) -> None:
        result = run_script(work_dir, "new-agent", "/nonexistent/path")
        assert result.returncode == 1
        assert "/nonexistent/path" in result.stderr

    # REQ-002.18
    def test_template_missing_core_knowledge_exits_1(
        self, work_dir: Path, tmp_path: Path
    ) -> None:
        empty_template = tmp_path / "empty-template"
        empty_template.mkdir()

        result = run_script(work_dir, "new-agent", str(empty_template))
        assert result.returncode == 1
        assert "core-knowledge.md" in result.stderr

    # REQ-002.19
    def test_copies_core_knowledge_from_template(
        self, work_dir: Path, template_agent: Path
    ) -> None:
        run_script(work_dir, "new-agent", str(template_agent))
        content = (
            work_dir / ".deepwork" / "learning-agents" / "new-agent" / "core-knowledge.md"
        ).read_text()
        assert "TODO" not in content
        assert "template domain" in content

    # REQ-002.20
    def test_copies_topics_from_template(
        self, work_dir: Path, template_agent: Path
    ) -> None:
        run_script(work_dir, "new-agent", str(template_agent))
        topics_dir = work_dir / ".deepwork" / "learning-agents" / "new-agent" / "topics"
        topic_files = sorted(f.name for f in topics_dir.glob("*.md"))
        assert topic_files == ["topic-one.md", "topic-two.md"]

    # REQ-002.20
    def test_no_template_topics_leaves_empty(
        self, work_dir: Path, tmp_path: Path
    ) -> None:
        template = tmp_path / "no-topics"
        template.mkdir()
        (template / "core-knowledge.md").write_text("Content.\n")
        (template / "topics").mkdir()
        (template / "topics" / ".gitkeep").touch()
        (template / "learnings").mkdir()

        run_script(work_dir, "new-agent", str(template))
        md_files = list(
            (work_dir / ".deepwork" / "learning-agents" / "new-agent" / "topics").glob("*.md")
        )
        assert len(md_files) == 0

    # REQ-002.21
    def test_copies_learnings_from_template(
        self, work_dir: Path, template_agent: Path
    ) -> None:
        run_script(work_dir, "new-agent", str(template_agent))
        learnings_dir = (
            work_dir / ".deepwork" / "learning-agents" / "new-agent" / "learnings"
        )
        learning_files = [f.name for f in learnings_dir.glob("*.md")]
        assert "learning-one.md" in learning_files

    # REQ-002.21
    def test_no_template_learnings_leaves_empty(
        self, work_dir: Path, tmp_path: Path
    ) -> None:
        template = tmp_path / "no-learnings"
        template.mkdir()
        (template / "core-knowledge.md").write_text("Content.\n")
        (template / "topics").mkdir()
        (template / "learnings").mkdir()
        (template / "learnings" / ".gitkeep").touch()

        run_script(work_dir, "new-agent", str(template))
        md_files = list(
            (work_dir / ".deepwork" / "learning-agents" / "new-agent" / "learnings").glob(
                "*.md"
            )
        )
        assert len(md_files) == 0

    # REQ-002.22
    def test_reports_copy_counts(
        self, work_dir: Path, template_agent: Path
    ) -> None:
        result = run_script(work_dir, "new-agent", str(template_agent))
        assert "Copied core-knowledge.md from template" in result.stdout
        assert "2 topic(s)" in result.stdout
        assert "1 learning(s)" in result.stdout

    # REQ-002.22
    def test_no_copies_no_count_messages(
        self, work_dir: Path, tmp_path: Path
    ) -> None:
        template = tmp_path / "minimal"
        template.mkdir()
        (template / "core-knowledge.md").write_text("Content.\n")
        (template / "topics").mkdir()
        (template / "learnings").mkdir()

        result = run_script(work_dir, "new-agent", str(template))
        assert "Copied core-knowledge.md from template" in result.stdout
        assert "topic(s)" not in result.stdout
        assert "learning(s)" not in result.stdout
