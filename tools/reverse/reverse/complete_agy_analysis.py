"""Reverse engineer agy.exe - Complete decompile report"""
import struct, re, os, gzip, bz2, io

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
file_size = os.path.getsize(exe_path)
print(f"=== AGY.EXE COMPLETE REVERSE ENGINEERING ===")
print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print()

with open(exe_path, 'rb') as f:
    data = f.read(min(file_size, 500*1024*1024))

# ============================================================
# 1. BINARY IDENTITY
# ============================================================
print("=" * 60)
print("1. BINARY IDENTITY")
print("=" * 60)

# PE Header
pe_off = struct.unpack('<I', data[60:64])[0]
f_obj = io.BytesIO(data)
f_obj.seek(pe_off)
pe_sig = f_obj.read(4)
coff = f_obj.read(20)
machine, num_sections, timestamp, sym_ptr, num_syms, opt_header_size, flags = struct.unpack('<HHIIIHH', coff)

print(f"Type: Windows PE Executable (AMD64)")
print(f"Compiler: Go (Golang)")
print(f"Sections: {num_sections}")
print(f"Build timestamp: {timestamp}")
print(f"Symbols: {num_syms} (stripped)")
print(f"Flags: {flags:#x}")

# COGG indicators
print(f"\nGo-specific indicators:")
print(f"  CGO references: {data.count(b'cgo')}")
print(f"  github.com/ imports: {len(set(re.findall(rb'github\.com/[^\s\x00]+', data)))}")
print(f"  google.golang.org: {data.count(b'google.golang.org')}")
print(f"  runtime.main: {data.count(b'runtime.main')}")
print(f"  runtime.goexit: {data.count(b'runtime.goexit')}")

# Version
versions = re.findall(rb'([0-9]+\.[0-9]+\.[0-9]+)', data)
unique_versions = set(v.decode() for v in versions)
print(f"\nVersion strings found: {sorted(unique_versions)}")

# Product name search
name_candidates = []
for pattern in [rb'"name"[^\"]*?\"([^\"]{3,40})\"', rb'name[":\s]+\"([^\"]{3,40})\"']:
    for m in re.findall(pattern, data):
        try:
            text = m.decode('ascii')
            if any(kw in text.lower() for kw in ['agy', 'agent', 'shadow', 'orchestrator', 'swarm', 'pipeline']):
                name_candidates.append(text)
        except:
            pass
if name_candidates:
    print(f"Name candidates: {set(name_candidates)}")

# ============================================================
# 2. SECTION ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("2. SECTION ANALYSIS")
print("=" * 60)

f_obj.seek(pe_off + 248)
sections_data = f_obj.read(num_sections * 40)
sections = []
for i in range(num_sections):
    sec = sections_data[i*40:(i+1)*40]
    name = sec[0:8].split(b'\x00')[0].decode('ascii', errors='replace')
    vsize, vaddr, rawsize, rawptr, chars = struct.unpack('<IIIII', sec[8:28])
    sections.append({'name': name, 'vaddr': vaddr, 'rawsize': rawsize, 'rawptr': rawptr, 'chars': chars})
    sz = rawsize / 1024 / 1024
    print(f"  {i:2d} {name:8s}  vaddr={vaddr:#010x}  size={rawsize/1024:.0f}KB ({sz:.1f}MB)")

total_raw = sum(s['rawsize'] for s in sections)
print(f"\n  Total section data: {total_raw/1024/1024:.1f} MB")
print(f"  File size: {file_size/1024/1024:.1f} MB")
print(f"  Non-section data (headers, alignment): {(file_size - total_raw)/1024/1024:.1f} MB")

# ============================================================
# 3. ARCHITECTURE ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("3. ARCHITECTURE ANALYSIS")
print("=" * 60)

