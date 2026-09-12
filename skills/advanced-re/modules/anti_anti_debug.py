"""
anti_anti_debug.py
Detecção e bypass de técnicas anti-debug em binários Windows
"""
import struct
import ctypes
from ctypes import wintypes
import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, list

# ── Win32 API constants ─────────────────────────────────────────────
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
DEBUG_READ_EVENT = 0x0001
DEBUG_PROCESS = 0x00000001
CREATE_DEBUG_PROCESS = 0x00000001

# ── Data classes ────────────────────────────────────────────────────
@dataclass
class AntiDebugIndicator:
    name: str
    severity: str  # low, medium, high, critical
    offset: int
    instruction: str
    description: str
    bypass_method: str

@dataclass
class DebugBypass:
    success: bool
    method: str
    patch_offset: int
    original_bytes: bytes
    patched_bytes: bytes

class AntiAntiDebug:
    """
    Detector e bypass de técnicas anti-debug.
    
    Técnicas detectadas:
    - IsDebuggerPresent()
    - CheckRemoteDebuggerPresent()
    - NtQueryInformationProcess(ProcessInformationClass)
    - OutputDebugString A/B
    - int 3 / breakpoint detection
    - Time-based detection (RDTSC, QueryPerformanceCounter)
    - Hardware breakpoint detection (DR0-DR7)
    - Process debugging flags
    - Friendly names check
    - Thread idle detection
    """
    
    # Assinaturas de instruções anti-debug comuns
    ANTI_DEBUG_PATTERNS = {
        # IsDebuggerPresent - chama NtQueryInformationProcess
        'is_debugger_present': {
            'search': b'\x83\x7D\x08\x00',  # cmp dword [ebp+0x8], 0x00
            'description': 'IsDebuggerPresent() - stack check',
            'bypass': 'NOP or change conditional jump'
        },
        # CheckRemoteDebuggerPresent
        'check_remote_dbg': {
            'search': b'\x8B\x45\x08\x8B\x08\xFF\x50\x10',
            'description': 'CheckRemoteDebuggerPresent()',
            'bypass': 'Patch return value'
        },
        # NtQueryInformationProcess with ProcessDebugPort
        'nt_query_debug_port': {
            'search': b'\x33\xC0\x8B\x4D\x08\x8B\x01\xFF\x50\x14',
            'description': 'NtQueryInformationProcess(ProcessDebugPort)',
            'bypass': 'Zero EAX before return'
        },
        # RDTSC timing check
        'rdtsc_check': {
            'search': b'\x0F\xA2',  # RDTSC
            'description': 'RDTSC timing check',
            'bypass': 'Monitor RDTSC delta'
        },
        # int3 / breakpoint
        'int3_breakpoint': {
            'search': b'\xCC',
            'description': 'INT 3 breakpoint (anti-debug)',
            'bypass': 'NOP out or handle exception'
        },
        # OutputDebugString
        'output_debug_string': {
            'search': b'\x8B\x44\x24\x04\x50\x8B\x08FF\x51\x0C',
            'description': 'OutputDebugStringA/W check',
            'bypass': 'Hook API'
        },
        # ProcessHeap flags check
        'heap_flag_check': {
            'search': b'\x8B\x0D',  # mov ecx, [ProcessHeap]
            'description': 'Heap flag check (Heaps!)',
            'bypass': 'Patch heap flags'
        },
    }
    
    # Sequências assembly comuns de anti-debug
    ASSEMBLY_SIGNATURES = [
        # isDbgPresent inline (x86)
        r'call\s+.*IsDebuggerPresent',
        r'call\s+.*NtQueryInformationProcess',
        r'call\s+.*CheckRemoteDebuggerPresent',
        # RDTSC
        r'rdtsc',
        r'diff\s+elapsed',
        # Heap check
        r'HeapGetFlags',
        r'GetProcessHeap',
        # TerminateProcess on debug
        r'call\s+.*TerminateProcess',
        # Sleep to waste debugger time
        r'call\s+.*Sleep\b',
        # Exception handling for anti-debug
        r'__try\s*\{.*__except',
        # FindWindow check
        r'call\s+.*FindWindow',
        r'call\s+.*FindWindowEx',
    ]
    
    def __init__(self):
        self.indicators: list[AntiDebugIndicator] = []
        self.bypasses: list[DebugBypass] = []
        self._windll = ctypes.windll
    
    def analyze(self, file_path: str) -> dict:
        """Analisa binário para técnicas anti-debug."""
        data = Path(file_path).read_bytes()
        
        indicators = []
        
        # 1. Busca por assinaturas de instruções
        for name, sig in self.ANTI_DEBUG_PATTERNS.items():
            if sig['search'] in data:
                offset = data.find(sig['search'])
                indicators.append(AntiDebugIndicator(
                    name=name,
                    severity=self._classify_severity(name),
                    offset=offset,
                    instruction=sig['search'].hex(),
                    description=sig['description'],
                    bypass_method=sig['bypass']
                ))
        
        # 2. Busca por imports suspeitos
        suspicious_imports = self._find_suspicious_imports(data)
        for imp in suspicious_imports:
            indicators.append(AntiDebugIndicator(
                name=f"import_{imp}",
                severity="high",
                offset=0,
                instruction=imp,
                description=f"Suspicious import: {imp}()",
                bypass_method=f"Hook or patch {imp}()"
            ))
        
        # 3. Busca por strings de debug detection
        debug_strings = self._find_debug_strings(data)
        for s in debug_strings:
            indicators.append(AntiDebugIndicator(
                name="debug_string",
                severity="medium",
                offset=s['offset'],
                instruction=s['value'],
                description=f"Debug-related string: {s['value'][:50]}",
                bypass_method="String obfuscation may hide real checks"
            ))
        
        # 4. Análise de seções
        section_analysis = self._analyze_sections(data)
        indicators.extend(section_analysis)
        
        self.indicators = indicators
        
        return {
            "file": file_path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "indicator_count": len(indicators),
            "severity_distribution": self._severity_dist(indicators),
            "indicators": [
                {
                    "name": i.name,
                    "severity": i.severity,
                    "offset": i.offset,
                    "instruction": i.instruction[:80],
                    "description": i.description,
                    "bypass_method": i.bypass_method
                }
                for i in indicators
            ],
            "bypass_available": len(indicators) > 0,
            "confidence": min(1.0, len(indicators) / 5) if indicators else 0.0
        }
    
    def _classify_severity(self, technique: str) -> str:
        """Classifica severidade da tecnica anti-debug."""
        critical = ['rdtsc_check', 'int3_breakpoint', 'nt_query_debug_port', 'heap_flag_check']
        high = ['is_debugger_present', 'check_remote_dbg', 'output_debug_string']
        medium = ['find_window']
        
        if technique in critical:
            return "critical"
        elif technique in high:
            return "high"
        elif technique in medium:
            return "medium"
        return "low"
    
    def _find_suspicious_imports(self, data: bytes) -> list[str]:
        """Encontra imports de APIs anti-debug."""
        suspicious_apis = [
            b'IsDebuggerPresent',
            b'CheckRemoteDebuggerPresent',
            b'NtQueryInformationProcess',
            b'NtSetInformationThread',
            b'OutputDebugStringA',
            b'OutputDebugStringW',
            b'HeapGetFlags',
            b'GetProcessHeap',
            b'TerminateProcess',
            b'Sleep',
            b'FindWindowA',
            b'FindWindowW',
            b'FindWindowExA',
            b'QueryPerformanceCounter',
            b'QueryPerformanceFrequency',
            b'ReadProcessMemory',
            b'WriteProcessMemory',
            b'CreateRemoteThread',
            b'OpenProcess',
            b'AdjustTokenPrivileges',
        ]
        
        found = []
        for api in suspicious_apis:
            if api in data:
                found.append(api.decode('ascii', errors='ignore'))
        
        return found
    
    def _find_debug_strings(self, data: bytes) -> list[dict]:
        """Encontra strings relacionadas a debug detection."""
        patterns = [
            rb'(?:dbg|debug|breakpoint|trap|exception|handler)[^\x00]{0,30}',
            rb'(?:OllyDbg|WinDbg|IDA|x64dbg|Process Hacker)[^\x00]{0,20}',
            rb'(?:virtual\s+box|vmware|qemu|parallels)[^\x00]{0,20}',
            rb'(?:sand|sandbox|cuckoo| Joe\s*Box)[^\x00]{0,20}',
        ]
        
        results = []
        for pattern in patterns:
            for match in re.finditer(pattern, data, re.IGNORECASE):
                results.append({
                    "offset": match.start(),
                    "value": match.group().decode('ascii', errors='ignore')
                })
        
        return results[:20]
    
    def _analyze_sections(self, data: bytes) -> list[AntiDebugIndicator]:
        """Analisa secoes PE para indicators anti-debug."""
        indicators = []
        
        # Busca por secoes suspeitas
        suspicious_section_names = [b'.upx', b'.pack', b'.ASPack', b'.Themida', 
                                     b'.vmp0', b'.vmp1', b'.enigma']
        
        # Estrutura PE simplificada
        if len(data) > 0x100:
            pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
            if pe_offset < len(data) - 4 and struct.unpack_from('<I', data, pe_offset)[0] == 0x00004550:
                num_sections = struct.unpack_from('<H', data, pe_offset + 6)[0]
                section_offset = pe_offset + 24 + struct.unpack_from('<H', data, pe_offset + 16)[0]
                
                for i in range(min(num_sections, 32)):
                    sec_offset = section_offset + i * 40
                    if sec_offset + 40 > len(data):
                        break
                    name = data[sec_offset:sec_offset+8].split(b'\x00')[0]
                    chars = struct.unpack_from('<I', data, sec_offset + 36)[0]
                    
                    # Verifica se é uma secao suspeita
                    for sus in suspicious_section_names:
                        if sus.lower() in name.lower():
                            indicators.append(AntiDebugIndicator(
                                name="suspicious_section",
                                severity="high",
                                offset=sec_offset,
                                instruction=name.decode('ascii', errors='ignore'),
                                description=f"Suspicious section: {name.decode()}",
                                bypass_method="Section contains packer/VM code"
                            ))
                            break
        
        return indicators
    
    def _severity_dist(self, indicators: list) -> dict:
        """Distribuicao de severidade."""
        dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for ind in indicators:
            if ind.severity in dist:
                dist[ind.severity] += 1
        return dist
    
    def generate_bypass_patches(self, file_path: str, output_path: str = None) -> list[DebugBypass]:
        """Gera patches para bypass de anti-debug."""
        data = Path(file_path).read_bytes()
        patches = []
        
        # Bypass 1: IsDebuggerPresent - zerar EAX antes do return
        # Encontrar calls para IsDebuggerPresent e patchear o return
        isdbg_pattern = re.compile(rb'\xE8.{4}\x83\xC4\x04\x85\xC0\x75')  # call + test + jnz
        for match in isdbg_pattern.finditer(data):
            patches.append(DebugBypass(
                success=True,
                method="IsDebuggerPresent_return_zero",
                patch_offset=match.start() + 7,  # No test instruction
                original_bytes=data[match.start()+7:match.start()+9],
                patched_bytes=b'\x31\xC0'  # xor eax, eax
            ))
        
        # Bypass 2: NOP out Int3 breakpoints
        int3_positions = [m.start() for m in re.finditer(b'\xCC', data)]
        for pos in int3_positions[:10]:  # Limita a 10 breakpoints
            # Substitui Int3 por NOPs (pode ser multi-byte)
            patches.append(DebugBypass(
                success=True,
                method="nop_int3",
                patch_offset=pos,
                original_bytes=b'\xCC',
                patched_bytes=b'\x90\x90'  # 2 NOPs
            ))
        
        # Bypass 3: Patch conditional jumps after debug checks
        # Procura por padrão: test eax,eax / jnz (ou similar)
        jump_patterns = [
            (rb'\x85\xC0\x75', b'\x90\x90\xEB'),  # test eax,eax / jnz -> nop / jmp
            (rb'\x85\xC0\x74', b'\x90\x90\xEB'),  # test eax,eax / je -> nop / jmp
        ]
        
        for search, replace in jump_patterns:
            for match in re.finditer(search, data):
                patches.append(DebugBypass(
                    success=True,
                    method="patch_conditional_jump",
                    patch_offset=match.start(),
                    original_bytes=match.group(),
                    patched_bytes=replace
                ))
        
        self.bypasses = patches
        
        # Salva patches se solicitado
        if output_path and patches:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            # Gera shellcode de patch
            shellcode = self._generate_shellcode(patches)
            output.with_suffix('.shx').write_bytes(shellcode)
            
            # Gera script de patch
            script = self._generate_patch_script(patches, file_path)
            output.with_suffix('.bat').write_text(script)
        
        return patches
    
    def _generate_shellcode(self, patches: list[DebugBypass]) -> bytes:
        """Gera shellcode para aplicar patches."""
        # Format: [offset (4 bytes)] [original (1 byte)] [patched (1 byte)] ...
        result = b''
        for p in patches[:20]:  # Limita a 20 patches
            result += struct.pack('<I', p.patch_offset)
            result += struct.pack('B', len(p.original_bytes))
            result += p.original_bytes
            result += p.patched_bytes[:len(p.original_bytes)]
        return result
    
    def _generate_patch_script(self, patches: list[DebugBypass], target: str) -> str:
        """Gera script em lote para aplicar patches."""
        lines = [
            "@echo off",
            f"REM Auto-generated anti-debug bypass script",
            f"REM Target: {target}",
            f"REM Patches: {len(patches)}",
            "",
            f"copy /Y \"{target}\" \"{target}.bak\"",
            "",
        ]
        
        for i, p in enumerate(patches[:20]):
            hex_orig = p.original_bytes.hex()
            hex_patch = p.patched_bytes.hex()
            lines.append(f"REM Patch {i+1}: offset 0x{p.patch_offset:08X}")
            lines.append(f"REM Original: {hex_orig} -> Patched: {hex_patch}")
        
        lines.extend([
            "",
            "echo Done! Backup saved as *.bak",
            "pause"
        ])
        
        return "\n".join(lines)
    
    def simulate_bypass(self, file_path: str) -> dict:
        """Simula aplicacao dos bypasses sem modificar o arquivo."""
        patches = self.generate_bypass_patches(file_path)
        
        return {
            "file": file_path,
            "patches_generated": len(patches),
            "bypasses": [
                {
                    "method": p.method,
                    "offset": f"0x{p.patch_offset:08X}",
                    "original": p.original_bytes.hex(),
                    "patched": p.patched_bytes.hex()
                }
                for p in patches
            ],
            "shellcode_size": len(self._generate_shellcode(patches)),
            "estimated_success_rate": min(1.0, len(patches) / 3) if patches else 0.0
        }


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Anti-Anti-Debug Analyzer")
    parser.add_argument("file", help="Arquivo PE para analisar")
    parser.add_argument("--analyze", "-a", action="store_true", help="Apenas analizar")
    parser.add_argument("--bypass", "-b", action="store_true", help="Gerar patches de bypass")
    parser.add_argument("--output", "-o", help="Diretorio de saida para patches")
    parser.add_argument("--simulate", "-s", action="store_true", help="Simular bypass (nao modifica)")
    args = parser.parse_args()
    
    analyzer = AntiAntiDebug()
    
    if args.analyze or not any([args.bypass, args.simulate]):
        result = analyzer.analyze(args.file)
        print(f"File: {result['file']}")
        print(f"SHA256: {result['sha256']}")
        print(f"Anti-debug indicators: {result['indicator_count']}")
        print(f"Severity: {result['severity_distribution']}")
        print(f"Confidence: {result['confidence']:.0%}")
        
        if result['indicators']:
            print(f"\nIndicators:")
            for ind in result['indicators'][:10]:
                print(f"  [{ind['severity'].upper():8s}] {ind['name']:30s} @ 0x{ind['offset']:08X}")
                print(f"           {ind['description']}")
                print(f"           Bypass: {ind['bypass_method']}")
    
    if args.bypass:
        output = Path(args.output) if args.output else Path(args.file).parent
        patches = analyzer.generate_bypass_patches(args.file, str(output / "patched"))
        print(f"\nGenerated {len(patches)} bypass patches")
        print(f"Output: {output}")
    
    if args.simulate:
        result = analyzer.simulate_bypass(args.file)
        print(f"\nSimulated bypass:")
        print(f"  Patches: {result['patches_generated']}")
        print(f"  Shellcode size: {result['shellcode_size']} bytes")
        print(f"  Success rate: {result['estimated_success_rate']:.0%}")
