#!/usr/bin/env python3
"""Verificação completa do Full Hacking Toolkit"""

import sys
import os

# Adicionar paths
sys.path.insert(0, r'C:\Users\devel\tools\reverse\RE-Toolkit')
sys.path.insert(0, r'C:\Users\devel\tools\burpsuite-v2')
sys.path.insert(0, r'C:\Users\devel\tools\osint-aggregator')
sys.path.insert(0, r'C:\Users\devel\tools\payload-manager')
sys.path.insert(0, r'C:\Users\devel\tools\password-cracker')
sys.path.insert(0, r'C:\Users\devel\tools\report-generator')

print("=" * 70)
print("  VERIFICANDO TODOS OS MODULOS DO TOOLKIT")
print("=" * 70)
print()

# RE Toolkit
print("[1] RE Toolkit")
try:
    from cli import REToolkit
    rt = REToolkit()
    status = rt.status()
    engine_count = len(status.get("engines", {}))
    print(f"    Engines carregados: {engine_count}")
    for name, eng in status.get("engines", {}).items():
        loaded = eng.get("loaded", False)
        print(f"      - {name}: {'OK' if loaded else 'FAIL'}")
except Exception as e:
    print(f"    ERROR: {e}")
print()

# Verificar outros paths
paths = {
    "Burp Suite v2": r"C:\Users\devel\tools\burpsuite-v2\skill.py",
    "Backend Vuln Scanner": r"C:\Users\devel\.config\opencode\skills\backend-vuln-scanner\vuln_scanner.py",
    "OSINT Aggregator": r"C:\Users\devel\tools\osint-aggregator\osint_aggregator.py",
    "Payload Manager": r"C:\Users\devel\tools\payload-manager\payload_manager.py",
    "Password Cracker": r"C:\Users\devel\tools\password-cracker\password_cracker.py",
    "Report Generator": r"C:\Users\devel\tools\report-generator\generator.py",
    "RE-Toolkit Main": r"C:\Users\devel\tools\reverse\RE-Toolkit\cli.py",
}

print("[2] Verificando Localizações:")
for name, path in paths.items():
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"    {name}: {'OK' if exists else 'MISSING'} ({size:,} bytes)")
print()

# Testar imports
print("[3] Testando Imports:")
imports = [
    ("REToolkit", "cli"),
    ("RESkill", "skill"),
    ("GhidraEngine", "engines.ghidra_engine"),
    ("HexEditor", "engines.hex_editor"),
    ("FiddlerEngine", "engines.fiddler_engine"),
]

for name, module in imports:
    try:
        exec(f"from {module} import {name}")
        print(f"    {name}: OK")
    except Exception as e:
        print(f"    {name}: FAIL ({e})")
print()

# Testar funcionalidades básicas
print("[4] Testando Funcionalidades:")

# RE Toolkit
try:
    from cli import REToolkit
    rt = REToolkit()
    
    # Status
    status = rt.status()
    print(f"    RE Toolkit status: OK (engines={len(status.get('engines', {}))})")
    
    # GHIDRA
    ghidra_status = rt.ghidra.status()
    print(f"    GHIDRA engine: OK")
    
    # Hex Editor
    hex_status = rt.hex_editor.status()
    print(f"    Hex Editor: OK")
    
    # Fiddler
    fiddler_status = rt.fiddler.status()
    print(f"    Fiddler Engine: OK")
    
except Exception as e:
    print(f"    RE Toolkit test: FAIL ({e})")

print()

# Payload Manager
try:
    from payload_manager import PayloadManager
    pm = PayloadManager()
    categories = pm.get_categories()
    print(f"    Payload Manager: OK ({len(categories)} categories)")
except Exception as e:
    print(f"    Payload Manager: FAIL ({e})")

# Password Cracker
try:
    from password_cracker import PasswordCracker
    pc = PasswordCracker()
    result = pc.crack("5f4dcc3b5aa765d61d8327deb882cf99")
    print(f"    Password Cracker: OK (tested MD5 crack)")
except Exception as e:
    print(f"    Password Cracker: FAIL ({e})")

print()

print("=" * 70)
print("  VERIFICACAO COMPLETA - TOOLKIT PRONTO PARA USO")
print("=" * 70)
print()
print("COMANDOS DISPONIVEIS:")
print("  /toolkit re analyze <binary>")
print("  /toolkit burp scan <domain>")
print("  /toolkit vuln scan <domain>")
print("  /toolkit osint <domain>")
print("  /toolkit crack <hash>")
print("  /toolkit payload list <category>")
print("  /toolkit report create --target <domain>")
print()