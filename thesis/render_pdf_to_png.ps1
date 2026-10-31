param(
    [string]$PdfPath = "thesis\figures\model_architecture_heads_style.pdf",
    [string]$PngPath = "thesis\figures\model_architecture_heads_style.png",
    [uint32]$Dpi = 300
)

$ErrorActionPreference = "Stop"
$PdfPath = (Resolve-Path $PdfPath).Path
$PngPath = [System.IO.Path]::GetFullPath($PngPath)

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
$page = $pdfDoc.GetPage(0)

$renderOptions = New-Object Windows.Data.Pdf.PdfPageRenderOptions
$scale = $Dpi / 96.0
$renderOptions.DestinationWidth = [uint32]([Math]::Round($page.Size.Width * $scale))
$renderOptions.DestinationHeight = [uint32]([Math]::Round($page.Size.Height * $scale))

if (Test-Path $PngPath) { Remove-Item $PngPath -Force }
$outFile = [System.IO.File]::Open($PngPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::ReadWrite)
$outStream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($outFile)

Await-Action ($page.RenderToStreamAsync($outStream, $renderOptions))

$outStream.Dispose()
$outFile.Dispose()
$page.Dispose()

Write-Host "Successfully rendered $PdfPath to $PngPath ($($renderOptions.DestinationWidth)x$($renderOptions.DestinationHeight) px at $Dpi DPI)" -ForegroundColor Green
