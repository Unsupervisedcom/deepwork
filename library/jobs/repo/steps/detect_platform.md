# Detect Platform

## Objective

Identify the git provider, verify CLI authentication, determine the default branch, and inventory existing labels, milestones, and boards.

## Task

### Process

1. **Determine the repository and provider**

   Handle three modes based on the `project_repo` input:

   a. **Omitted / empty** — detect from the current directory:
      - Run `git remote get-url origin` to get the remote URL
      - Parse the URL to extract the host and owner/repo slug

   b. **Remote URL provided** (SSH or HTTPS):
      - Parse the URL directly to extract host and owner/repo slug

   c. **Owner/repo slug provided** (e.g. `acme/widgets`):
      - Check for a known provider host in `.git` remote, or ask the user which provider to use

   **Provider detection from hostname:**
   - `github.com` → GitHub
   - `gitlab.com` → GitLab
   - Any other host → assume Forgejo/Gitea (the agent's tool conventions document CLI usage)

   **Transport detection:**
   - URLs starting with `git@` or `ssh://` → SSH
   - URLs starting with `https://` → HTTPS

   If no repository exists yet (no `.git` directory or no remote), offer to create one using the provider's CLI, then re-detect.

2. **Verify CLI authentication**
   - Use the provider's whoami or auth status command to confirm the current user is authenticated
   - If additional scopes are needed (e.g. GitHub's `project` scope), prompt for a refresh

3. **Get default branch**
   - Query the provider's API or CLI for the repository's default branch name

4. **Inventory existing labels**
   - List all labels on the repository with name, color, and description

5. **Inventory milestones**
   - List all milestones with title, number, state, and issue counts

6. **Inventory boards** (if the provider supports a board API)
   - List project boards with title, number, and URL
   - If the provider has no board API, record `boards_api: false`

## Output Format

### platform_context.md

```markdown
# Platform Context

## Provider
- **Provider**: [github | forgejo | gitea | gitlab]
- **Host**: [hostname]
- **Repository**: [owner/repo]
- **Transport**: [ssh | https]
- **Default Branch**: [main | master | etc.]
- **Auth Status**: [authenticated as {username} | needs refresh]
- **Boards API**: [true | false]

## Existing Labels

| Name | Color | Description |
|------|-------|-------------|
| ... | ... | ... |

## Milestones

| Title | Number | State | Open | Closed |
|-------|--------|-------|------|--------|
| ... | ... | ... | ... | ... |

## Boards

| Title | Number | URL |
|-------|--------|-----|
| ... | ... | ... |

[Or "N/A — provider does not support project boards via API"]
```

## Quality Criteria

- Provider is correctly identified from the remote URL
- CLI authentication is verified for the detected provider
- Default branch name is recorded
- Existing labels, milestones, and boards are inventoried
