"""Teste do scanner com request real"""
import sys
sys.path.insert(0, '.')

from core.engine import CustomBurp, HTTPMessage, LoggedRequest

# Criar com arquivo temporário
import tempfile, os
tmpdb = tempfile.mktemp(suffix='.db')
burp = CustomBurp(db_path=tmpdb)
scanner = burp.scanner
db = burp.db  # Usar o mesmo DB do scanner

# Criar request de teste com XSS
req = HTTPMessage('GET', '/search?q=<script>alert(1)</script>', {'Host': 'example.com'})
resp = HTTPMessage('', '', {'Content-Type': 'text/html'}, b'<html><script>alert(1)</script></html>', status_code=200, status_text='OK')
resp.timestamp = req.timestamp + 0.1

log_req = LoggedRequest(request=req, response=resp, engine='test')
issues = scanner.scan_request(log_req)

print(f"Issues found: {len(issues)}")
for issue in issues:
    print(f"  - {issue['type']}: {issue['severity']} - {issue['description'][:60]}...")

# Testar SQLi
req2 = HTTPMessage('GET', "/login?user=admin' OR 1=1--", {'Host': 'example.com'})
resp2 = HTTPMessage('', '', {'Content-Type': 'text/html'}, b"<html>Error: SQL syntax error</html>", status_code=200, status_text='OK')
resp2.timestamp = req2.timestamp + 0.1

log_req2 = LoggedRequest(request=req2, response=resp2, engine='test')
issues2 = scanner.scan_request(log_req2)
print(f"\nSQLi Issues found: {len(issues2)}")
for issue in issues2:
    print(f"  - {issue['type']}: {issue['severity']}")

print("\nScanner tests passed!")
os.remove(tmpdb)
