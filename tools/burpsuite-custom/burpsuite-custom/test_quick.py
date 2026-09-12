"""Teste rápido do CustomBurp"""
import sys
sys.path.insert(0, '.')

from core.engine import Decoder, CustomBurpDB, VulnScanner, BurpProxy, Intruder
from core.repeater import Repeater

print("=" * 50)
print("CustomBurp - Testes Rápidos")
print("=" * 50)

# Testar Decoder
d = Decoder()
print("\n[Decoder]")
print(f"  URL Decode: {d.url_decode('%7B%22test%22%3A1%7D')}")
print(f"  Base64 Decode: {d.base64_decode('aGVsbG8gd29ybGQ=')}")
print(f"  Base64 Encode: {d.base64_encode('hello world')}")
print(f"  MD5: {d.md5('test')}")
print(f"  SHA256: {d.sha256('test')}")
print(f"  HTML Decode: {d.html_decode('&lt;script&gt;alert(1)&lt;/script&gt;')}")
json_test = '{"id": 1, "name": "test"}'
print(f"  JSON Format: {d.json_format(json_test)}")
print(f"  Hex Encode: {d.hex_encode('hello')}")
print(f"  Hex Decode: {d.hex_decode('68656c6c6f')}")
print(f"  ROT13: {d.rot13('hello')}")
print(f"  Detect Base64: {d.detect_encoding('dGVzdA==')}")
print(f"  Detect Plain: {d.detect_encoding('hello world')}")

# Testar DB
print("\n[Database]")
db = CustomBurpDB(':memory:')
print("  In-memory DB OK")

# Testar Scanner
print("\n[Scanner]")
scanner = VulnScanner(db)
print(f"  Patterns: {len(scanner.VULN_PATTERNS)} vuln types")
print("  Scanner OK")

# Testar Proxy
print("\n[Proxy]")
proxy = BurpProxy(db, port=19999)
print(f"  Proxy on port {proxy.port} OK")

# Testar Intruder
print("\n[Intruder]")
intruder = Intruder(db)
print("  Intruder OK")

# Testar Repeater
print("\n[Repeater]")
rep = Repeater()
print("  Repeater OK")

print("\n" + "=" * 50)
print("Todos os testes passaram!")
print("=" * 50)
