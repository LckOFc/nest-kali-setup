#!/usr/bin/env python3
"""
AGY.EXE Complete Analysis & Reconstruction
============================================
Full reverse engineering of Google Antigravity CLI
"""

import os
import sys
import re
import json
import hashlib
import struct
from collections import Counter, defaultdict
from pathlib import Path

BINARY_PATH = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
OUTPUT_DIR = r'C:\Users\devel\tools\reverse\output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("  AGY.EXE COMPLETE ANALYSIS & RECONSTRUCTION")
print("=" * 80)
print()

# ============================================================
# PHASE 1: STRING EXTRACTION
# ============================================================
print("[PHASE 1] Extracting ALL strings from binary...")
print()

with open(BINARY_PATH, 'rb') as f:
    data = f.read()

file_size = len(data)
print(f"  Binary size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

# Extract ASCII strings (min length 4)
ascii_strings = []
current = b''
for i, byte in enumerate(data):
    if 32 <= byte <= 126:  # Printable ASCII
        current += bytes([byte])
    else:
        if len(current) >= 4:
            ascii_strings.append((i - len(current), current.decode('ascii', errors='replace')))
        current = b''

# Extract UTF-16 LE strings
utf16_strings = []
i = 0
while i < len(data) - 1:
    if data[i] == 0 and 32 <= data[i+1] <= 126:  # Start of UTF-16 LE string
        s = b''
        j = i
        while j < len(data) - 1 and data[j] == 0 and 32 <= data[j+1] <= 126:
            s += data[j+1:j+2]
            j += 2
        if len(s) >= 8:
            try:
                utf16_strings.append((i, s.decode('utf-16-le', errors='replace')))
            except:
                pass
        i = j
    else:
        i += 1

print(f"  ASCII strings (4+ chars): {len(ascii_strings):,}")
print(f"  UTF-16 strings (8+ chars): {len(utf16_strings):,}")
print()

# Save all strings
all_strings = ascii_strings + [(off, s.replace('\x00','')) for off, s in utf16_strings]
all_strings.sort(key=lambda x: x[0])

strings_file = os.path.join(OUTPUT_DIR, 'agy_all_strings.txt')
with open(strings_file, 'w', encoding='utf-8') as f:
    for offset, s in all_strings:
        f.write(f'0x{offset:08X}: {s}\n')
print(f"  Saved to: {strings_file}")
print()

# ============================================================
# PHASE 2: CATEGORIZATION
# ============================================================
print("[PHASE 2] Categorizing strings...")
print()

categories = {
    'urls': [],
    'paths': [],
    'emails': [],
    'hashes': [],
    'keys_secrets': [],
    'functions': [],
    'types': [],
    'errors': [],
    'commands': [],
    'packages': [],
    'go_runtime': [],
    'crypto': [],
    'http': [],
    'json': [],
    'other': [],
}

for offset, s in all_strings:
    s_lower = s.lower()
    
    if re.match(r'^https?://', s):
        categories['urls'].append(s)
    elif re.match(r'^[a-z]:\\', s) or '/usr/' in s or '/home/' in s:
        categories['paths'].append(s)
    elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', s):
        categories['emails'].append(s)
    elif re.match(r'^[a-f0-9]{32}$', s_lower) or re.match(r'^[a-f0-9]{64}$', s_lower):
        categories['hashes'].append(s)
    elif any(k in s_lower for k in ['password', 'secret', 'apikey', 'api_key', 'token', 'private', 'key']):
        categories['keys_secrets'].append(s)
    elif s.startswith('func ') or s.startswith('def ') or re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\(', s):
        categories['functions'].append(s)
    elif re.match(r'^type\s+\w+', s):
        categories['types'].append(s)
    elif any(e in s_lower for e in ['error', 'failed', 'invalid', 'cannot', 'unable']):
        categories['errors'].append(s)
    elif s.startswith('/') or s.startswith('--') or any(c in s for c in ['help', 'version', 'install', 'run', 'debug']):
        categories['commands'].append(s)
    elif s.startswith('github.com/') or s.startswith('golang.org/') or s.startswith('google.com/'):
        categories['packages'].append(s)
    elif any(g in s_lower for g in ['go.', 'runtime.', 'syscall.', 'unsafe.', 'reflect.']):
        categories['go_runtime'].append(s)
    elif any(c in s_lower for c in ['aes', 'sha', 'md5', 'rsa', 'ecdsa', 'elliptic', 'cipher', 'hash.', 'crypto.']):
        categories['crypto'].append(s)
    elif any(h in s_lower for h in ['content-type', 'authorization', 'cookie', 'user-agent', 'accept', 'header']):
        categories['http'].append(s)
    elif any(j in s_lower for j in ['json', 'marshal', 'unmarshal', 'encode', 'decode', 'field', 'tag']):
        categories['json'].append(s)
    else:
        categories['other'].append(s)

print("  Categories found:")
for cat, items in categories.items():
    unique = list(dict.fromkeys(items))[:5]  # First 5 unique
    print(f"    {cat:20s}: {len(items):6,d} items | Sample: {unique[:2]}")

print()

# Save categorized strings
cat_file = os.path.join(OUTPUT_DIR, 'agy_categorized_strings.json')
cat_data = {cat: list(dict.fromkeys(items))[:100] for cat, items in categories.items()}
with open(cat_file, 'w') as f:
    json.dump(cat_data, f, indent=2, ensure_ascii=False)
print(f"  Saved categories to: {cat_file}")
print()

# ============================================================
# PHASE 3: PE ANALYSIS
# ============================================================
print("[PHASE 3] PE Structure Analysis...")
print()

import pefile

pe = pefile.PE(BINARY_PATH)

print(f"  Entry Point:     0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08X}")
print(f"  Image Base:      0x{pe.OPTIONAL_HEADER.ImageBase:012X}")
print(f"  Image Size:      {pe.OPTIONAL_HEADER.SizeOfImage:,} bytes")
print(f"  Machine:         {pefile.MACHINE_TYPE.get(pe.FILE_HEADER.Machine, 'UNKNOWN')}")
print(f"  Num Sections:    {pe.FILE_HEADER.NumberOfSections}")
print(f"  Timestamp:       {pefile.DATESYNC.get(pe.FILE_HEADER.TimeDateStamp, 'N/A')}")
print(f"  CheckSum:        0x{pe.OPTIONAL_HEADER.CheckSum:08X}")
print(f"  Subsystem:       {pe.OPTIONAL_HEADER.Subsystem} ({'GUI' if pe.OPTIONAL_HEADER.Subsystem == 2 else 'CONSOLE'})")
print()

print("  --- SECTIONS ---")
for section in pe.sections:
    name = section.Name.decode().rstrip('\x00')
    entropy = section.get_entropy()
    print(f"    {name:8s} | VAddr=0x{section.VirtualAddress:08X} | VSize={section.Misc_VirtualSize:,} | FileOff=0x{section.PointerToRawData:08X} | FileSz={section.SizeOfRawData:,} | Entropy={entropy:.2f}")

# Go-specific sections
print()
print("  --- GO-SPECIFIC SECTIONS ---")
go_sections = ['.go.buildinfo', '.gopclntab', '.gosymtab', '.go.version', '.text.gofunc', '.rodata']
for section in pe.sections:
    name = section.Name.decode().rstrip('\x00').lower()
    for gs in go_sections:
        if gs.replace('.', '') in name.replace('.', '') or gs in name:
            print(f"    FOUND: {name} (Go section)")

pe.close()
print()

# ============================================================
# PHASE 4: KEY PATTERNS & ENTROPY
# ============================================================
print("[PHASE 4] Entropy & Pattern Analysis...")
print()

# Calculate entropy per section
import math

def calc_entropy(data):
    if not data:
        return 0
    counter = Counter(data)
    length = len(data)
    entropy = 0
    for count in counter.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

print("  Section Entropy Analysis:")
pe = pefile.PE(BINARY_PATH)
for section in pe.sections:
    name = section.Name.decode().rstrip('\x00')
    start = section.PointerToRawData
    size = min(section.SizeOfRawData, 1024*1024)  # Sample 1MB
    section_data = data[start:start+size]
    entropy = calc_entropy(section_data)
    print(f"    {name:12s}: entropy={entropy:.2f} bits/byte ({'compressed' if entropy > 7.0 else 'structured' if entropy > 5.0 else 'text-like'})")
pe.close()

print()

# ============================================================
# PHASE 5: FUNCTION SIGNATURES (Go pclntab)
# ============================================================
print("[PHASE 5] Extracting Go function names from pclntab...")
print()

# Go uses .gopclntab section for function names
# Try to extract function names from the binary
func_names = []
func_pattern = re.compile(rb'([\x20-\x7e]{4,})', re.DOTALL)

# Search for Go-style function names (package.funcname)
go_func_pattern = re.compile(rb'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)', re.DOTALL)

for match in go_func_pattern.finditer(data):
    name = match.group(1).decode('ascii', errors='replace')
    if len(name) > 5 and not name.startswith('.') and not name.endswith('.'):
        func_names.append(name)

# Remove duplicates while preserving order
unique_funcs = list(dict.fromkeys(func_names))
unique_funcs.sort()

print(f"  Found {len(unique_funcs)} Go-style function names")
print()

# Show top functions by category
func_categories = defaultdict(list)
for f in unique_funcs:
    parts = f.split('.')
    if len(parts) >= 2:
        pkg = parts[0]
        func_name = parts[-1]
        func_categories[pkg].append(f)

print("  Top packages by function count:")
sorted_pkgs = sorted(func_categories.items(), key=lambda x: -len(x[1]))[:30]
for pkg, funcs in sorted_pkgs:
    print(f"    {pkg:50s}: {len(funcs):4d} functions")
    # Show first 3 functions
    for f in funcs[:3]:
        print(f"      - {f}")

print()

# ============================================================
# PHASE 6: HTTP & NETWORK PATTERNS
# ============================================================
print("[PHASE 6] Network & HTTP Patterns...")
print()

http_methods = []
endpoints = []
headers = []
user_agents = []

for offset, s in all_strings:
    s_clean = s.strip()
    
    if s_clean in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
        http_methods.append(s_clean)
    elif re.match(r'^/[a-zA-Z0-9/_-]+$', s_clean) and len(s_clean) > 3:
        endpoints.append(s_clean)
    elif re.match(r'^[A-Za-z0-9-]+:\s*.+$', s_clean):
        headers.append(s_clean)
    elif 'Mozilla' in s_clean or 'curl' in s_clean or 'python-requests' in s_clean:
        user_agents.append(s_clean)

print(f"  HTTP Methods found: {len(set(http_methods))}")
print(f"  API Endpoints found: {len(set(endpoints))}")
print(f"  HTTP Headers found: {len(set(headers))}")
print(f"  User Agents found: {len(set(user_agents))}")
print()

if endpoints:
    print("  Sample Endpoints:")
    for ep in list(set(endpoints))[:20]:
        print(f"    {ep}")

if user_agents:
    print()
    print("  Sample User Agents:")
    for ua in list(set(user_agents))[:5]:
        print(f"    {ua}")

print()

# ============================================================
# PHASE 7: CRYPTO & SECURITY PATTERNS
# ============================================================
print("[PHASE 7] Crypto & Security Patterns...")
print()

crypto_algos = []
hash_funcs = []
enc_funcs = []
key_sizes = []

for offset, s in all_strings:
    s_lower = s.lower()
    
    if 'sha256' in s_lower or 'sha256.' in s_lower:
        hash_funcs.append('SHA256')
    if 'sha512' in s_lower or 'sha512.' in s_lower:
        hash_funcs.append('SHA512')
    if 'md5' in s_lower or 'md5.' in s_lower:
        hash_funcs.append('MD5')
    if 'aes' in s_lower and ('cipher' in s_lower or 'encrypt' in s_lower):
        crypto_algos.append('AES')
    if 'rsa' in s_lower:
        crypto_algos.append('RSA')
    if 'ecdsa' in s_lower:
        crypto_algos.append('ECDSA')
    if 'hmac' in s_lower:
        crypto_algos.append('HMAC')
    if 'base64' in s_lower:
        crypto_algos.append('Base64')
    if 'pbkdf2' in s_lower:
        crypto_algos.append('PBKDF2')
    if 'bcrypt' in s_lower:
        crypto_algos.append('Bcrypt')
    if 'argon2' in s_lower:
        crypto_algos.append('Argon2')
    if 'keysize' in s_lower or 'key_size' in s_lower:
        match = re.search(r'(\d+)', s)
        if match:
            key_sizes.append(match.group(1))

print(f"  Crypto Algorithms: {list(set(crypto_algos))}")
print(f"  Hash Functions: {list(set(hash_funcs))}")
print(f"  Key Sizes: {list(set(key_sizes))[:10]}")
print()

# ============================================================
# PHASE 8: ERROR HANDLING & LOGGING
# ============================================================
print("[PHASE 8] Error Handling & Logging Patterns...")
print()

errors = []
logs = []
warnings = []

for offset, s in all_strings:
    s_clean = s.strip()
    
    if any(e in s_clean.lower() for e in ['error:', 'failed to', 'cannot', 'unable to', 'invalid']):
        errors.append(s_clean)
    if any(l in s_clean.lower() for l in ['log.', 'logger', 'logging', 'info:', 'debug:', 'trace:']):
        logs.append(s_clean)
    if 'warn' in s_clean.lower():
        warnings.append(s_clean)

unique_errors = list(dict.fromkeys(errors))[:30]
unique_logs = list(dict.fromkeys(logs))[:20]

print(f"  Unique errors: {len(unique_errors)}")
print(f"  Unique logs: {len(unique_logs)}")
print()

print("  Sample Errors:")
for e in unique_errors[:15]:
    print(f"    {e}")

print()

# ============================================================
# PHASE 9: BUILD INFO & VERSION
# ============================================================
print("[PHASE 9] Build Information...")
print()

build_info = []
version_info = []
go_version = None

for offset, s in all_strings:
    if 'go-build' in s.lower():
        build_info.append(s)
    if 'go version' in s.lower():
        go_version = s
    if 'version' in s.lower() and any(c in s for c in ['v0.', 'v1.', 'v2.', '-']):
        version_info.append(s)

if go_version:
    print(f"  Go Version: {go_version}")
if build_info:
    print(f"  Build Info ({len(build_info)} items):")
    for bi in build_info[:5]:
        print(f"    {bi}")

print()

# ============================================================
# PHASE 10: COMMAND LINE INTERFACE ANALYSIS
# ============================================================
print("[PHASE 10] CLI/Command Analysis...")
print()

cli_flags = []
cli_commands = []
cli_args = []

for offset, s in all_strings:
    s_clean = s.strip()
    
    if re.match(r'^-{1,2}[\w-]+$', s_clean) and len(s_clean) > 2:
        cli_flags.append(s_clean)
    if s_clean in ['help', 'version', 'install', 'run', 'debug', 'test', 'build', 'start', 'stop', 'status']:
        cli_commands.append(s_clean)
    if re.match(r'^[\w-]+$', s_clean) and len(s_clean) > 2 and len(s_clean) < 30:
        cli_args.append(s_clean)

unique_flags = list(dict.fromkeys(cli_flags))
unique_cmds = list(dict.fromkeys(cli_commands))

print(f"  CLI Flags: {len(unique_flags)}")
print(f"  CLI Commands: {len(unique_cmds)}")
print()

if unique_flags:
    print("  Sample Flags:")
    for flag in unique_flags[:20]:
        print(f"    --{flag.lstrip('-')}")

if unique_cmds:
    print()
    print("  Sample Commands:")
    for cmd in unique_cmds:
        print(f"    {cmd}")

print()

# ============================================================
# FINAL: GENERATE RECONSTRUCTION PLAN
# ============================================================
print("[PHASE 11] Generating Reconstruction Plan...")
print()

# Summary
total_strings = len(all_strings)
unique_strings = len(set(s for _, s in all_strings))
total_functions = len(unique_funcs)
total_errors = len(unique_errors)

print("=" * 80)
print("  ANALYSIS SUMMARY")
print("=" * 80)
print()
print(f"  Binary:           agy.exe (Google Antigravity CLI)")
print(f"  Size:             {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print(f"  Total Strings:    {total_strings:,}")
print(f"  Unique Strings:   {unique_strings:,}")
print(f"  Go Functions:     {total_functions:,}")
print(f"  Error Messages:   {total_errors:,}")
print()
print("  Categories:")
for cat, items in categories.items():
    if items:
        print(f"    {cat:20s}: {len(items):6,d}")
print()
print("  Key Findings:")
print(f"    - HTTP/Network: {len(set(http_methods))} methods, {len(set(endpoints))} endpoints")
print(f"    - Crypto: {list(set(crypto_algos))}")
print(f"    - Top Packages: {[p[0] for p in sorted_pkgs[:5]]}")
print(f"    - CLI Commands: {unique_cmds[:10]}")
print()

# Save full analysis
analysis_file = os.path.join(OUTPUT_DIR, 'agy_complete_analysis.json')
analysis_data = {
    'binary': BINARY_PATH,
    'size': file_size,
    'total_strings': total_strings,
    'unique_strings': unique_strings,
    'functions': unique_funcs[:500],
    'categories': cat_data,
    'http': {
        'methods': list(set(http_methods)),
        'endpoints': list(set(endpoints))[:50],
        'user_agents': list(set(user_agents))[:10],
    },
    'crypto': {
        'algorithms': list(set(crypto_algos)),
        'hashes': list(set(hash_funcs)),
        'key_sizes': list(set(key_sizes))[:10],
    },
    'cli': {
        'flags': unique_flags[:50],
        'commands': unique_cmds,
    },
    'errors': unique_errors[:50],
    'packages': {pkg: funcs[:10] for pkg, funcs in sorted_pkgs[:20]},
}

with open(analysis_file, 'w') as f:
    json.dump(analysis_data, f, indent=2, ensure_ascii=False)

print(f"  Full analysis saved to: {analysis_file}")
print()
print("=" * 80)
print("  ANALYSIS COMPLETE - READY FOR RECONSTRUCTION")
print("=" * 80)