<#
.SYNOPSIS
    Real-time synchronization script to Google Sheet live tracker:
    https://docs.google.com/spreadsheets/d/173WXkbMXDCEVs4pYBRNXGTHihOda18adbJRJ7RpFw7o/edit

    Features:
    - Side-by-side per-seed detailed report across Seeds 42, 123, 1993, and Mean ± STD
    - Direct comparisons between Baseline LayoutLMv3, Ablations, and Proposed Full Model (OURS)
    - Direct Delta F1 Gain highlighted between models
    - Complete 23-column Quad-Block layout matching the sample sheet design
    - Standardized naming matching our official experiment titles
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
        return (Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json)
    }
    return $null
}

function Fmt-N($val) {
    if ($val -eq $null) { return '--' }
    return [string]::Format('{0:0.0000}', [double]$val)
}

function Fmt-MS($m, $s) {
    if ($m -eq $null) { return '--' }
    return [string]::Format('{0:0.0000} ± {1:0.0000}', [double]$m, [double]$s)
}

function Calc-Delta($targetObj, $baseObj) {
    if ($targetObj -and $baseObj -and $targetObj.mean_std -and $baseObj.mean_std) {
        $tF1 = [double]$targetObj.mean_std.eval_f1.mean
        $bF1 = [double]$baseObj.mean_std.eval_f1.mean
        $diff = ($tF1 - $bF1) * 100.0
        return [string]::Format('{0:+0.00;-0.00;0.00}%', $diff)
    }
    return '--'
}

function Make-QuadBlock(
    $t1, $o1,
    $t2, $o2,
    $t3, $o3,
    $t4, $o4,
    $gain2, $gain3, $gain4
) {
    $rows = @()
    # Row 0: Model Titles
    $r0 = @($t1, '', '', '', '', '', $t2, '', '', '', '', '', $t3, '', '', '', '', '', $t4, '', '', '', '')
    # Row 1: Headers
    $r1 = @(
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD', '',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD', 'Delta F1',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD', 'Delta F1',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD'
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

        # Model 2: Ablation w/o HPE
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

        # Model 4: Ablation w/o Boundary Loss
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
    $funsdLargeNoHpe = Load-Json "funsd-large-no_hpe_3seed_summary.json"
    $funsdLargeNoBdr = Load-Json "funsd-large-no_boundary_3seed_summary.json"
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
    $cordLargeNoHpe = Load-Json "cord-large-no_hpe_3seed_summary.json"
    $cordLargeNoBdr = Load-Json "cord-large-no_boundary_3seed_summary.json"
    $cordLargeNoSeg = Load-Json "cord-large-no_segment_3seed_summary.json"

    $blankRow = @('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')

    # 1. Section 1: LARGE - FUNSD
    $gain1_2 = Calc-Delta $funsdLargeNoHpe $funsdLargeBase
    $gain1_3 = Calc-Delta $funsdLargeFull $funsdLargeBase
    $gain1_4 = Calc-Delta $funsdLargeNoBdr $funsdLargeBase
    $sec1 = Make-QuadBlock `
        'Baseline: Layoutlmv3 (Large - FUNSD)' $funsdLargeBase `
        'Ablation: w/o HPE (Large - FUNSD)' $funsdLargeNoHpe `
        'OURS: Full Model (Large - FUNSD)' $funsdLargeFull `
        'Ablation: w/o Boundary Loss (Large - FUNSD)' $funsdLargeNoBdr `
        $gain1_2 $gain1_3 $gain1_4

    # 2. Section 2: BASE - FUNSD
    $gain2_2 = Calc-Delta $funsdBaseNoHpe $funsdBaseBase
    $gain2_3 = Calc-Delta $funsdBaseFull $funsdBaseBase
    $gain2_4 = Calc-Delta $funsdBaseNoBdr $funsdBaseBase
    $sec2 = Make-QuadBlock `
        'Baseline: Layoutlmv3 (Base - FUNSD)' $funsdBaseBase `
        'Ablation: w/o HPE (Base - FUNSD)' $funsdBaseNoHpe `
        'OURS: Full Model (Base - FUNSD)' $funsdBaseFull `
        'Ablation: w/o Boundary Loss (Base - FUNSD)' $funsdBaseNoBdr `
        $gain2_2 $gain2_3 $gain2_4

    # 3. Section 3: BASE - CORD
    $gain3_2 = Calc-Delta $cordBaseNoHpe $cordBaseBase
    $gain3_3 = Calc-Delta $cordBaseFull $cordBaseBase
    $gain3_4 = Calc-Delta $cordBaseNoBdr $cordBaseBase
    $sec3 = Make-QuadBlock `
        'Baseline: Layoutlmv3 (Base - CORD)' $cordBaseBase `
        'Ablation: w/o HPE (Base - CORD)' $cordBaseNoHpe `
        'OURS: Full Model (Base - CORD)' $cordBaseFull `
        'Ablation: w/o Boundary Loss (Base - CORD)' $cordBaseNoBdr `
        $gain3_2 $gain3_3 $gain3_4

    # 4. Section 4: LARGE - CORD
    $gain4_2 = Calc-Delta $cordLargeNoHpe $cordLargeBase
    $gain4_3 = Calc-Delta $cordLargeFull $cordLargeBase
    $gain4_4 = Calc-Delta $cordLargeNoBdr $cordLargeBase
    $sec4 = Make-QuadBlock `
        'Baseline: Layoutlmv3 (Large - CORD)' $cordLargeBase `
        'Ablation: w/o HPE (Large - CORD)' $cordLargeNoHpe `
        'OURS: Full Model (Large - CORD)' $cordLargeFull `
        'Ablation: w/o Boundary Loss (Large - CORD)' $cordLargeNoBdr `
        $gain4_2 $gain4_3 $gain4_4

    # 5. Section 5: Token-Segment Ablation (Base Models)
    $gain5_1 = Calc-Delta $funsdBaseNoSeg $funsdBaseBase
    $gain5_3 = Calc-Delta $cordBaseNoSeg $cordBaseBase
    $sec5 = Make-QuadBlock `
        'Ablation: w/o Token-Segment (Layoutlmv3 Base - FUNSD)' $funsdBaseNoSeg `
        'Reference: Baseline Layoutlmv3 (Base - FUNSD)' $funsdBaseBase `
        'Ablation: w/o Token-Segment (Layoutlmv3 Base - CORD)' $cordBaseNoSeg `
        'Reference: Baseline Layoutlmv3 (Base - CORD)' $cordBaseBase `
        $gain5_1 '--' $gain5_3

    # 6. Section 6: Token-Segment Ablation (Large Models)
    $gain6_1 = Calc-Delta $funsdLargeNoSeg $funsdLargeBase
    $gain6_3 = Calc-Delta $cordLargeNoSeg $cordLargeBase
    $sec6 = Make-QuadBlock `
        'Ablation: w/o Token-Segment (Layoutlmv3 Large - FUNSD)' $funsdLargeNoSeg `
        'Reference: Baseline Layoutlmv3 (Large - FUNSD)' $funsdLargeBase `
        'Ablation: w/o Token-Segment (Layoutlmv3 Large - CORD)' $cordLargeNoSeg `
        'Reference: Baseline Layoutlmv3 (Large - CORD)' $cordLargeBase `
        $gain6_1 '--' $gain6_3

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