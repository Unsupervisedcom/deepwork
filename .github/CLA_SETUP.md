# CLA Assistant Setup Guide

This document explains how to set up the CLA Assistant GitHub Action to automatically enforce Contributor License Agreement (CLA) signing for all pull requests.

## Overview

The CLA Assistant GitHub Action (`.github/workflows/cla.yml`) automatically:
- Comments on new pull requests asking contributors to sign the CLA
- Tracks who has signed the CLA in `.github/CLA_SIGNATORIES.json`
- Updates PR status checks based on CLA signature status
- Allows contributors to sign by commenting on their PR

## Prerequisites

To enable CLA enforcement, a repository administrator must create a Personal Access Token (PAT) with appropriate permissions.

## Setup Instructions

### 1. Create a Personal Access Token (PAT)

The CLA Assistant needs a PAT to commit signature data back to the repository.

**Steps:**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - URL: https://github.com/settings/tokens?type=beta

2. Click **"Generate new token"**

3. Configure the token:
   - **Token name**: `CLA Assistant - DeepWork`
   - **Expiration**: Choose appropriate expiration (recommend 1 year, then renew)
   - **Repository access**: Select "Only select repositories" and choose `Unsupervisedcom/deepwork`

4. Under **"Permissions"**, configure **Repository permissions**:
   - **Contents**: Read and write (required to commit signatures)
   - **Pull requests**: Read and write (required to comment and update status)
   - **Metadata**: Read-only (automatically selected)

5. Click **"Generate token"** and **copy the token** (you won't be able to see it again)

### 2. Add the PAT to Repository Secrets

1. Go to the DeepWork repository settings:
   - URL: https://github.com/Unsupervisedcom/deepwork/settings/secrets/actions

2. Click **"New repository secret"**

3. Add the secret:
   - **Name**: `CLA_ASSISTANT_PAT`
   - **Value**: Paste the PAT you generated in step 1

4. Click **"Add secret"**

### 3. Verify the Setup

To verify the CLA Assistant is working:

1. **Create a test pull request** from a different GitHub account (or ask a team member to create one)

2. **Check for the CLA comment**: The CLA Assistant bot should automatically comment on the PR with instructions to sign the CLA

3. **Sign the CLA**: Comment on the PR with:
   ```
   I have read the CLA Document and I hereby sign the CLA
   ```

4. **Verify signature tracking**: After signing, a new commit should be added to the main branch updating `.github/CLA_SIGNATORIES.json`

5. **Check PR status**: The PR status check should update to show "All contributors have signed the CLA ✅"

## How It Works

### For Contributors

When a contributor opens a pull request:

1. The CLA Assistant bot comments with a link to the CLA and instructions
2. The contributor reads the CLA at `/CLA.md`
3. The contributor signs by commenting: `I have read the CLA Document and I hereby sign the CLA`
4. The bot records the signature in `.github/CLA_SIGNATORIES.json`
5. The bot updates the PR status to indicate CLA is signed
6. Future PRs from the same contributor don't require re-signing

### Signature Storage

Signatures are stored in `.github/CLA_SIGNATORIES.json` in the following format:

```json
{
  "signedContributors": [
    {
      "name": "username",
      "id": 12345678,
      "comment_id": 987654321,
      "created_at": "YYYY-MM-DDTHH:MM:SSZ",
      "repoId": 123456789,
      "pullRequestNo": 42
    }
  ]
}
```

This file is automatically created and updated by the CLA Assistant.

## Troubleshooting

### CLA Assistant Not Commenting on PRs

**Possible causes:**
- The `CLA_ASSISTANT_PAT` secret is not set or has expired
- The PAT doesn't have the required permissions
- The workflow file has syntax errors

**Solutions:**
1. Check that the secret exists in repository settings
2. Verify PAT permissions (Contents: write, Pull requests: write)
3. Check the Actions tab for workflow errors

### Signatures Not Being Recorded

**Possible causes:**
- The PAT doesn't have write access to Contents
- Branch protection rules prevent the bot from committing

**Solutions:**
1. Verify the PAT has "Contents: Read and write" permission
2. Check branch protection rules and add the CLA Assistant as an exception if needed

### Contributor Signed But Status Still Shows Unsigned

**Possible causes:**
- The comment text was not exact
- The workflow didn't trigger

**Solutions:**
1. Ensure the comment is exactly: `I have read the CLA Document and I hereby sign the CLA`
2. Try commenting `recheck` to trigger the workflow again
3. Check the Actions tab to see if the workflow ran

## Allowlist

The following accounts are automatically exempt from CLA requirements:
- `dependabot[bot]`
- `github-actions[bot]`

To add more accounts to the allowlist, edit `.github/workflows/cla.yml` and update the `allowlist` field.

## Token Rotation

For security, rotate the PAT periodically:

1. Generate a new PAT following the steps above
2. Update the `CLA_ASSISTANT_PAT` secret with the new token
3. Delete the old PAT from GitHub settings

Recommended rotation period: Every 12 months

## Additional Resources

- [CLA Assistant GitHub Action Documentation](https://github.com/contributor-assistant/github-action)
- [GitHub Personal Access Tokens Guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [DeepWork CLA](../CLA.md)
- [DeepWork License](../LICENSE.md)

## Support

For questions or issues with CLA setup, please:
- Open an issue in the repository
- Contact the repository administrators
- Email legal@unsupervised.com for legal questions about the CLA
