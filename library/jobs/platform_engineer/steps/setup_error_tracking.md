# Set Up Error Tracking

## Objective

Configure exception monitoring for the project so that production errors are captured, surfaced to developers, and tied to releases. By the end of this step, the project has a working error tracking integration with environment tags, release tracking, source map or debug symbol uploads, and alert rules.

## Task

Read the project's platform context, check for existing error tracking, help the user choose a provider if none exists, integrate the chosen SDK, configure release tracking and source maps, set up alerts, verify the setup, and document everything in the repository.

### Process

1. **Read context.md to understand the tech stack**
   - Identify the language and framework (e.g., Node/Express, Python/Django, Rust/Actix, Go/Gin)
   - Identify the frontend stack if applicable (React, Vue, Svelte, etc.)
   - Identify the CI/CD provider (GitHub Actions, Forgejo Actions, GitLab CI, etc.)
   - Identify the deployment target (containers, serverless, static hosting, etc.)
   - Note the package manager and build tooling

2. **Check for existing error tracking**
   - Search for Sentry DSN in configuration files, environment variables, and code:
     - Look for `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN`, `VITE_SENTRY_DSN` in `.env*` files
     - Look for `@sentry/` in `package.json`, `sentry-sdk` in `requirements.txt` or `pyproject.toml`, `sentry` in `Cargo.toml` or `go.mod`
   - Search for Honeybadger API key (`HONEYBADGER_API_KEY`, `honeybadger` package)
   - Search for Bugsnag key (`BUGSNAG_API_KEY`, `@bugsnag/` package)
   - Search for GlitchTip configuration (uses Sentry SDK with a custom DSN)
   - Check environment variable files and CI config for any error tracking-related variables

3. **If error tracking already exists, audit the current setup**

   Check for gaps in the existing configuration:

   **Source map / debug symbol uploads**:
   - For JavaScript/TypeScript: check if `@sentry/webpack-plugin`, `@sentry/vite-plugin`, or `sentry-cli` is configured in the build pipeline
   - For compiled languages: check if debug symbols are uploaded during CI release
   - If not configured, this is a gap to address

   **Release tracking**:
   - Check if the SDK is configured with a `release` option (e.g., `Sentry.init({ release: ... })`)
   - Check if releases are created during CI (e.g., `sentry-cli releases new`, GitHub Action `getsentry/action-release`)
   - Check if commits are associated with releases

   **Environment tags**:
   - Check if the SDK is configured with an `environment` option
   - Verify that production, staging, and development environments are distinguished

   **Alert rules**:
   - Note that alert rules are configured in the provider dashboard, not in code
   - Document what the user should verify in their dashboard (new error alerts, error rate spike alerts)

   If all areas are covered, document the current setup and skip to the documentation step. If gaps are found, address them.

4. **If no error tracking exists, help user choose a provider**

   Use the AskUserQuestion tool to present options with trade-offs:

   | Provider | Strengths | Considerations |
   |----------|-----------|----------------|
   | **Sentry** | Most popular, self-hostable, generous free tier (5K errors/mo), excellent SDK ecosystem, source map support, performance monitoring | Can be complex to self-host; free tier limits may not suit high-traffic apps |
   | **Honeybadger** | Simple setup, clean UI, good for small teams, includes uptime monitoring | Smaller ecosystem, no free tier (trial only), fewer integrations |
   | **Bugsnag** | Strong mobile support (iOS/Android SDKs), stability scoring, release health | Focused on mobile; web SDKs are capable but less mature than Sentry |
   | **GlitchTip** | Open source Sentry alternative, self-hostable, uses Sentry SDKs | Fewer features than Sentry, smaller community, must self-host for free |

   Ask the user which provider they prefer or if they need more information to decide.

5. **Configure the chosen provider**

   **Install the SDK for the project's language/framework**:
   - Use the project's package manager (not global install) per Nix dev shell conventions
   - For Sentry with Node: `pnpm add @sentry/node` (or `@sentry/react`, `@sentry/nextjs`, etc.)
   - For Sentry with Python: add `sentry-sdk` to `pyproject.toml` or `requirements.txt`
   - For Sentry with Rust: add `sentry` to `Cargo.toml`
   - For Sentry with Go: add `github.com/getsentry/sentry-go`
   - For Honeybadger/Bugsnag: use the equivalent SDK for the detected framework
   - Commit the dependency addition separately per version control conventions

   **Configure the DSN / API key**:
   - Guide the user to create a project in their provider's dashboard
   - Use the AskUserQuestion tool to ask the user for the DSN or API key
   - Store the DSN in an environment variable (e.g., `SENTRY_DSN`), never hardcoded in source
   - Add the environment variable name to `.env.example` with a placeholder value
   - Add the actual value to `.env` (which MUST be gitignored)

   **Set up environment tags**:
   - Configure the SDK initialization to read the environment from an env var (e.g., `SENTRY_ENVIRONMENT` or `NODE_ENV`)
   - Ensure production, staging, and development are distinguished
   - Example (Sentry, Node):
     ```javascript
     Sentry.init({
       dsn: process.env.SENTRY_DSN,
       environment: process.env.NODE_ENV || 'development',
       release: process.env.RELEASE_VERSION,
     });
     ```

   **Configure release tracking**:
   - Tie errors to specific releases/commits so the user can see which deploy introduced a regression
   - Set the `release` SDK option to a version string (git SHA, SemVer tag, or CI build number)
   - For CI: create releases during the deploy pipeline
     - Sentry: `sentry-cli releases new $VERSION && sentry-cli releases set-commits $VERSION --auto`
     - Honeybadger: `honeybadger deploy --revision $SHA`
   - Add the release creation step to the CI workflow file

   **Set up source map or debug symbol uploads in CI**:
   - For JavaScript/TypeScript projects with bundled/minified output:
     - Add the appropriate build plugin (`@sentry/webpack-plugin`, `@sentry/vite-plugin`, `@sentry/esbuild-plugin`)
     - Or add a CI step: `sentry-cli releases files $VERSION upload-sourcemaps ./dist`
   - For compiled languages (Rust, Go, C++):
     - Add debug symbol upload to the CI release pipeline
   - Ensure source maps are NOT served to end users (upload only to the error tracking provider)

   **Configure alert rules**:
   - Guide the user through setting up alerts in their provider dashboard:
     - **New issue alert**: triggers when a new error type is seen for the first time
     - **Error rate spike alert**: triggers when the error rate exceeds a threshold (e.g., 2x baseline)
     - **Regression alert**: triggers when a previously resolved error reappears
   - Recommend setting alert notification channels (email, Slack, PagerDuty) per the team's on-call setup
   - Note: alert rules are managed in the provider dashboard, not in code

