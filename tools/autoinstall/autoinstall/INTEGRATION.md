"""
AutoInstall Agent Integration Guide
Como o agente Sombra/ratman4080 usa o AutoInstall automaticamente.
"""

# =========================================================================
# INTEGRATION WITH AGENT (Sombra / ratman4080)
# =========================================================================
# 
# Quando o usuario pedir algo como:
#   - "instala flask"
#   - "preciso do node"
#   - "bota o vscode aqui"
#   - "qual o melhor editor? sugere"
#   - "lista os pacotes python"
#
# O agente reconhece o padrao e chama automaticamente:
#
from engine import get_engine, KNOWN_PACKAGES

engine = get_engine()

# Exemplos de uso pelo agente:

# 1. Instalacao simples
result = engine.execute("instala flask")
# Output: [OK] Installed: flask

# 2. Multiplas pacotes
result = engine.execute("instala vite e eslint")
# Output: [OK] Installed: eslint, vite

# 3. Sugerir sem executar
result = engine.suggest("quero instalar um editor de codigo")
# Output: [SUGGEST] Command: winget install ... Microsoft.VisualStudioCode

# 4. Buscar pacotes
result = engine.search("flask")
# Output: [{'alias': 'flask', 'package_name': 'flask', 'manager': 'pip'}]

# 5. Listar todos
result = engine.list_all(manager='pip')
# Output: 44 python packages

# 6. Ver historico
history = engine.get_history(limit=10)
# Output: [{'timestamp': ..., 'packages': ['flask'], 'status': 'success'}, ...]

# 7. Stats
stats = engine.get_stats()
# Output: {'total_installs': 5, 'success_rate': '80.0%', ...}

# 8. Info do sistema
info = engine.info()
# Output: {'os': 'Windows', 'package_managers': {'pip': True, 'winget': True, ...}, ...}


# =========================================================================
# NATURAL LANGUAGE PATTERNS RECONHECIDOS
# =========================================================================
#
# Acoes:
#   "instala <pacote>"          -> instala
#   "instale <pacote>"          -> instala
#   "baixa <pacote>"            -> instala
#   "preciso do <pacote>"       -> instala
#   "bota <pacote> aki"         -> instala
#   "me da o <pacote>"          -> instala
#   "desinstala <pacote>"       -> desinstala
#   "remove <pacote>"           -> desinstala
#   "sugere <tipo>"             -> suggest
#   "busca <palavra>"           -> search
#   "lista <manager>"           -> list
#
# Multiplos:
#   "instala flask e django"    -> instala ambos
#   "instala vite e eslint"     -> instala ambos
#   "bota git e docker"         -> instala ambos
#
# Contexto automatico:
#   - "python" nos keywords -> usa pip
#   - "node/npm" nos keywords -> usa npm
#   - "windows app" -> usa winget
#   - padrao no Windows -> winget
#
# =========================================================================
# PACOTES CONHECIDOS (112+)
# =========================================================================
#
# Python (44):
#   flask, django, fastapi, numpy, pandas, torch, transformers,
#   jupyter, pytest, black, flake8, mypy, uvicorn, gunicorn,
#   pydantic, httpx, celery, sqlalchemy, scikit-learn, opencv...
#
# Node (18):
#   react, vue, next, vite, webpack, eslint, prettier, typescript,
#   jest, mocha, express, mongoose, axios, lodash, tailwindcss, nodemon...
#
# Windows Apps (25):
#   vscode, git, docker, postman, figma, discord, spotify, slack,
#   telegram, zoom, chrome, firefox, edge, obs, vlc, 7zip, notepad++,
#   powertoys, ffmpeg, helix, zed...
#
# CLI Tools (10):
#   ripgrep, fd, bat, fzf, starship, zoxide, jq, curl, wget...
#
# Languages (7):
#   go, rust, ruby, java, dotnet...
#
# =========================================================================
# COMANDOS CLI
# =========================================================================
#
#   python autoinstall.py "instala flask"
#   python autoinstall.py "instala vite e eslint" --dry-run
#   python autoinstall.py --search flask
#   python autoinstall.py --list
#   python autoinstall.py --list pip
#   python autoinstall.py --history
#   python autoinstall.py --stats
#   python autoinstall.py --info
#   python autoinstall.py "instala vscode" --suggest
#   python autoinstall.py "desinstala npm" --uninstall
#
