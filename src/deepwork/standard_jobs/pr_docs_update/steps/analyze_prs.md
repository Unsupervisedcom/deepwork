# Analyze PR Content

## Objective

Analyze the content of unprocessed pull requests to identify which ones contain changes relevant to documentation updates, specifically for AGENTS.md files or copilot-specific instructions.

## Task

Review each PR from the input list and determine what documentation updates are needed based on the PR's changes, title, description, and files modified.

### Step 1: Load PR List

1. **Read the input file** `pr_list.json`
   - Parse the JSON structure
   - Extract the list of PRs to analyze

2. **Verify the data**
   - Ensure PRs have all required fields
   - Note the repository context

### Step 2: Analyze Each PR

For each PR in the list, evaluate its relevance to documentation:

1. **Examine Changed Files**
   - Look for patterns that suggest documentation impact:
     - New features or capabilities added
     - Changes to job definitions or workflows
     - API or interface modifications
     - New standard jobs or tools
     - Configuration changes
     - Agent or LLM interaction changes
   
2. **Review PR Title and Description**
   - Identify the purpose of the PR
   - Note any documentation mentions
   - Look for keywords like: "add", "new", "feature", "job", "workflow", "agent", "copilot"

3. **Categorize the PR**
   - **General documentation**: Changes that affect all agents (→ AGENTS.md)
   - **Copilot-specific**: Changes specific to GitHub Copilot integration (→ copilot instructions)
   - **Not relevant**: Changes with no documentation impact
   - **Unclear**: Needs further investigation

4. **Extract Documentation Insights**
   For relevant PRs, identify:
   - What was added or changed?
   - What should agents know about this change?
   - Which documentation file should be updated?
   - What specific information should be added?

### Step 3: Determine Documentation Updates

For each relevant PR, create a documentation recommendation:

1. **For AGENTS.md updates**:
   - New job or workflow information
   - Codebase structure changes
   - New conventions or patterns
   - Important context for all agents

2. **For copilot-specific instructions**:
   - Copilot-specific features or integrations
   - Copilot workflow changes
   - Copilot tool usage patterns

3. **Documentation entry format**:
   - Clear, concise description
   - Reference to the PR number
   - Suggested location in the documentation
   - Specific text to add or update

### Step 4: Create Analysis Report

Create `pr_analysis.md` with the following structure:

```markdown
# PR Documentation Analysis

**Repository**: owner/repo-name
**Analysis Date**: 2026-01-19
**PRs Analyzed**: 5
**Documentation Updates Needed**: 3

## PRs Requiring Documentation Updates

### PR #123: Add new feature
- **Merge Date**: 2026-01-15
- **Author**: username
- **URL**: https://github.com/owner/repo/pull/123
- **Category**: General Documentation (AGENTS.md)
- **Summary**: This PR adds a new job type for automated testing
- **Documentation Update**: 
  - File: `.deepwork/jobs/[job_name]/AGENTS.md`
  - Section: Job Structure
  - Content: Document the new automated testing job available in the repository
  - Rationale: Agents should be aware of this capability for future task planning

### PR #456: Update copilot integration
- **Merge Date**: 2026-01-14
- **Author**: username2
- **URL**: https://github.com/owner/repo/pull/456
- **Category**: Copilot-Specific Instructions
- **Summary**: Enhanced copilot workflow with new commands
- **Documentation Update**: 
  - File: Copilot-specific instruction files
  - Section: Available Commands
  - Content: Document the new `/copilot-command` syntax and usage
  - Rationale: Copilot agents need to know about new command capabilities

## PRs Not Requiring Updates

### PR #789: Fix typo in README
- **Reason**: Minor documentation fix, no agent-relevant changes
```

## Output Format

- **File**: `pr_analysis.md`
- **Content**: Markdown document with analysis results and recommendations
- **Location**: Current working directory

## Quality Criteria

- ✓ All PRs from input list analyzed
- ✓ Each PR categorized (general docs, copilot-specific, not relevant, or unclear)
- ✓ Documentation updates clearly specified with target file and content
- ✓ Rationale provided for each recommended update
- ✓ Summary statistics included (PRs analyzed, updates needed)
- ✓ Clear, actionable recommendations for the next step

## Notes

- Focus on changes that provide value to AI agents working with the codebase
- Avoid documenting trivial changes (typos, formatting, etc.)
- When in doubt, err on the side of including information that might be helpful
- Consider the perspective of an agent encountering this codebase for the first time
