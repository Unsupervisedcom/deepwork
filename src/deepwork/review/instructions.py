"""Review instruction file generation.

Generates self-contained markdown instruction files for review agents.
Each file contains the review instructions, files to examine, and any
additional context. Written to .deepwork/tmp/review_instructions/.
"""

import hashlib
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from deepwork.review.config import ReferenceFile, ReviewTask
from deepwork.utils.fs import safe_write

INSTRUCTIONS_DIR = ".deepwork/tmp/review_instructions"

# Caps on inlined reference file content to keep review prompts tractable.
MAX_INLINE_FILES = 20
MAX_INLINE_TOTAL_BYTES = 256 * 1024

_FENCE_LANG_BY_EXT = {
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".sh": "bash",
    ".toml": "toml",
}

_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9\-_.]")


def compute_review_id(task: ReviewTask, project_root: Path) -> str:
    """Build a deterministic review ID encoding rule, paths, and content hash.

    Format: ``{sanitized_rule}--{sanitized_paths}--{content_hash_12}``.

    For tasks with ``inline_content`` (type: string outputs), the paths
    component is the literal ``"inline"`` and the content hash is derived
    from the inline string value.

    Args:
        task: The ReviewTask to compute an ID for.
        project_root: Absolute path to the project root.

    Returns:
        A deterministic, human-readable review ID string.
    """
    rule_part = _sanitize_for_id(task.rule_name)
    paths_part = _paths_component(task.files_to_review)
    hash_part = _content_hash(task.files_to_review, project_root, task.inline_content)
    return f"{rule_part}--{paths_part}--{hash_part}"


def _sanitize_for_id(name: str) -> str:
    """Replace non-alphanumeric chars (except ``-``, ``_``, ``.``) with ``-``."""
    return _SANITIZE_RE.sub("-", name)


def _paths_component(files: list[str]) -> str:
    """Build the file-paths segment of a review ID.

    Each path has ``/`` replaced with ``-``.  Multiple paths are sorted
    alphabetically, then joined with ``_AND_``.  If the result exceeds
    100 characters, falls back to ``{N}_files``.  When ``files`` is
    empty (inline-content tasks), returns the literal ``"inline"``.
    """
    if not files:
        return "inline"
    sanitized = sorted(f.replace("/", "-") for f in files)
    joined = "_AND_".join(sanitized)
    if len(joined) > 100:
        return f"{len(files)}_files"
    return joined


def _content_hash(files: list[str], project_root: Path, inline_content: str | None = None) -> str:
    """SHA-256 content hash (first 12 hex chars) of the task content.

    Files are sorted alphabetically before concatenation.  Files that
    cannot be read contribute the placeholder ``MISSING``.  When
    ``inline_content`` is provided, it is mixed into the hash (via a
    sentinel marker) so that each distinct string value produces a
    distinct review ID.

    ``files`` entries are expected to be repo-root-relative paths sourced
    from trusted ``.deepreview`` config files.  Absolute paths or ``..``
    segments are not validated here; callers MUST ensure paths stay
    inside ``project_root``.
    """
    h = hashlib.sha256()
    for filepath in sorted(files):
        try:
            content = (project_root / filepath).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            content = "MISSING"
        h.update(content.encode("utf-8"))
    if inline_content is not None:
        h.update(b"\x00INLINE\x00")
        h.update(inline_content.encode("utf-8"))
    return h.hexdigest()[:12]


PRECOMPUTE_TIMEOUT_SECONDS = 60


