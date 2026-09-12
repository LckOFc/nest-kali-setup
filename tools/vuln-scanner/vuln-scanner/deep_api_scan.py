"""Deep API discovery for ivi-bettx.net"""
import asyncio
import aiohttp
import json
import re

async def deep_api_scan():
    base = "https://ivi-bettx.net"
    findings = []
    
    # Comprehensive API paths to test
    api_paths = [
        # Base API
        "/api",
        "/api/v1",
        "/api/v2",
        "/api/v3",
        
        # Authentication
        "/api/v1/auth",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/signup",
        "/api/v1/auth/logout",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/refresh",
        "/api/v1/auth/verify",
        
        # Users
        "/api/v1/users",
        "/api/v1/user",
        "/api/v1/user/profile",
        "/api/v1/user/account",
        "/api/v1/user/settings",
        "/api/v1/user/me",
        
        # Betting
        "/api/v1/betting",
        "/api/v1/bets",
        "/api/v1/bet",
        "/api/v1/sports",
        "/api/v1/sports/events",
        "/api/v1/sports/leagues",
        "/api/v1/sports/teams",
        "/api/v1/odds",
        "/api/v1/live",
        "/api/v1/live-betting",
        
        # Casino
        "/api/v1/casino",
        "/api/v1/casino/games",
        "/api/v1/casino/slots",
        "/api/v1/casino/roulette",
        "/api/v1/casino/blackjack",
        
        # Payment
        "/api/v1/payment",
        "/api/v1/payments",
        "/api/v1/wallet",
        "/api/v1/deposit",
        "/api/v1/withdraw",
        "/api/v1/balance",
        "/api/v1/transactions",
        
        # Account
        "/api/v1/account",
        "/api/v1/account/profile",
        "/api/v1/account/settings",
        "/api/v1/account/security",
        
        # Admin (if exposed)
        "/api/v1/admin",
        "/api/v1/admin/users",
        "/api/v1/admin/settings",
        
        # GraphQL
        "/graphql",
        "/api/graphql",
        
        # Documentation
        "/swagger-ui.html",
        "/swagger-ui/",
        "/api-docs",
        "/v2/api-docs",
        "/v3/api-docs",
        "/openapi.json",
        "/openapi.yml",
        
        # Actuator (Spring Boot)
        "/actuator",
        "/actuator/health",
        "/actuator/info",
        "/actuator/env",
        "/actuator/mappings",
        "/actuator/beans",
        "/actuator/configprops",
        "/actuator/trace",
        "/actuator/loggers",
        "/actuator/threaddump",
        "/actuator/heapdump",
        
        # H2 Console
        "/h2-console",
        "/h2",
        "/console",
        
        # Debug
        "/debug",
        "/trace",
        "/metrics",
        "/prometheus",
        
        # Common info
        "/config",
        "/configuration",
        "/settings",
        "/status",
        "/version",
        "/health",
        "/ping",
        "/info",
        "/about",
    ]
    
    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("DEEP API DISCOVERY — ivi-bettx.net")
        print("=" * 60)
        print()
        
        json_endpoints = []
        html_endpoints = []
        redirect_endpoints = []
        
        for path in api_paths:
            try:
                async with session.get(f"{base}{path}", timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    status = resp.status
                    
                    if "json" in content_type:
                        body = await resp.text()
                        json_endpoints.append({
                            "path": path,
                            "status": status,
                            "content": body[:300],
                            "size": len(body)
                        })
                        print(f"[JSON] {path} ({status})")
                    elif status == 200 and ("html" in content_type or "text" in content_type):
                        html_endpoints.append(path)
                        print(f"[HTML] {path} ({status})")
                    elif status in [301, 302]:
                        location = resp.headers.get("Location", "")
                        redirect_endpoints.append({"path": path, "location": location})
                        print(f"[REDIR] {path} -> {location}")
                    elif status in [401, 403]:
                        print(f"[AUTH] {path} ({status})")
                    else:
                        print(f"[{status}] {path}")
                        
            except asyncio.TimeoutError:
                print(f"[TIMEOUT] {path}")
            except Exception as e:
                print(f"[ERR] {path}: {str(e)[:40]}")
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"JSON endpoints found: {len(json_endpoints)}")
    print(f"HTML endpoints found: {len(html_endpoints)}")
    print(f"Redirects found: {len(redirect_endpoints)}")
    
    # Analyze JSON endpoints
    print()
    print("=" * 60)
    print("JSON ENDPOINT DETAILS")
    print("=" * 60)
    
    for ep in json_endpoints:
        print(f"\n{ep['path']}:")
        print(f"  Status: {ep['status']}")
        print(f"  Size: {ep['size']} bytes")
        print(f"  Content: {ep['content'][:200]}...")
        
        # Check for sensitive data patterns
        if any(p in ep['content'].lower() for p in ['password', 'secret', 'token', 'key', 'admin', 'root']):
            print("  [!] POSSIBLE SENSITIVE DATA DETECTED!")
    
    return {
        "json_endpoints": json_endpoints,
        "html_endpoints": html_endpoints,
        "redirects": redirect_endpoints,
        "total_tested": len(api_paths)
    }