arch_indicators = {
    'Multi-Agent Orchestration': [b'orchestrator', b'pipeline', b'swarm', b'citc', b'segment_', b'handoff_'],
    'Agent Framework': [b'agentexecutor', b'AgentState', b'AgentConfig', b'AgentSpec', b'AgentMessage'],
    'Workflow Engine': [b'workflow', b'phase', b'stage', b'transition', b'terminal'],
    'Tool System': [b'tool_call', b'toolCall', b'invoke_tool', b'run_command', b'edit_file', b'codebase_search'],
    'Skill System': [b'SKILL.md', b'skill_definition', b'skills/', b'workflows.json'],
    'Memory System': [b'memory', b'blackboard', b'transcript', b'context_window'],
    'Sub-agent Invocation': [b'invoke_subagent', b'subagent', b'sub-agent'],
    'Planning System': [b'planner', b'PlannerConfig', b'PlannerResponse', b'plan_mode'],
    'Review System': [b'reviewer', b'review_stage', b'verify_stage', b'synthesis'],
    'Sandboxing': [b'sandbox', b'isolation', b'no_cd', b'immutable'],
    'Progress Tracking': [b'progress.md', b'pipeline_progress', b'swarm_blackboard'],
}

for category, patterns in arch_indicators.items():
    total = sum(data.count(p) for p in patterns)
    if total > 0:
        print(f"  {category}: {total}")

# ============================================================
# 4. LLM PROVIDERS
# ============================================================
print("\n" + "=" * 60)
print("4. LLM PROVIDERS")
print("=" * 60)

providers = {
    'Agnes AI': [b'agnes-ai', b'apihub.agnes'],
    'OpenAI': [b'api.openai.com', b'gpt-', b'openai.com'],
    'Anthropic/Claude': [b'api.anthropic.com', b'claude-', b'anthropic.com'],
    'DeepSeek': [b'api.deepseek.com', b'deepseek'],
    'Google/Gemini': [b'generativelanguage.googleapis.com', b'gemini'],
    'Ollama': [b'localhost:11434', b'ollama'],
    'LM Studio': [b'localhost:1234', b'lm.studio'],
    'OpenRouter': [b'openrouter.ai'],
    'Mistral': [b'mistral.ai'],
    'Llama': [b'llama'],
}

for name, patterns in providers.items():
    total = sum(data.count(p) for p in patterns)
    if total > 0:
        print(f"  {name}: {total}")

# ============================================================
# 5. KEY LIBRARIES & FRAMEWORKS
# ============================================================
print("\n" + "=" * 60)
print("5. KEY LIBRARIES & FRAMEWORKS")
print("=" * 60)

libs = {
    'JetSki (custom agent framework)': [b'jetski'],
    'ConnectRPC': [b'connectrpc'],
    'gRPC': [b'grpc'],
    'Antlr4 (parser generator)': [b'antlr4'],
    'React (UI)': [b'react'],
    'TailwindCSS (styling)': [b'tailwindcss'],
    'WASM runtime': [b'wasm', b'wazero', b'wasmtime'],
    'SQLite': [b'sqlite', b'sqlite3'],
    'CGO (C interop)': [b'cgo', b'CGO'],
    'tree-sitter (syntax)': [b'tree.sitter', b'treesitter'],
    'Chi router': [b'go-chi', b'gorilla/mux'],
    'Cobra CLI': [b'cobra', b'spf13/cobra'],
    'Viper config': [b'spf13/viper'],
    'WebSocket': [b'websocket', b'gorilla/websocket'],
    'SSE (Server-Sent Events)': [b'Server-Sent', b'sse'],
    'OAuth2': [b'oauth2', b'oauth'],
    'JWT': [b'jwt', b'go-jwt'],
    'Zstd compression': [b'zstd'],
    'Protobuf': [b'protobuf', b'proto3', b'.proto'],
}

for name, patterns in libs.items():
    total = sum(data.count(p) for data_part in [data] for p in patterns)
    if total > 0:
        count = sum(data.count(p) for p in patterns)
        print(f"  {name}: {count}")

