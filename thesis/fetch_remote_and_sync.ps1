# Fetch remotely compiled PDFs from GitHub Actions / Release and sync to Google Drive
param(
    [string]$Repo = "pn-minh/layoutlmv3-1",
    [string]$ReleaseTag = "latest"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SyncScript = Join-Path $ScriptDir "sync_thesis_to_gdrive.ps1"

Write-Host "=== Fetching Remotely Compiled PDFs ($Repo@$ReleaseTag) & Syncing to Google Drive ===" -ForegroundColor Magenta
& powershell.exe -ExecutionPolicy Bypass -File $SyncScript -FetchRemote -Repo $Repo -ReleaseTag $ReleaseTag
