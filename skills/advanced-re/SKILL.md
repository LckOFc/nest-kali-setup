---
name: advanced-re
description: Suite avançada de engenharia reversa para binários altamente protegidos. Anti-anti-debug, devirtualização VMProtect/Themida, bypass de anti-sandbox, análise Go/Rust, descriptografia automatica de strings, e pipeline orquestrado por IA. V2.1: modulos organizados, type hints.
aliases:
  - adv-re
  - anti-debug
  - devirtualize
  - anti-sandbox
  - go-rust
  - string-decrypt
  - obfuscation-bypass
  - advanced-reversing
---

# Advanced RE Suite v2.1 — Binários Protegidos & Anti-Análise

Toolkit completo para contornar proteções avançadas em executaveis.

> **v2.1**: Módulos organizados em `modules/` com type hints, `AIOrchestrator` com fallback offline, `PatternMatcher` com regex avançado.

## 🎯 Capabilities

```
┌──────────────────────────────────────────────────────────────────┐
│  PROTEÇÃO ALVO                  │  METODO DE BYPASS             │
│─────────────────────────────────┼───────────────────────────────│
│  Anti-Debug (IsDebuggerPres)    │  Patch + deteção proativa     │
│  Anti-VM (hypervisor detect)    │  Hardware spoofing            │
│  Anti-Sandbox (time/freshness)  │  Delay + ambiente falso       │
│  VMProtect (bytecode VM)        │  Devirtualizer + tracing      │
│  Themida (full VM)              │  Hybrid: trace + heuristics   │
│  STR/Armadillo (custom VM)      │  Manual OEP + Scylla          │
│  String encryption (custom)     │  Dynamic decrypt monitoring   │
│  Packed + obfuscated            │  Multi-layer unpack pipeline  │
│  Go/Rust (no symbols)           │  GoReSym + rustfilt + GHIDRA  │
│  Native C/C++ (stripped)        │  Ghidra + patterns + AI       │
└──────────────────────────────────────────────────────────────────┘
```

## 📦 Módulos (organizados em modules/)

| Módulo | Arquivo | Função |
|--------|---------|--------|
| AntiAntiDebug | `modules/anti_anti_debug.py` | Detecção + bypass de anti-debug |
| Devirtualizer | `modules/devirtualizer.py` | VMProtect/Themida trace+reconstruct |
| AntiSandboxBuster | `modules/anti_sandbox_buster.py` | Detecção + bypass de sandbox |
| GoRustAnalyzer | `modules/go_rust_analyzer.py` | Analisador especializado Go/Rust |
| StringDecryptor | `modules/string_decryptor.py` | Descriptografia dinamica de strings |
| PatternMatcher | `modules/pattern_matcher.py` | Matching de padrões obfuscados |
| AIOrchestrator | `modules/ai_orchestrator.py` | Orquestrador IA para pipeline |

## 🚀 Comandos

```bash
# Pipeline completo com IA
python advanced_re.py C:\protected.exe --full

# Bypass anti-debug
python advanced_re.py C:\protected.exe --anti-debug

# Devirtualizar (VMProtect/Themida)
python advanced_re.py C:\protected.exe --devirtualize

# Bypass anti-sandbox
python advanced_re.py C:\protected.exe --anti-sandbox

# Análise Go/Rust
python advanced_re.py C:\binary.exe --go-rust

# Decodificar strings
python advanced_re.py C:\protected.exe --decrypt-strings

# Somente padroes
python advanced_re.py C:\protected.exe --patterns

# Pipeline automatico com IA
python advanced_re.py C:\protected.exe --ai-pipeline --output ./results/

# Listar modulos disponiveis
python advanced_re.py --list-modules
```

## 🧠 Pipeline IA (v2.1)

```
1. [AI] Detect type + protectors (heuristics + signatures)
2. [Auto] Bypass anti-debug (patch dinamico)
3. [Auto] Bypass anti-sandbox (ambiente controlado)
4. [Auto] Unpacking multi-camada
5. [AI] Devirtualization (VMProtect/Themida)
6. [AI] String decryption (monitoramento dinamico)
7. [AI] Pattern matching (obfuscated code)
8. [AI] Code reconstruction (pseudo-codigo legivel)
9. [Auto] Gerar relatório consolidado
```

## 📊 Modulo: PatternMatcher

Detecta padrões de ofuscação comuns:
- XOR encoding (single-byte, multi-byte)
- Base64 encoding
- ROT13 / ROT-N
- String splitting + concatenation
- Dynamic API resolution (GetProcAddress patterns)
- Jump tables / indirect calls

## 📊 Modulo: GoRustAnalyzer

Análise especializada para binários Go e Rust:
- Go: identifica routines, goroutines, stack traces
- Rust: identifica panic handlers, ownership patterns
- Desmascara symbols stripped
- Mapeia control flow após compilação

---

**Advanced RE Suite v2.1 — Cada proteção contornada, cada string decifrado.** 🐀
