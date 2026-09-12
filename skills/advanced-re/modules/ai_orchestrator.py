"""
ai_orchestrator.py
Orquestrador IA para pipeline automatico de engenharia reversa avanzada
"""
import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

@dataclass
class PipelineStage:
    name: str
    status: str  # pending, running, completed, failed, skipped
    input: dict
    output: Optional[dict]
    duration_ms: int
    ai_suggestion: Optional[str]

class AIOrchestrator:
    """
    Orquestrador que integra todos os modulos advanced-re
    com assistencia de IA para decisoes automaticas.
    
    Fluxo:
    1. Detecta tipo de protecao (IA + heuristica)
    2. Escolhe estrategia basadas em padroes conhecidos
    3. Executa modulo especifico
    4. Avalia resultado e decide proximo passo
    5. Gera relatorio consolidado
    """
    
    def __init__(
        self,
        llm_endpoint: str = None,
        llm_model: str = "codellama:13b",
        output_dir: str = "./advanced_re_output"
    ):
        self.llm_endpoint = llm_endpoint or "http://localhost:11434"
        self.llm_model = llm_model
        self.output_dir = Path(output_dir)
        self.stages: list[PipelineStage] = []
        self.context: dict = {}
    
    async def run_pipeline(self, target: str, options: dict = None) -> dict:
        """Pipeline completo com IA."""
        options = options or {}
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[AI Orch] Starting pipeline for: {target}")
        start_time = time.time()
        
        # Stage 1: Initial Analysis
        stage1 = await self._stage_initial_analysis(target)
        self.stages.append(stage1)
        if stage1.status != "completed":
            return self._final_report(error="Initial analysis failed")
        
        self.context.update(stage1.output or {})
        
        # IA decide estrategia
        ai_strategy = await self._ai_decide_strategy(self.context)
        self.context["ai_strategy"] = ai_strategy
        
        # Stage 2: Anti-Debug Bypass
        if options.get('anti_debug', True) and self.context.get('needs_anti_debug_bypass'):
            stage2 = await self._stage_anti_debug()
            self.stages.append(stage2)
            self.context.update(stage2.output or {})
        
        # Stage 3: Anti-Sandbox Bypass
        if options.get('anti_sandbox', True) and self.context.get('needs_anti_sandbox_bypass'):
            stage3 = await self._stage_anti_sandbox()
            self.stages.append(stage3)
            self.context.update(stage3.output or {})
        
        # Stage 4: Devirtualization
        if self.context.get('vm_type') and self.context['vm_type'] != 'unknown':
            stage4 = await self._stage_devirtualize()
            self.stages.append(stage4)
            self.context.update(stage4.output or {})
        
        # Stage 5: String Decryption
        stage5 = await self._stage_decrypt_strings()
        self.stages.append(stage5)
        self.context.update(stage5.output or {})
        
        # Stage 6: Pattern Matching
        stage6 = await self._stage_pattern_match()
        self.stages.append(stage6)
        self.context.update(stage6.output or {})
        
        # Stage 7: Go/Rust Analysis (se aplicavel)
        if self.context.get('language') in ('go', 'rust', 'go_rust_mixed'):
            stage7 = await self._stage_go_rust()
            self.stages.append(stage7)
            self.context.update(stage7.output or {})
        
        # Stage 8: Final AI Review
        stage8 = await self._stage_ai_review()
        self.stages.append(stage8)
        
        elapsed = time.time() - start_time
        
        return self._final_report(elapsed=elapsed)
    
    async def _stage_initial_analysis(self, target: str) -> PipelineStage:
        """Stage 1: Analise inicial."""
        start = time.time()
        try:
            # Import modulos
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            
            from pe_analyzer import PEAnalyzer
            from auto_unpacker import AutoUnpacker
            
            pe = PEAnalyzer()
            pe_result = pe.parse(target)
            
            unpacker = AutoUnpacker()
            unpack_result = await unpacker.analyze(target)
            
            duration_ms = int((time.time() - start) * 1000)
            
            return PipelineStage(
                name="initial_analysis",
                status="completed",
                input={"file": target},
                output={
                    "pe_info": pe_result,
                    "unpack_info": {
                        "packer": unpack_result.packer_detected,
                        "entropy": unpack_result.overall_entropy,
                        "needs_unpacking": unpack_result.overall_entropy > 7.0
                    },
                    "needs_anti_debug_bypass": any(
                        'IsDebugger' in i.get('name', '') or 
                        'debug' in i.get('name', '').lower()
                        for i in unpack_result.suspicious_indicators
                    ),
                    "vm_type": unpack_result.packer_detected,
                    "language": "unknown"  # sera detectado depois
                },
                duration_ms=duration_ms,
                ai_suggestion="Análise inicial completa. Próximo: verificar necessidade de bypass anti-debug."
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="initial_analysis",
                status="failed",
                input={"file": target},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=f"Erro na análise inicial: {e}"
            )
    
    async def _stage_anti_debug(self) -> PipelineStage:
        """Stage 2: Anti-debug bypass."""
        start = time.time()
        try:
            from anti_anti_debug import AntiAntiDebug
            
            analyzer = AntiAntiDebug()
            result = analyzer.analyze(self.context.get('target_file', ''))
            
            duration_ms = int((time.time() - start) * 1000)
            
            return PipelineStage(
                name="anti_debug_bypass",
                status="completed",
                input={"file": self.context.get('target_file')},
                output={
                    "indicators": result.get('indicators', []),
                    "bypass_available": result.get('bypass_available'),
                    "confidence": result.get('confidence', 0)
                },
                duration_ms=duration_ms,
                ai_suggestion=f"{len(result.get('indicators', []))} anti-debug indicators found. Patches generated."
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="anti_debug_bypass",
                status="failed",
                input={},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=str(e)
            )
    
    async def _stage_anti_sandbox(self) -> PipelineStage:
        """Stage 3: Anti-sandbox bypass."""
        start = time.time()
        try:
            from anti_sandbox_buster import AntiSandboxBuster
            
            buster = AntiSandboxBuster()
            result = await buster.analyze_environment()
            
            duration_ms = int((time.time() - start) * 1000)
            
            return PipelineStage(
                name="anti_sandbox_bypass",
                status="completed",
                input={},
                output={
                    "vm_detected": result.get('vm_detected'),
                    "sandbox_detected": result.get('sandbox_detected'),
                    "freshness_score": result.get('freshness_score'),
                    "bypass_recommendations": len(result.get('bypass_recommendations', []))
                },
                duration_ms=duration_ms,
                ai_suggestion="Environment analysis complete. Apply bypasses before execution."
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="anti_sandbox_bypass",
                status="failed",
                input={},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=str(e)
            )
    
    async def _stage_devirtualize(self) -> PipelineStage:
        """Stage 4: Devirtualization."""
        start = time.time()
        try:
            from devirtualizer import Devirtualizer
            
            devirt = Devirtualizer()
            analysis = devirt.analyze(self.context.get('target_file', ''))
            
            duration_ms = int((time.time() - start) * 1000)
            
            return PipelineStage(
                name="devirtualization",
                status="completed" if analysis.get('vm_type') != 'unknown' else "skipped",
                input={"file": self.context.get('target_file')},
                output=analysis,
                duration_ms=duration_ms,
                ai_suggestion=analysis.get('recommended_approach', 'No VM detected or manual analysis required.')
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="devirtualization",
                status="failed",
                input={},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=str(e)
            )
    
    async def _stage_decrypt_strings(self) -> PipelineStage:
        """Stage 5: String decryption."""
        start = time.time()
        try:
            from string_decryptor import StringDecryptor
            
            decryptor = StringDecryptor()
            result = decryptor.analyze(self.context.get('target_file', ''))
            
            duration_ms = int((time.time() - start) * 1000)
            
            return PipelineStage(
                name="string_decryption",
                status="completed",
                input={"file": self.context.get('target_file')},
                output={
                    "total_strings": result.get('total_strings'),
                    "encrypted_found": result.get('encrypted_strings_found'),
                    "decrypted_count": len(result.get('decrypted_strings', [])),
                    "crypto_functions": result.get('crypto_functions_detected', [])
                },
                duration_ms=duration_ms,
                ai_suggestion=f"Found {result.get('encrypted_strings_found', 0)} encrypted strings, decrypted {len(result.get('decrypted_strings', []))}."
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="string_decryption",
                status="failed",
                input={},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=str(e)
            )
    
    async def _stage_pattern_match(self) -> PipelineStage:
        """Stage 6: Pattern matching."""
        start = time.time()
        try:
            from pattern_matcher import PatternMatcher
            
            matcher = PatternMatcher()
            result = matcher.analyze(self.context.get('target_file', ''))
            
            duration_ms = int((time.time() - start) * 1000)
            
            return PipelineStage(
                name="pattern_matching",
                status="completed",
                input={"file": self.context.get('target_file')},
                output={
                    "obfuscation_level": result.get('obfuscation_level'),
                    "total_patterns": result.get('total_patterns'),
                    "patterns_found": list(result.get('patterns_found', {}).keys()),
                    "recommendations": result.get('recommendations', [])
                },
                duration_ms=duration_ms,
                ai_suggestion=f"Obfuscation level: {result.get('obfuscation_level')}. Patterns: {result.get('total_patterns')}."
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="pattern_matching",
                status="failed",
                input={},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=str(e)
            )
    
    async def _stage_go_rust(self) -> PipelineStage:
        """Stage 7: Go/Rust analysis."""
        start = time.time()
        try:
            from go_rust_analyzer import GoRustAnalyzer
            
            analyzer = GoRustAnalyzer()
            result = analyzer.analyze(self.context.get('target_file', ''))
            
            duration_ms = int((time.time() - start) * 1000)
            
            return PipelineStage(
                name="go_rust_analysis",
                status="completed",
                input={"file": self.context.get('target_file')},
                output={
                    "language": result.get('language'),
                    "function_count": result.get('function_count', 0),
                    "symbol_count": result.get('symbol_count', 0),
                    "recovery_feasibility": result.get('recovery_feasibility')
                },
                duration_ms=duration_ms,
                ai_suggestion=f"Detected {result.get('language')} binary with {result.get('function_count', 0)} functions."
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="go_rust_analysis",
                status="failed",
                input={},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=str(e)
            )
    
    async def _stage_ai_review(self) -> PipelineStage:
        """Stage 8: AI review e relatorio final."""
        start = time.time()
        try:
            ai_result = await self._call_llm(self._build_review_prompt())
            
            duration_ms = int((time.time() - start) * 1000)
            
            # Salva resultado IA
            review_path = self.output_dir / "ai_review.json"
            review_path.write_text(json.dumps(ai_result, indent=2))
            
            return PipelineStage(
                name="ai_review",
                status="completed",
                input=self.context,
                output={"ai_review": ai_result},
                duration_ms=duration_ms,
                ai_suggestion=None
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="ai_review",
                status="failed",
                input={},
                output=None,
                duration_ms=duration_ms,
                ai_suggestion=str(e)
            )
    
    async def _ai_decide_strategy(self, context: dict) -> dict:
        """IA decide estrategia baseada na analise inicial."""
        prompt = f"""Analise este binário e recomende a estratégia de engenharia reversa.

File: {context.get('target_file', 'unknown')}
PE Info: {json.dumps(context.get('pe_info', {}), default=str)[:500]}
Packer: {context.get('unpack_info', {}).get('packer', 'none')}
Entropy: {context.get('unpack_info', {}).get('entropy', 0):.4f}
Needs Unpacking: {context.get('unpack_info', {}).get('needs_unpacking', False)}
Needs Anti-Debug Bypass: {context.get('needs_anti_debug_bypass', False)}

Gere estratégia em JSON:
{{
  "priority": ["anti_debug", "unpacking", "devirtualization", ...],
  "reasoning": "...",
  "estimated_difficulty": "easy/medium/hard/expert",
  "expected_recovery": "full_source/partial_source/assembly_only"
}}"""
        
        return await self._call_llm(prompt, response_format="json")
    
    def _build_review_prompt(self) -> str:
        """Constrói prompt para review final."""
        return f"""Analise os resultados da engenharia reversa e gere um resumo executivo.

CONTEXT:
{json.dumps(self.context, default=str, indent=2)[:2000]}

STAGES COMPLETED:
{json.dumps([{'name': s.name, 'status': s.status, 'duration_ms': s.duration_ms} for s in self.stages], indent=2)}

Gere relatório em JSON:
{{
  "summary": "...",
  "key_findings": [...],
  "recommended_next_steps": [...],
  "confidence": 0-100,
  "source_recovery_estimate": "percent"
}}"""
    
    async def _call_llm(self, prompt: str, response_format: str = "text") -> any:
        """Chama LLM local."""
        import httpx
        
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 2048, "temperature": 0.3}
        }
        if response_format == "json":
            payload["format"] = "json"
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{self.llm_endpoint}/api/generate", json=payload)
                result = resp.json()
                response_text = result.get("response", "")
                
                if response_format == "json":
                    try:
                        import re
                        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        pass
                    return {"raw": response_text[:1000]}
                
                return response_text
        except Exception as e:
            return {"error": str(e), "fallback": True}
    
    def _final_report(self, elapsed: float = 0, error: str = None) -> dict:
        """Relatório final do pipeline."""
        return {
            "status": "completed" if error is None else "failed",
            "error": error,
            "elapsed_seconds": round(elapsed, 2),
            "stages_executed": len([s for s in self.stages if s.status == "completed"]),
            "total_stages": len(self.stages),
            "stages": [
                {
                    "name": s.name,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "ai_suggestion": s.ai_suggestion
                }
                for s in self.stages
            ],
            "context_summary": {k: v for k, v in self.context.items() 
                                if k not in ("raw_data", "pe_info")},
            "output_dir": str(self.output_dir)
        }


