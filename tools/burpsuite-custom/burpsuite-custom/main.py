"""
CustomBurp - Main Entry Point
Inicia proxy e UI web
"""

import sys
import os
import argparse
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import CustomBurp, CustomBurpDB
from web.app import init_app, run_web


def main():
    parser = argparse.ArgumentParser(description='CustomBurp Suite - Ferramenta de Testes de Seguranca')
    parser.add_argument('--proxy-port', type=int, default=8080, help='Porta do proxy (padrao: 8080)')
    parser.add_argument('--web-port', type=int, default=4000, help='Porta da UI web (padrao: 4000)')
    parser.add_argument('--no-proxy', action='store_true', help='Não iniciar proxy')
    parser.add_argument('--no-web', action='store_true', help='Não iniciar UI web')
    parser.add_argument('--generate-ca', action='store_true', help='Gerar certificado CA')
    parser.add_argument('--db', type=str, default='custom_burp.db', help='Caminho do banco de dados')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  CustomBurp Suite - Ferramenta de Testes de Seguranca")
    print("  por ratman4080 / Sombra")
    print("=" * 60)
    print()
    
    # Inicializar
    db = CustomBurpDB(args.db)
    burp = CustomBurp(db_path=args.db, proxy_port=args.proxy_port)
    init_app(burp)
    
    # Gerar CA se solicitado
    if args.generate_ca:
        burp.proxy.ssl_cert_gen._load_or_create_ca()
        print(f"[+] CA Certificate: {burp.proxy._ca_cert_path}")
        print("[+] Instale no navegador para interceptar HTTPS")
    
    threads = []
    
    # Iniciar proxy
    if not args.no_proxy:
        t = threading.Thread(target=burp.start_proxy, daemon=True)
        t.start()
        threads.append(t)
        print(f"[+] Proxy iniciado em http://127.0.0.1:{args.proxy_port}")
        print("[+] Configure seu navegador para usar este proxy")
    
    # Iniciar UI web
    if not args.no_web:
        t = threading.Thread(target=run_web, args=('0.0.0.0', args.web_port), daemon=True)
        t.start()
        threads.append(t)
        print(f"[+] UI Web iniciada em http://localhost:{args.web_port}")
    
    if not threads:
        print("[!] Nenhum serviço iniciado.")
        return
    
    print()
    print("Pressione Ctrl+C para parar")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Shutting down...")
        if not args.no_proxy:
            burp.stop_proxy()
        print("[+] Done.")


if __name__ == '__main__':
    main()
