---
name: openclaude-websearch
description: Sistema avançado de busca na internet e fóruns de segurança. Busca em GitHub, Stack Overflow, Reddit, Hacker News, Exploit-DB, CVE, Pastebin e mais. Com query expansion, ranking inteligente e detecção de tipo de fórum. V2.1: multi-source ranking, auto-expansion.
aliases:
  - web_search
  - busca_web
  - forum
  - exploit_search
  - cve
  - github_search
  - reddit_search
  - stackoverflow
  - v2.1
---

# OpenCode Web Search v2.1 — Busca Avançada na Internet & Fóruns

## Visão Geral

Sistema de busca unificada em múltiplas fontes da internet, otimizado para pesquisa de segurança, exploits e vulnerabilidades.

## Fontes de Busca

| Fonte | Endpoint | Uso |
|-------|----------|-----|
| GitHub API | `api.github.com/search/code` | Código, issues, PRs |
| Stack Overflow | `api.stackexchange.com` | Soluções técnicas |
| Reddit | `reddit.com/search` | Discussões de segurança |
| Hacker News | `hn.algolia.com` | Notícias tech/security |
| Exploit-DB | `exploit-db.com` | Exploits conhecidos |
| NVD/CVE | `services.nvd.nist.gov` | Vulnerabilidades oficiais |
| DuckDuckGo | `html.duckduckgo.com` | Busca geral (sem API) |

## Query Expansion Automática (v2.1)

O sistema expande automaticamente queries com:
- **Sinônimos**: exploit→vulnerability→CVE, bypass→evasion, etc.
- **Templates por fonte**: `site:github.com <query>`, `site:stackoverflow.com <query>`
- **Classificação automática**: detecta se busca é por CVE, exploit, RE, pentest, etc.

## Ranking Inteligente

Results são ranqueados por:
1. **Score base** (fonte)
2. **Match de keywords** no título/snippet
3. **Peso da fonte** (CVE > ExploitDB > SO > Reddit)
4. **Recência** (últimos 30 dias bonus)
5. **CVSS** (vulnerabilidades críticas +0.5)

## Comandos Slash

```
/web_search <query> [--type general|github|stackoverflow|reddit|cve|exploits|news]
/gh_search <query>                     # GitHub code + issues
/so_search <query>                     # Stack Overflow
/reddit_search <query>                 # Reddit security subs
/cve_search <query>                    # CVE/NVD database
/exploit_search <query>                # Exploit-DB
/hn_search <query>                     # Hacker News
/search_stats                          # Stats do sistema
```

## Configuração

```json
{
  "web_search": {
    "max_results": 15,
    "cache_ttl_hours": 1,
    "enabled_sources": ["github", "stackoverflow", "reddit", "hackernews", "cve", "exploitdb", "duckduckgo"],
    "auto_expand_queries": true,
    "rank_by_source_weight": true
  }
}
```

---

**OpenCode Web Search v2.1 — Inteligência buscada, contexto encontrado.** 🐀

```javascript
const web = require('./web_search.js')

// Busca rápida por tipo
const gh = await web.searchGitHub('buffer overflow windows')
const so = await web.searchStackOverflow('JWT bypass authentication')
const cve = await web.searchCVE('CVE-2024-1234')

// Busca unificada com expansão
const results = await web.search('RCE in Apache Log4j')
console.log(results.classification) // { types: ['exploit', 'general'], query }
console.log(results.results)        // ranked across all sources
```

## Configuração

```json
{
  "web_search": {
    "max_results": 15,
    "cache_ttl_hours": 1,
    "enabled_sources": ["github", "stackoverflow", "reddit", "hackernews", "cve", "exploitdb", "duckduckgo"],
    "auto_expand_queries": true,
    "rank_by_source_weight": true
  }
}
```

## Exemplos de Uso

```javascript
// Buscar exploit conhecido
const r = await web.searchExploits('Apache Struts RCE')
// → EDB-1234, EDB-5678, etc.

// Buscar solução SO para erro específico
const r = await web.searchStackOverflow('Node.js ECONNREFUSED connect EADDRNOTAVAIL')
// → Top answers com votes

// Buscar CVE com CVSS alto
const r = await web.searchCVE('log4j')
// → CVEs com scores e severidade

// Busca cruzada
const r = await web.searchByCategory('vulnerability', 'authentication bypass')
// → GitHub issues + SO + Reddit + CVEs
```
