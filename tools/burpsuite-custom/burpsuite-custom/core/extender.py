"""
CustomBurp - Extender (Plugin System)
Sistema de extensibilidade estilo BApp Store mas em Python puro
"""

import os
import sys
import json
import importlib
import inspect
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger('custom_burp')


class Plugin:
    """Representa um plugin/extensao"""
    
    def __init__(self, name: str, description: str = '', version: str = '1.0.0',
                 author: str = '', enabled: bool = True, callbacks: Dict = None):
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.enabled = enabled
        self.callbacks = callbacks or {}
        self.install_date = datetime.now().isoformat()
        self.settings: Dict = {}
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'enabled': self.enabled,
            'callbacks': list(self.callbacks.keys()),
            'install_date': self.install_date,
            'settings': self.settings
        }


class Extender:
    """Sistema de extensibilidade para CustomBurp"""
    
    # Callbacks disponiveis (interface com o engine)
    CALLBACKS = {
        'http_send': 'Called before sending HTTP request',
        'http_received': 'Called after receiving HTTP response',
        'proxy_request': 'Called when proxy captures request',
        'proxy_response': 'Called when proxy captures response',
        'scanner_scan': 'Called during vulnerability scan',
        'intruder_attack': 'Called during intruder attack',
        'ui_render': 'Called to render UI panel',
        'menu_action': 'Called when menu item clicked',
    }
    
    def __init__(self, plugins_dir: str = 'plugins'):
        self.plugins: Dict[str, Plugin] = {}
        self.plugins_dir = plugins_dir
        self._plugin_modules: Dict[str, any] = {}
        self._callbacks_registry: Dict[str, List[Callable]] = {cb: [] for cb in self.CALLBACKS}
        self._load_plugins()
    
    def _load_plugins(self):
        """Carrega plugins do diretorio"""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return
        
        for fname in os.listdir(self.plugins_dir):
            if fname.endswith('.py') and not fname.startswith('_'):
                self._load_plugin_file(os.path.join(self.plugins_dir, fname))
    
    def _load_plugin_file(self, path: str):
        """Carrega plugin de arquivo Python"""
        try:
            module_name = os.path.basename(path)[:-3]
            
            # Criar plugin basico
            plugin = Plugin(
                name=module_name,
                description=f'Plugin loaded from {module_name}',
                version='1.0.0'
            )
            
            self.plugins[module_name] = plugin
            logger.info(f"Plugin loaded: {module_name}")
            
        except Exception as e:
            logger.error(f"Failed to load plugin {path}: {e}")
    
    def install_plugin(self, name: str, code: str, description: str = '', author: str = '') -> bool:
        """
        Instala plugin a partir de codigo Python
        
        Args:
            name: Nome do plugin
            code: Codigo Python do plugin
            description: Descricao
            author: Autor
        """
        try:
            # Validar estrutura basica
            if 'class' not in code and 'def ' not in code:
                raise ValueError("Plugin must contain class or function definitions")
            
            # Criar modulo temporario
            import types
            module = types.ModuleType(name)
            exec(code, module.__dict__)
            
            # Procurar classe Plugin
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if inspect.isclass(attr) and 'plugin' in attr_name.lower():
                    plugin_class = attr
                    break
            
            # Se nao encontrou, criar plugin genérico
            if not plugin_class:
                plugin = Plugin(
                    name=name,
                    description=description or f'Plugin: {name}',
                    author=author,
                    version='1.0.0'
                )
            else:
                # Instanciar e extrair info
                instance = plugin_class()
                plugin = Plugin(
                    name=getattr(instance, 'name', name),
                    description=getattr(instance, 'description', description or ''),
                    author=getattr(instance, 'author', author),
                    version=getattr(instance, 'version', '1.0.0')
                )
                
                # Registrar callbacks
                for cb_name in self.CALLBACKS:
                    cb_method = getattr(instance, f'on_{cb_name}', None)
                    if callable(cb_method):
                        self.register_callback(cb_name, cb_method, plugin.name)
            
            self.plugins[name] = plugin
            self._plugin_modules[name] = module
            
            # Salvar no disco
            self._save_plugin(name, code, description, author)
            
            logger.info(f"Plugin installed: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin {name}: {e}")
            return False
    
    def _save_plugin(self, name: str, code: str, description: str, author: str):
        """Salva plugin no disco"""
        plugin_dir = os.path.join(self.plugins_dir, name)
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Salvar codigo
        with open(os.path.join(plugin_dir, 'plugin.py'), 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Salvar metadados
        metadata = {
            'name': name,
            'description': description,
            'author': author,
            'version': '1.0.0',
            'installed_at': datetime.now().isoformat()
        }
        with open(os.path.join(plugin_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def uninstall_plugin(self, name: str) -> bool:
        """Desinstala plugin"""
        if name in self.plugins:
            # Remover callbacks
            for cb_name in list(self._callbacks_registry.keys()):
                self._callbacks_registry[cb_name] = [
                    cb for cb in self._callbacks_registry[cb_name]
                    if cb.get('plugin') != name
                ]
            
            del self.plugins[name]
            if name in self._plugin_modules:
                del self._plugin_modules[name]
            
            # Remover do disco
            plugin_dir = os.path.join(self.plugins_dir, name)
            if os.path.exists(plugin_dir):
                import shutil
                shutil.rmtree(plugin_dir)
            
            logger.info(f"Plugin uninstalled: {name}")
            return True
        return False
    
    def enable_plugin(self, name: str) -> bool:
        if name in self.plugins:
            self.plugins[name].enabled = True
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        if name in self.plugins:
            self.plugins[name].enabled = False
            return True
        return False
    
    def register_callback(self, callback_name: str, func: Callable, plugin_name: str = ''):
        """Registra callback de plugin"""
        if callback_name not in self._callbacks_registry:
            self._callbacks_registry[callback_name] = []
        
        self._callbacks_registry[callback_name].append({
            'func': func,
            'plugin': plugin_name
        })
    
    def trigger_callback(self, callback_name: str, **kwargs):
        """Dispara callback"""
        if callback_name not in self._callbacks_registry:
            return
        
        for cb in self._callbacks_registry[callback_name]:
            try:
                cb['func'](**kwargs)
            except Exception as e:
                logger.error(f"Callback {callback_name} error in {cb['plugin']}: {e}")
    
    def get_plugin(self, name: str) -> Optional[Dict]:
        plugin = self.plugins.get(name)
        return plugin.to_dict() if plugin else None
    
    def list_plugins(self) -> List[Dict]:
        return [p.to_dict() for p in self.plugins.values()]
    
    def get_available_callbacks(self) -> Dict:
        """Retorna lista de callbacks disponiveis"""
        return self.CALLBACKS.copy()
    
    def get_bapp_store(self) -> List[Dict]:
        """Simula BApp Store com plugins populares"""
        return [
            {
                'name': 'Logger Plus',
                'description': 'Enhanced request/response logging with filtering',
                'author': 'CustomBurp Team',
                'version': '2.1.0',
                'category': 'Logging',
                'rating': 4.8,
                'downloads': 15420,
                'installed': 'Logger Plus' in self.plugins
            },
            {
                'name': 'Session Handler Pro',
                'description': 'Advanced session token management and rotation',
                'author': 'SecurityTeam',
                'version': '1.5.3',
                'category': 'Session',
                'rating': 4.6,
                'downloads': 8930,
                'installed': 'Session Handler Pro' in self.plugins
            },
            {
                'name': 'Auto Repeater',
                'description': 'Automatically replay requests with variations',
                'author': 'Pentester',
                'version': '3.0.1',
                'category': 'Automation',
                'rating': 4.9,
                'downloads': 22100,
                'installed': 'Auto Repeater' in self.plugins
            },
            {
                'name': 'XSS Scanner Pro',
                'description': 'Advanced XSS detection with bypass techniques',
                'author': 'WebSec',
                'version': '1.2.0',
                'category': 'Scanner',
                'rating': 4.7,
                'downloads': 11200,
                'installed': 'XSS Scanner Pro' in self.plugins
            },
            {
                'name': 'SQLMap Integration',
                'description': 'Integrate with SQLMap for automated SQLi testing',
                'author': 'DBSec',
                'version': '2.0.0',
                'category': 'Scanner',
                'rating': 4.5,
                'downloads': 9800,
                'installed': 'SQLMap Integration' in self.plugins
            },
            {
                'name': 'Collaborator Pro',
                'description': 'Extended OAST with custom payloads and monitoring',
                'author': 'OAST Team',
                'version': '1.0.5',
                'category': 'OAST',
                'rating': 4.4,
                'downloads': 6700,
                'installed': 'Collaborator Pro' in self.plugins
            },
            {
                'name': 'Header Editor',
                'description': 'Mass header manipulation and injection testing',
                'author': 'HTTPHeader',
                'version': '1.1.0',
                'category': 'Proxy',
                'rating': 4.3,
                'downloads': 5400,
                'installed': 'Header Editor' in self.plugins
            },
            {
                'name': 'GraphQL Scanner',
                'description': 'Scan GraphQL endpoints for vulnerabilities',
                'author': 'GraphQLSec',
                'version': '1.0.0',
                'category': 'Scanner',
                'rating': 4.2,
                'downloads': 3200,
                'installed': 'GraphQL Scanner' in self.plugins
            }
        ]


# Exemplo de plugin
EXAMPLE_PLUGIN = '''
class MyPlugin:
    name = "Example Plugin"
    description = "Demonstracao de plugin CustomBurp"
    author = "ratman4080"
    version = "1.0.0"
    
    def on_http_send(self, request):
        print(f"[{self.name}] Sending: {request.get('method')} {request.get('path')}")
        return request
    
    def on_http_received(self, response):
        print(f"[{self.name}] Received: {response.get('status_code')}")
        return response
    
    def on_proxy_request(self, request):
        # Pode modificar request antes de enviar
        return request
    
    def on_proxy_response(self, response):
        # Pode modificar response antes de mostrar
        return response
'''


if __name__ == '__main__':
    ext = Extender()
    
    # Testar install
    print("Installing example plugin...")
    success = ext.install_plugin('Example Plugin', EXAMPLE_PLUGIN, 'Demo plugin', 'ratman4080')
    print(f"Install success: {success}")
    
    # Listar plugins
    plugins = ext.list_plugins()
    print(f"Plugins: {len(plugins)}")
    for p in plugins:
        print(f"  - {p['name']} v{p['version']} by {p['author']}")
    
    # BApp Store
    store = ext.get_bapp_store()
    print(f"\nBApp Store: {len(store)} plugins")
    for item in store[:3]:
        status = "[INSTALLED]" if item['installed'] else "[AVAILABLE]"
        print(f"  {item['name']} {status} ({item['category']}) - {item['downloads']} downloads")
    
    # Testar callback
    ext.trigger_callback('http_send', method='GET', path='/test')
    
    print("\nExtender OK!")
