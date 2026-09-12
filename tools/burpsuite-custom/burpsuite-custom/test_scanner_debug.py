"""Debug scanner"""
import sys, os, tempfile
sys.path.insert(0, '.')

from core.engine import CustomBurp, HTTPMessage, LoggedRequest

tmpdb = tempfile.mktemp(suffix='.db')
burp = CustomBurp(db_path=tmpdb)
scanner = burp.scanner

# XSS test
req = HTTPMessage('GET', '/search?q=test', {'Host': 'example.com'})
resp = HTTPMessage('', '', {'Content-Type': 'text/html'}, b'<html><script>alert(1)</script></html>', status_code=200, status_text='OK')
resp.timestamp = req.timestamp + 0.1
log_req = LoggedRequest(request=req, response=resp, engine='test')
issues = scanner.scan_request(log_req)
print(f"XSS test - Issues: {len(issues)}")
for i in issues:
    print(f"  {i['type']}: {i['severity']}")

# SQLi test
req2 = HTTPMessage('GET', "/login?user=admin", {'Host': 'example.com'})
resp2 = HTTPMessage('', '', {'Content-Type': 'text/html'}, b"<html>Error: SQL syntax error in query</html>", status_code=200, status_text='OK')
resp2.timestamp = req2.timestamp + 0.1
log_req2 = LoggedRequest(request=req2, response=resp2, engine='test')
issues2 = scanner.scan_request(log_req2)
print(f"\nSQLi test - Issues: {len(issues2)}")
for i in issues2:
    print(f"  {i['type']}: {i['severity']}")

os.remove(tmpdb)
print("\nDone!")
