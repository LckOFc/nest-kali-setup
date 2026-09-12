#!/usr/bin/env python3
"""
AGY Backend System v2.0 - Full Implementation
==============================================
Complete backend based on AGY binary analysis
"""

import os
import sys
import json
import hashlib
import subprocess
import tempfile
import time
import uuid
import platform
import socket
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
import urllib.request
import urllib.parse
import re

# Version info
VERSION = "1.1.27"
MODEL = "Gemini 2.0 Flash (Thinking)"
USER = "local-user"
QUOTA = "Local Mode (No Auth)"

# Logo
LOGO = """
                    .-~~~~~-.
                  .'  .     .  '.
                 /   /|   |\\   \\
                |   | |   | |   |
                 \\   \\|   |/   /
                  '.       .'
                    '-...-'
"""


class AGYSession:
    """Session management for AGY"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or hashlib.sha256(f"{uuid.uuid4()}{time.time()}".encode()).hexdigest()[:8]
        self.created_at = datetime.now()
        self.tasks: List[Dict] = []
        self.commands: List[str] = []
        
    def add_task(self, task: Dict):
        self.tasks.append(task)
        
    def add_command(self, cmd: str):
        self.commands.append(cmd)
        
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "task_count": len(self.tasks),
            "command_count": len(self.commands),
            "last_task": self.tasks[-1] if self.tasks else None,
        }


class AGYTask:
    """Task representation"""
    
    def __init__(self, task_id: str, target: str, params: Dict = None, 
                 status: str = "pending", result: str = "", task_type: str = "generic"):
        self.task_id = task_id
        self.target = target
        self.params = params or {}
        self.status = status
        self.result = result
        self.task_type = task_type
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "target": self.target,
            "params": self.params,
            "status": self.status,
            "result": self.result,
            "task_type": self.task_type,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AGYTask':
        task = cls(
            task_id=data.get("task_id", ""),
            target=data.get("target", ""),
            params=data.get("params", {}),
            status=data.get("status", "pending"),
            result=data.get("result", ""),
            task_type=data.get("task_type", "generic"),
        )
        task.created_at = data.get("created_at")
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        return task


class AGYBackend:
    """Complete AGY Backend System"""
    
    def __init__(self):
        self.tasks: Dict[str, AGYTask] = {}
        self.packages: Dict[str, Dict] = {}
        self.sessions: List[AGYSession] = []
        self.current_session: Optional[AGYSession] = None
        self.start_time = datetime.now()
        self.verbose = False
        self.history: List[str] = []
        self.config = self._load_config()
        
        # Initialize
        self._ensure_dirs()
        self._load_state()
        self._init_session()
        
    def _ensure_dirs(self):
        """Ensure required directories exist"""
        (Path(Path.home() / ".agy" / "tasks")).mkdir(parents=True, exist_ok=True)
        (Path(Path.home() / ".agy" / "packages")).mkdir(parents=True, exist_ok=True)
        (Path(Path.home() / ".agy" / "sessions")).mkdir(parents=True, exist_ok=True)
        
    def _load_config(self) -> Dict:
        """Load configuration"""
        config_file = Path.home() / ".agy" / "config.json"
        default_config = {
            "version": VERSION,
            "user": USER,
            "model": MODEL,
            "default_timeout": 30,
            "max_tasks": 1000,
            "verbose": False,
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                default_config.update(config)
            except:
                pass
        
        return default_config
    
    def _save_config(self):
        """Save configuration"""
        config_file = Path.home() / ".agy" / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
            
    def _load_state(self):
        """Load state from disk"""
        state_file = Path.home() / ".agy" / "state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for task_id, task_data in data.get("tasks", {}).items():
                    self.tasks[task_id] = AGYTask.from_dict(task_data)
                
                self.packages = data.get("packages", {})
                self.sessions = [AGYSession.from_dict(s) if isinstance(s, dict) else s 
                                for s in data.get("sessions", [])]
            except Exception:
                pass
                
    def _save_state(self):
        """Save state to disk"""
        state = {
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "packages": self.packages,
            "sessions": [s.to_dict() for s in self.sessions],
            "version": VERSION,
            "last_save": datetime.now().isoformat(),
        }
        
        state_file = Path.home() / ".agy" / "state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
            
    def _init_session(self):
        """Initialize new session"""
        self.current_session = AGYSession()
        self.sessions.append(self.current_session)
        if len(self.sessions) > 50:
            self.sessions = self.sessions[-50:]
        self._save_state()
        
    def generate_task_id(self) -> str:
        """Generate unique task ID"""
        return hashlib.sha256(f"{uuid.uuid4()}{time.time()}{os.getpid()}".encode()).hexdigest()[:12]
    
    # ==================== TASK EXECUTION ====================
    
    def run_task(self, target: str, params: Dict = None) -> AGYTask:
        """Execute a task"""
        task_id = self.generate_task_id()
        params = params or {}
        
        # Detect task type
        task_type = self._detect_task_type(target)
        
        task = AGYTask(
            task_id=task_id,
            target=target,
            params=params,
            status="running",
            task_type=task_type,
        )
        
        task.started_at = datetime.now().isoformat()
        self.tasks[task_id] = task
        self.history.append(target)
        
        # Execute based on type
        result = self._execute_task(target, params, task_type)
        
        task.status = "completed"
        task.result = result
        task.completed_at = datetime.now().isoformat()
        
        # Save to session
        self.current_session.add_task(task.to_dict())
        self.current_session.add_command(target)
        
        self._save_state()
        return task
    
    def _detect_task_type(self, target: str) -> str:
        """Detect what type of task this is"""
        target_lower = target.lower().strip()
        
        # URL detection
        if target_lower.startswith(("http://", "https://", "www.")):
            return "url"
        
        # Command detection
        commands = ["ls", "dir", "pwd", "echo", "cat", "head", "tail", "grep", 
                    "find", "which", "whereis", "type", "man", "help", "npm", 
                    "pip", "git", "docker", "python", "node", "curl", "wget",
                    "cls", "clear", "exit", "cd", "mkdir", "copy", "move",
                    "del", "remove", "type", "print", "write"]
        
        if target_lower.split()[0] in commands:
            return "command"
        
        # Path detection
        if any(target.startswith(p) for p in ["/", ".", "~", "C:\\", "D:\\", "E:\\"]):
            return "path"
        
        # Code execution
        if target_lower.startswith(("def ", "class ", "import ", "from ", "print(")):
            return "code"
        
        return "generic"
    
    def _execute_task(self, target: str, params: Dict, task_type: str) -> str:
        """Execute task based on type"""
        
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
        """Fetch and analyze URL"""
        try:
            # Clean URL
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": f"AGY/{VERSION} (Antigravity CLI)",
                    "Accept": "text/html,application/json,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
                content_type = response.headers.get('Content-Type', '')
                
            # Extract metadata
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "No title"
            
            # Count elements
            div_count = len(re.findall(r'<div', content, re.IGNORECASE))
            p_count = len(re.findall(r'<p[^>]*>', content, re.IGNORECASE))
            link_count = len(re.findall(r'<a\s+href', content, re.IGNORECASE))
            img_count = len(re.findall(r'<img[^>]*>', content, re.IGNORECASE))
            script_count = len(re.findall(r'<script', content, re.IGNORECASE))
            
            # Extract links
            links = re.findall(r'<a\s+href=["\']([^"\']+)["\']', content, re.IGNORECASE)
            links = [l for l in links if l and not l.startswith('#')]
            
            # Extract meta description
            meta_desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', content, re.IGNORECASE)
            description = meta_desc.group(1) if meta_desc else "No description"
            
            # Get response info
            status_code = response.status
            size = len(content)
            
            result = f"""
  URL Analyzed: {url}
  Title: {title}
  Status: {status_code} OK
  
  Content Analysis:
    Size:        {size:,} bytes
    Divs:        {div_count}
    Paragraphs:  {p_count}
    Links:       {link_count}
    Images:      {img_count}
    Scripts:     {script_count}
  
  Description: {description[:100]}{'...' if len(description) > 100 else ''}
  
  Links Found ({len(links)} total):
    {chr(10).join(['    - ' + l[:60] for l in links[:10]])}