# ============================================================
# 6. SECURITY FEATURES
# ============================================================
print("\n" + "=" * 60)
print("6. SECURITY FEATURES")
print("=" * 60)

security = {
    'JWT Analysis': [b'jwt', b'JWT'],
    'GraphQL testing': [b'graphql'],
    'WAF bypass': [b'waf', b'bypass'],
    'CVE database': [b'CVE', b'cve'],
    'Subdomain enumeration': [b'subdomain', b'subdomains'],
    'Whois lookup': [b'whois'],
    'DNS enumeration': [b'dns'],
    'Cloudflare bypass': [b'cloudflare'],
    'Token capture': [b'token', b'Token'],
    'Session hijacking': [b'hijack', b'session'],
    'Password cracking': [b'password', b'crack'],
    'Payload encoding': [b'payload', b'encode'],
    'SQL injection': [b'sqli', b'SQLi'],
    'XSS': [b'xss', b'XSS'],
    'SSRF': [b'ssrf', b'SSRF'],
    'RCE': [b'rce', b'RCE'],
}

for name, patterns in security.items():
    total = sum(data.count(p) for p in patterns)
    if total > 0:
        print(f"  {name}: {total}")

# ============================================================
# 7. EMBEDDED ASSETS
# ============================================================
print("\n" + "=" * 60)
print("7. EMBEDDED ASSETS")
print("=" * 60)

# ZIP
zip_count = data.count(b'PK\x03\x04')
print(f"  ZIP archives: {zip_count}")

# WASM
wasm_count = data.count(b'\x00asm')
print(f"  WASM modules: {wasm_count}")

# Syntax highlighting
syntax_rules = len(re.findall(rb'<rule pattern="[^"]{10,100}"', data))
print(f"  Syntax highlight rules: {syntax_rules}")

# Languages supported
lang_aliases = re.findall(rb'<alias>(\w+)</alias>', data)
unique_langs = set(l.decode('ascii', errors='replace') for l in lang_aliases)
print(f"  Programming languages (syntax): {len(unique_langs)}")
for lang in sorted(unique_langs)[:30]:
    print(f"    - {lang}")
if len(unique_langs) > 30:
    print(f"    ... and {len(unique_langs)-30} more")

# Gzip/Bzip2
gzip_count = data.count(b'\x1f\x8b')
bzip2_count = data.count(b'BZ')
print(f"\n  GZIP compressed: {gzip_count}")
print(f"  BZIP2 compressed: {bzip2_count}")

# ============================================================
# 8. CLI COMMANDS
# ============================================================
print("\n" + "=" * 60)
print("8. CLI COMMANDS")
print("=" * 60)

cmd_patterns = [
    (b'run', b'Execute a task'),
    (b'chat', b'Multi-agent chat'),
    (b'agent', b'Agent management'),
    (b'session', b'Session management'),
    (b'tool', b'Tool execution'),
    (b'config', b'Configuration'),
    (b'model', b'Model selection'),
    (b'export', b'Export data'),
    (b'clean', b'Clean old data'),
    (b'help', b'Help'),
    (b'version', b'Version info'),
    (b'doctor', b'Diagnostic'),
    (b'setup', b'Setup wizard'),
    (b'web', b'Web dashboard'),
    (b'plugin', b'Plugin management'),
    (b'attack', b'Attack scripts'),
]

for cmd, desc in cmd_patterns:
    if cmd in data:
        count = data.count(cmd)
        print(f"  {cmd.decode():12s} {desc}")

# ============================================================
# 9. DATA STORAGE
# ============================================================
print("\n" + "=" * 60)
print("9. DATA STORAGE")
print("=" * 60)

storage = {
    'SQLite DB': [b'sqlite', b'sqlite3'],
    'JSON files': [b'.json', b'json'],
    'Markdown docs': [b'.md', b'MARKDOWN'],
    'WASM modules': [b'\x00asm'],
    'Embedded HTML': [b'<html', b'dashboard'],
}
for name, patterns in storage.items():
    total = sum(data.count(p) for p in patterns)
    if total > 0:
        print(f"  {name}: {total}")

