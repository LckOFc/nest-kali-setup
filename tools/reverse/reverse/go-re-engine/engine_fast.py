"""
Go Reverse Engineering Toolkit v1.0 - Versão Otimizada
======================================================
Análise rápida e eficiente de binários Go.
"""

import os
import sys
import re
import json
import struct
from collections import defaultdict, Counter
from pathlib import Path

# Check dependencies
try:
    import lief
except ImportError:
    lief = None

try:
    import capstone
except ImportError:
    capstone = None

class GoREEngine:
    """Engine de RE otimizada para binários Go."""
    
    def __init__(self, exe_path: str):
        self.exe_path = exe_path
        self.file_size = os.path.getsize(exe_path)
        
        # Read only first 100MB for speed
        with open(exe_path, 'rb') as f:
            self.data = f.read(100 * 1024 * 1024)
        
        # Initialize
        self.pe = None
        self.md = None
        self.results = {}
        
        if lief:
            self.pe = lief.PE.parse(exe_path)
        if capstone:
            self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            self.md.detail = True
    
    def analyze_strings(self, max_strings=50000):
        """Análise de strings otimizada."""
        print("[*] Analyzing strings...")
        
        # Extract strings
        string_pattern = rb'[\x20-\x7e]{4,}'
        all_strings = re.findall(string_pattern, self.data)
        
        results = {
            'total': len(all_strings),
            'go_runtime': [],
            'go_functions': [],
            'go_types': [],
            'urls': [],
            'paths': [],
            'errors': [],
            'config': [],
            'other': [],
        }
        
        count = 0
        for s_bytes in all_strings:
            if count >= max_strings:
                break
            try:
                s = s_bytes.decode('ascii')
            except:
                continue
            
            sl = s.lower()
            
            if any(sl.startswith(p) for p in ['runtime.', 'sync.', 'reflect.', 'unsafe.']):
                results['go_runtime'].append(s[:100])
            elif '.' in s and any(sl.startswith(p) for p in ['github.com/', 'google.']):
                results['go_functions'].append(s[:100])
            elif re.match(r'^[A-Z][a-zA-Z0-9_]{3,30}$', s):
                results['go_types'].append(s)
            elif 'http' in sl or '://' in s:
                results['urls'].append(s[:100])
            elif '\\\\' in s or '/home/' in s or '/go/' in s:
                results['paths'].append(s[:100])
            elif any(kw in sl for kw in ['error', 'failed', 'unable', 'cannot']):
                results['errors'].append(s[:100])
            elif 'ANTIGRAVITY_' in s or 'AGY_' in s:
                results['config'].append(s[:100])
            else:
                results['other'].append(s[:100])
            
            count += 1
        
        self.results['strings'] = results
        print(f"[+] Found {results['total']:,} strings")
        return results
    
    def analyze_functions(self):
        """Análise de funções (amostral)."""
        print("[*] Analyzing functions...")
        
        if not self.md or not self.pe:
            print("[-] Capstone/LIEF not available")
            return {}
        
        # Get .text section
        text_section = None
        for s in self.pe.sections:
            if '.text' in s.name:
                text_section = s
                break
        
        if not text_section:
            return {}
        
        raw = bytes(text_section.content[:500000])  # First 500KB
        functions = []
        
        # Sample disassembly
        insns = list(self.md.disasm(raw, text_section.virtual_address))
        
        # Find function-like patterns
        func_starts = set()
        for i, inst in enumerate(insns):
            # Function prologue: push rbp; mov rbp, rsp
            if inst.mnemonic == 'push' and 'rbp' in inst.op_str:
                if i + 1 < len(insns) and insns[i+1].mnemonic == 'mov':
                    if 'rbp' in insns[i+1].op_str and 'rsp' in insns[i+1].op_str:
                        func_starts.add(inst.address)
        
        # Extract function info
        for addr in sorted(func_starts)[:50]:
            # Get function instructions
            func_insns = []
            for inst in insns:
                if addr <= inst.address < addr + 0x200:  # 512 byte window
                    func_insns.append(inst)
                elif inst.address > addr + 0x200:
                    break
            
            if func_insns:
                # Try to find function name
                name = f"sub_{addr:08x}"
                for fn_match in re.finditer(rb'[a-z][a-z0-9_]+\.[a-z][a-z0-9_]+', 
                                           self.data[max(0,addr-0x1000):addr+0x1000]):
                    try:
                        name = fn_match.group(0).decode('ascii')
                        break
                    except:
                        pass
                
                functions.append({
                    'addr': hex(addr),
                    'name': name,
                    'size': len(func_insns) * 10,  # Estimate
                    'instructions': len(func_insns),
                })
        
        self.results['functions'] = {
            'total': len(functions),
            'sample': functions[:20],
        }
        print(f"[+] Found {len(functions)} function candidates")
        return self.results['functions']
    
    def analyze_types(self):
        """Análise de tipos."""
        print("[*] Analyzing types...")
        
        types = {}
        
        # Look for Go type patterns
        type_patterns = [
            (rb'interface\s*\{[^}]{0,200}', 'interface'),
            (rb'struct\s*\{[^}]{0,200}', 'struct'),
        ]
        
        for pattern, kind in type_patterns:
            for match in re.finditer(pattern, self.data):
                try:
                    content = match.group(0).decode('ascii', errors='replace')
                    # Extract field names
                    fields = re.findall(r'\w+\s+\w+', content)
                    if fields:
                        type_name = f"{kind}_{hash(match.group(0)[:50]).hexdigest()[:8]}"
                        types[type_name] = {
                            'kind': kind,
                            'fields': len(fields),
                            'sample': content[:200]
                        }
                except:
                    pass
        
        self.results['types'] = {
            'total': len(types),
            'sample': list(types.items())[:20],
        }
        print(f"[+] Recovered {len(types)} type definitions")
        return self.results['types']
    
    def analyze_pe(self):
        """Análise PE."""
        print("[*] Analyzing PE structure...")
        
        if not self.pe:
            return {}
        
        sections = []
        for s in self.pe.sections:
            sections.append({
                'name': s.name,
                'virtual_size': s.virtual_size,
                'raw_size': s.sizeof_raw_data,
                'virtual_address': hex(s.virtual_address),
            })
        
        self.results['pe'] = {
            'machine': str(self.pe.header.machine),
            'sections': sections,
            'entry_point': hex(self.pe.entrypoint),
        }
        return self.results['pe']
    
    def run_analysis(self, output_dir: str):
        """Executar análise completa."""
        print("=" * 60)
        print("  Go RE Engine v1.0 - Quick Analysis")
        print("=" * 60)
        print(f"\n  Binary: {self.exe_path}")
        print(f"  Size: {self.file_size:,} bytes")
        print()
        
        # Run analyses
        self.analyze_pe()
        self.analyze_strings()
        self.analyze_functions()
        self.analyze_types()
        
        # Save results
        os.makedirs(output_dir, exist_ok=True)
        
        # Main report
        report_path = os.path.join(output_dir, 'report.json')
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n[+] Report saved: {report_path}")
        
        # Summary
        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"  Strings:     {self.results.get('strings', {}).get('total', 0):,}")
        print(f"  Functions:   {self.results.get('functions', {}).get('total', 0)}")
        print(f"  Types:       {self.results.get('types', {}).get('total', 0)}")
        print(f"\n  Output: {output_dir}/")
        
        return self.results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Go RE Engine v1.0')
    parser.add_argument('binary', help='Path to Go binary')
    parser.add_argument('--output', '-o', default='./re_output')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.binary):
        print(f"ERROR: Binary not found: {args.binary}")
        sys.exit(1)
    
    engine = GoREEngine(args.binary)
    engine.run_analysis(args.output)


if __name__ == '__main__':
    main()