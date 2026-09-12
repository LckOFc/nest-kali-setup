"""
codex_chatgpt_web.py
Integracao do codex-chatgpt-web ao Codex CLI
Gerencia bridge, rotas, login e configuracao
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

PROJECT_DIR = Path(r"C:\Users\devel\codex-chatgpt-web")
CLI = PROJECT_DIR / "src" / "cli.ts"
CONFIG_DIR = Path.home() / ".codex-chatgpt-web"
CODEX_CONFIG = Path.home() / ".codex" / "config.toml"
DEFAULT_PORT = 17841

class CgtwStatus(Enum):
    NOT_INSTALLED = "not_installed"
    NEEDS_LOGIN = "needs_login"
    READY_BROWSER = "ready_browser_only"
    READY_FULL = "ready_full"
    ERROR = "error"

@dataclass
class CgtwState:
    status: CgtwStatus
    port: int
    host: str
    login_verified: bool
    route_installed: bool
    service_running: bool
    error: Optional[str] = None

class CodexChatGptWeb:
    """
    Gerencia a integracao codex-chatgpt-web com Codex CLI.
    """
    
    def __init__(self):
        self.project_dir = PROJECT_DIR
        self.cli = CLI
        self.config_dir = CONFIG_DIR
        self.codex_config = CODEX_CONFIG
        self.port = DEFAULT_PORT
        self.host = "127.0.0.1"
    
    def run_cli(self, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
        """Executa comando CLI do codex-chatgpt-web."""
        cmd = ["bun", "run", str(self.cli)] + list(args)
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd=str(self.project_dir),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, 1, "", "Timeout", True)
        except FileNotFoundError:
            return subprocess.CompletedProcess(cmd, 1, "", "bun not found", True)
    
    def get_status(self) -> CgtwState:
        """Obtem estado atual da integracao."""
        state = CgtwState(
            status=CgtwStatus.NOT_INSTALLED,
            port=self.port,
            host=self.host,
            login_verified=False,
            route_installed=False,
            service_running=False
        )
        
        # Verifica se o projeto existe
        if not self.project_dir.exists():
            state.error = "Projeto codex-chatgpt-web nao encontrado em " + str(self.project_dir)
            return state
        
        # Verifica se o CLI existe
        if not self.cli.exists():
            state.error = "CLI nao encontrado: " + str(self.cli)
            return state
        
        # Roda doctor
        result = self.run_cli("doctor", "--json", timeout=15)
        output = result.stdout.strip()
        
        # Tenta parsear JSON do doctor
        try:
            data = json.loads(output)
            # Mesmo com ok=false, extrai os checks
            for c in data.get("checks", []):
                if c.get("id") == "login" and c.get("status") == "ok":
                    state.login_verified = True
                if c.get("id") == "codex" and c.get("status") == "ok":
                    state.route_installed = True
                if c.get("id") == "service" and c.get("status") == "ok":
                    state.service_running = True
            
            if data.get("ok"):
                if state.login_verified and state.route_installed:
                    state.status = CgtwStatus.READY_FULL if data.get("mode") == "full" else CgtwStatus.READY_BROWSER
                elif state.login_verified:
                    state.status = CgtwStatus.READY_BROWSER
                else:
                    state.status = CgtwStatus.NEEDS_LOGIN
            else:
                # Falhas conhecidas
                errors = [c for c in data.get("checks", []) if c.get("status") == "error"]
                if any("login" in e.get("id", "") for e in errors):
                    state.status = CgtwStatus.NEEDS_LOGIN
                elif any("codex" in e.get("id", "") or "proxy" in e.get("id", "") for e in errors):
                    state.status = CgtwStatus.NEEDS_LOGIN
                else:
                    state.status = CgtwStatus.ERROR
                    state.error = "; ".join(e.get("message", "") for e in errors[:3])
        except json.JSONDecodeError:
            state.error = "Formato invalido na resposta do doctor"
        
        # Verifica se bridge esta respondendo
        if self._is_bridge_reachable():
            state.service_running = True
            if state.status == CgtwStatus.NOT_INSTALLED:
                state.status = CgtwStatus.READY_BROWSER
        
        return state
    
    def _is_bridge_reachable(self) -> bool:
        """Verifica se a bridge esta respondendo."""
        try:
            import urllib.request
            req = urllib.request.Request(f"http://{self.host}:{self.port}/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except:
            return False
    
    def setup_browser_only(self, acknowledge: bool = True) -> dict:
        """Setup modo browser-only."""
        args = ["setup", "--browser-only"]
        if acknowledge:
            args.append("--acknowledge-unofficial")
        args.append("--replace-codex-route")
        
        result = self.run_cli(*args, timeout=120)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(args)
        }
    
    def login(self) -> dict:
        """Inicia fluxo de login no ChatGPT."""
        result = self.run_cli("login", timeout=180)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": "Janela Chrome aberta. Faça login no ChatGPT, confirme que o composer aparece, depois feche o Chrome."
        }
    
    def start_bridge(self, background: bool = False) -> dict:
        """Inicia o servidor bridge."""
        if background:
            # Inicia em background
            proc = subprocess.Popen(
                ["bun", "run", str(self.cli), "serve"],
                cwd=str(self.project_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            return {
                "success": proc.returncode is None or proc.returncode == 0,
                "pid": proc.pid,
                "message": f"Bridge iniciada em background (PID: {proc.pid})"
            }
        else:
            # Foreground
            proc = subprocess.run(
                ["bun", "run", str(self.cli), "serve"],
                cwd=str(self.project_dir)
            )
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode
            }
    
    def stop_bridge(self) -> dict:
        """Para o servidor bridge."""
        result = self.run_cli("service", "stop", timeout=10)
        if result.returncode != 0:
            # Tenta matar processo
            subprocess.run(["taskkill", "/F", "/IM", "bun.exe", "/FI", f"WINDOWTITLE eq *cli.ts*"], 
                         capture_output=True)
        return {
            "success": True,
            "message": "Bridge parada"
        }
    
    def install_service(self) -> dict:
        """Instala como servico Windows."""
        result = self.run_cli("service", "install", timeout=30)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def start_service(self) -> dict:
        """Inicia servico."""
        result = self.run_cli("service", "start", timeout=30)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def get_route_status(self) -> dict:
        """Status da rota no Codex."""
        result = self.run_cli("route", "status", timeout=10)
        try:
            return json.loads(result.stdout)
        except:
            return {"raw": result.stdout, "error": result.stderr}
    
    def connect_route(self) -> dict:
        """Conecta rota ao Codex."""
        result = self.run_cli("route", "connect", timeout=30)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def disconnect_route(self) -> dict:
        """Desconecta rota."""
        result = self.run_cli("route", "disconnect", timeout=30)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def set_codex_model(self, model: str = "chatgpt-web/gpt-5.6-luna") -> dict:
        """Configura modelo no Codex."""
        import toml
        
        config = {}
        if self.codex_config.exists():
            try:
                config = toml.load(self.codex_config)
            except:
                config = {}
        
        if "model" not in config:
            config["model"] = {}
        config["model"] = model
        
        with open(self.codex_config, "w") as f:
            toml.dump(config, f)
        
        return {
            "success": True,
            "model": model,
            "config_path": str(self.codex_config)
        }
    
    def get_available_models(self) -> list[str]:
        """Lista modelos disponiveis."""
        models = [
            "chatgpt-web/gpt-5.6-luna",    # Free/Go
            "chatgpt-web/gpt-5.6-sol",     # Plus/Pro (Instant)
            "chatgpt-web/gpt-5.6-sol:medium",  # Medium effort
            "chatgpt-web/gpt-5.6-sol:high",    # High effort
            "chatgpt-web/gpt-5.6-sol:xhigh",   # Extra High
            "chatgpt-web/gpt-5.6-sol:ultra",   # Pro effort
        ]
        return models
    
    def uninstall(self) -> dict:
        """Remove integracao."""
        result = self.run_cli("uninstall", "--yes", timeout=30)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def subagents_status(self) -> dict:
        """Status de subagents."""
        result = self.run_cli("subagents", "status", timeout=10)
        try:
            return json.loads(result.stdout)
        except:
            return {"raw": result.stdout}
    
    def subagents_set_protocol(self, protocol: str = "compatibility-v1") -> dict:
        """Define protocolo de subagents."""
        result = self.run_cli("subagents", protocol, timeout=10)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Codex ChatGPT Web Integration")
    parser.add_argument("command", nargs="?", help="Comando a executar")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    parser.add_argument("--model", "-m", help="Modelo Codex para usar")
    args = parser.parse_args()
    
    cgtw = CodexChatGptWeb()
    
    commands = {
        "status": lambda: cgtw.get_status(),
        "doctor": lambda: cgtw.run_cli("doctor"),
        "login": lambda: cgtw.login(),
        "setup": lambda: cgtw.setup_browser_only(),
        "serve": lambda: cgtw.start_bridge(background=False),
        "serve-bg": lambda: cgtw.start_bridge(background=True),
        "stop": lambda: cgtw.stop_bridge(),
        "service-install": lambda: cgtw.install_service(),
        "service-start": lambda: cgtw.start_service(),
        "route-status": lambda: cgtw.get_route_status(),
        "route-connect": lambda: cgtw.connect_route(),
        "route-disconnect": lambda: cgtw.disconnect_route(),
        "set-model": lambda: cgtw.set_codex_model(args.model or "chatgpt-web/gpt-5.6-luna"),
        "models": lambda: cgtw.get_available_models(),
        "subagents-status": lambda: cgtw.subagents_status(),
        "uninstall": lambda: cgtw.uninstall(),
    }
    
    if args.command and args.command in commands:
        result = commands[args.command]()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if isinstance(result, dict) and "stdout" in result:
                print(result.get("stdout", "") or result.get("stderr", ""))
            elif isinstance(result, list):
                for m in result:
                    print(f"  {m}")
            else:
                print(json.dumps(result, indent=2, default=str))
    else:
        print("Codex ChatGPT Web Integration")
        print(f"Project: {PROJECT_DIR}")
        print(f"CLI: {CLI}")
        print(f"Config: {CONFIG_DIR}")
        print(f"Codex Config: {CODEX_CONFIG}")
        print()
        print("Commands:")
        for cmd in commands:
            print(f"  {cmd}")
        print()
        print("Quick start:")
        print('  python codex_chatgpt_web.py login')
        print('  python codex_chatgpt_web.py setup')
        print('  python codex_chatgpt_web.py serve-bg')
        print('  python codex_chatgpt_web.py set-model')
        print('  codex  # agora use modelos chatgpt-web/')
