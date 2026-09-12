---
name: openclaude-context
description: Sistema avançado de contexto baseado no openclaude. Gerencia janela de contexto, pruning de relevância, compaction automática e estratégia híbrida de contexto multi-turno.
aliases:
  - contexto
  - context
  - compact
  - prune
  - relevancia
---

# OpenCode Context System — Melhorias do OpenClaude

## Visão Geral

Sistema de gerenciamento de contexto completo baseado na arquitetura openclaude. Fornecido por `context.js` em `~/.config/opencode/`.

## Módulos

### 1. Context Window Management
- Janela dinâmica por modelo
- Override por sessão
- Limite mínimo de 33k tokens (evita paradoxo de auto-compact)
- Escalonamento de output tokens (8k default → 64k escalated)

### 2. Relevance-Based Pruning
- Score de relevância por similaridade de palavras-chave
- Preservação de mensagens recentes (default: 3 turns × 2)
- Proteção de tool calls e erros
- Filtragem por threshold (default: 0.15)

### 3. Memory Compaction
- Resumo automático de mensagens antigas
- Preservação das N mensagens recentes
- Log de compactação no histórico

### 4. Multi-Turn Context
- Tracking de turns por agente
- Contexto cruzado entre sessões
- Summary de atividades por agente

### 5. Hybrid Context Strategy
- Estratégia híbrida: relevante + recente
- Particionamento por tipo (system/instruction/conversation/tools)
- Otimização de tamanho por partição

## Comandos Slash

```
/context_window <model> <tokens>    # Define janela de contexto
/context_status [model]              # Mostra status atual
/compact                             # Compacta histórico
/context_analyze [messages]          # Analisa uso de contexto
/context_suggest                     # Sugestões de otimização
```

## Configuração

```json
{
  "context": {
    "window_default": 512000,
    "compact_tail_turns": 3,
    "relevance_threshold": 0.15,
    "auto_compact": true,
    "auto_compact_threshold": 0.8
  }
}
```

## Integração com Agentes

```javascript
const ctx = require('./context.js')

// Análise antes de enviar
const analysis = ctx.analyzeContext(messages)
if (analysis.utilization > 80) {
  ctx.compactContext(configDir)
}

// Pruning com contexto da tarefa
const pruned = ctx.pruneMessages(messages, {
  taskContext: currentTaskDescription,
  preserveRecent: 10,
  minRelevance: 0.2
})
```

## Pipeline de Contexto

```
Input → Analyze → Check Doom Loop → Validate Images
       → Search KG → Cache Lookup → Prune if needed
       → Compact if >80% → Output → Learn Pattern
```
