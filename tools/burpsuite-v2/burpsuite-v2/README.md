# CustomBurp Skill v2 — Integração Completa com opencode

## Resumo

Burp Suite v2 foi redesenhado como **skill CLI-only** para o opencode. Sem UI web, uso via linha de comando e integra diretamente com os agentes (Sombra, ratman4080, Kuroko).

---

## Estrutura de Arquivos

```
C:\Users\devel\tools\burpsuite-v2\
├── skill.py              # Engine principal (CLI-only, ~800 linhas)
├── custom_burp.db        # SQLite database (criado automaticamente)
├── ca.crt / ca.key       # CA certificate (gerado pelo comando proxy_ca)
├── log/
│   └── burp_skill.log    # Log de execucoes
└── requirements.txt      # aiohttp, cryptography

C:\Users\devel\.config\opencode\skills\custom-burp-skill-v2\
└── SKILL.md              # Definicao da skill para opencode
```

---

## Comandos Disponiveis

| Comando | Descricao |
|---------|-----------|
| `/burp status` | Status do sistema (proxy, DB, issues) |
| `/burp proxy_start [porta]` | Inicia proxy HTTP/HTTPS |
| `/burp proxy_stop` | Para proxy |
| `/burp proxy_status` | Status do proxy |
| `/burp proxy_ca` | Gera certificado CA |
| `/burp logger [host] [limite]` | Lista requisicoes capturadas |
| `/burp logger_get <id>` | Busca requisicao especifica |
| `/burp logger_clear` | Limpa historico |
| `/burp logger_export` | Exporta JSON |
| `/burp scan <dominio> [caminhos]` | Scan de vulnerabilidades |
| `/burp issues [severidade]` | Lista issues detectadas |
| `/burp issues_clear` | Limpa issues |
| `/burp repeater <method> <url> [headers] [body]` | Envia request HTTP |
| `/burp intruder <url> <payloads> [modo]` | Ataque com payloads |
| `/burp decode <operacao> <data>` | Decoder/Encoder |
| `/burp operations` | Lista operacoes do decoder |
| `/burp target <host> [port]` | Adiciona ao escopo |
| `/burp targets` | Lista escopo |
| `/burp help` | Ajuda completa |

---

## Operacoes do Decoder

- `url_decode` / `url_encode`
- `base64_decode` / `base64_encode`
- `md5` / `sha256`
- `hex_encode` / `hex_decode`
- `rot13`
- `json_format`
- `jwt_decode`

---

## Modos do Intruder

- `sniper` — um payload por vez
- `battering_ram` — mesmo payload em todas posicoes
- `pitchfork` — sets paralelos
- `cluster_bomb` — todas combinacoes

---

## Testes Realizados

```bash
# Status
python skill.py status
# ✅ OK - sistema inicializa, DB criado

# Decoder
python skill.py decode base64_encode "Hello World"
# ✅ OK - SGVsbG8gV29ybGQ=

python skill.py decode jwt_decode eyJhbGci...
# ✅ OK - header e payload decodificados

# Repeater
python skill.py repeater GET https://httpbin.org/get
# ✅ OK - 200, response body recebido

python skill.py repeater POST https://httpbin.org/post '{"token":"x"}' '{"data":"test"}'
# ✅ OK - POST enviado, response 200

# Scanner
python skill.py scan httpbin.org
# ✅ OK - 11 issues found (Missing Security Headers)

python skill.py issues
# ✅ OK - mostra issues no formato JSON

# Proxy
python skill.py proxy_start
# ✅ OK - proxy iniciado em 127.0.0.1:8080

python skill.py proxy_ca
# ✅ OK - CA certificate gerado

# Logger
python skill.py logger
# ✅ OK - requisicoes salvas no banco

python skill.py targets
# ✅ OK - hosts capturados listados
```

---

## Como Usar nos Agentes

### Via Python (dentro do agente)
```python
from tools.burpsuite_v2.skill import BurpSkill

engine = BurpSkill()

# Status
status = engine.status()

# Scanner
import asyncio
results = asyncio.run(engine.scan("alvo.com"))

# Repeater
result = asyncio.run(engine.repeater_send("GET", "https://alvo.com/api/users"))

# Intruder
attack = asyncio.run(engine.intruder_attack(
    request_data={"method": "POST", "url": "https://alvo.com/login", "body": "user=[PAYLOAD]"},
    payloads=["admin", "root", "test"],
    mode="sniper"
))

# Decoder
decoded = engine.decoder_transform("base64_decode", "SGVsbG8=")
```

### Via CLI (comando slash)
```
/burp status
/burp proxy_start
/burp scan alvo.com
/burp repeater GET https://alvo.com/api/users
/burp decode base64_decode SGVsbG8=
/burp intruder https://alvo.com/login "admin,root,test" sniper
```

---

## Integracao com opencode.jsonc

Adicione ao arquivo de configuracao:

```json
{
  "skills": {
    "custom-burp-skill-v2": {
      "enabled": true,
      "path": "file://C:/Users/devel/.config/opencode/skills/custom-burp-skill-v2/SKILL.md"
    }
  }
}
```

---

## Vantagens sobre Versao Anterior

| Aspecto | v1 (Web UI) | v2 (Skill CLI) |
|---------|-------------|----------------|
| UI Web | Flask + HTML | Nao precisa |
| Uso | Navegador | CLI + API Python |
| Integracao | API REST separada | Direto nos agentes |
| Startup | 2 servicos (proxy + web) | 1 processo |
| Recursos | 17 abas UI | 20+ comandos |
| Escalabilidade | Limitada pelo browser | Ilimitada |
| Uso em agentes | Precisa de URL | Import direto |

---

## Dependencias

```bash
pip install aiohttp cryptography
```

Ja instalado no sistema:
- aiohttp 3.14.3 ✅
- cryptography 50.0.1 ✅

---

## Arquivos Criados/Modificados

```
C:\Users\devel\tools\burpsuite-v2\skill.py          # NOVO - engine CLI (~800 linhas)
C:\Users\devel\.config\opencode\skills\custom-burp-skill-v2\SKILL.md  # NOVO - definicao da skill
```

---

## Próximos Passos

1. Integrar com comando slash `/burp` no opencode
2. Adicionar mais testes de vulnerabilidade ao scanner
3. Implementar OAST collaborator (DNS/HTTP callbacks)
4. Adicionar suporte a GraphQL scanning
5. Criar bridge com backend-vuln-scanner para escanear juntos
