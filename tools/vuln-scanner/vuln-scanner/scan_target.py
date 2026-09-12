"""Test vulnerabilities on ivi-bettx.net"""
import asyncio
import aiohttp
import json

async def scan():
    url = "https://ivi-bettx.net"
    results = {"target": url, "findings": []}
    
    async with aiohttp.ClientSession() as session:
        # Test security headers
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            headers = dict(resp.headers)
            missing = []
            for h in ["X-Content-Type-Options", "X-Frame-Options", "Strict-Transport-Security", 
                      "Content-Security-Policy", "X-XSS-Protection", "Referrer-Policy"]:
                if h.lower() not in headers:
                    missing.append(h)
            if missing:
                results["findings"].append({
                    "severity": "LOW",
                    "type": "info_disclosure",
                    "title": "Missing Security Headers",
                    "details": f"Missing: {', '.join(missing)}"
                })
        
        # Test actuator endpoints
        actuator_paths = ["/actuator", "/actuator/env", "/actuator/health", 
                         "/actuator/info", "/actuator/mappings", "/actuator/beans"]
        for path in actuator_paths:
            try:
                async with session.get(f"{url}{path}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        results["findings"].append({
                            "severity": "HIGH",
                            "type": "info_disclosure",
                            "title": f"Spring Actuator Exposed: {path}",
                            "details": f"Status 200. Content-Type: {resp.headers.get('Content-Type', 'N/A')}"
                        })
            except Exception as e:
                pass
        
        # Test common paths
        test_paths = ["/.git/config", "/.env", "/wp-config.php", "/phpinfo.php",
                     "/admin", "/login", "/api/v1", "/graphql", "/backup.sql"]
        for path in test_paths:
            try:
                async with session.head(f"{url}{path}", timeout=aiohttp.ClientTimeout(total=8),
                                       allow_redirects=False) as resp:
                    if resp.status in [200, 403]:
                        results["findings"].append({
                            "severity": "MEDIUM" if resp.status == 200 else "LOW",
                            "type": "info_disclosure",
                            "title": f"Path accessible: {path}",
                            "details": f"Status: {resp.status}"
                        })
            except Exception:
                pass
    
    return results

if __name__ == "__main__":
    results = asyncio.run(scan())
    print(json.dumps(results, indent=2))
