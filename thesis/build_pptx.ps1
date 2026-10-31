param(
    [string]$PdfPath = "thesis\presentation\weekly_update_slides.pdf",
    [string]$PptxPath = "thesis\presentation\weekly_update_slides.pptx",
    [uint32]$Dpi = 300
)

$ErrorActionPreference = "Stop"
$PdfPath = (Resolve-Path $PdfPath).Path
$PptxPath = [System.IO.Path]::GetFullPath($PptxPath)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

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

Write-Host "Loading PDF: $PdfPath" -ForegroundColor Cyan
$file = Await-Operation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($PdfPath)) ([Windows.Storage.StorageFile])
$pdfDoc = Await-Operation ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
$pageCount = [int]$pdfDoc.PageCount
Write-Host "Rendering $pageCount slides at $Dpi DPI..." -ForegroundColor Cyan

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("pptx_build_" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "_rels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "ppt\_rels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "ppt\slides\_rels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "ppt\slideLayouts\_rels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "ppt\slideMasters\_rels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "ppt\theme") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "ppt\media") -Force | Out-Null

$scale = $Dpi / 96.0
for ($i = 0; $i -lt $pageCount; $i++) {
    $slideNum = $i + 1
    $page = $pdfDoc.GetPage([uint32]$i)
    $renderOptions = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $renderOptions.DestinationWidth = [uint32]([Math]::Round($page.Size.Width * $scale))
    $renderOptions.DestinationHeight = [uint32]([Math]::Round($page.Size.Height * $scale))

    $pngPath = Join-Path $tempDir "ppt\media\slide$slideNum.png"
    $outFile = [System.IO.File]::Open($pngPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::ReadWrite)
    $outStream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($outFile)
    Await-Action ($page.RenderToStreamAsync($outStream, $renderOptions))
    $outStream.Dispose()
    $outFile.Dispose()
    $page.Dispose()
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
function Write-XmlFile([string]$RelPath, [string]$XmlContent) {
    $fullPath = Join-Path $tempDir $RelPath
    [System.IO.File]::WriteAllText($fullPath, $XmlContent, $utf8NoBom)
}

# 1. [Content_Types].xml
$slideOverrides = ""
for ($s = 1; $s -le $pageCount; $s++) {
    $slideOverrides += "  <Override PartName=`"/ppt/slides/slide$s.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.slide+xml`"/>`r`n"
}
$contentTypesXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
$slideOverrides</Types>
"@
Write-XmlFile "[Content_Types].xml" $contentTypesXml

# 2. _rels/.rels
$rootRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>
"@
Write-XmlFile "_rels\.rels" $rootRelsXml

# 3. ppt/presentation.xml & ppt/_rels/presentation.xml.rels
# Widescreen 16:9 in EMUs: 12192000 x 6858000
$cx = 12192000
$cy = 6858000
$sldIdList = ""
$presRelsList = ""
for ($s = 1; $s -le $pageCount; $s++) {
    $idVal = 255 + $s
    $sldIdList += "    <p:sldId id=`"$idVal`" r:id=`"rIdSlide$s`"/>`r`n"
    $presRelsList += "  <Relationship Id=`"rIdSlide$s`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide`" Target=`"slides/slide$s.xml`"/>`r`n"
}

$presentationXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" saveSubsetFonts="1">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rIdMaster1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
$sldIdList  </p:sldIdLst>
  <p:sldSz cx="$cx" cy="$cy"/>
  <p:notesSz cx="$cy" cy="$cx"/>
</p:presentation>
"@
Write-XmlFile "ppt\presentation.xml" $presentationXml

$presRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdMaster1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rIdTheme1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
$presRelsList</Relationships>
"@
Write-XmlFile "ppt\_rels\presentation.xml.rels" $presRelsXml

# 4. ppt/slideMasters/slideMaster1.xml & rels
$slideMasterXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg>
      <p:bgRef idx="1001">
        <a:schemeClr val="bg1"/>
      </p:bgRef>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rIdLayout1"/>
  </p:sldLayoutIdLst>
</p:sldMaster>
"@
Write-XmlFile "ppt\slideMasters\slideMaster1.xml" $slideMasterXml

$slideMasterRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdLayout1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rIdTheme1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
"@
Write-XmlFile "ppt\slideMasters\_rels\slideMaster1.xml.rels" $slideMasterRelsXml

# 5. ppt/slideLayouts/slideLayout1.xml & rels
$slideLayoutXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sldLayout>
"@
Write-XmlFile "ppt\slideLayouts\slideLayout1.xml" $slideLayoutXml

$slideLayoutRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdMaster1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
"@
Write-XmlFile "ppt\slideLayouts\_rels\slideLayout1.xml.rels" $slideLayoutRelsXml

# 6. ppt/theme/theme1.xml
$themeXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F497D"/></a:dk2>
      <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
      <a:accent1><a:srgbClr val="195696"/></a:accent1>
      <a:accent2><a:srgbClr val="DC6414"/></a:accent2>
      <a:accent3><a:srgbClr val="18824C"/></a:accent3>
      <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
      <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
      <a:accent6><a:srgbClr val="F79646"/></a:accent6>
      <a:hlink><a:srgbClr val="0000FF"/></a:hlink>
      <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>
"@
Write-XmlFile "ppt\theme\theme1.xml" $themeXml

# 7. Individual slides (ppt/slides/slide1..N.xml and rels)
for ($s = 1; $s -le $pageCount; $s++) {
    $slideXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:pic>
        <p:nvPicPr>
          <p:cNvPr id="2" name="SlideImage$s"/>
          <p:cNvPicPr>
            <a:picLocks noChangeAspect="1"/>
          </p:cNvPicPr>
          <p:nvPr/>
        </p:nvPicPr>
        <p:blipFill>
          <a:blip r:embed="rIdImg1"/>
          <a:stretch>
            <a:fillRect/>
          </a:stretch>
        </p:blipFill>
        <p:spPr>
          <a:xfrm>
            <a:off x="0" y="0"/>
            <a:ext cx="$cx" cy="$cy"/>
          </a:xfrm>
          <a:prstGeom prst="rect">
            <a:avLst/>
          </a:prstGeom>
        </p:spPr>
      </p:pic>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>
"@
    Write-XmlFile "ppt\slides\slide$s.xml" $slideXml

    $slideRelsXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdLayout1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rIdImg1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/slide$s.png"/>
</Relationships>
"@
    Write-XmlFile "ppt\slides\_rels\slide$s.xml.rels" $slideRelsXml
}

# 8. Package into .pptx ZIP with forward-slash entry paths (required by OpenXML & Google Slides)
if (Test-Path $PptxPath) { Remove-Item $PptxPath -Force }
$zipFile = [System.IO.File]::Open($PptxPath, [System.IO.FileMode]::Create)
$zip = New-Object System.IO.Compression.ZipArchive($zipFile, [System.IO.Compression.ZipArchiveMode]::Create)

$allFiles = Get-ChildItem -Path $tempDir -Recurse -File
foreach ($f in $allFiles) {
    $rel = $f.FullName.Substring($tempDir.Length + 1).Replace('\', '/')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $f.FullName, $rel, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
}

$zip.Dispose()
$zipFile.Dispose()
Remove-Item -Path $tempDir -Recurse -Force

$sizeMb = [Math]::Round((Get-Item $PptxPath).Length / 1MB, 2)
Write-Host "Successfully built PowerPoint presentation: $PptxPath ($pageCount slides, $sizeMb MB)" -ForegroundColor Green

