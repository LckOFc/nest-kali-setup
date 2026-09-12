#!/usr/bin/env python3
"""Deep analysis of agy.exe to extract ALL possible code"""

import re
from collections import Counter

BINARY = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'

print("=" * 70)
print("  AGY.EXE DEEP CODE EXTRACTION")
print("=" * 70)
print()

with open(BINARY, 'rb') as f:
    data = f.read()

print(f"Binary size: {len(data):,} bytes")
print()

# ============================================================
# PHASE 1: Check if source code is embedded
# ============================================================
print("[PHASE 1] Checking for embedded source code...")
print()

# Go compiler sometimes embeds file paths with line numbers
line_ref_pattern = re.compile(rb'"([^"]*\.go):\d+"')
line_refs = line_ref_pattern.findall(data)
print(f"  Go file references: {len(line_refs)}")
for ref in line_refs[:30]:
    try:
        print(f"    {ref.decode()}")
    except:
        pass
print()

# Check for actual Go source code patterns
source_indicators = {
    b'package main': 'Go package declaration',
    b'func main()': 'Go main function',
    b'import (': 'Go import block',
    b'func (': 'Go method',
    b'type struct': 'Go struct type',
    b'interface {': 'Go interface',
    b'go func': 'Go goroutine',
    b'chan ': 'Go channel',
    b'select {': 'Go select',
    b'defer ': 'Go defer',
    b'range ': 'Go range',
    b'if err != nil': 'Go error handling',
    b'return err': 'Go error return',
    b'_ = ': 'Go blank identifier',
}

print("  Source code indicators:")
for pattern, desc in source_indicators.items():
    count = data.count(pattern)
    status = "FOUND" if count > 0 else "NOT FOUND"
    print(f"    [{status}] {desc}: {count}")
print()

# ============================================================
# PHASE 2: Extract ALL meaningful strings
# ============================================================
print("[PHASE 2] Extracting all meaningful strings...")
print()

# Extract all ASCII strings >= 4 chars
strings = []
current = b''
for i, byte in enumerate(data):
    if 32 <= byte <= 126:
        current += bytes([byte])
    else:
        if len(current) >= 4:
            strings.append((i - len(current), current.decode('ascii', errors='replace')))
        current = b''

print(f"  Total strings extracted: {len(strings):,}")

# Categorize strings
categories = {
    'code_like': [],
    'config_like': [],
    'url_endpoint': [],
    'error_msg': [],
    'func_name': [],
    'type_name': [],
    'var_name': [],
    'path_file': [],
    'command': [],
    'flag': [],
    'log_msg': [],
    'sql_query': [],
    'regex': [],
    'json_field': [],
    'other': [],
}

for offset, s in strings:
    s_clean = s.strip()
    if not s_clean or len(s_clean) > 1000:
        continue
    
    # Code-like patterns
    if re.match(r'^func\s+\w+', s_clean):
        categories['func_name'].append(s_clean)
    elif re.match(r'^type\s+\w+\s+struct', s_clean, re.I):
        categories['type_name'].append(s_clean)
    elif re.match(r'^var\s+\w+', s_clean, re.I):
        categories['var_name'].append(s_clean)
    elif re.match(r'^const\s+\w+', s_clean, re.I):
        categories['var_name'].append(s_clean)
    elif 'interface' in s_clean.lower() and '{' in s_clean:
        categories['code_like'].append(s_clean)
    elif 'struct' in s_clean.lower() and '{' in s_clean:
        categories['code_like'].append(s_clean)
    
    # Config patterns
    elif re.match(r'^[\w.]+\s*[:=]\s*', s_clean):
        categories['config_like'].append(s_clean)
    
    # URLs and endpoints
    elif s_clean.startswith('http'):
        categories['url_endpoint'].append(s_clean)
    elif re.match(r'^/api/', s_clean):
        categories['url_endpoint'].append(s_clean)
    
    # Errors
    elif any(e in s_clean.lower() for e in ['error', 'failed', 'cannot', 'unable']):
        categories['error_msg'].append(s_clean)
    
    # File paths
    elif re.match(r'^[a-zA-Z]:\\', s_clean) or '/usr/' in s_clean or '/home/' in s_clean:
        categories['path_file'].append(s_clean)
    
    # Commands
    elif re.match(r'^agy[\s]', s_clean) or s_clean in ['run', 'install', 'login', 'status', 'version']:
        categories['command'].append(s_clean)
    
    # Flags
    elif re.match(r'^--[\w-]+', s_clean):
        categories['flag'].append(s_clean)
    
    # Log messages
    elif any(l in s_clean.lower() for l in ['info:', 'debug:', 'warn:', 'error:', 'trace:']):
        categories['log_msg'].append(s_clean)
    
    # SQL
    elif re.match(r'^(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)\s', s_clean, re.I):
        categories['sql_query'].append(s_clean)
    
    # JSON fields
    elif re.match(r'^"[a-zA-Z_][a-zA-Z0-9_]*"\s*:', s_clean):
        categories['json_field'].append(s_clean)
    
    else:
        categories['other'].append(s_clean)

print("  String categories:")
for cat, items in categories.items():
    unique = list(dict.fromkeys(items))
    if unique:
        print(f"    {cat:20s}: {len(unique):6,d} unique items")

print()

# ============================================================
# PHASE 3: Extract function names from pclntab
# ============================================================
print("[PHASE 3] Extracting Go function names...")
print()

# Go function names pattern: package.FunctionName
func_pattern = re.compile(rb'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)')
func_matches = func_pattern.findall(data)
func_names = list(dict.fromkeys([m.decode('ascii', errors='replace') for m in func_matches]))

