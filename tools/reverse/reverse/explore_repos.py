"""Explore the antigravity repos on GitHub"""
import urllib.request, json, base64

headers = {'Accept': 'application/vnd.github.v3+json'}

# 1. List all files in antigravity-cli repo
print("=== ANTI-GRAVITY CLI REPO CONTENTS ===")
req = urllib.request.Request('https://api.github.com/repos/google-antigravity/antigravity-cli/git/trees/main?recursive=1', headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
    files = data.get('tree', [])
    for f in sorted(files, key=lambda x: x['path']):
        print(f"  {f['type']:5s} {f['path']}")

# 2. List org repos
print("\n=== GOOGLE-ANTIGRAVITY ORG REPOS ===")
req = urllib.request.Request('https://api.github.com/orgs/google-antigravity/repos?sort=stars&per_page=20', headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
    for repo in data:
        lang = repo.get('language', 'N/A')
        desc = repo.get('description', '')[:80] if repo.get('description') else ''
        print(f"  {repo['name']:30s} {lang:10s} stars={repo['stargazers_count']} fork={repo['fork']}")
        if desc:
            print(f"    {desc}")

# 3. Get SDK repo structure
print("\n=== SDK REPO STRUCTURE ===")
req = urllib.request.Request('https://api.github.com/repos/google-antigravity/antigravity-sdk-python/git/trees/main?recursive=1', headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
    files = data.get('tree', [])
    # Show only source files
    src_files = [f for f in files if '/test' not in f['path'] and '/example' not in f['path'] and not f['path'].endswith('.pyc') and f['type'] == 'blob']
    for f in sorted(src_files, key=lambda x: x['path'])[:50]:
        print(f"  {f['path']}")
    if len(src_files) > 50:
        print(f"  ... and {len(src_files)-50} more source files")

# 4. Get the main README from CLI repo
print("\n=== CLI README ===")
req = urllib.request.Request('https://api.github.com/repos/google-antigravity/antigravity-cli/readme', headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
    content = base64.b64decode(data['content']).decode()
    print(content[:2000])