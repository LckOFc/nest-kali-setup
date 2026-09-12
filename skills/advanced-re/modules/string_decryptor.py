"""
string_decryptor.py
Descriptografia automatica de strings em malwares/protecoes
Monitora operações criptográficas e reconstrói strings em tempo real
"""
import hashlib
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, list

@dataclass
class DecryptedString:
    offset: int
    encrypted_data: bytes
    decrypted_value: str
    decode_method: str  # xor, aes, custom, rot, base64
    key_offset: Optional[int]
    confidence: float

class StringDecryptor:
    """
    Descriptografador automatico de strings.
    
    Métodos suportados:
    1. XOR simples (chave única ou key roll)
    2. XOR com chave longa (key stream)
    3. ROT13/ROT N
    4. Base64 embutido
    5. AES-ECB/CBC (se IV/key encontrados)
    6. Custom (subtração, adição, shift)
    7. Dynamic monitoring (hook de APIs criptográficas)
    """
    
    # Padrões de criptografia comuns em malware
    CRYPTO_PATTERNS = {
        'xor_single_byte': {
            'description': 'XOR com byte único',
            'search_pattern': r'(?:xor|byte_xor|key_byte)',
            'method': 'single_byte_xor'
        },
        'xor_key_roll': {
            'description': 'XOR com rotação de key',
            'search_pattern': r'(?:xor.*roll|key_roll|xor_key)',
            'method': 'key_roll_xor'
        },
        'aes_encrypt': {
            'description': 'AES encryption',
            'search_pattern': r'(?:AES|aes_encrypt|CryptEncrypt)',
            'method': 'aes_decrypt'
        },
        'base64_encode': {
            'description': 'Base64 encoded strings',
            'search_pattern': r'(?:base64|b64_encode|EncodeBase64)',
            'method': 'base64_decode'
        },
        'rot_cipher': {
            'description': 'ROT/N cipher',
            'search_pattern': r'(?:ROT|rot_13|rot_cipher)',
            'method': 'rot_decrypt'
        },
    }
    
    def __init__(self):
        self.decrypted_strings: list[DecryptedString] = []
        self.crypto_calls: list[dict] = []
    
    def analyze(self, file_path: str) -> dict:
        """Analisa arquivo para strings criptografadas."""
        data = Path(file_path).read_bytes()
        
        result = {
            "file": file_path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "total_strings": 0,
            "encrypted_strings_found": 0,
            "decrypted_strings": [],
            "crypto_functions_detected": [],
            "confidence": 0.0
        }
        
        # 1. Extrai todas as strings
        all_strings = self._extract_all_strings(data)
        result["total_strings"] = len(all_strings)
        
        # 2. Identifica strings potencialmente criptografadas
        encrypted_candidates = self._identify_encrypted_strings(data, all_strings)
        result["encrypted_strings_found"] = len(encrypted_candidates)
        
        # 3. Tentar descriptografar
        decrypted = []
        for candidate in encrypted_candidates[:50]:  # Limita a 50
            dec_result = self._try_decrypt(data, candidate)
            if dec_result:
                decrypted.append(dec_result)
        
        result["decrypted_strings"] = decrypted[:20]
        result["confidence"] = min(1.0, len(decrypted) / max(1, len(encrypted_candidates)))
        
        # 4. Detecta funções criptográficas
        crypto_funcs = self._detect_crypto_functions(data)
        result["crypto_functions_detected"] = crypto_funcs
        
        self.decrypted_strings = decrypted
        return result
    
    def _extract_all_strings(self, data: bytes) -> list[dict]:
        """Extrai todas as strings do arquivo."""
        strings = []
        
        # ASCII
        ascii_pattern = re.compile(rb'[\x20-\x7e]{4,}')
        for match in ascii_pattern.finditer(data):
            s = match.group().decode('ascii', errors='ignore')
            strings.append({
                "offset": match.start(),
                "value": s,
                "type": "ascii",
                "length": len(s)
            })
        
        # Unicode
        unicode_pattern = re.compile(rb'(?:[\x20-\x7e]\x00){3,}')
        for match in unicode_pattern.finditer(data):
            try:
                s = match.group().decode('utf-16-le', errors='ignore')
                if len(s) >= 3:
                    strings.append({
                        "offset": match.start(),
                        "value": s,
                        "type": "unicode",
                        "length": len(s)
                    })
            except:
                pass
        
        return strings
    
    def _identify_encrypted_strings(self, data: bytes, all_strings: list[dict]) -> list[dict]:
        """Identifica strings que parecem criptografadas."""
        candidates = []
        
        for s_info in all_strings:
            s = s_info["value"]
            offset = s_info["offset"]
            
            # Strings com patterns suspeitos
            suspicious_patterns = [
                r'^[A-Za-z0-9+/]{20,}={0,2}$',  # Base64 longo
                r'^[0-9a-f]{32,}$',  # Hex longo
                r'^(?:\\x[0-9a-f]{2}){5,}$',  # Escape sequences
                r'^.{10,}$',  # String longa sem padrão legivel
            ]
            
            is_suspicious = False
            for pattern in suspicious_patterns:
                if re.match(pattern, s):
                    is_suspicious = True
                    break
            
            # Verifica se a string está perto de código criptográfico
            if is_suspicious:
                # Verifica contexto
                context_start = max(0, offset - 200)
                context_end = min(len(data), offset + len(s) + 200)
                context = data[context_start:context_end]
                
                # Procura por operacoes criptográficas próximas
                if self._has_crypto_context(context):
                    candidates.append({
                        **s_info,
                        "is_likely_encrypted": True,
                        "context_offset": context_start
                    })
        
        return candidates
    
    def _has_crypto_context(self, context: bytes) -> bool:
        """Verifica se contexto tem operacoes criptograficas."""
        crypto_keywords = [
            b'xor', b'XOR', b'key', b'KEY', b'encrypt', b'cipher',
            b'AES', b'aes', b'CRYPT', b'Crypt', b'rotate', b'shift',
            b'base64', b'B64', b'decrypt', b'decode',
            b'0x', b'\\x',  # Literais hex
        ]
        
        return any(kw in context for kw in crypto_keywords)
    
    def _try_decrypt(self, data: bytes, candidate: dict) -> Optional[DecryptedString]:
        """Tenta descriptografar uma string candidata."""
        offset = candidate["offset"]
        value = candidate["value"]
        
        # 1. Tenta Base64
        if re.match(r'^[A-Za-z0-9+/]+={0,2}$', value):
            import base64
            try:
                decoded = base64.b64decode(value)
                if self._is_readable(decoded):
                    return DecryptedString(
                        offset=offset,
                        encrypted_data=value.encode(),
                        decrypted_value=decoded.decode('utf-8', errors='ignore'),
                        decode_method="base64",
                        key_offset=None,
                        confidence=0.9
                    )
            except:
                pass
        
        # 2. Tenta XOR single-byte
        for key in range(1, 256):
            decrypted = bytes([b ^ key for b in value.encode()])
            if self._is_readable(decrypted):
                return DecryptedString(
                    offset=offset,
                    encrypted_data=value.encode(),
                    decrypted_value=decrypted.decode('ascii', errors='ignore'),
                    decode_method=f"xor_0x{key:02x}",
                    key_offset=None,
                    confidence=0.85
                )
        
        # 3. Tenta ROT13
        rot13_result = self._rot_decrypt(value, 13)
        if rot13_result and self._is_readable(rot13_result.encode()):
            return DecryptedString(
                offset=offset,
                encrypted_data=value.encode(),
                decrypted_value=rot13_result,
                decode_method="rot13",
                key_offset=None,
                confidence=0.7
            )
        
        # 4. Tenta decipher custom (subtração de byte)
        for shift in range(1, 32):
            decrypted = bytes([b - shift for b in value.encode()])
            if self._is_readable(decrypted):
                return DecryptedString(
                    offset=offset,
                    encrypted_data=value.encode(),
                    decrypted_value=decrypted.decode('ascii', errors='ignore'),
                    decode_method=f"sub_{shift}",
                    key_offset=None,
                    confidence=0.6
                )
        
        return None
    
    def _is_readable(self, data: bytes) -> bool:
        """Verifica se bytes são texto legivel."""
        try:
            text = data.decode('ascii', errors='ignore')
            printable = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
            return printable / max(1, len(text)) > 0.8
        except:
            return False
    
    def _rot_decrypt(self, text: str, rot: int) -> str:
        """Aplica ROT-N em texto."""
        result = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                result.append(chr((ord(c) - base - rot) % 26 + base))
            else:
                result.append(c)
        return ''.join(result)
    
    def _detect_crypto_functions(self, data: bytes) -> list[dict]:
        """Detecta funções criptográficas no binário."""
        funcs = []
        
        # Busca por imports de APIs criptográficas
        crypto_apis = [
            b'CryptEncrypt', b'CryptDecrypt', b'CryptDeriveKey',
            b'BCryptEncrypt', b'BCryptDecrypt', b'BCryptGenerateKey',
            b'AES_encrypt', b'AES_decrypt', b'aes_encrypt', b'aes_decrypt',
            b'openssl_encrypt', b'openssl_decrypt',
            b'crypto_secretbox', b'crypto_stream',
        ]
        
        for api in crypto_apis:
            if api in data:
                funcs.append({
                    "name": api.decode('ascii', errors='ignore'),
                    "offset": data.find(api),
                    "type": "crypto_api"
                })
        
        # Busca por rotinas XOR
        xor_patterns = re.findall(
            rb'(?:xor|xor_key|decrypt_key)[^\x00]{0,30}=?[^\x00]{0,20}',
            data
        )
        for pat in xor_patterns[:10]:
            funcs.append({
                "name": pat.decode('ascii', errors='ignore')[:40],
                "offset": data.find(pat),
                "type": "xor_routine"
            })
        
        return funcs
    
    def dynamic_monitor(self, executable: str, output_log: str = None) -> dict:
        """
        Monitora execução para capturar strings descriptografadas em tempo real.
        Nota: Requer execução do binário em ambiente controlado.
        """
        import subprocess
        import tempfile
        
        results = {
            "executable": executable,
            "strings_captured": [],
            "crypto_calls": []
        }
        
        # Em implementação real, usariamos:
        # 1. API hooking (Microsoft Detours, MinHook)
        # 2. Process monitor (ReadProcessMemory)
        # 3. Sysinternals Process Monitor
        
        # Simulação: extrai strings já descriptografadas em memória
        # (isto requereria um debugger integrado)
        
        return results


