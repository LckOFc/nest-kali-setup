# Backend Vulnerability Scanner + DarkWeb + Image Thinking

Sistema completo de testes de segurança, OSINT dark web e análise de imagens integrado ao opencode.

## 📦 Módulos Registrados no opencode.jsonc

| Skill | Comandos | Status |
|-------|----------|--------|
| **backend-vuln-scanner** | /vuln_scan, /vuln_quick, /vuln_list, /vuln_status | ✅ |
| **darkweb-tools** | /darkweb, /darkweb-safe, /virus-scan, /onion-resolve, /osint | ✅ |
| **image-thinking** | /think, /recreate, /analyze-design | ✅ |
| **burp-suite** | /burp_start, /burp_stop, /burp_status, /burp_generate_ca, /burp_scanner | ✅ |

## 🚀 Comandos Disponíveis

### Backend Scanning
```
/vuln_quick <dominio>     # Scan rápido (30s)
/vuln_scan <dominio>      # Scan completo
/vuln_list                # Lista resultados
/vuln_status              # Status do sistema
```

### DarkWeb / OSINT
```
/darkweb <query>          # Busca .onion (Ahmia)
/darkweb <query> --scan   # Busca + segurança
/darkweb-safe             # URLs seguras conhecidas
/virus-scan <url|file>    # Scan vírus/malware
/onion-resolve <addr>     # Valida endereço .onion
/osint <dominio>          # WHOIS, DNS, subdomains
```

### Image Thinking
```
/think <imagem>           # Analisa + recria UI
/recreate <imagem>        # Recria HTML/Luau
/analyze-design <html>    # Análise estrutura
```

### Burp Suite
```
/burp_start               # Inicia proxy+UI
/burp_stop                # Para Burp
/burp_status              # Status
/burp_generate_ca         # Gera certificado
/burp_scanner <dominio>   # Scan via proxy
```

## 📂 Arquivos do Sistema

```
opencode.jsonc
├── skills.backend-vuln-scanner.commands
├── skills.darkweb-tools.commands  
├── skills.image-thinking.commands
└── skills.burp-suite.commands

skills/backend-vuln-scanner/
├── integration.py          # 23 comandos slash
├── darkweb_search.py       # Busca .onion
├── virus_scanner.py        # Validação segurança
├── onion_resolver.py       # Resolução endereços
├── vuln_scanner.py         # SQLi, XSS, SSRF
├── exploit_executor.py     # Exploração
├── brute_force.py          # Força bruta
└── ... (19 módulos)

opencode/image_thinking_system.js  # Pipeline thinking
opencode/ui_recreator.py           # Recriação UI
```

## ✅ Testado e Funcional

```bash
# Status
python integration.py /vuln_status
# Modules: 23

# DarkWeb
python integration.py /darkweb-safe
python integration.py /virus-scan https://example.com

# Image
node -e "require('./image_thinking_system.js')"
```

---

**Total: 23 módulos Python + 4 skills registrados no opencode.jsonc**
