# FigmaPS2Roblox - Instalador Completo do Plugin Photoshop 2024
# ==========================================
# Executar COMO ADMINISTRADOR
# ==========================================

$src = "C:\Users\devel\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel"
$dst = "C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FigmaPS2Roblox - Instalacao Completa v2" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar extensao de origem
if (-not (Test-Path $src)) {
    Write-Host "ERRO: Extensao nao encontrada em:" -ForegroundColor Red
    Write-Host "  $src" -ForegroundColor Yellow
    pause
    exit 1
}

# Criar estrutura de diretorios
Write-Host "Preparando estrutura..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $dst | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dst "CSXS") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dst "META-INF") | Out-Null

# Copiar arquivos principais (incluindo cep.js)
$files = @("index.html", "hostscript.jsx", "BriefIcon.png", "cep.js")
foreach ($f in $files) {
    $srcFile = Join-Path $src $f
    $dstFile = Join-Path $dst $f
    if (Test-Path $srcFile) {
        Copy-Item $srcFile $dstFile -Force
        Write-Host "  OK: $f" -ForegroundColor Green
    } else {
        Write-Host "  FALHA: $f" -ForegroundColor Red
    }
}

# Copiar pasta CSXS
$csxsSrc = Join-Path $src "CSXS"
$csxsDst = Join-Path $dst "CSXS"
if (Test-Path $csxsSrc) {
    Get-ChildItem $csxsSrc | ForEach-Object {
        Copy-Item $_.FullName $csxsDst -Force
    }
    Write-Host "  OK: CSXS/" -ForegroundColor Green
}

# Criar META-INF/mimetype
$mimetype = "application/x-extension-htm"
[System.IO.File]::WriteAllText((Join-Path $dst "META-INF\mimetype"), $mimetype, [System.Text.Encoding]::ASCII)
Write-Host "  OK: META-INF/mimetype" -ForegroundColor Green

# Criar META-INF/signatures.xml
$signaturesXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://ns.adobe.com/axapplication/1.0/">
  <packageVersion>1.0.0</packageVersion>
</manifest>
"@
[System.IO.File]::WriteAllText((Join-Path $dst "META-INF\signatures.xml"), $signaturesXml, [System.Text.Encoding]::UTF8)
Write-Host "  OK: META-INF/signatures.xml" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  INSTALACAO CONCLUIDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Estrutura instalada:" -ForegroundColor Yellow
Write-Host "  $dst" -ForegroundColor White
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "  1. FECH O PHOTOSHOP COMPLETAMENTE" -ForegroundColor White
Write-Host "     (File > Exit, verifique no Task Manager)"
Write-Host ""
Write-Host "  2. ABRA O PHOTOSHOP NOVAMENTE" -ForegroundColor White
Write-Host ""
Write-Host "  3. Vá em: Window > Extensions > FigmaPS2Roblox" -ForegroundColor White
Write-Host "     OU no menu: Plug-ins > FigmaPS2Roblox"
Write-Host ""
Write-Host "Se o plugin NAO aparecer:" -ForegroundColor Yellow
Write-Host "  - Vá em Edit > Preferences > Plugins"
Write-Host "  - Garanta que estes dois estao marcados:" -ForegroundColor White
Write-Host "      [x] Allow Plugins to Access Files and Network"
Write-Host "      [x] Load Extension Panels"
Write-Host ""
