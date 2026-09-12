---
name: yara-generator
description: Gerador automatico de regras YARA a partir de samples. Analisa strings unicas, calcula entropia, gera condicionais otimizadas e escala regras para scan de diretórios. V2.1: escaping melhorado, tags support, condition optimization.
aliases:
  - yara
  - rule-gen
  - signature
  - pattern-match
  - malware-signature
---

# YARA Rule Generator v2.1

Gerador automatico de regras YARA a partir de amostras de malware/binarios.

> **v2.1**: Melhor escaping de caracteres especiais em strings YARA, suporte a tags meta, condição otimizada com 'of them' based em relevancia.

## Instalacao

```bash
pip install yara-python
# Para usar regras geradas:
# Install YARA CLI: https://virustotal.github.io/yara/
```

## Comandos

```bash
# Gerar regra a partir de sample
python yara_generator.py C:\malware.exe --name emotet_variant

# Gerar e escanear directory
python yara_generator.py C:\malware.exe --name test --scan C:\samples

# Ajustar parametros
python yara_generator.py C:\malware.exe --min-str-len 6 --max-rules 15

# Exportar para arquivo .yar
python yara_generator.py C:\malware.exe --name myrule --output rules.yar
```

## Uso via Python

```python
from skills.yara_generator.yara_generator import YaraRuleGenerator

generator = YaraRuleGenerator(min_string_length=4, max_rules=10)

# Gerar regra
rule = generator.generate_from_sample(
    "malware.exe",
    rule_name="emotet_family",
    tags=["malware", "emotet", "2024"]
)
print(rule.to_yara())

# Gerar multiplos regras para varios samples
rules = generator.generate_batch(
    ["sample1.exe", "sample2.exe", "sample3.exe"],
    prefix="family_"
)

# Escanear directory com regras geradas
from skills.yara_generator.yara_generator import YaraScanner
scanner = YaraScanner(rules_dir="./generated_rules")
results = await scanner.scan_directory("./suspect_files")
```

## Estrutura da Regra Gerada

```yara
rule emotet_variant {
    meta:
        description = "Generated from C:\\malware.exe"
        generated_date = "2024-01-15 10:30:00"
        hash_sha256 = "a3f2b8c9..."
        tags = "malware emotet 2024"

    strings:
        $s0 = "http://c2.server.com"
        $s1 = "Registry Run key persistence"
        $s2 = "Inject into svchost.exe"
        $s3 = "AES-256 encryption"

    condition:
        4 of them
}
```

## Strings Priorizadas

O gerador prioriza strings com base em:
1. **URLs** (http/https/ftp) — C2 communication
2. **API keys / tokens** — Credential extraction
3. **Registry paths** — Persistence mechanisms
4. **Suspicious APIs** — CreateRemoteThread, VirtualAllocEx, etc.
5. **LOLBins** — svchost.exe, rundll32.exe, regsvr32.exe
6. **File paths** — %APPDATA%, %TEMP%, Startup folders
7. **Crypto indicators** — CryptEncrypt, BCryptEncrypt, AES, RSA
8. **Base64 encoded** — Obfuscated payloads

## Limitacoes

- Regras geradas sao heuristicas — podem gerar falsos positivos
- Strings muito comuns (ex: "Windows") sao filtradas automaticamente
- Recomenda-se tuning manual antes de uso em producao

---

**YARA Rule Generator v2.1 — Signatures geradas, scan escalar.** 🐀
