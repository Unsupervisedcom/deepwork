"""Tests for expert definition parser."""

from datetime import date
from pathlib import Path

import pytest

from deepwork.core.experts_parser import (
    ExpertDefinition,
    ExpertParseError,
    Learning,
    Topic,
    _folder_name_to_expert_name,
    discover_experts,
    format_learnings_markdown,
    format_topics_markdown,
    parse_expert_definition,
    parse_learning_file,
    parse_topic_file,
)


class TestFolderNameConversion:
    """Tests for folder name to expert name conversion."""

    def test_underscores_to_dashes(self) -> None:
        """Test that underscores are converted to dashes."""
        assert _folder_name_to_expert_name("rails_activejob") == "rails-activejob"

    def test_spaces_to_dashes(self) -> None:
        """Test that spaces are converted to dashes."""
        assert _folder_name_to_expert_name("rails activejob") == "rails-activejob"

    def test_mixed_conversion(self) -> None:
        """Test mixed underscores and spaces."""
        assert _folder_name_to_expert_name("rails_active job") == "rails-active-job"

    def test_no_conversion_needed(self) -> None:
        """Test name that doesn't need conversion."""
        assert _folder_name_to_expert_name("experts") == "experts"

    def test_already_dashes(self) -> None:
        """Test name that already has dashes."""
        assert _folder_name_to_expert_name("rails-activejob") == "rails-activejob"


class TestTopic:
    """Tests for Topic dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating topic from minimal dict."""
        data = {"name": "Test Topic"}
        topic = Topic.from_dict(data)

        assert topic.name == "Test Topic"
        assert topic.keywords == []
        assert topic.last_updated is None
        assert topic.body == ""

    def test_from_dict_full(self) -> None:
        """Test creating topic from full dict."""
        data = {
            "name": "Retry Handling",
            "keywords": ["retry", "backoff"],
            "last_updated": "2025-01-30",
        }
        topic = Topic.from_dict(data, body="Content here", source_file=Path("topics/retry.md"))

        assert topic.name == "Retry Handling"
        assert topic.keywords == ["retry", "backoff"]
        assert topic.last_updated == date(2025, 1, 30)
        assert topic.body == "Content here"
        assert topic.source_file == Path("topics/retry.md")

    def test_relative_path(self) -> None:
        """Test relative path generation."""
        topic = Topic(name="Test", source_file=Path("/some/path/topics/test.md"))
        assert topic.relative_path == "topics/test.md"

    def test_relative_path_no_source(self) -> None:
        """Test relative path when no source file."""
        topic = Topic(name="Test")
        assert topic.relative_path is None


class TestLearning:
    """Tests for Learning dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating learning from minimal dict."""
        data = {"name": "Test Learning"}
        learning = Learning.from_dict(data)

        assert learning.name == "Test Learning"
        assert learning.last_updated is None
        assert learning.summarized_result is None
        assert learning.body == ""

    def test_from_dict_full(self) -> None:
        """Test creating learning from full dict."""
        data = {
            "name": "Job errors not going to Sentry",
            "last_updated": "2025-01-20",
            "summarized_result": "Sentry changed their gem.",
        }
        learning = Learning.from_dict(
            data, body="Full content", source_file=Path("learnings/sentry.md")
        )

        assert learning.name == "Job errors not going to Sentry"
        assert learning.last_updated == date(2025, 1, 20)
        assert learning.summarized_result == "Sentry changed their gem."
        assert learning.body == "Full content"
        assert learning.source_file == Path("learnings/sentry.md")

    def test_relative_path(self) -> None:
        """Test relative path generation."""
        learning = Learning(name="Test", source_file=Path("/some/path/learnings/test.md"))
        assert learning.relative_path == "learnings/test.md"


