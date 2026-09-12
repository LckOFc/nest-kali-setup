---
name: report-generator
description: Gerador de relatorios profissionais de pentest em Markdown, JSON e ASCII table. Entrada: resultados de scan em JSON. Saida: relatorio formatado com risk score, findings, recomendacoes. V2.1: multi-format export, executive summary auto-generated.
aliases:
  - report
  - relatorio
  - pentest-report
  - output
---

# Report Generator v2.1 — Relatorios Profissionais de Pentest

Gera relatorios formatados a partir de resultados de scans de vulnerabilidade.

> **v2.1**: Export multi-formato (markdown/json/ascii), executive summary auto-generated, risk score ponderado por severidade.

## Localizacao

```
C:\Users\devel\tools\report-generator\report_generator.py
```

## Comandos

```bash
# Gerar a partir de arquivo JSON
python report_generator.py --input scan_results.json

# Gerar a partir de target (minimo)
python report_generator.py --target example.com

# Especificar formato e saida
python report_generator.py --input results.json --format markdown -o report.md
python report_generator.py --input results.json --format json -o report.json
python report_generator.py --input results.json --format ascii

# Pipe de stdin
cat results.json | python report_generator.py --stdin -o report.md

# Ver exemplo de input
python report_generator.py --example
```

## Formatos

| Formato | Extensao | Descricao |
|---------|----------|-----------|
| Markdown | .md | Relatorio profissional com secoes |
| JSON | .json | Dados estruturados para integracao |
| ASCII | .txt | Tabela texto para terminal |

## Estrutura do Input JSON

```json
{
  "target": "example.com",
  "issues": [
    {"type": "SQLi", "severity": "Critical", "description": "...", "evidence": "...", "solution": "..."}
  ],
  "subdomains": ["www", "api"],
  "endpoints": ["/login", "/api"],
  "headers": {"Server": "nginx"}
}
```

## Saida do Relatorio

- **Risk Score** (0-100) calculado automaticamente ponderando severidade
- **Executive Summary** com avaliacao de risco geral
- **Risk Breakdown** por severidade (Critical/High/Medium/Low/Info)
- **Findings** detalhados com IDs (F-001, F-002...)
- **Recommendations** priorizadas por impacto
- **Raw Data** completo para integridade

## Uso via Python

```python
from tools.report_generator.report_generator import ReportGenerator

gen = ReportGenerator()
report = gen.generate({
    "target": "example.com",
    "issues": [...],
    "subdomains": [...]
})

# Exportar
gen.save_report(report, "report.md", "markdown")
markdown = gen.to_markdown(report)
json_data = gen.to_json(report)
ascii_table = gen.to_ascii_table(report)
```

---

**Report Generator v2.1 — Relatorios profissionais, decisoes informadas.** 🐀
