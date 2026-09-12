"""Search for source code location / repository info in agy.exe"""
import os, re, struct

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)
print(f"Searching for source/repository clues...")
print()

with open(exe_path, 'rb') as f:
    data = f.read(min(file_size, 500*1024*1024))

# 1. Search for GitHub/GitLab URLs
print("=== GIT REPOSITORY URLs ===")
github_urls = re.findall(rb'(?:https?://)?(?:www\.)?(?:github|gitlab|bitbucket)[.]com/[^\s\x00<>"]{5,200}', data)
unique_urls = set()
for u in github_urls:
    try:
        text = u.decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_./\\\\-:@?=&#%]', ' ', text)
        text = ' '.join(text.split())
        if 'github' in text.lower() or 'gitlab' in text.lower():
            unique_urls.add(text[:120])
    except:
        pass
for u in sorted(unique_urls)[:20]:
    print(f"  {u}")

# 2. Search for any domain names (could be the project's domain)
print("\n=== DOMAIN NAMES ===")
domains = re.findall(rb'[a-zA-Z0-9][a-zA-Z0-9\-]{1,30}\.[a-z]{2,}', data)
unique_domains = set(d.decode('ascii', errors='replace') for d in domains)
# Filter to likely project domains
project_domains = [d for d in unique_domains if d not in [
    'com', 'org', 'net', 'io', 'dev', 'ai', 'co', 'gov', 'edu',
    'github.com', 'gitlab.com', 'openai.com', 'anthropic.com',
    'deepseek.com', 'google.com', 'microsoft.com', 'amazon.com',
    'mozilla.org', 'ubuntu.com', 'debian.org', 'linux.org'
] and len(d) < 40]
for d in sorted(project_domains)[:30]:
    print(f"  {d}")

# 3. Search for go:build tags (reveal build configuration)
print("\n=== GO BUILD TAGS ===")
build_tags = re.findall(rb'go:build\s+[^\x00]{0,200}', data)
for b in build_tags[:20]:
    try:
        text = b.decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_\-|=]', ' ', text)
        text = ' '.join(text.split())
        if len(text) > 5:
            print(f"  {text[:100]}")
    except:
        pass

# 4. Search for //go:linkname (reveal internal function names)
print("\n=== GO LINKNAME DIRECTIVES ===")
linknames = re.findall(rb'//go:linkname\s+[^\x00]{0,100}', data)
for l in linknames[:20]:
    try:
        text = l.decode('ascii', errors='replace')
        print(f"  {text[:100]}")
    except:
        pass

# 5. Search for build constants
print("\n=== BUILD CONSTANTS ===")
build_consts = re.findall(rb'[A-Z_]{3,30}=[^\x00]{0,100}', data)
unique_consts = set()
for c in build_consts:
    try:
        text = c.decode('ascii', errors='replace')
        text = re.sub(r'[^a-zA-Z0-9_=\-]', ' ', text)
        text = ' '.join(text.split())
        if len(text) > 5 and not any(x in text for x in ['undefined', 'unknown', 'default']):
            unique_consts.add(text[:80])
    except:
        pass
for c in sorted(unique_consts)[:20]:
    print(f"  {c}")

# 6. Search for any author/committer info
print("\n=== AUTHOR/INFO STRINGS ===")
author_pats = [
    rb'[Aa]uthor[^\x00]{0,100}',
    rb'[Cc]opyright[^\x00]{0,100}',
    rb'[Ll]icensed[^\x00]{0,100}',
    rb'[Vv]ersion[^\x00]{0,100}',
    rb'[Bb]uild[^\x00]{0,100}',
    rb'[Dd]ate[^\x00]{0,100}',
]
for pat in author_pats:
    matches = re.findall(pat, data)
    for m in matches[:3]:
        try:
            text = m.decode('ascii', errors='replace')
            text = re.sub(r'[^a-zA-Z0-9_\-=. ]', ' ', text)
            text = ' '.join(text.split())
            if len(text) > 5:
                print(f"  {text[:100]}")
        except:
            pass

# 7. Check for any embedded README or documentation
print("\n=== EMBEDDED DOCUMENTATION ===")
readme_patterns = [
    rb'README[^\\x00]{0,500}',
    rb'documentation[^\\x00]{0,500}',
    rb'document[^\\x00]{0,500}',
]
for pat in readme_patterns:
    matches = re.findall(pat, data, re.I)
    for m in matches[:3]:
        try:
            text = m.decode('ascii', errors='replace')
            text = re.sub(r'[^a-zA-Z0-9_\-=.!?,;:() ]', ' ', text)
            text = ' '.join(text.split())
            if len(text) > 20:
                print(f"  {text[:150]}")
        except:
            pass

# 8. Look for the actual module path (go.mod content)
print("\n=== MODULE PATH SEARCH ===")
# Go module paths look like: github.com/user/repo or internal/package
mod_patterns = re.findall(rb'[a-zA-Z0-9_\-/]+\.[a-zA-Z0-9_\-/]+[^\x00]{0,200}', data)
module_candidates = set()
for m in mod_patterns:
    try:
        text = m.decode('ascii', errors='replace')
        # Look for patterns like github.com/..., internal/..., google.golang.org/...
        if any(prefix in text for prefix in ['github.com/', 'gitlab.com/', 'internal/', 'google.golang.org/', 'cloud.google.com/']):
            # Extract just the module path
            parts = re.findall(r'[a-zA-Z0-9_\-/]+\.[a-zA-Z0-9_\-/]+', text)
            for p in parts:
                if '/' in p and len(p) > 10 and len(p) < 100:
                    module_candidates.add(p[:100])
    except:
        pass

for m in sorted(module_candidates)[:30]:
    print(f"  {m}")

# 9. Check for embedded proto files (reveal API structure)
print("\n=== PROTO REFERENCES ===")
proto_pats = re.findall(rb'option\s+go_package\s*=\s*"[^"]+"', data)
for p in proto_pats[:10]:
    try:
        print(f"  {p.decode('ascii')[:120]}")
    except:
        pass

# 10. Final summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"GitHub/GitLab URLs: {len(unique_urls)}")
print(f"Unique domains: {len(project_domains)}")
print(f"Go build tags: {len(build_tags)}")
print(f"Module candidates: {len(module_candidates)}")
print(f"Proto references: {len(proto_pats)}")