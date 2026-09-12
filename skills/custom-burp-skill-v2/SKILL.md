"""
CustomBurp Skill — Skill Definition para opencode
Version: 2.0
Tipo: CLI-only (sem UI web)
Uso: Integração direta com agentes opencode via comandos slash
"""

---
name: custom-burp-skill
description: Sistema completo de testes de seguranca backend integrado ao opencode. Proxy HTTP/HTTPS, scanner de vulnerabilidades, intruder com payloads, repeater, decoder, logger. Versao skill — sem UI web, uso via comandos slash.
aliases:
  - burp
  - burpsuite
  - proxy
  - scanner
  - intruder
  - repeater
  - decoder
  - pentest
  - bug-bounty
  - security-test
---

# CustomBurp Skill v2 — Sistema de Testes de Seguranca

Engine CLI-only integrada ao opencode para testes de seguranca backend.

## Instalacao

```bash
cd C:\Users\devel\tools\burpsuite-v2
pip install aiohttp cryptography
```

## Comandos Slash Disponiveis

### /burp status
Mostra status do sistema (proxy, banco, issues).

**Exemplo:**
```
/burp status
```

### /burp proxy_start [porta]
Inicia proxy HTTP/HTTPS para interceptacao de trafego.

**Exemplo:**
```
/burp proxy_start 8080
```

### /burp proxy_stop
Para o proxy.

### /burp proxy_status
Mostra status do proxy.

### /burp proxy_ca
Gera certificado CA para interceptacao HTTPS.

**Exemplo:**
```
/burp proxy_ca
```
Depois instale o certificado no navegador do usuario para capturar HTTPS.

### /burp logger [host] [limite]
Lista requisicoes capturadas.

**Exemplo:**
```
/burp logger example.com 50
/burp logger
```

### /burp logger_get <request_id>
Busca requisicao especifica pelo ID.

### /burp logger_clear
Limpa todo o historico de logs.

### /burp logger_export
Exporta todas as requisicoes como JSON.

### /burp scan <dominio> [caminhos...]
Executa scan de vulnerabilidades ativo.

**Exemplo:**
```
/burp scan example.com
/burp scan example.com /login /api /admin
```

**Testes automaticos:**
- XSS Refletido
- SQL Injection
- SSRF
- Path Traversal
- Command Injection
- Headers de seguranca
- CORS misconfig

### /burp issues [severidade]
Lista vulnerabilidades detectadas.

**Exemplo:**
```
/burp issues
/burp issues Critical
/burp issues High
```

### /burp issues_clear
Remove todas as issues do banco.

### /burp repeater <metodo> <url> [corpo]
Envia request HTTP manual.

**Exemplo:**
```
/burp repeater GET https://example.com/api/users
/burp repeater POST https://example.com/api/login '{"user":"admin","pass":"test"}'
/burp repeater POST https://example.com/api/test body=data here
```

### /burp history [limite]
Mostra historico de requests do repeater.

### /burp intruder <url> <payloads> [modo]
Ataque com payloads.

**Modos:**
- `sniper` — um payload por vez (padrao)
- `battering_ram` — mesmo payload em todas posicoes
- `pitchfork` — sets paralelos
- `cluster_bomb` — todas combinacoes

**Exemplo:**
```
/burp intruder https://example.com/login "admin,root,test,guest" sniper
/burp intruder https://example.com/api "1,2,3,4,5" cluster_bomb
```

### /burp decode <operacao> <dados>
Decodifica/transforma dados.

**Operacoes:**
- `url_decode` / `url_encode`
- `base64_decode` / `base64_encode`
- `md5` / `sha256`
- `hex_encode` / `hex_decode`
- `rot13`
- `json_format`
- `jwt_decode`

**Exemplo:**
```
/burp decode base64_decode SGVsbG8gV29ybGQ=
/burp decode md5 hello
/burp decode url_decode %3Cscript%3Ealert(1)%3C%2Fscript%3E
/burp decode jwt_decode eyJhbGciOiJIUzI1NiJ9...
```

### /burp operations
Lista operacoes disponiveis no decoder.

### /burp target <host> [porta]
Adiciona host ao escopo.

### /burp targets
Lista hosts no escopo.

### /burp collaborator_status
Status do servidor OAST (em desenvolvimento).

## Fluxo de Trabalho Típico

```
1. INICIAR
   /burp proxy_start
   /burp proxy_ca
   → Instale o CA cert no navegador do usuario

2. CAPTURAR
   → Usuario navega com proxy configurado (127.0.0.1:8080)
   /burp logger          → Veja requests capturados

3. REPETIR
   /burp repeater GET https://alvo.com/api/users
   /burp history         → Veja resultado

4. SCANNAR
   /burp scan alvo.com
   /burp issues          → Veja vulns encontradas

5. INTRUDER
   /burp intruder https://alvo.com/login "admin,password,123456" sniper

6. DECODER
   /burp decode base64_decode <token>
   /burp decode jwt_decode <token>
```

## Integragao com Agentes

Os agentes opencode (Sombra, Kuroko, ratman4080) podem chamar o Burp Skill diretamente:

```python
from tools.burpsuite_v2.skill import BurpSkill

engine = BurpSkill()

# Status
status = engine.cmd_status()

# Proxy
engine.cmd_proxy_start(8080)
engine.cmd_proxy_generate_ca()

# Scanner
results = await engine.cmd_scanner_run("alvo.com")

# Repeater
resp = await engine.cmd_repeater_send("GET", "https://alvo.com/api/users")

# Intruder
attack = await engine.cmd_intruder_start(
    request_data={"method": "POST", "url": "https://alvo.com/login", "body": "user=[PAYLOAD]"},
    payloads=["admin", "root", "test"],
    mode="sniper"
)

# Decoder
result = engine.cmd_decoder_transform("base64_decode", "SGVsbG8=")
```

## Banco de Dados

SQLite em: `C:\Users\devel\tools\burpsuite-v2\custom_burp.db`

Tabelas:
- `requests` — Requisicoes capturadas
- `responses` — Respostas HTTP
- `issues` — Vulnerabilidades detectadas
- `intruder_results` — Resultados de ataques
- `collab_interactions` — Intericiones OAST

## Dependencias

```
aiohttp>=3.9.0
cryptography>=41.0.0
```

Install:
```bash
pip install aiohttp cryptography
```
