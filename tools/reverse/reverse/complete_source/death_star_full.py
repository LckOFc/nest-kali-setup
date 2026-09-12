#!/usr/bin/env python3
"""
Death Star CLI - Complete System
================================
Backend + Frontend funcional integrado
"""

import os
import sys
import json
import hashlib
import subprocess
import urllib.request
import urllib.error
import re
import uuid
import time
import socket
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict

# Colors
ACCENT = "\033[38;5;208m"
GREEN = "\033[38;5;114m"
MUTED = "\033[38;5;245m"
RED = "\033[38;5;203m"
RESET = "\033[0m"

VERSION = "1.0.0"

# Death Star Logo
DEATH_STAR = [
    "                    .-:::::-.",
    "                  .:::::::::::::.",
    "               .:::::::::::::::::::.",
    "             .:::::::::::::::::::::::::.",
    "           .::::::::..-:::::-..:::::::::.",
    "          .:::::-.-:::::::::::.-.:::::::.",
    "         .:::::-::-:::::::::::::::::::--:::::",
    "        :::::::--:::::::::::::::::::::::::--:::::",
    "       .:::::::--:::::::::::::::::::::::::::--::::",
    "       ::::::::--:::::::::::::::::::::::::::--::::",
    "      .::::::::--:::::::::::::::::::::::::::--::::",
    "      :::::::::--::::::::::::::::::::::::::::--::::",
    "      :::::::::-:::::::::::::::::::::::::::::-:::::",
    "      ::::::::::::::::::::::::::::::::::::::::::::",
    "       ::::::::::::::::::::::::::::::::::::::::::::",
    "        ::::::::::::::::::::::::::::::::::::::::::::",
    "         :::::::::--::::::::::::::::::::--:::::::::::",
    "          :::::::::-:::::::::::::::::::-:::::::::::",
    "           :::::::::--:::::::::--:::::::::::",
    "             ::::::::::::::::::::",
    "                `:::::::::`",
]


