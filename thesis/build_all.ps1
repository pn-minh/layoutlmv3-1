# Build LaTeX thesis and presentation copies using local Tectonic 0.15.0 compiler
param(
    [switch]$LocalOnly,
    [switch]$Slides,
    [switch]$Sync
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tectonic = Join-Path $ScriptDir "bin\tectonic.exe"

if (-not (Test-Path $Tectonic)) {
    Write-Error "Local Tectonic compiler not found at: $Tectonic"
}

Write-Host "=== [1/3] Compiling Model Architecture Diagram ===" -ForegroundColor Cyan
& $Tectonic (Join-Path $ScriptDir "figures\model_architecture_heads_style.tex") --outdir (Join-Path $ScriptDir "figures")

Write-Host "=== [2/3] Compiling Vietnamese Thesis (thesis/vi/main.tex) ===" -ForegroundColor Cyan
& $Tectonic (Join-Path $ScriptDir "vi\main.tex") --outdir (Join-Path $ScriptDir "vi")

Write-Host "=== [3/3] Compiling English Thesis (thesis/en/main.tex) ===" -ForegroundColor Cyan
& $Tectonic (Join-Path $ScriptDir "en\main.tex") --outdir (Join-Path $ScriptDir "en")

if ($Slides) {
    Write-Host "=== Compiling Weekly Presentation Slides ===" -ForegroundColor Cyan
    & $Tectonic (Join-Path $ScriptDir "presentation\weekly_update_slides.tex") --outdir (Join-Path $ScriptDir "presentation")
}

Write-Host "`n=== Local Compilation Complete! ===" -ForegroundColor Green
Write-Host "Vietnamese PDF : $(Join-Path $ScriptDir 'vi\main.pdf')"
Write-Host "English PDF    : $(Join-Path $ScriptDir 'en\main.pdf')"
if ($Slides) {
    Write-Host "Slides PDF     : $(Join-Path $ScriptDir 'presentation\weekly_update_slides.pdf')"
}

if (-not $LocalOnly -and $Sync) {
    $gdriveScript = Join-Path $ScriptDir "sync_thesis_to_gdrive.ps1"
    if (Test-Path $gdriveScript) {
        Write-Host "`n=== Syncing to Google Drive ===" -ForegroundColor Magenta
        & powershell.exe -ExecutionPolicy Bypass -File $gdriveScript
    }
}
