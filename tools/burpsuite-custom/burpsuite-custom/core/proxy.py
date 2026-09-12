"""
CustomBurp - Proxy HTTPS Melhorado
Interceptacao completa com CA certs dinamicos
"""

import socket
import threading
import ssl
import hashlib
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional

logger = logging.getLogger('custom_burp')


class SSLCertGenerator:
    """Gerador de certificados SSL para interceptacao HTTPS"""
    
    def __init__(self, ca_cert_path: str = 'ca.crt', ca_key_path: str = 'ca.key'):
        self.ca_cert_path = ca_cert_path
        self.ca_key_path = ca_key_path
        self.ca_cert = None
        self.ca_key = None
        self._cert_cache = {}
        self._load_or_create_ca()
    
    def _load_or_create_ca(self):
        """Carrega ou cria certificado CA"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            
            if os.path.exists(self.ca_cert_path) and os.path.exists(self.ca_key_path):
                with open(self.ca_cert_path, 'rb') as f:
                    self.ca_cert = x509.load_pem_x509_certificate(f.read())
                with open(self.ca_key_path, 'rb') as f:
                    self.ca_key = serialization.load_pem_private_key(f.read(), password=None)
                logger.info(f"CA certificate loaded from {self.ca_cert_path}")
                return
            
            # Criar novo CA
            self.ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CustomBurp"),
                x509.NameAttribute(NameOID.COMMON_NAME, "CustomBurp CA"),
            ])
            
            cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(self.ca_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.utcnow())
                .not_valid_after(datetime.utcnow() + timedelta(days=3650))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(self.ca_key, hashes.SHA256()))
            
            self.ca_cert = cert
            
            with open(self.ca_key_path, 'wb') as f:
                f.write(self.ca_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(self.ca_cert_path, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            logger.info(f"CA certificate created: {self.ca_cert_path}")
            
        except ImportError:
            logger.warning("cryptography not available. HTTPS interception limited.")
    
    def get_cert_for_host(self, host: str) -> tuple:
        """Get or generate certificate for host"""
        if host in self._cert_cache:
            return self._cert_cache[host]
        
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CustomBurp"),
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
                .add_extension(x509.SubjectAlternativeName([
                    x509.DNSName(host),
                    x509.DNSName(f"*.{host}"),
                ]), critical=False)
                .sign(self.ca_key, hashes.SHA256()))
            
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            key_pem = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            self._cert_cache[host] = (cert_pem, key_pem)
            logger.info(f"Generated cert for {host}")
            
            return cert_pem, key_pem
            
        except Exception as e:
            logger.error(f"Failed to generate cert for {host}: {e}")
            return None, None


class BurpProxy:
    """Proxy HTTP/HTTPS transparente com interceptacao completa"""
    
    def __init__(self, db, host: str = '127.0.0.1', port: int = 8080, intercept: bool = True):
        self.db = db
        self.host = host
        self.port = port
        self.intercept = intercept
        self.running = False
        self.server = None
        self.handlers = []
        self.request_queue = __import__('queue').Queue()
        
        # SSL
        self.ssl_cert_gen = SSLCertGenerator()
        self._ca_cert_path = self.ssl_cert_gen.ca_cert_path
        
        logger.info(f"Proxy configured: {host}:{port}, intercept={intercept}")
    
    def add_handler(self, handler: Callable):
        self.handlers.append(handler)
    
    def start(self):
        """Inicia o proxy"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(200)
        self.running = True
        
        logger.info(f"Proxy started on {self.host}:{self.port}")
        logger.info(f"CA cert: {self._ca_cert_path}")
        logger.info(f"Configure browser proxy to {self.host}:{self.port}")
        
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
        self.running = False
        if self.server:
            try:
                self.server.close()
            except:
                pass
        logger.info("Proxy stopped")
    
    def _handle_connection(self, client_socket: socket.socket, addr: tuple):
        """Processa conexao do cliente"""
        try:
            client_socket.settimeout(30)
            
            # Ler request
            data = b''
            while b'\r\n\r\n' not in data:
                chunk = client_socket.recv(8192)
                if not chunk:
                    break
                data += chunk
                
                # Limitar tamanho do header (16KB max)
                if len(data) > 16384:
                    break
            
            if not data:
                client_socket.close()
                return
            
            # Verificar se eh CONNECT (HTTPS tunnel)
            try:
                first_line = data.split(b'\r\n')[0].decode('utf-8', errors='replace')
                if first_line.upper().startswith('CONNECT '):
                    self._handle_connect(client_socket, data)
                    return
            except:
                pass
            
            # HTTP normal
            self._handle_http(client_socket, data)
            
        except Exception as e:
            logger.error(f"Connection handler error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _handle_connect(self, client_socket: socket.socket, data: bytes):
        """Handle CONNECT request for HTTPS"""
        try:
            # Parse host:port
            lines = data.decode('utf-8', errors='replace').split('\r\n')
            connect_line = lines[0]
            parts = connect_line.split(' ')
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
            client_socket.sendall(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Gerar certificado para o host
            cert_pem, key_pem = self.ssl_cert_gen.get_cert_for_host(host)
            if not cert_pem:
                client_socket.close()
                return
            
            # Criar socket SSL
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=cert_pem, keyfile=None, keydata=key_pem)
            
            ssl_socket = ctx.wrap_socket(client_socket, server_side=True)
            ssl_socket.settimeout(30)
            
            # Tunnel HTTPS
            self._handle_https_tunnel(ssl_socket, host, port)
            
        except Exception as e:
            logger.error(f"CONNECT handler error: {e}")
            try:
                client_socket.sendall(b'HTTP/1.1 500 Internal Server Error\r\n\r\n')
            except:
                pass
    
    def _handle_https_tunnel(self, ssl_socket, host: str, port: int):
        """Tunnel HTTPS atraves do proxy"""
        try:
            # Conectar ao servidor destino
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(30)
            server_socket.connect((host, port))
            
            # TLS para o servidor
            ctx = ssl.create_default_context()
            server_ssl = ctx.wrap_socket(server_socket, server_hostname=host)
            server_ssl.settimeout(30)
            
            # Forward dados
            self._forward_data(ssl_socket, server_ssl)
            
        except Exception as e:
            logger.error(f"HTTPS tunnel error: {e}")
        finally:
            try:
                ssl_socket.close()
            except:
                pass
    
    def _handle_http(self, client_socket: socket.socket, data: bytes):
        """Processa request HTTP normal"""
        try:
            # Parse request
            request = self._parse_request(data)
            if not request:
                return
            
            # Determinar destino
            host = request.get('host', 'localhost')
            port = request.get('port', 80)
            path = request.get('path', '/')
            
            # Forward request
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(30)
            server_socket.connect((host, port))
            server_socket.sendall(data)
            
            # Ler response
            response_data = b''
            while True:
                chunk = server_socket.recv(8192)
                if not chunk:
                    break
                response_data += chunk
                if b'\r\n\r\n' in response_data:
                    header_end = response_data.find(b'\r\n\r\n')
                    headers_text = response_data[:header_end].decode('utf-8', errors='replace')
                    
                    # Checar Content-Length
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_received = len(response_data) - header_end - 4
                    if body_received >= content_length or content_length == 0:
                        break
                    
                    # Continuar lendo body
                    while body_received < content_length:
                        server_socket.settimeout(1)
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
            
            # Forward response
            client_socket.sendall(response_data)
            
            # Log
            self._log_request(request, response_data)
            
        except Exception as e:
            logger.error(f"HTTP forward error: {e}")
            error_resp = b'HTTP/1.1 502 Bad Gateway\r\nContent-Length: ' + str(len(str(e))).encode() + b'\r\n\r\n' + str(e).encode()
            client_socket.sendall(error_resp)
        finally:
            try:
                server_socket.close()
            except:
                pass
    
    def _parse_request(self, data: bytes) -> dict:
        """Parse HTTP request"""
        try:
            text = data.decode('utf-8', errors='replace')
            lines = text.split('\r\n')
            
            first_line = lines[0].split(' ')
            method = first_line[0] if len(first_line) > 0 else 'GET'
            path = first_line[1] if len(first_line) > 1 else '/'
            
            headers = {}
            for line in lines[1:]:
                if ':' in line:
                    k, v = line.split(':', 1)
                    headers[k.strip()] = v.strip()
            
            host = headers.get('Host', 'localhost')
            port = 80
            if ':' in host:
                h, p = host.rsplit(':', 1)
                try:
                    port = int(p)
                except:
                    pass
                host = h
            
            body_start = text.find('\r\n\r\n')
            body = text[body_start + 4:] if body_start > 0 else ''
            
            return {
                'method': method,
                'path': path,
                'host': host,
                'port': port,
                'headers': headers,
                'body': body,
                'raw': data
            }
        except:
            return {}
    
    def _log_request(self, request: dict, response_data: bytes):
        """Log request/response no DB"""
        from core.engine import HTTPMessage, LoggedRequest
        
        try:
            req = HTTPMessage(
                method=request['method'],
                path=request['path'],
                headers=request['headers'],
                body=request.get('body', '').encode()
            )
            
            resp_text = response_data.decode('utf-8', errors='replace')
            resp_lines = resp_text.split('\r\n')
            status_line = resp_lines[0].split(' ')
            status_code = int(status_line[1]) if len(status_line) > 1 and status_line[1].isdigit() else 0
            status_text = status_line[2] if len(status_line) > 2 else ''
            
            resp_headers = {}
            body_start = resp_text.find('\r\n\r\n')
            body = resp_text[body_start + 4:] if body_start > 0 else ''
            
            for line in resp_lines[1:]:
                if ':' in line:
                    k, v = line.split(':', 1)
                    resp_headers[k.strip()] = v.strip()
                elif line == '':
                    break
            
            resp = HTTPMessage(
                method='',
                path='',
                headers=resp_headers,
                body=body.encode(),
                status_code=status_code,
                status_text=status_text
            )
            resp.timestamp = req.timestamp + 0.001
            
            log_req = LoggedRequest(request=req, response=resp, engine='proxy')
            self.db.save_request(log_req)
            
            # Call handlers
            for handler in self.handlers:
                try:
                    handler(log_req)
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    
        except Exception as e:
            logger.error(f"Log error: {e}")
    
    def _forward_data(self, a, b):
        """Forward data between two sockets"""
        import select
        sockets = [a, b]
        while True:
            try:
                readable, _, _ = select.select(sockets, [], [], 0.1)
                if not readable:
                    break
                for sock in readable:
                    if sock is a:
                        data = b.recv(8192)
                        if not data:
                            return
                        a.sendall(data)
                    else:
                        data = a.recv(8192)
                        if not data:
                            return
                        b.sendall(data)
            except:
                break
    
    def get_ca_cert_path(self) -> str:
        return self._ca_cert_path
    
    def export_ca_cert(self) -> bytes:
        """Export CA certificate for browser installation"""
        try:
            with open(self._ca_cert_path, 'rb') as f:
                return f.read()
        except:
            return b''


if __name__ == '__main__':
    import tempfile
    from core.engine import CustomBurpDB
    
    db = CustomBurpDB(':memory:')
    proxy = BurpProxy(db, port=18080)
    proxy.start()
    print(f"Proxy running on port 18080")
    print(f"CA cert: {proxy.get_ca_cert_path()}")
    
    try:
        while proxy.running:
            time.sleep(1)
    except KeyboardInterrupt:
        proxy.stop()
        print("Proxy stopped")
