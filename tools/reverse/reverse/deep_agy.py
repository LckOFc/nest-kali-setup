"""Deep analysis of agy.exe - What is it?"""
import struct, re, os, gzip, bz2, zipfile, io

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)

print("=== DEEP AGY.EXE ANALYSIS ===")
print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

with open(exe_path, 'rb') as f:
    data = f.read(min(file_size, 500*1024*1024))

# === 1. Identity ===
print("\n=== IDENTITY ===")
# Check for version info
version_strs = re.findall(rb'version[":\s]+([0-9]+\.[0-9]+\.[0-9]+)', data, re.I)
for v in version_strs[:5]:
    print(f"  Version: {v.decode()}")

# Check for name
name_matches = re.findall(rb'"name"[":\s]*"([^"]{3,50})"', data)
for n in name_matches[:10]:
    print(f"  Name ref: {n.decode()}")

# Check build info
build_matches = re.findall(rb'go build ([^\\]+)', data)
for b in build_matches[:5]:
    print(f"  Build: {b.decode()}")

build_go = re.findall(rb'go version go([0-9.]+) ', data)
if build_go:
    print(f"  Go version: go{build_go[0].decode()}")

# === 2. Architecture ===
print("\n=== ARCHITECTURE ===")
# Go runtime indicators
go_indicators = {
    'runtime.gopls': data.count(b'runtime.gopls'),
    'runtime.main': data.count(b'runtime.main'),
    'runtime.goexit': data.count(b'runtime.goexit'),
    'sync.runtime_notifyList': data.count(b'sync.runtime_notifyList'),
    'sync.runtime_procPin': data.count(b'sync.runtime_procPin'),
    'google.golang.org': data.count(b'google.golang.org'),
    'github.com/': data.count(b'github.com/'),
}
for k, v in go_indicators.items():
    if v > 0:
        print(f"  {k}: {v}")

# Check for Go binary signature
if b'go\r\n' in data[:1000] or b'GOOS=' in data[:2000]:
    print("  → CONFIRMED: Go binary")
    
# Check PE for Go-specific patterns
if b'gosynth' in data or b'.goobj' in data:
    print("  → Go object files embedded")
if b'runtime.pthread_cond' in data:
    print("  → Go runtime pthreads detected")

# === 3. Core functionality ===
print("\n=== CORE FUNCTIONALITY ===")
functionalities = {
    # Multi-agent orchestration
    'multi_agent_orchestration': data.count(b'multi.agent'),
    'subagent_invocation': data.count(b'invoke_subagent'),
    'agent_handoff': data.count(b'handoff_'),
    'orchestrator': data.count(b'orchestrator'),
    'pipeline_mode': data.count(b'pipeline'),
    'swarm_mode': data.count(b'swarm'),
    'citc_clone': data.count(b'citc'),
    'segment_processing': data.count(b'segment_'),
    
    # AI/LLM
    'llm_calls': data.count(b'/chat/completions'),
    'anthropic_api': data.count(b'api.anthropic.com'),
    'openai_api': data.count(b'api.openai.com'),
    'deepseek_api': data.count(b'api.deepseek.com'),
    'google_gemini': data.count(b'generativelanguage.googleapis.com'),
    'ollama_api': data.count(b'localhost:11434'),
    'lm_studio': data.count(b'localhost:1234'),
    
    # File operations
    'file_read': data.count(b'os.ReadFile'),
    'file_write': data.count(b'os.WriteFile'),
    'exec_command': data.count(b'exec.Command'),
    'shell_exec': data.count(b'shell.exec'),
    
    # Database
    'sqlite': data.count(b'sqlite3'),
    'database_ops': data.count(b'DATABASE'),
    
    # Web/HTTP
    'http_server': data.count(b'http.ListenAndServe'),
    'websocket': data.count(b'websocket'),
    'sse': data.count(b'Server-Sent Events'),
    
    # Auth
    'oauth': data.count(b'oauth'),
    'token_auth': data.count(b'Authorization: Bearer'),
    
    # MCP
    'mcp_server': data.count(b'MCP'),
    'mcp_client': data.count(b'mcp_server'),
    
    # Skills
    'skill_system': data.count(b'SKILL.md'),
    'skill_definition': data.count(b'skill_definition'),
    
    # Terminal/TUI
    'terminal': data.count(b'terminal'),
    'tui_engine': data.count(b'tui'),
    'crossterm': data.count(b'crossterm'),
}

for k, v in sorted(functionalities.items(), key=lambda x: -x[1]):
    if v > 0:
        print(f"  {k}: {v}")

# === 4. Embedded Assets ===
print("\n=== EMBEDDED ASSETS ===")
# ZIP files
zip_offsets = [m.start() for m in re.finditer(b'PK\x03\x04', data)]
print(f"  ZIP archives: {len(zip_offsets)}")