@dataclass
class Task:
    task_id: str
    target: str
    params: Dict[str, str]
    status: str = "pending"
    result: str = ""
    task_type: str = "generic"
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class Backend:
    """Complete functional backend for Death Star CLI"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.tasks: Dict[str, Task] = {}
        self.packages: Dict[str, Dict] = {}
        self.sessions: List[Dict] = []
        self.current_session_id: str = uuid.uuid4().hex[:8]
        self.start_time = datetime.now()
        self.verbose = False
        self.sector = "7-G"
        self.shields = False
        self.superlaser_ready = False
        
        self._ensure_dirs()
        self._load_state()
    
    def _ensure_dirs(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "tasks").mkdir(exist_ok=True)
        (self.config_dir / "packages").mkdir(exist_ok=True)
        (self.config_dir / "sessions").mkdir(exist_ok=True)
    
    def _load_state(self):
        state_file = self.config_dir / "state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for task_id, task_data in data.get("tasks", {}).items():
                    self.tasks[task_id] = Task.from_dict(task_data)
                self.packages = data.get("packages", {})
                self.sessions = data.get("sessions", [])
                self.current_session_id = data.get("current_session_id", self.current_session_id)
                self.sector = data.get("sector", "7-G")
                self.shields = data.get("shields", False)
                self.superlaser_ready = data.get("superlaser_ready", False)
            except:
                pass
    
    def _save_state(self):
        state = {
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "packages": self.packages,
            "sessions": self.sessions,
            "current_session_id": self.current_session_id,
            "sector": self.sector,
            "shields": self.shields,
            "superlaser_ready": self.superlaser_ready,
            "version": VERSION,
            "last_save": datetime.now().isoformat(),
        }
        state_file = self.config_dir / "state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    def generate_task_id(self) -> str:
        return hashlib.sha256(f"{uuid.uuid4()}{time.time()}{os.getpid()}".encode()).hexdigest()[:12]
    
    # ==================== TASK EXECUTION ====================
    
    def run_task(self, target: str, params: Dict = None) -> Task:
        task_id = self.generate_task_id()
        params = params or {}
        task_type = self._detect_task_type(target)
        
        task = Task(
            task_id=task_id,
            target=target,
            params=params,
            status="running",
            task_type=task_type,
        )
        
        self.tasks[task_id] = task
        self.sessions.append({"task_id": task_id, "target": target, "type": task_type, "status": "completed", "created_at": task.created_at})
        
        result = self._execute_task(target, params, task_type)
        
        task.status = "completed"
        task.result = result
        task.completed_at = datetime.now().isoformat()
        
        self._save_state()
        return task
    
    def _detect_task_type(self, target: str) -> str:
        target_lower = target.lower().strip()
        if target_lower.startswith(("http://", "https://", "www.")):
            return "url"
        commands = ["ls", "dir", "pwd", "echo", "cat", "head", "tail", "grep", "find", "which", "whereis", "type", "man", "help", "npm", "pip", "git", "docker", "python", "node", "curl", "wget", "cls", "clear", "exit", "cd", "mkdir", "copy", "move", "del", "remove", "print", "write", "ping", "tracert", "netstat", "ipconfig", "nslookup", "tasklist", "taskkill", "sc", "net", "powershell", "type", "more", "tree", "where"]
        if target_lower.split()[0] in commands:
            return "command"
        if any(target.startswith(p) for p in ["/", ".", "~", "C:\\", "D:\\", "E:\\"]):
            return "path"
        if target_lower.startswith(("def ", "class ", "import ", "from ", "print(")):
            return "code"
        return "generic"
    
    def _execute_task(self, target: str, params: Dict, task_type: str) -> str:
        if task_type == "url":
            return self._execute_url(target, params)
        elif task_type == "command":
            return self._execute_command(target, params)
        elif task_type == "path":
            return self._execute_path(target, params)
        elif task_type == "code":
            return self._execute_code(target, params)
        else:
            return self._execute_generic(target, params)
    
    def _execute_url(self, url: str, params: Dict) -> str:
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            req = urllib.request.Request(url, headers={"User-Agent": f"DeathStar/{VERSION}", "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "No title"
            
            div_count = len(re.findall(r'<div', content, re.IGNORECASE))
            p_count = len(re.findall(r'<p[^>]*>', content, re.IGNORECASE))
            link_count = len(re.findall(r'<a\s+href', content, re.IGNORECASE))
            img_count = len(re.findall(r'<img[^>]*>', content, re.IGNORECASE))
            links = re.findall(r'<a\s+href=["\']([^"\']+)["\']', content, re.IGNORECASE)
            links = [l for l in links if l and not l.startswith('#')]
            status_code = response.status
            size = len(content)
            
            return f"""URL Analyzed: {url}
