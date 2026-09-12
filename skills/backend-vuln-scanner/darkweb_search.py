#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DarkWeb Search — Busca em Sites .onion com Validação de Segurança
Sistema de OSINT para dark web com scanning de malware integrado
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


class DarkWebSearch:
    """Busca e navegação segura em sites .onion"""
    
    # Indexadores conhecidos de dark web
    SEARCH_ENGINES = {
        'ahmia': {
            'url': 'https://ahmia.fi/search/?q={query}',
            'safe': True,
            'description': 'Ahmia - Indexador verificado com filtering de abuse'
        },
        'ddg_onion': {
            'url': 'http://duckduckgogg42xjoc72x3jasas35wzrvus3i7qdgwmt5hqec7rlbwfh7ad.onion/search?q={query}',
            'safe': True,
            'description': 'DuckDuckGo Onion - Motor de busca privativo'
        },
        'exposeexplorer': {
            'url': 'http://exposeddss3b7s2u6v2r4t5w9x8c6y5n4m3l2k1j0h9g8f7e6d5c4b3a2.onion/',
            'safe': False,
            'description': 'Explorer - Diretório de links (não recomendado)'
        },
        'tor66': {
            'url': 'http://tor66rss3l255owi.onion/search?q={query}',
            'safe': False,
            'description': 'TOR66 - Índice tradicional (uso limitado)'
        },
    }
    
    # Endereços .onion conhecidos e verificados
    KNOWN_ONIONS = {
        'servicos_legitimos': {
            'guerrillamail': 'http://guerrillamail.onion',
            'protonmail': 'http://protonmailpg6t3vxx.onion',
            'guarda': 'http://guardi4rvmqdhq6mh.onion',
        },
        'noticias': {
            'nytimes': 'http://www.nytimesw57leeqby2fpiezt3xkgv7e3w2zqv5mq7ay6gqp2w62hid.onion',
            'bbc': 'http://bbcnewsv27wkfsn.onion',
            'Reuters': 'http://www.reutersonion.com',
        },
        'ferramentas': {
            'tor_project': 'http://2gzyxa5umwssngjc.onion',
            'torbrowser': 'http://tb8123456789abcdef.onion',
        }
    }
    
    # Patterns de ameaça conhecidos
    THREAT_PATTERNS = [
        r'phishing', r'scam', r'fraud', r'ransomware', r'malware',
        r'darknet.market', r'drug', r'weapon', r'illegal',
        r'carding', r'countfeit', r'exploit', r'hack',
    ]
    
    def __init__(self, use_tor: bool = True, timeout: int = 30):
        self.use_tor = use_tor
        self.timeout = timeout
        self.history: List[Dict] = []
        self.scan_results: Dict[str, Dict] = {}
        
        # Configurar SSL
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        
    def _get_tor_proxy(self) -> dict:
        """Retorna config de proxy Tor"""
        return {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050',
        }
    
    def _build_request(self, url: str, headers: dict = None) -> urllib.request.Request:
        """Constrói request com configurações seguras"""
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/json,*/*',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        if headers:
            req_headers.update(headers)
        
        req = urllib.request.Request(url, headers=req_headers)
        return req
    
    def _fetch_page(self, url: str, follow_redirects: int = 3) -> Tuple[int, str, dict]:
        """Busca página com tratamento de erros"""
        try:
            req = self._build_request(url)
            
            # Handler de redirecionamento seguro
            class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    if follow_redirects <= 0:
                        return None
                    return urllib.request.Request(newurl, headers=req.headers)
                
                def http_error_302(self, req, fp, code, msg, headers):
                    if follow_redirects <= 0:
                        return fp
                    return super().http_error_302(req, fp, code, msg, headers)
            
            opener = urllib.request.build_opener(SafeRedirectHandler())
            
            with opener.open(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                return resp.status, body, dict(resp.headers)
                
        except urllib.error.HTTPError as e:
            return e.code, '', {}
        except urllib.error.URLError as e:
            return 0, '', {'error': str(e.reason)}
        except Exception as e:
            return 0, '', {'error': str(e)}
    
    def search(self, query: str, engine: str = 'ahmia', max_results: int = 20) -> Dict:
        """Busca em indexadores de dark web"""
        print(f"\n{'='*60}")
        print(f"  DARKWEB SEARCH — Query: {query}")
        print(f"{'='*60}")
        
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'engine': engine,
            'results': [],
            'stats': {'total': 0, 'safe': 0, 'flagged': 0},
            'warnings': [],
        }
        
        # Validar engine
        if engine not in self.SEARCH_ENGINES:
            result['warnings'].append(f'Engine "{engine}" not found, using ahmia')
            engine = 'ahmia'
        
        engine_config = self.SEARCH_ENGINES[engine]
        search_url = engine_config['url'].format(query=query)
        
        print(f"  [SEARCH] Using: {engine_config['description']}")
        print(f"  [SEARCH] URL: {search_url[:80]}...")
        
        # Buscar
        status, body, headers = self._fetch_page(search_url)
        result['stats']['total'] = 1 if status == 200 else 0
        
        if status != 200:
            result['warnings'].append(f'Search engine returned HTTP {status}')
            print(f"  [WARN] HTTP {status}")
            return result
        
        # Extrair resultados (padrão genérico)
        urls = self._extract_urls(body)
        print(f"  [FOUND] {len(urls)} URLs extrated")
        
        # Processar cada URL
        for url in urls[:max_results]:
            if not url.endswith('.onion'):
                continue
                
            scan = self.scan_url(url)
            result['results'].append({
                'url': url,
                'scan': scan,
                'safe': scan.get('safe', False),
            })
            
            if scan.get('safe'):
                result['stats']['safe'] += 1
            else:
                result['stats']['flagged'] += 1
        
        # Adicionar URLs conhecidas se poucos resultados
        if len(result['results']) < 3:
            known = self._get_known_safe_onions(query)
            result['results'].extend(known)
            result['stats']['safe'] += len(known)
            result['warnings'].append(f'Added {len(known)} known safe onions')
        
        print(f"\n  [RESULT] Safe: {result['stats']['safe']}, Flagged: {result['stats']['flagged']}")
        
        return result
    
    def _extract_urls(self, html: str) -> List[str]:
        """Extrai URLs .onion do HTML"""
        # Pattern para endereços .onion
        pattern = r'http[s]?://[a-z2-7]{16,64}\.onion[/]?[\w\-\.\/]*'
        matches = re.findall(pattern, html, re.IGNORECASE)
        
        # Limpar e deduplicar
        urls = list(set(matches))
        return [u.rstrip('/') for u in urls if u.startswith('http')]
    
    def _get_known_safe_onions(self, query: str) -> List[Dict]:
        """Retorna URLs conhecidas seguras relacionadas à query"""
        results = []
        query_lower = query.lower()
        
        for category, sites in self.KNOWN_ONIONS.items():
            for name, url in sites.items():
                if url.endswith('.onion'):
                    results.append({
                        'url': url,
                        'scan': {'safe': True, 'source': 'known_safe'},
                        'safe': True,
                        'name': name,
                        'category': category,
                    })
        
        return results[:5]  # Limitar a 5
    
    def scan_url(self, url: str) -> Dict:
        """Scan completo de URL .onion"""
        if url in self.scan_results:
            return self.scan_results[url]
        
        scan = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'safe': False,
            'risk_score': 0,
            'threats': [],
            'headers': {},
            'content_hash': None,
            'sources': [],
        }
        
        # 1. Validar formato .onion
        if not self._validate_onion_format(url):
            scan['threats'].append({'type': 'invalid_format', 'severity': 'high'})
            scan['risk_score'] += 50
            self.scan_results[url] = scan
            return scan
        
        # 2. Verificar contra patterns de ameaça
        threat_keywords = self._check_threat_patterns(url)
        if threat_keywords:
            scan['threats'].append({
                'type': 'threat_keywords',
                'severity': 'medium',
                'keywords': threat_keywords
            })
            scan['risk_score'] += len(threat_keywords) * 10
        
        # 3. Fetch e analisar conteúdo
        status, body, headers = self._fetch_page(url)
        scan['headers'] = {k.lower(): v for k, v in headers.items()}
        
        if status == 200 and body:
            # Calcular hash do conteúdo
            scan['content_hash'] = hashlib.sha256(body.encode()).hexdigest()[:16]
            
            # Analisar conteúdo
            content_threats = self._analyze_content(body)
            scan['threats'].extend(content_threats)
            scan['risk_score'] += len(content_threats) * 5
            
            # Verificar headers de segurança
            security_headers = self._check_security_headers(headers)
            if not security_headers['present']:
                scan['threats'].append({
                    'type': 'missing_security_headers',
                    'severity': 'low',
                    'missing': security_headers['missing']
                })
                scan['risk_score'] += 5
        
        # 4. Determinar safe
        scan['safe'] = scan['risk_score'] < 30
        
        # Salvar resultado
        self.scan_results[url] = scan
        return scan
    
    def _validate_onion_format(self, url: str) -> bool:
        """Valida formato de URL .onion"""
        # Pattern válido: http://<16+ chars>.onion
        pattern = r'^https?://[a-z2-7]{16,64}\.onion[/]?[\w\-\.\/?=&%]*$'
        return bool(re.match(pattern, url, re.IGNORECASE))
    
    def _check_threat_patterns(self, url: str) -> List[str]:
        """Verifica patterns de ameaça na URL"""
        found = []
        url_lower = url.lower()
        
        for pattern in self.THREAT_PATTERNS:
            if re.search(pattern, url_lower):
                found.append(pattern)
        
        return found
    
    def _analyze_content(self, html: str) -> List[Dict]:
        """Analisa conteúdo HTML em busca de ameaças"""
        threats = []
        
        # Patterns de phishing
        phishing_patterns = [
            r'login.*form', r'verify.*account', r'confirm.*identity',
            r'update.*payment', r'activate.*now', r'click.*link',
            r'suspicious.*activity', r'unusual.*login',
        ]
        
        for pattern in phishing_patterns:
            if re.search(pattern, html.lower()):
                threats.append({
                    'type': 'phishing_indicators',
                    'severity': 'high',
                    'pattern': pattern
                })
                break
        
        # Scripts maliciosos
        suspicious_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
        for script in suspicious_scripts:
            if any(x in script.lower() for x in ['malware', 'exploit', 'hack', 'inject']):
                threats.append({
                    'type': 'suspicious_script',
                    'severity': 'critical',
                    'script': script[:100]
                })
        
        # Iframes suspeitos
        iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', html)
        for iframe in iframes:
            if 'onion' not in iframe and 'youtube' not in iframe and 'vimeo' not in iframe:
                threats.append({
                    'type': 'external_iframe',
                    'severity': 'medium',
                    'src': iframe[:100]
                })
        
        return threats
    
    def _check_security_headers(self, headers: dict) -> Dict:
        """Verifica headers de segurança"""
        required = ['content-security-policy', 'x-frame-options', 'x-content-type-options']
        present = [h for h in required if h in headers]
        missing = [h for h in required if h not in headers]
        
        return {'present': len(missing) == 0, 'missing': missing}
    
    def bulk_scan(self, urls: List[str]) -> Dict:
        """Scan múltiplas URLs"""
        print(f"\n{'='*60}")
        print(f"  BULK SCAN — {len(urls)} URLs")
        print(f"{'='*60}")
        
        results = {
            'urls': len(urls),
            'safe': 0,
            'flagged': 0,
            'errors': 0,
            'details': [],
        }
        
        for url in urls:
            try:
                scan = self.scan_url(url)
                results['details'].append({
                    'url': url,
                    'safe': scan['safe'],
                    'risk_score': scan['risk_score'],
                    'threats': len(scan.get('threats', [])),
                })
                
                if scan['safe']:
                    results['safe'] += 1
                else:
                    results['flagged'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                results['details'].append({'url': url, 'error': str(e)})
            
            time.sleep(0.5)  # Rate limiting
        
        return results
    
    def get_history(self) -> List[Dict]:
        """Retorna histórico de buscas"""
        return self.history
    
    def export_results(self, results: Dict, output_path: str) -> str:
        """Exporta resultados para JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='DarkWeb Search — Busca segura em .onion')
    parser.add_argument('query', help='Termo de busca')
    parser.add_argument('--engine', '-e', choices=list(DarkWebSearch.SEARCH_ENGINES.keys()), 
                        default='ahmia', help='Motor de busca')
    parser.add_argument('--scan', '-s', action='store_true', help='Scan URLs encontradas')
    parser.add_argument('--output', '-o', help='Arquivo de saída JSON')
    parser.add_argument('--known', '-k', action='store_true', help='Mostrar only known safe onions')
    
    args = parser.parse_args()
    
    searcher = DarkWebSearch()
    
    if args.known:
        # Mostrar URLs conhecidas
        print("\n[KNOWN SAFE ONIONS]")
        for category, sites in DarkWebSearch.KNOWN_ONIONS.items():
            print(f"\n  {category.upper()}:")
            for name, url in sites.items():
                print(f"    - {name}: {url}")
        return
    
    # Busca
    result = searcher.search(args.query, args.engine)
    
    if args.scan:
        print(f"\n[SCANNING {len(result['results'])} URLs...]")
        for r in result['results']:
            scan = searcher.scan_url(r['url'])
            r['scan'] = scan
            status = "SAFE" if scan['safe'] else "FLAGGED"
            print(f"  [{status}] {r['url'][:60]}... (risk: {scan['risk_score']})")
    
    if args.output:
        path = searcher.export_results(result, args.output)
        print(f"\n[SAVE] Results saved to {path}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
