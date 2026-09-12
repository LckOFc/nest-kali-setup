---
name: invasao
description: Skill completa de invasao cibernetica. Orquestra todos os tools: Payloads (515+), Vuln Scanner (27 modulos), Burp Suite, RE Toolkit, Advanced RE, OSINT, Cracker, Sandbox, YARA, AI Pipeline. Workflow pronto de reconnaissance a exploit. V2.1: toolkit atualizado, paths corrigidos.
aliases:
  - invasion
  - attack
  - offensive
  - pentest-complete
  - full-invasion
  - warfare
  - op-invasion
  - v2.1
---

# Invasao Skill v2.1 — Sistema Completo de Ataque

Skill unificada que orquestra TODAS as capacidades de invasao em workflows prontos.

> **v2.1**: Atualizado para todas as ferramentas v2.1 (payload_manager_v2 com busca, exploit_chain com 6 chains, shadow_orchestrator com path auto-detect).

## 🎯 ARCHITETURA

```
┌─────────────────────────────────────────────────────────────────┐
│                    INVASAO SKILL v2.1                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ RECON      │  │ EXPLOIT     │  │ POST-EXP   │         │
│  │   OSINT    │  │   PAYLOAD   │  │   C2       │         │
│  │  SUBDOMAIN │  │   VULN SCAN │  │  PERSIST   │         │
│  │   WHOIS    │  │  BREACH HUNT│  │  EXFIL     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   RE         │  │   AI        │  │   REPORT   │         │
│  │  BIN ANALYSE │  │  ANALYSIS   │  │  GENERATOR │         │
│  │ DECOMPILE    │  │  HYPOTHESES │  │  PDF/MARK  │         │
│  │  STRINGS     │  │  RISK SCORE │  │  FINDINGS  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  TOOLS INTEGRADOS: 16/16 funcionais                            │
│  - Payload Manager v2.1 (515 payloads, 29 cats, search)       │
│  - Backend Vuln Scanner (27 modulos)                          │
│  - Burp Suite v2 (22 methods)                                 │
│  - RE Toolkit (7 engines)                                     │
│  - Advanced RE (anti-debug, VM, sandbox)                      │
│  - OSINT Aggregator v2.1 (6 sources)                          │
│  - Password Cracker v2.1 (parallel, 100+ words)               │
│  - Behavioral Sandbox v2.1 (async monitoring)                 │
│  - YARA Generator v2.1 (tags, escaping)                       │
│  - Source Extractor v2.1 (6-stage pipeline)                   │
│  - AI Analysis Pipeline v2.1 (enriched context)               │
│  - CHMID Pipeline v2.1 (bug fixes)                            │
│  - Fuzzy Hash v2.1 (multi-part compare)                       │
│  - Auto-Unpacker v2.1 (typed dataclasses)                     │
│  - DeepSeek Chat (AI bridge)                                  │
│  - Shadow Toolkit v2.1 (path auto-detect)                     │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 WORKFLOWS PRONTOS

### Workflow 1: Web App Attack (Recon → Exploit)
```
1. /toolkit vuln quick <target>
2. /toolkit vuln scan <target>
3. /toolkit vuln jwt_hunt <target>
4. /toolkit vuln exploit <target> --report results.json
5. /toolkit report create <target> --type pentest
```

### Workflow 2: Binary Analysis (RE → Exploit)
```
1. /toolkit re analyze <binary.exe>
2. /toolkit unpack analyze <binary.exe>
3. /toolkit re strings <binary.exe>
4. /toolkit re disasm <binary.exe> 0x1000 100
5. /toolkit yara generate <binary.exe> --name family
6. /toolkit sandbox run <binary.exe>
```

### Workflow 3: Full Pentest (Complete)
```
1. /toolkit osint domain <target>
2. /toolkit vuln scan <target>
3. /toolkit vuln brute <target>
4. /toolkit vuln exploit <target> --auto
5. /toolkit vuln extract <target> --data
6. /toolkit report create <target> --format pdf
```

### Workflow 4: Malware Analysis (Reverse → Signature)
```
1. /toolkit re analyze <malware.exe>
2. /toolkit unpack analyze <malware.exe>
3. /toolkit sandbox run <malware.exe> --timeout 60
4. /toolkit yara generate <malware.exe> --name emotet_v2
5. /toolkit fuzzy hash <malware.exe>
6. /toolkit report create <malware.exe> --type re
```

## 📋 COMANDOS RAPIDOS

```
# Web Attack
/toolkit vuln quick <target>          # Recon + scan rapido
/toolkit vuln scan <target>           # Scan completo
/toolkit vuln hunt-jwt <target>       # Captura JWT
/toolkit vuln brute <target>          # Brute force
/toolkit vuln exploit <target>        # Exploracao automatica

