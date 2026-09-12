#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORS Scanner — Testa configuracoes malucas de CORS
"""

import sys
import json
import ssl
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from datetime import datetime


class CORSScanner:
    """Scanner de configuracao CORS"""

    EVIL_ORIGINS = [
        'http://evil.com',
        'https://evil.com',
        'null',
        'http://attacker.evil.com',
        'https://attacker.evil.com',
    ]

    def __init__(self, target: str, timeout: int = 5):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.user_agent = 'Mozilla/5.0'
        self.findings: List[Dict] = []

    def _request(self, url: str, origin: str, method: str = 'GET') -> tuple:
        """Send request with custom Origin header"""
        headers = {
            'Origin': origin,
            'User-Agent': self.user_agent,
            'Accept': '*/*',
        }
        if method == 'POST':
            headers['Content-Type'] = 'application/json'

        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                return resp.status, dict(resp.headers), resp.read().decode('utf-8', errors='ignore')[:200]
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers) if e.headers else {}, ''
        except Exception as e:
            return 0, {}, str(e)

    def scan(self, base_url: str = None) -> Dict:
        """Scan CORS configuration"""
        target_url = base_url or f"https://{self.target}"
        print(f"\n  [CORS] Scanning {target_url}")

        results = {
            'target': self.target,
            'base_url': target_url,
            'timestamp': datetime.now().isoformat(),
            'findings': [],
            'vulnerable': False,
        }

        # Test GET request
        print("  [CORS] Testing GET request...")
        status, headers, body = self._request(target_url, self.EVIL_ORIGINS[0])

        acao = headers.get('Access-Control-Allow-Origin', '')
        accreds = headers.get('Access-Control-Allow-Credentials', '')

        if acao:
            print(f"    ACAO: {acao}")

            # Check for reflection
            if acao == self.EVIL_ORIGINS[0]:
                finding = {
                    'type': 'CORS Origin Reflection',
                    'severity': 'HIGH',
                    'detail': f'Origin {self.EVIL_ORIGINS[0]} is reflected',
                }
                results['findings'].append(finding)
                results['vulnerable'] = True
                print(f"    [VULN] CORS origin reflection detected!")

            # Check for wildcard
            if acao == '*':
                finding = {
                    'type': 'CORS Wildcard Origin',
                    'severity': 'MEDIUM',
                    'detail': 'Wildcard (*) origin allowed',
                }
                results['findings'].append(finding)
                results['vulnerable'] = True
                print(f"    [VULN] Wildcard CORS origin!")

            # Check credentials
            if accreds.lower() == 'true' and acao != '*':
                finding = {
                    'type': 'CORS Credentials Allowed',
                    'severity': 'HIGH',
                    'detail': f'CORS with credentials + specific origin = vulnerable',
                }
                results['findings'].append(finding)
                results['vulnerable'] = True
                print(f"    [VULN] CORS with credentials is dangerous!")

        # Test POST request
        print("  [CORS] Testing POST request...")
        status2, headers2, body2 = self._request(
            target_url, self.EVIL_ORIGINS[0], method='POST'
        )

        acao2 = headers2.get('Access-Control-Allow-Origin', '')
        if acao2 and acao2 != '*':
            if acao2 == self.EVIL_ORIGINS[0]:
                finding = {
                    'type': 'CORS POST Reflection',
                    'severity': 'HIGH',
                    'detail': f'POST with reflected origin',
                }
                results['findings'].append(finding)
                results['vulnerable'] = True

        # Test OPTIONS (preflight)
        print("  [CORS] Testing OPTIONS preflight...")
        status3, headers3, body3 = self._request(target_url, self.EVIL_ORIGINS[0], method='OPTIONS')

        acmethods = headers3.get('Access-Control-Allow-Methods', '')
        ackheaders = headers3.get('Access-Control-Allow-Headers', '')

        if acmethods:
            print(f"    Methods: {acmethods}")
        if ackheaders:
            print(f"    Allowed Headers: {ackheaders}")

        # Summary
        if results['findings']:
            print(f"\n  [CORS] Found {len(results['findings'])} vulnerability(ies)")
        else:
            print(f"\n  [CORS] No CORS vulnerabilities found")

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='CORS Scanner')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--url', '-u', help='Specific URL to test')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    scanner = CORSScanner(args.target)
    result = scanner.scan(args.url)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
