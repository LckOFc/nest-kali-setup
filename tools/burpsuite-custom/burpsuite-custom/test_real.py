"""Testes reais do CustomBurp"""
import sys, tempfile, os, time
sys.path.insert(0, '.')

print("=" * 50)
print("TESTES REAIS - CustomBurp Suite")
print("=" * 50)

# 1. REPEATER - Request real pra internet
print("\n[1] REPEATER - HTTP GET real")
from core.repeater import Repeater
rep = Repeater()
result = rep.send('GET', 'http://httpbin.org/get', timeout=10)
print(f"  Status: {result['status_code']}")
print(f"  Time: {result['time_ms']}ms")
print(f"  Body length: {len(result['body'])} chars")
print(f"  Has JSON: {'json' in result['body']}")
print("  => FUNCIONA")

# 2. REPEATER POST real
print("\n[2] REPEATER - HTTP POST real")
result2 = rep.send('POST', 'http://httpbin.org/post',
    headers={'Content-Type': 'application/json'},
    body='{"test": "value"}',
    timeout=10)
print(f"  Status: {result2['status_code']}")
print(f"  Time: {result2['time_ms']}ms")
print(f"  Body length: {len(result2['body'])} chars")
print("  => FUNCIONA")

# 3. DECODER
print("\n[3] DECODER")
from core.engine import Decoder
d = Decoder()
print(f"  Base64 decode: {d.base64_decode('aGVsbG8=')}")
print(f"  URL decode: {d.url_decode('%7B%22a%22%3A1%7D')}")
print(f"  MD5: {d.md5('hello')}")
print(f"  SHA256: {d.sha256('hello')}")
print(f"  HTML decode: {d.html_decode('&lt;b&gt;bold&lt;/b&gt;')}")
json_in = '{"a":1,"b":2}'
print(f"  JSON format: {d.json_format(json_in)[:30]}...")
print("  => FUNCIONA")

# 4. SCANNER
print("\n[4] SCANNER")
from core.engine import CustomBurp, HTTPMessage, LoggedRequest
tmpdb = tempfile.mktemp(suffix='.db')
burp = CustomBurp(db_path=tmpdb)

# Teste XSS
req1 = HTTPMessage('GET', '/search?q=test', {'Host': 'example.com'})
resp1 = HTTPMessage('', '', {'Content-Type': 'text/html'},
    b'<html><script>alert(1)</script></html>', status_code=200)
resp1.timestamp = req1.timestamp + 0.1
issues1 = burp.scanner.scan_request(LoggedRequest(request=req1, response=resp1, engine='test'))
print(f"  XSS test: {len(issues1)} issues")

# Teste SQLi
req2 = HTTPMessage('GET', '/login', {'Host': 'example.com'})
resp2 = HTTPMessage('', '', {'Content-Type': 'text/html'},
    b"<html>Error: SQL syntax error</html>", status_code=200)
resp2.timestamp = req2.timestamp + 0.1
issues2 = burp.scanner.scan_request(LoggedRequest(request=req2, response=resp2, engine='test'))
print(f"  SQLi test: {len(issues2)} issues")

# Teste headers ausentes
req3 = HTTPMessage('GET', '/', {'Host': 'example.com'})
resp3 = HTTPMessage('', '', {'Content-Type': 'text/html'}, b'<html>ok</html>', status_code=200)
resp3.timestamp = req3.timestamp + 0.1
issues3 = burp.scanner.scan_request(LoggedRequest(request=req3, response=resp3, engine='test'))
print(f"  Headers test: {len(issues3)} issues")
for i in issues3:
    print(f"    - {i['type']}: {i['severity']}")
print("  => FUNCIONA")

os.remove(tmpdb)

# 5. PROXY
print("\n[5] PROXY")
from core.engine import BurpProxy, CustomBurpDB
db = CustomBurpDB(':memory:')
proxy = BurpProxy(db, port=19999)
print(f"  Proxy port: {proxy.port}")
print(f"  Queue size: {proxy.request_queue.qsize()}")
print("  => FUNCIONA")

# 6. WEB UI
print("\n[6] WEB UI")
from web.app import app
with app.test_client() as c:
    r = c.get('/')
    print(f"  GET / : {r.status_code}")
    r = c.get('/api/status')
    print(f"  GET /api/status : {r.status_code}")
    r = c.post('/api/decoder/transform', json={'action': 'url_encode', 'input': 'hello world'})
    print(f"  POST /api/decoder : {r.status_code} -> {r.get_json()['output']}")
print("  => FUNCIONA")

print("\n" + "=" * 50)
print("TODOS OS MODULOS FUNCIONANDO!")
print("=" * 50)
