# Backend Vulnerability Scanner — Reference Card

## Quick Commands
```bash
# Scan
/vuln_quick <dominio>     # Rápido (30s)
/vuln_scan <dominio>      # Completo (6 fases)

# JWT
/jwt_hunt <dominio>       # Captura tokens (browser real)
/jwt_hunt <dominio> -e <email> -p <senha>  # Login auto
/jwt_analyze <dominio>    # Analisa JWT encontrado

# Exploração
/exploit <dominio> -r scan.json  # Explora vulnerabilidades
/extract <dominio> -r scan.json  # Extrai dados (SQLi dump, arquivos)
/brute <dominio>          # Força bruta (login + JWT)

# Recon
/crawler <dominio>        # Crawler web
/subdomain <dominio>      # Subdomínios
/headers <dominio>        # Headers de segurança
/buster <dominio>         # 370+ paths
/cors <dominio>           # CORS tests
/fuzz <dominio>           # SQLi/XSS/LFI/SSRF

# Burp Suite
/burp_start               # Inicia proxy + web UI
/burp_status              # Status
/burp_scanner <dominio>   # Scan via proxy
/burp_generate_ca         # Gera certificado CA

# Multi-alvo
/mass t1.com t2.com t3.com
```

## Fluxo de Ataque Completo
```
1. /vuln_quick target.com    → Recon + WAF
2. /buster target.com        → Descobre paths
3. /jwt_hunt target.com      → Captura tokens
4. /jwt_analyze target.com   → Analisa JWT
5. /exploit target.com -r scan.json  → Explora!
6. /extract target.com -r scan.json  → Extrai dados!
```

## Burp Suite URLs
- Proxy: http://127.0.0.1:8080
- Web UI: http://localhost:4000
- DB: C:\Users\devel\custom_burp.db

## Módulos (20)
vuln_scanner | complete_scanner | token_hunter | jwt_analyzer
graphql_scanner | framework_scanner | waf_bypass | oauth_scanner
web_crawler | header_scanner | directory_buster | cors_scanner
parameter_fuzzer | exploit_executor | brute_force | subdomain_enum
data_extractor | mass_scanner | burp_bridge | integration
