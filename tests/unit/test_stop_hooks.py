"""Tests for stop hook functionality."""

from pathlib import Path

import pytest

from deepwork.core.adapters import ClaudeAdapter
from deepwork.core.generator import GeneratorError, SkillGenerator
from deepwork.core.parser import HookAction, JobDefinition, Step, StopHook
from deepwork.schemas.job_schema import JOB_SCHEMA
from deepwork.utils.validation import ValidationError, validate_against_schema


class TestStopHook:
    """Tests for StopHook dataclass."""

    def test_is_prompt(self) -> None:
        """Test is_prompt returns True for prompt hooks."""
        hook = StopHook(prompt="Check quality")
        assert hook.is_prompt() is True
        assert hook.is_prompt_file() is False
        assert hook.is_script() is False

    def test_is_prompt_file(self) -> None:
        """Test is_prompt_file returns True for prompt file hooks."""
        hook = StopHook(prompt_file="hooks/check.md")
        assert hook.is_prompt() is False
        assert hook.is_prompt_file() is True
        assert hook.is_script() is False

    def test_is_script(self) -> None:
        """Test is_script returns True for script hooks."""
        hook = StopHook(script="hooks/validate.sh")
        assert hook.is_prompt() is False
        assert hook.is_prompt_file() is False
        assert hook.is_script() is True

    def test_from_dict_prompt(self) -> None:
        """Test from_dict creates prompt hook."""
        data = {"prompt": "Verify all criteria are met"}
        hook = StopHook.from_dict(data)
        assert hook.prompt == "Verify all criteria are met"
        assert hook.prompt_file is None
        assert hook.script is None

    def test_from_dict_prompt_file(self) -> None:
        """Test from_dict creates prompt file hook."""
        data = {"prompt_file": "hooks/quality.md"}
        hook = StopHook.from_dict(data)
        assert hook.prompt is None
        assert hook.prompt_file == "hooks/quality.md"
        assert hook.script is None

    def test_from_dict_script(self) -> None:
        """Test from_dict creates script hook."""
        data = {"script": "hooks/validate.sh"}
        hook = StopHook.from_dict(data)
        assert hook.prompt is None
        assert hook.prompt_file is None
        assert hook.script == "hooks/validate.sh"


class TestStepWithStopHooks:
    """Tests for Step with stop_hooks."""

    def test_step_with_no_stop_hooks(self) -> None:
        """Test step without stop hooks."""
        step = Step(
            id="test",
            name="Test Step",
            description="A test step",
            instructions_file="steps/test.md",
            outputs=["output.md"],
        )
        assert step.stop_hooks == []

    def test_step_with_single_stop_hook(self) -> None:
        """Test step with single stop hook (using hooks dict)."""
        step = Step(
            id="test",
            name="Test Step",
            description="A test step",
            instructions_file="steps/test.md",
            outputs=["output.md"],
            hooks={"after_agent": [HookAction(prompt="Check quality")]},
        )
        assert len(step.stop_hooks) == 1
        assert step.stop_hooks[0].is_prompt()
        assert step.stop_hooks[0].prompt == "Check quality"

    def test_step_with_multiple_stop_hooks(self) -> None:
        """Test step with multiple stop hooks (using hooks dict)."""
        step = Step(
            id="test",
            name="Test Step",
            description="A test step",
            instructions_file="steps/test.md",
            outputs=["output.md"],
            hooks={
                "after_agent": [
                    HookAction(prompt="Check criteria 1"),
                    HookAction(script="hooks/validate.sh"),
                ]
            },
        )
        assert len(step.stop_hooks) == 2
        assert step.stop_hooks[0].is_prompt()
        assert step.stop_hooks[1].is_script()

    def test_step_from_dict_with_stop_hooks(self) -> None:
        """Test Step.from_dict parses stop_hooks array."""
        data = {
            "id": "test",
            "name": "Test Step",
            "description": "A test step",
            "instructions_file": "steps/test.md",
            "outputs": ["output.md"],
            "stop_hooks": [
                {"prompt": "Check quality criteria"},
                {"script": "hooks/run_tests.sh"},
            ],
        }
        step = Step.from_dict(data)
        assert len(step.stop_hooks) == 2
        assert step.stop_hooks[0].prompt == "Check quality criteria"
        assert step.stop_hooks[1].script == "hooks/run_tests.sh"

    def test_step_from_dict_without_stop_hooks(self) -> None:
        """Test Step.from_dict with no stop_hooks returns empty list."""
        data = {
            "id": "test",
            "name": "Test Step",
            "description": "A test step",
            "instructions_file": "steps/test.md",
            "outputs": ["output.md"],
        }
        step = Step.from_dict(data)
        assert step.stop_hooks == []

    def test_step_from_dict_with_hooks_structure(self) -> None:
        """Test Step.from_dict parses new hooks structure with lifecycle events."""
        data = {
            "id": "test",
            "name": "Test Step",
            "description": "A test step",
            "instructions_file": "steps/test.md",
            "outputs": ["output.md"],
            "hooks": {
                "after_agent": [
                    {"prompt": "Check quality"},
                    {"script": "hooks/validate.sh"},
                ],
                "before_tool": [
                    {"prompt": "Pre-tool check"},
                ],
            },
        }
        step = Step.from_dict(data)
        # stop_hooks property returns after_agent hooks
        assert len(step.stop_hooks) == 2
        assert step.stop_hooks[0].prompt == "Check quality"
        assert step.stop_hooks[1].script == "hooks/validate.sh"
        # Check full hooks dict
        assert "after_agent" in step.hooks
        assert "before_tool" in step.hooks
        assert len(step.hooks["after_agent"]) == 2
        assert len(step.hooks["before_tool"]) == 1