Title: {title}
Status: {status_code} OK
Size: {size:,} bytes
Divs: {div_count} | Paragraphs: {p_count} | Links: {link_count} | Images: {img_count}
Links Found ({len(links)} total):
  {chr(10).join(['  - ' + l[:70] for l in links[:10]])}"""
        except Exception as e:
            return f"Error fetching URL: {str(e)}"
    
    def _execute_command(self, cmd: str, params: Dict) -> str:
        try:
            parts = cmd.split()
            if not parts:
                return "No command specified"
            result = subprocess.run(parts, capture_output=True, text=True, timeout=30, shell=False)
            if result.stdout.strip():
                return f"Output:\n{result.stdout.strip()}"
            elif result.stderr.strip():
                return f"Error:\n{result.stderr.strip()}"
            else:
                return f"Executed successfully (exit code: {result.returncode})"
        except subprocess.TimeoutExpired:
            return "Command timed out (30s limit)"
        except FileNotFoundError:
            return f"Command not found: {parts[0] if parts else 'unknown'}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _execute_path(self, path: str, params: Dict) -> str:
        try:
            p = Path(path)
            if p.exists():
                if p.is_file():
                    size = p.stat().st_size
                    return f"File: {path}\nSize: {size:,} bytes\nModified: {datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}"
                elif p.is_dir():
                    items = list(p.iterdir())
                    dirs = sum(1 for i in items if i.is_dir())
                    files = sum(1 for i in items if i.is_file())
                    return f"Directory: {path}\nItems: {len(items)} (dirs: {dirs}, files: {files})"
            else:
                return f"Path not found: {path}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _execute_code(self, code: str, params: Dict) -> str:
        try:
            import io, contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                exec(code, {"__builtins__": __builtins__})
            output = f.getvalue().strip()
            return f"Output:\n{output}" if output else "Executed (no output)"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _execute_generic(self, target: str, params: Dict) -> str:
        try:
            parts = target.split()
            result = subprocess.run(parts, capture_output=True, text=True, timeout=10, shell=False)
            if result.stdout.strip():
                return f"Output:\n{result.stdout.strip()}"
        except:
            pass
        return f"Task executed for: {target}"
    
    # ==================== PACKAGE MANAGEMENT ====================
    
    def install_package(self, package: str, version: str = "latest") -> Dict:
        pkg_key = f"{package}@{version}"
        if pkg_key in self.packages:
            return {"status": "already_installed", "package": package, "version": version}
        self.packages[pkg_key] = {
            "name": package,
            "version": version,
            "installed_at": datetime.now().isoformat(),
            "status": "installed",
        }
        self._save_state()
        return {"status": "installed", "package": package, "version": version}
    
    def uninstall_package(self, package: str) -> Dict:
        found = False
        for key in list(self.packages.keys()):
            if key.startswith(f"{package}@"):
                del self.packages[key]
                found = True
        if found:
            self._save_state()
            return {"status": "uninstalled", "package": package}
        return {"status": "not_found", "package": package}
    
    def list_packages(self) -> List[Dict]:
        return list(self.packages.values())
    
    # ==================== DEATH STAR FUNCTIONS ====================
    
    def change_sector(self, sector: str):
        self.sector = sector
        self._save_state()
        return f"Sector changed to: {sector}"
    
    def toggle_shields(self, on: bool):
        self.shields = on
        self._save_state()
        return "ACTIVATED" if on else "DISENGAGED"
    
    def fire_superlaser(self, target: str) -> str:
        if not self.shields:
            return f"[!] Shields are OFF! Target {target} DESTROYED!"
        else:
            self.superlaser_ready = True
            self._save_state()
            return f"Charging superlaser... Target locked on {target}"
    
    def get_status(self) -> Dict:
        elapsed = datetime.now() - self.start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        return {
            "version": VERSION,
            "user": "Commander",
            "quota": "Imperial Access Level 5",
            "tasks": len(self.tasks),
            "packages": len(self.packages),
            "sessions": len(self.sessions),
            "uptime": f"{minutes:02d}:{seconds:02d}",
            "debug": self.verbose,
            "auth": "Imperial Clearance Required",
            "hostname": socket.gethostname(),
            "system": platform.system(),
            "python_version": platform.python_version(),
            "sector": self.sector,
            "shields": self.shields,
            "superlaser_ready": self.superlaser_ready,
        }
    
    def get_help(self) -> str:
        return """
DEATH STAR COMMANDS:
====================
  run <target>          Execute task (URL, command, or path)
  install <package>     Install a package
  uninstall <package>   Uninstall a package
  packages              List installed packages
  status                Show system status
  list                  List all tasks
  sessions              List sessions
  sector <num>          Change sector (7-G, etc)
  destroy <target>      Destroy target (simulation)
  shield <on/off>       Toggle deflector shields
  superlaser <target>   Fire superlaser
  star                  Show Death Star status
  whoami                Show commander info
  about                 Show about info
  clear-tasks           Clear all tasks
  help / ?              Show this help
  exit / quit           Exit agent

Examples:
  run https://example.com
  run ls -la
  install stormtrooper-sdk
  sector 7-G
  destroy Alderaan
  shield on
  superlaser Yavin IV
"""
    
    def clear_tasks(self):
        self.tasks.clear()
        self._save_state()
    
    def get_whoami(self) -> str:
        return f"""
* Imperial Command Center
{'-' * 40}
  Commander:    Commander
  Sector:       {self.sector}
  Hostname:     {socket.gethostname()}
  System:       {platform.system()} {platform.release()}
  Python:       {platform.python_version()}
  Quota:        Imperial Access Level 5
  Mode:         Local (No Authentication Required)
  Shields:      {'ACTIVE' if self.shields else 'DORMANT'}
  Superlaser:   {'READY' if self.superlaser_ready else 'CHARGING'}
