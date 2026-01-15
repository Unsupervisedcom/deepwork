# Changelog

All notable changes to DeepWork will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-15

### Added
- New `learn` step in deepwork_jobs for analyzing existing workflows
- Version and changelog update policy to enforce version tracking on src changes
- Supplemental file references support in job definitions
- Policy schema enhancements with new validation options

### Changed
- Reorganized CLA files into versioned directory structure
- Improved policy evaluation hooks with better change detection
- Renamed `capture_work_tree.sh` to `capture_prompt_work_tree.sh` for clarity
- Updated deepwork_jobs step instructions for better guidance

### Removed
- Deprecated `refine` step (replaced by `learn`)
- Removed `get_changed_files.sh` hook (functionality moved to policy evaluator)
- Removed CLA_SETUP.md (setup instructions moved to main docs)

## [0.1.0] - Initial Release

Initial version.

[0.1.1]: https://github.com/anthropics/deepwork/releases/tag/v0.1.1
[0.1.0]: https://github.com/anthropics/deepwork/releases/tag/v0.1.0
