---
name: deepseek-chat
description: Sistema completo de chat com IA usando o gateway DeepSeek Chat. Fornece API OpenAI-compatible, CLI interativo e wrapper de linha de comando — tudo roteado via ChatGPT Web Bridge (127.0.0.1:17841). V2.1: multi-modelo, session management.
aliases:
  - deepseek
  - ds
  - chat
  - ai-chat
  - v2.1
---

# DeepSeek Chat v2.1 — Gateway de IA

Sistema completo de chat com IA usando o gateway DeepSeek Chat. Fornece API OpenAI-compatible, CLI interativo e wrapper de linha de comando — tudo roteado via ChatGPT Web Bridge (127.0.0.1:17841).

> **v2.1**: Multi-modelo support (light/medium/high/extra-high/pro), session management com history.jsonl, config.json auto-created.

## Instalação

```bash
pip install fastapi uvicorn aiohttp pydantic
cd C:/Users/devel/deepseek-chat
python deepseek_chat.py  # inicia API no porto 18841
```

## Comandos Opencode

### `/deepseek` — Abre CLI interativo
```
/deepseek
```
Inicia o chat interativo na sessão atual.

### `/deepseek-query "mensagem"` — Pergunta direta
```
/deepseek-query "Explica transformadores em 3 linhas"
```
Envia uma pergunta e retorna a resposta sem abrir o chat interativo.

### `/deepseek-model <light|medium|high|extra-high|pro>` — Muda modelo
```
/deepseek-model pro
```
Troca o modelo de conversa atual.

### `/deepseek-sessions` — Lista sessões
```
/deepseek-sessions
```

### `/deepseek-status` — Status do gateway
```
/deepseek-status
```

## Endpoints da API

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/v1/models` | Lista modelos disponíveis |
| POST | `/v1/chat/completions` | Gera resposta (OpenAI format) |
| POST | `/v1/sessions` | Cria nova sessão |
| GET | `/v1/sessions` | Lista sessões ativas |
| DELETE | `/v1/sessions/{id}` | Remove sessão |
| GET | `/v1/health` | Status do gateway |
| GET | `/docs` | Swagger UI |

## Modelos Disponíveis

| Modelo | Uso | Latência | Qualidade |
|--------|-----|----------|-----------|
| `light` | Chat rápido, perguntas simples | ~500ms | Boa |
| `medium` | Código, explicacoes tecniche | ~1s | Muito boa |
| `high` | Analise profunda, debugging | ~2s | Excelente |
| `extra-high` | Tarefas complexas, multi-step | ~3s | Máxima |
| `pro` | Acesso ChatGPT Pro via bridge | ~2s | Excelente |

## Configuração

Arquivo: `~/.deepseek-chat/config.json` (criado automaticamente)

Variáveis de ambiente:
- `DEEPSEEK_PORT` — porta do gateway (default: 18841)
- `DEEPSEEK_BRIDGE` — URL do ChatGPT Web bridge (default: http://127.0.0.1:17841)
- `DEEPSEEK_API_KEY` — chave API DeepSeek (fallback direto)
- `DEEPSEEK_SYSTEM` — system prompt padrão
- `DEEPSEEK_MAX_TOKENS` — max tokens por resposta (default: 4096)
- `DEEPSEEK_SESSION_TIMEOUT` — timeout de sessão em minutos (default: 60)

## Uso como CLI

```bash
# Iniciar servidor API
python deepseek_chat.py

# Chat interativo
python deepseek_chat.py --cli

# Pergunta única
python deepseek_wrapper.py "explique deep learning"
python deepseek_wrapper.py "code me a rust async HTTP client" --model high
```

## Integração com opencode

O gateway funciona como proxy entre o opencode e o ChatGPT Web bridge. Qualquer cliente OpenAI-compatible pode se conectar:

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:18841/v1", api_key="not-needed")
resp = client.chat.completions.create(
    model="light",
    messages=[{"role": "user", "content": "hello"}],
)
print(resp.choices[0].message.content)
```

## Arquivos

| Arquivo | Função |
|---------|--------|
| `deepseek_chat.py` | Servidor API + CLI principal |
| `deepseek_wrapper.py` | Wrapper para uso via linha de comando |
| `config.json` | Configuração (criado automaticamente) |
| `history.jsonl` | Histórico de conversas por sessão |

---

**DeepSeek Chat v2.1 — IA acessível, respostas rápidas.** 🐀