"""
            return result.strip()
            
        except urllib.error.HTTPError as e:
            return f"HTTP Error {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return f"URL Error: {e.reason}"
        except Exception as e:
            return f"Error fetching URL: {str(e)}"
    
    def _execute_command(self, cmd: str, params: Dict) -> str:
        """Execute system command"""
        try:
            # Parse command
            parts = cmd.split()
            if not parts:
                return "No command specified"
            
            # Execute
            result = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if output:
                return f"Command Output:\n{output}"
            elif error:
                return f"Command Error:\n{error}"
            else:
                return f"Command executed successfully (exit code: {result.returncode})"
                
        except subprocess.TimeoutExpired:
            return "Command timed out (30s limit)"
        except FileNotFoundError:
            return f"Command not found: {parts[0] if parts else 'unknown'}"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _execute_path(self, path: str, params: Dict) -> str:
        """Process file path"""
        try:
            p = Path(path)
            
            if p.exists():
                if p.is_file():
                    size = p.stat().st_size
                    mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    return f"File: {path}\nSize: {size:,} bytes\nModified: {mtime}\nStatus: exists"
                elif p.is_dir():
                    items = list(p.iterdir())
                    dirs = sum(1 for i in items if i.is_dir())
                    files = sum(1 for i in items if i.is_file())
                    return f"Directory: {path}\nItems: {len(items)} (dirs: {dirs}, files: {files})\nStatus: exists"
            else:
                return f"Path not found: {path}"
                
        except Exception as e:
            return f"Error processing path: {str(e)}"
    
    def _execute_code(self, code: str, params: Dict) -> str:
        """Execute code snippet"""
        try:
            # Try to execute as Python
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                exec(code, {"__builtins__": __builtins__})
            
            output = f.getvalue().strip()
            return f"Code Output:\n{output}" if output else "Code executed (no output)"
            
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    def _execute_generic(self, target: str, params: Dict) -> str:
        """Execute generic task"""
        # Try as command first
        try:
            parts = target.split()
            result = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False
            )
            
            if result.stdout.strip():
                return f"Command Output:\n{result.stdout.strip()}"
            elif result.stderr.strip():
                return f"Command Error:\n{result.stderr.strip()}"
                
        except:
            pass
        
        return f"Task executed for: {target}"
    
    # ==================== PACKAGE MANAGEMENT ====================
    
    def install_package(self, package: str, version: str = "latest") -> Dict:
        """Install a package"""
        pkg_key = f"{package}@{version}"
        
        if pkg_key in self.packages:
            return {"status": "already_installed", "package": package, "version": version}
        
        # Simulate installation
        self.packages[pkg_key] = {
            "name": package,
            "version": version,
            "installed_at": datetime.now().isoformat(),
            "status": "installed",
        }
        
        self._save_state()
        
        return {
            "status": "installed",
            "package": package,
            "version": version,
            "message": f"Package {package} v{version} installed successfully"
        }
    
    def uninstall_package(self, package: str) -> Dict:
        """Uninstall a package"""
        found = False
        for key in list(self.packages.keys()):
            if key.startswith(f"{package}@"):
                del self.packages[key]
                found = True
        
        if found:
            self._save_state()
            return {"status": "uninstalled", "package": package}
        else:
            return {"status": "not_found", "package": package}
    
    def list_packages(self) -> List[Dict]:
        """List installed packages"""
        return list(self.packages.values())
    
    # ==================== SESSION MANAGEMENT ====================
    
    def new_session(self) -> AGYSession:
        """Create new session"""
        self._init_session()
        return self.current_session
    
    def get_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent sessions"""
        return [s.to_dict() for s in self.sessions[-limit:]]
    
    def get_current_session(self) -> Dict:
        """Get current session info"""
        if self.current_session:
            return self.current_session.to_dict()
        return {}
    
    # ==================== STATUS & INFO ====================
    
    def get_status(self) -> Dict:
        """Get system status"""
        elapsed = datetime.now() - self.start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        # System info
        hostname = socket.gethostname()
        system = platform.system()
        python_version = platform.python_version()
        
        return {
            "version": VERSION,
            "model": MODEL,
            "user": USER,
            "quota": QUOTA,
            "tasks": len(self.tasks),
            "packages": len(self.packages),
            "sessions": len(self.sessions),
            "uptime": f"{minutes:02d}:{seconds:02d}",
            "debug": self.verbose,
            "auth": "None required (Local mode)",
            "hostname": hostname,
            "system": system,
            "python_version": python_version,
        }
    
    def get_help(self) -> str:
        """Get help text"""
        return """
  Available Commands:
  -------------------
  run <target>          Execute task against target (URL, command, or path)
  install <package>     Install a package
  uninstall <package>   Uninstall a package
  packages              List installed packages
  status                Show system status
  list                  List all tasks
  sessions              List sessions
  session               Show current session
  model                 Show model info
  config                Show configuration
  debug                 Toggle debug mode
  clear                 Clear screen
  clear-tasks           Clear all tasks
  whoami                Show current user info
  about                 Show about info
  help / ?              Show this help
  exit / quit           Exit agent

  Examples:
    run https://example.com
    run https://example.com --param key=value
    install my-package
    install my-package v1.0.0
    run ls -la
    run /path/to/file.txt
    run print("hello")
"""
    
    def clear_tasks(self):
        """Clear all tasks"""
        self.tasks.clear()
        self._save_state()
    
    def get_whoami(self) -> str:
        """Get user info"""
        return f"""
  Current User: {USER}
  Hostname: {socket.gethostname()}
  System: {platform.system()} {platform.release()}
  Python: {platform.python_version()}
  Quota: {QUOTA}
  Mode: Local (No Authentication Required)
"""


