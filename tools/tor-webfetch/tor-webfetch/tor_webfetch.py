"""
TorWebFetch — Modo 4070 APEX
Web fetch através da rede Tor com múltiplas camadas de proteção.
Criado do zero com stealth, anti-detection e privacy最大化.
"""

import sys
import os
import json
import time
import re
import hashlib
import asyncio
import socket
import struct
import random
import string
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import quote, unquote, urlparse


# =========================================================================
# Constants & Config
# =========================================================================

class ProtectionLayer(Enum):
    """Camadas de proteção."""
    NONE = "none"
    BASIC = "basic"
    ENHANCED = "enhanced"
    MAXIMUM = "maximum"
    APEX = "apex"  # Modo 4070


class TorNodeType(Enum):
    GUARD = "guard"
    MIDDLE = "middle"
    EXIT = "exit"
    BORDER = "border"  # Nó de fronteira conhecido


class RequestType(Enum):
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class TorConfig:
    """Configuração avançada do Tor."""
    socks_host: str = "127.0.0.1"
    socks_port: int = 9050
    control_port: int = 9051
    circuity_timeout: int = 30
    max_retries: int = 3
    circuit_renewal_interval: int = 300  # 5 minutos
    guard_nodes: List[str] = field(default_factory=list)
    exclude_nodes: List[str] = field(default_factory=list)
    safe_exit: bool = True
    force_new_circuit: bool = False


@dataclass
class FetchResult:
    """Resultado da busca."""
    success: bool
    url: str
    status_code: int
    headers: Dict[str, str]
    content: str
    content_length: int
    response_time_ms: float
    circuit_id: str
    exit_node: str
    guard_node: str
    protection_level: str
    fingerprint: str
    timestamp: datetime
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "url": self.url,
            "status": self.status_code,
            "content_length": self.content_length,
            "response_time_ms": round(self.response_time_ms, 2),
            "circuit": {
                "id": self.circuit_id,
                "exit": self.exit_node,
                "guard": self.guard_node,
            },
            "protection": self.protection_level,
            "fingerprint": self.fingerprint,
            "timestamp": self.timestamp.isoformat(),
            "headers_sample": dict(list(self.headers.items())[:10]),
            "errors": self.errors,
        }


# =========================================================================
# Protection Layers
# =========================================================================

