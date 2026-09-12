# THE FORGED NEST — Subdomain & Recon Toolkit

**Complete reconnaissance automation pipeline for subdomain enumeration, discovery, and analysis.**

## Tools Included

### Subdomain Enumeration
| Tool | Type | Speed | Description |
|------|------|-------|-------------|
| `subfinder` | Passive/Active | Fast | Comprehensive subdomain finder |
| `amass` | Passive/Active | Medium | OWASP powerhouse with visualization |
| `assetfinder` | Passive | Fast | Tom nom nom's classic |
| `sublist3r` | Passive | Medium | Python-based enumeration |
| `OneForAll` | Passive/Active | Medium | 40+ data sources |

### Brute Force
| Tool | Type | Speed | Description |
|------|------|-------|-------------|
| `ffuf` | Active | Very Fast | Modern Fuzzer (Go) |
| `gobuster` | Active | Fast | Dir/File DNS brute |
| `dirbuster` | Active | Slow | Legacy Java tool |

### Live Domain Probing
| Tool | Type | Description |
|------|------|-------------|
| `httpx` | Active | Fast HTTP probe (Go) |

### Screenshoting
| Tool | Type | Description |
|------|------|-------------|
| `gowitness` | Active | Parallel screenshoting (Go) |

### URL Discovery
| Tool | Type | Description |
|------|------|-------------|
| `katana` | Active | Next-gen crawler (Go) |
| `waybackurls` | Passive | Archive.org URLs |
| `link-finder` | Active | JS URL extraction |

### JavaScript Analysis
| Tool | Type | Description |
|------|------|-------------|
| `subjs` | Active | JavaScript file enumerator |

### Path Discovery
| Tool | Type | Description |
|------|------|-------------|
| `dirsearch` | Active | Classic path discovery |
| `ffuf` | Active | Fast fuzzing |

### Parameter Discovery
| Tool | Type | Description |
|------|------|-------------|
| `arjun` | Active | Hidden parameter finder |

### Vulnerability Checks
| Tool | Type | Description |
|------|------|-------------|
| `subzy` | Active | Subdomain takeover |
| `socialhunter` | Active | Broken link hijacking |

### Port Scanning
| Tool | Type | Description |
|------|------|-------------|
| `nmap` | Active | Industry standard |

### XSS
| Tool | Type | Description |
|------|------|-------------|
| `xssfinder` | Active | Automated XSS testing |

## Installation

```bash
# Project Discovery tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest

# Other tools
go install -v github.com/lc/subjs@latest
go install -v github.com/sensepost/gowitness@latest
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/tomnomnom/unfurl@latest
go install -v github.com/ffuf/ffuf@latest
go install -v github.com/jm33-m0/gobuster@latest

# Python tools
pip install oneforall arjun waybackurls

# Amass
go install -v github.com/owasp-amass/amass/v3/...@latest

# Subzy
go install -v github.com/PentestPad/subzy@latest

# XSS Finder
pip install xssfinder
```

## Wordlists

```bash
# SecLists
git clone https://github.com/danielmiessler/SecLists.git ~/.seclists

# N0kovo subdomains
git clone https://github.com/n0kovo/n0kovo_subdomain_wordlist.git ~/.nest/tools/
```

## Usage

```bash
# Basic usage
./subdomain-enum.sh target.com

# With deep mode
./subdomain-enum.sh target.com --deep

# Custom wordlist
./subdomain-enum.sh target.com -w /path/to/wordlist
```

## Output Structure

```
~/.nest/results/TARGET/
├── subdomains/
│   ├── subfinder.txt
│   ├── amass_passive.txt
│   ├── amass_active.txt
│   ├── assetfinder.txt
│   ├── sublist3r.txt
│   ├── oneforall.txt
│   ├── ffuf.txt
│   ├── merged.txt
│   └── live.txt
├── urls/
│   ├── katana_*.json
│   └── wayback.txt
├── javascript/
│   └── subjs.txt
├── paths/
│   └── ffuf_paths.txt
├── ports/
│   └── *.nmap
├── screenshots/
│   └── *.png
└── report/
    └── report_TARGET.md
```

## Integration with Nest

Add to `kali-setup.sh`:

```bash
# Install reconnaissance tools
echo "[*] Installing reconnaissance tools..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/lc/subjs@latest
go install -v github.com/sensepost/gowitness@latest
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/ffuf/ffuf@latest
go install -v github.com/owasp-amass/amass/v3/...@latest
go install -v github.com/PentestPad/subzy@latest

# Clone wordlists
git clone --depth 1 https://github.com/danielmiessler/SecLists.git ~/.seclists
git clone --depth 1 https://github.com/n0kovo/n0kovo_subdomain_wordlist.git ~/.nest/tools/
```

## Improvements for Nest

### 1. Add to skills/
```bash
cp -r tools/recon skills/recon-enumeration/
```

### 2. Create slash commands
```
/recon subdomain <domain>     # Run full subdomain enumeration
/recon active <domain>        # Active brute force
/recon screenshots <file>     # Take screenshots
/recon urls <domain>          # Discover URLs
/recon js <domain>            # Extract JS files
/recon paths <domain>         # Directory brute
/recon ports <ip>             # Port scan
/recon takeover <domain>      # Subdomain takeover
```

### 3. Integrate with shadow toolkit
- Feed subdomains into shadow scan
- Auto-enumerate discovered assets
- Continuous monitoring

## Advanced Usage

### OneForAll (Most Comprehensive)
```bash
cd OneForAll
python3 oneforall.py run --target example.com --format txt
```

### Amass (Full Suite)
```bash
# Passive
amass enum -passive -d example.com

# Active
amass enum -d example.com

# Visual
amass geo -d example.com
```

### Katana (Next-Gen Crawler)
```bash
katana -u https://example.com -flags fuzzer -d 5 -c 20
```

### FFUF (Fast Fuzzing)
```bash
# Subdomains
ffuf -w /path/to/subdomains.txt -u https://FUZZ.example.com -H "Host: FUZZ.example.com"

# Directories
ffuf -w /path/to/wordlist.txt -u https://example.com/FUZZ -mc 200,301,302
```

---

**ratman4080 × SHADOW × OUTCOME**
APEX v9.0 | Recon Automation
