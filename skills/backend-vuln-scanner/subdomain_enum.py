#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subdomain Enumeration — Descobre subdominios ativos
Usa DNS brute force, cert transparency e recon passivo
"""

import sys
import json
import socket
import ssl
import urllib.request
import urllib.error
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime


class SubdomainEnumerator:
    """Enumeracao de subdominios"""

    # Wordlist padrao expandida
    DEFAULT_SUBDOMAINS = [
        # Comuns
        'www', 'mail', 'ftp', 'smtp', 'pop', 'imap', 'vpn', 'ns1', 'ns2',
        'ns3', 'dns', 'dns1', 'dns2', 'mx', 'webmail', 'cpanel', 'whm',
        'admin', 'administrator', 'dashboard', 'panel', 'cp',
        'api', 'apis', 'v1', 'v2', 'v3', 'rest', 'restapi',
        'app', 'apps', 'webapp', 'mobile', 'm', 'mobileapp',
        'blog', 'blogs', 'news', 'cms', 'content',
        'shop', 'store', 'ecommerce', 'ecom', 'marketplace',
        'cdn', 'static', 'assets', 'media', 'images', 'img',
        'dev', 'dev1', 'dev2', 'staging', 'stage', 'test', 'sandbox',
        'demo', 'docs', 'documentation', 'wiki', 'help', 'support',
        'status', 'health', 'ping', 'monitor', 'metrics', 'grafana',
        'login', 'signin', 'signup', 'auth', 'oauth', 'sso',
        'secure', 'securemail', 'security',
        'payment', 'payments', 'billing', 'checkout', 'cart',
        'account', 'accounts', 'user', 'users', 'profile',
        'search', 'analytics', 'tracking', 'tracking2',
        'upload', 'uploads', 'files', 'storage', 'bucket',
        'backup', 'backups', 'archive', 'archives',
        'chat', 'irc', 'slack', 'teams', 'meet', 'video',
        'calendar', 'crm', 'erp', 'hr', 'hrm',
        'git', 'github', 'gitlab', 'jenkins', 'ci', 'cd',
        'config', 'configuration',
        'email', 'newsletter', 'notifications',
        'feed', 'rss', 'atom',
        'graph', 'graphql', 'graphiql', 'playground',
        'internal', 'intranet', 'corp', 'company',
        'jobs', 'careers', 'recruiting',
        'kb', 'knowledgebase',
        'legal', 'terms', 'privacy', 'compliance',
        'live', 'livechat', 'sales',
        'marketing', 'marketing2', 'campaign',
        'membership', 'members',
        'old', 'new', 'beta', 'alpha', 'rc',
        'partners', 'partner',
        'pay', 'paypal', 'stripe',
        'phpmyadmin', 'pma',
        'portal',
        'pro', 'prodx',
        'qa', 'quality',
        'radar', 'report', 'reports',
        'sdk', 'sdk2',
        'servicedesk',
        'shop', 'shops',
        'social', 'socialclub',
        'sports',
        'stats', 'statistics',
        'team', 'teams',
        'ticket', 'tickets',
        'training',
        'uat', 'uat2',
        'up', 'upload',
        'us',
        'voice', 'voip',
        'web', 'web1', 'webmail',
        'welcome',
        'wiki',
        'ww', 'ww2',
        # Cert transparency / passivas
        'pastebin', 'crt', 'ct',
        'git', 'hackerone', 'bugcrowd',
        # Infra
        'kong', 'nginx', 'traefik', 'envoy', 'istio',
        'k8s', 'kubernetes', 'kube',
        # Cloud
        'aws', 'azure', 'gcp', 'cloudfront',
        # Monitoring
        'prometheus', 'alertmanager', ' PagerDuty',
        # DB
        'db', 'database', 'mongodb', 'redis', 'elastic',
    ]

    # Fontes de recon passivo (APIs publicas)
    PASSIVE_SOURCES = {
        'crtsh': 'https://crt.sh/?q=%25.{domain}&output=json',
        'securitytrails': None,  # Requires API key
        'shodan': None,  # Requires API key
    }

    def __init__(self, target: str, wordlist: List[str] = None, timeout: int = 3):
        self.target = target
        self.domain = target if '.' in target else f"{target}.com"
        self.wordlist = wordlist or self.DEFAULT_SUBDOMAINS
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.found_subdomains: Set[str] = set()
        self.results: List[Dict] = []

    def _resolve(self, subdomain: str) -> Optional[str]:
        """Resolve subdomain to IP"""
        try:
            ip = socket.gethostbyname(subdomain)
            return ip
        except socket.gaierror:
            return None

    def _http_check(self, subdomain: str) -> Tuple[int, str]:
        """Check if subdomain responds via HTTP"""
        try:
            url = f"http://{subdomain}"
            req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')[:500]
                return resp.status, body
        except urllib.error.HTTPError as e:
            return e.code, ''
        except Exception:
            return 0, ''

    def brute_force(self) -> List[Dict]:
        """DNS brute force enumeration"""
        print(f"\n  [ENUM] Brute forcing {len(self.wordlist)} subdomains...")

        found = []
        total = len(self.wordlist)

        for i, sub in enumerate(self.wordlist):
            full = f"{sub}.{self.domain}"
            ip = self._resolve(full)

            if ip:
                http_status, http_body = self._http_check(full)
                entry = {
                    'subdomain': full,
                    'ip': ip,
                    'http_status': http_status,
                    'alive': True,
                }
                found.append(entry)
                self.found_subdomains.add(full)

                icon = "[OK]" if http_status == 200 else "[BLOCKED]" if http_status == 403 else "[WEB]"
                print(f"    {icon} {full} -> {ip} (HTTP {http_status})")
            else:
                if (i + 1) % 50 == 0:
                    print(f"    Progress: {i+1}/{total} ({len(found)} found)")

            time.sleep(0.05)  # Rate limiting

        print(f"  [ENUM] Found {len(found)} subdomains")
        return found

    def passive_recon_crtsh(self) -> List[Dict]:
        """Passive recon via Certificate Transparency (crt.sh)"""
        print(f"\n  [ENUM] Querying crt.sh for {self.domain}...")
        found = []

        try:
            url = self.PASSIVE_SOURCES['crtsh'].format(domain=self.domain)
            req = urllib.request.Request(url, headers={
                'User-Agent': self.user_agent,
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=15, context=self.ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for entry in data:
                    name = entry.get('name_value', '')
                    for sub in name.split('\n'):
                        sub = sub.strip()
                        if sub.endswith(f'.{self.domain}') and sub != self.domain:
                            if sub not in self.found_subdomains:
                                self.found_subdomains.add(sub)
                                found.append({'subdomain': sub, 'source': 'crt.sh'})
                                print(f"    - {sub} (from crt.sh)")
        except Exception as e:
            print(f"    [WARN] crt.sh query failed: {e}")

        return found

    def run_full_enum(self) -> Dict:
        """Executa enum eracao completa"""
        print("\n" + "=" * 70)
        print(f"  SUBDOMAIN ENUMERATION — {self.domain}")
        print("=" * 70)

        all_results = []

        # Passive recon first (faster)
        passive = self.passive_recon_crtsh()
        all_results.extend(passive)

        # Brute force
        brute = self.brute_force()
        all_results.extend(brute)

        # Deduplicate
        seen = set()
        unique = []
        for r in all_results:
            key = r['subdomain']
            if key not in seen:
                seen.add(key)
                unique.append(r)

        result = {
            'target': self.domain,
            'timestamp': datetime.now().isoformat(),
            'total_found': len(unique),
            'subdomains': unique,
            'summary': {
                'with_ip': len([s for s in unique if s.get('ip')]),
                'alive_http': len([s for s in unique if s.get('http_status') in [200, 301, 302]]),
                'blocked_http': len([s for s in unique if s.get('http_status') == 403]),
            },
        }

        print(f"\n  [RESULT] Total: {result['total_found']} subdomains")
        print(f"  [RESULT] With IP: {result['summary']['with_ip']}")
        print(f"  [RESULT] Alive: {result['summary']['alive_http']}")

        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Subdomain Enumerator')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--wordlist', '-w', help='Custom wordlist file')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    enum = SubdomainEnumerator(args.target)

    if args.wordlist:
        with open(args.wordlist, 'r', encoding='utf-8') as f:
            enum.wordlist = [line.strip() for line in f if line.strip()]

    result = enum.run_full_enum()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
