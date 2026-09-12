"""Download Google Antigravity SDK source from GitHub"""
import urllib.request, json, base64, os, time

headers = {'Accept': 'application/vnd.github.v3+json'}
base_dir = r'C:\Users\devel\tools\reverse\antigravity-source'

print("Step 1: Getting repo tree...")
req = urllib.request.Request(
    'https://api.github.com/repos/google-antigravity/antigravity-sdk-python/git/trees/main?recursive=1',
    headers=headers
)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
    files = data.get('tree', [])
    print(f"Total files in repo: {len(files)}")

# Filter for source files
source_files = [f for f in files if f['path'].startswith('google/antigravity/') and f['path'].endswith('.py') and f['type'] == 'blob']
print(f"Source .py files: {len(source_files)}")

print("\nStep 2: Downloading source files...")
downloaded = 0
failed = 0
for i, f in enumerate(source_files):
    url = f['url']
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            file_data = json.loads(resp.read().decode())
            content = base64.b64decode(file_data['content']).decode('utf-8', errors='replace')
            full_path = os.path.join(base_dir, f['path'])
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as out:
                out.write(content)
            downloaded += 1
            if downloaded % 5 == 0:
                print(f"  {downloaded}/{len(source_files)} files...")
            time.sleep(0.1)  # Small delay to avoid rate limit
    except Exception as e:
        failed += 1
        if failed < 3:
            print(f"  Failed: {f['path']} - {e}")

print(f"\nDone! Downloaded: {downloaded}, Failed: {failed}")

# Show structure
print("\n=== SOURCE STRUCTURE ===")
for root, dirs, files in os.walk(os.path.join(base_dir, 'google')):
    level = root.replace(base_dir, '').count(os.sep)
    indent = '  ' * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = '  ' * (level + 1)
    for f in sorted(files)[:8]:
        fp = os.path.join(root, f)
        sz = os.path.getsize(fp)
        print(f'{subindent}{f} ({sz:,}B)')
    if len(files) > 8:
        print(f'{subindent}... and {len(files)-8} more')