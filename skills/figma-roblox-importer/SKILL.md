---
name: figma-roblox-importer
description: Skill para importar UI do Figma/Photoshop para o Roblox. Converte designs em scripts Luau usando conversor-engineering-reverse ou gerador procedural. Inclui detecção automática de UIListLayout, responsividade, gradientes e UICorner.
aliases:
  - ui-importer
  - figma-import
  - photoshop-import
  - roblox-ui
  - figma-roblox-converter
---

# Figma/Photoshop → Roblox UI Importer

Importa designs de UI do Figma ou Photoshop para o Roblox Studio automaticamente.

## Comandos

| Comando | Descrição |
|---------|-----------|
| `importar ui [caminho]` | Importa UI do Figma/Photoshop |
| `importar figma [arquivo.json]` | Importa do JSON exportado do Figma (conversor reverse-engineered) |
| `importar photoshop [arquivo]` | Importa do Photoshop (PSD/PNG) |
| `status ui` | Mostra estado dos assets importados |
| `sincronizar ui` | Sincroniza com Roblox Studio via Rojo |

## Como Usar

### Método 1: JSON do Figma (Conversor Reverse-Engineered)

O conversor Python implementa o pipeline completo do plugin figma-to-roblox-luau com melhorias:

```bash
python3 ~/.config/opencode/skills/figma-roblox-importer/figma_roblox_converter.py design.json -o output.lua
```

**Opções disponíveis:**
- `--no-scale` — Usa Offset puro (não Scale+Offset)
- `--no-list-layout` — Desativa detecção automática de UIListLayout
- `--no-responsive` — Desativa regras de responsividade
- `--no-screen-gui` — Não gera ScreenGui wrapper
- `--no-comments` — Remove comentários do código
- `--indent N` — Tamanho da indentação (default: 2)

**Melhorias em relação ao plugin original:**
- `sanitize_name` colapsa underscores múltiplos (`Help (FAQ)` → `Help_FAQ`)
- Escape de null byte em strings Lua
- Detecção de AutoLayout do Figma
- Regras de responsividade adicionais (elementos largos → full-width mobile)
- Conversão de cores com menor erro de arredondamento

### Método 2: Pasta de Imagens

```
importar photoshop ./design/
```

Onde `./design/` contém imagens PNG exportadas do Figma/Photoshop.

### Método 3: Descrição Textual

```
importar ui "Criar menu com fundo escuro, titulo centralizado e botoes PLAY, SETTINGS, SHOP"
```

## Pipeline de Conversão (Reverse-Engineered)

```
JSON Figma → parse_node() → compute_relative_position() → detect_list_layout()
    → inject_responsive_rules() → export_to_lua()
```

**Detecções automáticas:**
- UIListLayout: gaps ≤ 5px entre filhos alinhados
- AnchorPoint: constraints CENTER/MAX do Figma
- Interatividade: nomes contendo "button", "btn", "cta"
- AutoLayout: layoutMode do Figma → FillDirection
- Responsividade: fontSize > 20 reduz 30% em mobile, elementos largos → full-width

## Estrutura de Saída

```
src/StarterPlayer/StarterPlayerScripts/[NomeDoProjeto]/UI/
├── GeneratedUI/
│   ├── MainMenuUI.lua           # Script principal
│   ├── MainMenuUI.meta.json     # Config Rojo
│   └── assets/                  # Assets importados
└── UIManager.lua                # Gerenciador de telas
```

## Integração com Rojo

Adicione ao `default.project.json`:
```json
{
  "tree": {
    "StarterPlayer": {
      "StarterPlayerScripts": {
        "NomeDoProjeto": {
          "UI": {
            "$path": "src/StarterPlayer/StarterPlayerScripts/NomeDoProjeto/UI"
          }
        }
      }
    }
  }
}
```

## Arquivos da Skill

| Arquivo | Função |
|---------|--------|
| `figma_roblox_converter.py` | Conversor Figma JSON → Luau (reverse-engineered) |
| `ANALYSIS.md` | Relatório completo da engenharia reversa |
| `../roblox-ui-recognition/psd-to-roblox.js` | Exportador PSD → PNG + controller Lua |
| `../roblox-ui-recognition/roblox-ui-generator.js` | Gerador de boilerplate UI por tipo |
| `../roblox-ui-recognition/roblox-ui-analyzer.js` | Analisador de UI existente no projeto |

## Requisitos

- Python 3.8+
- Roblox Studio instalado
- Rojo instalado (`rokit install` ou `cargo install rojo`)
- Projeto Roblox configurado com estrutura de UI