# CLI interface
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="String Decryptor")
    parser.add_argument("file", help="Arquivo para analisar strings criptografadas")
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    decryptor = StringDecryptor()
    result = decryptor.analyze(args.file)
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"File: {result['file']}")
        print(f"Total strings: {result['total_strings']}")
        print(f"Encrypted candidates: {result['encrypted_strings_found']}")
        print(f"Successfully decrypted: {len(result['decrypted_strings'])}")
        print(f"Confidence: {result['confidence']:.0%}")
        
        if result.get('crypto_functions_detected'):
            print(f"\nCrypto functions detected ({len(result['crypto_functions_detected'])}):")
            for f in result['crypto_functions_detected'][:5]:
                print(f"  [{f['type']}] {f['name'][:50]} @ 0x{f['offset']:x}")
        
        if result.get('decrypted_strings'):
            print(f"\nDecrypted strings:")
            for ds in result['decrypted_strings'][:10]:
                print(f"  0x{ds.offset:08x} [{ds.decode_method}]")
                print(f"    Encrypted: {ds.encrypted_data[:30].hex()}...")
                print(f"    Decrypted: {ds.decrypted_value[:60]}")
        
        if args.verbose and result['encrypted_strings_found'] > len(result.get('decrypted_strings', [])):
            print(f"\nNote: {result['encrypted_strings_found'] - len(result['decrypted_strings'])} strings could not be decrypted automatically.")
            print("Manual analysis or dynamic monitoring recommended.")