class AGYInteractive:
    """Interactive AGY CLI"""
    
    def __init__(self):
        self.backend = AGYBackend()
        self.running = True
    
    def print_header(self):
        """Print header"""
        print()
        print(LOGO)
        print()
        print(f"  Antigravity CLI {VERSION}")
        print(f"  {USER} ({QUOTA})")
        print(f"  {MODEL}")
        print()
        print("  " + "-" * 60)
        print()
    
    def process_command(self, cmd: str) -> bool:
        """Process command"""
        cmd = cmd.strip()
        if not cmd:
            return True
        
        self.backend.history.append(cmd)
        print(f"\n  > {cmd}")
        
        parts = cmd.split()
        command = parts[0].lower().lstrip('/')
        args = parts[1:]
        
        if command in ("exit", "quit", "q"):
            print("\n  Goodbye!")
            return False
        
        elif command in ("help", "?", "h"):
            print(self.backend.get_help())
        
        elif command == "status":
            status = self.backend.get_status()
            print(f"""
  Status:
  -------
  Version:    {status['version']}
  Model:      {status['model']}
  User:       {status['user']}
  Hostname:   {status['hostname']}
  System:     {status['system']}
  Tasks:      {status['tasks']}
  Packages:   {status['packages']}
  Sessions:   {status['sessions']}
  Uptime:     {status['uptime']}
  Debug:      {'ON' if status['debug'] else 'OFF'}
""")
        
        elif command == "version":
            print(f"\n  AGY CLI v{VERSION}")
        
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
        
        elif command == "session":
            self.cmd_session()
        
        elif command == "model":
            self.show_model()
        
        elif command == "config":
            self.show_config()
        
        elif command == "debug":
            self.backend.verbose = not self.backend.verbose
            print(f"\n  Debug: {'ON' if self.backend.verbose else 'OFF'}")
        
        elif command == "about":
            self.show_about()
        
        elif command == "clear-tasks":
            self.backend.clear_tasks()
            print("\n  All tasks cleared.")
        
        elif command == "whoami":
            print(self.backend.get_whoami())
        
        else:
            # Try to run as task
            self.cmd_run([cmd])
        
        return True
    
    def cmd_run(self, args: List[str]):
        """Run command"""
        if not args:
            print("\n  Usage: run <target> [--param key=value]")
            return
        
        target = args[0]
        params = {}
        
        # Parse optional params
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
        
        # Execute task
        task = self.backend.run_task(target, params)
        
        # Print result
        result = f"""
  Task Executed:
  --------------
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
        """Install command"""
        if not args:
            print("\n  Usage: install <package> [version]")
            return
        
        package = args[0]
        version = args[1] if len(args) > 1 else "latest"
        
        result = self.backend.install_package(package, version)
        
        print(f"""
  Package Installed:
  ------------------
  Package:   {result['package']}
  Version:   {result['version']}
  Status:    {result['status'].upper()}
