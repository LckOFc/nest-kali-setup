#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode Integration — Backend Vulnerability Scanner
Interface integrada com o sistema OpenCode
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import re

# Adicionar paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'hardware-bridge' / 'tools'))
sys.path.insert(0, str(Path.home() / '.config' / 'opencode'))

try:
    from vuln_scanner import run_scan, ScanConfig, TargetRecon, VulnerabilityScanner
except ImportError:
    # Fallback para modo standalone
    print("[INFO] Running in standalone mode")
    run_scan = None


class OpenCodeVulnScanner:
    """Integração com OpenCode"""
    
    def __init__(self):
        self.results_dir = Path.home() / 'hardware-bridge' / 'scan_results'
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Sistema de inteligência integrado
        self.intel_sources = {
            'black_hat': self._load_black_hat(),
            'web_search': self._load_web_search(),
        }
    
    def _load_black_hat(self):
        """Carrega sistema black hat intelligence"""
        try:
            from black_hat_intelligence import BlackHatIntelligence
            return BlackHatIntelligence()
        except:
            return None
    
    def _load_web_search(self):
        """Carrega sistema web search"""
        try:
            from web_search import webSearch
            return webSearch
        except:
            return None
    
    def scan(self, target: str, options: dict = None) -> dict:
        """Executa scan completo"""
        if run_scan:
            result = run_scan(target, verbose=True)
        else:
            result = self._fallback_scan(target)
        
        # Adicionar inteligência integrada
        if self.intel_sources['web_search']:
            result['intelligence'] = self._collect_intel(target)
        
        # Salvar resultado
        self._save_result(target, result)
        
        return result
    
    def _fallback_scan(self, target: str) -> dict:
        """Scan fallback quando módulo principal não disponível"""
        import socket
        import urllib.request
        
        result = {
            'target': target,
            'ip': None,
            'technologies': [],
            'endpoints': [],
            'vulnerabilities': [],
            'intelligence': {},
            'scan_time': datetime.now().isoformat()
        }
        
        # Resolver IP
        try:
            result['ip'] = socket.gethostbyname(target)
        except:
            pass
        
        # Detectar tecnologias básicas
        try:
            url = f"http://{target}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                headers = dict(resp.headers)
                body = resp.read().decode('utf-8', errors='ignore')[:10000]
                
                # Detectar tecnologias
                if 'Server' in headers:
                    server = headers['Server'].lower()
                    if 'apache' in server:
                        result['technologies'].append('Apache')
                    elif 'nginx' in server:
                        result['technologies'].append('Nginx')
                    elif 'cloudflare' in server:
                        result['technologies'].append('Cloudflare')
                
                if 'X-Powered-By' in headers:
                    powered = headers['X-Powered-By'].lower()
                    if 'php' in powered:
                        result['technologies'].append('PHP')
                    elif 'asp' in powered:
                        result['technologies'].append('ASP.NET')
                    elif 'express' in powered:
                        result['technologies'].append('Express')
                
                # Detectar CMS
                if '<meta name="generator"' in body:
                    if 'wordpress' in body.lower():
                        result['technologies'].append('WordPress')
                    elif 'joomla' in body.lower():
                        result['technologies'].append('Joomla')
                    elif 'drupal' in body.lower():
                        result['technologies'].append('Drupal')
        except:
            pass
        
        return result
    
    def _collect_intel(self, target: str) -> dict:
        """Coleta inteligência usando sistemas existentes"""
        intel = {
            'cves': [],
            'exploits': [],
            'github': [],
            'discussions': []
        }
        
        # Usar web_search se disponível
        ws = self.intel_sources['web_search']
        if ws:
            try:
                # Buscar CVEs
                cve_results = ws.searchCVE(target)
                intel['cves'] = cve_results.get('results', [])[:5]
                
                # Buscar exploits
                exploit_results = ws.searchExploits(target)
                intel['exploits'] = exploit_results.get('results', [])[:5]
                
                # Buscar no GitHub
                github_results = ws.searchGitHub(target)
                intel['github'] = github_results.get('results', [])[:5]
                
            except Exception as e:
                print(f"  [WARN] Intel collection failed: {e}")
        
        return intel
    
    def _save_result(self, target: str, result: dict):
        """Salva resultado em JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = re.sub(r'[^\w\-]', '_', target)
        filename = f"scan_{safe_name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        result['save_path'] = str(filepath)
        return filepath
    
    def list_results(self) -> list:
        """Lista resultados anteriores"""
        results = []
        for f in sorted(self.results_dir.glob('scan_*.json'), reverse=True):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    results.append({
                        'file': f.name,
                        'target': data.get('target'),
                        'time': data.get('scan_time'),
                        'vulns': len(data.get('vulnerabilities', [])),
                        'critical': len([v for v in data.get('vulnerabilities', []) if v.get('severity') == 'CRITICAL']),
                        'high': len([v for v in data.get('vulnerabilities', []) if v.get('severity') == 'HIGH']),
                    })
            except:
                pass
        return results
    
    def generate_report(self, target: str, format: str = 'markdown') -> str:
        """Gera relatório em markdown"""
        # Carregar resultado mais recente
        safe_name = re.sub(r'[^\w\-]', '_', target)
        results = list(self.results_dir.glob(f'scan_{safe_name}_*.json'))
        
        if not results:
            return f"[[ERROR] No scan results found for {target}]"
        
        latest = results[-1]
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        report = f"""# Security Scan Report — {data.get('target')}

