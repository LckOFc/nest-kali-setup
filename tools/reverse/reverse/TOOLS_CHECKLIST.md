# 🛠️ Lista Completa de Ferramentas para Engenharia Reversa

**Data:** 2026-09-09  
**Objetivo:** Análise completa de binários Go (como agy.exe)

---

## 📊 Status Atual do Sistema

| Categoria | Instalado | Pendente |
|-----------|-----------|----------|
| **Python + Pacotes** | ✅ 10/10 | 0 |
| **Descompiladores** | ❌ 0/3 | 3 |
| **Debuggers** | ❌ 0/2 | 2 |
| **Análise de Rede** | ✅ 1/2 | 1 |
| **VMs** | ❌ 0/2 | 2 |
| **Utils** | ✅ 1/4 | 3 |

---

## 🥇 NÍVEL 1 — ESSENCIAIS (Instalar Primeiro)

### 1. FLARE-VM ⭐ RECOMENDADO
```
O que é:       Distro Windows pré-configurada com TODAS as ferramentas de RE
Custo:         GRÁTIS
Download:      https://github.com/mandiant/flare-vm
Instalação:    irm https://mandiant.github.io/flare-vm/setup.ps1 | iex
Para que serve: Ter TUDO instalado em 10 minutos
Importância:   ⭐⭐⭐⭐⭐
```

### 2. GHIDRA
```
O que é:       Descompilador gratuito da NSA
Custo:         GRÁTIS
Download:      https://ghidra-sre.org/
Instalação:    Extrair ZIP e executar ghidraRun.bat
Plugin Go:     https://github.com/numenum/ghidra-go
Para que serve: Descompilar agy.exe para pseudocódigo legível
Importância:   ⭐⭐⭐⭐⭐
```

### 3. X64DBG
```
O que é:       Debugger gráfico para Windows
Custo:         GRÁTIS
Download:      https://x64dbg.com/
Instalação:    Extrair e executar x64dbg.exe
Para que serve: Debugging dinâmico do agy.exe
Importância:   ⭐⭐⭐⭐⭐
```

### 4. HxD (Hex Editor)
```
O que é:       Editor hexadecimal
Custo:         GRÁTIS
Download:      https://mh-nexus.de/en/hxd/
Instalação:    Download e executar
Para que serve: Analisar bytes do binário, extrair strings manualmente
Importância:   ⭐⭐⭐⭐
```

### 5. Wireshark ✅ JÁ INSTALADO
```
O que é:       Analisador de protocolo de rede
Custo:         GRÁTIS
Status:        ✅ Instalado
Para que serve: Capturar tráfego do agy.exe
```

---

## 🥈 NÍVEL 2 — PROFISIONAL (Resultados Máximos)

### 6. BINARY NINJA
```
O que é:       Descompilador com MELHOR UI do mercado
Custo:         $399 (Trial 30 dias GRÁTIS)
Download:      https://binary.ninja/download
Para que serve: Análise Go com SSA form, melhor visualização
Importância:   ⭐⭐⭐⭐
```

### 7. IDA PRO + HEX-RAYS
```
O que é:       O descompilador MAIS poderoso existente
Custo:         ~$2500/ano (Demo gratuita limitada)
Download:      https://hex-rays.com/idea/evaluation.cfm
Plugin Go:     https://github.com/Lisitsyan/ida-go
Para que serve: Pseudocódigo próxima do fonte original
Importância:   ⭐⭐⭐⭐⭐ (mas caro)
```

### 8. FIDDLER
```
O que é:       HTTP Inspector/Proxy
Custo:         GRÁTIS (Classic) / Pago (Everywhere)
Download:      https://www.telerik.com/fiddler
Para que serve: Intercept HTTPS do agy.exe, decodificar JWT
Importância:   ⭐⭐⭐⭐
```

---

## 🥉 NÍVEL 3 — ÚTEIS (Automação e Análise)

### 9. PROCESS MONITOR (ProcMon)
```
O que é:       Monitor de sistema Windows (Sysinternals)
Custo:         GRÁTIS
Download:      https://docs.microsoft.com/en-us/sysinternals/downloads/procmon
Para que serve: Ver operações de arquivo/registro do agy.exe
```