"""


class Frontend:
    """Interactive frontend for Death Star CLI"""
    
    def __init__(self, backend: Backend):
        self.backend = backend
        self.running = True
        self.history: List[str] = []
    
    def print_header(self):
        print()
        for line in DEATH_STAR:
            print(f"  {MUTED}{line}{RESET}")
        print()
        status = self.backend.get_status()
        print(f"  {ACCENT}DEATH STAR CLI{RESET} {MUTED}v{status['version']}{RESET}")
        print(f"  {MUTED}{status['user']} ({status['quota']}){RESET}")
        print(f"  {MUTED}Sector: {status['sector']} | Shields: {'ON' if status['shields'] else 'OFF'} | Superlaser: {'READY' if status['superlaser_ready'] else 'CHARGING'}{RESET}")
        print()
        print("  " + "-" * 60)
        print()
    
    def process_command(self, cmd: str) -> bool:
        cmd = cmd.strip()
        if not cmd:
            return True
        
        self.history.append(cmd)
        print(f"\n  > {cmd}")
        
        parts = cmd.split()
        command = parts[0].lower().lstrip('/')
        args = parts[1:]
        
        if command in ("exit", "quit", "q"):
            print("\n  [SYSTEM] Shutting down Death Star...")
            return False
        
        elif command in ("help", "?", "h"):
            print(self.backend.get_help())
        
        elif command == "status":
            status = self.backend.get_status()
            print(f"""
  * DEATH STAR STATUS
  {'-' * 40}
  Version:      {status['version']}
  Model:        Death Star Protocol
  User:         {status['user']}
  Sector:       {status['sector']}
  Tasks:        {status['tasks']}
  Packages:     {status['packages']}
  Sessions:     {status['sessions']}
  Uptime:       {status['uptime']}
  Shields:      {'ACTIVE' if status['shields'] else 'DORMANT'}
  Superlaser:   {'READY' if status['superlaser_ready'] else 'CHARGING'}
""")
        
        elif command == "version":
            print(f"\n  DEATH STAR CLI v{VERSION}")
        
        elif command == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_header()
        
        elif command == "run":
            self.cmd_run(args)
        
        elif command == "exec":
            self.cmd_run(args)
        
        elif command == "install":
            self.cmd_install(args)
        
        elif command == "uninstall":
            self.cmd_uninstall(args)
        
        elif command == "packages":
            self.cmd_packages()
        
        elif command == "list":
            self.cmd_list()
        
        elif command == "tasks":
            self.cmd_list()
        
        elif command == "sessions":
            self.cmd_sessions()
        
        elif command == "sector":
            self.cmd_sector(args)
        
        elif command == "destroy":
            self.cmd_destroy(args)
        
        elif command == "shield":
            self.cmd_shield(args)
        
        elif command == "superlaser":
            self.cmd_superlaser(args)
        
        elif command == "star":
            self.cmd_star()
        
        elif command == "whoami":
            print(self.backend.get_whoami())
        
        elif command == "about":
            self.cmd_about()
        
        elif command == "clear-tasks":
            self.backend.clear_tasks()
            print("\n  [SYSTEM] All tasks cleared.")
        
        else:
            # Try to run as task
            self.cmd_run([cmd])
        
        return True
    
    def cmd_run(self, args: List[str]):
        if not args:
            print("\n  Usage: run <target> [--param key=value]")
            return
        
        target = args[0]
        params = {}
        
        i = 1
        while i < len(args):
            if args[i] == "--param" and i + 1 < len(args):
                param = args[i + 1]
                if "=" in param:
                    k, v = param.split("=", 1)
                    params[k] = v
                i += 2
            else:
                i += 1
        
        task = self.backend.run_task(target, params)
        
        result = f"""
  * TASK EXECUTED
  {'-' * 40}
  ID:         {task.task_id}
  Type:       {task.task_type.upper()}
  Target:     {task.target}
  Params:     {task.params if task.params else 'None'}
  Status:     {task.status.upper()}
  Created:    {task.created_at}
"""
        if task.result:
            result += f"\n  Result:\n  {task.result}"
        print(result)
    
    def cmd_install(self, args: List[str]):
        if not args:
            print("\n  Usage: install <package> [version]")
            return
        
        package = args[0]
        version = args[1] if len(args) > 1 else "latest"
        result = self.backend.install_package(package, version)
        
        print(f"""
  Package Installed
  -----------------
  Package:   {result['package']}
  Version:   {result['version']}
  Status:    {result['status'].upper()}
""")
    
    def cmd_uninstall(self, args: List[str]):
        if not args:
            print("\n  Usage: uninstall <package>")
            return
        
        package = args[0]
        result = self.backend.uninstall_package(package)
        
        print(f"""
  Package Uninstalled
  -------------------
  Package:   {result['package']}
  Status:    {result['status'].upper()}
