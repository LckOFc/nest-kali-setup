#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Vulnerability Scanner — Pipeline Completo e Funcional
Fases: Recon -> WAF -> Framework -> GraphQL -> JWT -> Exploit
"""

import sys
import json
import time
import socket
import ssl
import urllib.request
import urllib.error
import re
import hashlib
import hmac
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Adicionar path do modulo
sys.path.insert(0, str(Path(__file__).parent))

from vuln_scanner import run_scan as basic_vuln_scan, ScanConfig
from waf_bypass import AdvancedWAFBypass
from jwt_analyzer import JWTAnalyzer
from graphql_scanner import GraphQLScanner
from framework_scanner import RubyOnRailsScanner, NextJSScanner
from oauth_scanner import OAuthScanner


class CompleteScanner:
    """Scanner completo integrado com todas as fases"""

    def __init__(self, target: str, options: Dict = None):
        self.target = target
        self.options = options or {}
        self.results = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'phases': {},
            'summary': {},
            'tokens': {},
        }
        self.start_time = None

    def _resolve_target(self) -> str:
        """Resolve dominio para URL completa"""
        target = self.target.strip()
        if not target.startswith('http'):
            target = f"https://{target}"
        return target.rstrip('/')

    def phase_recon(self) -> Dict:
        """Fase 1: Reconhecimento basico"""
        print("\n" + "=" * 70)
        print("  [PHASE 1] RECONNAISSANCE")
        print("=" * 70)

        result = {
            'ip': None,
            'ports': {},
            'headers': {},
            'technologies': [],
            'endpoints': [],
            'ssl_info': {},
        }

        # DNS resolution
        try:
            result['ip'] = socket.gethostbyname(self.target)
            print(f"  [IP] {result['ip']}")
        except socket.gaierror:
            print(f"  [ERROR] Cannot resolve {self.target}")
            return result

        # HTTP headers
        try:
            url = self._resolve_target()
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                result['headers'] = dict(resp.headers)
                body = resp.read().decode('utf-8', errors='ignore')[:50000]

                # Detect technologies
                techs = []
                headers_str = json.dumps(result['headers']).lower()

                if 'cloudflare' in headers_str:
                    techs.append('Cloudflare')
                if 'akamai' in headers_str or 'x-served-by' in headers_str:
                    techs.append('Akamai')
                if 'server' in result['headers']:
                    srv = result['headers']['Server'].lower()
                    if 'nginx' in srv:
                        techs.append('Nginx')
                    elif 'apache' in srv:
                        techs.append('Apache')

                body_lower = body.lower()
                if 'react' in body_lower or 'data-reactroot' in body_lower:
                    techs.append('React')
                if '__next_data__' in body_lower or 'next.js' in body_lower:
                    techs.append('Next.js')
                if 'ruby' in headers_str or 'x-request-id' in headers_str:
                    techs.append('Ruby on Rails')
                if 'php' in headers_str or '.php' in body_lower:
                    techs.append('PHP')
                if 'express' in headers_str:
                    techs.append('Express')
                if 'django' in headers_str:
                    techs.append('Django')
                if 'wordpress' in body_lower:
                    techs.append('WordPress')

                result['technologies'] = techs
                print(f"  [TECH] {', '.join(techs) if techs else 'Unknown'}")

                # SSL info
                if resp.url.startswith('https'):
                    result['ssl_info'] = {'protocol': 'TLS', 'encrypted': True}

        except Exception as e:
            print(f"  [WARN] HTTP request failed: {e}")

        # Port scan basico (rapido)
        common_ports = [443, 80]
        open_ports = []
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                if sock.connect_ex((self.target, port)) == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass

        result['open_ports'] = open_ports
        print(f"  [PORTS] Open: {open_ports}")

        # Endpoint discovery (rapido)
        common_paths = [
            '/admin', '/login', '/api', '/robots.txt', '/sitemap.xml',
        ]
        endpoints = []
        for path in common_paths:
            try:
                url = f"{self._resolve_target()}{path}"
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, timeout=3, context=ctx) as resp:
                    status = resp.status
                    if status in [200, 301, 302, 403]:
                        endpoints.append({'path': path, 'status': status})
                        print(f"  [EP] {path} -> {status}")
            except urllib.error.HTTPError as e:
                if e.code in [200, 301, 302, 403, 404]:
                    endpoints.append({'path': path, 'status': e.code})
            except:
                pass

        result['endpoints'] = endpoints
        print(f"  [OK] Found {len(endpoints)} endpoints")

        return result

    def phase_waf_detection(self) -> Dict:
        """Fase 2: Detecao de WAF e bypass"""
        print("\n" + "=" * 70)
        print("  [PHASE 2] WAF DETECTION & BYPASS")
        print("=" * 70)

        result = {'detected': False, 'type': 'Unknown', 'bypass_attempts': []}

        try:
            url = self._resolve_target()
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                headers = dict(resp.headers)
                headers_str = json.dumps(headers).lower()

                if 'cf-ray' in headers or 'cloudflare' in headers_str:
                    result['detected'] = True
                    result['type'] = 'Cloudflare'
                    result['cf_ray'] = headers.get('CF-Ray', 'N/A')
                    print(f"  [WAF] Cloudflare detected (Ray: {result['cf_ray']})")
                elif 'x-frame-options' in headers:
                    result['detected'] = True
                    result['type'] = 'Generic WAF'
                    print(f"  [WAF] Generic WAF detected")

                # Test UA rotation
                uas = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0',
                    'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile',
                    'curl/7.88.1',
                    'python-requests/2.31.0',
                ]
                for ua in uas:
                    req = urllib.request.Request(url, headers={'User-Agent': ua})
                    try:
                        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp2:
                            result['bypass_attempts'].append({
                                'technique': f'UA: {ua[:30]}...',
                                'success': resp2.status == 200,
                                'status': resp2.status,
                            })
                    except urllib.error.HTTPError as e:
                        result['bypass_attempts'].append({
                            'technique': f'UA: {ua[:30]}...',
                            'success': False,
                            'status': e.code,
                        })

        except Exception as e:
            print(f"  [WARN] WAF test failed: {e}")
            result['error'] = str(e)

        return result

    def phase_graphql_scan(self) -> Dict:
        """Fase 3: GraphQL scanner"""
        print("\n" + "=" * 70)
        print("  [PHASE 3] GRAPHQL SCANNER")
        print("=" * 70)

        result = {'endpoints_found': [], 'introspection': False, 'vulnerabilities': []}

        graphql_paths = [
            '/graphql', '/graphql-explorer', '/graphiql', '/api/graphql',
            '/graphql/playground', '/graphql/main', '/v1/graphql',
        ]

        for path in graphql_paths:
            try:
                url = f"{self._resolve_target()}{path}"
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'application/json',
                })
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                    status = resp.status
                    result['endpoints_found'].append({'path': path, 'status': status})
                    print(f"  [GRAPHQL] {path} -> {status}")

                    # Test introspection
                    if status == 200:
                        introspect_payload = json.dumps({
                            'query': '{ __schema { types { name } } }'
                        }).encode()
                        req2 = urllib.request.Request(
                            url,
                            data=introspect_payload,
                            headers={
                                'User-Agent': 'Mozilla/5.0',
                                'Content-Type': 'application/json',
                                'Accept': 'application/json',
                            }
                        )
                        try:
                            with urllib.request.urlopen(req2, timeout=5, context=ctx) as resp2:
                                body = resp2.read().decode('utf-8')
                                if '__schema' in body:
                                    result['introspection'] = True
                                    print(f"  [VULN] GraphQL introspection enabled!")
                        except:
                            pass

            except urllib.error.HTTPError as e:
                if e.code == 405:
                    result['endpoints_found'].append({'path': path, 'status': 405, 'method_not_allowed': True})
            except:
                pass

        return result

    def phase_jwt_analysis(self) -> Dict:
        """Fase 4: JWT analysis com captura real do browser"""
        print("\n" + "=" * 70)
        print("  [PHASE 4] JWT TOKEN ANALYSIS")
        print("=" * 70)

        result = {
            'tokens_found': 0,
            'jwt_tokens': [],
            'analysis_results': [],
            'exploit_results': [],
            'summary': {},
        }

        try:
            from jwt_analyzer import JWTAnalyzer
            analyzer = JWTAnalyzer(self.target)

            # Tentar extrair tokens (browser first, then page source)
            tokens_info = analyzer.extract_all()
            result['tokens_found'] = len(tokens_info)

            for i, tok_info in enumerate(tokens_info[:3], 1):
                print(f"\n  [TOKEN {i}] From: {tok_info.get('source', 'unknown')}")
                decoded = tok_info.get('decoded') or analyzer.decode_jwt(tok_info['token'])

                if decoded:
                    print(f"    Header: {json.dumps(decoded['header'])}")
                    print(f"    Payload keys: {list(decoded['payload'].keys())}")
                    result['jwt_tokens'].append({
                        'source': tok_info.get('source'),
                        'decoded_header': decoded['header'],
                        'decoded_payload': decoded['payload'],
                        'algo': decoded.get('algo', 'unknown'),
                    })

                    # Analisar o token
                    analysis = analyzer.run_full_analysis(tok_info['token'])
                    result['analysis_results'].extend(analysis.get('analysis_results', []))
                    result['exploit_results'].extend(analysis.get('exploit_results', []))

        except ImportError:
            print("  [WARN] jwt_analyzer module not found")
        except Exception as e:
            print(f"  [ERROR] JWT analysis failed: {e}")
            result['error'] = str(e)

        # Calcular summary
        critical = [r for r in result['analysis_results'] if r.severity == 'CRITICAL' and getattr(r, 'success', False)]
        high = [r for r in result['analysis_results'] if r.severity == 'HIGH']
        exploit_successes = sum(
            len(e.get('access_granted', []))
            for e in result.get('exploit_results', [])
        )

        result['summary'] = {
            'total_tests': len(result['analysis_results']),
            'critical_vulns': len(critical),
            'high_vulns': len(high),
            'exploit_successes': exploit_successes,
        }

        print(f"\n  [JWT SUMMARY] Tests: {result['summary']['total_tests']}, "
              f"Critical: {result['summary']['critical_vulns']}, "
              f"Exploits: {result['summary']['exploit_successes']}")

        return result

    def phase_vuln_scan(self) -> Dict:
        """Fase 5: Vulnerability scan basico"""
        print("\n" + "=" * 70)
        print("  [PHASE 5] VULNERABILITY SCAN")
        print("=" * 70)

        result = {'vulnerabilities': [], 'summary': {}}

        try:
            scan_result = basic_vuln_scan(self.target, verbose=False)
            result['vulnerabilities'] = scan_result.get('vulnerabilities', [])
            result['summary'] = scan_result.get('summary', {})
            print(f"  [VULNS] Found {len(result['vulnerabilities'])} vulnerabilities")
        except Exception as e:
            print(f"  [ERROR] Vuln scan failed: {e}")
            result['error'] = str(e)

        return result

    def phase_sensitivity_scan(self) -> Dict:
        """Fase 6: Sensitive files and misconfigurations"""
        print("\n" + "=" * 70)
        print("  [PHASE 6] SENSITIVE FILES & MISCONFIGURATIONS")
        print("=" * 70)

        result = {'findings': [], 'sensitive_files': []}

        sensitive_paths = [
            '/.env', '/.git/config', '/.svn/entries', '/.DS_Store',
            '/config.php', '/wp-config.php', '/phpinfo.php',
            '/server-status', '/server-info', '/.aws/credentials',
            '/.ssh/authorized_keys', '/backup.sql', '/database.sql',
            '/web.config', '/robots.txt', '/sitemap.xml',
            '/api/swagger.json', '/api-docs', '/graphql.yml',
            '/actuator/env', '/actuator/health', '/trace',
            '/debug/pprof', '/metrics', '/console',
        ]

        for path in sensitive_paths:
            try:
                url = f"{self._resolve_target()}{path}"
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, timeout=3, context=ctx) as resp:
                    if resp.status == 200:
                        body = resp.read().decode('utf-8', errors='ignore')[:200]
                        finding = {
                            'path': path,
                            'status': 200,
                            'size': len(body),
                            'preview': body[:100],
                        }
                        result['sensitive_files'].append(finding)
                        print(f"  [FOUND] {path} -> 200 ({len(body)} bytes)")

                        # Verificar conteudo sensivel
                        if any(s in body.lower() for s in ['password', 'secret', 'apikey', 'token', 'key']):
                            result['findings'].append({
                                'type': 'Sensitive Data Exposure',
                                'severity': 'CRITICAL',
                                'path': path,
                                'details': 'Contains potential secrets',
                            })
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    result['findings'].append({
                        'type': 'Directory Listing Blocked',
                        'severity': 'LOW',
                        'path': path,
                        'details': 'Access denied (403)',
                    })
            except:
                pass

        return result

    def run_full_scan(self, quick: bool = False) -> Dict:
        """Executa scan completo ou rapido"""
        self.start_time = time.time()

        print("\n" + "#" * 70)
        print(f"  COMPLETE VULNERABILITY SCANNER v2.0")
        print(f"  Target: {self.target}")
        print("#" * 70)

        # Executar fases
        self.results['phases']['recon'] = self.phase_recon()

        if not quick:
            self.results['phases']['waf'] = self.phase_waf_detection()
            self.results['phases']['graphql'] = self.phase_graphql_scan()
            self.results['phases']['jwt'] = self.phase_jwt_analysis()

        self.results['phases']['vulns'] = self.phase_vuln_scan()
        self.results['phases']['sensitivity'] = self.phase_sensitivity_scan()

        # Calcular tempo e resumo
        elapsed = time.time() - self.start_time
        total_vulns = 0
        total_critical = 0

        for phase_name, phase_data in self.results['phases'].items():
            if isinstance(phase_data, dict):
                vulns = phase_data.get('vulnerabilities', [])
                findings = phase_data.get('findings', [])
                total_vulns += len(vulns) + len(findings)
                total_critical += len([v for v in vulns if v.get('severity') == 'CRITICAL'])
                total_critical += len([f for f in findings if f.get('severity') == 'CRITICAL'])

        self.results['summary'] = {
            'total_time_seconds': round(elapsed, 2),
            'total_vulnerabilities': total_vulns,
            'total_critical': total_critical,
            'phases_completed': len([p for p in self.results['phases'].values() if 'error' not in p]),
            'phases_total': len(self.results['phases']),
        }

        # Print summary
        print("\n" + "=" * 70)
        print("  SCAN COMPLETE")
        print("=" * 70)
        print(f"  Target: {self.target}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Vulnerabilities: {total_vulns}")
        print(f"  Critical: {total_critical}")
        print(f"  Phases: {self.results['summary']['phases_completed']}/{self.results['summary']['phases_total']}")
        print("=" * 70)

        return self.results

    def save_results(self, output_dir: str = None) -> str:
        """Salva resultados em arquivo JSON"""
        if output_dir is None:
            output_dir = str(Path.home() / 'hardware-bridge' / 'scan_results')

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_target = re.sub(r'[^\w\-]', '_', self.target)
        filename = f"complete_scan_{safe_target}_{timestamp}.json"
        filepath = Path(output_dir) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n  [SAVE] Results saved to: {filepath}")
        return str(filepath)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Complete Vulnerability Scanner v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python complete_scanner.py target.com
  python complete_scanner.py target.com --quick
  python complete_scanner.py target.com --output results.json
  python complete_scanner.py target.com --phase jwt
        """
    )
    parser.add_argument('target', help='Target domain (e.g., example.com)')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick scan (skip JWT/GraphQL)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--phase', '-p',
                        choices=['recon', 'waf', 'graphql', 'jwt', 'vulns', 'sensitivity'],
                        help='Run specific phase only')

    args = parser.parse_args()

    scanner = CompleteScanner(args.target)

    if args.phase:
        # Fase especifica
        phase_methods = {
            'recon': scanner.phase_recon,
            'waf': scanner.phase_waf_detection,
            'graphql': scanner.phase_graphql_scan,
            'jwt': scanner.phase_jwt_analysis,
            'vulns': scanner.phase_vuln_scan,
            'sensitivity': scanner.phase_sensitivity_scan,
        }
        result = phase_methods[args.phase]()
        print(json.dumps(result, indent=2, default=str))
    else:
        # Scan completo
        result = scanner.run_full_scan(quick=args.quick)

    # Salvar resultados
    if args.output:
        scanner.save_results(args.output)
    else:
        scanner.save_results()


if __name__ == "__main__":
    main()
