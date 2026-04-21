"""Tests for the full-convo-memory plugin — validates PLUG-REQ-004.

Each test class maps to a numbered requirement section in
doc/specs/deepwork/cli_plugins/PLUG-REQ-004-full-convo-memory-plugin.md.

Requirements that need judgment to evaluate (e.g., "skill body MUST instruct
the agent to fall back to an Explore sub-agent when jq matching is
insufficient") are validated by the anonymous DeepSchema next to SKILL.md,
not by tests. Only deterministic, boolean-verifiable requirements have tests
here.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugins" / "full-convo-memory"
SCRIPT_PATH = PLUGIN_DIR / "scripts" / "search_conversation.sh"
SKILL_PATH = PLUGIN_DIR / "skills" / "search_conversation" / "SKILL.md"
MARKETPLACE_PATH = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"

POINTER_LINE_PREFIX = (
    "If you want a more semantic search of the history, "
    "start an Explore agent and tell it what to look for in"
)


def _encode_cwd(path: Path) -> str:
    """Mirror the script's <encoded-cwd> rule: every '/' → '-'."""
    return str(path).replace("/", "-")


def _parse_yaml_frontmatter(skill_path: Path) -> dict[str, Any]:
    text = skill_path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{skill_path} must start with YAML frontmatter"
    end = text.index("---", 3)
    result: dict[str, Any] = yaml.safe_load(text[3:end])
    return result


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `$HOME` at a tmp dir and create the encoded-cwd project dir.

    The script resolves log files under `$HOME/.claude/projects/<encoded-cwd>/`,
    where `<encoded-cwd>` is computed from `$PWD`. We chdir into `tmp_path/cwd`
    (a path with no `-` in it) so the encoded form is deterministic for tests.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    encoded = _encode_cwd(cwd)
    project_dir = home / ".claude" / "projects" / encoded
    project_dir.mkdir(parents=True)

    # Keep sub-agent env vars unset by default; tests opt in.
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_AGENT_ID", raising=False)
    return project_dir


def _run_script(
    *args: str,
    env_overrides: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_overrides is not None:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd is not None else None,
        check=False,
    )


# ---------------------------------------------------------------------------
# PLUG-REQ-004.1: Plugin Manifest
# ---------------------------------------------------------------------------


class TestPluginManifest:
    manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.1.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_manifest_exists(self) -> None:
        """PLUG-REQ-004.1.1: manifest exists at the expected path."""
        assert self.manifest_path.exists()

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.1.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_manifest_name_is_full_convo_memory(self) -> None:
        """PLUG-REQ-004.1.2: manifest name field is 'full-convo-memory'."""
        data = json.loads(self.manifest_path.read_text())
        assert data["name"] == "full-convo-memory"

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.1.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_manifest_required_fields(self) -> None:
        """PLUG-REQ-004.1.3: manifest includes non-empty required fields."""
        data = json.loads(self.manifest_path.read_text())
        assert data["description"]
        assert data["version"]
        assert data["author"]["name"]
        assert data["repository"]


# ---------------------------------------------------------------------------
# PLUG-REQ-004.2: Marketplace Registration
# ---------------------------------------------------------------------------


class TestMarketplaceRegistration:
    @pytest.fixture(scope="class")
    def entry(self) -> dict[str, Any]:
        data = json.loads(MARKETPLACE_PATH.read_text())
        matches = [p for p in data["plugins"] if p.get("name") == "full-convo-memory"]
        assert len(matches) == 1, "expected exactly one marketplace entry for full-convo-memory"
        return matches[0]

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.2.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_marketplace_entry_present(self) -> None:
        """PLUG-REQ-004.2.1: plugin is registered in marketplace.json."""
        data = json.loads(MARKETPLACE_PATH.read_text())
        names = [p.get("name") for p in data["plugins"]]
        assert "full-convo-memory" in names

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.2.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_marketplace_name(self, entry: dict[str, Any]) -> None:
        """PLUG-REQ-004.2.2: marketplace entry name is 'full-convo-memory'."""
        assert entry["name"] == "full-convo-memory"

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.2.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_marketplace_source(self, entry: dict[str, Any]) -> None:
        """PLUG-REQ-004.2.3: marketplace source points to the plugin root."""
        assert entry["source"] == "./plugins/full-convo-memory"

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.2.4).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_marketplace_fields_present(self, entry: dict[str, Any]) -> None:
        """PLUG-REQ-004.2.4: marketplace entry has all required fields."""
        for field in (
            "description",
            "version",
            "author",
            "category",
            "keywords",
            "repository",
            "license",
        ):
            assert field in entry, f"marketplace entry missing field: {field}"


