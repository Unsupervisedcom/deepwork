# Define Policy

## Objective

Create or update policy entries in the `.deepwork.policy.yml` file to enforce team guidelines, documentation requirements, or other constraints when specific files change.

## Task

Guide the user through defining a new policy by asking structured questions. **Do not create the policy without first understanding what they want to enforce.**

**Important**: Use the AskUserQuestion tool to ask structured questions when gathering information from the user. This provides a better user experience with clear options and guided choices.

### Step 1: Understand the Policy Purpose

Start by asking structured questions to understand what the user wants to enforce:

1. **What guideline or constraint should this policy enforce?**
   - What situation triggers the need for action?
   - What files or directories, when changed, should trigger this policy?
   - Examples: "When config files change", "When API code changes", "When database schema changes"

2. **What action should be taken?**
   - What should the agent do when the policy triggers?
   - Update documentation? Perform a security review? Update tests?
   - Is there a specific file or process that needs attention?

3. **Are there any "safety" conditions?**
   - Are there files that, if also changed, mean the policy doesn't need to fire?
   - For example: If config changes AND install_guide.md changes, assume docs are already updated
   - This prevents redundant prompts when the user has already done the right thing

### Step 2: Define the Trigger Patterns

Help the user define glob patterns for files that should trigger the policy:

**Common patterns:**
- `src/**/*.py` - All Python files in src directory (recursive)
- `app/config/**/*` - All files in app/config directory
- `*.md` - All markdown files in root
- `src/api/**/*` - All files in the API directory
- `migrations/**/*.sql` - All SQL migrations

**Pattern syntax:**
- `*` - Matches any characters within a single path segment
- `**` - Matches any characters across multiple path segments (recursive)
- `?` - Matches a single character

### Step 3: Define Safety Patterns (Optional)

If there are files that, when also changed, mean the policy shouldn't fire:

**Examples:**
- Policy: "Update install guide when config changes"
  - Trigger: `app/config/**/*`
  - Safety: `docs/install_guide.md` (if already updated, don't prompt)

- Policy: "Security review for auth changes"
  - Trigger: `src/auth/**/*`
  - Safety: `SECURITY.md`, `docs/security_review.md`

### Step 3b: Choose the Comparison Mode (Optional)

The `compare_to` field controls what baseline is used when detecting "changed files":

**Options:**
- `base` (default) - Compares to the base of the current branch (merge-base with main/master). This is the most common choice for feature branches, as it shows all changes made on the branch.
- `default_tip` - Compares to the current tip of the default branch (main/master). Useful when you want to see the difference from what's currently in production.
- `prompt` - Compares to the state at the start of each prompt. Useful for policies that should only fire based on changes made during a single agent response.

**When to use each:**
- **base**: Best for most policies. "Did this branch change config files?" → trigger docs review
- **default_tip**: For policies about what's different from production/main
- **prompt**: For policies that should only consider very recent changes within the current session

Most policies should use the default (`base`) and don't need to specify `compare_to`.

### Step 4: Write the Instructions

Create clear, actionable instructions for what the agent should do when the policy fires.

**Good instructions include:**
- What to check or review
- What files might need updating
- Specific actions to take
- Quality criteria for completion

**Example:**
```
Configuration files have changed. Please:
1. Review docs/install_guide.md for accuracy
2. Update any installation steps that reference changed config
3. Verify environment variable documentation is current
4. Test that installation instructions still work
```

### Step 5: Create the Policy Entry

Create or update `.deepwork.policy.yml` in the project root.

**File Location**: `.deepwork.policy.yml` (root of project)

**Format**:
```yaml
- name: "[Friendly name for the policy]"
  trigger: "[glob pattern]"  # or array: ["pattern1", "pattern2"]
  safety: "[glob pattern]"   # optional, or array
  compare_to: "base"         # optional: "base" (default), "default_tip", or "prompt"
  instructions: |
    [Multi-line instructions for the agent...]
```

**Alternative with instructions_file**:
```yaml
- name: "[Friendly name for the policy]"
  trigger: "[glob pattern]"
  safety: "[glob pattern]"
  compare_to: "base"         # optional
  instructions_file: "path/to/instructions.md"
```

### Step 6: Verify the Policy

After creating the policy:

1. **Check the YAML syntax** - Ensure valid YAML formatting
2. **Test trigger patterns** - Verify patterns match intended files
3. **Review instructions** - Ensure they're clear and actionable
4. **Check for conflicts** - Ensure the policy doesn't conflict with existing ones

## Example Policies

### Update Documentation on Config Changes
```yaml
- name: "Update install guide on config changes"
  trigger: "app/config/**/*"
  safety: "docs/install_guide.md"
  instructions: |
    Configuration files have been modified. Please review docs/install_guide.md
    and update it if any installation instructions need to change based on the
    new configuration.
```

### Security Review for Auth Code
```yaml
- name: "Security review for authentication changes"
  trigger:
    - "src/auth/**/*"
    - "src/security/**/*"
  safety:
    - "SECURITY.md"
    - "docs/security_audit.md"
  instructions: |
    Authentication or security code has been changed. Please:
    1. Review for hardcoded credentials or secrets
    2. Check input validation on user inputs
    3. Verify access control logic is correct
    4. Update security documentation if needed
```

### API Documentation Sync
```yaml
- name: "API documentation update"
  trigger: "src/api/**/*.py"
  safety: "docs/api/**/*.md"
  instructions: |
    API code has changed. Please verify that API documentation in docs/api/
    is up to date with the code changes. Pay special attention to:
    - New or changed endpoints
    - Modified request/response schemas
    - Updated authentication requirements
```

## Output Format

### .deepwork.policy.yml
Create or update this file at the project root with the new policy entry.

## Quality Criteria

- Asked structured questions to understand user requirements
- Policy name is clear and descriptive
- Trigger patterns accurately match the intended files
- Safety patterns prevent unnecessary triggering
- Instructions are actionable and specific
- YAML is valid and properly formatted

## Context

Policies are evaluated automatically when you finish working on a task. The system:
1. Determines which files have changed based on each policy's `compare_to` setting:
   - `base` (default): Files changed since the branch diverged from main/master
   - `default_tip`: Files different from the current main/master branch
   - `prompt`: Files changed since the last prompt submission
2. Checks if any changes match policy trigger patterns
3. Skips policies where safety patterns also matched
4. Prompts you with instructions for any triggered policies

You can mark a policy as addressed by including `<promise>✓ Policy Name</promise>` in your response (replace Policy Name with the actual policy name). This tells the system you've already handled that policy's requirements.
