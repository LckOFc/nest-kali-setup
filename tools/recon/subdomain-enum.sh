#!/bin/bash
# ============================================================
# THE FORGED NEST — Subdomain & Recon Automation
# APEX v9.0 | Passive + Active Recon Pipeline
# ============================================================
set -e

echo "═══════════════════════════════════════════════════════════"
echo "  SUBDOMAIN & RECON AUTOMATION"
echo "  ratman4080 × SHADOW × OUTCOME"
echo "═══════════════════════════════════════════════════════════"
echo ""

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
    echo "Usage: $0 <domain.com>"
    echo "  $0 example.com"
    echo "  $0 target.com --deep"
    exit 1
fi

DOMAINT=$(echo "$TARGET" | sed 's/https\?:\/\///' | sed 's/\/.*//' | sed 's/^www\.//')
OUTPUT="$HOME/.nest/results/$DOMAINT"
mkdir -p "$OUTPUT"/{subdomains,urls,javascript,paths,ports,screenshots,report}

echo "[*] Target: $DOMAINT"
echo "[*] Output: $OUTPUT"
echo ""

# ─── CHECK TOOLS ──────────────────────────────────────────
echo "[*] Checking tools..."
TOOLS=(subfinder amass httpx gowitness ffuf dirsearch waybackurls katana subjs arjun subzy nmap)
for tool in "${TOOLS[@]}"; do
    if command -v $tool &>/dev/null; then
        echo "  [OK] $tool"
    else
        echo "  [X]  $tool (install needed)"
    fi
done
echo ""

# ─── PHASE 1: PASSIVE SUBDOMAIN ENUMERATION ───────────────
echo "[*] PHASE 1: Passive Subdomain Enumeration"
echo "═══════════════════════════════════════════════════════════"

# subfinder
if command -v subfinder &>/dev/null; then
    echo "[*] Running subfinder..."
    subfinder -d $DOMAINT -o "$OUTPUT/subdomains/subfinder.txt" -silent 2>/dev/null || true
fi

# amass (passive only)
if command -v amass &>/dev/null; then
    echo "[*] Running amass (passive)..."
    amass enum -passive -d $DOMAINT -o "$OUTPUT/subdomains/amass_passive.txt" 2>/dev/null || true
fi

# assetfinder
if command -v assetfinder &>/dev/null; then
    echo "[*] Running assetfinder..."
    assetfinder --subs-only $DOMAINT > "$OUTPUT/subdomains/assetfinder.txt" 2>/dev/null || true
fi

# sublist3r
if command -v sublist3r &>/dev/null; then
    echo "[*] Running sublist3r..."
    sublist3r -d $DOMAINT -o "$OUTPUT/subdomains/sublist3r.txt" 2>/dev/null || true
fi

# OneForAll (comprehensive)
if command -v python3 &>/dev/null; then
    echo "[*] Running OneForAll..."
    git clone --depth 1 https://github.com/shmilylty/OneForAll.git "$OUTPUT/OneForAll" 2>/dev/null || true
    if [ -f "$OUTPUT/OneForAll/oneforall.py" ]; then
        cd "$OUTPUT/OneForAll" && python3 oneforall.py run --target $DOMAINT --format txt 2>/dev/null || true
        if [ -f "$OUTPUT/OneForAll/save/results/$DOMAINT.txt" ]; then
            cp "$OUTPUT/OneForAll/save/results/$DOMAINT.txt" "$OUTPUT/subdomains/oneforall.txt"
        fi
        cd - >/dev/null
    fi
fi

echo "[OK] Phase 1 complete"
echo ""

# ─── PHASE 2: ACTIVE SUBDOMAIN BRUTE FORCE ────────────────
echo "[*] PHASE 2: Active Subdomain Brute Force"
echo "═══════════════════════════════════════════════════════════"

# ffuf with wordlist
if command -v ffuf &>/dev/null; then
    WORDLIST="/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt"
    if [ ! -f "$WORDLIST" ]; then
        WORDLIST="$HOME/.nest/tools/subdomains-top1million.txt"
    fi
    if [ -f "$WORDLIST" ]; then
        echo "[*] Running ffuf brute force..."
        ffuf -w "$WORDLIST" -u https://FUZZ.$DOMAINT -H "Host: FUZZ.$DOMAINT" -fs 0 -c -o "$OUTPUT/subdomains/ffuf.json" 2>/dev/null || true
        if [ -f "$OUTPUT/subdomains/ffuf.json" ]; then
            cat "$OUTPUT/subdomains/ffuf.json" | jq -r '.results[] | .input' 2>/dev/null | sort -u > "$OUTPUT/subdomains/ffuf.txt" || true
        fi
    else
        echo "[!] Wordlist not found. Download from SecLists."
    fi
