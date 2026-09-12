"""
CustomBurp v2 - Main Application
"""

import asyncio
import logging
import os
import sys
import argparse
import threading
import time
from typing import Optional

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db import Database
from core.proxy import BurpProxy
from core.repeater import Repeater
from core.intruder import Intruder
from core.scanner import VulnScanner
from core.logger import Logger
from core.decoder import Decoder
from core.target import Target
from core.session import SessionManager
from core.collaborator import Collaborator
from core.organizer import Organizer
from core.comparer import Comparer
from core.sequencer import Sequencer
from core.alerts import Alerts
from core.api import BurpAPI
from aiohttp import web


class CustomBurp:
    """Main CustomBurp v2 Application"""
    
    def __init__(self, db_path: str = 'custom_burp_v2.db', 
                 proxy_port: int = 8080,
                 web_port: int = 4000):
        self.db_path = db_path
        self.proxy_port = proxy_port
        self.web_port = web_port
        
        # Initialize components
        self.db = Database(db_path)
        self.proxy = BurpProxy(self.db, port=proxy_port)
        self.repeater = Repeater(self.db)
        self.intruder = Intruder(self.db)
        self.scanner = VulnScanner(self.db)
        self.logger = Logger(self.db)
        self.decoder = Decoder()
        self.target = Target(self.db)
        self.session = SessionManager(self.db)
        self.collaborator = Collaborator(self.db)
        self.organizer = Organizer(self.db)
        self.comparer = Comparer()
        self.sequencer = Sequencer()
        self.alerts = Alerts(self.db)
        
        # Wire up handlers
        self.proxy.add_request_handler(self._on_request)
        self.proxy.add_response_handler(self._on_response)
        
        # API
        self.api = BurpAPI(self)
        
        # Logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler('custom_burp_v2.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('custom_burp')
    
    def _on_request(self, request_data: dict):
        """Called when proxy receives a request"""
        self.logger.info(f"[REQ] {request_data.get('method', '')} {request_data.get('full_url', request_data.get('path', ''))}")
        self.alerts.check_request(request_data, {})
    
    def _on_response(self, request_data: dict, response_data: dict):
        """Called when proxy receives a response"""
        self.alerts.check_request(request_data, response_data)
    
    def start_proxy(self):
        """Start proxy in background thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _start():
            await self.proxy.start()
        
        self._proxy_thread = threading.Thread(
            target=lambda: loop.run_until_complete(_start()),
            daemon=True
        )
        self._proxy_thread.start()
        self._proxy_loop = loop
    
    def stop_proxy(self):
        """Stop proxy"""
        if hasattr(self, '_proxy_loop') and self._proxy_loop:
            try:
                asyncio.run_coroutine_threadsafe(self.proxy.stop(), self._proxy_loop)
            except:
                pass
    
    def run_web(self, host: str = '0.0.0.0', port: int = None):
        """Run web server"""
        port = port or self.web_port
        
        from aiohttp import web as aiohttp_web
        from aiohttp.web_middlewares import middleware
        
        app = self.api.get_app()
        
        # Add CORS middleware
        import aiohttp_cors
        
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allowed_headers=["*"],
                expose_headers=["*"],
                max_age=3600,
            )
        })
        
        # Apply CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)
        
        # Static files
        static_dir = os.path.join(os.path.dirname(__file__), 'web', 'static')
        if os.path.exists(static_dir):
            app.router.add_static('/static/', static_dir)
        
        # Index page
        app.router.add_get('/', self._serve_index)
        
        self.logger.info(f"Web UI starting on http://{host}:{port}")
        aiohttp_web.run_app(app, host=host, port=port)
    
    async def _serve_index(self, request: web.Request) -> web.Response:
        """Serve the main HTML page"""
        index_path = os.path.join(os.path.dirname(__file__), 'web', 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        return web.Response(text='No index.html found', status=404)


def main():
    parser = argparse.ArgumentParser(description='CustomBurp Suite v2')
    parser.add_argument('--proxy-port', type=int, default=8080, help='Proxy port (default: 8080)')
    parser.add_argument('--web-port', type=int, default=4000, help='Web UI port (default: 4000)')
    parser.add_argument('--no-proxy', action='store_true', help='Disable proxy')
    parser.add_argument('--no-web', action='store_true', help='Disable web UI')
    parser.add_argument('--generate-ca', action='store_true', help='Generate CA certificate')
    parser.add_argument('--db', type=str, default='custom_burp_v2.db', help='Database path')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  CustomBurp Suite v2")
    print("  por ratman4080 / Sombra")
    print("=" * 60)
    print()
    
    burp = CustomBurp(
        db_path=args.db,
        proxy_port=args.proxy_port,
        web_port=args.web_port
    )
    
    if args.generate_ca:
        print(f"[+] CA Certificate: {burp.proxy.ca_cert_path}")
        print("[+] Instale no navegador para interceptar HTTPS")
    
    threads = []
    
    if not args.no_proxy:
        burp.start_proxy()
        print(f"[+] Proxy iniciado em http://127.0.0.1:{args.proxy_port}")
        print("[+] Configure seu navegador para usar este proxy")
    
    if not args.no_web:
        web_thread = threading.Thread(
            target=burp.run_web,
            kwargs={'host': '0.0.0.0', 'port': args.web_port},
            daemon=True
        )
        web_thread.start()
        threads.append(web_thread)
        print(f"[+] Web UI iniciada em http://localhost:{args.web_port}")
    
    if not threads and args.no_proxy:
        print("[!] Nenhum serviço ativo.")
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
