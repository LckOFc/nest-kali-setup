"""
dotnet_decompiler.py
.NET/CLR decompiler - extrai CIL, recursos, assemblies e manifestos
"""
import struct
import hashlib
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

@dataclass
class AssemblyInfo:
    name: str
    version: str
    culture: str
    public_key_token: str
    processor_architecture: str

@dataclass
class ResourceType:
    name: str
    language: str
    size: int
    data: bytes

class DotNetDecompiler:
    """
    Decompilador .NET/CLR que extrai:
    - CIL (Common Intermediate Language) instructions
    - Recursos embutidos
    - Assembly manifest
    - Tip tabelas
    """
    
    # Magic CLR
    CLR_MAGIC = 0xBEEFCACE
    
    # CLR header offsets
    CLR_HEADER_OFFSET = 0x98  # Para PE32+
    
    # CIL opcodes (versoes mais comuns)
    CIL_OPCODES = {
        0x00: 'nop', 0x01: 'break', 0x02: 'ldarg.0', 0x03: 'ldarg.1',
        0x04: 'ldarg.2', 0x05: 'ldarg.3', 0x06: 'ldloc.0', 0x07: 'ldloc.1',
        0x08: 'ldloc.2', 0x09: 'ldloc.3', 0x0A: 'stloc.0', 0x0B: 'stloc.1',
        0x0C: 'stloc.2', 0x0D: 'stloc.3', 0x0E: 'ldarg.0', 0x0F: 'ldarg.1',
        0x1E: 'ldnull', 0x1F: 'ldc.i4.m1', 0x20: 'ldc.i4.0', 0x21: 'ldc.i4.1',
        0x22: 'ldc.i4.2', 0x23: 'ldc.i4.3', 0x24: 'ldc.i4.4', 0x25: 'ldc.i4.5',
        0x26: 'ldc.i4.6', 0x27: 'ldc.i4.7', 0x28: 'ldc.i4.8', 0x29: 'ldc.i4.s',
        0x2A: 'ldc.i4.u', 0x2B: 'ldc.i8', 0x2C: 'ldc.r4', 0x2D: 'ldc.r8',
        0x0B: 'stloc.1', 0x0C: 'stloc.2', 0x0D: 'stloc.3',
        # Mais opcodes...
        0x7A: 'call', 0x7B: 'calli', 0x7C: 'ret', 0x7D: 'cpobj',
        0x7E: 'ldobj', 0x7F: 'ldarga', 0x80: 'ldarga', 0x81: 'starg',
        0x82: 'ldind.i1', 0x83: 'ldind.u1', 0x84: 'ldind.i2', 0x85: 'ldind.u2',
        0x86: 'ldind.i4', 0x87: 'ldind.u4', 0x88: 'ldind.i8', 0x89: 'ldind.i8',
        0x8A: 'ldind.r4', 0x8B: 'ldind.r8', 0x8C: 'ldind.ptr',
        0x8D: 'stind.ref', 0x8E: 'stind.i1', 0x8F: 'stind.i2',
        0x90: 'stind.i4', 0x91: 'stind.i8', 0x92: 'stind.r4', 0x93: 'stind.r8',
        0x94: 'add', 0x95: 'sub', 0x96: 'mul', 0x97: 'div', 0x98: 'divun',
        0x99: 'rem', 0x9A: 'remun', 0x9B: 'and', 0x9C: 'or', 0x9D: 'xor',
        0x9E: 'shl', 0x9F: 'shr', 0xA0: 'shr_un', 0xA1: 'callvirt',
        0xA2: 'cpblk', 0xA3: 'initblk', 0xA4: 'icall',
        0xA8: 'throw', 0xAA: 'ldftn', 0xAB: 'ldvirtftn',
        0xB2: 'isinst', 0xB3: 'conv.u1', 0xB4: 'conv.u2', 0xB5: 'conv.u4',
        0xB6: 'conv.u8', 0xB7: 'conv.r4', 0xB8: 'conv.r8', 0xB9: 'conv.u',
        0xBA: 'Conv.ovf.u1', 0xBB: 'Conv.ovf.u2', 0xBC: 'Conv.ovf.u4',
        0xBD: 'Conv.ovf.u8', 0xBE: 'Conv.ovf.u', 0xBF: 'Conv.ovf.u1.un',
        0xC0: 'Conv.ovf.u2.un', 0xC1: 'Conv.ovf.u4.un', 0xC2: 'Conv.ovf.u8.un',
        0xC3: 'Conv.ovf.u.un', 0xC4: 'Conv.ovf.i1', 0xC5: 'Conv.ovf.i2',
        0xC6: 'Conv.ovf.i4', 0xC7: 'Conv.ovf.i8', 0xC8: 'Conv.ovf.i',
        0xC9: 'Conv.ovf.i1.un', 0xCA: 'Conv.ovf.i2.un', 0xCB: 'Conv.ovf.i4.un',
        0xCC: 'Conv.ovf.i8.un', 0xCD: 'Conv.ovf.i.un',
        0xCE: 'arglist', 0xCF: 'ceq', 0xD0: 'cgt', 0xD1: 'cgt_un',
        0xD2: 'clt', 0xD3: 'clt_un', 0xD4: 'ldfld', 0xD5: 'ldflda',
        0xD6: 'stfld', 0xD7: 'ldsfld', 0xD8: 'ldsflda', 0xD9: 'stsfld',
        0xDA: 'stobj', 0xDB: 'conv.o', 0xDC: 'conv.ovf.o',
        0xDD: 'conv.ovf.o.un', 0xDE: 'conv.ovf.u.o', 0xDF: 'conv.ovf.u.o.un',
        0xE0: 'mkrefany', 0xE1: 'ldrefany', 0xE2: 'strefany',
        0xE3: 'ldtoken', 0xE4: 'ldvirtftn', 0xE5: 'newobj',
        0xE6: 'ldstr', 0xE7: 'localloc', 0xE8: 'switch',
        0xE9: 'ldind.i', 0xEA: 'ldind.u', 0xEB: 'ldind.r4',
        0xEC: 'ldind.r8', 0xED: 'ldind.i1', 0xEE: 'ldind.u1',
        0xEF: 'ldind.i2', 0xF0: 'ldind.u2', 0xF1: 'ldind.i4', 0xF2: 'ldind.u4',
        0xF3: 'ldind.i8', 0xF4: 'ldind.u8', 0xF5: 'ldind.r4', 0xF6: 'ldind.r8',
        0xF7: 'stind.i', 0xF8: 'stind.u', 0xF9: 'stind.r4',
        0xFA: 'stind.r8', 0xFB: 'stind.i1', 0xFC: 'stind.u1',
        0xFD: 'stind.i2', 0xFE: 'stind.u2', 0xFF: 'stind.i4',
    }
    
    def __init__(self):
        self.data = b''
        self.assemblies = []
        self.resources = []
        self.types = []
        self.methods = []
    
    def analyze(self, file_path: str) -> dict:
        """Analisa arquivo .NET completo."""
        path = Path(file_path)
        self.data = path.read_bytes()
        
        # Verifica se é .NET
        if not self._is_dotnet():
            return {"error": "Não é um arquivo .NET/CLR", "type": "native_pe"}
        
        # Extrai informacoes
        result = {
            "file": str(path),
            "sha256": hashlib.sha256(self.data).hexdigest(),
            "size_bytes": len(self.data),
            "type": ".NET",
            "is_64bit": self._check_64bit(),
            "target_framework": self._detect_framework(),
            "assemblies": self._extract_assemblies(),
            "resources": self._extract_resources(),
            "strings": self._extract_strings(),
            "tlv_table": self._parse_type_library(),
        }
        
        return result
    
    def _is_dotnet(self) -> bool:
        """Verifica se arquivo tem CLR header."""
        # Busca assinatura CLR (CorExeMain ou CorDllMain)
        patterns = [b'CorExeMain', b'CorDllMain', b'.cor20', b'.cor30']
        for pattern in patterns:
            if pattern in self.data[:0x1000]:
                return True
        
        # Verifica se tem CLR header no PE
        if len(self.data) > 0x100:
            # Tenta encontrar assinatura MAGIC em CLR header
            for offset in range(0x100, min(0x2000, len(self.data)), 4):
                val = struct.unpack_from('<I', self.data, offset)[0]
                if val == self.CLR_MAGIC:
                    return True
        
        return False
    
    def _check_64bit(self) -> bool:
        """Verifica se é 64-bit."""
        # PE header offset
        if len(self.data) < 0x40:
            return False
        pe_offset = struct.unpack_from('<I', self.data, 0x3C)[0]
        if pe_offset + 20 > len(self.data):
            return False
        
        # Optional header magic
        opt_magic = struct.unpack_from('<H', self.data, pe_offset + 24)[0]
        return opt_magic == 0x20B  # PE32+
    
    def _detect_framework(self) -> str:
        """Detecta versao do .NET Framework."""
        # Procura por versoes no metadata
        patterns = [
            (b'.NETFramework,Version', 'NET Framework'),
            (b'.NETCoreApp', ' .NET Core'),
            (b'.NETStandard', ' .NET Standard'),
            (b'clr', 'CLR'),
        ]
        
        for pattern, name in patterns:
            if pattern in self.data:
                # Extrai versao
                idx = self.data.find(pattern)
                version_match = re.search(rb'v(\d+\.\d+)', self.data[idx:idx+100])
                if version_match:
                    return f"{name} {version_match.group(1).decode()}"
        
        return "Unknown"
    
    def _extract_assemblies(self) -> List[dict]:
        """Extrai informacoes de assemblies."""
        assemblies = []
        
        # Procura por nome de assembly no metadata
        # Pattern: .assembly extern ou .assembly
        assembly_pattern = re.compile(rb'\.assembly\s+(?:extern\s+)?([^\r\n{]+)')
        for match in assembly_pattern.finditer(self.data):
            name = match.group(1).decode('ascii', errors='ignore').strip()
            if name and len(name) > 2:
                assemblies.append({"name": name})
        
        # Procura por versao
        version_pattern = re.compile(rb'\.ver\s+(\d+)\.(\d+)')
        versions = version_pattern.findall(self.data)
        
        return assemblies[:20]
    
    def _extract_resources(self) -> List[dict]:
        """Extrai recursos embutidos."""
        resources = []
        
        # Procura por recursos em sections .resources ou .rsrc
        for section_name in ['.resources', '.rsrc', 'resources']:
            # Busca em toda a data por nomes de recurso
            pattern = section_name.encode()
            if pattern in self.data:
                idx = self.data.find(pattern)
                # Extrai contexto
                context = self.data[max(0, idx-50):idx+100]
                resources.append({
                    "type": section_name,
                    "offset": idx,
                    "size": len(context),
                    "data_preview": context[:50].hex()
                })
        
        # Tambem tenta extrair como ZIP (algunos resources sao XML/ZIP)
        if self.data[:2] == b'PK':
            try:
                with zipfile.ZipFile(Path(self.data)) as zf:
                    for name in zf.namelist():
                        resources.append({
                            "type": "zip_entry",
                            "name": name,
                            "size": zf.getinfo(name).file_size
                        })
            except:
                pass
        
        return resources
    
    def _extract_strings(self) -> List[str]:
        """Extrai strings legiveis."""
        ascii_pattern = re.compile(rb'[\x20-\x7e]{4,}')
        unicode_pattern = re.compile(rb'(?:[\x20-\x7e]\x00){3,}')
        
        strings = []
        for m in ascii_pattern.finditer(self.data):
            s = m.group().decode('ascii', errors='ignore')
            if len(s) >= 4:
                strings.append(s)
        
        for m in unicode_pattern.finditer(self.data):
            try:
                s = m.group().decode('utf-16-le', errors='ignore')
                if len(s) >= 4:
                    strings.append(s)
            except:
                pass
        
        return strings[:200]
    
    def _parse_type_library(self) -> dict:
        """Parseia tabela de tipos (TypeRef, TypeDef, MethodDef)."""
        # Simplificado: busca por referencias a tipos comuns
        type_patterns = [
            (rb'class\s+([A-Za-z_][A-Za-z0-9_]*)', 'class'),
            (rb'method\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', 'method'),
            (rb'property\s+([A-Za-z_][A-Za-z0-9_]*)', 'property'),
        ]
        
        types = {}
        for pattern, type_name in type_patterns:
            matches = re.findall(pattern, self.data)
            if matches:
                types[type_name] = [m.decode('ascii', errors='ignore') for m in matches[:20]]
        
        return types
    
    def decompile_method(self, method_offset: int, max_instructions: int = 100) -> List[str]:
        """
        Decompila um metodo a partir do offset.
        Nota: Implementacao简化ada — para CIL real, use ildasm ou dnSpy.
        """
        # Esta é uma simplificação — em produção, use bibliotecas como dnfile
        instructions = []
        offset = method_offset
        end = min(offset + max_instructions * 4, len(self.data))
        
        while offset < end:
            opcode_byte = self.data[offset]
            opcode = self.CIL_OPCODES.get(opcode_byte, f"0x{opcode_byte:02x}")
            instructions.append(f"  {offset:08x}: {opcode}")
            offset += 1
        
        return instructions


