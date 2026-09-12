"""
CustomBurp v2 - Target/Scope Manager
Manages target scope and sitemap
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger('custom_burp.target')


class Target:
    """Target scope management"""
    
    def __init__(self, db):
        self.db = db
    
    def add_host(self, host: str, port: int = 0, included: bool = True):
        """Add host to target scope"""
        self.db.add_target(host, port, included)
    
    def remove_host(self, host: str):
        """Remove host from target scope"""
        self.db.add_target(host, included=False)
    
    def get_scope(self) -> Dict:
        """Get current target scope"""
        targets = self.db.get_targets()
        included = [t for t in targets if t['included']]
        excluded = [t for t in targets if not t['included']]
        
        return {
            'included_hosts': [{'host': t['host'], 'port': t['port']} for t in included],
            'excluded_hosts': [{'host': t['host'], 'port': t['port']} for t in excluded],
            'total_included': len(included),
            'total_excluded': len(excluded),
        }
    
    def get_sitemap(self, host: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        """Get sitemap from logged requests"""
        requests = self.db.get_requests(host=host, limit=limit)
        
        sitemap = {}
        for req in requests:
            h = req.get('host', 'unknown')
            if h not in sitemap:
                sitemap[h] = {'paths': [], 'methods': set(), 'statuses': set()}
            
            sitemap[h]['paths'].append(req.get('path', '/'))
            sitemap[h]['methods'].add(req.get('method', 'GET'))
            resp = req.get('response', {})
            if resp:
                sitemap[h]['statuses'].add(resp.get('status_code', 0))
        
        # Convert sets to lists for JSON
        result = {}
        for h, data in sitemap.items():
            result[h] = {
                'paths': sorted(set(data['paths']))[:100],
                'methods': sorted(data['methods']),
                'statuses': sorted(data['statuses']),
            }
        
        return result
    
    def is_in_scope(self, host: str) -> bool:
        """Check if host is in scope"""
        targets = self.db.get_targets()
        if not targets:
            return True  # No scope = everything is in scope
        
        for t in targets:
            if t['host'] == host and t['included']:
                return True
        return False
    
    def clear_scope(self):
        """Clear target scope"""
        self.db.clear_targets()
