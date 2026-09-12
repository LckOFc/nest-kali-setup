"""Debug scan_request method"""
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

# Patch scan_request para debug
original_scan = scanner.scan_request

def debug_scan(log_req):
    issues = []
    resp = log_req.response
    
    print(f"VULN_PATTERNS keys: {list(scanner.VULN_PATTERNS.keys())}")
    
    for vuln_type, config in scanner.VULN_PATTERNS.items():
        matched = False
        evidence = ''
        
        body_text = resp.body.decode('utf-8', errors='replace') if resp.body else ''
        print(f"\nChecking {vuln_type}:")
        print(f"  body_text: {body_text[:50]}...")
        
        for pattern in config.get('patterns', []):
            try:
                m = re.search(pattern, body_text, re.IGNORECASE)
                if m:
                    matched = True
                    evidence = pattern
                    print(f"  MATCH: {pattern} -> {m.group()}")
                    break
                else:
                    print(f"  no match: {pattern}")
            except Exception as e:
                print(f"  error: {pattern} -> {e}")
        
        if matched:
            print(f"  => ISSUE FOUND: {vuln_type}")
            issue = {
                'type': vuln_type,
                'severity': config['severity'],
                'confidence': config.get('confidence', 'Medium'),
                'description': config['description'],
                'evidence': evidence,
                'solution': config.get('solution', ''),
                'request_id': log_req.request.id,
                'timestamp': __import__('time').time()
            }
            issues.append(issue)
            try:
                scanner.db.save_issue(
                    issue_type=vuln_type,
                    severity=config['severity'],
                    confidence=config.get('confidence', 'Medium'),
                    request_id=log_req.request.id,
                    description=config['description'],
                    evidence=evidence,
                    solution=config.get('solution', '')
                )
                print(f"  saved to DB")
            except Exception as e:
                print(f"  DB error: {e}")
    
    return issues

issues = debug_scan(log_req)
print(f"\nTotal issues: {len(issues)}")

os.remove(tmpdb)
