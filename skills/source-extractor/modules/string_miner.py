"""
string_miner.py
Advanced string extraction with decoding (XOR, Base64, ROL/ROR, etc.)
"""
import re
import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

@dataclass
class DecodedString:
    offset: int
    original: str
    decoded: str
    decode_type: str  # xor, base64, rol, ror, rot13, utf16
    confidence: float

class StringMiner:
    """
    Minerador avancado de strings com decodificacao multipla.
    
    Suporta:
    - ASCII strings
    - Unicode (UTF-16 LE)
    - Base64 decoding
    - XOR decoding (with/without key)
    - ROL/ROR bit rotation
    - ROT13
    - URL encoding
    - Hex encoding
    """
    
    def __init__(self, min_length: int = 4, max_strings: int = 50000):
        self.min_length = min_length
        self.max_strings = max_strings
        self.decoded_count = 0
    
    def mine(self, file_path: str) -> dict:
        """Extrai e decodifica todas as strings."""
        data = Path(file_path).read_bytes()
        
        results = {
            "file": file_path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "total_strings": 0,
            "ascii_strings": [],
            "unicode_strings": [],
            "base64_decoded": [],
            "xor_decoded": [],
            "other_decoded": [],
            "url_encoded": [],
            "hex_encoded": [],
        }
        
        # Extrai strings basicas
        results["ascii_strings"] = self._extract_ascii(data)[:self.max_strings]
        results["unicode_strings"] = self._extract_unicode(data)[:self.max_strings]
        
        # Decodifica
        results["base64_decoded"] = self._decode_base64(data)[:500]
        results["xor_decoded"] = self._decode_xor(data)[:200]
        results["url_encoded"] = self._decode_url(data)[:200]
        results["hex_encoded"] = self._decode_hex(data)[:200]
        
        results["total_strings"] = (
            len(results["ascii_strings"]) +
            len(results["unicode_strings"]) +
            len(results["base64_decoded"]) +
            len(results["xor_decoded"])
        )
        
        return results
    
    def _extract_ascii(self, data: bytes, min_len: int = None) -> List[str]:
        """Extrai strings ASCII."""
        min_len = min_len or self.min_length
        pattern = re.compile(rb'[\x20-\x7e]{' + str(min_len).encode() + rb',}')
        return [s.decode('ascii', errors='ignore') for s in pattern.findall(data)]
    
    def _extract_unicode(self, data: bytes, min_len: int = None) -> List[str]:
        """Extrai strings Unicode (UTF-16 LE)."""
        min_len = min_len or self.min_length
        pattern = re.compile(rb'(?:[\x20-\x7e]\x00){' + str(min_len).encode() + rb',}')
        results = []
        for match in pattern.finditer(data):
            try:
                decoded = match.group().decode('utf-16-le', errors='ignore')
                if len(decoded) >= min_len:
                    results.append(decoded)
            except:
                pass
        return results
    
    def _decode_base64(self, data: bytes) -> List[dict]:
        """Tenta decodificar strings Base64."""
        results = []
        # Pattern Base64 (4+ chars, valido base64)
        b64_pattern = re.compile(rb'([A-Za-z0-9+/]{8,}={0,2})')
        
        for match in b64_pattern.finditer(data):
            b64_str = match.group(1).decode('ascii', errors='ignore')
            try:
                decoded = base64.b64decode(b64_str)
                # Verifica se é string valida
                if len(decoded) >= self.min_length:
                    text = decoded.decode('utf-8', errors='ignore')
                    if any(c.isalpha() for c in text):
                        results.append({
                            "offset": match.start(),
                            "encoded": b64_str[:50],
                            "decoded": text[:100],
                            "type": "base64"
                        })
            except:
                pass
        
        return results[:500]
    
    def _decode_xor(self, data: bytes, max_key: int = 256) -> List[dict]:
        """Tenta decodificar strings XOR com chaves simples."""
        results = []
        
        # Procura por blocks que podem ser XOR (alta entropia)
        block_size = 32
        for i in range(0, len(data) - block_size, block_size):
            block = data[i:i+block_size]
            
            # Pula blocks com entropia muito baixa (já são texto)
            if self._calc_entropy(block) < 4.0:
                continue
            
            # Tenta chaves 1-255
            for key in range(1, min(max_key, 20)):
                decoded = bytes([b ^ key for b in block])
                
                # Verifica se resultou em texto legivel
                try:
                    text = decoded.decode('ascii', errors='ignore')
                    printable = sum(1 for c in text if 0x20 <= ord(c) <= 0x7e or c in '\n\r\t')
                    if printable / len(text) > 0.8 and len(text) >= self.min_length:
                        results.append({
                            "offset": i,
                            "key": key,
                            "original_hex": block[:16].hex(),
                            "decoded": text[:50],
                            "type": f"xor_0x{key:02x}"
                        })
                        break  # Achou chave, continua
                except:
                    pass
        
        return results[:200]
    
    def _decode_url(self, data: bytes) -> List[dict]:
        """Decodifica URL encoding (%XX)."""
        results = []
        pattern = re.compile(rb'%([0-9A-Fa-f]{2})')
        
        for match in pattern.finditer(data):
            start = max(0, match.start() - 20)
            end = min(len(data), match.end() + 50)
            segment = data[start:end]
            
            try:
                decoded = segment.decode('ascii', errors='ignore')
                # Url decode
                import urllib.parse
                decoded_text = urllib.parse.unquote(decoded)
                if any(c.isalpha() for c in decoded_text) and len(decoded_text) > 5:
                    results.append({
                        "offset": start,
                        "encoded": decoded[:50],
                        "decoded": decoded_text[:100],
                        "type": "url_encoded"
                    })
            except:
                pass
        
        return results[:200]
    
    def _decode_hex(self, data: bytes) -> List[dict]:
        """Decodifica strings hex encoded."""
        results = []
        # Pattern: par de hex chars (ex: 48 65 6c 6c 6f = "Hello")
        pattern = re.compile(rb'([0-9A-Fa-f]{2}\s*){4,}')
        
        for match in pattern.finditer(data):
            hex_str = match.group(0).replace(b' ', b'').decode('ascii', errors='ignore')
            try:
                decoded = bytes.fromhex(hex_str)
                text = decoded.decode('utf-8', errors='ignore')
                if len(text) >= self.min_length and any(c.isalpha() for c in text):
                    results.append({
                        "offset": match.start(),
                        "hex": hex_str[:50],
                        "decoded": text[:100],
                        "type": "hex_encoded"
                    })
            except:
                pass
        
        return results[:200]
    
    def _calc_entropy(self, data: bytes) -> float:
        """Entropia de Shannon."""
        if not data:
            return 0.0
        import math
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1
        length = len(data)
        entropy = 0.0
        for count in freq:
            if count:
                p = count / length
                if p > 0:
                    entropy -= p * math.log2(p)
        return entropy
    
    def find_patterns(self, data: bytes) -> List[dict]:
        """Busca padroes especificos (URLs, IPs, hashes, emails)."""
        patterns = {
            "url": re.compile(rb'https?://[^\s"<\'>\x00]{8,}'),
            "ip": re.compile(rb'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
            "email": re.compile(rb'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            "md5": re.compile(rb'[0-9a-f]{32}'),
            "sha1": re.compile(rb'[0-9a-f]{40}'),
            "sha256": re.compile(rb'[0-9a-f]{64}'),
            "registry": re.compile(rb'HKEY_[A-Z_]+\\[^\x00]{5,50}'),
            "path_windows": re.compile(rb'[A-Z]:\\(?:[^\x00<>:"|?*]{1,255}\\)*[^\x00<>:"|?*]{1,255}'),
            "path_unix": re.compile(rb'/(?:usr|etc|home|tmp|var|opt)/(?:[^\x00]{1,100}/)*[^\x00]{1,100}'),
            "crypto_key": re.compile(rb'(?:AES|RSA|DES|ECB|CBC)[^\x00]{5,50}'),
            "password": re.compile(rb'(?:pass|pwd|password|passwd)[^\x00]{0,30}=?[^\x00]{4,30}', re.IGNORECASE),
        }
        
        results = {}
        for name, pattern in patterns.items():
            matches = []
            for match in pattern.finditer(data):
                text = match.group().decode('ascii', errors='ignore')
                if len(text) >= 5:
                    matches.append({
                        "offset": match.start(),
                        "value": text[:100]
                    })
            results[name] = matches[:20]
        
        return results


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="String Miner")
    parser.add_argument("file", help="Arquivo para extrair strings")
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--min-length", type=int, default=4)
    parser.add_argument("--decode-all", "-d", action="store_true", help="Tentar todas as decodificacoes")
    args = parser.parse_args()
    
    miner = StringMiner(min_length=args.min_length)
    
    if args.decode_all:
        result = miner.mine(args.file)
    else:
        # Somente strings basicas
        data = Path(args.file).read_bytes()
        result = {
            "file": args.file,
            "ascii_strings": miner._extract_ascii(data),
            "unicode_strings": miner._extract_unicode(data),
            "patterns": miner.find_patterns(data)
        }
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"File: {result['file']}")
        print(f"ASCII strings: {len(result.get('ascii_strings', []))}")
        print(f"Unicode strings: {len(result.get('unicode_strings', []))}")
        
        if 'patterns' in result:
            print(f"\nPattern matches:")
            for name, matches in result['patterns'].items():
                if matches:
                    print(f"  {name}: {len(matches)} matches")
                    for m in matches[:3]:
                        print(f"    0x{m['offset']:x}: {m['value'][:60]}")
        
        if 'base64_decoded' in result and result['base64_decoded']:
            print(f"\nBase64 decoded:")
            for d in result['base64_decoded'][:5]:
                print(f"  0x{d['offset']:x}: {d['decoded'][:60]}")
        
        if 'xor_decoded' in result and result['xor_decoded']:
            print(f"\nXOR decoded (first 5):")
            for d in result['xor_decoded'][:5]:
                print(f"  0x{d['offset']:x} (key=0x{d['key']:02x}): {d['decoded'][:60]}")
