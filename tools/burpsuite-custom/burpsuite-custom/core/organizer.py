"""
CustomBurp - Organizer
Organizar, anotear e categorizar requests
"""

import json
import os
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime


class Organizer:
    """Organizador de requests para analise posterior"""
    
    def __init__(self, storage_path: str = 'organizer.json'):
        self.storage_path = storage_path
        self.items: List[Dict] = []
        self.tags: set = set()
        self.folders: Dict[str, List[str]] = {}  # folder -> [item_ids]
        self._use_memory = storage_path == ':memory:'
        self._load()
    
    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = data.get('items', [])
                    self.tags = set(data.get('tags', []))
                    self.folders = data.get('folders', {})
            except:
                self.items = []
                self.tags = set()
                self.folders = {}
    
    def _save(self):
        if self._use_memory:
            return
        data = {
            'items': self.items,
            'tags': list(self.tags),
            'folders': self.folders,
            'saved_at': datetime.now().isoformat()
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add(self, request: Dict, response: Dict = None, notes: str = '',
            tags: List[str] = None, folder: str = 'Geral', starred: bool = False) -> Dict:
        item = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': time.time(),
            'request': request,
            'response': response or {},
            'notes': notes,
            'tags': tags or [],
            'folder': folder,
            'starred': starred
        }
        
        self.items.append(item)
        if tags:
            self.tags.update(tags)
        
        # Adicionar ao folder
        if folder not in self.folders:
            self.folders[folder] = []
        self.folders[folder].append(item['id'])
        
        self._save()
        return item
    
    def remove(self, item_id: str) -> bool:
        self.items = [i for i in self.items if i['id'] != item_id]
        # Remover dos folders
        for folder_ids in self.folders.values():
            if item_id in folder_ids:
                folder_ids.remove(item_id)
        self._save()
        return True
    
    def get(self, item_id: str) -> Optional[Dict]:
        for item in self.items:
            if item['id'] == item_id:
                return item
        return None
    
    def list_items(self, folder: str = None, tag: str = None,
                   starred: bool = None, search: str = None) -> List[Dict]:
        items = self.items
        
        if folder:
            items = [i for i in items if i.get('folder') == folder]
        if tag:
            items = [i for i in items if tag in i.get('tags', [])]
        if starred is not None:
            items = [i for i in items if i.get('starred') == starred]
        if search:
            search_lower = search.lower()
            items = [i for i in items if 
                    search_lower in json.dumps(i.get('request', {})).lower() or
                    search_lower in i.get('notes', '').lower()]
        
        items.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return items
    
    def toggle_star(self, item_id: str) -> Optional[bool]:
        for item in self.items:
            if item['id'] == item_id:
                item['starred'] = not item.get('starred', False)
                self._save()
                return item['starred']
        return None
    
    def add_tag(self, tag: str):
        self.tags.add(tag)
        self._save()
    
    def remove_tag(self, tag: str):
        self.tags.discard(tag)
        self._save()
    
    def get_stats(self) -> Dict:
        folders = {}
        for folder, item_ids in self.folders.items():
            folders[folder] = len(item_ids)
        
        return {
            'total_items': len(self.items),
            'total_tags': len(self.tags),
            'folders': folders,
            'starred_count': sum(1 for i in self.items if i.get('starred')),
            'recent': [
                {
                    'id': i['id'],
                    'method': i.get('request', {}).get('method', 'GET'),
                    'path': i.get('request', {}).get('path', ''),
                    'folder': i.get('folder', 'Geral'),
                    'starred': i.get('starred'),
                    'notes': i.get('notes', '')[:50],
                    'timestamp': i.get('timestamp', 0)
                }
                for i in sorted(self.items, key=lambda x: x.get('timestamp', 0), reverse=True)[:10]
            ]
        }
    
    def export(self, path: str = None) -> str:
        if not path:
            path = f'organizer-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        
        data = {
            'items': self.items,
            'tags': list(self.tags),
            'folders': self.folders,
            'exported_at': datetime.now().isoformat()
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return path
    
    def import_data(self, data: Dict):
        self.items = data.get('items', [])
        self.tags = set(data.get('tags', []))
        self.folders = data.get('folders', {})
        self._save()
    
    def create_folder(self, name: str):
        if name not in self.folders:
            self.folders[name] = []
            self._save()
    
    def move_to_folder(self, item_id: str, new_folder: str):
        for item in self.items:
            if item['id'] == item_id:
                old_folder = item.get('folder', 'Geral')
                if old_folder in self.folders:
                    self.folders[old_folder].remove(item_id)
                item['folder'] = new_folder
                if new_folder not in self.folders:
                    self.folders[new_folder] = []
                self.folders[new_folder].append(item_id)
                self._save()
                return True
        return False


if __name__ == '__main__':
    org = Organizer(storage_path=':memory:')
    
    # Adicionar items
    item1 = org.add(
        request={'method': 'GET', 'path': '/admin', 'headers': {}},
        response={'status_code': 200, 'body': 'ok'},
        notes='Endpoint admin testado',
        tags=['auth', 'critical'],
        folder='Testes Auth'
    )
    
    item2 = org.add(
        request={'method': 'POST', 'path': '/login', 'headers': {}},
        response={'status_code': 401, 'body': 'unauthorized'},
        notes='Teste de login falhou',
        tags=['auth', 'login'],
        folder='Testes Auth'
    )
    
    item3 = org.add(
        request={'method': 'GET', 'path': '/api/users', 'headers': {}},
        notes='API de usuarios',
        tags=['api'],
        folder='API Tests'
    )
    
    print(f"Total items: {len(org.items)}")
    print(f"Tags: {org.tags}")
    print(f"Stats: {org.get_stats()}")
    
    # Listar com filtros
    auth_items = org.list_items(folder='Testes Auth')
    print(f"\nAuth items: {len(auth_items)}")
    for item in auth_items:
        print(f"  - {item['request']['method']} {item['request']['path']} ({item['notes']})")
    
    # Toggle star
    org.toggle_star(item1['id'])
    starred = [i for i in org.items if i.get('starred')]
    print(f"\nStarred: {len(starred)}")
    
    # Export
    path = org.export()
    print(f"Exported to: {path}")
    os.remove(path)
    
    print("\nOrganizer OK!")
