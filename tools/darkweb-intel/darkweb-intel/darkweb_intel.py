"""
DarkWeb Intel — Modo 4070
Ferramenta de inteligencia e pesquisa na darkweb.
Coleta real via gateways públicos, APIs de threat intelligence, paste sites.
Suporte a proxy SOCKS5/Tor.
"""

import sys
import os
import json
import time
import re
import hashlib
import asyncio
import aiohttp
import socket
import struct
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import quote, unquote


# =========================================================================
# Constants & Config
# =========================================================================

class SourceType(Enum):
    MARKET = "market"
    FORUM = "forum"
    PASTE = "paste"
    REPO = "repo"
    BLOG = "blog"
    DOX = "dox"
    EXPLOIT = "exploit"
    API = "api"  # Threat intelligence APIs


class ThreatCategory(Enum):
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    CREDENTIALS = "credentials"
    EXFILTRATION = "exfiltration"
    AUTH_BYPASS = "auth_bypass"
    SQLi = "sqli"
    XSS = "xss"
    RCE = "rce"
    SSRF = "ssrf"
    LFI = "lfi"
    COMMAND_INJ = "command_injection"
    DESERIALIZATION = "deserialization"
    C2 = "c2"
    STEALER = "stealer"
    LOADER = "loader"
    BULK_MAIL = "bulk_mail"
    CARDING = "carding"
    FRAUD = "fraud"
    PHI = "phi"
    PII = "pii"
    DATA_BREACH = "data_breach"
    EXPLOIT_KIT = "exploit_kit"


@dataclass
class DarkWebItem:
    item_id: str
    source_type: SourceType
    category: ThreatCategory
    title: str
    content_preview: str
    url: str
    timestamp: datetime
    quality_score: float
    tags: List[str] = field(default_factory=list)
    raw_data: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "source_type": self.source_type.value,
            "category": self.category.value,
            "title": self.title,
            "preview": self.content_preview[:500],
            "url": self.url,
            "timestamp": self.timestamp.isoformat(),
            "quality": self.quality_score,
            "tags": self.tags,
        }


# =========================================================================
# Tor/SOCKS5 Proxy Support
# =========================================================================

