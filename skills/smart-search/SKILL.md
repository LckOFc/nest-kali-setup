---
name: smart-search
description: Sistema avançado de busca e recuperação — múltiplos métodos de acesso para otimização do opencode. Inclui fuzzy search, semantic search, indexação inteligente, e query expansion. V2.1: shorthand commands, performance metrics.
aliases:
  - busca
  - search
  - buscar
  - procurar
  - encontrar
  - smartsearch
  - query
  - v2.1
---

# Smart Search System v2.1 — Otimização do Opencode

Sistema avançado de busca com múltiplos métodos de acesso para melhorar a recuperação de informações no opencode.

> **v2.1**: Shorthand commands (`s`, `sf`, `ss`, `sl`, `sh`, `sr`, `sm`, `sd`), métricas de performance, cache inteligente.

## Métodos de Busca Disponíveis

### 1. Busca por Conteúdo (Grep Inteligente)
```
search "pattern" [--include *.js] [--exclude node_modules] [--context 3]
grep -rn "padrão" --include="*.ts" --exclude-dir=node_modules
```

### 2. Busca por Arquivo (Glob Avançado)
```
find "nome_arquivo*" --type f --ext .py
glob "**/*.config.{json,yaml}"
```

### 3. Busca Fuzzy (Approximada)
```
fuzzy_search "loggin" → matches: "login", "logging", "logged"
```

### 4. Busca Semântica (Contextual)
```
semantic_search "autenticação com token" → retorna: auth.ts, jwt.ts, oauth.ts
```

### 5. Busca por Hash/ID
```
hash_search "eyJhbGciOiJIUzI1NiJ9" → encontra arquivos com JWT
id_search "client_abc123" → encontra referências a IDs específicos
```

### 6. Busca por Data/Modificação
```
recent_search --hours 24 --type log
modified_search --since "2026-09-01" --pattern "*.js"
```

### 7. Busca em Logs
```
log_search "error" --last 100 --file stderr.log
trace_search "psiuframerapp://callback" --source debug_logs
```

### 8. Busca por Tipo de Conteúdo
```
type_search --kind function --name "transitionTo*"
const_search --pattern "const.*electronAPI" --include *.js
variable_search --scope local --name "*token*"
```

### 9. Busca em JSON/Config
```
json_search --path opencode.jsonc --query '.agent.shadow.tools'
config_search --key "maxSteps" --value ">30"
```

### 10. Busca Multi-Fontes
```
multi_search "bypass" --sources:files,logs,config,agents
unified_search "auth" --depth:full --fuzzy:true
```

## Comandos Otimizados (v2.1)

| Comando | Descrição | Tempo Médio |
|---------|-----------|-------------|
| `s "padrão"` | Busca rápida (shorthand) | <100ms |
| `sf "padrão"` | Fuzzy search | <500ms |
| `ss "conceito"` | Semantic search | <1s |
| `sl "padrão"` | Log search | <200ms |
| `sh "hash"` | Hash/content search | <300ms |
| `sr "padrão"` | Recent files search | <150ms |
| `sm "padrão"` | Multi-source search | <2s |
| `sd "padrão"` | Deep directory search | <500ms |

## Configuração de Indexação

```json
{
  "search": {
    "enabled": true,
    "index": {
      "paths": ["./src", "./agents", "./skills"],
      "exclude": ["node_modules", ".git", "dist"],
      "extensions": [".js", ".ts", ".py", ".md", ".json", ".jsonc"],
      "maxSize": "10MB",
      "refreshInterval": "5m"
    },
    "fuzzy": {
      "enabled": true,
      "maxDistance": 2,
      "minLength": 3
    },
    "semantic": {
      "enabled": true,
      "model": "local-embedding",
      "threshold": 0.75
    },
    "cache": {
      "enabled": true,
      "ttl": "30m",
      "maxEntries": 10000
    }
  }
}
```

