"""Advanced vulnerability testing for ivi-bettx.net"""
import asyncio
import aiohttp
import json
import re

async def advanced_test():
    url = "https://ivi-bettx.net"
    findings = []
    
    async with aiohttp.ClientSession() as session:
        # 1. Check all actuator endpoints with different methods
        print("=== Testing Spring Actuator Endpoints ===")
        actuator_paths = [
            "/actuator", "/actuator/env", "/actuator/health", "/actuator/info",
            "/actuator/mappings", "/actuator/beans", "/actuator/configprops",
            "/actuator/conditions", "/actuator/loggers", "/actuator/threaddump",
            "/actuator/trace", "/actuator/heapdump", "/actuator/jolokia",
            "/actuator/liquibase", "/actuator/shutdown",
        ]
        
        for path in actuator_paths:
            try:
                async with session.get(f"{url}{path}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()
                    content_type = resp.headers.get("Content-Type", "")
                    
                    # Check if response is actual JSON (actuator) or HTML (SPA fallback)
                    if "application/json" in content_type or (content.strip().startswith("{") and "\"_links\"" in content):
                        findings.append({
                            "severity": "CRITICAL",
                            "type": "info_disclosure",
                            "title": f"Actuator endpoint exposed: {path}",
                            "details": f"JSON response detected - possible info disclosure",
                            "endpoint": f"{url}{path}"
                        })
                        print(f"  [CRITICAL] {path} - JSON response!")
                    elif resp.status == 200 and len(content) < 1000:
                        findings.append({
                            "severity": "MEDIUM",
                            "type": "info_disclosure",
                            "title": f"Actuator endpoint accessible: {path}",
                            "details": f"Status 200 but may be SPA fallback",
                            "endpoint": f"{url}{path}"
                        })
                        print(f"  [MEDIUM] {path} - 200 OK ({len(content)} bytes)")
                    else:
                        print(f"  [-] {path} - {resp.status}")
            except Exception as e:
                print(f"  [ERR] {path}: {str(e)[:50]}")
        
        # 2. Test for common API endpoints
        print("\n=== Testing API Endpoints ===")
        api_paths = [
            "/api/v1/users", "/api/v1/user", "/api/users", "/api/user",
            "/api/admin", "/api/config", "/api/settings",
            "/swagger-ui.html", "/swagger-resources", "/v2/api-docs",
            "/api-docs", "/graphql", "/api/graphql",
        ]
        
        for path in api_paths:
            try:
                async with session.get(f"{url}{path}", timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if len(content) > 100 and "application/json" in resp.headers.get("Content-Type", ""):
                            findings.append({
                                "severity": "HIGH",
                                "type": "info_disclosure",
                                "title": f"API endpoint exposed: {path}",
                                "details": f"JSON API response detected",
                                "endpoint": f"{url}{path}"
                            })
                            print(f"  [HIGH] {path} - JSON API!")
                        elif resp.status == 200:
                            print(f"  [INFO] {path} - 200 OK ({len(content)} bytes)")
                    elif resp.status == 403:
                        print(f"  [BLOCKED] {path}")
                    else:
                        print(f"  [-] {path} - {resp.status}")
            except Exception as e:
                pass
        
        # 3. Test for backup/config files
        print("\n=== Testing Sensitive Files ===")
        sensitive_paths = [
            "/backup.sql", "/database.sql", "/dump.sql", "/db.sql",
            "/config.json", "/config.yml", "/config.yaml",
            "/.git/HEAD", "/.git/config", "/.svn/entries",
            "/web.config", "/application.yml", "/application.properties",
            "/robots.txt", "/sitemap.xml", "/.well-known/security.txt",
        ]
        
        for path in sensitive_paths:
            try:
                async with session.head(f"{url}{path}", timeout=aiohttp.ClientTimeout(total=5),
                                       allow_redirects=False) as resp:
                    if resp.status == 200:
                        findings.append({
                            "severity": "HIGH",
                            "type": "info_disclosure",
                            "title": f"Sensitive file accessible: {path}",
                            "details": f"Status 200 - file may contain sensitive data",
                            "endpoint": f"{url}{path}"
                        })
                        print(f"  [HIGH] {path} - 200 OK!")
                    elif resp.status in [301, 302]:
                        print(f"  [REDIR] {path} -> {resp.headers.get('Location', 'N/A')}")
                    elif resp.status == 403:
                        print(f"  [BLOCKED] {path}")
            except Exception:
                pass
        
        # 4. Test headers and server info
        print("\n=== Testing Server Headers ===")
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                headers = dict(resp.headers)
                
                # Check for information leakage
                risky_headers = ["X-Powered-By", "Server", "X-AspNet-Version", "X-AspNetMvc-Version"]
                for h in risky_headers:
                    if h in headers:
                        findings.append({
                            "severity": "LOW",
                            "type": "info_disclosure",
                            "title": f"Server info leakage: {h}",
                            "details": f"{h}: {headers[h]}",
                            "endpoint": url
                        })
                        print(f"  [LOW] {h}: {headers[h]}")
                
                # Check missing security headers
                missing = []
                for h in ["X-Content-Type-Options", "X-Frame-Options", "Strict-Transport-Security",
                         "Content-Security-Policy", "X-XSS-Protection", "Referrer-Policy"]:
                    if h.lower() not in headers:
                        missing.append(h)
                
                if missing:
                    findings.append({
                        "severity": "LOW",
                        "type": "misconfiguration",
                        "title": "Missing Security Headers",
                        "details": f"Missing: {', '.join(missing)}",
                        "endpoint": url
                    })
        except Exception as e:
            print(f"  [ERR] Header test: {e}")
    
    return findings

if __name__ == "__main__":
    findings = asyncio.run(advanced_test())
    print(f"\n=== SUMMARY ===")
    print(f"Total findings: {len(findings)}")
    
    # Group by severity
    by_severity = {}
    for f in findings:
        sev = f["severity"]
        if sev not in by_severity:
            by_severity[sev] = []
        by_severity[sev].append(f["title"])
    
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if sev in by_severity:
            print(f"\n{sev}:")
            for title in by_severity[sev]:
                print(f"  - {title}")
    
    # Save report
    report = {
        "target": "https://ivi-bettx.net",
        "scan_date": "2026-09-11",
        "findings_count": len(findings),
        "findings": findings
    }
    
    with open("scan_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: scan_report.json")
