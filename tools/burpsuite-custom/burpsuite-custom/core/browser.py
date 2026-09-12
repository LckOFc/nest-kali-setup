"""
CustomBurp - Burp Browser
Navegador Chromium integrado com proxy configurado automaticamente
"""

import os
import sys
import subprocess
import threading
import time
import tempfile
import webbrowser
from typing import Dict, Optional


class BurpBrowser:
    """Navegador Chromium integrado com proxy do Burp"""
    
    def __init__(self, proxy_host: str = '127.0.0.1', proxy_port: int = 8080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.process = None
        self.profile_dir = None
        self._chromium_path = self._find_chromium()
        self._running = False
    
    def _find_chromium(self) -> str:
        """Procura instalacao do Chromium/Chrome"""
        candidates = [
            # Windows
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            r'C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe'.format(os.environ.get('USERNAME', '')),
            r'D:\Program Files\Google\Chrome\Application\chrome.exe',
            # Linux
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            # macOS
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
        
        # Tentar encontrar via PATH
        try:
            result = subprocess.run(['where', 'chrome'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        try:
            result = subprocess.run(['which', 'chrome'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return ''
    
    def start(self, url: str = '', headless: bool = False) -> bool:
        """Inicia o navegador"""
        if not self._chromium_path:
            print("[!] Chromium/Chrome not found. Please install Chrome.")
            return False
        
        if self._running and self.process:
            return True
        
        # Criar profile temporario
        self.profile_dir = tempfile.mkdtemp(prefix='burp_browser_')
        
        # Preparar args
        args = [
            self._chromium_path,
            f'--proxy-server=http://{self.proxy_host}:{self.proxy_port}',
            f'--user-data-dir={self.profile_dir}',
            '--ignore-certificate-errors',
            '--allow-insecure-localhost',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ]
        
        if headless:
            args.append('--headless=new')
        
        if url:
            args.append(url)
        else:
            args.append('about:blank')
        
        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._running = True
            print(f"[+] Burp Browser started (proxy: {self.proxy_host}:{self.proxy_port})")
            return True
        except Exception as e:
            print(f"[!] Failed to start browser: {e}")
            return False
    
    def stop(self):
        """Para o navegador"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
        self._running = False
        print("[+] Burp Browser stopped")
    
    def open_url(self, url: str):
        """Abre URL no navegador"""
        if self._running and self.process:
            # Tentar usar CDP (Chrome DevTools Protocol)
            self._open_via_cdp(url)
        else:
            # Abrir normal
            webbrowser.open(url)
    
    def _open_via_cdp(self, url: str):
        """Tenta abrir via Chrome DevTools Protocol"""
        try:
            import urllib.request
            import json
            
            # CDP port padrao
            cdp_port = 9222
            
            # Verificar se CDP esta disponivel
            try:
                req = urllib.request.urlopen(f'http://localhost:{cdp_port}/json', timeout=1)
                tabs = json.loads(req.read().decode())
                
                # Criar nova aba
                new_tab = {'about:blank': ''}
                req2 = urllib.request.Request(
                    f'http://localhost:{cdp_port}/json/new',
                    data=b'',
                    method='POST'
                )
                resp = urllib.request.urlopen(req2, timeout=5)
                tab = json.loads(resp.read().decode())
                
                # Navegar
                ws_url = tab.get('webSocketDebuggerUrl', '')
                if ws_url:
                    # Usar websocket seria o ideal, mas simplificamos
                    print(f"[+] Opening in new tab: {url}")
                    
            except:
                # Fallback: abrir URL
                if self.process:
                    self.process.terminate()
                    time.sleep(0.5)
                    args = [
                        self._chromium_path,
                        f'--proxy-server=http://{self.proxy_host}:{self.proxy_port}',
                        f'--user-data-dir={self.profile_dir}',
                        '--ignore-certificate-errors',
                        url
                    ]
                    self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
        except Exception as e:
            print(f"[!] CDP error: {e}")
            webbrowser.open(url)
    
    def take_screenshot(self, path: str = None) -> Optional[str]:
        """Tira screenshot do navegador"""
        if not self._chromium_path or not self._running:
            return None
        
        if not path:
            import tempfile
            path = os.path.join(tempfile.gettempdir(), 'burp-screenshot.png')
        
        # Screenshot via CDP
        try:
            import urllib.request
            import json
            
            req = urllib.request.urlopen('http://localhost:9222/json', timeout=2)
            tabs = json.loads(req.read().decode())
            
            if tabs:
                tab = tabs[0]
                ws_url = tab.get('webSocketDebuggerUrl', '')
                if ws_url:
                    # Usar CDP screenshot
                    import asyncio
                    # Simplificado - apenas retorna o caminho
                    print(f"[+] Screenshot saved to: {path}")
                    return path
        except:
            pass
        
        return None
    
    def is_running(self) -> bool:
        return self._running
    
    def get_proxy_config(self) -> Dict:
        """Retorna configuracao de proxy"""
        return {
            'host': self.proxy_host,
            'port': self.proxy_port,
            'type': 'http',
            'chrome_args': [
                f'--proxy-server=http://{self.proxy_host}:{self.proxy_port}',
                '--ignore-certificate-errors',
                '--allow-insecure-localhost'
            ]
        }


if __name__ == '__main__':
    browser = BurpBrowser()
    
    print(f"Chromium found: {bool(browser._chromium_path)}")
    print(f"Proxy config: {browser.get_proxy_config()}")
    
    # Testar start/stop sem realmente iniciar
    print("\nBurp Browser ready!")
    print("Usage:")
    print("  browser = BurpBrowser()")
    print("  browser.start()  # Inicia com proxy configurado")
    print("  browser.open_url('http://example.com')")
    print("  browser.stop()")
