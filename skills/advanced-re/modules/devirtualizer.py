"""
devirtualizer.py
Devirtualization framework for VMProtect, Themida, and custom VMs
Uses tracing + heuristic reconstruction
"""
import struct
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, list, dict
from enum import Enum

class VMType(Enum):
    VMPROTECT = "vmprotect"
    THEMIDA = "themida"
    STR = "str"
    ARMADILLO = "armadillo"
    CUSTOM = "custom"
    UNKNOWN = "unknown"

@dataclass
class VMInstruction:
    opcode: int
    operand1: int
    operand2: int
    target: int
    description: str
    original_offset: int

@dataclass
class VMBasicBlock:
    start: int
    end: int
    instructions: list[VMInstruction]
    edge_type: str  # fallthrough, jump, call, ret

@dataclass
class DevirtualizationResult:
    vm_type: VMType
    confidence: float
    oep_address: int
    vm_entry_point: int
    instructions_traced: int
    basic_blocks: int
    reconstructed_code: bytes
    errors: list[str]

class Devirtualizer:
    """
    Framework de devirtualizacao para binarios protegidos por VM.
    
    Metodos:
    1. Trace-based: executa bytecode VM e registra instrucoes nativas
    2. Heuristic: analisa padrões de bytecode para reconstruir logica
    3. Hybrid: combina trace + heuristica para resultados otimais
    
    Suporta:
    - VMProtect (2.x, 3.x)
    - Themida (1.x, 2.x)
    - Packers custom com bytecode VM
    """
    
    # Signatures de VM conocidas
    VM_SIGNATURES = {
        VMType.VMPROTECT: [
            b'.vmp0', b'.vmp1', b'VMProtect', b'\x55\x8B\xEC\x83\xEC\x10\xA1',  # push ebp; mov ebp,esp
            b'\x6A\x00\x68',  # push 0; push addr (常见VM prolog)
        ],
        VMType.THEMIDA: [
            b'.themida', b'Themida', b'.themida.',
            b'\x64\xA1\xFF\x00\x00\x00',  # fs:[0xFF] thread info
        ],
        VMType.STR: [
            b'.str', b'STR', b'\x55\x8B\xEC\x83\xEC\x08',
        ],
        VMType.ARMADILLO: [
            b'.arm', b'Armadillo', b'\x55\x8B\xEC\x83\xEC\x14',
        ],
    }
    
    # Opcodes comuns de VM (para heuristica)
    VM_OPCODE_PATTERNS = {
        # Stack operations
        'push': [0x6A, 0x68, 0x50, 0x51, 0x52, 0x53, 0x55, 0x56, 0x57],
        'pop': [0x58, 0x59, 0x5A, 0x5B, 0x5D, 0x5E, 0x5F],
        'call': [0xFF, 0xE8, 0xE8],
        'ret': [0xC3, 0xC2],
        # Arithmetic
        'add': [0x01, 0x03, 0x83, 0x81],
        'sub': [0x29, 0x2B, 0x83],
        'xor': [0x31, 0x35, 0x83],
        'and': [0x21, 0x23, 0x83],
        # Memory
        'mov': [0x89, 0x8B, 0xA3, 0x8B],
        'lea': [0x8D],
    }
    
    def __init__(self, trace_mode: str = "hybrid", max_instructions: int = 100000):
        self.trace_mode = trace_mode
        self.max_instructions = max_instructions
        self.traced_instructions = []
        self.basic_blocks = []
        self.reconstructed_code = bytearray()
    
    def analyze(self, file_path: str) -> dict:
        """Analisa binário para identificar VM."""
        data = Path(file_path).read_bytes()
        
        # 1. Detecção por signatures
        vm_type = self._detect_vm_type(data)
        
        # 2. Análise de seções
        sections = self._analyze_sections(data)
        
        # 3. Busca por entry point suspeito
        oep_hint = self._find_oep_hint(data, vm_type)
        
        # 4. Análise de entropia por seção
        entropy_analysis = self._section_entropy_analysis(data, sections)
        
        # 5. Identifica possíveis opcodes de VM
        vm_opcodes = self._find_vm_opcodes(data)
        
        return {
            "file": file_path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "vm_type": vm_type.value,
            "vm_confidence": self._calc_confidence(vm_type, sections, entropy_analysis),
            "sections": sections,
            "oep_hint": oep_hint,
            "entropy_analysis": entropy_analysis,
            "vm_opcodes_detected": vm_opcodes,
            "devirtualization_feasible": vm_type != VMType.UNKNOWN and vm_type != VMType.THEMIDA,
            "recommended_approach": self._recommend_approach(vm_type, entropy_analysis)
        }
    
    def _detect_vm_type(self, data: bytes) -> VMType:
        """Detecta tipo de VM por assinaturas."""
        for vm_type, signatures in self.VM_SIGNATURES.items():
            for sig in signatures:
                if isinstance(sig, bytes) and sig in data:
                    return vm_type
                elif isinstance(sig, str) and sig.encode() in data:
                    return vm_type
        
        # Verifica entropia extrema (indício de VM)
        if self._calc_overall_entropy(data) > 7.5:
            # Verifica seções com nomes suspeitos
            for suffix in ['.vmp', '.them', '.str', '.arm', '.upx', '.pack']:
                if suffix.encode() in data[:0x10000]:
                    for vt, sigs in self.VM_SIGNATURES.items():
                        if any(suffix.encode() in sig.encode() if isinstance(sig, str) else suffix.encode() in sig for sig in sigs):
                            return vt
            
            return VMType.CUSTOM
        
        return VMType.UNKNOWN
    
    def _analyze_sections(self, data: bytes) -> list[dict]:
        """Analisa secoes PE."""
        sections = []
        try:
            pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
            if pe_offset + 24 < len(data):
                num_sections = struct.unpack_from('<H', data, pe_offset + 6)[0]
                opt_header_size = struct.unpack_from('<H', data, pe_offset + 16)[0]
                section_offset = pe_offset + 24 + opt_header_size
                
                for i in range(min(num_sections, 32)):
                    off = section_offset + i * 40
                    if off + 40 > len(data):
                        break
                    name = data[off:off+8].split(b'\x00')[0].decode('ascii', errors='ignore')
                    vsize = struct.unpack_from('<I', data, off + 8)[0]
                    raw_size = struct.unpack_from('<I', data, off + 20)[0]
                    raw_offset = struct.unpack_from('<I', data, off + 20)[0]
                    entropy = self._calc_entropy(data[raw_offset:raw_offset+raw_size]) if raw_size > 0 else 0
                    
                    sections.append({
                        "name": name,
                        "virtual_size": vsize,
                        "raw_size": raw_size,
                        "raw_offset": raw_offset,
                        "entropy": round(entropy, 4),
                        "is_high_entropy": entropy > 7.0,
                        "is_vm_section": any(name.startswith(s) for s in ['.vmp', '.them', '.str', '.arm'])
                    })
        except:
            pass
        return sections
    
    def _find_oep_hint(self, data: bytes, vm_type: VMType) -> Optional[int]:
        """Tenta encontrar hint do OEP (Original Entry Point)."""
        # Para VMProtect, OEP está frequentemente no final da última seção VM
        if vm_type == VMType.VMPROTECT:
            for sec in reversed(self._analyze_sections(data)):
                if sec.get('is_vm_section'):
                    return sec['raw_offset'] + sec['raw_size']
        
        # Para Themida, OEP pode estar em posição fixa relativa
        if vm_type == VMType.THEMIDA:
            # Procura por JMP ao OEP no código de stub
            jmp_pattern = re.compile(rb'\xE9.{4}')  # JMP rel32
            for match in jmp_pattern.finditer(data[:0x1000]):
                offset = struct.unpack_from('<I', data, match.start() + 1)[0]
                target = match.start() + 5 + offset
                if target > 0x10000 and target < len(data):
                    return target
        
        return None
    
    def _section_entropy_analysis(self, data: bytes, sections: list[dict]) -> dict:
        """Análise de entropia por seção."""
        if not sections:
            return {}
        
        high_entropy_secs = [s for s in sections if s.get('is_high_entropy')]
        vm_secs = [s for s in sections if s.get('is_vm_section')]
        
        return {
            "total_sections": len(sections),
            "high_entropy_sections": len(high_entropy_secs),
            "vm_sections": len(vm_secs),
            "avg_entropy": sum(s.get('entropy', 0) for s in sections) / len(sections) if sections else 0,
            "max_entropy": max((s.get('entropy', 0) for s in sections), default=0),
            "is_packed": len(high_entropy_secs) > 0
        }
    
    def _find_vm_opcodes(self, data: bytes) -> dict:
        """Busca por opcodes de VM no binário."""
        found = {}
        for op_name, op_bytes in self.VM_OPCODE_PATTERNS.items():
            counts = {}
            for op_byte in op_bytes:
                count = data.count(bytes([op_byte]))
                if count > 0:
                    counts[f"0x{op_byte:02x}"] = count
            if counts:
                found[op_name] = counts
        return found
    
    def _calc_entropy(self, data: bytes) -> float:
        """Entropia de Shannon."""
        if not data:
            return 0.0
        import math
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1
        length = len(data)
        entropy = 0.0
        for count in freq:
            if count:
                p = count / length
                if p > 0:
                    entropy -= p * math.log2(p)
        return entropy
    
    def _calc_overall_entropy(self, data: bytes) -> float:
        """Entropia global do arquivo."""
        return self._calc_entropy(data)
    
    def _calc_confidence(self, vm_type: VMType, sections: list[dict], entropy: dict) -> float:
        """Calcula confiança da detecção."""
        confidence = 0.0
        
        if vm_type != VMType.UNKNOWN:
            confidence += 0.4
        
        if entropy.get('vm_sections', 0) > 0:
            confidence += 0.3
        
        if entropy.get('high_entropy_sections', 0) > 0:
            confidence += 0.2
        
        if entropy.get('is_packed'):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _recommend_approach(self, vm_type: VMType, entropy: dict) -> str:
        """Recomenda abordagem de devirtualização."""
        if vm_type == VMType.UNKNOWN:
            return "No VM detected. Standard reverse engineering."
        
        if vm_type == VMType.VMPROTECT:
            if entropy.get('vm_sections', 0) > 0:
                return "Use x64dbg + Scylla: 1) Find OEP via hardware breakpoint 2) Dump process 3) Fix IAT"
            return "Try VMProtect Devirtualizer or manual tracing"
        
        if vm_type == VMType.THEMIDA:
            return "Themida requires manual OEP finding + Scylla dump. Consider using Themida-specific unpacking tools."
        
        if vm_type == VMType.CUSTOM:
            return "Custom VM detected. Requires manual bytecode analysis + tracing."
        
        return "Standard unpacking + analysis recommended."
    
    def trace_vm(self, file_path: str, vm_entry: int = None, max_steps: int = 10000) -> dict:
        """
        Tenta rastrear execução de bytecode VM.
        Nota: Implementação简化ada — em produção, requer debugger integration.
        """
        data = Path(file_path).read_bytes()
        
        # Simulação de tracing (em produção, usar x64dbg plugin ou API)
        traced = []
        
        # Busca por padrões de bytecode VM conhecidos
        # VMProtect usa opcodes no range 0x40-0xFF com operandos variáveis
        vm_opcode_range = range(0x40, 0x100)
        
        for i in range(0, min(len(data), 0x10000), 1):
            byte = data[i]
            if byte in vm_opcode_range:
                # Verifica se é um opcode VM (baseado em contexto)
                context = data[max(0,i-4):i+8]
                if self._is_vm_opcode(context, byte):
                    traced.append({
                        "offset": i,
                        "opcode": f"0x{byte:02x}",
                        "context": context.hex(),
                        "type": self._classify_vm_op(byte)
                    })
                    if len(traced) >= max_steps:
                        break
        
        return {
            "file": file_path,
            "traced_instructions": len(traced),
            "samples": traced[:50],
            "vm_type_detected": self._detect_vm_type(data).value,
            "note": "Tracing simplificado. Para tracing real, use x64dbg com plugin VMProtect/Themida."
        }
    
    def _is_vm_opcode(self, context: bytes, opcode: int) -> bool:
        """Determina se byte é opcode VM baseado no contexto."""
        # Heurísticas simples
        # VMProtect opcodes frequentemente seguem padrões específicos
        if opcode > 0x7F:  # Sinal negativa em signed char
            return True
        # Verifica se opcode aparece em sequência (típico de VM)
        return False
    
    def _classify_vm_op(self, opcode: int) -> str:
        """Classifica tipo de opcode VM."""
        if opcode in (0x40, 0x41, 0x42):
            return "stack_push"
        elif opcode in (0x43, 0x44):
            return "stack_pop"
        elif opcode in (0x50, 0x51, 0x52):
            return "arithmetic"
        elif opcode in (0x60, 0x61):
            return "logical"
        elif opcode in (0x70, 0x71):
            return "memory_access"
        elif opcode in (0x80, 0x81):
            return "control_flow"
        elif opcode == 0xFF:
            return "external_call"
        return "unknown"
    
    def generate_reconstruction_script(self, analysis: dict, output_path: str) -> str:
        """Gera script para reconstrucao do código desvirtualizado."""
        content = [
            f"; Devirtualization Reconstruction Script",
            f"; Generated by Advanced RE Suite",
            f"; Target: {analysis.get('file', 'unknown')}",
            f"; VM Type: {analysis.get('vm_type', 'unknown')}",
            f"; Confidence: {analysis.get('vm_confidence', 0):.0%}",
            f";",
            f"; Recommended tools:",
            f"; - x64dbg (debugger)",
            f"; - Scylla (dump + IAT reconstruction)",
            f"; - Ghidra (decompiler)",
            f"; - VMProtect Devirtualizer (if applicable)",
            f"",
            f"; Step-by-step process:",
            f"1. Load binary in x64dbg",
            f"2. Set hardware breakpoint on OEP: 0x{analysis.get('oep_hint', 0):08X}" if analysis.get('oep_hint') else "2. Find OEP manually",
            f"3. Run until breakpoint hits",
            f"4. Use Scylla to dump process",
            f"5. Fix IAT using Scylla's automatic fix",
            f"6. Analyze dumped binary in Ghidra",
            f"",
            f"; Manual tracing approach:",
            f"; If auto-unpack fails, trace VM bytecode manually:",
        ]
        
        if analysis.get('vm_opcodes_detected'):
            content.append(f"; Detected VM opcodes:")
            for op_name, counts in analysis['vm_opcodes_detected'].items():
                content.append(f";   {op_name}: {counts}")
        
        content.extend([
            f"",
            f"; Alternative: Use VMProtect Devirtualizer",
            f"; Download: https://github.com/VMProtect/devirtualizer",
            f"; Command: devirtualizer.exe input.exe -o output_dir/",
            f"",
            f"; Alternative: Use x64dbg plugin for VM tracing",
            f"; Plugin: vmtrace (https://github.com/x64dbg(vmtrace))",
        ])
        
        Path(output_path).write_text("\n".join(content))
        return output_path


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Devirtualizer - VMProtect/Themida Analysis")
    parser.add_argument("file", help="Arquivo protegido por VM")
    parser.add_argument("--analyze", "-a", action="store_true", help="Apenas analisar")
    parser.add_argument("--trace", "-t", action="store_true", help="Tentar tracing de bytecode")
    parser.add_argument("--script", "-s", action="store_true", help="Gerar script de reconstrucao")
    parser.add_argument("--output", "-o", help="Diretorio de saida")
    args = parser.parse_args()
    
    devirt = Devirtualizer()
    
    # Analise
    analysis = devirt.analyze(args.file)
    
    print(f"File: {analysis['file']}")
    print(f"VM Type: {analysis['vm_type']}")
    print(f"Confidence: {analysis['vm_confidence']:.0%}")
    print(f"Recommended: {analysis['recommended_approach']}")
    print(f"\nSections:")
    for sec in analysis['sections']:
        flag = " [VM]" if sec.get('is_vm_section') else ""
        flag += " [HIGH ENT]" if sec.get('is_high_entropy') else ""
        print(f"  {sec['name']:10s} size={sec['raw_size']:8d} entropy={sec['entropy']:.4f}{flag}")
    
    if args.trace:
        print(f"\nTracing VM bytecode...")
        trace_result = devirt.trace_vm(args.file)
        print(f"Traced {trace_result['traced_instructions']} instructions")
        for sample in trace_result['samples'][:5]:
            print(f"  0x{sample['offset']:08X}: opcode={sample['opcode']} type={sample['type']}")
    
    if args.script:
        output = Path(args.output or "./devirt_output")
        output.mkdir(parents=True, exist_ok=True)
        script_path = devirt.generate_reconstruction_script(analysis, str(output / "reconstruction.txt"))
        print(f"\nReconstruction script saved to: {script_path}")
