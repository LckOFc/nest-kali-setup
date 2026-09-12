"""
advanced_re.py
Main entry point for Advanced RE Suite
"""
import asyncio
import json
import sys
from pathlib import Path

# Add modules path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from ai_orchestrator import AIOrchestrator

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced RE Suite — Binários Protegidos & Anti-Análise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python advanced_re.py malware.exe --full
  python advanced_re.py malware.exe --anti-debug
  python advanced_re.py malware.exe --devirtualize
  python advanced_re.py malware.exe --go-rust
  python advanced_re.py malware.exe --ai-pipeline
        """
    )
    
    parser.add_argument("target", help="Binário para analisar")
    parser.add_argument("--full", "-f", action="store_true", help="Pipeline completo com IA")
    parser.add_argument("--anti-debug", "-d", action="store_true", help="Somente anti-debug analysis")
    parser.add_argument("--devirtualize", action="store_true", help="Somente devirtualization analysis")
    parser.add_argument("--go-rust", action="store_true", help="Somente Go/Rust analysis")
    parser.add_argument("--strings", "-s", action="store_true", help="Somente string decryption")
    parser.add_argument("--patterns", "-p", action="store_true", help="Somente pattern matching")
    parser.add_argument("--sandbox", action="store_true", help="Analisar ambiente (anti-sandbox)")
    parser.add_argument("--output", "-o", default="./advanced_re_output")
    parser.add_argument("--model", "-m", default="codellama:13b", help="LLM model (Ollama)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    parser.add_argument("--list-modules", action="store_true", help="Listar módulos disponíveis")
    
    args = parser.parse_args()
    
    if args.list_modules:
        print("Available modules:")
        modules = [
            ("AntiAntiDebug", "anti_anti_debug.py", "Detecção e bypass de anti-debug"),
            ("Devirtualizer", "devirtualizer.py", "VMProtect/Themida devirtualization"),
            ("AntiSandboxBuster", "anti_sandbox_buster.py", "Detecção e bypass de sandbox"),
            ("GoRustAnalyzer", "go_rust_analyzer.py", "Análise especializada Go/Rust"),
            ("StringDecryptor", "string_decryptor.py", "Descriptografia de strings"),
            ("PatternMatcher", "pattern_matcher.py", "Matching de padrões ofuscados"),
            ("AIOrchestrator", "ai_orchestrator.py", "Orquestrador IA"),
        ]
        for name, file, desc in modules:
            print(f"  {name:25s} ({file:25s}) - {desc}")
        return
    
    async def run():
        if args.full or args.target:
            # Pipeline completo
            orchestrator = AIOrchestrator(
                llm_endpoint="http://localhost:11434",
                llm_model=args.model,
                output_dir=args.output
            )
            
            options = {
                'anti_debug': not args.no_anti_debug if hasattr(args, 'no_anti_debug') else True,
                'anti_sandbox': not args.no_anti_sandbox if hasattr(args, 'no_anti_sandbox') else True
            }
            
            result = await orchestrator.run_pipeline(args.target, options)
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"\n{'='*60}")
                print("ADVANCED RE SUITE — RESULTADO")
                print(f"{'='*60}")
                print(f"Target: {args.target}")
                print(f"Status: {result.get('status', 'unknown')}")
                print(f"Elapsed: {result.get('elapsed_seconds', 0):.1f}s")
                print(f"Stages: {result.get('stages_executed', 0)}/{result.get('total_stages', 0)} completed")
                print(f"Output: {result.get('output_dir', 'N/A')}")
                
                if result.get('error'):
                    print(f"\n❌ Error: {result['error']}")
                
                print(f"\nStage Details:")
                for s in result.get('stages', []):
                    icon = "✓" if s['status'] == 'completed' else "✗" if s['status'] == 'failed' else "○"
                    print(f"  [{icon}] {s['name']:30s} {s['duration_ms']}ms")
                    if s.get('ai_suggestion'):
                        print(f"       └─ {s['ai_suggestion'][:70]}")
                
                # Resumo do contexto
                ctx = result.get('context_summary', {})
                if ctx:
                    print(f"\nKey Findings:")
                    if ctx.get('vm_type') and ctx['vm_type'] != 'unknown':
                        print(f"  VM Type: {ctx['vm_type']}")
                    if ctx.get('packer'):
                        print(f"  Packer: {ctx['packer']}")
                    if ctx.get('language'):
                        print(f"  Language: {ctx['language']}")
                    if ctx.get('ai_strategy'):
                        print(f"  AI Strategy: {json.dumps(ctx['ai_strategy'], default=str)[:100]}...")
        
        # Módulos específicos
        if args.anti_debug:
            from anti_anti_debug import AntiAntiDebug
            analyzer = AntiAntiDebug()
            result = analyzer.analyze(args.target)
            print(json.dumps(result, indent=2, default=str) if args.json else print_analysis(result))
        
        if args.devirtualize:
            from devirtualizer import Devirtualizer
            devirt = Devirtualizer()
            result = devirt.analyze(args.target)
            print(json.dumps(result, indent=2, default=str) if args.json else print_devirt(result))
        
        if args.go_rust:
            from go_rust_analyzer import GoRustAnalyzer
            analyzer = GoRustAnalyzer()
            result = analyzer.analyze(args.target)
            print(json.dumps(result, indent=2, default=str) if args.json else print_go_rust(result))
        
        if args.strings:
            from string_decryptor import StringDecryptor
            decryptor = StringDecryptor()
            result = decryptor.analyze(args.target)
            print(json.dumps(result, indent=2, default=str) if args.json else print_strings(result))
        
        if args.patterns:
            from pattern_matcher import PatternMatcher
            matcher = PatternMatcher()
            result = matcher.analyze(args.target)
            print(json.dumps(result, indent=2, default=str) if args.json else print_patterns(result))
    
    asyncio.run(run())

def print_analysis(result):
    print(f"File: {result['file']}")
    print(f"SHA256: {result['sha256']}")
    print(f"Indicators: {result['indicator_count']}")
    print(f"Severity: {result['severity_distribution']}")
    print(f"Confidence: {result['confidence']:.0%}")

def print_devirt(result):
    print(f"File: {result['file']}")
    print(f"VM Type: {result['vm_type']}")
    print(f"Confidence: {result['vm_confidence']:.0%}")
    print(f"Recommended: {result['recommended_approach']}")

def print_go_rust(result):
    print(f"File: {result['file']}")
    print(f"Language: {result['language']}")
    print(f"Recovery: {result['recovery_feasibility']}")

def print_strings(result):
    print(f"File: {result['file']}")
    print(f"Total strings: {result['total_strings']}")
    print(f"Encrypted: {result['encrypted_strings_found']}")
    print(f"Decrypted: {len(result['decrypted_strings'])}")

def print_patterns(result):
    print(f"File: {result['file']}")
    print(f"Obfuscation Level: {result['obfuscation_level']}")
    print(f"Patterns: {result['total_patterns']}")

if __name__ == "__main__":
    main()
