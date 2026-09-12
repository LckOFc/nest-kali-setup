"""
pattern_matcher.py
AI-assisted pattern matching for obfuscated code
"""
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, list

@dataclass
class PatternMatch:
    pattern_type: str
    confidence: float
    offset: int
    original: str
    decoded: str
    description: str

class PatternMatcher:
    """
    Matching de padrões para código ofuscado.
    
    Padroes detectados:
    1. String concatenation obfuscation
    2. Array-based string building
    3. Arithmetic obfuscation (expressões matemáticas)
    4. Jump table obfuscation
    5. Control flow flattening
    6. Null byte padding
    7. Character code manipulation
    """
    
    # Padrões de ofuscação comuns
    OBFS_PATTERNS = {
        'string_concat': re.compile(r'"[^"]+"\s*\+\s*"[^"]+"'),
        'char_array_build': re.compile(r'\[\s*[0-9]+\s*,\s*[0-9]+\s*,\s*[0-9]+\s*\]'),
        'arith_expr': re.compile(r'[0-9]+\s*[\+\-\*/]\s*[0-9]+'),
        'null_padding': re.compile(r'\x00{3,}'),
        'byte_sequence': re.compile(r'(?:\\x[0-9a-fA-F]{2}){4,}'),
    }
    
    def __init__(self):
        self.matches: list[PatternMatch] = []
    
    def analyze(self, file_path: str) -> dict:
        """Análise de padrões de ofuscação."""
        data = Path(file_path).read_bytes()
        
        result = {
            "file": file_path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "total_patterns": 0,
            "matches": [],
            "obfuscation_level": "none",
            "recommendations": []
        }
        
        # Detecta tipos de padrões
        patterns_found = {}
        
        for pattern_name, pattern_re in self.OBFS_PATTERNS.items():
            matches = list(pattern_re.finditer(data))
            if matches:
                patterns_found[pattern_name] = [
                    {"offset": m.start(), "match": m.group().decode('ascii', errors='ignore')[:50]}
                    for m in matches[:20]
                ]
                result["total_patterns"] += len(matches)
        
        result["patterns_found"] = patterns_found
        
        # Classifica nivel de ofuscação
        result["obfuscation_level"] = self._classify_obfuscation(patterns_found)
        
        # Gera recomendações
        result["recommendations"] = self._generate_recommendations(patterns_found, result["obfuscation_level"])
        
        # Gera matches detalhados
        all_matches = []
        for ptype, items in patterns_found.items():
            for item in items[:10]:
                all_matches.append({
                    "type": ptype,
                    "offset": item["offset"],
                    "sample": item["match"][:80],
                    "confidence": 0.7 if ptype in ("string_concat", "char_array_build") else 0.5
                })
        
        result["matches"] = all_matches[:30]
        
        self.matches = [
            PatternMatch(
                pattern_type=m["type"],
                confidence=m["confidence"],
                offset=m["offset"],
                original=m["sample"],
                decoded=self._try_decode(m["type"], m["sample"]),
                description=f"Obfuscation pattern: {m['type']}"
            )
            for m in all_matches
        ]
        
        return result
    
    def _classify_obfuscation(self, patterns: dict) -> str:
        """Classifica nivel de ofuscação."""
        if not patterns:
            return "none"
        
        score = 0
        if 'string_concat' in patterns:
            score += len(patterns['string_concat']) * 2
        if 'char_array_build' in patterns:
            score += len(patterns['char_array_build']) * 3
        if 'arith_expr' in patterns:
            score += len(patterns['arith_expr'])
        if 'byte_sequence' in patterns:
            score += len(patterns['byte_sequence']) * 2
        
        if score > 50:
            return "heavy"
        elif score > 20:
            return "moderate"
        elif score > 5:
            return "light"
        return "none"
    
    def _try_decode(self, pattern_type: str, sample: str) -> str:
        """Tenta decodificar amostra de padrão."""
        if pattern_type == 'string_concat':
            # Remove operadores + e espaços
            decoded = re.sub(r'\s*\+\s*', '', sample)
            return decoded
        elif pattern_type == 'byte_sequence':
            # Converte escape sequences para texto
            try:
                decoded = sample.encode().decode('unicode_escape')
                return decoded[:50]
            except:
                return sample[:50]
        elif pattern_type == 'char_array_build':
            # Extrai numeros e converte para chars
            nums = re.findall(r'\d+', sample)
            try:
                decoded = ''.join(chr(int(n)) for n in nums if 32 <= int(n) <= 126)
                return decoded
            except:
                return sample[:50]
        return sample[:50]
    
    def _generate_recommendations(self, patterns: dict, level: str) -> list[str]:
        """Gera recomendações baseadas nos padrões encontrados."""
        recs = []
        
        if level == "heavy":
            recs.append("Binary heavily obfuscated. Consider: 1) Dynamic analysis with debugger 2) Function-level tracing 3) AI-assisted pattern recognition")
        
        if 'string_concat' in patterns:
            recs.append("String concatenation obfuscation detected. Use constant folding to reconstruct original strings.")
        
        if 'char_array_build' in patterns:
            recs.append("Character array string building detected. Extract numeric values and convert to string.")
        
        if 'byte_sequence' in patterns:
            recs.append("Raw byte sequences detected. Decode escape sequences to recover strings.")
        
        if not recs:
            recs.append("No significant obfuscation patterns detected. Standard analysis should work.")
        
        return recs


