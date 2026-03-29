# Music job

This folder contains the `music` DeepWork library job.

## Recommended workflows

- `music/produce` — Full production cycle: project setup → sound design → arrangement → mix → iterative review

## Directory structure

```
music/
├── AGENTS.md              # This file
├── job.yml                # Job specification
├── steps/
│   ├── project_setup.md   # Initialize project, git LFS, project brief
│   ├── sound_design.md    # VST/sample selection and patch documentation
│   ├── arrange.md         # Song structure and automation
│   ├── mix.md             # Levels, EQ, compression, FX chains
│   └── review_iterate.md  # Critical listen and loop/finalize decision
├── hooks/
├── scripts/
└── templates/
```

## Key design decisions

- **Git LFS for audio**: `.gitattributes` is configured in project_setup to track all audio formats via LFS. Stems are bounced to `music/[track_name]/stems/`.
- **Iterative loop**: `review_iterate` uses `go_to_step` to loop back to `sound_design`, `arrange`, or `mix` based on the most critical issue found. Maximum 3 iterations.
- **DAW agnostic**: The job supports Ableton Live (AbletonOSC MCP) and Ardour/open-source DAWs. The chosen DAW is documented in `project_brief.md` and referenced throughout.
- **Progressive disclosure**: DAW-specific tooling details (OSC ports, MCP URLs, Max for Live notes) are in `common_job_info` and expanded in step instructions only where relevant.
