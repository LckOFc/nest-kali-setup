"""
CustomBurp - Payload Processor
Processamento avançado de payloads para Intruder
"""

import re
import hashlib
import base64
import urllib.parse
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass


@dataclass
class PayloadRule:
    """Regra de processamento de payload"""
    name: str
    pattern: str
    replacement: str = ''
    applied_to: str = 'both'  # 'before', 'after', 'both'
    
    def compile(self):
        return re.compile(self.pattern, re.IGNORECASE)


class PayloadProcessor:
    """Processador de payloads para Intruder"""
    
    def __init__(self):
        self.rules: List[PayloadRule] = []
        self._builtins = {
            'url_encode': self._url_encode,
            'url_decode': self._url_decode,
            'base64_encode': self._base64_encode,
            'base64_decode': self._base64_decode,
            'html_encode': self._html_encode,
            'html_decode': self._html_decode,
            'md5': self._md5,
            'sha1': self._sha1,
            'sha256': self._sha256,
            'hex_encode': self._hex_encode,
            'hex_decode': self._hex_decode,
            'rot13': self._rot13,
            'upper': lambda x: x.upper(),
            'lower': lambda x: x.lower(),
            'capitalize': lambda x: x.capitalize(),
            'reverse': lambda x: x[::-1],
            'repeat': self._repeat,
            'concat': self._concat,
            'replace': self._replace,
            'urlencode': self._url_encode,
            'urldecode': self._url_decode,
            'b64encode': self._base64_encode,
            'b64decode': self._base64_decode,
        }
    
    def add_rule(self, name: str, pattern: str, replacement: str = '', applied_to: str = 'both'):
        """Adiciona regra de processamento"""
        self.rules.append(PayloadRule(name, pattern, replacement, applied_to))
    
    def process(self, payload: str, operation: str = None, **kwargs) -> str:
        """
        Processa um payload
        
        Args:
            payload: Payload original
            operation: Operacao builtin (url_encode, base64_encode, etc.)
            **kwargs: Argumentos para operacoes com parametros
        """
        result = payload
        
        # Aplicar rules customizadas
        for rule in self.rules:
            if rule.applied_to in ('before', 'both'):
                result = self._apply_regex(result, rule.pattern, rule.replacement)
        
        # Aplicar operacao builtin
        if operation and operation in self._builtins:
            fn = self._builtins[operation]
            if kwargs:
                result = fn(result, **kwargs)
            else:
                result = fn(result)
        
        # Aplicar rules customizadas (after)
        for rule in self.rules:
            if rule.applied_to in ('after', 'both'):
                result = self._apply_regex(result, rule.pattern, rule.replacement)
        
        return result
    
    def process_batch(self, payloads: List[str], operation: str = None, **kwargs) -> List[str]:
        """Processa batch de payloads"""
        return [self.process(p, operation, **kwargs) for p in payloads]
    
    def _apply_regex(self, text: str, pattern: str, replacement: str) -> str:
        """Aplica regex substitution"""
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            return compiled.sub(replacement, text)
        except:
            return text
    
    # Built-in operations
    def _url_encode(self, text: str) -> str:
        return urllib.parse.quote(text, safe='')
    
    def _url_decode(self, text: str) -> str:
        return urllib.parse.unquote(text)
    
    def _base64_encode(self, text: str) -> str:
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    def _base64_decode(self, text: str) -> str:
        try:
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        except:
            return text
    
    def _html_encode(self, text: str) -> str:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    
    def _html_decode(self, text: str) -> str:
        return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    
    def _md5(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _sha1(self, text: str) -> str:
        return hashlib.sha1(text.encode('utf-8')).hexdigest()
    
    def _sha256(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _hex_encode(self, text: str) -> str:
        return text.encode('utf-8').hex()
    
    def _hex_decode(self, text: str) -> str:
        try:
            return bytes.fromhex(text).decode('utf-8')
        except:
            return text
    
    def _rot13(self, text: str) -> str:
        result = []
        for c in text:
            if 'a' <= c <= 'z':
                result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= c <= 'Z':
                result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(c)
        return ''.join(result)
    
    def _repeat(self, text: str, count: int = 1) -> str:
        return text * int(count)
    
    def _concat(self, text: str, suffix: str = '') -> str:
        return text + suffix
    
    def _replace(self, text: str, old: str = '', new: str = '') -> str:
        return text.replace(old, new)
    
    def list_operations(self) -> List[str]:
        """Lista operacoes disponiveis"""
        return list(self._builtins.keys())


if __name__ == '__main__':
    pp = PayloadProcessor()
    
    # Testar operacoes
    tests = [
        ('test string', 'url_encode', None),
        ('%7B%22test%22%3A1%7D', 'url_decode', None),
        ('hello world', 'base64_encode', None),
        ('aGVsbG8gd29ybGQ=', 'base64_decode', None),
        ('test', 'md5', None),
        ('hello', 'rot13', None),
        ('test', 'upper', None),
        ('TEST', 'lower', None),
    ]
    
    for payload, op, kwargs in tests:
        result = pp.process(payload, op)
        print(f"{op}: {payload} -> {result}")
    
    # Testar regra customizada
    pp.add_rule('strip_dots', r'\.{2,}', '.')
    result = pp.process('a...b...c', 'strip_dots')
    print(f"\nCustom rule: a...b...c -> {result}")
    
    print("\nPayloadProcessor OK!")
