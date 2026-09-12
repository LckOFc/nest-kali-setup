"""
auto_unpacker.py
Pipeline de desempacotamento automatico de binarios PE
"""
import asyncio
import hashlib
import math
import os
import struct
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

class PackerType(Enum):
    UPX = "upx"
    ASPACK = "aspack"
    THEMIDA = "themida"
    VMPROTECT = "vmprotect"
    ENIGMA = "enigma"
    Packed_Unknown = "unknown_packed"
    Native = "native"

@dataclass
class SectionInfo:
    name: str
    virtual_size: int
    raw_size: int
    entropy: float
    is_high_entropy: bool

@dataclass
class UnpackResult:
    file_path: str
    sha256: str
    size_bytes: int
    packer_detected: str
    packer_confidence: float
    overall_entropy: float
    sections: list[SectionInfo]
    suspicious_indicators: list[str]
    recommended_strategy: str
    unpack_success: bool
    unpacked_path: Optional[str] = None
    oep_address: Optional[str] = None

class EntropyCalculator:
    """Calcula entropia de Shannon de chunks de dados."""
    
    @staticmethod
    def calculate(data: bytes) -> float:
        if not data:
            return 0.0
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
        return round(entropy, 4)

class PEParser:
    """Parser basico de headers PE para extracao de secoes."""
    
    @staticmethod
    def parse_sections(data: bytes) -> list[dict]:
        """Extrai informacoes das secoes PE."""
        sections = []
        try:
            # Offset da tabela de secoes
            e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
            
            # Numero de secoes (offset 6 apos NT Headers)
            num_sections = struct.unpack_from('<H', data, e_lfanew + 6)[0]
            
            # Tamanho do Optional Header
            optional_header_size = struct.unpack_from('<H', data, e_lfanew + 20)[0]
            
            # Offset da tabela de secoes
            section_table_offset = e_lfanew + 24 + optional_header_size
            
            for i in range(num_sections):
                offset = section_table_offset + (i * 40)
                
                # Nome da secao (8 bytes)
                name_bytes = data[offset:offset+8]
                name = name_bytes.split(b'\x00')[0].decode('ascii', errors='ignore')
                
                # Virtual Size
                virtual_size = struct.unpack_from('<I', data, offset + 8)[0]
                
                # Virtual Address
                virtual_addr = struct.unpack_from('<I', data, offset + 12)[0]
                
                # Raw Size
                raw_size = struct.unpack_from('<I', data, offset + 20)[0]
                
                # Raw Offset
                raw_offset = struct.unpack_from('<I', data, offset + 20)[0]
                
                # Characteristics
                characteristics = struct.unpack_from('<I', data, offset + 36)[0]
                
                sections.append({
                    'name': name or f'.sec{i}',
                    'virtual_size': virtual_size,
                    'virtual_address': virtual_addr,
                    'raw_size': raw_size,
                    'raw_offset': raw_offset,
                    'characteristics': characteristics
                })
        except Exception as e:
            sections.append({'error': str(e)})
        return sections

