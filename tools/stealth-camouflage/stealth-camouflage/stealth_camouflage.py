#!/usr/bin/env python3
"""
Stealth Camouflage System v1.0
Camufla todo o processo de penetracao como trafego legitimo.
User-Agent rotation, timing random, header spoofing, SSL fingerprinting.
"""

import sys
import time
import random
import asyncio
import argparse
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import json
import os

# ── Stealth Config ────────────────────────────────────────────────────────

USER_AGENTS = [
    # Browsers modernos
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

ACCEPT_HEADERS = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "application/json, text/plain, */*",
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
]

LANGUAGES = [
    "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
]

SEC_CH_UA = [
    '"Chromium";v="120", "Google Chrome";v="120", "Not_A Brand";v="99"',
    '"Not/A)Brand";v="99", "Chromium";v="120", "Google Chrome";v="120"',
]

SEC_FETCH = [
    "sec-fetch-dest: document",
    "sec-fetch-mode: navigate",
    "sec-fetch-site: none",
    "sec-fetch-user: ?1",
]

# ── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class StealthProfile:
    """Perfil de camuflagem para uma sessao."""
    user_agent: str = ""
    accept: str = ""
    accept_language: str = ""
    sec_ch_ua: str = ""
    sec_fetch_dest: str = ""
    sec_fetch_mode: str = ""
    sec_fetch_site: str = ""
    sec_fetch_user: str = ""
    cache_control: str = "no-cache"
    priority: str = "u=0, i"
    referer: str = ""
    origin: str = ""
    
    # Timing config
    min_delay: float = 0.8
    max_delay: float = 2.5
    jitter: float = 0.3
    
    # Session identity
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_headers(self) -> Dict[str, str]:
        """Converte perfil para headers HTTP."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": self.accept,
            "Accept-Language": self.accept_language,
            "Sec-Ch-Ua": self.sec_ch_ua,
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": self.sec_fetch_dest,
            "Sec-Fetch-Mode": self.sec_fetch_mode,
            "Sec-Fetch-Site": self.sec_fetch_site,
            "Sec-Fetch-User": self.sec_fetch_user,
            "Cache-Control": self.cache_control,
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
            "TE": "trailers",
        }
        if self.referer:
            headers["Referer"] = self.referer
        if self.origin:
            headers["Origin"] = self.origin
        return headers
    
    def random_delay(self) -> float:
        """Delay random com jitter realista."""
        base = random.uniform(self.min_delay, self.max_delay)
        jitter = random.uniform(-self.jitter, self.jitter)
        return max(0.1, base + jitter)
    
    @classmethod
    def generate(cls, realistic: bool = True) -> 'StealthProfile':
        """Gera perfil aleatorio realista."""
        profile = cls(
            user_agent=random.choice(USER_AGENTS),
            accept=random.choice(ACCEPT_HEADERS),
            accept_language=random.choice(LANGUAGES),
            sec_ch_ua=random.choice(SEC_CH_UA),
        )
        
        if realistic:
            # Simula comportamento de browser real
            profile.session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
            profile.min_delay = random.uniform(0.5, 1.2)
            profile.max_delay = random.uniform(1.5, 3.0)
        
        return profile


# ── Stealth Manager ───────────────────────────────────────────────────────

class StealthManager:
    """Gerencia camuflagem para operacoes de penetracao."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.profiles: Dict[str, StealthProfile] = {}
        self.request_log: List[Dict[str, Any]] = []
        self.config_path = config_path or os.path.expanduser("~/.stealth_config.json")
        self._load_config()
    
    def _load_config(self):
        """Carrega configuracao persistente."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.profiles = {
                        k: StealthProfile(**v) for k, v in data.get('profiles', {}).items()
                    }
            except Exception:
                pass
    
    def _save_config(self):
        """Salva configuracao persistente."""
        data = {
            'profiles': {k: {
                'user_agent': v.user_agent,
                'accept': v.accept,
                'accept_language': v.accept_language,
                'session_id': v.session_id,
                'min_delay': v.min_delay,
                'max_delay': v.max_delay,
            } for k, v in self.profiles.items()}
        }
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_profile(self, name: Optional[str] = None, realistic: bool = True) -> StealthProfile:
        """Cria novo perfil de camuflagem."""
        profile = StealthProfile.generate(realistic)
        profile_id = name or profile.session_id
        self.profiles[profile_id] = profile
        self._save_config()
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[StealthProfile]:
        """Recupera perfil por ID."""
        return self.profiles.get(profile_id)
    
    def get_random_profile(self) -> StealthProfile:
        """Recupera perfil aleatorio."""
        if not self.profiles:
            return self.create_profile()
        return random.choice(list(self.profiles.values()))
    
    def apply_to_headers(self, headers: Dict[str, str], profile: Optional[StealthProfile] = None) -> Dict[str, str]:
        """Aplica camuflagem aos headers."""
        if profile is None:
            profile = self.get_random_profile()
        
        stealth_headers = profile.to_headers()
        stealth_headers.update(headers)
        return stealth_headers
    
    async def sleep_realistic(self, profile: Optional[StealthProfile] = None):
        """Sleep com delay realista."""
        if profile is None:
            profile = self.get_random_profile()
        delay = profile.random_delay()
        await asyncio.sleep(delay)
    
    def log_request(self, profile_id: str, method: str, url: str, status: int, delay: float):
        """Log request camuflado."""
        self.request_log.append({
            'timestamp': datetime.now().isoformat(),
            'profile': profile_id,
            'method': method,
            'url': url,
            'status': status,
            'delay': delay,
            'legitimate': True  # Marca como trafego legitimo
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatisticas de camuflagem."""
        return {
            'total_profiles': len(self.profiles),
            'total_requests': len(self.request_log),
            'avg_delay': sum(r['delay'] for r in self.request_log[-100:]) / min(100, len(self.request_log)) if self.request_log else 0,
            'last_profile': list(self.profiles.keys())[-1] if self.profiles else None,
        }


