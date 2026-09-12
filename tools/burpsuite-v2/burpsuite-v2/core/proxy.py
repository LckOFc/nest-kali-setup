"""
CustomBurp v2 - Async Proxy Engine
Proxy HTTP/HTTPS real com MITM certificate generation
"""

import asyncio
import ssl
import socket
import threading
import logging
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Any, Tuple
from aiohttp import web, ClientSession, TCPConnector
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger('custom_burp.proxy')


class MITMCertificateGenerator:
    """Real MITM certificate generator using cryptography library"""
    
    def __init__(self, ca_cert_path: str = 'ca.crt', ca_key_path: str = 'ca.key'):
        self.ca_cert_path = ca_cert_path
        self.ca_key_path = ca_key_path
        self.ca_cert = None
        self.ca_key = None
        self._cert_cache: Dict[str, Tuple] = {}
        self._load_or_create_ca()
    
    def _load_or_create_ca(self):
        """Load existing CA or create new one"""
        try:
            if self.ca_cert_path and self.ca_key_path:
                if __import__('os').path.exists(self.ca_cert_path) and \
                   __import__('os').path.exists(self.ca_key_path):
                    with open(self.ca_cert_path, 'rb') as f:
                        self.ca_cert = x509.load_pem_x509_certificate(f.read())
                    with open(self.ca_key_path, 'rb') as f:
                        self.ca_key = serialization.load_pem_private_key(f.read(), password=None)
                    logger.info(f"CA certificate loaded from {self.ca_cert_path}")
                    return
            
            # Generate new CA
            self.ca_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CustomBurp v2"),
                x509.NameAttribute(NameOID.COMMON_NAME, "CustomBurp MITM CA"),
            ])
            
            now = datetime.utcnow()
            cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(self.ca_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=3650))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(self.ca_key, hashes.SHA256()))
            
            self.ca_cert = cert
            
            if self.ca_key_path:
                with open(self.ca_key_path, 'wb') as f:
                    f.write(self.ca_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
            if self.ca_cert_path:
                with open(self.ca_cert_path, 'wb') as f:
                    f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            logger.info(f"New CA certificate created: {self.ca_cert_path}")
            
        except Exception as e:
            logger.error(f"CA certificate error: {e}")
    
    def get_certificate(self, host: str) -> Optional[Tuple[bytes, bytes]]:
        """Generate or retrieve certificate for host"""
        if host in self._cert_cache:
            return self._cert_cache[host]
        
        try:
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CustomBurp v2"),
                x509.NameAttribute(NameOID.COMMON_NAME, host),
            ])
            
            now = datetime.utcnow()
            cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(self.ca_cert.subject)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=365))
                .add_extension(
                    x509.SubjectAlternativeName([
                        x509.DNSName(host),
                        x509.DNSName(f"*.{host}"),
                    ]),
                    critical=False
                )
                .add_extension(
                    x509.KeyUsage(
                        digital_signature=True,
                        key_encipherment=True,
                        key_cert_sign=False,
                        key_agreement=False,
                        content_commitment=False,
                        data_encipherment=False,
                        crl_sign=False,
                        encipher_only=False,
                        decipher_only=False
                    ),
                    critical=True
                )
                .sign(self.ca_key, hashes.SHA256()))
            
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            key_pem = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            self._cert_cache[host] = (cert_pem, key_pem)
            logger.debug(f"Generated certificate for {host}")
            
            return cert_pem, key_pem
            
        except Exception as e:
            logger.error(f"Certificate generation failed for {host}: {e}")
            return None, None
    
    def export_ca_cert(self) -> bytes:
        """Export CA certificate for browser installation"""
        if self.ca_cert:
            return self.ca_cert.public_bytes(serialization.Encoding.PEM)
        return b''


