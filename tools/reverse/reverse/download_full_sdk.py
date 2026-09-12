"""Download ALL SDK source files including tests"""
import urllib.request, json, base64, os

headers = {'Accept': 'application/vnd.github.v3+json'}
output_dir = r'C:\Users\devel\tools\reverse\antigravity-source'

# Get ALL files
print("Fetching ALL SDK repo files...")
req = urllib.request.Request('https://api.github.com/repos/google-antigravity/antigravity-sdk-python/git/trees/main?recursive=1', headers=headers)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())
    files = data.get('tree', [])
    print(f"Total files: {len(files)}")

# Download everything
downloaded = 0
for f in files:
    path = f['path']
    if f['type'] != 'blob':
        continue
    
    file_url = f['url']
    try:
        req = urllib.request.Request(file_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            file_data = json.loads(resp.read().decode())
            content = base64.b64decode(file_data['content']).decode('utf-8', errors='replace')
            
            full_path = os.path.join(output_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as out:
                out.write(content)
            downloaded += 1
    except Exception as e:
        pass

print(f"Downloaded: {downloaded} files")

# Show full structure
print("\n=== FULL SOURCE STRUCTURE ===")
for root, dirs, filenames in os.walk(output_dir):
    level = root.replace(output_dir, '').count(os.sep)
    indent = '  ' * level
    basename = os.path.basename(root)
    if basename.startswith('.'):
        continue
    print(f'{indent}{basename}/')
    subindent = '  ' * (level + 1)
    for file in sorted(filenames)[:15]:
        fp = os.path.join(root, file)
        sz = os.path.getsize(fp)
        print(f'{subindent}{file} ({sz:,}B)')
    if len(filenames) > 15:
        print(f'{subindent}... and {len(filenames)-15} more')