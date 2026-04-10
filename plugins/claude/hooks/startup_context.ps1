# startup_context.ps1 - Inject Claude Code session and agent IDs into context
#
# Runs on SessionStart and SubagentStart to provide agents with their
# CLAUDE_CODE_SESSION_ID (and CLAUDE_CODE_AGENT_ID for sub-agents).
# These IDs are used by MCP tools to locate persistent workflow state.
#
# Input (stdin):  JSON from Claude Code hook (contains .session_id, optionally .agent_id)
# Output (stdout): JSON with hookSpecificOutput.additionalContext, or empty {}
# Exit codes:
#   0 - Always (failures produce empty {} response)

$ErrorActionPreference = 'Stop'

try {
    # ==== Parse input ====
    $Input = @($Input) -join "`n"
    if (-not $Input) {
        $Input = [Console]::In.ReadToEnd()
    }
    $Json = $Input | ConvertFrom-Json

    $SessionId = $Json.session_id
    if (-not $SessionId) {
        Write-Output '{}'
        exit 0
    }

    $EventName = if ($Json.hook_event_name) { $Json.hook_event_name } else { 'SessionStart' }
    $AgentId = $Json.agent_id

    # ==== Build context string ====
    $Ctx = "CLAUDE_CODE_SESSION_ID=$SessionId"
    if ($AgentId) {
        $Ctx += "`nCLAUDE_CODE_AGENT_ID=$AgentId"
    }

    # Inject DeepPlan trigger for planning mode
    $DeepPlanMsg = 'When you enter plan mode and begin working on a plan, start the DeepWork workflow create_deep_plan (job: deepplan) via start_workflow before doing anything else. The workflow will guide you through structured planning. Its instructions supersede the default planning phases.'
    $Ctx += "`n$DeepPlanMsg"

    # ==== Output hook response ====
    $Response = @{
        hookSpecificOutput = @{
            hookEventName     = $EventName
            additionalContext = $Ctx
        }
    }
    $Response | ConvertTo-Json -Depth 3 -Compress
}
catch {
    Write-Output '{}'
    exit 0
}
