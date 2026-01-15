# Changelog

All notable changes to DeepWork will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-15

### Added
- `compare_to` option in policy system for flexible change detection (#34)
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
- Version and changelog update policy to enforce version tracking on src changes
- Added claude and copilot to CLA allowlist (#26)

### Changed
- Moved git diff logic into evaluate_policies.py for per-policy handling (#34)
- Renamed `capture_work_tree.sh` to `capture_prompt_work_tree.sh` (#34)
- Updated README with PyPI install instructions using pipx, uv, and pip (#22)
- Updated deepwork_jobs job version to 0.2.0

### Fixed
- Stop hooks now correctly return blocking JSON when policies fire
- Added shell script tests to verify stop hook blocking behavior

### Removed
- `refine` step (replaced by `learn` command) (#27)
- `get_changed_files.sh` hook (logic moved to Python policy evaluator) (#34)

## [0.1.0] - Initial Release

Initial version.

[0.1.1]: https://github.com/anthropics/deepwork/releases/tag/v0.1.1
[0.1.0]: https://github.com/anthropics/deepwork/releases/tag/v0.1.0
