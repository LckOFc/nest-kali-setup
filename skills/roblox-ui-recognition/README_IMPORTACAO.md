# 🚀 Guia Rápido — Importação Automatizada para Roblox

## Métodos de Importação Disponíveis

| Método | Comando | Descrição |
|--------|---------|-----------|
| **Cópia Automática** | `--method copy` | Copia arquivos para pasta do projeto (mais confiável) |
| **API Roblox** | `--method api` | Upload via API (requer cookie ROBLOX_COOKIE) |
| **Power Automate** | `--method powerautomate` | Gera script Windows para automação |
| **Plugin Drag & Drop** | `--method plugin` | Plugin Roblox para arrastar arquivos |

---

## Uso Rápido

### Método 1: Script Completo (Recomendado)

```powershell
cd C:\Users\devel\.config\opencode\skills\roblox-ui-recognition

# Processar PSD e importar automaticamente
.\import-complete.ps1 "C:\design\menu.psd" --screen MainMenu --project "C:\seu_projeto"
```

### Método 2: Passo a Passo

```powershell
# 1. Processar PSD
node psd-to-roblox-ai.js "menu.psd" --screen MainMenu --output ./output/

# 2. Importar para projeto
node roblox-auto-importer.js ./output --method copy --project "C:\seu_projeto" --screen MainMenu

# 3. No Roblox Studio, executar no Output:
local AM = require(game.ReplicatedStorage.UIBridge.AssetManager)
AM.LinkAssets("MainMenu")
```

### Método 3: Apenas Copiar (sem processar)

```powershell
# Se já tiver os assets prontos
node roblox-auto-importer.js "./assets/" --method copy --project "C:\seu_projeto"
```

---

## Estrutura de Pastas

```
SeuProjetoRoblox/
├── src/
│   └── StarterPlayer/
│       └── StarterPlayerScripts/
│           ├── UIBridge/              ← Motor UI
│           │   ├── UIBridge.luau
│           │   ├── AssetManager.luau
│           │   └── ImportManager.luau
│           │
│           └── UIAssets/              ← Assets importados
│               └── MainMenu/
│                   ├── bg_main_xxx.png   ← Copiados automaticamente
│                   ├── btn_play_xxx.png
│                   ├── _manifest.json
│                   └── _controller.lua
│
└── default.project.json
```

---

## Comandos Úteis

```powershell
# Ver ajuda
node roblox-auto-importer.js --help

# Gerar script Power Automate
node roblox-auto-importer.js ./output --method powerautomate

# Gerar plugin Roblox
node roblox-auto-importer.js ./output --method plugin

# Lista assets no projeto
node roblox-ui-manage.js list-assets

# Atualiza placeholders no código Lua
node roblox-ui-manage.js update-placeholders _controller.lua --assets=layer1=123456789
```

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Sharp não encontrado | `npm install sharp` |
| Cookie inválido | Obtenha cookie em Developer.roblox.com |
| Pasta não existe | Crie estrutura manualmente |
| Assets não aparecem | Aguarde upload completar no Roblox |
| Erro de script | Verifique se UIBridge está em ReplicatedStorage |

---

## Requisitos

- Node.js v18+
- sharp (`npm install sharp`)
- Roblox Studio instalado
- Projeto Roblox com estrutura correta

---

**Dúvidas?** Consulte `GUIA_PASSO_A_PASSO.md` para documentação completa.
