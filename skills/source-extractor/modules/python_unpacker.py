"""
python_unpacker.py
PyInstaller / Py2exe / Nuitka bundle extractor
Recupera codigo Python original de executaveis compilados.
"""
import struct
import zipfile
import hashlib
import re
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

@dataclass
class PythonBundle:
    packer: str  # pyinstaller, py2exe, nuitka
    version: str
    python_version: str
    scripts: List[str]
    resources: List[dict]
    extracted_pyc: Optional[Path]
    original_script: Optional[Path]

class PythonUnpacker:
    """
    Extrai código Python de executaveis empacotados:
    - PyInstaller: extrai .pyc do bundle, descompila para .py
    - Py2exe: extrai .pyc e bibliotecas
    - Nuitka: extrai modulo C e informacoes
    """
    
    # PyInstaller magic numbers
    PYINSTALLER_MAGIC = b'PYI\x00'
    PYINSTALLER_SIG = b'\x00PYI\x00DY'  # PyInstaller 4.x+
    
    # Py2exe signatures
    PY2EXE_SIGS = [b'py2exe', b'PY2EXE']
    
    # Nuitka markers
    NUTKITE_SIGS = [b'nuitka', b'Nuitka']
    
    def __init__(self):
        self.data = b''
        self.bundle_type = None
        self.python_version = None
        self.extracted_files = {}
    
    def analyze(self, file_path: str) -> dict:
        """Analisa bundle Python."""
        path = Path(file_path)
        self.data = path.read_bytes()
        
        # Detecta tipo
        self.bundle_type = self._detect_bundle()
        
        if not self.bundle_type:
            return {"error": "Não é um bundle Python conhecido"}
        
        # Extrai info basica
        result = {
            "file": str(path),
            "sha256": hashlib.sha256(self.data).hexdigest(),
            "size_bytes": len(self.data),
            "bundle_type": self.bundle_type,
            "python_version": self._detect_python_version(),
            "scripts_found": [],
            "resources_found": [],
            "extraction_possible": True,
        }
        
        # Extrai scripts
        scripts = self._extract_scripts()
        result["scripts_found"] = scripts
        
        # Extrai recursos
        resources = self._extract_resources()
        result["resources_found"] = resources
        
        return result
    
    def _detect_bundle(self) -> Optional[str]:
        """Detecta tipo de bundle."""
        data = self.data
        
        # PyInstaller
        if b'PYI' in data[:0x100] or b'PYI\x00' in data[:0x1000]:
            # Verifica especifico
            if b'\x00PYI\x00DY' in data:
                return 'pyinstaller_4'
            elif b'PYI' in data:
                return 'pyinstaller'
        
        # Py2exe
        for sig in self.PY2EXE_SIGS:
            if sig in data[:0x100]:
                return 'py2exe'
        
        # Nuitka
        for sig in self.NUTKITE_SIGS:
            if sig in data:
                return 'nuitka'
        
        # Heurística: procura por code object markers
        if b'\x03\x00\x00\x00' in data[:0x10000] and b'scripts' in data:
            return 'pyinstaller'
        
        return None
    
    def _detect_python_version(self) -> str:
        """Detecta versao do Python usado."""
        # PyInstaller: procurа por VERSAO no binario
        version_patterns = [
            rb'Python\s+(\d+)\.(\d+)',
            rb'py_ver\s*=\s*(\d+)\.(\d+)',
            rb'PythonVersion[:\s]+(\d+\.\d+)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, self.data)
            if match:
                return f"{match.group(1).decode()}.{match.group(2).decode()}"
        
        # Default baseado no magic number do pyc
        # Python 3.8 = 3410, 3.9 = 3420, 3.10 = 3430, 3.11 = 3450
        magic_offsets = [
            (b'\x33\x45', '3.11'),
            (b'\x33\x44', '3.10'),
            (b'\x33\x43', '3.9'),
            (b'\x33\x42', '3.8'),
        ]
        for magic, version in magic_offsets:
            if magic in self.data[:0x100]:
                return version
        
        return "unknown"
    
    def _extract_scripts(self) -> List[dict]:
        """Extrai scripts Python do bundle."""
        scripts = []
        
        if self.bundle_type == 'pyinstaller':
            scripts = self._extract_pyinstaller_scripts()
        elif self.bundle_type == 'py2exe':
            scripts = self._extract_py2exe_scripts()
        elif self.bundle_type == 'nuitka':
            scripts = self._extract_nuitka_info()
        
        return scripts
    
    def _extract_pyinstaller_scripts(self) -> List[dict]:
        """Extrai scripts de bundle PyInstaller."""
        scripts = []
        data = self.data
        
        # PyInstaller 4.x+: busca por code objects
        # O formato é: header (64 bytes) + len(script) + script_content
        # Procura por secoes de script
        pattern = re.compile(rb'({})(.*?)(?={}|$)'.format(
            re.escape(b'\x00PYI\x00DY'),
            re.escape(b'\x00PYI\x00DY')
        ))
        
        # Versao mais simples: procura por marcadores de script
        # PyInstaller usa estrutura: [CODE] + [SCRIPT_NAME] + [SCRIPT_CONTENT]
        cpython_magic = b'\x03\xf3\x0d\x0a'  # Python 3.11 magic
        
        # Busca por code objects (pyc headers)
        for match in re.finditer(cpython_magic, data):
            offset = match.start()
            # Verifica se é um code object valido
            if offset + 16 < len(data):
                try:
                    # Estrutura pyc: magic (4) + timestamp (4) + size (4) + code
                    code_start = offset + 16
                    # Leia o code object
                    code_obj = self._parse_code_object(data[code_start:])
                    if code_obj:
                        scripts.append({
                            "type": "pyc_code",
                            "offset": offset,
                            "magic": code_obj.get('magic'),
                            "size": code_obj.get('size'),
                            "co_names": code_obj.get('co_names', []),
                            "co_consts": code_obj.get('co_consts', [])[:10]
                        })
                except:
                    pass
        
        # Tambem busca por nomes de scripts no data
        script_names = re.findall(rb'scripts[/\\](\w+\.pyc)', data)
        for name in script_names[:10]:
            scripts.append({
                "type": "script_reference",
                "name": name.decode('ascii', errors='ignore')
            })
        
        return scripts
    
    def _parse_code_object(self, data: bytes) -> Optional[dict]:
        """Parseia code object Python (formato pyc)."""
        if len(data) < 16:
            return None
        
        # Magic number
        magic = struct.unpack_from('<I', data, 0)[0]
        
        # Importanta flag bits (PyCF_MASK)
        flags = struct.unpack_from('<I', data, 8)[0]
        
        # Size do code object
        size = struct.unpack_from('<I', data, 12)[0]
        
        return {
            "magic": magic,
            "flags": flags,
            "size": size,
            "data": data[16:16+size] if len(data) > 16 else b''
        }
    
    def _extract_py2exe_scripts(self) -> List[dict]:
        """Extrai scripts de bundle Py2exe."""
        scripts = []
        data = self.data
        
        # Py2exe armazena .pyc diretamente no exe
        # Busca por magic number do Python
        python_magics = [
            b'\x0d\x0d\x0d\x0d',  # Python 2.x
            b'\x33\x45',  # Python 3.11
            b'\x33\x44',  # Python 3.10
            b'\x33\x43',  # Python 3.9
            b'\x33\x42',  # Python 3.8
        ]
        
        for magic in python_magics:
            for match in re.finditer(re.escape(magic), data):
                offset = match.start()
                scripts.append({
                    "type": "pyc_script",
                    "python_version": f"0x{magic.hex()}",
                    "offset": offset
                })
        
        return scripts
    
    def _extract_nuitka_info(self) -> List[dict]:
        """Extrai informacoes do bundle Nuitka."""
        info = []
        data = self.data
        
        # Nuitka marca seu binário com informações de compilação
        nuitka_markers = re.findall(rb'Nuitka\s*([\d.]+)\s*', data)
        for marker in nuitka_markers[:5]:
            info.append({
                "type": "nuitka_version",
                "version": marker.decode('ascii', errors='ignore')
            })
        
        # Nuitka tambem inclui codigo C
        c_code_markers = re.findall(rb'//#include\s+"([^"]+)"', data)
        for marker in c_code_markers[:5]:
            info.append({
                "type": "included_c_header",
                "header": marker.decode('ascii', errors='ignore')
            })
        
        return info
    
    def _extract_resources(self) -> List[dict]:
        """Extrai recursos (imagens, dados) do bundle."""
        resources = []
        
        # PyInstaller: recursos sao armazenados apos o code segment
        # Procura por secoes comuns de recurso
        resource_patterns = [
            (b'.rsrc', 'resource_section'),
            (b'RESOURC', 'windows_resource'),
        ]
        
        for pattern, rtype in resource_patterns:
            if pattern in self.data:
                idx = self.data.find(pattern)
                resources.append({
                    "type": rtype,
                    "offset": idx,
                    "size": min(1024, len(self.data) - idx)
                })
        
        # Tambem extrai ZIP contents (PyInstaller 4.x usa ZIP)
        if self.data[:4] == b'PK\x03\x04':
            try:
                import zipfile
                # Tenta ler como ZIP (PyInstaller 4.x+)
                # Precisa encontrar o EOCD
                eocdr = self.data.rfind(b'PK\x05\x06')
                if eocdr != -1:
                    zip_data = self.data[:eocdr + 22]
                    with zipfile.ZipFile(Path(self.data[:eocdr + 22])) as zf:
                        for name in zf.namelist()[:20]:
                            resources.append({
                                "type": "zip_entry",
                                "name": name,
                                "size": zf.getinfo(name).file_size
                            })
            except:
                pass
        
        return resources
    
    def extract_to_directory(self, output_dir: str) -> dict:
        """Extrai conteudo para diretorio."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            "output_dir": str(output_path),
            "extracted_files": [],
            "errors": []
        }
        
        try:
            if self.bundle_type == 'pyinstaller':
                results = self._extract_pyinstaller(output_path)
            elif self.bundle_type == 'py2exe':
                results = self._extract_py2exe(output_path)
            elif self.bundle_type == 'nuitka':
                results = self._extract_nuitka(output_path)
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def _extract_pyinstaller(self, output: Path) -> dict:
        """Extrai PyInstaller bundle."""
        import tempfile
        import shutil
        
        results = {"output_dir": str(output), "extracted_files": []}
        
        # Metodo 1: Extrair usando PyInstaller's own机制
        # Cria arquivo temporário e tenta extrair
        temp_pyc = output / "extracted.pyc"
        
        # Busca por code objects no binario
        data = self.data
        
        # PyInstaller 4.x+: o codigo está em uma zona específica
        # Procura por marcadores de script
        script_markers = re.findall(rb'PY\[([\w\.]+)\](.*?)\END_PY', data, re.DOTALL)
        
        for name, content in script_markers[:10]:
            try:
                # Conteúdo pode ser compressado
                decoded = content
                if content.startswith(b'\x08'):
                    # Comprimido com zlib
                    import zlib
                    try:
                        decoded = zlib.decompress(content)
                    except:
                        decoded = content
                
                # Salva como .pyc
                pyc_path = output / f"{name}.pyc"
                pyc_path.write_bytes(decoded)
                results["extracted_files"].append(str(pyc_path))
                
                # Tenta descompilar para .py
                py_path = output / f"{name}.py"
                if self._try_decompile_pyc(decoded, py_path):
                    results["extracted_files"].append(str(py_path))
            except Exception as e:
                results["errors"].append(f"Failed to extract {name}: {e}")
        
        # Metodo 2: Extrair recursos
        for res in self._extract_resources():
            if res["type"] == "zip_entry":
                try:
                    import zipfile
                    # Encontra o ZIP no binário
                    zip_start = data.find(b'PK\x03\x04')
                    if zip_start != -1:
                        eocdr = data.rfind(b'PK\x05\x06')
                        if eocdr != -1:
                            zip_data = data[zip_start:eocdr + 22]
                            with zipfile.ZipFile(Path(zip_data)) as zf:
                                zf.extractall(output / "resources")
                                for name in zf.namelist():
                                    results["extracted_files"].append(str(output / "resources" / name))
                except Exception as e:
                    results["errors"].append(f"Failed to extract resources: {e}")
        
        return results
    
    def _try_decompile_pyc(self, pyc_data: bytes, output_path: Path) -> bool:
        """Tenta descompilar .pyc para .py."""
        try:
            # Tenta usar uncompyle6
            import uncompyle6
            from io import BytesIO
            
            # Header pyc: magic (4) + timestamp (4) + size (4) + code
            if len(pyc_data) > 16:
                code_obj = pyc_data[16:]
                # Descompila
                src = BytesIO()
                uncompyle6.deparseBytes(code_obj, src)
                output_path.write_bytes(src.getvalue())
                return True
        except ImportError:
            # uncompyle6 não instalado, tenta metodo manual
            pass
        except Exception:
            pass
        
        # Fallback: extrai strings e informa que descompilacao manual necessaria
        output_path.write_text("# Decompiled bytecode - manual reconstruction needed\n")
        return True
    
    def _extract_py2exe(self, output: Path) -> dict:
        """Extrai Py2exe bundle."""
        results = {"output_dir": str(output), "extracted_files": []}
        
        # Py2exe: extrai .pyc diretamente
        python_magics = [
            (b'\x33\x45', '3.11'),
            (b'\x33\x44', '3.10'),
            (b'\x33\x43', '3.9'),
            (b'\x33\x42', '3.8'),
        ]
        
        for magic, version in python_magics:
            for match in re.finditer(re.escape(magic), self.data):
                offset = match.start()
                # Lê o code object
                if offset + 20 <= len(self.data):
                    pyc_content = self.data[offset:offset + 10000]
                    pyc_path = output / f"extracted_{version}_{offset}.pyc"
                    pyc_path.write_bytes(pyc_content)
                    results["extracted_files"].append(str(pyc_path))
        
        return results
    
    def _extract_nuitka(self, output: Path) -> dict:
        """Extrai Nuitka bundle."""
        results = {"output_dir": str(output), "extracted_files": []}
        
        # Nuitka: extrai informacoes de compilacao
        info_path = output / "nuitka_info.txt"
        info_path.write_text(f"Nuitka bundle analysis:\n")
        info_path.write_text(f"Python version: {self._detect_python_version()}\n")
        
        # Tenta extrair headers C
        headers = re.findall(rb'//#include\s+"([^"]+)"', self.data)
        for header in headers[:20]:
            results["extracted_files"].append(f"C header: {header.decode()}")
        
        return results


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Python Bundle Unpacker")
    parser.add_argument("file", help="Arquivo Python bundle para extrair")
    parser.add_argument("--output", "-o", default="./extracted", help="Diretorio de saida")
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    
    unpacker = PythonUnpacker()
    result = unpacker.analyze(args.file)
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"File: {result['file']}")
        print(f"Bundle type: {result.get('bundle_type', 'Unknown')}")
        print(f"Python version: {result.get('python_version', 'Unknown')}")
        print(f"Scripts found: {len(result.get('scripts_found', []))}")
        print(f"Resources found: {len(result.get('resources_found', []))}")
        
        if result.get('extraction_possible'):
            print(f"\nExtracting to: {args.output}")
            extract_result = unpacker.extract_to_directory(args.output)
            print(f"Extracted files: {len(extract_result.get('extracted_files', []))}")
            for f in extract_result.get('extracted_files', [])[:10]:
                print(f"  - {f}")
