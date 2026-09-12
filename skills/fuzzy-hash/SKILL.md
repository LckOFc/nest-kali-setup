---
name: fuzzy-hash
description: Sistema de hashing fuzzy (SSdeep/spamsum) para deteccao de similaridade entre samples. Detecta parentesco entre malware, variants, e arquivos semelhantes sem exigir identidade exata. V2.1: comparacao multi-partes com pesos.
aliases:
  - fuzzy
  - ssdeep
  - spamsum
  - similarity
  - variant-detect
  - parentage
  - hash-compare
---

# Fuzzy Hash Engine v2.1

Implementacao completa de hashing fuzzy para deteccao de similaridade entre samples.

> **v2.1**: Algoritmo de comparacao multi-parte com pesos (rolling 50%, context 30%, global 20%), suporte a batch compare e find_similar contra baseline.

## Instalacao

```bash
pip install ssdeep
# Versao nativa Python incluida no modulo
```

## Conceito

Hash tradicional (SHA256): `arquivo_identicos → mesmo_hash`
Hash fuzzy: `arquivos_parecidos → hash_semelhante`

Ideal para:
- Detectar variantes de malware
- Encontrar parentesco entre samples
- Duplicacao de indicadores (IOCs)
- Clusterizacao de amostras

## Comandos

```bash
# Calcular hash fuzzy de um arquivo
python fuzzy_hash.py C:\sample1.exe

# Comparar dois arquivos
python fuzzy_hash.py --compare C:\sample1.exe C:\sample2.exe

# Comparar diretório inteiro (par a par)
python fuzzy_hash.py --dir C:\samples --recursive

# Gerar relatorio de similaridade
python fuzzy_hash.py --report C:\samples --threshold 60

# Exportar para JSON/CSV
python fuzzy_hash.py --dir C:\samples --format json --output results.json
```

## Uso via Python

```python
from skills.fuzzy_hash.fuzzy_hash import FuzzyHashEngine

engine = FuzzyHashEngine(block_size=3)

# Hash de um arquivo
hash1 = engine.compute("sample1.exe")
# '3:Kn4eMR/...:KXMR:abcDEF:1234'

# Comparar dois hashes
result = engine.compare(hash1, hash2)
# {'similarity': 85.5, 'verdict': 'similar', 'breakdown': {...}}

# Batch compare
results = engine.batch_compare(["file1.exe", "file2.exe", "file3.exe"], threshold=50)
# [{'file_a': ..., 'file_b': ..., 'similarity': 72.3, 'verdict': 'similar'}, ...]

# Detectar similar a baseline
similar = engine.find_similar("new_sample.exe", baseline_hashes, threshold=60)
# ['baseline_hash_1', 'baseline_hash_3']
```

## Veredictos

| Similaridade | Veredito | Interpretacao |
|--------------|----------|---------------|
| 100.0 | identical | Mesma amostra |
| 95-99 | near-identical | Quase igual |
| 60-94 | similar | Parentesco forte |
| 30-59 | somewhat_similar | Relação fraca |
| <30 | dissimilar | Sem relacao |

## Formato do Hash

```
[block_size]:[rolling_hash]:[context_hash]:[global_hash]
Ex: 3:Kn4eMR/xLr8eMR/xLr8eMR:abcDEF123456:a3f2b8c9d0e1f2
```

- `block_size`: tamanho do bloco base (3, 64, 1024...)
- `rolling_hash`: fingerprint das regioes unicas (peso 50%)
- `context_hash`: fingerprint do header/footer (peso 30%)
- `global_hash`: SHA256 do arquivo completo (peso 20%)

## Exemplo de Uso

```python
# Detectar se novo sample é variante de conhecido
known_samples = {
    "emotet": engine.compute("emotet.exe"),
    "trickbot": engine.compute("trickbot.exe"),
    "cobalt_strike": engine.compute("cobalt_strike.exe")
}

new_sample_hash = engine.compute("new_sample.exe")

for name, known_hash in known_samples.items():
    result = engine.compare(new_sample_hash, known_hash)
    if result['similarity'] >= 60:
        print(f"ALERTA: {name} variante detectada! Similaridade: {result['similarity']}%")
```

---

**Fuzzy Hash Engine v2.1 — Parentesco identificado, variants mapeados.** 🐀
