---
name: source-extractor
description: Toolkit completo de engenharia reversa para extracao de codigo fonte de qualquer .exe. Suporta .NET (CIL), Python (PyInstaller/Py2exe/Nuitka), Node.js (pkg/nexe), executaveis nativos (x86/x64 desassembly), e empacotadores (UPX/ASPack/VMProtect). Pipeline automatico com relatorio consolidado. V2.1: type hints, modulos organizados.
aliases:
  - extract
  - decompile
  - source
  - deobfuscate
  - unpack-all
  - source-recovery
  - full-decompile
  - binary-to-source
---

# Source Extractor Toolkit v2.1 — Recuperação Total de Código Fonte

Toolkit completo de engenharia reversa para recuperar código fonte de executaveis Windows (.exe) e Linux (.elf).

> **v2.1**: Type hints completos em dataclasses, organizacao modular com sub-módulos (pe_analyzer, dotnet_decompiler, python_unpacker, string_miner), pipeline com 6 estagios.

## 🎯 Arquitetura Modular

```
Source Extractor Toolkit v2.1
├── PE Analyzer (modules/pe_analyzer.py)    - Deep PE parsing (headers, sections, imports, exports)
├── .NET Decompiler (modules/dotnet_decompiler.py) - CIL disassembly + resource extraction
├── Python Unpacker (modules/python_unpacker.py)   - PyInstaller / Py2exe / Nuitka extraction
├── Node Unpacker (built-in)                  - pkg / nexe snapshot extraction
├── String Miner (modules/string_miner.py)     - ASCII, Unicode, Base64, XOR, ROL/ROR decoding
├── Control Flow Analyzer (built-in)          - Basic block detection + CFG generation
├── Auto Patcher (built-in)                   - Automated NOP/jump patching for bypass
└── Pipeline Orchestrator (source_extractor.py) - Multi-stage automated extraction
```

## 📦 Formatos Suportados

| Formatador | Extensoes | Recuperacao | Dificuldade |
|------------|-----------|-------------|-------------|
| PE Native | .exe, .dll, .sys | Assembly + strings + imports | Media-Alta |
| .NET | .exe, .dll (CLR) | CIL + Resources + Manifest | Baixa |
| Python | .exe (PyInstaller) | .pyc + assets + spec | Baixa |
| Python 2exe | .exe | .pyc + bootloader | Baixa |
| Python Nuitka | .exe | C source (parcial) | Media |
| Node pkg | .exe | JS snapshot | Baixa |
| Node nexe | .exe | JS snapshot | Baixa |
| UPX | .exe | Unpacked PE | Baixa |
| ASPack | .exe | Scylla dump | Media |
| VMProtect | .exe | Devirtualization | Alta |
| Themida | .exe | Manual OEP + dump | Muito Alta |

## 🚀 Comandos

```bash
# Analise completa automatica
python source_extractor.py C:\malware.exe --full

# Somente extracao de strings
python source_extractor.py C:\malware.exe --strings-only

# Extracao de resources
python source_extractor.py C:\malware.exe --resources

# Tentar unpack automatico
python source_extractor.py C:\malware.exe --unpack

# Pipeline completo com relatorio
python source_extractor.py C:\malware.exe --pipeline --output ./report/

# Analisar diretorio inteiro
python source_extractor.py --dir C:\samples\ --parallel

# Gerar relatório consolidado
python source_extractor.py C:\malware.exe --report --format markdown
python source_extractor.py C:\malware.exe --report --format json
```

## 🐍 Uso via Python

```python
from skills.source_extractor.source_extractor import SourceExtractor

extractor = SourceExtractor(output_dir="./output", max_workers=4)

# Analise rapida
result = extractor.analyze("malware.exe")
# {type, format, pe_info, imports, strings, entropy, suggested_actions}

# Decompile completo
source = extractor.extract("malware.exe")
# {extraction_type, source_files, strings, report_path, timing_ms}

# Pipeline automatico
pipeline = extractor.pipeline("malware.exe", output_dir="./output/")
# {stages, results, timing_total_ms}
```

## 📊 Pipeline de Extração (6 Estágios)

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: Format Detection                                 │
│  → Magic bytes + PE headers + CLR marker                    │
│  → Output: format type (.NET, Python, Node, Native)         │
├─────────────────────────────────────────────────────────────┤
│  STAGE 2: PE Deep Parse                                    │
│  → Sections, imports, exports, resources, entropy           │
├─────────────────────────────────────────────────────────────┤
│  STAGE 3: Unpacking (se necessario)                         │
│  → UPX: upx -d                                              │
│  → ASPack: Scylla dump                                      │
│  → Packed: entropy analysis + heuristic OEP                 │
├─────────────────────────────────────────────────────────────┤
│  STAGE 4: Language-Specific Extraction                     │
│  → .NET: CIL disassembly + resources + manifest             │
│  → Python: bootstrap + .pyc extraction + unzip              │
│  → Node: snapshot parsing + JS reconstruction               │
│  → Native: strings + disassembly + CFG                      │
├─────────────────────────────────────────────────────────────┤
│  STAGE 5: String Mining                                    │
│  → ASCII, Unicode, Base64, XOR, ROL/ROR decoding           │
├─────────────────────────────────────────────────────────────┤
│  STAGE 6: Report Generation                                │
│  → Markdown + JSON consolidated report                      │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Saida

```
./output/
├── report.md              # Relatorio completo
├── report.json            # Dados estruturados
├── extracted/
│   ├── source.py          # Codigo reconstruido
│   ├── source.js          # Se Node
│   ├── source.cil         # Se .NET
│   ├── resources/         # Assets extraidos
│   └── assembly/          # Se .NET assemblies
└── analysis/
    ├── strings.txt        # Todas as strings
    ├── imports.txt        # Imports detectados
    ├── cfg.dot            # Graphviz CFG
    └── pe_info.json       # Informacoes PE
```

## ⚙️ Configuracao

```bash
# Variaveis de ambiente
export SOURCE_EXTRACTOR_OUTPUT="./output"
export SOURCE_EXTRACTOR_WORKERS=4        # Parallel workers
export SOURCE_EXTRACTOR_DECODE_XOR=true  # Decode XOR strings
export SOURCE_EXTRACTOR_DECODE_B64=true  # Decode Base64 strings
export SOURCE_EXTRACTOR_MAX_STRINGS=50000
```

## 🎓 Dependencias

```bash
pip install pefile pyelftools capstone lief
# Opcional (melhora precisao):
pip install uncompyle6
# Para .NET (se clr-loader estiver disponivel):
pip install clr-loader
# Ferramentas externas (recomendado):
# upx, dnspy, ildasm, scylla, ghidra
```

---

**Source Extractor Toolkit v2.1 — Cada bit extraido, cada string decodificada.** 🐀
