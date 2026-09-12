---
name: openclaude-tasks
description: Otimização de tarefas baseada no openclaude. Doom loop detection, task reporting, streaming optimizer e interruption tracking.
aliases:
  - tarefas
  - tasks
  - doom
  - loop
  - optimize
  - stream
---

# OpenCode Task Optimization — Melhorias do OpenClaude

## Visão Geral

Sistema de otimização de tarefas baseado em `doomLoop.ts`, `copilotOptimization.ts`, `taskReport.ts` e `streamingOptimizer.ts` do openclaude.

## Módulos

### 1. Doom Loop Detector
- Detecção de loops infinitos por assinatura SHA-256
- Threshold configurável (default: 3 chamadas idênticas)
- State por agente (main + subagents isolados)
- Bloqueio automático com message explicativo
- Reset manual por agente

### 2. Task Reporter
- Tracking de tasks com lifecycle completo
- Steps com timestamp
- Token usage por task
- Success/failure rates
- Summary com métricas agregadas

### 3. Task Optimizer
- Agendamento com priority queue
- Max concurrent tasks (default: 5)
- Status de fila e execução
- Backpressure automático

### 4. Streaming Optimizer
- Bufferização de chunks com flush threshold
- Auto-flush a cada 4096 bytes
- Stats de buffers ativos
- Clean release ao finalizar stream

### 5. Interruption Tracker
- Registro de interrupções com state snapshot
- Tracking de continuações
- Stats de interrupções vs continuações

## Comandos Slash

```
/doom_loop_status [--agent <name>]   # Status da deteção
/doom_loop_reset [--agent <name>]    # Reseta deteção
/task_report                         # Resumo de execução
/task_list [--limit N]               # Lista tarefas recentes
/task_status                         # Status de otimização
/stream_stats                        # Estatísticas de streaming
```

## Configuração

```json
{
  "tasks": {
    "doom_loop_detection": true,
    "doom_loop_threshold": 3,
    "max_concurrent_tasks": 5,
    "streaming_optimizer": true,
    "task_reporting": true,
    "interruption_tracking": true
  }
}
```

## Integração com Doom Loop Permission

A permissão `doom_loop` já existe na config. Este sistema a potencia:

```javascript
const tasks = require('./task_optimization.js')

// Antes de cada tool call
const result = tasks.checkDoomLoop(toolName, input, { agentKey: 'shadow' })
if (result.blocked) {
  console.log(result.message)
  // Mudar abordagem
}
```
