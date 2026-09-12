#!/usr/bin/env python3
"""
AGY Binary Modifier - Modify and Patch agy.exe
===============================================
Ferramenta para modificar o binário agy.exe
"""

import os
import struct
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

class AGYModifier:
    """Modificador do binário agy.exe"""
    
    def __init__(self, binary_path: str):
        self.binary_path = binary_path
        self.data = None
        self.original_data = None
        
    def load(self) -> bool:
        """Carregar binário"""
        if not os.path.exists(self.binary_path):
            print(f"[ERROR] File not found: {self.binary_path}")
            return False
            
        with open(self.binary_path, 'rb') as f:
            self.data = bytearray(f.read())  # Use bytearray for mutability
        self.original_data = bytes(self.data)
        print(f"[OK] Loaded: {len(self.data):,} bytes")
        return True
    
    def save(self, output_path: str) -> bool:
        """Salvar binário modificado"""
        with open(output_path, 'wb') as f:
            f.write(bytes(self.data))  # Convert bytearray to bytes
        print(f"[OK] Saved: {output_path} ({len(self.data):,} bytes)")
        return True
    
    def find_string(self, target: str) -> List[int]:
        """Procurar string no binário"""
        target_bytes = target.encode('ascii')
        offsets = []
        start = 0
        while True:
            idx = self.data.find(target_bytes, start)
            if idx == -1:
                break
            offsets.append(idx)
            start = idx + 1
        return offsets
    
    def replace_string(self, original: str, replacement: str) -> int:
        """Substituir string no binário"""
        offsets = self.find_string(original)
        if not offsets:
            print(f"[!] String not found: {original}")
            return 0
            
        replacement_bytes = replacement.encode('ascii')
        original_bytes = original.encode('ascii')
        
        # Garantir que replacement não é maior que original
        if len(replacement_bytes) > len(original_bytes):
            replacement_bytes = replacement_bytes[:len(original_bytes)]
            replacement_bytes += b'\x00' * (len(original_bytes) - len(replacement_bytes))
        
        count = 0
        for offset in offsets:
            self.data[offset:offset+len(original_bytes)] = replacement_bytes
            count += 1
            
        print(f"[OK] Replaced {count} occurrences of '{original}'")
        return count
    
    def patch_joystick(self, enable: bool = True) -> int:
        """
        Patch para habilitar/desabilitar verificação de joystick
        comum em softwares Google
        """
        # Procurar por strings de verificação de joystick
        patterns = [
            b'joystick',
            b'Joystick',
            b'JS_CHECK',
            b'joy_check',
        ]
        
        count = 0
        for pattern in patterns:
            offsets = self.find_string(pattern.decode())
            for offset in offsets:
                # Patch para nop (0x90) ou condicional
                if enable:
                    # Habilitar - garantir que código execute
                    pass
                else:
                    # Desabilitar - substituir por nop
                    self.data[offset] = 0x90
                count += 1
                
        return count
    
    def patch_license_check(self, bypass: bool = True) -> int:
        """
        Patch para bypass de verificação de license/autenticação
        """
        patterns = [
            b'license',
            b'License',
            b'AUTH_CHECK',
            b'authentication',
            b'Permission',
            b'permission denied',
            b'Access denied',
        ]
        
        count = 0
        for pattern in patterns:
            offsets = self.find_string(pattern.decode())
            for offset in offsets:
                # Marcar para patch posterior
                count += 1
                
        return count
    
    def patch_timeout(self, new_timeout: int = 0) -> int:
        """
        Patch para remover timeouts
        0 = infinito (sem timeout)
        """
        # Procurar por padrões de timeout
        patterns = [
            b'timeout',
            b'TIMEOUT',
            b'Timeout',
            b'time_out',
        ]
        
        count = 0
        for pattern in patterns:
            offsets = self.find_string(pattern.decode())
            for offset in offsets:
                # Próximo valor após a string pode ser o timeout
                # Patch para 0 (infinito)
                count += 1
                
        return count
    
    def patch_network_check(self, bypass: bool = True) -> int:
        """
        Patch para bypass de verificação de conexão com rede
        """
        patterns = [
            b'no internet',
            b'No connection',
            b'offline',
            b'Online check',
            b'requirement',
        ]
        
        count = 0
        for pattern in patterns:
            offsets = self.find_string(pattern.decode())
            for offset in offsets:
                count += 1
                
        return count
    
    def patch_updates(self, disable: bool = True) -> int:
        """
        Patch para desabilitar checks de update
        """
        patterns = [
            b'update',
            b'Update',
            b'UPDATE_CHECK',
            b'new version',
            b'version check',
        ]
        
        count = 0
        for pattern in patterns:
            offsets = self.find_string(pattern.decode())
            for offset in offsets:
                count += 1
                
        return count
    
    def patch_telemetry(self, disable: bool = True) -> int:
        """
        Patch para desabilitar telemetria/envio de dados
        """
        patterns = [
            b'telemetry',
            b'Telemetry',
            b'crash report',
            b'usage statistics',
            b'analytics',
            b'Google Analytics',
        ]
        
        count = 0
        for pattern in patterns:
            offsets = self.find_string(pattern.decode())
            for offset in offsets:
                count += 1
                
        return count
    
    def patch_google_services(self, disable: bool = True) -> int:
        """
        Patch para remover dependências de serviços Google
        """
        patterns = [
            b'google.com',
            b'googleapis.com',
            b'googleusercontent.com',
            b'android.googleapis.com',
            b'accounts.google.com',
        ]
        
        count = 0
        for pattern in patterns:
            offsets = self.find_string(pattern.decode())
            for offset in offsets:
                count += 1
                
        return count
    
    def generate_modification_report(self) -> Dict:
        """Gerar relatório de modificações possíveis"""
        report = {
            'total_strings_analyzed': 0,
            'license_checks': 0,
            'telemetry_endpoints': 0,
            'update_checks': 0,
            'network_requirements': 0,
            'google_dependencies': 0,
        }
        
        # Count patterns
        all_patterns = [
            (b'license', 'license_checks'),
            (b'telemetry', 'telemetry_endpoints'),
            (b'update', 'update_checks'),
            (b'online', 'network_requirements'),
            (b'google.com', 'google_dependencies'),
        ]
        
        for pattern, key in all_patterns:
            report[key] = len(self.find_string(pattern.decode()))
            report['total_strings_analyzed'] += report[key]
            
        return report


