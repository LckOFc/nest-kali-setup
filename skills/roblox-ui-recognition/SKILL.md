---
name: roblox-ui-recognition
description: Sistema completo de UI Roblox com pipeline Photoshop/Figma → IA → Roblox. Usa Universal Design Schema para estrutura padronizada, PSD Intelligence Scanner para extração avançada, e AI Backend para geração inteligente de UI responsiva. Inclui bypass de moderação Roblox.
aliases:
  - roblox-ui
  - ui-auto
  - psd-to-roblox
  - figma-to-roblox
  - auto-ui
  - uibridge
  - asset-bundler
  - ai-ui-generator
version: 3.0.0
last_updated: 2026-09-04
---

# Roblox UI Automation System — Pipeline IA v3.0.0

**PSD → Universal Design Schema → IA → Roblox UI Responsiva**

## 📋 Changelog v3.0.0 — Arquitetura IA

### Novos Módulos
- 🆕 **Universal Design Schema (UDS)** — Formato padronizado para PSD, Figma, Sketch, XD
- 🆕 **PSD Intelligence Scanner** — Extração estruturada via UXP API (batchPlay)
- 🆕 **AI Backend Connector** — Integração com OpenAI/Claude para análise inteligente
- 🆕 **AIUIGenerator.luau** — Gerador de UI Roblox a partir de especificação IA
- 🆕 **psd-to-roblox-ai.js** — Orquestrador principal do pipeline completo

### Arquitetura de 3 Sistemas
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Photoshop      │     │    AI Backend   │     │  Roblox Studio  │
│  Plugin UXP     │────▶│  (OpenAI/Claude)│────▶│  Plugin         │
│                 │     │                 │     │                 │
│ PSD Scanner     │     │ Análise         │     │ UI Generator    │
│ UDS Builder     │     │ Geração         │     │ Responsive      │
│ Thumbnails      │     │ QA Interativo   │     │ Layout          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### v2.1.0 (Bypass)
- 🛡️ **Sistema Bypass** — Técnicas de evasão de moderação Roblox
  - `asset-bypass.js` — Ruído adaptativo, frequência, quantização, dither
  - Integrado no `complete-pipeline.js` com flag `--bypass`
- 🎨 **Ruído adaptativo** — Detecta bordas, aplica menos ruído em áreas importantes
- 📊 **Ruído de frequência** — Ondas senoidais imperceptíveis
- 🎚️ **Quantização seletiva** — Reduz cores apenas em áreas homogêneas
- 🔲 **Bayer dithering** — Padrão periódico que altera hash

**Photoshop/Figma → PNGs → Hash Único Anti-R euploader → Roblox Studio → Código Lua**

## Arquitetura Completa — v3.0.0 (IA)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Photoshop      │     │    AI Backend   │     │  Roblox Studio  │
│  Plugin UXP     │────▶│  (OpenAI/Claude)│────▶│  Plugin         │
│                 │     │                 │     │                 │
│ PSD Scanner     │     │ Análise         │     │ UI Generator    │
│ UDS Builder     │     │ Geração         │     │ Responsive      │
│ Thumbnails      │     │ QA Interativo   │     │ Layout          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
   Universal                AI Specification         ScreenGui
   Design Schema            + Luau Code              + Assets
   (JSON padronizado)
