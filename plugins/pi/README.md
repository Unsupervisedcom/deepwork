# DeepWork for Pi

Pi package resources for the main DeepWork plugin. This package includes the
DeepWork skills, the Pi extension glue, and an MCP adapter dependency so Pi can
talk to `deepwork serve`.

Install from this repository:

```bash
pi install git:github.com/Unsupervisedcom/deepwork
```

Then run Pi in a project and use:

```text
/deepwork_setup
```

That command merges the DeepWork MCP server into the project `.mcp.json` and
reloads Pi resources.

## Optional Parallel Reviews

DeepWork can use `tintinweb/pi-subagents` for `/review` when it is installed:

```bash
pi install npm:@tintinweb/pi-subagents
```

The DeepWork extension does not check for it at startup. The first `/review` run
pings the `subagents:rpc:ping` bus endpoint and caches whether the extension is
available for that Pi session. When available, review tasks are spawned through
`subagents:rpc:spawn`; otherwise DeepWork injects the same tasks back into the
current session for sequential review.
