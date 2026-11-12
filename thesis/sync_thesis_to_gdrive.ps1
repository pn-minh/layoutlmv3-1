<#
.SYNOPSIS
    Automated build, Overleaf extraction, and Google Drive synchronization for the English Thesis.

.DESCRIPTION
    1. Packages clean Overleaf ZIP archive (thesis_en_overleaf.zip) AND extracts it into
       thesis_en_overleaf_extracted/ for drag-and-drop Overleaf folder overwriting.
    2. Maintains a clean local copy of English_Thesis_LayoutLMv3.pdf at repo root.
    3. Uploads ONLY the whitelisted deliverables to the 'Thesis - LayoutLMv3' Google Drive root folder:
         - English_Thesis_LayoutLMv3.pdf
         - Weekly_Progress_Presentation_Slides.pdf & .pptx (plus Final Defense slides when generated)
         - Model_Architecture_Diagram.drawio & Model_Architecture_Diagram.pdf
         - Thesis Changelog Google Doc (synced from thesis/THESIS_CHANGELOG.md)
    4. Triggers 'cleanup_drive_folder' on Google Apps Script to move any experiment logs/JSONs/ZIPs
       into 'Experiments & Logs' and remove redundant .png/.tex/.md clutter from the root Drive folder.
#>

param(
    [string]$WebhookUrl = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec",
    [switch]$Watch,
    [switch]$SkipInitial,
    [int]$IntervalSeconds = 15,
    [switch]$FetchRemote,
    [string]$Repo = "pn-minh/layoutlmv3-1",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir   = Split-Path -Parent $ScriptDir
$Tectonic  = Join-Path $ScriptDir "bin\tectonic.exe"
$RenderPng = Join-Path $ScriptDir "render_pdf_to_png.ps1"

$EnPdf           = Join-Path $ScriptDir "en\main.pdf"
$RootEnPdf       = Join-Path $RootDir "English_Thesis_LayoutLMv3.pdf"
$DiagramTex      = Join-Path $ScriptDir "figures\model_architecture_heads_style.tex"
$DiagramPdf      = Join-Path $ScriptDir "figures\model_architecture_heads_style.pdf"
$DiagramPng      = Join-Path $ScriptDir "figures\model_architecture_heads_style.png"
$DiagramDrawio   = Join-Path $ScriptDir "figures\heads_model_architecture_migrated.drawio"
$SlidesTex       = Join-Path $ScriptDir "presentation\weekly_update_slides.tex"
$SlidesPdf       = Join-Path $ScriptDir "presentation\weekly_update_slides.pdf"
$SlidesPptx      = Join-Path $ScriptDir "presentation\weekly_update_slides.pptx"
$DefensePdf      = Join-Path $ScriptDir "presentation\final_defense_slides.pdf"
$DefensePptx     = Join-Path $ScriptDir "presentation\final_defense_slides.pptx"
$BuildPptx       = Join-Path $ScriptDir "build_pptx.ps1"
$ChangelogMd     = Join-Path $ScriptDir "THESIS_CHANGELOG.md"
$EnZip           = Join-Path $RootDir "thesis_en_overleaf.zip"
$EnExtractedDir  = Join-Path $RootDir "thesis_en_overleaf_extracted"

function Build-OverleafZipAndExtracted {
    param(
        [string]$LangDir,
        [string]$DestZip,
        [string]$DestExtractDir
    )

    if (Test-Path $DestZip) { Remove-Item $DestZip -Force }
    $excludeExts = @(".aux", ".log", ".out", ".toc", ".lof", ".lot", ".bbl", ".blg", ".synctex.gz", ".fls", ".fdb_latexmk", ".pdf", ".md")

    $zipStream = [System.IO.File]::Open($DestZip, [System.IO.FileMode]::Create)
    $archive   = New-Object System.IO.Compression.ZipArchive($zipStream, [System.IO.Compression.ZipArchiveMode]::Create)

    try {
        $langRoot = (Resolve-Path $LangDir).Path
        Get-ChildItem -Path $langRoot -Recurse -File | ForEach-Object {
            $ext = $_.Extension.ToLower()
            if ($_.Name.ToLower() -eq "main.pdf") { return }
            if (($excludeExts -contains $ext) -and ($ext -ne ".pdf")) { return }
            $relPath = $_.FullName.Substring($langRoot.Length).TrimStart('\', '/') -replace '\\', '/'
            $entry = $archive.CreateEntry($relPath, [System.IO.Compression.CompressionLevel]::Optimal)
            $entryStream = $entry.Open()
            try {
                if ($ext -in @(".tex", ".sty", ".bib")) {
                    $text = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::UTF8)
                    $text = $text.Replace("../figures/", "figures/")
                    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
                    $entryStream.Write($bytes, 0, $bytes.Length)
                } else {
                    $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
                    $entryStream.Write($bytes, 0, $bytes.Length)
                }
            } finally {
                $entryStream.Dispose()
            }
        }
    } finally {
        $archive.Dispose()
        $zipStream.Dispose()
    }

    # Always keep thesis_en_overleaf_extracted/ synchronized for direct Overleaf folder drag-and-drop
    if (Test-Path $DestExtractDir) {
        Remove-Item $DestExtractDir -Recurse -Force
    }
    [System.IO.Compression.ZipFile]::ExtractToDirectory($DestZip, $DestExtractDir)
}

function Update-AllPackages {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Packaging Overleaf ZIP & updating thesis_en_overleaf_extracted/..." -ForegroundColor Cyan
    Build-OverleafZipAndExtracted -LangDir (Join-Path $ScriptDir "en") -DestZip $EnZip -DestExtractDir $EnExtractedDir
    if (Test-Path $EnPdf) {
        Copy-Item -Path $EnPdf -Destination $RootEnPdf -Force
    }
}

function Upload-SingleFile {
    param(
        [string]$FilePath,
        [string]$RemoteName,
        [string]$Language = "",
        [string]$MimeType = "",
        [string]$Subfolder = ""
    )

    if (-not (Test-Path $FilePath)) {
        Write-Warning "File not found: $FilePath"
        return $null
    }

    if ($FilePath.EndsWith("weekly_update_slides.pptx")) {
        $updatedCopy = $FilePath -replace '\.pptx$', '_updated.pptx'
        if ((Test-Path $updatedCopy) -and ((Get-Item $updatedCopy).LastWriteTime -ge (Get-Item $FilePath).LastWriteTime)) {
            $FilePath = $updatedCopy
        }
    }

    try {
        $fs = New-Object System.IO.FileStream($FilePath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $bytes = New-Object byte[] $fs.Length
        $fs.Read($bytes, 0, $fs.Length) | Out-Null
        $fs.Dispose()
    } catch {
        Write-Warning "Failed to read $($FilePath): $($_.Exception.Message)"
        return $null
    }
    $base64 = [Convert]::ToBase64String($bytes)
    $sizeKb = [math]::Round($bytes.Length / 1KB, 1)

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Uploading $RemoteName ($sizeKb KB) to Google Drive..." -ForegroundColor Cyan

    $payload = @{
        action    = "upload_pdf"
        filename  = $RemoteName
        language  = $Language
        pdfBase64 = $base64
    }
    if ($MimeType)  { $payload["mimeType"]  = $MimeType }
    if ($Subfolder) { $payload["subfolder"] = $Subfolder }

    $body = $payload | ConvertTo-Json -Depth 3

    try {
        $resp = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $body -ContentType "application/json; charset=utf-8"
        if ($resp.status -eq "OK") {
            Write-Host "  -> Public View Link: $($resp.fileUrl)" -ForegroundColor Green
            return $resp
        } else {
            Write-Warning "Upload returned non-OK response: $resp"
            return $null
        }
    } catch {
        Write-Warning "Failed to upload $RemoteName : $_"
        return $null
    }
}

function Sync-ChangelogAndCleanupDrive {
    if (Test-Path $ChangelogMd) {
        $mdText = [System.IO.File]::ReadAllText($ChangelogMd, [System.Text.Encoding]::UTF8)
        $docPayload = @{
            action   = "sync_changelog_doc"
            markdown = $mdText
        } | ConvertTo-Json -Depth 3
        try {
            $docResp = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $docPayload -ContentType "application/json; charset=utf-8"
            if ($docResp.status -eq "OK") {
                Write-Host "  -> Thesis Changelog Google Doc: $($docResp.docUrl)" -ForegroundColor Green
            }
        } catch {
            Write-Warning "Changelog Doc sync note (deploy updated GoogleAppsScript.js if not yet active): $_"
        }
    }

    $cleanPayload = @{
        action = "cleanup_drive_folder"
    } | ConvertTo-Json -Depth 2
    try {
        $cleanResp = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $cleanPayload -ContentType "application/json; charset=utf-8"
        if ($cleanResp.status -eq "OK") {
            Write-Host "  -> Cleaned Drive Folder (Kept: $($cleanResp.keptFiles -join ', '))" -ForegroundColor Green
        }
    } catch {
        Write-Warning "Drive cleanup note: $_"
    }
}

function Get-GoogleSlidesEditUrl {
    param([string]$DriveFileUrl)
    if ($DriveFileUrl -match "/file/d/([^/]+)/") {
        return "https://docs.google.com/presentation/d/$($Matches[1])/edit"
    }
    return $DriveFileUrl
}

function Sync-AllMaterials {
    Write-Host "`n=== Syncing Whitelisted Thesis Deliverables to Google Drive ===" -ForegroundColor Magenta

    if ((Test-Path $DiagramPdf) -and (-not (Test-Path $DiagramPng) -or ((Get-Item $DiagramPdf).LastWriteTime -gt (Get-Item $DiagramPng).LastWriteTime))) {
        & powershell -ExecutionPolicy Bypass -File $RenderPng -PdfPath $DiagramPdf -PngPath $DiagramPng -Dpi 300
    }

    if ((Test-Path $SlidesPdf) -and (-not (Test-Path $SlidesPptx) -or ((Get-Item $SlidesPdf).LastWriteTime -gt (Get-Item $SlidesPptx).LastWriteTime))) {
        & powershell -ExecutionPolicy Bypass -File $BuildPptx -PdfPath $SlidesPdf -PptxPath $SlidesPptx -Dpi 300
    }

    # Rebuild local Overleaf ZIP + thesis_en_overleaf_extracted/ + local English_Thesis_LayoutLMv3.pdf
    Update-AllPackages

    # 1. English Thesis PDF
    $enResp = Upload-SingleFile -FilePath $EnPdf -RemoteName "English_Thesis_LayoutLMv3.pdf" -Language "en"

    # 2. Original Model Architecture Diagram (.drawio) & Rendered PDF (.pdf) ONLY
    $diagDrawioResp = Upload-SingleFile -FilePath $DiagramDrawio -RemoteName "Model_Architecture_Diagram.drawio"
    $diagPdfResp    = Upload-SingleFile -FilePath $DiagramPdf    -RemoteName "Model_Architecture_Diagram.pdf"

    # 3. Weekly Presentation Slides (and Final Defense Presentation Slides if present)
    $slidesPdfResp  = Upload-SingleFile -FilePath $SlidesPdf  -RemoteName "Weekly_Progress_Presentation_Slides.pdf"
    $slidesPptxResp = Upload-SingleFile -FilePath $SlidesPptx -RemoteName "Weekly_Progress_Presentation_Slides.pptx" -MimeType "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    if (Test-Path $DefensePdf) {
        Upload-SingleFile -FilePath $DefensePdf -RemoteName "Final_Thesis_Defense_Presentation_Slides.pdf" | Out-Null
    }
    if (Test-Path $DefensePptx) {
        Upload-SingleFile -FilePath $DefensePptx -RemoteName "Final_Thesis_Defense_Presentation_Slides.pptx" -MimeType "application/vnd.openxmlformats-officedocument.presentationml.presentation" | Out-Null
    }

    # 4. Sync Thesis Changelog Google Doc & Clean Up Drive Folder
    Sync-ChangelogAndCleanupDrive

    Write-Host "`n=== Google Drive Clean Thesis Folder Summary ===" -ForegroundColor Yellow
    if ($enResp)         { Write-Host "1. English Thesis PDF    : $($enResp.fileUrl)" -ForegroundColor Cyan }
    if ($diagDrawioResp) { Write-Host "2. Diagram (.drawio)     : $($diagDrawioResp.fileUrl)" -ForegroundColor Cyan }
    if ($diagPdfResp)    { Write-Host "3. Diagram (.pdf)        : $($diagPdfResp.fileUrl)" -ForegroundColor Cyan }
    if ($slidesPdfResp)  { Write-Host "4. Weekly Slides (.pdf)  : $($slidesPdfResp.fileUrl)" -ForegroundColor Cyan }
    if ($slidesPptxResp) {
        $gslidesUrl = Get-GoogleSlidesEditUrl -DriveFileUrl $slidesPptxResp.fileUrl
        Write-Host "5. Weekly Slides (.pptx) : $($slidesPptxResp.fileUrl)" -ForegroundColor Cyan
        Write-Host "   Google Slides Edit    : $gslidesUrl" -ForegroundColor Green
    }
    if ($enResp.folderUrl) { Write-Host "`nShared Drive Folder      : $($enResp.folderUrl)" -ForegroundColor Green }
}

if (-not $SkipInitial) {
    Sync-AllMaterials
}
