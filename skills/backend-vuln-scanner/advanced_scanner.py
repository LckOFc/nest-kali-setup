#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Vulnerability Scanner
Bypass Cloudflare, Auth Testing, Business Logic Tests
"""

import sys
import json
import time
import random
import urllib.request
import urllib.error
import ssl
import socket
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BypassResult:
    technique: str
    success: bool
    status_code: int
    response_time: float
    details: str = ""


class CloudflareBypasser:
    """Cloudflare WAF Bypass Engine"""
    
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        
    def _make_request(self, url: str, headers: Dict = None) -> tuple:
        if headers is None:
            headers = {}
        start = time.time()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                return resp.status, dict(resp.headers), time.time() - start
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), time.time() - start
        except Exception as e:
            return 0, {}, time.time() - start
    
    def detect_protection(self) -> Dict:
        results = {'protected': False, 'level': 'unknown', 'cf_ray': None}
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        status, headers, _ = self._make_request(f"https://{self.target}", {'User-Agent': ua})
        if 'cf-ray' in headers:
            results['protected'] = True
            results['cf_ray'] = headers['cf-ray']
            results['level'] = 'blocked' if status == 403 else 'standard'
        return results
    
    def bypass_ua_rotation(self) -> List[BypassResult]:
        results = []
        uas = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        ]
        for ua in uas:
            status, headers, elapsed = self._make_request(f"https://{self.target}", {'User-Agent': ua})
            results.append(BypassResult(f"UA: {ua[:40]}...", status == 200, status, elapsed, f"Status: {status}"))
        return results
    
    def bypass_subdomain_enum(self) -> List[BypassResult]:
        results = []
        subs = ['www', 'api', 'app', 'admin', 'dashboard', 'staging', 'dev', 'test', 'beta', 'mail']
        for sub in subs:
            url = f"https://{sub}.{self.target}"
            try:
                socket.gethostbyname(sub + '.' + self.target)
                status, _, _ = self._make_request(url)
                results.append(BypassResult(f"Subdomain: {sub}.{self.target}", status == 200, status, 0, "Found"))
            except:
                pass
        return results
    
    def run_all(self) -> Dict:
        print("\n[CF BYPASS] Testing Cloudflare WAF bypass...")
        detection = self.detect_protection()
        print(f"  Protection: {'YES' if detection['protected'] else 'NO'}")
        if detection['protected']:
            print(f"  CF-Ray: {detection.get('cf_ray')}")
            print(f"  Level: {detection.get('level')}")
        
        results = {'detection': detection, 'bypass_attempts': []}
        
        # UA Rotation
        ua_results = self.bypass_ua_rotation()
        for r in ua_results:
            icon = "[OK]" if r.success else "[ Blocked]"
            results['bypass_attempts'].append(r.__dict__)
        
        # Subdomain enum
        sub_results = self.bypass_subdomain_enum()
        for r in sub_results:
            if r.success:
                icon = "[FOUND]"
                results['bypass_attempts'].append(r.__dict__)
        
        success_count = sum(1 for a in results['bypass_attempts'] if a.get('success'))
        print(f"\n  Results: {success_count} successful bypasses")
        return results


class AuthenticatedScanner:
    """Scanner para areas autenticadas"""
    
    def __init__(self, target: str, cookie: str = None, token: str = None):
        self.target = target
        self.base_headers = {'User-Agent': 'Mozilla/5.0'}
        if cookie:
            self.base_headers['Cookie'] = cookie
        if token:
            self.base_headers['Authorization'] = f"Bearer {token}"
    
    def test_auth_bypass(self) -> List[Dict]:
        vulns = []
        endpoints = ['/admin', '/dashboard', '/api/user', '/settings', '/profile']
        for ep in endpoints:
            url = f"https://{self.target}{ep}"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        vulns.append({'type': 'Auth Bypass', 'severity': 'CRITICAL', 'endpoint': ep, 'evidence': '200 without auth'})
            except:
                pass
        return vulns
    
    def test_idor(self) -> List[Dict]:
        vulns = []
        for uid in [1, 2, 99999, -1]:
            url = f"https://{self.target}/api/user/{uid}"
            try:
                req = urllib.request.Request(url, headers=self.base_headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        vulns.append({'type': 'IDOR', 'severity': 'HIGH', 'endpoint': url, 'user_id': uid})
            except:
                pass
        return vulns
    
    def test_privilege_escalation(self) -> List[Dict]:
        vulns = []
        admin_eps = ['/admin/users', '/admin/settings', '/admin/dashboard', '/api/admin']
        for ep in admin_eps:
            url = f"https://{self.target}{ep}"
            try:
                req = urllib.request.Request(url, headers=self.base_headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        vulns.append({'type': 'Privilege Escalation', 'severity': 'CRITICAL', 'endpoint': ep})
            except:
                pass
        return vulns


class BusinessLogicScanner:
    """Scanner de logica de negocio"""
    
    def __init__(self, target: str):
        self.target = target
    
    def test_parameter_manipulation(self) -> List[Dict]:
        vulns = []
        test_cases = [
            ('price', '-1', 'negative_price'),
            ('price', '0', 'zero_price'),
            ('price', '999999', 'extreme_price'),
            ('quantity', '-1', 'negative_qty'),
            ('quantity', '0', 'zero_qty'),
            ('amount', '-100', 'negative_amount'),
            ('discount', '9999', 'extreme_discount'),
        ]
        for param, value, name in test_cases:
            url = f"https://{self.target}/api/test?{param}={value}"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = resp.read().decode('utf-8', errors='ignore')
                    if resp.status == 200 and ('success' in body.lower() or 'order' in body.lower()):
                        vulns.append({'type': 'Parameter Manipulation', 'severity': 'HIGH', 'param': param, 'value': value, 'test': name})
            except:
                pass
        return vulns
    
    def test_race_condition(self) -> List[Dict]:
        vulns = []
        import threading
        results = []
        
        def make_req():
            try:
                url = f"https://{self.target}/api/claim"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    results.append(resp.status)
            except:
                results.append(0)
        
        threads = [threading.Thread(target=make_req) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        
        if results.count(200) > 1:
            vulns.append({'type': 'Race Condition', 'severity': 'HIGH', 'evidence': f'{results.count(200)} simultaneous successes'})
        
        return vulns
    
    def test_workflow_bypass(self) -> List[Dict]:
        vulns = []
        # Testar pulo de etapas
        steps = ['/checkout/step1', '/checkout/step2', '/checkout/step3', '/payment/confirm']
        for i, step in enumerate(steps):
            url = f"https://{self.target}{step}"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200 and i > 0:  # Acessou passo sem ir nos anteriores
                        vulns.append({'type': 'Workflow Bypass', 'severity': 'MEDIUM', 'step': step})
            except:
                pass
        return vulns


def run_advanced_scan(target: str, auth_cookie: str = None, auth_token: str = None):
    """Executa scan avançado completo"""
    print("=" * 60)
    print(f"  ADVANCED SCAN - {target}")
    print("=" * 60)
    print()
    
    all_vulns = []
    
    # 1. Cloudflare Bypass
    print("[1] Testing Cloudflare WAF bypass...")
    cf_bypasser = CloudflareBypasser(target)
    cf_results = cf_bypasser.run_all()
    print()
    
    # 2. Auth Bypass (se credenciais fornecidas)
    if auth_cookie or auth_token:
        print("[2] Testing authentication bypass...")
        auth_scanner = AuthenticatedScanner(target, auth_cookie, auth_token)
        
        vulns = auth_scanner.test_auth_bypass()
        all_vulns.extend(vulns)
        print(f"  Auth bypass tests: {len(vulns)} vulnerabilities")
        
        vulns = auth_scanner.test_idor()
        all_vulns.extend(vulns)
        print(f"  IDOR tests: {len(vulns)} vulnerabilities")
        
        vulns = auth_scanner.test_privilege_escalation()
        all_vulns.extend(vulns)
        print(f"  Privilege escalation: {len(vulns)} vulnerabilities")
        print()
    
    # 3. Business Logic
    print("[3] Testing business logic vulnerabilities...")
    logic_scanner = BusinessLogicScanner(target)
    
    vulns = logic_scanner.test_parameter_manipulation()
    all_vulns.extend(vulns)
    print(f"  Parameter manipulation: {len(vulns)} vulnerabilities")
    
    vulns = logic_scanner.test_race_condition()
    all_vulns.extend(vulns)
    print(f"  Race conditions: {len(vulns)} vulnerabilities")
    
    vulns = logic_scanner.test_workflow_bypass()
    all_vulns.extend(vulns)
    print(f"  Workflow bypass: {len(vulns)} vulnerabilities")
    print()
    
    # Summary
    print("=" * 60)
    print("  SCAN SUMMARY")
    print("=" * 60)
    print(f"  Target: {target}")
    print(f"  Cloudflare Protection: {'Yes' if cf_results['detection']['protected'] else 'No'}")
    print(f"  Total Vulnerabilities: {len(all_vulns)}")
    
    if all_vulns:
        print(f"\n  Vulnerabilities Found:")
        for v in all_vulns:
            severity = v.get('severity', 'UNKNOWN')
            vtype = v.get('type', 'Unknown')
            print(f"    [{severity}] {vtype}")
    else:
        print("\n  [OK] No vulnerabilities found")
        print("  Note: Protected by Cloudflare WAF")
        print("  For deeper testing, use:")
        print("    - cloudflare-bypass tool")
        print("    - burp suite with WAF bypass extensions")
        print("    - manual testing with valid credentials")
    
    print("=" * 60)
    
    return {
        'target': target,
        'timestamp': datetime.now().isoformat(),
        'cloudflare': cf_results,
        'vulnerabilities': all_vulns,
        'summary': {'total': len(all_vulns)}
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Advanced Vulnerability Scanner')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--cookie', help='Session cookie for auth tests')
    parser.add_argument('--token', help='Auth token for API tests')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    result = run_advanced_scan(args.target, args.cookie, args.token)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[SAVE] Results saved to {args.output}")
