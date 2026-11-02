# Local PowerShell AI Detection & Writing Rhythm Evaluator
$ErrorActionPreference = "Stop"

$AI_BUZZWORDS = @(
    "delve", "delves", "delving",
    "testament", "tapestry", "pivotal",
    "underscores", "interplay", "leverage", "leveraging",
    "foster", "fostering", "beacon", "game-changer",
    "groundbreaking", "seamlessly", "holistic", "multifaceted",
    "plethora", "myriad", "paramount", "invaluable",
    "furthermore", "moreover", "in conclusion", "it is worth noting",
    "it is important to note", "not only", "spearheaded", "synergy"
)

function Strip-Latex([string]$text) {
    $text = [regex]::Replace($text, '(?m)%.*?$', '')
    $text = [regex]::Replace($text, '(?s)\$\$.*?\$\$', ' ')
    $text = [regex]::Replace($text, '\$.*?\$', ' ')
    $text = [regex]::Replace($text, '(?s)\\\[.*?\\\]', ' ')
    $text = [regex]::Replace($text, '(?s)\\begin\{(?:equation|align|table|tabular|tikzpicture|figure).*?\}\\end\{(?:equation|align|table|tabular|tikzpicture|figure)\*?\}', ' ')
    $text = [regex]::Replace($text, '\\(?:cite|ref|label|pageref|url|texttt)\{[^}]*\}', ' ')
    $text = [regex]::Replace($text, '\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}', '$1')
    $text = [regex]::Replace($text, '\\[a-zA-Z]+', ' ')
    $text = [regex]::Replace($text, '\s+', ' ').Trim()
    return $text
}

function Analyze-Prose([string]$prose) {
    $sentences = [regex]::Split($prose, '[.!?]+') | Where-Object { $_.Trim().Length -gt 3 }
    if ($sentences.Count -eq 0) { return $null }

    $lengths = @()
    foreach ($s in $sentences) {
        $w = ($s.Trim() -split '\s+') | Where-Object { $_.Length -gt 0 }
        if ($w.Count -gt 0) { $lengths += $w.Count }
    }
    if ($lengths.Count -eq 0) { return $null }

    $numS = $lengths.Count
    $totalW = ($lengths | Measure-Object -Sum).Sum
    $meanL = $totalW / $numS

    $sumSq = 0.0
    foreach ($l in $lengths) {
        $diff = $l - $meanL
        $sumSq += ($diff * $diff)
    }
    $variance = $sumSq / $numS
    $stdL = [Math]::Sqrt($variance)

    $shortS = ($lengths | Where-Object { $_ -le 12 }).Count
    $longS = ($lengths | Where-Object { $_ -gt 28 }).Count

    $lower = $prose.ToLower()
    $words = [regex]::Matches($lower, '\b[a-z\-]+\b') | ForEach-Object { $_.Value }
    $totalCleanWords = [Math]::Max(1, $words.Count)

    $buzzFound = 0
    $buzzDetails = @{}
    foreach ($bw in $AI_BUZZWORDS) {
        $c = [regex]::Matches($lower, "\b$bw\b").Count
        if ($c -gt 0) {
            $buzzDetails[$bw] = $c
            $buzzFound += $c
        }
    }
    $density = ($buzzFound / $totalCleanWords) * 1000

    $burstRisk = 2.0
    if ($stdL -lt 5.0) { $burstRisk = 35.0 }
    elseif ($stdL -lt 7.0) { $burstRisk = 20.0 }
    elseif ($stdL -lt 9.0) { $burstRisk = 8.0 }

    $buzzRisk = 1.0
    if ($density -gt 4.0) { $buzzRisk = 45.0 }
    elseif ($density -gt 2.0) { $buzzRisk = 25.0 }
    elseif ($density -gt 1.0) { $buzzRisk = 10.0 }

    $shortRatio = $shortS / $numS
    $longRatio = $longS / $numS
    $rhythmBonus = 5.0
    if ($shortRatio -ge 0.15 -and $longRatio -ge 0.10) { $rhythmBonus = -5.0 }

    $rawScore = [Math]::Max(1.5, [Math]::Min(95.0, ($burstRisk + $buzzRisk + $rhythmBonus)))

    return [PSCustomObject]@{
        NumSentences = $numS
        TotalWords = $totalW
        MeanLength = [Math]::Round($meanL, 2)
        StdDev = [Math]::Round($stdL, 2)
        ShortRatio = [Math]::Round($shortRatio * 100, 1)
        LongRatio = [Math]::Round($longRatio * 100, 1)
        TotalBuzzwords = $buzzFound
        BuzzwordDensity = [Math]::Round($density, 2)
        AiScorePercent = [Math]::Round($rawScore, 1)
        BuzzDetails = $buzzDetails
    }
}

Write-Host "================================================================"
Write-Host " LOCAL EVALUATOR: THESIS AI PATTERNS AND WRITING RHYTHM"
Write-Host "================================================================"

$rootMain = (Resolve-Path "thesis\en\main.tex").Path
$texFiles = Get-ChildItem -Path "thesis\en" -Filter "*.tex" -Recurse | Where-Object { $_.FullName -ne $rootMain -and $_.Name -ne "acronyms.tex" }
$allProse = @()

$header = ("{0,-32} | {1,6} | {2,7} | {3,10}" -f "Section / File", "Words", "StdDev", "% AI Score")
Write-Host $header
Write-Host ("-" * 64)

foreach ($f in $texFiles) {
    $raw = Get-Content -Path $f.FullName -Raw -Encoding UTF8
    $prose = Strip-Latex $raw
    $wCount = ($prose -split '\s+').Count
    if ($wCount -lt 30) { continue }

    $res = Analyze-Prose $prose
    if ($res) {
        $rel = $f.FullName.Replace((Resolve-Path "thesis\en").Path + "\", "")
        $line = ("{0,-32} | {1,6} | {2,7} | {3,9}%" -f $rel, $res.TotalWords, $res.StdDev, $res.AiScorePercent)
        Write-Host $line
        $allProse += $prose
    }
}

$fullProse = $allProse -join " "
$overall = Analyze-Prose $fullProse

Write-Host ("-" * 64)
$totalLine = ("{0,-32} | {1,6} | {2,7} | {3,9}%" -f "OVERALL THESIS (Aggregated)", $overall.TotalWords, $overall.StdDev, $overall.AiScorePercent)
Write-Host $totalLine
Write-Host ("=" * 64)

if ($overall.AiScorePercent -le 20.0) {
    Write-Host "VERDICT: PASS! Overall AI Score ($($overall.AiScorePercent)%) is comfortably below threshold (< 20%)."
} else {
    Write-Host "VERDICT: FAIL! Overall AI Score ($($overall.AiScorePercent)%) exceeds threshold (< 20%)."
}