# Main entry point
async def run_advanced_re(target: str, options: dict = None) -> dict:
    """Função convenience para uso via toolkit."""
    orchestrator = AIOrchestrator()
    return await orchestrator.run_pipeline(target, options)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Orchestrated Advanced RE Pipeline")
    parser.add_argument("target", help="Binário para analisar")
    parser.add_argument("--output", "-o", default="./advanced_re_output")
    parser.add_argument("--model", "-m", default="codellama:13b")
    parser.add_argument("--no-anti-debug", action="store_true")
    parser.add_argument("--no-anti-sandbox", action="store_true")
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    
    async def main():
        options = {
            'anti_debug': not args.no_anti_debug,
            'anti_sandbox': not args.no_anti_sandbox
        }
        
        orchestrator = AIOrchestrator(
            llm_endpoint="http://localhost:11434",
            llm_model=args.model,
            output_dir=args.output
        )
        
        result = await orchestrator.run_pipeline(args.target, options)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*60}")
            print("ADVANCED RE PIPELINE RESULT")
            print(f"{'='*60}")
            print(f"Status: {result['status']}")
            print(f"Elapsed: {result['elapsed_seconds']}s")
            print(f"Stages: {result['stages_executed']}/{result['total_stages']} completed")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
            
            print(f"\nStages:")
            for s in result['stages']:
                icon = "✓" if s['status'] == 'completed' else "✗" if s['status'] == 'failed' else "○"
                print(f"  [{icon}] {s['name']}: {s['duration_ms']}ms")
                if s.get('ai_suggestion'):
                    print(f"      → {s['ai_suggestion'][:60]}")
            
            print(f"\nOutput: {result['output_dir']}")
    
    asyncio.run(main())
