# THE FORGED NEST — Skills Index

This directory contains all opencode skills for the system.

## Available Skills

### full-hacking-toolkit
Complete hacking suite orchestrating:
- RE Toolkit (7 engines)
- Burp Suite v2
- Backend Vulnerability Scanner
- OSINT Aggregator
- Password Cracker
- Payload Manager (539+ payloads)
- Report Generator
- Shadow Toolkit v36.1
- JWT Brute Force
- GraphQL Attack Engine
- Race Condition Automator
- Exploit Chaining (6 chains)

### advanced-exploits
- JWT Brute Force v2.1
- GraphQL Attack Engine v2.1
- Race Condition Automator v2.1
- Exploit Chaining v2.1 (6 chains)

### advanced-re
- Anti-anti-debug bypass
- Devirtualization (VMProtect/Themida)
- Anti-sandbox detection
- Go/Rust analysis
- String decryption (XOR/AES/Base64)
- Pattern matching with IA

### shadow-toolkit
- Cloudflare bypass (curl_cffi)
- JWT analysis
- Vulnerability scanning
- Auto-exploit pipeline
- WebSocket real-time capture

## Installation

Copy skill directories from Windows:

```bash
cp -r /mnt/c/Users/devel/.config/opencode/skills/* ~/.nest/skills/
```

Or use WSL sync:

```bash
wsl -d kali-linux --user root -- bash -c "rsync -av /mnt/c/Users/devel/.config/opencode/skills/ /home/lck/.nest/skills/"
```

---

**cold wire. warm scent. gnaw through. find home.**