# ---------------------------------------------------------------------------
# PLUG-REQ-004.3: Plugin Root Directory Layout
# ---------------------------------------------------------------------------


class TestPluginLayout:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.3.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_expected_files_exist(self) -> None:
        """PLUG-REQ-004.3.1: plugin root contains manifest, script, and SKILL.md."""
        assert (PLUGIN_DIR / ".claude-plugin" / "plugin.json").is_file()
        assert SCRIPT_PATH.is_file()
        assert SKILL_PATH.is_file()


# ---------------------------------------------------------------------------
# PLUG-REQ-004.4: Search Script Existence and Shebang
# ---------------------------------------------------------------------------


class TestScriptExistence:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.4.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_script_exists(self) -> None:
        """PLUG-REQ-004.4.1: script exists at the expected path."""
        assert SCRIPT_PATH.is_file()

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.4.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_script_is_executable(self) -> None:
        """PLUG-REQ-004.4.2: script has the owner-executable bit set."""
        mode = SCRIPT_PATH.stat().st_mode
        assert mode & stat.S_IXUSR

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.4.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_script_shebang(self) -> None:
        """PLUG-REQ-004.4.3: script's first line is the env-bash shebang."""
        first_line = SCRIPT_PATH.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"


# ---------------------------------------------------------------------------
# PLUG-REQ-004.5: Zero-Argument Guard
# ---------------------------------------------------------------------------


class TestZeroArgGuard:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.5.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_no_args_exits_2_with_usage(self, fake_home: Path) -> None:
        """PLUG-REQ-004.5.1: no args → usage on stderr, exit 2."""
        result = _run_script()
        assert result.returncode == 2
        assert "Usage:" in result.stderr


# ---------------------------------------------------------------------------
# PLUG-REQ-004.6: jq Dependency Check
# ---------------------------------------------------------------------------


class TestJqDependency:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.6.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_missing_jq_exits_127(self, fake_home: Path, tmp_path: Path) -> None:
        """PLUG-REQ-004.6.1: jq absent → error on stderr, exit 127."""
        # Construct a minimal PATH that contains only the coreutils the script
        # needs (bash, sed, find, xargs, ls, head, printf, cat) but excludes jq.
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        for cmd in (
            "bash",
            "sed",
            "find",
            "xargs",
            "ls",
            "head",
            "printf",
            "cat",
            "chmod",
            "env",
        ):
            src = shutil.which(cmd)
            if src is not None:
                os.symlink(src, empty_bin / cmd)

        result = _run_script(
            "select(true)",
            env_overrides={"PATH": str(empty_bin)},
        )
        assert result.returncode == 127
        assert "jq" in result.stderr


# ---------------------------------------------------------------------------
# PLUG-REQ-004.7: Explicit Log-File Override
# ---------------------------------------------------------------------------


class TestLogFileOverride:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.7.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_override_uses_supplied_path(self, fake_home: Path, tmp_path: Path) -> None:
        """PLUG-REQ-004.7.1: --log-file <path> targets the supplied file."""
        log = tmp_path / "custom.jsonl"
        log.write_text('{"type":"user","message":{"content":"hello"}}\n')
        result = _run_script("--log-file", str(log), 'select(.type == "user") | .message.content')
        assert result.returncode == 0, result.stderr
        assert '"hello"' in result.stdout
        # pointer line names the exact overridden path
        assert str(log) in result.stdout

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.7.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_override_without_path_errors(self, fake_home: Path) -> None:
        """PLUG-REQ-004.7.2: --log-file with no value exits non-zero."""
        result = _run_script("--log-file")
        assert result.returncode != 0
        assert result.stderr  # diagnostic message required


# ---------------------------------------------------------------------------
# PLUG-REQ-004.8 / 004.9 / 004.10 / 004.11: Log-File Resolution Chain
# ---------------------------------------------------------------------------