class TestExpertDefinition:
    """Tests for ExpertDefinition dataclass."""

    def test_from_dict(self) -> None:
        """Test creating expert definition from dict."""
        data = {
            "discovery_description": "Test expert",
            "full_expertise": "You are an expert.",
        }
        expert = ExpertDefinition.from_dict(data, Path("/path/to/rails_activejob"))

        assert expert.name == "rails-activejob"
        assert expert.discovery_description == "Test expert"
        assert expert.full_expertise == "You are an expert."
        assert expert.expert_dir == Path("/path/to/rails_activejob")
        assert expert.topics == []
        assert expert.learnings == []

    def test_from_dict_with_topics_and_learnings(self) -> None:
        """Test creating expert with topics and learnings."""
        data = {
            "discovery_description": "Test expert",
            "full_expertise": "You are an expert.",
        }
        topics = [Topic(name="Topic 1"), Topic(name="Topic 2")]
        learnings = [Learning(name="Learning 1")]

        expert = ExpertDefinition.from_dict(
            data, Path("/path/to/test_expert"), topics=topics, learnings=learnings
        )

        assert len(expert.topics) == 2
        assert len(expert.learnings) == 1

    def test_get_topics_sorted(self) -> None:
        """Test topics are sorted by most recently updated."""
        topics = [
            Topic(name="Old", last_updated=date(2025, 1, 1)),
            Topic(name="New", last_updated=date(2025, 1, 30)),
            Topic(name="No Date"),
        ]
        expert = ExpertDefinition(
            name="test",
            discovery_description="Test",
            full_expertise="Test",
            expert_dir=Path("/test"),
            topics=topics,
        )

        sorted_topics = expert.get_topics_sorted()
        assert sorted_topics[0].name == "New"
        assert sorted_topics[1].name == "Old"
        assert sorted_topics[2].name == "No Date"

    def test_get_learnings_sorted(self) -> None:
        """Test learnings are sorted by most recently updated."""
        learnings = [
            Learning(name="Old", last_updated=date(2025, 1, 1)),
            Learning(name="New", last_updated=date(2025, 1, 30)),
            Learning(name="No Date"),
        ]
        expert = ExpertDefinition(
            name="test",
            discovery_description="Test",
            full_expertise="Test",
            expert_dir=Path("/test"),
            learnings=learnings,
        )

        sorted_learnings = expert.get_learnings_sorted()
        assert sorted_learnings[0].name == "New"
        assert sorted_learnings[1].name == "Old"
        assert sorted_learnings[2].name == "No Date"


class TestParseTopicFile:
    """Tests for parsing topic files."""

    def test_parse_valid_topic(self, tmp_path: Path) -> None:
        """Test parsing a valid topic file."""
        topic_file = tmp_path / "test_topic.md"
        topic_file.write_text(
            """---
name: Test Topic
keywords:
  - testing
  - unit test
last_updated: 2025-01-30
---

This is the topic content.
"""
        )

        topic = parse_topic_file(topic_file)

        assert topic.name == "Test Topic"
        assert topic.keywords == ["testing", "unit test"]
        assert topic.last_updated == date(2025, 1, 30)
        assert "topic content" in topic.body
        assert topic.source_file == topic_file

    def test_parse_minimal_topic(self, tmp_path: Path) -> None:
        """Test parsing a minimal topic file."""
        topic_file = tmp_path / "minimal.md"
        topic_file.write_text(
            """---
name: Minimal Topic
---

Content here.
"""
        )

        topic = parse_topic_file(topic_file)

        assert topic.name == "Minimal Topic"
        assert topic.keywords == []
        assert topic.last_updated is None

    def test_parse_topic_missing_frontmatter(self, tmp_path: Path) -> None:
        """Test parsing topic without frontmatter fails."""
        topic_file = tmp_path / "no_frontmatter.md"
        topic_file.write_text("Just content without frontmatter")

        with pytest.raises(ExpertParseError, match="frontmatter"):
            parse_topic_file(topic_file)

    def test_parse_topic_missing_name(self, tmp_path: Path) -> None:
        """Test parsing topic without name fails."""
        topic_file = tmp_path / "no_name.md"
        topic_file.write_text(
            """---
keywords:
  - test
---

Content
"""
        )

        with pytest.raises(ExpertParseError, match="name"):
            parse_topic_file(topic_file)

    def test_parse_topic_nonexistent(self, tmp_path: Path) -> None:
        """Test parsing nonexistent topic file fails."""
        with pytest.raises(ExpertParseError, match="does not exist"):
            parse_topic_file(tmp_path / "nonexistent.md")


