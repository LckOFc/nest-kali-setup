---
name: payload-manager
description: Gerenciador completo de payloads de ataque. 18 categorias, 119+ payloads prontos (SQLi, XSS, LFI, SSRF, RCE, JWT, XXE, etc). Codificacao, armazenamento customizado, geracao de wordlist.
aliases:
  - payload
  - payloads
  - fuzzer
  - waf-bypass
  - encode
---

# Payload Manager v1 — Gerenciador de Payloads de Ataque

Biblioteca completa de payloads de ataque com codificacoes WAF bypass, armazenamento customizado e geracao de wordlists.

## Localizacao

```
C:\Users\devel\tools\payload-manager\payload_manager.py
```

## Categorias (18, 119+ payloads)

| Categoria | Qtd | Descricao |
|-----------|-----|-----------|
| `sqli` | 32 | SQL Injection (error, blind, union, time) |
| `xss` | 26 | Cross-Site Scripting (reflected, stored, encoded) |
| `lfi` | 17 | Local File Inclusion / Path Traversal |
| `ssrf` | 15 | Server-Side Request Forgery |
| `rce` | 10 | Remote Code Execution (PHP, JSP, Python, CMDI) |
| `auth` | 10 | Authentication Bypass |
| `upload` | 7 | Web Shells (PHP, ASP, JSP, Python, Ruby) |
| `ldap` | 7 | LDAP Injection |
| `xpath` | 6 | XPath Injection |
| `xxe` | 5 | XML External Entity |
| `nosql` | 6 | NoSQL Injection |
| `jwt` | 3 | JWT Attacks (alg:none, weak secret) |
| `deser` | 4 | Deserialization (Java, Python, PHP) |
| `redirect` | 7 | Open Redirect |
| `injection` | 3 | Header/General Injection |

## Comandos

```bash
# Listar categorias
python payload_manager.py --list-categories

# Listar payloads de uma categoria
python payload_manager.py --list sqli
python payload_manager.py --list xss

# Buscar subcategoria
python payload_manager.py --get sqli union

# Codificar payload
python payload_manager.py --encode url "<script>alert(1)</script>"
python payload_manager.py --encode base64 "payload"
python payload_manager.py --encode hex "<script>"

# Armazenar payload customizado
python payload_manager.py --store sqli custom "' OR '1'='1' --"

# Exportar
python payload_manager.py --export sqli

# Gerar wordlist combinatorial
python payload_manager.py --generate 3 6
```

## Metodo de Codificacao

```python
from tools.payload_manager.payload_manager import PayloadManager

mgr = PayloadManager()

# Codificar
encoded = mgr.encode_payload("<script>alert(1)</script>", "url")
# → "%3Cscript%3Ealert%281%29%3C%2Fscript%3E"

# Codificar todos de uma categoria
payloads = mgr.get_payloads("sqli")
encoded_all = mgr.encode_all(payloads, "url_double")

# Armazenar custom
mgr.store_payload("sqli", "custom", "' OR '1'='1' --")

# Stats
stats = mgr.get_stats()
# → {'total_templates': 18, 'total_payloads': 119, 'by_category': {...}}
```

## Uso no Pentest

1. Escolher categoria: `--list sqli`
2. Copiar payload: `--get sqli union`
3. Codificar para bypass: `--encode url "<payload>"`
4. Armazenar para reuse: `--store <cat> <subcat> "<payload>"`
5. Exportar para arquivo: `--export <cat>`
