"""Check content of accessible sensitive files"""
import asyncio
import aiohttp
import json

async def check_content():
    url = "https://ivi-bettx.net"
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Check robots.txt
        print("=== robots.txt ===")
        try:
            async with session.get(f"{url}/robots.txt", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content = await resp.text()
                results["robots.txt"] = content
                print(content[:500])
        except Exception as e:
            results["robots.txt"] = {"error": str(e)}
        
        # Check sitemap.xml
        print("\n=== sitemap.xml ===")
        try:
            async with session.get(f"{url}/sitemap.xml", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content = await resp.text()
                results["sitemap.xml"] = content
                print(content[:500])
        except Exception as e:
            results["sitemap.xml"] = {"error": str(e)}
        
        # Check application.properties
        print("\n=== application.properties ===")
        try:
            async with session.get(f"{url}/application.properties", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content = await resp.text()
                results["application.properties"] = content
                # Look for sensitive patterns
                if any(p in content.lower() for p in ["password", "secret", "key", "token", "database"]):
                    print("WARNING: Possible credentials found!")
                print(content[:500])
        except Exception as e:
            results["application.properties"] = {"error": str(e)}
        
        # Check application.yml
        print("\n=== application.yml ===")
        try:
            async with session.get(f"{url}/application.yml", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content = await resp.text()
                results["application.yml"] = content
                if any(p in content.lower() for p in ["password", "secret", "key", "token", "database"]):
                    print("WARNING: Possible credentials found!")
                print(content[:500])
        except Exception as e:
            results["application.yml"] = {"error": str(e)}
        
        # Check backup.sql
        print("\n=== backup.sql ===")
        try:
            async with session.get(f"{url}/backup.sql", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content = await resp.text()
                results["backup.sql"] = content
                # Check if it's real SQL or just HTML
                if content.strip().startswith("<!doctype") or content.strip().startswith("<html"):
                    print("Note: This appears to be HTML (SPA fallback), not actual SQL")
                elif "CREATE TABLE" in content or "INSERT INTO" in content:
                    print("WARNING: Real database backup found!")
                print(f"Content length: {len(content)}")
                print(content[:300])
        except Exception as e:
            results["backup.sql"] = {"error": str(e)}
        
        # Check /v2/api-docs (Swagger)
        print("\n=== /v2/api-docs ===")
        try:
            async with session.get(f"{url}/v2/api-docs", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content = await resp.text()
                results["v2/api-docs"] = content
                print(f"Content-Type: {resp.headers.get('Content-Type')}")
                print(f"Content length: {len(content)}")
                # Try to parse as JSON
                try:
                    data = json.loads(content)
                    print("Valid JSON found!")
                    print(f"Keys: {list(data.keys())[:10]}")
                except:
                    print("Not valid JSON - likely SPA fallback")
        except Exception as e:
            results["v2/api-docs"] = {"error": str(e)}
    
    return results

if __name__ == "__main__":
    results = asyncio.run(check_content())
    print("\n=== FINAL REPORT ===")
    for key, value in results.items():
        if isinstance(value, dict) and "error" in value:
            print(f"{key}: ERROR - {value['error']}")
        elif isinstance(value, str):
            print(f"{key}: {len(value)} chars")
