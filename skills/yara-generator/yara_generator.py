"""
yara_generator.py
Automatic YARA rule generation from malware samples
"""
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

@dataclass
class YaraRule:
    name: str
    description: str
    generated_date: str
    hash_sha256: str
    strings: dict[int, str]
    condition: str
    tags: list[str]
    
    def to_yara(self) -> str:
        """Converte para string YARA valida."""
        tags_str = " ".join(self.tags)
        tags_line = f" {{tags=\"{tags_str}\"" if tags_str else " {"
        
        strings_block = "\n".join(
            f"        ${'s' if i > 0 else ''}{i} = \"{self._escape_yara(s)}\""
            for i, s in enumerate(self.strings.values())
        )
        
        return f"""rule {self.name}{tags_line}
{{
    meta:
        description = \"{self.description}\"
        generated_date = \"{self.generated_date}\"
        hash_sha256 = \"{self.hash_sha256}\"
    
    strings:
{strings_block}
    
    condition:
        {self.condition}
}}"""
    
    def _escape_yara(self, s: str) -> str:
        """Escapa caracteres para YARA."""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


class YaraRuleGenerator:
    """Gera regras YARA automaticamente a partir de samples."""
    
    # Palavras/comuns a remover (ruído)
    COMMON_PATTERNS = [
        r'http://', r'https://', r'www\.',
        r'Windows', r'Microsoft', r'Visual Studio',
        r'This program cannot', r'The application',
        r'error', r'debug', r'Debug',
        r'\x00', r'\\x00',
    ]
    
    # Patterns suspeitos a priorizar
    SUSPICIOUS_PATTERNS = [
        r'http[s]?://[^\s"<\'>]{8,}',  # URLs
        r'[A-Za-z0-9+/]{20,}={0,2}',  # Base64
        r'\\[A-Z][a-z]+\\[A-Z][a-z]+',  # Caminhos Windows
        r'HKLM|HKCU|Software\\Microsoft',  # Registry keys
        r'CreateRemoteThread|VirtualAllocEx|WriteProcessMemory',  # APIs de injecao
        r'CryptEncrypt|CryptDecrypt|BCryptEncrypt',  # Criptografia
        r'svchost\.exe|rundll32\.exe|regsvr32\.exe',  # LOLBins
        r'%APPDATA%|%TEMP%|LocalAppData',  # Paths de persistencia
    ]
    
    def __init__(self, min_string_length: int = 4, max_rules: int = 10):
        self.min_length = min_string_length
        self.max_rules = max_rules
    
    def generate_from_sample(self, file_path: str, rule_name: str = None, 
                              tags: list[str] = None) -> YaraRule:
        """Gera uma regra YARA a partir de um sample."""
        path = Path(file_path)
        data = path.read_bytes()
        
        # Nome da regra
        if not rule_name:
            rule_name = f"gen_{path.stem}_{hashlib.md5(data[:100]).hexdigest()[:8]}"
        
        # Extrai strings
        strings = self._extract_strings(data)
        
        # Filtra ruído e seleciona as mais relevantes
        filtered = self._filter_and_rank(strings, data)
        
        # Limita numero de strings
        selected = filtered[:self.max_rules * 2]  # duplica para ter fallback
        
        # Constrói condicao
        condition = self._build_condition(len(selected))
        
        # Cria regra
        return YaraRule(
            name=rule_name,
            description=f"Generated from {file_path}",
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hash_sha256=hashlib.sha256(data).hexdigest(),
            strings={i: s for i, s in enumerate(selected)},
            condition=condition,
            tags=tags or []
        )
    
    def generate_batch(self, file_paths: list[str], prefix: str = "gen") -> list[YaraRule]:
        """Gera regras para multiplos samples."""
        rules = []
        for i, path in enumerate(file_paths):
            try:
                rule_name = f"{prefix}_{i}_{Path(path).stem}"
                rule = self.generate_from_sample(path, rule_name=rule_name)
                rules.append(rule)
            except Exception as e:
                print(f"Erro ao processar {path}: {e}")
        return rules
    
    def _extract_strings(self, data: bytes) -> list[str]:
        """Extrai strings ASCII e Unicode do arquivo."""
        # ASCII strings
        ascii_strings = re.findall(rb'[\x20-\x7e]{4,}', data)
        ascii_list = [s.decode('ascii', errors='ignore') for s in ascii_strings]
        
        # Unicode strings (UTF-16 LE)
        unicode_strings = re.findall(rb'(?:[\x20-\x7e]\x00){3,}', data)
        unicode_list = []
        for s in unicode_strings:
            try:
                decoded = s.decode('utf-16-le', errors='ignore')
                unicode_list.append(decoded)
            except:
                pass
        
        return ascii_list + unicode_list
    
    def _filter_and_rank(self, strings: list[str], raw_data: bytes) -> list[str]:
        """Filtra ruído e rankeia por relevancia."""
        # Remove strings comuns (ruído)
        filtered = []
        for s in strings:
            # Remove vazio e muito curto
            if len(s) < self.min_length:
                continue
            
            # Remove strings muito comuns (ruído)
            is_common = False
            for pattern in self.COMMON_PATTERNS:
                if re.search(pattern, s, re.IGNORECASE):
                    is_common = True
                    break
            
            if is_common:
                continue
            
            filtered.append(s)
        
        # Rankeia por "suspeitosidade"
        scored = []
        for s in filtered:
            score = 0
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, s, re.IGNORECASE):
                    score += 1
            scored.append((score, s))
        
        # Ordena por score (mais relevante primeiro)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Retorna strings
        return [s for _, s in scored]
    
    def _build_condition(self, num_strings: int) -> str:
        """Constrói condicao YARA baseada no numero de strings."""
        if num_strings <= 2:
            return "all of them"
        elif num_strings <= 5:
            return "3 of them"
        elif num_strings <= 10:
            return "4 of them"
        else:
            return "5 of them"
    
    def save_rule(self, rule: YaraRule, output_path: str):
        """Salva regra em arquivo .yar."""
        Path(output_path).write_text(rule.to_yara())


