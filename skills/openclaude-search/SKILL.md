---
name: openclaude-search
description: Sistema avançado de busca e conhecimento baseado no openclaude. Inclui Knowledge Graph, Semantic Index, Transcript Search e Relevance Ranking.
aliases:
  - busca
  - search
  - knowledge
  - graph
  - transcript
---

# OpenCode Search System — Melhorias do OpenClaude

## Visão Geral

Sistema completo de busca e recuperação baseado em `knowledgeGraph.ts`, `queryContext.ts` e `transcriptSearch.ts` do openclaude.

## Módulos

### 1. Knowledge Graph
- Entidades com tipos e atributos
- Relações source→target tipadas
- Semantic summaries com keywords
- Migração automática de legacy JSON/SQLite
- Persistência em disco

### 2. Semantic Search Index
- Indexação por hash SHA-256
- Busca por palavras-chave com scoring
- Boost por hit count (popularidade)
- Filtro por tipo de conteúdo
- Threshold de similaridade ajustável (default: 0.65)

### 3. Transcript Search
- Busca em transcripts com regex
- Contexto de linhas (default: 2)
- Cache de resultados (TTL 60s)
- Case-sensitive option

### 4. Relevance Scoring & Ranking
- Score por keyword overlap (Jaccard-like)
- Rank por relevância + recência
- Preservação de mensagens recentes
- Filtro por minimum score

## Comandos Slash

```
/kg_add <type> <name> [attrs...]    # Adiciona entidade ao grafo
/kg_search <query>                  # Busca no knowledge graph
/kg_list [type]                     # Lista entidades
/search_index <query>               # Busca no índice semântico
/transcript_search <pattern>        # Busca em transcripts
```

## Configuração

```json
{
  "search": {
    "knowledge_graph": true,
    "semantic_index": true,
    "transcript_search": true,
    "max_results": 20,
    "similarity_threshold": 0.65,
    "fuzzy_enabled": true
  }
}
```

## Integração com Smart Search

O skill `smart-search` existente é complementado pelo knowledge graph:

```
smart-search (fuzzy/semantic) + openclaude-search (graph/index/transcript)
= Busca unificada com contexto estruturado
```
