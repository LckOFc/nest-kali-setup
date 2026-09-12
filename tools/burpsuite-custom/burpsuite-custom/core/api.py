"""
CustomBurp - REST API
API REST completa para automacao externa
"""

import json
import time
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class APIResponse:
    """Padroniza respostas da API"""
    success: bool
    data: Dict = None
    error: str = ''
    timestamp: float = None
    
    def to_dict(self) -> Dict:
        result = {
            'success': self.success,
            'timestamp': self.timestamp or time.time()
        }
        if self.data:
            result['data'] = self.data
        if self.error:
            result['error'] = self.error
        return result
    
    @classmethod
    def ok(cls, data: Dict = None) -> 'APIResponse':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, message: str) -> 'APIResponse':
        return cls(success=False, error=message)


class BurpAPI:
    """REST API para CustomBurp"""
    
    def __init__(self, burp_instance):
        self.burp = burp_instance
        self._request_count = 0
        self._api_key = str(uuid.uuid4())[:16]
        self._rate_limits = {}
    
    # ========================================================================
    # PROXY ENDPOINTS
    # ========================================================================
    
    def proxy_status(self) -> Dict:
        """Status do proxy"""
        return APIResponse.ok({
            'running': self.burp.proxy.running,
            'port': self.burp.proxy.port,
            'intercept': self.burp.proxy.intercept
        }).to_dict()
    
    def proxy_toggle(self, running: bool = None) -> Dict:
        """Liga/desliga proxy"""
        if running is None:
            running = not self.burp.proxy.running
        
        if running:
            self.burp.start_proxy()
        else:
            self.burp.stop_proxy()
        
        return APIResponse.ok({'running': self.burp.proxy.running}).to_dict()
    
    def proxy_intercept(self, enabled: bool = True) -> Dict:
        """Controla interceptacao"""
        self.burp.proxy.intercept = enabled
        return APIResponse.ok({'intercept': enabled}).to_dict()
    
    # ========================================================================
    # REQUESTS ENDPOINTS
    # ========================================================================
    
    def get_requests(
        self,
        host: str = None,
        method: str = None,
        min_status: int = None,
        max_status: int = None,
        search: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """Lista requests"""
        requests = self.burp.db.get_requests(
            host=host,
            limit=limit,
            offset=offset,
            search=search
        )
        total = len(requests)
        
        return APIResponse.ok({
            'requests': requests,
            'total': total,
            'limit': limit,
            'offset': offset
        }).to_dict()
    
    def get_request(self, request_id: str) -> Dict:
        """Busca request por ID"""
        requests = self.burp.db.get_requests(limit=1000)
        for r in requests:
            if r['id'] == request_id:
                return APIResponse.ok(r).to_dict()
        return APIResponse.fail('Request not found').to_dict()
    
    def delete_request(self, request_id: str) -> Dict:
        """Deleta request"""
        # Nao ha metodo de delete no DB ainda
        return APIResponse.ok({'deleted': False, 'note': 'Not implemented'}).to_dict()
    
    def clear_requests(self) -> Dict:
        """Limpa requests"""
        self.burp.db.clear_data()
        return APIResponse.ok({'cleared': True}).to_dict()
    
    # ========================================================================
    # ISSUES ENDPOINTS
    # ========================================================================
    
    def get_issues(
        self,
        severity: str = None,
        issue_type: str = None,
        limit: int = 100
    ) -> Dict:
        """Lista issues"""
        issues = self.burp.db.get_issues(
            severity=severity,
            issue_type=issue_type,
            limit=limit
        )
        return APIResponse.ok({'issues': issues, 'total': len(issues)}).to_dict()
    
    def run_scan(self, host: str = None) -> Dict:
        """Executa scan"""
        if host:
            issues = self.burp.scanner.scan_host(host)
        else:
            hosts = set()
            requests = self.burp.db.get_requests(limit=1000)
            for r in requests:
                if r.get('host'):
                    hosts.add(r['host'])
            
            issues = []
            for h in hosts:
                issues.extend(self.burp.scanner.scan_host(h))
        
        return APIResponse.ok({
            'scanned_hosts': list(hosts) if not host else [host],
            'issues_found': len(issues),
            'issues': issues
        }).to_dict()
    
    # ========================================================================
    # REPEATER ENDPOINTS
    # ========================================================================
    
    def repeater_send(
        self,
        method: str,
        url: str,
        headers: Dict = None,
        body: str = '',
        follow_redirects: bool = True
    ) -> Dict:
        """Envia request pelo Repeater"""
        result = self.burp.repeater.send(
            method=method,
            url=url,
            headers=headers or {},
            body=body,
            follow_redirects=follow_redirects
        )
        return APIResponse.ok(result).to_dict()
    
    # ========================================================================
    # INTRUDER ENDPOINTS
    # ========================================================================
    
    def intruder_start(
        self,
        request: str,
        payloads: List[str],
        mode: str = 'sniper',
        threads: int = 5,
        timeout: int = 30
    ) -> Dict:
        """Inicia ataque Intruder"""
        results = self.burp.intruder.attack(
            request_text=request,
            payloads=payloads,
            mode=mode,
            thread_count=threads,
            timeout=timeout
        )
        return APIResponse.ok({
            'results': results,
            'count': len(results)
        }).to_dict()
    
    def intruder_stop(self) -> Dict:
        """Para ataque Intruder"""
        self.burp.intruder.stop()
        return APIResponse.ok({'stopped': True}).to_dict()
    
    def intruder_results(self) -> Dict:
        """Retorna resultados do Intruder"""
        return APIResponse.ok({
            'results': self.burp.intruder.get_results(),
            'count': len(self.burp.intruder.get_results())
        }).to_dict()
    
    # ========================================================================
    # DECODER ENDPOINTS
    # ========================================================================
    
    def decoder_transform(self, action: str, input_data: str) -> Dict:
        """Transforma dado pelo Decoder"""
        result = self.burp.decoder.transform(action, input_data)
        return APIResponse.ok(result).to_dict()
    
    def decoder_list_operations(self) -> Dict:
        """Lista operacoes disponiveis"""
        ops = [
            'url_decode', 'url_encode',
            'base64_decode', 'base64_encode',
            'html_decode', 'html_encode',
            'md5', 'sha1', 'sha256',
            'hex_encode', 'hex_decode',
            'rot13',
            'json_format', 'json_minify'
        ]
        return APIResponse.ok({'operations': ops}).to_dict()
    
    # ========================================================================
    # TARGET ENDPOINTS
    # ========================================================================
    
    def target_add_scope(self, host: str, include: bool = True) -> Dict:
        """Adiciona host ao escopo"""
        if include:
            self.burp.target.add_scope(host, include=True)
        else:
            self.burp.target.exclude_scope(host)
        return APIResponse.ok({'host': host, 'in_scope': include}).to_dict()
    
    def target_is_in_scope(self, url: str) -> Dict:
        """Verifica se URL esta no escopo"""
        in_scope = self.burp.target.is_in_scope(url)
        return APIResponse.ok({'url': url, 'in_scope': in_scope}).to_dict()
    
    def target_get_sitemap(self) -> Dict:
        """Retorna sitemap"""
        return APIResponse.ok(self.burp.target.get_sitemap()).to_dict()
    
    # ========================================================================
    # COMPARER ENDPOINTS
    # ========================================================================
    
    def comparer_compare(self, left: Dict, right: Dict) -> Dict:
        """Compara duas responses"""
        result = self.burp.comparer.compare(left, right)
        return APIResponse.ok(result).to_dict()
    
    # ========================================================================
    # SEQUENCER ENDPOINTS
    # ========================================================================
    
    def sequencer_analyze(self, tokens: List[str], name: str = '') -> Dict:
        """Analisa entropia de tokens"""
        result = self.burp.sequencer.analyze(tokens, name)
        return APIResponse.ok(result).to_dict()
    
    # ========================================================================
    # COLLABORATOR ENDPOINTS
    # ========================================================================
    
    def collaborator_start(self) -> Dict:
        """Inicia Collaborator"""
        info = self.burp.collaborator.start()
        return APIResponse.ok(info).to_dict()
    
    def collaborator_stop(self) -> Dict:
        """Para Collaborator"""
        self.burp.collaborator.stop()
        return APIResponse.ok({'stopped': True}).to_dict()
    
    def collaborator_get_interactions(self, limit: int = 100) -> Dict:
        """Retorna interacoes do Collaborator"""
        return APIResponse.ok({
            'interactions': self.burp.collaborator.get_interactions(limit),
            'count': len(self.burp.collaborator.get_interactions(limit))
        }).to_dict()
    
    def collaborator_generate_payloads(self) -> Dict:
        """Gera payloads OAST"""
        return APIResponse.ok(self.burp.collaborator.generate_payloads()).to_dict()
    
    # ========================================================================
    # SESSION ENDPOINTS
    # ========================================================================
    
    def session_create(self) -> Dict:
        """Cria nova sessao"""
        session = self.burp.session_mgr.create_session()
        return APIResponse.ok(session.to_dict()).to_dict()
    
    def session_get(self, session_id: str) -> Dict:
        """Busca sessao"""
        session = self.burp.session_mgr.get_session(session_id)
        if session:
            return APIResponse.ok(session.to_dict()).to_dict()
        return APIResponse.fail('Session not found').to_dict()
    
    def session_add_cookie(self, session_id: str, name: str, value: str, **kwargs) -> Dict:
        """Adiciona cookie a sessao"""
        success = self.burp.session_mgr.add_cookie(session_id, name, value, **kwargs)
        return APIResponse.ok({'added': success}).to_dict()
    
    def session_list(self) -> Dict:
        """Lista sessoes"""
        return APIResponse.ok(self.burp.session_mgr.list_sessions()).to_dict()
    
    # ========================================================================
    # STATS ENDPOINTS
    # ========================================================================
    
    def stats_get(self) -> Dict:
        """Retorna estatisticas"""
        stats = self.burp.db.get_stats()
        stats['proxy_running'] = self.burp.proxy.running
        stats['requests_total'] = self._request_count
        return APIResponse.ok(stats).to_dict()
    
    def stats_reset(self) -> Dict:
        """Reseta estatisticas"""
        self._request_count = 0
        return APIResponse.ok({'reset': True}).to_dict()
    
    # ========================================================================
    # HELP ENDPOINTS
    # ========================================================================
    
    def help_list(self) -> Dict:
        """Lista endpoints disponiveis"""
        endpoints = [
            {'path': '/api/proxy/status', 'method': 'GET', 'desc': 'Status do proxy'},
            {'path': '/api/proxy/toggle', 'method': 'POST', 'desc': 'Liga/desliga proxy'},
            {'path': '/api/requests', 'method': 'GET', 'desc': 'Lista requests'},
            {'path': '/api/requests/<id>', 'method': 'GET', 'desc': 'Busca request'},
            {'path': '/api/requests/clear', 'method': 'POST', 'desc': 'Limpa requests'},
            {'path': '/api/issues', 'method': 'GET', 'desc': 'Lista issues'},
            {'path': '/api/scan/run', 'method': 'POST', 'desc': 'Executa scan'},
            {'path': '/api/repeater/send', 'method': 'POST', 'desc': 'Envia request'},
            {'path': '/api/intruder/start', 'method': 'POST', 'desc': 'Inicia ataque'},
            {'path': '/api/intruder/results', 'method': 'GET', 'desc': 'Resultados intruder'},
            {'path': '/api/decoder/transform', 'method': 'POST', 'desc': 'Transforma dado'},
            {'path': '/api/target/scope', 'method': 'POST', 'desc': 'Define escopo'},
            {'path': '/api/comparer/compare', 'method': 'POST', 'desc': 'Compara responses'},
            {'path': '/api/sequencer/analyze', 'method': 'POST', 'desc': 'Analisa tokens'},
            {'path': '/api/collaborator/start', 'method': 'POST', 'desc': 'Inicia OAST'},
            {'path': '/api/collaborator/payloads', 'method': 'GET', 'desc': 'Payloads OAST'},
            {'path': '/api/session/create', 'method': 'POST', 'desc': 'Cria sessao'},
            {'path': '/api/session/list', 'method': 'GET', 'desc': 'Lista sessoes'},
            {'path': '/api/stats', 'method': 'GET', 'desc': 'Estatisticas'},
            {'path': '/api/help', 'method': 'GET', 'desc': 'Lista endpoints'},
        ]
        return APIResponse.ok({'endpoints': endpoints, 'api_version': '1.0'}).to_dict()
    
    def handle_request(self, method: str, path: str, data: Dict = None) -> Dict:
        """
        Roteador principal da API
        
        Returns:
            Dict com resposta padronizada
        """
        self._request_count += 1
        
        # Proxy
        if path == '/api/proxy/status' and method == 'GET':
            return self.proxy_status()
        if path == '/api/proxy/toggle' and method == 'POST':
            return self.proxy_toggle(data.get('running'))
        
        # Requests
        if path == '/api/requests' and method == 'GET':
            return self.get_requests(
                host=data.get('host'),
                method=data.get('method'),
                min_status=data.get('min_status'),
                max_status=data.get('max_status'),
                search=data.get('search'),
                limit=data.get('limit', 100),
                offset=data.get('offset', 0)
            )
        if path.startswith('/api/requests/') and method == 'GET':
            return self.get_request(path.split('/')[-1])
        if path == '/api/requests/clear' and method == 'POST':
            return self.clear_requests()
        
        # Issues/Scan
        if path == '/api/issues' and method == 'GET':
            return self.get_issues(
                severity=data.get('severity'),
                issue_type=data.get('issue_type'),
                limit=data.get('limit', 100)
            )
        if path == '/api/scan/run' and method == 'POST':
            return self.run_scan(data.get('host'))
        
        # Repeater
        if path == '/api/repeater/send' and method == 'POST':
            return self.repeater_send(
                method=data.get('method', 'GET'),
                url=data.get('url', ''),
                headers=data.get('headers', {}),
                body=data.get('body', ''),
                follow_redirects=data.get('follow_redirects', True)
            )
        
        # Intruder
        if path == '/api/intruder/start' and method == 'POST':
            return self.intruder_start(
                request=data.get('request', ''),
                payloads=data.get('payloads', []),
                mode=data.get('mode', 'sniper'),
                threads=data.get('threads', 5),
                timeout=data.get('timeout', 30)
            )
        if path == '/api/intruder/results' and method == 'GET':
            return self.intruder_results()
        if path == '/api/intruder/stop' and method == 'POST':
            return self.intruder_stop()
        
        # Decoder
        if path == '/api/decoder/transform' and method == 'POST':
            return self.decoder_transform(data.get('action', ''), data.get('input', ''))
        if path == '/api/decoder/operations' and method == 'GET':
            return self.decoder_list_operations()
        
        # Target
        if path == '/api/target/add' and method == 'POST':
            return self.target_add_scope(data.get('host', ''), data.get('include', True))
        if path == '/api/target/check' and method == 'POST':
            return self.target_is_in_scope(data.get('url', ''))
        if path == '/api/target/sitemap' and method == 'GET':
            return self.target_get_sitemap()
        
        # Comparer
        if path == '/api/comparer/compare' and method == 'POST':
            return self.comparer_compare(data.get('left', {}), data.get('right', {}))
        
        # Sequencer
        if path == '/api/sequencer/analyze' and method == 'POST':
            return self.sequencer_analyze(
                data.get('tokens', []),
                data.get('name', '')
            )
        
        # Collaborator
        if path == '/api/collaborator/start' and method == 'POST':
            return self.collaborator_start()
        if path == '/api/collaborator/stop' and method == 'POST':
            return self.collaborator_stop()
        if path == '/api/collaborator/interactions' and method == 'GET':
            return self.collaborator_get_interactions()
        if path == '/api/collaborator/payloads' and method == 'GET':
            return self.collaborator_generate_payloads()
        
        # Session
        if path == '/api/session/create' and method == 'POST':
            return self.session_create()
        if path.startswith('/api/session/') and method == 'GET':
            session_id = path.split('/')[-1]
            if session_id == 'list':
                return self.session_list()
            return self.session_get(session_id)
        if path.startswith('/api/session/') and method == 'POST':
            parts = path.split('/')
            if len(parts) >= 4:
                session_id = parts[3]
                action = parts[4] if len(parts) > 4 else ''
                if action == 'cookie' and data:
                    return self.session_add_cookie(session_id, data.get('name', ''), data.get('value', ''))
        
        # Stats
        if path == '/api/stats' and method == 'GET':
            return self.stats_get()
        if path == '/api/stats/reset' and method == 'POST':
            return self.stats_reset()
        
        # Help
        if path == '/api/help' and method == 'GET':
            return self.help_list()
        
        return APIResponse.fail(f'Endpoint not found: {method} {path}').to_dict()


if __name__ == '__main__':
    # Teste rapido da API
    from core.engine import CustomBurp
    burp = CustomBurp(db_path=':memory:')
    api = BurpAPI(burp)
    
    print("=== API Tests ===")
    
    # Help
    r = api.handle_request('GET', '/api/help')
    print(f"Help: {len(r['data']['endpoints'])} endpoints")
    
    # Stats
    r = api.handle_request('GET', '/api/stats')
    print(f"Stats: {r['data']['total_requests']} requests")
    
    # Decoder
    r = api.handle_request('POST', '/api/decoder/transform', {'action': 'base64_encode', 'input': 'test'})
    print(f"Decoder: {r['data']['output']}")
    
    # Session
    r = api.handle_request('POST', '/api/session/create')
    session_id = r['data']['session_id']
    print(f"Session created: {session_id}")
    
    r = api.handle_request('GET', f'/api/session/{session_id}')
    print(f"Session retrieved: {r['data']['session_id']}")
    
    # Collaborator
    r = api.handle_request('POST', '/api/collaborator/start')
    print(f"Collaborator: {r['data']['subdomain']}")
    
    r = api.handle_request('GET', '/api/collaborator/payloads')
    print(f"Payloads generated: DNS={r['data']['dns']['full_domain'][:30]}...")
    
    print("\nAPI OK!")
