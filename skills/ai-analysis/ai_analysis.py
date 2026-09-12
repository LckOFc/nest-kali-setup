"""
ai_analysis.py
AI-assisted analysis pipeline for binary reverse engineering
"""
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class AnalysisContext:
    """Contexto enriquecido para analise da IA."""
    file_path: str
    sha256: str
    md5: str
    size_bytes: int
    entropy: float
    imports: list[str]
    strings_sample: list[str]
    suspicious_indicators: list[str]
    sections: list[dict]
    previous_analysis: Optional[dict] = None

class AIAnalysisPipeline:
    """Pipeline de analise assistida por IA."""
    
    def __init__(
        self,
        llm_endpoint: str = None,
        model: str = "codellama:13b",
        max_tokens: int = 2048,
        temperature: float = 0.3
    ):
        self.endpoint = llm_endpoint or os.getenv("AI_LLM_ENDPOINT", "http://localhost:11434")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    async def analyze(self, file_path: str) -> dict:
        """Analise completa com IA."""
        # 1. Coleta contexto
        context = self._collect_context(file_path)
        
        # 2. Gera hipoteses
        hypotheses = await self._generate_hypotheses(context)
        
        # 3. Sugere proximos passos
        next_steps = await self._suggest_next_steps(context, hypotheses)
        
        # 4. Avalia risco
        risk = await self._assess_risk(context, hypotheses)
        
        return {
            "file": file_path,
            "sha256": context.sha256,
            "hypotheses": hypotheses,
            "next_steps": next_steps,
            "risk_assessment": risk,
            "confidence": risk.get("confidence", 0),
            "timestamp": asyncio.get_event_loop().time()
        }
    
    def _collect_context(self, file_path: str) -> AnalysisContext:
        """Coleta contexto do binario."""
        path = Path(file_path)
        data = path.read_bytes()
        
        import hashlib
        sha256 = hashlib.sha256(data).hexdigest()
        md5 = hashlib.md5(data).hexdigest()
        
        # Extrai strings relevantes
        import re
        strings = re.findall(rb'[\x20-\x7e]{4,}', data)
        string_samples = [s.decode('ascii', errors='ignore') for s in strings[:100]]
        
        # Busca imports (simplificado — em prod usar pefile)
        imports = []
        for s in string_samples:
            if s.endswith('.dll') or '.dll' in s:
                imports.append(s)
        imports = list(set(imports))[:20]
        
        # Indicadores suspeitos
        suspicious = []
        suspicious_keywords = ['crypt', 'inject', 'hook', 'keylog', 'screenshot', 
                               'shellcode', 'exec', 'download', 'upload', 'backdoor']
        for s in string_samples:
            if any(kw in s.lower() for kw in suspicious_keywords):
                suspicious.append(s)
        
        return AnalysisContext(
            file_path=str(path),
            sha256=sha256,
            md5=md5,
            size_bytes=len(data),
            entropy=self._calc_entropy(data),
            imports=imports,
            strings_sample=string_samples[:30],
            suspicious_indicators=suspicious[:10],
            sections=[]
        )
    
    def _calc_entropy(self, data: bytes) -> float:
        import math
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
    
    async def _generate_hypotheses(self, context: AnalysisContext) -> list[dict]:
        """Gera hipoteses sobre comportamento do malware."""
        prompt = f"""Analise este binário e gere hipóteses sobre seu comportamento.

ARQUIVO: {context.file_path}
SHA256: {context.sha256}
ENTROPIA: {context.entropy}
SIZE: {context.size_bytes} bytes

IMPORTS DETECTADOS:
{chr(10).join(context.imports[:15]) if context.imports else 'N/A'}

STRINGS RELEVANTES:
{chr(10).join(context.strings_sample[:10])}

INDICADORES SUSPEITOS:
{chr(10).join(context.suspicious_indicators) if context.suspicious_indicators else 'Nenhum'}

Gere 3-5 hipóteses em formato JSON:
[
  {{"hipótese": "...", "evidencia": "...", "probabilidade": "alta/media/baixa"}}
]

Responda APENAS com JSON válido."""
        
        return await self._call_llm(prompt, response_format="json")
    
    async def _suggest_next_steps(self, context: AnalysisContext, hypotheses: list) -> list[str]:
        """Sugere próximos passos de análise."""
        prompt = f"""Com base nestas hipóteses: {hypotheses},
quais são os próximos 3-5 passos de engenharia reversa?

Considere:
1. Onde colocar breakpoints no debugger (x64dbg)
2. Quais APIs monitorar (API Monitor)
3. Quais seções examinar no hex editor
4. Técnicas de unpacking necessárias
5. YARA rules para detectar variantes

Responda como lista JSON de strings."""
        
        return await self._call_llm(prompt, response_format="json")
    
    async def _assess_risk(self, context: AnalysisContext, hypotheses: list) -> dict:
        """Avaliação de risco综合."""
        prompt = f"""Avalie o risco deste binário:

- Entropia: {context.entropy} (alto = packed/criptografado)
- Imports suspeitos: {[i for i in context.imports if any(k in i.lower() for k in ['crypt', 'inject', 'hook', 'keylog', 'screenshot', 'exec', 'download'])]}
- Hypotheses: {hypotheses}

Retorne JSON:
{{"threat_level": "critical/high/medium/low/info", "confidence": 0-100, "reasoning": "..."}}"""
        
        return await self._call_llm(prompt, response_format="json")
    
    async def _call_llm(self, prompt: str, response_format: str = "text") -> any:
        """Chama LLM local (Ollama)."""
        import httpx
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature
            }
        }
        if response_format != "text":
            payload["format"] = "json"
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{self.endpoint}/api/generate", json=payload)
                result = resp.json()
                response_text = result.get("response", "")
                
                if response_format == "json":
                    # Tenta extrair JSON da resposta
                    try:
                        # Procura por JSON na resposta
                        json_match = re.search(r'\[.*\]|\{.*\}', response_text, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        pass
                    return [{"error": "Failed to parse JSON", "raw": response_text[:500]}]
                
                return response_text
        except Exception as e:
            return {"error": str(e), "fallback": True}
    
    async def chat(self, query: str, context: dict = None) -> str:
        """Chat interativo com a IA sobre analise."""
        ctx_text = ''
        if context:
            ctx_text = f'Aqui está o contexto do binário analisado:\n{json.dumps(context, indent=2)}\n\n'
        prompt = f"""Você é um especialista em engenharia reversa e segurança.

{ctx_text}{query}

Responda de forma tecnica e direta."""
        
        return await self._call_llm(prompt)


# CLI interface
if __name__ == "__main__":
    import argparse
    import re
    
    parser = argparse.ArgumentParser(description="AI Analysis Pipeline")
    parser.add_argument("file", help="Binário para analisar")
    parser.add_argument("--hypotheses-only", action="store_true", help="Apenas gerar hipóteses")
    parser.add_argument("--next-steps", action="store_true", help="Apenas sugestões de próximos passos")
    parser.add_argument("--risk-assessment", action="store_true", help="Apenas avaliação de risco")
    parser.add_argument("--full", "-f", action="store_true", help="Analise completa")
    parser.add_argument("--output", "-o", help="Salvar resultado em JSON")
    parser.add_argument("--model", "-m", default=os.getenv("AI_MODEL", "codellama:13b"), help="Modelo LLM")
    args = parser.parse_args()
    
    async def main():
        pipeline = AIAnalysisPipeline(model=args.model)
        
        if args.full:
            result = await pipeline.analyze(args.file)
        else:
            # Análise parcial
            context = pipeline._collect_context(args.file)
            
            if args.hypotheses_only:
                result = await pipeline._generate_hypotheses(context)
            elif args.next_steps:
                hyp = await pipeline._generate_hypotheses(context)
                result = await pipeline._suggest_next_steps(context, hyp)
            elif args.risk_assessment:
                hyp = await pipeline._generate_hypotheses(context)
                result = await pipeline._assess_risk(context, hyp)
            else:
                result = await pipeline.analyze(args.file)
        
        # Output
        if isinstance(result, dict):
            output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output = str(result)
        
        print(output)
        
        if args.output:
            Path(args.output).write_text(output)
            print(f"\nResultado salvo em: {args.output}")
    
    asyncio.run(main())