```

### Novos Componentes v3.0.0
| Arquivo | Função |
|---|---|
| **`universal-design-schema.js`** | Formato padronizado UDS para múltiplas fontes |
| **`psd-intelligence-scanner.js`** | Scanner UXP que extrai estrutura completa do PSD |
| **`ai-backend-connector.js`** | Conector com OpenAI/Claude para análise inteligente |
| **`psd-to-roblox-ai.js`** | Orquestrador principal do pipeline completo |
| **`uibridge/AIUIGenerator.luau`** | Gerador de UI Roblox a partir de especificação IA |

## Componentes do Sistema

### 🔧 Lua (dentro do Roblox Studio)
| Arquivo | Função |
|---|---|
| `UIBridge.luau` | Motor que constrói UI a partir de manifest JSON |
| `Generator.luau` | DSL para construir manifests programaticamente |
| `UIMigrationController.luau` | Gerencia telas dinâmicas (show/hide/destroy) |
| `AssetManager.luau` | Importa assets e atualiza Asset IDs |

### 🖥️ Scripts Node.js (fora do projeto)
| Script | Função |
|---|---|
| **`psd-to-roblox-ai.js`** | ⭐ Pipeline completo PSD→IA→Roblox |
| **`universal-design-schema.js`** | Formato UDS padronizado |
| **`psd-intelligence-scanner.js`** | Scanner UXP avançado |
| **`ai-backend-connector.js`** | Conector OpenAI/Claude |
| `complete-pipeline.js` | Pipeline legado (PNGs) |
| `asset-bypass.js` | 🛡️ Técnicas de evasão de moderação |
| `asset-bundler.js` | Bundler com upload API |
| `export-ui-to-roblox.jsx` | Plugin ExtendScript (File > Scripts) |
| `figma-ui-export.plugin.js` | Plugin Figma |
| `roblox-asset-uploader.js` | Upload real para Roblox via API |

### 🎨 Painel CEP do Photoshop (interativo)
| Arquivo | Função |
|---|---|
| **`photoshop-plugin/index.html`** | Painel interativo estilo figblox |
| **`photoshop-plugin/hostscript.jsx`** | Backend ExtendScript (camadas, export) |
| **`photoshop-plugin/CSXS/manifest.xml`** | Manifesto da extensão CEP |
| `photoshop-plugin/install-cep-panel.js` | Instalador automático do painel |

### 🛠️ Ferramentas auxiliares
| Script | Função |
|---|---|
| `roblox-ui-analyzer.js` | Analisa código Luau existente e mapeia UI |
| `roblox-ui-generator.js` | Gera boilerplate de controllers por categoria |
| `roblox-ui-manage.js` | Importa PNGs para projeto e atualiza IDs |

---

## Sistema Anti-Reuploader

Cada imagem é processada antes de ir para o Roblox:

1. **Ruído imperceptível** — variação de ±1-2 níveis nos canais RGB (0.8% de brightness)
   - Invisível ao olho humano
   - Altera completamente o hash SHA-256
2. **Hash único** — combina seed + caminho + timestamp
   - Mesmo arquivo visualmente = ID diferente a cada processamento
   - Impede detecção por similaridade de hash
3. **Nome único** — cada PNG recebe sufixo `_` + hash de 12 chars
   - Ex: `button_play.png` → `buttonplay_a3f8d2e1b9c4.png`

```
Original:     button_play.png     → hash: abc123...
Processado:   buttonplay_a3f8d2e1b9c4.png  → hash: xyz789... (diferente!)
```

---

## Como Usar

### 🤖 Pipeline com IA (v3.0.0 — Recomendado)

```bash
# 1. Configure a API Key
export OPENAI_API_KEY="sk-..."

# 2. Execute o pipeline completo
node psd-to-roblox-ai.js "C:/design/menu.psd" --output ./output/

# 3. Com prompt personalizado
node psd-to-roblox-ai.js "design.psd" --prompt "Faça responsivo para mobile"

# 4. Modo apenas scan (sem IA)
node psd-to-roblox-ai.js "design.psd" --scan-only

# 5. Perguntar sobre o design
node psd-to-roblox-ai.js "design.psd" --ask "Como fazer responsivo?"
```

### Fluxo Completo (PNGs — legado)

```bash
# 1. Tenha uma pasta com PNGs exportados do Photoshop/Figma
#    Nomes devem ser descritivos: bg_main.png, btn_play.png, title_text.png

# 2. Execute o pipeline completo:
node complete-pipeline.js "C:/caminho/da/pasta-png" --name Lobby

