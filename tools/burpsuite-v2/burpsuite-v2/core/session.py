"""
CustomBurp v2 - Session Manager
Manages cookies and tokens across requests
"""

import json
import time
import logging
import uuid
from typing import Dict, List, Optional

logger = logging.getLogger('custom_burp.session')


class SessionManager:
    """Session management for cookies and tokens"""
    
    def __init__(self, db):
        self.db = db
        self._active_session: Optional[str] = None
    
    def create_session(self, name: str = '') -> Dict:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        now = time.time()
        
        session_data = {
            'session_id': session_id,
            'name': name or f'Session {session_id[:8]}',
            'created_at': now,
            'updated_at': now,
            'cookies': {},
            'tokens': {},
            'data': {},
            'metadata': {},
        }
        
        self.db.save_session(session_data)
        self._active_session = session_id
        
        logger.info(f"Session created: {session_id}")
        return session_data
    
    def get_active_session(self) -> Optional[Dict]:
        """Get the currently active session"""
        if self._active_session:
            return self.db.get_session(self._active_session)
        return None
    
    def set_session(self, session_id: str):
        """Set active session"""
        self._active_session = session_id
    
    def add_cookie(self, name: str, value: str, domain: str = '', 
                   path: str = '/', expires: int = 0, secure: bool = True,
                   http_only: bool = True):
        """Add a cookie to the active session"""
        if not self._active_session:
            self.create_session()
        
        session = self.db.get_session(self._active_session)
        if not session:
            return
        
        cookies = session.get('cookies', {})
        cookies[name] = {
            'value': value,
            'domain': domain,
            'path': path,
            'expires': expires,
            'secure': secure,
            'http_only': http_only,
            'created_at': time.time()
        }
        
        self.db.save_session({
            **session,
            'cookies': cookies,
            'updated_at': time.time()
        })
    
    def add_token(self, token_type: str, value: str, metadata: Dict = None):
        """Add an auth token to the active session"""
        if not self._active_session:
            self.create_session()
        
        session = self.db.get_session(self._active_session)
        if not session:
            return
        
        tokens = session.get('tokens', {})
        tokens[token_type] = {
            'value': value,
            'type': token_type,
            'added_at': time.time(),
            **(metadata or {})
        }
        
        self.db.save_session({
            **session,
            'tokens': tokens,
            'updated_at': time.time()
        })
    
    def get_session_headers(self) -> Dict:
        """Get headers for the active session (cookies + auth tokens)"""
        session = self.get_active_session()
        if not session:
            return {}
        
        headers = {}
        
        # Add cookies
        cookies = session.get('cookies', {})
        if cookies:
            cookie_str = '; '.join(f"{k}={v['value']}" for k, v in cookies.items())
            headers['Cookie'] = cookie_str
        
        # Add auth tokens
        tokens = session.get('tokens', {})
        if 'bearer' in tokens:
            headers['Authorization'] = f"Bearer {tokens['bearer']['value']}"
        elif 'token' in tokens:
            headers['Authorization'] = f"Token {tokens['token']['value']}"
        
        return headers
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
        return self.db.list_sessions()
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        self.db.delete_session(session_id)
        if self._active_session == session_id:
            self._active_session = None
    
    def clear_session(self):
        """Clear current session"""
        if self._active_session:
            self.delete_session(self._active_session)
