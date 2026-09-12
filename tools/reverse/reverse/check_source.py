"""Check if source code is embedded in agy.exe"""
import os, re, struct, zlib, bz2, io

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)
print(f"File: {exe_path}")
print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print()

with open(exe_path, 'rb') as f:
    data = f.read(min(file_size, 500*1024*1024))

# 1. Check for Go symbol table
print("=== GO SYMBOL TABLE ===")
# Go binaries have a .gopclntab section with symbol info
gopclntab = data.count(b'.gopclntab')
print(f"  .gopclntab references: {gopclntab}")

# Check for Go-specific debug sections
go_debug = [
    (b'.gosymtab', 'Go symbol table'),
    (b'.gopclntab', 'Go PC line table'),
    (b'.go.buildinfo', 'Go build info'),
    (b'go.build', 'Go build metadata'),
    (b'runtime.goexit', 'Go runtime'),
]
for sig, name in go_debug:
    count = data.count(sig)
    print(f"  {name}: {count}")

# 2. Check PE sections for debug info
print("\n=== PE DEBUG SECTIONS ===")
pe_off = struct.unpack('<I', data[60:64])[0]
f_obj = io.BytesIO(data)
f_obj.seek(pe_off)
f_obj.read(4)  # PE sig
coff = f_obj.read(20)
machine, num_sections, timestamp, sym_ptr, num_syms, opt_header_size, flags = struct.unpack('<HHIIIHH', coff)
print(f"  Symbol table pointer: 0x{sym_ptr:x}")
print(f"  Number of symbols: {num_syms}")
print(f"  Debug dir RVA: not checked (stripped)")

# 3. Look for embedded source files
print("\n=== EMBEDDED SOURCE FILES ===")
# Go embeds file paths in strings
go_file_patterns = [
    rb'[^\x00]{0,200}\.go[^\x00]{0,50}',
    rb'[^\x00]{0,200}\.mod[^\x00]{0,50}',
    rb'[^\x00]{0,200}\.sum[^\x00]{0,50}',
    rb'[^\x00]{0,200}\.proto[^\x00]{0,50}',
    rb'[^\x00]{0,200}BUILD[^\\x00]{0,100}',
    rb'[^\x00]{0,200}WORKSPACE[^\\x00]{0,100}',
]
for pat in go_file_patterns:
    matches = re.findall(pat, data)
    unique = set()
    for m in matches[:20]:
        try:
            text = m.decode('ascii', errors='replace')
            text = re.sub(r'[^a-zA-Z0-9_./\\-]', ' ', text)
            text = ' '.join(text.split())
            if len(text) > 10:
                unique.add(text)
        except:
            pass
    if unique:
        print(f"  Pattern {pat.decode()[:30]}: {len(unique)} unique")
        for u in sorted(unique)[:5]:
            print(f"    {u[:100]}")

# 4. Try to extract Go build info
print("\n=== GO BUILD INFO ===")
build_info = re.findall(rb'go build [^\x00]{0,200}', data)
for b in build_info[:5]:
    try:
        text = b.decode('ascii', errors='replace')
        print(f"  {text[:120]}")
    except:
        pass

# 5. Check for DWARF/debug info that might contain source
print("\n=== DEBUG/SOURCE INFO ===")
# Look for file paths that might be source locations
source_paths = re.findall(rb'(?:C:[/\\][^/\\s\x00]{10,200}|/[a-zA-Z][^/\\s\x00]{10,200})', data)
unique_paths = set()
for p in source_paths:
    try:
        text = p.decode('ascii', errors='replace')
        # Filter for source-like paths
        if any(text.endswith(ext) for ext in ['.go', '.mod', '.sum', '.proto', '.ts', '.js', '.py']):
            unique_paths.add(text)
        elif '.go/' in text or '/go/src/' in text or 'gopath' in text.lower():
            unique_paths.add(text)
    except:
        pass

print(f"  Source-like paths: {len(unique_paths)}")
for p in sorted(unique_paths)[:20]:
    print(f"    {p[:120]}")

# 6. Check for any actual Go source code
print("\n=== GO SOURCE CODE SEARCH ===")
# Look for complete Go source fragments (func + body)
go_source = re.findall(rb'func [a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)[^{]*\{[^}]{0,500}', data)
print(f"  Go function blocks: {len(go_source)}")
for s in go_source[:5]:
    try:
        text = s.decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_()\[\]{}.:;<>=+\-*/&|!?, \t\n]', ' ', text)
        text = ' '.join(text.split())
        if len(text) > 20:
            print(f"    {text[:150]}")
    except:
        pass

# 7. Check for any compressed source
print("\n=== COMPRESSED CONTENT ===")
# Try gzip decompression on all GZIP signatures
gzip_results = []
gzip_offsets = [m.start() for m in re.finditer(b'\x1f\x8b', data)]
for off in gzip_offsets[:20]:
    chunk = data[off:off+10000]
    try:
        decompressed = zlib.decompress(chunk, -15)
        gzip_results.append((off, len(decompressed), decompressed[:500]))
    except:
        pass

print(f"  Successfully decompressed: {len(gzip_results)}")
for off, size, content in gzip_results[:5]:
    try:
        text = content.decode('ascii', errors='replace')
        is_source = any(kw in text for kw in ['package ', 'func ', 'import ', 'struct ', 'type '])
        print(f"    0x{off:x}: {size} bytes {'(SOURCE-LIKE)' if is_source else ''}")
        if is_source:
            print(f"      {text[:200]}")
    except:
        pass

# 8. Final verdict
print("\n" + "=" * 60)
print("VERDICT")
print("=" * 60)

is_stripped = num_syms == 0
has_debug = any(data.count(s) > 0 for s in [b'.debug_info', b'DWARF', b'.gosymtab'])
has_source = len(go_source) > 0 or len(unique_paths) > 0

if is_stripped and not has_debug and not has_source:
    print("""
  BINARIO STRIPPED - CODIGO FONTE NAO ENCONTRADO
   
  O binario agy.exe foi compilado SEM informacoes de depuracao:
  - 0 simbolos no symbol table
  - Sem secoes .debug_info (DWARF removido)
  - Sem secoes .gosymtab/.gopclntab (Go symbols removidos)
  - Nao ha arquivos .go embutidos
   
  O que PODE ser recuperado:
  - Strings de erro e mensagens (ja extraidas)
  - Nomes de funcoes Go (parciais, via patterns)
  - Caminhos de arquivos fonte (limitado)
  - Estruturas de dados (via analisis de strings)
   
  Para obter o codigo fonte completo, seria necessario:
  1. Binario NAO stripped (com debug symbols)
  2. Ou acesso ao repositorio fonte original
  3. Ou engenharia reversa avancada (decompilador Go)
""")
elif has_source:
    print(f"\n  PARCIAL: {len(go_source)} blocos de codigo fonte possiveis")
    print(f"  {len(unique_paths)} caminhos de fonte encontrados")
else:
    print("\n  NENHUM CODIGO FONTE ENCONTRADO")
    print("  Binario esta completamente stripped.")