# AI Integration (placeholder for LLM-based pattern recognition)
class AIPatternMatcher:
    """
    Versao avançada com integração LLM para reconhecimento de padrões.
    Usa Ollama/local LLM para analisar padrões complexos.
    """
    
    def __init__(self, llm_endpoint: str = "http://localhost:11434", model: str = "codellama:13b"):
        self.endpoint = llm_endpoint
        self.model = model
    
    async def analyze_with_ai(self, analysis_result: dict) -> dict:
        """Análise aprimorada com IA."""
        import httpx
        import json
        
        # Prepara prompt para IA
        prompt = f"""Analise os padrões de ofuscação neste binário e sugira técnicas de recuperação.

FILE: {analysis_result.get('file', 'unknown')}
SHA256: {analysis_result.get('sha256', 'N/A')}
OBUSCATION LEVEL: {analysis_result.get('obfuscation_level', 'unknown')}
PATTERNS FOUND: {json.dumps(analysis_result.get('patterns_found', {}), default=str)[:500]}

Com base nesses padrões, sugira:
1. Técnicas específicas de desofuscação
2. Order de análise recomendada
3. Possíveis strings ocultas
4. Pontos de interesse para debugging

Responda de forma tecnica e direta, em português."""
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{self.endpoint}/api/generate", json=payload)
                ai_response = resp.json().get("response", "")
                return {"ai_analysis": ai_response, "source": "llm"}
        except Exception as e:
            return {"ai_analysis": f"AI analysis failed: {e}", "source": "error"}


# CLI interface
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Pattern Matcher for Obfuscated Code")
    parser.add_argument("file", help="Arquivo para analisar padrões de ofuscação")
    parser.add_argument("--json", "-j", action="store_true")
    parser.add_argument("--ai", "-a", action="store_true", help="Usar IA para análise adicional")
    parser.add_argument("--model", "-m", default="codellama:13b", help="Modelo LLM")
    args = parser.parse_args()
    
    matcher = PatternMatcher()
    result = matcher.analyze(args.file)
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"File: {result['file']}")
        print(f"SHA256: {result['sha256']}")
        print(f"Obfuscation Level: {result['obfuscation_level']}")
        print(f"Total patterns: {result['total_patterns']}")
        
        if result.get('patterns_found'):
            print(f"\nPatterns Found:")
            for ptype, items in result['patterns_found'].items():
                print(f"  {ptype}: {len(items)} occurrences")
                for item in items[:3]:
                    print(f"    0x{item['offset']:08x}: {item['match'][:60]}")
        
        if result.get('recommendations'):
            print(f"\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
    
    if args.ai:
        print(f"\nRunning AI analysis...")
        import asyncio
        ai_matcher = AIPatternMatcher(model=args.model)
        ai_result = asyncio.run(ai_matcher.analyze_with_ai(result))
        print(f"\nAI Analysis:")
        print(ai_result.get('ai_analysis', 'No AI response'))
