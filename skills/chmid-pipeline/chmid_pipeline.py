"""
chmid_pipeline.py
Chain-Heuristic-Multiple-Iteration-Debug Pipeline
Orquestra analise completa de binarios com todas as etapas automatizadas.
"""
import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class PipelineStage:
    name: str
    input_path: str
    output_path: Optional[str]
    duration_ms: int
    success: bool
    error: Optional[str] = None
    result_summary: Optional[dict] = None

class CHMIDPipeline:
    """
    Chain-Heuristic-Multiple-Iteration-Debug Pipeline
    
    Encadeia automaticamente:
    1. Initial Analysis (RE Toolkit)
    2. Packer Detection (Auto-Unpacker)
    3. Unpacking (se necessario)
    4. Re-analysis (pos-unpack)
    5. Fuzzy Comparison (contra baseline)
    6. Behavioral Sandbox
    7. Report Generation
    """
    
    def __init__(self, 
                 baseline_dir: str = None,
                 output_dir: str = "./pipeline_output",
                 fast_mode: bool = False,
                 save_intermediate: bool = False):
        self.baseline_dir = baseline_dir
        self.output_dir = Path(output_dir)
        self.fast_mode = fast_mode
        self.save_intermediate = save_intermediate
        self.stages: list[PipelineStage] = []
        self.context: dict = {}
    
    async def run(self, target: str) -> dict:
        """Executa pipeline completo."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        start_time = time.time()
        
        print(f"[CHMID] Iniciando pipeline para: {target}")
        
        # Estágio 1: Initial Analysis
        stage1 = await self._stage_initial_analysis(target)
        self.stages.append(stage1)
        if not stage1.success:
            return self._final_report(error=f"Stage 1 failed: {stage1.error}")
        
        self.context.update(stage1.result_summary or {})
        self._save_stage_output(1, stage1.result_summary)
        
        # Estágio 2: Packer Detection
        stage2 = await self._stage_packer_detection(target, self.context)
        self.stages.append(stage2)
        self.context.update(stage2.result_summary or {})
        self._save_stage_output(2, stage2.result_summary)
        
        # Estágio 3: Unpacking (se necessario)
        unpacked_target = target
        needs_unpack = stage2.result_summary.get("needs_unpacking", False)
        
        if needs_unpack:
            stage3 = await self._stage_unpacking(target, stage2.result_summary.get("strategy", ""))
            self.stages.append(stage3)
            self.context.update(stage3.result_summary or {})
            self._save_stage_output(3, stage3.result_summary)
            
            if stage3.success and stage3.output_path:
                unpacked_target = stage3.output_path
                self.context["unpacked_path"] = unpacked_target
        else:
            self.context["skipped_unpacking"] = True
        
        # Estágio 4: Re-analysis
        stage4 = await self._stage_reanalysis(unpacked_target, self.context)
        self.stages.append(stage4)
        self.context.update(stage4.result_summary or {})
        self._save_stage_output(4, stage4.result_summary)
        
        # Estágio 5: Fuzzy Comparison (se baseline configurado)
        if self.baseline_dir:
            stage5 = await self._stage_fuzzy_comparison(unpacked_target, self.baseline_dir)
            self.stages.append(stage5)
            self.context.update(stage5.result_summary or {})
            self._save_stage_output(5, stage5.result_summary)
        else:
            self.context["skipped_fuzzy_compare"] = True
        
        # Estágio 6: Behavioral Sandbox (se não fast_mode)
        if not self.fast_mode:
            stage6 = await self._stage_sandbox(unpacked_target)
            self.stages.append(stage6)
            self.context.update(stage6.result_summary or {})
            self._save_stage_output(6, stage6.result_summary)
        else:
            self.context["skipped_sandbox"] = True
        
        # Estágio 7: Report Generation
        stage7 = await self._stage_report_generation(self.context)
        self.stages.append(stage7)
        self._save_stage_output(7, stage7.result_summary)
        
        elapsed = time.time() - start_time
        
        return self._final_report(elapsed=elapsed)
    
    async def _stage_initial_analysis(self, target: str) -> PipelineStage:
        """Estágio 1: Analise inicial com RE Toolkit."""
        start = time.time()
        try:
            # Importa do RE Toolkit existente
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools" / "re-engineering"))
            from re_engine import ReEngineeringEngine
            
            engine = ReEngineeringEngine()
            result = engine.analyze(target)
            
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="initial_analysis",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=True,
                result_summary={
                    "pe_info": result.get("pe_info", {}),
                    "imports": [imp.get("name", "") for imp in result.get("imports", [])],
                    "strings_count": len(result.get("strings", [])),
                    "hashes": result.get("hashes", {}),
                    "risks": result.get("risks", [])
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="initial_analysis",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    async def _stage_packer_detection(self, target: str, ctx: dict) -> PipelineStage:
        """Estágio 2: Detecção de packer."""
        start = time.time()
        try:
            from auto_unpacker import AutoUnpacker
            unpacker = AutoUnpacker()
            result = await unpacker.analyze(target)
            
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="packer_detection",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=True,
                result_summary={
                    "packer": result.packer_detected,
                    "confidence": result.packer_confidence,
                    "entropy": result.overall_entropy,
                    "needs_unpacking": result.overall_entropy > 7.0 and result.packer_detected != "native",
                    "strategy": result.recommended_strategy,
                    "indicators": result.suspicious_indicators
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="packer_detection",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    async def _stage_unpacking(self, target: str, strategy: str) -> PipelineStage:
        """Estágio 3: Unpacking."""
        start = time.time()
        try:
            from auto_unpacker import AutoUnpacker
            unpacker = AutoUnpacker()
            result = await unpacker.try_unpack(target, str(self.output_dir / "unpacked"))
            
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="unpacking",
                input_path=target,
                output_path=result.unpacked_path,
                duration_ms=duration_ms,
                success=result.unpack_success,
                result_summary={
                    "packer": result.packer_detected,
                    "success": result.unpack_success,
                    "output": result.unpacked_path,
                    "entropy_before": result.overall_entropy
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="unpacking",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    async def _stage_reanalysis(self, target: str, ctx: dict) -> PipelineStage:
        """Estágio 4: Re-análise pós-unpack."""
        start = time.time()
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools" / "re-engineering"))
            from re_engine import ReEngineeringEngine
            
            engine = ReEngineeringEngine()
            result = engine.analyze(target)
            
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="reanalysis",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=True,
                result_summary={
                    "post_unpack_entropy": result.get("pe_info", {}).get("entropy", 0),
                    "new_strings_found": len(result.get("strings", [])),
                    "sections_analyzed": len(result.get("sections", []))
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="reanalysis",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    async def _stage_fuzzy_comparison(self, target: str, baseline_dir: str) -> PipelineStage:
        """Estágio 5: Comparação fuzzy."""
        start = time.time()
        try:
            from fuzzy_hash import FuzzyHashEngine
            engine = FuzzyHashEngine()
            
            # Encontra samples de baseline
            import glob
            baseline_files = glob.glob(f"{baseline_dir}/**/*.exe", recursive=True)
            
            if not baseline_files:
                return PipelineStage(
                    name="fuzzy_comparison",
                    input_path=target,
                    output_path=None,
                    duration_ms=0,
                    success=False,
                    error="No baseline samples found"
                )
            
            results = engine.batch_compare([target] + baseline_files[:10], threshold=40)
            
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="fuzzy_comparison",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=True,
                result_summary={
                    "similar_pairs": [
                        {"file_b": r.file_b, "similarity": r.similarity, "verdict": r.verdict}
                        for r in results if r.file_a == target
                    ],
                    "total_compared": len(baseline_files[:10])
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="fuzzy_comparison",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    async def _stage_sandbox(self, target: str) -> PipelineStage:
        """Estágio 6: Sandbox comportamental."""
        start = time.time()
        try:
            from behavioral_sandbox import BehavioralSandbox
            sandbox = BehavioralSandbox(timeout_seconds=30)
            result = await sandbox.run(target)
            
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="behavioral_sandbox",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=True,
                result_summary={
                    "threat_score": result["threat_score"],
                    "threat_level": result["threat_level"],
                    "events_count": result["events_count"],
                    "summary": result["summary"]
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="behavioral_sandbox",
                input_path=target,
                output_path=None,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    async def _stage_report_generation(self, context: dict) -> PipelineStage:
        """Estágio 7: Geração de relatório."""
        start = time.time()
        try:
            import hashlib
            report_data = {
                "pipeline_version": "1.0",
                "generated_at": asyncio.get_event_loop().time(),
                "target_file": context.get("target", "unknown"),
                "sha256": context.get("sha256", ""),
                "stages_completed": len([s for s in self.stages if s.success]),
                "total_stages": len(self.stages),
                "context": {k: v for k, v in context.items() if k not in ("raw_pe", "strings")}
            }
            
            output_path = self.output_dir / "report_final.json"
            output_path.write_text(json.dumps(report_data, indent=2))
            
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="report_generation",
                input_path=str(self.output_dir),
                output_path=str(output_path),
                duration_ms=duration_ms,
                success=True,
                result_summary={"report_path": str(output_path)}
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return PipelineStage(
                name="report_generation",
                input_path=str(self.output_dir),
                output_path=None,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    def _save_stage_output(self, stage_num: int, data: dict):
        """Salva saida intermediaria se configurado."""
        if not self.save_intermediate or not data:
            return
        path = self.output_dir / f"stage_{stage_num}.json"
        path.write_text(json.dumps(data, indent=2))
    
    def _final_report(self, elapsed: float = 0, error: str = None) -> dict:
        """Relatório final do pipeline."""
        return {
            "status": "completed" if error is None else "failed",
            "error": error,
            "elapsed_seconds": round(elapsed, 2),
            "stages_executed": len(self.stages),
            "stages": [
                {
                    "name": s.name,
                    "success": s.success,
                    "duration_ms": s.duration_ms,
                    "error": s.error
                }
                for s in self.stages
            ],
            "context_summary": {
                k: v for k, v in self.context.items()
                if k not in ("raw_pe", "strings", "pe_info")
            }
        }


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CHMID Pipeline")
    parser.add_argument("target", help="Binário para analisar")
    parser.add_argument("--baseline", "-b", help="Diretorio de baseline para comparacao fuzzy")
    parser.add_argument("--output", "-o", default="./pipeline_output", help="Diretorio de saida")
    parser.add_argument("--fast", "-f", action="store_true", help="Pula sandbox comportamental")
    parser.add_argument("--save-stages", action="store_true", help="Salva resultados intermediarios")
    parser.add_argument("--json", "-j", action="store_true", help="Output em JSON")
    args = parser.parse_args()
    
    async def main():
        pipeline = CHMIDPipeline(
            baseline_dir=args.baseline,
            output_dir=args.output,
            fast_mode=args.fast,
            save_intermediate=args.save_stages
        )
        
        result = await pipeline.run(args.target)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*60}")
            print("CHMID PIPELINE RESULT")
            print(f"{'='*60}")
            print(f"Status: {result['status']}")
            print(f"Elapsed: {result['elapsed_seconds']}s")
            print(f"Stages: {result['stages_executed']}/{len(result['stages'])} completed")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
            
            print(f"\nStages Detail:")
            for s in result['stages']:
                status = "✓" if s['success'] else "✗"
                print(f"  [{status}] {s['name']}: {s['duration_ms']}ms" + (f" - {s['error']}" if s['error'] else ""))
            
            print(f"\nKey Findings:")
            ctx = result.get('context_summary', {})
            if ctx.get('packer'):
                print(f"  Packer: {ctx['packer']}")
            if ctx.get('sha256'):
                print(f"  SHA256: {ctx['sha256']}")
            if ctx.get('unpacked_path'):
                print(f"  Unpacked: {ctx['unpacked_path']}")
    
    asyncio.run(main())
