# Changelog

All notable changes to DeepWork will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-01-18

### Fixed
- Command rule errors now include promise skip instructions with the exact rule name
  - Previously, failed command rules only showed "Command failed" with no guidance
  - Now each failed rule shows: `To skip, include <promise>Rule Name</promise> in your response`
  - This allows agents to understand how to proceed when a command rule fails

## [0.4.0] - 2026-01-16

### Added
- Rules system v2 with frontmatter markdown format in `.deepwork/rules/`
  - Detection modes: trigger/safety (default), set (bidirectional), pair (directional)
  - Action types: prompt (show instructions), command (run idempotent commands)
  - Variable pattern matching with `{path}` (multi-segment) and `{name}` (single-segment)
  - Queue system in `.deepwork/tmp/rules/queue/` for state tracking and deduplication
- New core modules:
  - `pattern_matcher.py`: Variable pattern matching with regex-based capture
  - `rules_queue.py`: Queue system for rule state persistence
  - `command_executor.py`: Command action execution with variable substitution
- Updated `rules_check.py` hook to use v2 system with queue-based deduplication

### Changed
- Documentation updated with v2 rules examples and configuration

### Removed
- v1 rules format (`.deepwork.rules.yml`) - now only v2 frontmatter markdown format is supported

## [0.3.0] - 2026-01-16

### Added
- Cross-platform hook wrapper system for writing hooks once and running on multiple platforms
  - `wrapper.py`: Normalizes input/output between Claude Code and Gemini CLI
  - `claude_hook.sh` and `gemini_hook.sh`: Platform-specific shell wrappers
  - `rules_check.py`: Cross-platform rule evaluation hook
- Platform documentation in `doc/platforms/` with hook references and learnings
- Claude Code platform documentation (`doc/platforms/claude/`)
- `update.job` for maintaining standard jobs (#41)
- `make_new_job.sh` script and templates directory for job scaffolding (#37)
- Default rules template file created during `deepwork install` (#42)
- Full e2e test suite: define → implement → execute workflow (#45)
- Automated tests for all shell scripts and hook wrappers (#40)

### Changed
- Standardized on "ask structured questions" phrasing across all jobs (#48)
- deepwork_jobs bumped to v0.5.0, deepwork_rules to v0.2.0

### Fixed
- Stop hooks now properly return blocking JSON (#38)
- Various CI workflow fixes (#35, #46, #47, #51, #52)

## [0.1.1] - 2026-01-15

### Added
- `compare_to` option in rules system for flexible change detection (#34)
  - `base` (default): Compare to merge-base with default branch
  - `default_tip`: Two-dot diff against default branch tip
  - `prompt`: Compare to state captured at prompt submission
- New `learn` command replacing `refine` for conversation-driven job improvement (#27)
  - Analyzes conversations where DeepWork jobs were run
  - Classifies learnings as generalizable (→ instructions) or bespoke (→ AGENTS.md)
  - Creates learning_summary.md documenting all changes
- "Think deeply" prompt in learn step for enhanced reasoning (#33)
- Supplementary markdown file support for job steps (#19)
- Browser automation capability consideration in job definition (#32)
- Platform-specific reload instructions in adapters (#31)
- Version and changelog update rule to enforce version tracking on src changes
- Added claude and copilot to CLA allowlist (#26)

### Changed
- Moved git diff logic into evaluate_rules.py for per-rule handling (#34)
- Renamed `capture_work_tree.sh` to `capture_prompt_work_tree.sh` (#34)
- Updated README with PyPI install instructions using pipx, uv, and pip (#22)
- Updated deepwork_jobs job version to 0.2.0

### Fixed
- Stop hooks now correctly return blocking JSON when rules fire
- Added shell script tests to verify stop hook blocking behavior

### Removed
- `refine` step (replaced by `learn` command) (#27)
- `get_changed_files.sh` hook (logic moved to Python rule evaluator) (#34)

## [0.1.0] - Initial Release

Initial version.

[0.4.1]: https://github.com/anthropics/deepwork/releases/tag/0.4.1
[0.4.0]: https://github.com/anthropics/deepwork/releases/tag/0.4.0
[0.3.0]: https://github.com/anthropics/deepwork/releases/tag/0.3.0
[0.1.1]: https://github.com/anthropics/deepwork/releases/tag/0.1.1
[0.1.0]: https://github.com/anthropics/deepwork/releases/tag/0.1.0