class TestSchemaValidation:
    """Tests for stop_hooks schema validation."""

    def test_valid_prompt_stop_hook(self) -> None:
        """Test schema accepts valid prompt stop hook."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [{"prompt": "Check quality"}],
                }
            ],
        }
        # Should not raise
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_valid_script_stop_hook(self) -> None:
        """Test schema accepts valid script stop hook."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [{"script": "hooks/validate.sh"}],
                }
            ],
        }
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_valid_prompt_file_stop_hook(self) -> None:
        """Test schema accepts valid prompt_file stop hook."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [{"prompt_file": "hooks/quality.md"}],
                }
            ],
        }
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_valid_multiple_stop_hooks(self) -> None:
        """Test schema accepts multiple stop hooks."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [
                        {"prompt": "Check quality"},
                        {"script": "hooks/tests.sh"},
                    ],
                }
            ],
        }
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_invalid_stop_hook_missing_type(self) -> None:
        """Test schema rejects stop hook without type."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [{}],  # Empty object
                }
            ],
        }
        with pytest.raises(ValidationError):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_invalid_stop_hook_extra_fields(self) -> None:
        """Test schema rejects stop hook with extra fields."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "stop_hooks": [{"prompt": "Check", "extra": "field"}],
                }
            ],
        }
        with pytest.raises(ValidationError):
            validate_against_schema(job_data, JOB_SCHEMA)

    def test_valid_hooks_with_after_agent(self) -> None:
        """Test schema accepts new hooks structure with after_agent event."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "hooks": {
                        "after_agent": [{"prompt": "Check quality"}],
                    },
                }
            ],
        }
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_valid_hooks_with_multiple_events(self) -> None:
        """Test schema accepts hooks with multiple lifecycle events."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "hooks": {
                        "after_agent": [{"prompt": "Check quality"}],
                        "before_tool": [{"script": "hooks/validate.sh"}],
                        "before_prompt": [{"prompt": "Initialize context"}],
                    },
                }
            ],
        }
        validate_against_schema(job_data, JOB_SCHEMA)

    def test_valid_hooks_with_script_action(self) -> None:
        """Test schema accepts hooks with script action."""
        job_data = {
            "name": "test_job",
            "version": "1.0.0",
            "summary": "Test job",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "A step",
                    "instructions_file": "steps/step1.md",
                    "outputs": ["output.md"],
                    "hooks": {
                        "before_tool": [{"script": "hooks/check.sh"}],
                    },
                }
            ],
        }
        validate_against_schema(job_data, JOB_SCHEMA)