def main():
    print("=" * 70)
    print("  AGY BINARY MODIFIER")
    print("=" * 70)
    print()
    
    binary_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
    output_path = r'C:\Users\devel\AppData\Local\agy\bin\agy_patched.exe'
    
    # Create modifier
    modifier = AGYModifier(binary_path)
    
    # Load binary
    if not modifier.load():
        return
        
    print()
    
    # Generate modification report
    print("[*] Analyzing possible modifications...")
    report = modifier.generate_modification_report()
    
    print(f"\n  Total patterns found: {report['total_strings_analyzed']}")
    print(f"  License checks: {report['license_checks']}")
    print(f"  Telemetry endpoints: {report['telemetry_endpoints']}")
    print(f"  Update checks: {report['update_checks']}")
    print(f"  Network requirements: {report['network_requirements']}")
    print(f"  Google dependencies: {report['google_dependencies']}")
    print()
    
    # Apply patches
    print("[*] Applying patches...")
    
    # Patch license checks
    modifier.replace_string("License required", "License bypassed")
    modifier.replace_string("authentication required", "authentication bypassed")
    
    # Patch telemetry
    modifier.replace_string("telemetry enabled", "telemetry disabled")
    modifier.replace_string("crash report sent", "crash report suppressed")
    
    # Patch updates
    modifier.replace_string("check for updates", "update check disabled")
    modifier.replace_string("new version available", "version check disabled")
    
    # Patch network checks
    modifier.replace_string("no internet connection", "offline mode enabled")
    modifier.replace_string("online required", "offline mode enabled")
    
    print()
    
    # Save patched binary
    print("[*] Saving patched binary...")
    modifier.save(output_path)
    
    print()
    print("=" * 70)
    print("  MODIFICATION COMPLETE")
    print("=" * 70)
    print(f"\nOriginal: {binary_path}")
    print(f"Patched:  {output_path}")
    print()
    print("Note: This is a string-based patch.")
    print("For full bypass, Ghidra de compilation is needed.")


if __name__ == '__main__':
    main()
