"""
CustomBurp v2 - Repeater Engine
Envia requests HTTP/HTTPS reais com modificação
"""

import asyncio
import hashlib
import json
import time
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urlunparse
import ssl as ssl_mod

logger = logging.getLogger('custom_burp.repeater')


class Repeater:
    """Real HTTP request repeater"""
    
    def __init__(self, db):
        self.db = db
        self._history: List[Dict] = []
        self._max_history = 500
    
    async def send(self, request_data: Dict) -> Dict:
        """Send a real HTTP request and return response"""
        method = request_data.get('method', 'GET').upper()
        url = request_data.get('url', '')
        headers = request_data.get('headers', {})
        body = request_data.get('body', '')
        
        # Parse URL
        parsed = urlparse(url)
        host = parsed.hostname or 'localhost'
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        path = parsed.path or '/'
        query = parsed.query or ''
        
        # Build raw request
        raw_request = self._build_request(method, path, query, headers, body)
        
        start_time = time.time()
        
        try:
            if port == 443:
                # HTTPS
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port, ssl=self._get_ssl_context()),
                    timeout=30
                )
            else:
                # HTTP
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=30
                )
            
            writer.write(raw_request.encode('utf-8'))
            await writer.drain()
            
            # Read response
            resp_data = b''
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=30)
                if not chunk:
                    break
                resp_data += chunk
                if b'\r\n\r\n' in resp_data:
                    header_end = resp_data.find(b'\r\n\r\n')
                    headers_text = resp_data[:header_end].decode('utf-8', errors='replace')
                    
                    content_length = 0
                    for line in headers_text.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_received = len(resp_data) - header_end - 4
                    if body_received >= content_length or content_length == 0:
                        break
                    
                    while body_received < content_length:
                        chunk = await asyncio.wait_for(
                            reader.read(min(65536, content_length - body_received)),
                            timeout=30
                        )
                        if not chunk:
                            break
                        resp_data += chunk
                        body_received = len(resp_data) - header_end - 4
                    break
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Parse response
            response = self._parse_response(resp_data, elapsed_ms)
            
            # Build result
            req_id = hashlib.md5(f"{method}{path}{body}{time.time()}".encode()).hexdigest()[:16]
            
            result = {
                'id': req_id,
                'request': {
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'body': body,
                    'raw': raw_request,
                },
                'response': response,
                'time_ms': elapsed_ms,
                'timestamp': time.time(),
            }
            
            # Save to history
            self._history.append(result)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            # Save to database
            self._save_to_db(result)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Repeater timeout for {host}:{port}")
            return {
                'error': f'Timeout connecting to {host}:{port}',
                'time_ms': 30000,
                'timestamp': time.time(),
            }
        except Exception as e:
            logger.error(f"Repeater error: {e}")
            return {
                'error': str(e),
                'time_ms': (time.time() - start_time) * 1000,
                'timestamp': time.time(),
            }
    
    def _build_request(self, method: str, path: str, query: str, 
                       headers: Dict, body: str) -> str:
        """Build raw HTTP request"""
        request_line = f"{method} {path}{'?' + query if query else ''} HTTP/1.1\r\n"
        
        # Default headers
        default_headers = {
            'Host': headers.get('Host', 'localhost'),
            'User-Agent': 'CustomBurp/2.0',
            'Accept': '*/*',
            'Connection': 'close',
        }
        
        # Merge headers
        all_headers = {**default_headers, **headers}
        
        # Remove Content-Length if body present (we'll compute it)
        if body and 'Content-Length' in all_headers:
            all_headers['Content-Length'] = str(len(body.encode('utf-8')))
        elif body:
            all_headers['Content-Length'] = str(len(body.encode('utf-8')))
        
        # Build header lines
        header_lines = ''.join(f"{k}: {v}\r\n" for k, v in all_headers.items())
        
        return f"{request_line}{header_lines}\r\n{body}"
    
    def _parse_response(self, data: bytes, elapsed_ms: float) -> Dict:
        """Parse HTTP response"""
        try:
            text = data.decode('utf-8', errors='replace')
            lines = text.split('\r\n')
            
            if not lines:
                return {}
            
            status_parts = lines[0].split(' ', 2)
            protocol = status_parts[0] if len(status_parts) > 0 else 'HTTP/1.1'
            status_code = int(status_parts[1]) if len(status_parts) > 1 and status_parts[1].isdigit() else 0
            status_text = status_parts[2] if len(status_parts) > 2 else ''
            
            headers = {}
            body_start = -1
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    k, v = line.split(':', 1)
                    headers[k.strip()] = v.strip()
            
            body = ''
            if body_start > 0:
                body = '\r\n'.join(lines[body_start:])
            
            return {
                'status_code': status_code,
                'status_text': status_text,
                'protocol': protocol,
                'headers': headers,
                'body': body,
                'content_type': headers.get('Content-Type', ''),
                'content_length': len(body),
                'raw': text,
                'time_ms': elapsed_ms,
            }
        except Exception as e:
            return {'error': str(e), 'time_ms': elapsed_ms}
    
    def _get_ssl_context(self) -> ssl_mod.SSLContext:
        """Get SSL context for HTTPS"""
        ctx = ssl_mod.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl_mod.CERT_NONE
        return ctx
    
    def _save_to_db(self, result: Dict):
        """Save to database"""
        try:
            req = result['request']
            resp = result.get('response', {})
            
            log_req = {
                'id': result['id'],
                'timestamp': result['timestamp'],
                'method': req['method'],
                'host': req.get('url', '').replace('http://', '').replace('https://', '').split('/')[0],
                'port': 443 if 'https://' in req.get('url', '') else 80,
                'path': urlparse(req['url']).path if req.get('url') else '/',
                'query': urlparse(req['url']).query if req.get('url') else '',
                'headers': req.get('headers', {}),
                'body': req.get('body', ''),
                'engine': 'repeater',
                'tags': [],
                'notes': '',
                'folder': '',
                'is_intercepted': 0,
                'is_modified': 0,
                'response': {
                    'status_code': resp.get('status_code', 0),
                    'status_text': resp.get('status_text', ''),
                    'protocol': resp.get('protocol', 'HTTP/1.1'),
                    'headers': resp.get('headers', {}),
                    'body': resp.get('body', ''),
                    'content_type': resp.get('content_type', ''),
                    'content_length': resp.get('content_length', 0),
                    'timestamp': result['timestamp'],
                    'time_ms': result.get('time_ms', 0),
                }
            }
            self.db.save_request(log_req)
        except Exception as e:
            logger.error(f"DB save error in repeater: {e}")
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get request history"""
        return self._history[-limit:]
    
    def clear_history(self):
        """Clear history"""
        self._history.clear()
