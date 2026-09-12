"""
Orquestrador Unificado — Modo 4070 APEX
Integra todas as ferramentas: VulnScanner, Burp Suite, DarkWeb Intel, TorWebFetch
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class Orchestrator:
    """Orquestrador unificado para todas as ferramentas de segurança."""
    
    def __init__(self, target: str):
        self.target = target
        self.start_time = time.time()
        self.results: Dict[str, Any] = {
            "target": target,
            "start_time": datetime.now().isoformat(),
            "tools": {},
            "correlated_findings": [],
            "summary": {},
        }
    
    async def run_full_scan(self) -> Dict[str, Any]:
        """Executa scan completo com todas as ferramentas."""
        print("=" * 60)
        print("ORQUESTRADOR UNIFICADO — MODO 4070 APEX")
        print("=" * 60)
        print(f"\nTarget: {self.target}")
        print()
        
        # Run all scanners in parallel
        tasks = [
            self._run_vuln_scanner(),
            self._run_darkweb_intel(),
            self._run_tor_webfetch(),
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Correlate findings
        self._correlate_findings()
        
        # Generate summary
        self.results["summary"] = self._generate_summary()
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration_seconds"] = time.time() - self.start_time
        
        return self.results
    
    async def _run_vuln_scanner(self):
        """Run VulnScanner (passive)."""
        print("[1/3] Running VulnScanner (passive)...")
        try:
            # Add vuln-scanner to path
            vs_path = Path(__file__).parent.parent / "vuln-scanner"
            if str(vs_path) not in sys.path:
                sys.path.insert(0, str(vs_path))
            
            from vuln_scanner import VulnScanner
            
            scanner = VulnScanner(concurrency=5)
            scan_results = await scanner.scan(self.target)
            
            self.results["tools"]["vuln_scanner"] = {
                "status": "completed",
                "findings_count": len(scan_results.findings),
                "findings": [f.to_dict() for f in scan_results.findings],
            }
            print(f"  -> {len(scan_results.findings)} findings")
        except Exception as e:
            print(f"  -> Error: {e}")
            self.results["tools"]["vuln_scanner"] = {"status": "error", "error": str(e)}
    
    async def _run_darkweb_intel(self):
        """Run DarkWeb Intel analysis."""
        print("[2/3] Running DarkWeb Intel...")
        try:
            # Add darkweb-intel to path
            dwi_path = Path(__file__).parent.parent / "darkweb-intel"
            if str(dwi_path) not in sys.path:
                sys.path.insert(0, str(dwi_path))
            
            from darkweb_intel import DarkWebIntelligence
            
            intel = DarkWebIntelligence()
            
            # Analyze target
            analysis = await intel.analyze_threat(self.target)
            
            # Search for related threats
            search_items = await intel.search("ransomware")
            
            self.results["tools"]["darkweb_intel"] = {
                "status": "completed",
                "analysis": analysis,
                "search_results_count": len(search_items),
            }
            print(f"  -> Threat analysis complete")
        except Exception as e:
            print(f"  -> Error: {e}")
            self.results["tools"]["darkweb_intel"] = {"status": "error", "error": str(e)}
    
    async def _run_tor_webfetch(self):
        """Run TorWebFetch for secure HTTP requests."""
        print("[3/3] Running TorWebFetch...")
        try:
            # Add tor-webfetch to path
            twf_path = Path(__file__).parent.parent / "tor-webfetch"
            if str(twf_path) not in sys.path:
                sys.path.insert(0, str(twf_path))
            
            from tor_webfetch import TorWebFetch, ProtectionLayer
            
            fetcher = TorWebFetch(level=ProtectionLayer.APEX)
            
            # Fetch target
            result = await fetcher.fetch(self.target)
            
            self.results["tools"]["tor_webfetch"] = {
                "status": "completed" if result.success else "failed",
                "status_code": result.status_code,
                "protection_level": result.protection_level,
                "fingerprint": result.fingerprint,
            }
            print(f"  -> Status: {result.status_code}")
        except Exception as e:
            print(f"  -> Error: {e}")
            self.results["tools"]["tor_webfetch"] = {"status": "error", "error": str(e)}
    
    def _correlate_findings(self):
        """Correlate findings from different tools."""
        print("\nCorrelating findings...")
        
        # Collect all findings
        all_findings = []
        
        # From VulnScanner
        vs_findings = self.results.get("tools", {}).get("vuln_scanner", {}).get("findings", [])
        for f in vs_findings:
            f["source"] = "vuln_scanner"
            all_findings.append(f)
        
        # From DarkWeb Intel
        dwi_analysis = self.results.get("tools", {}).get("darkweb_intel", {}).get("analysis", {})
        if dwi_analysis.get("matches"):
            for match in dwi_analysis["matches"]:
                match["source"] = "darkweb_intel"
                all_findings.append(match)
        
        # Correlate by type
        correlated = {}
        for f in all_findings:
            ftype = f.get("type", f.get("match", "unknown"))
            if ftype not in correlated:
                correlated[ftype] = []
            correlated[ftype].append(f.get("source", "unknown"))
        
        # Mark high-confidence findings (detected by multiple tools)
        for ftype, sources in correlated.items():
            if len(sources) > 1:
                self.results["correlated_findings"].append({
                    "type": ftype,
                    "sources": sources,
                    "confidence": "high" if len(sources) >= 2 else "medium",
                })
        
        print(f"  -> {len(self.results['correlated_findings'])} correlated findings")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate executive summary."""
        total_findings = 0
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        # Count from VulnScanner
        vs_data = self.results.get("tools", {}).get("vuln_scanner", {})
        for f in vs_data.get("findings", []):
            total_findings += 1
            sev = f.get("severity", "low").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
        
        # Determine overall risk
        if severity_counts["critical"] > 0:
            risk_level = "CRITICAL"
        elif severity_counts["high"] > 0:
            risk_level = "HIGH"
        elif severity_counts["medium"] > 0:
            risk_level = "MEDIUM"
        elif total_findings > 0:
            risk_level = "LOW"
        else:
            risk_level = "NONE"
        
        return {
            "total_findings": total_findings,
            "by_severity": severity_counts,
            "risk_level": risk_level,
            "tools_used": list(self.results.get("tools", {}).keys()),
            "correlated_findings": len(self.results.get("correlated_findings", [])),
        }
    
    def export_report(self, output_dir: str = "."):
        """Export comprehensive report."""
        output_path = Path(output_dir) / f"report_{self.target.replace('https://', '').replace('http://', '')}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nReport saved to: {output_path}")
        return output_path


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Orquestrador Unificado — Modo 4070")
    parser.add_argument("target", help="Target URL (e.g., https://example.com)")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    orchestrator = Orchestrator(args.target)
    results = await orchestrator.run_full_scan()
    
    # Export report
    output_dir = args.output or "."
    orchestrator.export_report(output_dir)
    
    # Print summary
    summary = results.get("summary", {})
    print()
    print("=" * 60)
    print("EXECUTIVE SUMMARY")
    print("=" * 60)
    print(f"Target: {args.target}")
    print(f"Total Findings: {summary.get('total_findings', 0)}")
    print(f"Risk Level: {summary.get('risk_level', 'UNKNOWN')}")
    print(f"Tools Used: {', '.join(summary.get('tools_used', []))}")
    print(f"Correlated Findings: {summary.get('correlated_findings', 0)}")
    print()
    print("Severity Breakdown:")
    for sev, count in summary.get("by_severity", {}).items():
        if count > 0:
            print(f"  {sev.upper()}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
