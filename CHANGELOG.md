# Changelog

All notable changes to DeepWork will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-01-21

### Fixed
- Stop hook prompt validation now uses correct JSON format recognized by Claude Code
  - Changed from `{"ok": true}` / `{"ok": false, "reason": "..."}` to `{}` / `{"decision": "block", "reason": "..."}`
  - This fixes quality criteria validation not properly blocking agent completion

### Changed
- Updated skill template best practices rule with stop hook response format guidance
- Updated Claude Code hooks documentation with correct JSON format examples

## [0.5.0] - 2026-01-20

### Changed
- **BREAKING**: Renamed `document_type` to `doc_spec` throughout the codebase
  - Job.yml field: `document_type` → `doc_spec` (e.g., `outputs: [{file: "report.md", doc_spec: ".deepwork/doc_specs/report.md"}]`)
  - Class: `DocumentTypeDefinition` → `DocSpec` (backward compat alias provided)
  - Methods: `has_document_type()` → `has_doc_spec()`, `validate_document_type_references()` → `validate_doc_spec_references()`
  - Template variables: `has_document_type` → `has_doc_spec`, `document_type` → `doc_spec`
  - Internal: `_load_document_type()` → `_load_doc_spec()`, `_doc_type_cache` → `_doc_spec_cache`

### Added
- Comprehensive tests for generator doc spec integration (9 new tests)
  - `test_load_doc_spec_returns_parsed_spec` - Verifies doc spec loading
  - `test_load_doc_spec_caches_result` - Verifies caching behavior
  - `test_load_doc_spec_returns_none_for_missing_file` - Graceful handling of missing files
  - `test_generate_step_skill_with_doc_spec` - End-to-end skill generation with doc spec
  - `test_build_step_context_includes_doc_spec_info` - Context building verification

### Migration Guide
- Update job.yml files: Change `document_type:` to `doc_spec:` in output definitions
- Update any code importing `DocumentTypeDefinition`: Use `DocSpec` instead (alias still works)
- Run `deepwork install` to regenerate skills with updated terminology

## [0.4.0] - 2026-01-20

### Added
- Doc specs (document specifications) as a first-class feature for formalizing document quality criteria
  - New `src/deepwork/schemas/doc_spec_schema.py` with JSON schema validation
  - New `src/deepwork/core/doc_spec_parser.py` with parser for frontmatter markdown doc spec files
  - Doc spec files stored in `.deepwork/doc_specs/` directory with quality criteria and example documents
  - Auto-creates `.deepwork/doc_specs/` directory during `deepwork install`
- Extended job.yml output schema to support doc spec references
  - Outputs can now be strings (backward compatible) or objects with `file` and optional `doc_spec` fields
  - Example: `outputs: [{file: "report.md", doc_spec: ".deepwork/doc_specs/monthly_report.md"}]`
  - The `doc_spec` uses the full path to the doc spec file, making references self-documenting
- Doc spec-aware skill generation
  - Step skills now include doc spec quality criteria, target audience, and example documents
  - Both Claude and Gemini templates updated for doc spec rendering
- Document detection workflow in `deepwork_jobs.define`
  - Steps 1.5, 1.6, 1.7 guide users through creating doc specs for document-oriented jobs
  - Pattern indicators: "report", "summary", "create", "monthly", "for stakeholders"
- Doc spec improvement workflow in `deepwork_jobs.learn`
  - Steps 3.5, 4.5 capture doc spec-related learnings and update doc spec files
- New `OutputSpec` dataclass in parser for structured output handling
- Comprehensive doc spec documentation in `doc/doc-specs.md`
- New test fixtures for doc spec validation and parsing

### Changed
- `Step.outputs` changed from `list[str]` to `list[OutputSpec]` for richer output metadata
- `SkillGenerator.generate_all_skills()` now accepts `project_root` parameter for doc spec loading
- Updated `deepwork_jobs` to v0.6.0 with doc spec-related quality criteria

## [0.3.1] - 2026-01-20

### Added
- `created` rule mode for matching only newly created files (#76)
  - Rules with `mode: created` only fire when files are first added, not on modifications
  - Useful for enforcing patterns on new files without triggering on existing file edits

### Fixed
- Fixed `created` mode rules incorrectly firing on modified files (#83)
- Fixed `compare_to: prompt` mode not detecting files that were committed during agent response
  - Rules like `uv-lock-sync` now correctly fire even when changes are committed before the Stop hook runs

## [0.3.0] - 2026-01-18

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
- **BREAKING**: Refactored "commands" terminology to "skills" throughout the codebase
  - Directory structure changed from `.claude/commands/` to `.claude/skills/`
  - Directory structure changed from `.gemini/commands/` to `.gemini/skills/`
  - Class renamed: `CommandGenerator` → `SkillGenerator`
  - Enum renamed: `CommandLifecycleHook` → `SkillLifecycleHook`
  - Class attributes renamed: `commands_dir` → `skills_dir`, `command_template` → `skill_template`
  - Methods renamed: `get_commands_dir()` → `get_skills_dir()`, `generate_all_commands()` → `generate_all_skills()`, etc.
  - Template files renamed: `command-job-step.md.jinja` → `skill-job-step.md.jinja`, etc.
- **BREAKING**: Removed `uw.` prefix convention for hidden steps
  - Step skills now use clean filenames (e.g., `job_name.step_id.md` instead of `uw.job_name.step_id.md`)
  - Hidden steps use `user-invocable: false` in YAML frontmatter instead
  - The `exposed` field in job.yml now controls the `user-invocable` frontmatter setting
- CLI output messages updated to use "skills" terminology
- Standardized on "ask structured questions" phrasing across all jobs (#48)
- deepwork_jobs bumped to v0.5.0, deepwork_rules to v0.2.0
- Documentation updated with v2 rules examples and configuration

### Fixed
- Stop hooks now properly return blocking JSON (#38)
- Various CI workflow fixes (#35, #46, #47, #51, #52)
- Command rule errors now include promise skip instructions with the exact rule name
  - Previously, failed command rules only showed "Command failed" with no guidance
  - Now each failed rule shows: `To skip, include <promise>Rule Name</promise> in your response`
  - This allows agents to understand how to proceed when a command rule fails

### Removed
- v1 rules format (`.deepwork.rules.yml`) - now only v2 frontmatter markdown format is supported

### Migration Guide
- Run `deepwork install --platform claude` to regenerate skills in the new location
- Remove old `.claude/commands/` and `.gemini/commands/` directories manually
- Update any custom code that imports `CommandGenerator` or `CommandLifecycleHook`

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

[0.5.1]: https://github.com/anthropics/deepwork/releases/tag/0.5.1
[0.5.0]: https://github.com/anthropics/deepwork/releases/tag/0.5.0
[0.4.0]: https://github.com/anthropics/deepwork/releases/tag/0.4.0
[0.3.1]: https://github.com/anthropics/deepwork/releases/tag/0.3.1
[0.3.0]: https://github.com/anthropics/deepwork/releases/tag/0.3.0
[0.1.1]: https://github.com/anthropics/deepwork/releases/tag/0.1.1
[0.1.0]: https://github.com/anthropics/deepwork/releases/tag/0.1.0
