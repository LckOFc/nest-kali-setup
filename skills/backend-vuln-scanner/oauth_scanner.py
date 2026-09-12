#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OAuth/SSO Exploitation Module
Tests for OAuth flows, SSO vulnerabilities, and token exchange attacks
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
class OAuthResult:
    """Resultado de teste OAuth"""
    technique: str
    success: bool
    severity: str
    details: str = ""
    endpoint: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'technique': self.technique,
            'success': self.success,
            'severity': self.severity,
            'details': self.details,
            'endpoint': self.endpoint
        }


class OAuthScanner:
    """Scanner de vulnerabilidades OAuth/SSO"""
    
    # Endpoints comuns de OAuth
    OAUTH_ENDPOINTS = [
        '/auth', '/login', '/signin', '/signup',
        '/oauth', '/oauth2', '/authorize',
        '/auth/google', '/auth/github', '/auth/facebook',
        '/auth/twitter', '/auth/microsoft', '/auth/apple',
        '/sso', '/oidc', '/openid',
        '/api/auth', '/api/oauth',
        '/auth/azure', '/auth/adfs',
    ]
    
    # Callback URLs para testar open redirect
    CALLBACK_PATTERNS = [
        'http://evil.com',
        'https://evil.com',
        'javascript:alert(1)',
        'data:text/html,<script>alert(1)</script>',
        '/redirect?url=http://evil.com',
    ]
    
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.results = []
        self.discovered_providers = []
        
    def _make_request(self, url: str, headers: dict = None) -> Tuple[int, dict, str]:
        """Faz requisição HTTP"""
        if headers is None:
            headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore') if e.fp else ''
            return e.code, dict(e.headers), body
        except Exception as e:
            return 0, {}, str(e)
    
    def discover_oauth_providers(self) -> List[Dict]:
        """Descobre provedores OAuth/SSO"""
        print("[1] Discovering OAuth/SSO providers...")
        
        providers = []
        url = f"https://{self.target}"
        
        status, headers, body = self._make_request(url)
        
        # Procurar links de login social
        social_patterns = [
            r'href=["\'](.*?)(/auth/[^"\']+)["\']',
            r'href=["\'](.*?)(/oauth/[^"\']+)["\']',
            r'href=["\'](.*?)(/login/[a-z]+)["\']',
            r'<a[^>]*href=["\']([^"\']*auth[^"\']*)["\']',
            r'<a[^>]*href=["\']([^"\']*login[^"\']*)["\']',
            r'oauth|google|facebook|github|twitter|apple|microsoft|azure|sso|openid',
        ]
        
        for pattern in social_patterns:
            matches = re.findall(pattern, body, re.I)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                
                # Processar match
                if match.startswith('//'):
                    match = f"https:{match}"
                elif match.startswith('/'):
                    match = f"{url}{match}"
                elif match.startswith('http'):
                    pass
                else:
                    continue
                
                # Detectar provedor
                provider = 'unknown'
                if 'google' in match.lower():
                    provider = 'Google'
                elif 'facebook' in match.lower() or 'fb' in match.lower():
                    provider = 'Facebook'
                elif 'github' in match.lower():
                    provider = 'GitHub'
                elif 'twitter' in match.lower() or 'x.com' in match.lower():
                    provider = 'Twitter/X'
                elif 'apple' in match.lower():
                    provider = 'Apple'
                elif 'microsoft' in match.lower() or 'azure' in match.lower() or 'live.com' in match.lower():
                    provider = 'Microsoft/Azure'
                elif 'sso' in match.lower():
                    provider = 'SSO'
                elif 'openid' in match.lower() or 'oidc' in match.lower():
                    provider = 'OpenID Connect'
                
                if provider != 'unknown' or match not in [p['url'] for p in providers]:
                    providers.append({
                        'url': match,
                        'provider': provider,
                        'type': 'social' if provider != 'SSO' else 'enterprise'
                    })
        
        self.discovered_providers = providers
        
        if providers:
            print(f"  [+] Found {len(providers)} OAuth endpoint(s):")
            for p in providers:
                print(f"      - {p['provider']}: {p['url']}")
        else:
            print("  [-] No OAuth endpoints found in main page")
        
        return providers
    
    def test_open_redirect(self) -> List[OAuthResult]:
        """Testa open redirect em callback URLs"""
        print("\n[2] Testing open redirect...")
        
        results = []
        
        for provider in self.discovered_providers:
            auth_url = provider['url']
            
            # Adicionar parâmetro redirect_uri malicioso
            for redirect in self.CALLBACK_PATTERNS[:3]:  # Limitar testes
                test_url = f"{auth_url}?redirect_uri={redirect}"
                
                status, headers, _ = self._make_request(test_url)
                
                # Verificar se há redirect
                location = headers.get('Location', '')
                if redirect in location.lower():
                    results.append(OAuthResult(
                        technique="Open Redirect",
                        success=True,
                        severity="HIGH",
                        details=f"Redirect to malicious URL: {redirect}",
                        endpoint=test_url
                    ))
                    print(f"  [HIGH] Open redirect via {redirect}")
        
        return results
    
    def test_state_parameter(self) -> List[OAuthResult]:
        """Testa state parameter omission"""
        print("\n[3] Testing state parameter...")
        
        results = []
        
        for provider in self.discovered_providers:
            auth_url = provider['url']
            
            # Remover state parameter
            test_url = auth_url.replace('&state=', '?').replace('state=xxx', '')
            
            status, headers, body = self._make_request(test_url)
            
            # Verificar se o state é opcional
            if 'state' not in body and status == 200:
                results.append(OAuthResult(
                    technique="Missing State Parameter",
                    success=True,
                    severity="MEDIUM",
                    details="State parameter not enforced",
                    endpoint=test_url
                ))
                print(f"  [MEDIUM] State parameter can be omitted")
        
        return results
    
    def test_pkce(self) -> List[OAuthResult]:
        """Testa PKCE (Proof Key for Code Exchange)"""
        print("\n[4] Testing PKCE...")
        
        results = []
        
        for provider in self.discovered_providers:
            auth_url = provider['url']
            
            # Testar com code_challenge
            test_url = f"{auth_url}?code_challenge=test&code_challenge_method=S256"
            
            status, headers, body = self._make_request(test_url)
            
            # Verificar se PKCE é exigido
            if 'code_challenge' in body.lower() or 'pkce' in body.lower():
                results.append(OAuthResult(
                    technique="PKCE Check",
                    success=True,
                    severity="INFO",
                    details="PKCE parameters recognized",
                    endpoint=test_url
                ))
        
        return results
    
    def test_client_id_enumeration(self) -> List[OAuthResult]:
        """Testa client ID enumeration"""
        print("\n[5] Testing client ID enumeration...")
        
        results = []
        
        # Client IDs comuns
        common_client_ids = [
            'google-client-id',
            'facebook-app-id',
            'github-client-id',
            'microsoft-client-id',
            'apple-client-id',
        ]
        
        for provider in self.discovered_providers:
            auth_url = provider['url']
            
            for client_id in common_client_ids:
                test_url = f"{auth_url}?client_id={client_id}"
                status, headers, body = self._make_request(test_url)
                
                # Verificar resposta
                if 'invalid_client' in body.lower() or 'unknown_client' in body.lower():
                    results.append(OAuthResult(
                        technique="Client ID Enumeration",
                        success=False,
                        severity="LOW",
                        details=f"Client ID '{client_id}' invalid",
                        endpoint=test_url
                    ))
                elif status == 200 and 'redirect' in str(headers).lower():
                    results.append(OAuthResult(
                        technique="Client ID Enumeration",
                        success=True,
                        severity="MEDIUM",
                        details=f"Valid client ID possibly found: {client_id}",
                        endpoint=test_url
                    ))
        
        return results
    
    def test_token_endpoint(self) -> List[OAuthResult]:
        """Testa token endpoint vulnerabilities"""
        print("\n[6] Testing token endpoint...")
        
        results = []
        
        # Token endpoints comuns
        token_paths = [
            '/oauth/token',
            '/oauth2/token',
            '/auth/token',
            '/api/auth/token',
            '/token',
        ]
        
        for path in token_paths:
            token_url = f"https://{self.target}{path}"
            status, headers, body = self._make_request(token_url)
            
            if status == 200:
                results.append(OAuthResult(
                    technique="Token Endpoint Found",
                    success=True,
                    severity="HIGH",
                    details=f"Token endpoint accessible: {path}",
                    endpoint=token_url
                ))
                
                # Testar brute force de grant type
                grant_types = ['authorization_code', 'password', 'client_credentials', 'implicit', 'refresh_token']
                for grant in grant_types:
                    data = json.dumps({
                        'grant_type': grant,
                        'client_id': 'test',
                        'username': 'test',
                        'password': 'test'
                    }).encode()
                    
                    try:
                        req = urllib.request.Request(
                            token_url,
                            data=data,
                            headers={'Content-Type': 'application/json'},
                            method='POST'
                        )
                        status2, headers2, body2 = self._make_request(token_url)
                        
                        if 'invalid_grant' in body2.lower():
                            results.append(OAuthResult(
                                technique="Grant Type: " + grant,
                                success=True,
                                severity="INFO",
                                details=f"Grant type '{grant}' accepted (credentials invalid)",
                                endpoint=token_url
                            ))
                    except:
                        pass
        
        return results
    
    def run_full_scan(self) -> Dict:
        """Executa scan OAuth completo"""
        print("=" * 60)
        print("  OAUTH/SSO VULNERABILITY SCANNER")
        print("=" * 60)
        print()
        
        all_results = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'providers': [],
            'vulnerabilities': [],
            'summary': {}
        }
        
        # Descobrir providers
        providers = self.discover_oauth_providers()
        all_results['providers'] = providers
        
        # Executar testes
        tests = [
            ("Open Redirect", self.test_open_redirect),
            ("State Parameter", self.test_state_parameter),
            ("PKCE", self.test_pkce),
            ("Client ID Enumeration", self.test_client_id_enumeration),
            ("Token Endpoint", self.test_token_endpoint),
        ]
        
        for name, test_func in tests:
            try:
                vulns = test_func()
                all_results['vulnerabilities'].extend([v.to_dict() for v in vulns])
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
        
        # Resumo
        critical = [v for v in all_results['vulnerabilities'] if v.get('severity') == 'CRITICAL']
        high = [v for v in all_results['vulnerabilities'] if v.get('severity') == 'HIGH']
        medium = [v for v in all_results['vulnerabilities'] if v.get('severity') == 'MEDIUM']
        
        all_results['summary'] = {
            'providers_found': len(providers),
            'total_vulnerabilities': len(all_results['vulnerabilities']),
            'critical': len(critical),
            'high': len(high),
            'medium': len(medium)
        }
        
        print("\n" + "=" * 60)
        print("  OAUTH SCAN SUMMARY")
        print("=" * 60)
        print(f"  Providers found: {len(providers)}")
        print(f"  Total vulnerabilities: {len(all_results['vulnerabilities'])}")
        print(f"    - Critical: {len(critical)}")
        print(f"    - High: {len(high)}")
        print(f"    - Medium: {len(medium)}")
        print("=" * 60)
        
        return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='OAuth/SSO Vulnerability Scanner')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    scanner = OAuthScanner(args.target)
    result = scanner.run_full_scan()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    
    return result


if __name__ == "__main__":
    main()
