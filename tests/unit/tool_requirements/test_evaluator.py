"""Tests for tool requirements LLM evaluator (DW-REQ-012.5)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from deepwork.tool_requirements.config import Requirement
from deepwork.tool_requirements.evaluator import (
    HaikuSubprocessEvaluator,
    _build_prompt,
    _extract_json_array,
    _parse_result,
)


class TestBuildPrompt:
    def test_includes_tool_info(self) -> None:
        reqs = {"r1": Requirement(rule="MUST check")}
        prompt = _build_prompt(reqs, "shell", {"command": "rm -rf /"})
        assert "shell" in prompt
        assert "rm -rf /" in prompt
        assert "r1" in prompt
        assert "MUST check" in prompt

    def test_includes_justifications_when_present(self) -> None:
        reqs = {"r1": Requirement(rule="MUST check")}
        prompt = _build_prompt(
            reqs,
            "shell",
            {"command": "ls"},
            justifications={"r1": "This is safe because..."},
        )
        assert "This is safe because..." in prompt
        assert "justification" in prompt.lower()

    def test_truncates_large_input(self) -> None:
        large_input = {"content": "x" * 20000}
        reqs = {"r1": Requirement(rule="MUST check")}
        prompt = _build_prompt(reqs, "write_file", large_input)
        assert "[truncated]" in prompt


class TestExtractJsonArray:
    def test_direct_array(self) -> None:
        text = '[{"a": 1}]'
        assert _extract_json_array(text) == [{"a": 1}]

    def test_array_with_surrounding_text(self) -> None:
        text = 'Here is my analysis:\n[{"a": 1}]\nDone.'
        assert _extract_json_array(text) == [{"a": 1}]

    def test_no_array(self) -> None:
        assert _extract_json_array("no json here") is None

    def test_empty_array(self) -> None:
        assert _extract_json_array("[]") == []


class TestParseResult:
    def test_parses_stream_json_result(self) -> None:
        verdicts = [
            {"requirement_id": "r1", "passed": True, "explanation": "OK"},
            {"requirement_id": "r2", "passed": False, "explanation": "Bad"},
        ]
        # Simulate stream-json output
        lines = [
            json.dumps({"type": "content", "content": json.dumps(verdicts)}),
        ]
        raw = "\n".join(lines)
        reqs = {
            "r1": Requirement(rule="MUST do A"),
            "r2": Requirement(rule="MUST do B"),
        }
        result = _parse_result(raw, reqs)
        assert len(result) == 2
        assert result[0].requirement_id == "r1"
        assert result[0].passed is True
        assert result[1].requirement_id == "r2"
        assert result[1].passed is False

    def test_missing_requirement_fails_closed(self) -> None:
        verdicts = [{"requirement_id": "r1", "passed": True, "explanation": "OK"}]
        raw = json.dumps(verdicts)
        reqs = {
            "r1": Requirement(rule="Rule 1"),
            "r2": Requirement(rule="Rule 2"),
        }
        result = _parse_result(raw, reqs)
        r2 = next(v for v in result if v.requirement_id == "r2")
        assert r2.passed is False
        assert "not evaluated" in r2.explanation

    def test_unparseable_output_fails_all(self) -> None:
        reqs = {"r1": Requirement(rule="Rule 1")}
        result = _parse_result("garbage output", reqs)
        assert len(result) == 1
        assert result[0].passed is False

    def test_result_type_message(self) -> None:
        verdicts = [{"requirement_id": "r1", "passed": True, "explanation": "OK"}]
        raw = json.dumps({"type": "result", "result": json.dumps(verdicts)})
        reqs = {"r1": Requirement(rule="Rule 1")}
        result = _parse_result(raw, reqs)
        assert result[0].passed is True

    def test_duplicate_requirement_ids_deduplicated(self) -> None:
        verdicts = [
            {"requirement_id": "r1", "passed": True, "explanation": "First"},
            {"requirement_id": "r1", "passed": False, "explanation": "Duplicate"},
        ]
        raw = json.dumps(verdicts)
        reqs = {"r1": Requirement(rule="Rule 1")}
        result = _parse_result(raw, reqs)
        assert len(result) == 1
        assert result[0].passed is True  # First occurrence wins

    def test_non_dict_items_filtered(self) -> None:
        result = _extract_json_array('[1, {"a": 1}, "str"]')
        assert result == [{"a": 1}]

    def test_bracket_search_invalid_json(self) -> None:
        result = _extract_json_array("prefix [not valid json] suffix")
        assert result is None


class TestHaikuSubprocessEvaluator:
    @pytest.mark.asyncio()
    @patch("asyncio.create_subprocess_exec")
    async def test_call_haiku_success(self, mock_exec: AsyncMock) -> None:
        verdicts = [{"requirement_id": "r1", "passed": True, "explanation": "OK"}]
        stdout = json.dumps(verdicts).encode()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (stdout, b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        evaluator = HaikuSubprocessEvaluator()
        reqs = {"r1": Requirement(rule="MUST check")}
        result = await evaluator.evaluate(reqs, "shell", {"command": "ls"})
        assert len(result) == 1
        assert result[0].passed is True

    @pytest.mark.asyncio()
    @patch("asyncio.create_subprocess_exec")
    async def test_call_haiku_failure_raises(self, mock_exec: AsyncMock) -> None:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"error")
        mock_proc.returncode = 1
        mock_exec.return_value = mock_proc

        evaluator = HaikuSubprocessEvaluator()
        reqs = {"r1": Requirement(rule="MUST check")}
        with pytest.raises(RuntimeError, match="Haiku subprocess failed"):
            await evaluator.evaluate(reqs, "shell", {"command": "ls"})

    @pytest.mark.asyncio()
    async def test_empty_requirements_returns_empty(self) -> None:
        evaluator = HaikuSubprocessEvaluator()
        result = await evaluator.evaluate({}, "shell", {"command": "ls"})
        assert result == []
