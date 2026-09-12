#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Headers Scanner — Analise completa de headers de seguranca
Verifica X-Frame-Options, CSP, HSTS, CORS, e outros headers criticos
"""

import sys
import json
import ssl
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from datetime import datetime


class HeaderScanner:
    """Scanner de headers de seguranca"""

    CRITICAL_HEADERS = {
        'Strict-Transport-Security': {
            'name': 'HSTS',
            'description': 'HTTP Strict Transport Security',
            'required_value': True,
            'checks': ['max-age', 'includeSubDomains', 'preload'],
        },
        'Content-Security-Policy': {
            'name': 'CSP',
            'description': 'Content Security Policy',
            'required_value': True,
            'checks': ["default-src", "script-src", "img-src"],
        },
        'X-Frame-Options': {
            'name': 'X-Frame-Options',
            'description': 'Clickjacking protection',
            'required_value': True,
            'valid_values': ['DENY', 'SAMEORIGIN'],
        },
        'X-Content-Type-Options': {
            'name': 'X-Content-Type-Options',
            'description': 'MIME type sniffing protection',
            'required_value': True,
            'valid_values': ['nosniff'],
        },
        'X-XSS-Protection': {
            'name': 'X-XSS-Protection',
            'description': 'XSS filter (legacy)',
            'required_value': False,
            'valid_values': ['1', '1; mode=block'],
        },
        'Referrer-Policy': {
            'name': 'Referrer-Policy',
            'description': 'Referrer information control',
            'required_value': False,
            'valid_values': ['strict-origin-when-cross-origin', 'no-referrer', 'same-origin'],
        },
        'Permissions-Policy': {
            'name': 'Permissions-Policy',
            'description': 'Browser feature permissions',
            'required_value': False,
            'checks': ['camera', 'microphone', 'geolocation'],
        },
        'Cache-Control': {
            'name': 'Cache-Control',
            'description': 'Caching policy',
            'required_value': False,
            'warn_no_cache': True,
        },
    }

    INFO_HEADERS = {
        'Server': {'description': 'Web server software'},
        'X-Powered-By': {'description': 'Technology stack info'},
        'Via': {'description': 'Proxy/gateway info'},
        'Access-Control-Allow-Origin': {'description': 'CORS policy'},
        'Access-Control-Allow-Credentials': {'description': 'CORS credentials'},
        'Access-Control-Allow-Methods': {'description': 'CORS methods'},
        'Access-Control-Allow-Headers': {'description': 'CORS headers'},
        'Set-Cookie': {'description': 'Cookie security flags'},
        'Public-Key-Pins': {'description': 'HPKP (deprecated)'},
        'Expect-CT': {'description': 'Certificate Transparency'},
    }

    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    def _fetch_headers(self, url: str) -> Dict:
        """Fetch headers from URL"""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                return dict(resp.headers)
        except urllib.error.HTTPError as e:
            return dict(e.headers) if e.headers else {}
        except Exception:
            return {}

    def scan(self, url: str = None) -> Dict:
        """Scan security headers"""
        target_url = url or f"https://{self.target}"
        print(f"\n  [HEADERS] Scanning {target_url}")

        headers = self._fetch_headers(target_url)
        results = {
            'url': target_url,
            'timestamp': datetime.now().isoformat(),
            'critical_headers': {},
            'info_headers': {},
            'vulnerabilities': [],
            'score': 0,
            'total_checks': len(self.CRITICAL_HEADERS),
        }

        # Check critical headers
        for header, config in self.CRITICAL_HEADERS.items():
            value = headers.get(header)
            result = {
                'present': value is not None,
                'value': value,
                'status': 'MISSING',
                'issues': [],
            }

            if value:
                value_lower = value.lower()

                # HSTS checks
                if header == 'Strict-Transport-Security':
                    if 'max-age' not in value_lower:
                        result['issues'].append('Missing max-age directive')
                    else:
                        max_age_match = __import__('re').search(r'max-age=(\d+)', value_lower)
                        if max_age_match:
                            max_age = int(max_age_match.group(1))
                            if max_age < 31536000:  # < 1 year
                                result['issues'].append(f'max-age too low: {max_age} seconds')
                            else:
                                result['status'] = 'OK'
                        else:
                            result['status'] = 'WARNING'
                    if 'includesubdomains' not in value_lower:
                        result['issues'].append('Missing includeSubDomains')
                    if 'preload' not in value_lower:
                        result['issues'].append('Missing preload directive')

                # CSP checks
                elif header == 'Content-Security-Policy':
                    if "default-src" not in value_lower:
                        result['issues'].append('Missing default-src directive')
                    if "'unsafe-inline'" in value_lower:
                        result['issues'].append("Contains unsafe-inline")
                    if "'unsafe-eval'" in value_lower:
                        result['issues'].append("Contains unsafe-eval")
                    if value_lower.strip() == "*":
                        result['issues'].append('Wildcard policy (too permissive)')
                    result['status'] = 'OK' if not result['issues'] else 'WARNING'

                # X-Frame-Options checks
                elif header == 'X-Frame-Options':
                    if value_upper := value.upper().strip() in ['DENY', 'SAMEORIGIN']:
                        result['status'] = 'OK'
                    else:
                        result['issues'].append(f'Invalid value: {value}')

                # X-Content-Type-Options checks
                elif header == 'X-Content-Type-Options':
                    if value_lower.strip() == 'nosniff':
                        result['status'] = 'OK'
                    else:
                        result['issues'].append(f'Invalid value: {value}')

                # X-XSS-Protection checks
                elif header == 'X-XSS-Protection':
                    if value.strip() in ['1', '1; mode=block']:
                        result['status'] = 'OK'
                    else:
                        result['issues'].append(f'Legacy header, prefer CSP')

                else:
                    result['status'] = 'OK'
            else:
                if config.get('required_value'):
                    result['status'] = 'MISSING'
                    results['vulnerabilities'].append({
                        'header': header,
                        'severity': 'HIGH',
                        'issue': f'{config["name"]} header missing',
                    })
                else:
                    result['status'] = 'OPTIONAL'

            results['critical_headers'][header] = result

        # Check info headers
        for header, config in self.INFO_HEADERS.items():
            value = headers.get(header)
            if value:
                results['info_headers'][header] = {
                    'present': True,
                    'value': value,
                    'description': config['description'],
                }

                # CORS vulnerability check
                if header == 'Access-Control-Allow-Origin' and value == '*':
                    results['vulnerabilities'].append({
                        'header': 'Access-Control-Allow-Origin',
                        'severity': 'MEDIUM',
                        'issue': 'Wildcard CORS allows any origin',
                    })
                if header == 'Set-Cookie':
                    if 'secure' not in value.lower():
                        results['vulnerabilities'].append({
                            'header': 'Set-Cookie',
                            'severity': 'MEDIUM',
                            'issue': 'Cookie missing Secure flag',
                        })
                    if 'httponly' not in value.lower():
                        results['vulnerabilities'].append({
                            'header': 'Set-Cookie',
                            'severity': 'MEDIUM',
                            'issue': 'Cookie missing HttpOnly flag',
                        })
                    if 'samesite' not in value.lower():
                        results['vulnerabilities'].append({
                            'header': 'Set-Cookie',
                            'severity': 'LOW',
                            'issue': 'Cookie missing SameSite attribute',
                        })

        # Server info disclosure
        server = headers.get('Server', '')
        if server and any(x in server.lower() for x in ['nginx', 'apache', 'express', 'node']):
            results['vulnerabilities'].append({
                'header': 'Server',
                'severity': 'INFO',
                'issue': f'Server version disclosed: {server}',
            })

        # Calculate score
        passed = sum(1 for h in results['critical_headers'].values() if h['status'] == 'OK')
        missing = sum(1 for h in results['critical_headers'].values() if h['status'] == 'MISSING')
        results['score'] = int((passed / results['total_checks']) * 100) if results['total_checks'] > 0 else 0

        # Print summary
        print(f"  [HEADERS] Score: {results['score']}/100")
        print(f"  [HEADERS] Passed: {passed}/{results['total_checks']}")
        print(f"  [HEADERS] Missing: {missing}")

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Security Headers Scanner')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--url', '-u', help='Specific URL to scan')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    scanner = HeaderScanner(args.target)
    result = scanner.scan(args.url)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
