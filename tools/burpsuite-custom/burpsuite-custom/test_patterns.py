"""Debug scanner patterns"""
import sys, re
sys.path.insert(0, '.')

from core.engine import VulnScanner

scanner = VulnScanner.__new__(VulnScanner)
patterns = scanner.VULN_PATTERNS

body = '<html><script>alert(1)</script></html>'
print(f"Body: {body}")
print()

for vuln_type, config in patterns.items():
    matched = False
    evidence = ''
    for pattern in config.get('patterns', []):
        try:
            m = re.search(pattern, body, re.IGNORECASE)
            if m:
                matched = True
                evidence = pattern
                print(f"{vuln_type}: MATCHED! pattern={pattern}, match={m.group()}")
                break
        except Exception as e:
            pass
    if not matched:
        print(f"{vuln_type}: no match")
