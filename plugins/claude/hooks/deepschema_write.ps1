# deepschema_write.ps1 - DeepSchema write hook
#
# PostToolUse hook for Write/Edit - validates files against applicable
# DeepSchemas by piping the hook input through `deepwork hook deepschema_write`.
#
# Input (stdin):  JSON from Claude Code PostToolUse hook
# Output (stdout): JSON response from deepwork hook deepschema_write
# Exit codes:
#   0 - Validation passed (or no applicable schema)
#   1 - Validation failed

$ErrorActionPreference = 'Stop'

try {
    # ==== Read stdin ====
    $Input = @($Input) -join "`n"
    if (-not $Input) {
        $Input = [Console]::In.ReadToEnd()
    }

    # ==== Set platform env var ====
    $env:DEEPWORK_HOOK_PLATFORM = 'claude'

    # ==== Pipe through deepwork CLI and propagate exit code ====
    $Result = $Input | deepwork hook deepschema_write
    $ExitCode = $LASTEXITCODE

    if ($Result) {
        Write-Output $Result
    }

    exit $ExitCode
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
