---
name: auto-unpacker
description: Pipeline de desempacotamento automatico de binarios PE. Detecta packers (UPX, ASPack, Themida, VMProtect, Enigma), calcula entropia por secao, recomenda estrategia e executa unpacking ou gera instrucoes manuais. V2.1: type hints em dataclasses, secao entropy calculo.
aliases:
  - unpack
  - unpacker
  - packer-detect
  - depack
  - upx
  - scylla
  - oep
---

# Auto-Unpacker Pipeline v2.1

Pipeline completo de deteccao e desempacotamento de binarios PE (Portable Executable).

> **v2.1**: Dataclasses tipadas para SectionInfo/UnpackResult, calculo de entropia por secao otimizado.

## Instalacao

```bash
pip install pefile lief
# Opcional: upx para desempacotamento automatico
# upx.exe deve estar no PATH
```

## Localizacao

```
C:\Users\devel\.config\opencode\skills\auto-unpacker\auto_unpacker.py
```

## Tipos de Packer Detectados

| Packer | Indicadores | Dificuldade | Metodo |
|--------|-------------|-------------|--------|
| UPX | Magic bytes `UPX`, secoes UPX0/UPX1/UPX2 | Baixa | `upx -d` automatico |
| ASPack | `!ThisProgr`, `.aspack` | Média | Scylla dump manual |
| Themida | `.themida`, VM customizada | Alta | Análise OEP manual |
| VMProtect | `.vmp0`, `.vmp1` | Muito alta | Devirtualizer + tracing |
| Enigma | `.enigma0`, criptografia de secoes | Muito alta | Bypass manual complexo |
| N/A | Entropia normal (< 6.5) | - | Nenhumaacao necessaria |

## Comandos

```bash
# Analisar e detectar packer
python auto_unpacker.py C:\malware.exe

# Analisar com detalhamento de secoes
python auto_unpacker.py C:\malware.exe --detailed

# Tentar unpack automatico (APENAS UPX)
python auto_unpacker.py C:\malware.exe --unpack

# Salvar resultado em JSON
python auto_unpacker.py C:\malware.exe --output resultado.json

# Analisar diretorio inteiro
python auto_unpacker.py --dir C:\samples --batch

# Verificar entropia de um arquivo
python auto_unpacker.py C:\malware.exe --entropy-only
```

## Uso via Python

```python
from skills.auto_unpacker.auto_unpacker import AutoUnpacker

unpacker = AutoUnpacker()

# Analise completa
result = await unpacker.analyze("malware.exe")
# {file, sha256, size, packer, overall_entropy, sections, suspicious_indicators, recommended_strategy}

# Tentativa de unpack
success = await unpacker.try_unpack("malware.exe", output_dir="./unpacked")
# True se sucesso, False se falhar (requer manual)

# Comparar entropia
entropy_before = unpacker.calculate_entropy(data)
# float: 0.0-8.0 (8.0 = perfeitamente aleatorio/criptografado)
```

## Saida JSON

```json
{
  "file": "C:\\malware.exe",
  "sha256": "a3f2b8c9...",
  "size_bytes": 245760,
  "packer": "upx",
  "packer_confidence": 0.95,
  "overall_entropy": 7.23,
  "sections": [
    {"name": ".text", "virtual_size": 65536, "raw_size": 65400, "entropy": 6.85, "is_high_entropy": true},
    {"name": ".rsrc", "virtual_size": 32768, "raw_size": 32000, "entropy": 5.12, "is_high_entropy": false},
    {"name": ".UPX0", "virtual_size": 131072, "raw_size": 130000, "entropy": 7.89, "is_high_entropy": true},
    {"name": ".UPX1", "virtual_size": 8192, "raw_size": 8000, "entropy": 0.0, "is_high_entropy": false}
  ],
  "suspicious_indicators": [
    "HIGH_ENTROPY_ALL",
    "KNOWN_SECTION:.UPX0",
    "KNOWN_SECTION:.UPX1"
  ],
  "recommended_strategy": "upx -d input.exe -o output.exe",
  "unpack_success": true,
  "unpacked_path": "C:\\unpacked\\malware.exe.unpacked",
  "oep_address": "0x401000"
}
```

## Fluxo de Decisao

```
1. Ler arquivo → calcular entropia global
2. Verificar magic bytes → identificar packer
3. Parsear secoes PE → entropia por secao
4. Buscar heurísticas avançadas
5. Recomendacao:
   ├─ Entropia < 6.5 → Nativo, sem packer
   ├─ Entropia > 7.0 + UPX magic → Auto-upx -d
   ├─ Entropia > 7.0 + Themida/VMProtect → Reportar OEP manual
   └─ Entropia alta + Unknown → Recomendar Scylla dump
```

## Notas Tecnicas

- **Entropia de Shannon**: 0-8 bits/simbolo. Valores > 7.0 indicam compressão/criptografia.
- **OEP** (Original Entry Point): endereco de entrada do codigo original, nao do packer.
- **Scylla**: ferramenta para dump de memoria + reconstrucao de IAT apos unpack manual.

---

**Auto-Unpacker v2.1 — Packets detected, strategies recommended, OEP mapped.** 🐀
