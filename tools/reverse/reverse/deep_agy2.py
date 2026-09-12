"""Extract embedded content from agy.exe - ZIP/WASM/etc"""
import os, re, struct, zipfile, gzip, bz2, io

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)
print(f"File size: {file_size:,} bytes")

with open(exe_path, 'rb') as f:
    data = f.read(min(file_size, 300*1024*1024))

# === 1. Extract ZIP archives ===
print("\n=== ZIP ARCHIVES ===")
zip_offsets = [m.start() for m in re.finditer(b'PK\x03\x04', data)]
extracted_files = []
for i, offset in enumerate(zip_offsets[:20]):
    # Read ZIP local file header
    if offset + 30 > len(data):
        continue
    header = data[offset:offset+30]
    if len(header) < 30:
        continue
    version, flags, method, mod_time, mod_date, crc32, comp_size, uncomp_size, name_len, extra_len = struct.unpack('<HHHHHIIIHH', header[:26])
    name = data[offset+30:offset+30+name_len].decode('ascii', errors='replace')
    
    data_start = offset + 30 + name_len + extra_len
    if comp_size == 0 or uncomp_size == 0 or data_start + comp_size > min(file_size, 300*1024*1024):
        continue
    
    if method == 0:  # Stored
        compressed_data = data[data_start:data_start+uncomp_size]
    elif method == 8:  # Deflate
        try:
            compressed_data = data[data_start:data_start+comp_size]
            uncompressed = gzip.decompress(compressed_data)
            compressed_data = uncompressed
        except:
            compressed_data = b''
    else:
        compressed_data = b''
    
    if compressed_data:
        ext = os.path.splitext(name)[1]
        extracted_files.append((name, len(compressed_data), ext))

print(f"Found {len(zip_offsets)} ZIP signatures, {len(extracted_files)} extractable files")
for name, size, ext in sorted(extracted_files, key=lambda x: -x[1])[:30]:
    print(f"  {size/1024:.0f}KB {ext:5s} {name[:80]}")

# === 2. WASM modules ===
print("\n=== WASM MODULES ===")
wasm_offsets = [m.start() for m in re.finditer(b'\x00asm', data)]
for off in wasm_offsets:
    header = data[off:off+8]
    print(f"  WASM at 0x{off:x}: magic={header[:4]} type={header[4:8]}")
    # Try to read WASM section sizes
    if header[:4] == b'\x00asm':
        # Parse WASM sections
        pos = off + 8
        sections = []
        for _ in range(10):
            if pos + 2 > len(data):
                break
            sec_id = data[pos]
            sec_size = 0
            shift = 0
            while True:
                b = data[pos+1+shift]
                sec_size |= (b & 0x7F) << (7 * shift)
                shift += 1
                if not (b & 0x80):
                    break
            sec_start = pos + 1 + shift
            sec_end = sec_start + sec_size
            if sec_end > len(data):
                break
            section_names = {0:'custom',1:'type',2:'import',3:'function',4:'table',5:'memory',6:'global',7:'export',8:'start',9:'element',10:'code',11:'data'}
            sec_name = section_names.get(sec_id, f'unknown_{sec_id}')
            sections.append((sec_name, sec_size))
            pos = sec_end
        print(f"    Sections: {sections[:10]}")

# === 3. Binary metadata ===
print("\n=== BINARY METADATA ===")
# Check for Go binary markers
go_markers = [
    (b'\x00.goobj', 'Go object'),
    (b'go build ', 'Go build cmd'),
    (b'runtime.main', 'Go runtime'),
    (b'runtime.systemstack', 'Go runtime'),
    (b'github.com/', 'Go modules'),
]
for marker, desc in go_markers:
    count = data.count(marker)
    if count > 0:
        print(f"  {desc}: {count}")

# Check for CGO
cgo_count = data.count(b'cgo')
print(f"  CGO usage: {cgo_count}")

# Look for build tags
build_tags = re.findall(rb'go:build ([^\n]+)', data)
for tag in set(build_tags)[:10]:
    print(f"  Build tag: {tag.decode()}")

