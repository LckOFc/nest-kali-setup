"""Install Google Antigravity SDK and verify setup"""
import subprocess, sys, os

print("=" * 60)
print("  AGY.EXE SETUP VERIFICATION")
print("=" * 60)
print()

# 1. Check Python
print("[1/5] Checking Python...")
result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
print("  " + result.stdout.strip())

# 2. Check if SDK is installed
print("\n[2/5] Checking SDK installation...")
try:
    import google.antigravity
    print("  [OK] SDK installed: google.antigravity")
except ImportError:
    print("  [MISSING] SDK NOT installed - need to run: pip install google-antigravity")

# 3. Check agy.exe
print("\n[3/5] Checking agy.exe...")
agy_paths = [
    r"C:\Users\devel\AppData\Local\agy\bin\agy.exe",
    "agy.exe",
]
agy_found = False
for p in agy_paths:
    if os.path.exists(p):
        size = os.path.getsize(p)
        print("  [OK] Found: {} ({:.1f} MB)".format(p, size/1024/1024))
        agy_found = True
        break
if not agy_found:
    print("  [MISSING] agy.exe NOT found")

# 4. Check PATH
print("\n[4/5] Checking PATH...")
path = os.environ.get("PATH", "")
paths = path.split(";")
agy_in_path = any("agy" in p.lower() for p in paths)
print("  agy.exe in PATH: {}".format("Yes" if agy_in_path else "No"))
if agy_in_path:
    for p in paths:
        if "agy" in p.lower():
            print("    -> " + p)

# 5. Check dependencies
print("\n[5/5] Checking dependencies...")
deps = ["pydantic", "protobuf", "anyio", "mcp"]
for dep in deps:
    try:
        mod = __import__(dep.replace("-", "_"))
        ver = getattr(mod, "__version__", "unknown")
        print("  [OK] {}: {}".format(dep, ver))
    except ImportError:
        print("  [MISSING] {}: NOT installed".format(dep))

print()
print("=" * 60)
print("  SUMMARY")
print("=" * 60)

sdk_installed = False
try:
    import google.antigravity
    sdk_installed = True
except:
    pass

if sdk_installed and agy_found:
    print("""
  [OK] SETUP COMPLETO!
  
  Voce pode:
  1. Rodar: agy                    (modo interativo)
  2. Rodar: python test_agy.py     (teste rapido)
  3. Explorar: examples/           (33 exemplos)
""")
elif not sdk_installed:
    print("""
  [ACTION REQUIRED] FALTA INSTALAR O SDK
  
  Execute:
    pip install google-antigravity==0.1.16
  
  Depois teste:
    python -c "from google.antigravity import Agent; print('OK')"
""")
else:
    print("""
  [ACTION REQUIRED] AGY.EXE NAO ENCONTRADO
  
  O binario deve estar em:
    C:\\Users\\devel\\AppData\\Local\\agy\\bin\\agy.exe
""")

print("=" * 60)