### 10. PROCESS EXPLORER
```
O que é:       Gerenciador de processos avançado
Custo:         GRÁTIS
Download:      https://docs.microsoft.com/en-us/sysinternals/downloads/process-explorer
Para que serve: Ver DLLs carregadas, handles, threads
```

### 11. VIRTUALBOX / VMWARE PLAYER
```
O que é:       Virtualização para isolamento
Custo:         GRÁTIS
Download:      https://www.virtualbox.org/ ou https://www.vmware.com/
Para que serve: Executar agy.exe em ambiente isolado
```

### 12. CUTTER (GUI radare2)
```
O que é:       Interface gráfica para radare2
Custo:         GRÁTIS
Download:      https://cutter.re/
Para que serve: Análise CLI com UI amigável
```

### 13. WINDBG
```
O que é:       Debugger avançado Microsoft
Custo:         GRÁTIS
Download:      Microsoft Store (WinDbg Preview)
Para que que serve: Debugging avançado, kernel mode
```

---

## 🧰 NÍVEL 4 — AUTOMAÇÃO E SCRIPTING

### Já Instalado ✅
```python
# Todos estes estão OK:
lief          1.0.0    # PE parsing
capstone      5.0.0    # Disassembly
unicorn       2.0.1    # Emulação
keystone      0.9.2    # Assembly
flask         3.0.0    # Web dashboard
rich          13.7.0   # Console output
click         8.1.7    # CLI framework
networkx      3.3      # Graph analysis
pydot         4.0      # Graph visualization
matplotlib    3.8.0    # Plotting
```

### Python Scripts Criados ✅
```
C:\Users\devel\tools\reverse\go-re-engine\
├── analyze.py            # Orchestrator principal
├── decompiler.py         # Motor Hex-Rays style
├── cfg_analyzer.py       # Análise CFG
├── type_recovery.py      # Recovery de tipos
├── func_reconstructor.py # Reconstrução de funções
└── engine_fast.py        # Engine otimizada
```

---

## 📋 CHECKLIST DE INSTALAÇÃO

```powershell
# === PASSO 1: Instalar FLARE-VM (RECOMENDADO) ===
irm https://mandiant.github.io/flare-vm/setup.ps1 | iex
# Aguardar instalação (10-15 minutos)

# === PASSO 2: Instalar Ghidra ===
# Download manual: https://ghidra-sre.org/
# Extrair para C:\Tools\ghidra\
# Copiar plugin Go:
git clone https://github.com/numenum/ghidra-go C:\Tools\ghidra\Ghidra\Extensions\go

# === PASSO 3: Instalar x64dbg ===
# Download: https://x64dbg.com/
# Extrair para C:\Tools\x64dbg\

# === PASSO 4: Instalar HxD ===
# Download: https://mh-nexus.de/en/hxd/
# Instalar normalmente

# === PASSO 5: Instalar Fiddler ===
# Download: https://www.telerik.com/fiddler
# Instalar Fiddler Classic (grátis)

# === VERIFICAR ===
Get-Command ghidra, x64dbg, fiddler, hxd -ErrorAction SilentlyContinue
```

---

## 💰 RESUMO DE CUSTOS

| Opção | Custo | Ferramentas Incluídas |
|-------|-------|----------------------|
| **Básico (Grátis)** | $0 | Ghidra + x64dbg + Wireshark + HxD + FLARE-VM |
| **Profissional** | $399 | + Binary Ninja (melhor UI) |
| **Enterprise** | $2500+ | + IDA Pro (melhor descompilador) |

**Recomendação:** Começar com FLARE-VM (grátis) + Ghidra + nosso toolkit.

---

## 🎯 ORDEM SUGERIDA DE INSTALAÇÃO

```
1. [10 min]  Instalar FLARE-VM (já vem com tudo)
2. [15 min]  Configurar Ghidra + plugin Go
3. [5 min]   Instalar x64dbg
4. [5 min]   Instalar HxD
5. [5 min]   Instalar Fiddler
6. [5 min]   Configurar VM (VirtualBox)
7. [Pronto]  Iniciar análise do agy.exe
```

**Total estimado:** ~45 minutos para setup completo

---

*Lista atualizada em 2026-09-09*