class YaraScanner:
    """Escaneia directories com regras YARA."""
    
    def __init__(self, rules_dir: str = "./yara_rules"):
        self.rules_dir = Path(rules_dir)
        self.rules: list[YaraRule] = []
        self._load_rules()
    
    def _load_rules(self):
        """Carrega regras do diretorio."""
        self.rules = []
        for yar_file in self.rules_dir.glob("*.yar"):
            try:
                content = yar_file.read_text()
                # Parse basico para extrair nomes das regras
                rules = re.findall(r'rule\s+(\w+)', content)
                self.rules.extend(rules)
            except:
                pass
    
    async def scan_directory(self, target_dir: str, recursive: bool = True) -> list[dict]:
        """Escaneia directory com regras YARA."""
        targets = list(Path(target_dir).rglob("*")) if recursive else list(Path(target_dir).glob("*"))
        results = []
        
        for target in targets:
            if target.is_file():
                hits = await self._scan_file(target)
                results.extend(hits)
        
        return results
    
    async def _scan_file(self, file_path: Path) -> list[dict]:
        """Escaneia arquivo unico."""
        try:
            import subprocess
            cmd = ["yara", "-r", str(self.rules_dir), str(file_path)]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            results = []
            for line in stdout.decode().splitlines():
                if line.strip():
                    parts = line.split()
                    results.append({
                        "rule": parts[0],
                        "file": str(file_path),
                        "matches": parts[1] if len(parts) > 1 else ""
                    })
            return results
        except FileNotFoundError:
            return [{"error": "YARA CLI not installed", "file": str(file_path)}]
        except Exception as e:
            return [{"error": str(e), "file": str(file_path)}]


# CLI interface
if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="YARA Rule Generator")
    parser.add_argument("file", help="Sample para gerar regra")
    parser.add_argument("--name", "-n", help="Nome da regra")
    parser.add_argument("--tags", "-t", nargs="*", help="Tags para a regra")
    parser.add_argument("--output", "-o", help="Salvar regra em arquivo .yar")
    parser.add_argument("--min-length", type=int, default=4, help="Tamanho minimo de string")
    parser.add_argument("--max-rules", type=int, default=10, help="Maximo de regras")
    parser.add_argument("--scan", "-s", help="Diretorio para escanear com regra gerada")
    args = parser.parse_args()
    
    generator = YaraRuleGenerator(
        min_string_length=args.min_length,
        max_rules=args.max_rules
    )
    
    # Gera regra
    rule = generator.generate_from_sample(args.file, args.name, args.tags)
    
    # Output
    print(rule.to_yara())
    
    # Salva se solicitado
    if args.output:
        generator.save_rule(rule, args.output)
        print(f"\nRegra salva em: {args.output}")
    
    # Escanea se solicitado
    if args.scan:
        scanner = YaraScanner(rules_dir=Path(args.output).parent if args.output else Path("./"))
        results = asyncio.run(scanner.scan_directory(args.scan))
        print(f"\nResultados do scan:")
        for r in results:
            print(f"  {r['rule']} -> {r['file']}")
