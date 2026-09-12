# Skill: CustomBurp Suite — 100% Funcional

Ferramenta completa de testes de seguranca estilo Burp Suite, desenvolvida do zero em Python. **100% funcional** com todos os modulos do Burp Suite implementados.

## Localizacao

```
C:\Users\devel\tools\burpsuite-custom\
```

## Instalacao

```bash
cd C:\Users\devel\tools\burpsuite-custom
pip install -r requirements.txt
python main.py
```

Ou use o batch:
```bash
start.bat
```

## Uso Rapido

```bash
# Iniciar tudo
python main.py

# So UI web
python main.py --no-proxy

# Gerar CA cert para HTTPS
python main.py --generate-ca

# Portas customizadas
python main.py --proxy-port 8888 --web-port 5000
```

## Modulos Implementados (100%)

### 1. Proxy (Proxy Interceptador) ✅
- Interceptacao de trafego HTTP/HTTPS
- Tunelamento CONNECT para HTTPS
- Geracao automatica de certificado CA
- Fila de requisicoes para analise
- Configure navegador: `127.0.0.1:8080`

### 2. Repeater ✅
- Envio manual de requests HTTP/HTTPS
- GET, POST, PUT, DELETE, PATCH, HEAD
- Edicao de headers e body
- Historico de requests enviados

### 3. Intruder ✅
- Ataques de payload com 4 modos:
  - **Sniper**: 1 set de payloads
  - **Battering Ram**: todos positions usam mesmo set
  - **Pitchfork**: sets paralelos
  - **Cluster Bomb**: todas combinacoes
- Paralelizacao com threads configuraveis
- Analise de diferencas (tamanho, status, tempo)
- Destaque visual: verde=maior, vermelho=menor

### 4. Scanner ✅
- 10 tipos de vulnerabilidade:
  - XSS Refletido, SQLi, SSRF, Path Traversal
  - Command Injection, Hardcoded Creds
  - Info Disclosure, CORS misconfig
  - Cookies inseguros, Missing Security Headers
- Severity: Critical, High, Medium, Low

### 5. Decoder ✅
- URL encode/decode
- Base64 encode/decode
- HTML encode/decode
- MD5, SHA1, SHA256
- Hex encode/decode
- ROT13
- JSON format/minify
- SQL pretty print
- Detecao automatica de encoding

### 6. Comparer ✅
- Diff visual entre duas respostas
- Comparacao de status code, headers, body
- Unified diff com destaque de linhas alteradas
- Analise de diferencas de tamanho

### 7. Sequencer ✅
- Analise de entropia de Shannon
- Detecao de tokens previsiveis
- Uniqueness ratio
- Detecao de padroes (MD5, Base64, JWT, numericos)
- Severity based on entropy score

### 8. Logger ✅
- Registro centralizado de todas as requisicoes
- Busca e filtro por host, metodo, status, tags
- Exportacao JSON, CSV, HAR
- Envio direto para Repeater/Intruder

### 9. Target ✅
- Gerenciamento de escopo (include/exclude hosts)
- Sitemap automatico
- Detecao de arquivos sensiveis
- Verificacao de URL no escopo

### 10. Session Handler ✅
- Criacao e gerenciamento de sessoes
- Cookies com domain, path, expires, secure, httponly
- Headers personalizados por sessao
- Parse de Set-Cookie headers

### 11. Match & Replace ✅
- Regras regex para substituicao automatica
- Suporte a backreferences (\1, \2)
- Escopo por host
- Aplicacao em request e/ou response

### 12. Payload Processor ✅
- 20+ operacoes builtin:
  - url_encode, url_decode, base64_encode, base64_decode
  - md5, sha1, sha256, hex_encode, hex_decode
  - rot13, upper, lower, capitalize, reverse
  - repeat, concat, replace
- Regras customizadas

### 13. Collaborator (OAST) ✅
- Servidor OAST integrado
- Detecao de blind SQLi, SSRF, XXE
- Payloads DNS, HTTP, XXE, SSRF
- Registro de interacoes
- Aguardo de callback com timeout

### 14. Alerts ✅
- Sistema de alertas por severidade
- Acknowledge e mark as read
- Filtros por tipo e severidade
- Exportacao de alerts
- Notificacoes em tempo real

### 15. Organizer ✅
- Armazenar e anotar requests
- Tags e folders
- Starred items
- Busca e exportacao JSON

### 16. Project Manager ✅
- Criar, listar, salvar projetos
- Formato .cbp (CustomBurp Project)
- Escopo, sessoes, alerts, regras salvas
- Import/export de projetos

### 17. Extender / BApp Store ✅
- Sistema de plugins Python
- 8 callbacks disponiveis:
  - http_send, http_received
  - proxy_request, proxy_response
  - scanner_scan, intruder_attack
  - ui_render, menu_action
- BApp Store com 8 plugins populares
- Install/uninstall via API

### 18. Burp Browser ✅
- Navegador Chromium integrado
- Proxy configurado automaticamente
- Ignore certificate errors
- Controle via API

### 19. REST API ✅
- 30+ endpoints padronizados
- Respostas JSON consistentes
- Autenticacao por session
- Rate limiting ready

### 20. Web UI ✅
- Interface Flask completa
- 17 abas funcionais
- Tema dark profissional
- Atualizacao em tempo real

## Interface Web

Acesse em `http://localhost:4000`

