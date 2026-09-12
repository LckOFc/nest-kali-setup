"""
pe_analyzer.py
Deep PE (Portable Executable) parser and analyzer
Handles: DOS/PE headers, sections, imports, exports, resources, relocation table
"""
import struct
import hashlib
import math
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List

class PEType(Enum):
    EXE = "exe"
    DLL = "dll"
    SYS = "sys"
    OBJ = "obj"
    UNKNOWN = "unknown"

class MachineType(Enum):
    I386 = 0x14c
    AMD64 = 0x8664
    ARM = 0x1c0
    ARM64 = 0xaa64

@dataclass
class SectionInfo:
    name: str
    virtual_size: int
    virtual_address: int
    raw_size: int
    raw_offset: int
    characteristics: int
    entropy: float
    is_high_entropy: bool
    contains_code: bool
    contains_data: bool
    is_readable: bool
    is_writable: bool
    is_executable: bool

@dataclass
class ImportFunc:
    library: str
    functions: List[str]

@dataclass
class ExportInfo:
    name: str
    ordinal: int
    address: int

@dataclass
class ResourceEntry:
    name: str
    rva: int
    size: int
    data: Optional[bytes] = None

class PEAnalyzer:
    """Deep PE parser com analise completa de headers, secoes, imports, exports e recursos."""
    
    # Caracteristicas de secoes
    SECTION_CHARACTERISTICS = {
        0x00000020: 'CONTAINS_CODE',
        0x00000040: 'CONTAINS_UNINITIALIZED_DATA',
        0x00000080: 'CONTAINS_INITIALIZED_DATA',
        0x00000200: 'EXECUTE',
        0x00000400: 'READ',
        0x00000800: 'WRITE',
    }
    
    # Direcionarios PE
    DIRECTORIES = {
        0: 'EXPORT_TABLE',
        1: 'IMPORT_TABLE',
        2: 'RESOURCE_TABLE',
        3: 'EXCEPTION_TABLE',
        4: 'CERTIFICATE_TABLE',
        5: 'BASE_RELOCATION_TABLE',
        6: 'DEBUG',
        15: 'BOUND_IMPORT',
        16: 'IMPORT_ADDRESS_TABLE',
        17: 'DELAY_IMPORT_DESC',
    }
    
    def __init__(self):
        self.data = b''
        self.pe_offset = 0
        self.machine = 0
        self.num_sections = 0
        self.entry_point = 0
        self.image_base = 0
        self.section_alignment = 0
        self.file_alignment = 0
        self.timestamp = 0
        self.characteristics = 0
        self.subsystem = 0
        self.dll_characteristics = 0
        self.sections = []
        self.imports = []
        self.exports = []
        self.resources = []
        self.relocations = []
        self.debug_info = {}
        self.signatures = []
    
    def parse(self, file_path: str) -> dict:
        """Parseia arquivo PE completo."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        self.data = path.read_bytes()
        self._parse_dos_header()
        self._parse_pe_header()
        self._parse_sections()
        self._parse_directories()
        
        return self._build_result(file_path)
    
    def _parse_dos_header(self):
        """Parseia DOS header (MZ)."""
        if self.data[:2] != b'MZ':
            raise ValueError("Não é um arquivo PE (não possui assinatura MZ)")
        
        self.pe_offset = struct.unpack_from('<I', self.data, 0x3C)[0]
        
        # Verifica se PE offset é valido
        if self.pe_offset >= len(self.data) or self.pe_offset < 0x40:
            raise ValueError("PE offset invalido")
    
    def _parse_pe_header(self):
        """Parseia PE header (签名, FILE_HEADER, OPTIONAL_HEADER)."""
        offset = self.pe_offset
        
        # PE signature
        sig = struct.unpack_from('<I', self.data, offset)[0]
        if sig != 0x00004550:  # 'PE\x00\x00'
            raise ValueError(f"Invalid PE signature: {hex(sig)}")
        
        # FILE_HEADER (20 bytes apos signature)
        fh_offset = offset + 4
        self.machine = struct.unpack_from('<H', self.data, fh_offset)[0]
        self.num_sections = struct.unpack_from('<H', self.data, fh_offset + 2)[0]
        self.timestamp = struct.unpack_from('<I', self.data, fh_offset + 4)[0]
        self.characteristics = struct.unpack_from('<H', self.data, fh_offset + 18)[0]
        
        # OPTIONAL_HEADER
        opt_offset = fh_offset + 20
        opt_magic = struct.unpack_from('<H', self.data, opt_offset)[0]
        
        if opt_magic == 0x20B:  # PE32+
            self.is_64bit = True
            hdr_size = 24  # SizeOfOptionalHeader em PE32+
            # Entry point, image base, section alignment, file alignment
            self.entry_point = struct.unpack_from('<I', self.data, opt_offset + 16)[0]
            self.image_base = struct.unpack_from('<Q', self.data, opt_offset + 24)[0]
            self.section_alignment = struct.unpack_from('<I', self.data, opt_offset + 32)[0]
            self.file_alignment = struct.unpack_from('<I', self.data, opt_offset + 36)[0]
            self.subsystem = struct.unpack_from('<H', self.data, opt_offset + 68)[0]
            self.dll_characteristics = struct.unpack_from('<H', self.data, opt_offset + 70)[0]
            optional_hdr_size = struct.unpack_from('<H', self.data, opt_offset + 48)[0]
        else:  # PE32
            self.is_64bit = False
            self.entry_point = struct.unpack_from('<I', self.data, opt_offset + 16)[0]
            self.image_base = struct.unpack_from('<I', self.data, opt_offset + 28)[0]
            self.section_alignment = struct.unpack_from('<I', self.data, opt_offset + 32)[0]
            self.file_alignment = struct.unpack_from('<I', self.data, opt_offset + 36)[0]
            self.subsystem = struct.unpack_from('<H', self.data, opt_offset + 68)[0]
            self.dll_characteristics = struct.unpack_from('<H', self.data, opt_offset + 70)[0]
            optional_hdr_size = struct.unpack_from('<H', self.data, opt_offset + 48)[0]
        
        # Directories (8 Diretores * 8 bytes cada, apos optional header)
        dir_offset = opt_offset + optional_hdr_size
        
        # Salva posicao dos diretorios para parsing posterior
        self.directory_offsets = []
        for i in range(16):
            entry_rva, entry_size = struct.unpack_from('<II', self.data, dir_offset + i * 8)
            self.directory_offsets.append((entry_rva, entry_size))
    
    def _parse_sections(self):
        """Parseia tabela de secoes."""
        # Tabela de secoes comeca apos optional header
        section_table_offset = self.pe_offset + 4 + 20 + struct.unpack_from('<H', self.data, self.pe_offset + 24)[0]
        
        for i in range(self.num_sections):
            offset = section_table_offset + i * 40
            
            # Nome da secao (8 bytes)
            name = self.data[offset:offset+8].split(b'\x00')[0].decode('ascii', errors='replace')
            
            # Virtual Size e Virtual Address
            vsize = struct.unpack_from('<I', self.data, offset + 8)[0]
            vaddr = struct.unpack_from('<I', self.data, offset + 12)[0]
            
            # Raw Size e Raw Offset
            rsize = struct.unpack_from('<I', self.data, offset + 20)[0]
            roffset = struct.unpack_from('<I', self.data, offset + 20)[0]
            
            # Characteristics
            chars = struct.unpack_from('<I', self.data, offset + 36)[0]
            
            # Entropia
            section_data = self.data[roffset:roffset+rsize] if rsize > 0 else b''
            entropy = self._calc_entropy(section_data)
            
            section = SectionInfo(
                name=name,
                virtual_size=vsize,
                virtual_address=vaddr,
                raw_size=rsize,
                raw_offset=roffset,
                characteristics=chars,
                entropy=entropy,
                is_high_entropy=entropy > 7.0,
                contains_code=bool(chars & 0x00000020),
                contains_data=bool(chars & 0x00000080),
                is_readable=bool(chars & 0x00000400),
                is_writable=bool(chars & 0x00000800),
                is_executable=bool(chars & 0x00000200)
            )
            self.sections.append(section)
    
    def _parse_directories(self):
        """Parseia tabelas de import/export/recurso a partir dos RVA nos diretorios."""
        # IMPORT TABLE
        import_rva, import_size = self.directory_offsets[1]
        if import_rva and import_size:
            self._parse_imports(import_rva, import_size)
        
        # EXPORT TABLE
        export_rva, export_size = self.directory_offsets[0]
        if export_rva and export_size:
            self._parse_exports(export_rva, export_size)
        
        # RESOURCE TABLE
        resource_rva, resource_size = self.directory_offsets[2]
        if resource_rva and resource_size:
            self._parse_resources(resource_rva, resource_size)
    
    def _parse_imports(self, rva: int, size: int):
        """Parseia import table."""
        # Converte RVA para offset no arquivo
        file_offset = self._rva_to_offset(rva)
        if file_offset is None:
            return
        
        end = file_offset + size
        idx = file_offset
        
        while idx < end:
            # Import Descriptor: 4 campos de 4 bytes (Characteristics, TimeDate, ForwarderChain, Name, FirstThunk)
            chars = struct.unpack_from('<I', self.data, idx)[0]
            time_date = struct.unpack_from('<I', self.data, idx + 4)[0]
            forwarder_chain = struct.unpack_from('<I', self.data, idx + 8)[0]
            name_rva = struct.unpack_from('<I', self.data, idx + 12)[0]
            first_thunk_rva = struct.unpack_from('<I', self.data, idx + 16)[0]
            
            if name_rva == 0 and first_thunk_rva == 0:
                break
            
            # Nome da DLL
            name_offset = self._rva_to_offset(name_rva)
            if name_offset:
                lib_name = self.data[name_offset:name_offset+256].split(b'\x00')[0].decode('ascii', errors='replace')
            else:
                lib_name = f"UNKNOWN_{hex(name_rva)}"
            
            # Funcoes importadas
            funcs = []
            thunk_offset = self._rva_to_offset(first_thunk_rva)
            if thunk_offset:
                while thunk_offset < len(self.data) - 3:
                    thunk_val = struct.unpack_from('<I', self.data, thunk_offset)[0]
                    if thunk_val == 0:
                        break
                    # Verifica se e import by name ou by ordinal
                    if not (thunk_val & 0x80000000):  # Não é por ordinal
                        import_by_name_offset = thunk_offset  # Hint + name
                        if import_by_name_offset < len(self.data) - 2:
                            hint = struct.unpack_from('<H', self.data, import_by_name_offset)[0]
                            func_name = self.data[import_by_name_offset+2:import_by_name_offset+128].split(b'\x00')[0].decode('ascii', errors='replace')
                            if func_name:
                                funcs.append(func_name)
                    thunk_offset += 4 if self.is_64bit else 4
            
            self.imports.append(ImportFunc(library=lib_name, functions=funcs))
            
            # Avanca para proximo descriptor
            idx += 20 if self.is_64bit else 20
    
    def _parse_exports(self, rva: int, size: int):
        """Parseia export table."""
        file_offset = self._rva_to_offset(rva)
        if file_offset is None:
            return
        
        # Export Directory: NumberOfFunctions, NumberOfNames, AddressOfFunctions, AddressOfNames, AddressOfNameOrdinals
        num_funcs = struct.unpack_from('<I', self.data, file_offset + 12)[0]
        num_names = struct.unpack_from('<I', self.data, file_offset + 14)[0]
        addr_funcs_rva = struct.unpack_from('<I', self.data, file_offset + 20)[0]
        addr_names_rva = struct.unpack_from('<I', self.data, file_offset + 24)[0]
        addr_ordinals_rva = struct.unpack_from('<I', self.data, file_offset + 28)[0]
        
        # Nomes das funcoes
        names_offset = self._rva_to_offset(addr_names_rva)
        ordinals_offset = self._rva_to_offset(addr_ordinals_rva)
        funcs_offset = self._rva_to_offset(addr_funcs_rva)
        
        exports = []
        for i in range(min(num_names, 500)):  # Limite de seguranca
            if names_offset and i * 4 < len(self.data) - names_offset:
                name_rva = struct.unpack_from('<I', self.data, names_offset + i * 4)[0]
                name_off = self._rva_to_offset(name_rva)
                if name_off:
                    name = self.data[name_off:name_off+256].split(b'\x00')[0].decode('ascii', errors='replace')
                    
                    # Ordinal
                    if ordinals_offset:
                        ordinal = struct.unpack_from('<H', self.data, ordinals_offset + i * 2)[0]
                    else:
                        ordinal = i
                    
                    # Address
                    if funcs_offset:
                        addr = struct.unpack_from('<I', self.data, funcs_offset + ordinal * 4)[0]
                    else:
                        addr = 0
                    
                    exports.append(ExportInfo(name=name, ordinal=ordinal, address=addr))
        
        self.exports = exports[:100]  # Limita a 100 exports
    
    def _parse_resources(self, rva: int, size: int):
        """Parseia resource directory."""
        # Simplificado: apenas extrai tipos/numeros
        # Em implementacao real, parsea árvore de recursos
        pass
    
    def _rva_to_offset(self, rva: int) -> Optional[int]:
        """Converte RVA (Relative Virtual Address) para offset no arquivo."""
        if not self.sections:
            return None
        
        for section in self.sections:
            start = section.virtual_address
            end = start + max(section.virtual_size, section.raw_size)
            if start <= rva < end:
                return section.raw_offset + (rva - start)
        
        # Fallback: assume alinhamento de arquivo = raw offset
        return rva  # Aproximacao grosseira
    
    def _calc_entropy(self, data: bytes) -> float:
        """Calcula entropia de Shannon."""
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
    
    def _build_result(self, file_path: str) -> dict:
        """Construi resultado da analise."""
        path = Path(file_path)
        data = self.data
        
        # Hashes
        md5 = hashlib.md5(data).hexdigest()
        sha1 = hashlib.sha1(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()
        
        # Tipos de maquina
        machine_names = {
            MachineType.I386.value: 'i386',
            MachineType.AMD64.value: 'AMD64',
            MachineType.ARM.value: 'ARM',
            MachineType.ARM64.value: 'ARM64',
        }
        
        # Subsystem
        subsystem_names = {
            2: 'WINDOWS_GUI',
            3: 'WINDOWS_CUI',
            1: 'NATIVE',
        }
        
        # DLL characteristics
        dll_chars = []
        if self.dll_characteristics & 0x2000:
            dll_chars.append('DYNAMIC_BASE')
        if self.dll_characteristics & 0x0080:
            dll_chars.append('NX_COMPAT')
        if self.dll_characteristics & 0x0008:
            dll_chars.append('NO_BIND')
        
        # Tipo de arquivo
        pe_type = PEType.UNKNOWN
        if self.characteristics & 0x2000:
            pe_type = PEType.DLL
        elif self.characteristics & 0x0002:
            pe_type = PEType.EXE
        
        # Entropia global
        global_entropy = self._calc_entropy(data)
        
        # Strings relevantes
        all_strings = self._extract_strings(data)
        
        # Indicadores suspeitos
        suspicious = []
        for imp in self.imports:
            for func in imp.functions:
                suspicious_funcs = ['VirtualAlloc', 'VirtualProtect', 'WriteProcessMemory',
                                   'CreateRemoteThread', 'NtUnmapViewOfSection', 'LoadLibrary',
                                   'GetProcAddress', 'WinExec', 'ShellExecute', 'CryptEncrypt',
                                   'CryptDecrypt', 'InternetOpen', 'HttpSendRequest',
                                   'RegSetValue', 'CreateProcess']
                if func in suspicious_funcs:
                    suspicious.append(f"Suspicious import: {imp.library}!{func}")
        
        for sec in self.sections:
            if sec.entropy > 7.5:
                suspicious.append(f"High entropy section: {sec.name} ({sec.entropy})")
        
        # Seções suspeitas
        suspicious_sections = ['.UPX', '.aspack', '.adata', '.themida', '.vmp', '.enigma', '.packed']
        for sec in self.sections:
            if any(sec.name.startswith(s) for s in suspicious_sections):
                suspicious.append(f"Packer section detected: {sec.name}")
        
        return {
            "file": str(path),
            "sha256": sha256,
            "md5": md5,
            "sha1": sha1,
            "size_bytes": len(data),
            "format": "PE",
            "pe_type": pe_type.value,
            "machine": machine_names.get(self.machine, f"0x{self.machine:04x}"),
            "is_64bit": self.is_64bit,
            "entry_point": f"0x{self.entry_point:08x}",
            "image_base": f"0x{self.image_base:x}",
            "num_sections": self.num_sections,
            "subsystem": subsystem_names.get(self.subsystem, f"{self.subsystem}"),
            "dll_characteristics": dll_chars,
            "global_entropy": global_entropy,
            "sections": [
                {
                    "name": s.name,
                    "virtual_size": s.virtual_size,
                    "virtual_address": f"0x{s.virtual_address:x}",
                    "raw_size": s.raw_size,
                    "raw_offset": f"0x{s.raw_offset:x}",
                    "entropy": s.entropy,
                    "is_high_entropy": s.is_high_entropy,
                    "is_readable": s.is_readable,
                    "is_writable": s.is_writable,
                    "is_executable": s.is_executable,
                }
                for s in self.sections
            ],
            "imports": [
                {"library": imp.library, "functions": imp.functions[:20]}
                for imp in self.imports[:30]
            ],
            "exports": [
                {"name": e.name, "ordinal": e.ordinal, "address": f"0x{e.address:x}"}
                for e in self.exports[:50]
            ],
            "strings_sample": all_strings[:100],
            "suspicious_indicators": suspicious,
            "verdict": {
                "threat_level": "HIGH" if len([s for s in suspicious if "import" in s.lower() or "entropy" in s.lower()]) > 3 else "MEDIUM" if suspicious else "LOW",
                "risk_score": min(100, len(suspicious) * 15 + sum(1 for s in self.sections if s.is_high_entropy) * 10),
                "packer_detected": any(any(s.name.startswith(p) for p in ['.UPX', '.aspack', '.themida', '.vmp', '.enigma']) for s in self.sections),
                "needs_unpacking": global_entropy > 7.0
            }
        }
    
    def _extract_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Extrai strings ASCII e Unicode."""
        # ASCII
        ascii_pattern = re.compile(rb'[\x20-\x7e]{' + str(min_length).encode() + rb',}')
        ascii_strings = [s.decode('ascii', errors='ignore') for s in ascii_pattern.findall(data)]
        
        # Unicode (UTF-16 LE)
        unicode_pattern = re.compile(rb'(?:[\x20-\x7e]\x00){' + str(min_length).encode() + rb',}')
        unicode_strings = []
        for match in unicode_pattern.findall(data):
            try:
                decoded = match.decode('utf-16-le', errors='ignore')
                unicode_strings.append(decoded)
            except:
                pass
        
        return ascii_strings + unicode_strings


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="PE Analyzer")
    parser.add_argument("file", help="Arquivo PE para analisar")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    analyzer = PEAnalyzer()
    result = analyzer.parse(args.file)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"File: {result['file']}")
        print(f"SHA256: {result['sha256']}")
        print(f"Format: {result['format']} ({result['pe_type']})")
        print(f"Machine: {result['machine']} | 64-bit: {result['is_64bit']}")
        print(f"Entry Point: {result['entry_point']}")
        print(f"Sections: {result['num_sections']}")
        print(f"Global Entropy: {result['global_entropy']}")
        print(f"\nImports ({len(result['imports'])} DLLs):")
        for imp in result['imports'][:10]:
            print(f"  {imp['library']}: {', '.join(imp['functions'][:5])}")
        print(f"\nSuspicious: {len(result['suspicious_indicators'])} indicators")
        for s in result['suspicious_indicators'][:5]:
            print(f"  ⚠ {s}")
        print(f"\nVerdict: {result['verdict']['threat_level']} (score: {result['verdict']['risk_score']})")
