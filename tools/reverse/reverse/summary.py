"""Quick summary of analysis results"""
import json
import os

report_path = r'C:\Users\devel\tools\reverse\output\report.json'

if os.path.exists(report_path):
    with open(report_path) as f:
        data = json.load(f)
    
    print("=" * 60)
    print("  GO RE ENGINE - ANALYSIS RESULTS")
    print("=" * 60)
    print()
    print(f"  Strings found:     {data.get('strings', {}).get('total', 0):,}")
    print(f"  Functions found:   {data.get('functions', {}).get('total', 0)}")
    print(f"  Types recovered:   {data.get('types', {}).get('total', 0)}")
    print()
    
    print("  String Categories:")
    strings = data.get('strings', {})
    for k, v in strings.items():
        if isinstance(v, list):
            print(f"    {k}: {len(v)}")
    print()
    
    print("  Sample Functions:")
    for f in data.get('functions', {}).get('sample', [])[:15]:
        print(f"    {f.get('addr')}: {f.get('name')} ({f.get('instructions', 0)} insns)")
    print()
    
    print("  PE Information:")
    pe = data.get('pe', {})
    print(f"    Machine: {pe.get('machine')}")
    print(f"    Entry: {pe.get('entry_point')}")
    print(f"    Sections: {len(pe.get('sections', []))}")
    print()
    
    print("=" * 60)
    print("  OUTPUT FILES:")
    print("=" * 60)
    output_dir = r'C:\Users\devel\tools\reverse\output'
    for f in os.listdir(output_dir):
        fp = os.path.join(output_dir, f)
        print(f"    {f} ({os.path.getsize(fp):,} bytes)")
else:
    print("Report not found!")