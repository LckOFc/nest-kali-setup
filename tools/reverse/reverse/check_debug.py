"""Check debug info and source recovery in agy.exe"""
import struct, re, os, io

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)
print(f"File: {exe_path}")
print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print()

with open(exe_path, 'rb') as f:
    data = f.read(min(file_size, 500*1024*1024))

# PE Analysis
pe_off = struct.unpack('<I', data[60:64])[0]
f_obj = io.BytesIO(data)
f_obj.seek(pe_off)
f_obj.read(4)  # PE sig
coff = f_obj.read(20)
machine, num_sections, timestamp, sym_ptr, num_syms, opt_header_size, flags = struct.unpack('<HHIIIHH', coff)
magic = struct.unpack('<H', data[pe_off+24:pe_off+26])[0]
is_pe32_plus = magic == 0x20b

print(f"Symbols: {num_syms} (stripped={num_syms==0})")
print(f"Debug dir RVA: checking...")

# Read data directories
dd_start = pe_off + 24 + (96 if is_pe32_plus else 88)
f_obj.seek(dd_start)
dirs = []
for i in range(16):
    rva, sz = struct.unpack('<II', f_obj.read(8))
    dirs.append((rva, sz))

dir_names = ['EXPORT', 'IMPORT', 'RESOURCE', 'EXCEPTION', 'SECURITY', 'BASERELOC',
             'DEBUG', 'ARCHITECTURE', 'GLOBALPTR', 'TLS', 'LOAD_CONFIG', 'BOUND_IMPORT',
             'IAT', 'DELAY_IMPORT', 'COM_DESCRIPTOR', 'RESERVED']

debug_rva, debug_size = dirs[6]
print(f"  DEBUG: RVA=0x{debug_rva:x} Size={debug_size}")

# Find section containing debug dir
f_obj.seek(pe_off + 248)
sec_data = f_obj.read(num_sections * 40)
debug_section = None
for i in range(num_sections):
    sec = sec_data[i*40:(i+1)*40]
    name = sec[0:8].split(b'\x00')[0].decode('ascii', errors='replace')
    vaddr = struct.unpack('<I', sec[4:8])[0]
    rawptr = struct.unpack('<I', sec[12:16])[0]
    rawsize = struct.unpack('<I', sec[16:20])[0]
    vsize = struct.unpack('<I', sec[8:12])[0]
    if vaddr <= debug_rva < vaddr + max(rawsize, vsize):
        debug_section = (name, rawptr, rawptr + (debug_rva - vaddr), debug_size)
        print(f"  Found in section: {name} (raw_offset=0x{debug_section[2]:x})")
        break

if debug_section and debug_size > 0:
    doff = debug_section[2]
    debug_data = data[doff:doff+debug_size]
    
    # Parse IMAGE_DEBUG_DIRECTORY entries (28 bytes each)
    entry_count = debug_size // 28
    print(f"  Debug entries: {entry_count}")
    
    types = {1:'UNKNOWN',2:'COFF',3:'CODEVIEW',7:'FPO',8:'MISC',9:'EXCEPTION',10:'FIXUP',11:'OMAP_TO_SRC',12:'OMAP_FROM_SRC'}
    
    for j in range(min(entry_count, 10)):
        entry = debug_data[j*28:(j+1)*28]
        if len(entry) < 28:
            break
        chars, tstamp, major, minor, dtype, addr, size = struct.unpack('<IIHHIII', entry[:24])
        type_name = types.get(dtype, f"0x{dtype:x}")
        print(f"    [{j}] Type={type_name} Addr=0x{addr:x} Size={size}")
        
        if dtype == 3:  # CODEVIEW
            # Read CV signature
            sig_off = debug_section[1] + (addr - debug_section[0])
            if sig_off >= 0 and sig_off + 4 <= len(data):
                sig = data[sig_off:sig_off+4]
                print(f"        Signature: {sig}")
                if sig == b'RSDS':
                    print(f"        -> CODEVIEW PDB found! Contains source paths!")
                elif sig == b'NB10':
                    print(f"        -> NB10 debug format")
                elif sig == b'USHP':
                    print(f"        -> Universal PDB (PDB7)")
                else:
                    print(f"        -> Unknown CV format: {sig.hex()}")

print()
print("=" * 60)
print("CONCLUSAO")
print("=" * 60)
print()

if num_syms == 0 and debug_size == 0:
    print("  BINARIO COMPLETAMENTE STRIPPED")
    print()
    print("  O que foi feito:")
    print("  1. Analise completa do PE header")
    print("  2. Extract de todas as strings (>200MB analisados)")
    print("  3. Identificacao de arquitectura (Go + JetSki)")
    print("  4. Mapeamento de todas as funcionalidades")
    print()
    print("  O que NAO foi possivel:")
    print("  1. Extrair codigo fonte Go (binario stripped)")
    print("  2. Recuperar simbolos de funcoes")
    print("  3. Encontrar caminhos de arquivos fonte")
    print()
    print("  Para obter o codigo fonte, seria necessario:")
    print("  1. Binario NAO stripped (com debug symbols)")
    print("  2. Arquivo PDB (.pdb) associado")
    print("  3. Decompilador Go (ex: go-decompiler)")
    print("  4. Ou acesso ao repositório fonte original")
elif debug_size > 0:
    print(f"  DEBUG INFO ENCONTRADO ({debug_size} bytes)")
    print("  Possivel recuperar alguns simbolos e caminhos.")
else:
    print("  Sem debug info detectado.")