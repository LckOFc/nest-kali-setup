"""Download the antigravity SDK source code"""
import urllib.request, json, base64, os, zipfile

headers = {'Accept': 'application/vnd.github.v3+json'}
output_dir = r'C:\Users\devel\tools\reverse\antigravity-source'
os.makedirs(output_dir, exist_ok=True)

# Get all files from SDK repo
print("Fetching SDK repo contents...")
req = urllib.request.Request('https://api.github.com/repos/google-antigravity/antigravity-sdk-python/git/trees/main?recursive=1', headers=headers)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())
    files = data.get('tree', [])
    print(f"Total files: {len(files)}")

# Download source files (excluding tests and examples)
downloaded = 0
skipped = 0
for f in files:
    path = f['path']
    
    # Skip tests, examples, docs
    if '/test' in path or '/example' in path or path.endswith('.md') or path.endswith('.toml'):
        skipped += 1
        continue
    
    # Only download blobs (files)
    if f['type'] != 'blob':
        continue
    
    # Download the file
    file_url = f['url']
    try:
        req = urllib.request.Request(file_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            file_data = json.loads(resp.read().decode())
            content = base64.b64decode(file_data['content']).decode('utf-8', errors='replace')
            
            # Save to disk
            full_path = os.path.join(output_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as out:
                out.write(content)
            downloaded += 1
    except Exception as e:
        skipped += 1

print(f"\nDownloaded: {downloaded} files")
print(f"Skipped: {skipped} files")
print(f"Output: {output_dir}")

# Show what was downloaded
print("\n=== DOWNLOADED SOURCE FILES ===")
for root, dirs, filenames in os.walk(output_dir):
    level = root.replace(output_dir, '').count(os.sep)
    indent = '  ' * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = '  ' * (level + 1)
    for file in filenames[:10]:
        fp = os.path.join(root, file)
        sz = os.path.getsize(fp)
        print(f'{subindent}{file} ({sz:,} bytes)')
    if len(filenames) > 10:
        print(f'{subindent}... and {len(filenames)-10} more')