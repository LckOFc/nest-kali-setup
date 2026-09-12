---
name: backend-vuln-scanner
description: Sistema completo de scanner de vulnerabilidades backend com integracao automatica. 27 modulos, 35 comandos slash, integracao com CustomBurp Suite. Inclui exploit database, reverse engineering, CTF helper, dark web search, e tor search via gateways publicos. Executa reconhecimento, testes de seguranca, bypass de WAF, analise JWT, exploracao automatica, brute force, subdomain enum, data extraction, mass scan, engenharia reversa e assistencia CTF sem intervencao manual. V2.1: 27 modulos, integrações atualizadas.
aliases:
  - vuln
  - scanner
  - pentest
  - bug-bounty
  - backend-scan
  - security-scan
  - waf-bypass
  - jwt
  - graphql
  - penetration-test
  - token-hunter
  - recon
  - fuzzer
  - exploit
  - brute
  - extract
  - mass
  - burp
  - reverse-engineering
  - ctf
  - exploit-db
  - explore
  - strings
  - pe
  - shellcode
---

# Backend Vulnerability Scanner + RE + CTF — Sistema Completo Integrado v2.1

Sistema integrado de testes de vulnerabilidade backend com **27 modulos** e **35 comandos slash**. Integrado com **CustomBurp Suite** (proxy, scanner, intruder, repeater, decoder). Inclui base de exploits, engenharia reversa e assistencia CTF.

> **v2.1**: Todos os 27 modulos funcional, integrações atualizadas com toolkit v2.1, paths corrigidos para skills em `.config/opencode/skills/`.

## 🚀 INSTALACAO

```bash
cd C:\Users\devel\.config\opencode\skills\backend-vuln-scanner
python setup.py
```

Ou manualmente:
```bash
pip install requests urllib3 cryptography selenium webdriver-manager flask
```

## 📍 Localização dos Módulos

```
C:\Users\devel\.config\opencode\skills\backend-vuln-scanner\
├── integration.py              # 35 comandos slash unificados
├── vuln_scanner.py             # SQLi, XSS, SSRF, LFI, RCE, IDOR, CSRF
├── complete_scanner.py         # Pipeline 6 fases unificado
├── token_hunter.py             # Browser token extraction (Selenium)
├── jwt_analyzer.py             # JWT analysis + brute force secrets
├── graphql_scanner.py          # GraphQL endpoints + introspection
├── framework_scanner.py        # Ruby on Rails + Next.js specific tests
├── waf_bypass.py               # DNS rebinding, IPv6, timing attacks
├── oauth_scanner.py            # OAuth/OpenID detection
├── web_crawler.py              # Crawler web recursivo
├── header_scanner.py           # Security headers analysis (score 0-100)
├── directory_buster.py         # 370+ paths sensitive files
├── cors_scanner.py             # CORS misconfiguration testing
├── parameter_fuzzer.py         # SQLi/XSS/LFI/SSRF parameter fuzzing
├── exploit_executor.py         # Automated exploitation
├── brute_force.py              # Login brute force, JWT secret crack
├── subdomain_enum.py           # DNS brute force + crt.sh passive recon
├── data_extractor.py           # SQLi data dump, LFI file extraction
├── mass_scanner.py             # Multi-target orchestration
├── burp_bridge.py              # Integracao com CustomBurp Suite
├── darkweb_search.py           # Dark web search via Ahmia/DuckDuckGo
├── virus_scanner.py            # Malware scanning (URLScan.io + VirusTotal)
├── onion_resolver.py           # .onion address validation
├── tor_search.py               # Tor search via public gateways
├── exploit_database.py         # Exploit DB (DeCSS, EternalBlue, Stuxnet)
├── reverse_engineering.py      # PE analysis, string extraction, shellcode
├── ctf_helper.py               # CTF helpers (pattern, ROP, encode/decode)
└── design_analyzer.py          # UI/UX security analysis
```

## 📋 COMANDOS SLASH (35)

