"""Debug scanner full flow"""
import sys, tempfile, os
sys.path.insert(0, '.')

from core.engine import CustomBurp, HTTPMessage, LoggedRequest

tmpdb = tempfile.mktemp(suffix='.db')
burp = CustomBurp(db_path=tmpdb)
scanner = burp.scanner

# XSS test - responder com script tag
req = HTTPMessage('GET', '/search?q=test', {'Host': 'example.com'})
resp_body = b'<html><script>alert(1)</script></html>'
resp = HTTPMessage('', '', {'Content-Type': 'text/html'}, resp_body, status_code=200, status_text='OK')
resp.timestamp = req.timestamp + 0.1

print(f"Request path: {req.path}")
print(f"Response body: {resp.body}")
print(f"Response headers: {resp.headers}")

log_req = LoggedRequest(request=req, response=resp, engine='test')
issues = scanner.scan_request(log_req)
print(f"\nIssues found: {len(issues)}")
for i in issues:
    print(f"  {i['type']}: {i['severity']} - evidence: {i['evidence'][:50]}")

os.remove(tmpdb)
