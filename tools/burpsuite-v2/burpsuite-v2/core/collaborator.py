"""
CustomBurp v2 - Collaborator (OAST)
Out-of-band interaction detection server
"""

import asyncio
import hashlib
import json
import logging
import socket
import threading
import uuid
import time
from typing import Dict, List, Optional
from aiohttp import web

logger = logging.getLogger('custom_burp.collaborator')


class Collaborator:
    """OAST server for detecting blind vulnerabilities"""
    
    def __init__(self, db):
        self.db = db
        self._running = False
        self._server = None
        self._port = 0
        self._subdomain = str(uuid.uuid4())[:8]
        self._interactions: List[Dict] = []
        self._payloads = {}
    
    async def start(self, port: int = 0) -> Dict:
        """Start the OAST server"""
        if self._running:
            return self.get_status()
        
        # Start DNS mock server
        self._port = port or 5300
        self._running = True
        
        # For simplicity, we'll use a TCP/HTTP server approach
        # In production, you'd want a real DNS server
        
        app = web.Application()
        app.router.add_get('/', self._handle_root)
        app.router.add_get('/{path:re:.*}', self._handle_request)
        app.router.add_post('/', self._handle_request)
        app.router.add_post('/{path:re:.*}', self._handle_request)
        
        self._http_server = web.AppRunner(app)
        await self._http_server.setup()
        
        site = web.TCPSite(self._http_server, '0.0.0.0', self._port)
        await site.start()
        
        self._port = self._http_server._sites[0]._server.sockets[0].getsockname()[1]
        
        # Generate payloads
        self._generate_payloads()
        
        logger.info(f"Collaborator OAST server started on port {self._port}")
        
        return self.get_status()
    
    async def stop(self):
        """Stop the OAST server"""
        if self._http_server:
            await self._http_server.cleanup()
        self._running = False
        logger.info("Collaborator OAST server stopped")
    
    def _generate_payloads(self):
        """Generate interaction payloads"""
        self._payloads = {
            'dns': {
                'full_domain': f"{self._subdomain}.collab.customburp",
                'short': self._subdomain,
            },
            'http': {
                'url': f"http://{self._subdomain}.collab.customburp:{self._port}/",
                'raw': f"http://{self._subdomain}.collab.customburp:{self._port}/",
            },
            'xxe': {
                'entity': f'<!ENTITY xxe SYSTEM "http://{self._subdomain}.collab.customburp:{self._port}/xxe">',
                'external': f'"http://{self._subdomain}.collab.customburp:{self._port}/external">',
            },
            'ssrf': {
                'url': f"http://{self._subdomain}.collab.customburp:{self._port}/ssrf",
            }
        }
    
    async def _handle_root(self, request: web.Request) -> web.Response:
        """Handle root request"""
        self._log_interaction('http', request)
        return web.Response(text=f'CustomBurp Collaborator - Interaction received from {request.remote}',
                          content_type='text/plain')
    
    async def _handle_request(self, request: web.Request) -> web.Response:
        """Handle any request"""
        self._log_interaction('http', request)
        return web.Response(text='Interaction logged', content_type='text/plain')
    
    def _log_interaction(self, interaction_type: str, request: web.Request):
        """Log an interaction"""
        interaction = {
            'id': hashlib.md5(f"{request.remote}{time.time()}".encode()).hexdigest()[:16],
            'timestamp': time.time(),
            'type': interaction_type,
            'source_ip': request.remote,
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'query_string': request.query_string,
            'body': '',
        }
        
        # Read body if present
        try:
            body = asyncio.get_event_loop().run_until_complete(request.read())
            interaction['body'] = body.decode('utf-8', errors='replace')[:1000]
        except:
            pass
        
        self._interactions.append(interaction)
        
        # Save to DB
        try:
            self.db.save_collab_interaction({
                'id': interaction['id'],
                'timestamp': interaction['timestamp'],
                'type': interaction['type'],
                'data': {k: v for k, v in interaction.items() if k not in ('id', 'timestamp')},
                'source_ip': interaction['source_ip'],
                'full_data': interaction,
            })
        except:
            pass
    
    def get_status(self) -> Dict:
        """Get server status"""
        return {
            'running': self._running,
            'subdomain': self._subdomain,
            'port': self._port,
            'total_interactions': len(self._interactions),
        }
    
    def get_payloads(self) -> Dict:
        """Get generated payloads"""
        return self._payloads
    
    def get_interactions(self, limit: int = 100) -> List[Dict]:
        """Get interactions"""
        return self._interactions[-limit:]
    
    def clear_interactions(self):
        """Clear interactions"""
        self._interactions.clear()