### Scans & Reconhecimento
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/vuln_quick <dominio>` | Scan rapido (recon + WAF + framework) | vuln_scanner |
| `/vuln_scan <dominio>` | Scan completo todas as fases | complete_scanner |
| `/vuln_list` | Lista scans anteriores | - |
| `/vuln_status` | Status do sistema | - |
| `/vuln_help` | Ajuda completa | - |
| `/subdomain <dominio>` | Enumera subdominios (DNS brute + crt.sh) | subdomain_enum |
| `/crawler <dominio>` | Crawler web recursivo | web_crawler |
| `/headers <dominio>` | Analisa headers de seguranca (score 0-100) | header_scanner |
| `/buster <dominio>` | Directory/file buster (370+ paths) | directory_buster |
| `/cors <dominio>` | Testa configuracao CORS | cors_scanner |
| `/fuzz <dominio>` | Fuzza parametros (SQLi, XSS, LFI, SSRF) | parameter_fuzzer |

### JWT & Tokens
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/jwt_hunt <dominio>` | Captura tokens via browser (Selenium) | token_hunter |
| `/jwt_hunt <dominio> --email <e> --pass <p>` | Login automatico + captura | token_hunter |
| `/jwt_hunt <dominio> --manual` | Login manual interativo | token_hunter |
| `/jwt_analyze <dominio>` | Analisa JWT encontrado | jwt_analyzer |
| `/jwt_analyze <dominio> --token <tok>` | Analisa token especifico | jwt_analyzer |

### GraphQL & Framework
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/graphql_scan <dominio>` | Scan GraphQL endpoints | graphql_scanner |
| `/vuln_scan <dominio>` | Testes specficos do framework | framework_scanner |

### Exploit & Brute Force
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/exploit <dominio> --report arquivo.json` | Explora vulns encontradas | exploit_executor |
| `/exploit <dominio> --token eyJ...` | Usa token JWT no exploit | exploit_executor |
| `/brute <dominio>` | Brute force login + JWT + diretorios | brute_force |
| `/brute <dominio> --token eyJ...` | So testa JWT secret | brute_force |
| `/brute <dominio> --passwords lista.txt` | Wordlist customizada | brute_force |
| `/extract <dominio> --report arquivo.json` | Extrai dados de vulns | data_extractor |
| `/mass t1.com t2.com` | Scan multi-alvo completo | mass_scanner |

### Burp Suite
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/burp_start` | Inicia CustomBurp (proxy + web UI) | burp_bridge |
| `/burp_stop` | Para CustomBurp | burp_bridge |
| `/burp_status` | Status do Burp (requests, issues) | burp_bridge |
| `/burp_generate_ca` | Gera certificado CA para HTTPS | burp_bridge |
| `/burp_scanner <dominio>` | Scan rapido via Burp proxy | burp_bridge |

### Dark Web & OSINT
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/darkweb <query>` | Busca em sites .onion (Ahmia) | darkweb_search |
| `/darkweb <query> --scan` | Busca + scan de seguranca | darkweb_search |
| `/darkweb-safe` | Lista URLs .onion seguras conhecidas | darkweb_search |
| `/virus-scan <url|file>` | Scan de virus/malware (URLScan.io) | virus_scanner |
| `/onion-resolve <address>` | Resolve e valida endereco .onion | onion_resolver |
| `/tor-search <query>` | Busca dark web via gateways publicos | tor_search |
| `/tor-known` | Lista URLs .onion conhecidas | tor_search |
| `/tor-check <url.onion>` | Verifica acessibilidade | tor_search |

### Exploit Database (NOVO)
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/exploit-db <query>` | Busca exploits (DeCSS, EternalBlue, Stuxnet...) | exploit_database |
| `/exploit-db <query> -c network_exploit` | Filtra por categoria | exploit_database |
| `/exploit-db-list` | Lista todas as entradas e tecnicas RE | exploit_database |

### Reverse Engineering (NOVO)
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/explore <arquivo>` | Analisa PE + extrai strings/urls/chaves/IPs | reverse_engineering |
| `/explore <arquivo> --strings` | Somente strings | reverse_engineering |
| `/explore <arquivo> --urls` | Somente URLs | reverse_engineering |
| `/explore <arquivo> --keys` | Somente chaves/API keys | reverse_engineering |
| `/explore <arquivo> --ips` | Somente IPs | reverse_engineering |
| `/explore <arquivo> --pe` | Somente analise PE headers | reverse_engineering |
| `/strings <arquivo>` | Extrai strings de binario | reverse_engineering |
| `/pe <arquivo>` | Analisa headers PE (secoes, imports, etc) | reverse_engineering |
| `/hash <arquivo>` | Calcula MD5/SHA1/SHA256 | reverse_engineering |
| `/shellcode <template>` | Retorna shellcode (x86/x64) | reverse_engineering |
| `/shellcode-list` | Lista templates disponiveis | reverse_engineering |

