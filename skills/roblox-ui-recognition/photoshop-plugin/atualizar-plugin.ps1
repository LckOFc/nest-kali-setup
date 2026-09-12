# FigmaPS2Roblox - Script de Atualização Unificado v2.1.0
# ==========================================
# Atualiza todos os arquivos do plugin para a versão mais recente
# ==========================================

param(
    [string]$SourceDir = "$PSScriptRoot",
    [string]$TargetDir = "",
    [switch]$Admin
)

$Version = "2.1.0"
$ExtensionId = "com.roblox.phototolua.panel"

# ── Detect Photoshop CEP Directories ─────────────────────────────
function Get-CEPDirectories {
    $results = @()
    $home = $env:USERPROFILE

    # User extensions (no need for admin)
    $userExt = Join-Path $home "AppData\Roaming\Adobe\CEP\extensions"
    if (Test-Path $userExt) {
        $results += $userExt
    }

    # System extensions (need admin)
    $sysExt = "C:\Program Files\Adobe\Common\Extensions"
    if (Test-Path $sysExt) {
        $results += $sysExt
    }

    return $results
}

# ── Copy files to target ────────────────────────────────────────
function Update-Plugin {
    param([string]$TargetDir)

    $extDir = Join-Path $TargetDir $ExtensionId
    Write-Host ""
    Write-Host "📦 Atualizando plugin para $extDir" -ForegroundColor Cyan

    # Create directories
    New-Item -ItemType Directory -Force -Path (Join-Path $extDir "CSXS") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $extDir "META-INF") | Out-Null

    # Files to update
    $files = @(
        "index.html",
        "hostscript.jsx",
        "cep.js",
        "BriefIcon.png"
    )

    $copied = 0
    foreach ($f in $files) {
        $src = Join-Path $SourceDir $f
        $dst = Join-Path $extDir $f
        if (Test-Path $src) {
            Copy-Item $src $dst -Force
            Write-Host "  ✅ $f" -ForegroundColor Green
            $copied++
        } else {
            Write-Host "  ⚠️  Não encontrado: $f" -ForegroundColor Yellow
        }
    }

    # CSXS folder
    $csxsSrc = Join-Path $SourceDir "CSXS"
    $csxsDst = Join-Path $extDir "CSXS"
    if (Test-Path $csxsSrc) {
        Get-ChildItem $csxsSrc | ForEach-Object {
            Copy-Item $_.FullName $csxsDst -Force
        }
        Write-Host "  ✅ CSXS/" -ForegroundColor Green
    }

    # META-INF/mimetype
    $mimetype = "application/x-extension-htm"
    [System.IO.File]::WriteAllText((Join-Path $extDir "META-INF\mimetype"), $mimetype, [System.Text.Encoding]::ASCII)
    Write-Host "  ✅ META-INF/mimetype" -ForegroundColor Green

    # META-INF/signatures.xml
    $signaturesXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://ns.adobe.com/axapplication/1.0/">
  <packageVersion>$Version</packageVersion>
</manifest>
"@
    [System.IO.File]::WriteAllText((Join-Path $extDir "META-INF\signatures.xml"), $signaturesXml, [System.Text.Encoding]::UTF8)
    Write-Host "  ✅ META-INF/signatures.xml" -ForegroundColor Green

    return $copied
}

# ── Main ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FigmaPS2Roblox - Update v$Version" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$cepDirs = Get-CEPDirectories

if ($cepDirs.Count -eq 0) {
    Write-Host "❌ Nenhum diretório de extensões do Photoshop encontrado." -ForegroundColor Red
    Write-Host ""
    Write-Host "Instalação manual:" -ForegroundColor Yellow
    Write-Host "Copie a pasta '$ExtensionId' para:" -ForegroundColor White
    foreach ($d in $cepDirs) {
        Write-Host "  $d" -ForegroundColor Gray
    }
    exit 1
}

# Use first available directory
$target = $TargetDir
if (-not $target) {
    $target = $cepDirs[0]
}

$copied = Update-Plugin -TargetDir $target

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ATUALIZAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. FECHA O PHOTOSHOP COMPLETAMENTE" -ForegroundColor White
Write-Host "     (File > Exit, verifique no Task Manager)"
Write-Host ""
Write-Host "  2. ABRA O PHOTOSHOP NOVAMENTE" -ForegroundColor White
Write-Host ""
Write-Host "  3. Vá em: Window > Extensions > FigmaPS2Roblox" -ForegroundColor White
Write-Host ""
Write-Host "Se o plugin NAO aparecer:" -ForegroundColor Yellow
Write-Host "  - Vá em Edit > Preferences > Plugins"
Write-Host "  - Garanta que estes dois estao marcados:" -ForegroundColor White
Write-Host "      [x] Allow Plugins to Access Files and Network"
Write-Host "      [x] Load Extension Panels"
Write-Host ""