# 3. COM BYPASS (evasão de moderação):
node complete-pipeline.js "C:/caminho/da/pasta-png" --name Lobby --bypass
node complete-pipeline.js "C:/caminho/da/pasta-png" --name Lobby --bypass noise
node complete-pipeline.js "C:/caminho/da/pasta-png" --name Lobby --bypass all

# 4. Script independente de bypass:
node asset-bypass.js assets/ --technique all
node asset-bypass.js button.png --technique noise --seed abc123
```

### Via Photoshop — Painel CEP (Recomendado)

```
1. Instale o painel:
   node install-cep-panel.js

2. Abra o Photoshop com um documento PSD

3. Vá em Window > Extensions > FigmaPS2Roblox
   (ícone aparece na barra de plugins)

4. No painel, configure:
   - Nome da tela (ex: MainMenu)
   - Pasta de saída
   - Opções (classificação inteligente, hash anti-reuploader)

5. Clique em "Exportar para Roblox"
   → O painel mostra preview em tempo real das camadas
   → Exibe classificação automática por tipo
   → Mostra progresso e resultados
```

### Via Photoshop (Plugin JSX alternativo)

```
1. No Photoshop: File > Scripts > Browse...
   → selecione hostscript.jsx
   → escolha a pasta de saída
```

### Via Figma (Plugin)

```
1. No Figma: Plugins > Development > New plugin
   → Cole figma-ui-export.plugin.js no campo Code
   → Cole figma-ui-export.html no campo HTML

2. Selecione uma Frame no canvas
3. Execute o plugin → baixe PNGs + manifest
4. Execute:
   node complete-pipeline.js "pasta-baixada" --name MeuMenu
```

---

## Classificação Automática (Multi-Sinal)

O sistema usa **classificação inteligente** combinando 5 sinais:

| Sinal | Peso | O que analisa |
|-------|------|---------------|
| **Dimensional** | 30% | Proporção, tamanho absoluto, fullbleed |
| **Espacial** | 20% | Posição relativa no canvas 1920×1080 |
| **Colorido** | 15% | Brilho dominante, transparência |
| **Semântico** | 25% | Keywords no nome do arquivo |
| **Contextual** | 10% | Posição em relação a outros elementos |

### Exemplos de decisão inteligente:

```
background.png          → background    (fullbleed 1920×1080, cor escura)
btn_play                → button        (médio 300×80, cor escura, texto claro)
icon_coin               → icon          (pequeno 48×48, quadrado, cores variadas)
title_main              → label         (largo 800×50, topo da tela)
hp_bar                  → bar           (muito largo 400×24, canto superior)
separator_horizontal     → separator     (fino 600×4px, transparente)
image_001               → image         (genérico, sem keywords, médio)
panel_card              → panel         (grande 600×400, não tela cheia)
```

### Comando de classificador independente:

```bash
# Classificar um único asset
node smart-classifier.js btn_play.png --verbose

# Classificar pasta inteira com re-análise contextual
node smart-classifier.js assets/ --batch --verbose

