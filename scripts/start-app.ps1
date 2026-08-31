<#
.SYNOPSIS
    Start the wogd-ddsp-trainer application in either debug or release mode.

.DESCRIPTION
    Ensures the frontend build is current, then starts the whole application
    (backend + frontend) together.

    Debug mode:
      - Rebuilds the frontend only if the build is missing/stale (vite build
        with --mode development).
      - Starts the backend with debugpy so VSCode can attach a debugger, and
        starts the Vite dev server (http://127.0.0.1:5173).
      - To debug the backend: start this task, then press F5 with the
        "Debug Backend (attach)" launch config in .vscode/launch.json.

    Release mode:
      - Rebuilds the frontend only if the build is missing/stale (vite build).
      - Starts the backend serving webui/dist (WOGD_SERVE_STATIC=1). The
        frontend and backend are served together at http://127.0.0.1:8000.

    Both processes run in the foreground of this task's terminal so their logs
    stay visible; Ctrl+C terminates them together.

.PARAMETER Mode
    "Debug" or "Release".
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Debug", "Release")]
    [string]$Mode
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot | Split-Path -Parent
$webui = Join-Path $root "webui"
$dist = Join-Path $webui "dist"
$python = Join-Path $root ".venv\Scripts\python.exe"
$backendPort = 8000
$debugPort = 5678

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-BuildIsCurrent {
    if (-not (Test-Path -LiteralPath $dist)) {
        return $false
    }
    $distFiles = Get-ChildItem -LiteralPath $dist -Recurse -File -ErrorAction SilentlyContinue
    if (-not $distFiles) {
        return $false
    }
    $newestDist = ($distFiles | Measure-Object -Property LastWriteTime -Maximum).Maximum

    $sourceRoots = @(
        (Join-Path $webui "src"),
        (Join-Path $webui "index.html"),
        (Join-Path $webui "vite.config.js"),
        (Join-Path $webui "package.json")
    )
    $newestSrc = [datetime]::MinValue
    foreach ($s in $sourceRoots) {
        if (Test-Path -LiteralPath $s) {
            $item = Get-Item -LiteralPath $s
            if ($item.PSIsContainer) {
                $files = Get-ChildItem -LiteralPath $s -Recurse -File -ErrorAction SilentlyContinue
                foreach ($f in $files) {
                    if ($f.LastWriteTime -gt $newestSrc) { $newestSrc = $f.LastWriteTime }
                }
            }
            elseif ($item.LastWriteTime -gt $newestSrc) {
                $newestSrc = $item.LastWriteTime
            }
        }
    }
    return $newestSrc -le $newestDist
}

function Invoke-Build {
    Push-Location $webui
    try {
        if ($Mode -eq "Debug") {
            Write-Step "Building frontend (debug mode)..."
            & npm run build -- --mode development
        }
        else {
            Write-Step "Building frontend (release mode)..."
            & npm run build
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Step "wogd-ddsp-trainer start ($Mode)"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python venv not found at: $python (run: python -m venv .venv)"
}

if (Test-BuildIsCurrent) {
    Write-Host "Frontend build is up to date (no rebuild needed)."
}
else {
    Invoke-Build
}

if ($Mode -eq "Debug") {
    Write-Step "Starting backend with debugpy on :$backendPort (debugger :$debugPort)..."
    Write-Host "  Attach your debugger: F5 -> 'Debug Backend (attach)' (listen $debugPort)."

    $backend = Start-Process -FilePath $python -ArgumentList @(
        "-m", "debugpy",
        "--listen", "127.0.0.1:$debugPort",
        "--wait-for-client",
        "-m", "uvicorn", "server.main:app",
        "--host", "127.0.0.1", "--port", "$backendPort"
    ) -WorkingDirectory $root -PassThru -NoNewWindow

    Start-Sleep -Seconds 2
    Write-Step "Starting Vite dev server on :5173..."
    Push-Location $webui
    try {
        & npm run dev
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Step "Starting backend serving webui/dist on :$backendPort..."
    $env:WOGD_SERVE_STATIC = "1"
    & $python -m uvicorn server.main:app --host 127.0.0.1 --port $backendPort
    Remove-Item Env:WOGD_SERVE_STATIC -ErrorAction SilentlyContinue
}