# Integragao com ferramentas externas
def decompile_with_ildasm(exe_path: str, output_dir: str) -> dict:
    """
    Decompila usando ildasm (parte do .NET SDK).
    Retorna dict com arquivo desassembly.
    """
    import subprocess
    import os
    
    output_file = Path(output_dir) / f"{Path(exe_path).stem}.il"
    
    try:
        # Tenta encontrar ildasm
        ildasm_paths = [
            r"C:\Program Files (x86)\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\ildasm.exe",
            r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\ildasm.exe",
            "ildasm",
        ]
        
        for ildasm in ildasm_paths:
            if os.path.exists(ildasm):
                result = subprocess.run(
                    [ildasm, exe_path, "/OUT=" + str(output_file), "/NOUNIFORM"],
                    capture_output=True, timeout=30
                )
                if result.returncode == 0 and output_file.exists():
                    return {
                        "success": True,
                        "output": str(output_file),
                        "tool": ildasm
                    }
        
        return {"success": False, "error": "ildasm não encontrado"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def decompile_with_dnspy(exe_path: str, output_dir: str) -> dict:
    """
    Decompila usando dnSpy (requer dnSpy instalado).
    """
    import subprocess
    
    # dnSpy command line (se suportado)
    # dnSpy.Console.exe /decompile "input.exe" /out "output/"
    output_path = Path(output_dir) / f"{Path(exe_path).stem}_dnspy"
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        result = subprocess.run(
            ["dnSpy.Console.exe", "/decompile", exe_path, "/out", str(output_path)],
            capture_output=True, timeout=60
        )
        if result.returncode == 0:
            return {
                "success": True,
                "output_dir": str(output_path),
                "files": list(output_path.glob("*.cs"))
            }
        return {"success": False, "error": result.stderr.decode()}
    except FileNotFoundError:
        return {"success": False, "error": "dnSpy.Console.exe não encontrado"}


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description=".NET Decompiler")
    parser.add_argument("file", help="Arquivo .NET para analisar")
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--strings-only", action="store_true")
    parser.add_argument("--resources-only", action="store_true")
    args = parser.parse_args()
    
    decompiler = DotNetDecompiler()
    result = decompiler.analyze(args.file)
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    elif args.strings_only:
        for s in result.get('strings', []):
            print(s)
    elif args.resources_only:
        for r in result.get('resources', []):
            print(f"Resource: {r.get('type', 'unknown')} @ 0x{r.get('offset', 0):x}")
    else:
        print(f"File: {result['file']}")
        print(f"Type: {result.get('type', 'unknown')}")
        if 'error' not in result:
            print(f"SHA256: {result['sha256']}")
            print(f"64-bit: {result.get('is_64bit', 'N/A')}")
            print(f"Framework: {result.get('target_framework', 'Unknown')}")
            print(f"Assemblies: {len(result.get('assemblies', []))}")
            print(f"Resources: {len(result.get('resources', []))}")
            print(f"Strings: {len(result.get('strings', []))}")
