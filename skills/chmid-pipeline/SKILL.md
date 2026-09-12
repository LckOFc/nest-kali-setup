---
name: chmid-pipeline
description: Pipeline orquestrador Chain-Heuristic-Multiple-Iteration-Debug que encadeia automaticamente todas as analises: deteccao de packer, unpacking, analise estatica, sandbox comportamental, comparacao fuzzy e geracao de relatorio final. V2.1: bug fix if_exists_ok -> exist_ok.
aliases:
  - pipeline
  - chain
  - automated
  - full-analysis
  - orchestrate
  - workflow
  - chmid
---

# CHMID Pipeline v2.1

Pipeline orquestrador que encadeia automaticamente todas as etapas de analise de engenharia reversa.

> **v2.1 changelog**: Fixed `if_exists_ok` -> `exist_ok` bug in `mkdir()` call.

## O Que o Pipeline Faz

```
Input: malware.exe
   │
   ├─→ [1] Initial Analysis    ← RE Toolkit (PE parsing, strings, imports)
   │        ↓
   ├─→ [2] Packer Detection    ← Auto-Unpacker (entropy, signatures)
   │        ↓
   ├─→ [3] Unpacking           ← UPX auto / Scylla manual hint
   │        ↓ (se unpack bem-sucedido)
   ├─→ [4] Re-analysis         ← RE Toolkit no resultado
   │        ↓
   ├─→ [5] Fuzzy Comparison    ← Fuzzy Hash (variant detection)
   │        ↓
   ├─→ [6] Behavioral Sandbox  ← Monitoramento comportamental
   │        ↓
   └─→ [7] Report Generation   ← PDF + JSON consolidado
         ↓
     Output: report_final.json
```

## Instalacao

```bash
# Dependencias principais
pip install pefile lief psutil httpx aiohttp
# Para sandbox comportamental:
pip install wmi    # Windows apenas
```

## Comandos

```bash
# Pipeline completo (7 estagios)
python chmid_pipeline.py C:\malware.exe

# Pipeline rapido (pula sandbox)
python chmid_pipeline.py C:\malware.exe --fast

# Com comparacao fuzzy contra baseline
python chmid_pipeline.py C:\malware.exe --baseline C:\known_samples\

# Salvar resultados intermediarios
python chmid_pipeline.py C:\malware.exe --save-stages ./stages/

# Output em JSON
python chmid_pipeline.py C:\malware.exe --json --output result.json
```

## Uso via Python

```python
from skills.chmid_pipeline.chmid_pipeline import CHMIDPipeline

pipeline = CHMIDPipeline(
    baseline_dir="C:\\known_malware\\",
    output_dir="./pipeline_output",
    fast_mode=False,
    save_intermediate=True
)
result = await pipeline.run("malware.exe")
# {stages, context, final_report, timing}
```

## Estagios do Pipeline

| Estágio | Duração Media | Saidas |
|---------|---------------|--------|
| 1. Initial Analysis | 2-5s | PE info, imports, strings, hashes |
| 2. Packer Detection | 1-2s | Packertype, entropy, strategy |
| 3. Unpacking | 5-30s | Arquivo desempacotado (se possivel) |
| 4. Re-analysis | 2-5s | Nova analise pos-unpack |
| 5. Fuzzy Compare | 1-3s | Similaridade com baseline |
| 6. Behavioral Sandbox | 30-120s | Threat score, eventos |
| 7. Report | 1-2s | PDF + JSON consolidado |

**Total estimado:** 40-165 segundos por amostra

---

**CHMID Pipeline v2.1 — Analise completa automatizada.** 🐀
