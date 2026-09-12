#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCode Vulnerability Scanner Integration — Versao Completa e Funcional
Todas as ferramentas integradas: recon, WAF, JWT, GraphQL, exploit
"""

import sys
import os
import json
import time
import subprocess
import socket
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse

# Adicionar path do modulo
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Configuracoes
RESULTS_DIR = Path.home() / "hardware-bridge" / "scan_results"
LOG_FILE = RESULTS_DIR / "integration.log"


class ToolManager:
    """Gerencia todas as ferramentas automaticamente"""

    def __init__(self):
        self.burp_process = None
        self.burp_running = False
        self.proxy_port = 8080
        self.web_port = 4000
        self.modules = {}
        self._load_modules()

    def _load_modules(self):
        """Carrega modulos disponiveis"""
        modules = [
            'vuln_scanner',
            'complete_scanner',
            'jwt_analyzer',
            'token_hunter',
            'graphql_scanner',
            'framework_scanner',
            'waf_bypass',
            'oauth_scanner',
            'scanner_integration',
            'web_crawler',
            'header_scanner',
            'directory_buster',
            'cors_scanner',
            'parameter_fuzzer',
            'exploit_executor',
            'brute_force',
            'subdomain_enum',
            'data_extractor',
            'mass_scanner',
            'burp_bridge',
            'darkweb_search',
            'virus_scanner',
            'onion_resolver',
            'tor_search',
            # Novo — Exploits & RE
            'exploit_database',
            'reverse_engineering',
            'ctf_helper',
        ]
        for mod in modules:
            path = BASE_DIR / f"{mod}.py"
            if path.exists():
                self.modules[mod] = str(path)

    def run_quick_scan(self, target: str) -> Dict:
        """Scan rapido (recon + WAF + framework)"""
        results = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'vulnerabilities': [],
            'summary': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0},
        }

        # Reconhecimento basico
        recon = self._quick_recon(target)
        results['recon'] = recon

        # WAF detection
        waf = self._quick_waf_test(target)
        results['waf'] = waf

        # Framework detection
        fw = self._quick_framework(target)
        results['framework'] = fw

        # Calcular resumo
        vulns = results.get('vulnerabilities', [])
        results['summary'] = {
            'total': len(vulns),
            'critical': len([v for v in vulns if v.get('severity') == 'CRITICAL']),
            'high': len([v for v in vulns if v.get('severity') == 'HIGH']),
            'medium': len([v for v in vulns if v.get('severity') == 'MEDIUM']),
        }

        return results

    def run_full_scan(self, target: str, quick: bool = False) -> Dict:
        """Scan completo usando CompleteScanner"""
        try:
            from complete_scanner import CompleteScanner
            scanner = CompleteScanner(target)
            result = scanner.run_full_scan(quick=quick)

            # Adicionar tokens capturados
            jwt_phase = result.get('phases', {}).get('jwt', {})
            if jwt_phase.get('tokens_found', 0) > 0:
                result['tokens'] = jwt_phase.get('jwt_tokens', [])

            return result
        except Exception as e:
            print(f"[ERROR] Full scan failed: {e}")
            return {'error': str(e), 'target': target}

    def analyze_jwt(self, target: str, token: str = None, browser: bool = False) -> Dict:
        """Analisa JWT com extracao via browser"""
        try:
            from jwt_analyzer import JWTAnalyzer
            analyzer = JWTAnalyzer(target)
            if browser:
                print("  [INFO] Using browser-based token extraction...")
                analyzer.extract_all()
            return analyzer.run_full_analysis(token)
        except ImportError:
            return {'error': 'jwt_analyzer not available'}
        except Exception as e:
            return {'error': str(e)}

    def hunt_tokens(self, target: str, email: str = None, password: str = None,
                    manual: bool = False) -> Dict:
        """Captura tokens via browser (Selenium)"""
        try:
            from token_hunter import TokenHunter
            hunter = TokenHunter(target, headless=True)
            result = hunter.run(email=email, password=password, manual_login=manual)
            hunter.close()
            return result
        except ImportError:
            return {'error': 'token_hunter not available (selenium needed)'}
        except Exception as e:
            return {'error': str(e)}

    def scan_graphql(self, target: str) -> Dict:
        """Scan GraphQL endpoints"""
        try:
            from graphql_scanner import GraphQLScanner
            scanner = GraphQLScanner(target)
            return scanner.run_full_scan()
        except ImportError:
            return {'error': 'graphql_scanner not available'}
        except Exception as e:
            return {'error': str(e)}

    def _quick_recon(self, target: str, timeout: int = 5) -> Dict:
        """Reconhecimento rapido"""
        result = {'ip': None, 'technologies': [], 'endpoints': []}

        try:
            ip = socket.gethostbyname(target)
            result['ip'] = ip
        except:
            pass

        try:
            url = f"https://{target}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            ctx = __import__('ssl').create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = __import__('ssl').CERT_NONE

            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                headers = dict(resp.headers)
                result['server'] = headers.get('Server', 'Unknown')
                result['x_powered_by'] = headers.get('X-Powered-By', 'Unknown')

                body = resp.read().decode('utf-8', errors='ignore')[:50000]

                techs = []
                if 'cloudflare' in str(headers).lower():
                    techs.append('Cloudflare')
                if 'react' in body.lower():
                    techs.append('React')
                if 'next' in body.lower() or '__NEXT_DATA__' in body:
                    techs.append('Next.js')
                if 'ruby' in str(headers).lower():
                    techs.append('Ruby on Rails')
                if 'php' in str(headers).lower():
                    techs.append('PHP')

                result['technologies'] = techs
                result['headers'] = {
                    k: v for k, v in headers.items()
                    if k.lower() in ['server', 'x-powered-by', 'cf-ray', 'strict-transport-security']
                }
        except Exception as e:
            result['error'] = str(e)

        return result

    def _quick_waf_test(self, target: str, timeout: int = 5) -> Dict:
        """Teste rapido de WAF"""
        result = {'detected': False, 'type': 'Unknown', 'bypassable': False}

        try:
            url = f"https://{target}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = __import__('ssl').create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = __import__('ssl').CERT_NONE

            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                headers = dict(resp.headers)
                if 'cloudflare' in str(headers).lower():
                    result['detected'] = True
                    result['type'] = 'Cloudflare'
                    result['cf_ray'] = headers.get('CF-Ray', 'N/A')
                elif 'x-frame-options' in headers:
                    result['detected'] = True
                    result['type'] = 'Generic WAF'
        except urllib.error.HTTPError as e:
            if e.code == 403:
                result['detected'] = True
                result['type'] = 'WAF Blocking'
                result['bypassable'] = True
        except Exception:
            pass

        return result

    def _quick_framework(self, target: str, timeout: int = 5) -> Dict:
        """Detecao rapida de framework"""
        result = {'rails': False, 'nextjs': False, 'express': False, 'django': False}

        try:
            url = f"https://{target}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = __import__('ssl').create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = __import__('ssl').CERT_NONE

            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                headers = dict(resp.headers)
                body = resp.read().decode('utf-8', errors='ignore')[:100000]

                if any(h in str(headers).lower() for h in ['x-request-id', 'x-runtime', 'x-rails']):
                    result['rails'] = True
                if 'next' in body.lower() or '__NEXT_DATA__' in body:
                    result['nextjs'] = True
                if 'express' in str(headers).lower():
                    result['express'] = True
                if 'django' in str(headers).lower() or 'set-cookie' in str(headers).lower():
                    result['django'] = True

        except Exception:
            pass

        return result

    def start_burp(self) -> bool:
        """Inicia Burp Suite (se configurado)"""
        burp_dir = Path.home() / "tools" / "burpsuite-custom"
        if not burp_dir.exists():
            return False

        try:
            self.burp_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                cwd=str(burp_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(2)
            if self.burp_process.poll() is None:
                self.burp_running = True
                return True
        except:
            pass
        return False

    def stop_burp(self):
        """Para Burp Suite"""
        if self.burp_process:
            try:
                self.burp_process.terminate()
                self.burp_running = False
            except:
                pass

    def save_results(self, target: str, results: Dict) -> str:
        """Salva resultados em JSON"""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = ''.join(c if c.isalnum() else '_' for c in target)
        filename = f"auto_{safe_name}_{timestamp}.json"
        filepath = RESULTS_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        return str(filepath)

    def _log(self, msg: str):
        """Log"""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


class CommandHandler:
    """Processa comandos slash"""

    def __init__(self, tm: ToolManager):
        self.tm = tm
        self.commands = {
            '/vuln_scan': self.cmd_scan,
            '/vuln_quick': self.cmd_quick,
            '/vuln_status': self.cmd_status,
            '/vuln_start_burp': self.cmd_start_burp,
            '/vuln_stop_burp': self.cmd_stop_burp,
            '/vuln_list': self.cmd_list,
            '/vuln_help': self.cmd_help,
            '/jwt_analyze': self.cmd_jwt_analyze,
            '/jwt_hunt': self.cmd_jwt_hunt,
            '/graphql_scan': self.cmd_graphql_scan,
            '/crawler': self.cmd_crawler,
            '/headers': self.cmd_headers,
            '/buster': self.cmd_buster,
            '/cors': self.cmd_cors,
            '/fuzz': self.cmd_fuzz,
            '/exploit': self.cmd_exploit,
            '/brute': self.cmd_brute,
            '/subdomain': self.cmd_subdomain,
            '/extract': self.cmd_extract,
            '/mass': self.cmd_mass,
            '/burp_start': self.cmd_burp_start,
            '/burp_stop': self.cmd_burp_stop,
            '/burp_status': self.cmd_burp_status,
            '/burp_generate_ca': self.cmd_burp_generate_ca,
            '/burp_scanner': self.cmd_burp_scanner,
            '/darkweb': self.cmd_darkweb,
            '/darkweb-safe': self.cmd_darkweb_safe,
            '/virus-scan': self.cmd_virus_scan,
            '/onion-resolve': self.cmd_onion_resolve,
            '/tor-search': self.cmd_tor_search,
            '/tor-known': self.cmd_tor_known,
            '/tor-check': self.cmd_tor_check,
            # Novo — Exploits & RE
            '/exploit-db': self.cmd_exploit_db,
            '/exploit-db-list': self.cmd_exploit_db_list,
            '/explore': self.cmd_explore,
            '/strings': self.cmd_strings,
            '/pe': self.cmd_pe,
            '/hash': self.cmd_hash,
            '/shellcode': self.cmd_shellcode,
            '/shellcode-list': self.cmd_shellcode_list,
            '/ctf': self.cmd_ctf,
            '/ctf-templates': self.cmd_ctf_templates,
        }

    def handle(self, command: str, args: List[str] = None, kwargs: Dict = None) -> str:
        """Processa comando"""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        if not command.startswith('/'):
            command = '/' + command

        if command in self.commands:
            try:
                return self.commands[command](args, kwargs)
            except Exception as e:
                return f"[ERROR] {e}"
        return f"[ERROR] Unknown command: {command}"

    def cmd_help(self, args: List[str] = None, kwargs: Dict = None) -> str:
        return """
  COMANDOS DISPONIVEIS (27 modulos):

  [SCANS]
    /vuln_scan <dominio>         Scan completo (todas as fases)
    /vuln_quick <dominio>        Scan rapido (30s)
    /vuln_list                   Lista scans anteriores

  [JWT]
    /jwt_analyze <dominio>       Analisa JWT (auto-extrai do browser)
    /jwt_analyze <dominio> --token <token>  Analisa token especifico
    /jwt_hunt <dominio>          Captura tokens via browser (Selenium)
    /jwt_hunt <dominio> --email <e> --pass <p>  Login automatico

  [GRAPHQL]
    /graphql_scan <dominio>      Scan GraphQL endpoints

  [CRAWLER]
    /crawler <dominio>           Crawler web recursivo
    /crawler <dominio> --depth 2 --max 50

  [HEADERS]
    /headers <dominio>           Analisa headers de seguranca (score 0-100)

  [DIRECTORY BUSTER]
    /buster <dominio>            Busca 300+ diretorios/arquivos sensiveis

  [CORS]
    /cors <dominio>              Testa configuracao CORS

  [FUZZER]
    /fuzz <dominio>              Fuzza parametros (SQLi, XSS, LFI, SSRF)
    /fuzz <dominio> --urls /login /api/users

  [EXPLOIT]
    /exploit <dominio> --report arquivo.json  Explora vulns encontradas
    /exploit <dominio> --token eyJ...         Usa token JWT no exploit

  [BRUTE FORCE]
    /brute <dominio>             Brute force em login + JWT + diretorios
    /brute <dominio> --token eyJ...  So testa JWT secret
    /brute <dominio> --passwords lista.txt  Wordlist customizada

  [SUBDOMAIN]
    /subdomain <dominio>         Enumera subdominios (DNS brute + crt.sh)
    /subdomain <dominio> --wordlist words.txt

  [EXTRACTION]
    /extract <dominio> --report arquivo.json  Extrai dados de vulns
    /extract <dominio> --token eyJ...         Extrai dados do JWT

  [MASS SCAN]
    /mass target1.com target2.com  Scan completo multi-alvo
    /mass target1.com target2.com --phases recon vuln

  [BURP SUITE INTEGRADO]
    /burp_start                    Inicia CustomBurp (proxy + web UI)
    /burp_stop                     Para CustomBurp
    /burp_status                   Status do Burp (requests, issues)
    /burp_generate_ca              Gera certificado CA para HTTPS
    /burp_scanner <dominio>        Scan rapido via Burp proxy
    /vuln_start_burp               Inicia Burp (compatibilidade)
    /vuln_stop_burp                Para Burp (compatibilidade)

  [DARKWEB / OSINT]
    /darkweb <query>               Busca em sites .onion (Ahmia)
    /darkweb <query> --scan        Busca + scan de segurança
    /darkweb-safe                  Lista URLs .onion seguras conhecidas
    /virus-scan <url|file>         Scan de vírus/malware (URLScan.io)
    /virus-scan <file> --type file --vt-key KEY
    /onion-resolve <address>       Resolve e valida endereço .onion

  [TOR SEARCH — sem Tor local]
    /tor-search <query>            Busca dark web via gateways públicos
    /tor-search <query> --engine ahmia_api
    /tor-known                     Lista URLs .onion conhecidas
    /tor-check <url.onion>         Verifica acessibilidade

  [EXPLOIT DATABASE — Engenharia Reversa]
    /exploit-db <query>            Busca exploits na base (DeCSS, EternalBlue, Stuxnet...)
    /exploit-db <query> -c network_exploit  Filtra por categoria
    /exploit-db-list               Lista todas as entradas e técnicas de RE

  [REVERSE ENGINEERING]
    /explore <arquivo>             Analisa PE + extrai strings/urls/chaves/IPs
    /explore <arquivo> --strings   Somente strings
    /explore <arquivo> --urls      Somente URLs
    /explore <arquivo> --keys      Somente chaves/API keys
    /explore <arquivo> --ips       Somente IPs
    /explore <arquivo> --pe        Somente análise PE headers
    /strings <arquivo>             Extrai strings de binário
    /pe <arquivo>                  Analisa headers PE (seções, imports, etc)
    /hash <arquivo>                Calcula MD5/SHA1/SHA256
    /shellcode <template>          Retorna shellcode (x86/x64)
    /shellcode-list                Lista templates disponiveis

  [CTF HELPER]
    /ctf pattern_create <len>      Gera padrão cíclico para offset
    /ctf pattern_offset <value>    Encontra offset no padrão
    /ctf rop_x86 [target_func]     ROP chain x86
    /ctf rop_x64 [target_func]     ROP chain x64
    /ctf encode <sc> <format>      Codifica shellcode (c/python/hex/base64/js)
    /ctf decode <encoded> <format> Decodifica shellcode
    /ctf template <nome>           Mostra template de exploit
    /ctf-templates                 Lista templates disponiveis

  [BURP SUITE WEB]
    Proxy: http://127.0.0.1:8080
    Web UI: http://localhost:4000
    API: http://localhost:4000/api/...

  Exemplos:
    /vuln_quick cassino.bet.br
    /jwt_hunt nnbet.mobi --email user@email.com --pass senha123
    /jwt_analyze nnbet.mobi
    /exploit example.com --report scan_result.json
    /brute example.com
    /subdomain example.com
    /mass example.com test.com
    /burp_start
    /burp_status
    /burp_scanner example.com
    /burp_generate_ca
        """

    def cmd_scan(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /vuln_scan <dominio>"

        target = args[0]
        print(f"\n[SCAN] Iniciando scan completo em {target}...")

        results = self.tm.run_full_scan(target)
        filepath = self.tm.save_results(target, results)

        return self._format_output(results, filepath)

    def cmd_quick(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /vuln_quick <dominio>"

        target = args[0]
        print(f"\n[QUICK SCAN] Iniciando scan rapido em {target}...")

        results = self.tm.run_quick_scan(target)
        filepath = self.tm.save_results(target, results)

        return self._format_output(results, filepath)

    def cmd_status(self, args: List[str] = None, kwargs: Dict = None) -> str:
        return f"""[SYSTEM STATUS]
  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

  [MODULES]
    Available: {len(self.tm.modules)}
    {', '.join(self.tm.modules.keys())}

  [BURP SUITE]
    Running: {'Yes' if self.tm.burp_running else 'No'}
    Proxy: http://127.0.0.1:{self.tm.proxy_port}
    Web UI: http://localhost:{self.tm.web_port}

  [RESULTS]
    Directory: {RESULTS_DIR}
    Files: {len(list(RESULTS_DIR.glob('*.json')) if RESULTS_DIR.exists() else 0)}
