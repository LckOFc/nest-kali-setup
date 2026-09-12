---
name: openclaude-learning
description: Harness de aprendizado baseado no openclaude. Session persistence, conversation cache LRU, recovery com checkpoints, pattern learning e cross-session memory.
aliases:
  - aprendizado
  - learning
  - session
  - cache
  - checkpoint
  - memoria
---

# OpenCode Learning Harness — Melhorias do OpenClaude

## Visão Geral

Sistema completo de aprendizado e persistência baseado em `sessionPersistence.ts`, `conversationCache.ts`, `conversationRecovery.ts` e `crossProjectResume.ts` do openclaude.

## Módulos

### 1. Session Manager
- Criação, salvamento e load de sessões
- Tags e metadados por sessão
- Histórico de sessões com rotação (max 500)
- Mensagens com timestamp e tracking de tokens

### 2. Conversation Cache (LRU)
- Cache in-memory com eviction LRU
- TTL configurável (default: 24h)
- Tracking de hits e evictions
- Stats de hit rate

### 3. Conversation Recovery
- Checkpoints automáticos por sessão
- Restore por timestamp ou último disponível
- Cleanup automático de checkpoints antigos (>24h)
- Snapshot das últimas 10 mensagens

### 4. Learning Patterns
- Detecção automática de padrões em interações
- Classificação por outcome (success/error/unknown)
- Suggestions baseadas em padrões anteriores
- Log de feedback para aprendizado contínuo

### 5. Cross-Session Memory
- Preferências do usuário persistentes
- Contexto por projeto
- Comandos aprendidos (últimos 50)
- Histórico de token usage

## Comandos Slash

```
/session_new [--model <m>] [--tag <t>]    # Nova sessão
/session_list [--limit N] [--tag <t>]     # Lista sessões
/session_resume <id>                      # Retoma sessão
/cache_stats                              # Stats do cache
/checkpoint_save <session_id>             # Salva checkpoint
/checkpoint_list [--session <id>]         # Lista checkpoints
/learn_pattern <outcome>                  # Registra padrão
/preference_set <key> <value>             # Define preferência
/preference_get <key>                     # Busca preferência
```

## Configuração

```json
{
  "learning": {
    "session_persistence": true,
    "conversation_cache": true,
    "cache_ttl_hours": 24,
    "max_cache_entries": 100,
    "pattern_learning": true,
    "cross_session_memory": true,
    "max_sessions": 500
  }
}
```

## Pipeline de Aprendizado

```
Start Session → Add Messages → Detect Patterns → Save Checkpoint
      ↓
Response → User Feedback → Learn Pattern → Update Cross-Session Memory
      ↓
Next Session → Restore Context → Apply Preferences
```
