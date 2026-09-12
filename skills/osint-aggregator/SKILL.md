---
name: osint-aggregator
description: Ferramenta OSINT (Open Source Intelligence) para coleta de inteligencia de fontes publicas. WHOIS, DNS enumeration, subdominios, emails, e detecção de brechas. V2.1: multiple source support, JSON export.
aliases:
  - osint
  - recon
  - whois
  - subdomain
  - email-hunter
  - dns-recon
---

# OSINT Aggregator v2.1 — Open Source Intelligence

Ferramenta de coleta de inteligencia de fontes aberturas para reconnaissance de alvos.

> **v2.1**: Suporte a múltiplas sources via flag --sources, export JSON, detectao automatica de headers de seguranca.

## Localizacao

```
C:\Users\devel\tools\osint-aggregator\osint_aggregator.py
```

## Instalacao

```bash
pip install python-whois aiohttp
```

## Comandos

```bash
# Coletar dados de um dominio (todas as sources)
python osint_aggregator.py example.com

# Sources especificas
python osint_aggregator.py example.com --sources whois dns subdomains emails
python osint_aggregator.py example.com --sources crtsh
python osint_aggregator.py example.com --json

# Exportar para arquivo
python osint_aggregator.py example.com --export report.json

# Listar sources disponiveis
python osint_aggregator.py --list-sources

# Batch mode
python osint_aggregator.py --file domains.txt
```

## Sources Disponiveis

| Source | Descricao | API |
|--------|-----------|-----|
| `whois` | Registracao do dominio, data de criacao, organizer | python-whois |
| `dns` | Records A, NS, MX, TXT, CNAME + reverse DNS | dnspython/subprocess |
| `subdomains` | Enumeracao via crt.sh + DNS brute force | crt.sh API |
| `emails` | Emails encontrados nas paginas web + padroes comuns | HTTP parsing |
| `breaches` | Checagem contra breaches conhecidos (HaveIBeenPwned) | API |
| `crtsh` | Certificate transparency logs | crt.sh API |

## Saida JSON

```json
{
  "target": "example.com",
  "collected_at": "2024-01-15T10:30:00Z",
  "whois": {
    "registrar": "GoDaddy",
    "created_date": "2020-01-01",
    "expired_date": "2025-01-01",
    "org": "Example Corp"
  },
  "dns": {
    "A": ["93.184.216.34"],
    "NS": ["ns1.example.com"],
    "MX": ["mail.example.com"],
    "TXT": ["v=spf1 ..."]
  },
  "subdomains": ["www", "api", "admin", "staging"],
  "emails": ["contact@example.com", "admin@example.com"],
  "security_headers": {
    "strict-transport-security": "max-age=31536000",
    "x-frame-options": "DENY"
  }
}
```

## Uso via Python

```python
from tools.osint_aggregator.osint_aggregator import OSINTAggregator

engine = OSINTAggregator()
result = engine.collect("example.com", sources=["whois", "dns", "subdomains"])
print(result["summary"])
```

---

**OSINT Aggregator v2.1 — Intelligence gathered, patterns identified.** 🐀