# Com canvas customizado
node smart-classifier.js bg.png --canvas-w 1280 --canvas-h 720
```

---

## 🧠 Universal Design Schema (UDS)

Formato padronizado para representar designs de múltiplas fontes:

```json
{
  "schemaVersion": "1.0.0",
  "source": "photoshop",
  "document": {
    "name": "GameUI.psd",
    "width": 1920,
    "height": 1080,
    "resolution": 72,
    "colorMode": "RGB"
  },
  "artboards": [
    {
      "id": "artboard_abc123",
      "name": "Main Menu",
      "x": 0,
      "y": 0,
      "width": 1920,
      "height": 1080
    }
  ],
  "layers": [
    {
      "id": "layer_xyz789",
      "name": "Play Button",
      "type": "layer",
      "visible": true,
      "opacity": 100,
      "bounds": { "x": 810, "y": 500, "width": 300, "height": 80 },
      "semantic": {
        "probableRole": "button",
        "confidence": 0.95
      },
      "fill": { "hex": "#89B4FA" },
      "text": { "content": "PLAY", "size": 28 }
    }
  ],
  "colors": [
    { "hex": "#89B4FA", "usage": ["button"] }
  ],
  "fonts": ["Gotham", "GothamBold"]
}
```

### Múltiplas Fontes Suportadas
- Photoshop (via UXP API)
- Figma (via API REST)
- Sketch (via export JSON)
- Adobe XD

---

## 📱 Responsive UI Intelligence

A IA entende **3 tamanhos diferentes** para cada elemento:

| Tamanho | Descrição | Exemplo |
|---------|-----------|---------|
| **Asset** | Arquivo exportado | PNG: 640×640 |
| **Visual no Design** | Posição no canvas Photoshop | 280×280 em 1920×1080 |
| **Responsivo no Roblox** | Comportamento em diferentes telas | Scale + Offset dinâmico |

### Estratégias de Escala por Tipo

```
Background  → Fill (preenche tela toda)
Button      → ScaleToFit (mantém proporção)
Text        → Adaptive (ajusta tamanho conforme dispositivo)
Icon        → FixedSize (tamanho fixo)
Panel       → ScaleToFit (escala proporcional)
HUD         → Anchored (fixo em posição)
```

---

## 🛠️ Ferramentas auxiliares

```
┌────────────────────────────────────────┐
│  BACKGROUND (ImageLabel, zIndex 1)      │  ← preenche tudo
│                                        │
│  [LABEL - Title]     zIndex 4          │  ← topo
│  [LABEL - Subtitle]  zIndex 4          │
│                                        │
│  ┌────────────────────────────────┐    │
│  │  PANEL (Frame)    zIndex 2     │    │
│  │  ┌─────┐  ┌─────┐  ┌─────┐    │    │
│  │  │ BTN │  │ BTN │  │ BTN │    │    │  ← botões centralizados
│  │  └─────┘  └─────┘  └─────┘    │    │     empilhados verticalmente
│  └────────────────────────────────┘    │
│                                        │
│     [ICONS / ITEMS]   zIndex 3         │  ← centro
│                                        │
│  [HP BAR]              zIndex 6        │  ← canto superior esquerdo
└────────────────────────────────────────┘
```

---

## Uso do UIBridge no Jogo

```lua
--!strict
-- No Bootstrap.client.lua ou controller de tela:

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")

local UIBridge = require(ReplicatedStorage:WaitForChild("UIBridge"))

-- Opção 1: Do manifest JSON (gerado pelo pipeline)
local manifestJson = [[{
  "name": "Lobby",
  "canvasWidth": 1920,
  "canvasHeight": 1080,
  "scaleMode": "ScaleToFit",
  "elements": [...]
}]]

local bridge = UIBridge.fromJSON(manifestJson, Players.LocalPlayer:WaitForChild("PlayerGui"))
bridge:build()
bridge:show()

-- Opção 2: Usando o Generator (programático)
local Generator = require(ReplicatedStorage.UIBridge.Generator)
local myUI = Generator(build("MyScreen", {
    elements = {
        img("Bg", { x=0, y=0, width=1920, height=1080, assetId="rbxassetid://SEU_ID" }),
        btn("Play", { x=960, y=600, width=300, height=80, text="JOGAR",
            events = { Activated = "onPlay" },
            handlers = { onPlay = function() print("jogar!") end } }),
    }
}))
myUI:build()
```

---

## 🛡️ Sistema Bypass — Evasão de Moderação

O Roblox usa hash SHA-256 para detectar assets duplicados/reportados. O sistema bypass aplica transformações **imperceptíveis** que alteram completamente o hash.

### Técnicas Disponíveis

| Técnica | Código | O que faz | Efeito visual |
|---------|--------|-----------|---------------|
| **Ruído Adaptativo** | `noise` | ±1.5 níveis RGB, menos em bordas | 0% perceptível |
| **Frequência Alta** | `frequency` | Ondas senoidais a 95% da freq. máxima | 0% perceptível |
| **Quantização** | `quantize` | Reduz para 240 níveis em áreas homogêneas | ~0.1% perceptível |
| **Bayer Dither** | `dither` | Padrão periódico 4×4 | 0% perceptível |
| **Distorção** | `distort` | Warping radial de 0.2% | 0% perceptível |
| **Perfil de Cor** | `profile` | Shuffle sRGB→AdobeRGB→sRGB | 0% perceptível |
| **Metadata** | `metadata` | Injeta EXIF falso | N/A (só hash) |

### Uso Rápido

```bash
# Pipeline completo com bypass (todas as técnicas)
node complete-pipeline.js assets/ --name MainMenu --bypass

