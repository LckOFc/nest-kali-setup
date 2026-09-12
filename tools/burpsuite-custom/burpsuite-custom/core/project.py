"""
CustomBurp - Project Manager
Salvar e carregar projetos completos
"""

import json
import os
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime


class ProjectManager:
    """Gerenciador de projetos CustomBurp"""
    
    def __init__(self, projects_dir: str = 'projects'):
        self.projects_dir = projects_dir
        self.current_project = None
        self._projects: Dict[str, Dict] = {}
        self._use_memory = projects_dir == ':memory:'
        self._load_projects()
    
    def _load_projects(self):
        """Carrega lista de projetos"""
        if os.path.exists(self.projects_dir):
            for fname in os.listdir(self.projects_dir):
                if fname.endswith('.cbp'):  # CustomBurp Project
                    fpath = os.path.join(self.projects_dir, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            project = json.load(f)
                            project_id = project.get('id', fname.replace('.cbp', ''))
                            self._projects[project_id] = project
                    except:
                        pass
    
    def create_project(self, name: str, description: str = '') -> Dict:
        """Cria novo projeto"""
        project_id = str(uuid.uuid4())[:8]
        project = {
            'id': project_id,
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'target': {
                'scope': {'included_hosts': [], 'excluded_hosts': []},
                'sitemap': {}
            },
            'sessions': {},
            'rules': {
                'match_replace': [],
                'payload_processing': []
            },
            'alerts': [],
            'organizer': {
                'items': [],
                'tags': [],
                'folders': {}
            },
            'settings': {
                'proxy_port': 8080,
                'web_port': 4000,
                'auto_scan': False,
                'intercept': True
            }
        }
        
        self._projects[project_id] = project
        self._save_project(project_id)
        self.current_project = project_id
        
        return project
    
    def _save_project(self, project_id: str):
        """Salva projeto no disco"""
        if self._use_memory:
            self._projects[project_id]['updated_at'] = datetime.now().isoformat()
            return
            
        project = self._projects.get(project_id)
        if not project:
            return
        
        os.makedirs(self.projects_dir, exist_ok=True)
        fpath = os.path.join(self.projects_dir, f"{project_id}.cbp")
        
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(project, f, indent=2, ensure_ascii=False)
        
        project['updated_at'] = datetime.now().isoformat()
    
    def load_project(self, project_id: str) -> Optional[Dict]:
        """Carrega um projeto"""
        project = self._projects.get(project_id)
        if project:
            self.current_project = project_id
            return project
        return None
    
    def delete_project(self, project_id: str) -> bool:
        """Deleta um projeto"""
        if project_id in self._projects:
            fpath = os.path.join(self.projects_dir, f"{project_id}.cbp")
            if os.path.exists(fpath):
                os.remove(fpath)
            del self._projects[project_id]
            if self.current_project == project_id:
                self.current_project = None
            return True
        return False
    
    def get_project(self, project_id: str = None) -> Optional[Dict]:
        """Retorna projeto atual ou especifico"""
        if project_id:
            return self._projects.get(project_id)
        return self._projects.get(self.current_project)
    
    def list_projects(self) -> List[Dict]:
        """Lista todos os projetos"""
        projects = []
        for pid, project in self._projects.items():
            projects.append({
                'id': pid,
                'name': project.get('name', ''),
                'description': project.get('description', ''),
                'created_at': project.get('created_at', ''),
                'updated_at': project.get('updated_at', ''),
                'request_count': len(project.get('target', {}).get('sitemap', {}).keys()),
                'alert_count': len(project.get('alerts', []))
            })
        projects.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return projects
    
    def update_target(self, project_id: str, target_data: Dict):
        """Atualiza dados do target"""
        project = self._projects.get(project_id)
        if project:
            project['target'].update(target_data)
            project['updated_at'] = datetime.now().isoformat()
            self._save_project(project_id)
    
    def add_session(self, project_id: str, session_id: str, session_data: Dict):
        """Adiciona sessao ao projeto"""
        project = self._projects.get(project_id)
        if project:
            project['sessions'][session_id] = session_data
            project['updated_at'] = datetime.now().isoformat()
            self._save_project(project_id)
    
    def add_alert(self, project_id: str, alert_data: Dict):
        """Adiciona alert ao projeto"""
        project = self._projects.get(project_id)
        if project:
            if 'alerts' not in project:
                project['alerts'] = []
            project['alerts'].append(alert_data)
            project['updated_at'] = datetime.now().isoformat()
            self._save_project(project_id)
    
    def add_match_rule(self, project_id: str, rule: Dict):
        """Adiciona regra match/replace"""
        project = self._projects.get(project_id)
        if project:
            if 'rules' not in project:
                project['rules'] = {'match_replace': [], 'payload_processing': []}
            project['rules']['match_replace'].append(rule)
            project['updated_at'] = datetime.now().isoformat()
            self._save_project(project_id)
    
    def import_project(self, data: Dict) -> str:
        """Importa projeto de um dict/JSON"""
        project_id = data.get('id', str(uuid.uuid4())[:8])
        data['updated_at'] = datetime.now().isoformat()
        self._projects[project_id] = data
        self._save_project(project_id)
        self.current_project = project_id
        return project_id
    
    def export_project(self, project_id: str = None) -> Optional[Dict]:
        """Exporta projeto para dict"""
        pid = project_id or self.current_project
        if not pid:
            return None
        project = self._projects.get(pid)
        if project:
            return project.copy()
        return None
    
    def export_to_file(self, project_id: str = None, path: str = None) -> str:
        """Exporta projeto para arquivo"""
        project = self.export_project(project_id)
        if not project:
            return ''
        
        if not path:
            path = f"project-export-{project.get('name', 'untitled')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(project, f, indent=2, ensure_ascii=False)
        
        return path
    
    def get_stats(self) -> Dict:
        """Estatisticas dos projetos"""
        return {
            'total_projects': len(self._projects),
            'current_project': self.current_project,
            'projects': [
                {
                    'id': pid,
                    'name': p.get('name', ''),
                    'updated_at': p.get('updated_at', '')
                }
                for pid, p in self._projects.items()
            ]
        }


if __name__ == '__main__':
    import tempfile, os
    
    tmpdir = tempfile.mkdtemp()
    pm = ProjectManager(projects_dir=tmpdir)
    
    # Criar projeto
    project = pm.create_project('Test Project', 'Projeto de teste')
    print(f"Created: {project['id']}")
    
    # Adicionar target
    pm.update_target(project['id'], {
        'scope': {'included_hosts': ['example.com']},
        'sitemap': {'example.com': ['/login', '/admin']}
    })
    
    # Adicionar sessao
    pm.add_session(project['id'], 'sess_1', {
        'session_id': 'sess_1',
        'cookies': {'session_id': 'abc123'}
    })
    
    # Adicionar alert
    pm.add_alert(project['id'], {
        'type': 'XSS',
        'severity': 'High',
        'description': 'XSS detected'
    })
    
    # Listar
    projects = pm.list_projects()
    print(f"Projects: {len(projects)}")
    print(f"Current: {pm.current_project}")
    
    # Stats
    stats = pm.get_stats()
    print(f"Stats: {stats}")
    
    # Export
    exported = pm.export_project()
    print(f"Exported name: {exported['name']}")
    
    # Cleanup
    import shutil
    shutil.rmtree(tmpdir)
    
    print("\nProjectManager OK!")
