---
name: job_porter.explain_scopes
description: "Provides detailed explanation of local vs global jobs and when to use each"

---

# job_porter.explain_scopes

**Standalone skill** - can be run anytime

> Helps users port DeepWork jobs between local and global locations


## Instructions

**Goal**: Provides detailed explanation of local vs global jobs and when to use each

# Explain Job Scopes

## Objective

Help users understand the difference between local and global jobs, and when to use each scope.

## Task

Create a comprehensive guide explaining local vs global jobs with examples and best practices.

### Step 1: Create the Scope Guide

Generate a detailed markdown document explaining job scopes:

```bash
cat > scope_guide.md << 'EOF'
# Understanding DeepWork Job Scopes

## Overview

DeepWork supports two types of job scopes: **local** and **global**. Understanding when to use each helps you organize your workflows effectively.

## Local Jobs

**Location**: `.deepwork/jobs/` (within your project)

**Characteristics**:
- ✅ Available only in the current project
- ✅ Version controlled with your project (via Git)
- ✅ Can be shared with team members through your repository
- ✅ Can be customized for project-specific needs

**Use local jobs when**:
- The workflow is specific to this project's domain or tech stack
- The job needs access to project-specific files or configurations
- You want team members to have the same workflows
- The job is still being developed/refined

**Examples**:
- `deploy_staging` - Deploys this specific application
- `run_project_tests` - Runs tests specific to this codebase
- `generate_api_docs` - Creates docs from this project's API
- `competitive_research` - Research specific to your product/market

## Global Jobs

**Location**: `~/.deepwork/jobs/` (in your home directory)

**Characteristics**:
- ✅ Available across all projects on your system
- ✅ Persists even if you delete projects
- ✅ Personal workflows that apply to many contexts
- ✅ No need to recreate in each project

**Use global jobs when**:
- The workflow applies across multiple projects
- The job is a general-purpose utility
- You want to use it in projects where you don't control the repo
- The workflow is mature and stable

**Examples**:
- `git_commit_summary` - Works with any Git repository
- `write_tutorial` - Generic documentation workflow
- `code_review_checklist` - Applies to any codebase
- `meeting_notes` - General note-taking workflow

## Decision Guide

Ask yourself these questions:

| Question | If Yes → | If No → |
|----------|----------|---------|
| Does this workflow only make sense in this specific project? | **Local** | Continue... |
| Do I want this workflow version-controlled with my code? | **Local** | Continue... |
| Will I use this workflow in multiple different projects? | **Global** | Continue... |
| Is this a general utility that works anywhere? | **Global** | **Local** |

## Migration Strategy

You can always change your mind! Use `/job_porter.port_job` to move jobs between scopes.

**Common migrations**:
- **Local → Global**: When you realize a workflow is useful across projects
- **Global → Local**: When you want to customize a global workflow for a specific project

## Best Practices

### Start Local, Go Global Later
When creating new jobs, start with local scope. Once you've used it successfully and realize it applies elsewhere, port it to global.

### Keep Team Workflows Local
If your team shares a repository, keep shared workflows local so everyone has access.

### Personal Utilities as Global
General-purpose tools you use frequently (like documentation generators, Git utilities, etc.) work best as global jobs.

### Version Control Local Jobs
Local jobs are in `.deepwork/jobs/`, so they're version controlled. This is perfect for team collaboration.

### Document Global Jobs
Since global jobs aren't in version control, document them separately or maintain a personal repository of your global jobs.

## Examples by Role

### For Engineers
- **Local**: `deploy_app`, `run_integration_tests`, `update_dependencies`
- **Global**: `git_summary`, `code_review`, `technical_blog_post`

### For Product Managers
- **Local**: `product_roadmap`, `feature_spec`, `release_notes`
- **Global**: `meeting_notes`, `stakeholder_update`, `competitive_research`

### For Data Analysts
- **Local**: `etl_pipeline`, `dashboard_update`, `model_training`
- **Global**: `data_exploration`, `report_template`, `chart_generator`

## Getting Help

- List all your jobs: `/job_porter.list_jobs`
- Port a job: `/job_porter.port_job`
- See this guide: `/job_porter.explain_scopes`

---

*Remember*: The scope decision isn't permanent. You can always move jobs later as your needs evolve!
EOF

echo "✓ Scope guide created: scope_guide.md"
```

### Step 2: Display Key Points

Show the user the most important takeaways:

```bash
echo ""
echo "=== Key Takeaways ==="
echo ""
echo "LOCAL JOBS (.deepwork/jobs/):"
echo "  • Project-specific workflows"
echo "  • Version controlled with your code"
echo "  • Shared with team members"
echo "  • Example: deploy_staging, run_project_tests"
echo ""
echo "GLOBAL JOBS (~/.deepwork/jobs/):"
echo "  • Available across all projects"
echo "  • Personal workflows and utilities"
echo "  • No need to recreate in each project"
echo "  • Example: git_commit_summary, write_tutorial"
echo ""
echo "RULE OF THUMB:"
echo "  Start local, go global when you realize it's useful elsewhere."
echo ""
```

### Step 3: Offer Next Steps

Provide actionable next steps:

```bash
echo "=== What You Can Do Now ==="
echo ""
echo "1. Review the full guide: cat scope_guide.md"
echo "2. List your current jobs: /job_porter.list_jobs"
echo "3. Port a job if needed: /job_porter.port_job"
echo "4. When creating new jobs with /deepwork_jobs, choose the right scope"
echo ""
```

## Quality Criteria

- **Comprehensive guide**: `scope_guide.md` covers all aspects of job scopes
- **Clear distinctions**: Local vs global differences are well explained
- **Practical examples**: Real-world examples for different use cases
- **Decision framework**: Clear guidance on choosing between local and global
- **Actionable**: User knows exactly what to do next
- **Role-specific examples**: Provided examples for different user types


### Job Context

This job assists users in managing job scope by porting jobs between local 
project-specific locations (.deepwork/jobs/) and global system-wide locations 
(~/.deepwork/jobs/). It guides users through discovering available jobs, 
understanding the differences between local and global scope, and safely 
migrating jobs between scopes.



## Work Branch

Use branch format: `deepwork/job_porter-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/job_porter-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `scope_guide.md`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## On Completion

1. Verify outputs are created
2. Inform user: "explain_scopes complete, outputs: scope_guide.md"

This standalone skill can be re-run anytime.

---

**Reference files**: `.deepwork/jobs/job_porter/job.yml`, `.deepwork/jobs/job_porter/steps/explain_scopes.md`