# 🎮 Sistema Completo FigmaPS2Roblox — Documentação Final

## 📋 Visão Geral

Sistema completo para converter designs do Photoshop/Figma em UIs funcionais no Roblox, com automação de importação e suporte a IA.

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│  FASE 1: DESIGN (Photoshop)                                             │
│                                                                         │
│  Designer cria interface no Photoshop                                   │
│         │                                                               │
│         ▼                                                               │
│  Plugin FigmaPS2Roblox (CEP)                                            │
│  • Detecta artboards/pranchetas                                         │
│  • Exporta PNGs por camada                                              │
│  • Gera _manifest.json                                                  │
│  • Gera _controller.lua                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FASE 2: PROCESSAMENTO (Node.js)                                        │
│                                                                         │
│  node psd-to-roblox-ai.js design.psd --screen MainMenu                  │
│         │                                                               │
│         ▼                                                               │
│  Gera:                                                                  │
│  ✅ design_uds.json (estrutura completa)                                │
│  ✅ ai_specification.json (análise da IA)                               │
│  ✅ _controller.lua (código pronto)                                     │
│  ✅ *.png (assets processados)                                          │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FASE 3: IMPORTAÇÃO (Roblox Studio)                                     │
│                                                                         │
│  Plugin RobloxUIImporter.lua                                            │
│         │                                                               │
│         ▼                                                               │
│  1. Lê _manifest.json                                                   │
│  2. Cria estrutura de pastas                                            │
│     ReplicatedStorage/UIAssets/MainMenu/                                │
│  3. Guia usuário para upload manual dos PNGs                            │
│  4. Atualiza asset IDs no manifest                                      │
│  5. Gera controller Lua automatizado                                    │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FASE 4: USO NO JOGO                                                    │
│                                                                         │
│  local UI = require(game.ReplicatedStorage.UIAssets.MainMenu._controller)
│  UI.new():Build()                                                       │
│                                                                         │
│  ✅ UI aparece no jogo!                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Arquivos

### Plugin Photoshop (CEP)
```
photoshop-plugin/
├── index.html              # Interface do painel
├── hostscript.jsx          # Backend ExtendScript
├── cep.js                  # Bridge CEP
├── CSXS/
│   ├── manifest.xml        # Manifesto da extensão
│   └── version.xml
├── META-INF/
│   ├── mimetype
│   └── signatures.xml
├── install-cep-panel.js    # Instalador
├── troubleshoot.ps1        # Diagnóstico
└── fix-plugin.ps1          # Reparos
```

### Módulo Roblox
```
uibridge/
├── UIBridge.luau           # Motor principal
├── UIGenerator.luau        # Construtor de UI
├── AssetManager.luau       # Gerenciador de assets
├── ImportManager.luau      # Importação
├── RobloxUIImporter.plugin.lua    # Plugin Roblox (leitor de manifest)
└── RobloxUIAutoImport.plugin.lua  # Plugin alternativo
```

### Scripts Node.js
```
├── psd-to-roblox-ai.js     # Pipeline principal
├── universal-design-schema.js # Schema UDS
├── psd-intelligence-scanner.js # Scanner PSD
├── ai-backend-connector.js # Conector IA
├── asset-bypass.js         # Evasão de moderação
├── roblox-auto-importer.js # Importação automática
└── roblox-ui-manage.js     # Gerenciamento
```

---

## 🚀 Como Usar — Passo a Passo

### 1️⃣ Preparar Ambiente

```powershell
# Verificar instalações
node --version          # Deve ser v18+
npm list sharp          # Deve estar instalado

# Instalar dependências (se necessário)
cd C:\Users\devel\.config\opencode\skills\roblox-ui-recognition
npm install
```

### 2️⃣ No Photoshop

```
1. Abra seu PSD
2. Window > Extensions > FigmaPS2Roblox
3. Na aba Camadas, selecione a prancheta desejada
4. Configure na aba Exportar:
   - Nome da tela: MainMenu
   - Pasta de saída: C:\output\
   - Opções: todas marcadas
5. Clique "Exportar para Roblox"
```

