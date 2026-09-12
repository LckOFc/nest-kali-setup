---
name: password-cracker
description: Ferramenta de cracking de hashes offline. Suporta MD5, SHA1, SHA256, SHA512, NTLM, CRC32 com wordlist builtin e personalizada. V2.1: parallel cracking, improved wordlist.
aliases:
  - crack
  - hash
  - md5
  - sha
  - password
  - ntlm
---

# Password Cracker v2.1 — Offline Hash Cracker

Cracker de hashes offline com wordlist builtin expandida + suporte a wordlists personalizadas.

> **v2.1**: Cracking paralelo com ThreadPoolExecutor, wordlist builtin expandida (100+ palavras), suporte a hash multi-linha.

## Localizacao

```
C:\Users\devel\tools\password-cracker\password_cracker.py
```

## Comandos

```bash
# Crack single hash
python password_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99

# Com wordlist customizada
python password_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99 --wordlist custom.txt

# Multiple hashes from file
python password_cracker.py --file hashes.txt

# Parallel cracking (N threads)
python password_cracker.py 5f4dcc3b5aa765d61d8327deb882cf99 --threads 4

# Ver info dos hashes suportados
python password_cracker.py --info

# Ver estatisticas
python password_cracker.py --stats
```

## Hash Types Suportados

| Type | Length | Exemplo |
|------|--------|---------|
| MD5 | 32 chars | `5f4dcc3b5aa765d61d8327deb882cf99` |
| SHA1 | 40 chars | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| SHA256 | 64 chars | `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8` |
| SHA512 | 128 chars | `b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86` |
| NTLM | 32 chars | Same as MD5 format |
| CRC32 | 8 chars | `fcde2b2edba56bf4` |

## Wordlist

- Builtin: 100+ palavras mais usadas (password, 123456, admin, secret, etc)
- Custom: passe caminho via `--wordlist arquivo.txt`
- Locacoes buscadas: rockyou.txt, seclists, custom
- Formato: uma palavra por linha, comentarios com `#` ignorados

## Uso via Python

```python
from tools.password_cracker.password_cracker import PasswordCracker

cracker = PasswordCracker(threads=4)
result = cracker.crack("5f4dcc3b5aa765d61d8327deb882cf99")
# {'status': 'cracked', 'plaintext': 'password', 'time_ms': 2, ...}

# Multi-hash
results = cracker.crack_file("hashes.txt")
# [{'hash': ..., 'status': ..., 'plaintext': ...}, ...]
```

---

**Password Cracker v2.1 — Hashes quebrados, senhas reveladas.** 🐀
