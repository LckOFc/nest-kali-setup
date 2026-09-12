"""
CustomBurp - Logger Centralizado
Registro completo de todas as requisicoes e respostas
"""

import sqlite3
import json
import time
import hashlib
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import defaultdict


class BurpLogger:
    """Logger centralizado para CustomBurp"""
    
    def __init__(self, db_path: str = 'custom_burp.log.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._conn = None
        self._init_db()
        self._handlers = []
        self._filters = []
        self._stats = defaultdict(int)
    
    def _get_conn(self):
        """Get or create persistent connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self):
        """Inicializa banco de dados"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            timestamp REAL,
            direction TEXT,
            method TEXT,
            host TEXT,
            port INTEGER,
            path TEXT,
            query TEXT,
            request_headers TEXT,
            request_body TEXT,
            response_status INTEGER,
            response_headers TEXT,
            response_body TEXT,
            response_time_ms REAL,
            content_type TEXT,
            tags TEXT,
            notes TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT,
            created REAL,
            request_count INTEGER,
            issue_count INTEGER,
            data TEXT
        )''')
        
        c.execute('CREATE INDEX IF NOT EXISTS idx_entries_time ON entries(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_entries_host ON entries(host)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_entries_method ON entries(method)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_entries_tags ON entries(tags)')
        
        conn.commit()
        
    
    def log(
        self,
        request: Dict,
        response: Dict = None,
        direction: str = 'request',
        tags: List[str] = None,
        notes: str = '',
        session_id: str = None
    ) -> str:
        """
        Registra uma entrada no logger
        
        Args:
            request: Dict com dados da request
            response: Dict com dados da response (opcional)
            direction: 'request' ou 'response'
            tags: Lista de tags
            notes: Notas
            session_id: ID da sessao
        
        Returns:
            ID da entrada
        """
        entry_id = hashlib.md5(f"{request.get('method','')}${request.get('path','')}${time.time()}".encode()).hexdigest()[:12]
        
        conn = self._get_conn()
        c = conn.cursor()
        
        req_headers = json.dumps(request.get('headers', {}))
        req_body = request.get('body', '')
        
        resp_status = response.get('status_code', 0) if response else 0
        resp_headers = json.dumps(response.get('headers', {})) if response else '{}'
        resp_body = response.get('body', '') if response else ''
        resp_time = response.get('time_ms', 0) if response else 0
        
        c.execute('''INSERT OR REPLACE INTO entries 
            (id, timestamp, direction, method, host, port, path, query,
             request_headers, request_body, response_status, response_headers, 
             response_body, response_time_ms, content_type, tags, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                entry_id, time.time(), direction,
                request.get('method', ''),
                request.get('host', ''),
                request.get('port', 80),
                request.get('path', '/'),
                request.get('query', ''),
                req_headers, req_body,
                resp_status, resp_headers, resp_body, resp_time,
                request.get('content_type', ''),
                json.dumps(tags or []),
                notes
            ))
        
        conn.commit()
        
        
        self._stats['total'] += 1
        self._stats[f"method_{request.get('method', 'UNKNOWN')}"] += 1
        
        # Notificar handlers
        for handler in self._handlers:
            try:
                handler(entry_id, request, response)
            except:
                pass
        
        # Aplicar filtros
        for filt in self._filters:
            if filt(request, response):
                self._on_filter_match(entry_id, request, response)
        
        return entry_id
    
    def _on_filter_match(self, entry_id: str, request: Dict, response: Dict):
        """Chamado quando um filtro corresponde"""
        pass  # Hook para subclasses
    
    def add_handler(self, handler: Callable):
        """Adiciona handler para novas entradas"""
        self._handlers.append(handler)
    
    def add_filter(self, filter_fn: Callable[[Dict, Dict], bool]):
        """Adiciona filtro (retorna True para aplicar)"""
        self._filters.append(filter_fn)
    
    def remove_filter(self, filter_fn: Callable):
        """Remove filtro"""
        if filter_fn in self._filters:
            self._filters.remove(filter_fn)
    
    def get_entries(
        self,
        host: str = None,
        method: str = None,
        min_status: int = None,
        max_status: int = None,
        search: str = None,
        tag: str = None,
        limit: int = 100,
        offset: int = 0,
        direction: str = None
    ) -> List[Dict]:
        """Busca entradas no logger"""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT * FROM entries WHERE 1=1"
        params = []
        
        if host:
            query += " AND host = ?"
            params.append(host)
        if method:
            query += " AND method = ?"
            params.append(method.upper())
        if min_status:
            query += " AND response_status >= ?"
            params.append(min_status)
        if max_status:
            query += " AND response_status <= ?"
            params.append(max_status)
        if search:
            query += " AND (path LIKE ? OR request_body LIKE ? OR response_body LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")
        if direction:
            query += " AND direction = ?"
            params.append(direction)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        c.execute(query, params)
        rows = c.fetchall()
        
        results = []
        for row in rows:
            entry = dict(row)
            # Parse JSON fields
            for field in ['request_headers', 'response_headers', 'tags']:
                if entry.get(field):
                    try:
                        entry[field] = json.loads(entry[field])
                    except:
                        pass
            results.append(entry)
        
        
        return results
    
    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """Busca entrada por ID"""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = c.fetchone()
        
        
        if row:
            entry = dict(row)
            for field in ['request_headers', 'response_headers', 'tags']:
                if entry.get(field):
                    try:
                        entry[field] = json.loads(entry[field])
                    except:
                        pass
            return entry
        return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """Remove entrada"""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
        
        return c.rowcount > 0
    
    def clear_entries(self):
        """Limpa todas as entradas"""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM entries")
        conn.commit()
        
    
    def get_stats(self) -> Dict:
        """Retorna estatisticas"""
        conn = self._get_conn()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM entries")
        total = c.fetchone()[0]
        
        c.execute("SELECT COUNT(DISTINCT host) FROM entries")
        unique_hosts = c.fetchone()[0]
        
        c.execute("SELECT method, COUNT(*) FROM entries GROUP BY method ORDER BY COUNT(*) DESC")
        methods = {row[0]: row[1] for row in c.fetchall()}
        
        c.execute("SELECT response_status, COUNT(*) FROM entries WHERE response_status > 0 GROUP BY response_status ORDER BY COUNT(*) DESC")
        statuses = {str(row[0]): row[1] for row in c.fetchall()}
        
        
        
        return {
            'total_entries': total,
            'unique_hosts': unique_hosts,
            'methods': methods,
            'status_codes': statuses,
            'internal_stats': dict(self._stats)
        }
    
    def export(self, format: str = 'json', host: str = None, limit: int = 1000) -> str:
        """Exporta entradas"""
        entries = self.get_entries(host=host, limit=limit)
        
        if format == 'json':
            return json.dumps(entries, indent=2, ensure_ascii=False, default=str)
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            if entries:
                writer = csv.DictWriter(output, fieldnames=entries[0].keys())
                writer.writeheader()
                writer.writerows(entries)
            return output.getvalue()
        elif format == 'har':
            return self._export_har(entries)
        else:
            return json.dumps(entries, default=str)
    
    def _export_har(self, entries: List[Dict]) -> str:
        """Exporta formato HAR"""
        har = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'CustomBurp Logger'},
                'entries': []
            }
        }
        
        for entry in entries:
            har_entry = {
                'startedDateTime': datetime.fromtimestamp(entry['timestamp']).isoformat(),
                'time': entry.get('response_time_ms', 0),
                'request': {
                    'method': entry.get('method', 'GET'),
                    'url': f"http://{entry.get('host', '')}{entry.get('path', '/')}",
                    'headers': entry.get('request_headers', []),
                    'postData': entry.get('request_body', '')
                },
                'response': {
                    'status': entry.get('response_status', 0),
                    'headers': entry.get('response_headers', []),
                    'content': {
                        'text': entry.get('response_body', '')
                    }
                }
            }
            har['log']['entries'].append(har_entry)
        
        return json.dumps(har, indent=2)
    
    def get_unique_hosts(self) -> List[str]:
        """Retorna lista de hosts unicos"""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT DISTINCT host FROM entries ORDER BY host")
        hosts = [row[0] for row in c.fetchall()]
        
        return hosts


if __name__ == '__main__':
    logger = BurpLogger(':memory:')
    
    # Testar log
    for i in range(5):
        entry_id = logger.log(
            request={
                'method': 'GET',
                'host': 'example.com',
                'port': 80,
                'path': f'/test{i}',
                'headers': {'User-Agent': 'CustomBurp'},
                'body': ''
            },
            response={
                'status_code': 200,
                'headers': {'Content-Type': 'text/html'},
                'body': f'<html>Test {i}</html>',
                'time_ms': 50 + i * 10
            },
            tags=['test'],
            notes=f'Test entry {i}'
        )
        print(f"Logged: {entry_id}")
    
    # Stats
    stats = logger.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")
    
    # Busca
    entries = logger.get_entries(host='example.com', limit=10)
    print(f"\nEntries found: {len(entries)}")
    for e in entries[:3]:
        print(f"  {e['method']} {e['path']} -> {e['response_status']}")
    
    print("\nLogger OK!")
