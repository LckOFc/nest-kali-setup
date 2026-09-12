# Guia Completo de Importação para Roblox Studio

## 📁 Estrutura de Pastas no Roblox Studio

```
SeuProjetoRoblox/
├── default.project.json
├── src/
│   └── StarterPlayer/
│       └── StarterPlayerScripts/
│           ├── UIBridge/                    # Motor da UI
│           │   ├── UIBridge.luau
│           │   ├── Generator.luau
│           │   ├── AssetManager.luau
│           │   ├── ImportManager.luau
│           │   └── AssetImporter.plugin.lua
│           │
│           └── UIAssets/                    # Assets importados
│               ├── MainMenu/
│               │   ├── _manifest.json
│               │   ├── _controller.lua
│               │   ├── bg_main_xxx.png
│               │   ├── btn_play_xxx.png
│               │   └── _upload_guide.txt
│               └── Shop/
│                   └── ...
│
└── tests/
```

---

## 🚀 Passo a Passo Completo

### 1️⃣ Preparar Projeto Roblox

```bash
# Criar estrutura de pastas no projeto
mkdir -p src/StarterPlayer/StarterPlayerScripts/UIBridge
mkdir -p src/StarterPlayer/StarterPlayerScripts/UIAssets/MainMenu
```

### 2️⃣ Copiar Arquivos do UIBridge

Copie os arquivos Luau para a pasta do projeto:
- `UIBridge.luau`
- `Generator.luau`
- `AssetManager.luau`
- `ImportManager.luau`

### 3️⃣ Executar Pipeline PSD → IA

```powershell
cd C:\Users\devel\.config\opencode\skills\roblox-ui-recognition

# Com IA (requer API Key)
node psd-to-roblox-ai.js "C:\design\menu.psd" --output ./output/ --screen MainMenu

# Modo simulado (teste)
node psd-to-roblox-ai.js "C:\design\menu.psd" --scan-only
```

### 4️⃣ Copiar Assets para Projeto

```powershell
# Copiar todos os arquivos gerados
Copy-Item output/*.png -Destination "src/StarterPlayer/StarterPlayerScripts/UIAssets/MainMenu/"
Copy-Item output/_manifest.json -Destination "src/StarterPlayer/StarterPlayerScripts/UIAssets/MainMenu/"
Copy-Item output/_controller.lua -Destination "src/StarterPlayer/StarterPlayerScripts/UIAssets/MainMenu/"
```

### 5️⃣ Importar Assets no Roblox Studio

**Método Manual (Recomendado):**

1. Abra o Roblox Studio
2. Vá em **View > Explorer**
3. Navegue até **ReplicatedStorage > UIAssets > MainMenu**
4. Arraste os arquivos PNG da pasta do projeto para o Explorer
5. Aguarde o upload completar (aparece barra de progresso)

**Método via Plugin:**

1. Abra o Roblox Studio
2. Vá em **View > Plugins > Plugin Editor**
3. Cole o código do `AssetImporter.plugin.lua`
4. Salve e execute
5. Use o painel para importar

### 6️⃣ Linkar Assets ao Manifest

No **Output** do Roblox Studio:

```lua
local AssetManager = require(game.ReplicatedStorage.UIBridge.AssetManager)
local mapping = AssetManager.LinkAssets("MainMenu")
print("Assets linkados:", mapping)
```

### 7️⃣ Atualizar Manifest

```lua
-- O manifest é atualizado automaticamente pelo AssetManager
-- Verifique em: ReplicatedStorage > UIAssets > MainMenu > _manifest.json
```

### 8️⃣ Testar a UI

```lua
local GeneratedUI = require(game.ReplicatedStorage.UIAssets.MainMenu._controller)
local ui = GeneratedUI.new()
ui:Build()
```

---

## 📋 Comandos Rápidos

```powershell
# Pipeline completo com IA
node psd-to-roblox-ai.js design.psd --screen MainMenu --output ./output/

# Apenas escanear (modo simulado)
node psd-to-roblox-ai.js design.psd --scan-only

# Gerar guia de importação
node roblox-import-helper.js ./output/ --screen MainMenu

# Listar assets no projeto
node roblox-ui-manage.js list-assets

# Atualizar placeholders manualmente
node roblox-ui-manage.js update-placeholders _controller.lua --assets=layer1=123456789,layer2=987654321
```

---

## 🎯 Fluxo de Trabalho Completo

```
┌─────────────────────────────────────────────────────────────────┐
│  FASE 1: DESIGN (Photoshop)                                     │
│                                                                 │
│  1. Designer cria interface no Photoshop                        │
│  2. Salva como .psd                                             │
│  3. Exporta layers como PNGs (manual ou plugin)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASE 2: PROCESSAMENTO (Node.js)                                │
│                                                                 │
│  node psd-to-roblox-ai.js design.psd --screen MainMenu          │
│                                                                 │
│  Gera:                                                          │
│  ✅ design_uds.json (estrutura completa)                        │
│  ✅ ai_specification.json (especificação IA)                    │
│  ✅ _controller.lua (código pronto)                             │
│  ✅ *.png (assets processados)                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASE 3: IMPORTAÇÃO (Roblox Studio)                             │
│                                                                 │
│  1. Copiar assets para ReplicatedStorage/UIAssets/MainMenu/    │
│  2. Arrastar PNGs para o Explorer                               │
│  3. Aguardar upload                                             │
│  4. Executar LinkAssets()                                       │
│  5. Verificar manifest atualizado                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASE 4: TESTE (Roblox Studio)                                  │
│                                                                 │
│  local UI = require(game.ReplicatedStorage.UIAssets.MainMenu._controller)
│  local ui = UI.new()
│  ui:Build()                                                     │
│                                                                 │
│  ✅ Verificar se UI aparece corretamente                        │
│  ✅ Testar em diferentes resoluções                             │
│  ✅ Ajustar se necessário                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| **Asset não aparece** | Upload incompleto | Aguarde a barra de progresso completar |
| **Erro de script** | UIBridge não encontrado | Verifique se está em `ReplicatedStorage.UIBridge` |
| **Posições erradas** | Canvas dimensions incorretas | Verifique `canvasWidth`/`canvasHeight` no manifest |
| **Imagens pixeladas** | Resolução muito alta | Redimensione para máximo 2048×2048 |
| **Textos sumindo** | Fonte não encontrada | Use Gotham, GothamBold, ou Arial |
| **Botões não clicáveis** | ZIndex incorreto | Ajuste zIndex nos elementos interativos |

---

## 📊 Estrutura do Manifest

```json
{
  "name": "MainMenu",
  "canvasWidth": 1920,
  "canvasHeight": 1080,
  "scaleMode": "ScaleToFit",
  "assets": [
    {
      "uniqueId": "abc123def456",
      "filename": "bg_main_abc123def456.png",
      "type": "background",
      "name": "bg_main",
      "x": 0,
      "y": 0,
      "width": 1920,
      "height": 1080,
      "assetId": "rbxassetid://123456789"
    }
  ],
  "elements": [...]
}
```

---

## ✅ Checklist de Verificação

- [ ] Pasta `ReplicatedStorage/UIAssets/MainMenu` criada
- [ ] Todos os PNGs importados e com Asset ID
- [ ] `_manifest.json` com IDs atualizados
- [ ] `_controller.lua` funcional
- [ ] UIBridge em `ReplicatedStorage`
- [ ] UI testada em diferentes resoluções

---

Gerado por **FigmaPS2Roblox v3.0.0**
