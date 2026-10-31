<#
.SYNOPSIS
    Real-time synchronization script for Research Citations Dashboard to Google Sheets and local CSV.

.PARAMETER WebhookUrl
    The Google Apps Script Web App URL.
#>

param(
    [string]$WebhookUrl = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourcePath = Join-Path $ScriptDir "citations_dashboard.md"
$CsvPath = Join-Path $ScriptDir "citations_dashboard.csv"

if (-not (Test-Path $SourcePath)) {
    Write-Error "Citations dashboard markdown file not found at $SourcePath"
}

Write-Host "Parsing Citations Dashboard from $SourcePath..." -ForegroundColor Cyan

$lines = Get-Content -Path $SourcePath -Encoding UTF8
$inTable = $false
$rows = @()
$headers = @()

foreach ($line in $lines) {
    $trimmed = $line.Trim()
    if ($trimmed -match '^\|\s*#\s*\|') {
        $inTable = $true
        $headers = ($trimmed.Trim('|') -split '\|') | ForEach-Object { $_.Trim() }
        continue
    }
    if ($inTable -and $trimmed -match '^\|\s*:?-+') {
        continue
    }
    if ($inTable -and $trimmed -match '^\|\s*\*\*\d+\*\*') {
        $cols = ($trimmed.Trim('|') -split '\|') | ForEach-Object { $_.Trim() }
        if ($cols.Count -ge 8) {
            # Extract clean title and link
            $titleCell = $cols[1]
            $titleText = $titleCell
            $titleUrl = ""
            if ($titleCell -match '\[(.*?)\]\((.*?)\)') {
                $titleText = $matches[1]
                $titleUrl = $matches[2]
            }

            # Extract origin link
            $originCell = $cols[6]
            $originText = $originCell
            $originUrl = ""
            if ($originCell -match '\[(.*?)\]\((.*?)\)') {
                $originText = $matches[1]
                $originUrl = $matches[2]
            }

            $rows += [PSCustomObject]@{
                Index         = ($cols[0] -replace '\*','').Trim()
                Title         = $titleText
                TitleUrl      = $titleUrl
                Authors       = $cols[2]
                YearVenue     = $cols[3]
                Category      = ($cols[4] -replace '\*','').Trim()
                Inheritance   = ($cols[5] -replace '`','' -replace '\$','').Trim()
                OriginText    = $originText
                OriginUrl     = $originUrl
                ThesisStatus  = ($cols[7] -replace '\*','').Trim()
            }
        }
    }
    if ($inTable -and $trimmed -eq '') {
        $inTable = $false
    }
}

Write-Host "Parsed $($rows.Count) citation entries." -ForegroundColor Green

# 1. Export CSV
$csvRows = $rows | Select-Object Index, Title, Authors, YearVenue, Category, Inheritance, OriginUrl, ThesisStatus
$csvRows | Export-Csv -Path $CsvPath -NoTypeInformation -Encoding UTF8
Write-Host "Exported local CSV: $CsvPath" -ForegroundColor Cyan

# 2. Build Matrix for Google Sheets (Using Excel HYPERLINK formulas)
$matrix = @()
$sheetHeaders = @("No.", "Work Title (Clickable)", "Author(s)", "Year & Venue", "Category / Paradigm", "Citation Lineage (Inheritance Tree)", "Origin Link", "Thesis Integration Status")
$matrix += ,$sheetHeaders

foreach ($r in $rows) {
    $titleVal = if ($r.TitleUrl) { "=HYPERLINK(`"$($r.TitleUrl)`", `"$($r.Title -replace '"', '""')`")" } else { $r.Title }
    $originVal = if ($r.OriginUrl) { "=HYPERLINK(`"$($r.OriginUrl)`", `"$($r.OriginText -replace '"', '""')`")" } else { $r.OriginText }

    $matrix += ,@(
        $r.Index,
        $titleVal,
        $r.Authors,
        $r.YearVenue,
        $r.Category,
        $r.Inheritance,
        $originVal,
        $r.ThesisStatus
    )
}

# 3. Post to Google Apps Script Web App
$bodyObj = @{
    action      = "sync_citations"
    lastUpdated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    rows        = $matrix
}
$jsonBody = $bodyObj | ConvertTo-Json -Depth 5

Write-Host "Posting to Google Apps Script Web App: $WebhookUrl..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $jsonBody -ContentType "application/json; charset=utf-8"
    Write-Host "Google Sheet Web App response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Cyan
}
catch {
    Write-Warning "Could not push directly to Web App: $_"
}

