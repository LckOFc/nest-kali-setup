"""
CustomBurp Skill v2 — Engine CLI-only para opencode
Sem UI web, uso via linha de comando e integra ag
"""

import sys
import os
import json
import time
import hashlib
import sqlite3
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Config
base_dir = Path(__file__).parent
log_dir = base_dir / 'log'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'burp_skill.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('burp_skill')


# =========================================================================
# Database
# =========================================================================

class BurpDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = str(base_dir / 'custom_burp.db')
        self.db_path = db_path
        self._conn = None
        self._lock = threading.Lock()
        self._init_db()
    
    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        with self._lock:
            c = self._get_conn().cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY, timestamp REAL, method TEXT, host TEXT,
                port INTEGER DEFAULT 80, path TEXT, query TEXT,
                headers TEXT, body TEXT, engine TEXT, tags TEXT, notes TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS responses (
                request_id TEXT PRIMARY KEY, timestamp REAL, status_code INTEGER,
                status_text TEXT, headers TEXT, body TEXT, content_type TEXT,
                content_length INTEGER, time_ms REAL,
                FOREIGN KEY(request_id) REFERENCES requests(id) ON DELETE CASCADE
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS issues (
                id TEXT PRIMARY KEY, timestamp REAL, request_id TEXT,
                issue_type TEXT, severity TEXT, confidence TEXT,
                description TEXT, evidence TEXT, solution TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS intruder_results (
                id TEXT PRIMARY KEY, timestamp REAL, request_id TEXT,
                payload_set INTEGER, payload_value TEXT, status_code INTEGER,
                response_length INTEGER, time_ms REAL, result TEXT
            )''')
            c.execute('CREATE INDEX IF NOT EXISTS idx_req_time ON requests(timestamp)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_req_host ON requests(host)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_issue_sev ON issues(severity)')
            self._get_conn().commit()
    
    def save_request(self, data):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            req_id = data.get('id', hashlib.md5(f"{time.time()}{data.get('path','')}".encode()).hexdigest()[:16])
            c.execute('''INSERT OR REPLACE INTO requests 
                (id, timestamp, method, host, port, path, query, headers, body, engine, tags, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                (req_id, data.get('timestamp', time.time()), data['method'], data['host'],
                 data.get('port', 80), data['path'], data.get('query',''),
                 json.dumps(data.get('headers',{})), data.get('body',''),
                 data.get('engine','unknown'), json.dumps(data.get('tags',[])), data.get('notes','')))
            
            resp = data.get('response', {})
            if resp:
                c.execute('''INSERT OR REPLACE INTO responses
                    (request_id, timestamp, status_code, status_text, headers, body, content_type, content_length, time_ms)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                    (req_id, resp.get('timestamp', time.time()), resp.get('status_code',0),
                     resp.get('status_text',''), json.dumps(resp.get('headers',{})),
                     resp.get('body',''), resp.get('content_type',''),
                     len(resp.get('body','')), resp.get('time_ms',0)))
            conn.commit()
            return req_id
    
    def get_requests(self, host=None, limit=100, search=None):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            q = "SELECT * FROM requests WHERE 1=1"
            p = []
            if host:
                q += " AND host = ?"
                p.append(host)
            if search:
                q += " AND (path LIKE ? OR body LIKE ?)"
                p.extend([f'%{search}%', f'%{search}%'])
            q += " ORDER BY timestamp DESC LIMIT ?"
            p.append(limit)
            c.execute(q, p)
            results = []
            for row in c.fetchall():
                r = dict(row)
                c.execute("SELECT * FROM responses WHERE request_id = ?", (r['id'],))
                resp = c.fetchone()
                r['response'] = dict(resp) if resp else {}
                try: r['headers'] = json.loads(r['headers'])
                except: pass
                results.append(r)
            return results
    
    def get_request(self, req_id):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
            req = c.fetchone()
            if not req:
                return None
            r = dict(req)
            c.execute("SELECT * FROM responses WHERE request_id = ?", (req_id,))
            resp = c.fetchone()
            r['response'] = dict(resp) if resp else {}
            try: r['headers'] = json.loads(r['headers'])
            except: pass
            return r
    
    def save_issue(self, data):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            issue_id = hashlib.md5(f"{data.get('type','')}{time.time()}".encode()).hexdigest()[:16]
            c.execute('''INSERT INTO issues 
                (id, timestamp, request_id, issue_type, severity, confidence, description, evidence, solution)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (issue_id, time.time(), data.get('request_id',''),
                 data['type'], data['severity'], data.get('confidence','Medium'),
                 data.get('description',''), data.get('evidence',''), data.get('solution','')))
            conn.commit()
            return issue_id
    
    def get_issues(self, severity=None, limit=100):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            q = "SELECT * FROM issues WHERE 1=1"
            p = []
            if severity:
                q += " AND severity = ?"
                p.append(severity)
            q += " ORDER BY timestamp DESC LIMIT ?"
            p.append(limit)
            c.execute(q, p)
            return [dict(r) for r in c.fetchall()]
    
    def clear_issues(self):
        with self._lock:
            self._get_conn().cursor().execute("DELETE FROM issues")
            self._get_conn().commit()
    
    def save_intruder_result(self, data):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            rid = hashlib.md5(f"{time.time()}{data.get('payload_value','')}".encode()).hexdigest()[:16]
            c.execute('''INSERT INTO intruder_results
                (id, timestamp, request_id, payload_set, payload_value, status_code, response_length, time_ms, result)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (rid, time.time(), data.get('request_id',''),
                 data.get('payload_set',0), data.get('payload_value',''),
                 data.get('status_code',0), data.get('response_length',0),
                 data.get('time_ms',0), json.dumps(data.get('result',{}))))
            conn.commit()
            return rid
    
    def get_stats(self):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM requests")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT host) FROM requests")
            hosts = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'Critical'")
            critical = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'High'")
            high = c.fetchone()[0]
            return {'total_requests': total, 'unique_hosts': hosts, 'critical_issues': critical, 'high_issues': high, 'total_issues': critical + high}
    
    def export_requests(self, limit=10000):
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("""SELECT r.*, resp.status_code, resp.headers as resp_h, resp.body as resp_b
                         FROM requests r LEFT JOIN responses resp ON r.id = resp.request_id
                         ORDER BY r.timestamp DESC LIMIT ?""", (limit,))
            results = []
            for row in c.fetchall():
                r = dict(row)
                try: r['headers'] = json.loads(r['headers'])
                except: pass
                if r.get('resp_h'):
                    try: r['response'] = {'headers': json.loads(r['resp_h']), 'body': r['resp_b'], 'status_code': r['status_code']}
                    except: pass
                results.append(r)
            return results


# =========================================================================
# Decoder
# =========================================================================

class Decoder:
    @staticmethod
    def url_decode(d):
        from urllib.parse import unquote
        return unquote(d)
    
    @staticmethod
    def url_encode(d, safe=''):
        from urllib.parse import quote
        return quote(d, safe=safe)
    
    @staticmethod
    def base64_decode(d):
        import base64
        try:
            d = d.replace('-','+').replace('_','/')
            pad = 4 - len(d) % 4
            if pad != 4: d += '=' * pad
            return base64.b64decode(d).decode('utf-8', errors='replace')
        except:
            return "Invalid Base64"
    
    @staticmethod
    def base64_encode(d):
        import base64
        return base64.b64encode(d.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def md5(d):
        import hashlib
        return hashlib.md5(d.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha256(d):
        import hashlib
        return hashlib.sha256(d.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hex_encode(d):
        return ' '.join(f'{ord(c):02x}' for c in d)
    
    @staticmethod
    def hex_decode(d):
        try:
            return bytes.fromhex(d.replace(' ','')).decode('utf-8', errors='replace')
        except:
            return "Invalid hex"
    
    @staticmethod
    def rot13(d):
        r = []
        for c in d:
            if 'a' <= c <= 'z': r.append(chr((ord(c)-ord('a')+13)%26 + ord('a')))
            elif 'A' <= c <= 'Z': r.append(chr((ord(c)-ord('A')+13)%26 + ord('A')))
            else: r.append(c)
        return ''.join(r)
    
    @staticmethod
    def json_format(d):
        try:
            return json.dumps(json.loads(d), indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"
    
    @staticmethod
    def jwt_decode(token):
        import base64
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return {'error': 'Invalid JWT'}
            decoded = []
            for p in parts:
                p += '=' * (4 - len(p) % 4)
                decoded.append(base64.urlsafe_b64decode(p).decode('utf-8', errors='replace'))
            try:
                return {'header': json.loads(decoded[0]), 'payload': json.loads(decoded[1]), 'sig': decoded[2][:20]+'...'}
            except:
                return {'raw': decoded}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def detect(data):
        import re
        patterns = {
            'Base64': r'^[A-Za-z0-9+/]+=*$',
            'Hex': r'^([0-9a-fA-F]{2}\s*)+$',
            'JWT': r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$',
            'MD5': r'^[a-f0-9]{32}$',
            'SHA1': r'^[a-f0-9]{40}$',
            'SHA256': r'^[a-f0-9]{64}$',
        }
        for name, pat in patterns.items():
            if re.match(pat, data.strip()):
                return name
        return 'Plain Text'
    
    def transform(self, action, data):
        methods = {
            'url_decode': self.url_decode, 'url_encode': self.url_encode,
            'base64_decode': self.base64_decode, 'base64_encode': self.base64_encode,
            'md5': self.md5, 'sha256': self.sha256,
            'hex_encode': self.hex_encode, 'hex_decode': self.hex_decode,
            'rot13': self.rot13, 'json_format': self.json_format, 'jwt_decode': self.jwt_decode,
        }
        if action not in methods:
            return {'error': f'Unknown action: {action}', 'available': list(methods.keys())}
        result = methods[action](data)
        if isinstance(result, dict):
            return {**result, 'action': action, 'input_length': len(data)}
        return {
            'input': data, 'output': result, 'action': action,
            'encoding_detected': self.detect(data),
            'input_length': len(data), 'output_length': len(result) if result else 0
        }


# =========================================================================
# Scanner
# =========================================================================

class VulnScanner:
    PATTERNS = {
        'XSS': {'patterns': [r'<script', r'javascript:', r'on\w+\s*=', r'alert\s*\('], 'severity': 'High'},
        'SQLi': {'patterns': [r'SQL syntax', r'mysql_fetch', r'unclosed quotation', r"OR 1=1", r'UNION.*SELECT'], 'severity': 'Critical'},
        'SSRF': {'patterns': [r'file:///etc/passwd', r'169.254.169.254', r'docker internal'], 'severity': 'High'},
        'Path_Traversal': {'patterns': [r'\.\./\.\./', r'etc/passwd', r'etc/shadow', r'win\.ini'], 'severity': 'High'},
        'Command_Injection': {'patterns': [r';\s*(ls|cat|id|whoami)\b', r'\|\s*(ls|cat|id)\b', r'\$\(', r'/bin/(sh|bash)'], 'severity': 'Critical'},
        'Info_Disclosure': {'patterns': [r'X-Powered-By', r'phpinfo\(\)', r'/debug', r'traceback'], 'severity': 'Low'},
        'CORS': {'patterns': [r'Access-Control-Allow-Origin:\s*\*', r'Access-Control-Allow-Credentials:\s*true'], 'severity': 'Medium'},
        'Missing_Headers': {'missing': ['X-Content-Type-Options', 'X-Frame-Options', 'Strict-Transport-Security', 'Content-Security-Policy'], 'severity': 'Medium'},
    }
    
    def __init__(self, db):
        self.db = db
    
    def scan_response(self, request_data):
        issues = []
        resp = request_data.get('response', {})
        body = resp.get('body', '')
        headers = resp.get('headers', {})
        headers_json = json.dumps(headers)
        
        for vtype, cfg in self.PATTERNS.items():
            matched = False
            evidence = ''
            
            # Check patterns in body/headers
            for pat in cfg.get('patterns', []):
                try:
                    import re
                    if re.search(pat, body, re.IGNORECASE) or re.search(pat, headers_json, re.IGNORECASE):
                        matched = True
                        evidence = pat
                        break
                except:
                    pass
            
            # Check missing headers
            if not matched and 'missing' in cfg:
                missing = [h for h in cfg['missing'] if h.lower() not in (k.lower() for k in headers)]
                if missing:
                    matched = True
                    evidence = ', '.join(missing)
            
            if matched:
                issue = {
                    'type': vtype,
                    'severity': cfg['severity'],
                    'confidence': 'High',
                    'description': f'{vtype} detected',
                    'evidence': evidence,
                    'solution': f'Remediate {vtype} vulnerability',
                    'request_id': request_data.get('id', '')
                }
                issues.append(issue)
                self.db.save_issue(issue)
        
        return issues
    
    async def scan_host(self, host, paths=None):
        import asyncio
        from urllib.parse import urlparse
        
        # Get stored requests
        stored = self.db.get_requests(host=host, limit=50)
        all_issues = []
        
        for req in stored:
            issues = self.scan_response(req)
            all_issues.extend(issues)
        
        # Active scanning on common paths
        common_paths = ['/', '/login', '/admin', '/api/', '/index.html', '/robots.txt',
                       '/.env', '/wp-admin', '/phpmyadmin', '/graphql', '/console']
        paths_to_scan = (paths or common_paths)[:10]
        
        for path in paths_to_scan:
            try:
                url = f"http://{host}{path}"
                result = await self._send_request('GET', url, host, 80)
                if result and 'response' in result:
                    req_data = {
                        'id': hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:16],
                        'timestamp': time.time(),
                        'method': 'GET',
                        'host': host,
                        'path': path,
                        'headers': {'User-Agent': 'CustomBurp-Skill/2.0'},
                        'body': '',
                        'engine': 'scanner',
                        'response': result['response']
                    }
                    issues = self.scan_response(req_data)
                    all_issues.extend(issues)
                    self.db.save_request(req_data)
            except:
                pass
        
        return {
            'host': host,
            'stored_requests_scanned': len(stored),
            'paths_tested': len(paths_to_scan),
            'issues_found': len(all_issues),
            'issues': all_issues
        }
    
    async def _send_request(self, method, url, host, port):
        """Send HTTP request and return response"""
        import ssl
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ssl.create_default_context() if port == 443 else None),
            timeout=15
        )
        
        raw = f"{method} / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: CustomBurp/2.0\r\nConnection: close\r\n\r\n"
        writer.write(raw.encode())
        await writer.drain()
        
        data = b''
        while True:
            chunk = await asyncio.wait_for(reader.read(8192), timeout=15)
            if not chunk:
                break
            data += chunk
            if b'\r\n\r\n' in data:
                break
        
        writer.close()
        await writer.wait_closed()
        
        text = data.decode('utf-8', errors='replace')
        lines = text.split('\r\n')
        status_parts = lines[0].split(' ', 2)
        status_code = int(status_parts[1]) if len(status_parts) > 1 and status_parts[1].isdigit() else 0
        
        resp_headers = {}
        body_start = -1
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                body_start = i + 1
                break
            if ':' in line:
                k, v = line.split(':', 1)
                resp_headers[k.strip()] = v.strip()
        
        body = ''
        if body_start > 0:
            body = '\r\n'.join(lines[body_start:])
        
        return {
            'response': {
                'status_code': status_code,
                'status_text': status_parts[2] if len(status_parts) > 2 else '',
                'headers': resp_headers,
                'body': body,
                'content_type': resp_headers.get('Content-Type', ''),
                'content_length': len(body),
                'time_ms': 0
            }
        }
    
    def get_summary(self):
        issues = self.db.get_issues()
        summary = {'by_severity': {}, 'by_type': {}}
        for i in issues:
            sev = i.get('severity', 'Unknown')
            typ = i.get('issue_type', 'unknown')
            summary['by_severity'][sev] = summary['by_severity'].get(sev, 0) + 1
            summary['by_type'][typ] = summary['by_type'].get(typ, 0) + 1
        return summary


# =========================================================================
# Main Skill Engine
# =========================================================================

class BurpSkill:
    def __init__(self, db_path=None):
        self.db = BurpDB(db_path)
        self.scanner = VulnScanner(self.db)
        self.decoder = Decoder()
        self._proxy_running = False
        self._proxy_port = 8080
    
    # ---- Status ----
    def status(self):
        stats = self.db.get_stats()
        scanner_summary = self.scanner.get_summary()
        return {
            'system': 'CustomBurp Skill v2',
            'proxy_running': self._proxy_running,
            'proxy_port': self._proxy_port,
            'database': self.db.db_path,
            'stats': stats,
            'scanner': scanner_summary,
        }
    
    # ---- Proxy ----
    def proxy_start(self, port=8080):
        if self._proxy_running:
            return {'status': 'already_running', 'port': self._proxy_port}
        
        import threading
        self._proxy_port = port
        self._proxy_running = True
        
        # Start proxy in background
        def run_proxy():
            import asyncio
            async def _run():
                try:
                    server = await asyncio.start_server(
                        lambda r, w: self._handle_proxy_conn(r, w),
                        '127.0.0.1', port
                    )
                    async with server:
                        await server.serve_forever()
                except Exception as e:
                    logger.error(f"Proxy error: {e}")
                    self._proxy_running = False
            
            asyncio.run(_run())
        
        t = threading.Thread(target=run_proxy, daemon=True)
        t.start()
        
        return {'status': 'started', 'port': port, 'message': f'Proxy rodando em 127.0.0.1:{port}'}
    
    def proxy_stop(self):
        self._proxy_running = False
        return {'status': 'stopped'}
    
    def proxy_status(self):
        return {'running': self._proxy_running, 'port': self._proxy_port}
    
    def proxy_generate_ca(self):
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from datetime import datetime, timedelta
            
            cert_path = base_dir / 'ca.crt'
            key_path = base_dir / 'ca.key'
            
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CustomBurp Skill"),
                x509.NameAttribute(NameOID.COMMON_NAME, "CustomBurp MITM CA"),
            ])
            now = datetime.utcnow()
            cert = (x509.CertificateBuilder()
                .subject_name(subject).issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now).not_valid_after(now + timedelta(days=3650))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(key, hashes.SHA256()))
            
            with open(key_path, 'wb') as f:
                f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
            with open(cert_path, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            return {
                'status': 'generated',
                'cert_path': str(cert_path),
                'key_path': str(key_path),
                'message': f'CA cert gerado em {cert_path}. Instale no navegador para HTTPS.'
            }
        except ImportError:
            return {'status': 'error', 'message': 'cryptography module not installed. pip install cryptography'}
    
    async def _handle_proxy_conn(self, reader, writer):
        """Handle proxy connection"""
        try:
            data = b''
            while True:
                chunk = await asyncio.wait_for(reader.read(8192), timeout=30)
                if not chunk:
                    break
                data += chunk
                if b'\r\n\r\n' in data:
                    header_end = data.find(b'\r\n\r\n')
                    headers_text = data[:header_end].decode('utf-8', errors='replace')
                    cl = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            cl = int(line.split(':')[1].strip())
                            break
                    body_rec = len(data) - header_end - 4
                    if body_rec < cl:
                        while body_rec < cl:
                            chunk = await asyncio.wait_for(reader.read(min(8192, cl - body_rec)), timeout=30)
                            if not chunk:
                                break
                            data += chunk
                            body_rec = len(data) - header_end - 4
                    break
            
            if not data:
                writer.close()
                return
            
            # Parse
            text = data.decode('utf-8', errors='replace')
            lines = text.split('\r\n')
            first = lines[0].split(' ')
            method = first[0].upper()
            raw_path = first[1]
            
            headers = {}
            body_start = -1
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    k, v = line.split(':', 1)
                    headers[k.strip()] = v.strip()
            
            body = ''
            if body_start > 0:
                body = '\r\n'.join(lines[body_start:])
            
            host = headers.get('Host', 'localhost')
            port = 80
            if ':' in host:
                h, p = host.rsplit(':', 1)
                try: port = int(p)
                except: pass
                host = h
            
            path = raw_path
            query = ''
            if '?' in raw_path:
                path, query = raw_path.split('?', 1)
            
            req_id = hashlib.md5(f"{method}{path}{body}{time.time()}".encode()).hexdigest()[:16]
            
            # Forward
            try:
                r, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=30)
                w.write(data)
                await w.drain()
                
                resp_data = b''
                while True:
                    chunk = await asyncio.wait_for(r.read(8192), timeout=30)
                    if not chunk:
                        break
                    resp_data += chunk
                    if b'\r\n\r\n' in resp_data:
                        he = resp_data.find(b'\r\n\r\n')
                        ht = resp_data[:he].decode('utf-8', errors='replace')
                        cl = 0
                        for line in ht.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                cl = int(line.split(':')[1].strip())
                                break
                        br = len(resp_data) - he - 4
                        if br >= cl or cl == 0:
                            break
                        while br < cl:
                            chunk = await asyncio.wait_for(r.read(min(8192, cl - br)), timeout=30)
                            if not chunk:
                                break
                            resp_data += chunk
                            br = len(resp_data) - he - 4
                        break
                
                # Parse response
                rt = resp_data.decode('utf-8', errors='replace')
                rl = rt.split('\r\n')
                sp = rl[0].split(' ', 2)
                sc = int(sp[1]) if len(sp) > 1 and sp[1].isdigit() else 0
                st = sp[2] if len(sp) > 2 else ''
                
                rh = {}
                rbs = -1
                for i, line in enumerate(rl[1:], 1):
                    if line == '':
                        rbs = i + 1
                        break
                    if ':' in line:
                        k, v = line.split(':', 1)
                        rh[k.strip()] = v.strip()
                
                rb = ''
                if rbs > 0:
                    rb = '\r\n'.join(rl[rbs:])
                
                request_data = {
                    'id': req_id,
                    'timestamp': time.time(),
                    'method': method,
                    'host': host,
                    'port': port,
                    'path': path,
                    'query': query,
                    'headers': headers,
                    'body': body,
                    'engine': 'proxy',
                    'tags': [],
                    'notes': '',
                    'response': {
                        'status_code': sc,
                        'status_text': st,
                        'headers': rh,
                        'body': rb,
                        'content_type': rh.get('Content-Type', ''),
                        'content_length': len(rb),
                        'timestamp': time.time(),
                        'time_ms': (time.time() - time.time()) * 1000,
                    }
                }
                
                self.db.save_request(request_data)
                writer.write(resp_data)
                await writer.drain()
                w.close()
                
            except Exception as e:
                logger.error(f"Proxy forward error: {e}")
                err_resp = b'HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/html\r\n\r\n<html><body><h1>502</h1></body></html>'
                writer.write(err_resp)
                await writer.drain()
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logger.debug(f"Proxy conn error: {e}")
            try:
                writer.close()
            except:
                pass
    
    # ---- Scanner ----
    async def scan(self, host, paths=None):
        return await self.scanner.scan_host(host, paths=paths)
    
    def issues(self, severity=None):
        return self.db.get_issues(severity=severity)
    
    def issues_clear(self):
        self.db.clear_issues()
        return {'status': 'cleared'}
    
    # ---- Repeater ----
    async def repeater_send(self, method, url, headers=None, body=''):
        import ssl
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        host = parsed.hostname or 'localhost'
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        path = parsed.path or '/'
        query = parsed.query or ''
        
        raw = f"{method} {path}{'?' + query if query else ''} HTTP/1.1\r\n"
        raw += f"Host: {host}\r\n"
        raw += "User-Agent: CustomBurp-Skill/2.0\r\n"
        raw += "Accept: */*\r\n"
        raw += "Connection: close\r\n"
        
        req_headers = headers or {}
        for k, v in req_headers.items():
            raw += f"{k}: {v}\r\n"
        
        if body:
            raw += f"Content-Length: {len(body.encode('utf-8'))}\r\n"
        raw += "\r\n"
        raw += body
        
        start = time.time()
        try:
            ctx = ssl.create_default_context() if port == 443 else None
            if ctx:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            
            r, w = await asyncio.wait_for(asyncio.open_connection(host, port, ssl=ctx), timeout=30)
            w.write(raw.encode())
            await w.drain()
            
            data = b''
            while True:
                chunk = await asyncio.wait_for(r.read(65536), timeout=30)
                if not chunk:
                    break
                data += chunk
                if b'\r\n\r\n' in data:
                    he = data.find(b'\r\n\r\n')
                    ht = data[:he].decode('utf-8', errors='replace')
                    cl = 0
                    for line in ht.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            cl = int(line.split(':')[1].strip())
                            break
                    br = len(data) - he - 4
                    if br >= cl or cl == 0:
                        break
                    while br < cl:
                        chunk = await asyncio.wait_for(r.read(min(65536, cl - br)), timeout=30)
                        if not chunk:
                            break
                        data += chunk
                        br = len(data) - he - 4
                    break
            
            elapsed = (time.time() - start) * 1000
            w.close()
            await w.wait_closed()
            
            # Parse
            rt = data.decode('utf-8', errors='replace')
            rl = rt.split('\r\n')
            sp = rl[0].split(' ', 2)
            sc = int(sp[1]) if len(sp) > 1 and sp[1].isdigit() else 0
            st = sp[2] if len(sp) > 2 else ''
            
            rh = {}
            rbs = -1
            for i, line in enumerate(rl[1:], 1):
                if line == '':
                    rbs = i + 1
                    break
                if ':' in line:
                    k, v = line.split(':', 1)
                    rh[k.strip()] = v.strip()
            
            rb = ''
            if rbs > 0:
                rb = '\r\n'.join(rl[rbs:])
            
            result = {
                'id': hashlib.md5(f"{method}{path}{body}{time.time()}".encode()).hexdigest()[:16],
                'request': {'method': method, 'url': url, 'headers': req_headers, 'body': body},
                'response': {'status_code': sc, 'status_text': st, 'headers': rh, 'body': rb,
                            'content_type': rh.get('Content-Type',''), 'content_length': len(rb), 'time_ms': elapsed},
                'time_ms': elapsed,
                'timestamp': time.time(),
            }
            
            self.db.save_request({
                **result['request'],
                'id': result['id'], 'timestamp': result['timestamp'],
                'host': host, 'port': port, 'path': path, 'query': query,
                'engine': 'repeater',
                'response': result['response'],
            })
            
            return result
            
        except asyncio.TimeoutError:
            return {'error': f'Timeout connecting to {host}:{port}', 'time_ms': 30000}
        except Exception as e:
            return {'error': str(e), 'time_ms': (time.time() - start) * 1000}
    
    # ---- Intruder ----
    async def intruder_attack(self, request_data, payloads, mode='sniper'):
        results = []
        for idx, payload in enumerate(payloads):
            modified = request_data.copy()
            body = modified.get('body', '')
            
            if '!@' in body:
                parts = body.split('!@')
                new_body = ''
                for i, part in enumerate(parts):
                    new_body += part
                    if i % 2 == 1:
                        new_body += payload
                body = new_body
            else:
                body = body.replace('[PAYLOAD]', payload)
            
            modified['body'] = body
            if body:
                modified['headers'] = dict(modified.get('headers', {}))
                modified['headers']['Content-Length'] = str(len(body.encode('utf-8')))
            
            result = await self.repeater_send(
                method=modified.get('method', 'GET'),
                url=modified.get('url', ''),
                headers=modified.get('headers', {}),
                body=body
            )
            
            resp = result.get('response', {})
            intruder_result = {
                'index': idx,
                'payload': payload,
                'status_code': resp.get('status_code', 0),
                'response_length': resp.get('content_length', 0),
                'time_ms': result.get('time_ms', 0),
            }
            
            self.db.save_intruder_result({
                'request_id': request_data.get('id', ''),
                'payload_set': 0,
                'payload_value': payload,
                'status_code': intruder_result['status_code'],
                'response_length': intruder_result['response_length'],
                'time_ms': intruder_result['time_ms'],
                'result': intruder_result,
            })
            results.append(intruder_result)
        
        return {
            'mode': mode,
            'total': len(results),
            'results': results,
        }
    
    # ---- Logger ----
    def logger_list(self, host=None, limit=100, search=None):
        return self.db.get_requests(host=host, limit=limit, search=search)
    
    def logger_get(self, req_id):
        return self.db.get_request(req_id)
    
    def logger_clear(self):
        with self.db._lock:
            conn = self.db._get_conn()
            conn.cursor().execute("DELETE FROM responses")
            conn.cursor().execute("DELETE FROM requests")
            conn.commit()
        return {'status': 'cleared'}
    
    def logger_export(self, limit=10000):
        return json.dumps(self.db.export_requests(limit=limit), indent=2, default=str)
    
    # ---- Decoder ----
    def decoder_transform(self, action, data):
        return self.decoder.transform(action, data)
    
    def decoder_operations(self):
        return self.decoder.transform.__globals__  # Not needed, just list
    # ---- Target ----
    def target_list(self):
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT DISTINCT host FROM requests ORDER BY host")
            return [r[0] for r in c.fetchall()]
    
    def target_add(self, host, port=0):
        # Just a log entry
        return {'status': 'added', 'host': host}
    
    # ---- Help ----
    def help(self):
        return {
            'commands': {
                'status': 'Show system status',
                'proxy_start [port]': 'Start HTTP proxy (default: 8080)',
                'proxy_stop': 'Stop proxy',
                'proxy_status': 'Proxy status',
                'proxy_ca': 'Generate CA certificate',
                'logger [host] [limit]': 'List logged requests',
                'logger_get <id>': 'Get single request',
                'logger_clear': 'Clear all logs',
                'logger_export': 'Export as JSON',
                'scan <host> [paths...]': 'Run vulnerability scan',
                'issues [severity]': 'List detected issues',
                'issues_clear': 'Clear issues',
                'repeater <method> <url> [headers_json] [body]': 'Send HTTP request',
                'intruder <url> <payloads_csv> [mode]': 'Start intruder attack',
                'decode <op> <data>': 'Decode/encode data',
                'operations': 'List decoder operations',
                'target <host> [port]': 'Add target',
                'targets': 'List targets',
                'help': 'Show this help',
            },
            'decoder_ops': [
                'url_decode', 'url_encode', 'base64_decode', 'base64_encode',
                'md5', 'sha256', 'hex_encode', 'hex_decode', 'rot13',
                'json_format', 'jwt_decode',
            ],
            'scan_types': [
                'XSS', 'SQLi', 'SSRF', 'Path_Traversal',
                'Command_Injection', 'Info_Disclosure', 'CORS', 'Missing_Headers'
            ],
            'intruder_modes': ['sniper', 'battering_ram', 'pitchfork', 'cluster_bomb'],
        }


# =========================================================================
# Async wrapper for CLI
# =========================================================================

def run_async(coro):
    """Run async function from sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =========================================================================
# CLI Entry
# =========================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='CustomBurp Skill v2 — CLI para opencode')
    parser.add_argument('command', nargs='?', help='Comando')
    parser.add_argument('args', nargs='*', help='Args')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--db', help='DB path')
    
    args = parser.parse_args()
    engine = BurpSkill(db_path=args.db)
    
    cmd = args.command or 'help'
    
    # Helper to parse JSON args
    def parse_json_arg(idx):
        if len(args.args) > idx:
            try:
                return json.loads(args.args[idx])
            except:
                return args.args[idx]
        return None
    
    try:
        if cmd == 'status' or cmd == 'stats':
            result = engine.status()
        elif cmd == 'proxy_start':
            port = int(args.args[0]) if args.args and args.args[0].isdigit() else 8080
            result = engine.proxy_start(port)
        elif cmd == 'proxy_stop':
            result = engine.proxy_stop()
        elif cmd == 'proxy_status':
            result = engine.proxy_status()
        elif cmd == 'proxy_ca':
            result = engine.proxy_generate_ca()
        elif cmd == 'logger':
            host = args.args[0] if len(args.args) > 0 else None
            limit = int(args.args[1]) if len(args.args) > 1 and args.args[1].isdigit() else 100
            result = engine.logger_list(host=host, limit=limit)
        elif cmd == 'logger_get':
            result = engine.logger_get(args.args[0]) if args.args else {}
        elif cmd == 'logger_clear':
            result = engine.logger_clear()
        elif cmd == 'logger_export':
            result = {'data': engine.logger_export()}
        elif cmd == 'scan':
            if not args.args:
                result = {'error': 'Host required: /burp scan <host> [paths...]'}
            else:
                host = args.args[0]
                paths = args.args[1:] if len(args.args) > 1 else None
                result = run_async(engine.scan(host, paths=paths))
        elif cmd == 'issues':
            severity = args.args[0] if args.args and args.args[0] in ['Critical','High','Medium','Low'] else None
            result = engine.issues(severity=severity)
        elif cmd == 'issues_clear':
            result = engine.issues_clear()
        elif cmd == 'repeater':
            if len(args.args) < 2:
                result = {'error': 'Usage: /burp repeater <method> <url> [headers_json] [body]'}
            else:
                method = args.args[0].upper()
                url = args.args[1]
                headers = {}
                body = ''
                if len(args.args) > 2:
                    try:
                        headers = json.loads(args.args[2])
                        if not isinstance(headers, dict):
                            headers = {}
                    except:
                        headers = {'X-Custom': args.args[2]}
                if len(args.args) > 3:
                    body = args.args[3]
                result = run_async(engine.repeater_send(method, url, headers=headers, body=body))
        elif cmd == 'intruder':
            if len(args.args) < 2:
                result = {'error': 'Usage: /burp intruder <url> <payloads_csv> [mode]'}
            else:
                url = args.args[0]
                payloads = args.args[1].split(',')
                mode = args.args[2] if len(args.args) > 2 else 'sniper'
                request_data = {'method': 'GET', 'url': url, 'headers': {}, 'body': ''}
                result = run_async(engine.intruder_attack(request_data, payloads, mode=mode))
        elif cmd == 'decode':
            if len(args.args) < 2:
                result = {'error': 'Usage: /burp decode <operation> <data>'}
            else:
                result = engine.decoder_transform(args.args[0], args.args[1])
        elif cmd == 'operations':
            result = {'operations': [
                'url_decode', 'url_encode', 'base64_decode', 'base64_encode',
                'md5', 'sha256', 'hex_encode', 'hex_decode', 'rot13',
                'json_format', 'jwt_decode'
            ]}
        elif cmd == 'target':
            if args.args:
                result = engine.target_add(args.args[0], int(args.args[1]) if len(args.args) > 1 and args.args[1].isdigit() else 0)
            else:
                result = {'error': 'Usage: /burp target <host> [port]'}
        elif cmd == 'targets':
            result = {'hosts': engine.target_list()}
        elif cmd == 'help':
            result = engine.help()
        else:
            result = {'error': f'Unknown command: {cmd}', 'help': 'Run /burp help'}
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if isinstance(result, dict):
                print(json.dumps(result, indent=2, default=str))
            elif isinstance(result, list):
                for item in result[:20]:
                    print(json.dumps(item, default=str))
                if len(result) > 20:
                    print(f"... ({len(result) - 20} more)")
            else:
                print(result)
    
    except Exception as e:
        print(json.dumps({'error': str(e)}, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
