#!/usr/bin/env python3
"""
Fiddler Engine - HTTP Inspector estilo Fiddler
===============================================
Recria funcionalidades de inspeção HTTP/HTTPS.
"""

import os
import sys
import json
import time
import hashlib
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import http.client
import urllib.request
import urllib.parse


@dataclass
class HttpSession:
    """Sessão HTTP."""
    id: str
    timestamp: datetime
    method: str
    url: str
    host: str
    path: str
    status_code: int = 0
    response_time_ms: float = 0.0
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: str = ""
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: str = ""
    is_https: bool = False
    client_ip: str = ""
    server_ip: str = ""
    
    # Analysis
    has_jwt: bool = False
    jwt_token: str = ""
    has_cookies: bool = False
    cookies: Dict[str, str] = field(default_factory=dict)
    content_type: str = ""
    body_size: int = 0
    is_binary: bool = False


@dataclass
class CaptureRule:
    """Regra de captura."""
    name: str
    filter: str
    action: str  # capture, ignore, modify
    headers: Dict[str, str] = field(default_factory=dict)


class FiddlerEngine:
    """
    Engine de inspeção HTTP/HTTPS estilo Fiddler.
    
    Funcionalidades:
    - Captura de tráfego HTTP/HTTPS
    - Visualização de sessões
    - Decodificação de responses
    - Modificação de requests/responses
    - Filtragem avançada
    - Exportação de sessões
    - Análise de JWT
    - Análise de cookies
    """
    
    def __init__(self, toolkit=None):
        self.toolkit = toolkit
        self.sessions: List[HttpSession] = []
        self.capturing = False
        self.capture_thread = None
        self.capture_host = 'localhost'
        self.capture_port = 8888
        self.rules: List[CaptureRule] = []
        self.session_counter = 0
        self._stop_event = threading.Event()
        
        # Statistics
        self.stats = {
            'total_sessions': 0,
            'total_bytes': 0,
            'requests_by_method': defaultdict(int),
            'responses_by_status': defaultdict(int),
            'requests_by_host': defaultdict(int),
        }
    
    def start_capture(self, host: str = None, port: int = None,
                      filter_expr: str = None) -> Dict[str, Any]:
        """Iniciar captura de tráfego."""
        self.capturing = True
        self._stop_event.clear()
        
        if host:
            self.capture_host = host
        if port:
            self.capture_port = port
        
        # Start capture thread (simulated for now)
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        return {
            'success': True,
            'message': f'Captura iniciada em {self.capture_host}:{self.capture_port}',
            'host': self.capture_host,
            'port': self.capture_port,
        }
    
    def stop_capture(self) -> Dict[str, Any]:
        """Parar captura."""
        self.capturing = False
        self._stop_event.set()
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        return {
            'success': True,
            'message': 'Captura parada',
            'sessions_captured': len(self.sessions),
        }
    
    def get_sessions(self, filter_expr: str = None, limit: int = 100,
                     offset: int = 0) -> Dict[str, Any]:
        """Retornar sessões capturadas."""
        sessions = self.sessions
        
        # Apply filter
        if filter_expr:
            sessions = [s for s in sessions if self._match_filter(s, filter_expr)]
        
        # Sort by timestamp
        sessions = sorted(sessions, key=lambda x: x.timestamp, reverse=True)
        
        # Paginate
        total = len(sessions)
        sessions = sessions[offset:offset + limit]
        
        return {
            'success': True,
            'total': total,
            'returned': len(sessions),
            'offset': offset,
            'limit': limit,
            'sessions': [self._session_to_dict(s) for s in sessions],
        }
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retornar sessão específica."""
        for s in self.sessions:
            if s.id == session_id:
                return {'success': True, 'session': self._session_to_dict(s)}
        return {'success': False, 'error': 'Sessão não encontrada'}
    
    def add_rule(self, name: str, filter_expr: str, action: str,
                 headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Adicionar regra de captura."""
        rule = CaptureRule(name=name, filter=filter_expr, action=action,
                          headers=headers or {})
        self.rules.append(rule)
        return {'success': True, 'rule': name}
    
    def remove_rule(self, name: str) -> Dict[str, Any]:
        """Remover regra."""
        self.rules = [r for r in self.rules if r.name != name]
        return {'success': True}
    
    def get_rules(self) -> Dict[str, Any]:
        """Retornar regras."""
        return {'rules': [self._rule_to_dict(r) for r in self.rules]}
    
    def analyze_jwt(self, token: str) -> Dict[str, Any]:
        """Analisar token JWT."""
        try:
            # Decode header
            header_b64 = token.split('.')[0]
            header_b64 += '=' * (4 - len(header_b64) % 4)
            import base64
            header = json.loads(base64.b64decode(header_b64))
            
            # Decode payload
            payload_b64 = token.split('.')[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(payload_b64))
            
            return {
                'success': True,
                'header': header,
                'payload': payload,
                'is_valid_format': True,
                'issuer': payload.get('iss', 'N/A'),
                'subject': payload.get('sub', 'N/A'),
                'expiration': payload.get('exp', 'N/A'),
                'issued_at': payload.get('iat', 'N/A'),
            }
            
        except Exception as e:
            return {'success': False, 'error': f'JWT inválido: {e}'}
    
    def decode_response(self, session_id: str, encoding: str = 'auto') -> Dict[str, Any]:
        """Decodificar response."""
        session = next((s for s in self.sessions if s.id == session_id), None)
        if not session:
            return {'error': 'Sessão não encontrada'}
        
        body = session.response_body
        
        if encoding == 'auto':
            # Auto-detect
            if session.content_type and 'json' in session.content_type.lower():
                try:
                    decoded = json.loads(body)
                    return {'success': True, 'encoding': 'json', 'data': decoded}
                except:
                    pass
            elif session.content_type and 'xml' in session.content_type.lower():
                return {'success': True, 'encoding': 'xml', 'data': body[:1000]}
        
        return {'success': True, 'encoding': encoding, 'data': body[:2000]}
    
    def export_sessions(self, format_type: str = 'json', 
                        output_path: str = None) -> Dict[str, Any]:
        """Exportar sessões."""
        if not output_path:
            output_path = f'sessions_{int(time.time())}.{format_type}'
        
        try:
            if format_type == 'json':
                data = [self._session_to_dict(s) for s in self.sessions]
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            
            elif format_type == 'text':
                with open(output_path, 'w') as f:
                    for s in self.sessions:
                        f.write(f'[{s.timestamp}] {s.method} {s.url} -> {s.status_code}\n')
                        f.write(f'  Response: {s.response_body[:200]}\n\n')
            
            elif format_type == 'har':
                # HAR format
                har = {
                    'log': {
                        'version': '1.2',
                        'creator': {'name': 'RE-Toolkit Fiddler'},
                        'entries': [self._session_to_har(s) for s in self.sessions]
                    }
                }
                with open(output_path, 'w') as f:
                    json.dump(har, f, indent=2)
            
            return {'success': True, 'path': output_path, 'count': len(self.sessions)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retornar estatísticas."""
        return {
            'total_sessions': len(self.sessions),
            'total_bytes': sum(s.body_size for s in self.sessions),
            'requests_by_method': dict(self.stats['requests_by_method']),
            'responses_by_status': dict(self.stats['responses_by_status']),
            'top_hosts': dict(sorted(self.stats['requests_by_host'].items(), 
                                    key=lambda x: -x[1])[:10]),
        }
    
    def simulate_request(self, method: str, url: str, 
                         headers: Dict[str, str] = None,
                         body: str = None) -> Dict[str, Any]:
        """Simular requisição HTTP (para teste)."""
        try:
            parsed = urllib.parse.urlparse(url)
            
            session = HttpSession(
                id=f'sim_{int(time.time())}',
                timestamp=datetime.now(),
                method=method,
                url=url,
                host=parsed.hostname or 'unknown',
                path=parsed.path or '/',
                status_code=200,
                request_headers=headers or {},
                request_body=body or '',
            )
            
            # Simulate response
            session.response_headers = {
                'Content-Type': 'application/json',
                'Server': 'TestServer',
            }
            session.response_body = json.dumps({
                'status': 'ok',
                'simulated': True,
                'method': method,
                'url': url,
            })
            session.body_size = len(session.response_body.encode())
            
            self.sessions.append(session)
            self._update_stats(session)
            
            return {
                'success': True,
                'session': self._session_to_dict(session),
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ============================================================
    # METODOS INTERNOS
    # ============================================================
    
    def _capture_loop(self):
        """Loop de captura (simulado)."""
        while self.capturing and not self._stop_event.is_set():
            # In real implementation, would use a proxy or socket monitor
            time.sleep(1)
    
    def _match_filter(self, session: HttpSession, filter_expr: str) -> bool:
        """Verificar se sessão corresponde ao filtro."""
        expr = filter_expr.lower()
        
        if 'status:' in expr:
            status_val = expr.replace('status:', '').strip()
            if str(session.status_code) != status_val:
                return False
        
        if 'host:' in expr:
            host_val = expr.replace('host:', '').strip()
            if host_val not in session.host.lower():
                return False
        
        if 'type:' in expr:
            type_val = expr.replace('type:', '').strip()
            if type_val not in session.content_type.lower():
                return False
        
        return True
    
    def _update_stats(self, session: HttpSession):
        """Atualizar estatísticas."""
        self.stats['total_sessions'] += 1
        self.stats['total_bytes'] += session.body_size
        self.stats['requests_by_method'][session.method] += 1
        self.stats['responses_by_status'][session.status_code] += 1
        self.stats['requests_by_host'][session.host] += 1
    
    def _session_to_dict(self, session: HttpSession) -> Dict:
        """Converter sessão para dict."""
        return {
            'id': session.id,
            'timestamp': session.timestamp.isoformat(),
            'method': session.method,
            'url': session.url,
            'host': session.host,
            'status_code': session.status_code,
            'response_time_ms': session.response_time_ms,
            'request_headers': session.request_headers,
            'request_body': session.request_body[:500],
            'response_headers': session.response_headers,
            'response_body': session.response_body[:500],
            'content_type': session.content_type,
            'body_size': session.body_size,
            'has_jwt': session.has_jwt,
            'has_cookies': session.has_cookies,
        }
    
    def _rule_to_dict(self, rule: CaptureRule) -> Dict:
        """Converter regra para dict."""
        return {
            'name': rule.name,
            'filter': rule.filter,
            'action': rule.action,
            'headers': rule.headers,
        }
    
    def _session_to_har(self, session: HttpSession) -> Dict:
        """Converter para formato HAR."""
        return {
            'startedDateTime': session.timestamp.isoformat(),
            'request': {
                'method': session.method,
                'url': session.url,
                'headers': [{'name': k, 'value': v} for k, v in session.request_headers.items()],
                'postData': session.request_body,
            },
            'response': {
                'status': session.status_code,
                'headers': [{'name': k, 'value': v} for k, v in session.response_headers.items()],
                'content': {
                    'size': session.body_size,
                    'text': session.response_body[:1000],
                },
            },
        }


# Quick test
if __name__ == '__main__':
    engine = FiddlerEngine()
    
    # Start capture
    result = engine.start_capture()
    print(f"Start: {result}")
    
    # Simulate some requests
    engine.simulate_request('GET', 'https://api.example.com/users')
    engine.simulate_request('POST', 'https://api.example.com/login', 
                           body='{"username":"test","password":"pass"}')
    engine.simulate_request('GET', 'https://api.example.com/token')
    
    # Get sessions
    sessions = engine.get_sessions()
    print(f"Sessions: {sessions.get('total')} total, {sessions.get('returned')} returned")
    
    # Analyze JWT
    test_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    jwt_result = engine.analyze_jwt(test_jwt)
    print(f"JWT: {jwt_result.get('success')}")
    
    # Get stats
    stats = engine.get_statistics()
    print(f"Stats: {stats}")
    
    # Export
    export = engine.export_sessions('json', 'test_sessions.json')
    print(f"Export: {export}")
    
    engine.stop_capture()