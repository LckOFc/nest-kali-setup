"""
CustomBurp v2 - Logger Engine
Real-time request logging com busca e filtro
"""

import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger('custom_burp.logger')


class Logger:
    """Request/response logger"""
    
    def __init__(self, db, max_entries: int = 50000):
        self.db = db
        self.max_entries = max_entries
        self._callbacks = []
    
    def add_callback(self, callback):
        """Add callback for new requests"""
        self._callbacks.append(callback)
    
    def on_request(self, request_data: Dict):
        """Called when a new request is logged by the proxy"""
        for cb in self._callbacks:
            try:
                cb(request_data)
            except Exception as e:
                logger.error(f"Logger callback error: {e}")
    
    def get_entries(self, 
                    host: Optional[str] = None,
                    method: Optional[str] = None,
                    status_codes: Optional[List[int]] = None,
                    search: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    limit: int = 200,
                    offset: int = 0) -> List[Dict]:
        """Get logged entries with filters"""
        return self.db.get_requests(
            host=host,
            method=method,
            status_codes=status_codes,
            search=search,
            tags=tags,
            limit=limit,
            offset=offset
        )
    
    def get_entry(self, req_id: str) -> Optional[Dict]:
        """Get a single entry"""
        return self.db.get_request(req_id)
    
    def get_hosts(self) -> List[str]:
        """Get list of unique hosts"""
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT DISTINCT host FROM requests ORDER BY host")
            return [row['host'] for row in c.fetchall()]
    
    def get_methods(self) -> List[str]:
        """Get list of unique methods"""
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT DISTINCT method FROM requests ORDER BY method")
            return [row['method'] for row in c.fetchall()]
    
    def get_status_codes(self) -> Dict[int, int]:
        """Get status code distribution"""
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("""
                SELECT status_code, COUNT(*) as count 
                FROM requests r 
                LEFT JOIN responses resp ON r.id = resp.request_id
                GROUP BY status_code 
                ORDER BY count DESC
            """)
            return {row['status_code']: row['count'] for row in c.fetchall() if row['status_code']}
    
    def get_time_range(self) -> Dict:
        """Get time range of logged requests"""
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT MIN(timestamp) as min_ts, MAX(timestamp) as max_ts FROM requests")
            row = c.fetchone()
            if row and row['min_ts']:
                return {
                    'first_request': datetime.fromtimestamp(row['min_ts']).isoformat(),
                    'last_request': datetime.fromtimestamp(row['max_ts']).isoformat(),
                    'span_seconds': row['max_ts'] - row['min_ts']
                }
            return {}
    
    def clear_entries(self):
        """Clear all logged entries"""
        self.db.clear_all()
    
    def export_entries(self, format: str = 'json', 
                       host: Optional[str] = None,
                       limit: int = 10000) -> str:
        """Export entries in specified format"""
        entries = self.get_entries(host=host, limit=limit)
        
        if format == 'json':
            return json.dumps(entries, indent=2, default=str)
        elif format == 'har':
            return self._export_har(entries)
        elif format == 'text':
            return self._export_text(entries)
        else:
            return json.dumps(entries, indent=2, default=str)
    
    def _export_har(self, entries: List[Dict]) -> str:
        """Export as HAR format"""
        pages = [{"startedDateTime": datetime.fromtimestamp(e['timestamp']).isoformat(), 
                  "id": f"page_{e['id']}", "pageTitle": e.get('host', ''), 
                  "pageRef": e.get('host', '')} for e in entries[:1]]
        
        entries_har = []
        for e in entries:
            resp = e.get('response', {})
            entry = {
                "startedDateTime": datetime.fromtimestamp(e['timestamp']).isoformat(),
                "time": resp.get('time_ms', 0),
                "request": {
                    "method": e['method'],
                    "url": f"http://{e['host']}{e['path']}",
                    "headers": [{"name": k, "value": v} for k, v in e.get('headers', {}).items()],
                    "postData": e.get('body', ''),
                },
                "response": {
                    "status": resp.get('status_code', 0),
                    "statusText": resp.get('status_text', ''),
                    "headers": [{"name": k, "value": v} for k, v in resp.get('headers', {}).items()],
                    "content": {"size": len(resp.get('body', '')), "mimeType": resp.get('content_type', '')},
                }
            }
            entries_har.append(entry)
        
        return json.dumps({
            "log": {
                "version": "1.2",
                "creator": {"name": "CustomBurp", "version": "2.0"},
                "pages": pages,
                "entries": entries_har
            }
        }, indent=2)
    
    def _export_text(self, entries: List[Dict]) -> str:
        """Export as plain text"""
        lines = []
        for e in entries:
            resp = e.get('response', {})
            lines.append(f"[{datetime.fromtimestamp(e['timestamp']).strftime('%H:%M:%S')}] "
                        f"{e['method']} {e['host']}{e['path']} -> {resp.get('status_code', '-')} "
                        f"({resp.get('content_length', 0)} bytes)")
        return '\n'.join(lines)
