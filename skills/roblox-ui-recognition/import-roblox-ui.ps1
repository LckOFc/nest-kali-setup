# ============================================================
# Script de Importação Automática — FigmaPS2Roblox v3.0.0
# ============================================================
# Uso: .\import-roblox-ui.ps1 <psd-path> [--screen NomeTela] [--project CaminhoProjeto]
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$PsdPath,
    
    [string]$ScreenName = "Screen",
    
    [string]$ProjectPath = "",
    
    [switch]$SkipPipeline,
    
    [switch]$ShowOnly
)

$ErrorActionPreference = "Stop"

# ── Configurações ─────────────────────────────────────────────────────────────

$ScriptDir = $PSScriptRoot
$SkillDir = "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition"
$OutputDir = Join-Path $SkillDir "output"
$NodeScript = Join-Path $SkillDir "psd-to-roblox-ai.js"

# ── Funções Utilitárias ───────────────────────────────────────────────────────

function Write-Step {
    param([string]$Message)
    Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ️  $Message" -ForegroundColor Blue
}

# ── Verificar Pré-requisitos ──────────────────────────────────────────────────

function Test-Prerequisites {
    Write-Step "Verificando pré-requisitos..."
    
    $errors = @()
    
    # Node.js
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        $errors += "Node.js não instalado"
    } else {
        $version = node --version
        Write-Success "Node.js: $version"
    }
    
    # Sharp
    $sharpCheck = node -e "try { require('sharp'); console.log('ok') } catch(e) { console.log('missing') }" 2>$null
    if ($sharpCheck -eq "ok") {
        Write-Success "Sharp: instalado"
    } else {
        $errors += "Sharp não instalado (execute: npm install sharp)"
    }
    
    # Photoshop
    $psPath = "C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe"
    if (Test-Path $psPath) {
        Write-Success "Photoshop 2024: encontrado"
    } else {
        Write-Warning-Custom "Photoshop não encontrado em C:\Program Files\Adobe\"
    }
    
    # PSD Path
    if (-not (Test-Path $PsdPath)) {
        $errors += "PSD não encontrado: $PsdPath"
    } else {
        Write-Success "PSD encontrado: $PsdPath"
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "`n❌ Erros encontrados:" -ForegroundColor Red
        foreach ($err in $errors) {
            Write-Host "  - $err" -ForegroundColor Red
        }
        exit 1
    }
}

# ── Fase 1: Pipeline ──────────────────────────────────────────────────────────

function Run-Pipeline {
    Write-Step "Fase 1: Processando PSD com IA..."
    
    $args = @($PsdPath, "--screen", $ScreenName, "--output", $OutputDir)
    
    # Adicionar API key se disponível
    $apiToken = $env:OPENAI_API_KEY
    if ($apiToken) {
        $args += "--api-key"
        $args += $apiToken
    }
    
    Write-Info "Executando: node psd-to-roblox-ai.js $($args -join ' ')"
    
    try {
        $output = node $NodeScript @args 2>&1
        Write-Host $output
        Write-Success "Pipeline concluído!"
    } catch {
        Write-Error-Custom "Falha no pipeline: $_"
        exit 1
    }
}

# ── Fase 2: Copiar para Projeto ───────────────────────────────────────────────

function Copy-To-Project {
    param([string]$TargetPath)
    
    Write-Step "Fase 2: Copiando para projeto Roblox..."
    
    if (-not $TargetPath) {
        Write-Warning-Custom "Nenhum caminho de projeto informado."
        Write-Info "Os arquivos foram gerados em: $OutputDir"
        Write-Info "Copie manualmente para seu projeto Roblox."
        return
    }
    
    # Verificar se é projeto Roblox válido
    if (-not (Test-Path (Join-Path $TargetPath "default.project.json"))) {
        Write-Warning-Custom "default.project.json não encontrado em $TargetPath"
        Write-Info "Certifique-se de que o caminho está correto."
        return
    }
    
    $destDir = Join-Path $TargetPath "src/StarterPlayer/StarterPlayerScripts/UIAssets/$ScreenName"
    
    # Criar pasta
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Write-Success "Pasta criada: $destDir"
    
    # Copiar arquivos
    $files = Get-ChildItem (Join-Path $OutputDir "$ScreenName") -ErrorAction SilentlyContinue
    if (-not $files) {
        $files = Get-ChildItem $OutputDir -Filter "*.png" -ErrorAction SilentlyContinue
    }
    
    $copied = 0
    foreach ($file in $files) {
        if ($file.FullName -like "*_$ScreenName*") { continue } # Pular pastas
        try {
            Copy-Item $file.FullName -Destination $destDir -Force
            $copied++
        } catch {
            Write-Warning-Custom "Falha ao copiar: $($file.Name)"
        }
    }
    
    # Copiar manifest e controller
    $manifest = Join-Path $OutputDir "_manifest.json"
    if (Test-Path $manifest) {
        Copy-Item $manifest -Destination $destDir -Force
        Write-Success "Manifest copiado"
    }
    
    $controller = Join-Path $OutputDir "_controller.lua"
    if (Test-Path $controller) {
        Copy-Item $controller -Destination $destDir -Force
        Write-Success "Controller copiado"
    }
    
    Write-Success "$copied arquivos copiados para $destDir"
}

