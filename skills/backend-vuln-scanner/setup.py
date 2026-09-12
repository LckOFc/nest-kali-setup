#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Vulnerability Scanner — Setup e Instalacao
Instala todas as dependencias e configura o ambiente
"""

import sys
import subprocess
import os
from pathlib import Path


def run(cmd, desc):
    print(f"  [SETUP] {desc}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *cmd],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  [OK] {' '.join(cmd)}")
        return True
    except Exception as e:
        print(f"  [WARN] {' '.join(cmd)}: {e}")
        return False


def check_module(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def main():
    print("=" * 60)
    print("  Backend Vulnerability Scanner — Setup")
    print("=" * 60)
    print()

    # Core dependencies
    core = [
        (['requests'], 'HTTP requests'),
        (['urllib3'], 'HTTP library'),
        (['cryptography'], 'SSL/TLS and crypto'),
    ]

    # Browser automation
    browser = [
        (['selenium', 'webdriver-manager'], 'Browser automation'),
    ]

    # Optional
    optional = [
        (['flask'], 'Web UI (Burp)'),
        (['graphql'], 'GraphQL support'),
    ]

    print("[1/3] Core dependencies")
    for cmd, desc in core:
        if not all(check_module(m.split('[')[0].split()[0]) for m in cmd):
            run(cmd, desc)

    print()
    print("[2/3] Browser automation (Selenium)")
    for cmd, desc in browser:
        if not all(check_module(m.split('[')[0].split()[0]) for m in cmd):
            run(cmd, desc)

    print()
    print("[3/3] Optional dependencies")
    for cmd, desc in optional:
        if not all(check_module(m.split('[')[0].split()[0]) for m in cmd):
            run(cmd, desc)

    # Generate CA cert
    print()
    print("[4/4] Generate CA certificate")
    try:
        from burp_bridge import BurpBridge
        bridge = BurpBridge()
        ca_path = bridge.get_ca_cert_path()
        if not ca_path or not Path(ca_path).exists():
            bridge.generate_ca_cert()
        print(f"  [OK] CA certificate ready")
    except Exception as e:
        print(f"  [INFO] CA cert generation skipped: {e}")

    # Verify all modules
    print()
    print("[VERIFY] Checking all modules...")
    skill_dir = Path(__file__).parent
    modules = [
        'vuln_scanner', 'complete_scanner', 'jwt_analyzer', 'token_hunter',
        'graphql_scanner', 'framework_scanner', 'waf_bypass', 'oauth_scanner',
        'web_crawler', 'header_scanner', 'directory_buster', 'cors_scanner',
        'parameter_fuzzer', 'exploit_executor', 'brute_force', 'subdomain_enum',
        'data_extractor', 'mass_scanner', 'burp_bridge',
    ]

    ok = 0
    for mod in modules:
        path = skill_dir / f"{mod}.py"
        if path.exists():
            try:
                sys.path.insert(0, str(skill_dir))
                __import__(mod)
                print(f"  [OK] {mod}")
                ok += 1
            except Exception as e:
                print(f"  [FAIL] {mod}: {e}")
        else:
            print(f"  [MISS] {mod}.py")

    print()
    print("=" * 60)
    print(f"  Setup complete: {ok}/{len(modules)} modules OK")
    print("=" * 60)
    print()
    print("  Quick start:")
    print("    python integration.py /vuln_quick <dominio>")
    print("    python integration.py /jwt_hunt <dominio>")
    print("    python integration.py /burp_start")
    print()


if __name__ == "__main__":
    main()
