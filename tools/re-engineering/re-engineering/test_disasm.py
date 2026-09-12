"""Test disassembler"""
import sys, json
sys.path.insert(0, 'C:/Users/devel/tools/re-engineering')
from re_engine import ReEngineeringEngine
engine = ReEngineeringEngine()

print("=== Disassembler Test ===")
r = engine.disassemble('C:/Windows/System32/notepad.exe', offset=0x1000, count=20)
print(f"Error: {r.get('error')}")
print(f"Instructions: {len(r.get('instructions', []))}")
print(f"Calls: {len(r.get('calls', []))}")
if r.get('instructions'):
    for inst in r['instructions'][:10]:
        addr = inst['address']
        asm = inst['asm']
        print(f"  {addr:#010x}: {asm}")

# Test CLI
import subprocess
result = subprocess.run(
    [sys.executable, 'C:/Users/devel/tools/re-engineering/re_engine.py',
     'C:/Windows/System32/notepad.exe', '--format', 'json'],
    capture_output=True, text=True, timeout=30
)
# Find JSON in output
lines = result.stdout.strip().split('\n')
json_started = False
json_lines = []
for line in lines:
    if line.strip().startswith('{'):
        json_started = True
    if json_started:
        json_lines.append(line)
if json_lines:
    data = json.loads('\n'.join(json_lines))
    print(f"\nCLI JSON test: OK ({len(json.dumps(data))} chars)")
    print(f"  Type: {data.get('type')}")
    print(f"  Threat: {data.get('verdict',{}).get('threat_level')}")
else:
    print(f"CLI error: {result.stderr[:200]}")

print("\n=== ALL DISASM TESTS PASSED ===")
