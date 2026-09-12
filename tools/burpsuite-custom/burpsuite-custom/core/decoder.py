"""
CustomBurp - Decoder Module
Compatibilidade com imports do app.py
Re-exporta funções do engine.py para manter compatibilidade
"""

from core.engine import Decoder as Decoder


if __name__ == '__main__':
    d = Decoder()
    
    test_data = "Hello World! &lt;script&gt;alert(1)&lt;/script&gt;"
    
    print("=== TESTES DECODER ===\n")
    print(f"Input: {test_data}")
    print(f"HTML Decode: {d.html_decode(test_data)}")
    print(f"HTML Encode: {d.html_encode('Hello <world>')}")
    print(f"URL Encode: {d.url_encode('hello world')}")
    print(f"URL Decode: {d.url_decode('hello%20world')}")
    print(f"Base64 Encode: {d.base64_encode('test')}")
    print(f"Base64 Decode: {d.base64_decode('dGVzdA==')}")
    print(f"MD5: {d.md5('test')}")
    print(f"SHA256: {d.sha256('test')}")
    json_test = '{"a":1,"b":2}'
    print(f"JSON Format: {d.json_format(json_test)}")
    print(f"Detect: {d.detect_encoding('dGVzdA==')}")
    print(f"Detect: {d.detect_encoding('hello world')}")
