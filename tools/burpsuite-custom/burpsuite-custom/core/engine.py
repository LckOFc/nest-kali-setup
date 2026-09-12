"""
CustomBurp - Burp Suite Personal
Framework principal - Proxy HTTP/HTTPS, Scanner, Repeater, Intruder, Logger, Decoder
Autor: ratman4080 / Sombra
"""

import os
import sys
import json
import time
import hashlib
import socket
import threading
import queue
import sqlite3
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any, Callable

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('custom_burp.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('custom_burp')

# ============================================================================
# MODELOS DE DADOS
# ============================================================================

class HTTPMessage:
    """Representa uma requisição ou resposta HTTP"""
    
    def __init__(self, method: str, path: str, headers: Dict[str, str], 
                 body: bytes = b'', protocol: str = 'HTTP/1.1',
                 status_code: int = 0, status_text: str = ''):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.protocol = protocol
        self.status_code = status_code
        self.status_text = status_text
        self.timestamp = time.time()
        self.id = hashlib.md5(f"{method}{path}{body}{self.timestamp}".encode()).hexdigest()[:12]
    
    def to_raw(self) -> bytes:
        """Converte para formato raw HTTP"""
        if self.method:
            # É uma request
            raw = f"{self.method} {self.path} {self.protocol}\r\n"
            for k, v in self.headers.items():
                raw += f"{k}: {v}\r\n"
            raw += "\r\n"
            if self.body:
                raw += self.body.decode('utf-8', errors='replace')
            return raw.encode('utf-8')
        else:
            # É uma response
            raw = f"{self.protocol} {self.status_code} {self.status_text}\r\n"
            for k, v in self.headers.items():
                raw += f"{k}: {v}\r\n"
            raw += "\r\n"
            return raw.encode('utf-8')
    
    def to_dict(self) -> Dict:
        return {
            'method': self.method,
            'path': self.path,
            'headers': self.headers,
            'body': self.body.decode('utf-8', errors='replace') if self.body else '',
            'protocol': self.protocol,
            'status_code': self.status_code,
            'status_text': self.status_text,
            'timestamp': self.timestamp,
            'id': self.id
        }
    
    @classmethod
    def from_raw(cls, raw: bytes) -> 'HTTPMessage':
        """Parseia de texto raw HTTP"""
        try:
            text = raw.decode('utf-8', errors='replace')
        except:
            text = raw.decode('latin-1')
        
        lines = text.split('\r\n')
        if not lines:
            return cls('', '', {})
        
        # Parsear linha de início
        first_line = lines[0]
        parts = first_line.split(' ', 2)
        
        if len(parts) >= 3:
            # Response
            method, path, protocol = '', first_line, ''
            # Checar se é request ou response
            if parts[0].upper() in ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH', 'TRACE', 'CONNECT'):
                method, path, protocol = parts[0], parts[1], parts[2] if len(parts) > 2 else 'HTTP/1.1'
            else:
                # É response
                status_code = int(parts[1]) if parts[1].isdigit() else 0
                status_text = parts[2] if len(parts) > 2 else ''
                headers = {}
                body = b''
                in_headers = True
                for line in lines[1:]:
                    if in_headers:
                        if line == '':
                            in_headers = False
                        else:
                            if ':' in line:
                                k, v = line.split(':', 1)
                                headers[k.strip()] = v.strip()
                    else:
                        body += line.encode('utf-8') + b'\r\n'
                return cls(method, path, headers, body, protocol, status_code, status_text)
        elif len(parts) == 2:
            # Pode ser path apenas
            return cls(parts[0], parts[1], {})
        
        headers = {}
        body = b''
        in_headers = True
        for line in lines[1:]:
            if in_headers:
                if line == '':
                    in_headers = False
                else:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        headers[k.strip()] = v.strip()
            else:
                body += line.encode('utf-8') + b'\r\n'
        
        return cls(method, path, headers, body.rstrip(), protocol)


class LoggedRequest:
    """Requisição logada no histórico"""
    
    def __init__(self, request: HTTPMessage, response: HTTPMessage, engine: str = '', 
                 tags: List[str] = None, notes: str = ''):
        self.request = request
        self.response = response
        self.engine = engine
        self.tags = tags or []
        self.notes = notes
        self.time_ms = (response.timestamp - request.timestamp) * 1000 if response.timestamp > request.timestamp else 0
        self.id = request.id
        self.timestamp = request.timestamp


# ============================================================================
# BANCO DE DADOS
# ============================================================================

class CustomBurpDB:
    """SQLite para persistência de dados do Burp"""
    
    def __init__(self, db_path: str = 'custom_burp.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._conn = None
        self._init_db()
    
    def _get_conn(self):
        """Get or create persistent connection (for :memory: DBs)"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        with self.lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            c.execute('''CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                method TEXT,
                host TEXT,
                port INTEGER,
                path TEXT,
                query TEXT,
                headers TEXT,
                body TEXT,
                engine TEXT,
                tags TEXT,
                notes TEXT
            )''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS responses (
                request_id TEXT PRIMARY KEY,
                timestamp REAL,
                status_code INTEGER,
                status_text TEXT,
                headers TEXT,
                body TEXT,
                content_type TEXT,
                content_length INTEGER,
                time_ms REAL,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS issues (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                request_id TEXT,
                issue_type TEXT,
                severity TEXT,
                confidence TEXT,
                description TEXT,
                evidence TEXT,
                solution TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS intruder_results (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                request_id TEXT,
                payload_set TEXT,
                payload_value TEXT,
                status_code INTEGER,
                response_length INTEGER,
                time_ms REAL,
                result TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )''')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_requests_time ON requests(timestamp)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_requests_host ON requests(host)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_issues_type ON issues(issue_type)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity)')
            
            conn.commit()
            
        logger.info(f"Database initialized: {self.db_path}")
    
    def save_request(self, log_req: LoggedRequest) -> str:
        with self.lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            r = log_req.request
            parsed = self._parse_url(r.path)
            
            c.execute('''INSERT OR REPLACE INTO requests 
                (id, timestamp, method, host, port, path, query, headers, body, engine, tags, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (r.id, r.timestamp, r.method, parsed['host'], parsed['port'], 
                 parsed['path'], parsed['query'],
                 json.dumps(r.headers), r.body.decode('utf-8', errors='replace') if r.body else '',
                 log_req.engine, json.dumps(log_req.tags), log_req.notes))
            
            resp = log_req.response
            c.execute('''INSERT OR REPLACE INTO responses
                (request_id, timestamp, status_code, status_text, headers, body, content_type, content_length, time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (r.id, resp.timestamp, resp.status_code, resp.status_text,
                 json.dumps(resp.headers), resp.body.decode('utf-8', errors='replace') if resp.body else '',
                 resp.headers.get('Content-Type', ''),
                 len(resp.body) if resp.body else 0,
                 log_req.time_ms))
            
            conn.commit()
            
            return r.id
    
    def save_issue(self, issue_type: str, severity: str, confidence: str, 
                   request_id: str, description: str, evidence: str, solution: str):
        with self.lock:
            conn = self._get_conn()
            c = conn.cursor()
            issue_id = hashlib.md5(f"{issue_type}{request_id}{time.time()}".encode()).hexdigest()[:12]
            c.execute('''INSERT INTO issues 
                (id, timestamp, request_id, issue_type, severity, confidence, description, evidence, solution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (issue_id, time.time(), request_id, issue_type, severity, confidence, 
                 description, evidence, solution))
            conn.commit()
            
            return issue_id
    
    def save_intruder_result(self, request_id: str, payload_set: int, payload_value: str,
                             status_code: int, response_length: int, time_ms: float, result: str):
        with self.lock:
            conn = self._get_conn()
            c = conn.cursor()
            result_id = hashlib.md5(f"{request_id}{payload_set}{payload_value}{time.time()}".encode()).hexdigest()[:12]
            c.execute('''INSERT INTO intruder_results
                (id, timestamp, request_id, payload_set, payload_value, status_code, 
                 response_length, time_ms, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (result_id, time.time(), request_id, payload_set, payload_value,
                 status_code, response_length, time_ms, result))
            conn.commit()
            
            return result_id
    
    def get_requests(self, host: str = None, limit: int = 1000, offset: int = 0,
                     min_status: int = None, max_status: int = None,
                     search: str = None) -> List[Dict]:
        with self.lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = "SELECT * FROM requests WHERE 1=1"
            params = []
            
            if host:
                query += " AND host = ?"
                params.append(host)
            if search:
                query += " AND (path LIKE ? OR body LIKE ? OR headers LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            c.execute(query, params)
            rows = c.fetchall()
            
            results = []
            for row in rows:
                req = dict(row)
                # Buscar response
                c.execute("SELECT * FROM responses WHERE request_id = ?", (req['id'],))
                resp_row = c.fetchone()
                if resp_row:
                    resp = dict(resp_row)
                    req['response'] = resp
                results.append(req)
            
            
            return results
    
    def get_issues(self, severity: str = None, issue_type: str = None, limit: int = 100) -> List[Dict]:
        with self.lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = "SELECT * FROM issues WHERE 1=1"
            params = []
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            if issue_type:
                query += " AND issue_type = ?"
                params.append(issue_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            c.execute(query, params)
            rows = c.fetchall()
            
            results = []
            for row in rows:
                issue = dict(row)
                # Buscar request associado
                c.execute("SELECT * FROM requests WHERE id = ?", (issue['request_id'],))
                req_row = c.fetchone()
                if req_row:
                    issue['request'] = dict(req_row)
                results.append(issue)
            
            
            return results
    
    def get_intruder_results(self, request_id: str) -> List[Dict]:
        with self.lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM intruder_results WHERE request_id = ? ORDER BY timestamp", (request_id,))
            rows = c.fetchall()
            
            return [dict(r) for r in rows]
    
    def get_stats(self) -> Dict:
        with self.lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM requests")
            total_requests = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues")
            total_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'High'")
            high_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'Medium'")
            medium_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'Low'")
            low_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(DISTINCT host) FROM requests")
            unique_hosts = c.fetchone()[0]
            
            
            
            return {
                'total_requests': total_requests,
                'total_issues': total_issues,
                'high_issues': high_issues,
                'medium_issues': medium_issues,
                'low_issues': low_issues,
                'unique_hosts': unique_hosts
            }
    
    def clear_data(self):
        with self.lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM intruder_results")
            c.execute("DELETE FROM issues")
            c.execute("DELETE FROM responses")
            c.execute("DELETE FROM requests")
            conn.commit()
            
    
    def _parse_url(self, url: str) -> Dict:
        """Parsear URL em host, port, path, query"""
        host, port, path, query = '', 80, '/', ''
        
        # Remover scheme
        if '://' in url:
            url = url.split('://', 1)[1]
        
        # Separar host e path
        if '/' in url:
            host_part, rest = url.split('/', 1)
            path = '/' + rest
        else:
            host_part = url
            path = '/'
        
        # Separar query
        if '?' in path:
            path, query = path.split('?', 1)
        
        # Extrair host e port
        if ':' in host_part:
            host, port_str = host_part.rsplit(':', 1)
            try:
                port = int(port_str)
            except:
                pass
        else:
            host = host_part
        
        return {'host': host, 'port': port, 'path': path, 'query': query}


# ============================================================================
# PROXY HTTP
# ============================================================================

class BurpProxy:
    """Proxy HTTP/HTTPS transparente"""
    
    def __init__(self, db: CustomBurpDB, host: str = '127.0.0.1', port: int = 8080,
                 intercept: bool = True):
        self.db = db
        self.host = host
        self.port = port
        self.intercept = intercept
        self.running = False
        self.server = None
        self.handlers = []
        self.request_queue = queue.Queue()
        self.https_certs = {}
        self._ca_cert = None
        self._ca_key = None
        
        logger.info(f"Proxy configured: {host}:{port}, intercept={intercept}")
    
    def add_handler(self, handler: Callable[[LoggedRequest], None]):
        """Adiciona um handler para processar requests logados"""
        self.handlers.append(handler)
    
    def generate_ca_cert(self, cert_path: str = 'ca.crt', key_path: str = 'ca.key'):
        """Gera certificado CA para interceptação HTTPS"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            
            # Gerar chave CA
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            with open(key_path, 'wb') as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Gerar certificado CA
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CustomBurp"),
                x509.NameAttribute(NameOID.COMMON_NAME, "CustomBurp CA"),
            ])
            
            cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.utcnow())
                .not_valid_after(datetime.utcnow() + timedelta(days=3650))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(key, hashes.SHA256()))
            
            with open(cert_path, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            self._ca_cert = cert_path
            self._ca_key = key_path
            logger.info(f"CA certificate generated: {cert_path}")
            
        except ImportError:
            logger.warning("cryptography module not available. HTTPS interception disabled.")
    
    def start(self):
        """Inicia o proxy"""
        import socket
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(100)
        self.running = True
        
        logger.info(f"Proxy started on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, addr = self.server.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    logger.error(f"Accept error: {e}")
    
    def stop(self):
        """Para o proxy"""
        self.running = False
        if self.server:
            try:
                self.server.close()
            except:
                pass
        logger.info("Proxy stopped")
    
    def _handle_connection(self, client_socket: socket.socket, addr: tuple):
        """Processa conexão do cliente"""
        try:
            data = b''
            client_socket.settimeout(30)
            
            while True:
                chunk = client_socket.recv(8192)
                if not chunk:
                    break
                data += chunk
                if b'\r\n\r\n' in data:
                    # Headers completos recebidos
                    header_end = data.find(b'\r\n\r\n')
                    headers_text = data[:header_end].decode('utf-8', errors='replace')
                    
                    # Se tiver body, continuar lendo
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_received = len(data) - header_end - 4  # -4 para os \r\n\r\n
                    if body_received < content_length:
                        while body_received < content_length:
                            chunk = client_socket.recv(8192)
                            if not chunk:
                                break
                            data += chunk
                            body_received = len(data) - header_end - 4
                    break
            
            if not data:
                client_socket.close()
                return
            
            # Parsear request
            request = HTTPMessage.from_raw(data)
            
            # Determinar host e port alvo
            host = request.headers.get('Host', '')
            port = 443 if request.path.startswith('https://') else 80
            
            if ':' in host:
                h, p = host.rsplit(':', 1)
                try:
                    port = int(p)
                except:
                    pass
                host = h
            
            log_req = LoggedRequest(
                request=request,
                response=HTTPMessage('', '', {}),  # Response será preenchido
                engine='proxy'
            )
            
            # Se interceptação estiver habilitada, enviar para fila
            if self.intercept:
                self.request_queue.put(log_req)
            
            # Forward para o destino
            self._forward_request(client_socket, request, host, port)
            
            # Salvar no DB
            self.db.save_request(log_req)
            
        except Exception as e:
            logger.error(f"Connection handler error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _forward_request(self, client_socket: socket.socket, request: HTTPMessage,
                         host: str, port: int):
        """Encaminha request para o destino e retorna response"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(30)
        
        try:
            if port == 443:
                import ssl
                ctx = ssl.create_default_context()
                server_socket = ctx.wrap_socket(server_socket, server_hostname=host)
            
            server_socket.connect((host, port))
            
            # Forward request
            server_socket.sendall(request.to_raw())
            
            # Read response
            response_data = b''
            server_socket.settimeout(30)
            while True:
                chunk = server_socket.recv(8192)
                if not chunk:
                    break
                response_data += chunk
                if b'\r\n\r\n' in response_data:
                    header_end = response_data.find(b'\r\n\r\n')
                    headers_text = response_data[:header_end].decode('utf-8', errors='replace')
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    body_received = len(response_data) - header_end - 4
                    if body_received < content_length:
                        server_socket.settimeout(1)
                        while body_received < content_length:
                            try:
                                chunk = server_socket.recv(8192)
                                if not chunk:
                                    break
                                response_data += chunk
                                body_received = len(response_data) - header_end - 4
                            except socket.timeout:
                                break
                        server_socket.settimeout(30)
                    break
            
            # Forward response to client
            client_socket.sendall(response_data)
            
            # Parse e log response
            response = HTTPMessage.from_raw(response_data)
            
            # Atualizar logged request
            import queue
            try:
                log_req = self.request_queue.get_nowait()
                log_req.response = response
                self.db.save_request(log_req)
                
                # Call handlers
                for handler in self.handlers:
                    try:
                        handler(log_req)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
            except queue.Empty:
                pass
                
        except Exception as e:
            logger.error(f"Forward error to {host}:{port}: {e}")
            # Enviar erro para o cliente
            error_resp = HTTPMessage('', '', {
                'Content-Type': 'text/html',
                'Connection': 'close'
            }, b'<html><body><h1>Proxy Error</h1><p>Connection to ' + host.encode() + b' failed: ' + str(e).encode() + b'</p></body></html>')
            client_socket.sendall(error_resp.to_raw())
        finally:
            try:
                server_socket.close()
            except:
                pass
    
    def get_pending_requests(self, timeout: float = 1.0) -> List[LoggedRequest]:
        """Retorna requests pendentes na fila de interceptação"""
        requests = []
        try:
            while True:
                req = self.request_queue.get_nowait()
                requests.append(req)
        except queue.Empty:
            pass
        return requests


# ============================================================================
# SCANNER DE VULNERABILIDADES
# ============================================================================

class VulnScanner:
    """Scanner de vulnerabilidades"""
    
    # Padrões de detecção
    VULN_PATTERNS = {
        'XSS_Reflected': {
            'patterns': [
                r'<script.*?>', r'javascript:', r'on\w+\s*=',
                r'<iframe', r'<img.*src\s*=', r'alert\s*\('
            ],
            'severity': 'High',
            'confidence': 'Medium',
            'description': 'Cross-Site Scripting (XSS) Refletido detectado na resposta',
            'solution': 'Implementar input sanitization e output encoding (HTML entities)'
        },
        'SQLi': {
            'patterns': [
                r"SQL syntax.*MySQL", r"Warning.*mysql_", r"valid MySQL result",
                r"Microsoft SQL Server", r"ODBC Driver", r"SQLite3::",
                r"unclosed quotation mark", r"SQL command not properly ended",
                r"SQL injection.*detected", r"UNION.*SELECT",
                r"OR 1=1", r"AND 1=1", r"\' OR \'=\'",
                r"sys\.objects", r"INFORMATION_SCHEMA"
            ],
            'severity': 'Critical',
            'confidence': 'High',
            'description': 'SQL Injection detectado na resposta',
            'solution': 'Utilizar parameterized queries / prepared statements. Nunca concatene inputs diretamente no SQL.'
        },
        'SSRF': {
            'patterns': [
                r'file:///etc/passwd', r'file:///c:/windows',
                r'docker internal', r'169.254.169.254',
                r'internal metadata'
            ],
            'severity': 'High',
            'confidence': 'Medium',
            'description': 'Server-Side Request Forgery (SSRF) - acesso a recursos internos detectado',
            'solution': 'Validar e restringir URLs de saída. Bloquear schemes internos e RFC1918.'
        },
        'Path_Traversal': {
            'patterns': [
                r'\.\./\.\./', r'%2e%2e%2f', r'%252e%252e%252f',
                r'etc/passwd', r'etc/shadow', r'win\.ini',
                r'boot\.ini'
            ],
            'severity': 'High',
            'confidence': 'Medium',
            'description': 'Path Traversal detectado',
            'solution': 'Validar inputs de caminho. Usar allowlist de diretórios. Normalizar paths antes de usar.'
        },
        'Hardcoded_Creds': {
            'patterns': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'private[_-]?key',
                r'AKIA[0-9A-Z]{16}',  # AWS keys
                r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'
            ],
            'severity': 'High',
            'confidence': 'High',
            'description': 'Credenciais hardcoded detectadas na resposta',
            'solution': 'Remover credenciais do código. Usar variáveis de ambiente ou secret managers.'
        },
        'Info_Disclosure': {
            'patterns': [
                r'X-Powered-By', r'X-AspNet-Version',
                r'Server:.*Apache/\d', r'Server:.*nginx/\d',
                r'phpinfo\(\)', r'/debug', r'/trace',
                r'backtrace', r'traceback',
                r'File.*Line.*in.*\w+.*\(\)'
            ],
            'severity': 'Low',
            'confidence': 'High',
            'description': 'Informações de tecnologia/versão expostas',
            'solution': 'Remover headers sensíveis. Desabilitar debug em produção.'
        },
        'Insecure_Cookie': {
            'headers': ['Set-Cookie'],
            'patterns': [
                r'(?<!Security-)(?:Set-Cookie:\s*[^;]*(?<!;\s*Secure)(?<!;\s*HttpOnly))'
            ],
            'severity': 'Medium',
            'confidence': 'Medium',
            'description': 'Cookie sem flags Secure/HttpOnly detectado',
            'solution': 'Adicionar flags Secure e HttpOnly em todos os cookies sensíveis.'
        },
        'CORS_Misconfig': {
            'headers': ['Access-Control-Allow-Origin'],
            'patterns': [
                r'Access-Control-Allow-Origin:\s*\*',
                r'Access-Control-Allow-Credentials:\s*true'
            ],
            'severity': 'Medium',
            'confidence': 'High',
            'description': 'CORS mal configurado - wildcard origin com credentials',
            'solution': 'Restringir origins permitidas. Não usar * com credentials.'
        },
        'Missing_Security_Headers': {
            'missing_headers': [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'Strict-Transport-Security',
                'Content-Security-Policy',
                'X-XSS-Protection'
            ],
            'severity': 'Low',
            'confidence': 'High',
            'description': 'Headers de segurança ausentes',
            'solution': 'Adicionar headers de segurança: X-Content-Type-Options, X-Frame-Options, HSTS, CSP'
        },
        'Command_Injection': {
            'patterns': [
                r';\s*(ls|cat|id|whoami|uname|curl|wget)\b',
                r'\|\s*(ls|cat|id|whoami)\b',
                r'\$\(', r'`[^`]+`',
                r'&&\s*(ls|cat|id)\b',
                r'command not found', r'/bin/(sh|bash|cat)',
                r'exit code \d+'
            ],
            'severity': 'Critical',
            'confidence': 'Medium',
            'description': 'Command Injection potencialmente detectado',
            'solution': 'Nunca passe inputs do usuário para system calls. Usar allowlists de comandos.'
        }
    }
    
    def __init__(self, db: CustomBurpDB):
        self.db = db
        self.scan_results = []
        self._lock = threading.Lock()
    
    def scan_request(self, log_req: LoggedRequest) -> List[Dict]:
        """Escanea uma única request/response"""
        issues = []
        resp = log_req.response
        
        for vuln_type, config in self.VULN_PATTERNS.items():
            matched = False
            evidence = ''
            
            # Checar padrões no body
            body_text = resp.body.decode('utf-8', errors='replace') if resp.body else ''
            for pattern in config.get('patterns', []):
                try:
                    if __import__('re').search(pattern, body_text, re.IGNORECASE):
                        matched = True
                        evidence = pattern
                        break
                except:
                    pass
            
            # Checar padrões nos headers
            headers_text = json.dumps(resp.headers) if resp.headers else ''
            if not matched:
                for pattern in config.get('patterns', []):
                    try:
                        if __import__('re').search(pattern, headers_text, re.IGNORECASE):
                            matched = True
                            evidence = pattern
                            break
                    except:
                        pass
            
            # Verificar headers ausentes
            if not matched and 'missing_headers' in config:
                missing = [h for h in config['missing_headers'] 
                          if h.lower() not in (k.lower() for k in resp.headers)]
                if missing:
                    matched = True
                    evidence = ', '.join(missing)
            
            if matched:
                issue = {
                    'type': vuln_type,
                    'severity': config['severity'],
                    'confidence': config.get('confidence', 'Medium'),
                    'description': config['description'],
                    'evidence': evidence,
                    'solution': config.get('solution', ''),
                    'request_id': log_req.request.id,
                    'timestamp': time.time()
                }
                issues.append(issue)
                
                # Salvar no DB
                self.db.save_issue(
                    issue_type=vuln_type,
                    severity=config['severity'],
                    confidence=config.get('confidence', 'Medium'),
                    request_id=log_req.request.id,
                    description=config['description'],
                    evidence=evidence,
                    solution=config.get('solution', '')
                )
        
        return issues
    
    def scan_host(self, host: str, max_requests: int = 100) -> List[Dict]:
        """Escanea todas as requests de um host"""
        requests = self.db.get_requests(host=host, limit=max_requests)
        all_issues = []
        
        for req_data in requests:
            # Reconstruir LoggedRequest a partir dos dados do DB
            import json as json_mod
            req = HTTPMessage(
                method=req_data['method'],
                path=req_data['path'],
                headers=json_mod.loads(req_data['headers']) if req_data['headers'] else {},
                body=req_data['body'].encode() if req_data['body'] else b''
            )
            
            resp_data = req_data.get('response', {})
            resp = HTTPMessage(
                method='',
                path='',
                headers=json_mod.loads(resp_data.get('headers', '{}')) if resp_data.get('headers') else {},
                body=resp_data.get('body', '').encode() if resp_data.get('body') else b'',
                status_code=resp_data.get('status_code', 0),
                status_text=resp_data.get('status_text', '')
            )
            
            log_req = LoggedRequest(request=req, response=resp, engine='scanner')
            issues = self.scan_request(log_req)
            all_issues.extend(issues)
        
        return all_issues
    
    def get_summary(self) -> Dict:
        """Retorna resumo dos scans"""
        issues = self.db.get_issues()
        summary = defaultdict(int)
        for issue in issues:
            summary[issue['severity']] += 1
        return dict(summary)


# ============================================================================
# INTRUDER (Payload Attack)
# ============================================================================

class Intruder:
    """Ferramenta de ataque com payloads - similar ao Burp Intruder"""
    
    def __init__(self, db: CustomBurpDB):
        self.db = db
        self.results = []
        self._lock = threading.Lock()
    
    def attack(self, request: HTTPMessage, payload_sets: List[List[str]],
               position_indicators: List[Tuple[int, int]], 
               thread_count: int = 10,
               callback: Callable = None) -> List[Dict]:
        """
        Executa ataque de intruder
        
        Args:
            request: Request base
            payload_sets: Lista de conjuntos de payloads (max 4 positions)
            position_indicators: Lista de (start, end) indicando onde inserir payloads
            thread_count: Número de threads
            callback: Função chamada a cada resultado
        """
        results = []
        total_combinations = 1
        for ps in payload_sets:
            total_combinations *= len(ps)
        
        logger.info(f"Intruder starting: {total_combinations} combinations, {thread_count} threads")
        
        def worker(payload_indices):
            local_results = []
            for idx in payload_indices:
                # Montar payload
                payload_values = []
                for set_idx, pos_indices in enumerate(payload_sets):
                    # Encontrar qual posição corresponde a este payload set
                    pass
                
                # Construir request com payload
                modified_request = self._apply_payloads(request, payload_sets, position_indicators, idx)
                
                # Enviar request
                resp = self._send_request(modified_request)
                
                result = {
                    'index': idx,
                    'payload': self._get_payload_string(payload_sets, position_indicators, idx),
                    'status_code': resp.status_code,
                    'response_length': len(resp.body) if resp.body else 0,
                    'time_ms': resp.timestamp * 1000,
                    'response_headers': resp.headers,
                    'response_body': resp.body.decode('utf-8', errors='replace')[:500] if resp.body else ''
                }
                
                # Salvar no DB
                self.db.save_intruder_result(
                    request_id=request.id,
                    payload_set=0,
                    payload_value=result['payload'],
                    status_code=resp.status_code,
                    response_length=result['response_length'],
                    time_ms=result['time_ms'],
                    result=json.dumps(result)
                )
                
                local_results.append(result)
                
                if callback:
                    callback(result)
            
            return local_results
        
        # Gerar índices de payload
        payload_indices = list(range(total_combinations))
        
        # Dividir entre threads
        chunks = [[] for _ in range(thread_count)]
        for i, idx in enumerate(payload_indices):
            chunks[i % thread_count].append(idx)
        
        # Executar em threads
        threads = []
        for chunk in chunks:
            if chunk:
                t = threading.Thread(target=worker, args=(chunk,))
                t.start()
                threads.append(t)
        
        for t in threads:
            t.join()
        
        logger.info(f"Intruder completed: {len(results)} results")
        return results
    
    def _apply_payloads(self, request: HTTPMessage, payload_sets: List[List[str]],
                        position_indicators: List[Tuple[int, int]], combo_idx: int) -> HTTPMessage:
        """Aplica payloads na request"""
        # Decompor índice em índices por set
        idx = combo_idx
        payload_values = []
        for ps in payload_sets:
            payload_values.append(ps[idx % len(ps)])
            idx //= len(ps)
        
        # Aplicar no body
        body = request.body.decode('utf-8', errors='replace') if request.body else ''
        
        # Aplicar nos positions indicados
        for i, (start, end) in enumerate(position_indicators):
            if i < len(payload_values):
                body = body[:start] + payload_values[i] + body[end:]
        
        # Reconstruir request
        new_request = HTTPMessage(
            method=request.method,
            path=request.path,
            headers=dict(request.headers),
            body=body.encode('utf-8'),
            protocol=request.protocol
        )
        
        # Atualizar Content-Length se necessário
        if new_request.body:
            new_request.headers['Content-Length'] = str(len(new_request.body))
        
        return new_request
    
    def _get_payload_string(self, payload_sets: List[List[str]], 
                            position_indicators: List[Tuple[int, int]],
                            combo_idx: int) -> str:
        """Retorna string de payload para display"""
        idx = combo_idx
        values = []
        for ps in payload_sets:
            values.append(ps[idx % len(ps)])
            idx //= len(ps)
        return ' | '.join(values)
    
    def _send_request(self, request: HTTPMessage) -> HTTPMessage:
        """Envia request e retorna response"""
        import urllib.request
        import urllib.error
        
        try:
            url = f"http://{request.headers.get('Host', 'localhost')}{request.path}"
            
            req = urllib.request.Request(
                url,
                data=request.body,
                method=request.method
            )
            
            for k, v in request.headers.items():
                if k.lower() not in ('host', 'content-length'):
                    req.add_header(k, v)
            
            start = time.time()
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read()
                elapsed = (time.time() - start) * 1000
                
                return HTTPMessage(
                    method='',
                    path='',
                    headers=dict(resp.headers),
                    body=body,
                    status_code=resp.status,
                    status_text=resp.status
                )
        except urllib.error.HTTPError as e:
            body = e.read()
            return HTTPMessage(
                method='',
                path='',
                headers=dict(e.headers),
                body=body,
                status_code=e.code,
                status_text=str(e.code)
            )
        except Exception as e:
            return HTTPMessage(
                method='',
                path='',
                headers={},
                body=f"Error: {e}".encode(),
                status_code=0,
                status_text=str(e)
            )


# ============================================================================
# DECODER
# ============================================================================

class Decoder:
    """Decoder/Encoder para dados"""
    
    @staticmethod
    def url_decode(data: str) -> str:
        """Decode URL encoding"""
        from urllib.parse import unquote
        return unquote(data)
    
    @staticmethod
    def url_encode(data: str) -> str:
        """Encode URL encoding"""
        from urllib.parse import quote
        return quote(data, safe='')
    
    @staticmethod
    def base64_decode(data: str) -> str:
        """Decode Base64"""
        import base64
        try:
            decoded = base64.b64decode(data)
            return decoded.decode('utf-8', errors='replace')
        except:
            return f"Erro: dados inválidos em Base64"
    
    @staticmethod
    def base64_encode(data: str) -> str:
        """Encode Base64"""
        import base64
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def html_decode(data: str) -> str:
        """Decode HTML entities"""
        from html import unescape
        return unescape(data)
    
    @staticmethod
    def html_encode(data: str) -> str:
        """Encode HTML entities"""
        from html import escape
        return escape(data)
    
    @staticmethod
    def md5(data: str) -> str:
        """Calcular MD5"""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha1(data: str) -> str:
        """Calcular SHA1"""
        return hashlib.sha1(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha256(data: str) -> str:
        """Calcular SHA256"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hex_encode(data: str) -> str:
        """Converter para hex"""
        return data.encode('utf-8').hex()
    
    @staticmethod
    def hex_decode(data: str) -> str:
        """Converter de hex"""
        try:
            return bytes.fromhex(data).decode('utf-8', errors='replace')
        except:
            return "Erro: dados hex inválidos"
    
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
    def json_format(data: str) -> str:
        """Formatar JSON"""
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            return f"JSON inválido: {e}"
    
    @staticmethod
    def json_minify(data: str) -> str:
        """Minificar JSON"""
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
        except json.JSONDecodeError as e:
            return f"JSON inválido: {e}"
    
    @staticmethod
    def sql_pretty(data: str) -> str:
        """Formatar SQL simples"""
        keywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'INSERT', 'INTO', 
                    'VALUES', 'UPDATE', 'SET', 'DELETE', 'JOIN', 'ON', 'ORDER',
                    'BY', 'GROUP', 'HAVING', 'LIMIT', 'UNION', 'ALL', 'CREATE',
                    'TABLE', 'DROP', 'ALTER', 'ADD', 'INDEX']
        
        result = []
        current = ''
        for word in data.split():
            upper = word.upper().strip('();,')
            if upper in keywords:
                if current:
                    result.append(current)
                result.append(word)
                current = ''
            else:
                current += word + ' '
        if current:
            result.append(current.strip())
        
        return '\n'.join(result)
    
    @staticmethod
    def detect_encoding(data: str) -> str:
        """Detectar tipo de codificação"""
        import base64
        patterns = {
            'Base64': r'^[A-Za-z0-9+/]+=*$',
            'Hex': r'^[0-9a-fA-F]+$',
            'URL': r'%[0-9a-fA-F]{2}',
            'HTML Entities': r'&[#\w]+;',
            'JSON': r'^[\{\[].*[\}\]]$',
            'MD5': r'^[a-f0-9]{32}$',
            'SHA1': r'^[a-f0-9]{40}$',
            'SHA256': r'^[a-f0-9]{64}$',
        }
        
        for name, pattern in patterns.items():
            import re
            if re.match(pattern, data.strip()):
                return name
        return 'Plain Text'
    
    def transform(self, action: str, input_data: str) -> Dict:
        """Transforma dado pela ação especificada"""
        methods = {
            'url_decode': self.url_decode,
            'url_encode': self.url_encode,
            'base64_decode': self.base64_decode,
            'base64_encode': self.base64_encode,
            'html_decode': self.html_decode,
            'html_encode': self.html_encode,
            'md5': self.md5,
            'sha1': self.sha1,
            'sha256': self.sha256,
            'hex_encode': self.hex_encode,
            'hex_decode': self.hex_decode,
            'rot13': self.rot13,
            'json_format': self.json_format,
            'json_minify': self.json_minify,
        }
        
        output = ''
        if action in methods:
            output = methods[action](input_data)
        
        encoding = self.detect_encoding(input_data) if action.endswith('_decode') else '-'
        
        return {'output': output, 'encoding': encoding}


# ============================================================================
# MAIN APP
# ============================================================================

class CustomBurp:
    """Classe principal que orquestra todos os módulos"""
    
    def __init__(self, db_path: str = 'custom_burp.db', proxy_port: int = 8080):
        self.db = CustomBurpDB(db_path)
        self.proxy = BurpProxy(self.db, port=proxy_port)
        self.scanner = VulnScanner(self.db)
        self.intruder = Intruder(self.db)
        self.decoder = Decoder()
        self.running = False
        
        # Registrar scanner como handler do proxy
        self.proxy.add_handler(self.scanner.scan_request)
        
        # Novos modulos
        from core.logger import BurpLogger
        from core.comparer import Comparer
        from core.sequencer import Sequencer
        from core.target import Target
        from core.session_handler import SessionManager
        from core.match_replace import MatchReplace
        from core.payload_processor import PayloadProcessor
        from core.collaborator import Collaborator
        from core.alerts import Alerts
        from core.organizer import Organizer
        from core.project import ProjectManager
        from core.extender import Extender
        from core.browser import BurpBrowser
        from core.api import BurpAPI
        
        self.logger = BurpLogger(db_path)
        self.comparer = Comparer()
        self.sequencer = Sequencer()
        self.target = Target()
        self.session_mgr = SessionManager()
        self.match_replace = MatchReplace()
        self.payload_processor = PayloadProcessor()
        self.collaborator = Collaborator()
        self.alerts = Alerts()
        self.organizer = Organizer()
        self.project_mgr = ProjectManager()
        self.extender = Extender()
        self.browser = BurpBrowser()
        self.api = BurpAPI(self)
        
        logger.info("CustomBurp initialized")
    
    def start_proxy(self):
        """Inicia o proxy em thread separada"""
        self.running = True
        t = threading.Thread(target=self.proxy.start, daemon=True)
        t.start()
        logger.info(f"Proxy started on port {self.proxy.port}")
        return t
    
    def stop_proxy(self):
        """Para o proxy"""
        self.proxy.stop()
        self.running = False
    
    def get_status(self) -> Dict:
        """Retorna status do sistema"""
        stats = self.db.get_stats()
        return {
            'proxy_running': self.proxy.running,
            'proxy_port': self.proxy.port,
            'stats': stats,
            'modules': {
                'collaborator_running': self.collaborator._running,
                'session_count': len(self.session_mgr.list_sessions()),
                'target_hosts': len(self.target.get_hosts()),
                'logger_entries': stats['total_requests']
            }
        }


if __name__ == '__main__':
    app = CustomBurp()
    app.start_proxy()
    print(f"CustomBurp iniciado. Proxy em http://127.0.0.1:{app.proxy.port}")
    print("Aguardando conexões...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop_proxy()
        print("CustomBurp parado.")