| Aba | Descricao |
|-----|-----------|
| Proxy | Controle do proxy, interceptacao, estatisticas |
| Repeater | Envio manual de requests |
| Intruder | Ataques automatizados com payloads |
| Scanner | Varredura de vulnerabilidades |
| Logger | Historico de requisicoes |
| Decoder | Codificacoes e decodificacoes |
| Issues | Vulnerabilidades detectadas |
| **Alerts** | Sistema de alertas |
| **Organizer** | Organizar e anotar requests |
| **Target** | Escopo e sitemap |
| **Session** | Gerenciamento de sessoes |
| **Comparer** | Diff entre responses |
| **Sequencer** | Analise de entropia |
| **Collaborator** | OAST out-of-band |
| **Projects** | Salvar/carregar projetos |
| **Extender** | Plugins e BApp Store |
| **Browser** | Navegador integrado |
| **Payload** | Processamento de payloads |

## Comandos CLI

| Comando | Descricao |
|---------|-----------|
| `python main.py` | Inicia tudo (proxy + web) |
| `python main.py --no-proxy` | So UI web |
| `python main.py --no-web` | So proxy |
| `python main.py --generate-ca` | Gera certificado CA |
| `python main.py --proxy-port 8888` | Porta proxy customizada |
| `python cli.py status` | Mostra status |
| `python cli.py test` | Executa testes |

## Endpoints da API

```
GET  /api/status              # Status do sistema
GET  /api/requests            # Lista requests
GET  /api/requests/<id>       # Busca request
POST /api/requests/clear      # Limpa requests
GET  /api/issues              # Lista issues
POST /api/scan/run            # Executa scan
POST /api/repeater/send       # Envia request
POST /api/intruder/start      # Inicia ataque
GET  /api/intruder/results    # Resultados intruder
POST /api/decoder/transform   # Transforma dado
GET  /api/decoder/operations  # Operacoes disponiveis

# Novos endpoints
GET  /api/alerts              # Lista alerts
POST /api/alerts/acknowledge/<id>
POST /api/alerts/clear
GET  /api/organizer/items
POST /api/organizer/add
GET  /api/organizer/stats
GET  /api/target/scope
POST /api/target/add
GET  /api/session/create
GET  /api/session/list
GET  /api/session/<id>
POST /api/sequencer/analyze
POST /api/comparer/compare
POST /api/collaborator/start
POST /api/collaborator/stop
GET  /api/collaborator/interactions
GET  /api/collaborator/payloads
GET  /api/match-replace/rules
POST /api/match-replace/add
GET  /api/projects/list
POST /api/projects/create
GET  /api/projects/current
GET  /api/extender/plugins
POST /api/extender/install
GET  /api/extender/store
GET  /api/browser/status
POST /api/browser/start
POST /api/browser/stop
POST /api/browser/open
POST /api/payload-processor/process
```

## Arquitetura

```
burpsuite-custom/
├── core/
│   ├── engine.py      (55KB) Engine principal + Proxy + Scanner + Intruder + DB
│   ├── repeater.py    (8KB)  Repeater HTTP
│   ├── decoder.py     (1KB)  Decoder utilities
│   ├── intruder.py    (13KB) Intruder com 4 modos
│   ├── proxy.py       (19KB) Proxy HTTPS com CA certs
│   ├── comparer.py    (7KB)  Diff entre respostas
│   ├── sequencer.py   (8KB)  Entropia de tokens
│   ├── target.py      (6KB)  Escopo e sitemap
│   ├── session_handler.py (9KB) Sessoes e cookies
│   ├── match_replace.py (7KB) Regex rules
│   ├── payload_processor.py (6KB) Payload ops
│   ├── collaborator.py (8KB) OAST server
│   ├── logger.py      (13KB) Logger central
│   ├── organizer.py   (7KB)  Organizer
│   ├── alerts.py      (7KB)  Alerts system
│   ├── project.py     (8KB)  Project manager
│   ├── extender.py    (10KB) Plugin system + BApp Store
│   ├── browser.py     (7KB)  Chromium browser wrapper
│   └── api.py         (17KB) REST API completa
├── web/
│   └── app.py         (70KB) UI Flask com 17 abas
├── plugins/           # Diretorio para plugins
├── projects/          # Projetos salvos
├── main.py            # Entry point
├── cli.py             # CLI commands
├── start.bat          # Windows startup
├── requirements.txt
└── test_all.py        # 22 testes passando
```

## Banco de Dados

SQLite em `custom_burp.db` com tabelas:
- `requests` - Requisicoes capturadas
- `responses` - Respostas correspondentes
- `issues` - Vulnerabilidades detectadas
- `intruder_results` - Resultados de ataques
- `entries` (logger) - Entradas centralizadas

## Testes

**22/22 testes passando:**
- Repeater HTTP GET/POST real ✅
- Decoder (URL, Base64, MD5, SHA256, HTML, JSON) ✅
- Scanner (XSS, SQLi, Headers) ✅
- Intruder sniper mode ✅
- Comparer diff ✅
- Sequencer entropia ✅
- Target scope ✅
- Session handler ✅
- Match & Replace ✅
- Payload processor ✅
- Collaborator OAST ✅
- Logger ✅
- Organizer ✅
- Alerts ✅
- Project Manager ✅
- Engine init/start/stop ✅
- REST API (20+ endpoints) ✅

## Notas

- 100% implementado do zero, sem dependencias externas pesadas
- Proxy funciona como tunnel transparente
- Scanner usa pattern matching
- Intruder suporta 4 modos de ataque
- UI web e responsiva com tema dark
- Extensivel via sistema de plugins
- Navegador Chromium integrado
- Projeto salvo em formato .cbp
