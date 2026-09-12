# 🎮 Guia Passo a Passo — Importação UI Photoshop → Roblox

## 📋 Pré-Requisitos

- [ ] Node.js instalado (v18+)
- [ ] Photoshop instalado
- [ ] Roblox Studio instalado
- [ ] API Key da OpenAI (opcional, para IA real)
- [ ] Projeto Roblox criado

---

## 🚀 FASE 1: Preparar Ambiente

### 1.1 Verificar Instalações

```powershell
# Verificar Node.js
node --version
# Deve mostrar: v18.x.x ou superior

# Verificar dependências
cd C:\Users\devel\.config\opencode\skills\roblox-ui-recognition
npm list sharp
# Deve mostrar: sharp@0.35.4
```

### 1.2 Estrutura do Projeto Roblox

Certifique-se que seu projeto Roblox tem esta estrutura:

```
SeuProjetoRoblox/
├── default.project.json
├── src/
│   └── StarterPlayer/
│       └── StarterPlayerScripts/
│           ├── UIBridge/          ← Copiar arquivos Luau aqui
│           │   ├── UIBridge.luau
│           │   ├── Generator.luau
│           │   ├── AssetManager.luau
│           │   └── ImportManager.luau
│           │
│           └── UIAssets/          ← Assets importados vão aqui
│               └── MainMenu/
│                   ├── _manifest.json
│                   ├── _controller.lua
│                   └── *.png
└── tests/
```

### 1.3 Copiar Arquivos do UIBridge

```powershell
# Copiar motor UI para o projeto
Copy-Item "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\uibridge\*.luau" `
  -Destination "C:\seu_projeto\src\StarterPlayer\StarterPlayerScripts\UIBridge\"
```

---

## 🎨 FASE 2: Preparar Design no Photoshop

### 2.1 Criar/Abir PSD

1. Abra seu design no Photoshop
2. Certifique-se que:
   - Canvas está em **RGB** (não CMYK)
   - Resolução é **72 DPI** (padrão web)
   - Dimensões são múltiplo de 1920×1080 (ou proporção similar)

### 2.2 Nomear Camadas Corretamente

Use nomes descritivos para melhor classificação:

| Tipo | Nomes Recomendados |
|------|-------------------|
| Fundo | `bg_main`, `background`, `base` |
| Botão | `btn_play`, `button_start`, `cta_main` |
| Texto | `title_main`, `label_subtitle`, `text_body` |
| Ícone | `icon_coin`, `img_avatar`, `logo_app` |
| Painel | `panel_card`, `frame_dialog`, `box_content` |
| Barra | `bar_health`, `hp_bar`, `progress_xp` |

### 2.3 Salvar PSD

```
File > Save As > SeuDesign.psd
```

---

## ⚙️ FASE 3: Processar com Node.js

### 3.1 Executar Pipeline

```powershell
cd C:\Users\devel\.config\opencode\skills\roblox-ui-recognition

# Modo teste (sem IA)
node psd-to-roblox-ai.js "C:\caminho\SeuDesign.psd" --scan-only --output ./output/

# Modo completo (com IA)
node psd-to-roblox-ai.js "C:\caminho\SeuDesign.psd" --screen MainMenu --output ./output/ --api-key sk-...
```

### 3.2 Verificar Saída

```powershell
# Listar arquivos gerados
Get-ChildItem output/ -Recurse
```

Deve aparecer:

```
output/
├── design_uds.json          ✅ Estrutura extraída
├── ai_specification.json    ✅ Especificação IA
├── _controller.lua          ✅ Código pronto
├── _upload_guide.txt        ✅ Guia de upload
└── MainMenu/                ✅ Pasta da tela
    ├── bg_main_xxx.png
    ├── btn_play_xxx.png
    └── ...
```

---

## 📁 FASE 4: Copiar para Projeto Roblox

### 4.1 Copiar Assets

```powershell
# Copiar todos os arquivos para o projeto
$projectPath = "C:\seu_projeto"
$screenName = "MainMenu"

# Criar pasta se não existir
New-Item -ItemType Directory -Force -Path "$projectPath\src\StarterPlayer\StarterPlayerScripts\UIAssets\$screenName" | Out-Null

# Copiar assets PNG
Get-ChildItem "output\$screenName\*.png" | ForEach-Object {
    Copy-Item $_.FullName -Destination "$projectPath\src\StarterPlayer\StarterPlayerScripts\UIAssets\$screenName\"
}

