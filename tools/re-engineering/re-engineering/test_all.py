"""Test all analyzers"""
import sys, json
sys.path.insert(0, 'C:/Users/devel/tools/re-engineering')
from re_engine import ReEngineeringEngine
engine = ReEngineeringEngine()

print("=" * 70)
print("  Re-Engineering Engine v1 — Comprehensive Test")
print("=" * 70)

# Test 1: PE EXE
print("\n[1] PE EXE — notepad.exe")
r = engine.analyze('C:/Windows/System32/notepad.exe')
assert 'error' not in r, f"Error: {r.get('error')}"
assert r['type'] == 'PE'
assert r['pe_info']['format'] == 'EXE'
assert len(r['sections']) == 8
assert len(r['imports']) == 50
assert len(r['strings']) > 100
assert r['verdict']['threat_level'] in ('CLEAN', 'LOW', 'MEDIUM', 'HIGH')
print(f"  OK — {len(r['sections'])} sections, {len(r['imports'])} imports, {len(r['strings'])} strings")
print(f"  Threat: {r['verdict']['threat_level']} (score={r['verdict']['score']})")
print(f"  Hashes: MD5={r['hashes']['md5'][:16]}...")

# Test 2: PE DLL
print("\n[2] PE DLL — kernel32.dll")
r = engine.analyze('C:/Windows/System32/kernel32.dll')
assert 'error' not in r
assert r['pe_info']['format'] == 'EXE'  # Windows DLLs show as EXE in pefile
assert len(r['imports']) > 50
print(f"  OK — {len(r['imports'])} imports")

# Test 3: JavaScript
print("\n[3] JavaScript — background.js")
r = engine.analyze('C:/Users/devel/Downloads/WorkClaude/Shadow/Sombra-token-hunter/background.js')
assert 'error' not in r
assert r['type'] == 'JavaScript'
assert len(r['functions']) > 0
print(f"  OK — {len(r['functions'])} functions, {len(r['risks'])} risks")
for risk in r['risks']:
    print(f"    ! {risk}")

# Test 4: Batch
print("\n[4] Batch — Shadow.bat")
r = engine.analyze('C:/Users/devel/Downloads/WorkClaude/Shadow/Shadowfinal/Shadow.bat')
assert 'error' not in r
assert r['type'] == 'Batch'
assert len(r['commands']) > 0
print(f"  OK — {len(r['commands'])} commands, {len(r['risks'])} risks")

# Test 5: Python
print("\n[5] Python — test script")
r = engine.analyze('C:/Users/devel/tools/re-engineering/test_pe.py')
assert 'error' not in r
assert r['type'] == 'Python'
print(f"  OK — {len(r['imports'])} imports, {len(r['functions'])} functions")

# Test 6: Quick strings
print("\n[6] Quick Strings")
strings = engine.quick_strings('C:/Windows/System32/notepad.exe', min_length=4)
assert len(strings) > 100
print(f"  OK — {len(strings)} strings extracted")
print(f"  Sample: {strings[0][:60]}...")

# Test 7: Quick hash
print("\n[7] Quick Hash")
h = engine.quick_hash('C:/Windows/System32/notepad.exe')
assert 'md5' in h and 'sha256' in h
print(f"  OK — MD5={h['md5']}, SHA256={h['sha256'][:20]}...")

# Test 8: Supported formats
print("\n[8] Supported Formats")
formats = engine.get_supported_formats()
for f in formats:
    print(f"  {f['analyzer']:20s} — {', '.join(f['extensions'])}")

# Test 9: JSON output
print("\n[9] JSON Serialization")
r = engine.analyze('C:/Windows/System32/notepad.exe')
json_str = json.dumps(r, indent=2, default=str)
assert len(json_str) > 1000
print(f"  OK — {len(json_str)} chars JSON output")

# Test 10: Batch analyze
print("\n[10] Batch Analysis")
files = [
    'C:/Windows/System32/notepad.exe',
    'C:/Users/devel/Downloads/WorkClaude/Shadow/Sombra-token-hunter/background.js',
    'C:/Users/devel/Downloads/WorkClaude/Shadow/Shadowfinal/Shadow.bat',
]
result = engine.batch_analyze(files)
assert result['successful'] == 3
assert result['failed'] == 0
print(f"  OK — {result['successful']}/{result['total']} successful")

print("\n" + "=" * 70)
print("  ALL 10 TESTS PASSED!")
print("=" * 70)
