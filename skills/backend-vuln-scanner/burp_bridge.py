#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Burp Bridge — Integracao entre Backend Vuln Scanner e CustomBurp Suite
Conecta os scanners automaticos com o proxy interativo do Burp
"""

import sys
import json
import time
import threading
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# Paths
SKILL_DIR = Path(__file__).parent
BURP_DIR = Path.home() / 'tools' / 'burpsuite-custom'
DB_PATH = BURP_DIR / 'custom_burp.db' if BURP_DIR.exists() else Path.home() / 'custom_burp.db'


class BurpBridge:
    """Ponte entre o scanner automatico e o CustomBurp"""

    def __init__(self):
        self.burp_db_path = str(DB_PATH)
        self.scanner_results = {}
        self.burp_process = None
        self.burp_running = False
        self.proxy_port = 8080
        self.web_port = 4000

    def start_burp(self, headless: bool = False) -> bool:
        """Inicia o CustomBurp Suite"""
        if self.burp_running:
            return True

        try:
            import subprocess
            cmd = [sys.executable, str(BURP_DIR / 'main.py')]
            if headless:
                cmd.extend(['--no-web'])

            self.burp_process = subprocess.Popen(
                cmd,
                cwd=str(BURP_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(2)

            if self.burp_process.poll() is None:
                self.burp_running = True
                return True
        except Exception as e:
            print(f"  [ERROR] Falha ao iniciar Burp: {e}")

        return False

    def stop_burp(self):
        """Para o CustomBurp"""
        if self.burp_process:
            try:
                self.burp_process.terminate()
                self.burp_running = False
            except:
                pass

    def get_burp_status(self) -> Dict:
        """Status do Burp"""
        status = {
            'running': self.burp_running,
            'proxy_port': self.proxy_port,
            'web_port': self.web_port,
            'db_path': str(self.burp_db_path),
        }

        # Tentar conectar ao DB para stats
        try:
            conn = sqlite3.connect(self.burp_db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM requests")
            status['requests_count'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues")
            status['issues_count'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'Critical'")
            status['critical_issues'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'High'")
            status['high_issues'] = c.fetchone()[0]
            conn.close()
        except:
            status['requests_count'] = 0
            status['issues_count'] = 0
            status['critical_issues'] = 0
            status['high_issues'] = 0

        return status

    def run_scanner_through_burp(self, target: str) -> Dict:
        """Executa scanner usando o proxy do Burp como intermediario"""
        print(f"\n[BURP BRIDGE] Running scanner through Burp proxy for {target}")

        # Iniciar Burp se necessario
        if not self.burp_running:
            print("  [BURP] Starting CustomBurp...")
            if not self.start_burp(headless=True):
                return {'error': 'Failed to start Burp Suite'}

        # Executar scanner basico
        results = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'burp_proxy': f"http://127.0.0.1:{self.proxy_port}",
            'burp_web': f"http://localhost:{self.web_port}",
            'scanner_results': {},
            'issues_from_burp': [],
        }

        # Rodar modulos de scanner
        try:
            sys.path.insert(0, str(SKILL_DIR))
            from vuln_scanner import run_scan
            scan_result = run_scan(target, verbose=False)
            results['scanner_results']['vuln_scan'] = scan_result
        except Exception as e:
            results['scanner_results']['vuln_scan'] = {'error': str(e)}

        # Query issues do Burp DB
        try:
            conn = sqlite3.connect(self.burp_db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM issues ORDER BY timestamp DESC LIMIT 20")
            for row in c.fetchall():
                issue = dict(row)
                results['issues_from_burp'].append(issue)
            conn.close()
        except Exception as e:
            results['issues_from_burp'] = []

        results['summary'] = {
            'total_vulns': len(results['issues_from_burp']),
            'critical': len([i for i in results['issues_from_burp'] if i.get('severity') == 'Critical']),
            'high': len([i for i in results['issues_from_burp'] if i.get('severity') == 'High']),
            'medium': len([i for i in results['issues_from_burp'] if i.get('severity') == 'Medium']),
        }

        return results

    def export_scan_to_burp(self, scan_result: Dict, target: str) -> bool:
        """Exporta resultados do scan para o DB do Burp"""
        try:
            conn = sqlite3.connect(self.burp_db_path)
            c = conn.cursor()

            vulns = scan_result.get('vulnerabilities', [])
            for vuln in vulns:
                issue_type = vuln.get('type', 'Unknown')
                severity = vuln.get('severity', 'Medium')
                evidence = vuln.get('evidence', '')[:200]
                description = f"{issue_type}: {evidence}"

                c.execute('''INSERT INTO issues 
                    (id, timestamp, request_id, issue_type, severity, confidence, description, evidence, solution)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (f"bridge_{int(time.time())}_{hash(issue_type)}",
                     time.time(),
                     f"auto_scan_{target}",
                     issue_type,
                     severity,
                     'High' if severity in ('CRITICAL', 'HIGH') else 'Medium',
                     description,
                     evidence,
                     'Review and remediate'))

            conn.commit()
            conn.close()
            print(f"  [EXPORT] Exported {len(vulns)} issues to Burp DB")
            return True
        except Exception as e:
            print(f"  [ERROR] Export failed: {e}")
            return False

    def get_ca_cert_path(self) -> str:
        """Retorna caminho do certificado CA do Burp"""
        ca_path = BURP_DIR / 'ca.crt'
        if ca_path.exists():
            return str(ca_path)
        # Tentar gerar
        try:
            sys.path.insert(0, str(BURP_DIR))
            from core.engine import CustomBurp
            burp = CustomBurp(str(DB_PATH), self.proxy_port)
            burp.proxy.generate_ca_cert(str(ca_path), str(BURP_DIR / 'ca.key'))
            return str(ca_path)
        except:
            return ''

    def generate_ca_cert(self) -> bool:
        """Gera certificado CA"""
        ca_path = BURP_DIR / 'ca.crt'
        key_path = BURP_DIR / 'ca.key'

        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from datetime import datetime, timedelta

            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            with open(key_path, 'wb') as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CustomBurp"),
                x509.NameAttribute(NameOID.COMMON_NAME, "CustomBurp CA"),
            ])

            cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.utcnow())
                .not_valid_after(datetime.utcnow() + timedelta(days=3650))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(key, hashes.SHA256()))

            with open(ca_path, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            print(f"  [CA] Certificate generated: {ca_path}")
            print(f"  [CA] Install in browser to intercept HTTPS")
            return True
        except ImportError:
            print("  [ERROR] cryptography module not installed")
            return False
        except Exception as e:
            print(f"  [ERROR] CA generation failed: {e}")
            return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Burp Bridge — Integracao Scanner + Burp')
    parser.add_argument('command', nargs='?', help='Comando')
    parser.add_argument('args', nargs='*', help='Argumentos')
    parser.add_argument('--target', '-t', help='Target domain')
    parser.add_argument('--start', action='store_true', help='Start Burp')
    parser.add_argument('--stop', action='store_true', help='Stop Burp')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--cert', action='store_true', help='Generate CA cert')
    parser.add_argument('--scan', action='store_true', help='Run scanner through Burp')

    args = parser.parse_args()

    bridge = BurpBridge()

    if args.start:
        if bridge.start_burp():
            print(f"[BURP] Started on port {bridge.proxy_port}")
            print(f"[BURP] Web UI: http://localhost:{bridge.web_port}")
            print(f"[BURP] Proxy: http://127.0.0.1:{bridge.proxy_port}")
        else:
            print("[BURP] Failed to start")

    elif args.stop:
        bridge.stop_burp()
        print("[BURP] Stopped")

    elif args.status:
        status = bridge.get_burp_status()
        print(f"\n[BURP STATUS]")
        print(f"  Running: {status['running']}")
        print(f"  Proxy: {status['proxy_port']}")
        print(f"  Web UI: {status['web_port']}")
        print(f"  Requests: {status.get('requests_count', 0)}")
        print(f"  Issues: {status.get('issues_count', 0)}")
        print(f"  Critical: {status.get('critical_issues', 0)}")
        print(f"  High: {status.get('high_issues', 0)}")

    elif args.cert:
        bridge.generate_ca_cert()

    elif args.scan and args.target:
        result = bridge.run_scanner_through_burp(args.target)
        print(json.dumps(result, indent=2, default=str))

    elif args.command:
        # Comandos slash
        cmd = args.command.lstrip('/')
        if cmd == 'start_burp':
            bridge.start_burp()
        elif cmd == 'stop_burp':
            bridge.stop_burp()
        elif cmd == 'status':
            print(json.dumps(bridge.get_burp_status(), indent=2))
        elif cmd == 'generate_ca':
            bridge.generate_ca_cert()
        else:
            print(f"Unknown command: {cmd}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
