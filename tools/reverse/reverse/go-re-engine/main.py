"""
Go Reverse Engineering Toolkit - Entry Point
============================================
Uso: python main.py <binary.exe> [--output output_dir] [--dashboard]
"""

import sys
import os
import argparse
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import GoREEngine

def main():
    parser = argparse.ArgumentParser(
        description='Go Reverse Engineering Toolkit v1.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py agy.exe
  python main.py agy.exe --output ./results
  python main.py agy.exe --dashboard
  python main.py agy.exe --functions-only
        """
    )
    
    parser.add_argument('binary', help='Caminho para o binário Go (.exe)')
    parser.add_argument('--output', '-o', default=None, help='Diretório de saída')
    parser.add_argument('--dashboard', '-d', action='store_true', help='Abrir dashboard web')
    parser.add_argument('--functions-only', action='store_true', help='Apenas analisar funções')
    parser.add_argument('--strings-only', action='store_true', help='Apenas analisar strings')
    parser.add_argument('--json', action='store_true', help='Output em JSON')
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.binary):
        print(f"ERROR: Binary not found: {args.binary}")
        sys.exit(1)
    
    # Setup output directory
    output_dir = args.output or os.path.join(os.path.dirname(args.binary), 're_output')
    
    print("=" * 70)
    print("  GO RE ENGINE v1.0 - Reverse Engineering Toolkit")
    print("=" * 70)
    print(f"\n  Binary:   {args.binary}")
    print(f"  Output:   {output_dir}")
    print(f"  Size:     {os.path.getsize(args.binary):,} bytes")
    print()
    
    # Create engine
    engine = GoREEngine(args.binary)
    
    # Run analysis
    if args.functions_only:
        engine.initialize()
        engine.analyze_functions()
        engine.generate_report(output_dir)
    elif args.strings_only:
        engine.initialize()
        engine.analyze_strings()
        engine.generate_report(output_dir)
    else:
        engine.run_full_analysis(output_dir)
    
    # Open dashboard if requested
    if args.dashboard:
        from dashboard import load_analysis, app
        report_path = os.path.join(output_dir, 'analysis_report.json')
        load_analysis(report_path)
        print(f"\n[*] Starting dashboard at http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    
    print("\n" + "=" * 70)
    print("  ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\n  Results saved to: {output_dir}/")
    print("    - analysis_report.json")
    print("    - strings.json")
    print("    - functions.json")
    print()

if __name__ == '__main__':
    main()