**Resultado:** Pasta `C:\output\MainMenu\` com:
- `bg_main_xxx.png`
- `btn_play_xxx.png`
- `_manifest.json`
- `_controller.lua`

### 3️⃣ No Roblox Studio

```
1. View > Plugins > Plugin Editor
2. Cole o conteúdo de:
   uibridge/RobloxUIImporter.plugin.lua
3. Salve como "RobloxUIImporter.lua"
4. Execute o plugin
```

**No plugin:**
```
1. Pasta de Assets: C:\output\MainMenu
2. Nome da Tela: MainMenu
3. Clique "🔍 Escanear Pasta"
4. Clique "📥 Importar Assets"
5. Siga instruções para upload manual
6. Clique "🏗️ Construir UI"
```

### 4️⃣ No Jogo

```lua
-- No seu Bootstrap ou ScreenController
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local MainMenu = require(ReplicatedStorage:WaitForChild("UIAssets"):
    WaitForChild("MainMenu"):
    WaitForChild("_controller"))

local ui = MainMenu.new()
ui:Build(Players.LocalPlayer:WaitForChild("PlayerGui"))
```

---

## 🎯 Funcionalidades

### Plugin Photoshop
- ✅ Detecção de artboards/pranchetas
- ✅ Filtro por prancheta selecionada
- ✅ Classificação automática de camadas
- ✅ Exportação com hash único anti-reuploader
- ✅ Geração de controller Lua
- ✅ Modo bypass (evasão de moderação)

### Plugin Roblox
- ✅ Leitura automática do manifest
- ✅ Criação de estrutura de pastas
- ✅ Guia passo a passo para importação
- ✅ Geração de controller Lua
- ✅ Atualização de asset IDs

### Scripts Node.js
- ✅ Pipeline completo PSD → Roblox
- ✅ Análise com IA (OpenAI/Claude)
- ✅ Schema universal (UDS)
- ✅ Técnicas de bypass
- ✅ Automação de importação

---

## 📊 Comandos Rápidos

```powershell
# Pipeline completo
node psd-to-roblox-ai.js menu.psd --screen MainMenu --output ./output/

# Apenas escanear
node psd-to-roblox-ai.js menu.psd --scan-only

# Com IA real
node psd-to-roblox-ai.js menu.psd --screen MainMenu --api-key sk-...

# Importação automática
node roblox-auto-importer.js ./output --method copy --project ./meu_projeto

# Troubleshooting
.\troubleshoot.ps1 --fix
```

---

## 🔧 Troubleshooting

| Problema | Solução |
|----------|---------|
| Plugin Photoshop desconectado | Execute `.\troubleshoot.ps1 --fix` |
| Assets não aparecem | Aguarde upload completar no Roblox |
| Erro de script | Verifique se UIBridge está em ReplicatedStorage |
| Posições erradas | Verifique canvasWidth/Height no manifest |
| IA não responde | Verifique API Key e conexão |

---

## 📝 Notas Importantes

⚠️ **Limitação do Roblox:** Upload de assets deve ser feito manualmente (arrastar para o Explorer). O plugin automatiza toda a estrutura e código, mas o upload em si requer interação do usuário.

✅ **Automatizado:**
- Leitura do manifest
- Criação de pastas
- Geração de código
- Mapeamento de assets

❌ **Manual:**
- Upload dos PNGs (limitação da plataforma)

---

## 🎓 Glossário

| Termo | Definição |
|-------|-----------|
| **Artboard** | Prancheta no Photoshop (equivalente a Frame no Figma) |
| **UDS** | Universal Design Schema — formato padronizado |
| **Manifest** | Arquivo JSON que descreve a UI |
| **Asset ID** | Identificador único do Roblox (rbxassetid://123) |
| **Bypass** | Técnicas para evitar detecção de assets |

---

**Versão:** 3.0.0
**Data:** 2026-09-04
**Autor:** FigmaPS2Roblox System
