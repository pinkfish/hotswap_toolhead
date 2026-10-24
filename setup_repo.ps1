# Creates Documents\github\hotswap_toolhead and pushes it to a new GitHub repo.
# Needs: git, and the GitHub CLI (gh) logged in (`gh auth login`).
# Usage: run from the unzipped hotswap_toolhead folder:  .\setup_repo.ps1  [-Public]
param([switch]$Public)
$ErrorActionPreference = "Stop"
$vis = if ($Public) { "--public" } else { "--private" }
$src = $PSScriptRoot
$dest = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "github\hotswap_toolhead"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git is not installed" }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "GitHub CLI (gh) is not installed: https://cli.github.com" }
gh auth status *> $null; if ($LASTEXITCODE -ne 0) { throw "Run 'gh auth login' first" }
if ($src -ne $dest) {
  if (Test-Path $dest) { throw "$dest already exists - move or delete it first" }
  New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
  Copy-Item -Recurse $src $dest
}
Set-Location $dest
git init -q -b main
git add .
git commit -q -m "Initial commit: 24 V CAN toolhead board design, KiCad project and generator"
gh repo create hotswap_toolhead $vis --source=. --remote=origin --push --description "24 V CAN toolhead board: heater, fan, thermistor, USB debug (STM32G0B1, Klipper)"
Write-Host "Done: $dest"
