# TorWebFetch — Modo 4070 APEX

Web fetch seguro através da rede Tor com múltiplas camadas de proteção criadas do zero.

## Camadas de Proteção

| Camada | Nível | Descrição |
|--------|-------|-----------|
| NONE | none | Sem proteção |
| BASIC | basic | User-Agent rotation básica |
| ENHANCED | enhanced | + Header randomization |
| MAXIMUM | maximum | + Circuit renewal frequente |
| **APEX** | **apex** | **Todas + fingerprint único por request** |

## Features

### 1. User-Agent Rotation (9+ fingerprints)
- Chrome Windows/Mac/Linux
- Firefox Windows/Mac/Linux  
- Safari Mac/iOS
- Edge Windows
- Mobile (iPhone/Android)
- Tor Browser (variantes)
- Randomização com suffixes aleatórios

### 2. Header Anti-Fingerprinting
- Accept-Language rotativo
- Sec-Fetch-* headers aleatórios
- Referer rotativo (Google, DuckDuckGo, Startpage, Bing)
- DNT (Do Not Track) sempre ativo
- Cache-Control variável

### 3. Circuit Management
- Renovação automática a cada 5 minutos
- Rotação aleatória (30% no modo APEX)
- Solicitação NEWNYM via Control Port
- Fallback para conexão direta se Tor indisponível

### 4. Fingerprint Único
- Hash SHA-256 por request
- Timestamp + random seed
- Tracking de anomalias

### 5. Safe Exit Nodes
- Lista de países permitidos
- Exclusão de nós maliciosos conhecidos
- Guard nodes confiáveis

## Instalação

```bash
# Dependências
pip install aiohttp

# Usar sem Tor (fallback HTTP)
python tor_webfetch.py https://example.com

# Usar com Tor
python tor_webfetch.py https://example.onion --level apex
```

## Uso CLI

```bash
# Fetch básico
python tor_webfetch.py https://example.com

# Com nível de proteção
python tor_webfetch.py https://example.onion --level apex

# POST request
python tor_webfetch.py https://api.example.com \
  --method POST \
  --data '{"key":"value"}' \
  --header "Authorization: Bearer token"

# JSON output
python tor_webfetch.py https://example.com --json

# Stats
python tor_webfetch.py --stats

# Info
python tor_webfetch.py --info

# Salvar conteúdo
python tor_webfetch.py https://example.com --output result.html
```

## Uso Python

```python
from tools.tor_webfetch import TorWebFetch, ProtectionLayer

# Inicializar com proteção APEX
fetcher = TorWebFetch(
    level=ProtectionLayer.APEX,
    tor_enabled=True,
)

# Fetch simples
result = await fetcher.fetch("https://example.onion")
print(result.content)
print(result.exit_node)
print(result.fingerprint)

# Fetch múltiplo
results = await fetcher.fetch_multiple([
    "https://example1.onion",
    "https://example2.onion",
])

# Estatísticas
stats = fetcher.get_stats()
print(f"Requests: {stats['requests']}")
print(f"Successful: {stats['successful']}")

# Exportar histórico
fetcher.export_history("history.json")
```

## Configuração Avançada

```python
from tools.tor_webfetch import TorConfig, TorWebFetch

config = TorConfig(
    socks_host="127.0.0.1",
    socks_port=9050,
    control_port=9051,
    circuity_timeout=30,
    max_retries=3,
    circuit_renewal_interval=300,
    safe_exit=True,
    guard_nodes=["57.128.138.123", "104.218.241.123"],
)

fetcher = TorWebFetch(level=ProtectionLayer.APEX, config=config)
```

## Headers Personalizados

```bash
python tor_webfetch.py https://example.com \
  --header "X-Custom: value" \
  --header "Authorization: Bearer token"
```

## Segurança

- ✅ Requests passam pelo circuito Tor (3 hops)
- ✅ IP real nunca exposto
- ✅ Fingerprint único por request
- ✅ Circuitos renovados periodicamente
- ✅ Safe exit nodes filtrados
- ✅ Sem logging de conteúdo

## Requisitos

- Python 3.8+
- aiohttp
- Tor rodando localmente (opcional, tem fallback HTTP)

---

**TorWebFetch v4070-APEX — Anonymity最大化, protection completa.** 🐀
