"""
anti_sandbox_buster.py
Detecção e bypass de técnicas anti-sandbox/anti-VM em malwares
"""
import asyncio
import json
import platform
import socket
import subprocess
import time
import wmi
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, list

@dataclass
class SandboxIndicator:
    name: str
    category: str  # vm, sandbox, analysis_tool, freshness
    severity: str
    evidence: str
    bypass_possible: bool

@dataclass
class BypassAction:
    action: str
    description: str
    implementation: str
    risk: str

class AntiSandboxBuster:
    """
    Detector e bypass de técnicas anti-sandbox/anti-VM.
    
    Categorias de detecção:
    1. VM Detection (Hyper-V, VMware, VirtualBox, QEMU)
    2. Sandbox Detection (network, hardware, behavior)
    3. Analysis Tool Detection (debuggers, sandboxes)
    4. Freshness Detection (time-based, first-run checks)
    5. User Presence Detection
    6. Resource Limit Detection
    """
    
    # Indicadores de VM
    VM_INDICATORS = {
        'hyper_v': {
            'registry': [r'HKEY_LOCAL_MACHINE\HARDWARE\DEVICEMAP\Virtualization'],
            'bios': ['Hyper-V', 'Microsoft'],
            'cpuinfo': ['Hyper-V', 'hypervisor'],
            'severity': 'high'
        },
        'vmware': {
            'registry': [
                r'HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\BIOS',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\VMware, Inc.\VMware Tools',
            ],
            'strings': ['VMware', 'vmware', 'VMW'],
            'mac_prefix': ['00:0C:29', '00:50:56', '00:05:69'],
            'severity': 'high'
        },
        'virtualbox': {
            'registry': [r'HKEY_LOCAL_MACHINE\HARDWARE\ACPI\DSDT\VBOX__'],
            'strings': ['VBox', 'VBOX', 'VirtualBox'],
            'severity': 'high'
        },
        'qemu': {
            'strings': ['QEMU', 'qemu'],
            'severity': 'medium'
        },
        'parallels': {
            'strings': ['Parallels'],
            'severity': 'medium'
        },
    }
    
    # Indicadores de sandbox
    SANDBOX_INDICATORS = {
        'cuckoo': {
            'files': [r'C:\cuckoo', r'C:\Program Files\Cuckoo'],
            'processes': ['cuckoo', 'cuckood', 'aux', 'helper.exe'],
            'severity': 'high'
        },
        'any.run': {
            'processes': ['any.run', 'anysign'],
            'severity': 'high'
        },
        'joe_sandbox': {
            'files': [r'C:\JoeSandbox'],
            'processes': ['joewIN32', 'joe'],
            'severity': 'high'
        },
        'virustotal': {
            'processes': ['vtanalysis', 'vtwin32'],
            'severity': 'medium'
        },
    }
    
    # Indicadores de ferramentas de análise
    ANALYSIS_TOOLS = {
        'ollydbg': {'processes': ['ollydbg', 'ollydbg2']},
        'x64dbg': {'processes': ['x64dbg', 'x32dbg', 'debugging']},
        'idapro': {'processes': ['ida', 'idasvc', 'idag']},
        'process_hacker': {'processes': ['procmon', 'procexp', 'processhacker']},
        'api_monitor': {'processes': ['apimon', 'api monitor']},
        'process_monitor': {'processes': ['procmon64', 'procmon']},
    }
    
    def __init__(self):
        self.wmi_service = None
        self.indicators: list[SandboxIndicator] = []
        self.bypasses: list[BypassAction] = []
    
    async def analyze_environment(self) -> dict:
        """Análise completa do ambiente atual."""
        results = {
            "timestamp": time.time(),
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "vm_detected": False,
            "sandbox_detected": False,
            "analysis_tools_detected": False,
            "freshness_score": 0.0,
            "indicators": [],
            "bypass_recommendations": []
        }
        
        # 1. Detecção de VM
        vm_results = await self._detect_vm()
        results["vm_detected"] = any(v.severity in ("high", "critical") for v in vm_results)
        results["indicators"].extend([
            {"type": "vm", "name": v.name, "severity": v.severity, "evidence": v.evidence}
            for v in vm_results
        ])
        
        # 2. Detecção de sandbox
        sandbox_results = await self._detect_sandbox()
        results["sandbox_detected"] = len(sandbox_results) > 0
        results["indicators"].extend([
            {"type": "sandbox", "name": s.name, "severity": s.severity, "evidence": s.evidence}
            for s in sandbox_results
        ])
        
        # 3. Ferramentas de análise
        tools_results = await self._detect_analysis_tools()
        results["analysis_tools_detected"] = len(tools_results) > 0
        results["indicators"].extend([
            {"type": "tool", "name": t.name, "severity": t.severity, "evidence": t.evidence}
            for t in tools_results
        ])
        
        # 4. Freshness (idade do sistema)
        freshness = await self._check_freshness()
        results["freshness_score"] = freshness
        
        # 5. Gera recomendações de bypass
        results["bypass_recommendations"] = self._generate_bypasses(results)
        
        return results
    
    async def _detect_vm(self) -> list[SandboxIndicator]:
        """Detecta máquinas virtuais."""
        indicators = []
        
        try:
            c = wmi.WMI()
            
            # BIOS/Win32_BIOS
            for bios in c.Win32_BIOS():
                bios_str = f"{bios.Manufacturer} {bios.Version} {bios.Description}".upper()
                for vm_name, vm_data in self.VM_INDICATORS.items():
                    for keyword in vm_data.get('strings', []) + vm_data.get('bios', []):
                        if keyword.upper() in bios_str:
                            indicators.append(SandboxIndicator(
                                name=f"vm_{vm_name}",
                                category="vm",
                                severity=vm_data['severity'],
                                evidence=f"BIOS contains '{keyword}' in: {bios_str[:80]}",
                                bypass_possible=True
                            ))
            
            # Win32_ComputerSystem (Manufacturer)
            for cs in c.Win32_ComputerSystem():
                manuf = cs.Manufacturer.upper()
                if 'VMWARE' in manuf:
                    indicators.append(SandboxIndicator("vm_vmware", "vm", "high",
                        f"System manufacturer: {manuf}", True))
                elif 'VIRTUALBOX' in manuf or 'ORACLE' in manuf:
                    indicators.append(SandboxIndicator("vm_virtualbox", "vm", "high",
                        f"System manufacturer: {manuf}", True))
                elif 'HYPER-V' in manuf or 'MICROSOFT' in manuf:
                    indicators.append(SandboxIndicator("vm_hyper_v", "vm", "high",
                        f"System manufacturer: {manuf}", True))
            
            # Win32_Processor (ProcessorId, Name)
            for cpu in c.Win32_Processor():
                proc_str = f"{cpu.Name} {cpu.ProcessorId}".upper()
                if 'HYPERVISOR' in proc_str or 'VM' in cpu.Name.upper():
                    indicators.append(SandboxIndicator("vm_cpu_hypervisor", "vm", "high",
                        f"CPU indicates hypervisor: {cpu.Name[:50]}", True))
            
            # Win32_BaseBoard (Manufacturer, Product)
            for board in c.Win32_BaseBoard():
                board_str = f"{board.Manufacturer} {board.Product}".upper()
                for vm_name in ['VMWARE', 'VIRTUALBOX', 'QEMU']:
                    if vm_name in board_str:
                        indicators.append(SandboxIndicator(f"vm_board_{vm_name.lower()}", "vm", "high",
                            f"Base board: {board_str[:60]}", True))
            
            # Win32_VideoController (adaptador de vídeo)
            for video in c.Win32_VideoController():
                vid_str = video.Name.upper()
                for vm_name in ['VMWARE', 'VIRTUALBOX', 'QEMU', 'RED HAT', 'BOCHS']:
                    if vm_name in vid_str:
                        indicators.append(SandboxIndicator(f"vm_video_{vm_name.lower()}", "vm", "high",
                            f"Video controller: {vid_str[:50]}", True))
            
            # Win32_DiskDrive (modelo do disco)
            for disk in c.Win32_DiskDrive():
                disk_str = f"{disk.Model} {disk.Series}".upper()
                if 'VMWARE' in disk_str or 'VIRTUAL DISK' in disk_str:
                    indicators.append(SandboxIndicator("vm_disk", "vm", "medium",
                        f"Disk model: {disk.Model[:50]}", True))
            
            # Win32_NetworkAdapter (MAC address prefixes)
            for nic in c.Win32_NetworkAdapter():
                mac = (nic.MACAddress or '').upper()
                for prefix, vm_name in [('00:0C:29', 'vmware'), ('00:50:56', 'vmware'),
                                        ('08:00:27', 'virtualbox'), ('52:54:00', 'qemu')]:
                    if mac.startswith(prefix):
                        indicators.append(SandboxIndicator(f"vm_nic_{vm_name}", "vm", "high",
                            f"MAC prefix {prefix} indicates {vm_name}", True))
            
            #registry check (limited in WMI, use subprocess)
            reg_check = await self._check_vm_registry()
            indicators.extend(reg_check)
            
        except Exception as e:
            indicators.append(SandboxIndicator("wmi_error", "vm", "low",
                f"WMI query failed: {e}", False))
        
        return indicators
    
    async def _check_vm_registry(self) -> list[SandboxIndicator]:
        """Verifica registry para indicadores de VM."""
        indicators = []
        import subprocess
        
        # Keys que indicam VM
        vm_registry_keys = [
            r'HKEY_LOCAL_MACHINE\HARDWARE\DEVICEMAP\Virtualization',
            r'HKEY_LOCAL_MACHINE\SOFTWARE\VMware, Inc.\VMware Tools',
            r'HKEY_LOCAL_MACHINE\SOFTWARE\Oracle\VirtualBox Guest Additions',
            r'HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Services\VBoxGuest',
            r'HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Services\VBoxService',
        ]
        
        for key in vm_registry_keys:
            try:
                result = subprocess.run(
                    ['reg', 'query', key],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    indicators.append(SandboxIndicator(
                        "vm_registry", "vm", "high",
                        f"VM registry key found: {key}", True
                    ))
            except:
                pass
        
        return indicators
    
    async def _detect_sandbox(self) -> list[SandboxIndicator]:
        """Detecta ambientes de sandbox."""
        indicators = []
        
        try:
            c = wmi.WMI()
            
            # Processos de sandbox conhecidos
            sandbox_processes = []
            for name, data in self.SANDBOX_INDICATORS.items():
                for proc in data.get('processes', []):
                    sandbox_processes.append(proc.lower())
            
            running_procs = set()
            for proc in c.Win32_Process():
                proc_name = (proc.Name or '').lower()
                running_procs.add(proc_name)
                for sp in sandbox_processes:
                    if sp in proc_name:
                        indicators.append(SandboxIndicator(
                            f"sandbox_{name}", "sandbox", data['severity'],
                            f"Sandbox process detected: {proc.Name}", True
                        ))
            
            # Caminhos de sandbox
            sandbox_paths = []
            for name, data in self.SANDBOX_INDICATORS.items():
                for path in data.get('files', []):
                    sandbox_paths.append(path)
            
            for spath in sandbox_paths:
                if Path(spath).exists():
                    indicators.append(SandboxIndicator(
                        "sandbox_path", "sandbox", "high",
                        f"Sandbox path exists: {spath}", True
                    ))
            
            # Recursos limitados (indicador de sandbox)
            try:
                # CPU count baixo
                cpu_count = len(asyncio.get_event_loop().run_in_executor(None, os.cpu_count) or 1)
                if cpu_count <= 2:
                    indicators.append(SandboxIndicator(
                        "low_cpu_count", "sandbox", "medium",
                        f"Only {cpu_count} CPU(s) detected (sandbox-like)", True
                    ))
                
                # Memória baixa
                import psutil
                mem = psutil.virtual_memory()
                if mem.total < 4 * 1024 * 1024 * 1024:  # 4GB
                    indicators.append(SandboxIndicator(
                        "low_memory", "sandbox", "medium",
                        f"Only {mem.total // (1024**3)}GB RAM (sandbox-like)", True
                    ))
            except:
                pass
            
            # Resolução de tela baixa (sandbox)
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Monitors')
                # Simplificado - apenas verifica existência
            except:
                pass
            
        except Exception as e:
            indicators.append(SandboxIndicator("sandbox_detect_error", "sandbox", "low",
                f"Detection error: {e}", False))
        
        return indicators
    
    async def _detect_analysis_tools(self) -> list[SandboxIndicator]:
        """Detecta ferramentas de análise em execução."""
        indicators = []
        
        try:
            import wmi
            c = wmi.WMI()
            
            for proc in c.Win32_Process():
                proc_name = (proc.Name or '').lower()
                for tool_name, tool_data in self.ANALYSIS_TOOLS.items():
                    for pattern in tool_data.get('processes', []):
                        if pattern in proc_name:
                            indicators.append(SandboxIndicator(
                                f"tool_{tool_name}", "analysis_tool", "medium",
                                f"Analysis tool running: {proc.Name}", True
                            ))
        except:
            pass
        
        return indicators
    
    async def _check_freshness(self) -> float:
        """Calcula score de 'freshness' (sistema novo vs usado)."""
        try:
            # Tempo desde ultimo reboot
            import win32api
            boot_time = win32api.GetLastInputInfo()  # Não exato, mas indica atividade
            
            # Uptime do sistema
            c = wmi.WMI()
            for os in c.Win32_OperatingSystem():
                last_boot = os.LastBootUpTime
                if last_boot:
                    # Converte formato WMI
                    from datetime import datetime
                    boot_dt = datetime.strptime(last_boot[:8], '%Y%m%d')
                    uptime_days = (datetime.now() - boot_dt).days
                    # Sistemas com < 7 dias são suspeitos (sandbox comum)
                    if uptime_days < 7:
                        return 0.8  # Alto risco de sandbox
                    elif uptime_days < 30:
                        return 0.5
                    return 0.1  # Sistema maduro
            
            return 0.0
        except:
            return 0.0
    
    def _generate_bypasses(self, analysis: dict) -> list[BypassAction]:
        """Gera ações de bypass baseadas na análise."""
        bypasses = []
        
        # VM bypass
        if analysis.get('vm_detected'):
            bypasses.extend([
                BypassAction(
                    action="vm_undetected_run",
                    description="Executar em hardware real (não VM)",
                    implementation="Rodar o binário diretamente no host físico",
                    risk="Necessita acesso ao hardware alvo"
                ),
                BypassAction(
                    action="vm_spoof_registry",
                    description="Spoofar registry para esconder VM",
                    implementation="Remover/modificar chaves de registry detectáveis por VM",
                    risk="Modificação do sistema, pode quebrar funcionalidades"
                ),
                BypassAction(
                    action="vm_undetected_process",
                    description="Renomear processo e limpar marcas",
                    implementation="Usar process renaming + memory scrubbing",
                    risk="Pode ser detectado por análise comportamental"
                ),
            ])
        
        # Sandbox bypass
        if analysis.get('sandbox_detected'):
            bypasses.extend([
                BypassAction(
                    action="sandbox_delay",
                    description="Delay inicial para bypass de freshness check",
                    implementation="Sleep(60000-300000) no início da execução",
                    risk="Aumenta tempo de análise"
                ),
                BypassAction(
                    action="sandbox_resource_spoof",
                    description="Spoofar recursos do sistema",
                    implementation="Mockar CPU count, memória, resolução de tela",
                    risk="Complexo de implementar corretamente"
                ),
                BypassAction(
                    action="sandbox_user_interaction",
                    description="Simular interação do usuário",
                    implementation="Movimentar mouse, cliques aleatórios, keys random",
                    risk="Pode ser detectado por análise de padrão"
                ),
            ])
        
        # Analysis tool bypass
        if analysis.get('analysis_tools_detected'):
            bypasses.extend([
                BypassAction(
                    action="tool_termination",
                    description="Tentar terminar processos de análise",
                    implementation="TerminateProcess nos processos detectados",
                    risk="Altamente suspeito, pode triggerar outras defesas"
                ),
                BypassAction(
                    action="tool_hide",
                    description="Esconder janelas de ferramentas",
                    implementation="FindWindow + ShowWindow(SW_HIDE) nas janelas conhecidas",
                    risk="Efeito limitado"
                ),
            ])
        
        self.bypasses = bypasses
        return bypasses
    
    def generate_execution_script(self, output_path: str = None) -> str:
        """Gera script Python para executar com bypasses aplicados."""
        script = '''"""
Anti-Sandbox Execution Script
Gerado por Advanced RE Suite
Aplica bypasses automáticos antes de executar o binário alvo.
"""
import ctypes
import os
import random
import subprocess
import sys
import time
import winreg

def spoof_vm_indicators():
    """Tenta spoofar indicadores de VM no registry."""
    try:
        # Remover chaves de VM conocidas
        vm_keys = [
            r'HARDWARE\\DEVICEMAP\\Virtualization',
            r'SOFTWARE\\VMware, Inc.\\VMware Tools',
        ]
        for key in vm_keys:
            try:
                winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key)
            except:
                pass
    except Exception as e:
        print(f"[!] VM spoof error: {e}")

def delay_execution(seconds: int = 60):
    """Delay para bypass de freshness checks."""
    print(f"[+] Sleeping {seconds}s to bypass freshness checks...")
    time.sleep(seconds)

def spoof_user_activity():
    """Simula atividade de usuário."""
    import random
    # Move mouse aleatoriamente
    ctypes.windll.user32.CursorPos(
        random.randint(100, 900),
        random.randint(100, 700)
    )
    # Click aleatorio
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
    print("[+] Simulated user activity")

def hide_analysis_windows():
    """Tenta esconder janelas de ferramentas de análise."""
    import ctypes
    user32 = ctypes.windll.user32
    
    # Janelas conhecidas de ferramentas
    window_titles = [
        "Process Monitor", "API Monitor", "x64dbg", "x32dbg",
        "IDA Pro", "OllyDbg", "Process Hacker"
    ]
    
    for title in window_titles:
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # SW_HIDE
            print(f"[+] Hidden window: {title}")

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        print("Usage: python anti_sandbox_buster_exec.py <target.exe>")
        sys.exit(1)
    
    print("[*] Applying anti-sandbox bypasses...")
    
    # 1. Delay
    delay_execution(30)
    
    # 2. User activity
    spoof_user_activity()
    
    # 3. Hide analysis windows
    hide_analysis_windows()
    
    # 4. VM spoof
    spoof_vm_indicators()
    
    print(f"[+] Bypasses applied. Launching: {target}")
    
    # Executa o binário alvo
    subprocess.run([target], shell=True)

if __name__ == "__main__":
    main()
'''
        
        output_path = output_path or "./anti_sandbox_bypass.py"
        Path(output_path).write_text(script)
        print(f"Execution script saved to: {output_path}")
        return output_path


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Anti-Sandbox Buster")
    parser.add_argument("--analyze", "-a", action="store_true", help="Analisar ambiente atual")
    parser.add_argument("--script", "-s", action="store_true", help="Gerar script de bypass")
    parser.add_argument("--output", "-o", help="Diretorio de saida")
    args = parser.parse_args()
    
    buster = AntiSandboxBuster()
    
    async def main():
        if args.analyze or not any([args.script]):
            result = await buster.analyze_environment()
            
            print(f"Hostname: {result['hostname']}")
            print(f"OS: {result['os']} {result['os_version']}")
            print(f"VM Detected: {result['vm_detected']}")
            print(f"Sandbox Detected: {result['sandbox_detected']}")
            print(f"Analysis Tools: {result['analysis_tools_detected']}")
            print(f"Freshness Score: {result['freshness_score']:.0%}")
            
            if result['indicators']:
                print(f"\nIndicators ({len(result['indicators'])}):")
                for ind in result['indicators'][:10]:
                    print(f"  [{ind['severity'].upper():8s}] {ind['type']:15s} {ind['name']}")
                    print(f"           {ind['evidence'][:60]}")
            
            if result['bypass_recommendations']:
                print(f"\nBypass Recommendations:")
                for b in result['bypass_recommendations'][:5]:
                    print(f"  • {b.action}: {b.description}")
                    print(f"    Implementation: {b.implementation[:60]}")
        
        if args.script:
            output = args.output or "./anti_sandbox_bypass.py"
            buster.generate_execution_script(output)
    
    asyncio.run(main())
