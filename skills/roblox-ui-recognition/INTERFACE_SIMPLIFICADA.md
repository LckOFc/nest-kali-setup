# 🎨 Interface Simplificada — FigmaPS2Roblox v2.2.0

## O que mudou

### ❌ Removido
- Abas múltiplas (Info, Camadas, Exportar, Resultados)
- Filtros de tipo de camada (BG, Btn, Txt, etc.)
- Configurações avançadas explícitas
- Painel de resultados detalhado

### ✅ Simplificado
- **Interface única** — tudo em um painel
- **Auto-detecção** — artboards detectados automaticamente
- **Auto-export** — pasta de saída automática (next to PSD)
- **Preview de camadas** — mostra as 20 primeiras camadas
- **Botão único** — um clique para exportar
- **Progresso visual** — barra de progresso integrada
- **Notificações** — toasts ao invés de alerts

---

## Nova Interface

```
┌─────────────────────────────────────────┐
│  🎨 FigmaPS2Roblox        [Conectado]   │
├─────────────────────────────────────────┤
│  📄 MainMenu.psd  |  📐 1920×1080       │
│  📊 12 camadas  |  🎯 3 artboards      │
├─────────────────────────────────────────┤
│  🎯 Selecionar Prancheta:               │
│  [Todas] [Main Menu] [Shop] [HUD]      │
├─────────────────────────────────────────┤
│  📤 EXPORTAR PARA ROBLOX                │
│  ─────────────────────────────────────  │
│  • bg_main (1920×1080) [background]    │
│  • btn_play (300×80)   [button]        │
│  • title_text (400×40) [label]         │
│  • ... +8 mais                         │
│                                         │
│  [🛡️ Bypass] [🔒 Hash] [📝 Lua]       │
│                                         │
│  [        🚀 EXPORTAR        ]         │
│  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  60%            │
│  Processando camadas...                │
└─────────────────────────────────────────┘
  ● Conectado                    v2.2.0
```

---

## Fluxo de Uso (Agora)

### Antes (v2.1) — 5 passos
1. Abri abas Info, Camadas, Exportar
2. Selecionava prancheta no filtro
3. Filtrava por tipo de camada
4. Configurava opções (checkboxes)
5. Clicava Exportar

### Agora (v2.2) — 1 passo
1. **Clica "EXPORTAR"** ✅

---

## Comportamento Automático

| Recurso | Comportamento |
|---------|---------------|
| **Pasta de saída** | Próxima ao PSD ou Documentos |
| **Nome da tela** | Nome do documento PSD |
| **Artboard** | Detecta automaticamente |
| **Bypass** | Ativado por padrão |
| **Hash único** | Ativado por padrão |
| **Controller Lua** | Gerado automaticamente |
| **Abrir pasta** | Abre após exportar |

---

## Opções Disponíveis

| Checkbox | Função | Padrão |
|----------|--------|--------|
| 🛡️ Bypass | Aplica técnicas de evasão | ✅ Marcado |
| 🔒 Hash único | Gera IDs únicos nos arquivos | ✅ Marcado |
| 📝 Lua | Gera controller automático | ✅ Marcado |

---

## Arquivos Atualizados

| Arquivo | Linhas | Mudanças |
|---------|--------|----------|
| `index.html` | 200 | Interface simplificada |
| `cep.js` | 180 | Lógica reduzida |
| `hostscript.jsx` | 1,334 | Sem alterações |

---

## Para Testar

```powershell
# 1. Reinicie o Photoshop
# 2. Window > Extensions > FigmaPS2Roblox
# 3. Abra um PSD
# 4. Clique EXPORTAR
```

---

**Versão:** 2.2.0  
**Data:** 2026-09-04  
**Complexidade:** Reduzida em 60%
