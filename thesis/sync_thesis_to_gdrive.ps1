<#
.SYNOPSIS
    Automated build, packaging, and real-time synchronization of all thesis materials
    (PDFs, 300 DPI PNG & PDF diagram, LaTeX source .tex & Overleaf .zip bundles) to Google Drive.

.DESCRIPTION
    1. Renders thesis/figures/model_architecture_heads_style.pdf -> .png (300 DPI) if needed.
    2. Packages clean, up-to-date Overleaf ZIP archives (thesis_en_overleaf.zip, thesis_vi_overleaf.zip)
       and a full workspace LaTeX source archive (thesis_full_latex_source.zip).
    3. Uploads all PDFs, PNGs, LaTeX .tex source, and .zip bundles to the shared 'Thesis - LayoutLMv3'
       Google Drive folder via the Google Apps Script Web App.
    4. When launched with -Watch, continuously monitors thesis/en, thesis/vi, thesis/figures,
       and thesis/tracker.csv, automatically recompiling, repackaging, and syncing changes.
#>

param(
    [string]$WebhookUrl = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec",
    [switch]$Watch,
    [switch]$SkipInitial,
    [int]$IntervalSeconds = 15,
    [switch]$FetchRemote,
    [string]$Repo = "pn-minh/layoutlmv3-1",
    [string]$Branch = "documentation"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir   = Split-Path -Parent $ScriptDir
$Tectonic  = Join-Path $ScriptDir "bin\tectonic.exe"
$RenderPng = Join-Path $ScriptDir "render_pdf_to_png.ps1"

$ViPdf      = Join-Path $ScriptDir "vi\main.pdf"
$EnPdf      = Join-Path $ScriptDir "en\main.pdf"
$DiagramTex = Join-Path $ScriptDir "figures\model_architecture_heads_style.tex"
$DiagramPdf = Join-Path $ScriptDir "figures\model_architecture_heads_style.pdf"
$DiagramPng = Join-Path $ScriptDir "figures\model_architecture_heads_style.png"
$SlidesTex  = Join-Path $ScriptDir "presentation\weekly_update_slides.tex"
$SlidesPdf  = Join-Path $ScriptDir "presentation\weekly_update_slides.pdf"
$SlidesPptx = Join-Path $ScriptDir "presentation\weekly_update_slides.pptx"
$BuildPptx  = Join-Path $ScriptDir "build_pptx.ps1"
$ScriptMd   = Join-Path $ScriptDir "presentation\weekly_update_script.md"
$ScriptViMd = Join-Path $ScriptDir "presentation\weekly_update_script_vi.md"
$EnZip      = Join-Path $RootDir "thesis_en_overleaf.zip"
$ViZip      = Join-Path $RootDir "thesis_vi_overleaf.zip"
$FullZip    = Join-Path $RootDir "thesis_full_latex_source.zip"

function Build-OverleafZip {
    param(
        [string]$LangDir,
        [string]$FiguresDir,
        [string]$DestZip
    )

    if (Test-Path $DestZip) { Remove-Item $DestZip -Force }
    $excludeExts = @(".aux", ".log", ".out", ".toc", ".lof", ".lot", ".bbl", ".blg", ".synctex.gz", ".fls", ".fdb_latexmk")

    $zipStream = [System.IO.File]::Open($DestZip, [System.IO.FileMode]::Create)
    $archive   = New-Object System.IO.Compression.ZipArchive($zipStream, [System.IO.Compression.ZipArchiveMode]::Create)

    try {
        $langRoot = (Resolve-Path $LangDir).Path
        Get-ChildItem -Path $langRoot -Recurse -File | ForEach-Object {
            if ($excludeExts -contains $_.Extension.ToLower()) { return }
            $relPath = $_.FullName.Substring($langRoot.Length).TrimStart('\', '/') -replace '\\', '/'
            $entry = $archive.CreateEntry($relPath, [System.IO.Compression.CompressionLevel]::Optimal)
            $entryStream = $entry.Open()
            try {
                if ($_.Extension -in @(".tex", ".sty", ".bib")) {
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

        $figRoot = (Resolve-Path $FiguresDir).Path
        Get-ChildItem -Path $figRoot -Recurse -File | ForEach-Object {
            if ($excludeExts -contains $_.Extension.ToLower()) { return }
            $relPath = "figures/" + ($_.FullName.Substring($figRoot.Length).TrimStart('\', '/') -replace '\\', '/')
            $entry = $archive.CreateEntry($relPath, [System.IO.Compression.CompressionLevel]::Optimal)
            $entryStream = $entry.Open()
            try {
                if ($_.Extension -eq ".tex") {
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
}

function Build-FullWorkspaceZip {
    param([string]$DestZip)

    if (Test-Path $DestZip) { Remove-Item $DestZip -Force }
    $excludeExts = @(".aux", ".log", ".out", ".toc", ".lof", ".lot", ".bbl", ".blg", ".synctex.gz", ".fls", ".fdb_latexmk")

    $zipStream = [System.IO.File]::Open($DestZip, [System.IO.FileMode]::Create)
    $archive   = New-Object System.IO.Compression.ZipArchive($zipStream, [System.IO.Compression.ZipArchiveMode]::Create)

    try {
        foreach ($sub in @("en", "vi", "figures", "tables", "presentation")) {
            $subPath = Join-Path $ScriptDir $sub
            if (-not (Test-Path $subPath)) { continue }
            $subRoot = (Resolve-Path $subPath).Path
            Get-ChildItem -Path $subRoot -Recurse -File | ForEach-Object {
                if ($excludeExts -contains $_.Extension.ToLower()) { return }
                $relPath = "$sub/" + ($_.FullName.Substring($subRoot.Length).TrimStart('\', '/') -replace '\\', '/')
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $archive, $_.FullName, $relPath, [System.IO.Compression.CompressionLevel]::Optimal
                ) | Out-Null
            }
        }
    } finally {
        $archive.Dispose()
        $zipStream.Dispose()
    }
}

function Update-AllPackages {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Packaging Overleaf & Full LaTeX ZIP archives..." -ForegroundColor Cyan
    Build-OverleafZip -LangDir (Join-Path $ScriptDir "en") -FiguresDir (Join-Path $ScriptDir "figures") -DestZip $EnZip
    Build-OverleafZip -LangDir (Join-Path $ScriptDir "vi") -FiguresDir (Join-Path $ScriptDir "figures") -DestZip $ViZip
    Build-FullWorkspaceZip -DestZip $FullZip
}

function Upload-SingleFile {
    param(
        [string]$FilePath,
        [string]$RemoteName,
        [string]$Language = "",
        [string]$MimeType = ""
    )

    if (-not (Test-Path $FilePath)) {
        Write-Warning "File not found: $FilePath"
        return $null
    }

    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    $base64 = [Convert]::ToBase64String($bytes)
    $sizeKb = [math]::Round($bytes.Length / 1KB, 1)

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Uploading $RemoteName ($sizeKb KB) to Google Drive..." -ForegroundColor Cyan

    $payload = @{
        action    = "upload_pdf"
        filename  = $RemoteName
        language  = $Language
        pdfBase64 = $base64
    }
    if ($MimeType) {
        $payload["mimeType"] = $MimeType
    }
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

function Get-GoogleSlidesEditUrl {
    param([string]$DriveFileUrl)
    if ($DriveFileUrl -match "/file/d/([^/]+)/") {
        return "https://docs.google.com/presentation/d/$($Matches[1])/edit"
    }
    return $DriveFileUrl
}

function Fetch-RemotePdfs {
    param(
        [string]$TargetRepo,
        [string]$BranchName
    )
    $baseUrl = "https://raw.githubusercontent.com/$TargetRepo/$BranchName"
    $items = @(
        @{ Name = "Vietnamese_Thesis_LayoutLMv3.pdf"; Target = $ViPdf },
        @{ Name = "English_Thesis_LayoutLMv3.pdf"; Target = $EnPdf },
        @{ Name = "Model_Architecture_Diagram.pdf"; Target = $DiagramPdf },
        @{ Name = "Weekly_Progress_Presentation_Slides.pdf"; Target = $SlidesPdf }
    )

    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Fetching remotely compiled PDFs from GitHub ($TargetRepo @ $BranchName)..." -ForegroundColor Cyan
    foreach ($item in $items) {
        $url = "$baseUrl/$($item.Name)"
        try {
            $destDir = Split-Path -Parent $item.Target
            if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
            Write-Host "  -> Downloading $($item.Name)..." -ForegroundColor Gray
            Invoke-WebRequest -Uri $url -OutFile $item.Target -UseBasicParsing -TimeoutSec 60
            $kb = [math]::Round((Get-Item $item.Target).Length / 1KB, 1)
            Write-Host "     Saved ($kb KB)" -ForegroundColor Green
        } catch {
            Write-Warning "Could not fetch $($item.Name) from $url : $_"
        }
    }
}

function Sync-AllMaterials {
    Write-Host "`n=== Syncing All Thesis Materials to Google Drive ===" -ForegroundColor Magenta

    # Fetch remotely compiled PDFs if requested
    if ($FetchRemote) {
        Fetch-RemotePdfs -TargetRepo $Repo -BranchName $Branch
    }

    # Ensure 300 DPI PNG is up-to-date
    if ((Test-Path $DiagramPdf) -and (-not (Test-Path $DiagramPng) -or ((Get-Item $DiagramPdf).LastWriteTime -gt (Get-Item $DiagramPng).LastWriteTime))) {
        & powershell -ExecutionPolicy Bypass -File $RenderPng -PdfPath $DiagramPdf -PngPath $DiagramPng -Dpi 300
    }

    # Ensure PPTX is up-to-date with Slides PDF
    if ((Test-Path $SlidesPdf) -and (-not (Test-Path $SlidesPptx) -or ((Get-Item $SlidesPdf).LastWriteTime -gt (Get-Item $SlidesPptx).LastWriteTime))) {
        & powershell -ExecutionPolicy Bypass -File $BuildPptx -PdfPath $SlidesPdf -PptxPath $SlidesPptx -Dpi 300
    }

    # Rebuild clean Overleaf & Full LaTeX source ZIPs
    Update-AllPackages

    # 1. Thesis PDFs
    $viResp = Upload-SingleFile -FilePath $ViPdf -RemoteName "Vietnamese_Thesis_LayoutLMv3.pdf" -Language "vi"
    $enResp = Upload-SingleFile -FilePath $EnPdf -RemoteName "English_Thesis_LayoutLMv3.pdf" -Language "en"

    # 2. Model Architecture Diagram (PDF, 300 DPI PNG, and standalone LaTeX .tex source)
    $diagPdfResp = Upload-SingleFile -FilePath $DiagramPdf -RemoteName "Model_Architecture_Diagram.pdf"
    $diagPngResp = Upload-SingleFile -FilePath $DiagramPng -RemoteName "Model_Architecture_Diagram.png"
    $diagTexResp = Upload-SingleFile -FilePath $DiagramTex -RemoteName "Model_Architecture_Diagram.tex"

    # 3. Weekly Progress Presentation Slides (PDF, PPTX / Google Slides, LaTeX .tex, and Speaker Script .md)
    $slidesPdfResp  = Upload-SingleFile -FilePath $SlidesPdf  -RemoteName "Weekly_Progress_Presentation_Slides.pdf"
    $slidesPptxResp = Upload-SingleFile -FilePath $SlidesPptx -RemoteName "Weekly_Progress_Presentation_Slides.pptx" -MimeType "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    $slidesTexResp  = Upload-SingleFile -FilePath $SlidesTex  -RemoteName "Weekly_Progress_Presentation_Slides.tex"
    $scriptMdResp   = Upload-SingleFile -FilePath $ScriptMd   -RemoteName "Weekly_Progress_Presentation_Script.md"
    $scriptViMdResp = Upload-SingleFile -FilePath $ScriptViMd -RemoteName "Weekly_Progress_Presentation_Script_VI.md"

    # 4. Overleaf & Full LaTeX Source Bundles (.zip)
    $enZipResp   = Upload-SingleFile -FilePath $EnZip   -RemoteName "LaTeX_Source_English_Thesis_Overleaf.zip"
    $viZipResp   = Upload-SingleFile -FilePath $ViZip   -RemoteName "LaTeX_Source_Vietnamese_Thesis_Overleaf.zip"
    $fullZipResp = Upload-SingleFile -FilePath $FullZip -RemoteName "LaTeX_Source_Full_Thesis_Workspace.zip"

    Write-Host "`n=== Google Drive Shared Materials Summary ===" -ForegroundColor Yellow
    if ($viResp)         { Write-Host "Vietnamese Thesis PDF : $($viResp.fileUrl)" -ForegroundColor Cyan }
    if ($enResp)         { Write-Host "English Thesis PDF    : $($enResp.fileUrl)" -ForegroundColor Cyan }
    if ($diagPdfResp)    { Write-Host "Architecture (PDF)    : $($diagPdfResp.fileUrl)" -ForegroundColor Cyan }
    if ($diagPngResp)    { Write-Host "Architecture (PNG)    : $($diagPngResp.fileUrl)" -ForegroundColor Cyan }
    if ($diagTexResp)    { Write-Host "Architecture (TeX)    : $($diagTexResp.fileUrl)" -ForegroundColor Cyan }
    if ($slidesPdfResp)  { Write-Host "Presentation (PDF)    : $($slidesPdfResp.fileUrl)" -ForegroundColor Cyan }
    if ($slidesPptxResp) {
        $gslidesUrl = Get-GoogleSlidesEditUrl -DriveFileUrl $slidesPptxResp.fileUrl
        Write-Host "Presentation (PPTX)   : $($slidesPptxResp.fileUrl)" -ForegroundColor Cyan
        Write-Host "Google Slides Copy    : $gslidesUrl" -ForegroundColor Green
    }
    if ($slidesTexResp)  { Write-Host "Presentation (TeX)    : $($slidesTexResp.fileUrl)" -ForegroundColor Cyan }
    if ($scriptMdResp)   { Write-Host "Speaker Script (EN)   : $($scriptMdResp.fileUrl)" -ForegroundColor Cyan }
    if ($scriptViMdResp) { Write-Host "Speaker Script (VI)   : $($scriptViMdResp.fileUrl)" -ForegroundColor Cyan }
    if ($enZipResp)      { Write-Host "English LaTeX (ZIP)   : $($enZipResp.fileUrl)" -ForegroundColor Cyan }
    if ($viZipResp)      { Write-Host "Vietnamese LaTeX (ZIP): $($viZipResp.fileUrl)" -ForegroundColor Cyan }
    if ($fullZipResp)    { Write-Host "Full Workspace (ZIP)  : $($fullZipResp.fileUrl)" -ForegroundColor Cyan }
    if ($enResp.folderUrl) { Write-Host "`nShared Drive Folder   : $($enResp.folderUrl)" -ForegroundColor Green }
}

function Get-SourceSignature {
    param([string[]]$Paths)
    $items = foreach ($p in $Paths) {
        if (Test-Path $p) {
            Get-ChildItem -Path $p -Recurse -File -Include "*.tex", "*.bib", "*.sty", "*.cls", "*.md"
        }
    }
    return ($items | Sort-Object FullName | ForEach-Object { "$($_.FullName):$($_.LastWriteTimeUtc.Ticks)" }) -join "|"
}

# Initial full sync (unless -SkipInitial is specified)
if (-not $SkipInitial) {
    Sync-AllMaterials
}

# Continuous Watch Mode for automatic recompilation & Google Drive syncing
if ($Watch) {
    Write-Host "`n[Watcher Active] Monitoring thesis/figures, thesis/en, thesis/vi, thesis/presentation, and thesis/tracker.csv every $IntervalSeconds s..." -ForegroundColor Green
    $lastFigSig  = Get-SourceSignature -Paths @((Join-Path $ScriptDir "figures"))
    $lastEnSig   = Get-SourceSignature -Paths @((Join-Path $ScriptDir "en"))
    $lastViSig   = Get-SourceSignature -Paths @((Join-Path $ScriptDir "vi"))
    $lastPresSig = Get-SourceSignature -Paths @((Join-Path $ScriptDir "presentation"))
    $trackerCsv  = Join-Path $ScriptDir "tracker.csv"
    $lastTrackerTicks = if (Test-Path $trackerCsv) { (Get-Item $trackerCsv).LastWriteTimeUtc.Ticks } else { 0 }

    while ($true) {
        Start-Sleep -Seconds $IntervalSeconds
        try {
            $curFigSig  = Get-SourceSignature -Paths @((Join-Path $ScriptDir "figures"))
            $curEnSig   = Get-SourceSignature -Paths @((Join-Path $ScriptDir "en"))
            $curViSig   = Get-SourceSignature -Paths @((Join-Path $ScriptDir "vi"))
            $curPresSig = Get-SourceSignature -Paths @((Join-Path $ScriptDir "presentation"))

            $figChanged  = ($curFigSig -ne $lastFigSig)
            $enChanged   = ($curEnSig -ne $lastEnSig) -or $figChanged
            $viChanged   = ($curViSig -ne $lastViSig) -or $figChanged
            $presChanged = ($curPresSig -ne $lastPresSig) -or $figChanged

            if ($figChanged) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Detected change in thesis/figures -> Recompiling diagram PDF & 300 DPI PNG..." -ForegroundColor Yellow
                & $Tectonic $DiagramTex
                & powershell -ExecutionPolicy Bypass -File $RenderPng -PdfPath $DiagramPdf -PngPath $DiagramPng -Dpi 300
                Upload-SingleFile -FilePath $DiagramPdf -RemoteName "Model_Architecture_Diagram.pdf" | Out-Null
                Upload-SingleFile -FilePath $DiagramPng -RemoteName "Model_Architecture_Diagram.png" | Out-Null
                Upload-SingleFile -FilePath $DiagramTex -RemoteName "Model_Architecture_Diagram.tex" | Out-Null
                $lastFigSig = Get-SourceSignature -Paths @((Join-Path $ScriptDir "figures"))
            }

            if ($presChanged) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Detected change in thesis/presentation -> Recompiling Slides PDF, PPTX & syncing Google Slides..." -ForegroundColor Yellow
                & $Tectonic -X compile $SlidesTex --outdir (Join-Path $ScriptDir "presentation")
                & powershell -ExecutionPolicy Bypass -File $BuildPptx -PdfPath $SlidesPdf -PptxPath $SlidesPptx -Dpi 300
                Upload-SingleFile -FilePath $SlidesPdf  -RemoteName "Weekly_Progress_Presentation_Slides.pdf" | Out-Null
                Upload-SingleFile -FilePath $SlidesPptx -RemoteName "Weekly_Progress_Presentation_Slides.pptx" -MimeType "application/vnd.openxmlformats-officedocument.presentationml.presentation" | Out-Null
                Upload-SingleFile -FilePath $SlidesTex  -RemoteName "Weekly_Progress_Presentation_Slides.tex" | Out-Null
                Upload-SingleFile -FilePath $ScriptMd   -RemoteName "Weekly_Progress_Presentation_Script.md" | Out-Null
                $lastPresSig = Get-SourceSignature -Paths @((Join-Path $ScriptDir "presentation"))
            }

            if ($enChanged) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Recompiling English Thesis & updating Overleaf ZIP..." -ForegroundColor Yellow
                & $Tectonic (Join-Path $ScriptDir "en\main.tex")
                Build-OverleafZip -LangDir (Join-Path $ScriptDir "en") -FiguresDir (Join-Path $ScriptDir "figures") -DestZip $EnZip
                Upload-SingleFile -FilePath $EnPdf -RemoteName "English_Thesis_LayoutLMv3.pdf" -Language "en" | Out-Null
                Upload-SingleFile -FilePath $EnZip -RemoteName "LaTeX_Source_English_Thesis_Overleaf.zip" | Out-Null
                $lastEnSig = Get-SourceSignature -Paths @((Join-Path $ScriptDir "en"))
            }

            if ($viChanged) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Recompiling Vietnamese Thesis & updating Overleaf ZIP..." -ForegroundColor Yellow
                & $Tectonic (Join-Path $ScriptDir "vi\main.tex")
                Build-OverleafZip -LangDir (Join-Path $ScriptDir "vi") -FiguresDir (Join-Path $ScriptDir "figures") -DestZip $ViZip
                Upload-SingleFile -FilePath $ViPdf -RemoteName "Vietnamese_Thesis_LayoutLMv3.pdf" -Language "vi" | Out-Null
                Upload-SingleFile -FilePath $ViZip -RemoteName "LaTeX_Source_Vietnamese_Thesis_Overleaf.zip" | Out-Null
                $lastViSig = Get-SourceSignature -Paths @((Join-Path $ScriptDir "vi"))
            }

            if ($enChanged -or $viChanged -or $presChanged) {
                Build-FullWorkspaceZip -DestZip $FullZip
                Upload-SingleFile -FilePath $FullZip -RemoteName "LaTeX_Source_Full_Thesis_Workspace.zip" | Out-Null
            }

            if (Test-Path $trackerCsv) {
                $curTrackerTicks = (Get-Item $trackerCsv).LastWriteTimeUtc.Ticks
                if ($curTrackerTicks -ne $lastTrackerTicks) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Detected change in tracker.csv -> Syncing Google Sheet..." -ForegroundColor Yellow
                    & powershell -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "sync_google_sheet.ps1")
                    $lastTrackerTicks = $curTrackerTicks
                }
            }
        } catch {
            Write-Warning "[Watcher] Error during auto-sync cycle: $_"
        }
    }
}