class TorProxyManager:
    """Gerencia conexões via proxy SOCKS5/Tor."""
    
    DEFAULT_SOCKS_HOST = "127.0.0.1"
    DEFAULT_SOCKS_PORT = 9050
    DEFAULT_HTTP_PORT = 9051
    
    @classmethod
    def detect_tor(cls) -> bool:
        """Detecta se o Tor está rodando localmente."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((cls.DEFAULT_SOCKS_HOST, cls.DEFAULT_SOCKS_PORT))
            sock.close()
            return True
        except Exception:
            pass
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((cls.DEFAULT_SOCKS_HOST, cls.DEFAULT_HTTP_PORT))
            sock.close()
            return True
        except Exception:
            return False
    
    @classmethod
    def get_proxy_config(cls) -> Dict[str, str]:
        """Retorna config de proxy se Tor estiver disponível."""
        if cls.detect_tor():
            return {
                "socks_host": cls.DEFAULT_SOCKS_HOST,
                "socks_port": cls.DEFAULT_SOCKS_PORT,
                "http_port": cls.DEFAULT_HTTP_PORT,
                "enabled": True,
            }
        return {
            "socks_host": None,
            "socks_port": None,
            "http_port": None,
            "enabled": False,
        }
    
    @classmethod
    async def get_session(cls, proxy_config: Optional[Dict] = None) -> Tuple[aiohttp.ClientSession, Dict]:
        """Cria session com proxy configurado."""
        if proxy_config is None:
            proxy_config = cls.get_proxy_config()
        
        connector = None
        proxy_url = None
        
        if proxy_config.get("enabled"):
            # Try SOCKS5
            socks_url = f"socks5://{proxy_config['socks_host']}:{proxy_config['socks_port']}"
            connector = aiohttp.TCPConnector(
                limit=10,
                force_close=True,
            )
            proxy_url = socks_url
        else:
            connector = aiohttp.TCPConnector(
                limit=10,
                force_close=True,
            )
        
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
        )
        
        return session, proxy_config


# =========================================================================
# Public DarkWeb Gateways
# =========================================================================

class PublicGateways:
    """Gateways públicos para acessar .onion sites."""
    
    # Gateways HTTP que convertem .onion em HTTP normal
    HTTP_GATEWAYS = [
        "https://onion.link",
        "https://onion.sh",
        "https://degradedweb.org",
    ]
    
    # APIs públicas de indexação de darkweb
    APIs = {
        "onion_scan": "https://api.onion.ws",
        "darkweb_index": "https://www.darkweb.com.tr/api",
        "tor_lookup": "https://torproject.org",
    }
    
    # Pastebin e coleções de dados vazados (acessíveis via HTTP normal)
    LEAK_SOURCES = [
        "https://psbdmp.ws/api/v3/search/{query}",
        "https://pastebin.com/ajax/ajax_search.php",
        "https://sopha.me/search?q={query}",
    ]


# =========================================================================
# Threat Intelligence APIs
# =========================================================================

class ThreatIntelAPI:
    """Interfaces com APIs públicas de threat intelligence."""
    
    # APIs gratuitas (sem key necessária ou com rate limit)
    ENRICHMENT_APIS = [
        {
            "name": "VirusTotal",
            "url": "https://www.virustotal.com/api/v3/ip_addresses/{ip}",
            "requires_key": True,
            "description": "Análise de IPs e hashes",
        },
        {
            "name": "AlienVault OTX",
            "url": "https://otx.alienvault.com/api/v1/indicators/{indicator}/general",
            "requires_key": True,
            "description": "Open Threat Exchange",
        },
        {
            "name": "AbuseIPDB",
            "url": "https://api.abuseipdb.com/api/v2/ip/{ip}",
            "requires_key": True,
            "description": "Reportes de abuso",
        },
    ]
    
    # Pastebin search API (pública)
    PASTE_API = "https://psbdmp.ws/api/v3/search/{query}"
    
    # HaveIBeenPwned (para verificação de creds)
    HIBP_API = "https://haveibeenpwned.com/api/v3/breachedaccount/{domain}"
    
    # APIs públicas de inteligência (sem key)
    PUBLIC_APIS = {
        "greynoise": "https://api.greynoise.io/v3/query",  # Requires key
        "shodan": "https://api.shodan.io/shodan/host/{ip}",  # Requires key
        "crtsh": "https://crt.sh/?q={domain}&output=json",
    }
    
    @classmethod
    async def search_pastes(cls, session: aiohttp.ClientSession, query: str) -> List[Dict]:
        """Busca em paste sites via psbdmp.ws."""
        items = []
        try:
            url = cls.PASTE_API.format(query=quote(query))
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and "paste" in data:
                        for paste in data["paste"][:10]:
                            items.append({
                                "source": "psbdmp",
                                "title": f"{query} - paste leak",
                                "content": paste.get("paste", "")[:500],
                                "date": paste.get("date", ""),
                                "views": paste.get("views", 0),
                            })
        except Exception as e:
            print(f"[ThreatIntelAPI] Paste search error: {e}", file=sys.stderr)
        return items
    
    @classmethod
    async def check_pastebin(cls, session: aiohttp.ClientSession, query: str) -> List[Dict]:
        """Busca direta no Pastebin."""
        items = []
        search_terms = [
            f"{query} password",
            f"{query} credentials",
            f"{query} dump",
            f"{query} leak",
            f"{query} exploit",
        ]
        
        for term in search_terms:
            try:
                url = f"https://pastebin.com/ajax/ajax_search.php"
                data = {"searchstring": term, "searchincontent": "1"}
                async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Parse resultados
                        posts = re.findall(r'<a href="/(.+?)"[^>]*>(.+?)</a>', html)
                        for post_id, title in posts[:5]:
                            items.append({
                                "source": "pastebin",
                                "title": f"{term} - {title[:100]}",
                                "url": f"https://pastebin.com/{post_id}",
                                "content": title[:300],
                            })
            except Exception:
                continue
        
        return items[:20]


# =========================================================================
# DarkWeb Sources
# =========================================================================

class DarkWebSource:
    """Base class for darkweb sources."""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.last_crawl: Optional[datetime] = None
        self.items_found: int = 0
    
    async def crawl(self, query: str, session: aiohttp.ClientSession, 
                   proxy_config: Dict) -> List[DarkWebItem]:
        raise NotImplementedError
    
    def should_crawl(self, min_hours: int = 24) -> bool:
        if not self.enabled:
            return False
        if self.last_crawl is None:
            return True
        return (datetime.now() - self.last_crawl).total_seconds() > min_hours * 3600


class PasteSource(DarkWebSource):
    """Search paste sites for leaks and credentials."""
    
    # Fallback sources quando psbdmp não funciona
    FALLBACK_PASTE_SOURCES = [
        "https://pastebin.com/ajax/ajax_search.php",
        "https://sopha.me/search?q=",
    ]
    
    def __init__(self):
        super().__init__("paste_search")
        self.active_source = "psbdmp"  # Tentar psbdmp primeiro
    
    async def crawl(self, query: str, session: aiohttp.ClientSession,
                   proxy_config: Dict) -> List[DarkWebItem]:
        items = []
        
        # Try psbdmp first
        try:
            url = ThreatIntelAPI.PASTE_API.format(query=quote(query))
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict) and "paste" in data:
                        for paste in data["paste"][:10]:
                            content = paste.get("paste", "")
                            if len(content) > 20:
                                items.append(DarkWebItem(
                                    item_id=hashlib.md5(content.encode()).hexdigest()[:12],
                                    source_type=SourceType.PASTE,
                                    category=self._detect_category(content),
                                    title=f"{query} - paste leak",
                                    content_preview=content[:500],
                                    url=f"https://psbdmp.ws/pastes/{paste.get('id', '')}",
                                    timestamp=datetime.now(),
                                    quality_score=0.7,
                                    tags=[query, "paste", "leak"],
                                ))
                        self.active_source = "psbdmp"
        except Exception as e:
            print(f"[PasteSource] psbdmp unavailable, trying fallbacks...", file=sys.stderr)
        
        # Try Pastebin
        pastebin_items = await ThreatIntelAPI.check_pastebin(session, query)
        for p in pastebin_items:
            items.append(DarkWebItem(
                item_id=hashlib.md5(p.get("url", "").encode()).hexdigest()[:12],
                source_type=SourceType.PASTE,
                category=ThreatCategory.CREDENTIALS,
                title=p["title"],
                content_preview=p.get("content", "")[:300],
                url=p.get("url", ""),
                timestamp=datetime.now(),
                quality_score=0.6,
                tags=[query, "pastebin"],
            ))
            self.active_source = "pastebin"
        
        # Try sopha.me as fallback
        if not items:
            try:
                url = f"https://sopha.me/search?q={quote(query)}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Parse results
                        pastes = re.findall(r'<a href="([^"]+)">([^<]+)</a>.*?<p>([^<]+)</p>', html)
                        for link, title, snippet in pastes[:5]:
                            items.append(DarkWebItem(
                                item_id=hashlib.md5(link.encode()).hexdigest()[:12],
                                source_type=SourceType.PASTE,
                                category=self._detect_category(snippet),
                                title=title[:200],
                                content_preview=snippet[:300],
                                url=link,
                                timestamp=datetime.now(),
                                quality_score=0.5,
                                tags=[query, "sopha"],
                            ))
                        if items:
                            self.active_source = "sopha"
            except Exception:
                pass
        
        self.items_found += len(items)
        return items
    
    def _detect_category(self, content: str) -> ThreatCategory:
        content_lower = content.lower()
        if any(k in content_lower for k in ["password", "passwd", "cred", "login", "user:"]):
            return ThreatCategory.CREDENTIALS
        if any(k in content_lower for k in ["exploit", "cve", "0day", "rce"]):
            return ThreatCategory.RCE
        if any(k in content_lower for k in ["ransom", "decrypt", "bitcoin"]):
            return ThreatCategory.RANSOMWARE
        return ThreatCategory.DATA_BREACH


class ForumSource(DarkWebSource):
    """Search hacker forums and communities."""
    
    # Fóruns públicos de segurança (não darkweb, mas relevantes)
    FORUMS = [
        {
            "name": "Reddit r/netsec",
            "url": "https://www.reddit.com/r/netsec/search?q={query}&restrict_sr=1",
            "type": SourceType.FORUM,
        },
        {
            "name": "Reddit r/cybersecurity",
            "url": "https://www.reddit.com/r/cybersecurity/search?q={query}&restrict_sr=1",
            "type": SourceType.FORUM,
        },
        {
            "name": "HackerNews",
            "url": "https://hn.algolia.com/api/v1/search?query={query}",
            "type": SourceType.FORUM,
        },
    ]
    
    def __init__(self):
        super().__init__("forum_search")
    
    async def crawl(self, query: str, session: aiohttp.ClientSession,
                   proxy_config: Dict) -> List[DarkWebItem]:
        items = []
        
        # Search Reddit r/netsec
        try:
            url = "https://www.reddit.com/r/netsec/search?q={}&restrict_sr=1".format(quote(query))
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # Parse JSON data embedded in page
                    json_matches = re.findall(r'"title":"([^"]+)"', html)
                    for title in json_matches[:10]:
                        items.append(DarkWebItem(
                            item_id=hashlib.md5(title.encode()).hexdigest()[:12],
                            source_type=SourceType.FORUM,
                            category=self._detect_category(query),
                            title=title[:200],
                            content_preview=f"Reddit r/netsec discussion about {query}",
                            url="https://reddit.com/r/netsec",
                            timestamp=datetime.now(),
                            quality_score=0.6,
                            tags=[query, "reddit", "netsec"],
                        ))
        except Exception as e:
            print(f"[ForumSource] Reddit error: {e}", file=sys.stderr)
        
        # Search HackerNews (most reliable)
        try:
            url = "https://hn.algolia.com/api/v1/search?query={}".format(quote(query))
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    hits = data.get("hits", [])[:15]
                    for hit in hits:
                        title = hit.get("title", "")
                        url = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}")
                        items.append(DarkWebItem(
                            item_id=hashlib.md5(hit.get("objectID", "").encode()).hexdigest()[:12],
                            source_type=SourceType.BLOG,
                            category=self._detect_category(query),
                            title=title[:200],
                            content_preview=f"HackerNews discussion: {query}",
                            url=url,
                            timestamp=datetime.now(),
                            quality_score=0.7,
                            tags=[query, "hackernews", "security"],
                        ))
        except Exception as e:
            print(f"[ForumSource] HN error: {e}", file=sys.stderr)
        
        self.items_found += len(items)
        return items
    
    def _parse_reddit(self, html: str, query: str) -> List[DarkWebItem]:
        items = []
        # Parse Reddit search results (different format)
        posts = re.findall(r'<a href="/r/netsec/comments/([^"]+)"[^>]*>([^<]+)</a>', html)
        for post_id, title in posts[:10]:
            items.append(DarkWebItem(
                item_id=hashlib.md5(post_id.encode()).hexdigest()[:12],
                source_type=SourceType.FORUM,
                category=self._detect_category(query),
                title=title.strip()[:200],
                content_preview=f"Discussion about {query} on Reddit r/netsec",
                url=f"https://reddit.com/r/netsec/comments/{post_id}",
                timestamp=datetime.now(),
                quality_score=0.6,
                tags=[query, "reddit", "forum"],
            ))
        
        # Also try to find titles in JSON data
        json_data = re.findall(r'"title":"([^"]+)"', html)
        for title in json_data[:5]:
            items.append(DarkWebItem(
                item_id=hashlib.md5(title.encode()).hexdigest()[:12],
                source_type=SourceType.FORUM,
                category=self._detect_category(query),
                title=title[:200],
                content_preview=f"Reddit discussion about {query}",
                url="https://reddit.com/r/netsec",
                timestamp=datetime.now(),
                quality_score=0.5,
                tags=[query, "reddit"],
            ))
        return items[:10]
    
    def _parse_hn(self, data: Dict, query: str) -> List[DarkWebItem]:
        items = []
        hits = data.get("hits", [])[:10]
        for hit in hits:
            items.append(DarkWebItem(
                item_id=hashlib.md5(hit.get("objectID", "").encode()).hexdigest()[:12],
                source_type=SourceType.BLOG,
                category=self._detect_category(query),
                title=hit.get("title", "")[:200],
                content_preview=hit.get("story_text", "")[:300] if hit.get("story_text") else "",
                url=hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"),
                timestamp=datetime.now(),
                quality_score=0.6,
                tags=[query, "hackernews"],
            ))
        return items
    
    def _detect_category(self, query: str) -> ThreatCategory:
        q = query.lower()
        if any(k in q for k in ["exploit", "cve", "rce", "0day"]):
            return ThreatCategory.RCE
        if any(k in q for k in ["ransom", "lockbit", "conti"]):
            return ThreatCategory.RANSOMWARE
        if any(k in q for k in ["phishing", "credential"]):
            return ThreatCategory.CREDENTIALS
        return ThreatCategory.DATA_BREACH


class ExploitDBSource(DarkWebSource):
    """Search Exploit-DB and public exploit databases."""
    
    EXPLOIT_DB_API = "https://www.exploit-db.com/search?keyword={query}"
    
    def __init__(self):
        super().__init__("exploit_search")
    
    async def crawl(self, query: str, session: aiohttp.ClientSession,
                   proxy_config: Dict) -> List[DarkWebItem]:
        items = []
        try:
            url = self.EXPLOIT_DB_API.format(query=quote(query))
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # Look for exploit titles in various formats
                    # Format 1: Direct links
                    exploits = re.findall(r'href="(/exploits/\d+)"[^>]*>([^<]+)</a>', html)
                    for path, title in exploits[:10]:
                        items.append(DarkWebItem(
                            item_id=hashlib.md5(path.encode()).hexdigest()[:12],
                            source_type=SourceType.EXPLOIT,
                            category=self._detect_exploit_category(title),
                            title=title.strip()[:200],
                            content_preview=f"Exploit database entry for {query}",
                            url=f"https://www.exploit-db.com{path}",
                            timestamp=datetime.now(),
                            quality_score=0.8,
                            tags=[query, "exploit-db"],
                        ))
                    
                    # Format 2: Table rows with dates
                    if not items:
                        rows = re.findall(r'<td class="date">([^<]+)</td>.*?<td><a href="(/exploits/\d+)">([^<]+)</a>', html, re.DOTALL)
                        for date, path, title in rows[:10]:
                            items.append(DarkWebItem(
                                item_id=hashlib.md5(path.encode()).hexdigest()[:12],
                                source_type=SourceType.EXPLOIT,
                                category=self._detect_exploit_category(title),
                                title=title.strip()[:200],
                                content_preview=f"Exploit from {date.strip()}",
                                url=f"https://www.exploit-db.com{path}",
                                timestamp=datetime.now(),
                                quality_score=0.7,
                                tags=[query, "exploit-db"],
                            ))
                    
                    # Format 3: Any link containing /exploits/
                    if not items:
                        all_links = re.findall(r'href="(/exploits/\d+)"', html)
                        for path in list(set(all_links))[:10]:
                            items.append(DarkWebItem(
                                item_id=hashlib.md5(path.encode()).hexdigest()[:12],
                                source_type=SourceType.EXPLOIT,
                                category=self._detect_exploit_category(query),
                                title=f"{query} exploit",
                                content_preview=f"Exploit entry: {path}",
                                url=f"https://www.exploit-db.com{path}",
                                timestamp=datetime.now(),
                                quality_score=0.6,
                                tags=[query, "exploit-db"],
                            ))
        except Exception as e:
            print(f"[ExploitDBSource] Error: {e}", file=sys.stderr)
        
        self.items_found += len(items)
        return items
    
    def _detect_exploit_category(self, title: str) -> ThreatCategory:
        t = title.lower()
        if "rce" in t or "remote code" in t:
            return ThreatCategory.RCE
        if "sqli" in t or "sql injection" in t:
            return ThreatCategory.SQLi
        if "xss" in t or "cross-site" in t:
            return ThreatCategory.XSS
        if "lfi" in t or "local file" in t:
            return ThreatCategory.LFI
        if "ssrf" in t:
            return ThreatCategory.SSRF
        return ThreatCategory.EXPLOIT_KIT


# =========================================================================
# Main Engine
# =========================================================================

class DarkWebIntelligence:
    """
    DarkWeb Intelligence Engine — Modo 4070
    Coleta e analisa informações da darkweb para threat intelligence.
    """
    
    def __init__(self, max_concurrent: int = 5, timeout: int = 30, use_tor: bool = False):
        self.sources: List[DarkWebSource] = [
            PasteSource(),
            ForumSource(),
            ExploitDBSource(),
        ]
        self.knowledge_db = ThreatKnowledgeDB()
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.use_tor = use_tor
        self.collected_items: List[DarkWebItem] = []
        self.search_history: List[Dict[str, Any]] = []
        self.proxy_config: Dict = TorProxyManager.get_proxy_config()
        
    async def search(self, query: str, source_types: Optional[List[SourceType]] = None) -> List[DarkWebItem]:
        """Search across all enabled sources."""
        items = []
        source_filter = set(source_types) if source_types else {s for s in SourceType}
        
        session, proxy_config = await TorProxyManager.get_session(self.proxy_config)
        
        try:
            tasks = []
            for source in self.sources:
                if source.enabled:
                    tasks.append(self._crawl_source(source, query, session, proxy_config))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    items.extend(result)
        finally:
            await session.close()
        
        # Deduplicate
        seen = set()
        unique_items = []
        for item in items:
            if item.item_id not in seen:
                seen.add(item.item_id)
                unique_items.append(item)
        
        self.collected_items.extend(unique_items)
        return unique_items
    
    async def _crawl_source(self, source: DarkWebSource, query: str,
                           session: aiohttp.ClientSession,
                           proxy_config: Dict) -> List[DarkWebItem]:
        """Crawl a single source."""
        try:
            items = await source.crawl(query, session, proxy_config)
            source.last_crawl = datetime.now()
            return items
        except Exception as e:
            print(f"[DarkWebIntel] Error crawling {source.name}: {e}", file=sys.stderr)
            return []
    
    async def analyze_threat(self, indicator: str) -> Dict[str, Any]:
        """Analyze a threat indicator against knowledge base."""
        result = {
            "indicator": indicator,
            "matches": [],
            "risk_score": 0.0,
            "recommendations": [],
            "sources": [],
        }
        
        # Check against known TTPs
        ttps = self.knowledge_db.search_ttps("", indicator)
        if ttps:
            result["matches"].extend([{
                "type": "ttp",
                "match": t,
                "confidence": 0.8,
            } for t in ttps])
            result["risk_score"] += 0.3
        
        # Check against exploit patterns
        exploit = self.knowledge_db.get_exploit_info(indicator)
        if exploit:
            result["matches"].append({
                "type": "exploit",
                "cve": exploit["cve"],
                "severity": exploit["severity"],
                "description": exploit["description"],
                "confidence": 0.9,
            })
            result["risk_score"] += 0.5
        
        # Check against malware families
        malware = self.knowledge_db.get_malware_info(indicator)
        if malware:
            result["matches"].append({
                "type": "malware",
                "family": indicator,
                "malware_type": malware["type"],
                "status": malware["status"],
                "confidence": 0.85,
            })
            result["risk_score"] += 0.4
        
        # Check against tools
        tool = self.knowledge_db.get_tool_info(indicator)
        if tool:
            result["matches"].append({
                "type": "tool",
                "name": indicator,
                "info": tool,
                "confidence": 0.7,
            })
            result["risk_score"] += 0.2
        
        # Search external sources
        search_items = await self.search(indicator)
        if search_items:
            result["sources"] = [item.to_dict() for item in search_items[:5]]
            result["risk_score"] += 0.1 * len(search_items)
        
        # Generate recommendations
        if result["risk_score"] > 0.5:
            result["recommendations"] = [
                "High confidence match found",
                "Update threat signatures",
                "Review defensive controls",
                "Check for Indicators of Compromise",
                "Monitor for related activity",
            ]
        
        result["risk_level"] = (
            "critical" if result["risk_score"] > 0.8 else
            "high" if result["risk_score"] > 0.6 else
            "medium" if result["risk_score"] > 0.4 else
            "low"
        )
        
        return result
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of known threat knowledge."""
        return {
            "ttp_categories": len(self.knowledge_db.known_ttps),
            "known_exploits": len(self.knowledge_db.exploit_patterns),
            "malware_families": len(self.knowledge_db.malware_families),
            "tools_database": len(self.knowledge_db.tool_database),
            "categories": self.knowledge_db.get_all_categories(),
        }
    
    def export_results(self, filename: str, format: str = "json"):
        """Export collected items to file."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_items": len(self.collected_items),
            "tor_enabled": self.proxy_config.get("enabled", False),
            "items": [item.to_dict() for item in self.collected_items],
        }
        
        if format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif format == "txt":
            with open(filename, 'w', encoding='utf-8') as f:
                for item in self.collected_items:
                    f.write(f"[{item.category.value.upper()}] {item.title}\n")
                    f.write(f"  Preview: {item.content_preview[:200]}\n")
                    f.write(f"  Quality: {item.quality_score}\n")
                    f.write(f"  URL: {item.url}\n\n")
        
        print(f"Exported {len(self.collected_items)} items to {filename}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get intelligence collection statistics."""
        return {
            "total_items_collected": len(self.collected_items),
            "sources_enabled": sum(1 for s in self.sources if s.enabled),
            "tor_enabled": self.proxy_config.get("enabled", False),
            "sources_stats": [
                {
                    "name": s.name,
                    "enabled": s.enabled,
                    "items_found": s.items_found,
                    "last_crawl": s.last_crawl.isoformat() if s.last_crawl else None,
                }
                for s in self.sources
            ],
            "knowledge_base": self.get_knowledge_summary(),
        }