### CTF Helper (NOVO)
| Comando | Descricao | Modulo |
|---------|-----------|--------|
| `/ctf pattern_create <len>` | Gera padrao ciclico para offset | ctf_helper |
| `/ctf pattern_offset <value>` | Encontra offset no padrao | ctf_helper |
| `/ctf rop_x86 [target_func]` | ROP chain x86 | ctf_helper |
| `/ctf rop_x64 [target_func]` | ROP chain x64 | ctf_helper |
| `/ctf encode <sc> <format>` | Codifica shellcode (c/python/hex/base64/js) | ctf_helper |
| `/ctf decode <encoded> <format>` | Decodifica shellcode | ctf_helper |
| `/ctf template <nome>` | Mostra template de exploit | ctf_helper |
| `/ctf-templates` | Lista templates disponiveis | ctf_helper |

## 🔄 FLUXO COMPLETO DE PENTEST

```
1. RECONHECIMENTO
   /vuln_quick target.com      → IP, headers, tecnologias, WAF
   /subdomain target.com       → Subdominios ativos
   /crawler target.com         → Paginas e endpoints escondidos

2. TESTES DE VULNERABILIDADE
   /vuln_scan target.com       → SQLi, XSS, SSRF, LFI, RCE, IDOR, CSRF
   /headers target.com         → Headers de seguranca (score 0-100)
   /buster target.com          → 370+ paths sensíveis
   /cors target.com            → CORS misconfig
   /fuzz target.com            → Fuzzer de parametros

3. CAPTURA DE CREDENCIAIS
   /jwt_hunt target.com        → Tokens do browser (cookies, localStorage, rede)
   /jwt_analyze target.com     → Analisa JWT (alg confusion, weak secrets)
   /brute target.com           → Brute force em login + JWT

4. EXPLOITACAO
   /exploit target.com --report scan_result.json  → Explora vulns encontradas
   /extract target.com --report scan_result.json  → Extrai dados (SQLi dump, arquivos)

5. BURP SUITE
   /burp_start                 → Inicia proxy + web UI
   /burp_scanner target.com    → Scan via proxy
   Web UI: http://localhost:4000
   Proxy: http://127.0.0.1:8080
```

## 🛠️ MODULOS DISPONIVEIS (27)

```
✓ vuln_scanner.py          — SQLi, XSS, SSRF, LFI, RCE, IDOR, CSRF
✓ complete_scanner.py      — Pipeline 6 fases unificado
✓ token_hunter.py          — Browser token extraction (Selenium)
✓ jwt_analyzer.py          — JWT analysis + brute force secrets
✓ graphql_scanner.py       — GraphQL endpoints + introspection
✓ framework_scanner.py     — Ruby on Rails + Next.js specific tests
✓ waf_bypass.py            — DNS rebinding, IPv6, timing attacks
✓ oauth_scanner.py         — OAuth/OpenID detection
✓ web_crawler.py           — Crawler web recursivo
✓ header_scanner.py        — Security headers analysis (score 0-100)
✓ directory_buster.py      — 370+ paths sensitive files
✓ cors_scanner.py          — CORS misconfiguration testing
✓ parameter_fuzzer.py      — SQLi/XSS/LFI/SSRF parameter fuzzing
✓ exploit_executor.py      — Automated exploitation (SQLi dump, LFI read, JWT forge)
✓ brute_force.py           — Login brute force, JWT secret crack, API key test
✓ subdomain_enum.py        — DNS brute force + crt.sh passive recon
✓ data_extractor.py        — SQLi data dump, LFI file extraction, JWT claims
✓ mass_scanner.py          — Multi-target orchestration
✓ burp_bridge.py           — Integracao com CustomBurp Suite
✓ integration.py           — 35 comandos slash unificados
✓ darkweb_search.py        — Dark web search via Ahmia/DuckDuckGo
✓ virus_scanner.py         — Malware scanning (URLScan.io + VirusTotal)
✓ onion_resolver.py        — .onion address validation and health
✓ tor_search.py            — Tor search via public gateways (no local Tor)
✓ exploit_database.py      — Exploit DB (DeCSS, EternalBlue, Stuxnet, CTF techniques)
✓ reverse_engineering.py   — PE analysis, string extraction, shellcode templates
✓ ctf_helper.py            — CTF helpers (pattern, ROP, format string, encode/decode)
```