class TestLogFileResolution:
    def _write_jsonl(self, path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Include a unique marker so we can tell which file the script picked.
        path.write_text(
            f'{{"type":"user","message":{{"content":"{value}"}}}}\n',
            encoding="utf-8",
        )

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.8.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_subagent_resolution(self, fake_home: Path) -> None:
        """PLUG-REQ-004.8.1: sub-agent path is preferred when both IDs set."""
        sid = str(uuid.uuid4())
        aid = "abc123def"
        sub = fake_home / sid / "subagents" / f"agent-{aid}.jsonl"
        self._write_jsonl(sub, "SUB")
        top = fake_home / f"{sid}.jsonl"
        self._write_jsonl(top, "TOP")
        result = _run_script(
            ".message.content",
            env_overrides={
                "CLAUDE_CODE_SESSION_ID": sid,
                "CLAUDE_CODE_AGENT_ID": aid,
            },
        )
        assert result.returncode == 0, result.stderr
        assert '"SUB"' in result.stdout
        assert str(sub) in result.stdout
        assert '"TOP"' not in result.stdout

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.8.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_subagent_fallthrough_to_top_level(self, fake_home: Path) -> None:
        """PLUG-REQ-004.8.2: missing sub-agent file falls through to top-level."""
        sid = str(uuid.uuid4())
        aid = "missingagent"
        top = fake_home / f"{sid}.jsonl"
        self._write_jsonl(top, "TOP")
        # Do NOT create the sub-agent file.
        result = _run_script(
            ".message.content",
            env_overrides={
                "CLAUDE_CODE_SESSION_ID": sid,
                "CLAUDE_CODE_AGENT_ID": aid,
            },
        )
        assert result.returncode == 0, result.stderr
        assert '"TOP"' in result.stdout
        assert str(top) in result.stdout

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.9.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_top_level_resolution(self, fake_home: Path) -> None:
        """PLUG-REQ-004.9.1: SESSION_ID alone resolves to top-level path."""
        sid = str(uuid.uuid4())
        top = fake_home / f"{sid}.jsonl"
        self._write_jsonl(top, "TOP")
        result = _run_script(
            ".message.content",
            env_overrides={"CLAUDE_CODE_SESSION_ID": sid},
        )
        assert result.returncode == 0, result.stderr
        assert '"TOP"' in result.stdout
        assert str(top) in result.stdout

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.10.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_fallback_picks_most_recent(self, fake_home: Path) -> None:
        """PLUG-REQ-004.10.1: fallback picks most-recently-modified jsonl."""
        older = fake_home / f"{uuid.uuid4()}.jsonl"
        self._write_jsonl(older, "OLDER")
        newer = fake_home / f"{uuid.uuid4()}.jsonl"
        self._write_jsonl(newer, "NEWER")
        # Force mtimes so `newer` is strictly more recent.
        os.utime(older, (1_000_000, 1_000_000))
        os.utime(newer, (2_000_000, 2_000_000))
        result = _run_script(".message.content")
        assert result.returncode == 0, result.stderr
        assert '"NEWER"' in result.stdout
        assert str(newer) in result.stdout

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.11.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_unresolvable_exits_1(self, fake_home: Path) -> None:
        """PLUG-REQ-004.11.1: nothing to resolve → diagnostic + exit 1."""
        # fake_home's project dir is empty and no env vars are set.
        result = _run_script(".")
        assert result.returncode == 1
        assert "CLAUDE_CODE_SESSION_ID" in result.stderr
        assert "CLAUDE_CODE_AGENT_ID" in result.stderr


# ---------------------------------------------------------------------------
# PLUG-REQ-004.12: Compaction-Summary Filter
# ---------------------------------------------------------------------------


class TestCompactionFilter:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.12.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_compaction_lines_are_dropped(self, fake_home: Path, tmp_path: Path) -> None:
        """PLUG-REQ-004.12.1: isCompactSummary lines are pre-filtered out."""
        log = tmp_path / "compact.jsonl"
        log.write_text(
            '{"type":"user","message":{"content":"keep-me"}}\n'
            '{"type":"user","isCompactSummary":true,"message":{"content":"DROP"}}\n'
            '{"type":"user","message":{"content":"also-keep"}}\n',
            encoding="utf-8",
        )
        # A filter that would match the compaction entry ONLY. If the pre-filter
        # works, this returns zero lines of jq output.
        result = _run_script(
            "--log-file",
            str(log),
            "select(.isCompactSummary == true) | .message.content",
        )
        assert result.returncode == 0, result.stderr
        # jq stdout should have no match lines (pointer line is stripped below)
        jq_lines = [
            ln
            for ln in result.stdout.splitlines()
            if ln.strip() and not ln.startswith(POINTER_LINE_PREFIX)
        ]
        assert jq_lines == []


# ---------------------------------------------------------------------------
# PLUG-REQ-004.13: jq Pass-Through
# ---------------------------------------------------------------------------


class TestJqPassthrough:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.13.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_raw_flag_is_honored(self, fake_home: Path, tmp_path: Path) -> None:
        """PLUG-REQ-004.13.1: jq flags (e.g. -r) pass through verbatim."""
        log = tmp_path / "raw.jsonl"
        log.write_text(
            '{"type":"user","message":{"content":"hello"}}\n',
            encoding="utf-8",
        )
        result = _run_script("--log-file", str(log), "-r", ".message.content")
        assert result.returncode == 0, result.stderr
        # With -r the first line of output is unquoted `hello`, not `"hello"`.
        first = result.stdout.splitlines()[0]
        assert first == "hello"


# ---------------------------------------------------------------------------
# PLUG-REQ-004.14: Exit Code Propagation
# ---------------------------------------------------------------------------


class TestExitCodePropagation:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.14.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_user_jq_error_surfaces(self, fake_home: Path, tmp_path: Path) -> None:
        """PLUG-REQ-004.14.1: user jq's non-zero exit propagates."""
        log = tmp_path / "ok.jsonl"
        log.write_text(
            '{"type":"user","message":{"content":"x"}}\n',
            encoding="utf-8",
        )
        # Malformed jq filter → jq exits 3.
        result = _run_script("--log-file", str(log), "this is not valid jq syntax ###")
        assert result.returncode != 0
        # Pointer line is still emitted (see PLUG-REQ-004.15.2).
        assert "Explore agent" in result.stdout

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.14.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_prefilter_error_does_not_mask_user_jq_success(
        self, fake_home: Path, tmp_path: Path
    ) -> None:
        """PLUG-REQ-004.14.2: malformed JSON in the transcript doesn't flip exit."""
        log = tmp_path / "malformed.jsonl"
        # The second line is malformed JSON — jq -c of the pre-filter will
        # exit non-zero when it hits this line. The user's jq (.) on the
        # preceding good line should still succeed and set exit 0.
        log.write_text(
            '{"type":"user","message":{"content":"good"}}\nthis is not json\n',
            encoding="utf-8",
        )
        result = _run_script("--log-file", str(log), ".message.content")
        assert result.returncode == 0, result.stderr
        assert '"good"' in result.stdout


# ---------------------------------------------------------------------------
# PLUG-REQ-004.15: Trailing Pointer Line
# ---------------------------------------------------------------------------


class TestTrailingPointerLine:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.15.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_pointer_line_on_match(self, fake_home: Path, tmp_path: Path) -> None:
        """PLUG-REQ-004.15.1: pointer line names the resolved log file path."""
        log = tmp_path / "ptr.jsonl"
        log.write_text(
            '{"type":"user","message":{"content":"hi"}}\n',
            encoding="utf-8",
        )
        result = _run_script("--log-file", str(log), ".type")
        assert result.returncode == 0, result.stderr
        assert f"{POINTER_LINE_PREFIX} {log}" in result.stdout

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.15.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_pointer_line_on_empty_match(self, fake_home: Path, tmp_path: Path) -> None:
        """PLUG-REQ-004.15.2: pointer line is printed even when jq returns nothing."""
        log = tmp_path / "empty.jsonl"
        log.write_text(
            '{"type":"user","message":{"content":"hi"}}\n',
            encoding="utf-8",
        )
        result = _run_script("--log-file", str(log), 'select(.type == "never_matches")')
        assert result.returncode == 0, result.stderr
        assert str(log) in result.stdout
        assert "Explore agent" in result.stdout


# ---------------------------------------------------------------------------
# PLUG-REQ-004.16: Skill Location and Frontmatter
# ---------------------------------------------------------------------------


class TestSkillFrontmatter:
    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.16.1).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skill_exists(self) -> None:
        """PLUG-REQ-004.16.1: SKILL.md exists at the expected path."""
        assert SKILL_PATH.is_file()

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.16.2).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skill_name_matches_directory(self) -> None:
        """PLUG-REQ-004.16.2: frontmatter name matches directory name."""
        fm = _parse_yaml_frontmatter(SKILL_PATH)
        assert fm["name"] == "search_conversation"

    # THIS TEST VALIDATES A HARD REQUIREMENT (PLUG-REQ-004.16.3).
    # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
    def test_skill_description_non_empty(self) -> None:
        """PLUG-REQ-004.16.3: frontmatter has a non-empty description."""
        fm = _parse_yaml_frontmatter(SKILL_PATH)
        assert isinstance(fm["description"], str)
        assert fm["description"].strip()
