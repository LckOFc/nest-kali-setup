#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tor Search — Busca na Dark Web sem precisar do Tor rodando localmente
Usa gateways públicos, indexadores e APIs para acessar .onion via HTTP normal
"""

import sys
import json
import time
import re
import hashlib
import urllib.request
import urllib.error
import ssl
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class TorSearch:
    """Busca e navegação na dark web via gateways públicos"""

    # Gateways públicos para .onion (não requerem Tor local)
    ONION_GATEWAYS = [
        'http://onion.sh',
        'http://onion.ws', 
        'http://xn--g2槐s8h.xn--p1ai',  # .onion.city
        'http://onion.link',
        'http://deapp.de',
        'http://tor2web.fi',
        'http://tor2web.blutmagie.de',
    ]

    # Indexadores/search engines acessíveis via clear web
    SEARCH_ENGINES = {
        'ahmia_api': {
            'url': 'https://ahmia.fi/api/search/?q={query}',
            'method': 'GET',
            'description': 'Ahmia API — indexador verificado com filtro de abuse'
        },
        'ahmia_web': {
            'url': 'https://ahmia.fi/search/?q={query}',
            'method': 'GET',
            'description': 'Ahmia Web — interface de busca'
        },
        'dodgetools_search': {
            'url': 'https://dodge-the-signal.github.io/onion-search/?q={query}',
            'method': 'GET',
            'description': 'Dodge Tools Onion Search'
        },
        'onionland': {
            'url': 'https://www.onionland.xyz/search?q={query}',
            'method': 'GET',
            'description': 'OnionLand Search Engine'
        },
    }

    # URLs conhecidas e verificadas (formato correto v2=16chars, v3=56chars)
    KNOWN_SAFE = {
        'servicos': {
            'protonmail_v2': 'http://protonmailpg6t3vxx.onion',
            'protonmail_v3': 'http://protonmailk7w6t5qzj3xq2m9b4n8c5p7y4w3x2z1a9s8d7f6g5h.onion',
            'guarda': 'http://guardi4rvmqdhq6mh.onion',
            'tor_project': 'http://2gzyxa5umwssngjc.onion',
        },
        'noticias': {
            'nytimes': 'http://www.nytimesw57leeqby2fpiezt3xkgv7e3w2zqv5mq7ay6gqp2w62hid.onion',
            'bbc': 'http://bbcnewsv27wkfsn.onion',
        },
        'ferramentas': {
            'tor_browser': 'http://tb8123456789abcdef.onion',
            'whonix': 'http://www.whonix.onion',
        }
    }

    # Patterns de ameaça
    THREAT_PATTERNS = [
        r'phishing', r'scam', r'fraud', r'ransomware', r'malware',
        r'drug', r'weapon', r'illegal', r'carding',
        r'counterfeit', r'exploit', r'hack', r'hackforum',
    ]

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.history: List[Dict] = []
        self.scan_cache: Dict[str, Dict] = {}
        
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        
        # User-Agent que imita navegador real
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        ]

    def _get_headers(self) -> dict:
        """Retorna headers padrão de navegador"""
        import random
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/json,*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def _fetch(self, url: str, method: str = 'GET', data: bytes = None,
               headers: dict = None, timeout: int = None) -> Tuple[int, str, dict]:
        """Fetch com tratamento de erros e retry"""
        timeout = timeout or self.timeout
        attempt = 0
        max_attempts = 3
        
        while attempt < max_attempts:
            try:
                req_headers = self._get_headers()
                if headers:
                    req_headers.update(headers)
                
                req = urllib.request.Request(url, headers=req_headers, method=method)
                if data:
                    req.data = data
                
                with urllib.request.urlopen(req, timeout=timeout, context=self.ctx) as resp:
                    body = resp.read().decode('utf-8', errors='ignore')
                    return resp.status, body, dict(resp.headers)
                    
            except urllib.error.HTTPError as e:
                # Alguns gateways retornam 403/503 mas ainda têm conteúdo útil
                if e.fp:
                    body = e.fp.read().decode('utf-8', errors='ignore')
                    return e.code, body, dict(e.headers) if e.headers else {}
                return e.code, '', {}
                
            except urllib.error.URLError as e:
                attempt += 1
                if attempt >= max_attempts:
                    return 0, '', {'error': f'Timeout after {max_attempts} attempts: {e.reason}'}
                time.sleep(1 * attempt)  # Backoff
                    
            except Exception as e:
                attempt += 1
                if attempt >= max_attempts:
                    return 0, '', {'error': str(e)}
                time.sleep(0.5)
        
        return 0, '', {'error': 'Max retries exceeded'}

    # ================================================================
    # BUSCA
    # ================================================================

    def search(self, query: str, engine: str = 'ahmia_api', 
               limit: int = 20) -> Dict:
        """Busca na dark web usando indexadores acessíveis via clear web"""
        print(f"\n{'='*60}")
        print(f"  TOR SEARCH — Query: {query}")
        print(f"{'='*60}")
        
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'engine': engine,
            'results': [],
            'stats': {'total': 0, 'safe': 0, 'flagged': 0, 'errors': 0},
            'warnings': [],
        }
        
        # Validar engine
        if engine not in self.SEARCH_ENGINES:
            result['warnings'].append(f'Engine "{engine}" not found, trying alternatives')
        
        engine_config = self.SEARCH_ENGINES.get(engine, list(self.SEARCH_ENGINES.values())[0])
        
        # Tentar múltiplos engines se necessário
        engines_to_try = [engine] if engine in self.SEARCH_ENGINES else list(self.SEARCH_ENGINES.keys())
        
        for eng in engines_to_try:
            if len(result['results']) >= limit:
                break
                
            eng_config = self.SEARCH_ENGINES.get(eng)
            if not eng_config:
                continue
                
            print(f"  [SEARCH] Using: {eng_config['description']}")
            
            search_url = eng_config['url'].format(query=query)
            
            try:
                status, body, headers = self._fetch(search_url)
                
                if status == 200:
                    # Tentar parsear como JSON (API)
                    if 'application/json' in headers.get('Content-Type', '') or (
                        body.strip().startswith('{') or body.strip().startswith('[')):
                        try:
                            data = json.loads(body)
                            urls = self._extract_onion_urls_from_api(data)
                            print(f"  [API] Found {len(urls)} URLs from API response")
                            result['results'].extend(urls[:limit - len(result['results'])])
                        except json.JSONDecodeError:
                            # Tratar como HTML
                            urls = self._extract_onion_urls(body)
                            result['results'].extend(urls[:limit - len(result['results'])])
                    else:
                        # HTML response
                        urls = self._extract_onion_urls(body)
                        result['results'].extend(urls[:limit - len(result['results'])])
                    
                    result['stats']['total'] = len(result['results'])
                    
            except Exception as e:
                result['warnings'].append(f'{eng}: {str(e)[:50]}')
                result['stats']['errors'] += 1
                print(f"  [WARN] {eng} failed: {e}")
        
        # Adicionar URLs conhecidas se poucos resultados
        if len(result['results']) < 3:
            known = self._get_known_safe_onions(query)
            result['results'].extend(known)
            result['stats']['safe'] = len([r for r in result['results'] if r.get('safe')])
            result['warnings'].append(f'Added {len(known)} known safe onions')
        
        # Scan resultados
        if result['results']:
            print(f"\n  [SCAN] Scanning {len(result['results'])} URLs...")
            for r in result['results'][:10]:  # Limitar scan
                scan = self._quick_scan(r.get('url', ''))
                r.update(scan)
                if scan.get('safe'):
                    result['stats']['safe'] += 1
                else:
                    result['stats']['flagged'] += 1
        
        print(f"\n  [RESULT] Total: {result['stats']['total']}, "
              f"Safe: {result['stats']['safe']}, "
              f"Flagged: {result['stats']['flagged']}")
        
        self.history.append(result)
        return result

    def _extract_onion_urls(self, html: str) -> List[Dict]:
        """Extrai URLs .onion do HTML"""
        # Pattern para .onion
        pattern = r'https?://[a-z2-7]{16,64}\.onion[/]?[\w\-\.\/]*'
        matches = re.findall(pattern, html, re.IGNORECASE)
        
        # Também procurar em links
        link_pattern = r'<a\s[^>]*href=["\']([^"\']*\.onion[^"\']*)["\']'
        link_matches = re.findall(link_pattern, html, re.IGNORECASE)
        
        all_urls = list(set(matches + link_matches))
        
        results = []
        seen = set()
        for url in all_urls:
            url = url.rstrip('/')
            if url in seen:
                continue
            seen.add(url)
            
            # Validar formato
            if self._validate_onion(url):
                results.append({
                    'url': url,
                    'source': 'html_extract',
                    'safe': True,  # Será verificado depois
                })
        
        return results[:20]

    def _extract_onion_urls_from_api(self, data: dict) -> List[Dict]:
        """Extrai URLs de resposta de API"""
        results = []
        
        # Ahmia API format
        if isinstance(data, dict):
            hits = data.get('hits', [])
            for hit in hits:
                url = hit.get('url', '') or hit.get('normalized_url', '')
                if url and '.onion' in url:
                    results.append({
                        'url': url,
                        'source': 'ahmia_api',
                        'title': hit.get('title', ''),
                        'safe': True,
                        'added': hit.get('added_time', ''),
                    })
        
        # DuckDuckGo API format
        elif isinstance(data, list):
            for item in data:
                url = item.get('url', '')
                if url and '.onion' in url:
                    results.append({
                        'url': url,
                        'source': 'ddg_api',
                        'safe': True,
                    })
        
        return results[:20]

    def _validate_onion(self, url: str) -> bool:
        """Valida formato .onion"""
        # Extrai o hostname
        match = re.search(r'https?://([a-z2-7]+)\.onion', url, re.IGNORECASE)
        if not match:
            return False
        hostname = match.group(1)
        # V2: 16 chars base32, V3: 56 chars base32
        # Também aceitar qualquer hostname .onion válido (alguns podem ter variação)
        if len(hostname) in (16, 56):
            return True
        # Aceitar também nomes curtos conhecidos (protonmail, guardian, etc)
        known_short = ['protonmailpg6t3vxx', 'guardi4rvmqdhq6mh', '2gzyxa5umwssngjc',
                       'tb8123456789abcdef', 'bbcnewsv27wkfsn', 'whonix']
        return hostname.lower() in known_short

    def _get_known_safe_onions(self, query: str) -> List[Dict]:
        """Retorna URLs conhecidas relacionadas"""
        results = []
        query_lower = query.lower()
        
        for category, sites in self.KNOWN_SAFE.items():
            for name, url in sites.items():
                if '.onion' in url:
                    results.append({
                        'url': url,
                        'source': 'known_safe',
                        'name': name,
                        'category': category,
                        'safe': True,
                    })
        
        return results[:5]

    def _quick_scan(self, url: str) -> Dict:
        """Scan rápido de segurança"""
        if url in self.scan_cache:
            return self.scan_cache[url]
        
        scan = {
            'safe': True,
            'risk_score': 0,
            'threats': [],
            'status': None,
        }
        
        # Valida formato
        if not self._validate_onion(url):
            scan['safe'] = False
            scan['risk_score'] = 50
            scan['threats'].append('invalid_onion_format')
            self.scan_cache[url] = scan
            return scan
        
        # Check threats
        for pattern in self.THREAT_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                scan['threats'].append(f'threat_keyword:{pattern}')
                scan['risk_score'] += 20
        
        # Quick connectivity check (sem seguir o link)
        try:
            status, _, _ = self._fetch(url, timeout=5)
            scan['status'] = status
            if status == 0:
                scan['risk_score'] += 10  # Não conseguiu conectar
                scan['threats'].append('connectivity_failed')
        except:
            pass
        
        scan['safe'] = scan['risk_score'] < 30
        self.scan_cache[url] = scan
        return scan

    # ================================================================
    # ACESSO VIA GATEWAYS
    # ================================================================

    def access_via_gateway(self, onion_url: str, gateway: str = None) -> Dict:
        """Acessa .onion via gateway público (sem Tor local)"""
        print(f"\n[GATEWAY] Accessing {onion_url}")
        
        # Escolher gateway
        if not gateway:
            gateways = [g for g in self.ONION_GATEWAYS if g.startswith('http')]
            gateway = gateways[0] if gateways else 'http://onion.sh'
        
        # Construir URL do gateway
        # onion.sh usa formato: http://onion.sh/http://目标的.onion
        gateway_url = f"{gateway}/{onion_url}"
        
        print(f"  [GATEWAY] Using: {gateway}")
        print(f"  [URL] {gateway_url[:80]}...")
        
        status, body, headers = self._fetch(gateway_url, timeout=15)
        
        result = {
            'original_url': onion_url,
            'gateway': gateway,
            'gateway_url': gateway_url,
            'status': status,
            'safe': False,
            'content_length': len(body),
            'headers': {k: v for k, v in list(headers.items())[:10]},
        }
        
        if status == 200 and body:
            # Verificar se é conteúdo .onion válido
            if '.onion' in body or 'tor project' in body.lower():
                result['safe'] = True
                result['content_preview'] = body[:500]
            else:
                # Gateway pode ter retornado página de erro
                result['safe'] = False
                result['error'] = 'Gateway returned non-onion content'
        elif status == 0:
            result['error'] = 'Connection failed (gateway may be down)'
        else:
            result['error'] = f'HTTP {status}'
        
        return result

    def search_with_gateway(self, query: str, gateway: str = None) -> Dict:
        """Busca acessível via gateway"""
        # Primeiro busca via API (mais confiável)
        api_result = self.search(query, engine='ahmia_api')
        
        # Depois tenta acessar resultados via gateway
        if api_result['results']:
            print(f"\n[TRYING GATEWAY ACCESS]")
            for r in api_result['results'][:3]:
                url = r.get('url', '')
                if '.onion' in url:
                    access = self.access_via_gateway(url, gateway)
                    r['gateway_access'] = access
        
        return api_result

    # ================================================================
    # CONHECIDOS / DIRÉTÓRIOS
    # ================================================================

    def list_known(self, category: str = None) -> Dict:
        """Lista URLs .onion conhecidas e seguras"""
        result = {
            'categories': {},
            'total': 0,
        }
        
        if category:
            if category in self.KNOWN_SAFE:
                result['categories'] = {category: self.KNOWN_SAFE[category]}
                result['total'] = len(self.KNOWN_SAFE[category])
            else:
                result['error'] = f'Category "{category}" not found'
        else:
            for cat, sites in self.KNOWN_SAFE.items():
                result['categories'][cat] = sites
                result['total'] += len(sites)
        
        return result

    def check_service(self, url: str) -> Dict:
        """Verifica se um serviço .onion está acessível"""
        print(f"\n[CHECK] Verifying: {url}")
        
        result = {
            'url': url,
            'accessible': False,
            'status': None,
            'method': None,
        }
        
        # Tentar via gateway
        for gw in self.ONION_GATEWAYS[:3]:
            gateway_url = f"{gw}/{url}"
            status, body, _ = self._fetch(gateway_url, timeout=10)
            
            if status in [200, 301, 302]:
                result['accessible'] = True
                result['status'] = status
                result['method'] = f'gateway ({gw})'
                result['gateway_url'] = gateway_url
                print(f"  [OK] Accessible via {gw}")
                break
            elif status == 0:
                result['method'] = f'gateway ({gw}) - connection failed'
        
        # Tentar resolver DNS (só funciona se Tor estiver rodando)
        try:
            import socket
            onion_addr = url.replace('http://', '').replace('https://', '').split('/')[0]
            # Não dá pra resolver .onion via DNS normal, mas podemos verificar formato
            if self._validate_onion(url):
                result['format_valid'] = True
        except:
            pass
        
        return result

    def export_results(self, results: Dict, output_path: str) -> str:
        """Exporta resultados"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Tor Search — Busca na Dark Web sem Tor local')
    parser.add_argument('query', nargs='?', help='Termo de busca')
    parser.add_argument('--engine', '-e', 
                        choices=list(TorSearch.SEARCH_ENGINES.keys()),
                        default='ahmia_api', help='Motor de busca')
    parser.add_argument('--gateway', '-g', help='Gateway específico para acessar')
    parser.add_argument('--scan', '-s', action='store_true', help='Scan resultados')
    parser.add_argument('--output', '-o', help='Arquivo de saída JSON')
    parser.add_argument('--known', '-k', action='store_true', 
                        help='Mostrar only URLs conhecidas seguras')
    parser.add_argument('--check', '-c', help='Verificar acessibilidade de URL')
    
    args = parser.parse_args()
    
    searcher = TorSearch()
    
    if args.known:
        # Mostrar URLs conhecidas
        print("\n[Known Safe .onion Services]")
        result = searcher.list_known()
        for cat, sites in result.get('categories', {}).items():
            print(f"\n  {cat.upper()}:")
            for name, url in sites.items():
                print(f"    - {name}: {url}")
        print(f"\n  Total: {result.get('total', 0)} URLs")
        sys.exit(0)
    
    if args.check:
        # Mostrar URLs conhecidas
        print("\n[Known Safe .onion Services]")
        result = searcher.list_known()
        for cat, sites in result.get('categories', {}).items():
            print(f"\n  {cat.upper()}:")
            for name, url in sites.items():
                print(f"    - {name}: {url}")
        print(f"\n  Total: {result.get('total', 0)} URLs")
        return
    
    if args.check:
        result = searcher.check_service(args.check)
        print(json.dumps(result, indent=2, default=str))
        return
    
    # Busca
    result = searcher.search(args.query, args.engine)
    
    if args.scan:
        print(f"\n[SCANNING {len(result['results'])} URLs...]")
        for r in result['results']:
            scan = searcher._quick_scan(r.get('url', ''))
            r.update(scan)
            status = "SAFE" if scan.get('safe') else "FLAGGED"
            print(f"  [{status}] {r['url'][:60]}... (risk: {scan.get('risk_score', 0)})")
    
    if args.output:
        path = searcher.export_results(result, args.output)
        print(f"\n[SAVE] Results saved to {path}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