## 🔗 CustomBurp Suite Integrado

Local: `C:\Users\devel\tools\burpsuite-custom\`

Componentes:
| Componente | Funcao |
|------------|--------|
| **Proxy** | HTTP/HTTPS transparente com CA certs dinamicos |
| **Scanner** | Detecao automatica de vulns (XSS, SQLi, SSRF, LFI, etc) |
| **Intruder** | Ataques com payloads (Sniper, Battering Ram, Pitchfork, Cluster Bomb) |
| **Repeater** | Envio manual de requests HTTP |
| **Decoder** | Codificacoes (Base64, URL, Hex, ROT13, JSON, SQL) |
| **Comparer** | Comparacao de respostas |
| **Sequencer** | Analise de tokens (entropia) |
| **Collaborator** | Out-of-band detection (DNS/HTTP callbacks) |
| **Logger** | Log de requests/responses |
| **Alerts** | Sistema de alertas e notificacoes |

URLs:
- Proxy: http://127.0.0.1:8080
- Web UI: http://localhost:4000
- API: http://localhost:4000/api/

## 📊 SAIDA DOS RESULTADOS

```
C:\Users\devel\hardware-bridge\scan_results\
├── auto_DOMINIO_TIMESTAMP.json          # Scans rapidos
├── integration.log                       # Log do sistema
├── complete_scan_DOMINIO_TIMESTAMP.json  # Scan completo
├── jwt_analysis_DOMINIO_TIMESTAMP.json   # Analisis JWT
├── *_crawler.json                        # Crawler results
├── *_headers.json                        # Header analysis
├── *_buster.json                         # Directory buster
├── *_cors.json                           # CORS scan
├── *_fuzz.json                           # Parameter fuzz
├── *_exploit.json                        # Exploit results
├── *_brute.json                          # Brute force results
├── *_subdomains.json                     # Subdomain enum
├── *_extract.json                        # Data extraction
├── mass_*_TIMESTAMP.json                 # Mass scan per-target
└── mass_scan_consolidated_TIMESTAMP.json # Mass scan consolidated
```

DB Burp: `C:\Users\devel\custom_burp.db`

## ⚙️ CONFIGURACAO

### Dependencias
- python >= 3.8
- requests, urllib3, cryptography
- selenium, webdriver-manager (para token hunter)
- flask (para web UI do Burp)

### Uso Avancado

Via linha de comando:
```bash
# Scan rapido
python integration.py /vuln_quick target.com

# Token hunt com login automatico
python integration.py /jwt_hunt target.com --email user@mail.com --pass secret123

# Token hunt com login manual
python integration.py /jwt_hunt target.com --manual

# Analisar JWT
python integration.py /jwt_analyze target.com

# Explorar vulnerabilidades
python integration.py /exploit target.com --report scan_result.json

# Extrair dados
python integration.py /extract target.com --report scan_result.json

# Brute force
python integration.py /brute target.com
python integration.py /brute target.com --token eyJhbGci...

# Subdomain enum
python integration.py /subdomain target.com

# Mass scan
python integration.py /mass target1.com target2.com target3.com

# Burp Suite
python integration.py /burp_start
python integration.py /burp_status
python integration.py /burp_scanner target.com
python integration.py /burp_generate_ca
```

Via Python:
```python
from integration import ToolManager, CommandHandler
from complete_scanner import CompleteScanner
from jwt_analyzer import JWTAnalyzer
from token_hunter import TokenHunter
from exploit_executor import ExploitExecutor
from brute_force import BruteForce
from data_extractor import DataExtractor
from subdomain_enum import SubdomainEnumerator
from mass_scanner import MassScanner
from burp_bridge import BurpBridge

# Scan completo
scanner = CompleteScanner("target.com")
results = scanner.run_full_scan()