async def test_graphql():
    """Test GraphQL endpoint specifically"""
    base = "https://ivi-bettx.net"
    
    print()
    print("=" * 60)
    print("GRAPHQL TESTING")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test introspection
        introspection_query = {
            "query": "{ __schema { types { name } } }"
        }
        
        try:
            async with session.post(
                f"{base}/graphql",
                json=introspection_query,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                content = await resp.text()
                print(f"GraphQL Introspection: {resp.status}")
                if resp.status == 200 and "introspection" in content.lower():
                    print("  [!] GraphQL introspection ENABLED - schema exposure risk")
                    print(f"  Response: {content[:300]}...")
                elif "json" in resp.headers.get("Content-Type", ""):
                    print(f"  Response: {content[:200]}...")
                else:
                    print(f"  Response is HTML (SPA fallback)")
        except Exception as e:
            print(f"GraphQL error: {e}")
        
        # Test common queries
        test_queries = [
            {"query": "{ users { id username } }"},
            {"query": "{ user { id email password } }"},
            {"query": "{ betting { id odds } }"},
        ]
        
        for query in test_queries:
            try:
                async with session.post(
                    f"{base}/graphql",
                    json=query,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    content = await resp.text()
                    if resp.status == 200 and "json" in resp.headers.get("Content-Type", ""):
                        print(f"Query {list(query.keys())[0]}: {resp.status} - {content[:100]}...")
            except:
                pass

async def check_subdomains():
    """Check for related subdomains"""
    print()
    print("=" * 60)
    print("SUBDOMAIN & RELATED DOMAINS")
    print("=" * 60)
    
    domains = [
        "ivi-bettx.net",
        "ivibet.com",
        "www.ivibet.com",
        "api.ivibet.com",
        "app.ivibet.com",
        "bet.ivibet.com",
        "live.ivibet.com",
        "casino.ivibet.com",
        "sports.ivibet.com",
        "payment.ivibet.com",
        "admin.ivibet.com",
    ]
    
    async with aiohttp.ClientSession() as session:
        for domain in domains:
            try:
                url = f"https://{domain}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=False) as resp:
                    print(f"[{resp.status}] {domain}")
                    if resp.status == 200:
                        location = resp.headers.get("Location", "")
                        if location:
                            print(f"       Redirects to: {location}")
            except Exception as e:
                print(f"[ERR] {domain}: {str(e)[:40]}")

async def main():
    results = await deep_api_scan()
    await test_graphql()
    await check_subdomains()
    
    print()
    print("=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"\nTotal API paths tested: {results['total_tested']}")
    print(f"JSON endpoints: {len(results['json_endpoints'])}")
    print(f"HTML endpoints: {len(results['html_endpoints'])}")
    
    if results['json_endpoints']:
        print("\n[!] JSON endpoints found - potential API exposure:")
        for ep in results['json_endpoints']:
            print(f"    - {ep['path']} ({ep['status']})")

if __name__ == "__main__":
    asyncio.run(main())