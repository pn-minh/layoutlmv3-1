Add-Type -AssemblyName System.Drawing

$imgFile = (Resolve-Path "thesis/figures/heads_model_architecture_migrated.png").Path
$bmp = [System.Drawing.Bitmap]::FromFile($imgFile)

$outDir = (Resolve-Path "thesis/presentation/images").Path
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

# Scale factor & offset mapping from draw.io coordinates to pixel coordinates
# Drawio content: X in [40, 1160] (width 1120), Y in [40, 1130] (height 1090)
# Pixel content: X in [160, 3556] (width 3396), Y in [240, 3544] (height 3304)
$scaleX = 3396.0 / 1120.0
$scaleY = 3304.0 / 1090.0
$offsetX = 160.0 - 40.0 * $scaleX
$offsetY = 240.0 - 40.0 * $scaleY

function Export-Crop {
    param(
        [string]$Name,
        [double]$dx, [double]$dy, [double]$dw, [double]$dh,
        [double]$pad = 6.0
    )
    # Convert draw.io coordinates to pixel coordinates with padding
    $px0 = [Math]::Max(0, [int](($dx - $pad) * $scaleX + $offsetX))
    $py0 = [Math]::Max(0, [int](($dy - $pad) * $scaleY + $offsetY))
    $px1 = [Math]::Min($bmp.Width, [int](($dx + $dw + $pad) * $scaleX + $offsetX))
    $py1 = [Math]::Min($bmp.Height, [int](($dy + $dh + $pad) * $scaleY + $offsetY))

    $cw = $px1 - $px0
    $ch = $py1 - $py0

    $cropBmp = New-Object System.Drawing.Bitmap($cw, $ch)
    $g = [System.Drawing.Graphics]::FromImage($cropBmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

    $srcRect = New-Object System.Drawing.Rectangle($px0, $py0, $cw, $ch)
    $dstRect = New-Object System.Drawing.Rectangle(0, 0, $cw, $ch)
    $g.DrawImage($bmp, $dstRect, $srcRect, [System.Drawing.GraphicsUnit]::Pixel)

    $outPath = Join-Path $outDir "$Name.png"
    $cropBmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)

    $g.Dispose()
    $cropBmp.Dispose()
    Write-Host "Exported $Name.png : $cw x $ch (from drawio: x=$dx, y=$dy, w=$dw, h=$dh)"
}

# 1. Input Module (c_input: x=40, y=40, w=460, h=260)
Export-Crop "crop_input" 40 40 460 260 8

# 2. Hierarchical Position Encoding (c_hpe: x=40, y=330, w=460, h=270)
Export-Crop "crop_hpe" 40 330 460 270 8

# 3. LayoutLMv3 Backbone (adder node x=535, pillar x=605, token cubes to x=825, y=40..600)
Export-Crop "crop_backbone" 525 35 315 570 8

# 4. Segment Context Module & Classifier (c_scm: x=730, y=40, w=430, h=140; fusion + softmax down to y=400)
Export-Crop "crop_scm" 725 35 440 370 8

# 5. Intra-Line Boundary Loss (c_boundary: x=40, y=650, w=435, h=310)
Export-Crop "crop_boundary" 40 650 435 310 8

# 6. Cross-Modal Contrastive Loss (c_contrastive: x=505, y=650, w=435, h=310)
Export-Crop "crop_contrastive" 505 650 435 310 8

# 7. Classification Loss (c_cls_loss: x=965, y=650, w=195, h=310)
Export-Crop "crop_cls_loss" 965 650 195 310 8

# 8. Multi-Task Training Objective (c_total_loss: x=40, y=1020, w=1120, h=110)
Export-Crop "crop_total_loss" 40 1020 1120 110 8

# 9. Loss Integration & Multi-Task Objective combined
Export-Crop "crop_loss_objective" 35 645 1130 490 8

$bmp.Dispose()
Write-Host "All component crops successfully created!"