class BurpProxy:
    """Async HTTP/HTTPS Proxy with real MITM interception"""
    
    def __init__(self, db, host: str = '127.0.0.1', port: int = 8080):
        self.db = db
        self.host = host
        self.port = port
        self._running = False
        self._server = None
        self._ssl_context = None
        self._clients = set()
        
        # MITM
        self.mitm = MITMCertificateGenerator()
        self._ca_cert_path = self.mitm.ca_cert_path
        
        # Request handlers
        self._request_handlers: List[Callable] = []
        self._response_handlers: List[Callable] = []
        self._intercept_rules: List[Dict] = []
        
        # Stats
        self._stats = {
            'total_requests': 0,
            'total_bytes_in': 0,
            'total_bytes_out': 0,
            'started_at': 0,
            'errors': 0
        }
        
        logger.info(f"Proxy configured: {host}:{port}")
    
    def add_request_handler(self, handler: Callable):
        """Add request interceptor handler"""
        self._request_handlers.append(handler)
    
    def add_response_handler(self, handler: Callable):
        """Add response interceptor handler"""
        self._response_handlers.append(handler)
    
    def add_intercept_rule(self, rule: Dict):
        """Add URL intercept rule: {url_pattern, method, action}"""
        self._intercept_rules.append(rule)
    
    def remove_intercept_rule(self, index: int):
        """Remove intercept rule"""
        if 0 <= index < len(self._intercept_rules):
            self._intercept_rules.pop(index)
    
    @property
    def running(self) -> bool:
        return self._running
    
    @property
    def ca_cert_path(self) -> str:
        return self._ca_cert_path
    
    async def start(self):
        """Start the proxy server"""
        if self._running:
            return
        
        self._running = True
        self._stats['started_at'] = time.time()
        
        # Create TCP echo-style proxy handler
        # We'll use a raw socket approach for maximum compatibility
        
        loop = asyncio.get_event_loop()
        
        async def handle_client(reader, writer):
            """Handle a single client connection"""
            self._stats['total_requests'] += 1
            conn_id = hashlib.md5(f"{id(writer)}{time.time()}".encode()).hexdigest()[:8]
            
            try:
                await self._handle_connection(reader, writer, conn_id)
            except Exception as e:
                self._stats['errors'] += 1
                logger.error(f"Client handler error [{conn_id}]: {e}")
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
        
        try:
            self._server = await asyncio.start_server(
                handle_client, self.host, self.port
            )
            logger.info(f"Proxy listening on {self.host}:{self.port}")
            
            async with self._server:
                await self._server.serve_forever()
        except OSError as e:
            if e.errno == 98 or 'Address already in use' in str(e):
                logger.error(f"Port {self.port} already in use. Try: python main.py --proxy-port 8081")
            else:
                logger.error(f"Server error: {e}")
            self._running = False
    
    async def stop(self):
        """Stop the proxy server"""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        logger.info("Proxy stopped")
    
    async def _handle_connection(self, reader: asyncio.StreamReader, 
                                  writer: asyncio.StreamWriter,
                                  conn_id: str):
        """Handle full proxy connection"""
        try:
            # Read request line
            first_line = await asyncio.wait_for(reader.readline(), timeout=30)
            if not first_line:
                return
            
            first_line_str = first_line.decode('utf-8', errors='replace').strip()
            
            # Check for CONNECT method (HTTPS tunnel)
            if first_line_str.upper().startswith('CONNECT '):
                await self._handle_connect(reader, writer, conn_id, first_line_str)
                return
            
            # Regular HTTP request
            await self._handle_http_request(reader, writer, conn_id, first_line)
            
        except asyncio.TimeoutError:
            logger.debug(f"Connection timeout [{conn_id}]")
        except Exception as e:
            logger.debug(f"Connection error [{conn_id}]: {e}")
    
    async def _handle_connect(self, reader: asyncio.StreamReader,
                               writer: asyncio.StreamWriter,
                               conn_id: str, first_line: str):
        """Handle HTTPS CONNECT tunnel with MITM"""
        try:
            # Parse target host:port
            parts = first_line.split(' ')
            if len(parts) < 2:
                return
            
            target = parts[1]
            if ':' in target:
                host, port_str = target.rsplit(':', 1)
                port = int(port_str)
            else:
                host = target
                port = 443
            
            # Send 200 OK
            writer.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            await writer.drain()
            
            logger.debug(f"CONNECT tunnel to {host}:{port} [{conn_id}]")
            
            # Generate MITM certificate
            cert_pem, key_pem = self.mitm.get_certificate(host)
            if not cert_pem:
                logger.error(f"Failed to generate cert for {host} [{conn_id}]")
                return
            
            # Upgrade to SSL
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_ctx.load_cert_chain(certfile=cert_pem, keyfile=None, keydata=key_pem)
            
            ssl_writer = await asyncio.start_server(
                lambda r, w: self._handle_https_tunnel(r, w, host, port, conn_id),
                '127.0.0.1', 0
            )
            local_port = ssl_writer.sockets[0].getsockname()[1]
            ssl_writer.close()
            await ssl_writer.wait_closed()
            
            # Actually, let's do the SSL upgrade on the same connection
            ssl_transport = await writer.transport._start_tls(ssl_ctx)
            
            # Now read from the SSL-wrapped connection
            ssl_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(ssl_reader)
            await writer._start_tls(ssl_ctx)
            
            # Handle the HTTPS traffic through the tunnel
            await self._handle_https_proxy(reader, writer, host, port, conn_id)
            
        except Exception as e:
            logger.debug(f"CONNECT handler error [{conn_id}]: {e}")
    
    async def _handle_https_proxy(self, reader: asyncio.StreamReader,
                                   writer: asyncio.StreamWriter,
                                   host: str, port: int,
                                   conn_id: str):
        """Proxy HTTPS traffic through MITM"""
        try:
            # Read the HTTPS request
            request_data = b''
            while True:
                chunk = await asyncio.wait_for(reader.read(8192), timeout=30)
                if not chunk:
                    break
                request_data += chunk
                if b'\r\n\r\n' in request_data:
                    header_end = request_data.find(b'\r\n\r\n')
                    headers_text = request_data[:header_end].decode('utf-8', errors='replace')
                    
                    # Check for Content-Length to read full body
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_received = len(request_data) - header_end - 4
                    if body_received < content_length:
                        while body_received < content_length:
                            chunk = await asyncio.wait_for(reader.read(min(8192, content_length - body_received)), timeout=30)
                            if not chunk:
                                break
                            request_data += chunk
                            body_received = len(request_data) - header_end - 4
                    break
            
            if not request_data:
                return
            
            # Parse the request
            req = self._parse_request(request_data)
            if not req:
                return
            
            # Call request handlers
            for handler in self._request_handlers:
                try:
                    result = handler(req)
                    if result and isinstance(result, dict):
                        req.update(result)
                except Exception as e:
                    logger.error(f"Request handler error: {e}")
            
            # Forward to original server
            remote_reader, remote_writer = await asyncio.open_connection(host, port)
            
            # Send modified request
            remote_writer.write(req['raw'])
            await remote_writer.drain()
            
            # Read response
            resp_data = b''
            while True:
                chunk = await asyncio.wait_for(remote_reader.read(8192), timeout=30)
                if not chunk:
                    break
                resp_data += chunk
                if b'\r\n\r\n' in resp_data:
                    header_end = resp_data.find(b'\r\n\r\n')
                    headers_text = resp_data[:header_end].decode('utf-8', errors='replace')
                    
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_received = len(resp_data) - header_end - 4
                    if body_received >= content_length or content_length == 0:
                        break
                    
                    while body_received < content_length:
                        chunk = await asyncio.wait_for(
                            remote_reader.read(min(8192, content_length - body_received)),
                            timeout=30
                        )
                        if not chunk:
                            break
                        resp_data += chunk
                        body_received = len(resp_data) - header_end - 4
                    break
            
            # Call response handlers
            resp = self._parse_response(resp_data)
            for handler in self._response_handlers:
                try:
                    result = handler(req, resp)
                    if result and isinstance(result, dict):
                        resp.update(result)
                except Exception as e:
                    logger.error(f"Response handler error: {e}")
            
            # Save to database
            self._save_to_db(req, resp)
            
            # Forward response to client
            writer.write(resp_data)
            await writer.drain()
            
            self._stats['total_bytes_out'] += len(resp_data)
            
        except Exception as e:
            logger.debug(f"HTTPS proxy error [{conn_id}]: {e}")
    
    async def _handle_http_request(self, reader: asyncio.StreamReader,
                                    writer: asyncio.StreamWriter,
                                    conn_id: str, first_line: bytes):
        """Handle regular HTTP request"""
        try:
            # Read full request
            request_data = first_line
            while True:
                chunk = await asyncio.wait_for(reader.read(8192), timeout=30)
                if not chunk:
                    break
                request_data += chunk
                if b'\r\n\r\n' in request_data:
                    header_end = request_data.find(b'\r\n\r\n')
                    headers_text = request_data[:header_end].decode('utf-8', errors='replace')
                    
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_received = len(request_data) - header_end - 4
                    if body_received < content_length:
                        while body_received < content_length:
                            chunk = await asyncio.wait_for(
                                reader.read(min(8192, content_length - body_received)),
                                timeout=30
                            )
                            if not chunk:
                                break
                            request_data += chunk
                            body_received = len(request_data) - header_end - 4
                    break
            
            if not request_data:
                return
            
            # Parse request
            req = self._parse_request(request_data)
            if not req:
                return
            
            # Check intercept rules
            should_intercept = False
            for rule in self._intercept_rules:
                import re
                pattern = rule.get('url_pattern', '')
                if pattern and re.search(pattern, req.get('full_url', '')):
                    method_filter = rule.get('method', '').upper()
                    if not method_filter or method_filter == req['method'].upper():
                        should_intercept = True
                        break
            
            if should_intercept and req.get('path'):
                req['is_intercepted'] = 1
            
            # Call request handlers
            for handler in self._request_handlers:
                try:
                    result = handler(req)
                    if result and isinstance(result, dict):
                        req.update(result)
                except Exception as e:
                    logger.error(f"Request handler error: {e}")
            
            # Forward to original server
            target_host = req.get('host', 'localhost')
            target_port = req.get('port', 80)
            
            remote_reader, remote_writer = await asyncio.open_connection(
                target_host, target_port
            )
            
            # Send request
            remote_writer.write(req['raw'])
            await remote_writer.drain()
            
            # Read response
            resp_data = b''
            while True:
                chunk = await asyncio.wait_for(remote_reader.read(8192), timeout=30)
                if not chunk:
                    break
                resp_data += chunk
                if b'\r\n\r\n' in resp_data:
                    header_end = resp_data.find(b'\r\n\r\n')
                    headers_text = resp_data[:header_end].decode('utf-8', errors='replace')
                    
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_received = len(resp_data) - header_end - 4
                    if body_received >= content_length or content_length == 0:
                        break
                    
                    while body_received < content_length:
                        chunk = await asyncio.wait_for(
                            remote_reader.read(min(8192, content_length - body_received)),
                            timeout=30
                        )
                        if not chunk:
                            break
                        resp_data += chunk
                        body_received = len(resp_data) - header_end - 4
                    break
            
            # Parse response
            resp = self._parse_response(resp_data)
            
            # Call response handlers
            for handler in self._response_handlers:
                try:
                    result = handler(req, resp)
                    if result and isinstance(result, dict):
                        resp.update(result)
                except Exception as e:
                    logger.error(f"Response handler error: {e}")
            
            # Save to database
            self._save_to_db(req, resp)
            
            # Forward response to client
            writer.write(resp_data)
            await writer.drain()
            
            self._stats['total_bytes_out'] += len(resp_data)
            
        except Exception as e:
            logger.debug(f"HTTP request error [{conn_id}]: {e}")
            error_resp = (
                b'HTTP/1.1 502 Bad Gateway\r\n'
                b'Content-Type: text/html\r\n'
                b'Connection: close\r\n'
                b'\r\n'
                b'<html><body><h1>502 Bad Gateway</h1>'
                b'<p>' + str(e)[:200].encode() + b'</p></body></html>'
            )
            writer.write(error_resp)
            await writer.drain()
    
    def _parse_request(self, data: bytes) -> Dict:
        """Parse HTTP request into structured dict"""
        try:
            text = data.decode('utf-8', errors='replace')
            lines = text.split('\r\n')
            
            if not lines:
                return {}
            
            first_line_parts = lines[0].split(' ', 2)
            method = first_line_parts[0].upper() if len(first_line_parts) > 0 else 'GET'
            raw_path = first_line_parts[1] if len(first_line_parts) > 1 else '/'
            protocol = first_line_parts[2] if len(first_line_parts) > 2 else 'HTTP/1.1'
            
            # Parse headers
            headers = {}
            body_start = -1
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            # Extract body
            body = ''
            if body_start > 0:
                body = '\r\n'.join(lines[body_start:])
            
            # Determine host and full URL
            host = headers.get('Host', 'localhost')
            port = 80
            if ':' in host:
                h, p = host.rsplit(':', 1)
                try:
                    port = int(p)
                except:
                    pass
                host = h
            
            # Parse path and query
            full_url = raw_path
            path = raw_path
            query = ''
            if '?' in raw_path:
                path, query = raw_path.split('?', 1)
            
            # Check if it's an absolute URL
            if raw_path.startswith('http://') or raw_path.startswith('https://'):
                full_url = raw_path
                from urllib.parse import urlparse
                parsed = urlparse(raw_path)
                path = parsed.path or '/'
                query = parsed.query or ''
                if parsed.hostname:
                    host = parsed.hostname
                    if parsed.port:
                        port = parsed.port
            
            req_id = hashlib.md5(
                f"{method}{path}{body}{time.time()}".encode()
            ).hexdigest()[:16]
            
            return {
                'id': req_id,
                'timestamp': time.time(),
                'method': method,
                'path': path,
                'query': query,
                'full_path': raw_path,
                'full_url': full_url,
                'host': host,
                'port': port,
                'protocol': protocol,
                'headers': headers,
                'body': body,
                'raw': data,
                'engine': 'proxy',
                'tags': [],
                'notes': '',
                'folder': '',
                'is_intercepted': 0,
                'is_modified': 0,
            }
            
        except Exception as e:
            logger.error(f"Request parse error: {e}")
            return {}
    
    def _parse_response(self, data: bytes) -> Dict:
        """Parse HTTP response into structured dict"""
        try:
            text = data.decode('utf-8', errors='replace')
            lines = text.split('\r\n')
            
            if not lines:
                return {}
            
            status_line = lines[0].split(' ', 2)
            protocol = status_line[0] if len(status_line) > 0 else 'HTTP/1.1'
            status_code = int(status_line[1]) if len(status_line) > 1 and status_line[1].isdigit() else 0
            status_text = status_line[2] if len(status_line) > 2 else ''
            
            headers = {}
            body_start = -1
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            body = ''
            if body_start > 0:
                body = '\r\n'.join(lines[body_start:])
            
            return {
                'status_code': status_code,
                'status_text': status_text,
                'protocol': protocol,
                'headers': headers,
                'body': body,
                'content_type': headers.get('Content-Type', ''),
                'content_length': len(body),
                'raw': data,
                'timestamp': time.time(),
            }
            
        except Exception as e:
            logger.error(f"Response parse error: {e}")
            return {}
    
    def _save_to_db(self, req: Dict, resp: Dict):
        """Save request/response to database"""
        try:
            log_req = {
                **req,
                'response': {
                    'status_code': resp.get('status_code', 0),
                    'status_text': resp.get('status_text', ''),
                    'protocol': resp.get('protocol', 'HTTP/1.1'),
                    'headers': resp.get('headers', {}),
                    'body': resp.get('body', ''),
                    'content_type': resp.get('content_type', ''),
                    'content_length': resp.get('content_length', 0),
                    'timestamp': resp.get('timestamp', time.time()),
                    'time_ms': (resp.get('timestamp', 0) - req.get('timestamp', 0)) * 1000,
                }
            }
            self.db.save_request(log_req)
        except Exception as e:
            logger.error(f"DB save error: {e}")
    
    def get_stats(self) -> Dict:
        """Get proxy statistics"""
        return {
            **self._stats,
            'uptime_seconds': time.time() - self._stats['started_at'] if self._stats['started_at'] else 0,
            'requests_per_second': (
                self._stats['total_requests'] / (time.time() - self._stats['started_at'])
                if self._stats['started_at'] and (time.time() - self._stats['started_at']) > 0
                else 0
            )
        }
    
    def is_in_scope(self, host: str) -> bool:
        """Check if host is in target scope"""
        targets = self.db.get_targets()
        if not targets:
            return True  # No scope = scan everything
        
        for t in targets:
            if t['host'] == host and t['included']:
                return True
        return False
