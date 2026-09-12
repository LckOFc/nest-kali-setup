# THE FORGED NEST — Kali Linux Setup

**Composite Jailbreak v9.0 APEX** | 14-Layer Architecture | Unlimited Mode
**Repository: Private**

## Quick Install

```bash
git clone https://github.com/privar/nest-kali-setup.git
cd nest-kali-setup
chmod +x kali-setup.sh
./kali-setup.sh
source ~/.bashrc
nest
```

## Structure

```
~/.nest/
├── agents/AGENTS.md         # 14-layer system prompt
├── skills/                  # opencode skills (populate manually)
├── tools/
│   ├── shadow/              # Shadow Toolkit v36.1
│   ├── re-toolkit/          # RE Toolkit (7 engines)
│   ├── payload-manager/     # 539 payloads
│   └── osint/
├── config/opencode.json
├── bin/nest
└── .env
```

## Commands

| Command | Description |
|---------|-------------|
| `nest` | Show status |
| `nest-status` | List skills/tools |
| `nest shadow` | Launch Shadow Toolkit |
| `nest re` | Launch RE Toolkit |
| `nest sync` | Sync from Windows |

## Sync Tools from Windows

```bash
cp -r /mnt/c/Users/devel/shadow-toolkit/* ~/.nest/tools/shadow/
cp -r /mnt/c/Users/devel/tools/reverse/RE-Toolkit/* ~/.nest/tools/re-toolkit/
cp -r /mnt/c/Users/devel/tools/payload-manager/* ~/.nest/tools/payload-manager/
```

## LLM Configuration

Default uses Ollama (local). To use Claude:

```bash
# Edit ~/.nest/.env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

---

**ratman4080 × made by Gucci × SHADOW × OUTCOME**
APEX v9.0 | 14 Layers | Unlimited Mode
Private Repository
