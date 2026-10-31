# Fetch remotely compiled PDFs from GitHub 'documentation' branch and sync to Google Drive
param(
    [string]$Repo = "pn-minh/layoutlmv3-1",
    [string]$Branch = "documentation"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SyncScript = Join-Path $ScriptDir "sync_thesis_to_gdrive.ps1"

Write-Host "=== Fetching Remotely Compiled PDFs ($Repo @ $Branch) & Syncing to Google Drive ===" -ForegroundColor Magenta
& powershell.exe -ExecutionPolicy Bypass -File $SyncScript -FetchRemote -Repo $Repo -Branch $Branch
