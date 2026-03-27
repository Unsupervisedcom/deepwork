# Gather Platform Context

## Objective

Auto-detect the available tools, infrastructure type, repository structure, and existing configurations so that all subsequent workflow steps can adapt their behavior to the actual environment. This step MUST NOT require user input — it discovers everything automatically.

## Task

Probe the local machine and repository to build a comprehensive platform context document. The output informs every other step in every workflow (12 workflows depend on this step), so thoroughness matters more than speed — but avoid blocking operations (no network calls that could hang without a timeout).

### Process

#### 1. Detect Available Tools

For each tool category, check whether the binary exists and capture its version. Record each tool as **available** or **not found**.

**Container orchestration:**
- `kubectl version --client -o json 2>/dev/null` — record client version
- `helm version --short 2>/dev/null`
- `k9s version --short 2>/dev/null`
- `docker --version 2>/dev/null` or `podman --version 2>/dev/null`
- `docker compose version 2>/dev/null` or `podman-compose --version 2>/dev/null`

**Observability:**
- Grafana MCP — attempt to list dashboards via the Grafana MCP tool. If the tool responds, record as available and note the Grafana instance URL if returned. If the tool is not available or errors, record as not found.
- `promtool --version 2>/dev/null` (Prometheus CLI)
- `logcli --version 2>/dev/null` (Loki CLI)
- `amtool --version 2>/dev/null` (AlertManager CLI)

**CI provider (detect from repo files, not CLIs):**
- Check for `.github/workflows/` directory — if present, record GitHub Actions
- Check for `.forgejo/workflows/` directory — if present, record Forgejo Actions
- Check for `.gitlab-ci.yml` — if present, record GitLab CI
- Check for `.circleci/` directory — if present, record CircleCI
- Check for `Jenkinsfile` — if present, record Jenkins
- `gh --version 2>/dev/null` (GitHub CLI)

**Cloud CLIs:**
- `aws --version 2>/dev/null`
- `gcloud --version 2>/dev/null` (first line only)
- `az --version 2>/dev/null` (first line only)
- `doctl version 2>/dev/null`
- `terraform --version 2>/dev/null` (first line only)
- `pulumi version 2>/dev/null`
- `kubectl config get-contexts 2>/dev/null` — note the current context name

**Nix ecosystem:**
- `nix --version 2>/dev/null`
- `nixos-rebuild --help 2>/dev/null` (check exit code only, suppress output)
- `home-manager --version 2>/dev/null`
- Check if `flake.nix` exists at repo root
- Check if `flake.lock` exists at repo root

**Error tracking:**
- `sentry-cli --version 2>/dev/null`
- `honeybadger --version 2>/dev/null`

**Package managers & build tools:**
- `nix develop --help 2>/dev/null` (check exit code only)
- `npm --version 2>/dev/null`
- `pnpm --version 2>/dev/null`
- `yarn --version 2>/dev/null`
- `cargo --version 2>/dev/null`
- `go version 2>/dev/null`
- `uv --version 2>/dev/null`
- `pip --version 2>/dev/null`

#### 2. Determine Infrastructure Type

Based on tool detection results and repo contents, classify the infrastructure type. Exactly one primary type MUST be assigned, with optional secondary types.

| Type | Evidence |
|------|----------|
| **kubernetes** | `kubectl` available AND a kubeconfig exists (`~/.kube/config` or `$KUBECONFIG`) AND cluster is reachable (`kubectl cluster-info 2>/dev/null` exits 0) |
| **nix** | `flake.nix` exists at repo root OR NixOS configuration files are present |
| **cloud-managed** | Cloud CLI available AND no k8s/nix evidence (e.g., pure AWS Lambda, GCP Cloud Run) |
| **hybrid** | More than one of the above applies |
| **none** | None of the above applies — likely a local-only or new project |

If `kubectl` is available but cluster is not reachable, note this as "kubernetes (disconnected)" — the tool exists but cannot query live state.

#### 3. Survey Repository Structure

Scan the repository for platform-relevant files and directories. Do NOT read file contents — just note existence and paths.

**Key directories to check:**
- `k8s/`, `kubernetes/`, `deploy/`, `manifests/`, `charts/`, `helm/` — Kubernetes manifests
- `terraform/`, `tf/`, `infra/`, `infrastructure/` — IaC definitions
- `nix/`, `nixos/`, `modules/` — Nix configurations
- `.github/workflows/`, `.forgejo/workflows/`, `.gitlab-ci.yml`, `.circleci/` — CI configs
- `docker/`, `Dockerfile*`, `docker-compose*`, `compose*` — Container definitions
- `monitoring/`, `observability/`, `dashboards/`, `alerts/`, `grafana/` — Monitoring configs
- `scripts/`, `bin/` — Operational scripts
- `docs/`, `doc/` — Documentation (check for infrastructure docs specifically)
- `.deepwork/` — DeepWork artifacts from previous runs
- `.sentry*`, `sentry.properties` — Error tracking configs