# Copiar manifest e controller
Copy-Item "output\$screenName\_manifest.json" -Destination "$projectPath\src\StarterPlayer\StarterPlayerScripts\UIAssets\$screenName\"
Copy-Item "output\_controller.lua" -Destination "$projectPath\src\StarterPlayer\StarterPlayerScripts\UIAssets\$screenName\"
```

### 4.2 Verificar Arquivos

```powershell
Get-ChildItem "$projectPath\src\StarterPlayer\StarterPlayerScripts\UIAssets\$screenName"
```

---

## 🎮 FASE 5: Importar no Roblox Studio

### 5.1 Abrir Projeto

1. Abra o Roblox Studio
2. Abra seu projeto (`SeuProjetoRoblox`)
3. Vá em **View > Explorer** (Ctrl+Shift+E)

### 5.2 Criar Estrutura (se não existir)

No Explorer:
1. Clique direito em **ReplicatedStorage**
2. **Insert Folder** → nomeie como **UIAssets**
3. Clique direito em **UIAssets**
4. **Insert Folder** → nomeie como **MainMenu**

### 5.3 Importar Assets

1. Abra a pasta do projeto no Windows Explorer
2. Navegue até: `src/StarterPlayer/StarterPlayerScripts/UIAssets/MainMenu/`
3. **Selecione todos os arquivos .png**
4. **Arraste para a pasta MainMenu** no Explorer do Roblox Studio
5. Aguarde o upload completar (barra de progresso aparece)

⏱️ **Tempo estimado:** 2-5 minutos por asset

---

## 🔗 FASE 6: Linkar Assets

### 6.1 Executar no Output

No Roblox Studio, abra **Output** (View > Output) e execute:

```lua
-- Carregar AssetManager
local AssetManager = require(game.ReplicatedStorage.UIBridge.AssetManager)

-- Linkar assets da tela MainMenu
local mapping = AssetManager.LinkAssets("MainMenu")

-- Verificar resultado
print("Assets linkados:", #mapping)
for name, id in pairs(mapping) do
    print(string.format("  %s → %s", name, id))
end
```

### 6.2 Verificar Manifest

O `_manifest.json` deve ser atualizado automaticamente. Verifique:

```
ReplicatedStorage > UIAssets > MainMenu > _manifest.json
```

Os campos `assetId` devem estar preenchidos com `rbxassetid://123456789`.

---

## ✅ FASE 7: Testar UI

### 7.1 Criar Teste Rápido

No **Output** do Roblox Studio:

```lua
-- Testar importação da UI
local GeneratedUI = require(game.ReplicatedStorage.UIAssets.MainMenu._controller)

local ui = GeneratedUI.new()
local screenGui = ui:Build()

print("✅ UI criada com sucesso!")
print("📐 ScreenGui:", screenGui.Name)
print("📊 Elementos:", #ui.Elements)
```

### 7.2 Verificar no Jogo

1. Clique em **Play** (ou Press F5)
2. A interface deve aparecer
3. Verifique:
   - Posições corretas
   - Tamanhos proporcionais
   - Cores e textos
   - Botões clicáveis

### 7.3 Ajustes (se necessário)

Se algo estiver errado:

```lua
-- Ver elementos criados
for name, element in pairs(ui.Elements) do
    print(string.format("%s: %dx%d @ %d,%d", 
        name, element.Size.X.Offset, element.Size.Y.Offset,
        element.Position.X.Offset, element.Position.Y.Offset))
end
```

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| Erro "UIBridge não encontrado" | Verifique se arquivos estão em `ReplicatedStorage.UIBridge` |
| Assets não aparecem | Aguarde upload completar no Roblox Studio |
| Posições erradas | Verifique `canvasWidth` e `canvasHeight` no manifest |
| Textos sumindo | Use fontes do Roblox: Gotham, Arial, Helvetica |
| Botões não funcionam | Verifique se são `TextButton` e não `Frame` |
| Erro de script | Verifique sintaxe no `_controller.lua` |

---

## 📝 Checklist Final

- [ ] PSD processado com sucesso
- [ ] Arquivos copiados para o projeto Roblox
- [ ] PNGs importados no Roblox Studio
- [ ] Assets linkados com `LinkAssets()`
- [ ] Manifest atualizado com Asset IDs
- [ ] UI testada e funcionando
- [ ] Responsividade verificada em diferentes resoluções

---

## 🎯 Próximos Passos

1. **Personalizar cores e textos** editando o `_manifest.json`
2. **Adicionar interatividade** no `_controller.lua`
3. **Testar em mobile** ajustando estratégias responsivas
4. **Otimizar assets** usando compressão adequada

---

**Dúvidas?** Consulte `IMPORT_GUIDE.md` para documentação completa.