# Token hunt com Selenium
hunter = TokenHunter("target.com", headless=True)
tokens = hunter.run(email="user@mail.com", password="secret")

# JWT analysis
analyzer = JWTAnalyzer("target.com")
result = analyzer.run_full_analysis()

# Exploit executor
executor = ExploitExecutor("target.com")
result = executor.run_all_exploits(vuln_report)

# Data extraction
extractor = DataExtractor("target.com")
result = extractor.run_full_extraction(vuln_report)

# Mass scan
mass = MassScanner(["target1.com", "target2.com"])
result = mass.run_mass_scan()

# Burp Bridge
bridge = BurpBridge()
bridge.start_burp()
status = bridge.get_burp_status()
```

## ✅ STATUS DO SISTEMA

Todos os 27 modulos estao 100% funcionais e testados:

| Modulo | Detecao | Análise | Exploracao | RE/CTF | Status |
|--------|---------|---------|------------|--------|--------|
| Reconhecimento | ✅ | ✅ | - | - | ✅ |
| WAF Detection | ✅ | ✅ | - | - | ✅ |
| JWT Analysis | ✅ | ✅ | ✅ | - | ✅ |
| Token Hunter | ✅ | ✅ | ✅ | - | ✅ |
| GraphQL Scan | ✅ | ✅ | - | - | ✅ |
| Framework Tests | ✅ | ✅ | - | - | ✅ |
| Header Scanner | ✅ | ✅ | - | - | ✅ |
| Directory Buster | ✅ | ✅ | ✅ | - | ✅ |
| CORS Scanner | ✅ | ✅ | - | - | ✅ |
| Parameter Fuzzer | ✅ | ✅ | ✅ | - | ✅ |
| Exploit Executor | - | ✅ | ✅ | - | ✅ |
| Brute Force | - | ✅ | ✅ | - | ✅ |
| Subdomain Enum | ✅ | ✅ | - | - | ✅ |
| Data Extractor | - | ✅ | ✅ | - | ✅ |
| Mass Scanner | ✅ | ✅ | ✅ | - | ✅ |
| Web Crawler | ✅ | ✅ | - | - | ✅ |
| OAuth Scanner | ✅ | ✅ | - | - | ✅ |
| Vuln Scanner | ✅ | ✅ | ✅ | - | ✅ |
| Burp Bridge | ✅ | ✅ | ✅ | - | ✅ |
| Dark Web Search | ✅ | ✅ | - | - | ✅ |
| Virus Scanner | ✅ | ✅ | - | - | ✅ |
| Onion Resolver | ✅ | ✅ | - | - | ✅ |
| Tor Search | ✅ | ✅ | - | - | ✅ |
| **Exploit Database** | - | ✅ | ✅ | - | ✅ |
| **Reverse Engineering** | - | ✅ | - | ✅ | ✅ |
| **CTF Helper** | - | ✅ | - | ✅ | ✅ |
| Integration | ✅ | ✅ | ✅ | - | ✅ |

---

## 🔄 NOVO: Exploit Database + RE + CTF

### Exploit Database (`/exploit-db`)
Base de dados com exploits e técnicas catalogados:
- **DRM Reversing**: DeCSS, FairPlay/iPhone Activation
- **ICS Attack**: Stuxnet (SMB, Print Spooler, USB LNK)
- **Network Exploits**: EternalBlue, EternalRomance, EternalChampion, EternalSynergy
- **Backdoors**: DoublePulsar
- **CTF Techniques**: Buffer Overflow, Ret2libc, ROP Chain, Format String, Shellcode Injection

### Reverse Engineering (`/explore`, `/strings`, `/pe`)
- Extração de strings (ASCII + UTF-16)
- Extração de URLs, IPs, chaves/API keys
- Análise de headers PE (seções, imports, exports)
- Cálculo de hashes (MD5/SHA1/SHA256)
- Templates de shellcode (x86/x64, exec/bind/reverse TCP)

### CTF Helper (`/ctf`)
- Padrão cíclico (Metasploit-compatible)
- ROP chains (x86 e x64)
- Format string payloads
- Codificação/decodificação de shellcode (C, Python, Hex, Base64, JS, Ruby)
- Templates de exploit prontos (buffer overflow, ROP, format string)