**Key files to check:**
- `Makefile`, `Justfile`, `Taskfile.yml` — Task runners
- `flake.nix`, `flake.lock` — Nix flake
- `.envrc` — direnv configuration
- `.env`, `.env.example`, `.env.local` — Environment files (note existence, do NOT read contents)
- `INFRASTRUCTURE.md`, `docs/infrastructure.md` — Infrastructure docs per convention 14
- `CODEOWNERS`, `.github/CODEOWNERS` — Code ownership
- `renovate.json`, `.github/dependabot.yml` — Dependency automation per convention 33

#### 4. Catalog Existing Configurations

Note existing monitoring and operational configurations without reading sensitive content.

**Monitoring:**
- Grafana dashboard JSON files (list paths)
- Prometheus rule files or ServiceMonitor CRDs (list paths)
- Alert rule definitions (list paths)
- Loki configuration files (list paths)

**Secrets management:**
- Note which secret management approach is used (env vars, Kubernetes secrets, Vault, SOPS, sealed-secrets, etc.) based on file presence — do NOT read secret values
- Check for `.env` files and note they exist but are NOT read

**Existing dashboards (if Grafana MCP is available):**
- Use Grafana MCP to list dashboards — record dashboard titles and UIDs
- Note which services have dashboards and which do not

## Output Format

Write the context document to `.deepwork/tmp/platform_engineer/context.md`. Create parent directories if they do not exist.

```markdown
# Platform Context

**Generated**: YYYY-MM-DD HH:MM
**Repository**: <repo name from git remote or directory name>

## Available Tools

### Container Orchestration
| Tool | Status | Version |
|------|--------|---------|
| kubectl | available / not found | vX.Y.Z |
| helm | available / not found | vX.Y.Z |
| docker | available / not found | vX.Y.Z |
| ... | ... | ... |

### Observability
| Tool | Status | Version / Notes |
|------|--------|-----------------|
| Grafana MCP | available / not found | <instance URL if known> |
| promtool | available / not found | vX.Y.Z |
| logcli | available / not found | vX.Y.Z |
| ... | ... | ... |

### CI Provider
| Provider | Detected | Config Location |
|----------|----------|-----------------|
| GitHub Actions | yes / no | .github/workflows/ |
| ... | ... | ... |

### Cloud CLIs
| Tool | Status | Version |
|------|--------|---------|
| aws | available / not found | vX.Y.Z |
| ... | ... | ... |

### Nix Ecosystem
| Tool | Status | Version |
|------|--------|---------|
| nix | available / not found | vX.Y.Z |
| flake.nix | present / absent | — |
| ... | ... | ... |

### Error Tracking
| Tool | Status | Version |
|------|--------|---------|
| sentry-cli | available / not found | vX.Y.Z |
| ... | ... | ... |

## Infrastructure Type

**Primary**: kubernetes / nix / cloud-managed / hybrid / none
**Secondary**: <if hybrid, list all types>
**Notes**: <any caveats, e.g., "kubernetes (disconnected)" or "kubectl exists but no kubeconfig found">

### Kubernetes Context (if applicable)
- Current context: <context name>
- Cluster reachable: yes / no

## Repository Structure

### Platform-Relevant Directories
- `<path>/` — <brief description>
- ...

### Platform-Relevant Files
- `<path>` — <brief description>
- ...

### CI/CD Configurations
- <list of CI config files found>

### Container Definitions
- <list of Dockerfiles, compose files found>

## Existing Configurations

### Monitoring
- Dashboards: <list or "none found">
- Alert rules: <list or "none found">
- Prometheus configs: <list or "none found">

### Secrets Management
- Approach: <detected approach or "unknown">
- .env files: <list of .env files found, NOT their contents>

### Dependency Automation
- <renovate/dependabot/none detected>

### Grafana Dashboards (if MCP available)
| Dashboard Title | UID | Service |
|-----------------|-----|---------|
| ... | ... | ... |
```

## Quality Criteria

- **Tools Detected**: Available tools (kubectl, Grafana MCP, CI provider, cloud CLI, Nix) are explicitly listed with version info where available. Tools that are not found are also listed as "not found" so the absence is explicit.
- **Infrastructure Type Identified**: The infrastructure type (k8s, nix, cloud-managed, hybrid, or none) is clearly stated with supporting evidence explaining why that classification was chosen.
- **Repo Structure Documented**: Key directories and configuration files relevant to platform engineering are cataloged with brief descriptions.
- **No User Input Required**: The step completed fully through auto-detection without prompting the user for any information.
- **No Sensitive Data Captured**: `.env` file contents, secrets, tokens, and credentials are never read or included in the output. Only file existence is noted.
- **Idempotent**: Running this step again produces a consistent result (modulo actual environment changes).

## Context

This step is the foundation for all 12 workflows in the platform_engineer job. Every subsequent step reads `context.md` to decide which tools to use, which commands to run, and which sections to skip. A thorough context document prevents later steps from attempting to use tools that do not exist or missing tools that are available.

The step is marked `hidden: true` in the job definition because users do not interact with it directly — it runs automatically at the start of each workflow.

Per convention 6, documenting what was checked (even when not found) is valuable because it narrows the scope for later steps. For example, if Grafana MCP is "not found", the investigate step knows to fall back to CLI tools per convention 56.
