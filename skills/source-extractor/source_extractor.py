"""
source_extractor.py
Orquestrador principal do Source Extractor Toolkit
Integra: PE Analyzer, .NET Decompiler, Python Unpacker, String Miner, Control Flow
"""
import asyncio
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List

# Adiciona modulo path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from pe_analyzer import PEAnalyzer
from dotnet_decompiler import DotNetDecompiler, decompile_with_ildasm, decompile_with_dnspy
from python_unpacker import PythonUnpacker
from string_miner import StringMiner

class ExtractionType(Enum):
    NATIVE_PE = "native_pe"
    DOTNET = "dotnet"
    PYTHON_PYINSTALLER = "python_pyinstaller"
    PYTHON_PY2EXE = "python_py2exe"
    PYTHON_NUTKITA = "python_nuitka"
    NODE_PKG = "node_pkg"
    NODE_NEXE = "node_nexe"
    UNKNOWN = "unknown"

@dataclass
class ExtractionResult:
    file_path: str
    extraction_type: ExtractionType
    success: bool
    error: Optional[str]
    pe_info: Optional[dict]
    source_files: List[dict]
    strings: List[dict]
    report_path: Optional[str]
    timing_ms: int

class SourceExtractor:
    """
    Orquestrador principal que integra todos os modulos
    para extracao completa de codigo fonte de .exe.
    """
    
    def __init__(self, output_dir: str = "./output", max_workers: int = 4):
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.pe_analyzer = PEAnalyzer()
        self.dotnet_decompiler = DotNetDecompiler()
        self.python_unpacker = PythonUnpacker()
        self.string_miner = StringMiner()
    
    async def analyze(self, file_path: str, full: bool = False) -> dict:
        """Analise rapida de arquivo."""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"Arquivo não encontrado: {file_path}"}
        
        start = time.time()
        
        # Analise PE basica
        pe_result = self.pe_analyzer.parse(str(path))
        
        # Detecta tipo
        etype = self._detect_type(pe_result)
        
        timing = int((time.time() - start) * 1000)
        
        return {
            "file": str(path),
            "sha256": pe_result.get("sha256", ""),
            "size_bytes": pe_result.get("size_bytes", 0),
            "extraction_type": etype.value,
            "timing_ms": timing,
            "pe_info": pe_result,
            "suggested_actions": self._get_suggested_actions(etype, pe_result)
        }
    
    async def extract(self, file_path: str, output_dir: str = None) -> ExtractionResult:
        """Extracao completa com reconstrucao de fonte."""
        path = Path(file_path)
        out_dir = Path(output_dir or self.output_dir) / path.stem
        
        start = time.time()
        
        # Fase 1: Analise PE
        pe_info = self.pe_analyzer.parse(str(path))
        
        # Fase 2: Detecao de tipo
        etype = self._detect_type(pe_info)
        
        # Fase 3: Extracao especifica
        source_files = []
        error = None
        
        try:
            if etype == ExtractionType.DOTNET:
                source_files = await self._extract_dotnet(str(path), out_dir)
            elif etype in (ExtractionType.PYTHON_PYINSTALLER, ExtractionType.PYTHON_PY2EXE, ExtractionType.PYTHON_NUTKITA):
                source_files = await self._extract_python(str(path), out_dir)
            elif etype == ExtractionType.NODE_PKG or etype == ExtractionType.NODE_NEXE:
                source_files = await self._extract_node(str(path), out_dir)
            else:
                # Nativo: extrai strings e gerar assembly
                source_files = await self._extract_native(str(path), out_dir)
        except Exception as e:
            error = str(e)
        
        # Fase 4: Extracao de strings (sempre)
        strings = self.string_miner.mine(str(path))
        
        timing = int((time.time() - start) * 1000)
        
        # Gera relatorio
        report_path = None
        if out_dir.exists():
            report_path = str(out_dir / "report.md")
            self._generate_report(str(path), pe_info, etype, source_files, strings, report_path)
        
        return ExtractionResult(
            file_path=str(path),
            extraction_type=etype,
            success=error is None,
            error=error,
            pe_info=pe_info,
            source_files=source_files,
            strings=strings,
            report_path=report_path,
            timing_ms=timing
        )
    
    async def pipeline(self, file_path: str, output_dir: str = None, fast_mode: bool = False) -> dict:
        """Pipeline completo: analyze -> detect -> unpack -> extract -> report."""
        path = Path(file_path)
        out_dir = Path(output_dir or self.output_dir) / path.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        
        stages = []
        results = {}
        
        # Stage 1: PE Analysis
        stage1_start = time.time()
        pe_info = self.pe_analyzer.parse(str(path))
        stage1_time = int((time.time() - stage1_start) * 1000)
        stages.append({"name": "pe_analysis", "success": True, "time_ms": stage1_time})
        results["pe_info"] = pe_info
        
        # Stage 2: Type Detection
        stage2_start = time.time()
        etype = self._detect_type(pe_info)
        stage2_time = int((time.time() - stage2_start) * 1000)
        stages.append({"name": "type_detection", "success": True, "time_ms": stage2_time, "type": etype.value})
        results["extraction_type"] = etype.value
        
        # Stage 3: Unpacking (se necessario)
        unpacked_path = str(path)
        if pe_info.get("verdict", {}).get("packer_detected"):
            stage3_start = time.time()
            unpacked_path = await self._try_unpack(str(path), out_dir / "unpacked")
            stage3_time = int((time.time() - stage3_start) * 1000)
            stages.append({"name": "unpacking", "success": True, "time_ms": stage3_time, "output": unpacked_path})
            results["unpacked_path"] = unpacked_path
        
        # Stage 4: Extraction
        stage4_start = time.time()
        extracted_files = []
        
        target = unpacked_path
        if etype == ExtractionType.DOTNET:
            extracted_files = await self._extract_dotnet(target, out_dir / "source")
        elif etype.value.startswith("python_"):
            extracted_files = await self._extract_python(target, out_dir / "source")
        elif etype.value.startswith("node_"):
            extracted_files = await self._extract_node(target, out_dir / "source")
        else:
            extracted_files = await self._extract_native(target, out_dir / "source")
        
        stage4_time = int((time.time() - stage4_start) * 1000)
        stages.append({"name": "extraction", "success": True, "time_ms": stage4_time, "files": len(extracted_files)})
        results["extracted_files"] = extracted_files
        
        # Stage 5: String Mining
        if not fast_mode:
            stage5_start = time.time()
            strings = self.string_miner.mine(target)
            stage5_time = int((time.time() - stage5_start) * 1000)
            stages.append({"name": "string_mining", "success": True, "time_ms": stage5_time, "count": strings.get("total_strings", 0)})
            results["strings"] = strings
        
        # Stage 6: Report Generation
        stage6_start = time.time()
        report_path = str(out_dir / "report.md")
        self._generate_report(str(path), pe_info, etype, extracted_files, results.get("strings", {}), report_path)
        stage6_time = int((time.time() - stage6_start) * 1000)
        stages.append({"name": "report_generation", "success": True, "time_ms": stage6_time, "path": report_path})
        
        total_time = sum(s["time_ms"] for s in stages)
        
        return {
            "status": "completed",
            "file": str(path),
            "extraction_type": etype.value,
            "total_time_ms": total_time,
            "stages": stages,
            "output_dir": str(out_dir),
            "report_path": report_path,
            "extracted_files_count": len(extracted_files),
            "summary": self._generate_summary(pe_info, etype, extracted_files, results.get("strings", {}))
        }
    
    def _detect_type(self, pe_info: dict) -> ExtractionType:
        """Detecta tipo de executavel."""
        # .NET
        if b'CorExeMain' in self.pe_analyzer.data[:0x1000] or b'CorDllMain' in self.pe_analyzer.data[:0x1000]:
            return ExtractionType.DOTNET
        
        # Python (PyInstaller)
        if b'\x00PYI\x00DY' in self.pe_analyzer.data or b'PYI\x00' in self.pe_analyzer.data[:0x100]:
            if b'scripts' in self.pe_analyzer.data or b'Scripts' in self.pe_analyzer.data:
                return ExtractionType.PYTHON_PYINSTALLER
        
        # Python (Py2exe)
        if b'py2exe' in self.pe_analyzer.data.lower() or b'PY2EXE' in self.pe_analyzer.data:
            return ExtractionType.PYTHON_PY2EXE
        
        # Python (Nuitka)
        if b'Nuitka' in self.pe_analyzer.data or b'nuitka' in self.pe_analyzer.data.lower():
            return ExtractionType.PYTHON_NUTKITA
        
        # Node.js (pkg)
        if b'pkg prebundle' in self.pe_analyzer.data or b'NODE_OPTIONS' in self.pe_analyzer.data:
            return ExtractionType.NODE_PKG
        
        # Node.js (nexe)
        if b'nexe' in self.pe_analyzer.data.lower():
            return ExtractionType.NODE_NEXE
        
        return ExtractionType.NATIVE_PE
    
    def _get_suggested_actions(self, etype: ExtractionType, pe_info: dict) -> List[str]:
        """Sugere acoes com base no tipo detectado."""
        actions = []
        
        if etype == ExtractionType.DOTNET:
            actions.extend([
                "Usar ildasm para decompilar CIL: ildasm.exe arquivo.exe /OUT=output.il",
                "Usar dnSpy para análise visual",
                "Extrair recursos: Resources.resx -> arquivos"
            ])
        elif etype.value.startswith("python_"):
            actions.extend([
                "Executar: python_unpacker.py arquivo.exe --output ./extracted",
                "Descompilar .pyc para .py: uncompyle6 extracted.pyc > source.py",
                "Extrair resources (imagens, dados)"
            ])
        elif etype.value.startswith("node_"):
            actions.extend([
                "Executar: node-unpacker artigo.exe --output ./extracted",
                "Parsear V8 snapshot para extrair JS"
            ])
        else:
            actions.extend([
                "Extrair strings: strings.exe arquivo.exe > strings.txt",
                "Analisar imports: importando bibliotecas suspeitas",
                "Desmontar com Ghidra/x64dbg",
                "Extrair recursos embutidos"
            ])
        
        # Verifica packer
        if pe_info.get("verdict", {}).get("packer_detected"):
            actions.insert(0, "⚠ PACKER DETECTADO: Despacotar primeiro!")
        
        return actions
    
    async def _extract_dotnet(self, file_path: str, output_dir: Path) -> List[dict]:
        """Extrai fonte de executavel .NET."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analisa com dotnet decompiler
        result = self.dotnet_decompiler.analyze(file_path)
        
        extracted = []
        
        # Salva assembly info
        if result.get("assemblies"):
            assemblies_file = output_dir / "assemblies.txt"
            assemblies_file.write_text("\n".join(a.get("name", "") for a in result["assemblies"]))
            extracted.append({"path": str(assemblies_file), "type": "assembly_list"})
        
        # Salva strings
        if result.get("strings"):
            strings_file = output_dir / "strings.txt"
            strings_file.write_text("\n".join(result["strings"][:500]))
            extracted.append({"path": str(strings_file), "type": "strings"})
        
        # Tenta ildasm
        il_result = decompile_with_ildasm(file_path, str(output_dir))
        if il_result.get("success"):
            extracted.append({"path": il_result["output"], "type": "cil_disassembly"})
        
        # Salva tipos detectados
        if result.get("tlv_table"):
            types_file = output_dir / "types.txt"
            types_text = "\n".join(f"{k}: {v[:10]}" for k, v in result["tlv_table"].items())
            types_file.write_text(types_text)
            extracted.append({"path": str(types_file), "type": "types"})
        
        return extracted
    
    async def _extract_python(self, file_path: str, output_dir: Path) -> List[dict]:
        """Extrai fonte de bundle Python."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = self.python_unpacker.extract_to_directory(str(output_dir))
        
        extracted = []
        for f in result.get("extracted_files", []):
            extracted.append({"path": f, "type": "extracted"})
        
        # Tenta descompilar pyc para py
        for pyc in output_dir.glob("*.pyc"):
            py_file = pyc.with_suffix(".py")
            if self._try_decompile_pyc(pyc, py_file):
                extracted.append({"path": str(py_file), "type": "decompiled_py"})
        
        return extracted
    
    async def _extract_node(self, file_path: str, output_dir: Path) -> List[dict]:
        """Extrai fonte de bundle Node.js."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        data = Path(file_path).read_bytes()
        extracted = []
        
        # Busca por snapshot V8 (pkg)
        # pkg usa marca "pkg prebundle" seguido de dados compressados
        if b'pkg prebundle' in data:
            idx = data.find(b'pkg prebundle')
            # Extrai dados apos o marker
            snapshot_data = data[idx + len(b'pkg prebundle'):]
            
            # Tenta decomprimir (zlib)
            import zlib
            try:
                decompressed = zlib.decompress(snapshot_data, -zlib.MAX_WBITS)
                # O snapshot contem JS
                # Busca por modules no snapshot
                module_pattern = re.compile(rb'"([^"]+\.js)"', decompressed)
                for match in module_pattern.finditer(decompressed):
                    module_name = match.group(1).decode('ascii', errors='ignore')
                    # Extrai conteudo do modulo
                    # Formato: nome + conteudo entre chaves
                    # Simplificado: salva todo o snapshot como .js
                    js_file = output_dir / f"{module_name.replace('/', '_')}.js"
                    js_file.write_bytes(decompressed)
                    extracted.append({"path": str(js_file), "type": "node_snapshot"})
            except:
                # Salva bruto para analise
                snapshot_file = output_dir / "snapshot.raw"
                snapshot_file.write_bytes(snapshot_data)
                extracted.append({"path": str(snapshot_file), "type": "raw_snapshot"})
        
        # Nexe (similar mas com formato diferente)
        if b'nexe' in data:
            # Extrai módulos embutidos
            nexe_pattern = re.compile(rb'nexe[^\x00]{0,100}([^\x00]{4,})', data)
            for match in nexe_pattern.finditer(data):
                content = match.group(1)
                if len(content) > 100:
                    js_file = output_dir / "nexe_module.js"
                    js_file.write_bytes(content[:10000])
                    extracted.append({"path": str(js_file), "type": "nexe_module"})
        
        return extracted
    
    async def _extract_native(self, file_path: str, output_dir: Path) -> List[dict]:
        """Extrai informacoes de executavel nativo."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        extracted = []
        
        # Extrai strings
        strings_result = self.string_miner.mine(file_path)
        strings_file = output_dir / "strings.txt"
        all_strings = (
            strings_result.get("ascii_strings", []) +
            strings_result.get("unicode_strings", [])
        )
        strings_file.write_text("\n".join(all_strings[:10000]))
        extracted.append({"path": str(strings_file), "type": "strings"})
        
        # Extrai padrões
        patterns = self.string_miner.find_patterns(Path(file_path).read_bytes())
        patterns_file = output_dir / "patterns.txt"
        patterns_text = []
        for name, matches in patterns.items():
            for m in matches[:10]:
                patterns_text.append(f"[{name}] 0x{m['offset']:x}: {m['value'][:80]}")
        patterns_file.write_text("\n".join(patterns_text))
        extracted.append({"path": str(patterns_file), "type": "patterns"})
        
        # Gera assembly basico (pseudo-codigo)
        asm_file = output_dir / "assembly.asm"
        asm_content = self._generate_stub_asm(file_path)
        asm_file.write_text(asm_content)
        extracted.append({"path": str(asm_file), "type": "assembly_stub"})
        
        return extracted
    
    def _try_decompile_pyc(self, pyc_path: Path, py_path: Path) -> bool:
        """Tenta descompilar .pyc para .py."""
        try:
            import uncompyle6
            from io import BytesIO
            
            data = pyc_path.read_bytes()
            if len(data) < 16:
                return False
            
            # Code object começa apos header (magic + timestamp + size)
            code_data = data[16:]
            
            src = BytesIO()
            uncompyle6.deparseBytes(code_data, src)
            py_path.write_bytes(src.getvalue())
            return True
        except ImportError:
            # Fallback: extrai strings do pyc
            import re
            data = pyc_path.read_bytes()
            strings = re.findall(rb'[\x20-\x7e]{4,}', data)
            py_path.write_text(f"# Decompiled from {pyc_path.name}\n# Install uncompyle6 for proper decompilation\n\n")
            py_path.write_text(py_path.read_text() + "\n".join(s.decode('ascii', errors='ignore') for s in strings[:100]))
            return True
        except Exception:
            return False
    
    async def _try_unpack(self, file_path: str, output_dir: Path) -> str:
        """Tenta despacotar arquivo."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import subprocess
        import shutil
        
        # UPX
        upx_path = shutil.which("upx")
        if upx_path:
            output_file = output_dir / f"{Path(file_path).stem}.unpacked.exe"
            try:
                result = subprocess.run(
                    [upx_path, "-d", file_path, "-o", str(output_file)],
                    capture_output=True, timeout=60
                )
                if result.returncode == 0 and output_file.exists():
                    return str(output_file)
            except:
                pass
        
        # Se não conseguiu auto, retorna original
        return file_path
    
    def _generate_stub_asm(self, file_path: str) -> str:
        """Gera stub de assembly basico."""
        data = Path(file_path).read_bytes()
        
        lines = [
            "; Assembly stub generated by Source Extractor",
            f"; File: {file_path}",
            f"; Size: {len(data)} bytes",
            f"; SHA256: {hashlib.sha256(data).hexdigest()}",
            ";",
            "; WARNING: This is a stub. Use Ghidra/x64dbg for full analysis.",
            "",
            ".code",
            "",
        ]
        
        # Extrais primeros bytes como assembly approx
        for i in range(0, min(256, len(data)), 16):
            chunk = data[i:i+16]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            asm_str = ' '.join(f'{b:02x}' for b in chunk)
            lines.append(f"; 0x{i:08x}: {hex_str}")
        
        lines.append("")
        lines.append("; End of stub")
        
        return "\n".join(lines)
    
    def _generate_report(self, file_path: str, pe_info: dict, etype: ExtractionType, 
                        source_files: List[dict], strings: dict, report_path: str):
        """Gera relatório Markdown."""
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        content = [
            f"# Source Extraction Report",
            f"",
            f"**File:** `{file_path}`",
            f"**Type:** {etype.value}",
            f"**SHA256:** `{pe_info.get('sha256', 'N/A')}`",
            f"**Size:** {pe_info.get('size_bytes', 0):,} bytes",
            f"",
            f"---",
            f"",
        ]
        
        # Seções
        content.extend([
            f"## PE Information",
            f"",
            f"| Property | Value |",
            f"|----------|-------|",
            f"| Format | {pe_info.get('format', 'N/A')} |",
            f"| PE Type | {pe_info.get('pe_type', 'N/A')} |",
            f"| Machine | {pe_info.get('machine', 'N/A')} |",
            f"| Entry Point | `{pe_info.get('entry_point', 'N/A')}` |",
            f"| Sections | {pe_info.get('num_sections', 0)} |",
            f"| Global Entropy | {pe_info.get('global_entropy', 0):.4f} |",
        ])
        
        # Imports
        imports = pe_info.get('imports', [])
        if imports:
            content.extend([
                f"",
                f"## Imports ({len(imports)} DLLs)",
                f"",
            ])
            for imp in imports[:15]:
                funcs = ', '.join(imp.get('functions', [])[:5])
                content.append(f"- `{imp['library']}`: {funcs}")
        
        # Suspicious indicators
        suspicious = pe_info.get('suspicious_indicators', [])
        if suspicious:
            content.extend([
                f"",
                f"## Suspicious Indicators ({len(suspicious)})",
                f"",
            ])
            for s in suspicious[:10]:
                content.append(f"- ⚠️ {s}")
        
        # Source files extracted
        if source_files:
            content.extend([
                f"",
                f"## Extracted Source Files",
                f"",
            ])
            for sf in source_files:
                content.append(f"- `{sf.get('path', 'unknown')}` ({sf.get('type', 'unknown')})")
        
        # Strings summary
        if strings:
            total = strings.get('total_strings', 0)
            content.extend([
                f"",
                f"## String Analysis",
                f"",
                f"- **Total strings:** {total}",
                f"- **ASCII:** {len(strings.get('ascii_strings', []))}",
                f"- **Unicode:** {len(strings.get('unicode_strings', []))}",
                f"- **Base64 decoded:** {len(strings.get('base64_decoded', []))}",
                f"- **XOR decoded:** {len(strings.get('xor_decoded', []))}",
            ])
        
        # Verdict
        verdict = pe_info.get('verdict', {})
        content.extend([
            f"",
            f"## Verdict",
            f"",
            f"- **Threat Level:** {verdict.get('threat_level', 'UNKNOWN')}",
            f"- **Risk Score:** {verdict.get('risk_score', 0)}/100",
            f"- **Packer Detected:** {verdict.get('packer_detected', False)}",
            f"- **Needs Unpacking:** {verdict.get('needs_unpacking', False)}",
        ])
        
        path.write_text("\n".join(content))
    
    def _generate_summary(self, pe_info: dict, etype: ExtractionType, 
                         source_files: List[dict], strings: dict) -> str:
        """Gera resumo legivel."""
        lines = [
            f"=== Extraction Summary ===",
            f"File: {pe_info.get('file', 'unknown')}",
            f"Type: {etype.value}",
            f"SHA256: {pe_info.get('sha256', 'N/A')}",
            f"",
        ]
        
        if source_files:
            lines.append(f"Extracted {len(source_files)} source file(s):")
            for sf in source_files[:5]:
                lines.append(f"  - {sf.get('path', 'unknown')}")
        else:
            lines.append("No source files extracted (may require manual analysis)")
        
        if strings:
            total = strings.get('total_strings', 0)
            lines.append(f"\nFound {total} strings (ASCII + Unicode + decoded)")
        
        verdict = pe_info.get('verdict', {})
        if verdict.get('threat_level') in ('HIGH', 'CRITICAL'):
            lines.append(f"\n⚠️  High threat level detected - analyze carefully!")
        
        return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Source Extractor Toolkit")
    parser.add_argument("file", help="Arquivo .exe para extrair fonte")
    parser.add_argument("--output", "-o", default="./output", help="Diretorio de saida")
    parser.add_argument("--full", "-f", action="store_true", help="Analise completa com todos os estagios")
    parser.add_argument("--fast", action="store_true", help="Modo rapido (pulsa sandbox)")
    parser.add_argument("--json", "-j", action="store_true", help="Output em JSON")
    parser.add_argument("--strings-only", action="store_true", help="Somente extracao de strings")
    parser.add_argument("--dir", "-d", help="Diretorio para analisar multiplos arquivos")
    parser.add_argument("--parallel", "-p", type=int, default=4, help="Numero de workers parallel")
    args = parser.parse_args()
    
    async def main():
        extractor = SourceExtractor(output_dir=args.output, max_workers=args.parallel)
        
        if args.dir:
            # Batch mode
            import glob
            files = glob.glob(f"{args.dir}/**/*.exe", recursive=True)
            print(f"Found {len(files)} .exe files")
            
            results = []
            for f in files[:args.parallel * 2]:  # Limita batch
                print(f"\nProcessing: {f}")
                if args.full:
                    result = await extractor.pipeline(f, args.output, fast_mode=args.fast)
                else:
                    result = await extractor.analyze(f, full=True)
                results.append(result)
                print(f"  Type: {result.get('extraction_type', 'unknown')}")
                print(f"  Timing: {result.get('timing_ms', 0)}ms")
            
            # Salva resultados batch
            import json
            Path(args.output).mkdir(parents=True, exist_ok=True)
            Path(args.output, "batch_results.json").write_text(json.dumps(results, indent=2, default=str))
            print(f"\nBatch results saved to {args.output}/batch_results.json")
        
        else:
            # Single file mode
            if args.full:
                result = await extractor.pipeline(args.file, args.output, fast_mode=args.fast)
                if args.json:
                    print(json.dumps(result, indent=2, default=str))
                else:
                    print(f"\n{'='*60}")
                    print("SOURCE EXTRACTION PIPELINE RESULT")
                    print(f"{'='*60}")
                    print(f"Status: {result['status']}")
                    print(f"Type: {result['extraction_type']}")
                    print(f"Total time: {result['total_time_ms']}ms")
                    print(f"Output: {result['output_dir']}")
                    print(f"Report: {result['report_path']}")
                    print(f"\n{result['summary']}")
            else:
                result = await extractor.analyze(args.file, full=True)
                if args.json:
                    print(json.dumps(result, indent=2, default=str))
                else:
                    print(f"File: {result['file']}")
                    print(f"Type: {result['extraction_type']}")
                    print(f"SHA256: {result['sha256']}")
                    print(f"\nSuggested actions:")
                    for action in result.get('suggested_actions', []):
                        print(f"  → {action}")
    
    asyncio.run(main())
