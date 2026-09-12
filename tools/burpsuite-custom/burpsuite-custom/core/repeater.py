"""
CustomBurp - Repeater
Envio manual de requests HTTP com controle total
"""

import urllib.request
import urllib.error
import json
import ssl
import time
from typing import Dict, Optional, Tuple


class Repeater:
    """Ferraterra Repeater - Envio manual de requests HTTP"""
    
    def __init__(self):
        self.history = []
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE
    
    def send(self, method: str, url: str, headers: Dict[str, str] = None,
             body: str = '', follow_redirects: bool = True,
             timeout: int = 30) -> Dict:
        """
        Envia request HTTP e retorna response
        
        Returns:
            Dict com status_code, headers, body, time_ms, url_final
        """
        start = time.time()
        
        # Parsear URL
        if not url.startswith('http'):
            url = 'http://' + url
        
        parsed = self._parse_url(url)
        target_url = f"{parsed['scheme']}://{parsed['host']}:{parsed['port']}{parsed['path']}"
        if parsed['query']:
            target_url += f"?{parsed['query']}"
        
        # Preparar request
        req = urllib.request.Request(target_url, method=method.upper())
        
        # Adicionar headers
        default_headers = {
            'User-Agent': 'CustomBurp-Repeater/1.0',
            'Accept': '*/*',
        }
        if headers:
            default_headers.update(headers)
        
        # Remover Host duplicado
        if 'Host' in default_headers:
            del default_headers['Host']
        
        for k, v in default_headers.items():
            req.add_header(k, v)
        
        # Body
        data = None
        if body:
            data = body.encode('utf-8')
            if 'Content-Type' not in default_headers:
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        # Enviar
        final_url = target_url
        status_code = 0
        response_headers = {}
        response_body = ''
        
        try:
            if follow_redirects:
                # Permitir redirects
                handler = urllib.request.HTTPRedirectHandler()
                opener = urllib.request.build_opener(handler)
                resp = opener.open(req, data=data, timeout=timeout)
            else:
                # Desabilitar redirects
                class NoRedirect(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self, req, fp, code, msg, headers, newurl):
                        return None
                    def http_error_302(self, req, fp, code, msg, headers):
                        fp.close()
                        raise urllib.error.HTTPError(newurl, code, msg, headers, fp)
                    def http_error_301(self, req, fp, code, msg, headers):
                        fp.close()
                        raise urllib.error.HTTPError(newurl, code, msg, headers, fp)
                    def http_error_303(self, req, fp, code, msg, headers):
                        fp.close()
                        raise urllib.error.HTTPError(newurl, code, msg, headers, fp)
                    def http_error_307(self, req, fp, code, msg, headers):
                        fp.close()
                        raise urllib.error.HTTPError(newurl, code, msg, headers, fp)
                
                opener = urllib.request.build_opener(NoRedirect)
                resp = opener.open(req, data=data, timeout=timeout)
            
            response_headers = dict(resp.headers)
            response_body = resp.read().decode('utf-8', errors='replace')
            status_code = resp.status
            final_url = resp.url if hasattr(resp, 'url') else target_url
            
        except urllib.error.HTTPError as e:
            status_code = e.code
            response_headers = dict(e.headers) if e.headers else {}
            try:
                response_body = e.read().decode('utf-8', errors='replace')
            except:
                response_body = str(e)
            final_url = e.url if hasattr(e, 'url') else target_url
            
        except urllib.error.URLError as e:
            status_code = 0
            response_body = f"Connection Error: {e.reason}"
            
        except Exception as e:
            status_code = 0
            response_body = f"Error: {str(e)}"
        
        elapsed_ms = (time.time() - start) * 1000
        
        result = {
            'method': method.upper(),
            'url': target_url,
            'final_url': final_url,
            'status_code': status_code,
            'headers': response_headers,
            'body': response_body,
            'time_ms': round(elapsed_ms, 2),
            'sent_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.history.append(result)
        return result
    
    def send_raw(self, raw_request: str) -> Dict:
        """
        Envia request raw (formato HTTP completo)
        """
        import re
        
        lines = raw_request.strip().split('\r\n')
        if not lines:
            return {'error': 'Request vazio'}
        
        # Parsear linha de início
        first_line = lines[0].split(' ')
        if len(first_line) < 2:
            return {'error': 'Formato de request inválido'}
        
        method = first_line[0].upper()
        path = first_line[1]
        
        # Parsear headers
        headers = {}
        body_start = -1
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                body_start = i + 1
                break
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip()] = v.strip()
        
        # Body
        body = ''
        if body_start > 0:
            body = '\r\n'.join(lines[body_start:])
        
        # Determinar URL
        host = headers.get('Host', 'localhost')
        scheme = 'https' if ':443' in host or host.endswith(':443') else 'http'
        port = 443 if ':443' in host else 80
        if ':' in host:
            h, p = host.rsplit(':', 1)
            try:
                port = int(p)
            except:
                pass
            host = h
        
        url = f"{scheme}://{host}:{port}{path}"
        
        return self.send(method, url, headers=headers, body=body)
    
    def save_request(self, method: str, url: str, headers: Dict, body: str,
                     name: str = '') -> Dict:
        """Salva request para reuso"""
        request = {
            'name': name or f"Request {len(self.history) + 1}",
            'method': method,
            'url': url,
            'headers': headers,
            'body': body,
            'saved_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        return request
    
    def _parse_url(self, url: str) -> Dict:
        """Parsear URL"""
        scheme = 'http'
        host = 'localhost'
        port = 80
        path = '/'
        query = ''
        
        # Scheme
        if '://' in url:
            scheme, url = url.split('://', 1)
        
        # Host e path
        if '/' in url:
            host_part, rest = url.split('/', 1)
            path = '/' + rest
        else:
            host_part = url
        
        # Query
        if '?' in path:
            path, query = path.split('?', 1)
        
        # Port
        if ':' in host_part:
            host, port_str = host_part.rsplit(':', 1)
            try:
                port = int(port_str)
            except:
                pass
        else:
            host = host_part
        
        if scheme == 'https':
            port = 443
        
        return {'scheme': scheme, 'host': host, 'port': port, 'path': path, 'query': query}


if __name__ == '__main__':
    rep = Repeater()
    
    # Teste
    result = rep.send('GET', 'http://httpbin.org/get', timeout=10)
    print(f"Status: {result['status_code']}")
    print(f"Time: {result['time_ms']}ms")
    print(f"Body preview: {result['body'][:200]}...")