class TestParseLearningFile:
    """Tests for parsing learning files."""

    def test_parse_valid_learning(self, tmp_path: Path) -> None:
        """Test parsing a valid learning file."""
        learning_file = tmp_path / "test_learning.md"
        learning_file.write_text(
            """---
name: Test Learning
last_updated: 2025-01-30
summarized_result: |
  Discovered that X causes Y.
---

## Context
Full learning content here.
"""
        )

        learning = parse_learning_file(learning_file)

        assert learning.name == "Test Learning"
        assert learning.last_updated == date(2025, 1, 30)
        assert "Discovered that X causes Y" in learning.summarized_result
        assert "Full learning content" in learning.body

    def test_parse_minimal_learning(self, tmp_path: Path) -> None:
        """Test parsing a minimal learning file."""
        learning_file = tmp_path / "minimal.md"
        learning_file.write_text(
            """---
name: Minimal Learning
---

Content here.
"""
        )

        learning = parse_learning_file(learning_file)

        assert learning.name == "Minimal Learning"
        assert learning.last_updated is None
        assert learning.summarized_result is None

    def test_parse_learning_missing_frontmatter(self, tmp_path: Path) -> None:
        """Test parsing learning without frontmatter fails."""
        learning_file = tmp_path / "no_frontmatter.md"
        learning_file.write_text("Just content")

        with pytest.raises(ExpertParseError, match="frontmatter"):
            parse_learning_file(learning_file)