print(f"  Function names found: {len(func_names)}")

# Group by package
by_package = {}
for fn in func_names:
    parts = fn.split('.')
    if len(parts) >= 2:
        pkg = parts[0]
        if pkg not in by_package:
            by_package[pkg] = []
        by_package[pkg].append(fn)

print(f"  Packages found: {len(by_package)}")
print()
print("  Top packages:")
sorted_pkgs = sorted(by_package.items(), key=lambda x: -len(x[1]))[:20]
for pkg, funcs in sorted_pkgs:
    print(f"    {pkg:50s}: {len(funcs):4d} functions")
    for f in funcs[:3]:
        print(f"      - {f}")
print()

# ============================================================
# PHASE 4: Extract interface definitions
# ============================================================
print("[PHASE 4] Extracting interfaces and types...")
print()

# Look for interface patterns
interface_pattern = re.compile(rb'(\w+)\s+interface\s*\{([^}]+)\}', re.DOTALL)
interfaces = interface_pattern.findall(data)
print(f"  Interfaces found: {len(interfaces)}")
for name, body in interfaces[:10]:
    try:
        print(f"    interface {name.decode()}:")
        for line in body.decode().split('\n')[:5]:
            print(f"      {line.strip()}")
    except:
        pass
print()

# Look for struct patterns
struct_pattern = re.compile(rb'type\s+(\w+)\s+struct\s*\{([^}]+)\}', re.DOTALL)
structs = struct_pattern.findall(data)
print(f"  Structs found: {len(structs)}")
for name, body in structs[:10]:
    try:
        print(f"    type {name.decode()}:")
        for line in body.decode().split('\n')[:5]:
            print(f"      {line.strip()}")
    except:
        pass
print()

# ============================================================
# PHASE 5: Extract all constants and variables
# ============================================================
print("[PHASE 5] Extracting constants and variables...")
print()

const_pattern = re.compile(rb'const\s+(\w+)\s*=\s*([^;\n]+)', re.DOTALL)
consts = const_pattern.findall(data)
print(f"  Constants found: {len(consts)}")
for name, value in consts[:20]:
    try:
        print(f"    const {name.decode()} = {value.decode()[:50]}")
    except:
        pass
print()

var_pattern = re.compile(rb'var\s+(\w+)\s*(?:[:=]\s*([^;\n]+))?', re.DOTALL)
vars_found = var_pattern.findall(data)
print(f"  Variables found: {len(vars_found)}")
for name, value in vars_found[:20]:
    try:
        val_str = value.decode()[:50] if value else ""
        print(f"    var {name.decode()} = {val_str}")
    except:
        pass
print()

# ============================================================
# PHASE 6: Save everything
# ============================================================
print("[PHASE 6] Saving extracted data...")
print()

import os
import json

output_dir = r'C:\Users\devel\tools\reverse\output'
os.makedirs(output_dir, exist_ok=True)

# Save all strings
with open(os.path.join(output_dir, 'agy_all_strings.txt'), 'w', encoding='utf-8') as f:
    for offset, s in strings:
        f.write(f'0x{offset:08X}: {s}\n')
print(f"  Saved strings to: agy_all_strings.txt")

# Save functions
with open(os.path.join(output_dir, 'agy_functions.json'), 'w') as f:
    json.dump({
        'total': len(func_names),
        'by_package': {k: v[:20] for k, v in sorted_pkgs},
        'all': func_names[:500]
    }, f, indent=2)
print(f"  Saved functions to: agy_functions.json")

# Save interfaces
with open(os.path.join(output_dir, 'agy_interfaces.json'), 'w') as f:
    json.dump([{
        'name': name.decode() if isinstance(name, bytes) else name,
        'body': body.decode()[:200] if isinstance(body, bytes) else body
    } for name, body in interfaces[:50]], f, indent=2)
print(f"  Saved interfaces to: agy_interfaces.json")

# Save structs
with open(os.path.join(output_dir, 'agy_structs.json'), 'w') as f:
    json.dump([{
        'name': name.decode() if isinstance(name, bytes) else name,
        'body': body.decode()[:200] if isinstance(body, bytes) else body
    } for name, body in structs[:50]], f, indent=2)
print(f"  Saved structs to: agy_structs.json")

# Save constants
with open(os.path.join(output_dir, 'agy_constants.json'), 'w') as f:
    json.dump([{
        'name': name.decode() if isinstance(name, bytes) else name,
        'value': value.decode()[:100] if isinstance(value, bytes) else value
    } for name, value in consts[:100]], f, indent=2)
print(f"  Saved constants to: agy_constants.json")

# Save categorised strings
cat_data = {k: list(dict.fromkeys(v))[:50] for k, v in categories.items()}
with open(os.path.join(output_dir, 'agy_categorized_deep.json'), 'w') as f:
    json.dump(cat_data, f, indent=2, ensure_ascii=False)
print(f"  Saved categorized strings to: agy_categorized_deep.json")

print()
print("=" * 70)
print("  EXTRACTION COMPLETE")
print("=" * 70)
print()
print("SUMMARY:")
print(f"  Total strings: {len(strings):,}")
print(f"  Functions: {len(func_names):,}")
print(f"  Interfaces: {len(interfaces)}")
print(f"  Structs: {len(structs)}")
print(f"  Constants: {len(consts)}")
print()
print("FILES GENERATED:")
for f in os.listdir(output_dir):
    if f.startswith('agy_'):
        size = os.path.getsize(os.path.join(output_dir, f))
        print(f"  {f}: {size:,} bytes")