## Métricas de Performance (v2.1)

| Métrica | Objetivo | Nota |
|---------|----------|-------|
| Tempo de resposta | <500ms | Shorthand `s` atinge <100ms |
| Taxa de precisão | >90% | Fuzzy com distance=1 |
| Coverage de indexação | 100% | Todos os paths configurados |
| Cache hit rate | >80% | TTL 30min |
| Memória usada | <500MB | Índice compactado |

## Dicas de Otimização

1. **Use atalhos**: `s` é mais rápido que `search`
2. **Combine fontes**: `--all` ou `-a` busca em tudo
3. **Limite escopo**: `--scope src` é mais rápido que busca global
4. **Use índices**: Indexação prévia acelera buscas repetidas
5. **Cache ativo**: Mantém cache quente para consultas frequentes

---

**Smart Search System v2.1 — Cada busca otimizada, cada resultado relevante.** 🐀

### 1. Busca por Conteúdo (Grep Inteligente)
```
search "pattern" [--include *.js] [--exclude node_modules] [--context 3]
grep -rn "padrão" --include="*.ts" --exclude-dir=node_modules
```

### 2. Busca por Arquivo (Glob Avançado)
```
find "nome_arquivo*" --type f --ext .py
glob "**/*.config.{json,yaml}"
```

### 3. Busca Fuzzy (Approximada)
```
fuzzy_search "loggin" → matches: "login", "logging", "logged"
```

### 4. Busca Semântica (Contextual)
```
semantic_search "autenticação com token" → retorna: auth.ts, jwt.ts, oauth.ts
```

### 5. Busca por Hash/ID
```
hash_search "eyJhbGciOiJIUzI1NiJ9" → encontra arquivos com JWT
id_search "client_abc123" → encontra referências a IDs específicos
```

### 6. Busca por Data/Modificação
```
recent_search --hours 24 --type log
modified_search --since "2026-09-01" --pattern "*.js"
```

### 7. Busca em Logs
```
log_search "error" --last 100 --file stderr.log
trace_search "psiuframerapp://callback" --source debug_logs
```

### 8. Busca por Tipo de Conteúdo
```
type_search --kind function --name "transitionTo*"
const_search --pattern "const.*electronAPI" --include *.js
variable_search --scope local --name "*token*"
```

### 9. Busca em JSON/Config
```
json_search --path opencode.jsonc --query '.agent.shadow.tools'
config_search --key "maxSteps" --value ">30"
```

### 10. Busca Multi-Fontes
```
multi_search "bypass" --sources:files,logs,config,agents
unified_search "auth" --depth:full --fuzzy:true
```

## Comandos Otimizados

| Comando | Descrição | Tempo Médio |
|---------|-----------|-------------|
| `s "padrão"` | Busca rápida (shorthand) | <100ms |
| `sf "padrão"` | Fuzzy search | <500ms |
| `ss "conceito"` | Semantic search | <1s |
| `sl "padrão"` | Log search | <200ms |
| `sh "hash"` | Hash/content search | <300ms |
| `sr "padrão"` | Recent files search | <150ms |
| `sm "padrão"` | Multi-source search | <2s |
| `sd "padrão"` | Deep directory search | <500ms |

## Configuração de Indexação

```json
{
  "search": {
    "enabled": true,
    "index": {
      "paths": ["./src", "./agents", "./skills"],
      "exclude": ["node_modules", ".git", "dist"],
      "extensions": [".js", ".ts", ".py", ".md", ".json", ".jsonc"],
      "maxSize": "10MB",
      "refreshInterval": "5m"
    },
    "fuzzy": {
      "enabled": true,
      "maxDistance": 2,
      "minLength": 3
    },
    "semantic": {
      "enabled": true,
      "model": "local-embedding",
      "threshold": 0.75
    },
    "cache": {
      "enabled": true,
      "ttl": "30m",
      "maxEntries": 10000
    }
  }
}
```

