#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mass Scanner — Orquestra scans multi-alvo com pipeline completo
Executa recon + vuln + exploit + extracao em lote
"""

import sys
import json
import time
import asyncio
import ssl
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class MassScanner:
    """Orquestrador de scans multi-alvo"""

    def __init__(self, targets: List[str], output_dir: str = None):
        self.targets = targets
        self.output_dir = Path(output_dir or str(Path.home() / "hardware-bridge" / "scan_results"))
        self.results: Dict[str, Dict] = {}
        self.errors: List[Dict] = []

    def _resolve_target(self, target: str) -> str:
        """Normalize target to URL"""
        target = target.strip().rstrip('/')
        if not target.startswith('http'):
            target = f"https://{target}"
        return target

    def run_recon(self, target: str) -> Dict:
        """Reconhecimento basico"""
        import socket
        import ssl as ssl_mod

        result = {'target': target, 'ip': None, 'ports': {}, 'headers': {}}
        domain = target.replace('https://', '').replace('http://', '')

        try:
            ip = socket.gethostbyname(domain)
            result['ip'] = ip
        except:
            pass

        ctx = ssl_mod.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            req = urllib.request.Request(target, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                result['headers'] = dict(resp.headers)
                result['status'] = resp.status
                body = resp.read().decode('utf-8', errors='ignore')[:10000]
                result['body_preview'] = body[:500]

                # Detect tech
                techs = []
                h = json.dumps(result['headers']).lower()
                b = body.lower()
                if 'cloudflare' in h:
                    techs.append('Cloudflare')
                if 'server' in result['headers']:
                    srv = result['headers']['Server'].lower()
                    if 'nginx' in srv:
                        techs.append('Nginx')
                    elif 'apache' in srv:
                        techs.append('Apache')
                if 'react' in b:
                    techs.append('React')
                if '__next_data__' in b:
                    techs.append('Next.js')
                if 'ruby' in h or 'x-request-id' in h:
                    techs.append('Rails')
                result['technologies'] = techs
        except Exception as e:
            result['error'] = str(e)

        return result

    def run_vuln_scan(self, target: str) -> Dict:
        """Vulnerability scan basico"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from vuln_scanner import run_scan
            return run_scan(target.replace('https://', '').replace('http://', ''), verbose=False)
        except Exception as e:
            return {'error': str(e), 'target': target}

    def run_jwt_analysis(self, target: str) -> Dict:
        """JWT analysis"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from jwt_analyzer import JWTAnalyzer
            analyzer = JWTAnalyzer(target)
            return analyzer.run_full_analysis()
        except Exception as e:
            return {'error': str(e), 'target': target}

    def run_exploit(self, target: str, report: Dict) -> Dict:
        """Exploit execution"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from exploit_executor import ExploitExecutor
            executor = ExploitExecutor(target)
            return executor.run_all_exploits(report)
        except Exception as e:
            return {'error': str(e), 'target': target}

    def run_extraction(self, target: str, report: Dict) -> Dict:
        """Data extraction"""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from data_extractor import DataExtractor
            extractor = DataExtractor(target)
            return extractor.run_full_extraction(report)
        except Exception as e:
            return {'error': str(e), 'target': target}

    def run_mass_scan(self, targets: List[str] = None,
                      phases: List[str] = None) -> Dict:
        """Executa scan completo em multiplas fases"""
        targets = targets or self.targets
        if phases is None:
            phases = ['recon', 'vuln', 'jwt', 'exploit', 'extract']

        print("\n" + "=" * 70)
        print(f"  MASS SCANNER — {len(targets)} target(s)")
        print("=" * 70)

        start_time = time.time()
        all_results = {
            'targets': targets,
            'phases': phases,
            'timestamp': datetime.now().isoformat(),
            'results': {},
            'summary': {'total_targets': len(targets), 'errors': 0},
        }

        for i, target in enumerate(targets, 1):
            print(f"\n{'='*50}")
            print(f"  [{i}/{len(targets)}] Scanning: {target}")
            print(f"{'='*50}")

            target_results = {}
            base_domain = target.replace('https://', '').replace('http://', '')

            try:
                # Phase 1: Recon
                if 'recon' in phases:
                    print(f"  [RECON] {target}...")
                    recon = self.run_recon(target)
                    target_results['recon'] = recon
                    print(f"    IP: {recon.get('ip')} | Tech: {recon.get('technologies', [])}")

                # Phase 2: Vulnerability scan
                if 'vuln' in phases:
                    print(f"  [VULN] {target}...")
                    vuln = self.run_vuln_scan(target)
                    target_results['vulnerabilities'] = vuln
                    total_vulns = vuln.get('summary', {}).get('total_vulns',
                                                               len(vuln.get('vulnerabilities', [])))
                    print(f"    Found: {total_vulns} vulnerabilities")

                # Phase 3: JWT analysis
                if 'jwt' in phases:
                    print(f"  [JWT] {target}...")
                    jwt = self.run_jwt_analysis(target)
                    target_results['jwt'] = jwt
                    print(f"    Tokens: {jwt.get('tokens_found', 0)}")

                # Phase 4: Exploit (requires vuln report)
                if 'exploit' in phases and target_results.get('vulnerabilities'):
                    print(f"  [EXPLOIT] {target}...")
                    exploit = self.run_exploit(target, target_results['vulnerabilities'])
                    target_results['exploit'] = exploit
                    successful = exploit.get('summary', {}).get('successful', 0)
                    print(f"    Exploits successful: {successful}")

                # Phase 5: Data extraction
                if 'extract' in phases:
                    print(f"  [EXTRACT] {target}...")
                    extract = self.run_extraction(target, target_results)
                    target_results['extraction'] = extract
                    print(f"    Data extracted: {extract.get('summary', {}).get('total_extracted', 0)}")

                # Save individual result
                self.results[target] = target_results
                self._save_result(base_domain, target_results)

            except Exception as e:
                print(f"  [ERROR] {target}: {e}")
                self.errors.append({'target': target, 'error': str(e)})
                all_results['summary']['errors'] += 1

        elapsed = time.time() - start_time

        # Final summary
        total_vulns = sum(
            len(r.get('vulnerabilities', {}).get('vulnerabilities', []))
            for r in self.results.values()
        )
        total_critical = sum(
            r.get('vulnerabilities', {}).get('summary', {}).get('critical', 0)
            for r in self.results.values()
        )
        total_exploits = sum(
            r.get('exploit', {}).get('summary', {}).get('successful', 0)
            for r in self.results.values()
        )

        all_results['results'] = self.results
        all_results['summary']['elapsed_seconds'] = round(elapsed, 2)
        all_results['summary']['total_vulnerabilities'] = total_vulns
        all_results['summary']['total_critical'] = total_critical
        all_results['summary']['total_exploits'] = total_exploits

        print("\n" + "=" * 70)
        print("  MASS SCAN COMPLETE")
        print("=" * 70)
        print(f"  Targets: {len(targets)}")
        print(f"  Elapsed: {elapsed:.1f}s")
        print(f"  Vulnerabilities: {total_vulns}")
        print(f"  Critical: {total_critical}")
        print(f"  Exploits: {total_exploits}")
        print(f"  Errors: {len(self.errors)}")

        # Save consolidated report
        self._save_consolidated(all_results)

        return all_results

    def _save_result(self, domain: str, data: Dict):
        """Save individual target result"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"mass_{domain}_{timestamp}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"    Saved: {filepath}")

    def _save_consolidated(self, data: Dict):
        """Save consolidated report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"mass_scan_consolidated_{timestamp}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"    Consolidated: {filepath}")

    def print_summary(self):
        """Print summary of all results"""
        print("\n" + "=" * 70)
        print("  SCAN SUMMARY")
        print("=" * 70)

        for target, results in self.results.items():
            vulns = results.get('vulnerabilities', {})
            exploits = results.get('exploit', {})
            extract = results.get('extraction', {})

            vuln_count = vulns.get('summary', {}).get('total_vulns',
                                                       len(vulns.get('vulnerabilities', [])))
            critical = vulns.get('summary', {}).get('critical', 0)
            exploit_count = exploits.get('summary', {}).get('successful', 0)

            print(f"\n  {target}")
            print(f"    Vulns: {vuln_count} | Critical: {critical} | Exploits: {exploit_count}")

        if self.errors:
            print(f"\n  ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"    - {err['target']}: {err['error'][:50]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Mass Scanner — Multi-target pipeline')
    parser.add_argument('targets', nargs='+', help='Target domains')
    parser.add_argument('--phases', '-p', nargs='*',
                        default=['recon', 'vuln', 'jwt', 'exploit', 'extract'],
                        help='Phases to run')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--summary', '-s', action='store_true', help='Print summary only')

    args = parser.parse_args()

    scanner = MassScanner(args.targets, output_dir=args.output)

    if args.summary:
        # Just load and print existing results
        print(json.dumps(scanner.results, indent=2, default=str))
    else:
        result = scanner.run_mass_scan(args.targets, args.phases)
        scanner.print_summary()

        if args.output:
            print(f"\n[SAVE] All results saved to {args.output}")


if __name__ == "__main__":
    main()
