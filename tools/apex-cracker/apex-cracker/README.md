# APEX Cracker — Modo 4070

Ferramenta completa de cracking de hashes offline com múltiplas estratégias.

## Hash Types Suportados

| Type | Length | Exemplo |
|------|--------|---------|
| MD5 | 32 chars | `5f4dcc3b5aa765d61d8327deb882cf99` |
| SHA1 | 40 chars | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| SHA256 | 64 chars | `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8` |
| SHA512 | 128 chars | `b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86` |
| NTLM | 32 chars | Same format as MD5 |
| MD4 | 32 chars | Not in standard hashlib |
| RIPEMD160 | 40 chars | |
| CRC32 | 8 chars | `fcde2b2edba56bf4` |
| BCRYPT | 60 chars | `$2b$12$...` |
| MD5-Unix | `$1$...` | Unix crypt MD5 |
| SHA256-Unix | `$5$...` | Unix crypt SHA256 |
| SHA512-Unix | `$6$...` | Unix crypt SHA512 |

## Estratégias de Ataque

| Método | Descrição | Uso |
|--------|-----------|-----|
| dict | Dicionário + regras de transformação | Principal |
| mask | Ataque por padrão/máscara | Quando sabe o formato |
| incremental | Força bruta de todas combinações | Palavras curtas |
| all | Tenta todas as estratégias | Padrão |

## Regras de Transformação (Rule Engine)

O rule engine aplica automaticamente:
- **Leetspeak**: a→4/@, e→3, i→1/!, o→0, s→5/$, t→7/+
- **Capitalização**: password → Password → PASSWORD
- **Suffixes**: +1, +123, +2024, +!, +#
- **Reversão**: password → dovastap
- **Duplicação**: password → passwordpassword
- **Swap case**: password → pASSWORD

## Comandos

```bash
# Crack single hash
python apex_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99

# Com wordlist customizada
python apex_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99 --wordlist custom.txt

# Múltiplos hashes de arquivo
python apex_cracker.py --file hashes.txt

# Parallel cracking (N threads)
python apex_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99 --threads 8

# Mask attack
python apex_cracker.py --mask ?l?l?l?d --hash test

# JSON output
python apex_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99 --json

# Info dos hashes suportados
python apex_cracker.py --info

# Stats após cracking
python apex_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99 --stats

# Salvar resultados
python apex_cracker.py --file hashes.txt --output results.txt
```

## Uso via Python

```python
from tools.apex_cracker import APEXCracker, HashDetector, WordlistManager

# Cracking básico
cracker = APEXCracker(threads=4)
result = cracker.crack("5f4dcc3b5aa765d61d8327deb882cf99")
print(f"Plaintext: {result.plaintext}")

# Com wordlist custom
cracker = APEXCracker()
result = cracker.crack(hash_val, wordlist_path="custom.txt")

# Arquivo múltiplo
results = cracker.crack_file("hashes.txt")

# Stats
stats = cracker.get_stats()
print(stats["success_rate"])
print(stats["cracks_per_second"])
```

## Performance

```
Hardware: Testado em CPU multi-core
Threads: 4-8 recomendados
Velocidade: ~20k+ attempts/segundo (depende do hash type)
Wordlist builtin: 400+ palavras + 17 variações cada = ~7k candidates
```

## Dependências

Python 3.8+ — Nenhuma dependência externa necessária (usa apenas stdlib)

---

**APEX Cracker v4070 — Hashes quebrados, senhas reveladas.** 🐀