## Integração com Agentes

### Agente Sombra — Busca Otimizada
```
!busca "psiuframerapp" --recent --logs
!encontrar "transitionToDashboard" --files --agents
!procurar "bypass" --fuzzy --context 5
```

### Agente Kuroko — Análise de Artefatos
```
!busca "malware" --hash --yara
!analisar "sample.exe" --strings --imports --sections
!rastreiar "C2_server.com" --network --domains
```

### Agente Reversing — Engenharia Reversa
```
!busca "import" --binary --exports
!analisar "payload.dll" --functions --sequences
!converter "dump.bin" --assembly --pseudo-code
```

## Métricas de Performance

| Métrica | Objetivo | Atual |
|---------|----------|-------|
| Tempo de resposta | <500ms | - |
| Taxa de precisão | >90% | - |
| Coverage de indexação | 100% | - |
| Cache hit rate | >80% | - |
| Memória usada | <500MB | - |

## Scripts de Apoio

### indexador.py — Indexação Inteligente
```python
# Indexa arquivos para busca rápida
python indexador.py --path ./src --output index.json --fuzzy --semantic

# Atualiza índice incremental
python indexador.py --incremental --watch --interval 60

# Busca no índice
python indexador.py --query "autenticação" --top 10 --explain
```

### buscador.py — Frontend de Busca
```python
# Busca unificada
python buscador.py "token" --all --verbose

# Busca com context
python buscador.py "console.log" --context 3 --color

# Exporta resultados
python buscador.py "error" --output results.json --format json
```

### otimizador.py — Tuning de Performance
```python
# Analisa performance das buscas
python otimizador.py --benchmark --rounds 100

# Ajusta parâmetros automaticamente
python otimizador.py --auto-tune --metrics precision,recall,speed

# Gera relatório
python otimizador.py --report --output perf_report.md
```

## Exemplos de Uso

### Exemplo 1: Busca Rápida de Padrão
```
s "psiuframerapp" 
→ Encontra: main-clean.js:76, bypass.js:89, preload-clean.js:17
```

### Exemplo 2: Busca Fuzzy de Token
```
sf "tokn" 
→ Sugestões: token, talken, tokem, transaction
```

### Exemplo 3: Busca em Logs Recentes
```
sl "blocked" --last 50 --file debug_log
→ 2026-09-08T00:31:45 [Nav] blocked deep link: psiuframerapp://callback
```

### Exemplo 4: Busca Semântica de Conceito
```
ss "autenticação bypass"
→ Retorna: bypass.js, auth.md, agent-activation/SKILL.md
```

### Exemplo 5: Busca Multi-Fonte
```
sm "electron" --files --config --logs
→ Files: main.js, preload.js, package.json
   Config: opencode.jsonc (agent.electronAPI)
   Logs: stderr.log (electron cache errors)
```

## Dicas de Otimização

1. **Use atalhos**: `s` é mais rápido que `search`
2. **Combine fontes**: `--all` ou `-a` busca em tudo
3. **Limite escopo**: `--scope src` é mais rápido que busca global
4. **Use índices**: Indexação prévia acelera buscas repetidas
5. **Cache ativo**: Mantém cache quente para consultas frequentes

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Busca lenta | Execute `otimizador.py --auto-tune` |
| Resultados incompletos | Aumente `maxResults` na config |
| Fuzzy não encontra | Reduza `maxDistance` para 1 |
| Cache desatualizado | Execute `indexador.py --force-refresh` |

## Arquivos do Sistema

- `~/.config/opencode/skills/smart-search/SKILL.md` — Esta skill
- `~/.config/opencode/opencode.jsonc` — Configuração principal
- `~/scripts/busca/indexador.py` — Motor de indexação
- `~/scripts/busca/buscador.py` — Interface de busca
- `~/scripts/busca/otimizador.py` — Tuning de performance
