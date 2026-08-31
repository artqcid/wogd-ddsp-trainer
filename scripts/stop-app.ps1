<#
.SYNOPSIS
    Stop the wogd-ddsp-trainer application and free all associated ports.
.DESCRIPTION
    Kills any running uvicorn, Vite dev server, and debugpy processes
    that were started by start-app.ps1, and frees ports 8000, 5173, and 5678.
.PARAMETER Mode
    "Debug" or "Release". Only affects the log message; both modes clean the
    same set of processes/ports.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Debug", "Release")]
    [string]$Mode
)

$stopped = $false

function Stop-ProcessOnPort($Port, $Label) {
    $conn = netstat -ano | Select-String "LISTENING" | Select-String ":$Port\s"
    foreach ($line in $conn) {
        $parts = $line.ToString() -split '\s+'
        $pid = $parts[-1]
        if ($pid -and $pid -match '^\d+$') {
            try {
                $proc = Get-Process -Id $pid -ErrorAction Stop
                if ($proc.SessionId -eq (Get-Process -Id $PID).SessionId) {
                    Write-Host "  Stopping $Label (PID $pid on port $Port)..."
                    $proc.Kill()
                    $stopped = $true
                }
            }
            catch {
                # already gone
            }
        }
    }
}

Write-Host "==> wogd-ddsp-trainer stop ($Mode)" -ForegroundColor Cyan

Stop-ProcessOnPort -Port 8000 -Label "uvicorn (backend)"
Stop-ProcessOnPort -Port 5173 -Label "Vite (dev server)"
Stop-ProcessOnPort -Port 5678 -Label "debugpy"

if (-not $stopped) {
    Write-Host "  No running processes found on ports 8000/5173/5678."
}
else {
    Write-Host "  Done — ports freed."
}