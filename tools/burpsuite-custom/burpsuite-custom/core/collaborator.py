"""
CustomBurp - Collaborator (OAST)
Out-of-Band Security Tester - detect blind SQLi, SSRF, XXE via external callbacks
"""

import socket
import threading
import time
import uuid
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger('custom_burp')


class Collaborator:
    """
    Collaborator service para detectar vulnerabilidades out-of-band (OAST)
    Simula interacoes externas sem precisar de servidor real
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 9000):
        self.host = host
        self.port = port
        self.subdomain = f"{uuid.uuid4().hex[:8]}.collab.customburp"
        self.interactions = []
        self._server = None
        self._running = False
        self._callbacks = []
        self._lock = threading.Lock()
        
        logger.info(f"Collaborator initialized: {self.subdomain}")
    
    def start(self) -> Dict:
        """Inicia o servidor Collaborator"""
        self._running = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.host, self.port))
        self._server.listen(50)
        
        t = threading.Thread(target=self._listen, daemon=True)
        t.start()
        
        logger.info(f"Collaborator server started on {self.host}:{self.port}")
        
        return {
            'subdomain': self.subdomain,
            'host': self.host,
            'port': self.port,
            'dns_hint': f'{self.subdomain}.9000.collaborator.example.com',
            'https_hint': f'https://{self.subdomain}',
            'http_hint': f'http://{self.host}:{self.port}/callback/{self.subdomain}'
        }
    
    def stop(self):
        """Para o servidor"""
        self._running = False
        if self._server:
            try:
                self._server.close()
            except:
                pass
    
    def _listen(self):
        """Escuta conexoes entrantes"""
        while self._running:
            try:
                self._server.settimeout(1.0)
                conn, addr = self._server.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Accept error: {e}")
    
    def _handle_client(self, conn: socket.socket, addr: tuple):
        """Processa conexao do cliente (simulando DNS/HTTP callback)"""
        try:
            conn.settimeout(10)
            data = b''
            while b'\r\n\r\n' not in data:
                chunk = conn.recv(8192)
                if not chunk:
                    break
                data += chunk
            
            if data:
                text = data.decode('utf-8', errors='replace')
                self._record_interaction(addr, text)
                
                # Responder HTTP 200
                response = (
                    b'HTTP/1.1 200 OK\r\n'
                    b'Content-Type: text/plain\r\n'
                    b'X-Collaborator: CustomBurp\r\n'
                    b'Connection: close\r\n'
                    b'\r\n'
                    b'OAST interaction recorded'
                )
                conn.sendall(response)
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
    
    def _record_interaction(self, addr: tuple, data: str):
        """Registra interacao no collaborator"""
        interaction = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': time.time(),
            'source_ip': addr[0],
            'source_port': addr[1],
            'data': data,
            'type': self._detect_type(data),
            'parsed': self._parse_data(data)
        }
        
        with self._lock:
            self.interactions.append(interaction)
        
        # Notificar callbacks
        for cb in self._callbacks:
            try:
                cb(interaction)
            except:
                pass
        
        logger.info(f"Collaborator interaction from {addr[0]}: {interaction['type']}")
    
    def _detect_type(self, data: str) -> str:
        """Detecta tipo de interacao"""
        data_upper = data.upper()
        if 'GET' in data_upper:
            if 'DNS' in data_upper or 'A ' in data_upper or 'AAAA ' in data_upper:
                return 'DNS'
            return 'HTTP'
        return 'UNKNOWN'
    
    def _parse_data(self, data: str) -> Dict:
        """Parseia dados da interacao"""
        parsed = {
            'raw': data[:500],
            'method': '',
            'path': '',
            'headers': {},
            'body': ''
        }
        
        lines = data.split('\r\n')
        if lines:
            parts = lines[0].split(' ')
            if len(parts) >= 2:
                parsed['method'] = parts[0]
                parsed['path'] = parts[1]
        
        for line in lines[1:]:
            if ':' in line:
                k, v = line.split(':', 1)
                parsed['headers'][k.strip()] = v.strip()
            elif line == '':
                break
            else:
                parsed['body'] += line + '\n'
        
        return parsed
    
    def add_callback(self, callback: Callable[[Dict], None]):
        """Adiciona callback para novas interacoes"""
        self._callbacks.append(callback)
    
    def get_interactions(self, limit: int = 100, type_filter: str = None) -> List[Dict]:
        """Retorna interacoes registradas"""
        with self._lock:
            interactions = self.interactions[:]
        
        if type_filter:
            interactions = [i for i in interactions if i['type'] == type_filter]
        
        return interactions[-limit:]
    
    def clear_interactions(self):
        """Limpa interacoes"""
        with self._lock:
            self.interactions.clear()
    
    def generate_payloads(self) -> Dict:
        """Gera payloads para testes OAST"""
        payload_id = str(uuid.uuid4())[:8]
        
        return {
            'payload_id': payload_id,
            'dns': {
                'subdomain': f'{payload_id}.{self.subdomain}',
                'full_domain': f'{payload_id}.{self.subdomain}.9000.collaborator.example.com',
                'description': 'Use este dominio em queries DNS para detectar SSRF blind'
            },
            'http': {
                'url': f'http://{self.host}:{self.port}/callback/{payload_id}',
                'description': 'Use esta URL em requests HTTP para detectar SSRF/XXE blind'
            },
            'xxe': {
                'entity': f'<!ENTITY xxe SYSTEM "http://{self.host}:{self.port}/{payload_id}">',
                'description': 'Payload XXE para detectar XML injection blind'
            },
            'ssrf': {
                'url': f'http://{self.host}:{self.port}/ssrf/{payload_id}',
                'description': 'URL para testar SSRF'
            }
        }
    
    def wait_for_interaction(self, payload_id: str, timeout: float = 30.0) -> Optional[Dict]:
        """
        Espera por uma interacao com payload especifico
        
        Returns:
            Dict com detalhes da interacao ou None se timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            interactions = self.get_interactions()
            for inter in interactions:
                if payload_id in inter.get('data', ''):
                    return inter
            time.sleep(0.5)
        return None


if __name__ == '__main__':
    import sys
    
    collab = Collaborator()
    
    # Start server
    info = collab.start()
    print(f"Collaborator started!")
    print(f"  Subdomain: {info['subdomain']}")
    print(f"  DNS hint: {info['dns_hint']}")
    print(f"  HTTP hint: {info['http_hint']}")
    print()
    
    # Generate payloads
    payloads = collab.generate_payloads()
    print("Generated payloads:")
    print(f"  DNS: {payloads['dns']['full_domain']}")
    print(f"  HTTP: {payloads['http']['url']}")
    print(f"  XXE: {payloads['xxe']['entity']}")
    print()
    
    # Add callback
    def on_interaction(inter):
        print(f"[!] New interaction: {inter['type']} from {inter['source_ip']}")
        print(f"    Data: {inter['parsed']['raw'][:100]}")
    
    collab.add_callback(on_interaction)
    
    print("Waiting for interactions (30 seconds)...")
    print("Send a DNS query or HTTP request to the payload URLs to test.")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        collab.stop()
        print("\nCollaborator stopped.")
        print(f"Total interactions: {len(collab.get_interactions())}")
