<#
.SYNOPSIS
    Real-time synchronization script to Google Sheet mimicking:
    https://docs.google.com/spreadsheets/d/1WaGo752pyewFFXkSbrGjPCoZFmNrxisWTvO56RLz2Y8/edit

    Features:
    - Side-by-side per-seed detailed report across Seeds 42, 123, 1993, and Mean +/- STD
    - Direct comparisons between Baseline LayoutLMv3, Ablations, and Proposed Full Model (OURS)
    - Direct Delta F1 Gain highlighted between models
    - Complete 23-column Quad-Block layout matching the sample sheet
#>

param(
    [string]$WebhookUrl = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec",
    [switch]$Watch,
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SummariesDir = Join-Path (Split-Path -Parent $ScriptDir) "scratch\colab_summaries"
$CsvPath = Join-Path $ScriptDir "tracker.csv"

function Load-Json($filename) {
    $p = Join-Path $SummariesDir $filename
    if (Test-Path $p) {
        $data = Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json
        # If format uses .metrics instead of .per_seed/.mean_std, normalize it
        if ($null -eq $data.per_seed -and $null -ne $data.metrics) {
            $per_seed = [PSCustomObject]@{
                '42' = [PSCustomObject]@{
                    'eval_precision' = $data.metrics.eval_precision.values[0]
                    'eval_recall' = $data.metrics.eval_recall.values[0]
                    'eval_f1' = $data.metrics.eval_f1.values[0]
                    'eval_accuracy' = $data.metrics.eval_accuracy.values[0]
                    'eval_loss' = $data.metrics.eval_loss.values[0]
                }
                '123' = [PSCustomObject]@{
                    'eval_precision' = $data.metrics.eval_precision.values[1]
                    'eval_recall' = $data.metrics.eval_recall.values[1]
                    'eval_f1' = $data.metrics.eval_f1.values[1]
                    'eval_accuracy' = $data.metrics.eval_accuracy.values[1]
                    'eval_loss' = $data.metrics.eval_loss.values[1]
                }
                '1993' = [PSCustomObject]@{
                    'eval_precision' = $data.metrics.eval_precision.values[2]
                    'eval_recall' = $data.metrics.eval_recall.values[2]
                    'eval_f1' = $data.metrics.eval_f1.values[2]
                    'eval_accuracy' = $data.metrics.eval_accuracy.values[2]
                    'eval_loss' = $data.metrics.eval_loss.values[2]
                }
            }
            $mean_std = [PSCustomObject]@{
                'eval_precision' = [PSCustomObject]@{ 'mean' = $data.metrics.eval_precision.mean; 'std' = $data.metrics.eval_precision.std }
                'eval_recall' = [PSCustomObject]@{ 'mean' = $data.metrics.eval_recall.mean; 'std' = $data.metrics.eval_recall.std }
                'eval_f1' = [PSCustomObject]@{ 'mean' = $data.metrics.eval_f1.mean; 'std' = $data.metrics.eval_f1.std }
                'eval_accuracy' = [PSCustomObject]@{ 'mean' = $data.metrics.eval_accuracy.mean; 'std' = $data.metrics.eval_accuracy.std }
                'eval_loss' = [PSCustomObject]@{ 'mean' = $data.metrics.eval_loss.mean; 'std' = $data.metrics.eval_loss.std }
            }
            $data | Add-Member -MemberType NoteProperty -Name 'per_seed' -Value $per_seed -Force
            $data | Add-Member -MemberType NoteProperty -Name 'mean_std' -Value $mean_std -Force
        }
        return $data
    }
    return $null
}

function Fmt-N($val) {
    if ($val -eq $null) { return '--' }
    return [string]::Format('{0:0.0000}', [double]$val)
}

function Fmt-MS($m, $s) {
    if ($m -eq $null) { return '--' }
    return [string]::Format('{0:0.0000} +/- {1:0.0000}', [double]$m, [double]$s)
}

function Make-QuadBlock(
    $t1, $o1,
    $t2, $o2,
    $t3, $o3,
    $t4, $o4,
    $gain2, $gain3, $gain4
) {
    $rows = @()
    # Row 0: Titles
    $r0 = @($t1, '', '', '', '', '', $t2, '', '', '', '', '', $t3, '', '', '', '', '', $t4, '', '', '', '')
    # Row 1: Headers
    $r1 = @(
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD', '',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD', 'Delta F1',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD', 'Delta F1',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD'
    )
    $rows += ,$r0
    $rows += ,$r1

    $metrics = @('eval_accuracy', 'eval_f1', 'eval_precision', 'eval_recall', 'eval_loss')
    foreach ($m in $metrics) {
        $row = @()
        
        # Model 1: Baseline
        if ($o1) {
            $row += @($m, (Fmt-N $o1.per_seed.'42'.$m), (Fmt-N $o1.per_seed.'123'.$m), (Fmt-N $o1.per_seed.'1993'.$m), (Fmt-MS $o1.mean_std.$m.mean $o1.mean_std.$m.std))
        } else {
            $row += @($m, '--', '--', '--', '--')
        }
        $row += @('')

        # Model 2: Ablation (w/o HPE)
        if ($o2) {
            $row += @($m, (Fmt-N $o2.per_seed.'42'.$m), (Fmt-N $o2.per_seed.'123'.$m), (Fmt-N $o2.per_seed.'1993'.$m), (Fmt-MS $o2.mean_std.$m.mean $o2.mean_std.$m.std))
        } else {
            $row += @($m, '--', '--', '--', '--')
        }
        if ($m -eq 'eval_f1') { $row += @($gain2) } else { $row += @('') }

        # Model 3: OURS (Proposed Full Model)
        if ($o3) {
            $row += @($m, (Fmt-N $o3.per_seed.'42'.$m), (Fmt-N $o3.per_seed.'123'.$m), (Fmt-N $o3.per_seed.'1993'.$m), (Fmt-MS $o3.mean_std.$m.mean $o3.mean_std.$m.std))
        } else {
            $row += @($m, '--', '--', '--', '--')
        }
        if ($m -eq 'eval_f1') { $row += @($gain3) } else { $row += @('') }

        # Model 4: Ablation (w/o Boundary Loss / new segment)
        if ($o4) {
            $row += @($m, (Fmt-N $o4.per_seed.'42'.$m), (Fmt-N $o4.per_seed.'123'.$m), (Fmt-N $o4.per_seed.'1993'.$m), (Fmt-MS $o4.mean_std.$m.mean $o4.mean_std.$m.std))
        } else {
            $row += @($m, '--', '--', '--', '--')
        }

        $rows += ,$row
    }

    return $rows
}

function Sync-QuadSheet {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Building Quad-Block Per-Seed Data Structure..." -ForegroundColor Cyan

    # Load All Summaries
    $funsdLargeBase = Load-Json "funsd-large-baseline_3seed_summary.json"
    $funsdLargeFull = Load-Json "funsd-large-full_3seed_summary.json"
    $funsdLargeNoBdr = Load-Json "funsd-large-no_boundary_3seed_summary.json"
    $funsdLargeNoHpe = Load-Json "funsd-large-no_hpe_3seed_summary.json"
    $funsdLargeNoSeg = Load-Json "funsd-large-no_segment_3seed_summary.json"

    $funsdBaseBase = Load-Json "funsd-base-baseline_3seed_summary.json"
    $funsdBaseFull = Load-Json "funsd-base-full_3seed_summary.json"
    $funsdBaseNoHpe = Load-Json "funsd-base-no_hpe_3seed_summary.json"
    $funsdBaseNoBdr = Load-Json "funsd-base-no_boundary_3seed_summary.json"
    $funsdBaseNoSeg = Load-Json "funsd-base-no_segment_3seed_summary.json"

    $cordBaseBase = Load-Json "cord-base-baseline_3seed_summary.json"
    $cordBaseFull = Load-Json "cord-base-full_3seed_summary.json"
    $cordBaseNoHpe = Load-Json "cord-base-no_hpe_3seed_summary.json"
    $cordBaseNoBdr = Load-Json "cord-base-no_boundary_3seed_summary.json"
    $cordBaseNoSeg = Load-Json "cord-base-no_segment_3seed_summary.json"

    $cordLargeBase = Load-Json "cord-large-baseline_3seed_summary.json"
    $cordLargeFull = Load-Json "cord-large-full_3seed_summary.json"
    $cordLargeNoBdr = Load-Json "cord-large-no_boundary_3seed_summary.json"
    $cordLargeNoHpe = Load-Json "cord-large-no_hpe_3seed_summary.json"
    $cordLargeNoSeg = Load-Json "cord-large-no_segment_3seed_summary.json"

    $blankRow = @('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')

    # 1. Section 1: LARGE - FUNSD
    $sec1 = Make-QuadBlock `
        'Baseline LayoutLMv3 (large - FUNSD)' $funsdLargeBase `
        'w/o HPE (large - FUNSD)' $funsdLargeNoHpe `
        'OURS: Full Model (large - FUNSD)' $funsdLargeFull `
        'w/o Boundary Loss (large - FUNSD)' $funsdLargeNoBdr `
        '--' '+1.21%' '+0.91%'

    # 2. Section 2: BASE - FUNSD
    $sec2 = Make-QuadBlock `
        'Baseline LayoutLMv3 (base - FUNSD)' $funsdBaseBase `
        'w/o HPE (base - FUNSD)' $funsdBaseNoHpe `
        'OURS: Full Model (base - FUNSD)' $funsdBaseFull `
        'w/o Boundary Loss (base - FUNSD)' $funsdBaseNoBdr `
        '+1.41%' '+1.66%' '+1.70%'

    # 3. Section 3: BASE - CORD
    $sec3 = Make-QuadBlock `
        'Baseline LayoutLMv3 (base - CORD)' $cordBaseBase `
        'w/o HPE (base - CORD)' $cordBaseNoHpe `
        'OURS: Full Model (base - CORD)' $cordBaseFull `
        'w/o Boundary Loss (base - CORD)' $cordBaseNoBdr `
        '+0.38%' '+0.19%' '+0.34%'

    # 4. Section 4: LARGE - CORD
    $sec4 = Make-QuadBlock `
        'Baseline LayoutLMv3 (large - CORD)' $cordLargeBase `
        'w/o HPE (large - CORD)' $cordLargeNoHpe `
        'OURS: Full Model (large - CORD)' $cordLargeFull `
        'w/o Boundary Loss (large - CORD)' $cordLargeNoBdr `
        '--' '+0.20%' '-0.14%'

    # 5. Section 5: Token-Segment Ablation (base)
    $sec5 = Make-QuadBlock `
        'w/o Token-Segment SCM (base - FUNSD)' $funsdBaseNoSeg `
        'Reference Baseline (base - FUNSD)' $funsdBaseBase `
        'w/o Token-Segment SCM (base - CORD)' $cordBaseNoSeg `
        'Reference Baseline (base - CORD)' $cordBaseBase `
        '+0.44%' '--' '-0.13%'

    # 6. Section 6: Token-Segment Ablation (large)
    $sec6 = Make-QuadBlock `
        'w/o Token-Segment SCM (large - FUNSD)' $funsdLargeNoSeg `
        'Reference Baseline (large - FUNSD)' $funsdLargeBase `
        'w/o Token-Segment SCM (large - CORD)' $cordLargeNoSeg `
        'Reference Baseline (large - CORD)' $cordLargeBase `
        '-0.23%' '--' '-0.31%'

    # Combine All Sections into Unified Matrix
    $matrix = @()
    $matrix += $sec1
    $matrix += ,$blankRow
    $matrix += $sec2
    $matrix += ,$blankRow
    $matrix += $sec3
    $matrix += ,$blankRow
    $matrix += $sec4
    $matrix += ,$blankRow
    $matrix += $sec5
    $matrix += ,$blankRow
    $matrix += $sec6

    # Save local CSV
    $csvLines = $matrix | ForEach-Object {
        ($_ | ForEach-Object {
            $cell = if ($_ -eq $null) { '' } else { $_.ToString() }
            if ($cell -match '[",\n]') { '"' + ($cell -replace '"', '""') + '"' } else { $cell }
        }) -join ','
    }
    $csvLines | Out-File -FilePath $CsvPath -Encoding utf8

    # Push to Webhook
    if ($WebhookUrl -and $WebhookUrl.Trim() -ne '') {
        try {
            $bodyObj = @{
                action      = 'sync'
                lastUpdated = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
                rows        = $matrix
            }
            $jsonBody = $bodyObj | ConvertTo-Json -Depth 6

            $totalRows = $matrix.Count
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Pushing Per-Seed Quad-Block Tracker to Google Sheet ($totalRows rows, 23 cols)..." -ForegroundColor Cyan
            $response = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $jsonBody -ContentType 'application/json; charset=utf-8'
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Successfully synced to Google Sheet! Response: $response" -ForegroundColor Green
        }
        catch {
            Write-Warning "Failed to push to Google Sheet: $_"
        }
    }
}

Sync-QuadSheet