# WASM modules
wasm_offsets = [m.start() for m in re.finditer(b'\x00asm', data)]
print(f"  WASM modules: {len(wasm_offsets)}")
for off in wasm_offsets[:5]:
    # Read WASM header
    wasm_header = data[off:off+8]
    print(f"    WASM at 0x{off:x}: {wasm_header}")

# tree-sitter grammars
ts_count = data.count(b'tree-sitter')
print(f"  tree-sitter references: {ts_count}")

# Syntax highlighting patterns
syntax_rules = re.findall(rb'<rule pattern="[^"]{10,100}"', data)
print(f"  Syntax highlight rules: {len(syntax_rules)}")

# === 5. CLI Commands ===
print("\n=== CLI COMMANDS ===")
cmd_patterns = re.findall(rb'cmd[._-]?(run|chat|agent|session|tool|config|model|export|clean|attack|plugin|doctor|setup|web|help|version)[^\w]*', data, re.I)
cmd_set = set(cmd_patterns)
for c in sorted(cmd_set, key=len, reverse=True)[:30]:
    print(f"  {c.decode()}")

# === 6. Agent Types ===
print("\n=== AGENT TYPES ===")
agent_types = {}
for match in re.finditer(rb'(agent|worker|orchestrator|synthesizer|conductor|sentinel|reviewer|analyst|planner)[_\s]*(\w+)', data, re.I):
    full = match.group(0).decode('ascii', errors='replace')
    agent_types[full] = agent_types.get(full, 0) + 1

for agent, count in sorted(agent_types.items(), key=lambda x: -x[1])[:20]:
    print(f"  {agent}: {count}")

# === 7. File Formats Supported ===
print("\n=== FILE FORMATS (from syntax highlighting) ===")
lang_patterns = re.findall(rb'<alias>(\w+)</alias>', data)
languages = set()
for l in lang_patterns:
    languages.add(l.decode('ascii', errors='replace'))
for lang in sorted(languages)[:30]:
    print(f"  {lang}")

# === 8. Key Libraries ===
print("\n=== KEY LIBRARIES ===")
libs = {
    'connectrpc': data.count(b'connectrpc'),
    'grpc': data.count(b'grpc'),
    'gin': data.count(b'gin-gonic'),
    'chi': data.count(b'gorilla/mux') or data.count(b'go-chi'),
    'cobra': data.count(b'cobra'),
    'viper': data.count(b'spf13/viper'),
    'sqlite': data.count(b'mattes/martin'),
    'rusqlite': data.count(b'lightman'),
    'wasm': data.count(b'wasmtime') or data.count(b'wazero'),
    'tree_sitter': data.count(b'tree-sitter'),
    'antlr': data.count(b'antlr4'),
    ' jetski': data.count(b'jetski'),
    'tailwind': data.count(b'tailwindcss'),
    'react': data.count(b'react'),
    'solidjs': data.count(b'solidjs'),
    'ratatui': data.count(b'ratatui'),
    'crossterm': data.count(b'crossterm'),
    'axum': data.count(b'axum'),
}
for lib, count in sorted(libs.items(), key=lambda x: -x[1]):
    if count > 0:
        print(f"  {lib}: {count}")

# === 9. Specific Features ===
print("\n=== DETAILED FEATURES ===")
features = [
    ('Auto-install', b'autoinstall'),
    ('Package manager', b'pip install'),
    ('npm install', b'npm install'),
    ('winget', b'winget'),
    ('Chocolatey', b'choco'),
    ('Brew', b'brew install'),
    ('Report generation', b'report_generator'),
    ('OSINT', b'osint'),
    ('Password cracking', b'password_cracker'),
    ('Payload management', b'payload_manager'),
    ('Burp Suite', b'burpsuite'),
    ('RE engine', b're_engine'),
    ('Token hunter', b'token_hunter'),
    ('Cloudflare bypass', b'cloudflare'),
    ('JWT analysis', b'jwt'),
    ('GraphQL', b'graphql'),
    ('WAF bypass', b'waf'),
    ('CVE lookup', b'CVE'),
    ('Subdomain enum', b'subdomain'),
    ('Whois', b'whois'),
    ('DNS enum', b'dns_enumeration'),
]
for name, pattern in features:
    count = data.count(pattern)
    if count > 0:
        print(f"  {name}: {count}")

# === 10. Project structure clues ===
print("\n=== PROJECT STRUCTURE ===")
paths_found = re.findall(rb'(?:C:[/\\][^\\s<>:"|?*]+|/[^\\s<>:"|?*]{5,})', data)
unique_paths = set()
for p in paths_found:
    try:
        text = p.decode('ascii', errors='replace')
        if any(x in text for x in ['.agents/', 'skills/', 'workflows/', 'system/', 'tools/', 'core/']):
            unique_paths.add(text[:80])
    except:
        pass

for p in sorted(unique_paths)[:30]:
    print(f"  {p}")

print("\n=== DONE ===")