"""

    def cmd_start_burp(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if self.tm.start_burp():
            return f"""[BURP STARTED]
  Proxy: http://127.0.0.1:{self.tm.proxy_port}
  Web UI: http://localhost:{self.tm.web_port}

  Configure browser:
    Settings -> Network -> Proxy
    Manual: 127.0.0.1:{self.tm.proxy_port}
"""
        return "[ERROR] Falha ao iniciar Burp"

    def cmd_stop_burp(self, args: List[str] = None, kwargs: Dict = None) -> str:
        self.tm.stop_burp()
        return "[BURP STOPPED]"

    def cmd_burp_start(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if self.tm.start_burp():
            return f"""[BURP STARTED]
  Proxy: http://127.0.0.1:{self.tm.proxy_port}
  Web UI: http://localhost:{self.tm.web_port}

  Configure browser:
    Settings -> Network -> Proxy
    Manual: 127.0.0.1:{self.tm.proxy_port}
"""
        return "[ERROR] Falha ao iniciar Burp"

    def cmd_burp_stop(self, args: List[str] = None, kwargs: Dict = None) -> str:
        self.tm.stop_burp()
        return "[BURP STOPPED]"

    def cmd_burp_status(self, args: List[str] = None, kwargs: Dict = None) -> str:
        import os
        db_path = Path.home() / 'custom_burp.db'
        stats = {'requests': 0, 'issues': 0, 'critical': 0, 'high': 0}
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM requests")
            stats['requests'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues")
            stats['issues'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues WHERE severity='Critical'")
            stats['critical'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM issues WHERE severity='High'")
            stats['high'] = c.fetchone()[0]
            conn.close()
        except:
            pass

        burp_running = False
        try:
            import urllib.request
            urllib.request.urlopen('http://localhost:4000/api/status', timeout=2)
            burp_running = True
        except:
            pass

        return f"""[BURP STATUS]
  Running: {'Yes' if burp_running else 'No'}
  Proxy: http://127.0.0.1:{self.tm.proxy_port}
  Web UI: http://localhost:{self.tm.web_port}
  Requests logged: {stats['requests']}
  Issues found: {stats['issues']}
  Critical: {stats['critical']}
  High: {stats['high']}
  DB: {db_path}
