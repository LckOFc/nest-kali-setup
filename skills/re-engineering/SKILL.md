---
name: re-engineering
description: Sistema completo de engenharia reversa multi-formato. Analisa .exe, .dll, .js, .bat, .py, .ps1, .bin com PE parsing, disassembly Capstone, extracao de strings, deteccao de riscos e hashing. V2.1: type hints, melhorias de erro.
aliases:
  - reverse
  - re
  - pe
  - disasm
  - binary
  - analyze
  - strings
  - hash
---

# Re-Engineering Engine v2.1 — Analise Multi-Formato

Engine completa de engenharia reversa integrada ao opencode. Suporta 6+ formatos com análise automática.

> **v2.1**: Type hints melhorados, tratamento de erro em imports opcionais (pefile, capstone), logging consistente.

## Instalacao

```bash
pip install pefile capstone
# Opcional para mais formadores:
pip install lief pyelftools
```

## Localizacao

```
C:\Users\devel\tools\re-engineering\re_engine.py
```

## Formatos Suportados

| Formatador | Extensoes | Descricao |
|------------|-----------|-----------|
| PEAnalyzer | .exe, .dll, .sys, .ocx, .drv | Headers PE, secoes, imports, exports, strings, entropy, hash |
| JavaScriptAnalyzer | .js, .jsx, .mjs, .cjs | Funcoes, imports, padroes perigosos (eval, innerHTML, localStorage) |
| BatchAnalyzer | .bat, .cmd | Comandos, variaveis de ambiente, detecção de comandos perigosos |
| PythonAnalyzer | .py, .pyw | Imports, funcoes, chamadas perigosas (eval, exec, subprocess) |
| PowerShellAnalyzer | .ps1, .psm1, .psd1 | Cmdlets perigosos, codigos encoded, obfuscacao |
| BinaryAnalyzer | .bin, .raw, .dat, .mem, .dmp | Magic bytes, entropy, strings, hex dump |
| Disassembler | .exe, .dll, .bin | Disassembly x86/x64 com Capstone |

## Comandos

```bash
# Analisar arquivo
python re_engine.py arquivo.exe
python re_engine.py arquivo.exe --format json
python re_engine.py arquivo.exe --format ascii

# Somente strings
python re_engine.py arquivo.exe --strings-only
python re_engine.py arquivo.exe --strings-only --min-string-length 6

# Somente hashes
python re_engine.py arquivo.exe --hash-only

# Listar formatos
python re_engine.py --list-formats

# Escanear diretorio
python re_engine.py --dir C:\pasta --depth 1
```

## Uso via Python

```python
from tools.re_engine.re_engine import ReEngineeringEngine

engine = ReEngineeringEngine()

# Analisar unico arquivo
result = engine.analyze('target.exe')
# result: {type, pe_info, sections, imports, exports, strings, interesting_strings, hashes, risks, verdict}

# Disassembly
disasm = engine.disassemble('target.exe', offset=0x1000, count=50)
# disasm: {instructions, calls, jumps, error}

# Quick strings
strings = engine.quick_strings('target.exe', min_length=4)

# Quick hash
hashes = engine.quick_hash('target.exe')
# {md5, sha1, sha256, size_bytes}

# Batch analyze
batch = engine.batch_analyze(['file1.exe', 'file2.dll', 'script.js'])

# Formatos suportados
formats = engine.get_supported_formats()
```

## Campos da Saida JSON

### PE Analysis
```json
{
  "type": "PE",
  "pe_info": {
    "format": "EXE|DLL",
    "machine": "IMAGE_FILE_MACHINE_AMD64",
    "entry_point": "0x19b0",
    "num_sections": 8,
    "subsystem": "IMAGE_SUBSYSTEM_WINDOWS_GUI",
    "is_dll": false,
    "dll_characteristics": ["DYNAMIC_BASE", "NX_COMPAT"]
  },
  "sections": [
    {"name": ".text", "virtual_size": 157410, "entropy": 6.23, "suspicious": false}
  ],
  "imports": [{"library": "USER32.dll", "functions": [{"name": "MessageBoxA"}]}],
  "exports": [{"name": "Ordinal_1", "ordinal": 1}],
  "strings": ["This program cannot", ...],
  "interesting_strings": [{"type": "URL", "value": "http://..."}],
  "hashes": {"md5": "...", "sha256": "..."},
  "risks": ["Suspicious import: WinExec", ...],
  "verdict": {"threat_level": "HIGH", "risk_score": 55}
}
```

### Script Analysis
```json
{
  "type": "JavaScript",
  "lines": 500,
  "functions": ["func1", "func2"],
  "interesting_patterns": [{"type": "eval", "count": 2}],
  "risks": ["eval: 2 occurrence(s)"],
  "verdict": {"threat_level": "MODERATE", "risk_score": 20}
}
```

## Testes

```bash
# Rodar todos os testes
python test_all.py

# Testar disassembly
python test_disasm.py
```

**Resultado:** 10/10 testes passando.

---

**Re-Engineering Engine v2.1 — Cada bit analisado, cada string extraida.** 🐀
