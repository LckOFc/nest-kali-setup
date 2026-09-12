"""
behavioral_sandbox.py
Behavioral sandbox for monitoring executable behavior
"""
import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

@dataclass
class SandboxEvent:
    timestamp: float
    event_type: str  # file_create, file_modify, reg_write, network_connect, process_create, crypto_op, inject_attempt
    target: str
    details: dict
    severity: str  # info, low, medium, high, critical

class BehavioralSandbox:
    """
    Sandbox comportamental para execucao e monitoramento de binarios.
    
    Observa:
    - Criacao/modificacao de arquivos
    - Modificacoes de registro
    - Conexoes de rede
    - Criacao de processos filhos
    - Operacoes criptograficas
    """
    
    SUSPICIOUS_PATHS = [
        r'%TEMP%', r'\AppData\Local\Temp', r'\Windows\Temp',
        r'\AutoRun', r'\Startup', r'\Run', r'\RunOnce',
        r'\System32\Tasks', r'\SchTasks',
    ]
    
    SUSPICIOUS_REGISTRY_KEYS = [
        r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
        r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
        r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
        r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
    ]
    
    SUSPICIOUS_NETWORK_PORTS = [4444, 5555, 8888, 1337, 31337]
    
    def __init__(self, timeout_seconds: int = 60):
        self.timeout = timeout_seconds
        self.events: list[SandboxEvent] = []
        self.snapshots = {
            "files": set(),
            "registry_keys": set(),
            "network_connections": set(),
            "running_processes": set()
        }
    
    async def run(self, executable: str, args: str = "", quiet: bool = False) -> dict:
        """Executa binario e monitora comportamento."""
        self.events = []
        start_time = time.time()
        
        # Snapshot inicial
        initial_state = self._take_snapshot()
        
        # Executa o processo
        proc = await self._launch_process(executable, args)
        
        # Monitora durante execucao
        monitor_tasks = [
            asyncio.create_task(self._monitor_files(initial_state["files"])),
            asyncio.create_task(self._monitor_registry(initial_state["registry_keys"])),
            asyncio.create_task(self._monitor_network()),
            asyncio.create_task(self._monitor_processes(initial_state["processes"]))
        ]
        
        try:
            if quiet:
                await asyncio.wait_for(proc.wait(), timeout=self.timeout)
            else:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
        except asyncio.TimeoutError:
            proc.kill()
            stdout, stderr = b"", b"TIMEOUT"
        
        # Cancela monitores
        for task in monitor_tasks:
            task.cancel()
        
        elapsed = time.time() - start_time
        
        # Analisa resultados
        threats = self._analyze_threats()
        threat_score = self._calculate_threat_score(threats)
        
        return {
            "executable": executable,
            "args": args,
            "duration_seconds": round(elapsed, 2),
            "exit_code": proc.returncode,
            "stdout_length": len(stdout),
            "stderr_length": len(stderr),
            "events_count": len(self.events),
            "threat_score": threat_score,
            "threat_level": self._score_to_level(threat_score),
            "threats_detected": threats,
            "events": [asdict(e) for e in self.events[-50:]],  # ultimos 50 eventos
            "summary": self._generate_summary(threats)
        }
    
    async def _launch_process(self, executable: str, args: str = "") -> asyncio.subprocess.Process:
        """Lanca o processo monitorado."""
        cmd = [executable] + args.split() if args else [executable]
        return await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    
    def _take_snapshot(self) -> dict:
        """Tira snapshot do estado inicial do sistema."""
        return {
            "files": set(),
            "registry_keys": set(),
            "network_connections": set(),
            "processes": set()
        }
    
    async def _monitor_files(self, initial_files: set):
        """Monitora criacao/modificacao de arquivos."""
        import os
        temp_dirs = [
            os.environ.get('TEMP', '/tmp'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            os.path.join(os.environ.get('WINDIR', ''), 'Temp')
        ]
        
        while True:
            try:
                for temp_dir in temp_dirs:
                    if Path(temp_dir).exists():
                        current_files = set(str(p) for p in Path(temp_dir).rglob('*') if p.is_file())
                        new_files = current_files - initial_files
                        
                        for f in new_files:
                            if self._is_suspicious_path(f):
                                self.events.append(SandboxEvent(
                                    timestamp=time.time(),
                                    event_type="file_create",
                                    target=f,
                                    details={"path_type": "temp", "suspicious": True},
                                    severity="high"
                                ))
                        
                        initial_files.update(current_files)
            except Exception:
                pass
            await asyncio.sleep(0.5)
    
    async def _monitor_registry(self, initial_keys: set):
        """Monitora modificacoes no registro."""
        # Em Windows real, usariamos wmi ou pywin32
        # Aqui simula o monitoramento
        while True:
            await asyncio.sleep(1)
    
    async def _monitor_network(self):
        """Monitora conexoes de rede."""
        while True:
            try:
                # Em Windows real, usar wmi Win32_NetworkConnection
                # Aqui simulamos a logica
                await asyncio.sleep(2)
            except:
                break
    
    async def _monitor_processes(self, initial_procs: set):
        """Monitora criacao de processos."""
        import psutil
        while True:
            try:
                current_procs = set(p.pid for p in psutil.process_iter(['pid', 'name']))
                # Detecta spawns suspeitos
                for pid in current_procs:
                    try:
                        proc = psutil.Process(pid)
                        if proc.name().lower() in ('cmd.exe', 'powershell.exe', 'psexec.exe', 'mimikatz.exe'):
                            # Processo suspeito detectado
                            self.events.append(SandboxEvent(
                                timestamp=time.time(),
                                event_type="suspicious_process",
                                target=f"{proc.name()} (PID: {pid})",
                                details={"parent": proc.parent().name() if proc.parent() else "unknown"},
                                severity="critical"
                            ))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception:
                pass
            await asyncio.sleep(1)
    
    def _is_suspicious_path(self, path: str) -> bool:
        """Verifica se caminho é suspeito."""
        import re
        for pattern in self.SUSPICIOUS_PATHS:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        return False
    
    def _analyze_threats(self) -> list[dict]:
        """Análise de ameaças baseada nos eventos."""
        threats = []
        
        # Agrupa eventos
        file_events = [e for e in self.events if e.event_type == "file_create"]
        process_events = [e for e in self.events if e.event_type == "suspicious_process"]
        
        # Regras de detecção
        if any(self._is_suspicious_path(e.target) for e in file_events):
            suspicious_count = len([e for e in file_events if self._is_suspicious_path(e.target)])
            threats.append({
                "type": "SUSPICIOUS_FILE_OPERATION",
                "severity": "high",
                "count": suspicious_count,
                "description": f"Arquivos criados em paths suspeitos ({suspicious_count}x)"
            })
        
        if process_events:
            threats.append({
                "type": "SUSPICIOUS_PROCESS_SPAWN",
                "severity": "critical",
                "count": len(process_events),
                "description": f"Processos suspeitos detectados ({len(process_events)}x)"
            })
        
        # Contagem de eventos por severity
        high_critical = len([e for e in self.events if e.severity in ("high", "critical")])
        if high_critical > 5:
            threats.append({
                "type": "HIGH_ACTIVITY_VOLUME",
                "severity": "medium",
                "count": high_critical,
                "description": f"Volume alto de atividades suspeitas ({high_critical} eventos)"
            })
        
        return threats
    
    def _calculate_threat_score(self, threats: list[dict]) -> int:
        """Score de 0-100 baseado nas ameaças."""
        severity_weights = {"info": 5, "low": 15, "medium": 30, "high": 60, "critical": 100}
        score = 0
        for t in threats:
            score += severity_weights.get(t["severity"], 10) * min(t["count"], 5)  # cap em 5
        return min(100, score)
    
    def _score_to_level(self, score: int) -> str:
        """Converte score para nivel."""
        if score <= 20:
            return "SAFE"
        elif score <= 40:
            return "LOW"
        elif score <= 60:
            return "MEDIUM"
        elif score <= 80:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _generate_summary(self, threats: list[dict]) -> str:
        """Resumo legivel do comportamento."""
        if not threats:
            return "Nenhuma atividade maliciosa detectada."
        
        lines = [f"Detectado {len(threats)} tipo(s) de ameaca:"]
        for t in threats:
            lines.append(f"  - [{t['severity'].upper()}] {t['description']}")
        return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Behavioral Sandbox")
    parser.add_argument("executable", help="Binário para analisar")
    parser.add_argument("--args", "-a", default="", help="Argumentos do programa")
    parser.add_argument("--timeout", "-t", type=int, default=60, help="Timeout em segundos")
    parser.add_argument("--quiet", "-q", action="store_true", help="Silenciar stdout/stderr")
    parser.add_argument("--output", "-o", help="Salvar resultado em JSON")
    args = parser.parse_args()
    
    async def main():
        sandbox = BehavioralSandbox(timeout_seconds=args.timeout)
        result = await sandbox.run(args.executable, args=args.args, quiet=args.quiet)
        
        # Output
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2))
            print(f"Resultado salvo em: {args.output}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"BEHAVIORAL SANDBOX RESULT")
        print(f"{'='*60}")
        print(f"Executable: {result['executable']}")
        print(f"Duration: {result['duration_seconds']}s")
        print(f"Exit Code: {result['exit_code']}")
        print(f"Threat Score: {result['threat_score']}/100 ({result['threat_level']})")
        print(f"Events: {result['events_count']}")
        print(f"\n{result['summary']}")
        
        if result['threats_detected']:
            print(f"\nThreats Detected:")
            for t in result['threats_detected']:
                print(f"  [{t['severity'].upper()}] {t['type']}: {t['description']}")
    
    asyncio.run(main())
