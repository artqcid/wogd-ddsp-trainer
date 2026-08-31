<#
.SYNOPSIS
    Build a self-contained, portable Windows package of the application.

.DESCRIPTION
    Produces a distributable folder under `dist/installer/` that runs the app
    entirely from its own venv - no global Python install, no changes to the
    user's machine-only configuration. This is the packaging precursor to the
    full NSIS/InnoSetup Windows installer (which is a later milestone).

    The package contains:
      - the backend source (server/, dataset/, model/, train/, inference/)
      - the production frontend build (webui/dist)
      - the application venv (Python interpreter + all runtime libraries)
      - the launch scripts (start-app.ps1) + a double-click `start.bat` that
        boots uvicorn serving webui/dist

    User data is NOT bundled: at first run the app places its data directory
    under %LOCALAPPDATA%\wogd-ddsp-trainer (see server/paths.py). Nothing on
    the host is installed or modified.

.PARAMETER BuildFrontend
    If true (default), rebuilds webui/dist from source beforehand.
#>
param(
    [bool]$BuildFrontend = $true
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot | Split-Path -Parent
$webui = Join-Path $root "webui"
$python = Join-Path $root ".venv\Scripts\python.exe"

$outRoot = Join-Path $root "dist\installer"
$appName = "wogd-ddsp-trainer"
$pkgDir = Join-Path $outRoot $appName

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

# 1. Ensure frontend is built.
if ($BuildFrontend) {
    Write-Step "Building production frontend..."
    Push-Location $webui
    try {
        & npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed with exit code $LASTEXITCODE" }
    }
    finally {
        Pop-Location
    }
}
elseif (-not (Test-Path -LiteralPath (Join-Path $webui "dist"))) {
    throw "webui/dist is missing. Run with -BuildFrontend or build it first."
}

# 2. Verify the venv exists (self-contained Python + libraries).
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python venv not found at: $python (run: python -m venv .venv)"
}

# 3. Clear the previous package output.
Write-Step "Preparing package directory: $pkgDir"
if (Test-Path -LiteralPath $pkgDir) {
    Remove-Item -LiteralPath $pkgDir -Recurse -Force
}
$null = New-Item -ItemType Directory -Path $pkgDir -Force

# 4. Copy backend source + frontend build.
Write-Step "Copying backend source..."
foreach ($d in @("server", "dataset", "model", "train", "inference")) {
    $src = Join-Path $root $d
    if (Test-Path -LiteralPath $src) {
        Copy-Item -Path $src -Destination $pkgDir -Recurse
    }
}

Write-Step "Copying frontend build (webui/dist)..."
$distDir = New-Item -ItemType Directory -Path (Join-Path $pkgDir "webui\dist") -Force
Copy-Item -Path (Join-Path $webui "dist\*") -Destination $distDir -Recurse

Write-Step "Copying launcher scripts and metadata..."
Copy-Item -Path (Join-Path $root "scripts") -Destination $pkgDir -Recurse
Copy-Item -Path (Join-Path $root "pyproject.toml") -Destination $pkgDir -Force

# 5. Copy the venv (Python interpreter + all runtime libraries) so the package
#    is fully self-contained and installs nothing globally.
Write-Step "Copying application venv (this can take a while)..."
Copy-Item -Path (Join-Path $root ".venv") -Destination $pkgDir -Recurse

# 6. Write a double-click launcher that serves the app from its bundled venv.
$startBat = @"
@echo off
setlocal
cd /d "%~dp0"
echo Starting wogd-ddsp-trainer... open http://127.0.0.1:8000
set "WOGD_SERVE_STATIC=1"
".venv\Scripts\python.exe" -m uvicorn server.main:app --host 127.0.0.1 --port 8000
"@
Set-Content -LiteralPath (Join-Path $pkgDir "start.bat") -Value $startBat -Encoding ASCII

# 7. Indicate run-only note.
$readme = @"
wogd-ddsp-trainer - portable package

This folder runs the full application from its own bundled venv.

To start:
  double-click start.bat
Then open http://127.0.0.1:8000 in a browser.

User data (datasets, runs, database) is stored under
%LOCALAPPDATA%\wogd-ddsp-trainer on first run and can be changed in
the app (Settings -> Data directory).

No global Python installation or user configuration is modified.
"@
Set-Content -LiteralPath (Join-Path $pkgDir "README.txt") -Value $readme -Encoding UTF8

Write-Step "Created package: $pkgDir"
Write-Host "  - backend source + webui/dist (production build)"
Write-Host "  - bundled .venv (Python + libraries)"
Write-Host "  - start.bat / scripts/start-app.ps1 launchers"
Write-Host "Next: zip $pkgDir and distribute, or wrap in a Windows installer (later milestone)."
