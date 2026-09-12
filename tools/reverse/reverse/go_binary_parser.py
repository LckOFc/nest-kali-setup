#!/usr/bin/env python3
"""
Go Binary Parser - Manual parsing of .gopclntab and .gosymtab
===============================================================
Recupera informações completas de funções Go de binários stripped
"""

import struct
import re
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

class GoBinaryParser:
    """Parser completo para binários Go"""
    
    def __init__(self, binary_path: str):
        self.binary_path = binary_path
        self.data = None
        self.sections = {}
        self.functions = []
        self.types = []
        self.packages = []
        
    def load(self):
        """Carregar binário e extrair seções"""
        print(f"[+] Carregando: {self.binary_path}")
        with open(self.binary_path, 'rb') as f:
            self.data = f.read()
        print(f"[+] Tamanho: {len(self.data):,} bytes")
        
        # Extrair seções Go
        self._extract_sections()
        return len(self.data) > 0
    
    def _extract_sections(self):
        """Extrair todas as seções Go do binário"""
        print("[*] Extraindo seções Go...")
        
        # Procurar por nomes de seções
        section_names = [
            b'.gopclntab',
            b'.gosymtab', 
            b'.go.buildinfo',
            b'.go.version',
            b'.text',
            b'.rodata',
            b'.data',
            b'.bss',
            b'.noptrdata',
            b'.gosetctr',
            b'.gcc_except_table',
        ]
        
        for sec_name in section_names:
            if sec_name in self.data:
                idx = self.data.index(sec_name)
                # Extrair nome da seção (até null terminator)
                end = idx
                while end < len(self.data) and self.data[end:end+1] != b'\x00':
                    end += 1
                name = self.data[idx:end].decode('ascii', errors='replace')
                
                # Encontrar início e tamanho (heurística)
                start = idx - 8  # Antes do nome
                if start < 0:
                    start = 0
                
                # Procurar próximo nome de seção ou marker
                next_idx = self.data.find(b'\x00\x00', idx)
                if next_idx == -1:
                    next_idx = len(self.data)
                
                size = next_idx - start
                if size > 0 and size < len(self.data):
                    self.sections[name] = {
                        'offset': start,
                        'size': size,
                        'data': self.data[start:start+size]
                    }
                    print(f"  [OK] {name}: offset=0x{start:08X}, size={size:,}")
    
    def parse_buildinfo(self) -> Dict[str, str]:
        """Parsear .go.buildinfo para metadados"""
        print("\n[+] Parseando .go.buildinfo...")
        
        result = {}
        buildinfo_data = self.sections.get('.go.buildinfo', {}).get('data', b'')
        
        if not buildinfo_data:
            print("  [--] Seção .go.buildinfo não encontrada")
            return result
        
        # Format: header + key-value pairs
        # Header: 4 bytes magic + 4 bytes version
        if len(buildinfo_data) < 8:
            return result
        
        # Procurar por "go:build" directives
        build_directives = re.findall(rb'go:build\s+(.+)', buildinfo_data)
        for d in build_directives:
            result['build_directive'] = d.decode('ascii', errors='replace')
        
        # Procurar por GOOS e GOARCH
        goos_match = re.search(rb'GOOS=(\w+)', buildinfo_data)
        if goos_match:
            result['GOOS'] = goos_match.group(1).decode()
        
        goarch_match = re.search(rb'GOARCH=(\w+)', buildinfo_data)
        if goarch_match:
            result['GOARCH'] = goarch_match.group(1).decode()
        
        # Procurar por Go version
        go_version_match = re.search(rb'go1\.\d+\.\d+', buildinfo_data)
        if go_version_match:
            result['go_version'] = go_version_match.group(0).decode()
        
        # Procurar por module path
        module_match = re.search(rb'module\s+(\S+)', buildinfo_data)
        if module_match:
            result['module'] = module_match.group(1).decode()
        
        print(f"  Build info encontrado: {len(result)} campos")
        for k, v in result.items():
            print(f"    {k}: {v}")
        
        return result
    
    def parse_pclntab(self) -> List[Dict]:
        """
        Parsear .gopclntab - Tabela de funções Go
        Formato: https://github.com/golang/go/wiki/GoRemotable
        """
        print("\n[+] Parseando .gopclntab...")
        
        pclntab_data = self.sections.get('.gopclntab', {}).get('data', b'')
        if not pclntab_data:
            print("  [--] Seção .gopclntab não encontrada")
            return []
        
        functions = []
        offset = 0
        data_len = len(pclntab_data)
        
        # Go 1.17+ format
        # Cada entrada tem:
        # - funcID (1 byte)
        # - entryoff (4 bytes, little-endian)
        # - startlocation (varies)
        
        # Procurar por padrões de funções
        # Funções Go têm padding e alinhamento específico
        
        # Método 1: Procurar por magic bytes de função
        # Go usa 0xFF como marker para fim da tabela
        
        func_pattern = re.compile(rb'([\x20-\x7e]{4,})')
        
        # Extrair todos os nomes de funções do pclntab
        func_names = set()
        for match in func_pattern.finditer(pclntab_data):
            name = match.group(1).decode('ascii', errors='replace')
            # Filtrar nomes válidos de funções Go
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) and len(name) > 3:
                # Verificar se parece ser um nome de função Go (package.func)
                if '.' in name or name.islower():
                    func_names.add(name)
        
        print(f"  Nomes de funções encontrados: {len(func_names)}")
        
        # Método 2: Parsear estrutura binária do pclntab
        # Tentar encontrar entry points de funções
        entry_points = self._find_function_entries(pclntab_data)
        print(f"  Entry points encontrados: {len(entry_points)}")
        
        # Combinar informações
        for i, (entry_off, name) in enumerate(zip(entry_points, list(func_names)[:len(entry_points)])):
            func_info = {
                'index': i,
                'entry_offset': entry_off,
                'name': name,
                'package': name.split('.')[0] if '.' in name else 'unknown',
                'function': name.split('.')[-1] if '.' in name else name,
            }
            functions.append(func_info)
        
        self.functions = functions
        return functions
    
    def _find_function_entries(self, data: bytes) -> List[int]:
        """Procurar por entry points de funções no pclntab"""
        entries = []
        
        # Entry points em Go são offsets relative ao início da seção .text
        # Procurar por padrões de alinhamento (normalmente 16 bytes)
        
        # Método: Procurar por valores que parecem ser offsets de função
        # Em Go, function entry tables têm entries de 4 ou 8 bytes
        
        # Tentar parsear como tabela de offsets
        for i in range(0, len(data) - 4, 4):
            val = struct.unpack_from('<I', data, i)[0]
            # Validar se é um offset razoável (< 100MB)
            if 0 < val < 0x10000000 and val % 16 == 0:  # Alinhado em 16 bytes
                # Verificar se não é um valor comum (muito frequente)
                if val not in entries or len(entries) < 100:
                    entries.append(val)
        
        # Limitar a entradas únicas e ordenadas
        entries = sorted(list(set(entries)))[:500]
        return entries
    
    def parse_symtab(self) -> List[Dict]:
        """Parsear .gosymtab - Tabela de símbolos Go"""
        print("\n[+] Parseando .gosymtab...")
        
        symtab_data = self.sections.get('.gosymtab', {}).get('data', b'')
        if not symtab_data:
            print("  [--] Seção .gosymtab não encontrada")
            return []
        
        symbols = []
        
        # Procurar por nomes de pacote e funções
        pkg_pattern = re.compile(rb'package\s+(\w+)')
        for match in pkg_pattern.finditer(symtab_data):
            pkg_name = match.group(1).decode('ascii', errors='replace')
            symbols.append({
                'type': 'package',
                'name': pkg_name,
                'offset': match.start()
            })
        
        # Procurar por definições de tipo
        type_pattern = re.compile(rb'type\s+(\w+)\s+struct')
        for match in type_pattern.finditer(symtab_data):
            type_name = match.group(1).decode('ascii', errors='replace')
            symbols.append({
                'type': 'struct',
                'name': type_name,
                'offset': match.start()
            })
        
        # Procurar por interfaces
        iface_pattern = re.compile(rb'type\s+(\w+)\s+interface')
        for match in iface_pattern.finditer(symtab_data):
            iface_name = match.group(1).decode('ascii', errors='replace')
            symbols.append({
                'type': 'interface',
                'name': iface_name,
                'offset': match.start()
            })
        
        print(f"  Símbolos encontrados: {len(symbols)}")
        for sym in symbols[:20]:
            print(f"    [{sym['type']}] {sym['name']}")
        
        return symbols
    
    def parse_file_lines(self) -> List[Dict]:
        """Extrair informações de arquivo e linha"""
        print("\n[+] Extraindo informações de arquivo/linha...")
        
        file_info = []
        
        # Procurar por referências a arquivos Go
        file_pattern = re.compile(rb'([^\\s]+\.go):(\d+)')
        for match in file_pattern.finditer(self.data):
            try:
                filename = match.group(1).decode('ascii', errors='replace')
                lineno = int(match.group(2))
                file_info.append({
                    'file': filename,
                    'line': lineno,
                    'offset': match.start()
                })
            except:
                pass
        
        # Deduplicate
        unique_files = list(dict.fromkeys([f['file'] for f in file_info]))
        print(f"  Arquivos Go encontrados: {len(unique_files)}")
        for f in unique_files[:30]:
            print(f"    {f}")
        
        return file_info
    
    def extract_source_paths(self) -> List[str]:
        """Extrair caminhos de arquivos fonte embutidos"""
        print("\n[+] Procurando caminhos de fontes...")
        
        paths = []
        
        # Procurar por caminhos de arquivos Go
        go_path_pattern = re.compile(rb'[A-Za-z]:\\[^\\s\"]+\.go')
        for match in go_path_pattern.finditer(self.data):
            try:
                path = match.group(0).decode('ascii', errors='replace')
                paths.append(path)
            except:
                pass
        
        # Procurar por caminhos Unix
        unix_path_pattern = re.compile(rb'/[a-zA-Z0-9_./-]+\.go')
        for match in unix_path_pattern.finditer(self.data):
            try:
                path = match.group(0).decode('ascii', errors='replace')
                paths.append(path)
            except:
                pass
        
        # Deduplicate
        unique_paths = list(dict.fromkeys(paths))
        print(f"  Caminhos de fontes encontrados: {len(unique_paths)}")
        for p in unique_paths[:50]:
            print(f"    {p}")
        
        return unique_paths
    
    def analyze_runtime(self) -> Dict:
        """Analisar código do runtime Go"""
        print("\n[+] Analisando runtime Go...")
        
        runtime_info = {
            'version': None,
            'arch': None,
            'os': None,
            'features': []
        }
        
        # Procurar por versão Go
        go_version_patterns = [
            rb'go1\.(\d+)\.(\d+)',
            rb'runtime\.ver\s*=\s*"go1\.(\d+)\.(\d+)"',
        ]
        
        for pattern in go_version_patterns:
            match = re.search(pattern, self.data)
            if match:
                if match.group(1) and match.group(2):
                    runtime_info['version'] = f"go1.{match.group(1).decode()}.{match.group(2).decode()}"
                    break
        
        # Procurar por features do runtime
        features = [
            (rb'race', 'Race detector'),
            (rb'debug', 'Debug mode'),
            (rb'cgo', 'CGO enabled'),
            (rb'netgo', 'Pure Go net'),
            (rb'osusergo', 'OS user lookup'),
        ]
        
        for flag, name in features:
            if flag in self.data:
                runtime_info['features'].append(name)
        
        print(f"  Runtime info: {runtime_info}")
        return runtime_info
    
    def generate_reconstruction(self, output_dir: str):
        """Gerar código reconstruído baseado na análise"""
        print(f"\n[+] Gerando reconstrução em: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Gerar lista completa de funções
        funcs_file = os.path.join(output_dir, 'functions.go')
        with open(funcs_file, 'w') as f:
            f.write('// Auto-generated function list from agy.exe\n')
            f.write(f'// Total functions: {len(self.functions)}\n\n')
            f.write('package main\n\n')
            
            # Group by package
            by_package = defaultdict(list)
            for func in self.functions:
                pkg = func.get('package', 'unknown')
                by_package[pkg].append(func)
            
            for pkg, funcs in sorted(by_package.items()):
                f.write(f'// Package: {pkg}\n')
                f.write(f'// Functions: {len(funcs)}\n\n')
                
                for func in funcs[:20]:  # First 20 per package
                    name = func.get('function', 'Unknown')
                    entry = func.get('entry_offset', 0)
                    f.write(f'// func {name}() - entry: 0x{entry:08X}\n')
                
                f.write('\n')
        
        print(f"  Created: {funcs_file}")
        
        # 2. Gerar estrutura de pacotes
        packages_file = os.path.join(output_dir, 'packages.txt')
        with open(packages_file, 'w') as f:
            f.write('Go Packages in agy.exe\n')
            f.write('=' * 50 + '\n\n')
            
            by_package = defaultdict(list)
            for func in self.functions:
                pkg = func.get('package', 'unknown')
                by_package[pkg].append(func.get('function', 'unknown'))
            
            for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1])):
                f.write(f'{pkg}: {len(funcs)} functions\n')
                for func in funcs[:5]:
                    f.write(f'  - {func}\n')
                f.write('\n')
        
        print(f"  Created: {packages_file}")
        
        # 3. Gerar relatório completo
        report_file = os.path.join(output_dir, 'analysis_report.txt')
        with open(report_file, 'w') as f:
            f.write('AGY.EXE Go Binary Analysis Report\n')
            f.write('=' * 60 + '\n\n')
            
            f.write(f'Binary: {self.binary_path}\n')
            f.write(f'Size: {len(self.data):,} bytes\n\n')
            
            f.write('SECTIONS FOUND:\n')
            for sec_name, sec_info in self.sections.items():
                f.write(f'  {sec_name}: offset=0x{sec_info["offset"]:08X}, size={sec_info["size"]:,}\n')
            f.write('\n')
            
            f.write(f'TOTAL FUNCTIONS: {len(self.functions)}\n\n')
            
            f.write('TOP PACKAGES:\n')
            by_package = defaultdict(list)
            for func in self.functions:
                pkg = func.get('package', 'unknown')
                by_package[pkg].append(func)
            
            for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1]))[:30]:
                f.write(f'  {pkg}: {len(funcs)} functions\n')
            
            f.write('\n' + '=' * 60 + '\n')
            f.write('End of Report\n')
        
        print(f"  Created: {report_file}")
        
        return {
            'functions_file': funcs_file,
            'packages_file': packages_file,
            'report_file': report_file,
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python go_binary_parser.py <agy.exe>")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    
    if not os.path.exists(binary_path):
        print(f"Error: {binary_path} not found")
        sys.exit(1)
    
    # Create parser
    parser = GoBinaryParser(binary_path)
    
    # Load binary
    if not parser.load():
        print("Failed to load binary")
        sys.exit(1)
    
    # Parse build info
    buildinfo = parser.parse_buildinfo()
    
    # Parse pclntab
    functions = parser.parse_pclntab()
    
    # Parse symtab
    symbols = parser.parse_symtab()
    
    # Extract file/line info
    file_lines = parser.parse_file_lines()
    
    # Extract source paths
    source_paths = parser.extract_source_paths()
    
    # Analyze runtime
    runtime = parser.analyze_runtime()
    
    # Generate reconstruction
    output_dir = r'C:\Users\devel\tools\reverse\go_reconstruction'
    files = parser.generate_reconstruction(output_dir)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nFunctions parsed: {len(functions)}")
    print(f"Symbols found: {len(symbols)}")
    print(f"Source files found: {len(source_paths)}")
    print(f"\nOutput files:")
    for name, path in files.items():
        print(f"  {name}: {path}")
    
    # Show top packages
    by_package = defaultdict(list)
    for func in functions:
        pkg = func.get('package', 'unknown')
        by_package[pkg].append(func)
    
    print("\nTop 20 Packages:")
    for pkg, funcs in sorted(by_package.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {pkg:50s}: {len(funcs):4d} functions")


if __name__ == '__main__':
    main()
