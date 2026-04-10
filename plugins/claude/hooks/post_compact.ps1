# post_compact.ps1 - Post-compaction context restoration hook
#
# Restores DeepWork workflow context after Claude Code compacts its context.
# Registered as a SessionStart hook with matcher "compact" in hooks.json.
#
# Input (stdin):  JSON from Claude Code SessionStart hook (contains .cwd)
# Output (stdout): JSON with hookSpecificOutput.additionalContext, or empty {}
# Exit codes:
#   0 - Always (failures produce empty {} response)

$ErrorActionPreference = 'Stop'

function Write-EmptyAndExit {
    Write-Output '{}'
    exit 0
}

try {
    # ==== Parse input ====
    $Input_ = [Console]::In.ReadToEnd()
    $InputObj = $Input_ | ConvertFrom-Json
    $Cwd = $InputObj.cwd

    if (-not $Cwd) {
        Write-EmptyAndExit
    }

    # ==== Fetch active sessions ====
    try {
        $StackRaw = & deepwork jobs get-stack --path $Cwd 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-EmptyAndExit
        }
    } catch {
        Write-EmptyAndExit
    }

    $StackJson = $StackRaw | Out-String
    $Stack = $StackJson | ConvertFrom-Json

    # ==== Check for active sessions ====
    $Sessions = $Stack.active_sessions
    if (-not $Sessions -or $Sessions.Count -eq 0) {
        Write-EmptyAndExit
    }

    $SessionCount = $Sessions.Count

    # ==== Build markdown context from active sessions ====
    $Context = @"
# DeepWork Workflow Context (Restored After Compaction)

You are in the middle of a DeepWork workflow. Use the DeepWork MCP tools to continue.
Call ``finished_step`` with your outputs and the ``session_id`` shown below when you complete the current step.

"@

    for ($i = 0; $i -lt $SessionCount; $i++) {
        $Session = $Sessions[$i]

        $SessionId     = if ($Session.session_id)                { $Session.session_id } else { '' }
        $JobName       = if ($Session.job_name)                  { $Session.job_name } else { '' }
        $WorkflowName  = if ($Session.workflow_name)             { $Session.workflow_name } else { '' }
        $Goal          = if ($Session.goal)                      { $Session.goal } else { '' }
        $CurrentStep   = if ($Session.current_step_id)           { $Session.current_step_id } else { '' }
        $StepNum       = if ($null -ne $Session.step_number)     { "$($Session.step_number)" } else { '' }
        $TotalSteps    = if ($null -ne $Session.total_steps)     { "$($Session.total_steps)" } else { '' }
        $CompletedArr  = if ($Session.completed_steps)           { $Session.completed_steps } else { @() }
        $Completed     = $CompletedArr -join ', '
        $CommonInfo    = if ($Session.common_job_info)           { $Session.common_job_info } else { '' }
        $StepInstr     = if ($Session.current_step_instructions) { $Session.current_step_instructions } else { '' }

        $StepLabel = $CurrentStep
        if ($StepNum -ne '' -and $TotalSteps -ne '') {
            $StepLabel = "$CurrentStep (step $StepNum of $TotalSteps)"
        }

        $Context += @"

## Active Session
- **session_id**: ``$SessionId`` (pass this to ``finished_step``, ``abort_workflow``, and ``go_to_step``)
- **Workflow**: $JobName/$WorkflowName
- **Goal**: $Goal
- **Current Step**: $StepLabel
"@

        if ($Completed -ne '') {
            $Context += "`n- **Completed Steps**: $Completed"
        }

        if ($CommonInfo -ne '') {
            $Context += @"

### Common Job Info
$CommonInfo
"@
        }

        if ($StepInstr -ne '') {
            $Context += @"

### Current Step Instructions
$StepInstr
"@
        }

        $Context += "`n"
    }

    # ==== Output hook response ====
    $Output = @{
        hookSpecificOutput = @{
            hookEventName     = 'SessionStart'
            additionalContext = $Context
        }
    }
    $Output | ConvertTo-Json -Depth 5 -Compress
    exit 0

} catch {
    Write-EmptyAndExit
}