# =========================================================================
# Knowledge Database
# =========================================================================

class ThreatKnowledgeDB:
    """Database of known threats, techniques, and patterns."""
    
    def __init__(self):
        self.known_ttps: Dict[str, List[str]] = {}
        self.exploit_patterns: Dict[str, Dict[str, Any]] = {}
        self.malware_families: Dict[str, Dict[str, Any]] = {}
        self.tool_database: Dict[str, Dict[str, Any]] = {}
        self._load_baseline_knowledge()
    
    def _load_baseline_knowledge(self):
        """Load baseline threat intelligence."""
        self.known_ttps = {
            "initial_access": [
                "phishing", "supply_chain", "zero_day", "valid_accounts",
                "drive-by", "trusted_relationship"
            ],
            "execution": [
                "powershell", "cmd", "shell", "scripting",
                "scheduled_task", "launcher", "dll_search_order_hijack"
            ],
            "persistence": [
                "registry_run_keys", "startup_folder", "service",
                "scheduled_task", "ntfs_alternate_data_stream"
            ],
            "privilege_escalation": [
                "unquoted_service_path", "always_install_elevated",
                "token_manipulation", "abuse_elevation_control"
            ],
            "defense_evasion": [
                "obfuscated_files", "masquerading", "disable_security",
                "process_injection", "fileless", "nativelibs"
            ],
            "credential_access": [
                "brute_force", "password_spraying", "credential_dumping",
                "oscredential_harvesting", "input_capture"
            ],
            "discovery": [
                "system_info", "network_discovery", "account_discovery",
                "permission_discovery", "file_directory_discovery"
            ],
            "lateral_movement": [
                "remote_services", "rdp", "ssh", "vnc",
                "smb_admin", "internal_spearphishing"
            ],
            "collection": [
                "screen_capture", "audio_capture", "keylogging",
                "network_cap", "data_from_local_system"
            ],
            "command_control": [
                "standard_protocol", "application_layer_protocol",
                "encrypted_channel", "multiband_command",
                "domain_fronting", "dns_tunneling"
            ],
            "exfiltration": [
                "exfil_over_network", "exfil_over_backup_service",
                "compressed_archived", "encrypted_channel"
            ],
        }
        
        self.exploit_patterns = {
            "log4j": {
                "cve": "CVE-2021-44228",
                "severity": "critical",
                "pattern": r"\$\{jndi:(?:ldap|rmi|dns|iiop)://.*\}",
                "description": "Apache Log4j Remote Code Execution",
                "impact": "Full system compromise",
            },
            "proxyshell": {
                "cve": "CVE-2021-34473",
                "severity": "high",
                "pattern": r"/ecp/.*(?:proxy|shell)",
                "description": "Microsoft Exchange ProxyShell",
                "impact": "Exchange server compromise",
            },
            "zerologon": {
                "cve": "CVE-2020-1472",
                "severity": "critical",
                "pattern": r"zerologon|ncacn_np.*\\\\",
                "description": "Netlogon elevation of privilege",
                "impact": "Domain controller compromise",
            },
            "spectre": {
                "cve": "CVE-2017-5753",
                "severity": "high",
                "pattern": r"spectre",
                "description": "CPU speculative execution side channel",
                "impact": "Memory information disclosure",
            },
            "heartbleed": {
                "cve": "CVE-2014-0160",
                "severity": "critical",
                "pattern": r"heartbleed",
                "description": "OpenSSL TLS heartbeat buffer overflow",
                "impact": "Private key and memory leak",
            },
        }
        
        self.malware_families = {
            "lockbit": {"type": "ransomware", "status": "active"},
            "conti": {"type": "ransomware", "status": "dismantled_2023"},
            "alpharansomware": {"type": "ransomware", "status": "active"},
            "rhaidata": {"type": "ransomware", "status": "active"},
            "emotet": {"type": "banker", "status": "dismantled_2021"},
            "qakbot": {"type": "banker", "status": "dismantled_2023"},
            "lumma": {"type": "stealer", "status": "active"},
            "idborer": {"type": "stealer", "status": "active"},
            "redline": {"type": "stealer", "status": "active"},
            "razor": {"type": "loader", "status": "active"},
            "astra": {"type": "c2", "status": "active"},
            "obsidian": {"type": "ransomware", "status": "active"},
        }
        
        self.tool_database = {
            "cobalt_strike": {"type": "c2_framework", "vendor": "Proofpoint"},
            "covenant": {"type": "c2_framework", "vendor": "PowerShell Empire"},
            "sliver": {"type": "c2_framework", "vendor": "BishopFox"},
            "empire": {"type": "c2_framework", "vendor": "Chris Truncer"},
            "meterpreter": {"type": "payload", "vendor": "Rapid7"},
            "mimikatz": {"type": "credential_tool", "vendor": "Gentil Kiwi"},
        }
    
    def search_ttps(self, category: str, keyword: str = "") -> List[str]:
        results = []
        cat_lower = category.lower()
        kw_lower = keyword.lower() if keyword else ""
        for ttp_cat, techniques in self.known_ttps.items():
            if cat_lower in ttp_cat or ttp_cat in cat_lower:
                for t in techniques:
                    if not kw_lower or kw_lower in t:
                        results.append(f"{ttp_cat}:{t}")
        return results[:20]
    
    def get_exploit_info(self, name: str) -> Optional[Dict[str, Any]]:
        name_lower = name.lower()
        for n, info in self.exploit_patterns.items():
            if name_lower in n or n in name_lower:
                return info
            # Also check CVE pattern
            if "cve" in name_lower and info.get("cve", "").lower() in name_lower:
                return info
        return None
    
    def get_malware_info(self, family: str) -> Optional[Dict[str, Any]]:
        family_lower = family.lower()
        for n, info in self.malware_families.items():
            if family_lower in n or n in family_lower:
                return info
        return None
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        tool_lower = tool_name.lower()
        for n, info in self.tool_database.items():
            if tool_lower in n or n in tool_lower:
                return info
        return None
    
    def get_all_categories(self) -> List[str]:
        categories = set()
        for ttp_cat in self.known_ttps.keys():
            categories.add(ttp_cat.replace("_", " "))
        for family in self.malware_families.keys():
            categories.add(f"{self.malware_families[family]['type']}")
        return sorted(categories)


