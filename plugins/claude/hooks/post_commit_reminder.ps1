<#
.SYNOPSIS
    Post-commit reminder hook for DeepWork Claude Code plugin.

.DESCRIPTION
    Triggers after Bash tool uses that contain "git commit" to remind
    the agent to run the review skill.

.INPUTS
    JSON object on stdin with structure: { "tool_input": { "command": "..." } }

.OUTPUTS
    JSON object on stdout with hookSpecificOutput when the command contains
    "git commit". No output otherwise.

.NOTES
    Exit codes:
      0 - Success (hook matched or no match)
      0 - On error, outputs {} and exits 0 to avoid blocking the agent
#>

$ErrorActionPreference = 'Stop'

try {
    $Input = [Console]::In.ReadToEnd()
    $Parsed = $Input | ConvertFrom-Json
    $Command = $Parsed.tool_input.command

    if ($Command -and $Command -match 'git commit') {
        Write-Output '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"You **MUST** use AskUserQuestion tool to offer to the user to run the `review` skill to review the changes you just committed if you have not run a review recently."}}'
    }
}
catch {
    Write-Output '{}'
}
