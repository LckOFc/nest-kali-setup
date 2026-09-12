"""Test Match & Replace"""
from core.match_replace import MatchReplace
mr = MatchReplace()
mr.add_rule(r'<script[^>]*>.*?</script>', '<!-- REMOVED -->', target='response')
req = {'path': '/admin/test', 'headers': {'Host': 'example.com'}}
processed = mr.process_request(req, host='example.com')
print('Path:', processed['path'])
pat = r'/admin/(.*)'
rep = r'/private/\$1'
mr.add_rule(pat, rep, target='request', scope='example.com')
processed = mr.process_request({'path': '/admin/settings'}, host='example.com')
print('After rule:', processed['path'])
assert processed['path'] == '/private/settings', f"Expected /private/settings, got {processed['path']}"
print('MatchReplace OK')
