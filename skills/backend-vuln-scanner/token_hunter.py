#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token Hunter — Browser-based Token Extraction
Captura tokens JWT/OAuth de cookies, localStorage, sessionStorage e rede
Uso: python token_hunter.py <domain> [--headless] [--login-email <email>] [--login-pass <senha>]
"""

import sys
import json
import time
import re
import base64
import urllib.parse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class TokenHunter:
    """Captura tokens de um site via navegador automotico"""

    # Lista de nomes de cookies/token para capturar
    TOKEN_COOKIE_PATTERNS = [
        'jwt', 'token', 'auth', 'session', 'sid', 'user', 'account',
        'access_token', 'refresh_token', 'bearer', 'x-token',
        'csrf', 'csrftoken', '_csrf', 'remember_token',
        'newjwt', 'oldjwt', 'accessToken', 'id_token',
    ]

    TOKEN_LS_KEYS = [
        'newjwt', 'token', 'userToken', 'accessToken', 'jwt', 'auth',
        'userId', 'accountId', 'user', 'account', 'session', 'sid',
        'authorization', 'x-token', 'api_token', 'bearer',
        'wallet', 'balance', 'user_id', 'account_id', 'refresh_token',
        'id_token', 'csrf_token', '_csrf', 'cart', 'wishlist',
        'preferences', 'settings', 'profile',
    ]

    def __init__(self, target: str, headless: bool = True, timeout: int = 30):
        self.target = target.rstrip('/')
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.tokens: Dict[str, str] = {}
        self.cookies: List[Dict] = []
        self.page_source = ""
        self.network_logs: List[Dict] = []

    def _setup_driver(self) -> webdriver.Chrome:
        """Configura o Chrome headless com anti-detection"""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=pt-BR')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Prevenir deteccao de automation
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            driver = webdriver.Chrome(options=options)

        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
            '''
        })

        return driver

    def open_page(self, url: str = None) -> bool:
        """Abre a pagina no navegador"""
        if not SELENIUM_AVAILABLE:
            print("[ERROR] Selenium nao instalado. Instale: pip install selenium webdriver-manager")
            return False

        target_url = url or self.target
        if not target_url.startswith('http'):
            target_url = f"https://{target_url}"

        try:
            self.driver = self._setup_driver()
            self.driver.get(target_url)
            time.sleep(3)  # Aguardar carregamento
            self.page_source = self.driver.page_source
            print(f"  [OK] Page loaded: {self.driver.title}")
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to open page: {e}")
            return False

    def login(self, email: str, password: str) -> bool:
        """Tenta fazer login automatico"""
        if not self.driver:
            return False

        print(f"  [LOGIN] Attempting login with {email}...")
        try:
            wait = WebDriverWait(self.driver, 15)

            # Procurar campos de login
            email_field = None
            for selector in [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='Email']",
                "input[placeholder*='email']",
                "#email",
                'input[name="email"]',
            ]:
                try:
                    email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue

            if email_field:
                email_field.clear()
                email_field.send_keys(email)
                print(f"  [LOGIN] Email field found and filled")
            else:
                print(f"  [WARN] Email field not found, trying generic inputs")
                for inp in self.driver.find_elements(By.TAG_NAME, 'input'):
                    val = inp.get_attribute('value') or ''
                    if '@' in val or 'email' in (inp.get_attribute('placeholder') or '').lower():
                        inp.clear()
                        inp.send_keys(email)
                        email_field = inp
                        break

            pwd_field = None
            for selector in [
                "input[type='password']",
                "input[name='password']",
                "#password",
                'input[name="password"]',
            ]:
                try:
                    pwd_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue

            if pwd_field:
                pwd_field.clear()
                pwd_field.send_keys(password)
                print(f"  [LOGIN] Password field filled")
            else:
                print(f"  [WARN] Password field not found")

            # Clicar em botao de login
            login_found = False
            for selector in [
                "button[type='submit']",
                ".login-btn",
                ".submit-btn",
                ".btn-primary",
                'input[type="submit"]',
                'button:contains("Login")',
                'button:contains("Entrar")',
                '#login-btn',
                '#submit',
            ]:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    btn.click()
                    login_found = True
                    print(f"  [LOGIN] Login button clicked")
                    break
                except:
                    continue

            if not login_found:
                forms = self.driver.find_elements(By.TAG_NAME, 'form')
                if forms:
                    forms[0].submit()
                    print(f"  [LOGIN] Form submitted")

            # Aguardar redirecionamento
            time.sleep(5)
            print(f"  [LOGIN] Current URL: {self.driver.current_url}")
            return True

        except Exception as e:
            print(f"  [ERROR] Login failed: {e}")
            return False

    def manual_login_wait(self) -> bool:
        """Aguarda login manual pelo usuario"""
        print("\n  [INFO] Login manual requerido.")
        print("  [INFO] Faça login no navegador que abriu.")
        print("  [INFO] Pressione ENTER quando estiver logado...")
        try:
            input()
        except KeyboardInterrupt:
            return False
        return True

    def capture_cookies(self) -> Dict[str, str]:
        """Captura cookies relevantes"""
        captured = {}
        try:
            cookies = self.driver.get_cookies()
            self.cookies = cookies
            for cookie in cookies:
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                if any(p in name.lower() for p in self.TOKEN_COOKIE_PATTERNS):
                    captured[name] = value
                    if 'jwt' in name.lower() and '.' in value:
                        captured['cookie_jwt'] = value
                    print(f"    Cookie: {name} = {value[:40]}...")
        except Exception as e:
            print(f"  [WARN] Cookie capture failed: {e}")
        return captured

    def capture_local_storage(self) -> Dict[str, str]:
        """Captura tokens do localStorage"""
        captured = {}
        try:
            script = """
            const keys = %s;
            const found = {};
            for (const key of keys) {
                try {
                    const value = localStorage.getItem(key);
                    if (value) found[key] = value;
                } catch(e) {}
            }
            return found;
            """ % json.dumps(self.TOKEN_LS_KEYS)

            result = self.driver.execute_script(script)
            for key, value in result.items():
                if value:
                    captured[key] = value
                    if 'jwt' in key.lower() and '.' in value:
                        captured['ls_jwt'] = value
                    print(f"    localStorage: {key} = {value[:40]}...")
        except Exception as e:
            print(f"  [WARN] localStorage capture failed: {e}")
        return captured

    def capture_session_storage(self) -> Dict[str, str]:
        """Captura tokens do sessionStorage"""
        captured = {}
        try:
            script = """
            const keys = %s;
            const found = {};
            for (const key of keys) {
                try {
                    const value = sessionStorage.getItem(key);
                    if (value) found[key] = value;
                } catch(e) {}
            }
            return found;
            """ % json.dumps(self.TOKEN_LS_KEYS[:10])

            result = self.driver.execute_script(script)
            for key, value in result.items():
                if value:
                    captured[f'{key}_session'] = value
                    print(f"    sessionStorage: {key} = {value[:40]}...")
        except Exception as e:
            print(f"  [WARN] sessionStorage capture failed: {e}")
        return captured

    def capture_network_logs(self) -> Dict[str, str]:
        """Captura tokens do trafego de rede (CDP)"""
        captured = {}
        try:
            # Tentar obter logs de performance
            try:
                logs = self.driver.get_log('performance')
            except Exception:
                # Fallback: usar get_log sem especificar tipo
                logs = self.driver.get_log('browser')
                return captured

            for log_entry in logs[-50:]:  # Ultimas 50 entradas
                try:
                    msg = json.loads(log_entry.get('message', '{}'))
                    method = msg.get('method', '')
                    params = msg.get('params', {})

                    # Capturar requests com tokens
                    if method == 'Network.requestWillBeSent':
                        request = params.get('request', {})
                        headers = request.get('headers', {})
                        url = request.get('url', '')

                        # Verificar Authorization header
                        auth = headers.get('Authorization', '')
                        if auth and ('Bearer' in auth or 'Token' in auth):
                            token = auth.replace('Bearer ', '').replace('Token ', '')
                            captured['network_auth_token'] = token
                            print(f"    Network: Authorization token found in {url[:60]}...")

                        # Verificar headers personalizados
                        for h_name, h_val in headers.items():
                            if h_name.lower() in ('token', 'x-token', 'authorization', 'jwt', 'newjwt'):
                                captured[f'network_{h_name.lower()}'] = h_val
                                print(f"    Network: {h_name} = {h_val[:40]}...")

                    # Verificar response headers
                    elif method == 'Network.responseReceived':
                        response = params.get('response', {})
                        resp_headers = response.get('headers', {})
                        for h_name, h_val in resp_headers.items():
                            if h_name.lower() in ('set-cookie', 'authorization', 'jwt'):
                                captured[f'response_{h_name.lower()}'] = h_val

                except (json.JSONDecodeError, KeyError):
                    continue
        except Exception as e:
            print(f"  [WARN] Network log capture failed: {e}")
        return captured

    def extract_from_page_source(self) -> Dict[str, str]:
        """Extrai tokens do fonte da pagina (HTML/JS)"""
        captured = {}
        try:
            source = self.page_source

            # JWT pattern no HTML
            jwt_pattern = r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'
            matches = re.findall(jwt_pattern, source)
            for i, match in enumerate(matches[:3]):
                captured.setdefault('html_jwt', []).append(match)
                print(f"    HTML JWT #{i+1}: {match[:40]}...")

            # Patterns de tokens em JS
            token_patterns = [
                (r'"(token)"\s*:\s*"([^"]+)"', 'js_token'),
                (r'"(access_token)"\s*:\s*"([^"]+)"', 'js_access_token'),
                (r'"(bearer)"\s*:\s*"([^"]+)"', 'js_bearer'),
                (r'"(jwt)"\s*:\s*"([^"]+)"', 'js_jwt'),
                (r'"(newjwt)"\s*:\s*"([^"]+)"', 'js_newjwt'),
                (r'"(authorization)"\s*:\s*"([^"]+)"', 'js_authorization'),
                (r'Authorization["\']?\s*[:=]\s*["\']?([A-Za-z0-9\-_.]+\. [A-Za-z0-9\-_.]+\. [A-Za-z0-9\-_.]+)', 'js_auth_header'),
                (r'window\.(token|jwt|accessToken|authToken)\s*=\s*["\']([^"\']+)["\']', 'js_window_token'),
                (r'document\.cookie\s*=.*?((?:jwt|token|auth)[^;]*)', 'js_cookie_set'),
            ]

            for pattern, key in token_patterns:
                matches = re.findall(pattern, source, re.IGNORECASE)
                for match in matches[:2]:
                    if isinstance(match, tuple):
                        value = match[1] if len(match) > 1 else match[0]
                    else:
                        value = match
                    if value and len(value) > 10:
                        captured[key] = value
                        print(f"    HTML Pattern {key}: {value[:40]}...")

            # Procurar em variaveis globais
            global_patterns = [
                r'var\s+(token|jwt|accessToken|authToken)\s*=\s*["\']([^"\']+)["\']',
                r'const\s+(token|jwt|accessToken|authToken)\s*=\s*["\']([^"\']+)["\']',
                r'let\s+(token|jwt|accessToken|authToken)\s*=\s*["\']([^"\']+)["\']',
            ]
            for pattern in global_patterns:
                matches = re.findall(pattern, source, re.IGNORECASE)
                for match in matches[:2]:
                    if isinstance(match, tuple):
                        value = match[1] if len(match) > 1 else match[0]
                    else:
                        value = match
                    if value and len(value) > 10:
                        var_name = match[0] if isinstance(match, tuple) else ''
                        captured[f'global_{var_name}'] = value

        except Exception as e:
            print(f"  [WARN] Page source extraction failed: {e}")
        return captured

    def run(self, email: str = None, password: str = None,
            manual_login: bool = False) -> Dict:
        """Executa captura completa de tokens"""
        print("\n" + "=" * 60)
        print(f"  TOKEN HUNTER — {self.target}")
        print("=" * 60)

        if not SELENIUM_AVAILABLE:
            return {'error': 'Selenium not installed', 'tokens': {}}

        # Abrir pagina
        if not self.open_page():
            return {'error': 'Failed to open page', 'tokens': {}}

        # Fazer login se credentials fornecidas
        if email and password:
            self.login(email, password)
        elif manual_login:
            self.manual_login_wait()

        time.sleep(2)

        # Capturar tokens de todas as fontes
        print("\n  [CAPTURE] Cookies...")
        cookies = self.capture_cookies()

        print("\n  [CAPTURE] localStorage...")
        localStorage = self.capture_local_storage()

        print("\n  [CAPTURE] sessionStorage...")
        sessionStorage = self.capture_session_storage()

        print("\n  [CAPTURE] Network traffic...")
        network = self.capture_network_logs()

        print("\n  [CAPTURE] Page source...")
        html_tokens = self.extract_from_page_source()

        # Consolidar todos os tokens
        all_tokens = {}
        all_tokens.update(cookies)
        all_tokens.update(localStorage)
        all_tokens.update(sessionStorage)
        all_tokens.update(network)
        all_tokens.update(html_tokens)

        # Identificar JWT principais
        jwt_tokens = []
        for key, value in all_tokens.items():
            if '.' in str(value) and len(str(value)) > 30:
                parts = str(value).split('.')
                if len(parts) == 3:
                    try:
                        # Validar se é JWT base64
                        b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
                        decoded = base64.urlsafe_b64decode(b64)
                        json.loads(decoded)
                        jwt_tokens.append({
                            'source': key,
                            'token': value,
                            'decoded': self._decode_jwt(value)
                        })
                    except:
                        pass

        result = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'current_url': self.driver.current_url if self.driver else '',
            'page_title': self.driver.title if self.driver else '',
            'all_tokens': all_tokens,
            'jwt_tokens': jwt_tokens,
            'cookies_count': len(self.cookies),
            'total_tokens_found': len(all_tokens),
        }

        print(f"\n  [RESULT] Found {len(all_tokens)} tokens, {len(jwt_tokens)} JWT(s)")
        for jwt in jwt_tokens:
            decoded = jwt.get('decoded', {})
            print(f"    JWT from {jwt['source']}:")
            print(f"      Header: {json.dumps(decoded.get('header', {}))}")
            print(f"      Payload keys: {list(decoded.get('payload', {}).keys())}")
            if 'role' in decoded.get('payload', {}):
                print(f"      Role: {decoded['payload']['role']}")
            if 'user_id' in decoded.get('payload', {}) or 'sub' in decoded.get('payload', {}):
                uid = decoded['payload'].get('user_id') or decoded['payload'].get('sub')
                print(f"      User ID: {uid}")

        return result

    def _decode_jwt(self, token: str) -> Optional[Dict]:
        """Decodifica JWT para verificar"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            return {'header': header, 'payload': payload}
        except:
            return None

    def close(self):
        """Fecha o navegador"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Token Hunter — Captura tokens JWT/OAuth de sites')
    parser.add_argument('target', help='Domain do alvo (ex: example.com)')
    parser.add_argument('--url', '-u', help='URL especifica para abrir')
    parser.add_argument('--email', '-e', help='Email para login automatico')
    parser.add_argument('--password', '-p', help='Senha para login automatico')
    parser.add_argument('--manual', '-m', action='store_true', help='Login manual (aguarda interacao)')
    parser.add_argument('--no-headless', action='store_true', help='Mostrar navegador (nao headless)')
    parser.add_argument('--output', '-o', help='Arquivo JSON de saida')
    parser.add_argument('--tokens-only', action='store_true', help='Mostrar apenas os tokens')

    args = parser.parse_args()

    hunter = TokenHunter(
        target=args.target,
        headless=not args.no_headless
    )

    try:
        result = hunter.run(
            email=args.email,
            password=args.password,
            manual_login=args.manual
        )

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n  [SAVE] Results saved to {args.output}")

        if args.tokens_only:
            # Somente tokens JWT
            for jwt in result.get('jwt_tokens', []):
                print(jwt['token'])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    finally:
        hunter.close()


if __name__ == "__main__":
    main()
