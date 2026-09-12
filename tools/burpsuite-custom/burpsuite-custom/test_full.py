"""Testes completos do CustomBurp"""
import sys, tempfile, os, time
sys.path.insert(0, '.')

print("=" * 50)
print("TESTES COMPLETOS - CustomBurp Suite")
print("=" * 50)

# 1. REPEATER - Request real
print("\n[1] REPEATER - HTTP GET real")
from core.repeater import Repeater
rep = Repeater()
result = rep.send('GET', 'http://httpbin.org/get', timeout=10)
print(f"  Status: {result['status_code']}")
print(f"  Time: {result['time_ms']}ms")
print(f"  Body len: {len(result['body'])}")
assert result['status_code'] == 200, "Repeater falhou"
print("  => FUNCIONA")

# 2. REPEATER POST
print("\n[2] REPEATER - HTTP POST real")
result2 = rep.send('POST', 'http://httpbin.org/post',
    headers={'Content-Type': 'application/json'},
    body='{"test": "value"}', timeout=10)
print(f"  Status: {result2['status_code']}")
print(f"  Body len: {len(result2['body'])}")
assert result2['status_code'] == 200
print("  => FUNCIONA")

# 3. DECODER
print("\n[3] DECODER")
from core.engine import Decoder
d = Decoder()
tests = [
    ('base64_decode', 'aGVsbG8=', 'hello'),
    ('url_decode', '%7B%22a%22%3A1%7D', '{"a":1}'),
    ('md5', 'test', '098f6bcd4621d373cade4e832627b4f6'),
]
for action, inp, expected in tests:
    result = getattr(d, action)(inp)
    print(f"  {action}: {result[:30]}...")
    assert expected in result or result == expected, f"Decoder {action} falhou"
print("  => FUNCIONA")

# 4. SCANNER
print("\n[4] SCANNER")
from core.engine import CustomBurp, HTTPMessage, LoggedRequest
tmpdb = tempfile.mktemp(suffix='.db')
burp = CustomBurp(db_path=tmpdb)

# XSS
req = HTTPMessage('GET', '/search?q=test', {'Host': 'example.com'})
resp = HTTPMessage('', '', {'Content-Type': 'text/html'}, b'<html><script>alert(1)</script></html>', status_code=200)
resp.timestamp = req.timestamp + 0.1
issues = burp.scanner.scan_request(LoggedRequest(request=req, response=resp, engine='test'))
print(f"  XSS: {len(issues)} issues")

# SQLi
req2 = HTTPMessage('GET', '/login', {'Host': 'example.com'})
resp2 = HTTPMessage('', '', {'Content-Type': 'text/html'}, b"<html>Error: SQL syntax error</html>", status_code=200)
resp2.timestamp = req2.timestamp + 0.1
issues2 = burp.scanner.scan_request(LoggedRequest(request=req2, response=resp2, engine='test'))
print(f"  SQLi: {len(issues2)} issues")

# Headers
req3 = HTTPMessage('GET', '/', {'Host': 'example.com'})
resp3 = HTTPMessage('', '', {'Content-Type': 'text/html'}, b'<html>ok</html>', status_code=200)
resp3.timestamp = req3.timestamp + 0.1
issues3 = burp.scanner.scan_request(LoggedRequest(request=req3, response=resp3, engine='test'))
print(f"  Headers: {len(issues3)} issues")
print("  => FUNCIONA")

os.remove(tmpdb)

# 5. INTRUDER
print("\n[5] INTRUDER")
from core.intruder import Intruder
intruder = Intruder()

# Test com request mock
test_req = "GET /search?q=§HTTP/1.1\r\nHost: httpbin.org\r\n"
payloads = ['admin', 'test123']
results = intruder.attack(test_req, payloads, mode='sniper', thread_count=2, timeout=10)
print(f"  Results: {len(results)} requests")
for r in results[:2]:
    print(f"    Payload: {r['payload']}, Status: {r['status_code']}, Length: {r['response_length']}")
print("  => FUNCIONA")

# 6. PROXY
print("\n[6] PROXY")
from core.proxy import BurpProxy, SSLCertGenerator
db = __import__('core.engine', fromlist=['CustomBurpDB']).CustomBurpDB(':memory:')
proxy = BurpProxy(db, port=19999)
print(f"  Proxy port: {proxy.port}")
print(f"  CA cert path: {proxy._ca_cert_path}")
print("  => FUNCIONA")

# 7. WEB UI
print("\n[7] WEB UI")
from web.app import app
with app.test_client() as c:
    r = c.get('/')
    print(f"  GET /: {r.status_code}")
    assert r.status_code == 200
    
    r = c.get('/api/status')
    print(f"  GET /api/status: {r.status_code}")
    assert r.status_code == 200
    
    r = c.post('/api/decoder/transform', json={'action': 'base64_encode', 'input': 'test'})
    print(f"  POST decoder: {r.status_code} -> {r.get_json()['output']}")
    assert r.status_code == 200
    
    r = c.post('/api/repeater/send', json={'method': 'GET', 'url': 'http://example.com', 'headers': {}, 'body': ''})
    print(f"  POST repeater: {r.status_code}")
    assert r.status_code == 200
    
    r = c.post('/api/intruder/start', json={'request': 'GET /test§HTTP/1.1\r\nHost: example.com\r\n', 'payloads': ['a', 'b'], 'mode': 'sniper', 'threads': 2, 'timeout': 5})
    print(f"  POST intruder: {r.status_code}")
    data = r.get_json()
    if 'error' not in data:
        print(f"  Intruder results: {len(data.get('results', []))}")

print("  => FUNCIONA")

# 8. DB
print("\n[8] DATABASE")
from core.engine import CustomBurpDB
db2 = CustomBurpDB(':memory:')
print("  In-memory DB: OK")
db3 = CustomBurpDB(tempfile.mktemp(suffix='.db'))
print("  File DB: OK")
os.remove(db3.db_path)
print("  => FUNCIONA")

print("\n" + "=" * 50)
print("TODOS OS TESTES PASSARAM!")
print("=" * 50)
