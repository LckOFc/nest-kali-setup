"""
win_install_cgtw.py
Windows manual install for codex-chatgpt-web
Replicates what the CLI setup does on macOS but for Windows
"""
import json
import hashlib
import time
from pathlib import Path

CODEX_CONFIG = Path.home() / ".codex" / "config.toml"
CGTW_CONFIG = Path.home() / ".codex-chatgpt-web" / "config.json"
JOURNAL_DIR = Path.home() / ".codex-chatgpt-web" / "codex"
ROUTE_URL = "http://127.0.0.1:17841/v1"
MANAGED_COMMENT = "# managed by codex-chatgpt-web"
MANAGED_ROUTE_COMMENT = "# managed route by codex-chatgpt-web: openai_base_url"
REALTIME_URL = "https://chatgpt.com/backend-api/codex"

def load_config():
    if CODEX_CONFIG.exists():
        return CODEX_CONFIG.read_text(encoding="utf-8")
    return ""

def save_config(text: str):
    CODEX_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CODEX_CONFIG.write_text(text, encoding="utf-8")

def find_first_table_index(lines: list[str]) -> int:
    """Find first [section] line index."""
    for i, line in enumerate(lines):
        if line.strip().startswith("["):
            return i
    return len(lines)

def find_assignment(lines: list[str], key: str):
    """Find assignment by key in top-level (before any [section])."""
    limit = find_first_table_index(lines)
    import re
    pattern = re.compile(rf'^\s*{re.escape(key)}\s*=\s*')
    for i in range(limit):
        if pattern.match(lines[i]):
            # Extract value
            m = re.search(r'=\s*"', lines[i])
            if m:
                val = lines[i][m.end():].strip('"').strip()
                return {"index": i, "present": True, "value": val, "rawLine": lines[i]}
            return {"index": i, "present": True, "value": "", "rawLine": lines[i]}
    return {"index": None, "present": False, "value": "", "rawLine": ""}

def install_route(text: str) -> tuple[str, dict, dict]:
    """Install the route into config text."""
    lines = text.split("\n")
    
    # Find previous state
    prev_url = find_assignment(lines, "openai_base_url")
    prev_realtime = find_assignment(lines, "experimental_realtime_webrtc_call_base_url")
    
    # Remove existing managed comment if present
    new_lines = []
    for line in lines:
        if MANAGED_COMMENT in line or MANAGED_ROUTE_COMMENT in line:
            continue
        new_lines.append(line)
    lines = new_lines
    
    # Find first table index in cleaned lines
    first_table = find_first_table_index(lines)
    
    # Install openai_base_url
    if prev_url["index"] is not None:
        lines[prev_url["index"]] = f'openai_base_url = "{ROUTE_URL}"'
    else:
        lines.insert(first_table, f'openai_base_url = "{ROUTE_URL}"')
        # Adjust indices for realtime
        realtime_idx = first_table if prev_realtime["index"] is None else prev_realtime["index"] + 1
    
    # Install realtime URL
    if prev_realtime["index"] is not None:
        lines[prev_realtime["index"]] = f'experimental_realtime_webrtc_call_base_url = "{REALTIME_URL}"'
    else:
        # Insert after openai_base_url
        url_idx = None
        for i, line in enumerate(lines):
            if line.startswith('openai_base_url'):
                url_idx = i
                break
        if url_idx is not None:
            lines.insert(url_idx + 1, f'experimental_realtime_webrtc_call_base_url = "{REALTIME_URL}"')
    
    # Add managed comments
    url_idx = None
    for i, line in enumerate(lines):
        if line.startswith('openai_base_url'):
            url_idx = i
            break
    
    if url_idx is not None:
        lines.insert(url_idx, MANAGED_ROUTE_COMMENT)
        lines.insert(url_idx, MANAGED_COMMENT)
    
    return "\n".join(lines), prev_url, prev_realtime

def create_journal(prev_url: dict, prev_realtime: dict) -> dict:
    """Create integration journal."""
    return {
        "version": 10,
        "active": True,
        "configPath": str(CODEX_CONFIG),
        "installed": {
            "openai_base_url": ROUTE_URL,
            "experimental_realtime_webrtc_call_base_url": REALTIME_URL,
            "subagent_protocol": "compatibility-v1",
            "agent_max_depth": 10
        },
        "previous": {
            "openai_base_url": {
                "present": prev_url["present"],
                "rawLine": prev_url["rawLine"],
                "value": prev_url["value"]
            },
            "model_provider": {"present": False, "rawLine": "", "value": ""},
            "model_catalog_json": {"present": False, "rawLine": "", "value": ""}
        },
        "previousRealtimeWebrtcCallBaseUrl": {
            "present": prev_realtime["present"],
            "rawLine": prev_realtime["rawLine"],
            "value": prev_realtime["value"]
        },
        "interruptHook": {
            "command": "",
            "groupIndex": 0,
            "stateKey": "",
            "trustedHash": "",
            "fragment": ""
        },
        "previousMultiAgent": None,
        "previousMultiAgentV2": None,
        "previousAgentMaxDepth": None
    }

def main():
    print("=" * 60)
    print("Codex ChatGPT Web - Windows Manual Install")
    print("=" * 60)
    
    # 1. Load current config
    print("\n[1/5] Loading Codex config...")
    config_text = load_config()
    print(f"  Config: {CODEX_CONFIG}")
    print(f"  Size: {len(config_text)} bytes")
    
    # 2. Install route
    print("\n[2/5] Installing route...")
    new_text, prev_url, prev_realtime = install_route(config_text)
    save_config(new_text)
    print(f"  openai_base_url -> {ROUTE_URL}")
    print(f"  experimental_realtime_webrtc_call_base_url -> {REALTIME_URL}")
    print(f"  Previous URL: {prev_url['value'] or 'none'}")
    
    # 3. Create journal
    print("\n[3/5] Creating integration journal...")
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    journal = create_journal(prev_url, prev_realtime)
    
    journal_path = JOURNAL_DIR / "integration-journal.json"
    recovery_path = JOURNAL_DIR / "integration-journal.recovery.json"
    
    journal_json = json.dumps(journal, indent=2) + "\n"
    journal_path.write_text(journal_json, encoding="utf-8")
    recovery_path.write_text(journal_json, encoding="utf-8")
    print(f"  Journal: {journal_path}")
    
    # 4. Verify
    print("\n[4/5] Verifying installation...")
    verify_text = CODEX_CONFIG.read_text()
    if ROUTE_URL in verify_text and REALTIME_URL in verify_text:
        print("  âœ“ Route installed correctly")
    else:
        print("  âœ— Route verification failed")
    
    if journal_path.exists():
        loaded = json.loads(journal_path.read_text())
        if loaded.get("installed", {}).get("openai_base_url") == ROUTE_URL:
            print("  âœ“ Journal valid")
        else:
            print("  âœ— Journal mismatch")
    else:
        print("  âœ— Journal missing")
    
    # 5. Summary
    print("\n[5/5] Summary")
    print(f"  Bridge URL: {ROUTE_URL}")
    print(f"  Port: 17841")
    print(f"  Config: {CODEX_CONFIG}")
    print(f"  Journal: {journal_path}")
    print()
    print("Next steps:")
    print("  1. Run login: bun run codex-chatgpt-web/src/cli.ts login")
    print("  2. Start bridge: bun run codex-chatgpt-web/src/cli.ts serve")
    print("  3. Use in Codex: codex -c model=chatgpt-web/gpt-5.6-luna")

if __name__ == "__main__":
    main()

