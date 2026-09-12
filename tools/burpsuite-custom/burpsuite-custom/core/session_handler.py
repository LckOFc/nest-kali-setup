"""
CustomBurp - Session Handler
Gerenciamento de sessoes, cookies e macros
"""

import http.cookies
import time
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime


class Session:
    """Representa uma sessao HTTP"""
    
    def __init__(self, session_id: str = '', cookies: Dict[str, str] = None):
        self.session_id = session_id or str(int(time.time() * 1000))
        self.cookies: Dict[str, 'Cookie'] = {}
        self.headers: Dict[str, str] = {}
        self.auth_type = ''  # 'none', 'basic', 'bearer', 'session'
        self.created_at = time.time()
        self.last_used = time.time()
        self.metadata: Dict = {}
    
    def add_cookie(self, name: str, value: str, domain: str = '', path: str = '/',
                   expires: float = 0, secure: bool = False, http_only: bool = False):
        """Adiciona cookie a sessao"""
        cookie = Cookie(name, value, domain, path, expires, secure, http_only)
        self.cookies[name] = cookie
        self.last_used = time.time()
    
    def get_cookie(self, name: str) -> Optional['Cookie']:
        """Busca cookie por nome"""
        return self.cookies.get(name)
    
    def remove_cookie(self, name: str):
        """Remove cookie"""
        if name in self.cookies:
            del self.cookies[name]
    
    def clear_cookies(self):
        """Limpa todos os cookies"""
        self.cookies.clear()
    
    def get_cookie_header(self) -> str:
        """Retorna header Cookie formatado"""
        parts = []
        for cookie in self.cookies.values():
            if not cookie.is_expired():
                parts.append(f"{cookie.name}={cookie.value}")
        return '; '.join(parts)
    
    def is_expired(self) -> bool:
        """Verifica se sessao expirou (30 min sem uso)"""
        return time.time() - self.last_used > 1800
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'auth_type': self.auth_type,
            'cookie_count': len(self.cookies),
            'created_at': self.created_at,
            'last_used': self.last_used,
            'cookies': {k: v.to_dict() for k, v in self.cookies.items()},
            'headers': self.headers,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        session = cls(data.get('session_id', ''))
        session.auth_type = data.get('auth_type', '')
        session.created_at = data.get('created_at', time.time())
        session.last_used = data.get('last_used', time.time())
        session.metadata = data.get('metadata', {})
        
        for name, cookie_data in data.get('cookies', {}).items():
            session.add_cookie(
                name=name,
                value=cookie_data.get('value', ''),
                domain=cookie_data.get('domain', ''),
                path=cookie_data.get('path', '/'),
                expires=cookie_data.get('expires', 0),
                secure=cookie_data.get('secure', False),
                http_only=cookie_data.get('http_only', False)
            )
        
        return session


class Cookie:
    """Representa um cookie HTTP"""
    
    def __init__(self, name: str, value: str, domain: str = '', path: str = '/',
                 expires: float = 0, secure: bool = False, http_only: bool = False):
        self.name = name
        self.value = value
        self.domain = domain
        self.path = path
        self.expires = expires
        self.secure = secure
        self.http_only = http_only
    
    def is_expired(self) -> bool:
        """Verifica se cookie expirou"""
        if self.expires == 0:
            return False  # Session cookie
        return time.time() > self.expires
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'value': self.value,
            'domain': self.domain,
            'path': self.path,
            'expires': self.expires,
            'secure': self.secure,
            'http_only': self.http_only
        }
    
    def __str__(self) -> str:
        return f"{self.name}={self.value}"


