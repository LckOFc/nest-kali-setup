"""
CustomBurp - Intruder Completo
Ataque de payload com 4 modos, threads, análise de resultados
"""

import threading
import time
import urllib.request
import urllib.error
import ssl
import json
import re
from typing import Dict, List, Tuple, Optional, Callable


class Intruder:
    """Intruder - Attack tool with payloads (Sniper, Battering Ram, Pitchfork, Cluster Bomb)"""
    
    def __init__(self):
        self.results = []
        self._running = False
        self._lock = threading.Lock()
    
    def parse_positions(self, request_text: str) -> Tuple[str, List[Tuple[int, int]], List[str]]:
        """
        Parsear request text e encontrar posições marcadas com §
        Retorna: (request_sem_markers, positions, payloads)
        """
        positions = []
        # Encontrar todas as marcações §
        pattern = r'§'
        matches = list(re.finditer(pattern, request_text))
        
        if not matches:
            # Se não tem markers, tentar detectar automaticamente
            return request_text, [], []
        
        # Agrupar markers consecutivos como ranges
        i = 0
        while i < len(matches):
            start = matches[i].start()
            # Encontrar o fim do range (§...§)
            j = i
            while j < len(matches) - 1 and matches[j+1].start() == matches[j].start() + 1:
                j += 1
            end = matches[j].start() + 1
            positions.append((start, end))
            i = j + 1
        
        # Remover markers do request
        clean_request = request_text
        for start, end in reversed(positions):
            clean_request = clean_request[:start] + clean_request[end:]
        
        return clean_request, positions, [''] * len(positions)
    
    def attack(
        self,
        request_text: str,
        payloads: List[str],
        mode: str = 'sniper',
        thread_count: int = 10,
        timeout: int = 30,
        callback: Callable = None
    ) -> List[Dict]:
        """
        Executa ataque de intruder
        
        Args:
            request_text: Request HTTP completo com marcas § nas posições
            payloads: Lista de payloads
            mode: 'sniper', 'battering_ram', 'pitchfork', 'cluster_bomb'
            thread_count: Numero de threads
            timeout: Timeout em segundos
            callback: Funcao chamada a cada resultado (result_dict)
        """
        self._running = True
        results = []
        
        # Parsear request e posicoes
        base_request, positions, default_payloads = self.parse_positions(request_text)
        
        if not positions:
            # Se nao tem posicoes, tentar detectar automaticamente no URL ou body
            positions = self._auto_detect_positions(base_request)
        
        # Preparar payload sets baseado no modo
        if mode == 'sniper':
            # 1 set de payloads
            payload_sets = [payloads]
        elif mode == 'battering_ram':
            # Todos os positions usam o mesmo set
            payload_sets = [payloads] * max(len(positions), 1)
        elif mode == 'pitchfork':
            # Cada position tem seu proprio set (se varios sets forem fornecidos)
            if len(payloads) > 0 and isinstance(payloads[0], list):
                payload_sets = payloads[:len(positions)]
                # Preencher com primeiros elementos se faltar
                while len(payload_sets) < len(positions):
                    payload_sets.append([''])
            else:
                payload_sets = [payloads] * max(len(positions), 1)
        elif mode == 'cluster_bomb':
            # Todas combinacoes possiveis
            payload_sets = [payloads] * max(len(positions), 1)
        else:
            payload_sets = [payloads]
        
        # Gerar combinacoes
        combinations = self._generate_combinations(payload_sets, mode)
        
        total = len(combinations)
        logger_info(f"Intruder {mode}: {total} combinations, {thread_count} threads")
        
        # Dividir entre threads
        chunks = [[] for _ in range(thread_count)]
        for i, combo in enumerate(combinations):
            chunks[i % thread_count].append((i, combo))
        
        # Executar
        all_results = []
        threads = []
        
        def worker(chunk):
            local_results = []
            for idx, combo in chunk:
                if not self._running:
                    break
                
                # Aplicar payload
                modified_request = self._apply_combo(base_request, combo, positions)
                
                # Enviar
                resp = self._send_request(modified_request, timeout)
                
                # Analisar diferenca
                diff = self._analyze_diff(resp, combo, positions)
                
                result = {
                    'index': idx,
                    'payload': ' | '.join(combo) if combo else '',
                    'status_code': resp.get('status_code', 0),
                    'response_length': resp.get('length', 0),
                    'time_ms': resp.get('time_ms', 0),
                    'diff_length': diff['length_diff'],
                    'diff_status': diff['status_diff'],
                    'headers': resp.get('headers', {}),
                    'body_preview': resp.get('body', '')[:500],
                    'success': resp.get('status_code', 0) != 0
                }
                
                local_results.append(result)
                
                if callback:
                    callback(result)
            
            return local_results
        
        for chunk in chunks:
            if chunk:
                t = threading.Thread(target=lambda c=chunk: all_results.extend(worker(c)))
                t.start()
                threads.append(t)
        
        for t in threads:
            t.join()
        
        self.results = all_results
        self._running = False
        
        logger_info(f"Intruder complete: {len(all_results)} results")
        return all_results
    
    def _auto_detect_positions(self, request: str) -> List[Tuple[int, int]]:
        """Detectar posicoes automaticas no request"""
        positions = []
        
        # Procurar por parametros URL (?key=value)
        if '?' in request:
            url_part = request.split('\r\n')[0]
            if '?' in url_part:
                query_start = url_part.find('?') + 1
                # Encontrar primeiro parametro
                for match in re.finditer(r'[?&](\w+)=', request):
                    start = match.start()
                    end = match.end()
                    positions.append((start, end))
        
        # Se nao encontrou nada, marcar o body
        if not positions and '\r\n\r\n' in request:
            body_start = request.find('\r\n\r\n') + 4
            positions.append((body_start, body_start))
        
        return positions
    
    def _apply_combo(self, base_request: str, combo: List[str], positions: List[Tuple[int, int]]) -> str:
        """Aplicar combinacao de payloads no request"""
        result = base_request
        
        # Aplicar da direita para esquerda para manter indices
        for i, (start, end) in enumerate(reversed(positions)):
            if i < len(combo):
                payload = combo[len(combo) - 1 - i] if i < len(combo) else ''
                result = result[:start] + payload + result[end:]
        
        return result
    
    def _generate_combinations(self, payload_sets: List[List[str]], mode: str) -> List[List[str]]:
        """Gerar combinacoes de payloads"""
        if mode == 'cluster_bomb':
            # Todas combinacoes
            from itertools import product
            return [list(combo) for combo in product(*payload_sets)]
        elif mode == 'pitchfork':
            # Paralelo, ate o menor set
            min_len = min(len(ps) for ps in payload_sets) if payload_sets else 0
            return [[ps[i] for ps in payload_sets] for i in range(min_len)]
        else:
            # Sniper e Battering Ram: um set por vez
            return [[p] for p in payload_sets[0]] if payload_sets else []
    
    def _send_request(self, request_text: str, timeout: int = 30) -> Dict:
        """Enviar request e retornar response"""
        try:
            lines = request_text.strip().split('\r\n')
            if not lines:
                return {'status_code': 0, 'length': 0, 'time_ms': 0, 'body': 'Empty request'}
            
            first_line = lines[0].split(' ')
            method = first_line[0].upper()
            path = first_line[1] if len(first_line) > 1 else '/'
            
            # Parse headers
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
            
            # Determinar URL
            host = headers.get('Host', 'localhost')
            scheme = 'https' if host.endswith(':443') or ':443' in host else 'http'
            port = 443 if scheme == 'https' else 80
            if ':' in host:
                h, p = host.rsplit(':', 1)
                try:
                    port = int(p)
                except:
                    pass
                host = h
            
            url = f"{scheme}://{host}:{port}{path}"
            
            # Preparar request
            req = urllib.request.Request(url, method=method)
            for k, v in headers.items():
                if k.lower() not in ('host', 'content-length'):
                    req.add_header(k, v)
            
            data = body.encode('utf-8') if body else None
            if data and 'Content-Type' not in headers:
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            # Enviar
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            start = time.time()
            resp = urllib.request.urlopen(req, data=data, timeout=timeout, context=ctx)
            elapsed = (time.time() - start) * 1000
            
            resp_body = resp.read().decode('utf-8', errors='replace')
            
            return {
                'status_code': resp.status,
                'length': len(resp_body),
                'time_ms': round(elapsed, 2),
                'headers': dict(resp.headers),
                'body': resp_body
            }
            
        except urllib.error.HTTPError as e:
            elapsed = (time.time() - start) * 1000 if 'start' in dir() else 0
            try:
                body = e.read().decode('utf-8', errors='replace')
            except:
                body = str(e)
            return {
                'status_code': e.code,
                'length': len(body),
                'time_ms': round(elapsed, 2),
                'headers': dict(e.headers) if e.headers else {},
                'body': body
            }
        except Exception as e:
            return {
                'status_code': 0,
                'length': 0,
                'time_ms': 0,
                'headers': {},
                'body': f'Error: {str(e)}'
            }
    
    def _analyze_diff(self, resp: Dict, combo: List[str], positions: List[Tuple[int, int]]) -> Dict:
        """Analisar diferencas na response"""
        return {
            'length_diff': resp.get('length', 0),
            'status_diff': resp.get('status_code', 0),
            'time_diff': resp.get('time_ms', 0)
        }
    
    def stop(self):
        """Para o ataque"""
        self._running = False
    
    def get_results(self) -> List[Dict]:
        """Retorna resultados do ultimo ataque"""
        return self.results
    
    def clear(self):
        """Limpa resultados"""
        self.results = []


def logger_info(msg: str):
    import logging
    logging.getLogger('custom_burp').info(msg)


if __name__ == '__main__':
    # Teste rapido
    intruder = Intruder()
    
    test_request = "GET /search?q=test§HTTP/1.1\r\nHost: httpbin.org\r\n"
    
    payloads = ['admin', 'root', 'test123', 'password']
    
    print("Testing Intruder...")
    results = intruder.attack(test_request, payloads, mode='sniper', thread_count=5)
    print(f"Results: {len(results)}")
    for r in results[:3]:
        print(f"  Payload: {r['payload']}, Status: {r['status_code']}, Length: {r['response_length']}")
    
    print("Intruder test complete!")