class TestGeneratorStopHooks:
    """Tests for generator stop hooks context building."""

    @pytest.fixture
    def generator(self, tmp_path: Path) -> SkillGenerator:
        """Create generator with temp templates."""
        templates_dir = tmp_path / "templates"
        claude_dir = templates_dir / "claude"
        claude_dir.mkdir(parents=True)

        # Create minimal template
        template_content = """---
description: {{ step_description }}
{% if stop_hooks %}
hooks:
  Stop:
    - hooks:
{% for hook in stop_hooks %}
{% if hook.type == "script" %}
        - type: command
          command: ".deepwork/jobs/{{ job_name }}/{{ hook.path }}"
{% else %}
        - type: prompt
          prompt: "{{ hook.content }}"
{% endif %}
{% endfor %}
{% endif %}
---
# {{ job_name }}.{{ step_id }}
{{ instructions_content }}
"""
        (claude_dir / "skill-job-step.md.jinja").write_text(template_content)
        return SkillGenerator(templates_dir)

    @pytest.fixture
    def job_with_hooks(self, tmp_path: Path) -> JobDefinition:
        """Create job with stop hooks."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Step 1 Instructions")

        return JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="A test job",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="First step",
                    instructions_file="steps/step1.md",
                    outputs=["output.md"],
                    hooks={
                        "after_agent": [HookAction(prompt="Verify quality criteria")],
                    },
                ),
            ],
            job_dir=job_dir,
        )

    @pytest.fixture
    def job_with_script_hook(self, tmp_path: Path) -> JobDefinition:
        """Create job with script stop hook."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Step 1 Instructions")

        return JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="A test job",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="First step",
                    instructions_file="steps/step1.md",
                    outputs=["output.md"],
                    hooks={
                        "after_agent": [HookAction(script="hooks/validate.sh")],
                    },
                ),
            ],
            job_dir=job_dir,
        )

    @pytest.fixture
    def job_with_prompt_file_hook(self, tmp_path: Path) -> JobDefinition:
        """Create job with prompt file stop hook."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        hooks_dir = job_dir / "hooks"
        hooks_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Step 1 Instructions")
        (hooks_dir / "quality.md").write_text("Check all quality criteria")

        return JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test job",
            description="A test job",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="First step",
                    instructions_file="steps/step1.md",
                    outputs=["output.md"],
                    hooks={
                        "after_agent": [HookAction(prompt_file="hooks/quality.md")],
                    },
                ),
            ],
            job_dir=job_dir,
        )

    def test_build_context_with_prompt_hook(
        self, generator: SkillGenerator, job_with_hooks: JobDefinition
    ) -> None:
        """Test context building includes prompt stop hook."""
        adapter = ClaudeAdapter()
        context = generator._build_step_context(job_with_hooks, job_with_hooks.steps[0], 0, adapter)
        assert "stop_hooks" in context
        assert len(context["stop_hooks"]) == 1
        assert context["stop_hooks"][0]["type"] == "prompt"
        assert context["stop_hooks"][0]["content"] == "Verify quality criteria"

    def test_build_context_with_script_hook(
        self, generator: SkillGenerator, job_with_script_hook: JobDefinition
    ) -> None:
        """Test context building includes script stop hook."""
        adapter = ClaudeAdapter()
        context = generator._build_step_context(
            job_with_script_hook, job_with_script_hook.steps[0], 0, adapter
        )
        assert "stop_hooks" in context
        assert len(context["stop_hooks"]) == 1
        assert context["stop_hooks"][0]["type"] == "script"
        assert context["stop_hooks"][0]["path"] == "hooks/validate.sh"

    def test_build_context_with_prompt_file_hook(
        self, generator: SkillGenerator, job_with_prompt_file_hook: JobDefinition
    ) -> None:
        """Test context building reads prompt file content."""
        adapter = ClaudeAdapter()
        context = generator._build_step_context(
            job_with_prompt_file_hook, job_with_prompt_file_hook.steps[0], 0, adapter
        )
        assert "stop_hooks" in context
        assert len(context["stop_hooks"]) == 1
        assert context["stop_hooks"][0]["type"] == "prompt_file"
        assert context["stop_hooks"][0]["content"] == "Check all quality criteria"

    def test_build_context_with_missing_prompt_file(
        self, generator: SkillGenerator, tmp_path: Path
    ) -> None:
        """Test error when prompt file is missing."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Step 1")

        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=["out.md"],
                    hooks={
                        "after_agent": [HookAction(prompt_file="missing.md")],
                    },
                )
            ],
            job_dir=job_dir,
        )

        adapter = ClaudeAdapter()
        with pytest.raises(GeneratorError, match="prompt file not found"):
            generator._build_step_context(job, job.steps[0], 0, adapter)

    def test_build_context_no_hooks(self, generator: SkillGenerator, tmp_path: Path) -> None:
        """Test context with no stop hooks."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Step 1")

        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=["out.md"],
                )
            ],
            job_dir=job_dir,
        )

        adapter = ClaudeAdapter()
        context = generator._build_step_context(job, job.steps[0], 0, adapter)
        assert context["stop_hooks"] == []

    def test_build_context_multiple_hooks(self, generator: SkillGenerator, tmp_path: Path) -> None:
        """Test context with multiple stop hooks."""
        job_dir = tmp_path / "test_job"
        job_dir.mkdir()
        steps_dir = job_dir / "steps"
        steps_dir.mkdir()
        (steps_dir / "step1.md").write_text("# Step 1")

        job = JobDefinition(
            name="test_job",
            version="1.0.0",
            summary="Test",
            description="Test",
            steps=[
                Step(
                    id="step1",
                    name="Step 1",
                    description="Step",
                    instructions_file="steps/step1.md",
                    outputs=["out.md"],
                    hooks={
                        "after_agent": [
                            HookAction(prompt="Check criteria 1"),
                            HookAction(script="hooks/test.sh"),
                            HookAction(prompt="Check criteria 2"),
                        ],
                    },
                )
            ],
            job_dir=job_dir,
        )

        adapter = ClaudeAdapter()
        context = generator._build_step_context(job, job.steps[0], 0, adapter)
        assert len(context["stop_hooks"]) == 3
        assert context["stop_hooks"][0]["type"] == "prompt"
        assert context["stop_hooks"][1]["type"] == "script"
        assert context["stop_hooks"][2]["type"] == "prompt"
