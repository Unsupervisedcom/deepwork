import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

const deepworkServer = {
  command: "uvx",
  args: ["deepwork", "serve", "--platform", "pi"],
  lifecycle: "lazy",
  directTools: [
    "get_workflows",
    "start_workflow",
    "finished_step",
    "go_to_step",
    "abort_workflow",
    "get_review_instructions",
    "get_configured_reviews",
    "mark_review_as_passed",
    "get_named_schemas",
  ],
};

let subagentsAvailability: Promise<boolean> | null = null;

type ReviewTask = {
  description: string;
  reviewer: string;
  promptFile: string;
};

type RpcReply<T> =
  | { success: true; data: T }
  | { success: false; error: string };

export default function deepworkPi(pi: ExtensionAPI) {
  pi.registerCommand("review", {
    description: "Run DeepWork Reviews",
    handler: async (_args, ctx) => {
      await runDeepworkReview(pi, ctx.cwd);
    },
  });

  pi.registerCommand("deepwork_review", {
    description: "Run DeepWork Reviews",
    handler: async (_args, ctx) => {
      await runDeepworkReview(pi, ctx.cwd);
    },
  });

  pi.registerCommand("deepwork_setup", {
    description: "Configure DeepWork MCP for this Pi project",
    handler: async (_args, ctx) => {
      const configPath = resolve(ctx.cwd, ".mcp.json");
      await mergeDeepworkMcpConfig(configPath);
      ctx.ui.notify("DeepWork MCP server added to .mcp.json. Reloading Pi resources.", "success");
      await ctx.reload();
    },
  });

  pi.registerCommand("deepwork_status", {
    description: "Show active DeepWork workflow stack",
    handler: async (_args, ctx) => {
      const stack = await getActiveWorkflowStack(ctx.cwd);
      ctx.ui.notify(stack ?? "No active DeepWork workflow sessions found.", "info");
    },
  });

  pi.on("session_start", async (_event, ctx) => {
    if (!hasDeepworkMcpConfig(ctx.cwd)) {
      ctx.ui.notify(
        "DeepWork is installed. Run /deepwork_setup once in this project to add the MCP server.",
        "info",
      );
    }
  });

  pi.on("before_agent_start", async (_event, ctx) => {
    const stack = await getActiveWorkflowStack(ctx.cwd);
    if (!stack) return;

    return {
      message: {
        customType: "deepwork-context",
        content: stack,
        display: false,
      },
    };
  });

  pi.on("tool_result", async (event, ctx) => {
    if (event.toolName === "bash") {
      const command = String((event.input as { command?: unknown }).command ?? "");
      if (/\bgit\s+commit\b/.test(command)) {
        pi.sendMessage(
          {
            customType: "deepwork-review-reminder",
            content: "A git commit just ran. If this branch has DeepWork review rules, run /review before merging.",
            display: true,
          },
          { deliverAs: "followUp" },
        );
      }
    }

    if (event.toolName !== "write" && event.toolName !== "edit") return;

    const filePath = toolFilePath(event.input);
    if (!filePath) return;

    const output = await runDeepworkHook("deepschema_write", {
      hook_event_name: "tool_result",
      cwd: ctx.cwd,
      tool_name: event.toolName,
      tool_input: { file_path: filePath },
    });
    const context = output?.hookSpecificOutput?.additionalContext;
    if (!context) return;

    return {
      content: [
        ...(Array.isArray(event.content) ? event.content : []),
        { type: "text", text: String(context) },
      ],
      details: {
        ...(typeof event.details === "object" && event.details !== null ? event.details : {}),
        deepwork: { deepschemaContext: context },
      },
    };
  });
}