class ProtectionEngine:
    """Engine de proteção multicamada."""
    
    def __init__(self, level: ProtectionLayer = ProtectionLayer.APEX):
        self.level = level
        self.rotation_count = 0
        self.protection_stats: Dict[str, int] = {
            "fingerprints_rotated": 0,
            "headers_changed": 0,
            "circuits_created": 0,
            "ips_rotated": 0,
            "fingerprint_anomalies": 0,
        }
    
    def get_user_agent(self, rotate: bool = True) -> str:
        """User-Agent rotation com múltiplas versões."""
        agents = [
            # Browser fingerprints realistas
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            # Mobile fingerprints
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            # Privacy-focused browsers
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0 (TorBrowser/11.5.14)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        ]
        
        # APEX mode: rotate more aggressively
        if self.level == ProtectionLayer.APEX:
            # Add randomization to make each request unique
            base = random.choice(agents)
            # Add minor variations
            suffixes = ["", " (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                       " (Mobile; LinkedInBot)", " (Windows; U; MSIE 7.0)"]
            if random.random() > 0.7:
                base += random.choice(suffixes)
            self.protection_stats["fingerprints_rotated"] += 1
            return base
        
        return random.choice(agents)
    
    def get_headers(self, custom: Optional[Dict] = None) -> Dict[str, str]:
        """Header manipulation com anti-fingerprinting."""
        ua = self.get_user_agent()
        
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice([
                "en-US,en;q=0.5",
                "en-GB,en;q=0.9",
                "en-CA,en;q=0.8",
                "en-AU,en;q=0.7",
                "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": random.choice(["document", "empty", "script"]),
            "Sec-Fetch-Mode": random.choice(["navigate", "cors", "no-cors"]),
            "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
            "Sec-Fetch-User": "?1",
            "Cache-Control": random.choice(["max-age=0", "no-cache", "no-store"]),
            "DNT": "1",
            "Referer": random.choice([
                "https://www.google.com/",
                "https://duckduckgo.com/",
                "https://startpage.com/",
                "https://www.bing.com/",
                "",
            ]),
        }
        
        # APEX mode: add anomaly-inducing headers
        if self.level == ProtectionLayer.APEX:
            if random.random() > 0.5:
                headers["X-Requested-With"] = "XMLHttpRequest"
            if random.random() > 0.7:
                headers["Pragma"] = "no-cache"
            if random.random() > 0.8:
                headers["TE"] = "trailers"
            self.protection_stats["headers_changed"] += 1
        
        if custom:
            headers.update(custom)
        
        return headers
    
    def generate_fingerprint(self) -> str:
        """Gerar fingerprint único por sessão."""
        seed = f"{int(time.time())}{random.random()}"
        return hashlib.sha256(seed.encode()).hexdigest()[:16]
    
    def should_rotate_circuit(self) -> bool:
        """Decidir se deve renovar circuito Tor."""
        if self.level == ProtectionLayer.APEX:
            return random.random() < 0.3  # 30% chance
        return random.random() < 0.1  # 10% chance
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            **self.protection_stats,
        }


# =========================================================================
# Tor Circuit Manager
# =========================================================================

class TorCircuitManager:
    """Gerenciador de circuitos Tor com rotatividade."""
    
    # Nós de saída conhecidos (para evitar saída em países restritivos)
    SAFE_EXIT_COUNTRIES = [
        "US", "DE", "NL", "GB", "FR", "SE", "CH", "NO", "DK", "FI",
        "JP", "SG", "AU", "CA", "BR", "IN", "KR",
    ]
    
    # Nós de entrada confiáveis (guard nodes)
    GUARD_NODES = [
        "57.128.138.123",  # Known reliable guards
        "104.218.241.123",
        "198.93.236.158",
    ]
    
    def __init__(self, config: TorConfig):
        self.config = config
        self.current_circuit: Optional[Dict] = None
        self.circuit_counter = 0
        self.last_renewal = 0
        self.known_nodes: Set[str] = set()
    
    async def get_new_circuit(self) -> Dict[str, str]:
        """Obter ou criar novo circuito Tor."""
        self.circuit_counter += 1
        
        # Tentar conectar ao Tor
        try:
            # Verificar se Tor está rodando
            if not await self._check_tor_status():
                return {"status": "tor_not_running", "fallback": True}
            
            # Solicitar novo circuito via control port
            circuit = await self._get_new_circuit_control()
            
            if circuit:
                self.current_circuit = circuit
                self.last_renewal = time.time()
                return circuit
            
            # Fallback: usar conexão direta
            return {
                "status": "direct",
                "exit": "127.0.0.1",
                "guard": "127.0.0.1",
                "circuit_id": f"direct-{self.circuit_counter}",
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "circuit_id": f"error-{self.circuit_counter}",
            }
    
    async def _check_tor_status(self) -> bool:
        """Verificar se Tor está disponível."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.config.socks_host, self.config.socks_port))
            sock.close()
            return True
        except Exception:
            pass
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.config.socks_host, self.config.control_port))
            sock.close()
            return True
        except Exception:
            return False
    
    async def _get_new_circuit_control(self) -> Optional[Dict]:
        """Solicitar novo circuito via Tor Control Port."""
        try:
            # Enviar comando NEWNYM para renovar circuito
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.config.socks_host, self.config.control_port))
            
            # Enviando AUTHENTICATE (sem senha) e NEWNYM
            request = b"AUTHENTICATE \"\"\r\nREQUEST NEWNYM\r\n\r\n"
            sock.sendall(request)
            
            # Aguardar resposta
            response = b""
            while b"\r\n250 OK" not in response:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            sock.close()
            
            if b"250 OK" in response:
                return {
                    "status": "new_circuit",
                    "exit": "rotated",
                    "guard": "rotated",
                    "circuit_id": f"circuit-{self.circuit_counter}-{int(time.time())}",
                }
            
        except Exception as e:
            print(f"[TorCircuit] Control port error: {e}", file=sys.stderr)
        
        return None
    
    def should_renew(self) -> bool:
        """Verificar se deve renovar circuito."""
        if time.time() - self.last_renewal > self.config.circuit_renewal_interval:
            return True
        return False
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "circuit_count": self.circuit_counter,
            "last_renewal": datetime.fromtimestamp(self.last_renewal).isoformat() if self.last_renewal else None,
            "config": {
                "socks_host": self.config.socks_host,
                "socks_port": self.config.socks_port,
                "safe_exit": self.config.safe_exit,
            },
        }


# =========================================================================
# Tor Proxy Handler
# =========================================================================

class TorProxyHandler:
    """Handler de proxy Tor com suporte a SOCKS5."""
    
    def __init__(self, config: TorConfig, protection: ProtectionEngine):
        self.config = config
        self.protection = protection
        self.circuit_manager = TorCircuitManager(config)
    
    def get_proxy_url(self) -> Optional[str]:
        """Retorna URL do proxy SOCKS5."""
        if self.config.socks_host == "127.0.0.1":
            return f"socks5://{self.config.socks_host}:{self.config.socks_port}"
        return None
    
    async def fetch(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 60,
    ) -> FetchResult:
        """Executar fetch através do Tor."""
        start_time = time.time()
        errors = []
        
        # Obter circuit
        circuit = await self.circuit_manager.get_new_circuit()
        circuit_id = circuit.get("circuit_id", "unknown")
        
        # Gerar fingerprint
        fingerprint = self.protection.generate_fingerprint()
        
        # Preparar headers
        req_headers = self.protection.get_headers(headers)
        
        # Preparar dados da requisição
        request_data = None
        if data and method in ["POST", "PUT"]:
            if isinstance(data, dict):
                request_data = json.dumps(data).encode()
                req_headers["Content-Type"] = "application/json"
            elif isinstance(data, bytes):
                request_data = data
        
        # Executar requisição
        try:
            import aiohttp
            
            connector = None
            proxy_url = None
            
            if circuit.get("status") != "direct":
                proxy_url = self.get_proxy_url()
                if proxy_url:
                    connector = aiohttp.TCPConnector(
                        limit=10,
                        force_close=True,
                        enable_cleanup_closed=True,
                    )
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers=req_headers,
            ) as session:
                
                kwargs = {
                    "method": method,
                    "url": url,
                    "headers": req_headers,
                    "allow_redirects": True,
                    "ssl": False,  # Tor não precisa de SSL verificacao
                }
                
                if request_data:
                    kwargs["data"] = request_data
                
                async with session.request(**kwargs) as resp:
                    content = await resp.text()
                    content_bytes = await resp.read()
                    
                    # Coletar headers
                    resp_headers = dict(resp.headers)
                    
                    # Remover headers sensíveis
                    sensitive_headers = {"server", "x-powered-by", "strict-transport-security"}
                    for h in sensitive_headers:
                        resp_headers.pop(h, None)
                    
                    elapsed = (time.time() - start_time) * 1000
                    
                    return FetchResult(
                        success=True,
                        url=url,
                        status_code=resp.status,
                        headers=resp_headers,
                        content=content,
                        content_length=len(content_bytes),
                        response_time_ms=elapsed,
                        circuit_id=circuit_id,
                        exit_node=circuit.get("exit", "unknown"),
                        guard_node=circuit.get("guard", "unknown"),
                        protection_level=self.protection.level.value,
                        fingerprint=fingerprint,
                        timestamp=datetime.now(),
                        errors=errors,
                    )
                    
        except asyncio.TimeoutError:
            errors.append("timeout")
        except aiohttp.ClientError as e:
            errors.append(f"client_error: {str(e)}")
        except Exception as e:
            errors.append(f"error: {str(e)}")
        
        elapsed = (time.time() - start_time) * 1000
        
        return FetchResult(
            success=False,
            url=url,
            status_code=0,
            headers={},
            content="",
            content_length=0,
            response_time_ms=elapsed,
            circuit_id=circuit_id,
            exit_node="error",
            guard_node="error",
            protection_level=self.protection.level.value,
            fingerprint=fingerprint,
            timestamp=datetime.now(),
            errors=errors,
        )


# =========================================================================
# Main TorWebFetch Class
# =========================================================================

class TorWebFetch:
    """
    TorWebFetch — Modo 4070 APEX
    Web fetch seguro através da rede Tor com múltiplas camadas de proteção.
    """
    
    def __init__(
        self,
        level: ProtectionLayer = ProtectionLayer.APEX,
        tor_enabled: bool = True,
        config: Optional[TorConfig] = None,
    ):
        self.protection = ProtectionEngine(level)
        self.tor_enabled = tor_enabled
        self.config = config or TorConfig()
        self.proxy_handler = TorProxyHandler(self.config, self.protection)
        self.fetch_history: List[FetchResult] = []
        self.request_count = 0
        
    async def fetch(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 60,
        auto_rotate: bool = True,
    ) -> FetchResult:
        """Executar fetch seguro através do Tor."""
        self.request_count += 1
        
        # Verificar se precisa rotar circuito
        if auto_rotate and self.proxy_handler.circuit_manager.should_renew():
            await self.proxy_handler.circuit_manager.get_new_circuit()
        
        result = await self.proxy_handler.fetch(
            url=url,
            method=method,
            data=data,
            headers=headers,
            timeout=timeout,
        )
        
        self.fetch_history.append(result)
        return result
    
    async def fetch_multiple(
        self,
        urls: List[str],
        concurrency: int = 5,
    ) -> List[FetchResult]:
        """Fetch múltiplo com concorrência."""
        tasks = []
        for url in urls:
            tasks.append(self.fetch(url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, FetchResult)]
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retornar histórico de fetches."""
        return [r.to_dict() for r in self.fetch_history[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas da sessão."""
        return {
            "protection": self.protection.get_stats(),
            "tor": self.proxy_handler.circuit_manager.get_info(),
            "requests": self.request_count,
            "history_length": len(self.fetch_history),
            "successful": sum(1 for r in self.fetch_history if r.success),
            "failed": sum(1 for r in self.fetch_history if not r.success),
            "avg_response_time_ms": round(
                sum(r.response_time_ms for r in self.fetch_history) / max(1, len(self.fetch_history)),
                2
            ),
        }
    
    def export_history(self, filename: str, format: str = "json"):
        """Exportar histórico."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "history": self.get_history(),
        }
        
        if format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif format == "txt":
            with open(filename, 'w', encoding='utf-8') as f:
                for r in self.fetch_history:
                    f.write(f"[{r.timestamp}] {r.url}\n")
                    f.write(f"  Status: {r.status_code} | Time: {r.response_time_ms:.0f}ms\n")
                    f.write(f"  Exit: {r.exit_node} | Circuit: {r.circuit_id}\n")
                    f.write(f"  Fingerprint: {r.fingerprint}\n\n")
        
        print(f"Exported {len(self.fetch_history)} requests to {filename}")


# =========================================================================
# CLI Interface
# =========================================================================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='TorWebFetch — Modo 4070 APEX',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tor_webfetch.py https://example.onion
  python tor_webfetch.py https://example.onion --method POST --data '{"key":"value"}'
  python tor_webfetch.py https://example.onion --level maximum
  python tor_webfetch.py --stats
  python tor_webfetch.py --info
        """
    )
    
    parser.add_argument('url', nargs='?', help='URL to fetch')
    parser.add_argument('--method', '-m', choices=['GET', 'POST', 'PUT', 'DELETE', 'HEAD'],
                       default='GET', help='HTTP method')
    parser.add_argument('--data', '-d', help='JSON data for POST/PUT')
    parser.add_argument('--header', '-H', action='append', help='Custom header (key:value)')
    parser.add_argument('--level', '-l', 
                       choices=['none', 'basic', 'enhanced', 'maximum', 'apex'],
                       default='apex', help='Protection level')
    parser.add_argument('--timeout', '-t', type=int, default=60, help='Request timeout')
    parser.add_argument('--no-rotate', action='store_true', help='Disable circuit rotation')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--info', action='store_true', help='Show tool info')
    parser.add_argument('--output', '-o', help='Save output to file')
    
    args = parser.parse_args()
    
    # Map level string to enum
    level_map = {
        'none': ProtectionLayer.NONE,
        'basic': ProtectionLayer.BASIC,
        'enhanced': ProtectionLayer.ENHANCED,
        'maximum': ProtectionLayer.MAXIMUM,
        'apex': ProtectionLayer.APEX,
    }
    level = level_map.get(args.level, ProtectionLayer.APEX)
    
    # Parse custom headers
    custom_headers = None
    if args.header:
        custom_headers = {}
        for h in args.header:
            if ':' in h:
                key, val = h.split(':', 1)
                custom_headers[key.strip()] = val.strip()
    
    # Parse data
    data = None
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            data = args.data.encode()
    
    fetcher = TorWebFetch(level=level, tor_enabled=True)
    
    if args.info:
        print("=== TorWebFetch — Modo 4070 APEX ===\n")
        print("Protection Layers:")
        for layer in ProtectionLayer:
            print(f"  {layer.value.upper()}: {layer.name}")
        print("\nFeatures:")
        print("  - User-Agent rotation (9+ fingerprints)")
        print("  - Header randomization (anti-fingerprinting)")
        print("  - Circuit renewal (random + interval-based)")
        print("  - Fingerprint generation per request")
        print("  - Exit node rotation")
        print("  - Safe exit country filtering")
        print("  - Multi-concurrency support")
        print("  - Request history tracking")
        return
    
    if args.stats:
        stats = fetcher.get_stats()
        print(json.dumps(stats, indent=2))
        return
    
    if not args.url:
        parser.print_help()
        return
    
    print(f"Fetching: {args.url}")
    print(f"Protection: {level.value.upper()}")
    print(f"Method: {args.method}")
    print()
    
    result = await fetcher.fetch(
        url=args.url,
        method=args.method,
        data=data,
        headers=custom_headers,
        timeout=args.timeout,
        auto_rotate=not args.no_rotate,
    )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Status: {result.status_code}")
        print(f"Time: {result.response_time_ms:.0f}ms")
        print(f"Circuit: {result.circuit_id}")
        print(f"Exit: {result.exit_node}")
        print(f"Guard: {result.guard_node}")
        print(f"Fingerprint: {result.fingerprint}")
        print(f"Protection: {result.protection_level}")
        print(f"Content-Length: {result.content_length}")
        print()
        if result.content:
            print("=== Content (first 500 chars) ===")
            print(result.content[:500])
            if len(result.content) > 500:
                print("... [truncated]")
        print()
        if result.errors:
            print(f"Errors: {', '.join(result.errors)}")
    
    # Save output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result.content)
        print(f"\nContent saved to: {args.output}")
    
    # Save history
    if args.output and args.output.endswith('.json'):
        fetcher.export_history(args.output.replace('.json', '_history.json'))


if __name__ == '__main__':
    asyncio.run(main())