"""

    def cmd_burp_generate_ca(self, args: List[str] = None, kwargs: Dict = None) -> str:
        try:
            from burp_bridge import BurpBridge
            bridge = BurpBridge()
            if bridge.generate_ca_cert():
                ca_path = bridge.get_ca_cert_path()
                return f"""[CA GENERATED]
  Certificate: {ca_path}
  
  Install in browser:
    Chrome: Settings -> Privacy -> Security -> Manage certificates
    Import the .crt file into Trusted Root Certification Authorities
"""
            return "[ERROR] Failed to generate CA certificate"
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_burp_scanner(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /burp_scanner <dominio>"
        target = args[0]
        print(f"\n[BURP SCANNER] Running scanner via Burp proxy for {target}")

        try:
            from burp_bridge import BurpBridge
            bridge = BurpBridge()
            result = bridge.run_scanner_through_burp(target)

            summary = result.get('summary', {})
            issues = result.get('issues_from_burp', [])

            output = f"""[BURP SCAN] {target}
  Proxy: {result.get('burp_proxy', 'N/A')}
  Web UI: {result.get('burp_web', 'N/A')}
  Issues from Burp: {summary.get('total_vulns', 0)}
  Critical: {summary.get('critical', 0)}
  High: {summary.get('high', 0)}
  Medium: {summary.get('medium', 0)}
