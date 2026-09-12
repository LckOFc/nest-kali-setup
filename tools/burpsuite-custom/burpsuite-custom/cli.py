"""
CustomBurp - Comandos CLI para opencode
"""

import subprocess
import sys
import os

BURP_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'burpsuite-custom')


def run(args=None):
    """Executa comando do CustomBurp"""
    cmd = [sys.executable, 'main.py']
    if args:
        cmd.extend(args)
    
    proc = subprocess.run(cmd, cwd=BURP_DIR, capture_output=False)
    return proc.returncode


def start(proxy_port=8080, web_port=4000, generate_ca=False):
    """Inicia o CustomBurp"""
    args = []
    if proxy_port != 8080:
        args.extend(['--proxy-port', str(proxy_port)])
    if web_port != 4000:
        args.extend(['--web-port', str(web_port)])
    if generate_ca:
        args.append('--generate-ca')
    return run(args)


def status():
    """Mostra status"""
    print("CustomBurp Suite Status:")
    print("=" * 40)
    print(f"  Diretorio: {BURP_DIR}")
    print(f"  Proxy: http://127.0.0.1:8080")
    print(f"  Web: http://localhost:4000")
    print("=" * 40)


def test():
    """Executa testes"""
    test_file = os.path.join(BURP_DIR, 'test_full.py')
    if os.path.exists(test_file):
        return subprocess.run([sys.executable, test_file], cwd=BURP_DIR).returncode
    return 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='?', default='status',
                       choices=['start', 'status', 'test'])
    parser.add_argument('--proxy-port', type=int, default=8080)
    parser.add_argument('--web-port', type=int, default=4000)
    parser.add_argument('--generate-ca', action='store_true')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        sys.exit(start(args.proxy_port, args.web_port, args.generate_ca))
    elif args.command == 'status':
        status()
    elif args.command == 'test':
        sys.exit(test())