class TestParseExpertDefinition:
    """Tests for parsing expert definitions."""

    def test_parse_valid_expert(self, tmp_path: Path) -> None:
        """Test parsing a valid expert definition."""
        expert_dir = tmp_path / "test_expert"
        expert_dir.mkdir()

        # Create expert.yml
        (expert_dir / "expert.yml").write_text(
            """discovery_description: |
  Test expert for unit testing

full_expertise: |
  You are an expert on testing.
"""
        )

        # Create topics directory with a topic
        topics_dir = expert_dir / "topics"
        topics_dir.mkdir()
        (topics_dir / "basics.md").write_text(
            """---
name: Testing Basics
keywords:
  - basics
last_updated: 2025-01-30
---

Content
"""
        )

        # Create learnings directory with a learning
        learnings_dir = expert_dir / "learnings"
        learnings_dir.mkdir()
        (learnings_dir / "discovery.md").write_text(
            """---
name: Important Discovery
last_updated: 2025-01-20
summarized_result: Found something important.
---

Details
"""
        )

        expert = parse_expert_definition(expert_dir)

        assert expert.name == "test-expert"
        assert "unit testing" in expert.discovery_description
        assert "expert on testing" in expert.full_expertise
        assert len(expert.topics) == 1
        assert expert.topics[0].name == "Testing Basics"
        assert len(expert.learnings) == 1
        assert expert.learnings[0].name == "Important Discovery"

    def test_parse_expert_no_topics_or_learnings(self, tmp_path: Path) -> None:
        """Test parsing expert without topics or learnings directories."""
        expert_dir = tmp_path / "minimal_expert"
        expert_dir.mkdir()

        (expert_dir / "expert.yml").write_text(
            """discovery_description: Minimal expert
full_expertise: Minimal expertise.
"""
        )

        expert = parse_expert_definition(expert_dir)

        assert expert.name == "minimal-expert"
        assert expert.topics == []
        assert expert.learnings == []

    def test_parse_expert_missing_expert_yml(self, tmp_path: Path) -> None:
        """Test parsing expert without expert.yml fails."""
        expert_dir = tmp_path / "no_yml"
        expert_dir.mkdir()

        with pytest.raises(ExpertParseError, match="expert.yml not found"):
            parse_expert_definition(expert_dir)

    def test_parse_expert_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test parsing nonexistent directory fails."""
        with pytest.raises(ExpertParseError, match="does not exist"):
            parse_expert_definition(tmp_path / "nonexistent")

    def test_parse_expert_invalid_yml(self, tmp_path: Path) -> None:
        """Test parsing expert with invalid YAML fails."""
        expert_dir = tmp_path / "invalid"
        expert_dir.mkdir()
        (expert_dir / "expert.yml").write_text("discovery_description: only one field")

        with pytest.raises(ExpertParseError, match="full_expertise"):
            parse_expert_definition(expert_dir)


class TestDiscoverExperts:
    """Tests for discovering expert directories."""

    def test_discover_experts_multiple(self, tmp_path: Path) -> None:
        """Test discovering multiple experts."""
        experts_dir = tmp_path / "experts"
        experts_dir.mkdir()

        # Create two expert directories
        for name in ["expert_a", "expert_b"]:
            expert_dir = experts_dir / name
            expert_dir.mkdir()
            (expert_dir / "expert.yml").write_text(
                f"discovery_description: {name}\nfull_expertise: Content"
            )

        expert_dirs = discover_experts(experts_dir)

        assert len(expert_dirs) == 2
        names = {d.name for d in expert_dirs}
        assert names == {"expert_a", "expert_b"}

    def test_discover_experts_empty(self, tmp_path: Path) -> None:
        """Test discovering experts in empty directory."""
        experts_dir = tmp_path / "experts"
        experts_dir.mkdir()

        expert_dirs = discover_experts(experts_dir)

        assert expert_dirs == []

    def test_discover_experts_nonexistent(self, tmp_path: Path) -> None:
        """Test discovering experts in nonexistent directory."""
        expert_dirs = discover_experts(tmp_path / "nonexistent")

        assert expert_dirs == []

    def test_discover_experts_ignores_non_expert_dirs(self, tmp_path: Path) -> None:
        """Test that directories without expert.yml are ignored."""
        experts_dir = tmp_path / "experts"
        experts_dir.mkdir()

        # Valid expert
        valid_dir = experts_dir / "valid_expert"
        valid_dir.mkdir()
        (valid_dir / "expert.yml").write_text(
            "discovery_description: Valid\nfull_expertise: Content"
        )

        # Invalid - no expert.yml
        invalid_dir = experts_dir / "not_an_expert"
        invalid_dir.mkdir()
        (invalid_dir / "readme.md").write_text("Not an expert")

        expert_dirs = discover_experts(experts_dir)

        assert len(expert_dirs) == 1
        assert expert_dirs[0].name == "valid_expert"


class TestFormatTopicsMarkdown:
    """Tests for formatting topics as markdown."""

    def test_format_topics_empty(self) -> None:
        """Test formatting empty topics list."""
        expert = ExpertDefinition(
            name="test",
            discovery_description="Test",
            full_expertise="Test",
            expert_dir=Path("/test"),
            topics=[],
        )

        result = format_topics_markdown(expert)

        assert result == "_No topics yet._"

    def test_format_topics_with_content(self) -> None:
        """Test formatting topics with content."""
        topics = [
            Topic(
                name="First Topic",
                keywords=["key1", "key2"],
                source_file=Path("/test/topics/first.md"),
            ),
            Topic(name="Second Topic", source_file=Path("/test/topics/second.md")),
        ]
        expert = ExpertDefinition(
            name="test",
            discovery_description="Test",
            full_expertise="Test",
            expert_dir=Path("/test"),
            topics=topics,
        )

        result = format_topics_markdown(expert)

        assert "[First Topic](topics/first.md)" in result
        assert "[Second Topic](topics/second.md)" in result
        assert "Keywords: key1, key2" in result


class TestFormatLearningsMarkdown:
    """Tests for formatting learnings as markdown."""

    def test_format_learnings_empty(self) -> None:
        """Test formatting empty learnings list."""
        expert = ExpertDefinition(
            name="test",
            discovery_description="Test",
            full_expertise="Test",
            expert_dir=Path("/test"),
            learnings=[],
        )

        result = format_learnings_markdown(expert)

        assert result == "_No learnings yet._"

    def test_format_learnings_with_content(self) -> None:
        """Test formatting learnings with content."""
        learnings = [
            Learning(
                name="First Learning",
                summarized_result="Found something important.",
                source_file=Path("/test/learnings/first.md"),
            ),
            Learning(name="Second Learning", source_file=Path("/test/learnings/second.md")),
        ]
        expert = ExpertDefinition(
            name="test",
            discovery_description="Test",
            full_expertise="Test",
            expert_dir=Path("/test"),
            learnings=learnings,
        )

        result = format_learnings_markdown(expert)

        assert "[First Learning](learnings/first.md)" in result
        assert "[Second Learning](learnings/second.md)" in result
        assert "Found something important" in result
