# DeepReview Rough Spec

DeepReview allows you to define `.deepreview` files throughout the filesystem. They define glob match patterns along with `.deepwork/review/` entries to apply to them. Once configured, you can then have your CLI agent run a review at any time, and it will do so appropriately based on the policies set here.

## Config File
Each .deepreview file applies to the directory it is in and defines globs that can match subdirectories. i.e. like .gitignore or similar.

#### Example `.deepreview` file
```yaml
p# =====================================================================
# Name: Standard Python File Review
# Summary: Triggers on changes to any Python file outside of tests or 
# docs. Every modified file is reviewed individually using the external 
# guidelines file, keeping the AI's feedback scoped strictly to that 
# specific file without any outside noise.
# =====================================================================
python_file_best_practices:
  match:
    include:
      - "**/*.py"
    exclude:
      - "tests/**/*.py"
      - "docs/**/*.py"
  review:
    strategy: individual
    instructions:
      file: .github/prompts/python_review.md

# =====================================================================
# Name: UI Component Contextual Review
# Summary: Triggers when a React component (.tsx) is modified. Each 
# component is reviewed individually, but the AI is also given a 
# high-level list of all other files changed in the pull request. 
# This helps the AI spot if a component's API changed without the 
# developer remembering to update the parent components.
# =====================================================================
ui_component_review:
  match:
    include:
      - "src/components/**/*.tsx"
  review:
    strategy: individual
    additional_context:
      all_changed_filenames: true 
    instructions: |
      Review this React component for accessibility and prop-type safety. 
      Check the changed filenames list to see if the consumer of this component 
      was also updated if you notice breaking API changes.

# =====================================================================
# Name: Database Migration Batch Review
# Summary: Triggers when Alembic database migration scripts are added 
# or modified. Instead of looking at them one by one, all changed 
# migration files are reviewed together in a single prompt so the 
# agent can check for sequence conflicts and overall migration safety.
# =====================================================================
db_migration_safety:
  match:
    include:
      - "alembic/versions/*.py"
  review:
    strategy: matches_together 
    agent:
      claude: "db-expert"
    instructions: |
      Review these database migrations together. 
      Ensure there are no conflicting locks, no destructive 
      drops without backups, and that the sequence IDs are ordered correctly.

# =====================================================================
# Name: Version Synchronization Check
# Summary: Triggers if any of the core project configuration files 
# (CHANGELOG, pyproject.toml, uv.lock) are modified. If even one file 
# changes, the system groups all three files together—including the 
# unchanged ones—so the agent can verify the version strings match 
# exactly across the entire project.
# =====================================================================
versions_in_sync:
  match:
    include:
      - "CHANGELOG.md"
      - "pyproject.toml"
      - "uv.lock"
  review:
    strategy: matches_together
    additional_context:
      unchanged_matching_files: true 
    instructions: "Make sure the version number is exactly the same across all three of these files."

# =====================================================================
# Name: Global Security Audit
# Summary: Acts as a tripwire. If any file in the core authentication 
# module or configuration directory is touched, this rule triggers. 
# It gathers the full contents of *all files* changed across the 
# entire branch and sends them to the specialized security agent.
# =====================================================================
pr_security_review:
  match:
    include:
      - "src/auth/**/*.py"
      - "config/*"
    exclude:
      - "config/*.dev.yaml"
  review:
    strategy: all_changed_files 
    agent:
      claude: "security-expert"
    instructions: |
      A change was detected in the authentication module or core config. 
      Review all the changed files in this changeset for potential security 
      regressions, leaked secrets, or broken authorization logic.

# =====================================================================
# Name: API Route Authorization Check
# Summary: Triggers when backend route definitions are modified. 
# It reviews each route file individually using a strict security 
# persona to ensure endpoints aren't exposed without proper middleware.
# =====================================================================
api_route_auth_check:
  match:
    include:
      - "src/routes/**/*.ts"
  review:
    strategy: individual
    agent:
      claude: "security-expert"
    instructions: |
      Verify that all exported API routes in this file are protected by 
      the `requireAuth` middleware unless explicitly decorated with `@Public`. 
      Check for proper role-based access control (RBAC) scopes.

# =====================================================================
# Name: Dockerfile Optimization
# Summary: Triggers when a Dockerfile or Compose file is modified. 
# Evaluates the file individually to ensure image sizes are kept small 
# and security best practices (like not running as root) are followed.
# =====================================================================
dockerfile_optimization:
  match:
    include:
      - "**/Dockerfile"
      - "docker-compose*.yml"
  review:
    strategy: individual
    agent:
      claude: "devops-engineer"
    instructions: |
      Review this container configuration. Ensure multi-stage builds are used 
      where appropriate, layers are optimized for caching, dependencies are 
      pinned, and the default execution user is not root.

# =====================================================================
# Name: CI/CD Pipeline Audit
# Summary: Triggers on changes to GitHub Actions workflows. It reviews 
# all matched workflow files together to ensure that environment 
# variables and deployment steps remain consistent across jobs.
# =====================================================================
cicd_pipeline_audit:
  match:
    include:
      - ".github/workflows/*.yml"
  review:
    strategy: matches_together
    agent:
      claude: "devops-engineer"
    instructions: |
      Review these CI/CD workflows. Verify that no secrets are being echoed 
      to the console, third-party actions are pinned to a specific commit SHA, 
      and deployment environments require manual approval.

# =====================================================================
# Name: Documentation Link & Consistency Check
# Summary: Triggers when Markdown documentation is updated. It reviews 
# the matched files together so the agent can check if links between the 
# newly modified docs are broken, ensuring a cohesive reading experience.
# =====================================================================
docs_consistency_check:
  match:
    include:
      - "docs/**/*.md"
  review:
    strategy: matches_together
    instructions: |
      Review these documentation files. Ensure the tone is consistent, 
      check for any broken relative links between these documents, and 
      verify that code blocks have language tags for syntax highlighting.

# =====================================================================
# Name: GraphQL Schema Evolution
# Summary: Triggers when the GraphQL schema is modified. It reviews the 
# matched schema files together and provides a list of all other changed 
# files in the PR to help the agent identify if a deprecated field was 
# removed before the frontend clients stopped using it.
# =====================================================================
graphql_schema_evolution:
  match:
    include:
      - "schema/**/*.graphql"
  review:
    strategy: matches_together
    additional_context:
      all_changed_filenames: true
    instructions: |
      Review these GraphQL schema changes. Flag any breaking changes 
      (e.g., removing a field, changing a type). If there are breaking changes, 
      check the list of changed filenames to ensure the corresponding frontend 
      queries were also updated.
```

