---
name: openclaude-cli
description: Enhancements de CLI baseado no openclaude. Terminal status, context-aware display, enhanced prompt, error formatting e session display.
aliases:
  - cli
  - terminal
  - status
  - display
  - prompt
---

# OpenCode CLI Enhancements — Melhorias do OpenClaude

## Visão Geral

Sistema de melhorias de CLI baseado em padrões do openclaude (`terminal.ts`, `status.tsx`, `promptEditor.ts`, `format.ts`).

## Módulos

### 1. TerminalStatus
- Write com cor e bold
- Progress bars dinâmicas
- Spinner animations
- Clear line para updates in-place
- Indicadores de status coloridos

### 2. ContextAwareDisplay
- Display de contexto em tempo real
- Modelo, agente, uso de tokens
- Atualização auto ao mudar contexto
- Cores por utilization (green/yellow/red)

### 3. EnhancedPrompt
- Prefix personalizado (◆)
- History navigation (up/down arrows)
- Auto-complete support
- Clear on new session

### 4. ErrorDisplay
- Error com formato estruturado
- Warning amarelo
- Success verde
- Info cyan

### 5. SessionDisplay
- Info da sessão ativa
- ID, modelo, timestamps
- Contagem de mensagens

### 6. Format Utils
- Token count format (1.5K, 2.3M)
- Duration format (1.2s, 3m 45s)
- Table formatting com borders

## Comandos Slash

```
Nenhum comando direto — tudo é UI/UX
```

## Configuração

```json
{
  "cli": {
    "status_bar": true,
    "progress_indicators": true,
    "token_display": true,
    "session_indicator": true,
    "color_output": true,
    "spinner_animations": true,
    "table_formatting": true
  }
}
```

## Exemplo de Uso

```javascript
const cli = require('./cli_enhancements.js')

const term = cli.createTerminal()
const prompt = cli.createPrompt()

// Spinner durante operação longa
const spinner = term.spinner(['Processing', 'Analyzing', 'Building'], { interval: 100 })
// ... trabalho ...
spinner.stop('Done!')

// Display contextual
const ctxDisplay = cli.createContextDisplay(term)
ctxDisplay.setContext({ model: 'agnes/agnes-2.5-flash', tokenUsage: 45000 })

// Formatting
console.log(cli.formatTokenCount(1500000))  // "1.5M"
console.log(cli.formatDuration(123456))      // "2m 3s"
console.log(cli.formatTable(rows, headers))  // ASCII table
```