class AutoUnpacker:
    """Pipeline completo de deteccao e desempacotamento."""
    
    KNOWN_PACKER_SIGNATURES = {
        PackerType.UPX: [b'UPX', b'UPX0', b'UPX1', b'UPX2'],
        PackerType.ASPACK: [b'!ThisProgramCannot', b'aspac'],
        PackerType.THEMIDA: [b'Themida', b'.themida', b'.themida.'],
        PackerType.VMPROTECT: [b'VMProtect', b'.vmp0', b'.vmp1', b'.vmp'],
        PackerType.ENIGMA: [b'Enigma', b'.enigma0', b'.enigma1'],
    }
    
    HIGH_ENTROPY_THRESHOLD = 7.0
    SUSPICIOUS_SECTION_ENTROPY = 6.5
    
    def __init__(self, upx_path: str = "upx"):
        self.upx_path = upx_path
        self.entropy_calc = EntropyCalculator()
        self.pe_parser = PEParser()
    
    async def analyze(self, file_path: str, detailed: bool = False) -> UnpackResult:
        """Analise completa de um arquivo PE."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        data = path.read_bytes()
        
        # Hashes
        sha256 = hashlib.sha256(data).hexdigest()
        
        # Entropia global
        overall_entropy = self.entropy_calc.calculate(data)
        
        # Detecção de packer
        packer, confidence = self._detect_packer(data)
        
        # Analisis de secoes
        sections_raw = self.pe_parser.parse_sections(data)
        sections = []
        for sec in sections_raw:
            if 'error' in sec:
                continue
            entropy = self.entropy_calc.calculate(data[sec['raw_offset']:sec['raw_offset']+sec['raw_size']])
            sections.append(SectionInfo(
                name=sec['name'],
                virtual_size=sec['virtual_size'],
                raw_size=sec['raw_size'],
                entropy=entropy,
                is_high_entropy=entropy > self.SUSPICIOUS_SECTION_ENTROPY
            ))
        
        # Indicadores suspeitos
        indicators = self._find_indicators(data, sections)
        
        # Estratégia recomendada
        strategy = self._recommend_strategy(packer, overall_entropy, sections)
        
        return UnpackResult(
            file_path=str(path),
            sha256=sha256,
            size_bytes=len(data),
            packer_detected=packer.value,
            packer_confidence=confidence,
            overall_entropy=overall_entropy,
            sections=sections,
            suspicious_indicators=indicators,
            recommended_strategy=strategy,
            unpack_success=False
        )
    
    async def try_unpack(self, file_path: str, output_dir: str = "./unpacked") -> UnpackResult:
        """Tenta desempacotar automaticamente."""
        # Analisa primeiro
        result = await self.analyze(file_path)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if result.packer_detected == PackerType.UPX.value:
            # Tenta UPX
            try:
                output_file = output_path / f"{Path(file_path).name}.unpacked.exe"
                proc = await asyncio.create_subprocess_exec(
                    self.upx_path, "-d", "-o", str(output_file), file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(proc.communicate(), timeout=60)
                
                if output_file.exists():
                    result.unpack_success = True
                    result.unpacked_path = str(output_file)
                    # Recalcula entropia apos unpack
                    new_data = output_file.read_bytes()
                    result.overall_entropy = self.entropy_calc.calculate(new_data)
            except Exception as e:
                result.suspicious_indicators.append(f"UNPACK_ERROR: {str(e)}")
        
        elif result.packer_detected in (PackerType.THEMIDA.value, PackerType.VMPROTECT.value):
            result.suspicious_indicators.append("MANUAL_OEP_REQUIRED")
            result.suspicious_indicators.append("USE_X64DBG_PLUSscyLLA")
        
        return result
    
    def _detect_packer(self, data: bytes) -> tuple[PackerType, float]:
        """Detecta packer por assinaturas."""
        header_check = data[:0x10000]
        
        for packer_type, signatures in self.KNOWN_PACKER_SIGNATURES.items():
            matches = sum(1 for sig in signatures if sig in header_check)
            if matches > 0:
                confidence = min(1.0, matches * 0.3)
                return packer_type, confidence
        
        # Heuristica por entropia
        if self.entropy_calc.calculate(data) > self.HIGH_ENTROPY_THRESHOLD:
            return PackerType.Packed_Unknown, 0.7
        
        return PackerType.Native, 1.0
    
    def _find_indicators(self, data: bytes, sections: list[SectionInfo]) -> list[str]:
        """Busca indicadores suspeitos."""
        indicators = []
        
        # Entropia alta global
        if self.entropy_calc.calculate(data) > self.HIGH_ENTROPY_THRESHOLD:
            indicators.append("HIGH_ENTROPY_GLOBAL")
        
        # Seções com nomes suspeitos
        suspicious_names = ['.UPX', '.aspack', '.adata', '.themida', '.vmp', '.enigma']
        for sec in sections:
            if any(sec.name.startswith(sn) for sn in suspicious_names):
                indicators.append(f"SUSPICIOUS_SECTION:{sec.name}")
            if sec.entropy > 7.5:
                indicators.append(f"HIGH_ENTROPY_SECTION:{sec.name}={sec.entropy}")
        
        # Zero-fill patterns (comum em packers)
        if b'\x00' * 100 in data[:0x10000]:
            indicators.append("ZERO_FILL_PATTERN")
        
        return indicators
    
    def _recommend_strategy(self, packer: PackerType, entropy: float, sections: list[SectionInfo]) -> str:
        """Recomenda estratégia baseada na análise."""
        if packer == PackerType.Native:
            return "No packing detected. Native executable."
        
        if packer == PackerType.UPX:
            return "upx -d input.exe -o output.exe"
        
        if packer == PackerType.ASPACK:
            return "Use x64dbg to find OEP, then Scylla for dump"
        
        if packer in (PackerType.THEMIDA, PackerType.VMPROTECT):
            return "Complex packer detected. Manual OEP finding required via x64dbg + Scylla."
        
        if packer == PackerType.Packed_Unknown:
            if entropy > 7.5:
                return "High entropy suggests packing/encryption. Try: 1) x64dbg OEP finding 2) Scylla dump 3) FLOSS strings extraction"
            return "Possibly packed. Analyze sections and try manual unpacking."
        
        return "Unknown packer. Manual analysis recommended."
    
    def calculate_entropy(self, data: bytes) -> float:
        """Calcula entropia de Shannon."""
        return self.entropy_calc.calculate(data)

# CLI interface
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Auto-Unpacker PE Pipeline")
    parser.add_argument("file", help="Arquivo PE para analisar")
    parser.add_argument("--detailed", action="store_true", help="Output detalhado")
    parser.add_argument("--unpack", action="store_true", help="Tentar unpack automatico")
    parser.add_argument("--output", "-o", help="Salvar resultado em arquivo JSON")
    parser.add_argument("--output-dir", default="./unpacked", help="Diretorio de output")
    parser.add_argument("--entropy-only", action="store_true", help="Apenas calcular entropia")
    args = parser.parse_args()
    
    async def main():
        unpacker = AutoUnpacker()
        
        if args.entropy_only:
            data = Path(args.file).read_bytes()
            print(f"Entropy: {unpacker.calculate_entropy(data):.4f}")
            return
        
        if args.unpack:
            result = await unpacker.try_unpack(args.file, args.output_dir)
        else:
            result = await unpacker.analyze(args.file)
        
        # Output
        output = {
            "file": result.file_path,
            "sha256": result.sha256,
            "size_bytes": result.size_bytes,
            "packer": result.packer_detected,
            "confidence": result.packer_confidence,
            "entropy": result.overall_entropy,
            "sections": [
                {"name": s.name, "virtual_size": s.virtual_size, "raw_size": s.raw_size, 
                 "entropy": s.entropy, "high_entropy": s.is_high_entropy}
                for s in result.sections
            ],
            "indicators": result.suspicious_indicators,
            "strategy": result.recommended_strategy,
            "unpack_success": result.unpack_success,
            "unpacked_path": result.unpacked_path
        }
        
        print(json.dumps(output, indent=2))
        
        if args.output:
            Path(args.output).write_text(json.dumps(output, indent=2))
            print(f"\nResultado salvo em: {args.output}")
    
    asyncio.run(main())
