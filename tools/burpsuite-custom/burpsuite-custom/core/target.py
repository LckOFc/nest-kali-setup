"""
CustomBurp - Target Scope Manager
Gerenciamento de escopo e sitemap
"""

import re
import threading
from typing import Dict, List, Set, Optional
from urllib.parse import urlparse, urljoin
import json


class Target:
    """Gerenciamento de escopo e sitemap"""
    
    def __init__(self):
        self.scope = {
            'included_hosts': [],
            'excluded_hosts': [],
            'included_paths': [],
            'excluded_paths': [],
            'included_extensions': [],
            'excluded_extensions': ['.jpg', '.png', '.gif', '.css', '.js', '.ico', '.svg']
        }
        self.sitemap = {}  # host -> set of paths
        self._lock = threading.Lock()
    
    def add_scope(self, host: str, include: bool = True, path: str = None):
        """Adiciona/remover host do escopo"""
        with self._lock:
            if include:
                if host not in self.scope['included_hosts']:
                    self.scope['included_hosts'].append(host)
                if path and host not in self.scope['included_paths']:
                    self.scope['included_paths'].append(path)
            else:
                if host in self.scope['included_hosts']:
                    self.scope['included_hosts'].remove(host)
                if path and path in self.scope['included_paths']:
                    self.scope['included_paths'].remove(path)
    
    def exclude_scope(self, host: str):
        """Exclui host do escopo"""
        with self._lock:
            if host in self.scope['included_hosts']:
                self.scope['included_hosts'].remove(host)
            if host not in self.scope['excluded_hosts']:
                self.scope['excluded_hosts'].append(host)
    
    def is_in_scope(self, url: str) -> bool:
        """Verifica se URL esta no escopo"""
        parsed = urlparse(url)
        host = parsed.hostname or ''
        
        # Verificar exclusoes primeiro (antes de verificar inclusoes)
        for excluded in self.scope['excluded_hosts']:
            if excluded == host or host.endswith('.' + excluded):
                return False
        
        # Se nao tem escopo definido, tudo esta no escopo
        if not self.scope['included_hosts']:
            return True
        
        # Verificar inclusoes
        for included in self.scope['included_hosts']:
            if included == host or host.endswith('.' + included):
                # Verificar caminho
                if self.scope['included_paths']:
                    for path in self.scope['included_paths']:
                        if path in parsed.path:
                            return True
                    # Se tem paths inclusos mas nenhum corresponde, verificar se path está excluído
                    for excl_path in self.scope.get('excluded_paths', []):
                        if excl_path in parsed.path:
                            return False
                    return False  # Path não corresponde a nenhuma inclusão
                return True
        
        return False
    
    def add_to_sitemap(self, url: str):
        """Adiciona URL ao sitemap"""
        parsed = urlparse(url)
        host = parsed.netloc
        
        with self._lock:
            if host not in self.sitemap:
                self.sitemap[host] = set()
            self.sitemap[host].add(parsed.path)
    
    def get_sitemap(self) -> Dict[str, List[str]]:
        """Retorna sitemap"""
        with self._lock:
            return {host: sorted(list(paths)) for host, paths in self.sitemap.items()}
    
    def get_hosts(self) -> List[str]:
        """Retorna hosts no escopo"""
        with self._lock:
            return self.scope['included_hosts'][:]
    
    def get_issues(self, url: str) -> List[Dict]:
        """Verifica issues potenciais em uma URL"""
        issues = []
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Verificar arquivos sensiveis
        sensitive_files = [
            '.env', 'wp-config.php', 'config.php', 'web.config',
            '.git', '.svn', 'backup', 'dump', 'sql',
            'phpinfo.php', 'info.php', 'test.php',
            'admin', 'administrator', 'login', 'signin'
        ]
        
        for sensitive in sensitive_files:
            if sensitive in path:
                issues.append({
                    'type': 'sensitive_file',
                    'severity': 'Medium',
                    'path': url,
                    'description': f'Arquivo/senha possivelmente sensivel detectado: {sensitive}'
                })
        
        # Verificar directory listing
        if path.endswith('/'):
            issues.append({
                'type': 'directory',
                'severity': 'Info',
                'path': url,
                'description': 'Diretorio listado'
            })
        
        # Verificar extensions sensiveis
        sensitive_ext = ['.php', '.asp', '.aspx', '.jsp', '.bak', '.old', '.sql', '.zip', '.tar']
        for ext in sensitive_ext:
            if path.endswith(ext):
                issues.append({
                    'type': 'sensitive_extension',
                    'severity': 'Low',
                    'path': url,
                    'description': f'Extensao sensivel detectada: {ext}'
                })
        
        return issues
    
    def match_url(self, url: str) -> bool:
        """Verifica se URL corresponde ao padrao do escopo"""
        return self.is_in_scope(url)
    
    def load_scope(self, scope_config: Dict):
        """Carrega configuracao de escopo"""
        with self._lock:
            self.scope.update(scope_config)
    
    def save_scope(self) -> Dict:
        """Salva configuracao atual"""
        with self._lock:
            return self.scope.copy()
    
    def clear_scope(self):
        """Limpa escopo"""
        with self._lock:
            self.scope = {
                'included_hosts': [],
                'excluded_hosts': [],
                'included_paths': [],
                'excluded_paths': [],
                'included_extensions': [],
                'excluded_extensions': ['.jpg', '.png', '.gif', '.css', '.js', '.ico', '.svg']
            }
            self.sitemap.clear()


if __name__ == '__main__':
    target = Target()
    
    # Configurar escopo
    target.add_scope('example.com', include=True)
    target.add_scope('api.example.com', include=True)
    target.exclude_scope('cdn.example.com')
    
    # Testar scoping
    urls = [
        'http://example.com/login',
        'http://example.com/admin',
        'http://api.example.com/v1/users',
        'http://cdn.example.com/image.jpg',
        'http://other.com/page'
    ]
    
    print("Scope test:")
    for url in urls:
        in_scope = target.is_in_scope(url)
        print(f"  {url}: {'IN' if in_scope else 'OUT'}")
    
    # Adicionar ao sitemap
    target.add_to_sitemap('http://example.com/login')
    target.add_to_sitemap('http://example.com/admin')
    target.add_to_sitemap('http://example.com/api/users')
    
    print(f"\nSitemap: {target.get_sitemap()}")
    
    # Issues
    issues = target.get_issues('http://example.com/.env')
    print(f"\nIssues for .env: {issues}")
    
    print("\nTarget OK!")
