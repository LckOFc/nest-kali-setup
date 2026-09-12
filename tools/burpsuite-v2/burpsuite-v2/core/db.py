"""
CustomBurp v2 - Database Engine
SQLite com transações, conexões por thread, e índices otimizados
"""

import sqlite3
import threading
import json
import os
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger('custom_burp')


class Database:
    """Engine SQLite para CustomBurp v2"""
    
    SCHEMA_VERSION = 3
    
    def __init__(self, db_path: str = 'custom_burp_v2.db'):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.RLock()
        self._init_database()
        logger.info(f"Database initialized: {db_path}")
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30
            )
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA cache_size=-64000")
            self._local.conn.execute("PRAGMA temp_store=MEMORY")
            self._local.conn.row_factory = sqlite3.Row
            logger.debug("New thread-local DB connection created")
        return self._local.conn
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        conn = self._get_conn()
        conn.execute("BEGIN")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def _init_database(self):
        """Initialize database schema"""
        with self.transaction() as conn:
            c = conn.cursor()
            
            # Requests table
            c.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    method TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL DEFAULT 80,
                    path TEXT NOT NULL,
                    query TEXT,
                    headers TEXT NOT NULL,
                    body TEXT,
                    engine TEXT DEFAULT 'unknown',
                    tags TEXT DEFAULT '[]',
                    notes TEXT DEFAULT '',
                    folder TEXT DEFAULT '',
                    is_intercepted INTEGER DEFAULT 0,
                    is_modified INTEGER DEFAULT 0
                )
            ''')
            
            # Responses table
            c.execute('''
                CREATE TABLE IF NOT EXISTS responses (
                    request_id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    status_code INTEGER,
                    status_text TEXT,
                    headers TEXT NOT NULL,
                    body TEXT,
                    content_type TEXT,
                    content_length INTEGER,
                    time_ms REAL,
                    protocol TEXT DEFAULT 'HTTP/1.1',
                    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
                )
            ''')
            
            # Issues table
            c.execute('''
                CREATE TABLE IF NOT EXISTS issues (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    request_id TEXT,
                    issue_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    description TEXT,
                    evidence TEXT,
                    solution TEXT,
                    patched INTEGER DEFAULT 0,
                    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
                )
            ''')
            
            # Intruder results
            c.execute('''
                CREATE TABLE IF NOT EXISTS intruder_results (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    request_id TEXT NOT NULL,
                    payload_set INTEGER NOT NULL,
                    payload_value TEXT NOT NULL,
                    status_code INTEGER,
                    response_length INTEGER,
                    time_ms REAL,
                    result TEXT,
                    is_highlighted INTEGER DEFAULT 0,
                    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
                )
            ''')
            
            # Sessions table
            c.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    cookies TEXT NOT NULL DEFAULT '{}',
                    tokens TEXT DEFAULT '{}',
                    data TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}'
                )
            ''')
            
            # Collaborator interactions
            c.execute('''
                CREATE TABLE IF NOT EXISTS collab_interactions (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    interaction_type TEXT NOT NULL,
                    data TEXT,
                    source_ip TEXT,
                    full_data TEXT,
                    correlated_request_id TEXT
                )
            ''')
            
            # Targets / Scope
            c.execute('''
                CREATE TABLE IF NOT EXISTS target_scope (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT UNIQUE NOT NULL,
                    port INTEGER DEFAULT 0,
                    included INTEGER DEFAULT 1,
                    added_at REAL NOT NULL
                )
            ''')
            
            # Projects
            c.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    settings TEXT DEFAULT '{}',
                    data_path TEXT
                )
            ''')
            
            # Alerts
            c.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT,
                    evidence TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    request_id TEXT
                )
            ''')
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_requests_time ON requests(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_requests_host ON requests(host)",
                "CREATE INDEX IF NOT EXISTS idx_requests_method ON requests(method)",
                "CREATE INDEX IF NOT EXISTS idx_requests_engine ON requests(engine)",
                "CREATE INDEX IF NOT EXISTS idx_requests_tags ON requests(tags)",
                "CREATE INDEX IF NOT EXISTS idx_responses_status ON responses(status_code)",
                "CREATE INDEX IF NOT EXISTS idx_issues_type ON issues(issue_type)",
                "CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity)",
                "CREATE INDEX IF NOT EXISTS idx_issues_request ON issues(request_id)",
                "CREATE INDEX IF NOT EXISTS idx_intruder_request ON intruder_results(request_id)",
                "CREATE INDEX IF NOT EXISTS idx_collab_type ON collab_interactions(interaction_type)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_sev ON alerts(severity)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_ack ON alerts(acknowledged)",
            ]
            for idx_sql in indexes:
                c.execute(idx_sql)
            
            conn.commit()
        
        logger.info(f"Database schema ready at {self.db_path}")
    
    def close(self):
        """Close thread-local connection"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
    
    # =========================================================================
    # REQUEST/RESPONSE OPERATIONS
    # =========================================================================
    
    def save_request(self, request_data: Dict) -> str:
        """Save a request to the database"""
        with self.transaction() as conn:
            c = conn.cursor()
            req_id = request_data['id']
            
            c.execute('''
                INSERT OR REPLACE INTO requests 
                (id, timestamp, method, host, port, path, query, headers, body, 
                 engine, tags, notes, folder, is_intercepted, is_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                req_id,
                request_data.get('timestamp', 0),
                request_data['method'],
                request_data['host'],
                request_data.get('port', 80),
                request_data['path'],
                request_data.get('query', ''),
                json.dumps(request_data.get('headers', {})),
                request_data.get('body', ''),
                request_data.get('engine', 'unknown'),
                json.dumps(request_data.get('tags', [])),
                request_data.get('notes', ''),
                request_data.get('folder', ''),
                request_data.get('is_intercepted', 0),
                request_data.get('is_modified', 0)
            ))
            
            resp = request_data.get('response', {})
            if resp:
                c.execute('''
                    INSERT OR REPLACE INTO responses
                    (request_id, timestamp, status_code, status_text, headers, body,
                     content_type, content_length, time_ms, protocol)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    req_id,
                    resp.get('timestamp', 0),
                    resp.get('status_code', 0),
                    resp.get('status_text', ''),
                    json.dumps(resp.get('headers', {})),
                    resp.get('body', ''),
                    resp.get('content_type', ''),
                    len(resp.get('body', '')),
                    resp.get('time_ms', 0),
                    resp.get('protocol', 'HTTP/1.1')
                ))
            
            conn.commit()
            return req_id
    
    def get_requests(self, 
                     host: Optional[str] = None,
                     method: Optional[str] = None,
                     status_codes: Optional[List[int]] = None,
                     search: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     engine: Optional[str] = None,
                     limit: int = 200,
                     offset: int = 0,
                     sort_by: str = 'timestamp',
                     sort_order: str = 'DESC') -> List[Dict]:
        """Query requests with filters"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            query = "SELECT * FROM requests WHERE 1=1"
            params = []
            
            if host:
                query += " AND host = ?"
                params.append(host)
            if method:
                query += " AND method = ?"
                params.append(method.upper())
            if status_codes:
                placeholders = ','.join(['?'] * len(status_codes))
                query += f" AND status_code IN ({placeholders})"
                params.extend(status_codes)
            if search:
                query += " AND (path LIKE ? OR body LIKE ? OR headers LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            if tags:
                for tag in tags:
                    query += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            if engine:
                query += " AND engine = ?"
                params.append(engine)
            
            # Join with responses for status code
            query += " LEFT JOIN responses ON requests.id = responses.request_id"
            
            sort_col = sort_by if sort_by in ('timestamp', 'method', 'host', 'path') else 'timestamp'
            query += f" ORDER BY requests.{sort_col} {sort_order}"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            c.execute(query, params)
            rows = c.fetchall()
            
            results = []
            for row in rows:
                r = dict(row)
                if r.get('headers'):
                    try:
                        r['headers'] = json.loads(r['headers'])
                    except:
                        pass
                if r.get('tags'):
                    try:
                        r['tags'] = json.loads(r['tags'])
                    except:
                        pass
                results.append(r)
            
            return results
    
    def get_request(self, req_id: str) -> Optional[Dict]:
        """Get a single request with its response"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            c.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
            req = c.fetchone()
            if not req:
                return None
            
            r = dict(req)
            if r.get('headers'):
                try:
                    r['headers'] = json.loads(r['headers'])
                except:
                    pass
            if r.get('tags'):
                try:
                    r['tags'] = json.loads(r['tags'])
                except:
                    pass
            
            c.execute("SELECT * FROM responses WHERE request_id = ?", (req_id,))
            resp = c.fetchone()
            if resp:
                resp_dict = dict(resp)
                if resp_dict.get('headers'):
                    try:
                        resp_dict['headers'] = json.loads(resp_dict['headers'])
                    except:
                        pass
                r['response'] = resp_dict
            
            return r
    
    def update_request(self, req_id: str, updates: Dict):
        """Update request fields"""
        with self.transaction() as conn:
            c = conn.cursor()
            set_clauses = []
            params = []
            for key, value in updates.items():
                if key in ('headers', 'tags', 'notes', 'folder'):
                    set_clauses.append(f"{key} = ?")
                    params.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
                else:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            params.append(req_id)
            c.execute(f"UPDATE requests SET {', '.join(set_clauses)} WHERE id = ?", params)
            conn.commit()
    
    def delete_request(self, req_id: str):
        """Delete a request and its response"""
        with self.transaction() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM responses WHERE request_id = ?", (req_id,))
            c.execute("DELETE FROM requests WHERE id = ?", (req_id,))
            conn.commit()
    
    def clear_all(self):
        """Clear all data"""
        with self.transaction() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM intruder_results")
            c.execute("DELETE FROM issues")
            c.execute("DELETE FROM responses")
            c.execute("DELETE FROM requests")
            c.execute("DELETE FROM alerts")
            conn.commit()
    
    def get_stats(self) -> Dict:
        """Get statistics"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM requests")
            total_requests = c.fetchone()[0]
            
            c.execute("SELECT COUNT(DISTINCT host) FROM requests")
            unique_hosts = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM requests WHERE engine = 'proxy'")
            proxy_requests = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM requests WHERE engine = 'repeater'")
            repeater_requests = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM intruder_results")
            intruder_requests = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues")
            total_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'Critical'")
            critical_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'High'")
            high_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'Medium'")
            medium_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM issues WHERE severity = 'Low'")
            low_issues = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")
            unack_alerts = c.fetchone()[0]
            
            # Last 60s activity
            import time
            recent = time.time() - 60
            c.execute("SELECT COUNT(*) FROM requests WHERE timestamp > ?", (recent,))
            recent_requests = c.fetchone()[0]
            
            return {
                'total_requests': total_requests,
                'unique_hosts': unique_hosts,
                'proxy_requests': proxy_requests,
                'repeater_requests': repeater_requests,
                'intruder_requests': intruder_requests,
                'total_issues': total_issues,
                'critical_issues': critical_issues,
                'high_issues': high_issues,
                'medium_issues': medium_issues,
                'low_issues': low_issues,
                'unacknowledged_alerts': unack_alerts,
                'recent_requests_60s': recent_requests
            }
    
    # =========================================================================
    # ISSUES OPERATIONS
    # =========================================================================
    
    def save_issue(self, issue_data: Dict) -> str:
        """Save a vulnerability issue"""
        with self.transaction() as conn:
            c = conn.cursor()
            issue_id = issue_data['id']
            
            c.execute('''
                INSERT INTO issues 
                (id, timestamp, request_id, issue_type, severity, confidence,
                 description, evidence, solution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                issue_id,
                issue_data.get('timestamp', 0),
                issue_data.get('request_id', ''),
                issue_data['issue_type'],
                issue_data['severity'],
                issue_data.get('confidence', 'Medium'),
                issue_data.get('description', ''),
                issue_data.get('evidence', ''),
                issue_data.get('solution', '')
            ))
            conn.commit()
            return issue_id
    
    def get_issues(self,
                   severity: Optional[str] = None,
                   issue_type: Optional[str] = None,
                   limit: int = 100,
                   include_patch_info: bool = True) -> List[Dict]:
        """Get issues with filters"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            query = "SELECT * FROM issues WHERE 1=1"
            params = []
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            if issue_type:
                query += " AND issue_type = ?"
                params.append(issue_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            c.execute(query, params)
            rows = c.fetchall()
            
            results = []
            for row in rows:
                issue = dict(row)
                if include_patch_info and issue.get('request_id'):
                    c.execute("SELECT id, path, method FROM requests WHERE id = ?", 
                             (issue['request_id'],))
                    req = c.fetchone()
                    if req:
                        issue['request'] = dict(req)
                results.append(issue)
            
            return results
    
    def clear_issues(self):
        """Clear all issues"""
        with self.transaction() as conn:
            conn.cursor().execute("DELETE FROM issues")
            conn.commit()
    
    # =========================================================================
    # INTRUDER OPERATIONS
    # =========================================================================
    
    def save_intruder_result(self, result_data: Dict) -> str:
        """Save intruder attack result"""
        with self.transaction() as conn:
            c = conn.cursor()
            result_id = result_data['id']
            
            c.execute('''
                INSERT INTO intruder_results
                (id, timestamp, request_id, payload_set, payload_value,
                 status_code, response_length, time_ms, result, is_highlighted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result_id,
                result_data.get('timestamp', 0),
                result_data['request_id'],
                result_data.get('payload_set', 0),
                result_data.get('payload_value', ''),
                result_data.get('status_code', 0),
                result_data.get('response_length', 0),
                result_data.get('time_ms', 0),
                json.dumps(result_data.get('result', {})),
                result_data.get('is_highlighted', 0)
            ))
            conn.commit()
            return result_id
    
    def get_intruder_results(self, request_id: str) -> List[Dict]:
        """Get intruder results for a request"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("""
                SELECT * FROM intruder_results 
                WHERE request_id = ? ORDER BY timestamp
            """, (request_id,))
            rows = c.fetchall()
            return [dict(r) for r in rows]
    
    def clear_intruder_results(self, request_id: str = None):
        """Clear intruder results"""
        with self.transaction() as conn:
            c = conn.cursor()
            if request_id:
                c.execute("DELETE FROM intruder_results WHERE request_id = ?", (request_id,))
            else:
                c.execute("DELETE FROM intruder_results")
            conn.commit()
    
    # =========================================================================
    # SESSION OPERATIONS
    # =========================================================================
    
    def save_session(self, session_data: Dict):
        """Save session data"""
        with self.transaction() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO sessions
                (session_id, name, created_at, updated_at, cookies, tokens, data, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_data['session_id'],
                session_data.get('name', ''),
                session_data.get('created_at', 0),
                session_data.get('updated_at', 0),
                json.dumps(session_data.get('cookies', {})),
                json.dumps(session_data.get('tokens', {})),
                json.dumps(session_data.get('data', {})),
                json.dumps(session_data.get('metadata', {}))
            ))
            conn.commit()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = c.fetchone()
            if not row:
                return None
            s = dict(row)
            for field in ('cookies', 'tokens', 'data', 'metadata'):
                if s.get(field):
                    try:
                        s[field] = json.loads(s[field])
                    except:
                        pass
            return s
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT session_id, name, created_at, updated_at, cookies FROM sessions ORDER BY updated_at DESC")
            return [dict(r) for r in c.fetchall()]
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        with self.transaction() as conn:
            conn.cursor().execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
    
    # =========================================================================
    # COLLABORATOR OPERATIONS
    # =========================================================================
    
    def save_collab_interaction(self, interaction_data: Dict) -> str:
        """Save collaborator interaction"""
        with self.transaction() as conn:
            c = conn.cursor()
            inter_id = interaction_data['id']
            c.execute('''
                INSERT INTO collab_interactions
                (id, timestamp, interaction_type, data, source_ip, full_data, correlated_request_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                inter_id,
                interaction_data.get('timestamp', 0),
                interaction_data.get('type', 'dns'),
                json.dumps(interaction_data.get('data', {})),
                interaction_data.get('source_ip', ''),
                json.dumps(interaction_data.get('full_data', {})),
                interaction_data.get('correlated_request_id', '')
            ))
            conn.commit()
            return inter_id
    
    def get_collab_interactions(self, limit: int = 100) -> List[Dict]:
        """Get collaborator interactions"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("""
                SELECT * FROM collab_interactions 
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            results = []
            for row in c.fetchall():
                r = dict(row)
                if r.get('data'):
                    try:
                        r['data'] = json.loads(r['data'])
                    except:
                        pass
                results.append(r)
            return results
    
    # =========================================================================
    # TARGET / SCOPE
    # =========================================================================
    
    def add_target(self, host: str, port: int = 0, included: bool = True):
        """Add/remove target from scope"""
        with self.transaction() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO target_scope (host, port, included, added_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(host) DO UPDATE SET included = excluded.included, port = excluded.port
            """, (host, port, 1 if included else 0, __import__('time').time()))
            conn.commit()
    
    def get_targets(self) -> List[Dict]:
        """Get target scope"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT host, port, included, added_at FROM target_scope ORDER BY added_at DESC")
            return [dict(r) for r in c.fetchall()]
    
    def clear_targets(self):
        """Clear all targets"""
        with self.transaction() as conn:
            conn.cursor().execute("DELETE FROM target_scope")
            conn.commit()
    
    # =========================================================================
    # PROJECTS
    # =========================================================================
    
    def save_project(self, project_data: Dict):
        """Save project"""
        with self.transaction() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO projects
                (id, name, created_at, updated_at, settings, data_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                project_data['id'],
                project_data['name'],
                project_data.get('created_at', 0),
                project_data.get('updated_at', 0),
                json.dumps(project_data.get('settings', {})),
                project_data.get('data_path', '')
            ))
            conn.commit()
    
    def list_projects(self) -> List[Dict]:
        """List projects"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            return [dict(r) for r in c.fetchall()]
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = c.fetchone()
            return dict(row) if row else None
    
    def delete_project(self, project_id: str):
        """Delete project"""
        with self.transaction() as conn:
            conn.cursor().execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
    
    # =========================================================================
    # ALERTS
    # =========================================================================
    
    def save_alert(self, alert_data: Dict) -> str:
        """Save an alert"""
        with self.transaction() as conn:
            c = conn.cursor()
            alert_id = alert_data['id']
            c.execute('''
                INSERT INTO alerts
                (id, timestamp, alert_type, severity, message, evidence, acknowledged, request_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_id,
                alert_data.get('timestamp', 0),
                alert_data.get('type', 'info'),
                alert_data.get('severity', 'Medium'),
                alert_data.get('message', ''),
                alert_data.get('evidence', ''),
                0,
                alert_data.get('request_id', '')
            ))
            conn.commit()
            return alert_id
    
    def get_alerts(self, severity: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get alerts"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            c.execute(query, params)
            return [dict(r) for r in c.fetchall()]
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        with self.transaction() as conn:
            conn.cursor().execute(
                "UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,)
            )
            conn.commit()
    
    def clear_alerts(self):
        """Clear all alerts"""
        with self.transaction() as conn:
            conn.cursor().execute("DELETE FROM alerts")
            conn.commit()
    
    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================
    
    def export_requests(self, limit: int = 10000) -> List[Dict]:
        """Export requests as JSON"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("""
                SELECT r.*, resp.status_code, resp.headers as resp_headers, resp.body as resp_body
                FROM requests r
                LEFT JOIN responses resp ON r.id = resp.request_id
                ORDER BY r.timestamp DESC LIMIT ?
            """, (limit,))
            results = []
            for row in c.fetchall():
                r = dict(row)
                if r.get('headers'):
                    try:
                        r['headers'] = json.loads(r['headers'])
                    except:
                        pass
                if r.get('tags'):
                    try:
                        r['tags'] = json.loads(r['tags'])
                    except:
                        pass
                results.append(r)
            return results
    
    def count_requests(self, host: Optional[str] = None) -> int:
        """Count total requests"""
        with self._lock:
            conn = self._get_conn()
            c = conn.cursor()
            if host:
                c.execute("SELECT COUNT(*) FROM requests WHERE host = ?", (host,))
            else:
                c.execute("SELECT COUNT(*) FROM requests")
            return c.fetchone()[0]