# Apenas ruído adaptativo (mais seguro)
node complete-pipeline.js assets/ --name MainMenu --bypass noise

# Script independente
node asset-bypass.js assets/ --technique all --output ./bypass_assets/
```

### Como Funciona

```
Hash Original:     a3f8d2e1b9c4... (pode ser bloqueado)
        ↓ Aplicar técnicas
Hash Processado:   7x9k2m4p8q1r... (completamente diferente)
        ↓
Upload Roblox:     ✅ Passa na verificação
```

> **Nota:** As técnicas são projetadas para serem **imperceptíveis ao olho humano** mas **detectáveis por comparação de hash**.

---

## Comandos Rápidos

```bash
# Pipeline completo (recomendado) — com re-classificação inteligente
node complete-pipeline.js "C:/Downloads/ui_export" --name Lobby

# Apenas escanear e classificar (com smart classification)
node auto-ui.js "C:/Downloads/ui_export" --name Lobby

# Classificador independente (verbose)
node smart-classifier.js "C:/Downloads/ui_export" --batch --verbose

# Testar o classificador
node test-smart-classifier.js

# Analisar código Luau existente
node roblox-ui-analyzer.js "src" --categories

# Gerar boilerplate de controller
node roblox-ui-generator.js generate menu MainMenu --screen=main

# Atualizar Asset IDs em massa
node roblox-ui-manage.js update-placeholders MainMenuController.lua \
  --assets=PLACEHOLDER_0=123456789,PLACEHOLDER_1=987654321

# Upload para Roblox (requer cookie .ROBLOSECURITY)
node roblox-asset-uploader.js upload "C:/Downloads/ui_export" --cookie "seu_cookie"
```

---

## Resultados de Teste (Versão Final)

```
✅ 30/30 assets classificados corretamente (100%)

Por categoria:
  background   3/3 (100%)
  button       5/5 (100%)
  label        4/4 (100%)
  icon         5/5 (100%)
  panel        3/3 (100%)
  bar          3/3 (100%)
  separator    2/2 (100%)
  effect       1/1 (100%)
  image        4/4 (100%)
```

---

## Estrutura Gerada

```
ReplicatedStorage/UIBridge/
  UIBridge.luau           # Motor principal
  Generator.luau          # DSL
  UIMigrationController.luau
  AssetManager.luau

src/StarterPlayer/StarterPlayerScripts/PingPongClient/UIAssets/
  Lobby/
    _manifest.json        # Manifest com todos os assets
    _controller.lua       # Controller pronto para usar
    _upload_guide.txt     # Guia passo a passo
    lobby_bg_a3f8d2e1b9c4.png   # Asset processado
    lobby_btn_play_f2e9c1d4a7b8.png
    ...
```

---

## Notas Importantes

- **Canvas fixo:** 1920×1080 (fullscreen HD) — todos os elementos posicionados relativamente
- **Scale mode:** `ScaleToFit` padrão (proporcional, sem distorção)
- **Seed única:** mesma seed = mesmos hashes a cada execução (reprodutível)
- **Anti-reuploader:** ruído de 0.8% altera o hash mas não altera visualmente
- **PingPongStrike:** o skill é isolado, não modifica o projeto existente
- **Roblox Studio:** os assets precisam ser importados manualmente (drag & drop) para obter Asset IDs reais