class SessionManager:
    """Gerenciador central de sessoes"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []
    
    def create_session(self, session_id: str = None) -> Session:
        """Cria nova sessao"""
        with self._lock:
            sid = session_id or str(int(time.time() * 1000))
            session = Session(sid)
            self.sessions[sid] = session
            self._notify('created', session)
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Busca sessao por ID"""
        with self._lock:
            return self.sessions.get(session_id)
    
    def add_cookie(self, session_id: str, name: str, value: str, **kwargs) -> bool:
        """Adiciona cookie a sessao"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.add_cookie(name, value, **kwargs)
                session.last_used = time.time()
                self._notify('cookie_added', session)
                return True
        return False
    
    def remove_cookie(self, session_id: str, name: str) -> bool:
        """Remove cookie da sessao"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.remove_cookie(name)
                return True
        return False
    
    def set_header(self, session_id: str, name: str, value: str):
        """Define header na sessao"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.headers[name] = value
                session.last_used = time.time()
    
    def get_session_header(self, session_id: str, name: str) -> Optional[str]:
        """Busca header da sessao"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                return session.headers.get(name)
        return None
    
    def parse_response_cookies(self, session_id: str, set_cookie_header: str):
        """Parseia Set-Cookie header e adiciona as sessoes"""
        session = self.get_session(session_id)
        if not session:
            return
        
        # Parse Set-Cookie
        parts = set_cookie_header.split(';')
        if not parts:
            return
        
        name_value = parts[0].strip()
        if '=' not in name_value:
            return
        
        name, value = name_value.split('=', 1)
        name = name.strip()
        value = value.strip()
        
        # Extrair atributos
        domain = ''
        path = '/'
        expires = 0
        secure = False
        http_only = False
        
        for part in parts[1:]:
            part = part.strip()
            if part.lower() == 'secure':
                secure = True
            elif part.lower() == 'httponly':
                http_only = True
            elif part.lower().startswith('domain='):
                domain = part[7:].strip()
            elif part.lower().startswith('path='):
                path = part[5:].strip()
            elif part.lower().startswith('expires='):
                try:
                    expires_str = part[8:].strip()
                    # Parse date
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(expires_str)
                    expires = dt.timestamp()
                except:
                    pass
        
        session.add_cookie(name, value, domain, path, expires, secure, http_only)
        self._notify('cookie_set', session)
    
    def clean_expired(self) -> int:
        """Remove sessoes e cookies expirados"""
        with self._lock:
            to_remove = []
            for sid, session in self.sessions.items():
                if session.is_expired():
                    to_remove.append(sid)
                else:
                    # Limpar cookies expirados
                    expired_cookies = [name for name, cookie in session.cookies.items() 
                                     if cookie.is_expired()]
                    for name in expired_cookies:
                        session.remove_cookie(name)
            
            for sid in to_remove:
                del self.sessions[sid]
                self._notify('expired', sid)
            
            return len(to_remove)
    
    def import_session(self, session_dict: Dict) -> str:
        """Importa sessao de um dict"""
        session = Session.from_dict(session_dict)
        with self._lock:
            self.sessions[session.session_id] = session
        return session.session_id
    
    def export_session(self, session_id: str) -> Optional[Dict]:
        """Exporta sessao para dict"""
        session = self.get_session(session_id)
        if session:
            return session.to_dict()
        return None
    
    def list_sessions(self) -> List[Dict]:
        """Lista todas as sessoes"""
        with self._lock:
            return [s.to_dict() for s in self.sessions.values()]
    
    def add_callback(self, callback: Callable):
        """Adiciona callback para eventos de sessao"""
        self._callbacks.append(callback)
    
    def _notify(self, event: str, data):
        """Notifica callbacks"""
        for cb in self._callbacks:
            try:
                cb(event, data)
            except:
                pass
    
    def clear_all(self):
        """Limpa todas as sessoes"""
        with self._lock:
            self.sessions.clear()


if __name__ == '__main__':
    manager = SessionManager()
    
    # Criar sessao
    session = manager.create_session()
    print(f"Created session: {session.session_id}")
    
    # Adicionar cookie
    manager.add_cookie(session.session_id, 'session_id', 'abc123', 
                       domain='.example.com', path='/', secure=True, http_only=True)
    manager.add_cookie(session.session_id, 'csrf_token', 'xyz789')
    
    # Set header
    manager.set_header(session.session_id, 'Authorization', 'Bearer token123')
    
    # Verificar
    auth = manager.get_session_header(session.session_id, 'Authorization')
    print(f"Auth header: {auth}")
    
    # Parse Set-Cookie
    manager.parse_response_cookies(session.session_id, 
        'new_session=def456; Domain=.example.com; Path=/; Secure; HttpOnly')
    
    cookie = session.get_cookie('new_session')
    print(f"New cookie: {cookie}")
    
    # List sessions
    sessions = manager.list_sessions()
    print(f"Sessions: {len(sessions)}")
    
    # Export
    exported = manager.export_session(session.session_id)
    print(f"Exported session cookies: {len(exported['cookies'])}")
    
    print("\nSessionHandler OK!")