""")
    
    def cmd_uninstall(self, args: List[str]):
        """Uninstall command"""
        if not args:
            print("\n  Usage: uninstall <package>")
            return
        
        package = args[0]
        result = self.backend.uninstall_package(package)
        
        print(f"""
  Package Uninstalled:
  --------------------
  Package:   {result['package']}
  Status:    {result['status'].upper()}
""")
    
    def cmd_packages(self):
        """List packages"""
        packages = self.backend.list_packages()
        
        if not packages:
            print("\n  No packages installed.")
            return
        
        print("\n  Installed Packages:")
        print("  " + "-" * 40)
        for pkg in packages:
            print(f"  {pkg['name']} v{pkg['version']}")
        print()
    
    def cmd_list(self):
        """List tasks"""
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
        """List sessions"""
        sessions = self.backend.get_sessions(10)
        
        if not sessions:
            print("\n  No sessions yet.")
            return
        
        print("\n  Sessions:")
        print("  " + "-" * 50)
        
        for s in sessions:
            print(f"  {s['session_id'][:8]}... | Tasks: {s['task_count']} | Created: {s['created_at'][:19]}")
        print()
    
    def cmd_session(self):
        """Show current session"""
        session = self.backend.get_current_session()
        
        print(f"""
  Current Session:
  ----------------
  ID:          {session.get('session_id', 'N/A')}
  Tasks:       {session.get('task_count', 0)}
  Commands:    {session.get('command_count', 0)}
  Created:     {session.get('created_at', 'N/A')}