**Scan Time:** {data.get('scan_time')}  
**Target IP:** {data.get('ip', 'Unknown')}  
**Technologies:** {', '.join(data.get('technologies', ['Unknown']))}

---

## Summary

| Metric | Count |
|--------|-------|
| Total Endpoints | {len(data.get('endpoints', []))} |
| Vulnerabilities | {data.get('summary', {}).get('total_vulns', len(data.get('vulnerabilities', [])))} |
| Critical | {data.get('summary', {}).get('critical', 0)} |
| High | {data.get('summary', {}).get('high', 0)} |
| Medium | {data.get('summary', {}).get('medium', 0)} |
| Low | {data.get('summary', {}).get('low', 0)} |

---

## Vulnerabilities Found

"""
        
        vulns = data.get('vulnerabilities', [])
        if vulns:
            for i, vuln in enumerate(vulns, 1):
                report += f"""### {i}. {vuln.get('type', 'Unknown')}

- **Severity:** {vuln.get('severity', 'Unknown')}
- **URL:** {vuln.get('url', 'N/A')}
- **Payload:** `{vuln.get('payload', 'N/A')}`
- **Evidence:** {vuln.get('evidence', 'N/A')}

---

"""
        else:
            report += "*No vulnerabilities found.*\n\n---\n"
        
        # Adicionar inteligência
        intel = data.get('intelligence', {})
        if intel.get('cves') or intel.get('exploits'):
            report += "## Intelligence\n\n"
            
            if intel.get('cves'):
                report += "### CVEs\n\n"
                for cve in intel['cves'][:5]:
                    report += f"- {cve.get('title', cve.get('id', 'Unknown'))}\n"
                report += "\n"
            
            if intel.get('exploits'):
                report += "### Exploits\n\n"
                for exp in intel['exploits'][:5]:
                    report += f"- {exp.get('title', exp.get('id', 'Unknown'))}\n"
                report += "\n"
        
        report += f"""
---

*Report generated by OpenCode Backend Vulnerability Scanner*
*Source: {latest.name}*
"""
        
        return report


# ============================================================
# COMANDOS SLASH
# ============================================================

def cmd_vuln_scan(args: list) -> str:
    """Comando /vuln_scan"""
    if not args:
        return "[ERROR] Usage: /vuln_scan <domain>"
    
    target = args[0]
    options = {}
    
    # Parsear opções
    if '--depth' in args:
        idx = args.index('--depth')
        if idx + 1 < len(args):
            options['depth'] = args[idx + 1]
    
    if '--output' in args:
        idx = args.index('--output')
        if idx + 1 < len(args):
            options['output'] = args[idx + 1]
    
    scanner = OpenCodeVulnScanner()
    result = scanner.scan(target, options)
    
    return f"""[SCAN] Completed for {target}
[RESULT] {len(result.get('vulnerabilities', []))} vulnerabilities found
[SAVE] Results: {result.get('save_path', 'N/A')}
"""


def cmd_vuln_recon(args: list) -> str:
    """Comando /vuln_recon"""
    if not args:
        return "[ERROR] Usage: /vuln_recon <domain>"
    
    target = args[0]
    scanner = OpenCodeVulnScanner()
    result = scanner._fallback_scan(target)
    
    return f"""[RECON] {target}