"""
            if issues:
                output += "\n  [ISSUES]\n"
                for issue in issues[:5]:
                    output += f"    [{issue.get('severity', '?')}] {issue.get('issue_type', '?')}: {issue.get('description', '')[:80]}\n"

            return output
        except Exception as e:
            return f"[ERROR] Burp scan failed: {e}"

    def cmd_list(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not RESULTS_DIR.exists():
            return "[INFO] Nenhum scan encontrado"

        files = sorted(RESULTS_DIR.glob("auto_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]

        if not files:
            return "[INFO] Nenhum scan rapido encontrado"

        output = "[RESULTS] Recent scans:\n\n"
        output += "| File | Time | Target | Vulns |\n"
        output += "|------|------|--------|-------|\n"

        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    target = data.get('target', 'Unknown')
                    ts = data.get('timestamp', 'Unknown')[:19]
                    summary = data.get('summary', {})
                    vulns = summary.get('total', 0)
                    output += f"| {f.name} | {ts} | {target} | {vulns} |\n"
            except:
                output += f"| {f.name} | Error |\n"

        return output

    def cmd_jwt_analyze(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /jwt_analyze <dominio> [--token <token>]"

        target = args[0]
        token = None
        browser = False

        # Parsear argumentos
        if '--token' in args:
            idx = args.index('--token')
            if idx + 1 < len(args):
                token = args[idx + 1]

        if '--browser' in args or '-b' in args:
            browser = True

        print(f"\n[JWT ANALYZE] {target}")
        results = self.tm.analyze_jwt(target, token=token, browser=browser)
        filepath = self.tm.save_results(f"{target}_jwt", results)

        summary = results.get('summary', {})
        output = f"""[JWT ANALYSIS] {target}
  Tokens Found: {results.get('tokens_found', 0)}
  Tests Run: {summary.get('total_tests', 0)}
  Critical: {summary.get('critical_vulns', 0)}
  High: {summary.get('high_vulns', 0)}
  Exploit Successes: {summary.get('exploit_successes', 0)}
  Saved: {filepath}
"""
        return output

    def cmd_jwt_hunt(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /jwt_hunt <dominio> [--email <e>] [--pass <p>]"

        target = args[0]
        email = None
        password = None
        manual = False

        if '--email' in args:
            idx = args.index('--email')
            if idx + 1 < len(args):
                email = args[idx + 1]

        if '--pass' in args:
            idx = args.index('--pass')
            if idx + 1 < len(args):
                password = args[idx + 1]

        if '--manual' in args:
            manual = True

        print(f"\n[TOKEN HUNT] {target}")
        results = self.tm.hunt_tokens(target, email=email, password=password, manual=manual)

        tokens_found = results.get('total_tokens_found', 0)
        jwt_found = len(results.get('jwt_tokens', []))

        output = f"""[TOKEN HUNT] {target}
  Total Tokens: {tokens_found}
  JWT Tokens: {jwt_found}
  URL: {results.get('current_url', 'N/A')}
  Title: {results.get('page_title', 'N/A')}
"""
        return output

    def cmd_graphql_scan(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /graphql_scan <dominio>"

        target = args[0]
        print(f"\n[GRAPHQL SCAN] {target}")
        results = self.tm.scan_graphql(target)

        endpoints = results.get('endpoints_found', [])
        introspection = results.get('introspection', False)

        output = f"""[GRAPHQL SCAN] {target}
  Endpoints Found: {len(endpoints)}
  Introspection Enabled: {introspection}
