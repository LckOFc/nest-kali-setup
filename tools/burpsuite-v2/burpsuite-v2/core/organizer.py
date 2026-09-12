"""
CustomBurp v2 - Organizer
Tag/folder/note management for requests
"""

import json
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('custom_burp.organizer')


class Organizer:
    """Organize requests with tags, folders, and notes"""
    
    def __init__(self, db):
        self.db = db
        self._folders = {}
        self._load_folders()
    
    def _load_folders(self):
        """Load folder structure from DB"""
        try:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT DISTINCT folder FROM requests WHERE folder != '' AND folder IS NOT NULL")
            self._folders = {row['folder']: [] for row in c.fetchall()}
        except:
            self._folders = {}
    
    def add_tag(self, request_id: str, tag: str):
        """Add a tag to a request"""
        req = self.db.get_request(request_id)
        if req:
            tags = req.get('tags', [])
            if tag not in tags:
                tags.append(tag)
                self.db.update_request(request_id, {'tags': tags})
    
    def remove_tag(self, request_id: str, tag: str):
        """Remove a tag from a request"""
        req = self.db.get_request(request_id)
        if req:
            tags = [t for t in req.get('tags', []) if t != tag]
            self.db.update_request(request_id, {'tags': tags})
    
    def set_folder(self, request_id: str, folder: str):
        """Set folder for a request"""
        self.db.update_request(request_id, {'folder': folder})
        if folder not in self._folders:
            self._folders[folder] = []
        if request_id not in self._folders[folder]:
            self._folders[folder].append(request_id)
    
    def set_notes(self, request_id: str, notes: str):
        """Set notes for a request"""
        self.db.update_request(request_id, {'notes': notes})
    
    def get_items(self, folder: Optional[str] = None, tag: Optional[str] = None,
                  search: Optional[str] = None) -> List[Dict]:
        """Get organized items"""
        kwargs = {}
        if folder:
            kwargs['search'] = f"folder:{folder}"
        if tag:
            kwargs['tags'] = [tag]
        if search and not folder:
            kwargs['search'] = search
        
        items = self.db.get_requests(limit=200, **kwargs)
        return items
    
    def get_tags(self) -> List[str]:
        """Get all unique tags"""
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT DISTINCT tags FROM requests WHERE tags != '[]' AND tags IS NOT NULL")
            tags = set()
            for row in c.fetchall():
                try:
                    row_tags = json.loads(row['tags'])
                    tags.update(row_tags)
                except:
                    pass
            return sorted(tags)
    
    def get_folders(self) -> List[str]:
        """Get all folders"""
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT DISTINCT folder FROM requests WHERE folder != '' AND folder IS NOT NULL")
            return [row['folder'] for row in c.fetchall()]
    
    def count_by_tag(self, tag: str) -> int:
        """Count items with a tag"""
        count = 0
        with self.db._lock:
            conn = self.db._get_conn()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM requests WHERE tags LIKE ?", (f'%{tag}%',))
            count = c.fetchone()[0]
        return count
