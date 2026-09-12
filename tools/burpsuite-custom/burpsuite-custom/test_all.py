"""CustomBurp - Testes Completos 100% Funcional"""
import sys, tempfile, os, time
sys.path.insert(0, '.')

print("=" * 60)
print("  CUSTOMBURP SUITE - TESTES COMPLETOS 100%")
print("  por ratman4080 / Sombra")
print("=" * 60)

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  [PASS] {name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1


# ========================================================================
# 1. REPEATER
# ========================================================================
print("\n[1] REPEATER")
from core.repeater import Repeater

def test_repeater_get():
    rep = Repeater()
    r = rep.send('GET', 'http://httpbin.org/get', timeout=10)
    assert r['status_code'] == 200
    assert len(r['body']) > 0

def test_repeater_post():
    rep = Repeater()
    r = rep.send('POST', 'http://httpbin.org/post',
                 headers={'Content-Type': 'application/json'},
                 body='{"test": "value"}', timeout=10)
    assert r['status_code'] == 200
    assert 'test' in r['body']

test("HTTP GET real", test_repeater_get)
test("HTTP POST real", test_repeater_post)


# ========================================================================
# 2. DECODER
# ========================================================================
print("\n[2] DECODER")
from core.engine import Decoder

def test_decoder_all():
    d = Decoder()
    assert d.url_decode('%7B%22a%22%3A1%7D') == '{"a":1}'
    assert d.base64_decode('aGVsbG8=') == 'hello'
    assert d.md5('test') == '098f6bcd4621d373cade4e832627b4f6'
    assert d.html_decode('&lt;b&gt;') == '<b>'
    assert 'a' in d.json_format('{"a":1}')

test("Decoder completo", test_decoder_all)


# ========================================================================
# 3. SCANNER
# ========================================================================
print("\n[3] SCANNER")
from core.engine import CustomBurp, HTTPMessage, LoggedRequest

def test_scanner_xss():
    burp = CustomBurp(db_path=':memory:')
    req = HTTPMessage('GET', '/search?q=test', {'Host': 'example.com'})
    resp = HTTPMessage('', '', {'Content-Type': 'text/html'},
                       b'<html><script>alert(1)</script></html>', status_code=200)
    resp.timestamp = req.timestamp + 0.1
    issues = burp.scanner.scan_request(LoggedRequest(request=req, response=resp, engine='test'))
    assert len(issues) > 0

def test_scanner_sqli():
    burp = CustomBurp(db_path=':memory:')
    req = HTTPMessage('GET', '/login', {'Host': 'example.com'})
    resp = HTTPMessage('', '', {'Content-Type': 'text/html'},
                       b"<html>Error: SQL syntax error</html>", status_code=200)
    resp.timestamp = req.timestamp + 0.1
    issues = burp.scanner.scan_request(LoggedRequest(request=req, response=resp, engine='test'))
    assert len(issues) > 0

test("XSS detection", test_scanner_xss)
test("SQLi detection", test_scanner_sqli)


# ========================================================================
# 4. INTRUDER
# ========================================================================
print("\n[4] INTRUDER")
from core.intruder import Intruder

def test_intruder():
    intruder = Intruder()
    req = "GET /search?q=§HTTP/1.1\r\nHost: httpbin.org\r\n"
    results = intruder.attack(req, ['admin', 'test'], mode='sniper', thread_count=2, timeout=10)
    assert len(results) == 2
    assert all(r['status_code'] != 0 for r in results)

test("Intruder sniper mode", test_intruder)


# ========================================================================
# 5. COMPARER
# ========================================================================
print("\n[5] COMPARER")
from core.comparer import Comparer

def test_comparer():
    comp = Comparer()
    left = {'status_code': 200, 'headers': {'Server': 'Apache'}, 'body': 'Hello World'}
    right = {'status_code': 200, 'headers': {'Server': 'nginx'}, 'body': 'Hello Modified'}
    result = comp.compare(left, right)
    assert result['summary']['total_diffs'] > 0
    assert result['summary']['length_diff'] > 0

test("Comparer diff", test_comparer)


# ========================================================================
# 6. SEQUENCER
# ========================================================================
print("\n[6] SEQUENCER")
from core.sequencer import Sequencer

def test_sequencer_good():
    seq = Sequencer()
    tokens = ['a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4', 'b7e1f3a5c9d2e4f6a8b0c2d4e6f8a0b2']
    result = seq.analyze(tokens, 'Test')
    assert 'entropy' in result
    assert 'severity' in result

def test_sequencer_bad():
    seq = Sequencer()
    tokens = ['token_1', 'token_2', 'token_3']
    result = seq.analyze(tokens, 'Bad')
    assert result['severity'] in ['Low', 'Critical']

test("Sequencer good tokens", test_sequencer_good)
test("Sequencer bad tokens", test_sequencer_bad)


# ========================================================================
# 7. TARGET
# ========================================================================
print("\n[7] TARGET")
from core.target import Target

def test_target_scope():
    target = Target()
    target.add_scope('example.com', include=True)
    assert target.is_in_scope('http://example.com/login')
    assert not target.is_in_scope('http://other.com/login')
    target.exclude_scope('example.com')
    assert not target.is_in_scope('http://example.com/login')

def test_target_sitemap():
    target = Target()
    target.add_scope('example.com', include=True)
    target.add_to_sitemap('http://example.com/login')
    sitemap = target.get_sitemap()
    assert 'example.com' in sitemap

test("Target scope management", test_target_scope)
test("Target sitemap", test_target_sitemap)


# ========================================================================
# 8. SESSION HANDLER
# ========================================================================
print("\n[8] SESSION HANDLER")
from core.session_handler import SessionManager

def test_session():
    mgr = SessionManager()
    session = mgr.create_session()
    assert session.session_id
    mgr.add_cookie(session.session_id, 'session_id', 'abc123')
    cookie = session.get_cookie('session_id')
    assert cookie.value == 'abc123'
    mgr.set_header(session.session_id, 'Authorization', 'Bearer token')
    auth = mgr.get_session_header(session.session_id, 'Authorization')
    assert auth == 'Bearer token'

def test_session_cookies():
    mgr = SessionManager()
    session = mgr.create_session()
    mgr.parse_response_cookies(session.session_id,
        'auth_token=xyz; Domain=.example.com; Path=/; Secure; HttpOnly')
    cookie = session.get_cookie('auth_token')
    assert cookie is not None
    assert cookie.secure
    assert cookie.http_only

test("Session create/get", test_session)
test("Session cookies", test_session_cookies)


# ========================================================================
# 9. MATCH & REPLACE
# ========================================================================
print("\n[9] MATCH & REPLACE")
from core.match_replace import MatchReplace

def test_match_replace():
    mr = MatchReplace()
    mr.add_rule(r'<script[^>]*>.*?</script>', '<!-- REMOVED -->', target='response')
    resp = {'body': b'<html><script>alert(1)</script></html>'}
    result = mr.process_response(resp)
    body_str = result['body'].decode('utf-8') if isinstance(result['body'], bytes) else result['body']
    assert '<!-- REMOVED -->' in body_str
    
    mr.add_rule(r'/admin/(.*)', r'/private/\1', target='request', scope='example.com')
    req = {'path': '/admin/settings'}
    result = mr.process_request(req, host='example.com')
    assert result['path'] == '/private/settings'

test("Match & Replace rules", test_match_replace)


# ========================================================================
# 10. PAYLOAD PROCESSOR
# ========================================================================
print("\n[10] PAYLOAD PROCESSOR")
from core.payload_processor import PayloadProcessor

def test_payload_processor():
    pp = PayloadProcessor()
    assert pp.process('hello', 'upper') == 'HELLO'
    assert pp.process('test', 'md5') == '098f6bcd4621d373cade4e832627b4f6'
    ops = pp.list_operations()
    assert 'base64_encode' in ops

test("Payload processing", test_payload_processor)


# ========================================================================
# 11. COLLABORATOR
# ========================================================================
print("\n[11] COLLABORATOR")
from core.collaborator import Collaborator

def test_collaborator():
    collab = Collaborator(port=19001)
    info = collab.start()
    assert info['subdomain']
    payloads = collab.generate_payloads()
    assert 'dns' in payloads
    assert 'http' in payloads
    collab.stop()

test("Collaborator start/payloads", test_collaborator)


# ========================================================================
# 12. LOGGER
# ========================================================================
print("\n[12] LOGGER")
from core.logger import BurpLogger

def test_logger():
    log = BurpLogger(':memory:')
    entry_id = log.log(
        request={'method': 'GET', 'host': 'example.com', 'path': '/test', 'headers': {}},
        response={'status_code': 200, 'headers': {}, 'body': 'ok', 'time_ms': 50},
        tags=['test']
    )
    assert entry_id
    entries = log.get_entries(host='example.com')
    assert len(entries) > 0
    stats = log.get_stats()
    assert stats['total_entries'] > 0

test("Logger basic operations", test_logger)


# ========================================================================
# 13. ORGANIZER
# ========================================================================
print("\n[13] ORGANIZER")
from core.organizer import Organizer

def test_organizer():
    org = Organizer(storage_path=':memory:')
    item = org.add(
        request={'method': 'GET', 'path': '/admin'},
        notes='Test item',
        tags=['auth', 'critical'],
        folder='Testes'
    )
    assert item['id']
    items = org.list_items(folder='Testes')
    assert len(items) > 0
    stats = org.get_stats()
    assert stats['total_items'] > 0
    org.toggle_star(item['id'])
    starred = [i for i in org.items if i.get('starred')]
    assert len(starred) == 1

test("Organizer operations", test_organizer)


# ========================================================================
# 14. ALERTS
# ========================================================================
print("\n[14] ALERTS")
from core.alerts import Alerts

def test_alerts():
    alerts = Alerts()
    a1 = alerts.add_alert('XSS', 'High', 'XSS detected', 'req_001', '<script>')
    a2 = alerts.add_alert('SQLi', 'Critical', 'SQLi detected', 'req_002', "OR 1=1")
    assert len(alerts.alerts) == 2
    assert alerts.get_unread_count() == 2
    summary = alerts.get_summary()
    assert summary['total'] == 2
    alerts.acknowledge_alert(a1.alert_id)
    assert a1.acknowledged

test("Alerts system", test_alerts)


# ========================================================================
# 15. PROJECT MANAGER
# ========================================================================
print("\n[15] PROJECT MANAGER")
from core.project import ProjectManager

def test_project():
    pm = ProjectManager(projects_dir=':memory:')
    project = pm.create_project('Test Project')
    assert project['id']
    pm.update_target(project['id'], {'scope': {'included_hosts': ['example.com']}})
    pm.add_session(project['id'], 'sess_1', {'cookies': {'session': 'abc'}})
    pm.add_alert(project['id'], {'type': 'XSS', 'severity': 'High'})
    projects = pm.list_projects()
    assert len(projects) > 0
    exported = pm.export_project(project['id'])
    assert exported['name'] == 'Test Project'

test("Project management", test_project)


# ========================================================================
# 16. MAIN ENGINE
# ========================================================================
print("\n[16] MAIN ENGINE (CustomBurp)")
from core.engine import CustomBurp

def test_engine():
    import time
    burp = CustomBurp(db_path=':memory:')
    status = burp.get_status()
    assert 'proxy_running' in status
    assert 'modules' in status
    assert status['modules']['collaborator_running'] == False
    burp.start_proxy()
    time.sleep(0.3)  # Wait for thread to start
    assert burp.proxy.running
    burp.stop_proxy()
    time.sleep(0.2)
    assert not burp.proxy.running

test("Engine init/start/stop", test_engine)


# ========================================================================
# 17. REST API
# ========================================================================
print("\n[17] REST API")
from core.api import BurpAPI

def test_api():
    burp = CustomBurp(db_path=':memory:')
    api = BurpAPI(burp)
    
    # Help
    r = api.handle_request('GET', '/api/help')
    assert r['success']
    assert len(r['data']['endpoints']) > 15
    
    # Stats
    r = api.handle_request('GET', '/api/stats')
    assert r['success']
    
    # Decoder
    r = api.handle_request('POST', '/api/decoder/transform',
                           {'action': 'base64_encode', 'input': 'test'})
    assert r['success']
    assert r['data']['output'] == 'dGVzdA=='
    
    # Session
    r = api.handle_request('POST', '/api/session/create')
    assert r['success']
    session_id = r['data']['session_id']
    
    r = api.handle_request('GET', f'/api/session/{session_id}')
    assert r['success']
    assert r['data']['session_id'] == session_id
    
    # Collaborator
    r = api.handle_request('POST', '/api/collaborator/start')
    assert r['success']
    assert r['data']['subdomain']
    
    r = api.handle_request('GET', '/api/collaborator/payloads')
    assert r['success']
    assert 'dns' in r['data']
    
    # Target
    r = api.handle_request('POST', '/api/target/add', {'host': 'example.com'})
    assert r['success']
    
    r = api.handle_request('GET', '/api/target/sitemap')
    assert r['success']
    
    # Comparer
    r = api.handle_request('POST', '/api/comparer/compare',
                           {'left': {'body': 'hello'}, 'right': {'body': 'world'}})
    assert r['success']
    assert r['data']['summary']['total_diffs'] > 0
    
    # Sequencer
    r = api.handle_request('POST', '/api/sequencer/analyze',
                           {'tokens': ['abc123', 'def456'], 'name': 'test'})
    assert r['success']
    assert 'entropy' in r['data']
    
    burp.stop_proxy()

test("API endpoints", test_api)


# ========================================================================
# RESULTADO FINAL
# ========================================================================
print("\n" + "=" * 60)
print(f"  RESULTADOS: {passed} PASS, {failed} FAIL")
print("=" * 60)

if failed == 0:
    print("\n  TODOS OS TESTES PASSARAM - 100% FUNCIONAL!")
else:
    print(f"\n  {failed} teste(s) falharam.")

sys.exit(0 if failed == 0 else 1)