def _run_precompute_command(command: str, project_root: Path) -> str:
    """Run a single precompute bash command and return its stdout.

    Precompute commands are fully trusted input sourced from the repo's own
    ``.deepreview`` files; they run via ``shell=True`` and MUST NOT be fed
    any untrusted external data (e.g., user-supplied strings interpolated
    into the command).

    Args:
        command: Shell command string to execute. The first path component
            has been resolved to an absolute path by the caller; the rest
            of the command is passed through to the shell verbatim.
        project_root: Working directory for command execution.

    Returns:
        Command stdout on success, or an error message on failure.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=PRECOMPUTE_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            return (
                f"**Precompute command failed** (exit code {result.returncode}):\n"
                f"```\n{result.stderr.strip()}\n```"
            )
        return result.stdout
    except subprocess.TimeoutExpired:
        return f"**Precompute command timed out** after {PRECOMPUTE_TIMEOUT_SECONDS}s:\n`{command}`"
    except OSError as e:
        return f"**Precompute command error**: {e}"


def _run_precompute_commands(commands: set[str], project_root: Path) -> dict[str, str]:
    """Run multiple precompute commands in parallel.

    Args:
        commands: Set of unique command strings to execute.
        project_root: Working directory for command execution.

    Returns:
        Dict mapping command string to its stdout or error message.
    """
    if not commands:
        return {}

    # Cap concurrent precompute shells so a repo with many rules does not
    # briefly fork dozens of subprocesses at once on CI runners.
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_run_precompute_command, cmd, project_root): cmd for cmd in commands
        }
        for future in as_completed(futures):
            cmd = futures[future]
            results[cmd] = future.result()

    return results


def write_instruction_files(
    tasks: list[ReviewTask],
    project_root: Path,
) -> list[tuple[ReviewTask, Path]]:
    """Write instruction files for all review tasks.

    Clears any existing ``.md`` instruction files (preserving ``.passed``
    marker files), then generates a new file for each task that does not
    already have a ``.passed`` marker.

    Args:
        tasks: List of ReviewTask objects to generate files for.
        project_root: Absolute path to the project root.

    Returns:
        List of (ReviewTask, instruction_file_path) tuples for tasks that
        were *not* skipped.
    """
    instructions_dir = project_root / INSTRUCTIONS_DIR

    # Clear stale .md instruction files (preserve .passed markers and their .md files)
    if instructions_dir.exists():
        for child in instructions_dir.iterdir():
            if child.suffix == ".md":
                passed_marker = child.with_suffix(".passed")
                if not passed_marker.exists():
                    child.unlink()
            elif child.suffix == ".txt":
                child.unlink()
    instructions_dir.mkdir(parents=True, exist_ok=True)

    # Run all precompute commands in parallel before building files
    unique_commands = {
        task.precomputed_info_bash_command
        for task in tasks
        if task.precomputed_info_bash_command is not None
    }
    precompute_results = _run_precompute_commands(unique_commands, project_root)

    results: list[tuple[ReviewTask, Path]] = []

    for task in tasks:
        review_id = compute_review_id(task, project_root)

        # Skip if a .passed marker exists for this exact review_id
        passed_marker = instructions_dir / f"{review_id}.passed"
        if passed_marker.exists():
            continue

        # Direct key access (not .get()): the invariant below enforces that
        # every non-None command produced unique_commands above MUST have a
        # result in precompute_results — a missing key indicates drift.
        precomputed_info = (
            precompute_results[task.precomputed_info_bash_command]
            if task.precomputed_info_bash_command is not None
            else None
        )
        content = build_instruction_file(task, review_id, precomputed_info, project_root)
        file_path = instructions_dir / f"{review_id}.md"
        alias_path = instructions_dir / short_instruction_filename(review_id)

        safe_write(file_path, content)
        safe_write(alias_path, content)
        results.append((task, file_path))

    return results


def short_instruction_filename(review_id: str) -> str:
    """Build a short deterministic filename for OpenClaw review prompts."""
    digest = hashlib.sha256(review_id.encode("utf-8")).hexdigest()[:10]
    return f"r-{digest}.txt"


def build_instruction_file(
    task: ReviewTask,
    review_id: str = "",
    precomputed_info: str | None = None,
    project_root: Path | None = None,
) -> str:
    """Build the markdown content for a single review instruction file.

    Args:
        task: The ReviewTask to generate instructions for.
        review_id: The deterministic review ID for this task (used in the
            "After Review" section).
        precomputed_info: Pre-executed command output to include as context.
        project_root: Absolute path to the project root that all relative
            file paths in this instruction file resolve against. When
            provided, the file includes an explicit "Project Root"
            directive so the reviewer agent reads files from the correct
            working tree even when its cwd differs (e.g., in a git
            worktree dispatched from the main checkout).

    Returns:
        Markdown string containing the complete review instructions.
    """
    parts: list[str] = []

    # Header
    scope = _describe_scope(task)
    parts.append(f"# Review: {task.rule_name} — {scope}\n")

    # Project root directive — tells the reviewer where to read files from.
    # Critical in git-worktree setups where the agent's cwd may differ from
    # the worktree the commits actually live in.
    if project_root is not None:
        abs_root = project_root.resolve()
        parts.append("## Project Root\n")
        parts.append(
            f"**All file paths in this document are relative to `{abs_root}`.** "
            "When reading any file below with the Read tool, you MUST construct "
            "the absolute path by prepending this project root. Do NOT read files "
            "relative to your current working directory — it may differ from the "
            "project root (e.g., when this review runs against a git worktree)."
        )
        parts.append("")

    # Review instructions
    parts.append("## Review Instructions\n")
    parts.append(task.instructions.strip())
    parts.append("")

    # Relevant file contents — inlined for reviewer context (subject to caps)
    if task.reference_files:
        parts.append("## Relevant File Contents\n")
        parts.append(_build_reference_files_section(task.reference_files))
        parts.append("")

    # Files to review (omitted for inline-content tasks with no files).
    # NOTE: The @filepath references below are NOT auto-expanded when the
    # instruction file is consumed by the reviewing agent.  They are path
    # pointers — the agent must Read each file itself.  Any content that
    # the reviewer needs without a round-trip should go in reference_files
    # (rendered in "Relevant File Contents" above).
    if task.files_to_review:
        parts.append("## Files to Review\n")
        for filepath in task.files_to_review:
            parts.append(f"- @{filepath}")
        parts.append("")

    # Inline content to review (for type: string outputs)
    if task.inline_content is not None:
        parts.append("## Content to Review\n")
        parts.append(task.inline_content.rstrip())
        parts.append("")

    # Additional context: unchanged matching files
    if task.additional_files:
        parts.append("## Unchanged Matching Files\n")
        parts.append(
            "These files match the review patterns but were not changed. "
            "They are provided for context.\n"
        )
        for filepath in task.additional_files:
            parts.append(f"- @{filepath}")
        parts.append("")

    # Additional context: all changed filenames
    if task.all_changed_filenames:
        parts.append("## All Changed Files\n")
        parts.append(
            "The following files were changed in this changeset "
            "(listed for context, not all are subject to this review).\n"
        )
        for filepath in task.all_changed_filenames:
            parts.append(f"- {filepath}")
        parts.append("")

    # Precomputed context (at the end, after all file sections)
    if precomputed_info is not None:
        parts.append("## Precomputed Context\n")
        parts.append(precomputed_info.rstrip())
        parts.append("")

    # After Review: instruct agent to mark review as passed
    if review_id:
        parts.append("## After Review\n")
        parts.append(
            "If this review passes with no findings, or if all findings have been "
            "addressed or explicitly dismissed, call the `mark_review_as_passed` tool with:\n"
        )
        parts.append(f'- `review_id`: `"{review_id}"`')
        parts.append("")

    # Traceability: link back to the source policy
    if task.source_location:
        parts.append("---\n")
        parts.append(f"This review was requested by the policy at `{task.source_location}`.")
        parts.append("")

    return "\n".join(parts)


def _build_reference_files_section(reference_files: list[ReferenceFile]) -> str:
    """Build a markdown section inlining reference file contents.

    Reads each file in order and emits a `### {label}` subsection with an
    optional description and a fenced code block. Honors ``MAX_INLINE_FILES``
    and ``MAX_INLINE_TOTAL_BYTES`` — once either cap is hit, remaining
    entries are summarized in an "omitted" line rather than inlined.

    Files that cannot be read produce a graceful marker but do not abort the
    section (and their would-be bytes do not count toward the budget).
    """
    parts: list[str] = []
    total_bytes = 0
    inlined_count = 0
    omitted: list[str] = []

    for ref in reference_files:
        if inlined_count >= MAX_INLINE_FILES or total_bytes >= MAX_INLINE_TOTAL_BYTES:
            omitted.append(ref.relative_label)
            continue

        header = f"### {ref.relative_label}"
        if ref.description:
            header += f"\n\n{ref.description.strip()}"

        try:
            content = ref.path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            parts.append(header)
            parts.append(f"\n\n(could not inline {ref.relative_label}: {e})\n")
            continue

        lang = _FENCE_LANG_BY_EXT.get(ref.path.suffix.lower(), "text")
        remaining = MAX_INLINE_TOTAL_BYTES - total_bytes
        truncated_marker = ""
        content_bytes = content.encode("utf-8")
        original_byte_len = len(content_bytes)
        if original_byte_len > remaining:
            # Truncate at a character boundary near the byte budget.
            content = content_bytes[:remaining].decode("utf-8", errors="ignore")
            truncated_marker = (
                f"\n... (truncated: file is {original_byte_len} bytes, budget left was {remaining})"
            )
            consumed = remaining
        else:
            consumed = original_byte_len

        parts.append(header)
        parts.append(f"\n\n```{lang}\n{content}{truncated_marker}\n```\n")
        total_bytes += consumed
        inlined_count += 1

    if omitted:
        omitted_list = ", ".join(omitted)
        parts.append(
            f"\n_({len(omitted)} more reference file(s) omitted due to size/count caps: "
            f"{omitted_list})_\n"
        )

    return "".join(parts)


def _describe_scope(task: ReviewTask) -> str:
    """Generate a human-readable scope description for the task.

    Args:
        task: The ReviewTask to describe.

    Returns:
        Scope description string.
    """
    if not task.files_to_review and task.inline_content is not None:
        return "inline content"
    if len(task.files_to_review) == 1:
        return task.files_to_review[0]
    return f"{len(task.files_to_review)} files"