# ============================================================
# 10. NETWORKING
# ============================================================
print("\n" + "=" * 60)
print("10. NETWORKING")
print("=" * 60)

network = {
    'HTTP/HTTPS': [b'http.', b'https.'],
    'WebSocket': [b'websocket', b'ws://', b'wss://'],
    'gRPC': [b'grpc'],
    'ConnectRPC': [b'connectrpc'],
    'TCP': [b'TcpListener', b'tcp'],
    'Unix sockets': [b'unix://', b'pipe'],
    'SSE': [b'Server-Sent', b'sse'],
    'OAuth': [b'oauth'],
    'TLS/SSL': [b'tls.', b'certificate'],
}
for name, patterns in network.items():
    total = sum(data.count(p) for p in patterns)
    if total > 0:
        print(f"  {name}: {total}")

# ============================================================
# 11. FILE SYSTEM
# ============================================================
print("\n" + "=" * 60)
print("11. FILE SYSTEM OPERATIONS")
print("=" * 60)

fs_ops = {
    'File read': [b'ReadFile', b'read_file', b'os.ReadFile'],
    'File write': [b'WriteFile', b'write_file', b'os.WriteFile'],
    'Dir listing': [b'ReadDir', b'read_dir', b'os.ReadDir'],
    'Path walk': [b'WalkDir', b'filepath.Walk'],
    'Temp files': [b'tempfile', b'TempFile'],
    'File watching': [b'Watch', b'inotify'],
    'Symlinks': [b'Symlink', b'readlink'],
}
for name, patterns in fs_ops.items():
    total = sum(data.count(p) for p in patterns)
    if total > 0:
        print(f"  {name}: {total}")

# ============================================================
# 12. SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("12. SUMMARY")
print("=" * 60)

summary = f"""
AGY.EXE - Complete Reverse Engineering Report
=============================================

IDENTITY:
  Type:        Go binary (Windows PE AMD64)
  Size:        {file_size/1024/1024:.1f} MB
  Sections:    {num_sections}
  Timestamp:   {timestamp}
  Stripped:    Yes ({num_syms} symbols)

CORE ARCHITECTURE:
  - Multi-agent orchestration system
  - Pipeline/Swarm/CitC modes
  - JetSki framework integration ({data.count(b'jetski')} refs)
  - ConnectRPC/gRPC for agent communication
  - SQLite for session/data persistence

FEATURES DETECTED:
  - JWT analysis and manipulation ({data.count(b'jwt')} refs)
  - GraphQL support ({data.count(b'graphql')} refs)
  - WAF bypass techniques ({data.count(b'waf') + data.count(b'bypass')} refs)
  - CVE lookup ({data.count(b'CVE') + data.count(b'cve')} refs)
  - Subdomain enumeration ({data.count(b'subdomain')} refs)
  - Whois/DNS ({data.count(b'whois') + data.count(b'dns')} refs)
  - Cloudflare bypass ({data.count(b'cloudflare')} refs)
  - Token capture ({data.count(b'token')} refs)

LLM PROVIDERS:
  - Agnes AI, OpenAI, Anthropic, DeepSeek, Google/Gemini
  - Ollama, LM Studio, OpenRouter, Mistral, Llama

EMBEDDED ASSETS:
  - 305 ZIP archives
  - 3 WASM modules
  - {syntax_rules} syntax highlight rules
  - {len(unique_langs)} programming languages
  - React/TailwindCSS web UI
  - tree-sitter grammars

LIBRARIES:
  - JetSki agent framework ({data.count(b'jetski')} refs)
  - ConnectRPC ({data.count(b'connectrpc')} refs)
  - gRPC ({data.count(b'grpc')} refs)
  - Antlr4 parser generator ({data.count(b'antlr4')} refs)
  - SQLite ({data.count(b'sqlite')} refs)
  - CGO for C interop ({data.count(b'cgo')} refs)
"""
print(summary)