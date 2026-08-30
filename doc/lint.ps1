# wogd-ddsp-trainer LLM-Wiki Lint Script
#
# Checks the doc/ wiki for consistency problems:
#   1. Orphan pages (files not listed in index.md)
#   2. Duplicate index entries
#   3. Stale claims (stale_after >= today)
#   4. Cross-reference health (deprecated files not in archive/)
#   5. Summary report
#
# Usage: pwsh doc/lint.ps1
# Exit code: 0 = all clean, 1 = warnings, 2 = errors

$ErrorActionPreference = "Stop"
$today = [DateTime]::Today
$docDir = $PSScriptRoot
$indexFile = Join-Path $docDir "index.md"
$hasErrors = $false
$hasWarnings = $false

Write-Host "=== wogd-ddsp-trainer Wiki Lint ===" -ForegroundColor Cyan
Write-Host "Date: $($today.ToString('yyyy-MM-dd'))`n" -ForegroundColor Gray

# Helper: extract all `](./some/path)` links from index.md
function Get-IndexLinks {
  param([string]$Path)
  $content = Get-Content -Path $Path -Raw
  $pattern = '\]\(\./([^)]+)\)'
  $matches = [regex]::Matches($content, $pattern)
  return $matches | ForEach-Object { $_.Groups[1].Value -replace '/', '\' } | ForEach-Object { $_.Trim() }
}

# Helper: parse YAML frontmatter (flat keys only)
function Get-Frontmatter {
  param([string]$Path)
  $content = Get-Content -Path $Path -Raw
  if ($content -match '^---\s*\n(.*?)\n---') {
    $yaml = $Matches[1]
    $result = @{}
    foreach ($line in $yaml -split '\n') {
      if ($line -match '^(\w+):\s*(.*)') {
        $result[$Matches[1]] = $Matches[2].Trim().Trim('"'' ')
      }
    }
    return $result
  }
  return $null
}

# --- 1. Orphan pages --------------------------------------------------------
Write-Host "Checking orphan pages..." -ForegroundColor Yellow
$wl = Get-ChildItem -Path $docDir -Filter "*.md" -Recurse | Where-Object {
  $_.Name -notin @("index.md", "log.md", "code_wiki.md")
}
$indexLinks = Get-IndexLinks -Path $indexFile
foreach ($f in $wl) {
  $rel = $f.FullName.Substring($docDir.Length).TrimStart('\')
  if ($indexLinks -notcontains $rel) {
    Write-Host "  ORPHAN: $rel" -ForegroundColor Red
    $hasErrors = $true
  }
}

# --- 2. Duplicate index entries ---------------------------------------------
Write-Host "Checking duplicate index entries..." -ForegroundColor Yellow
$dup = $indexLinks | Group-Object | Where-Object { $_.Count -gt 1 }
foreach ($d in $dup) {
  Write-Host "  DUPLICATE: $($d.Name) x$($d.Count)" -ForegroundColor Red
  $hasErrors = $true
}

# --- 3. Stale claims --------------------------------------------------------
Write-Host "Checking stale claims..." -ForegroundColor Yellow
foreach ($f in $wl) {
  $fm = Get-Frontmatter -Path $f.FullName
  if ($fm -and $fm["stale_after"]) {
    try {
      $staleDate = [DateTime]::ParseExact($fm["stale_after"], "yyyy-MM-dd", $null)
      if ($today -ge $staleDate) {
        Write-Host "  STALE: $($f.Name) (stale_after $($fm['stale_after']))" -ForegroundColor Red
        $hasErrors = $true
      }
    } catch {
      Write-Host "  WARN: $($f.Name) unparseable stale_after '$($fm['stale_after'])'" -ForegroundColor Yellow
      $hasWarnings = $true
    }
  }
}

# --- 4. Cross-reference health (deprecated files) ---------------------------
Write-Host "Checking deprecated files..." -ForegroundColor Yellow
foreach ($f in $wl) {
  $fm = Get-Frontmatter -Path $f.FullName
  if ($fm -and $fm["status"] -eq "deprecated") {
    $parent = Split-Path -Leaf (Split-Path -Parent $f.FullName)
    if ($parent -ne "archive") {
      Write-Host "  DEPRECATED-NOT-ARCHIVED: $($f.Name)" -ForegroundColor Red
      $hasErrors = $true
    }
  }
}

# --- Summary ----------------------------------------------------------------
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
if ($hasErrors) {
  Write-Host "Errors: YES (fix before sync)" -ForegroundColor Red
  exit 2
}
if ($hasWarnings) {
  Write-Host "Warnings: YES" -ForegroundColor Yellow
  Write-Host "Wiki lint: clean (with warnings)" -ForegroundColor Green
  exit 1
}
Write-Host "Wiki lint: all clean" -ForegroundColor Green
exit 0
