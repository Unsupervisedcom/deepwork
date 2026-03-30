# Engineer Job: RFC 2119 Requirements Specification

This specification defines the normative requirements for the engineer job's
`implement`, `doctor`, and `requirements` workflows. The term "engineer" refers
to the agent or human executing the workflow.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in RFC 2119.

Note: All general version control operations SHALL adhere to the current
established repository standards, beyond the explicit strictures defined below.

## Implement workflow requirements

## 1. Product and engineering issue delineation

The workflow MUST initiate with a high-level Product Issue containing the
overarching user story and functional RFC 2119 requirements.

An engineer MUST translate this Product Issue into a distinct Engineering Issue.

The Engineering Issue MUST include the following payloads: the definitive
implementation plan, applicable design artifacts (e.g., architecture diagrams,
data models, schematics, or domain-equivalent artifacts as defined in
`common_job_info`), and explicit definitions of expected red and green test
states.

## 2. Version control initialization

A dedicated Git worktree or branch MUST be created specifically for the
Engineering Issue.

The engineer SHALL commit the newly required specifications into the branch
prior to executing implementation code.

A Pull Request (PR) MUST be opened in a draft state immediately following the
specification commit, strictly utilizing the repository's standardized PR
template.

## 3. Test-driven execution and verification

The engineer MUST either implement new failing (red) tests or explicitly verify
current existing tests against the new requirements.

Each test MUST explicitly reference a specific requirement defined in the
Engineering Issue.

The engineer SHALL implement the necessary logic, hardware parameters, or
configuration changes to transition the test suite to a passing (green) state.

## 4. Continuous state synchronization

The engineer MUST keep the PR checkboxes strictly synchronized with the state of
the active worktree.

Checkboxes MUST be updated to reflect completion immediately as tasks are
finished and pushed to the remote branch.

## 5. Artifact generation and continuous integration

The engineer MUST verify that the CI system produces visual artifacts appropriate
to the domain (as listed in `common_job_info`) upon a successful green state. If
the CI system does not produce the expected artifacts, the engineer MUST document
the gap and manually capture equivalents.

## 6. Pull request finalization and handoff

The `## Demo` section of the PR MUST display the automatically generated visual
artifacts to facilitate asynchronous review.

If the implementation unblocks downstream work or requires specific
staging/production verification, the engineer MUST document this in a formal
comment or within the `## Handoff` section of the PR.

The PR SHALL NOT be merged until peer review validates the visual artifacts and
verifies that all synchronized task checkboxes are complete.

## 7. Product synchronization

Upon the successful merge of the PR and closure of the Engineering Issue, the
engineer MUST author a formal comment on the parent Product Issue.

This comment MUST document the high-level user stories completed and provide
explicit links using the PR's permanent numeric URL (e.g.,
`https://github.com/org/repo/pull/123`) to the merged PR(s) and closed
Engineering Issue(s), ensuring product managers maintain up-to-date visibility
without parsing engineering telemetry.

## Doctor workflow requirements

## 8. Contextual awareness and the doctor workflow

To maintain a project-agnostic shared workflow, every repository MUST contain an
AGENTS.md file (or equivalent domain documentation).

This documentation MUST explicitly define the project's engineering domain (e.g.,
AnchorCAD, web application, PCB layout) and instruct the automated agents on how
to parse, build, and test the repository.

A separate doctor workflow MUST exist and be executed to validate that the
AGENTS.md and related context files are present, correctly linked, and
syntactically valid, ensuring the automation agent knows how to interact with the
repository's specific medium.

## Requirements workflow requirements

## 9. Requirements directory and discovery

Every project using the requirements workflow MUST store requirement files in a
dedicated directory. The default path SHALL be `./requirements/` relative to the
repository root.

If a project uses a non-default path, the path MUST be documented in the
project's agent context file (`AGENTS.md` or equivalent) under a
`## Requirements` section so that DeepWork can locate it without conflict.

The workflow MUST scan existing `REQ-*.md` files and the `REQUIREMENTS.md` index
before creating or modifying any requirement.

## 10. Requirement file format

Each requirement file MUST be named `REQ-NNN-slug.md` where `NNN` is a
zero-padded sequential number and `slug` is a lowercase hyphenated summary.

Each file MUST begin with a heading `# REQ-NNN: Title` followed by a brief
description and the RFC 2119 key words declaration paragraph.

Sub-requirements MUST be numbered `REQ-NNN.X` starting at 1 and MUST each
contain at least one RFC 2119 keyword (`MUST`, `MUST NOT`, `SHALL`,
`SHALL NOT`, `SHOULD`, `SHOULD NOT`, `MAY`, `REQUIRED`, `OPTIONAL`) in
uppercase.

Every sub-requirement MUST describe a verifiable behavior that can be validated
by an automated test or a DeepWork review rule.

## 11. Requirements index

A `REQUIREMENTS.md` file MUST exist in the requirements directory and serve as
the index of all requirement files.

The index MUST be a Markdown table with columns `ID`, `Title`, and `File`
linking to each `REQ-*.md` file.

Every `REQ-*.md` file in the directory MUST have a corresponding row in the
index. The index MUST NOT reference files that do not exist.

## 12. Amending requirements

When amending an existing requirement, the engineer MUST preserve existing
sub-requirement numbers. New sub-requirements SHALL be appended to the end of
the existing list rather than renumbered, unless the user explicitly requests
renumbering.

Amendments MUST NOT silently remove or weaken existing sub-requirements. Any
removal or weakening of a requirement MUST be explicitly noted in the commit
message.