6. **Verify the setup**
   - Add a test route or script that deliberately throws an error:
     - For web apps: a `/debug-sentry` route (to be removed before production)
     - For CLI tools: a test command that raises an exception
   - Run the test and confirm the error appears in the provider dashboard
   - Use the AskUserQuestion tool to ask the user to verify they can see the test event in their dashboard
   - Remove or disable the test trigger after verification

7. **Document everything**
   - Add an error tracking section to the project's documentation (e.g., `docs/error-tracking.md` or a section in `README.md`)
   - Documentation MUST include (per convention 54):
     - Provider name and project URL (dashboard link)
     - Environment variable name for the DSN (NOT the actual DSN value)
     - SDK package name and version
     - How releases are tracked (CI step or manual)
     - How source maps / debug symbols are uploaded
     - Where to configure alert rules
     - How to verify the setup (test event instructions)
   - Add the documentation file path to the output

## Output Format

### error_tracking_config.md

A comprehensive document recording the error tracking setup decisions and configuration.

**Structure**:
```markdown
# Error Tracking Configuration

**Date**: [current date]
**Provider**: [Sentry | Honeybadger | Bugsnag | GlitchTip]
**Status**: [NEW_SETUP | AUDITED_EXISTING | GAPS_ADDRESSED]

## Provider Selection

**Chosen**: [provider name]
**Rationale**: [why this provider was selected for this project]

## Integration Details

| Component | Value |
|-----------|-------|
| SDK Package | [e.g., `@sentry/node@8.x`] |
| DSN Env Var | [e.g., `SENTRY_DSN`] |
| Environment Env Var | [e.g., `NODE_ENV`] |
| Release Source | [e.g., `git describe --tags`, CI build number] |
| Init File | [e.g., `src/instrument.ts`] |

## Release Tracking

**Method**: [CI pipeline step | build plugin | manual]
**CI Step**: [description of the CI step that creates releases]
**Commit Association**: [yes/no — whether commits are linked to releases]

## Source Maps / Debug Symbols

**Upload Method**: [build plugin | CLI upload | not applicable]
**CI Step**: [description of the CI step that uploads source maps]
**Served to Users**: [no — uploaded to provider only]

## Alert Rules

| Alert Type | Configuration |
|------------|---------------|
| New Issue | [configured / needs configuration — triggers on first occurrence] |
| Error Rate Spike | [configured / needs configuration — threshold and window] |
| Regression | [configured / needs configuration — triggers on resolved-then-reopened] |
| Notification Channel | [email / Slack / PagerDuty / needs configuration] |

## Verification

**Test Event Sent**: [yes/no]
**Test Event Visible in Dashboard**: [yes/no — confirmed by user]
**Test Trigger Location**: [file path of test route/script, or "removed after verification"]

## Documentation

**Documentation File**: [path to the docs file created or updated]
**Covers**: DSN env var, SDK version, release tracking, source maps, alert setup, verification steps

## Files Modified

- [list of files added or modified during this setup]
```

## Quality Criteria

- **Provider Selected**: An error tracking provider is selected with rationale for the choice, or an existing provider is documented. The selection considers the project's tech stack, team size, and deployment model.
- **Integration Complete**: SDK integration is configured with DSN stored as an environment variable (never hardcoded), environment tags distinguishing production/staging/development, and release tracking tying errors to specific deploys.
- **Verification**: A test event was sent and confirmed visible in the provider dashboard by the user, or clear verification steps are documented for the user to follow.
- **Documented**: Configuration details are documented in the repository per convention 54 — including provider name, DSN environment variable name, SDK version, release tracking method, source map upload process, and alert configuration guidance.

## Context

This step is part of the `error_tracking` workflow. It runs after `gather_context`, which provides the `context.md` file describing the project's tech stack, available tools, and infrastructure type.

Error tracking is a foundational observability practice (conventions 50-54). Production services MUST have exception monitoring configured. Without it, errors go unnoticed until users report them, and debugging relies on searching through logs rather than seeing structured stack traces with request context.

The step is designed to be technology-agnostic — it adapts to the detected stack from context.md rather than assuming a specific provider or framework. It handles both greenfield setup (no error tracking exists) and gap analysis (error tracking exists but is incomplete).

Key conventions referenced:
- Convention 50: Production services MUST have exception monitoring
- Convention 51: Error tracking MUST capture stack traces, request context, user context, and environment metadata
- Convention 52: Source maps or debug symbols SHOULD be uploaded during release
- Convention 53: Alerts SHOULD be configured for new error types and rate spikes
- Convention 54: Error tracking configuration MUST be documented in the repository