# ── Fase 3: Instruções Roblox Studio ──────────────────────────────────────────

function Show-RobloxInstructions {
    Write-Step "Fase 3: Instruções para Roblox Studio"
    
    $instructions = @"

┌─────────────────────────────────────────────────────────────────┐
│  PASSOS NO ROBLOX STUDIO                                       │
├─────────────────────────────────────────────────────────────────┤

1️⃣  ABRIR PROJETO
   • Abra o Roblox Studio
   • Abra seu projeto: $ProjectPath

2️⃣  VERIFICAR ESTRUTURA
   • View > Explorer (Ctrl+Shift+E)
   • Navegue até: ReplicatedStorage > UIAssets > $ScreenName
   • Se não existir, crie as pastas

3️⃣  IMPORTAR ASSETS
   • Abra a pasta: $OutputDir\$ScreenName
   • Selecione todos os arquivos .png
   • Arraste para a pasta $ScreenName no Explorer do Roblox
   • Aguarde o upload completar

4️⃣  LINKAR ASSETS
   No Output do Roblox Studio, execute:

   local AM = require(game.ReplicatedStorage.UIBridge.AssetManager)
   AM.LinkAssets("$ScreenName")

5️⃣  TESTAR UI
   local Menu = require(game.ReplicatedStorage.UIAssets.$ScreenName._controller)
   local ui = Menu.new()
   ui:Build()

6️⃣  VERIFICAR RESULTADO
   • Pressione Play (F5)
   • Verifique se a UI aparece corretamente
   • Teste em diferentes resoluções

└─────────────────────────────────────────────────────────────────┘
"@
    
    Write-Host $instructions -ForegroundColor White
    
    # Salvar instruções em arquivo
    $guidePath = Join-Path $OutputDir "$ScreenName_roblox_instructions.txt"
    $instructions | Out-File -FilePath $guidePath -Encoding UTF8
    Write-Success "Instruções salvas em: $guidePath"
}

# ── Fase 4: Resumo ────────────────────────────────────────────────────────────

function Show-Summary {
    Write-Step "Resumo"
    
    $files = Get-ChildItem $OutputDir -Recurse -File | Measure-Object -Property Length -Sum
    $pngCount = (Get-ChildItem $OutputDir -Recurse -Filter "*.png" | Measure-Object).Count
    
    Write-Host @"

✅ PROCESSAMENTO CONCLUÍDO!

📂 Arquivos gerados:
   • Local: $OutputDir
   • Total: $($files.Count) arquivos
   • PNGs: $pngCount assets

📋 Próximos passos:
   1. Abra o Roblox Studio
   2. Importe os PNGs manualmente
   3. Execute LinkAssets()
   4. Teste a UI

🔗 Arquivos importantes:
   • _manifest.json - Lista completa dos assets
   • _controller.lua - Código pronto para usar
   • *_instructions.txt - Guia detalhado

"@ -ForegroundColor Green
}

# ── Main ──────────────────────────────────────────────────────────────────────

function Main {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     FigmaPS2Roblox — Importação UI para Roblox v3.0.0    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    
    # Verificar pré-requisitos
    Test-Prerequisites
    
    # Executar pipeline (se não skip)
    if (-not $SkipPipeline) {
        Run-Pipeline
    } else {
        Write-Info "Pipeline pulado (--skip-pipeline)"
    }
    
    # Copiar para projeto
    Copy-To-Project -TargetPath $ProjectPath
    
    # Mostrar instruções
    Show-RobloxInstructions
    
    # Resumo
    Show-Summary
}

# Executar
Main
