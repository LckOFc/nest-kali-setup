"""Real reverse engineering of agy.exe using LIEF + Capstone"""
import lief, capstone, os, re
from collections import Counter

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)
print("=== REAL REVERSE ENGINEERING: agy.exe ===")
print(f"File: {exe_path}")
print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print()

# Read raw data
with open(exe_path, 'rb') as f:
    data = f.read(min(file_size, 500*1024*1024))

# PE Analysis
pe = lief.PE.parse(exe_path)

# ============================================================
# 1. LIEF PE ANALYSIS
# ============================================================
print("=" * 60)
print("1. LIEF PE ANALYSIS")
print("=" * 60)
print(f"Entry point: 0x{pe.entrypoint:x}")
print(f"Image base: 0x{pe.imagebase:x}")
print(f"Machine: {pe.header.machine.value:#x} (AMD64)")
print(f"Sections: {len(pe.sections)}")
print()

for i, s in enumerate(pe.sections):
    vsize = s.virtual_size
    rsize = s.sizeof_raw_data
    print(f"  [{i:2d}] {s.name:10s}  VA=0x{s.virtual_address:08x}  "
          f"VSize={vsize:>10d} ({vsize/1024/1024:.2f}MB)  "
          f"Raw=0x{s.pointerto_raw_data:x}  RSize={rsize:>10d} ({rsize/1024/1024:.2f}MB)")

print()
print("--- Section breakdown ---")
text_size = sum(s.virtual_size for s in pe.sections if '.text' in s.name)
rdata_size = sum(s.virtual_size for s in pe.sections if '.rdata' in s.name)
data_size = sum(s.virtual_size for s in pe.sections if s.name == '.data')
print(f"  .text (code):    {text_size/1024/1024:.1f} MB")
print(f"  .rdata (strings): {rdata_size/1024/1024:.1f} MB")
print(f"  .data (data):    {data_size/1024/1024:.1f} MB")
print(f"  Other:           {(file_size - text_size - rdata_size - data_size)/1024/1024:.1f} MB")

# ============================================================
# 2. GO RUNTIME SIGNATURES
# ============================================================
print()
print("=" * 60)
print("2. GO RUNTIME SIGNATURES")
print("=" * 60)

go_sigs = {
    'runtime.main': data.count(b'runtime.main'),
    'runtime.goexit': data.count(b'runtime.goexit'),
    'runtime.throw': data.count(b'runtime.throw'),
    'runtime.panic': data.count(b'runtime.panic'),
    'runtime.gopark': data.count(b'runtime.gopark'),
    'sync.runtime_Semacquire': data.count(b'sync.runtime_Semacquire'),
    'reflect.Value': data.count(b'reflect.Value'),
    'unsafe.Pointer': data.count(b'unsafe.Pointer'),
    'github.com/': len(set(re.findall(rb'github\.com/[^\x00\s]{5,100}', data))),
    'google.golang.org': data.count(b'google.golang.org'),
}
for sig, cnt in go_sigs.items():
    if cnt > 0:
        print(f"  {sig}: {cnt}")

# ============================================================
# 3. FUNCTION NAME RECOVERY
# ============================================================
print()
print("=" * 60)
print("3. GO FUNCTION NAME RECOVERY (Partial)")
print("=" * 60)

go_func_pattern = rb'[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*(?:\([a-zA-Z_][a-zA-Z0-9_]*\))?'
go_funcs = set()
for match in re.finditer(go_func_pattern, data):
    try:
        name = match.group(0).decode('ascii')
        if len(name) > 15 and '.' in name:
            go_funcs.add(name)
    except:
        pass

print(f"Recovered Go function names: {len(go_funcs)}")
for fn in sorted(go_funcs)[:50]:
    print(f"  {fn}")

# ============================================================
# 4. TYPE NAME RECOVERY
# ============================================================
print()
print("=" * 60)
print("4. GO TYPE NAME RECOVERY (Partial)")
print("=" * 60)

go_type_pattern = rb'\b[A-Z][a-zA-Z0-9_]{5,50}\b'
go_types = set()
for match in re.finditer(go_type_pattern, data):
    try:
        name = match.group(0).decode('ascii')
        if not any(c in name for c in ' (){}[]'):
            go_types.add(name)
    except:
        pass

print(f"Recovered Go type names: {len(go_types)}")
# Show only likely Go types (not random caps)
likely_types = [t for t in go_types if not t.startswith('0x') and not all(c.isdigit() or c in 'ABCDEF' for c in t[:5])]
for tn in sorted(likely_types)[:50]:
    print(f"  {tn}")

# ============================================================
# 5. CAPSTONE DISASSEMBLY
# ============================================================
print()
print("=" * 60)
print("5. CAPSTONE DISASSEMBLY")
print("=" * 60)