# Binary Analysis
/toolkit re analyze <binary>          # Analise PE completa
/toolkit re strings <binary>          # Extrai strings
/toolkit re disasm <binary> <off> <n> # Disassembly
/toolkit unpack analyze <binary>      # Detecta packer
/toolkit unpack auto <binary>         # Unpack UPX automatico
/toolkit extract full <binary>        # Recover source code

# Advanced RE
/toolkit advre full <binary>          # Pipeline anti-protecoes
/toolkit advre devirtualize <binary>  # VMProtect/Themida
/toolkit advre strings <binary>       # String decryption

# Sandboxing & AI
/toolkit sandbox run <binary>         # Executa + monitora
/toolkit ai analyze <binary>          # Hipoteses IA
/toolkit pipeline run <binary>        # CHMID 7 stages

# YARA & Signatures
/toolkit yara generate <binary> --name name  # Gera regra
/toolkit fuzzy hash <file>                 # Hash fuzzy

# Credentials
/toolkit crack <hash>                    # Crack hash offline
/toolkit payload list                    # Lista payloads
/toolkit payload search <keyword>        # Busca payloads (v2.1)
/toolkit payload waf-bypass <payload>    # WAF bypass

# JWT & GraphQL
/toolkit jwt analyze <token>             # Análise JWT
/toolkit jwt crack <token>               # Brute force JWT
/toolkit graphql test <endpoint>         # GraphQL scan
/toolkit race hot-payout <url>           # Race condition test
/toolkit chain <target> --chain jwt_chain # Exploit chain

# Shadow
/toolkit shadow status                   # Status serviços
/toolkit shadow flare solve <url>        # Cloudflare bypass
/toolkit shadow token hunt <url>         # Token capture
```

## 📊 STATUS DO SISTEMA

```python
# Verificar tudo funcionando
from toolkit_v2 import ToolManager
t = ToolManager()
status = t.status()
print(f"Tools loaded: {status['total']}/16")

# Testar payload
pm = t.tools['payload']
print(f"Payloads: {pm.get_stats()['total_payloads']}")
print(f"Categories: {len(pm.list_categories())}")

# Testar busca (v2.1)
results = pm.search_payloads("admin")
print(f"Search results: {len(results)}")

# Testar WAF bypass
bypasses = pm.waf_bypass("<script>alert(1)</script>")
print(f"WAF variants: {len(bypasses)}")

# Testar mutation
mutate = pm.mutate_payload("' OR 1=1--", 'sqli')
print(f"Mutations: {len(mutate)}")
```

## ⚡ PERFORMANCE

```
Web App Scan (example.com):
  - Recon: ~2s
  - Scan: ~15s
  - JWT Hunt: ~30s (com Selenium)
  - Report: ~1s

Malware Analysis (180MB agy.exe):
  - PE Parse: ~3s
  - Strings: ~5s (1.9M strings)
  - Sandbox: ~45s
  - YARA Gen: ~2s

RE Toolkit (binary.exe):
  - Functions: 100 identified
  - Types: 100 recovered
  - Memory: ~200MB (vs 1-2GB ferramentas originais)
```

## 🔧 DEPENDENCIAS

```bash
# Core
pip install pefile capstone lief python-whois aiohttp cryptography

# Web
pip install selenium webdriver-manager flask

# RE
pip install yara-python psutil wmi

# AI (opcional)
pip install httpx
# Instale Ollama: https://ollama.ai
```

---

**Invasao Skill v2.1 — 16 tools, 515 payloads, workflows prontos.** 🐀
