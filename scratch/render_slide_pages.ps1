param(
    [string]$PdfPath = "thesis\presentation\weekly_update_slides.pdf",
    [string]$OutDir = "thesis\presentation\previews",
    [uint32]$Dpi = 150
)

$ErrorActionPreference = "Stop"
$PdfPath = (Resolve-Path $PdfPath).Path
$OutDir = [System.IO.Path]::GetFullPath($OutDir)
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
$asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
})[0]

function Await-Operation($WinRtTask, $ResultType) {
    $netTask = $asTaskGeneric.MakeGenericMethod($ResultType).Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}
function Await-Action($WinRtAction) {
    $netTask = $asTaskAction.Invoke($null, @($WinRtAction))
    $netTask.Wait(-1) | Out-Null
}

$file = Await-Operation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($PdfPath)) ([Windows.Storage.StorageFile])
$pdfDoc = Await-Operation ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])

Write-Host "Rendering $($pdfDoc.PageCount) pages from $PdfPath to $OutDir ..."

for ($i = 0; $i -lt $pdfDoc.PageCount; $i++) {
    $page = $pdfDoc.GetPage($i)
    $renderOptions = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $scale = $Dpi / 96.0
    $renderOptions.DestinationWidth = [uint32]([Math]::Round($page.Size.Width * $scale))
    $renderOptions.DestinationHeight = [uint32]([Math]::Round($page.Size.Height * $scale))

    $pngPath = Join-Path $OutDir ("slide_" + ($i + 1).ToString("D2") + ".png")
    if (Test-Path $pngPath) { Remove-Item $pngPath -Force }
    $outFile = [System.IO.File]::Open($pngPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::ReadWrite)
    $outStream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($outFile)

    Await-Action ($page.RenderToStreamAsync($outStream, $renderOptions))
    $outStream.Dispose()
    $outFile.Dispose()
    Write-Host "Rendered slide $($i + 1) -> $pngPath"
}

