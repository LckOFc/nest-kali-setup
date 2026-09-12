#!/usr/bin/env python3
"""
Complete Go Binary Analysis - Manual .gopclntab Parser
========================================================
Recupera TODAS as informações de funções Go do binário
"""

import struct
import re
import os
import sys
import json
from collections import defaultdict

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

BINARY_PATH = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
OUTPUT_DIR = r'C:\Users\devel\tools\reverse\go_deep_analysis'

print("=" * 70)
print("  GO BINARY DEEP ANALYSIS")
print("=" * 70)
print()

# Load binary
print("[*] Loading binary...")
with open(BINARY_PATH, 'rb') as f:
    data = f.read()
print(f"[+] Size: {len(data):,} bytes ({len(data)/1024/1024:.1f} MB)")
print()

# Find Go sections by searching for markers
print("[*] Finding Go sections...")

# Common Go section names (without leading dot)
section_names = [
    'gopclntab',
    'gosymtab', 
    'go.buildinfo',
    'go.version',
    'gosetctr',
    'noptrdata',
    'data',
    'rodata',
    'text',
]

sections_found = {}
for sec_name in section_names:
    # Search for null-terminated section name
    marker = sec_name.encode('ascii') + b'\x00'
    idx = 0
    while True:
        idx = data.find(marker, idx)
        if idx == -1:
            break
        
        # Extract full section name (might have prefix)
        start = idx
        while start > 0 and data[start-1:start] != b'\x00':
            start -= 1
        
        end = idx + len(marker)
        while end < len(data) and data[end:end+1] != b'\x00':
            end += 1
        
        full_name = data[start:end].decode('ascii', errors='replace')
        sections_found[full_name] = {
            'offset': start,
            'size': 0,  # Will calculate later
            'data_start': idx + len(marker)
        }
        print(f"  [FOUND] {full_name} at 0x{start:08X}")
        idx += 1

print()

# Calculate section sizes
for sec_name, sec_info in sections_found.items():
    start = sec_info['data_start']
    # Find next section or end
    next_offset = len(data)
    for other_name, other_info in sections_found.items():
        if other_info['offset'] > start and other_info['offset'] < next_offset:
            next_offset = other_info['offset']
    
    sec_info['size'] = next_offset - start
    sec_info['data'] = data[start:start + sec_info['size']]
    print(f"  {sec_name}: offset=0x{sec_info['offset']:08X}, size={sec_info['size']:,}")

print()

# Parse .gopclntab
pclntab_data = None
for name, info in sections_found.items():
    if 'pclntab' in name.lower():
        pclntab_data = info['data']
        print(f"[+] Using .gopclntab: {len(pclntab_data):,} bytes")
        break

functions = []

if pclntab_data:
    print()
    print("[*] Parsing .gopclntab...")
    
    # Try to parse Go function table
    # Format varies by Go version, but generally:
    # - funcID (1 byte)
    # - entryoff (4 bytes LE)
    # - ... more fields
    
    offset = 0
    max_offset = min(len(pclntab_data), 50 * 1024 * 1024)  # Max 50MB
    
    while offset + 13 < max_offset:
        try:
            # Try to read funcID
            func_id = pclntab_data[offset]
            
            # Read entryoff (4 bytes LE at offset+1)
            entryoff = struct.unpack_from('<I', pclntab_data, offset + 1)[0]
            
            # Read nameoff (4 bytes LE at offset+9 for Go 1.17+)
            nameoff = struct.unpack_from('<I', pclntab_data, offset + 9)[0]
            
            # Validate
            if entryoff > 0x2000000:  # Unreasonably large
                offset += 1
                continue
            
            # Extract function name
            func_name = ""
            if 0 < nameoff < len(pclntab_data):
                name_start = nameoff
                name_end = name_start
                while name_end < len(pclntab_data) and pclntab_data[name_end] != 0:
                    name_end += 1
                if name_end > name_start:
                    try:
                        func_name = pclntab_data[name_start:name_end].decode('ascii', errors='replace')
                    except:
                        pass
            
            if func_name and len(func_name) > 5:
                # Parse package and function name
                parts = func_name.split('.')
                pkg = parts[0] if parts else 'unknown'
                fname = parts[-1] if parts else func_name
                
                functions.append({
                    'index': len(functions),
                    'entry_offset': entryoff,
                    'name': func_name,
                    'package': pkg,
                    'function': fname,
                })
            
            # Advance - minimum entry size is about 13 bytes
            # But can vary, so we use a heuristic
            advance = max(13, func_id + 5)
            offset += advance
            
            if len(functions) % 10000 == 0 and len(functions) > 0:
                print(f"  Parsed {len(functions)} functions...")
            
            if len(functions) > 100000:
                print("  [!] Reached 100k functions limit")
                break
                
        except Exception as e:
            offset += 1
            continue

