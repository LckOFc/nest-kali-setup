# 🦊 AGY.EXE — Guia Completo de Instalação e Configuração

**Data:** 2026-09-09  
**Engenheiro:** Sombra

---

## Resumo do que Já Temos

| Item | Status | Local |
|------|--------|-------|
| **agy.exe** (binário Go) | ✅ Instalado | `C:\Users\devel\AppData\Local\agy\bin\agy.exe` (180MB) |
| **PATH configurado** | ✅ Sim | `C:\Users\devel\AppData\Local\agy\bin` está no PATH |
| **SDK Python fonte** | ✅ Parcial | `C:\Users\devel\tools\reverse\antigravity-source\` (321KB) |
| **Relatórios** | ✅ Completos | `C:\Users\devel\tools\reverse\AGY_COMPLETE_REPORT.md` |
| **Pydantic** | ✅ Instalado | v2.13.5 |
| **Protobuf** | ✅ Instalado | v7.36.1 |
| **AnyIO** | ✅ Instalado | v4.14.2 |
| **MCP SDK** | ✅ Instalado | v1.29.1 |

---

## O Que Falta Instalar

### 1. SDK Python `google-antigravity`

```powershell
# Instalar o SDK oficial (40.3 MB)
pip install google-antigravity==0.1.16

# Dependências que serão instaladas:
# - absl-py          (Google logging)
# - google-genai>=1.0     (API Google AI)
# - google-auth      (Autenticação Google)
# - tenacity         (Retry logic)
# - pyasn1-modules   (Crypto helpers)
```

### 2. Autenticação

O SDK usa **Google Sign-In** automático. Duas opções:

#### Opção A: Google Sign-In (Recomendado)
```powershell
# Ao rodar o agente pela primeira vez, abre o browser automaticamente
agy
# Ou via Python:
python -c "from google.antigravity import Agent, LocalAgentConfig; import asyncio; asyncio.run((lambda: exec('async def m(): async with Agent(LocalAgentConfig()) as a: print(await (await a.chat(\"hi\")).text())'); asyncio.run(m()))())"
```

#### Opção B: API Key (Para servidores/SSH)
```powershell
# Exportar a chave antes de rodar
$env:GEMINI_API_KEY = "sua-chave-aqui"
# Ou no código:
config = LocalAgentConfig(api_key="sua-chave")
```

### 3. (Opcional) Clonar Repositório SDK

```powershell
git clone https://github.com/google-antigravity/antigravity-sdk-python
cd antigravity-sdk-python
pip install -e .
```

---

## Comandos CLI Disponíveis

```powershell
# Já funcionam (agy.exe está no PATH)
agy                    # Iniciar modo interativo (TUI)
agy --help            # Ver ajuda
agy --version         # Ver versão
agy doctor            # Diagnóstico do sistema
agy setup             # Setup inicial
agy web --port 8080   # Web dashboard
```

---

## Teste Rápido (Hello World)

Criar arquivo `test_agy.py`:

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig

async def main():
    config = LocalAgentConfig()
    async with Agent(config) as agent:
        response = await agent.chat("Say 'Hello from Sombra!'")
        print(await response.text())

asyncio.run(main())
```

Rodar:
```powershell
python test_agy.py
```

---

## Exemplos Avançados do Código Fonte

