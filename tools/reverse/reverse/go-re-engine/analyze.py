#!/usr/bin/env python3
"""
Go Reverse Engineering Toolkit v2.0
====================================
Script principal de análise completa com saída estruturada.

Uso:
    python analyze.py <binary.exe> [--output dir] [--format json|text]
"""

import os
import sys
import json
import re
import time
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add engine directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class GoREToolkit:
    """Toolkit completo de Engenharia Reversa para binários Go."""
    
    def __init__(self, exe_path: str, output_dir: str = None):
        self.exe_path = exe_path
        self.output_dir = output_dir or os.path.join(os.path.dirname(exe_path), 're_output')
        
        # File info
        self.file_size = os.path.getsize(exe_path)
        self.file_hash = self._calc_hash(exe_path)
        
        # Results
        self.results = {
            'metadata': {},
            'pe_info': {},
            'strings': {},
            'functions': {},
            'types': {},
            'cfg': {},
            'decompiler': {},
            'summary': {},
        }
        
        # Timings
        self.timings = {}
        
    def _calc_hash(self, path: str) -> str:
        """Calcular hash MD5 do arquivo."""
        h = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def run_full_analysis(self) -> dict:
        """Executar análise completa."""
        print("=" * 70)
        print("  Go RE Toolkit v2.0 - Full Analysis")
        print("=" * 70)
        print(f"\n  Binary: {self.exe_path}")
        print(f"  Size: {self.file_size:,} bytes ({self.file_size/1024/1024:.1f} MB)")
        print(f"  MD5: {self.file_hash}")
        print(f"  Output: {self.output_dir}/")
        print()
        
        start_time = time.time()
        
        # 1. Metadata
        self.results['metadata'] = {
            'binary': self.exe_path,
            'size': self.file_size,
            'md5': self.file_hash,
            'analyzed_at': datetime.now().isoformat(),
            'toolkit_version': '2.0.0',
        }
        
        # 2. PE Analysis
        self._analyze_pe()
        
        # 3. String Extraction
        self._analyze_strings()
        
        # 4. Type Recovery
        self._analyze_types()
        
        # 5. Function Reconstruction
        self._analyze_functions()
        
        # 6. CFG Analysis
        self._analyze_cfg()
        
        # 7. Generate summary
        self.timings['total'] = time.time() - start_time
        self.results['summary'] = self._generate_summary()
        
        # Save results
        self._save_results()
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _analyze_pe(self):
        """Análise PE."""
        print("[*] Analyzing PE structure...")
        start = time.time()
        
        try:
            import lief
            import math
            pe = lief.PE.parse(self.exe_path)
            
            sections = []
            for s in pe.sections:
                # Calculate entropy
                raw = bytes(s.content) if hasattr(s, 'content') else b''
                entropy = 0.0
                if raw:
                    freq = defaultdict(int)
                    for byte in raw:
                        freq[byte] += 1
                    for count in freq.values():
                        p = count / len(raw)
                        if p > 0:
                            entropy -= p * math.log2(p)
                
                sections.append({
                    'name': s.name,
                    'virtual_size': s.virtual_size,
                    'raw_size': s.sizeof_raw_data,
                    'virtual_address': hex(s.virtual_address),
                    'entropy': round(entropy, 2),
                })
            
            self.results['pe_info'] = {
                'machine': str(pe.header.machine),
                'entry_point': hex(pe.entrypoint),
                'image_base': hex(pe.imagebase),
                'sections': sections,
                'has_debug': pe.has_debug,
            }
            
            print(f"[+] PE analyzed: {len(sections)} sections")
            
        except Exception as e:
            self.results['pe_info'] = {'error': str(e)}
            print(f"[-] PE analysis failed: {e}")
        
        self.timings['pe'] = time.time() - start
    
    def _analyze_strings(self):
        """Análise de strings."""
        print("[*] Analyzing strings...")
        start = time.time()
        
        try:
            with open(self.exe_path, 'rb') as f:
                data = f.read(min(self.file_size, 200 * 1024 * 1024))
            
            # Extract strings
            string_pattern = rb'[\x20-\x7e]{4,}'
            all_strings = re.findall(string_pattern, data)
            
            categories = {
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
                if count >= 50000:
                    break
                try:
                    s = s_bytes.decode('ascii')
                except:
                    continue
                
                sl = s.lower()
                
                if any(sl.startswith(p) for p in ['runtime.', 'sync.', 'reflect.', 'unsafe.']):
                    categories['go_runtime'].append(s[:80])
                elif '.' in s and any(sl.startswith(p) for p in ['github.com/', 'google.']):
                    categories['go_functions'].append(s[:80])
                elif re.match(r'^[A-Z][a-zA-Z0-9_]{3,30}$', s):
                    categories['go_types'].append(s)
                elif 'http' in sl or '://' in s:
                    categories['urls'].append(s[:80])
                elif '\\\\' in s or '/home/' in s or '/go/' in s:
                    categories['paths'].append(s[:80])
                elif any(kw in sl for kw in ['error', 'failed', 'unable', 'cannot']):
                    categories['errors'].append(s[:80])
                elif 'ANTIGRAVITY_' in s or 'AGY_' in s:
                    categories['config'].append(s[:80])
                else:
                    categories['other'].append(s[:80])
                
                count += 1
            
            self.results['strings'] = categories
            total_categorized = sum(len(v) for k, v in categories.items() if k != 'total')
            print(f"[+] Found {categories['total']:,} strings ({total_categorized:,} categorized)")
            
        except Exception as e:
            self.results['strings'] = {'error': str(e)}
            print(f"[-] String analysis failed: {e}")
        
        self.timings['strings'] = time.time() - start
    
    def _analyze_types(self):
        """Análise de tipos."""
        print("[*] Analyzing types...")
        start = time.time()
        
        try:
            with open(self.exe_path, 'rb') as f:
                data = f.read(min(self.file_size, 200 * 1024 * 1024))
            
            types = []
            
            # Detect structs
            struct_pattern = rb'struct\s*\{([^}]{0,300})\}'
            for match in re.finditer(struct_pattern, data):
                try:
                    content = match.group(1).decode('ascii', errors='replace')
                    fields = re.findall(r'\s+(\w+)\s+(\w+)', content)
                    if fields and len(types) < 200:
                        type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                        types.append({
                            'kind': 'struct',
                            'name': f'Struct_{type_hash}',
                            'fields': len(fields),
                            'sample': content[:150],
                            'confidence': 0.7,
                        })
                except:
                    pass
            
            # Detect interfaces
            iface_pattern = rb'interface\s*\{([^}]{0,300})\}'
            for match in re.finditer(iface_pattern, data):
                try:
                    content = match.group(1).decode('ascii', errors='replace')
                    methods = re.findall(r'\s*(\w+)\s*\(', content)
                    if methods and len(types) < 200:
                        type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                        types.append({
                            'kind': 'interface',
                            'name': f'Interface_{type_hash}',
                            'methods': len(methods),
                            'sample': content[:150],
                            'confidence': 0.8,
                        })
                except:
                    pass
            
            # Detect generics
            slice_pattern = rb'\[\]([a-zA-Z_][a-zA-Z0-9_.{}]*)'
            for match in re.finditer(slice_pattern, data):
                try:
                    elem = match.group(1).decode('ascii')
                    type_name = f'[]{elem}'
                    if not any(t['name'] == type_name for t in types):
                        types.append({
                            'kind': 'slice',
                            'name': type_name,
                            'element_type': elem,
                            'confidence': 0.6,
                        })
                except:
                    pass
            
            # Sort by confidence
            types.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            self.results['types'] = {
                'total': len(types),
                'types': types[:100],
                'by_kind': {
                    'struct': sum(1 for t in types if t['kind'] == 'struct'),
                    'interface': sum(1 for t in types if t['kind'] == 'interface'),
                    'slice': sum(1 for t in types if t['kind'] == 'slice'),
                }
            }
            
            print(f"[+] Recovered {len(types)} types")
            
        except Exception as e:
            self.results['types'] = {'error': str(e)}
            print(f"[-] Type analysis failed: {e}")
        
        self.timings['types'] = time.time() - start
    
    def _analyze_functions(self):
        """Análise de funções."""
        print("[*] Analyzing functions...")
        start = time.time()
        
        try:
            import capstone
            
            # Read binary
            with open(self.exe_path, 'rb') as f:
                data = f.read(50 * 1024 * 1024)
            
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            md.detail = True
            
            # Find function prologues
            prologue = b'\x55\x48\x89\xe5'  # push rbp; mov rbp, rsp
            
            functions = []
            for match in re.finditer(re.escape(prologue), data):
                addr = match.start()
                
                # Extract function instructions
                func_data = data[addr:addr + 0x1000]
                try:
                    insts = list(md.disasm(func_data, addr))
                except:
                    continue
                
                if len(insts) < 5:
                    continue
                
                # Estimate function size
                func_end = addr
                for inst in insts:
                    if inst.mnemonic == 'ret':
                        func_end = inst.address + inst.size
                        break
                else:
                    func_end = addr + 0x500
                
                # Try to find function name
                name = f"fn_{addr:04x}"
                
                functions.append({
                    'addr': hex(addr),
                    'end': hex(func_end),
                    'size': func_end - addr,
                    'name': name,
                    'instructions': len(insts),
                })
                
                if len(functions) >= 50:
                    break
            
            # Sort by address
            functions.sort(key=lambda x: int(x['addr'], 16))
            
            self.results['functions'] = {
                'total': len(functions),
                'functions': functions[:50],
            }
            
            print(f"[+] Analyzed {len(functions)} functions")
            
        except Exception as e:
            self.results['functions'] = {'error': str(e)}
            print(f"[-] Function analysis failed: {e}")
        
        self.timings['functions'] = time.time() - start
    
    def _analyze_cfg(self):
        """Análise CFG."""
        print("[*] Analyzing control flow...")
        start = time.time()
        
        try:
            import capstone
            
            with open(self.exe_path, 'rb') as f:
                data = f.read(10 * 1024 * 1024)
            
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            md.detail = True
            
            prologue = b'\x55\x48\x89\xe5'
            
            cfgs = []
            for match in re.finditer(re.escape(prologue), data):
                addr = match.start()
                
                func_data = data[addr:addr + 0x800]
                try:
                    insts = list(md.disasm(func_data, addr))
                except:
                    continue
                
                if len(insts) < 3:
                    continue
                
                # Build simple CFG
                blocks = []
                current_block = {'start': addr, 'insts': []}
                
                for inst in insts:
                    current_block['insts'].append(inst)
                    mnem = inst.mnemonic.lower()
                    
                    if mnem in ('ret', 'jmp'):
                        blocks.append(current_block)
                        current_block = {'start': inst.address + inst.size, 'insts': []}
                    elif mnem.startswith('j'):
                        blocks.append(current_block)
                        current_block = {'start': inst.address + inst.size, 'insts': []}
                
                if current_block['insts']:
                    blocks.append(current_block)
                
                cfgs.append({
                    'func_addr': hex(addr),
                    'blocks': len(blocks),
                    'instructions': len(insts),
                })
                
                if len(cfgs) >= 20:
                    break
            
            self.results['cfg'] = {
                'total_analyzed': len(cfgs),
                'cfgs': cfgs[:20],
            }
            
            print(f"[+] Analyzed CFG for {len(cfgs)} functions")
            
        except Exception as e:
            self.results['cfg'] = {'error': str(e)}
            print(f"[-] CFG analysis failed: {e}")
        
        self.timings['cfg'] = time.time() - start
    
    def _generate_summary(self) -> dict:
        """Gerar resumo da análise."""
        return {
            'total_time_seconds': round(self.timings.get('total', 0), 2),
            'binary_size_mb': round(self.file_size / 1024 / 1024, 2),
            'strings_total': self.results.get('strings', {}).get('total', 0),
            'strings_categorized': sum(
                len(v) for k, v in self.results.get('strings', {}).items() 
                if k != 'total' and isinstance(v, list)
            ),
            'types_recovered': self.results.get('types', {}).get('total', 0),
            'functions_analyzed': self.results.get('functions', {}).get('total', 0),
            'cfgs_analyzed': self.results.get('cfg', {}).get('total_analyzed', 0),
            'pe_sections': len(self.results.get('pe_info', {}).get('sections', [])),
        }
    
    def _save_results(self):
        """Salvar resultados."""
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Main report
        report_path = os.path.join(self.output_dir, 'analysis_report.json')
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"[+] Report saved: {report_path}")
        
        # Summary only
        summary_path = os.path.join(self.output_dir, 'summary.json')
        with open(summary_path, 'w') as f:
            json.dump(self.results.get('summary', {}), f, indent=2)
        print(f"[+] Summary saved: {summary_path}")
    
    def _print_summary(self):
        """Imprimir resumo."""
        summary = self.results.get('summary', {})
        
        print("\n" + "=" * 70)
        print("  ANALYSIS SUMMARY")
        print("=" * 70)
        print(f"""
  [INFO]
    Binary:     {self.results.get('metadata', {}).get('binary', 'N/A')}
    Size:       {summary.get('binary_size_mb', 0):.1f} MB
    MD5:        {self.results.get('metadata', {}).get('md5', 'N/A')}
    Time:       {summary.get('total_time_seconds', 0):.1f}s
  
  [RESULTS]
    Strings:    {summary.get('strings_total', 0):,} total ({summary.get('strings_categorized', 0):,} categorized)
    Types:      {summary.get('types_recovered', 0)}
    Functions:  {summary.get('functions_analyzed', 0)}
    CFGs:       {summary.get('cfgs_analyzed', 0)}
    PE Sect:    {summary.get('pe_sections', 0)}
  
  [OUTPUT]
    {self.output_dir}/
      - analysis_report.json  (complete results)
      - summary.json          (quick overview)
""")
        print("=" * 70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Go Reverse Engineering Toolkit v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze.py agy.exe
  python analyze.py agy.exe --output ./results
  python analyze.py agy.exe --format json
        """
    )
    
    parser.add_argument('binary', help='Path to Go binary (.exe)')
    parser.add_argument('--output', '-o', default=None, help='Output directory')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.binary):
        print(f"ERROR: Binary not found: {args.binary}")
        sys.exit(1)
    
    output_dir = args.output or os.path.join(os.path.dirname(os.path.abspath(args.binary)), 're_output')
    
    # Run analysis
    toolkit = GoREToolkit(args.binary, output_dir)
    results = toolkit.run_full_analysis()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())