# ── CLI Interface ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Stealth Camouflage System — Camufla trafego como legitimo'
    )
    subparsers = parser.add_subparsers(dest='command', help='Comando')
    
    # Create profile
    create_parser = subparsers.add_parser('create', help='Criar novo perfil')
    create_parser.add_argument('--name', help='Nome do perfil')
    create_parser.add_argument('--realistic', action='store_true', default=True, help='Comportamento realista')
    
    # Show profiles
    subparsers.add_parser('list', help='Listar perfis')
    
    # Show stats
    subparsers.add_parser('stats', help='Estatisticas')
    
    # Test headers
    test_parser = subparsers.add_parser('test', help='Testar headers')
    test_parser.add_argument('--url', help='URL para testar')
    
    args = parser.parse_args()
    
    manager = StealthManager()
    
    if args.command == 'create':
        profile = manager.create_profile(args.name, args.realistic)
        print(f"[+] Perfil criado: {profile.session_id}")
        print(f"    User-Agent: {profile.user_agent[:60]}...")
        print(f"    Delay: {profile.min_delay:.2f}-{profile.max_delay:.2f}s")
    
    elif args.command == 'list':
        if not manager.profiles:
            print("[] Nenhum perfil criado. Use: stealth create")
        else:
            print(f"[+] {len(manager.profiles)} perfis ativos:")
            for pid, profile in manager.profiles.items():
                print(f"    - {pid}: {profile.user_agent[:40]}...")
    
    elif args.command == 'stats':
        stats = manager.get_stats()
        print("[+] Estatisticas de camuflagem:")
        print(f"    Perfis: {stats['total_profiles']}")
        print(f"    Requests: {stats['total_requests']}")
        print(f"    Avg delay: {stats['avg_delay']:.2f}s")
    
    elif args.command == 'test':
        profile = manager.get_random_profile()
        print("[+] Headers camuflados:")
        for k, v in profile.to_headers().items():
            print(f"    {k}: {v[:50]}...")


if __name__ == '__main__':
    main()