async function runDeepworkReview(pi: ExtensionAPI, cwd: string): Promise<void> {
  const review = await runCommand("uvx", ["deepwork", "review", "--instructions-for", "pi", "--path", cwd], cwd);
  const output = review.stdout.trim();
  if (review.code !== 0) {
    pi.sendMessage(
      {
        customType: "deepwork-review-error",
        content: `DeepWork review setup failed.\n\n${review.stderr || output}`,
        display: true,
      },
      { deliverAs: "followUp" },
    );
    return;
  }

  const tasks = parseReviewTasks(output);
  if (tasks.length === 0) {
    pi.sendMessage(
      {
        customType: "deepwork-review-status",
        content: output || "No DeepWork review tasks to run.",
        display: true,
      },
      { deliverAs: "followUp" },
    );
    return;
  }

  const subagentsAvailable = await getSubagentsAvailable(pi);
  if (!subagentsAvailable) {
    pi.sendMessage(
      {
        customType: "deepwork-review-tasks",
        content: sequentialReviewPrompt(tasks),
        display: true,
      },
      { deliverAs: "followUp" },
    );
    return;
  }

  const spawned: string[] = [];
  const failed: ReviewTask[] = [];
  for (const task of tasks) {
    const reply = await requestSubagentRpc<{ id: string }>(pi, "spawn", {
      type: task.reviewer === "deepwork-reviewer" ? "general-purpose" : task.reviewer,
      prompt: subagentReviewPrompt(task),
      options: {
        description: task.description,
        run_in_background: true,
      },
    });

    if (reply.success) {
      spawned.push(reply.data.id);
    } else {
      failed.push(task);
    }
  }

  const summary = [
    spawned.length > 0
      ? `Spawned ${spawned.length} DeepWork review subagent(s): ${spawned.join(", ")}.`
      : "No DeepWork review subagents were spawned.",
    failed.length > 0
      ? `\n\n${failed.length} task(s) failed to spawn. Run these sequentially:\n\n${sequentialReviewPrompt(failed)}`
      : "",
  ].join("");

  pi.sendMessage(
    {
      customType: "deepwork-review-subagents",
      content: summary,
      display: true,
    },
    { deliverAs: "followUp" },
  );
}

async function getSubagentsAvailable(pi: ExtensionAPI): Promise<boolean> {
  if (subagentsAvailability === null) {
    subagentsAvailability = requestSubagentRpc<{ version: string }>(pi, "ping", {}).then(
      (reply) => reply.success,
    );
  }
  return subagentsAvailability;
}

function requestSubagentRpc<T>(
  pi: ExtensionAPI,
  method: "ping" | "spawn" | "stop",
  payload: Record<string, unknown>,
  timeoutMs = 750,
): Promise<RpcReply<T>> {
  return new Promise((resolveReply) => {
    const requestId = randomUUID();
    const replyEvent = `subagents:rpc:${method}:reply:${requestId}`;
    let settled = false;
    let unsubscribe: (() => void) | undefined;
    let timeout: ReturnType<typeof setTimeout>;

    const finish = (reply: RpcReply<T>) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      unsubscribe?.();
      resolveReply(reply);
    };

    timeout = setTimeout(() => {
      finish({ success: false, error: "pi-subagents did not reply to RPC ping." });
    }, timeoutMs);

    unsubscribe = pi.events.on(replyEvent, (reply: RpcReply<T>) => {
      finish(reply);
    });

    pi.events.emit(`subagents:rpc:${method}`, {
      ...payload,
      requestId,
    });
  });
}

function parseReviewTasks(output: string): ReviewTask[] {
  const tasks: ReviewTask[] = [];
  let current: Partial<ReviewTask> = {};

  const flush = () => {
    if (current.description && current.reviewer && current.promptFile) {
      tasks.push({
        description: current.description,
        reviewer: current.reviewer,
        promptFile: current.promptFile,
      });
    }
    current = {};
  };

  for (const line of output.split(/\r?\n/)) {
    if (line.startsWith("description: ")) {
      flush();
      current.description = line.slice("description: ".length).trim();
    } else if (line.trimStart().startsWith("reviewer: ")) {
      current.reviewer = line.trim().slice("reviewer: ".length).trim();
    } else if (line.trimStart().startsWith("prompt_file: ")) {
      current.promptFile = line.trim().slice("prompt_file: ".length).trim();
    }
  }
  flush();

  return tasks;
}