Já temos 33 exemplos baixados em `C:\Users\devel\tools\reverse\antigravity-source\examples\`:

| Arquivo | O que mostra |
|---------|-------------|
| `hello_world.py` | Uso básico do Agent |
| `subagents.py` | Subagentes dinâmicos, estáticos e hierárquicos |
| `policies.py` | Sistema de políticas (ALLOW/DENY/ASK_USER) |
| `sandboxing.py` | Sandbox OS-level para comandos |
| `hooks.py` | Lifecycle hooks (pre/post tool call) |
| `triggers.py` | Background triggers (timer, file watch) |
| `mcp_tools.py` | Integração com MCP servers |
| `streaming.py` | Streaming de respostas |
| `custom_tools.py` | Ferramentas customizadas |
| `persona_config.py` | Configuração de persona/identity |

---

## Arquitetura Completa (do código fonte)

```
┌─────────────────────────────────────────────────────────────────┐
│  Python SDK (google-antigravity)                                │
│  ├── Layer 1: Agent (agent.py)                                 │
│  │   └── async with Agent(config) as agent:                   │
│  │       response = await agent.chat(prompt)                   │
│  ├── Layer 2: Conversation                                     │
│  │   ├── Stateful session com history                          │
│  │   ├── HookRunner (pre/post tool call)                       │
│  │   ├── ToolRunner (registry + executor)                      │
│  │   └── TriggerRunner (background tasks)                      │
│  └── Layer 3: Connection                                       │
│      ├── LocalConnection → agy.exe (subprocess)               │
│      └── LiteRTConnection → Google internal                    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼ IPC/subprocess
┌─────────────────────────────────────────────────────────────────┐
│  agy.exe (Go binary - 180MB)                                    │
│  ├── Multi-Agent Orchestrator                                   │
│  │   ├── Pipeline Mode (sequencial)                            │
│  │   ├── Swarm Mode (paralelo)                                 │
│  │   └── CitC Mode (clone-in-the-cloud)                        │
│  ├── JetSki Framework (89.857 refs)                            │
│  │   ├── AgentExecutor, AgentState, Planner                    │
│  │   └── invoke_subagent, handoff files                        │
│  ├── Tool System (20+ tools)                                   │
│  │   ├── File ops (read, write, edit, grep, find)              │
│  │   ├── Shell (run_command, sandboxed)                        │
│  │   ├── Git (status, diff, log, commit)                       │
│  │   └── Web (search, fetch)                                   │
│  ├── LLM Integration (10+ providers)                           │
│  │   ├── Google Gemini (default)                               │
│  │   ├── OpenAI, Anthropic, DeepSeek                           │
│  │   └── Ollama, LM Studio, OpenRouter                         │
│  ├── Security Tools                                            │
│  │   ├── JWT Analysis (234 refs)                               │
│  │   ├── GraphQL testing                                       │
│  │   ├── WAF bypass (59 refs)                                  │
│  │   ├── CVE lookup                                            │
│  │   └── Token capture (14.085 refs)                           │
│  ├── Web Dashboard (React + TailwindCSS)                       │
│  ├── SQLite Database                                           │
│  ├── Syntax Highlighting (5.000+ rules, 421 langs)             │
│  └── 3 WASM modules embedded                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## O Que NÃO Temos (e Porquê)

| Algo | Porquê | Como Obter |
|------|--------|------------|
| **Código fonte Go** | Binário stripped, sem symbols | Solicitar ao mantenedor ou usar decompilador |
| **Arquivo PDB** | Não foi gerado junto com o binary | Build customizado necessário |
| **Fonte dos módulos JetSki** | Código proprietário do Google | Acesso interno requerido |

---

## Checklist de Instalação

```powershell
# 1. Verificar dependências existentes
python --version                          # ✅ 3.11.9
pip show pydantic protobuf anyio mcp      # ✅ Todos instalados

# 2. Instalar SDK (único passo necessário)
pip install google-antigravity==0.1.16    # ⏳ 40.3 MB

# 3. Verificar agy.exe no PATH
where agy                                 # ✅ C:\Users\devel\AppData\Local\agy\bin\agy.exe

# 4. Testar instalação
python -c "from google.antigravity import Agent; print('OK')"

# 5. Rodar primeiro teste
agy --version
```

---

## Próximos Passos Sugeridos

1. **Instalar o SDK** → `pip install google-antigravity`
2. **Autenticar** → Rodar `agy` uma vez para Google Sign-In
3. **Rodar hello_world.py** → Testar integração
4. **Explorar exemplos** → `subagents.py`, `policies.py`, `sandboxing.py`
5. **Criar agente customizado** → Usar o código fonte como base
6. **(Avançado) Decompilar Go** → Usar ghidra-go para extrair mais código

---

*Guia gerado por engenharia reversa completa + extração de repositórios públicos*