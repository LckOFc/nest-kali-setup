---
name: ai-analysis
description: Pipeline de analise assistida por IA integrada ao toolkit. Usa LLM local (Ollama) ou API para triagem inteligente, geracao de hipoteses, sugestao de next-steps e avaliacao de risco de binarios. V2.1: contexto enriquecido, multi-modelo support.
aliases:
  - ai
  - llm
  - copilot
  - intelligence
  - assistant
  - smart-analyze
  - ai-re
---

# AI Analysis Pipeline v2.1

Pipeline de analise assistida por IA para engenharia reversa e analise de malware.

> **v2.1**: Contexto enriquecido com imports top-20, strings sample, entropy; suporte a multiplas URLs de LLM; fallback para modo offline com análsie heuristica.

## Instalacao

```bash
# LLM Local (recomendado)
# Instale Ollama: https://ollama.ai
ollama pull codellama:13b
# ou para code:
ollama pull deepseek-coder:6.7b

# Dependencias Python
pip install httpx aiohttp
```

## Configuracao

```bash
# Variaveis de ambiente
export AI_LLM_ENDPOINT="http://localhost:11434"  # Ollama
export AI_MODEL="codellama:13b"                  # Modelo
export AI_MAX_TOKENS=2048
export AI_TEMPERATURE=0.3
```

## Comandos

```bash
# Analise completa com IA
python ai_analysis.py C:\malware.exe

# Apenas hipoteses
python ai_analysis.py C:\malware.exe --hypotheses-only

# Sugestoes de proximos passos
python ai_analysis.py C:\malware.exe --next-steps

# Avaliacao de risco
python ai_analysis.py C:\malware.exe --risk-assessment

# Análise completa + relatorio
python ai_analysis.py C:\malware.exe --full --output report.json
```

## Uso via Python

```python
from skills.ai_analysis.ai_analysis import AIAnalysisPipeline

pipeline = AIAnalysisPipeline(
    llm_endpoint="http://localhost:11434",
    model="deepseek-coder:6.7b",
    max_tokens=2048,
    temperature=0.3
)

# Analise completa
result = await pipeline.analyze("malware.exe")
# {hypotheses, next_steps, risk_assessment, confidence, raw_output}

# Analise focada
hyp = await pipeline.generate_hypotheses(context)
steps = await pipeline.suggest_next_steps(context, hyp)
risk = await pipeline.assess_risk(context, hyp)
```

## Contexto Enriquecido

A IA recebe contexto estruturado:
- Hashes (MD5, SHA256) do arquivo
- Entropia das secoes PE
- Top 20 imports mais relevantes
- Strings relevantes (URLs, IPs, caminhos, APIs suspeitas)
- Indicadores suspeitos (LOLBins, criptografia, persistencia)
- Resultados de analisis anteriores (se disponiveis)

## Fluxo de Analise

```
1. Coleta contexto do binário (PE info, strings, imports)
2. Envia para LLM com prompt estruturado
3. Parseia resposta (JSON ou texto)
4. Valida e estrutura resultados
5. Retorna hipóteses, próximos passos e avaliação de risco
```

## Modos de Operacao

| Modo | Uso | Requisito |
|------|-----|-----------|
| Full | Analise completa com todas as etapas | LLM disponivel |
| Hypotheses-only | Somente hipoteses | LLM disponivel |
| Next-steps | Somente sugestoes | LLM disponivel |
| Risk-assessment | Somente avaliacao de risco | LLM disponivel |
| Offline | Analise heuristica sem LLM | Nenhum |

---

**AI Analysis Pipeline v2.1 — Inteligência aumentada, hipóteses geradas.** 🐀