function subagentReviewPrompt(task: ReviewTask): string {
  return [
    `You are running a DeepWork review task: ${task.description}.`,
    `Read ${task.promptFile} and follow its instructions exactly.`,
    "Report findings with file and line references. If there are no findings, say so clearly.",
  ].join("\n\n");
}

function sequentialReviewPrompt(tasks: ReviewTask[]): string {
  const taskLines = tasks
    .map(
      (task, index) =>
        `${index + 1}. ${task.description}\n   reviewer: ${task.reviewer}\n   prompt_file: ${task.promptFile}`,
    )
    .join("\n\n");

  return [
    "Run these DeepWork review tasks sequentially in this session.",
    "For each task, read the prompt_file and follow its instructions exactly. Report findings with file and line references.",
    taskLines,
  ].join("\n\n");
}

async function mergeDeepworkMcpConfig(configPath: string): Promise<void> {
  let config: Record<string, unknown> = {};
  if (existsSync(configPath)) {
    const raw = await readFile(configPath, "utf8");
    config = raw.trim() ? JSON.parse(raw) : {};
  }

  const mcpServers = asRecord(config.mcpServers);
  mcpServers.deepwork = deepworkServer;
  config.mcpServers = mcpServers;

  await mkdir(dirname(configPath), { recursive: true });
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`, "utf8");
}

function hasDeepworkMcpConfig(cwd: string): boolean {
  for (const rel of [".mcp.json", ".pi/mcp.json"]) {
    const configPath = resolve(cwd, rel);
    if (!existsSync(configPath)) continue;
    try {
      const config = JSON.parse(readFileSync(configPath, "utf8"));
      if (asRecord(config.mcpServers).deepwork) return true;
    } catch {
      continue;
    }
  }
  return false;
}

async function getActiveWorkflowStack(cwd: string): Promise<string | null> {
  if (!existsSync(resolve(cwd, ".deepwork", "tmp"))) return null;

  const result = await runCommand("uvx", ["deepwork", "jobs", "get-stack", "--path", cwd], cwd);
  if (result.code !== 0 || !result.stdout.trim()) return null;

  try {
    const stack = JSON.parse(result.stdout);
    if (!Array.isArray(stack) || stack.length === 0) return null;
    return `Active DeepWork workflow stack:\n\n\`\`\`json\n${JSON.stringify(stack, null, 2)}\n\`\`\``;
  } catch {
    return null;
  }
}

async function runDeepworkHook(
  hookName: string,
  input: Record<string, unknown>,
): Promise<Record<string, any> | null> {
  const result = await runCommand(
    "uvx",
    ["deepwork", "hook", hookName],
    String(input.cwd ?? process.cwd()),
    JSON.stringify(input),
    { DEEPWORK_HOOK_PLATFORM: "pi" },
  );
  if (result.code !== 0 || !result.stdout.trim()) return null;

  try {
    return JSON.parse(result.stdout);
  } catch {
    return null;
  }
}

function runCommand(
  command: string,
  args: string[],
  cwd: string,
  stdin?: string,
  env?: Record<string, string>,
): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolveResult) => {
    const child = spawn(command, args, {
      cwd,
      env: { ...process.env, ...env },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.on("error", (error) => {
      resolveResult({ code: 1, stdout, stderr: String(error) });
    });
    child.on("close", (code) => {
      resolveResult({ code: code ?? 1, stdout, stderr });
    });
    if (stdin) child.stdin.write(stdin);
    child.stdin.end();
  });
}

function asRecord(value: unknown): Record<string, any> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, any>)
    : {};
}

function toolFilePath(input: unknown): string | null {
  const data = asRecord(input);
  const value = data.file_path ?? data.filePath ?? data.path;
  return typeof value === "string" && value.length > 0 ? value : null;
}
