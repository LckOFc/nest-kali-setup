# Backend Vulnerability Scanner + CustomBurp Suite

Sistema completo de testes de seguranca backend integrado com CustomBurp Suite.

## 🔧 Instalacao

```bash
cd C:\Users\devel\.config\opencode\skills\backend-vuln-scanner
python setup.py
```

Ou manualmente:
```bash
pip install requests urllib3 cryptography selenium webdriver-manager flask
```

## 🚀 Uso Rapido

```bash
# Scan rapido
python integration.py /vuln_quick example.com

# Token hunt (browser)
python integration.py /jwt_hunt example.com

# Analisar JWT
python integration.py /jwt_analyze example.com

# Explorar vulnerabilidades
python integration.py /exploit example.com --report scan_result.json

# Brute force
python integration.py /brute example.com

# Subdominios
python integration.py /subdomain example.com

# Burp Suite
python integration.py /burp_start
python integration.py /burp_status
python integration.py /burp_scanner example.com
```

## 📦 Modulos (20)

| Modulo | Funcao |
|--------|--------|
| vuln_scanner | SQLi, XSS, SSRF, LFI, RCE, IDOR, CSRF |
| complete_scanner | Pipeline 6 fases |
| token_hunter | Captura tokens via Selenium |
| jwt_analyzer | Analisa e explora JWT |
| graphql_scanner | Scan GraphQL endpoints |
| framework_scanner | Tests Rails/Next.js |
| waf_bypass | DNS rebinding, IPv6, timing |
| oauth_scanner | OAuth/OpenID detection |
| web_crawler | Crawler web recursivo |
| header_scanner | Security headers (score 0-100) |
| directory_buster | 370+ paths sensíveis |
| cors_scanner | CORS misconfiguration |
| parameter_fuzzer | SQLi/XSS/LFI/SSRF fuzzing |
| exploit_executor | Explora vulnerabilidades |
| brute_force | Brute force login/JWT/API |
| subdomain_enum | Enumeracao subdominios |
| data_extractor | Extrai dados de SQLi/LFI/JWT |
| mass_scanner | Multi-alvo orchestration |
| burp_bridge | Integracao com CustomBurp |
| integration | 25 comandos slash |

## 🔗 CustomBurp Suite

Local: `C:\Users\devel\tools\burpsuite-custom\`

Componentes:
- **Proxy** — HTTP/HTTPS com CA certs dinamicos
- **Scanner** — Detecao automatica de vulnerabilidades
- **Intruder** — Ataques com payloads (Sniper, Battering Ram, Pitchfork, Cluster Bomb)
- **Repeater** — Envio manual de requests
- **Decoder** — Codificacoes (Base64, URL, Hex, ROT13, etc)
- **Comparer** — Comparacao de respostas
- **Sequencer** — Analise de tokens
- **Collaborator** — Out-of-band detection
- **Logger** — Log de requests/responses
- **Alerts** — Sistema de alertas

URLs:
- Proxy: http://127.0.0.1:8080
- Web UI: http://localhost:4000
- API: http://localhost:4000/api/

## 📊 Resultados

Todos os resultados sao salvos em:
`C:\Users\devel\hardware-bridge\scan_results\`

## 📝 Comandos Slash (25)

```
/vuln_quick /vuln_scan /vuln_list /vuln_status /vuln_help
/jwt_hunt /jwt_analyze
/graphql_scan
/crawler
/headers
/buster
/cors
/fuzz
/exploit
/brute
/subdomain
/extract
/mass
/burp_start /burp_stop /burp_status /burp_generate_ca /burp_scanner
```
