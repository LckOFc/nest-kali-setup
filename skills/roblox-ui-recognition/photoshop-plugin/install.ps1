$dst = "C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel"
$src = "C:\Users\devel\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel"

New-Item -ItemType Directory -Force -Path (Join-Path $dst "CSXS") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dst "META-INF") | Out-Null

Copy-Item (Join-Path $src "index.html") $dst -Force
Copy-Item (Join-Path $src "hostscript.jsx") $dst -Force
Copy-Item (Join-Path $src "cep.js") $dst -Force
Copy-Item (Join-Path $src "BriefIcon.png") $dst -Force
Copy-Item (Join-Path $src "CSXS\*") (Join-Path $dst "CSXS") -Force

"application/x-extension-htm" | Out-File -Encoding ASCII (Join-Path $dst "META-INF\mimetype")

$xml = '<?xml version="1.0" encoding="UTF-8" ?><manifest xmlns="http://ns.adobe.com/axapplication/1.0/"><packageVersion>1.0.0</packageVersion></manifest>'
$xml | Out-File -Encoding UTF8 (Join-Path $dst "META-INF\signatures.xml")

Write-Host "INSTALACAO CONCLUIDA!" -ForegroundColor Green
