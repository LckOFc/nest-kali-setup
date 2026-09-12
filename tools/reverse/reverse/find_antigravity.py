"""Extract ANTIGRAVITY project info from agy.exe"""
import os, re

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
with open(exe_path, 'rb') as f:
    data = f.read(min(os.path.getsize(exe_path), 500*1024*1024))

print("=" * 60)
print("  ANTI-GRAVITY PROJECT IDENTIFIED!")
print("=" * 60)
print()

# Find all ANTIGRAVITY references
print("=== ANTIGRAVITY ENV VARS ===")
env_vars = re.findall(rb'ANTIGRAVITY[_A-Z]+[^\x00]{0,100}', data)
unique_envs = set()
for e in env_vars:
    try:
        text = e.decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_=\-]', ' ', text)
        text = ' '.join(text.split())
        if text.startswith('ANTIGRAVITY_'):
            unique_envs.add(text)
    except:
        pass
for e in sorted(unique_envs):
    print(f"  {e}")

# Find ANTIGRAVITY strings in context
print("\n=== ANTIGRAVITY CONTEXT ===")
antigravity_refs = list(re.finditer(rb'ANTIGRAVITY[^\x00]{0,200}', data))
contexts = set()
for m in antigravity_refs[:50]:
    try:
        text = m.group(0).decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_./\\\\-=!?,;:() ]', ' ', text)
        text = ' '.join(text.split())
        if len(text) > 10 and text not in contexts:
            contexts.add(text[:150])
    except:
        pass

for c in sorted(contexts)[:30]:
    print(f"  {c}")

# Find github.com/google-antigravity references
print("\n=== GITHUB ANTIGRAVITY REFS ===")
gh_refs = re.findall(rb'github\.com/google-antigravity[^\x00]{0,200}', data)
for g in gh_refs[:10]:
    try:
        text = g.decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_./\\\\-=]', ' ', text)
        text = ' '.join(text.split())
        print(f"  {text[:120]}")
    except:
        pass

# Search for the actual project name in different forms
print("\n=== PROJECT NAME VARIATIONS ===")
name_pats = [
    rb'antigravity',
    rb'AntiGravity',
    rb'ANTI_GRAVITY',
    rb'aigency',
    rb'AIGency',
]
for p in name_pats:
    count = data.count(p)
    if count > 0:
        print(f"  {p.decode()}: {count} refs")

# Check for the binary name patterns
print("\n=== BINARY NAME PATTERNS ===")
bin_pats = [
    rb'"agy"',
    rb'agy-cli',
    rb'agy_cli',
    rb'AGY_CLI',
    rb'binary_name',
    rb'BinaryName',
]
for p in bin_pats:
    matches = re.findall(p, data, re.I)
    for m in matches[:3]:
        try:
            text = m.decode('ascii', errors='replace')
            print(f"  {text}")
        except:
            pass

# Check for any version/build info related to antigravity
print("\n=== VERSION/BUILD INFO ===")
ver_pats = [
    rb'antigravity[^\x00]{0,100}',
    rb'version[^\x00]{0,100}',
    rb'build[^\x00]{0,100}',
]
for p in ver_pats:
    matches = list(re.finditer(p, data, re.I))
    for m in matches[:5]:
        try:
            start = max(0, m.start()-20)
            end = min(len(data), m.end()+80)
            ctx = data[start:end]
            text = ctx.decode('ascii', errors='replace')
            text = re.sub(r'[^a-zA-Z0-9_./\\\\-=!?,;:() ]', ' ', text)
            text = ' '.join(text.split())
            if len(text) > 15:
                print(f"  {text[:120]}")
        except:
            pass

# Check for any Go workspace info
print("\n=== GO WORKSPACE INFO ===")
work_pats = [
    rb'go\.work',
    rb'gopath',
    rb'GOPATH',
    rb'GOMODCACHE',
    rb'GoPath',
]
for p in work_pats:
    count = data.count(p)
    if count > 0:
        # Find context
        for m in re.finditer(p, data):
            start = max(0, m.start()-30)
            end = min(len(data), m.end()+100)
            ctx = data[start:end]
            try:
                text = ctx.decode('ascii', errors='replace')
                text = re.sub(r'[^a-zA-Z0-9_./\\\\-= ]', ' ', text)
                text = ' '.join(text.split())
                if len(text) > 10:
                    print(f"  {text[:120]}")
                    break
            except:
                pass

# Check for antigravity-related Go packages
print("\n=== ANTI-GRAVITY GO PACKAGES ===")
pkg_pats = re.findall(rb'google\.com/antigravity[^\x00]{0,200}', data)
for p in pkg_pats[:10]:
    try:
        text = p.decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_./\\\\-]', ' ', text)
        text = ' '.join(text.split())
        print(f"  {text[:120]}")
    except:
        pass

# Final summary
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
print("""
  PROJETO IDENTIFICADO: ANTI-GRAVITY
  
  O binário agy.exe é parte do projeto ANTIGRAVITY, que parece ser
  um sistema de agentes de IA desenvolvido pelo Google (referências
  a google-antigravity no GitHub).
  
  CARACTERÍSTICAS DO PROJETO:
  - Nome: Antigravity / AGY
  - Tipo: Multi-Agent AI Orchestration Platform
  - Framework: JetSki (proprietário)
  - Linguagem: Go + CGO
  - Tamanho: 180.7 MB
  
  PARA OBTER O CÓDIGO FONTE:
  1. O projeto pode ser interno do Google (não público)
  2. Verificar: github.com/google-antigravity/*
  3. O binário está completamente stripped
  4. Sem PDB disponível
  5. Sem source code embedded
  
  OPÇÕES DISPONÍVEIS:
  - Procurar repositórios públicos relacionados a "antigravity agent"
  - Verificar se há builds públicos no GitHub
  - Tentar obter acesso ao repositório fonte original
""")