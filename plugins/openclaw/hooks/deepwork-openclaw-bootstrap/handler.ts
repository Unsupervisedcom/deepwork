import fs from "node:fs";
import path from "node:path";

const SYNTHETIC_NOTES = [
  {
    name: "BOOTSTRAP.md",
    relativePath: ".deepwork/tmp/openclaw/DEEPWORK_OPENCLAW_BOOTSTRAP.md",
  },
  {
    name: "TOOLS.md",
    relativePath: ".deepwork/tmp/openclaw/DEEPWORK_OPENCLAW.md",
  },
] as const;

function readTrimmedString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

const handler = async (event: any) => {
  if (event?.type !== "agent" || event?.action !== "bootstrap") {
    return;
  }

  const context = event.context ?? {};
  if (!Array.isArray(context.bootstrapFiles)) {
    return;
  }

  const workspaceDir = readTrimmedString(context.workspaceDir);
  const sessionId = readTrimmedString(context.sessionId);
  if (!workspaceDir || !sessionId) {
    return;
  }

  const sessionKey = readTrimmedString(context.sessionKey) || "(unknown)";
  const agentId = readTrimmedString(context.agentId) || "(unknown)";
  const syntheticNotes = SYNTHETIC_NOTES.map((note) => ({
    ...note,
    path: path.join(workspaceDir, note.relativePath),
  }));
  const statePath = path.join(
    workspaceDir,
    ".deepwork",
    "tmp",
    "sessions",
    "openclaw",
    `session-${sessionId}`,
    "state.json",
  );
  const hasActiveState = fs.existsSync(statePath);

  const content = `# DeepWork OpenClaw Runtime

Use these values when calling DeepWork MCP tools from this OpenClaw session:

- session_id: \`${sessionId}\`
- session_key: \`${sessionKey}\`
- agent_id: \`${agentId}\`
- workspace_dir: \`${workspaceDir}\`

Guidance:

- Use the current OpenClaw session's \`sessionId\` as DeepWork \`session_id\`.
- Ignore any stale \`BOOTSTRAP.md\` files or hardcoded \`session_id\` values elsewhere in the workspace. The current OpenClaw session values above win.
- In OpenClaw, leave DeepWork \`agent_id\` unset unless you intentionally want a separate agent-scoped DeepWork state file.
- DeepWork relative paths are rooted at \`workspace_dir\`, not the plugin bundle directory.
- ${
    hasActiveState
      ? "DeepWork state already exists for this session. Call `deepwork__get_active_workflow` before starting a new workflow unless you are sure you want a second one."
      : "No DeepWork state has been detected for this session yet."
  }
- Before \`deepwork__finished_step\`, compare your outputs to \`step_expected_outputs\` or call \`deepwork__validate_step_outputs\`.
- For review work returned by DeepWork quality gates, prefer parallel OpenClaw sub-agents via \`sessions_spawn\`.
- Spawn all requested review sub-agents before waiting for completions.
- Keep DeepWork instruction paths workspace-relative; do not rewrite them as absolute host paths.
- Omit \`timeoutSeconds\` on review spawns so the runtime default applies. If a timeout value is required, use \`0\`.
- After all review spawns are accepted, use \`sessions_yield\` while you wait for completion events.
`;

  for (const note of syntheticNotes) {
    try {
      fs.mkdirSync(path.dirname(note.path), { recursive: true });
      fs.writeFileSync(note.path, content, "utf8");
    } catch {
      // Best-effort persistence for runtime session hints. The in-memory bootstrap
      // injection below still gives the model the same guidance if disk writes fail.
    }
  }

  context.bootstrapFiles = context.bootstrapFiles
    .filter((file: any) => {
      const filePath = readTrimmedString(file?.path);
      const fileName = readTrimmedString(file?.name);
      if (fileName === "BOOTSTRAP.md") {
        return false;
      }
      return !syntheticNotes.some((note) => note.path === filePath);
    })
    .concat(
      syntheticNotes.map((note) => ({
        name: note.name,
        path: note.path,
        content,
        missing: false,
      })),
    );
};

export default handler;