""")
    
    def cmd_packages(self):
        packages = self.backend.list_packages()
        
        if not packages:
            print("\n  No packages installed.")
            return
        
        print("\n  Installed Packages:")
        print("  " + "-" * 40)
        for pkg in packages:
            print(f"  * {pkg['name']} v{pkg['version']}")
        print()
    
    def cmd_list(self):
        tasks = sorted(self.backend.tasks.values(), key=lambda t: t.created_at, reverse=True)[:20]
        
        if not tasks:
            print("\n  No tasks executed yet.")
            return
        
        print(f"\n  Tasks ({len(tasks)} shown):")
        print("  " + "-" * 50)
        
        for task in tasks:
            preview = task.result[:50] + "..." if len(task.result) > 50 else task.result
            print(f"  [{task.task_id}] {task.target}")
            print(f"    Type: {task.task_type} | Status: {task.status}")
            print(f"    Created: {task.created_at[:19]}")
            print()
    
    def cmd_sessions(self):
        sessions = self.backend.sessions[-10:]
        
        if not sessions:
            print("\n  No sessions yet.")
            return
        
        print("\n  Sessions:")
        print("  " + "-" * 50)
        for s in sessions:
            print(f"  [{s['task_id'][:8]}...] {s.get('target', 'N/A')} - {s.get('status', 'unknown')}")
        print()
    
    def cmd_sector(self, args: List[str]):
        if not args:
            status = self.backend.get_status()
            print(f"\n  Current sector: {status['sector']}")
            print("  Usage: sector <sector_id>")
            return
        
        sector = args[0]
        self.backend.change_sector(sector)
        print(f"\n  Sector changed to: {sector}")
    
    def cmd_destroy(self, args: List[str]):
        if not args:
            print("\n  Usage: destroy <target>")
            return
        
        target = " ".join(args)
        print(f"\n  [WARNING] Destroying {target}...")
        print(f"  [SYSTEM] Target destroyed successfully.")
    
    def cmd_shield(self, args: List[str]):
        if not args:
            status = self.backend.get_status()
            print(f"\n  Current shields: {'ACTIVE' if status['shields'] else 'DORMANT'}")
            print("  Usage: shield on|off")
            return
        
        action = args[0].lower()
        if action == "on":
            result = self.backend.toggle_shields(True)
            print(f"\n  [SYSTEM] Deflector shields {result}.")
        elif action == "off":
            result = self.backend.toggle_shields(False)
            print(f"\n  [SYSTEM] Deflector shields {result}.")
        else:
            print(f"\n  Unknown shield action: {action}")
    
    def cmd_superlaser(self, args: List[str]):
        if not args:
            print("\n  Usage: superlaser <target>")
            return
        
        target = " ".join(args)
        result = self.backend.fire_superlaser(target)
        print(f"\n  {result}")
        if self.backend.superlaser_ready:
            print(f"  [SYSTEM] FIRE!")
            print(f"  [RESULT] Target destroyed.")
    
    def cmd_star(self):
        print()
        for line in DEATH_STAR:
            print(f"  {MUTED}{line}{RESET}")
        print()
        status = self.backend.get_status()
        print(f"  {ACCENT}STATUS: ONLINE{RESET}")
        print(f"  {MUTED}Sector: {status['sector']} | Uptime: {status['uptime']}{RESET}")
        print()
    
    def cmd_about(self):
        print("""
  About Death Star CLI:
  ---------------------
  Death Star CLI - Imperial-grade command system
  Built for maximum computational superiority
  
  Features:
    - Run tasks against targets (URLs, commands, files)
    - Install packages  
    - Browser automation
    - Sector management
    - Shield harmonics control
    - Superlaser targeting
    - Imperial reporting
""")
    
    def run(self):
        self.print_header()
        
        while self.running:
            try:
                cmd = input("  > ")
                if not self.process_command(cmd):
                    break
            except EOFError:
                print("\n  [SYSTEM] Goodbye!")
                break
            except KeyboardInterrupt:
                print("\n  (Use 'exit' to quit)")
                continue
            except Exception as e:
                print(f"\n  [Error] {e}")


def main():
    """Main entry point"""
    config_dir = Path.home() / ".death-star"
    backend = Backend(config_dir)
    frontend = Frontend(backend)
    
    # Check for command line args
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower().lstrip('/')
        args = sys.argv[2:]
        
        if cmd == "run":
            task = backend.run_task(args[0] if args else "", dict(a.split("=") for a in args[1:] if "=" in a) if len(args) > 1 else {})
            print(f"""
  * TASK EXECUTED
  {'-' * 40}
  ID:        {task.task_id}
  Type:      {task.task_type.upper()}
  Target:    {task.target}
  Status:    {task.status.upper()}
  Result:    {task.result[:200]}
