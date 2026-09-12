"""
go_rust_analyzer.py
Análise especializada para binários compilados em Go e Rust
"""
import hashlib
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, list

@dataclass
class GoFuncInfo:
    name: str
    offset: int
    size: int
    package: str
    is_exported: bool
    has_receiver: bool

@dataclass
class RustSymbol:
    name: str
    demangled: str
    offset: int
    kind: str  # function, struct, impl, etc.

class GoRustAnalyzer:
    """
    Analisador especializado para binários Go e Rust.
    
    Go:
    - Mantién metadatos de símbolos em seções .gopclntab, .go.buildinfo
    - Nomes de funções e pacotes recuperáveis
    - Estrutura de dados do runtime Go
    
    Rust:
    - Nomes "mangled" em .text mas com informações em .rustc e .comment
    - Demangling via rustfilt ou regex
    - Metadados de crates em sections especiais
    """
    
    # Padrões Go
    GO_SIGNATURES = [
        b'\x00Go buildid:',  # Build ID Go
        b'\x00go build',
        b'.gopclntab',
        b'.go.buildinfo',
        b'\x00runtime.main',
        b'\x00main.main',
    ]
    
    # Padrões Rust
    RUST_SIGNATURES = [
        b'.rustc',
        b'\x00rustc',
        b'_ZN',  # Rust name mangling prefix
        b'.comment',  # Contém versão do compilador
    ]
    
    # Regex para demangle Rust
    RUST_MANGLE_PATTERN = re.compile(r'_ZN[0-9]+[^_]+_')
    
    # Regex para extrair nomes Go
    GO_FUNC_PATTERN = re.compile(rb'\x00([a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*)\x00')
    GO_PKG_PATTERN = re.compile(rb'\x00(([a-zA-Z][a-zA-Z0-9_/]*)(?:\.[a-zA-Z][a-zA-Z0-9_]*)?)\x00')
    
    def __init__(self):
        self.data = b''
        self.go_functions = []
        self.rust_symbols = []
        self.metadata = {}
    
    def analyze(self, file_path: str) -> dict:
        """Analisa binário Go ou Rust."""
        self.data = Path(file_path).read_bytes()
        
        result = {
            "file": file_path,
            "sha256": hashlib.sha256(self.data).hexdigest(),
            "size_bytes": len(self.data),
            "language": self._detect_language(),
            "version_info": self._extract_version(),
            "functions": [],
            "symbols": [],
            "metadata": {},
            "recovery_feasibility": "none"
        }
        
        lang = result["language"]
        
        if lang == "go":
            result.update(self._analyze_go())
            result["recovery_feasibility"] = "high"
        elif lang == "rust":
            result.update(self._analyze_rust())
            result["recovery_feasibility"] = "medium"
        elif lang == "go_rust_mixed":
            result.update(self._analyze_go())
            result.update(self._analyze_rust())
            result["recovery_feasibility"] = "medium"
        
        return result
    
    def _detect_language(self) -> str:
        """Detecta linguagem do binário."""
        data = self.data
        
        go_count = sum(1 for sig in self.GO_SIGNATURES if sig in data)
        rust_count = sum(1 for sig in self.RUST_SIGNATURES if sig in data)
        
        if go_count > rust_count and go_count > 0:
            return "go"
        elif rust_count > go_count and rust_count > 0:
            return "rust"
        elif go_count > 0 and rust_count > 0:
            return "go_rust_mixed"
        else:
            return "unknown"
    
    def _extract_version(self) -> dict:
        """Extrai informação de versão."""
        version_info = {}
        
        # Go version
        go_ver_match = re.search(rb'Go buildid: [^\x00]+\x00[^\x00]*GOAPI[^\x00]*', self.data)
        if go_ver_match:
            version_info["go_buildid"] = go_ver_match.group(0)[:100].decode('ascii', errors='ignore')
        
        # Rust version (da sección .comment)
        comment_section = re.search(rb'\x00GCC: \(.*?\) ([^\x00]+)', self.data)
        if comment_section:
            version_info["compiler"] = comment_section.group(1).decode('ascii', errors='ignore')
        
        # Rustc version específica
        rustc_match = re.search(rb'rustc ([^\x00]+)', self.data)
        if rustc_match:
            version_info["rustc"] = rustc_match.group(1).decode('ascii', errors='ignore')
        
        return version_info
    
    def _analyze_go(self) -> dict:
        """Análise específica para Go."""
        data = self.data
        
        # Extrai nomes de funções Go
        functions = []
        for match in self.GO_FUNC_PATTERN.finditer(data):
            func_name = match.group(1).decode('ascii', errors='ignore')
            # Go usa formato: package.Function
            parts = func_name.split('.')
            if len(parts) >= 2:
                package = '.'.join(parts[:-1])
                name = parts[-1]
                functions.append({
                    "name": func_name,
                    "package": package,
                    "function": name,
                    "offset": match.start(),
                    "is_main": name == "main" and package == "main"
                })
        
        # Deduplica
        seen = set()
        unique_funcs = []
        for f in functions:
            if f['name'] not in seen:
                seen.add(f['name'])
                unique_funcs.append(f)
        
        # Extrai tabelas de código Go (gopclntab)
        gopclntab_offset = data.find(b'.gopclntab')
        gopclntab_info = {}
        if gopclntab_offset != -1:
            gopclntab_info = {
                "found": True,
                "offset": gopclntab_offset,
                "description": "Go program counter table - contém mapping de PCs para funções"
            }
        
        # Build info
        buildinfo_offset = data.find(b'.go.buildinfo')
        buildinfo_info = {}
        if buildinfo_offset != -1:
            buildinfo_info = {
                "found": True,
                "offset": buildinfo_offset,
                "description": "Go build information - contém modinfo, compiler version"
            }
        
        # Extrai string de módulo Go (go.mod embed)
        mod_matches = re.findall(rb'mod [a-zA-Z0-9_./-]+; [a-zA-Z0-9.\-]+', data)
        modules = list(set(m.decode('ascii', errors='ignore') for m in mod_matches[:10]))
        
        return {
            "functions": unique_funcs[:100],
            "function_count": len(unique_funcs),
            "gopclntab": gopclntab_info,
            "buildinfo": buildinfo_info,
            "modules": modules,
            "has_main": any(f.get('is_main') for f in unique_funcs),
            "recovery_notes": [
                "Go mantém nomes de funções originales nas strings",
                "Use 'go tool compile -S' para analisar bytecode se tiver o .a",
                "Seções .gopclntab permitem mapear PC para função",
                "Build info contém hash do módulo e dependências"
            ]
        }
    
    def _analyze_rust(self) -> dict:
        """Análise específica para Rust."""
        data = self.data
        
        # Extrai símbolos mangled
        symbols = []
        
        # Pattern para símbolos Rust (ziga-ing complexo)
        # Formato: _ZN<crate_path>::<item>[[abcdef...]]
        rust_pattern = re.compile(rb'_ZN[0-9]+\([^)]+\)[^z]*')
        
        for match in rust_pattern.finditer(data):
            mangled = match.group(0).decode('ascii', errors='ignore')
            demangled = self._demangle_rust(mangled)
            
            if demangled and len(demangled) > 3:
                symbols.append({
                    "mangled": mangled[:80],
                    "demangled": demangled[:100],
                    "offset": match.start(),
                    "kind": self._classify_rust_symbol(demangled)
                })
        
        # Também procura por padrões mais simples
        simple_pattern = re.compile(rb'_ZN[a-zA-Z0-9_]+')
        for match in simple_pattern.finditer(data):
            mangled = match.group(0).decode('ascii', errors='ignore')
            if mangled not in [s['mangled'] for s in symbols]:
                demangled = self._demangle_rust(mangled)
                if demangled:
                    symbols.append({
                        "mangled": mangled[:80],
                        "demangled": demangled[:100],
                        "offset": match.start(),
                        "kind": self._classify_rust_symbol(demangled)
                    })
        
        # Deduplica
        seen = set()
        unique_symbols = []
        for s in symbols:
            key = s['demangled'][:50]
            if key not in seen:
                seen.add(key)
                unique_symbols.append(s)
        
        # Seção .rustc (contém metadados da crate)
        rustc_offset = data.find(b'.rustc')
        rustc_info = {}
        if rustc_offset != -1:
            rustc_info = {
                "found": True,
                "offset": rustc_offset,
                "size": min(1024, len(data) - rustc_offset),
                "description": "Rust compiler metadata - contém informações da crate"
            }
        
        # Extrai nomes de crates do .comment
        comment_section = re.search(rb'\x00\x01\xC0\xRA\xC7\x93.*?\x00', data)
        crate_info = {}
        
        return {
            "symbols": unique_symbols[:100],
            "symbol_count": len(unique_symbols),
            "rustc_section": rustc_info,
            "top_crates": list(set(s['demangled'].split('::')[0] for s in unique_symbols if '::' in s['demangled']))[:10],
            "recovery_notes": [
                "Rust usa name mangling — use rustfilt para demangle",
                "Seção .rustc contém metadados da crate (cargo metadata)",
                "Nomes de structs/enums são preservados no mangling",
                "Traits aparecem como _ZN...Trait... no mangled name"
            ]
        }
    
    def _demangle_rust(self, mangled: str) -> str:
        """Tenta demangle símbolo Rust."""
        # Implementação simplificada de demangling
        # Em produção, usar rustfilt ou biblioteca
        
        if not mangled.startswith('_ZN'):
            return mangled
        
        try:
            # Remove prefixo _ZN e sufixo possível
            name = mangled[3:]  # Remove _ZN
            
            # Remove número de segmentos inicial
            num_match = re.match(r'(\d+)', name)
            if num_match:
                name = name[num_match.end():]
            
            # Converte números de comprimento em delimitadores
            # Formato Rust: <number><name><delimiter>
            # Delimitadores: E (fim), _ (seguinte elemento)
            parts = []
            i = 0
            current = ""
            while i < len(name):
                if name[i].isdigit():
                    # Lê o número
                    num_end = i
                    while num_end < len(name) and name[num_end].isdigit():
                        num_end += 1
                    length = int(name[i:num_end])
                    # Próximo 'length' chars são o nome
                    segment = name[num_end:num_end + length]
                    parts.append(segment)
                    i = num_end + length
                else:
                    if name[i] == 'E':
                        break  # Fim do nome
                    current += name[i]
                    i += 1
            
            if parts:
                return '::'.join(parts)
            
            return mangled
        except:
            return mangled
    
    def _classify_rust_symbol(self, demangled: str) -> str:
        """Classifica tipo de símbolo Rust."""
        if '::new' in demangled:
            return "constructor"
        elif '::<' in demangled or 'impl' in demangled.lower():
            return "impl_block"
        elif demangled.endswith('::main'):
            return "main_function"
        elif 'trait' in demangled.lower():
            return "trait"
        elif re.search(r'struct\s+\w+', demangled):
            return "struct"
        elif re.search(r'enums?\s+\w+', demangled, re.IGNORECASE):
            return "enum"
        elif '(' in demangled and ')' in demangled:
            return "function"
        return "unknown"
    
    def generate_recovery_script(self, analysis: dict, output_path: str) -> str:
        """Gera script para recuperação de código."""
        lang = analysis.get('language', 'unknown')
        
        if lang == 'go':
            script = f'''"""
Go Binary Recovery Script
Target: {analysis['file']}
Functions recovered: {analysis.get('function_count', 0)}
"""
import subprocess
import re
from pathlib import Path

target = "{analysis['file']}"
output_dir = Path("{output_path}")
output_dir.mkdir(parents=True, exist_ok=True)

# Extrai funções Go conhecidas
go_functions = {analysis.get('functions', [])[:20]}

print(f"Recovering Go binary: {{target}}")
print(f"Found {{len(go_functions)}} functions")

# Usa objdump para extrair assembly com nomes
result = subprocess.run([
    'objdump', '-d', '--disassemble-symbols={{{", ".join(f"{{{f[\"name\"]}}}" for f in go_functions[:5])}}}',
    target
], capture_output=True, text=True)

with open(output_dir / "disassembly.asm", "w") as f:
    f.write(result.stdout)

print(f"Disassembly saved to {{output_dir / 'disassembly.asm'}}")

# Extrai strings relevantes
result2 = subprocess.run(['strings', target], capture_output=True, text=True)
with open(output_dir / "strings.txt", "w") as f:
    f.write(result2.stdout)

print("Done!")
'''
        elif lang == 'rust':
            script = f'''"""
Rust Binary Recovery Script
Target: {analysis['file']}
Symbols recovered: {analysis.get('symbol_count', 0)}
"""
import subprocess
from pathlib import Path

target = "{analysis['file']}"
output_dir = Path("{output_path}")
output_dir.mkdir(parents=True, exist_ok=True)

# Usa rustfilt para demanglar símbolos
rust_symbols = {analysis.get('symbols', [])[:20]}

print(f"Recovering Rust binary: {{target}}")
print(f"Found {{len(rust_symbols)}} symbols")

# Demangle com rustfilt (se disponível)
try:
    result = subprocess.run(['rustfilt', target], capture_output=True, text=True)
    with open(output_dir / "demangled.txt", "w") as f:
        f.write(result.stdout)
except FileNotFoundError:
    print("rustfilt não encontrado. Instale: cargo install rustfilt")
    # Fallback: extração manual
    import re
    data = open(target, 'rb').read()
    symbols = re.findall(rb'_ZN[0-9]+[^_]+_', data)
    with open(output_dir / "mangled_symbols.txt", "wb") as f:
        f.write(b'\\n'.join(symbols[:100]))

# Extraí assembly
result2 = subprocess.run(['objdump', '-d', target], capture_output=True, text=True)
with open(output_dir / "disassembly.asm", "w") as f:
    f.write(result2.stdout)

print(f"Done! Output in {{output_dir}}")
'''
        else:
            script = "# No language-specific recovery available\n"
        
        Path(output_path).write_text(script)
        return output_path


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Go/Rust Binary Analyzer")
    parser.add_argument("file", help="Binário Go ou Rust para analisar")
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--script", "-s", action="store_true", help="Gerar script de recuperação")
    parser.add_argument("--output", "-o", help="Diretorio de saida")
    args = parser.parse_args()
    
    analyzer = GoRustAnalyzer()
    result = analyzer.analyze(args.file)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"File: {result['file']}")
        print(f"Language: {result['language']}")
        print(f"SHA256: {result['sha256']}")
        print(f"Recovery Feasibility: {result['recovery_feasibility']}")
        
        if result.get('version_info'):
            print(f"\nVersion Info:")
            for k, v in result['version_info'].items():
                print(f"  {k}: {v[:80]}")
        
        if result['language'] == 'go':
            print(f"\nGo Functions ({result.get('function_count', 0)}):")
            for f in result.get('functions', [])[:15]:
                main_mark = " [MAIN]" if f.get('is_main') else ""
                print(f"  {f['package']}.{f['function']}{main_mark}")
            
            if result.get('gopclntab', {}).get('found'):
                print(f"\n.gopclntab section found at 0x{result['gopclntab']['offset']:x}")
            if result.get('buildinfo', {}).get('found'):
                print(f".go.buildinfo section found at 0x{result['buildinfo']['offset']:x}")
        
        elif result['language'] == 'rust':
            print(f"\nRust Symbols ({result.get('symbol_count', 0)}):")
            for s in result.get('symbols', [])[:15]:
                print(f"  {s['demangled'][:60]}")
            
            if result.get('rustc_section', {}).get('found'):
                print(f"\n.rustc section found at 0x{result['rustc_section']['offset']:x}")
        
        if result.get('recovery_notes'):
            print(f"\nRecovery Notes:")
            for note in result['recovery_notes']:
                print(f"  • {note}")
    
    if args.script:
        output = args.output or "./go_rust_recovery"
        Path(output).mkdir(parents=True, exist_ok=True)
        script_path = analyzer.generate_recovery_script(result, output)
        print(f"\nRecovery script saved to: {script_path}")
