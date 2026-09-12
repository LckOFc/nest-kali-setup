"""Reverse engineer agy.exe - Full binary analysis"""
import struct, re, os

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)
print(f"=== AGY.EXE BINARY ANALYSIS ===")
print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print()

with open(exe_path, 'rb') as f:
    header = f.read(64)
    pe_off = struct.unpack('<I', header[60:64])[0]
    print(f"PE offset: 0x{pe_off:x}")
    
    f.seek(pe_off)
    pe_sig = f.read(4)
    print(f"PE signature: {pe_sig}")
    
    coff = f.read(20)
    machine, num_sections, timestamp, sym_ptr, num_syms, opt_header_size, flags = struct.unpack('<HHIIIHH', coff)
    machine_name = "AMD64" if machine == 0x8664 else "x86" if machine == 0x14c else f"0x{machine:x}"
    print(f"Machine: {machine_name}")
    print(f"Sections: {num_sections}")
    print(f"Timestamp: {timestamp}")
    print(f"Symbol count: {num_syms}")
    print(f"Opt header size: {opt_header_size}")
    print(f"Flags: {flags:#x}")
    
    f.seek(pe_off + 24)
    magic = struct.unpack('<H', f.read(2))[0]
    is_pe32_plus = magic == 0x20b
    print(f"\nOptional header magic: {'PE32+' if is_pe32_plus else 'PE32'}")
    
    ep = struct.unpack('<I', f.read(4))[0]
    image_size = struct.unpack('<I', f.read(4))[0]
    print(f"Entry point: 0x{ep:x}")
    print(f"Image size: {image_size:,} bytes ({image_size/1024/1024:.1f} MB)")
    
    # Data directories start at offset 96 in optional header (for PE32+)
    dd_start = pe_off + 24 + 96
    f.seek(dd_start)
    dirs = []
    for i in range(16):
        rva, sz = struct.unpack('<II', f.read(8))
        dirs.append((rva, sz))
        names = ['EXPORT', 'IMPORT', 'RESOURCE', 'EXCEPTION', 'SECURITY', 'BASERELOC',
                 'DEBUG', 'ARCHITECTURE', 'GLOBALPTR', 'TLS', 'LOAD_CONFIG', 'BOUND_IMPORT',
                 'IAT', 'DELAY_IMPORT', 'COM_DESCRIPTOR', 'RESERVED']
        if rva or sz:
            print(f"  {names[i]:15s} RVA=0x{rva:x} Size={sz}")
    
    # Export directory
    export_rva, export_size = dirs[0]
    import_rva, import_size = dirs[1]
    
    print(f"\n=== IMPORTS ===")
    if import_rva and import_size > 0:
        # Find which section contains import_rva
        section_table_start = pe_off + 248
        f.seek(section_table_start)
        sections = []
        for i in range(num_sections):
            sec = f.read(40)
            name = sec[0:8].split(b'\x00')[0].decode('ascii', errors='replace')
            vsize, vaddr, rawsize, rawptr, chars = struct.unpack('<IIIII', sec[8:28])
            sections.append({'name': name, 'vaddr': vaddr, 'rawsize': rawsize, 'rawptr': rawptr, 'chars': chars})
        
        imp_sec = None
        for sec in sections:
            end = sec['vaddr'] + max(sec['vsize'], sec['rawsize'])
            if sec['vaddr'] <= import_rva < end:
                imp_sec = sec
                break
        
        if imp_sec:
            import_base = imp_sec['rawptr'] + (import_rva - imp_sec['vaddr'])
            f.seek(import_base)
            imp_count = 0
            while imp_count < 300:
                desc = f.read(20)
                if len(desc) < 20 or desc == b'\x00' * 20:
                    break
                fwd_ref, timestamp, forwarder_chains, name_rva, first_thunk = struct.unpack('<IIIII', desc)
                if name_rva == 0:
                    break
                name_pos = name_rva - imp_sec['vaddr'] + imp_sec['rawptr']
                f.seek(name_pos)
                mod_name = b''
                while True:
                    c = f.read(1)
                    if c == b'\x00':
                        break
                    mod_name += c
                imp_count += 1
                print(f"  [{imp_count:3d}] {mod_name.decode('ascii', errors='replace')}")
            
            if imp_count >= 300:
                print(f"  ... and more (stopped at 300)")
    
    # Read ALL strings from entire file
    print(f"\n=== FULL STRING EXTRACTION ({file_size} bytes) ===")
    all_strings = set()
    chunk_size = 16 * 1024 * 1024
    with open(exe_path, 'rb') as f:
        for offset in range(0, min(file_size, 200 * 1024 * 1024), chunk_size):
            data = f.read(chunk_size)
            if not data:
                break
            for match in re.finditer(rb'([\x20-\x7e]{5,})', data):
                s = match.group(1).decode('ascii')
                all_strings.add(s)
    
    # Categorize strings
    categories = {}
    for s in all_strings:
        sl = s.lower()
        if any(kw in sl for kw in ['http://', 'https://', 'ftp://']):
            cat = 'urls'
        elif '@' in s and ('.' in s or '://' in s):
            cat = 'emails_urls'
        elif s.startswith('--') or (s.startswith('-') and len(s) > 3 and not s[1].isalpha()):
            cat = 'cli_flags'
        elif any(kw in sl for kw in ['kuroko', 'sombra', 'ratman', 'orchestrator', 'worker', 'synthesizer', 'segment', 'agentic', 'pipeline', 'swarm', 'citc', 'handoff']):
            cat = 'agents_system'
        elif any(kw in sl for kw in ['agnes', 'deepseek', 'openai', 'anthropic', 'ollama', 'lm studio', 'openrouter', 'claude', 'gpt-', 'gemini', 'llama', 'model_id', 'provider']):
            cat = 'llm_providers'
        elif any(kw in sl for kw in ['session', 'chat', 'command', 'tool_call', 'forge', 'bridge', 'terminal', 'tui', 'dashboard', 'webhook', 'mcp_server', 'skill', 'artifact', 'transcript', 'prompt']):
            cat = 'features_core'
        elif any(kw in sl for kw in ['.config', '.local', 'appdata', 'shadow', 'opencode', 'cargo', 'rustup', 'agent', 'workspace']):
            cat = 'paths_config'
        elif any(kw in sl for kw in ['error:', 'failed to', 'unable to', 'unauthorized', 'not found', 'timeout', 'connection refused', 'permission', 'denied']):
            cat = 'errors_messages'
        elif any(kw in sl for kw in ['fn ', 'struct ', 'impl ', 'pub ', 'let ', 'async ', 'match ', 'enum ', 'trait ', 'use ', 'mod ']):
            cat = 'rust_code'
        elif any(kw in sl for kw in ['function ', 'const ', 'await ', 'fetch(', 'document.', 'navigator.', 'window.']):
            cat = 'javascript'
        elif any(kw in sl for kw in ['select ', 'insert into', 'create table', 'primary key', 'foreign key']):
            cat = 'sql'
        elif any(kw in sl for kw in ['.exe', '.dll', '.py', '.json', '.md', '.toml', '.yaml', '.yml', '.rs', '.js', '.ts', '.html', '.css']):
            cat = 'file_exts'
        elif len(s) > 100:
            cat = 'long_strings'
        else:
            continue
        if cat not in categories:
            categories[cat] = set()
        categories[cat].add(s)
    
    for cat, strings in sorted(categories.items()):
        items = sorted(strings, key=len, reverse=True)
        print(f'\n[{cat}] ({len(items)} items)')
        for s in items[:15]:
            print(f'  {s[:110]}')
        if len(items) > 15:
            print(f'  ... and {len(items)-15} more')
    
    # Also look for embedded files (zip/tar/etc)
    print(f'\n=== EMBEDDED FILE SEARCH ===')
    with open(exe_path, 'rb') as f:
        data = f.read(min(file_size, 200*1024*1024))
    
    # Look for common archive signatures
    archives = {
        b'PK\x03\x04': 'ZIP',
        b'\x1f\x8b': 'GZIP',
        b'__ARCHIVE__': 'ARCHIVE',
        b'BZ': 'BZIP2',
        b'\xfd7zXZ': 'XZ',
        b'Rar!\x1a\x07': 'RAR',
        b'\x7fELF': 'ELF',
    }
    for sig, fmt in archives.items():
        count = data.count(sig)
        if count > 0:
            print(f'  {fmt}: found {count} occurrence(s)')
    
    # Look for .NET/Mono
    if b'.NET' in data or b'.NETCoreApp' in data:
        print('  .NET detected')
    
    # Look for Go runtime
    if b'runtime.main' in data or b'go build' in data:
        print('  Go runtime detected')
    
    # Look for Python
    if b'Python' in data and b'python' in data.lower():
        print('  Python references detected')
    
    # Look for Bun/Deno
    if b'Bun' in data or b'bun.sh' in data.lower():
        print('  Bun runtime detected')
    
    # Check for WASM
    wasm_magic = b'\x00asm'
    if wasm_magic in data:
        print('  WASM module detected')
        # Count WASM modules
        wasm_count = data.count(wasm_magic)
        print(f'  WASM modules: {wasm_count}')

print("\n=== DONE ===")