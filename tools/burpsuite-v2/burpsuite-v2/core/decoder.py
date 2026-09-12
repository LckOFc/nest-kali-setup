"""
CustomBurp v2 - Decoder Engine
Comprehensive encoding/decoding operations
"""

import base64
import hashlib
import html
import json
import logging
import re
from typing import Dict, Optional
from urllib.parse import quote, unquote, urlencode

logger = logging.getLogger('custom_burp.decoder')


class Decoder:
    """Comprehensive decoder/encoder"""
    
    @staticmethod
    def url_decode(data: str) -> str:
        """Decode URL encoding"""
        try:
            return unquote(data)
        except:
            return data
    
    @staticmethod
    def url_encode(data: str, safe: str = '') -> str:
        """Encode URL encoding"""
        try:
            return quote(data, safe=safe)
        except:
            return data
    
    @staticmethod
    def base64_decode(data: str) -> str:
        """Decode Base64"""
        try:
            # Handle URL-safe base64
            data = data.replace('-', '+').replace('_', '/')
            padding = 4 - len(data) % 4
            if padding != 4:
                data += '=' * padding
            decoded = base64.b64decode(data)
            return decoded.decode('utf-8', errors='replace')
        except:
            return "Invalid Base64"
    
    @staticmethod
    def base64_encode(data: str) -> str:
        """Encode Base64"""
        try:
            return base64.b64encode(data.encode('utf-8')).decode('utf-8')
        except:
            return "Encoding error"
    
    @staticmethod
    def html_decode(data: str) -> str:
        """Decode HTML entities"""
        try:
            return html.unescape(data)
        except:
            return data
    
    @staticmethod
    def html_encode(data: str) -> str:
        """Encode HTML entities"""
        try:
            return html.escape(data, quote=True)
        except:
            return data
    
    @staticmethod
    def hex_decode(data: str) -> str:
        """Decode hex"""
        try:
            clean = data.replace(' ', '').replace('\\x', '')
            return bytes.fromhex(clean).decode('utf-8', errors='replace')
        except:
            return "Invalid hex"
    
    @staticmethod
    def hex_encode(data: str) -> str:
        """Encode hex"""
        return ' '.join(f'{ord(c):02x}' for c in data)
    
    @staticmethod
    def rot13(data: str) -> str:
        """ROT13 cipher"""
        result = []
        for c in data:
            if 'a' <= c <= 'z':
                result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
            elif 'A' <= c <= 'Z':
                result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
            else:
                result.append(c)
        return ''.join(result)
    
    @staticmethod
    def md5(data: str) -> str:
        """MD5 hash"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha1(data: str) -> str:
        """SHA1 hash"""
        return hashlib.sha1(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha256(data: str) -> str:
        """SHA256 hash"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha512(data: str) -> str:
        """SHA512 hash"""
        return hashlib.sha512(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def json_format(data: str) -> str:
        """Format JSON"""
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"
    
    @staticmethod
    def json_minify(data: str) -> str:
        """Minify JSON"""
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"
    
    @staticmethod
    def sql_format(data: str) -> str:
        """Pretty-print SQL"""
        keywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'INSERT', 'INTO', 
                    'VALUES', 'UPDATE', 'SET', 'DELETE', 'JOIN', 'ON', 'ORDER',
                    'BY', 'GROUP', 'HAVING', 'LIMIT', 'UNION', 'ALL', 'CREATE',
                    'TABLE', 'DROP', 'ALTER', 'ADD', 'INDEX', 'LEFT', 'RIGHT',
                    'INNER', 'OUTER', 'EXISTS', 'NOT', 'IN', 'BETWEEN', 'LIKE']
        
        result = []
        current = ''
        for word in re.findall(r'\b\w+\b|[^\s\w]', data):
            upper = word.upper().strip('();,')
            if upper in keywords and current.strip():
                result.append(current.strip())
                result.append(word)
                current = ''
            else:
                current += word
        if current.strip():
            result.append(current.strip())
        
        return '\n'.join(result)
    
    @staticmethod
    def jwt_decode(token: str) -> Dict:
        """Decode JWT without verification"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return {'error': 'Invalid JWT format'}
            
            decoded_parts = []
            for part in parts:
                # Add padding
                part += '=' * (4 - len(part) % 4)
                decoded = base64.urlsafe_b64decode(part).decode('utf-8', errors='replace')
                decoded_parts.append(decoded)
            
            try:
                header = json.loads(decoded_parts[0])
                payload = json.loads(decoded_parts[1])
                return {'header': header, 'payload': payload, 'signature': decoded_parts[2][:20] + '...'}
            except json.JSONDecodeError:
                return {'raw_parts': decoded_parts}
                
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def detect_encoding(data: str) -> str:
        """Detect data encoding type"""
        import re
        
        patterns = {
            'Base64': r'^[A-Za-z0-9+/]+=*$',
            'Base64URL': r'^[A-Za-z0-9_-]+=*$',
            'Hex': r'^([0-9a-fA-F]{2}\s*)+$',
            'URL': r'%[0-9a-fA-F]{2}',
            'HTML Entities': r'&[#\w]+;',
            'JWT': r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$',
            'MD5': r'^[a-f0-9]{32}$',
            'SHA1': r'^[a-f0-9]{40}$',
            'SHA256': r'^[a-f0-9]{64}$',
            'SHA512': r'^[a-f0-9]{128}$',
            'JSON': r'^[\{\[].*[\}\]]$',
        }
        
        for name, pattern in patterns.items():
            if re.match(pattern, data.strip()):
                return name
        return 'Plain Text'
    
    def transform(self, action: str, input_data: str) -> Dict:
        """Apply transformation"""
        methods = {
            'url_decode': self.url_decode,
            'url_encode': self.url_encode,
            'base64_decode': self.base64_decode,
            'base64_encode': self.base64_encode,
            'html_decode': self.html_decode,
            'html_encode': self.html_encode,
            'hex_decode': self.hex_decode,
            'hex_encode': self.hex_encode,
            'rot13': self.rot13,
            'md5': self.md5,
            'sha1': self.sha1,
            'sha256': self.sha256,
            'sha512': self.sha512,
            'json_format': self.json_format,
            'json_minify': self.json_minify,
            'sql_format': self.sql_format,
        }
        
        output = ''
        if action in methods:
            output = methods[action](input_data)
        
        encoding = self.detect_encoding(input_data) if action.endswith('_decode') else '-'
        
        return {
            'input': input_data,
            'output': output,
            'action': action,
            'encoding_detected': encoding,
            'input_length': len(input_data),
            'output_length': len(output) if output else 0,
        }
    
    def batch_transform(self, actions: list, input_data: str) -> list:
        """Apply multiple transformations in sequence"""
        results = []
        current = input_data
        for action in actions:
            result = self.transform(action, current)
            results.append(result)
            current = result.get('output', current)
        return results