"""
        for ep in endpoints[:5]:
            output += f"  - {ep.get('path', 'N/A')} -> {ep.get('status', 'N/A')}\n"

        return output

    def cmd_crawler(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /crawler <dominio> [--depth N] [--max N]"
        target = args[0]
        depth = 2
        max_pages = 50
        if '--depth' in args:
            idx = args.index('--depth')
            if idx + 1 < len(args):
                depth = int(args[idx + 1])
        if '--max' in args:
            idx = args.index('--max')
            if idx + 1 < len(args):
                max_pages = int(args[idx + 1])

        print(f"\n[CRAWLER] {target} (depth={depth}, max={max_pages})")
        try:
            from web_crawler import WebCrawler
            crawler = WebCrawler(target, max_depth=depth, max_pages=max_pages)
            result = crawler.crawl()
            filepath = self.tm.save_results(f"{target}_crawler", result)
            return f"""[CRAWLER] {target}
  Pages Crawled: {result['stats']['pages_crawled']}
  Endpoints Found: {result['stats']['endpoints_found']}
  Forms Found: {result['stats']['forms_found']}
  Sensitive Data: {len(result.get('sensitive_data', []))} items
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Crawler failed: {e}"

    def cmd_headers(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /headers <dominio> [--url URL]"
        target = args[0]
        url = None
        if '--url' in args:
            idx = args.index('--url')
            if idx + 1 < len(args):
                url = args[idx + 1]

        print(f"\n[HEADERS] {target}")
        try:
            from header_scanner import HeaderScanner
            scanner = HeaderScanner(target)
            result = scanner.scan(url)
            filepath = self.tm.save_results(f"{target}_headers", result)
            return f"""[HEADERS] {target}
  Score: {result.get('score', 0)}/100
  Vulnerabilities: {len(result.get('vulnerabilities', []))}
  Critical Headers Missing: {sum(1 for h in result.get('critical_headers', {}).values() if h.get('status') == 'MISSING')}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Header scan failed: {e}"

    def cmd_buster(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /buster <dominio> [--timeout N]"
        target = args[0]
        timeout = 3
        if '--timeout' in args:
            idx = args.index('--timeout')
            if idx + 1 < len(args):
                timeout = int(args[idx + 1])

        print(f"\n[BUSTER] {target} (timeout={timeout}s)")
        try:
            from directory_buster import DirectoryBuster
            buster = DirectoryBuster(target, timeout=timeout)
            result = buster.scan()
            filepath = self.tm.save_results(f"{target}_buster", result)
            return f"""[BUSTER] {target}
  Paths Tested: {result['total_paths_tested']}
  Found: {result['found_count']}
  Sensitive: {len(result.get('sensitive_findings', []))}
  By Status: 200={result['by_status']['200']}, 301={result['by_status']['301']}, 403={result['by_status']['403']}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Buster failed: {e}"

    def cmd_cors(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /cors <dominio> [--url URL]"
        target = args[0]
        url = None
        if '--url' in args:
            idx = args.index('--url')
            if idx + 1 < len(args):
                url = args[idx + 1]

        print(f"\n[CORS] {target}")
        try:
            from cors_scanner import CORSScanner
            scanner = CORSScanner(target)
            result = scanner.scan(url)
            filepath = self.tm.save_results(f"{target}_cors", result)
            vulnerable = result.get('vulnerable', False)
            return f"""[CORS] {target}
  Vulnerable: {'YES' if vulnerable else 'No'}
  Findings: {len(result.get('findings', []))}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] CORS scan failed: {e}"

    def cmd_fuzz(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /fuzz <dominio> [--urls URL1 URL2]"
        target = args[0]
        urls = None
        if '--urls' in args:
            idx = args.index('--urls')
            if idx + 1 < len(args):
                urls = args[idx + 1:]

        print(f"\n[FUZZ] {target}")
        try:
            from parameter_fuzzer import ParameterFuzzer
            fuzzer = ParameterFuzzer(target)
            result = fuzzer.run_full_fuzz(urls)
            filepath = self.tm.save_results(f"{target}_fuzz", result)
            summary = result.get('summary', {})
            return f"""[FUZZ] {target}
  Total Findings: {summary.get('total_findings', 0)}
  Critical: {summary.get('critical', 0)}
  High: {summary.get('high', 0)}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Fuzz failed: {e}"

    def cmd_exploit(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /exploit <dominio> --report arquivo.json [--token <token>]"
        target = args[0]
        report = None
        token = None
        if '--report' in args:
            idx = args.index('--report')
            if idx + 1 < len(args):
                report = args[idx + 1]
        if '--token' in args:
            idx = args.index('--token')
            if idx + 1 < len(args):
                token = args[idx + 1]

        print(f"\n[EXPLOIT] {target}")
        try:
            from exploit_executor import ExploitExecutor
            executor = ExploitExecutor(target, token=token)
            if report:
                with open(report, 'r', encoding='utf-8') as f:
                    vuln_report = json.load(f)
                result = executor.run_all_exploits(vuln_report)
            else:
                result = {'error': 'No vulnerability report provided. Run /vuln_scan first.'}
            filepath = self.tm.save_results(f"{target}_exploit", result)
            summary = result.get('summary', {})
            return f"""[EXPLOIT] {target}
  Exploits attempted: {summary.get('total', 0)}
  Successful: {summary.get('successful', 0)}
  Critical: {summary.get('critical', 0)}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Exploit failed: {e}"

    def cmd_brute(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /brute <dominio> [--token <token>] [--passwords lista.txt]"
        target = args[0]
        token = None
        password_file = None
        if '--token' in args:
            idx = args.index('--token')
            if idx + 1 < len(args):
                token = args[idx + 1]
        if '--passwords' in args:
            idx = args.index('--passwords')
            if idx + 1 < len(args):
                password_file = args[idx + 1]

        print(f"\n[BRUTE] {target}")
        try:
            from brute_force import BruteForce
            bf = BruteForce(target)
            if token:
                result = bf.brute_jwt_secret(token)
            else:
                result = bf.run_all()
            filepath = self.tm.save_results(f"{target}_brute", result)
            return f"""[BRUTE] {target}
  Tests run: {result.get('summary', {}).get('total_tests', 0)}
  Successful: {result.get('summary', {}).get('successful', 0)}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Brute force failed: {e}"

    def cmd_subdomain(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /subdomain <dominio> [--wordlist words.txt]"
        target = args[0]
        wordlist = None
        if '--wordlist' in args:
            idx = args.index('--wordlist')
            if idx + 1 < len(args):
                wordlist = args[idx + 1]

        print(f"\n[SUBDOMAIN] {target}")
        try:
            from subdomain_enum import SubdomainEnumerator
            enum = SubdomainEnumerator(target)
            if wordlist:
                with open(wordlist, 'r', encoding='utf-8') as f:
                    enum.wordlist = [line.strip() for line in f if line.strip()]
            result = enum.run_full_enum()
            filepath = self.tm.save_results(f"{target}_subdomains", result)
            return f"""[SUBDOMAIN] {target}
  Total found: {result.get('total_found', 0)}
  With IP: {result.get('summary', {}).get('with_ip', 0)}
  Alive HTTP: {result.get('summary', {}).get('alive_http', 0)}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Subdomain enumeration failed: {e}"

    def cmd_extract(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /extract <dominio> --report arquivo.json [--token <token>]"
        target = args[0]
        report = None
        token = None
        if '--report' in args:
            idx = args.index('--report')
            if idx + 1 < len(args):
                report = args[idx + 1]
        if '--token' in args:
            idx = args.index('--token')
            if idx + 1 < len(args):
                token = args[idx + 1]

        print(f"\n[EXTRACT] {target}")
        try:
            from data_extractor import DataExtractor
            extractor = DataExtractor(target, token=token)
            if report:
                with open(report, 'r', encoding='utf-8') as f:
                    vuln_report = json.load(f)
                result = extractor.run_full_extraction(vuln_report)
            else:
                result = {'error': 'No vulnerability report provided'}
            filepath = self.tm.save_results(f"{target}_extract", result)
            summary = result.get('summary', {})
            return f"""[EXTRACT] {target}
  Total extractions: {summary.get('total_extracted', 0)}
  Secrets found: {summary.get('secrets_found', 0)}
  Files exported: {len(result.get('exported_files', []))}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Extraction failed: {e}"

    def cmd_mass(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /mass target1.com target2.com [--phases recon vuln jwt exploit extract]"
        targets = args[:3]
        phases = ['recon', 'vuln', 'jwt', 'exploit', 'extract']
        if '--phases' in args:
            idx = args.index('--phases')
            phases = args[idx + 1:idx + 6]

        print(f"\n[MASS] Scanning {len(targets)} targets: {', '.join(targets)}")
        try:
            from mass_scanner import MassScanner
            scanner = MassScanner(targets)
            result = scanner.run_mass_scan(targets, phases)
            scanner.print_summary()
            return f"""[MASS SCAN] {len(targets)} target(s)
  Phases: {', '.join(phases)}
  Elapsed: {result.get('summary', {}).get('elapsed_seconds', 0)}s
  Vulnerabilities: {result.get('summary', {}).get('total_vulnerabilities', 0)}
  Critical: {result.get('summary', {}).get('total_critical', 0)}
  Exploits: {result.get('summary', {}).get('total_exploits', 0)}
  Errors: {result.get('summary', {}).get('errors', 0)}
"""
        except Exception as e:
            return f"[ERROR] Mass scan failed: {e}"

    def cmd_darkweb(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /darkweb <query> [--engine ahmia] [--scan]"
        query = args[0]
        engine = 'ahmia'
        do_scan = False
        
        if '--engine' in args:
            idx = args.index('--engine')
            if idx + 1 < len(args):
                engine = args[idx + 1]
        if '--scan' in args or '-s' in args:
            do_scan = True
        
        print(f"\n[DARKWEB] Searching: {query}")
        try:
            from darkweb_search import DarkWebSearch
            searcher = DarkWebSearch()
            result = searcher.search(query, engine)
            
            if do_scan:
                print(f"  [SCAN] Scanning {len(result['results'])} URLs...")
                for r in result['results']:
                    scan = searcher.scan_url(r['url'])
                    r['scan'] = scan
            
            filepath = self.tm.save_results(f"darkweb_{query}", result)
            
            safe_count = sum(1 for r in result.get('results', []) if r.get('safe', False))
            return f"""[DARKWEB] Query: {query}
  Engine: {engine}
  Results: {len(result.get('results', []))}
  Safe: {safe_count}
  Flagged: {len(result.get('results', [])) - safe_count}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Darkweb search failed: {e}"

    def cmd_darkweb_safe(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Mostra URLs .onion conhecidas e seguras"""
        try:
            from darkweb_search import DarkWebSearch
            print("\n[KOWN SAFE ONIONS]")
            for category, sites in DarkWebSearch.KNOWN_ONIONS.items():
                print(f"\n  {category.upper()}:")
                for name, url in sites.items():
                    print(f"    - {name}: {url}")
            return "Done"
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_tor_search(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Busca na dark web via gateways públicos (sem Tor local)"""
        if not args:
            return "[ERROR] Uso: /tor-search <query> [--engine ahmia_api]"
        query = args[0]
        engine = 'ahmia_api'
        
        if '--engine' in args:
            idx = args.index('--engine')
            if idx + 1 < len(args):
                engine = args[idx + 1]
        
        print(f"\n[TOR SEARCH] Query: {query} (via public gateways)")
        try:
            from tor_search import TorSearch
            searcher = TorSearch()
            result = searcher.search(query, engine)
            
            filepath = self.tm.save_results(f"tor_{query}", result)
            
            safe_count = sum(1 for r in result.get('results', []) if r.get('safe', False))
            return f"""[TOR SEARCH] Query: {query}
  Engine: {engine}
  Results: {len(result.get('results', []))}
  Safe: {safe_count}
  Flagged: {len(result.get('results', [])) - safe_count}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Tor search failed: {e}"

    def cmd_tor_known(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Lista URLs .onion conhecidas e seguras"""
        try:
            from tor_search import TorSearch
            searcher = TorSearch()
            result = searcher.list_known()
            
            output = "[KNOWN SAFE .ONION SERVICES]\n\n"
            for cat, sites in result.get('categories', {}).items():
                output += f"  {cat.upper()}:\n"
                for name, url in sites.items():
                    output += f"    - {name}: {url}\n"
                output += "\n"
            output += f"  Total: {result.get('total', 0)} URLs\n"
            return output
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_tor_check(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Verifica acessibilidade de URL .onion"""
        if not args:
            return "[ERROR] Uso: /tor-check <url.onion>"
        url = args[0]
        
        print(f"\n[TOR CHECK] {url}")
        try:
            from tor_search import TorSearch
            searcher = TorSearch()
            result = searcher.check_service(url)
            
            status = "ACCESSIBLE" if result.get('accessible') else "UNAVAILABLE"
            fmt_valid = result.get('format_valid', False)
            method = result.get('method', 'N/A')
            return f"""[TOR CHECK] {url}
  Status: {status}
  Method: {method}
  Format Valid: {fmt_valid}
"""
        except Exception as e:
            return f"[ERROR] Tor check failed: {e}"

    def cmd_virus_scan(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /virus-scan <url_or_file> [--type url|file] [--vt-key KEY]"
        target = args[0]
        scan_type = 'url'
        vt_key = None
        
        if '--type' in args:
            idx = args.index('--type')
            if idx + 1 < len(args):
                scan_type = args[idx + 1]
        if '--vt-key' in args:
            idx = args.index('--vt-key')
            if idx + 1 < len(args):
                vt_key = args[idx + 1]
        
        print(f"\n[VIRUS SCAN] {target} ({scan_type})")
        try:
            from virus_scanner import VirusScanner
            scanner = VirusScanner(vt_api_key=vt_key)
            
            if scan_type == 'url':
                result = scanner.scan_url(target)
            else:
                result = scanner.scan_file(target)
            
            filepath = self.tm.save_results(f"virus_{target}", result)
            
            status = "SAFE" if result.get('safe', False) else "THREAT"
            return f"""[VIRUS SCAN] {target}
  Status: {status}
  Risk Score: {result.get('risk_score', 0)}/100
  Severity: {result.get('severity', 'N/A')}
  Threats: {len(result.get('threats', []))}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Virus scan failed: {e}"

    def cmd_onion_resolve(self, args: List[str] = None, kwargs: Dict = None) -> str:
        if not args:
            return "[ERROR] Uso: /onion-resolve <address>"
        address = args[0]
        
        print(f"\n[ONION RESOLVE] {address}")
        try:
            from onion_resolver import OnionResolver
            resolver = OnionResolver()
            result = resolver.resolve(address)
            
            filepath = self.tm.save_results(f"onion_{address}", result)
            
            status = "OK" if result.get('resolved', False) else "FAIL"
            return f"""[ONION RESOLVE] {address}
  Status: {status}
  Version: {result.get('validation', {}).get('version', 'N/A')}
  IP: {result.get('ip', 'N/A')}
  Tor Accessible: {result.get('tor_accessible', False)}
  Health: {result.get('health', {}).get('status', 'N/A')}
  Saved: {filepath}
"""
        except Exception as e:
            return f"[ERROR] Onion resolve failed: {e}"

    # ================================================================
    # NOVO — Exploit Database & RE
    # ================================================================

    def cmd_exploit_db(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Busca exploits na base de dados"""
        if not args:
            return "[ERROR] Uso: /exploit-db <query> [--category drm_reversing|network_exploit|ctf_binary]"
        query = args[0]
        category = None
        output = None
        if '--category' in args or '-c' in args:
            idx = args.index('--category') if '--category' in args else args.index('-c')
            if idx + 1 < len(args):
                category = args[idx + 1]
        if '--output' in args or '-o' in args:
            idx = args.index('--output') if '--output' in args else args.index('-o')
            if idx + 1 < len(args):
                output = args[idx + 1]

        print(f"\n[EXPLOIT DB] Searching: {query}")
        try:
            from exploit_database import ExploitDatabase
            db = ExploitDatabase()
            result = db.search(query, category)

            if result['results']:
                output_text = f"""[EXPLOIT DATABASE] Query: {query}
  Found: {result['stats']['total']}
  Critical: {result['stats']['critical']}
  High: {result['stats']['high']}
  Medium: {result['stats']['medium']}
"""
                for exp in result['results']:
                    output_text += f"""
  [{exp.get('severity', '?').upper()}] {exp.get('name', 'Unknown')}
    Target: {exp.get('target', exp.get('vuln', 'N/A'))}
    {exp.get('description', '')[:120]}...
    Year: {exp.get('year', 'N/A')}
"""
                    if exp.get('cve'):
                        output_text += f"    CVE: {exp['cve']}\n"
                    if exp.get('reference'):
                        output_text += f"    Ref: {exp['reference']}\n"
            else:
                output_text = f"[NO RESULTS] for '{query}'\nTry: /exploit-db --list"

            if output:
                path = db.export_json(output)
                output_text += f"\n[SAVE] Exported to {path}"

            return output_text
        except Exception as e:
            return f"[ERROR] Exploit DB failed: {e}"

    def cmd_exploit_db_list(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Lista todos os exploits"""
        print("\n[EXPLOIT DB LIST]")
        try:
            from exploit_database import ExploitDatabase
            db = ExploitDatabase()
            cats = db.list_categories()
            output = "[EXPLOITS CATEGORIES]\n"
            for cat, names in cats.items():
                output += f"\n  {cat.upper()}:\n"
                for n in names:
                    output += f"    - {n}\n"
            output += f"\n[RE TECHNIQUES]\n"
            for cat, tech in db.get_techniques().items():
                output += f"\n  {tech['name'].upper()}:\n"
                output += f"    Tools: {', '.join(tech.get('tools', []))}\n"
                output += f"    {tech['description']}\n"
            return output
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_explore(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Analisa PE / extrai strings de binarios"""
        if not args:
            return "[ERROR] Uso: /explore <arquivo.exe> [--strings|--urls|--keys|--ips|--pe]"
        file_path = args[0]
        mode = 'all'
        for arg in args[1:]:
            if arg in ('--strings', '-s'): mode = 'strings'
            elif arg in ('--urls', '-u'): mode = 'urls'
            elif arg in ('--keys', '-k'): mode = 'keys'
            elif arg in ('--ips', '-i'): mode = 'ips'
            elif arg in ('--pe',): mode = 'pe'
        if '--min-length' in args:
            idx = args.index('--min-length')
            if idx + 1 < len(args):
                min_len = int(args[idx + 1])
            else:
                min_len = 4
        else:
            min_len = 4

        print(f"\n[EXPLORE] {file_path} ({mode})")
        try:
            from reverse_engineering import REHelper
            helper = REHelper()
            result = {}

            if mode in ('all', 'strings'):
                result['strings'] = helper.extract_strings(file_path, min_len)
            if mode in ('all', 'urls'):
                result['urls'] = helper.extract_urls(file_path)
            if mode in ('all', 'keys'):
                result['keys'] = helper.extract_keys(file_path)
            if mode in ('all', 'ips'):
                result['ips'] = helper.extract_ips(file_path)
            if mode in ('all', 'pe'):
                result['pe'] = helper.analyze_pe(file_path)

            output = json.dumps(result, indent=2, default=str)

            # Salvar
            out_path = str(Path(file_path).stem) + "_explore.json"
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            output += f"\n\n[SAVE] Saved to {out_path}"
            return output
        except Exception as e:
            return f"[ERROR] Explore failed: {e}"

    def cmd_strings(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Extrai strings de arquivo"""
        if not args:
            return "[ERROR] Uso: /strings <arquivo> [--min N]"
        file_path = args[0]
        min_len = 4
        if '--min' in args:
            idx = args.index('--min')
            if idx + 1 < len(args):
                min_len = int(args[idx + 1])

        try:
            from reverse_engineering import REHelper
            helper = REHelper()
            strings = helper.extract_strings(file_path, min_len)
            return f"[STRINGS from {file_path}] ({len(strings)} found)\n" + "\n".join(strings[:100])
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_pe(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Analisa headers PE"""
        if not args:
            return "[ERROR] Uso: /pe <arquivo.exe>"
        file_path = args[0]
        try:
            from reverse_engineering import REHelper
            helper = REHelper()
            result = helper.analyze_pe(file_path)
            output = json.dumps(result, indent=2, default=str)
            if args and '--output' in args:
                idx = args.index('--output')
                if idx + 1 < len(args):
                    path = helper.export_analysis(result, args[idx + 1])
                    output += f"\n[SAVE] {path}"
            return output
        except Exception as e:
            return f"[ERROR] PE analysis failed: {e}"

    def cmd_hash(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Calcula hashes de arquivo"""
        if not args:
            return "[ERROR] Uso: /hash <arquivo>"
        file_path = args[0]
        try:
            from reverse_engineering import REHelper
            helper = REHelper()
            result = helper.calculate_hashes(file_path)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_shellcode(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Retorna shellcode de template"""
        if not args:
            return "[ERROR] Uso: /shellcode <template_name>"
        template_name = args[0]
        try:
            from reverse_engineering import REHelper
            helper = REHelper()
            result = helper.get_shellcode(template_name)
            if 'error' in result:
                return f"[ERROR] {result['error']}"
            return f"""[SHELLCODE] {result['name']}
  Description: {result['description']}
  Length: {result['length']} bytes
  Flags: {', '.join(result.get('flags', [])) or 'None'}

  C format:
    char shellcode[] = "{result['shellcode_c']}";

  Hex:
    {result['shellcode_hex']}
"""
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_shellcode_list(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Lista shellcodes disponiveis"""
        try:
            from reverse_engineering import REHelper
            helper = REHelper()
            result = helper.list_shellcodes()
            output = "[AVAILABLE SHELLCODES]\n\n"
            for name in result['templates']:
                tmpl = helper.SHELLCODE_TEMPLATES[name]
                output += f"  - {name}: {tmpl['description']} ({tmpl['length']} bytes)\n"
            output += f"\n  Total: {result['count']}\n"
            return output
        except Exception as e:
            return f"[ERROR] {e}"

    def cmd_ctf(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """CTF helper commands"""
        if not args:
            return "[ERROR] Uso: /ctf <pattern_create|pattern_offset|rop_x86|rop_x64|encode|decode|template> [args...]"
        cmd = args[0]
        cmd_args = args[1:]

        try:
            from ctf_helper import CTFHelper
            helper = CTFHelper()
            result = helper.run(cmd, cmd_args)

            if 'error' in result:
                return f"[ERROR] {result['error']}"
            if 'result' in result:
                r = result['result']
                if isinstance(r, (bytes, bytearray)):
                    return r.hex()
                return json.dumps(r, indent=2, default=str)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return f"[ERROR] CTF helper failed: {e}"

    def cmd_ctf_templates(self, args: List[str] = None, kwargs: Dict = None) -> str:
        """Lista templates de exploit"""
        try:
            from ctf_helper import CTFHelper
            helper = CTFHelper()
            templates = helper.list_templates()
            output = "[CTF EXPLOIT TEMPLATES]\n\n"
            for t in templates:
                output += f"  - {t}\n"
            output += "\nUse: /ctf template <nome>\n"
            return output
        except Exception as e:
            return f"[ERROR] {e}"

    def _format_output(self, results: Dict, filepath: str) -> str:
        summary = results.get('summary', {})
        recon = results.get('recon', {})
        waf = results.get('waf', {})
        fw = results.get('framework', {})

        output = f"""[{results.get('target', 'Unknown').upper()}]
  Time: {results.get('timestamp', 'Unknown')}

  [RECONNAISSANCE]
    IP: {recon.get('ip', 'Unknown')}
    Server: {recon.get('server', 'Unknown')}
    Technologies: {', '.join(recon.get('technologies', [])) or 'None detected'}

  [WAF DETECTION]
    Detected: {'Yes' if waf.get('detected') else 'No'}
    Type: {waf.get('type', 'Unknown')}
    CF-Ray: {waf.get('cf_ray', 'N/A')}

  [FRAMEWORK]
    Ruby on Rails: {'Yes' if fw.get('rails') else 'No'}
    Next.js: {'Yes' if fw.get('nextjs') else 'No'}
    Express: {'Yes' if fw.get('express') else 'No'}
    Django: {'Yes' if fw.get('django') else 'No'}

  [SUMMARY]
    Total Vulnerabilities: {summary.get('total', 0)}
    Critical: {summary.get('critical', 0)}
    High: {summary.get('high', 0)}
    Medium: {summary.get('medium', 0)}

  [RESULTS]
    Saved: {filepath}
"""

        if results.get('vulnerabilities'):
            output += "\n  [VULNERABILITIES]\n"
            for v in results['vulnerabilities'][:5]:
                output += f"    [{v.get('severity', 'UNKNOWN')}] {v.get('type', 'Unknown')}\n"

        return output


def main():
    # Fix Windows console encoding
    import io as _io
    import sys as _sys
    _sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Parse manually to support --flags in args
    import sys
    args = sys.argv[1:]

    if not args:
        print("OpenCode Vulnerability Scanner Integration")
        print("Usage: integration.py /command [args...]")
        print("Use /vuln_help for full command list")
        return

    command = args[0]
    cmd_args = args[1:]

    tm = ToolManager()
    handler = CommandHandler(tm)
    result = handler.handle(command, cmd_args)
    print(result)


if __name__ == "__main__":
    main()
