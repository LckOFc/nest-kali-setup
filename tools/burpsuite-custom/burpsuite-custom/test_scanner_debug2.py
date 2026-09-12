"""Debug scanner patterns in context"""
import sys, re, json, tempfile, os
sys.path.insert(0, '.')

from core.engine import CustomBurp, HTTPMessage, LoggedRequest

tmpdb = tempfile.mktemp(suffix='.db')
burp = CustomBurp(db_path=tmpdb)
scanner = burp.scanner

req = HTTPMessage('GET', '/search?q=test', {'Host': 'example.com'})
resp_body = b'<html><script>alert(1)</script></html>'
resp = HTTPMessage('', '', {'Content-Type': 'text/html'}, resp_body, status_code=200, status_text='OK')
resp.timestamp = req.timestamp + 0.1

log_req = LoggedRequest(request=req, response=resp, engine='test')
resp = log_req.response

print(f"resp.body type: {type(resp.body)}")
print(f"resp.body value: {resp.body}")
print(f"resp.body bool: {bool(resp.body)}")

body_text = resp.body.decode('utf-8', errors='replace') if resp.body else ''
print(f"body_text: {body_text}")

# Testar cada pattern do XSS
config = scanner.VULN_PATTERNS['XSS_Reflected']
print(f"\nXSS patterns: {config['patterns']}")
for pattern in config['patterns']:
    try:
        m = re.search(pattern, body_text, re.IGNORECASE)
        print(f"  {pattern}: {m}")
    except Exception as e:
        print(f"  {pattern}: ERROR {e}")

# Agora testar o scan_request completo
print("\n--- Calling scan_request ---")
issues = scanner.scan_request(log_req)
print(f"Issues: {len(issues)}")
for i in issues:
    print(f"  {i['type']}: {i['severity']}")

os.remove(tmpdb)
