"""
Report Generator v1 — Gerar relatorios profissionais de pentest
Formatos: Markdown, JSON, ASCII table, resumo executivo
"""

import sys
import os
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ReportGenerator:
    """Generate professional pentest reports"""
    
    SEVERITY_COLORS = {
        'Critical': '🔴 CRITICAL',
        'High': '🟠 HIGH',
        'Medium': '🟡 MEDIUM',
        'Low': '🔵 LOW',
        'Info': '⚪ INFO',
    }
    
    SEVERITY_ORDER = ['Critical', 'High', 'Medium', 'Low', 'Info']
    
    def __init__(self):
        self._reports = {}
    
    def generate(self, report_data: Dict) -> Dict:
        """Generate a complete report from scan data"""
        target = report_data.get('target', 'Unknown')
        generated_at = datetime.now().isoformat()
        
        # Collect all issues
        issues = report_data.get('issues', [])
        requests = report_data.get('requests', [])
        subdomains = report_data.get('subdomains', [])
        endpoints = report_data.get('endpoints', [])
        headers = report_data.get('headers', {})
        
        # Severity breakdown
        severity_counts = {}
        for sev in self.SEVERITY_ORDER:
            severity_counts[sev] = len([i for i in issues if i.get('severity') == sev])
        
        # Type breakdown
        type_counts = {}
        for issue in issues:
            t = issue.get('type', 'Unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Risk score (0-100)
        risk_score = self._calculate_risk_score(severity_counts)
        
        # Executive summary
        executive_summary = self._generate_executive_summary(
            target, issues, severity_counts, risk_score
        )
        
        # Findings detail
        findings_detail = self._generate_findings_detail(issues)
        
        # Recommendations
        recommendations = self._generate_recommendations(issues)
        
        report = {
            'title': f'Pentest Report — {target}',
            'target': target,
            'generated_at': generated_at,
            'risk_score': risk_score,
            'summary': {
                'total_issues': len(issues),
                'critical': severity_counts.get('Critical', 0),
                'high': severity_counts.get('High', 0),
                'medium': severity_counts.get('Medium', 0),
                'low': severity_counts.get('Low', 0),
                'info': severity_counts.get('Info', 0),
                'risk_score': risk_score,
                'subdomains_found': len(subdomains),
                'endpoints_scanned': len(endpoints),
                'requests_logged': len(requests),
            },
            'executive_summary': executive_summary,
            'findings': findings_detail,
            'recommendations': recommendations,
            'raw_data': {
                'issues': issues,
                'subdomains': subdomains[:50],
                'endpoints': endpoints[:100],
                'headers': headers,
            },
        }
        
        return report
    
    def _calculate_risk_score(self, severity_counts: Dict) -> int:
        """Calculate risk score 0-100"""
        weights = {'Critical': 25, 'High': 15, 'Medium': 5, 'Low': 2, 'Info': 0}
        score = sum(severity_counts.get(sev, 0) * w for sev, w in weights.items())
        return min(100, max(0, score))
    
    def _generate_executive_summary(self, target: str, issues: List[Dict],
                                     severity_counts: Dict, risk_score: int) -> str:
        """Generate executive summary text"""
        lines = []
        lines.append(f"Target: {target}")
        lines.append(f"Risk Score: {risk_score}/100")
        lines.append("")
        
        if risk_score >= 80:
            lines.append("⚠️  **CRITICAL RISK** — Immediate action required.")
        elif risk_score >= 60:
            lines.append("🔴 **HIGH RISK** — Significant vulnerabilities found. Priority remediation needed.")
        elif risk_score >= 40:
            lines.append("🟡 **MEDIUM RISK** — Several vulnerabilities found. Remediation recommended.")
        elif risk_score >= 20:
            lines.append("🟢 **LOW RISK** — Minor issues found. Address during regular maintenance.")
        else:
            lines.append("✅ **MINIMAL RISK** — System appears well-configured.")
        
        lines.append("")
        lines.append("**Summary:**")
        lines.append(f"- {severity_counts.get('Critical', 0)} Critical issues requiring immediate attention")
        lines.append(f"- {severity_counts.get('High', 0)} High severity issues")
        lines.append(f"- {severity_counts.get('Medium', 0)} Medium severity issues")
        lines.append(f"- {severity_counts.get('Low', 0)} Low severity issues")
        
        if issues:
            top_issues = sorted(issues, key=lambda x: self.SEVERITY_ORDER.index(x.get('severity', 'Info')) if x.get('severity') in self.SEVERITY_ORDER else 4)[:3]
            lines.append("")
            lines.append("**Top Findings:**")
            for i in top_issues:
                lines.append(f"- [{i.get('severity', 'N/A')}] {i.get('description', i.get('type', 'Unknown'))}")
        
        return '\n'.join(lines)
    
    def _generate_findings_detail(self, issues: List[Dict]) -> List[Dict]:
        """Generate detailed findings"""
        findings = []
        for i, issue in enumerate(sorted(issues, 
                          key=lambda x: self.SEVERITY_ORDER.index(x.get('severity', 'Info')) 
                          if x.get('severity') in self.SEVERITY_ORDER else 4), 1):
            finding = {
                'id': f"F-{i:03d}",
                'type': issue.get('type', 'Unknown'),
                'severity': issue.get('severity', 'Info'),
                'description': issue.get('description', ''),
                'evidence': issue.get('evidence', ''),
                'solution': issue.get('solution', ''),
                'request_id': issue.get('request_id', ''),
            }
            findings.append(finding)
        return findings
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate prioritized recommendations"""
        recs = []
        seen_types = set()
        
        for issue in sorted(issues, key=lambda x: self.SEVERITY_ORDER.index(x.get('severity', 'Info')) 
                           if x.get('severity') in self.SEVERITY_ORDER else 4):
            t = issue.get('type', '')
            if t not in seen_types:
                seen_types.add(t)
                solution = issue.get('solution', 'Review and remediate.')
                recs.append(f"[{issue.get('severity', 'Info')}] {t}: {solution}")
        
        return recs
    
    def to_markdown(self, report: Dict) -> str:
        """Convert report to Markdown format"""
        lines = []
        
        # Header
        lines.append(f"# {report['title']}")
        lines.append("")
        lines.append(f"**Generated:** {report['generated_at']}")
        lines.append(f"**Target:** {report['target']}")
        lines.append(f"**Risk Score:** {report['risk_score']}/100")
        lines.append("")
        
        # Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(report['executive_summary'])
        lines.append("")
        
        # Risk breakdown
        lines.append("## Risk Breakdown")
        lines.append("")
        s = report['summary']
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for sev in self.SEVERITY_ORDER:
            lines.append(f"| {sev} | {s.get(sev.lower(), 0)} |")
        lines.append(f"| **Total** | **{s['total_issues']}** |")
        lines.append("")
        
        # Findings
        lines.append("## Findings")
        lines.append("")
        
        for finding in report['findings']:
            lines.append(f"### {finding['id']} — {finding['type']} [{finding['severity']}]")
            lines.append("")
            lines.append(f"**Description:** {finding['description']}")
            if finding.get('evidence'):
                lines.append(f"**Evidence:** `{finding['evidence'][:200]}`")
            if finding.get('solution'):
                lines.append(f"**Solution:** {finding['solution']}")
            lines.append("")
        
        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        for i, rec in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        
        # Raw data
        lines.append("## Raw Data")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(report.get('raw_data', {}), indent=2, default=str))
        lines.append("```")
        
        return '\n'.join(lines)
    
    def to_json(self, report: Dict, pretty: bool = True) -> str:
        """Convert report to JSON"""
        if pretty:
            return json.dumps(report, indent=2, ensure_ascii=False, default=str)
        return json.dumps(report, ensure_ascii=False, default=str)
    
    def to_ascii_table(self, report: Dict) -> str:
        """Convert report to ASCII table format"""
        lines = []
        
        lines.append("=" * 70)
        lines.append(f"  {report['title']}")
        lines.append(f"  Generated: {report['generated_at']}")
        lines.append(f"  Target: {report['target']}")
        lines.append(f"  Risk Score: {report['risk_score']}/100")
        lines.append("=" * 70)
        lines.append("")
        
        # Summary table
        lines.append("RISK BREAKDOWN:")
        lines.append("-" * 40)
        s = report['summary']
        lines.append(f"  Critical:  {s.get('critical', 0)}")
        lines.append(f"  High:      {s.get('high', 0)}")
        lines.append(f"  Medium:    {s.get('medium', 0)}")
        lines.append(f"  Low:       {s.get('low', 0)}")
        lines.append(f"  Info:      {s.get('info', 0)}")
        lines.append(f"  Total:     {s['total_issues']}")
        lines.append("")
        
        # Findings
        lines.append("FINDINGS:")
        lines.append("-" * 40)
        for finding in report['findings'][:20]:
            icon = {'Critical': '💀', 'High': '🔴', 'Medium': '🟡', 'Low': '🔵'}.get(finding['severity'], '⚪')
            lines.append(f"  {icon} [{finding['severity']}] {finding['id']} — {finding['type']}")
            if finding.get('description'):
                desc = finding['description'][:60]
                lines.append(f"     {desc}{'...' if len(finding['description']) > 60 else ''}")
        lines.append("")
        
        # Recommendations
        lines.append("RECOMMENDATIONS:")
        lines.append("-" * 40)
        for i, rec in enumerate(report['recommendations'][:10], 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")
        
        return '\n'.join(lines)
    
    def save_report(self, report: Dict, filepath: str, fmt: str = 'auto') -> str:
        """Save report to file"""
        if fmt == 'auto':
            if filepath.endswith('.md'):
                fmt = 'markdown'
            elif filepath.endswith('.json'):
                fmt = 'json'
            elif filepath.endswith('.txt'):
                fmt = 'ascii'
            else:
                fmt = 'markdown'
        
        content = {
            'markdown': self.to_markdown,
            'json': self.to_json,
            'ascii': self.to_ascii_table,
        }[fmt](report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath


# =========================================================================
# CLI Entry
# =========================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Report Generator v1 — Relatorios profissionais de pentest')
    parser.add_argument('--input', '-i', help='Input JSON file with scan results')
    parser.add_argument('--target', '-t', help='Target domain name')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--format', '-f', choices=['markdown', 'json', 'ascii'], default='markdown', help='Output format')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    parser.add_argument('--example', action='store_true', help='Show example input')
    
    args = parser.parse_args()
    
    gen = ReportGenerator()
    
    if args.example:
        example = {
            "target": "example.com",
            "issues": [
                {"type": "SQLi", "severity": "Critical", "description": "SQL injection in login parameter", "evidence": "' OR 1=1--", "solution": "Use parameterized queries"},
                {"type": "XSS", "severity": "High", "description": "Reflected XSS in search", "evidence": "<script>alert(1)</script>", "solution": "Sanitize input"},
                {"type": "Missing_Headers", "severity": "Medium", "description": "Missing security headers", "evidence": "X-Frame-Options, HSTS", "solution": "Add security headers"},
            ],
            "subdomains": ["www", "api", "admin", "staging"],
            "endpoints": ["/login", "/api/users", "/admin"],
            "headers": {"Server": "nginx", "X-Powered-By": "PHP/8.1"}
        }
        print(json.dumps(example, indent=2))
        sys.exit(0)
    
    # Read input data
    if args.stdin:
        import sys as _sys
        data = json.loads(_sys.stdin.read())
    elif args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif args.target:
        # Generate minimal report from target name
        data = {"target": args.target, "issues": [], "subdomains": [], "endpoints": [], "headers": {}}
    else:
        print("""
Report Generator v1 — Relatorios profissionais de pentest
Uso:
  python report_generator.py --input scan_results.json
  python report_generator.py --input scan_results.json --format json -o report.json
  python report_generator.py --target example.com -o report.md
  echo '{"target":"x","issues":[]}' | python report_generator.py --stdin -o report.md
  python report_generator.py --example
""")
        sys.exit(0)
    
    # Ensure target is set
    if 'target' not in data:
        data['target'] = args.target or 'unknown'
    
    # Generate report
    report = gen.generate(data)
    
    # Output
    if args.output:
        filepath = gen.save_report(report, args.output, args.format)
        print(f"[+] Report saved: {filepath}")
    else:
        output = {
            'markdown': gen.to_markdown,
            'json': gen.to_json,
            'ascii': gen.to_ascii_table,
        }[args.format](report)
        print(output)
    
    # Also print summary to stderr
    print(f"\n[+] Risk Score: {report['risk_score']}/100", file=sys.stderr)
    print(f"[+] Issues: {report['summary']['total_issues']}", file=sys.stderr)


if __name__ == '__main__':
    main()
