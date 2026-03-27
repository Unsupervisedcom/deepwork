"""Tests for the record standard job definition (JOBS-REQ-011)."""

from pathlib import Path

import pytest

from deepwork.jobs.parser import parse_job_definition

RECORD_JOB_DIR = (
    Path(__file__).parent.parent.parent.parent / "src" / "deepwork" / "standard_jobs" / "record"
)


@pytest.fixture()
def job():
    """Parse the record standard job definition."""
    return parse_job_definition(RECORD_JOB_DIR)


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.1).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_job_location():
    """The record job MUST be at src/deepwork/standard_jobs/record/."""
    assert RECORD_JOB_DIR.exists()
    assert (RECORD_JOB_DIR / "job.yml").exists()


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.2).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_job_parses_successfully(job):
    """The job.yml MUST pass schema validation."""
    assert job is not None
    assert job.name == "record"


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.3).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_job_has_four_steps(job):
    """The job MUST define exactly four steps."""
    assert len(job.steps) == 4
    step_ids = [s.id for s in job.steps]
    assert step_ids == ["observe", "document", "reflect", "generate_job"]


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.1.4).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_record_workflow_sequences_all_steps(job):
    """The job MUST define a record workflow sequencing all four steps."""
    workflow = next((w for w in job.workflows if w.name == "record"), None)
    assert workflow is not None
    assert workflow.steps == ["observe", "document", "reflect", "generate_job"]


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.1).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_observe_no_inputs(job):
    """The observe step MUST NOT require any user-provided inputs."""
    observe = next(s for s in job.steps if s.id == "observe")
    assert observe.inputs == []


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.2.2).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_observe_empty_outputs(job):
    """The observe step MUST have empty outputs."""
    observe = next(s for s in job.steps if s.id == "observe")
    assert observe.outputs == []


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.3.1).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_document_no_file_inputs_from_observe(job):
    """The document step MUST NOT consume file inputs from the observe step."""
    document = next(s for s in job.steps if s.id == "document")
    file_inputs_from_observe = [
        i for i in document.inputs if i.file is not None and i.from_step == "observe"
    ]
    assert file_inputs_from_observe == []


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.3.2).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_document_produces_process_document(job):
    """The document step MUST produce a process_document.md output."""
    document = next(s for s in job.steps if s.id == "document")
    output_names = [o.name for o in document.outputs]
    assert "process_document.md" in output_names
    output = next(o for o in document.outputs if o.name == "process_document.md")
    assert output.required is True


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.3.5).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_document_has_quality_reviews(job):
    """The document step MUST have quality reviews."""
    document = next(s for s in job.steps if s.id == "document")
    assert len(document.reviews) > 0
    criteria_keys = set()
    for review in document.reviews:
        criteria_keys.update(review.quality_criteria.keys())
    assert "Complete Coverage" in criteria_keys
    assert "Clear Structure" in criteria_keys
    assert "User Clarification Incorporated" in criteria_keys


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.4.1).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_reflect_consumes_process_document(job):
    """The reflect step MUST consume process_document.md from document."""
    reflect = next(s for s in job.steps if s.id == "reflect")
    file_inputs = [i for i in reflect.inputs if i.file == "process_document.md"]
    assert len(file_inputs) == 1
    assert file_inputs[0].from_step == "document"


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.4.2).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_reflect_produces_reflection(job):
    """The reflect step MUST produce a reflection.md output."""
    reflect = next(s for s in job.steps if s.id == "reflect")
    output_names = [o.name for o in reflect.outputs]
    assert "reflection.md" in output_names
    output = next(o for o in reflect.outputs if o.name == "reflection.md")
    assert output.required is True


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.4.4).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_reflect_has_quality_reviews(job):
    """The reflect step MUST have quality reviews."""
    reflect = next(s for s in job.steps if s.id == "reflect")
    assert len(reflect.reviews) > 0
    criteria_keys = set()
    for review in reflect.reviews:
        criteria_keys.update(review.quality_criteria.keys())
    assert "Actionable Improvements" in criteria_keys
    assert "Stumbling Blocks Identified" in criteria_keys
    assert "Grounded in Evidence" in criteria_keys


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.5.1).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_generate_job_consumes_both_inputs(job):
    """The generate_job step MUST consume process_document.md and reflection.md."""
    gen = next(s for s in job.steps if s.id == "generate_job")
    file_inputs = {i.file: i.from_step for i in gen.inputs if i.file is not None}
    assert file_inputs == {
        "process_document.md": "document",
        "reflection.md": "reflect",
    }


# THIS TEST VALIDATES A HARD REQUIREMENT (JOBS-REQ-011.5.2).
# YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
def test_generate_job_produces_confirmation(job):
    """The generate_job step MUST produce a job_created.md output."""
    gen = next(s for s in job.steps if s.id == "generate_job")
    output_names = [o.name for o in gen.outputs]
    assert "job_created.md" in output_names
    output = next(o for o in gen.outputs if o.name == "job_created.md")
    assert output.required is True
