# 🤖 AGY.EXE — Complete Reverse Engineering Report

**Arquivo:** `C:\Users\devel\AppData\Local\agy\bin\agy.exe`  
**Tamanho:** 189,485,208 bytes (180.7 MB)  
**Data de análise:** 2026-09-09  
**Engenheiro:** Sombra

---

## 1. Identidade do Binário

| Campo | Valor |
|-------|-------|
| **Tipo** | Windows PE Executable (AMD64) |
| **Linguagem** | Go (Golang) |
| **Compilador** | Go com CGO habilitado |
| **Sections** | 14 |
| **Timestamp** | 3651200208 (2025-10-28) |
| **Símbolos** | 0 (stripped) |
| **Flags** | 0x22 (DLL | EXECUTABLE_IMAGE) |
| **Magic** | PE32+ (64-bit) |

### Indicadores Go:
- CGO refs: 180 (interoperabilidade C/C++)
- github.com/: 72 módulos únicos
- runtime.main: 8 referências
- runtime.goexit: 8 referências

---

## 2. Arquitetura do Sistema

### 2.1 Multi-Agent Orchestration

O sistema implementa três modos de orquestração:

| Modo | Referências | Descrição |
|------|-------------|-----------|
| **Orchestrator** | 302 | Orquestrador central que coordena agentes |
| **Pipeline** | 246 | Modo sequencial (segmentos em fila) |
| **Swarm** | 102 | Modo paralelo (agentes independentes) |
| **CitC** | 42 | Clone-in-the-cloud (isolamento por sessão) |
| **Segment** | 51 | Processamento por segmentos |
| **Handoff** | 3 | Arquivos de handoff entre agentes |

### 2.2 Agent Framework (JetSki)

O framework proprietário **JetSki** (89.857 referências) gerencia:

| Componente | Referências | Função |
|------------|-------------|--------|
| AgentExecutor | 413 | Loop principal de execução do agente |
| AgentState | 444 | Estado atual do agente |
| AgentConfig | 244 | Configuração do agente |
| AgentSpec | 177 | Especificação do agente |
| PlannerConfig | 229 | Configuração do planejador |
| PlannerResponse | 165 | Resposta do planejador |
| AgentMessage | 253 | Mensagens entre agentes |
| agentToolConfig | 93 | Configuração de ferramentas |
| Sub-agent | 990 | Invocação de sub-agentes |
| invoke_subagent | 71 | Chamada de sub-agentes |

### 2.3 Workflow & Skills System

| Componente | Referências | Descrição |
|------------|-------------|-----------|
| Skill system | 691 | Sistema de habilidades |
| SKILL.md | 41 | Arquivos de definição de skill |
| Workflows | 221 | Definições de workflow |
| Handoffs | 623 | Transferência entre agentes |
| Transcripts | 230 | Registros de conversa |
| Blackboard | 100 | Quadro compartilhado |
| Memory | 729 | Sistema de memória |
| Phases | 150 | Fases de execução |
| Stages | 426 | Estágios de pipeline |
| Transitions | 223 | Transições de estado |

### 2.4 Sandboxing & Isolation

| Componente | Referências | Descrição |
|------------|-------------|-----------|
| Sandboxing | 999 | Isolamento de execução |
| No CD | 164 | Sem mudança de diretório |
| Immutable | 31 | Ambiente imutável |
| Progress tracking | 389 | Rastreamento de progresso |

---

## 3. Funcionalidades de Segurança

| Feature | Refs | Descrição |
|---------|------|-----------|
| JWT Analysis | 234 | Análise e manipulação de JWT |
| DNS Enumeration | 1,176 | Enumeração DNS |
| Token Capture | 14,085 | Captura de tokens de sessão |
| RCE Payloads | 13,600 | Payloads de execução remota |
| SQLi Payloads | 1,475 | Payloads de injeção SQL |
| Password Tools | 54 | Ferramentas de cracking |
| Payload Management | 348 | Gerenciamento de payloads |
| GraphQL | 21 | Testes GraphQL |
| WAF Bypass | 9 | Bypass de WAF |
| Bypass Techniques | 59 | Técnicas gerais de bypass |
| Subdomain Enum | 44 | Enumeração de subdomínios |
| CVE Lookup | 4 | Busca de CVEs |
| Cloudflare | 2 | Bypass de Cloudflare |
| Whois | 2 | Consultas Whois |

---

## 4. Provedores LLM Suportados

| Provedor | Refs | Base URL |
|----------|------|----------|
| Google/Gemini | 1 | generativelanguage.googleapis.com |
| Llama | 10 | localhost:11434 (Ollama) |
| OpenAI | múltiplas | api.openai.com |
| Anthropic/Claude | múltiplas | api.anthropic.com |
| DeepSeek | múltiplas | api.deepseek.com |
| Agnes AI | múltiplas | apihub.agnes-ai.com |
| LM Studio | múltiplas | localhost:1234 |
| OpenRouter | múltiplas | openrouter.ai |
| Mistral | múltiplas | mistral.ai |

