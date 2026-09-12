# 🎮 Plugin Roblox UI Auto Import — Guia Completo

## O que este plugin faz

Este plugin **DENTRO do Roblox Studio** automatiza toda a importação de UIs do Photoshop:

1. **Lê o manifest** gerado pelo plugin do Photoshop
2. **Encontra os assets PNG** na pasta exportada
3. **Importa para o Roblox** (upload de assets)
4. **Cria a estrutura de pastas** no Roblox
5. **Constrói a UI** automaticamente baseada no manifest

---

## Instalação

### Passo 1: Copiar Plugin para o Projeto

```powershell
# Copiar plugin para o projeto Roblox
Copy-Item "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\uibridge\RobloxUIAutoImport.plugin.lua" `
  "C:\seu_projeto\src\StarterPlayer\StarterPlayerScripts\UIBridge\RobloxUIAutoImport.lua"
```

### Passo 2: Instalar no Roblox Studio

1. Abra o Roblox Studio
2. Vá em **View > Plugins > Plugin Editor**
3. Cole o código do `RobloxUIAutoImport.plugin.lua`
4. Salve como **"RobloxUIAutoImport.lua"**
5. Execute o plugin (botão Run)

---

## Uso — Fluxo Completo

### No Photoshop

```
1. Abra seu PSD
2. Vá em Window > Extensions > FigmaPS2Roblox
3. Selecione a prancheta desejada
4. Configure e clique "Exportar para Roblox"
5. Anote o caminho da pasta de saída
```

### No Roblox Studio

```
1. Abra o projeto Roblox
2. Vá em View > Plugins > Roblox UI Auto Import
3. No campo "Pasta de Assets", cole o caminho da exportação
   Ex: C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\output\MainMenu
4. No campo "Nome da Tela", deixe "MainMenu"
5. Clique "🔍 Escanear Pasta"
6. Clique "📥 Importar Assets"
7. Clique "🏗️ Construir UI"
```

---

## O que o Plugin Lê do Manifest

O plugin lê o arquivo `_manifest.json` e extrai:

```json
{
  "name": "MainMenu",              // Nome da tela
  "canvasWidth": 1920,             // Largura do canvas
  "canvasHeight": 1080,            // Altura do canvas
  "scaleMode": "ScaleToFit",       // Modo de escala
  "assets": [                      // Lista de assets
    {
      "uniqueId": "abc123def456",  // ID único do asset
      "filename": "bg_main_xxx.png", // Nome do arquivo
      "type": "background",         // Tipo (background, button, etc.)
      "name": "bg_main",            // Nome para referência
      "x": 0, "y": 0,              // Posição
      "width": 1920, "height": 1080, // Tamanho
      "assetId": "rbxassetid://0"   // ID do Roblox (preenchido após import)
    }
  ],
  "elements": [...]                // Estrutura da UI
}
```

---

## Estrutura Gerada no Roblox

Após importar, o plugin cria:

```
ReplicatedStorage/
└── UIAssets/
    └── MainMenu/
        ├── _manifest.json      ← Manifest original (atualizado com IDs)
        ├── _controller.lua     ← Código Lua gerado
        ├── bg_main_abc123.png  ← Asset importado (ID preenchido)
        ├── btn_play_xyz789.png
        └── ...
```

---

## Comandos Disponíveis no Plugin

| Botão | Função |
|-------|--------|
| 🔍 **Escanear Pasta** | Lista todos os PNGs na pasta selecionada |
| 📥 **Importar Assets** | Faz upload dos assets para o Roblox |
| 🏗️ **Construir UI** | Cria a interface baseada no manifest |
| 🔄 **Atualizar Manifest** | Copia o mapeamento de assets para clipboard |

---

## Workflow Automatizado (PowerShell)

Para automatizar todo o processo:

```powershell
# 1. Processar PSD (Node.js)
node psd-to-roblox-ai.js "menu.psd" --screen MainMenu --output ./output/

# 2. Copiar para projeto Roblox
Copy-Item output/MainMenu/* -Destination "C:\projeto\src\...\UIAssets\MainMenu\"

# 3. No Roblox Studio, executar plugin
# Abra o plugin RobloxUIAutoImport e clique nos botões
```

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Plugin não aparece | Verifique se está em `ReplicatedStorage.UIBridge` |
| Assets não importam | Roblox Studio precisa de upload manual via Explorer |
| UI não aparece | Verifique se `ScreenGui.Parent` está correto |
| Erro de JSON | Verifique se `_manifest.json` está válido |

---

## Notas Importantes

⚠️ **Limitação do Roblox:** O Roblox Studio **não permite upload programático** de assets via Luau. O plugin guia você para fazer o upload manual, mas automatiza toda a estrutura e código.

✅ **O que é automatizado:**
- Leitura do manifest
- Criação da estrutura de pastas
- Geração do código Lua
- Mapeamento de assets

❌ **O que é manual:**
- Upload dos PNGs (requer interação do usuário no Explorer)

---

**Versão:** 1.0.0
**Autor:** FigmaPS2Roblox System
**Data:** 2026-09-04