The requirements I am trying to get with the patterns and groupings are:
1. You can have each changed file matching the patterns reviewed individually
2. You can have all the changed files that match the patterns reviewed together
	1. Variant of this where you do them together, and you include UNCHANGED files in the review as long as at least 1 changed
3. You can have all the files all the files that changed reviewed together
4. There is an option to say "include list of other files that changed (outside the patterns)"

## Implementation
The heavy lifting is done by the `deepwork` cli. It can be called with various arguments to facilitate the review in different ways, but the primary one is demonstrated below.

#### Review inside Claude Code
The `deepwork:review` skill has instructions that us the "!`bash command`" syntax to run and include the output of `deepwork review --instructions_for claude` . That gives precise instructions for Claude of what to do to run a bunch of review agents in parallel. 

It does this in a very token-efficient way by generating files in `.deepwork/tmp/review_instructions/random-long-number.md`, then having the resulting instructions say things (very roughly) like:
```
Invoke the following list of Tasks in parallel:
Name: "python_test_files review of test/foo.py"
	Agent: Default
	prompt: "@.deepwork/tmp/review_instructions/7142141.md"
Name: "python_test_files review of test/bar.py"
	Agent: Default
	prompt: "@.deepwork/tmp/review_instructions/6316224.md"
```
The effect of that is that the outer agent does not need to have any context on what each sub-task is doing, and the instructions make it to the sub-agent precisely.

#### Requirements
Put the requirements files for this under spec/deepwork/review