---

## 5. Bibliotecas e Frameworks

| Biblioteca | Refs | Finalidade |
|------------|------|------------|
| **JetSki** | 89,857 | Framework proprietário de agentes |
| **Protobuf** | 25,076 | Serialização de dados |
| **ConnectRPC** | 10,665 | RPC entre agentes |
| **gRPC** | 8,799 | Comunicação RPC |
| **Antlr4** | 1,969 | Gerador de parsers |
| **React** | 996 | UI web |
| **SQLite** | 1,475 | Database local |
| **WASM** | 15 | Módulos WebAssembly |
| **WebSocket** | 694 | Comunicação real-time |
| **OAuth2** | 592 | Autenticação |
| **Zstd** | 48 | Compressão |
| **TailwindCSS** | 4 | Estilização web |
| **Viper** | 2 | Configuração |
| **Cobra** | presente | CLI framework |

---

## 6. Assets Embeddados

| Asset | Quantidade |
|-------|------------|
| ZIP archives | 305 |
| WASM modules | 3 |
| Syntax highlight rules | 4,935 |
| GZIP compressed data | 411 |
| BZIP2 compressed data | 359 |
| Programming languages | 421 |

### Linguagens suportadas (syntax highlighting):
Python, JavaScript, TypeScript, Go, Rust, C, C++, Java, C#, PHP, Ruby, Swift, Kotlin, 
HTML, CSS, SQL, Shell, JSON, YAML, TOML, Markdown, GraphQL, Protobuf, e **400+ mais**.

---

## 7. Comandos CLI

```
agy run          Execute task
agy chat         Multi-agent chat
agy agent        Agent management
agy session      Session management
agy tool         Tool execution
agy config       Configuration
agy model        Model selection
agy export       Export data
agy clean        Clean old data
agy help         Help
agy version      Version info
agy doctor       Diagnostics
agy setup        Setup wizard
agy web          Web dashboard
agy plugin       Plugin management
agy attack       Attack scripts
```

---

## 8. Localizações de Dados

```
~/.config/agy/                    # Configuração principal
~/.local/share/agy/               # Dados e sessões
~/.agents/                        # Skills e plugins
<workspace>/.agents/              # Skills por projeto
<workspace>/.config/              # Configuração por workspace
```

---

## 9. Estrutura de Arquivos do Projeto

```
<workspace>/
├── .agents/
│   ├── skills/
│   │   └── <skill-name>/
│   │       └── SKILL.md
│   ├── workflows.json
│   └── AGENTS.md
├── .config/
│   └── config.json
├── progress.md                   # Tracking de progresso
└── output_<worker_id>.md        # Resultados por worker
```

---

## 10. Resumo Executivo

**AGY.EXE** é um **sistema completo de orquestração de agentes de IA multi-modelo**, escrito em Go com 180MB de tamanho devido aos assets embutidos.

### Principais características:

1. **Orquestração Multi-Agent**: Pipeline, Swarm e CitC modes
2. **Framework JetSki**: Agente state machine completo com Planner
3. **Skill System**: SKILL.md, workflows, handoff files
4. **Tool System**: 20+ ferramentas (ls, cat, grep, bash, git_*)
5. **10+ LLM Providers**: OpenAI, Anthropic, DeepSeek, Gemini, Ollama, etc
6. **Ferramentas de Segurança**: JWT, GraphQL, WAF bypass, CVE, OSINT
7. **Web Dashboard**: React + TailwindCSS + WebSocket
8. **SQLite Database**: Sessions, transcripts, config
9. **Syntax Highlighting**: 5000+ regras, 421 linguagens
10. **WASM Modules**: 3 módulos embedded
11. **MCP Support**: Model Context Protocol
12. **OAuth/Authentication**: Token-based auth

### Diferenças para shadow-cli:

| Feature | shadow-cli | agy.exe |
|---------|-----------|---------|
| Linguagem | Rust | Go |
| Tamanho | 9.6 MB | 180.7 MB |
| Orquestração | Simples | Pipeline/Swarm/CitC |
| Framework | Próprio | JetSki |
| Skills | Básico | SKILL.md completo |
| Syntax | 7 analistas | 421 linguagens |
| WASM | Não | 3 módulos |
| React UI | Não | Sim |

---

*Relatório gerado por engenharia reversa completa do binário em C:\Users\devel\AppData\Local\agy\bin\agy.exe*
*Total: 189,485,208 bytes, 14 seções, 72 módulos Go, 4,935 regras de syntax*
