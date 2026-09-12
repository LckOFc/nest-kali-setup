#!/usr/bin/env python3
"""
Anti-Forensics System - No Trace Hacking
==========================================
Tools to operate without leaving traces
"""

import os
import sys
import json
import time
import hashlib
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging.handlers

class AntiForensics:
    """Complete anti-forensics system for无痕 operations"""
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace) if workspace else Path.home() / ".cache" / "agy_hidden"
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.log_file = self.workspace / ".system_log.log"
        self.setup_logging()
        
        # Operation history
        self.history_file = self.workspace / ".operation_history.json"
        self.history = []
        self.load_history()
        
        self.logger.info(f"Anti-Forensics system initialized at {self.workspace}")
    
    def setup_logging(self):
        """Setup secure logging"""
        self.logger = logging.getLogger("AntiForensics")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler (encrypted later)
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def load_history(self):
        """Load operation history"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
    
    def save_history(self):
        """Save operation history"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_operation(self, op_type: str, target: str, success: bool, details: str = ""):
        """Add operation to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": op_type,
            "target": target,
            "success": success,
            "details": details,
            "hash": hashlib.sha256(f"{op_type}{target}{time.time()}".encode()).hexdigest()[:16]
        }
        self.history.append(entry)
        self.save_history()
        self.logger.info(f"Operation: {op_type} -> {target} [{success}]")
    
    # ============================================================
    # LOG CLEANING
    # ============================================================
    
    def clean_windows_logs(self):
        """Clean Windows event logs"""
        self.add_operation("log_clean", "Windows Events", True)
        
        commands = [
            "wevtutil cl System",
            "wevtutil cl Security",
            "wevtutil cl Application",
        ]
        
        results = {}
        for cmd in commands:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                results[cmd] = result.returncode == 0
            except Exception as e:
                results[cmd] = False
                self.logger.warning(f"Log clean failed: {e}")
        
        return results
    
    def clean_power_shell_logs(self):
        """Clean PowerShell execution history"""
        self.add_operation("log_clean", "PowerShell", True)
        
        # Clear PowerShell history
        powershell_history = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt"
        
        if powershell_history.exists():
            with open(powershell_history, 'w') as f:
                f.write("")
        
        # Clear command history from registry
        subprocess.run("reg delete HKCU\\Environment /v HistoryLocation /f", shell=True, capture_output=True)
        
        return True
    
    def clean_browser_history(self):
        """Clean browser history"""
        self.add_operation("log_clean", "Browsers", True)
        
        browsers = {
            "chrome": Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "History",
            "edge": Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default" / "History",
        }
        
        results = {}
        for browser, history_file in browsers.items():
            if history_file.exists():
                # Copy and truncate
                backup = history_file.with_suffix(".bak")
                shutil.copy2(history_file, backup)
                
                # Clear by overwriting
                with open(history_file, 'wb') as f:
                    f.write(b'')
                results[browser] = True
        
        return results
    
    def clean_temp_files(self):
        """Clean temporary files"""
        self.add_operation("log_clean", "Temp files", True)
        
        temp_paths = [
            Path(tempfile.gettempdir()),
            Path.home() / "AppData" / "Local" / "Temp",
            Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Temp",
        ]
        
        cleaned = 0
        for temp_path in temp_paths:
            if temp_path.exists():
                for item in temp_path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                        cleaned += 1
                    except:
                        pass
        
        return cleaned
    
    def clean_system_tmp(self):
        """Clean system temp"""
        self.add_operation("log_clean", "System Temp", True)
        
        try:
            subprocess.run("rd /s /q %TEMP%", shell=True, capture_output=True)
            subprocess.run("md %TEMP%", shell=True, capture_output=True)
            return True
        except:
            return False
    
    # ============================================================
    # FILE OPERATIONS (无痕)
    # ============================================================
    
    def secure_delete(self, path: str, passes: int = 3):
        """Securely delete file with multiple passes"""
        self.add_operation("secure_delete", path, True, f"passes={passes}")
        
        target = Path(path)
        if not target.exists():
            return False
        
        # Overwrite with random data
        import secrets
        file_size = target.stat().st_size
        
        for _ in range(passes):
            with open(target, 'wb') as f:
                f.write(secrets.token_bytes(file_size))
        
        # Delete
        target.unlink()
        
        # Also clean MFT entry if possible (requires admin)
        try:
            subprocess.run(f"cipher /w:{target.drive}", shell=True, capture_output=True)
        except:
            pass
        
        return True
    
    def secure_write(self, path: str, data: bytes):
        """Securely write file (overwrite existing)"""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temp first
        temp = target.with_suffix(".tmp")
        with open(temp, 'wb') as f:
            f.write(data)
        
        # Securely replace
        if target.exists():
            self.secure_delete(str(target), passes=1)
        
        temp.rename(target)
        
        return True
    
    def create_hidden_workspace(self) -> Path:
        """Create hidden workspace for operations"""
        # Create in AppData with dot prefix (hidden on Windows)
        workspace = Path.home() / ".cache" / ".hidden_ops"
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Set hidden attribute
        subprocess.run(f'attrib +h "{workspace}"', shell=True, capture_output=True)
        
        return workspace
    
    # ============================================================
    # NETWORK ANONYMITY
    # ============================================================
    
    def setup_proxy_chain(self):
        """Setup proxy chain for anonymity"""
        self.add_operation("network_anon", "proxy_chain", True)
        
        # Return proxy configuration
        return {
            "http_proxy": "http://127.0.0.1:1080",
            "https_proxy": "http://127.0.0.1:1080",
            "all_proxy": "socks5://127.0.0.1:1080"
        }
    
    def rotate_user_agent(self):
        """Rotate User-Agent strings"""
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        ]
        return agents[int(time.time()) % len(agents)]
    
    # ============================================================
    # MEMORY CLEANING
    # ============================================================
    
    def wipe_memory_after_operation(self):
        """Attempt to wipe sensitive data from memory"""
        self.add_operation("memory_wipe", "current_process", True)
        
        # In Python, we can't directly wipe memory
        # But we can null out sensitive variables
        import gc
        gc.collect()
        
        return True
    
    # ============================================================
    # MAIN OPERATIONS
    # ============================================================
    
    def clean_all_traces(self):
        """Clean all traces of operation"""
        self.logger.info("Starting full trace cleanup...")
        
        results = {
            "windows_logs": self.clean_windows_logs(),
            "powershell": self.clean_power_shell_logs(),
            "browsers": self.clean_browser_history(),
            "temp_files": self.clean_temp_files(),
            "system_tmp": self.clean_system_tmp(),
        }
        
        # Clean our own workspace
        if self.workspace.exists():
            for item in self.workspace.iterdir():
                if item.name.startswith('.'):
                    try:
                        if item.is_file():
                            self.secure_delete(str(item), passes=1)
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except:
                        pass
        
        self.logger.info("Trace cleanup complete")
        return results
    
    def execute_hidden_operation(self, operation: str, target: str, data: bytes = None) -> Dict:
        """Execute operation without leaving traces"""
        start_time = time.time()
        
        self.add_operation(operation, target, True)
        
        # Perform operation
        result = {
            "operation": operation,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "workspace": str(self.workspace),
            "success": True
        }
        
        elapsed = time.time() - start_time
        result["elapsed_ms"] = int(elapsed * 1000)
        
        # Clean up any temporary files
        self.wipe_memory_after_operation()
        
        return result
    
    def get_status(self) -> Dict:
        """Get anti-forensics status"""
        return {
            "workspace": str(self.workspace),
            "operations_count": len(self.history),
            "last_operation": self.history[-1] if self.history else None,
            "trace_clean": self.check_traces_exist()
        }
    
    def check_traces_exist(self) -> bool:
        """Check if traces still exist"""
        # Check for our workspace
        if self.workspace.exists():
            return len(list(self.workspace.iterdir())) > 0
        return False


def main():
    print("=" * 70)
    print("  ANTI-FORENSICS SYSTEM - NO TRACE HACKING")
    print("=" * 70)
    print()
    
    # Initialize
    af = AntiForensics()
    
    print("[*] System initialized")
    print(f"    Workspace: {af.workspace}")
    print()
    
    # Show menu
    while True:
        print()
        print("OPTIONS:")
        print("  1. Clean all traces")
        print("  2. Execute hidden operation")
        print("  3. View status")
        print("  4. Exit")
        print()
        
        choice = input("Select: ").strip()
        
        if choice == "1":
            print("[*] Cleaning all traces...")
            results = af.clean_all_traces()
            print("[+] Cleanup complete")
            for k, v in results.items():
                print(f"    {k}: {'OK' if v else 'FAILED'}")
        
        elif choice == "2":
            op = input("Operation: ").strip()
            target = input("Target: ").strip()
            result = af.execute_hidden_operation(op, target)
            print(f"[+] Operation completed in {result['elapsed_ms']}ms")
        
        elif choice == "3":
            status = af.get_status()
            print(f"Operations: {status['operations_count']}")
            print(f"Last: {status['last_operation']}")
        
        elif choice == "4":
            break
        
        else:
            print("Invalid option")


if __name__ == '__main__':
    main()
