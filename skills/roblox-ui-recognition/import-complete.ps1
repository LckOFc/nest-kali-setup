# ============================================================
# Script de Importação Completa — FigmaPS2Roblox v3.0.0
# ============================================================
# Automatiza todo o processo: PSD → Processamento → Importação
#
# Uso: .\import-complete.ps1 <psd-path> [--project caminho] [--screen Nome]
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$PsdPath,
    
    [string]$ScreenName = "Screen",
    
    [string]$ProjectPath = "",
    
    [string]$Method = "copy",  # copy, api, powerautomate
    [string]$Cookie = "",
    
    [switch]$NoPipeline,
    [switch]$OpenRoblox,
    [switch]$GenerateGuide
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     FigmaPS2Roblox — Importação Completa Automatizada    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# ── Funções ─────────────────────────────────────────────────────────────────────

function Write-Step {
    param([string]$Message)
    Write-Host "`n[STEP] $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor Red
}

# ── Verificar Pré-requisitos ────────────────────────────────────────────────────

Write-Step "Verificando pré-requisitos..."

$checks = @{
    "Node.js" = $null
    "Sharp" = $null
    "PSD Exists" = Test-Path $PsdPath
}

# Node.js
try {
    $nodeVersion = node --version
    $checks["Node.js"] = "OK ($nodeVersion)"
    Write-Success "Node.js: $nodeVersion"
} catch {
    $checks["Node.js"] = "MISSING"
    Write-Error-Custom "Node.js não encontrado"
}

# Sharp
try {
    $sharpCheck = node -e "require('sharp')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $checks["Sharp"] = "OK"
        Write-Success "Sharp: instalado"
    } else {
        $checks["Sharp"] = "MISSING"
        Write-Error-Custom "Sharp não instalado (execute: npm install sharp)"
    }
} catch {
    $checks["Sharp"] = "ERROR"
}

# PSD
if ($checks["PSD Exists"]) {
    Write-Success "PSD encontrado: $PsdPath"
} else {
    Write-Error-Custom "PSD não encontrado: $PsdPath"
    exit 1
}

# ── Fase 1: Pipeline PSD → Assets ──────────────────────────────────────────────

if (-not $NoPipeline) {
    Write-Step "Fase 1: Processando PSD..."
    
    $outputDir = Join-Path $ScriptDir "output"
    $nodeScript = Join-Path $ScriptDir "psd-to-roblox-ai.js"
    
    $args = @($PsdPath, "--screen", $ScreenName, "--output", $outputDir)
    
    if ($Cookie) {
        $env:OPENAI_API_KEY = $Cookie
    }
    
    try {
        $output = node $nodeScript @args 2>&1
        Write-Host $output
        Write-Success "Pipeline concluído!"
    } catch {
        Write-Error-Custom "Falha no pipeline: $_"
        exit 1
    }
} else {
    Write-Info "Pipeline pulado (--no-pipeline)"
}

# ── Fase 2: Importação Automatizada ────────────────────────────────────────────

Write-Step "Fase 2: Importando para Roblox..."

$autoImporter = Join-Path $ScriptDir "roblox-auto-importer.js"
$assetsDir = Join-Path $ScriptDir "output"

if (Test-Path $autoImporter) {
    $importArgs = @($assetsDir, "--method", $Method)
    
    if ($ProjectPath) {
        $importArgs += "--project"
        $importArgs += $ProjectPath
    }
    
    $importArgs += "--screen"
    $importArgs += $ScreenName
    
    if ($Cookie) {
        $importArgs += "--cookie"
        $importArgs += $Cookie
    }
    
    try {
        $importOutput = node $autoImporter @importArgs 2>&1
        Write-Host $importOutput
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Importação concluída!"
        } else {
            Write-Error-Custom "Falha na importação"
        }
    } catch {
        Write-Error-Custom "Erro na importação: $_"
    }
} else {
    Write-Error-Custom "roblox-auto-importer.js não encontrado"
}

# ── Fase 3: Abrir Roblox Studio (opcional) ─────────────────────────────────────

if ($OpenRoblox) {
    Write-Step "Abrindo Roblox Studio..."
    
    $robloxPath = "${env:LOCALAPPDATA}\Roblox\Versions\roblox-player.exe"
    if (Test-Path $robloxPath) {
        Start-Process $robloxPath
        Write-Success "Roblox Studio aberto!"
    } else {
        Write-Error-Custom "Roblox Studio não encontrado em: $robloxPath"
    }
}

# ── Fase 4: Gerar Guia (opcional) ──────────────────────────────────────────────

if ($GenerateGuide) {
    Write-Step "Gerando guia de importação..."
    
    $guideContent = @"
# Guia de Importação — $ScreenName
# Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Arquivos Gerados
- Assets PNG: $assetsDir
- Manifest: $assetsDir/_manifest.json
- Controller: $assetsDir/_controller.lua

## Passos no Roblox Studio

1. Abra o Roblox Studio
2. Vá em View > Explorer
3. Navegue até ReplicatedStorage > UIAssets > $ScreenName
4. Arraste os arquivos PNG da pasta acima
5. Aguarde o upload completar
6. No Output, execute:

   local AM = require(game.ReplicatedStorage.UIBridge.AssetManager)
   AM.LinkAssets("$ScreenName")

7. Teste:
   
   local Menu = require(game.ReplicatedStorage.UIAssets.$ScreenName._controller)
   Menu.new():Build()

---
Gerado por FigmaPS2Roblox v3.0.0
"@
    
    $guidePath = Join-Path $assetsDir "$ScreenName_import_guide.txt"
    $guideContent | Out-File -FilePath $guidePath -Encoding UTF8
    Write-Success "Guia gerado: $guidePath"
}

# ── Resumo Final ────────────────────────────────────────────────────────────────

Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                     RESUMO FINAL                          ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host @"

✅ PROCESSAMENTO CONCLUÍDO!

📂 Assets processados:
   • Localização: $assetsDir
   • Tela: $ScreenName
   • Método: $Method

📋 Próximos passos:
   1. Abra o Roblox Studio
   2. Verifique se os arquivos foram copiados
   3. Execute LinkAssets() no Output
   4. Teste a UI com Build()

🔗 Comandos úteis:
   node roblox-auto-importer.js $assetsDir --method $Method --project "$ProjectPath"
   node roblox-ui-manage.js list-assets
   node roblox-import-helper.js $assetsDir --screen $ScreenName

"@ -ForegroundColor White