""")
        elif cmd == "install":
            result = backend.install_package(args[0] if args else "", args[1] if len(args) > 1 else "latest")
            print(f"""
  Package Installed
  -----------------
  Package:   {result['package']}
  Version:   {result['version']}
  Status:    {result['status'].upper()}
""")
        elif cmd == "uninstall":
            result = backend.uninstall_package(args[0] if args else "")
            print(f"""
  Package Uninstalled
  -------------------
  Package:   {result['package']}
  Status:    {result['status'].upper()}
""")
        elif cmd == "packages":
            packages = backend.list_packages()
            if packages:
                print("\n  Installed Packages:")
                for p in packages:
                    print(f"    * {p['name']} v{p['version']}")
            else:
                print("\n  No packages installed.")
        elif cmd == "status":
            status = backend.get_status()
            print(f"""
  * DEATH STAR STATUS
  {'-' * 40}
  Version:    {status['version']}
  Sector:     {status['sector']}
  Tasks:      {status['tasks']}
  Packages:   {status['packages']}
  Sessions:   {status['sessions']}
  Uptime:     {status['uptime']}
  Shields:    {'ACTIVE' if status['shields'] else 'DORMANT'}
  Superlaser: {'READY' if status['superlaser_ready'] else 'CHARGING'}
""")
        elif cmd == "list":
            tasks = sorted(backend.tasks.values(), key=lambda t: t.created_at, reverse=True)[:10]
            if tasks:
                print(f"\n  Tasks ({len(tasks)}):")
                for task in tasks:
                    print(f"  [{task.task_id}] {task.target} - {task.status}")
            else:
                print("\n  No tasks executed yet.")
        elif cmd == "sector":
            if args:
                backend.change_sector(args[0])
                print(f"\n  Sector changed to: {args[0]}")
            else:
                status = backend.get_status()
                print(f"\n  Current sector: {status['sector']}")
        elif cmd == "shield":
            if args and args[0].lower() == "on":
                backend.toggle_shields(True)
                print("\n  [SYSTEM] Deflector shields ACTIVATED.")
            elif args and args[0].lower() == "off":
                backend.toggle_shields(False)
                print("\n  [SYSTEM] Deflector shields DISENGAGED.")
            else:
                status = backend.get_status()
                print(f"\n  Current shields: {'ACTIVE' if status['shields'] else 'DORMANT'}")
        elif cmd == "superlaser":
            if args:
                target = " ".join(args)
                result = backend.fire_superlaser(target)
                print(f"\n  {result}")
        elif cmd == "destroy":
            if args:
                target = " ".join(args)
                print(f"\n  [WARNING] Destroying {target}...")
                print(f"  [SYSTEM] Target destroyed successfully.")
        elif cmd == "star":
            print()
            for line in DEATH_STAR:
                print(f"  {MUTED}{line}{RESET}")
            print()
            status = backend.get_status()
            print(f"  {ACCENT}STATUS: ONLINE{RESET}")
            print(f"  {MUTED}Sector: {status['sector']} | Uptime: {status['uptime']}{RESET}")
            print()
        elif cmd == "whoami":
            print(backend.get_whoami())
        elif cmd == "about":
            print("""
  About Death Star CLI:
  ---------------------
  Death Star CLI - Imperial-grade command system
  Built for maximum computational superiority
""")
        elif cmd == "clear-tasks":
            backend.clear_tasks()
            print("\n  [SYSTEM] All tasks cleared.")
        elif cmd == "help" or cmd == "--help" or cmd == "-h":
            print(backend.get_help())
        elif cmd == "version":
            print(f"DEATH STAR CLI v{VERSION}")
        else:
            print(f"Unknown command: {cmd}")
            print("Use 'death-star help' for available commands")
    else:
        # Interactive mode
        frontend.run()


if __name__ == "__main__":
    main()
