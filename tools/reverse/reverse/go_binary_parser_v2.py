#!/usr/bin/env python3
"""
Advanced Go Binary Parser - Manual .gopclntab and .gosymtab parsing
=====================================================================
Recupera informações COMPLETAS de funções Go de binários stripped
"""

import struct
import re
import os
import sys
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class GoBinaryParser:
    """Parser completo para binários Go com análise avançada"""
    
    def __init__(self, binary_path: str):
        self.binary_path = binary_path
        self.data = None
        self.sections = {}
        self.functions = []
        self.types = []
        self.packages = []
        self.build_info = {}
        
    def load(self):
        """Carregar binário"""
        print("[+] Carregando binário...")
        with open(self.binary_path, 'rb') as f:
            self.data = f.read()
        print(f"[+] Tamanho: {len(self.data):,} bytes ({len(self.data)/1024/1024:.1f} MB)")
        return len(self.data) > 0
    
    def find_section(self, section_name: str) -> Tuple[int, int]:
        """
        Encontrar seção no binário usando heurísticas
        Retorna (offset, size)
        """
        # Procurar pelo nome da seção
        name_bytes = section_name.encode('ascii')
        idx = self.data.find(name_bytes)
        
        if idx == -1:
            # Tentar variantas
            alt_names = {
                '.gopclntab': [b'.gopclntab', b'pclntab'],
                '.gosymtab': [b'.gosymtab', b'symtab'],
                '.go.buildinfo': [b'.go.buildinfo', b'buildinfo'],
                '.go.version': [b'.go.version', b'goversion'],
            }
            
            for alt in alt_names.get(section_name, []):
                idx = self.data.find(alt)
                if idx != -1:
                    break
        
        if idx == -1:
            return (-1, 0)
        
        # Estimar tamanho baseado no próximo marker ou fim do arquivo
        # Ir procurar pelo próximo nome de seção válido
        next_idx = len(self.data)
        
        # Procurar por outros nomes de seção conhecidos
        known_sections = [
            b'.text', b'.rdata', b'.data', b'.pdata', b'.ctors',
            b'.go.buildinfo', b'.gopclntab', b'.gosymtab', b'.go.version',
            b'.gosetctr', b'.gcc_except_table', b'.noptrdata',
        ]
        
        for sec in known_sections:
            if sec != name_bytes:
                sec_idx = self.data.find(sec, idx + len(name_bytes))
                if sec_idx != -1 and sec_idx < next_idx:
                    next_idx = sec_idx
        
        size = next_idx - idx
        
        # Limitar tamanho razoável
        max_sizes = {
            '.gopclntab': 50 * 1024 * 1024,  # 50 MB max
            '.gosymtab': 20 * 1024 * 1024,   # 20 MB max
            '.go.buildinfo': 1 * 1024 * 1024,  # 1 MB max
            '.go.version': 1024,              # 1 KB max
        }
        
        max_size = max_sizes.get(section_name, 10 * 1024 * 1024)
        size = min(size, max_size)
        
        return (idx, size)
    
    def extract_section(self, section_name: str) -> bytes:
        """Extrair dados de uma seção"""
        offset, size = self.find_section(section_name)
        if offset == -1:
            return b''
        return self.data[offset:offset+size]
    
    def parse_buildinfo(self) -> Dict[str, str]:
        """Parsear .go.buildinfo"""
        print("\n[+] Parseando .go.buildinfo...")
        
        data = self.extract_section('.go.buildinfo')
        if not data:
            print("  [--] Seção .go.buildinfo não encontrada")
            return {}
        
        result = {}
        
        # Format: version (4 bytes) + key=value pairs
        # Versão Go vai em go1.X.Y
        
        # Procurar por versão
        version_match = re.search(rb'go1\.(\d+)\.(\d+)', data)
        if version_match:
            result['go_version'] = f"go1.{version_match.group(1).decode()}.{version_match.group(2).decode()}"
        
        # Procurar por build settings
        settings = re.findall(rb'([\w]+)=([\w./-]+)', data)
        for key, val in settings:
            try:
                result[key.decode()] = val.decode()
            except:
                pass
        
        # Procurar por module path
        module_match = re.search(rb'module\s+(\S+)', data)
        if module_match:
            result['module'] = module_match.group(1).decode('ascii', errors='replace')
        
        # Procurar por GOOS e GOARCH
        goos_match = re.search(rb'GOOS=(\w+)', data)
        if goos_match:
            result['GOOS'] = goos_match.group(1).decode()
        
        goarch_match = re.search(rb'GOARCH=(\w+)', data)
        if goarch_match:
            result['GOARCH'] = goarch_match.group(1).decode()
        
        print(f"  Build info: {len(result)} campos")
        for k, v in list(result.items())[:10]:
            print(f"    {k}: {v}")
        
        return result
    
    def parse_gopclntab_v2(self) -> List[Dict]:
        """
        Parsear .gopclntab - Versão melhorada
        Formato Go 1.17+ (mais recente)
        """
        print("\n[+] Parseando .gopclntab (Go 1.17+ format)...")
        
        data = self.extract_section('.gopclntab')
        if not data:
            print("  [--] Seção .gopclntab não encontrada")
            return []
        
        print(f"  Tamanho: {len(data):,} bytes")
        
        functions = []
        
        # Go pclntab format (simplificado):
        # Cada função tem:
        # - funcID (1 byte) - tipo de função
        # - entryoff (4 bytes LE) - offset do entry point
        # - SPsize (1 byte) - size da stack pointer
        # - nfuncdata (1 byte) - number of funcdata
        # - nfile (2 bytes) - file index
        # - pcsp (4 bytes LE) - PC to stack pointer delta
        # - pcfile (4 bytes LE) - PC to file index
        # - pcln (4 bytes LE) - PC to line number
        # - NPCDATA (1 byte) - number of pcdata entries
        # - NPCFUNCDATA (1 byte) - number of funcdata entries
        # - name_off (4 bytes LE) - offset para nome da função
        # - args (4 bytes LE) - size dos args
        # - deferredcall (1 byte) - se tem deferred call
        
        # Mínimo: 1 + 4 + 1 + 1 + 2 + 4 + 4 + 4 + 1 + 1 + 4 + 4 + 1 = 27 bytes
        
        MIN_FUNC_SIZE = 27
        
        # Procurar por padrões de entry points válidos
        # Entry points são offsets relative ao início da seção .text
        text_offset, text_size = self.find_section('.text')
        
        print(f"  .text section: offset=0x{text_offset:08X}, size={text_size:,}")
        
        # Método 1: Parsear entradas da tabela
        offset = 0
        func_count = 0
        
        while offset + MIN_FUNC_SIZE <= len(data):
            try:
                # Read funcID
                func_id = data[offset]
                
                # Validar funcID (0-255, mas valores específicos são válidos)
                # Go usa: 0=plain, 1=wrapper, 2=async, etc.
                if func_id > 10:  # Valores muito altos são raros
                    offset += 1
                    continue
                
                # Read entryoff (4 bytes LE)
                entryoff = struct.unpack_from('<I', data, offset + 1)[0]
                
                # Validar entryoff (deve ser relativo ao .text)
                if entryoff > text_size or entryoff == 0:
                    offset += 1
                    continue
                
                # Read SPsize
                spsize = data[offset + 5]
                
                # Read nfuncdata
                nfuncdata = data[offset + 6]
                
                # Read nfile (2 bytes)
                nfile = struct.unpack_from('<H', data, offset + 7)[0]
                
                # Read pcsp
                pcsp = struct.unpack_from('<I', data, offset + 9)[0]
                
                # Read pcfile
                pcfile = struct.unpack_from('<I', data, offset + 13)[0]
                
                # Read pcln
                pcln = struct.unpack_from('<I', data, offset + 17)[0]
                
                # Read NPCDATA
                npCDATA = data[offset + 21]
                
                # Read NPCFUNCDATA
                npFuncData = data[offset + 22]
                
                # Read name_off (4 bytes)
                name_off = struct.unpack_from('<I', data, offset + 23)[0]
                
                # Read args
                args = struct.unpack_from('<I', data, offset + 27)[0] if offset + 31 <= len(data) else 0
                
                # Read deferredcall
                deferredcall = data[offset + 31] if offset + 32 <= len(data) else 0
                
                # Extrair nome da função se name_off for válido
                func_name = ""
                if name_off < len(data) and name_off > 0:
                    # Nome começa em name_off e vai até null terminator
                    name_start = name_off
                    name_end = name_start
                    while name_end < len(data) and data[name_end] != 0:
                        name_end += 1
                    if name_end > name_start:
                        try:
                            func_name = data[name_start:name_end].decode('ascii', errors='replace')
                        except:
                            func_name = ""
                
                # Adicionar função
                if func_name and len(func_name) > 3:
                    pkg = func_name.split('.')[0] if '.' in func_name else 'unknown'
                    fname = func_name.split('.')[-1] if '.' in func_name else func_name
                    
                    functions.append({
                        'index': func_count,
                        'entry_offset': entryoff,
                        'name': func_name,
                        'package': pkg,
                        'function': fname,
                        'file_index': nfile,
                        'line': pcln,
                        'args_size': args,
                    })
                    func_count += 1
                
                # Avançar para próxima função
                # Tamanho variável baseado em nfuncdata e NPCDATA
                advance = MIN_FUNC_SIZE + (nfuncdata * 4) + (npCDATA * 4)
                offset += max(advance, 32)
                
            except Exception as e:
                offset += 1
                continue
            
            # Limite de segurança
            if func_count > 100000:
                print(f"  [!] Limite atingido: {func_count} funções")
                break
        
        # Se não encontrou através do parse estrutural, usar regex
        if func_count == 0:
            print("  [*] Tentando extração por regex...")
            func_pattern = re.compile(rb'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)')
            matches = func_pattern.findall(data)
            for m in matches:
                try:
                    name = m.decode('ascii')
                    if len(name) > 5 and '.' in name:
                        pkg = name.split('.')[0]
                        fname = name.split('.')[-1]
                        functions.append({
                            'index': len(functions),
                            'entry_offset': 0,
                            'name': name,
                            'package': pkg,
                            'function': fname,
                            'file_index': 0,
                            'line': 0,
                            'args_size': 0,
                        })
                except:
                    pass
        
        print(f"  Funções encontradas: {len(functions)}")
        
        # Mostrar top packages
        by_package = defaultdict(list)
        for func in functions:
            by_package[func['package']].append(func)
        
        print(f"  Packages únicos: {len(by_package)}")
        for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1]))[:20]:
            print(f"    {pkg:50s}: {len(funcs):4d} funções")
        
        self.functions = functions
        return functions
    
    def parse_gosymtab(self) -> List[Dict]:
        """Parsear .gosymtab - Tabela de símbolos"""
        print("\n[+] Parseando .gosymtab...")
        
        data = self.extract_section('.gosymtab')
        if not data:
            print("  [--] Seção .gosymtab não encontrada")
            return []
        
        print(f"  Tamanho: {len(data):,} bytes")
        
        symbols = []
        
        # Procurar por nomes de pacotes
        pkg_pattern = re.compile(rb'package\s+(\w+)')
        for match in pkg_pattern.finditer(data):
            pkg_name = match.group(1).decode('ascii', errors='replace')
            symbols.append({
                'type': 'package',
                'name': pkg_name,
                'offset': match.start()
            })
        
        # Procurar por definições de struct
        struct_pattern = re.compile(rb'type\s+(\w+)\s+struct\s*\{')
        for match in struct_pattern.finditer(data):
            type_name = match.group(1).decode('ascii', errors='replace')
            symbols.append({
                'type': 'struct',
                'name': type_name,
                'offset': match.start()
            })
        
        # Procurar por interfaces
        iface_pattern = re.compile(rb'type\s+(\w+)\s+interface\s*\{')
        for match in iface_pattern.finditer(data):
            iface_name = match.group(1).decode('ascii', errors='replace')
            symbols.append({
                'type': 'interface',
                'name': iface_name,
                'offset': match.start()
            })
        
        # Procurar por funções (métodos)
        method_pattern = re.compile(rb'func\s+\([^)]+\)\s+(\w+)\s*\(')
        for match in method_pattern.finditer(data):
            method_name = match.group(1).decode('ascii', errors='replace')
            symbols.append({
                'type': 'method',
                'name': method_name,
                'offset': match.start()
            })
        
        print(f"  Símbolos encontrados: {len(symbols)}")
        
        # Agrupar por tipo
        by_type = defaultdict(list)
        for sym in symbols:
            by_type[sym['type']].append(sym)
        
        for sym_type, sym_list in by_type.items():
            print(f"    {sym_type}: {len(sym_list)}")
            for sym in sym_list[:5]:
                print(f"      - {sym['name']}")
        
        return symbols
    
    def extract_source_paths(self) -> List[str]:
        """Extrair caminhos de arquivos fonte"""
        print("\n[+] Extraindo caminhos de fontes...")
        
        paths = set()
        
        # Caminhos Windows
        win_pattern = re.compile(rb'[A-Z]:\\(?:[^\\s\"]+\\.go)+')
        for match in win_pattern.finditer(self.data):
            try:
                path = match.group(0).decode('ascii', errors='replace')
                paths.add(path)
            except:
                pass
        
        # Caminhos Unix
        unix_pattern = re.compile(rb'/[a-zA-Z0-9_./-]+\.go')
        for match in unix_pattern.finditer(self.data):
            try:
                path = match.group(0).decode('ascii', errors='replace')
                paths.add(path)
            except:
                pass
        
        # Padrão simples de arquivos .go
        go_file_pattern = re.compile(rb'([a-zA-Z0-9_/-]+\.go)')
        for match in go_file_pattern.finditer(self.data):
            try:
                path = match.group(1).decode('ascii', errors='replace')
                if '/' in path or '\\' in path:
                    paths.add(path)
            except:
                pass
        
        unique_paths = sorted(paths)
        print(f"  Caminhos de fontes: {len(unique_paths)}")
        for p in unique_paths[:50]:
            print(f"    {p}")
        
        return unique_paths
    
    def analyze_function_signatures(self) -> List[Dict]:
        """Analisar signatures de funções"""
        print("\n[+] Analisando signatures de funções...")
        
        signatures = []
        
        # Procurar por padrões de assinatura de função
        sig_pattern = re.compile(
            rb'func\s+(\(?)?([^\s\(]+)\s*(?:\(([^)]+)\))?\s*(?:\(([^)]+)\))?\s*\{?',
            re.DOTALL
        )
        
        for match in sig_pattern.finditer(self.data):
            try:
                receiver = match.group(1) or ''
                name = match.group(2).decode('ascii', errors='replace') if match.group(2) else ''
                params = match.group(3).decode('ascii', errors='replace') if match.group(3) else ''
                returns = match.group(4).decode('ascii', errors='replace') if match.group(4) else ''
                
                if name and len(name) > 2:
                    signatures.append({
                        'name': name,
                        'receiver': receiver,
                        'params': params[:100],
                        'returns': returns[:100],
                    })
            except:
                pass
        
        print(f"  Signatures encontradas: {len(signatures)}")
        for sig in signatures[:20]:
            params_preview = sig['params'][:50] if sig['params'] else ''
            returns_preview = sig['returns'][:50] if sig['returns'] else ''
            print(f"    func {sig['name']}({params_preview}){f' {returns_preview}' if returns_preview else ''}")
        
        return signatures
    
    def generate_full_reconstruction(self, output_dir: str):
        """Gerar reconstrução completa"""
        print(f"\n[+] Gerando reconstrução em: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Relatório principal
        report_path = os.path.join(output_dir, 'RECOVERY_REPORT.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('# AGY.EXE - Complete Go Binary Recovery Report\n\n')
            f.write(f'**Binary:** {self.binary_path}\n\n')
            f.write(f'**Size:** {len(self.data):,} bytes ({len(self.data)/1024/1024:.1f} MB)\n\n')
            f.write(f'**Analysis Date:** 2026-09-09\n\n')
            
            f.write('## Summary\n\n')
            f.write(f'- **Functions Recovered:** {len(self.functions):,}\n')
            f.write(f'- **Packages Identified:** {len(set(func["package"] for func in self.functions))}\n')
            f.write(f'- **Build Info:** {self.build_info.get("go_version", "Unknown")}\n\n')
            
            f.write('## Top Packages\n\n')
            by_package = defaultdict(list)
            for func in self.functions:
                by_package[func['package']].append(func)
            
            for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1]))[:30]:
                f.write(f'### {pkg}\n\n')
                f.write(f'**Functions:** {len(funcs):,}\n\n')
                f.write('**Sample Functions:**\n\n')
                f.write('```go\n')
                for func in funcs[:15]:
                    f.write(f'func {func["name"]}()\n')
                f.write('```\n\n')
            
            f.write('## Function Signatures\n\n')
            f.write('```go\n')
            for sig in self.signatures[:50]:
                returns_str = f" {sig['returns']}" if sig['returns'] else ""
                f.write(f'func {sig["name"]}({sig["params"]}){returns_str}\n')
            f.write('```\n\n')
            
            f.write('## Source Files\n\n')
            for path in self.source_paths[:50]:
                f.write(f'- `{path}`\n')
            
            f.write('\n## Conclusion\n\n')
            f.write('This report was generated by manual parsing of .gopclntab and .gosymtab sections.\n')
            f.write('The binary is stripped but Go maintains enough metadata to recover function names.\n')
        
        print(f"  Created: {report_path}")
        
        # 2. Funções em JSON
        funcs_json = os.path.join(output_dir, 'functions.json')
        
        # Build by_package dict properly
        by_package = defaultdict(list)
        for func in self.functions:
            by_package[func['package']].append(func['name'])
        
        with open(funcs_json, 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(self.functions),
                'by_package': dict(by_package),
                'functions': self.functions[:5000]  # First 5000
            }, f, indent=2, ensure_ascii=False)
        print(f"  Created: {funcs_json}")
        
        # 3. Lista de pacotes
        packages_txt = os.path.join(output_dir, 'packages.txt')
        with open(packages_txt, 'w', encoding='utf-8') as f:
            by_package = defaultdict(list)
            for func in self.functions:
                by_package[func['package']].append(func['function'])
            
            for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1])):
                f.write(f'{pkg}: {len(funcs)} functions\n')
                for func in funcs[:10]:
                    f.write(f'  - {func}\n')
                f.write('\n')
        print(f"  Created: {packages_txt}")
        
        return {
            'report': report_path,
            'functions': funcs_json,
            'packages': packages_txt,
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python go_binary_parser.py <agy.exe>")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    
    if not os.path.exists(binary_path):
        print(f"Error: {binary_path} not found")
        sys.exit(1)
    
    print("=" * 70)
    print("  GO BINARY PARSER - Advanced Analysis")
    print("=" * 70)
    
    # Create parser
    parser = GoBinaryParser(binary_path)
    
    # Load binary
    if not parser.load():
        print("Failed to load binary")
        sys.exit(1)
    
    # Parse build info
    parser.build_info = parser.parse_buildinfo()
    
    # Parse pclntab
    functions = parser.parse_gopclntab_v2()
    
    # Parse symtab
    symbols = parser.parse_gosymtab()
    
    # Extract source paths
    parser.source_paths = parser.extract_source_paths()
    
    # Analyze signatures
    parser.signatures = parser.analyze_function_signatures()
    
    # Generate reconstruction
    output_dir = r'C:\Users\devel\tools\reverse\go_reconstruction_v2'
    files = parser.generate_full_reconstruction(output_dir)
    
    print("\n" + "=" * 70)
    print("  ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nFunctions recovered: {len(functions):,}")
    print(f"Symbols found: {len(symbols):,}")
    print(f"Source paths: {len(parser.source_paths):,}")
    print(f"Signatures: {len(parser.signatures):,}")
    print(f"\nOutput files:")
    for name, path in files.items():
        size = os.path.getsize(path)
        print(f"  {name}: {path} ({size:,} bytes)")


if __name__ == '__main__':
    main()
