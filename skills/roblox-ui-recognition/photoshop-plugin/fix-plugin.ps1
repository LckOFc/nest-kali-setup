# Fix Plugin - FigmaPS2Roblox
# Simple fix script for Photoshop plugin connection issues

$PluginID = "com.roblox.phototolua.panel"
$SourceDir = "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin"
$PluginPath = Join-Path $env:APPDATA "Adobe\CEP\extensions\$PluginID"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FigmaPS2Roblox - Fix Plugin" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Reinstall plugin
Write-Host "[1/4] Reinstalando plugin..." -ForegroundColor Yellow

if (Test-Path $PluginPath) {
    Remove-Item $PluginPath -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $PluginPath | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PluginPath "CSXS") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PluginPath "META-INF") | Out-Null

# Copy files
Copy-Item (Join-Path $SourceDir "index.html") $PluginPath -Force
Copy-Item (Join-Path $SourceDir "hostscript.jsx") $PluginPath -Force
Copy-Item (Join-Path $SourceDir "cep.js") $PluginPath -Force
Copy-Item (Join-Path $SourceDir "BriefIcon.png") $PluginPath -Force
Copy-Item (Join-Path $SourceDir "CSXS\*") (Join-Path $PluginPath "CSXS") -Recurse -Force

# Create META-INF files
"application/x-extension-htm" | Out-File (Join-Path $PluginPath "META-INF\mimetype") -Encoding ascii
@"
<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://ns.adobe.com/axapplication/1.0/">
  <packageVersion>2.1.0</packageVersion>
</manifest>
"@ | Out-File (Join-Path $PluginPath "META-INF\signatures.xml") -Encoding utf8

Write-Host "  [OK] Plugin reinstalado" -ForegroundColor Green
Write-Host ""

# Step 2: Check CEP installation
Write-Host "[2/4] Verificando CEP Runtime..." -ForegroundColor Yellow

$cepPaths = @(
    "HKLM:\SOFTWARE\Adobe\CSXS.11",
    "HKLM:\SOFTWARE\WOW6432Node\Adobe\CSXS.11",
    "HKCU:\SOFTWARE\Adobe\CSXS.11"
)

$cepFound = $false
foreach ($p in $cepPaths) {
    if (Test-Path $p) {
        $cepFound = $true
        Write-Host "  [OK] CEP encontrado em: $p" -ForegroundColor Green
        break
    }
}

if (-not $cepFound) {
    Write-Host "  [X] CEP Runtime nao encontrado!" -ForegroundColor Red
    Write-Host "      Baixe em: https://github.com/Adobe-CEP/CEP-Resources" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Check Photoshop preferences
Write-Host "[3/4] Verificando preferencias do Photoshop..." -ForegroundColor Yellow

$psPaths = @(
    "HKCU:\Software\Adobe\Photoshop",
    "HKLM:\SOFTWARE\Adobe\Photoshop"
)

foreach ($psPath in $psPaths) {
    if (Test-Path $psPath) {
        $versions = Get-ChildItem $psPath -ErrorAction SilentlyContinue
        if ($versions) {
            $latest = $versions | Sort-Object Name -Descending | Select-Object -First 1
            $configPath = $latest.PSPath + "\Configuration"
            
            if (-not (Test-Path $configPath)) {
                New-Item -ItemType Directory -Force -Path $configPath | Out-Null
            }
            
            Set-ItemProperty -Path $configPath -Name "AMGeneral_ADOBE_EXTENSIONS_ALLOW_PLUGIN" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $configPath -Name "AMGeneral_ADOBE_EXTENSIONS_ALLOW_PANELS" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
            
            Write-Host "  [OK] Plugins habilitados" -ForegroundColor Green
            break
        }
    }
}
Write-Host ""

# Step 4: Instructions
Write-Host "[4/4] PROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. FECHA O PHOTOSHOP COMPLETAMENTE" -ForegroundColor White
Write-Host "     - Pressione Ctrl+Shift+Esc" -ForegroundColor Gray
Write-Host "     - Finalize todos os processos 'Photoshop'" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. ABRA O PHOTOSHOP NOVAMENTE" -ForegroundColor White
Write-Host ""
Write-Host "  3. Vá em: Window > Extensions > FigmaPS2Roblox" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  CONCLUIDO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
