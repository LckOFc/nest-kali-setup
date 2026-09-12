---
name: codex-chatgpt-web
description: Integra o codex-chatgpt-web ao Codex CLI — usa ChatGPT Web (Free/Go/Plus/Pro) como modelo nativo do Codex via bridge local. Suporta browser-only e full harness com MCP. V2.1: service management, subagent support.
aliases:
  - chatgpt-web
  - cgtw
  - codex-web
  - chatgpt-bridge
  - gpt-web-codex
  - v2.1
---

# Codex ChatGPT Web Integration v2.1

Integra o projeto [miuuyy/codex-chatgpt-web](https://github.com/miuuyy/codex-chatgpt-web) ao Codex CLI.

> **v2.1**: Service management commands, subagent protocol support (v1 + native), doctor improvements.

## O Que É

Bridge local que roteia tarefas do Codex através do ChatGPT Web (incluindo contas Pro),
usando automação de navegador via Playwright. O Codex mantém sua UI, contexto e ferramentas nativas;
apenas o model turn é roteado para o ChatGPT Web.

## Instalacao

```bash
# Projeto ja clonado em C:\Users\devel\codex-chatgpt-web
# Dependencias instaladas via bun
cd C:\Users\devel\codex-chatgpt-web && bun install
```

## Configuracao

```bash
# Verificar status
bun run C:\Users\devel\codex-chatgpt-web\src\cli.ts doctor

# Fazer login no ChatGPT (abre Chrome)
bun run C:\Users\devel\codex-chatgpt-web\src\cli.ts login

# Configurar modo browser-only (recomendado para inicio)
bun run C:\Users\devel\codex-chatgpt-web\src\cli.ts setup --browser-only --acknowledge-unofficial --replace-codex-route

# Iniciar o servidor bridge
bun run C:\Users\devel\codex-chatgpt-web\src\cli.ts serve
# OU como servico (Windows):
bun run C:\Users\devel\codex-chatgpt-web\src\cli.ts service install
bun run C:\Users\devel\codex-chatgpt-web\src\cli.ts service start
```

## Uso com Codex CLI

```bash
# Selecionar modelo ChatGPT Web no Codex
codex -c model="chatgpt-web/gpt-5.6-luna"
codex -c model="chatgpt-web/gpt-5.6-sol"

# Ou editar config.toml permanentemente
echo 'model = "chatgpt-web/gpt-5.6-luna"' >> ~/.codex/config.toml

# Modo full harness (requer tunnel + connector)
codex -c model="chatgpt-web/gpt-5.6-sol" -c model_reasoning_effort="high"
```

## Comandos Slash (v2.1 expandido)

```
# Status e diagnostico
/toolkit cgtw status              # Status completo da integracao
/toolkit cgtw doctor              # Roda doctor do projeto
/toolkit cgtw login               # Inicia fluxo de login

# Servico
/toolkit cgtw serve               # Inicia bridge (foreground)
/toolkit cgtw serve-bg            # Inicia bridge (background)
/toolkit cgtw serve-stop          # Para bridge
/toolkit cgtw service-install     # Instala como servico Windows
/toolkit cgtw service-start       # Inicia servico
/toolkit cgtw service-stop        # Para servico
/toolkit cgtw service-status      # Status do servico

# Configuracao
/toolkit cgtw setup-browser       # Setup browser-only
/toolkit cgtw setup-full          # Setup full harness
/toolkit cgtw route-status        # Status da rota no Codex
/toolkit cgtw route-connect       # Conecta rota ao Codex
/toolkit cgtw route-disconnect    # Desconecta rota
/toolkit cgtw uninstall           # Remove integracao

# Subagents (v2.1)
/toolkit cgtw subagents-status    # Status de subagents
/toolkit cgtw subagents-v1        # Forca compatibility-v1
/toolkit cgtw subagents-native    # Forca native protocol
```

## Modos

| Modo | Modelo | Ferramentas Locais | Setup Extra |
|------|--------|-------------------|-------------|
| Browser-only | Luna (Free/Go), Instant-High (Plus), +Pro (Pro) | Nao | Nenhum |
| Full harness | Mesmo acima | Sim (filesystem, shell, imagens) | OpenAI tunnel + ChatGPT connector |
| Zero Risk | Manual | Sim (harness nativo) | Tunnel + connector manual |

## Arquitetura

```
┌─────────────┐     Responses API      ┌──────────────────┐     Playwright      ┌─────────────┐
│   Codex     │ ────────────────────▶  │ codex-chatgpt-web │ ─────────────────▶  │  Chrome     │
│   CLI       │                        │   :17841/v1       │    (automacao)      │  ChatGPT    │
└─────────────┘                        └──────────────────┘                     │   Web       │
                                                                             └─────────────┘
      ▲                                      │
      │                                      ▼
      │                              ┌──────────────────┐
      └─────────────────────────────│  Temp Chat       │
                                    │  (session-bound) │
                                    └──────────────────┘
```

## Variaveis de Ambiente

```bash
CODEX_CHATGPT_WEB_HOME=C:\Users\devel\.codex-chatgpt-web
CODEX_CHATGPT_WEB_BROWSER_DIAGNOSTICS=1  # Screenshots em cada checkpoint
```

---

**Codex ChatGPT Web Integration v2.1 — ChatGPT como modelo nativo do Codex.** 🐀