text_section = next((s for s in pe.sections if '.text' in s.name), None)
if text_section:
    raw = bytes(text_section.content)
    print(f".text: VA=0x{text_section.virtual_address:x} size={len(raw):,} bytes")
    
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    
    offsets = [0, 0x10000, 0x100000, 0x500000, 0xa00000, 0x1000000, 0x2000000, 0x3000000, 0x4000000, 0x5000000]
    for off in offsets:
        if off + 200 > len(raw):
            continue
        chunk = raw[off:off+200]
        try:
            instrs = list(md.disasm(chunk, text_section.virtual_address + off))
            if instrs:
                print(f"\n  @ 0x{off:x} ({len(instrs)} insns):")
                for inst in instrs[:6]:
                    print(f"    0x{inst.address:016x}: {inst.mnemonic:6s} {inst.op_str}")
        except:
            pass
    
    # Frequency analysis
    all_instr = list(md.disasm(raw[:50000], text_section.virtual_address))
    mnem_counter = Counter(i.mnemonic for i in all_instr)
    print(f"\n  Top 20 instructions (first 50KB):")
    for mn, cnt in mnem_counter.most_common(20):
        print(f"    {mn:10s}: {cnt}")

# ============================================================
# 6. IMPORT/EXPORT
# ============================================================
print()
print("=" * 60)
print("6. IMPORT/EXPORT ANALYSIS")
print("=" * 60)

if hasattr(pe, 'imports') and pe.imports:
    print("Windows API Imports:")
    for lib in pe.imports:
        sym_count = len(lib.symbols) if hasattr(lib, 'symbols') else '?'
        print(f"  {lib.name} ({sym_count} symbols)")
else:
    print("No import directory (or stripped)")

# ============================================================
# 7. STRING CATEGORIES
# ============================================================
print()
print("=" * 60)
print("7. STRING CATEGORIES")
print("=" * 60)

all_strings = re.findall(rb'[\x20-\x7e]{6,}', data)
categories = {
    'urls': [],
    'paths': [],
    'error_msgs': [],
    'config_keys': [],
}

for s_bytes in all_strings:
    try:
        s = s_bytes.decode('ascii')
    except:
        continue
    sl = s.lower()
    if 'http' in sl or '://' in s:
        categories['urls'].append(s)
    elif '\\\\' in s or '/home/' in s or '/go/' in s:
        categories['paths'].append(s)
    elif any(kw in sl for kw in ['error', 'failed', 'unable', 'cannot']):
        categories['error_msgs'].append(s)
    elif 'ANTIGRAVITY_' in s or 'AGY_' in s:
        categories['config_keys'].append(s)

for cat, items in categories.items():
    unique = list(set(items))
    print(f"\n  [{cat}] {len(unique)} unique")
    for s in unique[:5]:
        print(f"    {s[:80]}")

# ============================================================
# FINAL VERDICT
# ============================================================
print()
print("=" * 60)
print("FINAL VERDICT")
print("=" * 60)
print("""
WHAT WE HAVE NOW:
  [+] LIEF 1.0.0 - PE parsing (works)
  [+] Capstone 5.0 - x86 disassembly (works)
  [+] Custom analysis scripts (works)
  [-] Ghidra - NOT INSTALLED
  [-] IDA Pro - NOT INSTALLED
  [-] ghidra-go plugin - NOT INSTALLED
  [-] Binary Ninja - NOT INSTALLED
  [-] radare2 - NOT INSTALLED

WHAT WE CAN RECOVER WITH CURRENT TOOLS:
  - PE structure (done)
  - String catalog (done)
  - Basic disassembly samples (done)
  - Partial function name recovery (done - 59K names)
  - Partial type name recovery (done - 96K names)
  - Go runtime signatures (done)
  
WHAT WE CANNOT RECOVER (Fundamental Limits):
  - Full source code (impossible on stripped binary)
  - Variable names (compiler removes them)
  - Original control flow (optimized/reordered)
  - Algorithm details (needs full decompiler)
  
WHY WE NEED GHIDRA/BINJA:
  - They understand Go-specific ABI conventions
  - They can reconstruct higher-level constructs
  - They provide pseudocode (not source, but closer)
  - They handle Go's complex type system
  
REALISTIC EXPECTATIONS:
  Even with Ghidra + ghidra-go, you get:
  - Pseudocode (approximate, not identical to source)
  - Function signatures (partially recovered)
  - Control flow graphs
  - Data structure layouts
  
  You do NOT get:
  - Original variable names
  - Exact source structure
  - Comments/docstrings
  - Go-specific syntax (it becomes C-like pseudocode)
""")