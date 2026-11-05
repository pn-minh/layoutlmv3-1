<#
.SYNOPSIS
    Automated launcher for LayoutLMv3 fine-tuning pipeline on a remote Vast.ai instance.
.DESCRIPTION
    Connects to the Vast.ai instance via SSH, updates the repository to origin/main,
    and starts scratch/run_vast_finetune.sh in the background. The instance will
    automatically resolve all environment issues, train the fine-tuned contrastive models,
    sync to Google Sheets & Google Drive, and self-destruct upon completion.
.PARAMETER SshCmd
    The full SSH command provided by Vast.ai (e.g., 'ssh -p 55757 root@36.139.132.16 -L 8080:localhost:8080')
.PARAMETER Cells
    Comma-separated list of cells to run (default: "24,25,26,27" for the Contrastive Loss suite)
.EXAMPLE
    .\scratch\launch_vast_remote.ps1 -SshCmd "ssh -p 55757 root@36.139.132.16"
#>
param(
    [Parameter(Mandatory=$false)]
    [string]$SshCmd = "",

    [Parameter(Mandatory=$false)]
    [string]$HostName = "",

    [Parameter(Mandatory=$false)]
    [int]$Port = 0,

    [Parameter(Mandatory=$false)]
    [string]$KeyPath = "$HOME/.ssh/id_ed25519",

    [Parameter(Mandatory=$false)]
    [string]$Cells = "24,25,26,27",

    [Parameter(Mandatory=$false)]
    [switch]$ForceRerun = $true
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [VAST.AI] REMOTE FINE-TUNING PIPELINE LAUNCHER" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Parse SSH command if provided
if ($SshCmd -match "-p\s+(\d+)\s+([^\s]+)@([^\s]+)") {
    $Port = [int]$matches[1]
    $User = $matches[2]
    $HostName = $matches[3]
} elseif ($SshCmd -match "([^\s]+)@([^\s]+)\s+-p\s+(\d+)") {
    $User = $matches[1]
    $HostName = $matches[2]
    $Port = [int]$matches[3]
}

if (-not $HostName) {
    Write-Host "[ERROR] Please provide a valid SSH command via -SshCmd or specify -HostName and -Port." -ForegroundColor Red
    Write-Host "Example: .\scratch\launch_vast_remote.ps1 -SshCmd `"ssh -p 55757 root@36.139.132.16`"" -ForegroundColor Yellow
    exit 1
}

if ($Port -eq 0) { $Port = 22 }
$User = "root"

Write-Host "[TARGET] Host: $HostName | Port: $Port | User: $User" -ForegroundColor Green
Write-Host "[TARGET] Cells to run: $Cells (Contrastive Loss Fine-Tuning Suite)" -ForegroundColor Green

# Generate temporary SSH options
$sshOpts = @(
    "-p", "$Port",
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "ConnectTimeout=10",
    "-o", "ServerAliveInterval=30"
)
if (Test-Path $KeyPath) {
    $sshOpts += @("-i", $KeyPath)
}

Write-Host "`n[1/3] Testing SSH connectivity..." -ForegroundColor Yellow
$testConn = ssh @sshOpts "$User@$HostName" "echo SSH_CONNECTED" 2>&1
if ($testConn -notmatch "SSH_CONNECTED") {
    Write-Host "[ERROR] Failed to connect to $HostName`:$Port. Output: $testConn" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] SSH connection verified." -ForegroundColor Green

Write-Host "`n[2/3] Initializing workspace & pulling latest code from origin/main..." -ForegroundColor Yellow
$remoteInit = @"
mkdir -p /workspace && cd /workspace
if [ ! -d "/workspace/layoutlmv3-1" ]; then
    git clone https://github.com/pn-minh/layoutlmv3-1.git /workspace/layoutlmv3-1
else
    cd /workspace/layoutlmv3-1 && git fetch origin main && git reset --hard origin/main
fi
chmod +x /workspace/layoutlmv3-1/scratch/*.sh
"@
ssh @sshOpts "$User@$HostName" $remoteInit

Write-Host "`n[3/3] Launching autonomous fine-tuning script in background..." -ForegroundColor Yellow
$forceVal = if ($ForceRerun) { "1" } else { "0" }
$remoteLaunch = @"
export CELLS='$Cells'
export FORCE_RERUN=$forceVal
nohup bash /workspace/layoutlmv3-1/scratch/run_vast_finetune.sh > /workspace/bootstrap_and_runner.log 2>&1 < /dev/null &
sleep 3
ps aux | grep -E "run_vast|vast_runner" | grep -v grep
"@
ssh @sshOpts "$User@$HostName" $remoteLaunch

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " [SUCCESS] PIPELINE LAUNCHED AUTONOMOUSLY ON VAST.AI!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "1. Training will run in background on the instance." -ForegroundColor White
Write-Host "2. You can safely close your terminal or turn off your PC." -ForegroundColor White
Write-Host "3. Real-time updates will automatically stream to Google Sheets:" -ForegroundColor White
Write-Host "   https://docs.google.com/spreadsheets/d/173WXkbMXDCEVs4pYBRNXGTHihOda18adbJRJ7RpFw7o/edit" -ForegroundColor Cyan
Write-Host "4. Checkpoints, logs, and summaries will upload to Google Drive." -ForegroundColor White
Write-Host "5. The instance will automatically self-destruct once finished." -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
