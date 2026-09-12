# FigmaPS2Roblox - Instalador do Plugin para Photoshop 2024
# ==========================================
# Este script copia a extensão para o diretório do Photoshop.
# PRECISA SER EXECUTADO COMO ADMINISTRADOR.
# ==========================================

$src = "C:\Users\devel\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel"
$dst = "C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FigmaPS2Roblox - Instalador" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se a extensão de origem existe
if (-not (Test-Path $src)) {
    Write-Host "ERRO: Extensao nao encontrada!" -ForegroundColor Red
    Write-Host "  Caminho: $src" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Verifique se a extensao foi gerada corretamente." -ForegroundColor Yellow
    pause
    exit 1
}

# Criar diretorio de destino
Write-Host "Copiando extensao..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $dst | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dst "CSXS") | Out-Null

# Copiar arquivos principais
$files = @("index.html", "hostscript.jsx", "BriefIcon.png")
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
        Write-Host "  OK: CSXS/$($_.Name)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  INSTALACAO CONCLUIDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "  1. Feche o Photoshop COMPLETAMENTE" -ForegroundColor White
Write-Host "     (File > Exit, verifique no Task Manager)"
Write-Host ""
Write-Host "  2. Abra o Photoshop" -ForegroundColor White
Write-Host ""
Write-Host "  3. Vá em: Window > Extensions > FigmaPS2Roblox" -ForegroundColor White
Write-Host "     OU: Plug-ins > FigmaPS2Roblox"
Write-Host ""
Write-Host "Se ainda nao aparecer:" -ForegroundColor Yellow
Write-Host "  - Vá em Edit > Preferences > Plugins"
Write-Host "  - Marque: 'Allow Plugins to Access Files and Network'"
Write-Host "  - Marque: 'Load Extension Panels'"
Write-Host "  - Reinicie o Photoshop"
Write-Host ""
