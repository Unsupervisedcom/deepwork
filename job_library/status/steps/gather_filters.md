# Gather Filters

## Objective

Collect optional filter substrings from the user to scope the status search to specific topics, features, or areas of work.

## Task

Prompt the user for filter keywords and create a filters.txt file with the provided keywords (or empty if none provided).

### Process

1. **Explain the purpose of filters**
   - Filters allow focusing the status search on specific topics
   - Multiple keywords can be provided to search for work related to those topics
   - Keywords will be used to search:
     - Branch names (e.g., "feature/foo-bar" matches "foo" and "bar")
     - Commit messages (e.g., "Fix foo issue" matches "foo")
     - PR titles and descriptions
     - Issue titles and descriptions
   - If no filters are provided, all work will be included in the report

2. **Prompt the user for filter keywords**
   - Ask: "What keywords would you like to filter by? (comma-separated, or press Enter for no filters)"
   - Examples:
     - "foo,bar" - searches for work related to foo AND bar
     - "authentication" - searches for authentication-related work
     - "" (empty) - includes all work

3. **Parse and normalize the input**
   - Split comma-separated values
   - Trim whitespace from each keyword
   - Convert to lowercase for case-insensitive matching
   - Remove duplicates

4. **Create filters.txt**
   - Write each filter keyword on a separate line
   - If no filters provided, create an empty file
   - Example content:
     ```
     foo
     bar
     authentication
     ```

5. **Confirm with user**
   - Display the filters that will be used
   - Explain that results must match ALL provided keywords
   - If empty, explain that all work will be included

## Quality Criteria

- User was prompted for filter keywords
- filters.txt was created in the working directory
- File contains normalized keywords (one per line, lowercase, trimmed)
- User understands how filters will be applied
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the first step of the status workflow. The filters gathered here will be used by subsequent steps to scope the search of git branches, commits, PRs, and issues.

## Example Interaction

**Agent:** "What keywords would you like to filter by? (comma-separated, or press Enter for no filters)"

**User:** "foo, bar"

**Agent:** "I'll search for work containing both 'foo' and 'bar' in branch names, commit messages, PRs, and issues. Creating filters.txt..."

[Creates filters.txt with:]
```
foo
bar
```

**Agent:** "Filters configured. All results will match both 'foo' AND 'bar'. Ready to proceed to the next step."