# =========================================================================
# CLI Interface
# =========================================================================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DarkWeb Intel — Modo 4070',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python darkweb_intel.py search "ransomware"
  python darkweb_intel.py search "exploit" --source paste
  python darkweb_intel.py analyze "CVE-2021-44228"
  python darkweb_intel.py analyze "lockbit"
  python darkweb_intel.py knowledge
  python darkweb_intel.py stats
        """
    )
    
    parser.add_argument('action', choices=['search', 'analyze', 'knowledge', 'stats'],
                       help='Action to perform')
    parser.add_argument('query', nargs='?', help='Search query or indicator')
    parser.add_argument('--source', choices=['all', 'paste', 'forum', 'exploit'],
                       default='all', help='Source type to search')
    parser.add_argument('--output', '-o', help='Output file')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout')
    parser.add_argument('--tor', action='store_true', help='Use Tor proxy')
    
    args = parser.parse_args()
    
    intel = DarkWebIntelligence(timeout=args.timeout, use_tor=args.tor)
    
    print(f"Tor enabled: {intel.proxy_config.get('enabled', False)}")
    print()
    
    if args.action == 'search':
        if not args.query:
            print("Error: query required for search", file=sys.stderr)
            sys.exit(1)
        
        print(f"Searching for: {args.query}")
        items = await intel.search(args.query)
        
        if args.json:
            print(json.dumps([i.to_dict() for i in items], indent=2))
        else:
            print(f"\nFound {len(items)} items:\n")
            for item in items[:20]:
                print(f"[{item.category.value.upper()}] {item.title}")
                print(f"  Preview: {item.content_preview[:150]}...")
                print(f"  Quality: {item.quality_score:.2f}")
                print(f"  Source: {item.url}")
                print()
        
        if args.output:
            intel.export_results(args.output)
    
    elif args.action == 'analyze':
        if not args.query:
            print("Error: indicator required for analyze", file=sys.stderr)
            sys.exit(1)
        
        print(f"Analyzing: {args.query}")
        result = await intel.analyze_threat(args.query)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nRisk Level: {result['risk_level'].upper()}")
            print(f"Risk Score: {result['risk_score']:.2f}")
            print(f"\nMatches ({len(result['matches'])}):")
            for match in result['matches']:
                print(f"  [{match['type']}] {json.dumps(match, indent=4)[:100]}")
            
            if result['sources']:
                print(f"\nExternal Sources ({len(result['sources'])}):")
                for src in result['sources'][:5]:
                    print(f"  - {src['title'][:60]}...")
            
            if result['recommendations']:
                print(f"\nRecommendations:")
                for rec in result['recommendations']:
                    print(f"  - {rec}")
    
    elif args.action == 'knowledge':
        summary = intel.get_knowledge_summary()
        print("=== Threat Knowledge Database ===\n")
        print(f"TTP Categories: {summary['ttp_categories']}")
        print(f"Known Exploits: {summary['known_exploits']}")
        print(f"Malware Families: {summary['malware_families']}")
        print(f"Tool Database: {summary['tools_database']}")
        print(f"\nCategories: {', '.join(summary['categories'][:15])}")
    
    elif args.action == 'stats':
        stats = intel.get_stats()
        print("=== DarkWeb Intelligence Stats ===\n")
        print(f"Total Items Collected: {stats['total_items_collected']}")
        print(f"Sources Enabled: {stats['sources_enabled']}")
        print(f"Tor Status: {'ENABLED' if stats['tor_enabled'] else 'DISABLED'}")
        print("\nSource Details:")
        for s in stats['sources_stats']:
            status = "ONLINE" if s['enabled'] else "OFFLINE"
            print(f"  {s['name']}: {status} ({s['items_found']} items)")
        
        print("\nKnowledge Base:")
        kb = stats['knowledge_base']
        print(f"  TTP Categories: {kb['ttp_categories']}")
        print(f"  Known Exploits: {kb['known_exploits']}")
        print(f"  Malware Families: {kb['malware_families']}")


if __name__ == '__main__':
    asyncio.run(main())
