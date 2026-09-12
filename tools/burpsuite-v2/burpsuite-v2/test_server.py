"""Test server - start and verify CustomBurp v2"""
import asyncio
import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import CustomBurp

# Create app
burp = CustomBurp(db_path=':memory:', proxy_port=18080, web_port=18000)

# Start web server in thread
def run_web():
    burp.run_web(host='127.0.0.1', port=18000)

t = threading.Thread(target=run_web, daemon=True)
t.start()

# Wait for server to start
time.sleep(2)

# Test API
import urllib.request
import json

def get(url):
    req = urllib.request.Request(f'http://127.0.0.1:18000{url}')
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())

def post(url, data):
    req = urllib.request.Request(
        f'http://127.0.0.1:18000{url}',
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

print("[TEST] CustomBurp v2 - Testando API...")

# Test status
status = get('/api/status')
print(f"[OK] Status: {status.get('name')} v{status.get('version')}")

# Test stats
stats = get('/api/stats')
print(f"[OK] Stats: {stats['total_requests']} requests, {stats['unique_hosts']} hosts")

# Test decoder
dec_result = post('/api/decoder/transform', {'action': 'base64_encode', 'input': 'Hello World'})
print(f"[OK] Decoder: base64('Hello World') = {dec_result['output']}")

# Test sequencer
seq_result = post('/api/sequencer/analyze', {'tokens': ['abc123', 'def456', 'ghi789'], 'name': 'test'})
print(f"[OK] Sequencer: entropy={seq_result['entropy']['shannon_avg']}, severity={seq_result['severity']}")

# Test comparer
comp_result = post('/api/comparer/compare', {
    'left': {'status_code': 200, 'body': '{"a":1}'},
    'right': {'status_code': 200, 'body': '{"a":2}'}
})
print(f"[OK] Comparer: {comp_result['summary']['total_diffs']} diffs found")

# Test target
post('/api/target/add', {'host': 'example.com', 'include': True})
scope = get('/api/target/scope')
print(f"[OK] Target: {len(scope['included_hosts'])} hosts in scope")

# Test session
session = post('/api/session/create', {'name': 'test'})
print(f"[OK] Session: {session['session_id'][:8]}... created")

# Test projects
project = post('/api/projects/create', {'name': 'Test Project'})
print(f"[OK] Project: {project['name']} created")

# Test organizer
post('/api/requests/clear', {})
print("[OK] Logger cleared")

print()
print("=" * 50)
print("ALL TESTS PASSED!")
print("Server running at: http://127.0.0.1:18000")
print("=" * 50)

# Keep running
while True:
    time.sleep(1)