# === 4. Product identification ===
print("\n=== PRODUCT IDENTIFICATION ===")
product_patterns = [
    (rb'"name"[^\"]*\"([^\"]{3,40})\"', 'name'),
    (rb'name[":\s]+\"([^"\s]{3,40})\"', 'name2'),
    (rb'binary.name[":\s]+\"([^\"]{3,40})\"', 'binary_name'),
    (rb'product[":\s]+\"([^\"]{3,40})\"', 'product'),
    (rb'app\.name[":\s]+\"([^\"]{3,40})\"', 'app_name'),
    (rb'appName[":\s]+\"([^\"]{3,40})\"', 'appname'),
    (rb'DISPLAY_NAME[":\s]+\"([^\"]{3,40})\"', 'display_name'),
]
for pattern, label in product_patterns:
    matches = re.findall(pattern, data)
    for m in matches[:5]:
        try:
            text = m.decode('ascii')
            if len(text) > 2:
                print(f"  {label}: {text}")
        except:
            pass

# === 5. Agent system architecture ===
print("\n=== AGENT SYSTEM ARCHITECTURE ===")
agent_arch = {
    'Orchestrator': data.count(b'orchestrator'),
    'Pipeline': data.count(b'pipeline'),
    'Swarm': data.count(b'swarm'),
    'CitC (clone-in-the-cloud)': data.count(b'citc'),
    'Handoff': data.count(b'handoff'),
    'Segment': data.count(b'segment'),
    'Phase': data.count(b'phase'),
    'Skill': data.count(b'skill'),
    'Tool calling': data.count(b'tool_call'),
    'Sub-agent': data.count(b'sub.agent') or data.count(b'subagent'),
    'Multi-agent': data.count(b'multi.agent'),
    'Agent loop': data.count(b'agent_loop') or data.count(b'AgentLoop'),
    'Memory': data.count(b'memory'),
    'Context': data.count(b'context'),
    'Transcript': data.count(b'transcript'),
    'Blackboard': data.count(b'blackboard'),
    'Workflows': data.count(b'workflow'),
    'Handoff file': data.count(b'handoff_'),
    'Progress tracking': data.count(b'progress.md') or data.count(b'pipeline_progress'),
}
for k, v in sorted(agent_arch.items(), key=lambda x: -x[1]):
    if v > 0:
        print(f"  {k}: {v}")

# === 6. LLM Providers ===
print("\n=== LLM PROVIDERS ===")
providers = {
    'Agnes AI': data.count(b'agnes-ai'),
    'OpenAI': data.count(b'openai'),
    'Anthropic/Claude': data.count(b'anthropic'),
    'DeepSeek': data.count(b'deepseek'),
    'Google/Gemini': data.count(b'gemini') + data.count(b'google.generativeai'),
    'Ollama': data.count(b'ollama'),
    'LM Studio': data.count(b'lm.studio') + data.count(b'localhost:1234'),
    'OpenRouter': data.count(b'openrouter'),
    'Mistral': data.count(b'mistral'),
    'Llama': data.count(b'llama'),
}
for k, v in sorted(providers.items(), key=lambda x: -x[1]):
    if v > 0:
        print(f"  {k}: {v}")

# === 7. Key features ===
print("\n=== KEY FEATURES ===")
features = {
    'JWT Analysis': data.count(b'jwt'),
    'GraphQL': data.count(b'graphql'),
    'WAF Bypass': data.count(b'waf') + data.count(b'bypass'),
    'CVE Lookup': data.count(b'CVE') + data.count(b'cve'),
    'Subdomain Enumeration': data.count(b'subdomain'),
    'Whois': data.count(b'whois'),
    'DNS Enumeration': data.count(b'dns'),
    'Cloudflare': data.count(b'cloudflare'),
    'Token Capture': data.count(b'token'),
    'Reverse Engineering': data.count(b'reverse.engineer') + data.count(b're_engine'),
    'Payload Manager': data.count(b'payload'),
    'Report Generation': data.count(b'report'),
    'OSINT': data.count(b'osint'),
    'Password Cracking': data.count(b'password') + data.count(b'crack'),
    'Browser Automation': data.count(b'browser') + data.count(b'selenium') + data.count(b'playwright'),
    'Chrome Extension': data.count(b'chrome.extension') + data.count(b'extension'),
    'Session Hijacking': data.count(b'session.hijack') + data.count(b'hijack'),
}
for k, v in sorted(features.items(), key=lambda x: -x[1]):
    if v > 0:
        print(f"  {k}: {v}")

print("\n=== DONE ===")