# Changelog

All notable changes to DeepWork will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-10

### Added

#### Core Functionality
- Job definition parser with JSON Schema validation
- Job registry for tracking installed workflows
- Multi-platform support (Claude Code, Google Gemini, GitHub Copilot)
- Platform auto-detection
- Git integration utilities (branch management, uncommitted changes detection)
- Jinja2-based skill file generation
- YAML configuration management
- Filesystem utilities with safe operations

#### CLI
- `deepwork install` command with platform selection
- `--platform` option for explicit platform choice
- `--path` option for specifying project directory
- Rich terminal output with progress indicators
- Auto-detection of AI platforms when not specified
- Comprehensive error messages and user guidance

#### Templates
- `skill-job-step.md.jinja` - Individual step skill template
- `skill-deepwork.define.md.jinja` - Job definition wizard
- `skill-deepwork.refine.md.jinja` - Job refinement tool

#### Testing
- 147 unit tests across all modules
- 19 integration tests for full workflows
- Test fixtures for simple and complex jobs
- 100% coverage of critical paths

#### Documentation
- Complete architecture specification
- Template design review document
- Implementation status tracking
- Quick start guide
- Development setup instructions

### Technical Details

**Modules Implemented:**
- `src/deepwork/cli/` - Command-line interface
- `src/deepwork/core/parser.py` - Job definition parsing (243 lines, 23 tests)
- `src/deepwork/core/registry.py` - Job registry (222 lines, 19 tests)
- `src/deepwork/core/detector.py` - Platform detection (128 lines, 14 tests)
- `src/deepwork/core/generator.py` - Skill generation (243 lines, 13 tests)
- `src/deepwork/schemas/job_schema.py` - JSON Schema (137 lines, 10 tests)
- `src/deepwork/utils/fs.py` - Filesystem utilities (134 lines, 23 tests)
- `src/deepwork/utils/git.py` - Git operations (157 lines, 25 tests)
- `src/deepwork/utils/yaml_utils.py` - YAML utilities (82 lines, 20 tests)
- `src/deepwork/utils/validation.py` - Schema validation (31 lines)

**Dependencies:**
- Python 3.11+
- Jinja2 >= 3.1.0
- PyYAML >= 6.0
- GitPython >= 3.1.0
- click >= 8.1.0
- rich >= 13.0.0
- jsonschema >= 4.17.0

### Features

#### Job Definition
- Declarative YAML format for job definitions
- JSON Schema validation with clear error messages
- Circular dependency detection using topological sort
- Support for user parameter inputs
- Support for file inputs from previous steps
- Step dependency management
- Multiple output files per step

#### Skill Generation
- Context-aware skill generation from templates
- Embedded step instructions
- Prerequisites section for dependent steps
- Work branch management guidance
- Next step recommendations
- Platform-specific skill formatting

#### Git Integration
- Work branch format: `work/[job_name]-[instance]-[date]`
- Git repository detection
- Uncommitted changes detection
- Branch existence checking
- Work directory organization

#### Platform Support
- Claude Code (.claude/ directory)
- Google Gemini (.gemini/ directory)
- GitHub Copilot (.github/ directory)
- Auto-detection of available platforms
- Platform-specific skill prefixes and extensions

### Known Limitations

- No runtime job execution tracking (planned for Phase 2)
- No automatic skill invocation (planned for Phase 2)
- No progress visualization (planned for Phase 2)
- Templates only for Claude Code (Gemini and Copilot use same templates currently)

### Breaking Changes

None - this is the initial release.

[0.1.0]: https://github.com/anthropics/deepwork/releases/tag/v0.1.0
