---
name: deepwork-openclaw-bootstrap
description: "Inject DeepWork session and resume guidance into OpenClaw bootstrap context"
metadata:
  {
    "openclaw":
      {
        "emoji": "🧭",
        "events": ["agent:bootstrap"],
        "install": [{ "id": "deepwork", "kind": "bundled", "label": "Bundled with DeepWork OpenClaw plugin" }],
      },
  }
---

# DeepWork OpenClaw Bootstrap

Injects a small synthetic bootstrap note that tells the agent which `session_id`
to use for DeepWork MCP tools in the current OpenClaw session, and whether it
should try `deepwork__get_active_workflow` to restore prior DeepWork state.
