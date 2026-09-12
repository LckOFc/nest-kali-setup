# 🎮 Scripts Roblox Studio — FigmaPS2Roblox

## 📁 Estrutura de Arquivos

```
uibridge/
├── UIBridge.luau              # Motor principal (lê manifest e constrói UI)
├── GameUIManager.luau         # Gerenciador de telas (show/hide/destroy)
├── AssetManager.luau          # Gerenciador de assets
├── Bootstrap.client.lua       # Script principal (inicializa UI)
├── QuickTest.lua              # Teste rápido
├── RobloxUIImport.plugin.lua  # Plugin para importar UIs
└── README.md                  # Este arquivo
```

---

## 🚀 Instalação Rápida

### Passo 1: Copiar Arquivos para o Projeto

```powershell
# Copiar módulos para o projeto Roblox
Copy-Item "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\uibridge\*.luau" `
  -Destination "C:\seu_projeto\src\StarterPlayer\StarterPlayerScripts\UIBridge\"

# Copiar Bootstrap
Copy-Item "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\uibridge\Bootstrap.client.lua" `
  -Destination "C:\seu_projeto\src\StarterPlayer\StarterPlayerScripts\"

# Copiar plugin (opcional)
Copy-Item "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\uibridge\RobloxUIImport.plugin.lua" `
  -Destination "C:\seu_projeto\src\StarterPlayer\StarterPlayerScripts\UIBridge\"
```

### Passo 2: Configurar no Roblox Studio

1. Abra seu projeto Roblox
2. Vá em **View > Explorer**
3. Certifique-se que a estrutura está correta:
   ```
   ReplicatedStorage/
   └── UIBridge/
       ├── UIBridge.luau
       ├── GameUIManager.luau
       └── AssetManager.luau
   ```

### Passo 3: Testar

No **Output** do Roblox Studio, execute:

```lua
require(game.ReplicatedStorage.UIBridge.QuickTest)()
```

---

## 📖 Uso do Sistema

### Mostrar uma Tela

```lua
local UIManager = require(game.ReplicatedStorage.UIBridge.GameUIManager)
UIManager:Show("MainMenu")
```

### Esconder uma Tela

```lua
UIManager:Hide("MainMenu")
```

### Destruir uma Tela

```lua
UIManager:Destroy("MainMenu")
```

### Alternar entre Telas

```lua
UIManager:Switch("MainMenu", "GameHUD")
```

---

## 🔧 Workflow Completo

### 1. No Photoshop

```
1. Abra seu PSD
2. Window > Extensions > FigmaPS2Roblox
3. Selecione a prancheta
4. Exporte
```

**Resultado:** Pasta com `_manifest.json` e PNGs

### 2. No Roblox Studio

```
1. View > Plugins > Roblox UI Import
2. Cole o caminho da pasta exportada
3. Clique "Importar UI"
4. Arraste os PNGs para o Explorer
5. Aguarde upload
```

### 3. No Jogo

```lua
-- Bootstrap.client.lua faz tudo automaticamente
-- Ou use manualmente:
local UIManager = require(game.ReplicatedStorage.UIBridge.GameUIManager)
UIManager:Show("MainMenu")
```

---

## 📊 Estrutura de Pastas no Roblox

Após importação, a estrutura será:

```
ReplicatedStorage/
├── UIBridge/                    # Módulos do sistema
│   ├── UIBridge.luau
│   ├── GameUIManager.luau
│   └── AssetManager.luau
│
└── UIAssets/                    # Assets das telas
    └── MainMenu/                # Nome da tela
        ├── Images/              # PNGs importados
        │   ├── bg_main_xxx.png
        │   ├── btn_play_xxx.png
        │   └── ...
        ├── Scripts/             # Controllers
        │   └── _controller.lua
        ├── _asset_mapping.json  # Mapeamento de assets
        └── _manifest_processed.json
```

---

## 🎯 API do GameUIManager

| Método | Descrição |
|--------|-----------|
| `Show(name)` | Exibe uma tela |
| `Hide(name)` | Oculta uma tela |
| `Destroy(name)` | Destrói uma tela |
| `Switch(from, to)` | Alterna entre telas |
| `IsVisible(name)` | Verifica se tela está visível |
| `ListScreens()` | Lista todas as telas |

---

## 🐛 Troubleshooting

### UIBridge não encontrado
```
Certifique-se que os arquivos .luau estão em:
ReplicatedStorage.UIBridge
```

### Tela não aparece
```
1. Verifique se o manifest foi importado
2. Execute o QuickTest no Output
3. Verifique se os assets foram uploadados
```

### Erro de script
```
Verifique se o Bootstrap.client.lua está em:
StarterPlayer.StarterPlayerScripts
```

---

## 📝 Exemplo Completo

```lua
-- No seu script de jogo:
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIManager = require(ReplicatedStorage.UIBridge.GameUIManager)

-- Quando o jogador entrar no jogo
Players.PlayerAdded:Connect(function(player)
    -- Mostrar menu principal
    UIManager:Show("MainMenu")
    
    -- Quando clicar em Play
    local mainScreen = UIManager.screens["MainMenu"]
    if mainScreen then
        local playButton = mainScreen:FindFirstChild("PlayButton")
        if playButton then
            playButton.Activated:Connect(function()
                -- Trocar para tela do jogo
                UIManager:Switch("MainMenu", "GameHUD")
            end)
        end
    end
end)
```

---

**Versão:** 1.0.0  
**Data:** 2026-09-04