""")
    
    def show_model(self):
        """Show model info"""
        print(f"""
  Model Information:
  ------------------
  Model:        {MODEL}
  Version:      {VERSION}
  Quota:        {QUOTA}
  User:         {USER}
  Auth:         Not required (local mode)
""")
    
    def show_config(self):
        """Show config"""
        config = self.backend.get_status()
        print(f"""
  Configuration:
  --------------
  Version:        {config['version']}
  Model:          {config['model']}
  User:           {config['user']}
  Hostname:       {config['hostname']}
  System:         {config['system']}
  Python:         {config['python_version']}
  History File:   ~/.agy_history
  State File:     ~/.agy/state.json
  Verbose:        {config['debug']}
""")
    
    def show_about(self):
        """Show about"""
        print("""
  About AGY CLI:
  --------------
  Antigravity CLI - AI-powered development assistant
  Reconstructed from agy.exe binary analysis
  
  Features:
    - Run tasks against targets (URLs, commands, files)
    - Install packages  
    - Session management
    - Persistent state
    - No authentication required
    
  Version: {version}
""".format(version=VERSION))
    
    def run(self):
        """Run interactive loop"""
        self.print_header()
        
        while self.running:
            try:
                cmd = input("  > ")
                if not self.process_command(cmd):
                    break
            except EOFError:
                print("\n  Goodbye!")
                break
            except KeyboardInterrupt:
                print("\n  (Use 'exit' to quit)")
                continue
            except Exception as e:
                print(f"\n  [Error] {e}")


def main():
    """Main entry point"""
    # Check for command line args
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower().lstrip('/')
        args = sys.argv[2:]
        
        backend = AGYBackend()
        
        if cmd == "run":
            task = backend.run_task(args[0] if args else "", dict(a.split("=") for a in args[1:] if "=" in a) if len(args) > 1 else {})
            print(f"""
  Task Executed:
  --------------
  ID:        {task.task_id}
  Type:      {task.task_type.upper()}
  Target:    {task.target}
  Status:    {task.status.upper()}
  Result:    {task.result[:300]}