[IP] {result.get('ip', 'Unknown')}
[TECH] {', '.join(result.get('technologies', ['Unknown']))}
[ENDPOINTS] Scanning...
"""


def cmd_vuln_intel(args: list) -> str:
    """Comando /vuln_intel"""
    if not args:
        return "[ERROR] Usage: /vuln_intel <domain>"
    
    target = args[0]
    scanner = OpenCodeVulnScanner()
    intel = scanner._collect_intel(target)
    
    report = "[INTEL] Intelligence collected:\n\n"
    
    if intel.get('cves'):
        report += f"### CVEs ({len(intel['cves'])})\n"
        for cve in intel['cves'][:5]:
            report += f"- {cve.get('title', cve.get('id', 'Unknown'))}\n"
        report += "\n"
    
    if intel.get('exploits'):
        report += f"### Exploits ({len(intel['exploits'])})\n"
        for exp in intel['exploits'][:5]:
            report += f"- {exp.get('title', exp.get('id', 'Unknown'))}\n"
        report += "\n"
    
    if intel.get('github'):
        report += f"### GitHub Repos ({len(intel['github'])})\n"
        for repo in intel['github'][:5]:
            report += f"- {repo.get('full_name', repo.get('name', 'Unknown'))}\n"
        report += "\n"
    
    if not any([intel.get('cves'), intel.get('exploits'), intel.get('github')]):
        report += "*No intelligence found.*\n"
    
    return report


def cmd_vuln_report(args: list) -> str:
    """Comando /vuln_report"""
    if not args:
        return "[ERROR] Usage: /vuln_report <domain>"
    
    target = args[0]
    scanner = OpenCodeVulnScanner()
    report = scanner.generate_report(target)
    
    return report


def cmd_vuln_list(args: list) -> str:
    """Comando /vuln_list"""
    scanner = OpenCodeVulnScanner()
    results = scanner.list_results()
    
    if not results:
        return "[INFO] No scan results found."
    
    report = "[RESULTS] Recent scans:\n\n"
    report += "| Target | Time | Vulns | Critical | High |\n"
    report += "|--------|------|-------|----------|------|\n"
    
    for r in results[:10]:
        report += f"| {r.get('target', 'N/A')} | {r.get('time', 'N/A')[:10]} | {r.get('vulns', 0)} | {r.get('critical', 0)} | {r.get('high', 0)} |\n"
    
    return report


# ============================================================
# REGISTRO DE COMANDOS
# ============================================================

commands = {
    '/vuln_scan': {
        'description': 'Full vulnerability scan of a target',
        'usage': '/vuln_scan <domain> [--depth shallow|medium|deep]',
        'handler': cmd_vuln_scan,
    },
    '/vuln_recon': {
        'description': 'Reconnaissance only (IP, tech, endpoints)',
        'usage': '/vuln_recon <domain>',
        'handler': cmd_vuln_recon,
    },
    '/vuln_intel': {
        'description': 'Collect intelligence (CVEs, exploits, GitHub)',
        'usage': '/vuln_intel <domain>',
        'handler': cmd_vuln_intel,
    },
    '/vuln_report': {
        'description': 'Generate markdown report from recent scan',
        'usage': '/vuln_report <domain>',
        'handler': cmd_vuln_report,
    },
    '/vuln_list': {
        'description': 'List all scan results',
        'usage': '/vuln_list',
        'handler': cmd_vuln_list,
    },
}


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenCode Backend Vulnerability Scanner')
    parser.add_argument('target', nargs='?', help='Target domain')
    parser.add_argument('--command', '-c', help='Command to execute (scan, recon, intel, report, list)')
    parser.add_argument('--output', '-o', choices=['json', 'markdown', 'text'], default='text')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    scanner = OpenCodeVulnScanner()
    
    if args.command == 'scan' or (not args.command and args.target):
        if args.target:
            result = scanner.scan(args.target)
            if args.output == 'json':
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"[OK] Scan completed: {len(result.get('vulnerabilities', []))} vulns found")
        else:
            print("[ERROR] Please provide a target domain")
    
    elif args.command == 'recon':
        if args.target:
            result = scanner._fallback_scan(args.target)
            print(f"[RECON] {args.target}")
            print(f"  IP: {result.get('ip')}")
            print(f"  Tech: {', '.join(result.get('technologies', []))}")
    
    elif args.command == 'intel':
        if args.target:
            intel = scanner._collect_intel(args.target)
            print(f"[INTEL] {args.target}")
            print(f"  CVEs: {len(intel.get('cves', []))}")
            print(f"  Exploits: {len(intel.get('exploits', []))}")
            print(f"  GitHub: {len(intel.get('github', []))}")
    
    elif args.command == 'report':
        if args.target:
            report = scanner.generate_report(args.target, args.output)
            print(report)
    
    elif args.command == 'list':
        results = scanner.list_results()
        print(f"[RESULTS] {len(results)} scan(s) found")
        for r in results[:5]:
            print(f"  {r.get('target')} - {r.get('vulns')} vulns ({r.get('critical')} critical)")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