fi

# amass (active)
if command -v amass &>/dev/null; then
    echo "[*] Running amass (active)..."
    amass enum -d $DOMAINT -o "$OUTPUT/subdomains/amass_active.txt" 2>/dev/null || true
fi

echo "[OK] Phase 2 complete"
echo ""

# ─── PHASE 3: MERGE & RESOLVE ─────────────────────────────
echo "[*] PHASE 3: Merging & Resolving"
echo "═══════════════════════════════════════════════════════════"

cat "$OUTPUT"/subdomains/*.txt 2>/dev/null | sort -u | grep -v "^$" > "$OUTPUT/subdomains/merged.txt" || true
TOTAL_SUBDOMAINS=$(wc -l < "$OUTPUT/subdomains/merged.txt" 2>/dev/null || echo "0")
echo "[*] Total unique subdomains: $TOTAL_SUBDOMAINS"
echo ""

# ─── PHASE 4: LIVE DOMAIN PROBING ────────────────────────
echo "[*] PHASE 4: Live Domain Probing"
echo "═══════════════════════════════════════════════════════════"

if command -v httpx &>/dev/null; then
    echo "[*] Running httpx..."
    httpx -l "$OUTPUT/subdomains/merged.txt" -silent -mc 200,301,302,403 -o "$OUTPUT/subdomains/live.txt" 2>/dev/null || true
    LIVE_COUNT=$(wc -l < "$OUTPUT/subdomains/live.txt" 2>/dev/null || echo "0")
    echo "[*] Live domains: $LIVE_COUNT"
else
    echo "[!] httpx not installed. Use: go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest"
fi
echo ""

# ─── PHASE 5: SCREENSHOTS ─────────────────────────────────
echo "[*] PHASE 5: Screenshoting"
echo "═══════════════════════════════════════════════════════════"

if command -v gowitness &>/dev/null; then
    echo "[*] Running gowitness..."
    mkdir -p "$OUTPUT/screenshots"
    gowitness file -f "$OUTPUT/subdomains/live.txt" -p "$OUTPUT/screenshots/" 2>/dev/null || true
    echo "[OK] Screenshots saved to $OUTPUT/screenshots/"
else
    echo "[!] gowitness not installed. Use: go install github.com/sensepost/gowitness@latest"
fi
echo ""

# ─── PHASE 6: URL DISCOVERY ───────────────────────────────
echo "[*] PHASE 6: URL Discovery"
echo "═══════════════════════════════════════════════════════════"

if command -v katana &>/dev/null; then
    echo "[*] Running katana..."
    for domain in $(head -20 "$OUTPUT/subdomains/live.txt" 2>/dev/null); do
        katana -u "$domain" -flags fuzzer -d 3 -c 10 -retry 2 -json -o "$OUTPUT/urls/katana_$DOMAINT.json" 2>/dev/null || true
    done
fi

if command -v waybackurls &>/dev/null; then
    echo "[*] Running waybackurls..."
    waybackurls $DOMAINT > "$OUTPUT/urls/wayback.txt" 2>/dev/null || true
    for sub in $(head -10 "$OUTPUT/subdomains/live.txt" 2>/dev/null); do
        waybackurls $sub >> "$OUTPUT/urls/wayback.txt" 2>/dev/null || true
    done
    sort -u "$OUTPUT/urls/wayback.txt" -o "$OUTPUT/urls/wayback.txt"
fi
echo ""

# ─── PHASE 7: JAVASCRIPT ENUMERATION ─────────────────────
echo "[*] PHASE 7: JavaScript Analysis"
echo "═══════════════════════════════════════════════════════════"

if command -v subjs &>/dev/null; then
    echo "[*] Running subjs..."
    subjs -u "$DOMAIN" -o "$OUTPUT/javascript/subjs.txt" 2>/dev/null || true
    for domain in $(head -10 "$OUTPUT/subdomains/live.txt" 2>/dev/null); do
        subjs -u "$domain" >> "$OUTPUT/javascript/subjs.txt" 2>/dev/null || true
    done
    sort -u "$OUTPUT/javascript/subjs.txt" -o "$OUTPUT/javascript/subjs.txt"
fi
echo ""

# ─── PHASE 8: PATH DISCOVERY ─────────────────────────────
echo "[*] PHASE 8: Path Discovery"
echo "═══════════════════════════════════════════════════════════"

if command -v ffuf &>/dev/null; then
    WORDLIST_DIR="/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt"
    if [ ! -f "$WORDLIST_DIR" ]; then
        WORDLIST_DIR="$HOME/.nest/tools/directory-list-2.3-medium.txt"
    fi
    if [ -f "$WORDLIST_DIR" ]; then
        echo "[*] Running ffuf path discovery (first 5 domains)..."
        head -5 "$OUTPUT/subdomains/live.txt" 2>/dev/null | while read domain; do
            ffuf -w "$WORDLIST_DIR" -u "$domain/FUZZ" -H "User-Agent: Mozilla/5.0" -mc 200,301,302,403 -c -t 50 2>/dev/null | grep -E "^\[2[0-9]{2}" | awk '{print $2}' >> "$OUTPUT/paths/ffuf_paths.txt" || true
        done
    fi
fi

if command -v dirsearch &>/dev/null; then
    echo "[*] Running dirsearch..."
    dirsearch -l "$OUTPUT/subdomains/live.txt" -e php,html,js,xml,backup -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -t 25 --timeout 10 2>/dev/null || true
fi
echo ""

# ─── PHASE 9: PARAMETER DISCOVERY ─────────────────────────
echo "[*] PHASE 9: Parameter Discovery"
echo "═══════════════════════════════════════════════════════════"

if command -v arjun &>/dev/null; then
    echo "[*] Running arjun..."
    arjun -u "https://$DOMAINT" -m get -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-dev.txt 2>/dev/null || true
fi
echo ""

# ─── PHASE 10: PORT SCANNING ──────────────────────────────
echo "[*] PHASE 10: Port Scanning"
echo "═══════════════════════════════════════════════════════════"

if command -v nmap &>/dev/null; then
    echo "[*] Running nmap (top ports)..."
    for ip in $(cat "$OUTPUT/subdomains/live.txt" 2>/dev/null | head -10); do
        # Resolve to IP
        IP=$(dig +short $ip 2>/dev/null | head -1)
        if [ -n "$IP" ]; then
            echo "[*] Scanning $ip ($IP)..."
            nmap -T4 -sC -sV -p- --min-rate 1000 $IP -oN "$OUTPUT/ports/$(echo $IP | tr '.' '_').nmap" 2>/dev/null || true
        fi
    done
fi
echo ""

# ─── PHASE 11: SUBDOMAIN TAKEOVER CHECK ──────────────────
echo "[*] PHASE 11: Subdomain Takeover Check"
echo "═══════════════════════════════════════════════════════════"

if command -v subzy &>/dev/null; then
    echo "[*] Running subzy..."
    subzy scan --target-file "$OUTPUT/subdomains/live.txt" --root-domain $DOMAINT 2>/dev/null || true
fi
echo ""

# ─── GENERATE REPORT ──────────────────────────────────────
echo "[*] PHASE 12: Generating Report"
echo "═══════════════════════════════════════════════════════════"

REPORT="$OUTPUT/report/report_$DOMAINT.md"
cat > "$REPORT" << EOF
# Recon Report: $DOMAINT
Generated: $(date)

## Summary
- Total Subdomains: $TOTAL_SUBDOMAINS
- Live Domains: $(wc -l < "$OUTPUT/subdomains/live.txt" 2>/dev/null || echo "0")

## Subdomains
### All Found
\`\`\`
$(cat "$OUTPUT/subdomains/merged.txt" 2>/dev/null | head -100)
\`\`\`

### Live Domains
\`\`\`
$(cat "$OUTPUT/subdomains/live.txt" 2>/dev/null)
\`\`\`

## Links
- [Screenshots](./screenshots/)
- [Full Report](./report/)
- [Subdomains](./subdomains/)
- [URLs](./urls/)
- [JavaScript](./javascript/)
- [Paths](./paths/)
- [Ports](./ports/)

---
**THE FORGED NEST — Subdomain Automation**
EOF

echo "[OK] Report saved to $REPORT"
echo ""

# ─── CLEANUP ──────────────────────────────────────────────
echo "[*] Cleanup..."
rm -rf "$OUTPUT/OneForAll" 2>/dev/null || true
echo "[OK] Cleanup complete"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  RECON COMPLETE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Results: $OUTPUT"
echo "Report:  $REPORT"
echo ""
echo "Next steps:"
echo "  - Check screenshots: $OUTPUT/screenshots/"
echo "  - Review paths: $OUTPUT/paths/"
echo "  - Analyze JS: $OUTPUT/javascript/"
echo ""
echo "cold wire. warm scent. gnaw through. find home."