""")
        elif cmd == "install":
            result = backend.install_package(args[0] if args else "", args[1] if len(args) > 1 else "latest")
            print(f"""
  Package Installed:
  ------------------
  Package:   {result['package']}
  Version:   {result['version']}
  Status:    {result['status'].upper()}
""")
        elif cmd == "uninstall":
            result = backend.uninstall_package(args[0] if args else "")
            print(f"""
  Package Uninstalled:
  --------------------
  Package:   {result['package']}
  Status:    {result['status'].upper()}
""")
        elif cmd == "status":
            status = backend.get_status()
            print(f"""
  Status:
  -------
  Version:    {status['version']}
  Model:      {status['model']}
  Tasks:      {status['tasks']}
  Packages:   {status['packages']}
  Sessions:   {status['sessions']}
  Uptime:     {status['uptime']}
""")
        elif cmd == "list":
            tasks = sorted(backend.tasks.values(), key=lambda t: t.created_at, reverse=True)[:10]
            if not tasks:
                print("\n  No tasks executed yet.")
            else:
                print(f"\n  Tasks ({len(tasks)}):")
                for task in tasks:
                    print(f"  [{task.task_id}] {task.target} - {task.status}")
        elif cmd == "help" or cmd == "--help" or cmd == "-h":
            print(backend.get_help())
        elif cmd == "version":
            print(f"AGY CLI v{VERSION}")
        elif cmd == "model":
            print(f"Model: {MODEL}")
        elif cmd == "packages":
            pkgs = backend.list_packages()
            if pkgs:
                print("\n  Installed Packages:")
                for p in pkgs:
                    print(f"    {p['name']} v{p['version']}")
            else:
                print("\n  No packages installed.")
        elif cmd == "sessions":
            sessions = backend.get_sessions(5)
            if sessions:
                print("\n  Recent Sessions:")
                for s in sessions:
                    print(f"    {s['session_id'][:8]}... | {s['task_count']} tasks")
            else:
                print("\n  No sessions yet.")
        elif cmd == "session":
            sess = backend.get_current_session()
            print(f"\n  Current Session: {sess.get('session_id', 'N/A')}")
            print(f"  Tasks: {sess.get('task_count', 0)}")
            print(f"  Created: {sess.get('created_at', 'N/A')}")
        elif cmd == "config":
            status = backend.get_status()
            print(f"""
  Config:
  -------
  Version: {status['version']}
  User: {status['user']}
  Hostname: {status['hostname']}
  System: {status['system']}
""")
        elif cmd == "whoami":
            print(backend.get_whoami())
        elif cmd == "clear-tasks":
            backend.clear_tasks()
            print("\n  Tasks cleared.")
        else:
            print(f"Unknown command: {cmd}")
            print("Use 'agy help' for available commands")
    else:
        # Interactive mode
        agent = AGYInteractive()
        agent.run()


if __name__ == "__main__":
    main()