print(f"[+] Total functions parsed: {len(functions)}")
print()

# Also extract function names using regex as fallback
if len(functions) < 1000:
    print("[*] Using regex fallback...")
    func_pattern = re.compile(rb'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)')
    matches = func_pattern.findall(pclntab_data or data)
    
    for m in matches:
        try:
            name = m.decode('ascii')
            if len(name) > 5 and '.' in name:
                parts = name.split('.')
                functions.append({
                    'index': len(functions),
                    'entry_offset': 0,
                    'name': name,
                    'package': parts[0],
                    'function': parts[-1],
                })
        except:
            pass
    
    # Deduplicate
    seen = set()
    unique_funcs = []
    for f in functions:
        if f['name'] not in seen:
            seen.add(f['name'])
            unique_funcs.append(f)
    functions = unique_funcs
    
    print(f"[+] Functions after regex: {len(functions)}")

print()

# Group by package
by_package = defaultdict(list)
for func in functions:
    by_package[func['package']].append(func['function'])

print("[*] Top Packages:")
for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1]))[:40]:
    print(f"  {pkg:50s}: {len(funcs):4d} functions")

print()

# Extract source file references
print("[*] Extracting source file references...")
source_files = set()

# Pattern for Go source files
go_file_pattern = re.compile(rb'([a-zA-Z0-9_./\\-]+\.go)')
for match in go_file_pattern.finditer(data):
    try:
        path = match.group(1).decode('ascii', errors='replace')
        # Clean up path
        path = path.strip('/\\')
        if path and len(path) > 5:
            source_files.add(path)
    except:
        pass

print(f"[+] Source files found: {len(source_files)}")

# Show some source files
go_files = sorted([f for f in source_files if f.endswith('.go')])[:100]
print("[*] Sample Go source files:")
for f in go_files[:50]:
    print(f"    {f}")

print()

# Extract build info
print("[*] Extracting build information...")
build_info = {}

# Go version
version_match = re.search(rb'go1\.(\d+)\.(\d+)', data)
if version_match:
    build_info['go_version'] = f"go1.{version_match.group(1).decode()}.{version_match.group(2).decode()}"

# GOOS and GOARCH
goos_match = re.search(rb'GOOS[= ](\w+)', data)
if goos_match:
    build_info['GOOS'] = goos_match.group(1).decode()

goarch_match = re.search(rb'GOARCH[= ](\w+)', data)
if goarch_match:
    build_info['GOARCH'] = goarch_match.group(1).decode()

# Module path
module_match = re.search(rb'module\s+([^\s]+)', data)
if module_match:
    build_info['module'] = module_match.group(1).decode('ascii', errors='replace')

print("[+] Build info:")
for k, v in build_info.items():
    print(f"    {k}: {v}")

print()

# Save results
print("[*] Saving results...")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Save functions
funcs_file = os.path.join(OUTPUT_DIR, 'functions.json')
with open(funcs_file, 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(functions),
        'by_package': {pkg: funcs[:20] for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1]))},
        'functions': functions[:10000]  # First 10k
    }, f, indent=2, ensure_ascii=False)
print(f"  Saved: {funcs_file}")

# Save packages
pkgs_file = os.path.join(OUTPUT_DIR, 'packages.txt')
with open(pkgs_file, 'w', encoding='utf-8') as f:
    f.write("Go Packages in agy.exe\n")
    f.write("=" * 60 + "\n\n")
    for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1])):
        f.write(f"{pkg}: {len(funcs)} functions\n")
        for func in funcs[:10]:
            f.write(f"  - {func}\n")
        f.write("\n")
print(f"  Saved: {pkgs_file}")

# Save source files
files_file = os.path.join(OUTPUT_DIR, 'source_files.txt')
with open(files_file, 'w', encoding='utf-8') as f:
    f.write(f"Go Source Files ({len(go_files)} found)\n")
    f.write("=" * 60 + "\n\n")
    for src in go_files:
        f.write(f"{src}\n")
print(f"  Saved: {files_file}")

# Save build info
build_file = os.path.join(OUTPUT_DIR, 'build_info.json')
with open(build_file, 'w') as f:
    json.dump(build_info, f, indent=2)
print(f"  Saved: {build_file}")

print()
print("=" * 70)
print("  ANALYSIS COMPLETE")
print("=" * 70)
print()
print(f"Functions recovered: {len(functions):,}")
print(f"Packages found: {len(by_package)}")
print(f"Source files: {len(go_files)}")
print(f"Build info: {build_info}")
print()
print(f"Output directory: {OUTPUT_DIR}")
