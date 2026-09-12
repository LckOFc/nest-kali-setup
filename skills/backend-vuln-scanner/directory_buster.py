#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Directory Buster — Fuerca bruta de diretorios e arquivos
Testa paths comuns para descobrir conteudo exposto
"""

import sys
import json
import ssl
import urllib.request
import urllib.error
import time
from typing import Dict, List, Optional
from datetime import datetime


class DirectoryBuster:
    """Scanner de diretórios e arquivos sensíveis"""

    # Wordlist padrao expandido
    DEFAULT_WORDLIST = [
        # Directories
        '/admin', '/administrator', '/admin1', '/admin2', '/admin3',
        '/api', '/api/v1', '/api/v2', '/api/v3', '/api/docs',
        '/app', '/apps', '/application',
        '/auth', '/authentication', '/authorize',
        '/backup', '/backups', '/bak', '/old',
        '/bin', '/bins', '/binary', '/binaries',
        '/blog', '/blogs', '/blogs',
        '/cgi', '/cgi-bin', '/cgi-bin/',
        '/cloud', '/cloudinary',
        '/cms', '/content', '/control',
        '/dashboard', '/dash',
        '/data', '/database', '/db', '/dump',
        '/dev', '/development', '/demo',
        '/doc', '/docs', '/documentation', '/documents',
        '/download', '/downloads',
        '/email', '/emails',
        '/files', '/file', '/files/', '/file/',
        '/forum', '/forums',
        '/ftp', '/ftp-', '/ftps',
        '/gis', '/geo',
        '/home', '/homepage',
        '/images', '/img', '/imgs', '/image',
        '/include', '/includes', '/inc',
        '/index', '/index.php', '/index.html',
        '/info', '/information',
        '/install', '/installation',
        '/js', '/javascript', '/scripts',
        '/landing', '/landingpages',
        '/lib', '/libs', '/library',
        '/live', '/livechat',
        '/local', '/localhost',
        '/log', '/logs',
        '/login', '/logout', '/signin', '/signup', '/register',
        '/mail', '/mailer', '/mailing',
        '/media', '/media/',
        '/member', '/members', '/membership',
        '/mobile',
        '/mod', '/modules',
        '/my', '/myaccount',
        '/news', '/newsletter',
        '/oauth', '/oauth2',
        '/old', '/oldsite',
        '/panel',
        '/partners', '/partner',
        '/payment', '/payments', '/billing',
        '/photo', '/photos', '/gallery',
        '/php', '/phpmyadmin', '/pma',
        '/plugin', '/plugins',
        '/portal',
        '/private', '/protected',
        '/profile', '/profiles',
        '/project', '/projects',
        '/public', '/public/',
        '/python',
        '/rest', '/restapi', '/rest-api',
        '/search', '/s',
        '/security',
        '/server', '/server-info', '/server-status',
        '/service', '/services',
        '/shop', '/store', '/shopping',
        '/signup', '/sign-up',
        '/site', '/sitemap.xml', '/sitemap',
        '/src', '/source',
        '/ssl', '/staging', '/stage',
        '/stat', '/statistik', '/statistics', '/stats',
        '/status',
        '/store', '/stores',
        '/support', '/help',
        '/sys', '/system',
        '/team', '/teams',
        '/temp', '/test', '/testing', '/tests',
        '/theme', '/themes',
        '/track', '/tracking',
        '/uploads', '/upload', '/upload/',
        '/user', '/users', '/userdata',
        '/util', '/utils',
        '/vault', '/vpn',
        '/web', '/webapp', '/webmail', '/webmaster',
        '/webroot', '/website',
        '/widget', '/widgets',
        '/wp', '/wp-admin', '/wp-content', '/wp-includes',
        '/www',
        # Sensitive files
        '/.env', '/.env.local', '/.env.production', '/.env.development',
        '/.git', '/.git/config', '/.git/HEAD', '/.git/index',
        '/.svn', '/.svn/entries',
        '/.DS_Store',
        '/.htaccess', '/.htpasswd',
        '/.aws', '/.aws/credentials',
        '/.ssh', '/.ssh/authorized_keys', '/.ssh/id_rsa',
        '/config.php', '/config.yml', '/config.json', '/config.xml',
        '/wp-config.php', '/configuration.php',
        '/phpinfo.php', '/info.php', '/test.php',
        '/server-status', '/server-info',
        '/robots.txt', '/sitemap.xml',
        '/backup.sql', '/database.sql', '/dump.sql', '/db.sql',
        '/web.config', '/web.config.bak',
        '/package.json', '/composer.json', '/requirements.txt',
        '/Dockerfile', '/docker-compose.yml',
        '/swagger.json', '/swagger.yaml', '/openapi.json',
        '/graphql', '/graphiql', '/playground',
        '/actuator', '/actuator/env', '/actuator/health',
        '/trace', '/metrics',
        '/debug', '/debug/pprof',
        '/console',
        '/.well-known', '/.well-known/jwks.json',
        '/.well-known/openid-configuration',
        '/credentials', '/secrets', '/keys', '/tokens',
        '/id_rsa', '/id_dsa', '/id_ecdsa',
        '/node_modules',
        '/vendor',
        '/storage', '/storage/',
        '/tmp', '/temp',
        '/.npmrc', '/.yarnrc', '/.babelrc',
        '/.gitignore', '/.dockerignore',
        '/.env.example', '/.env.sample',
        '/crossdomain.xml', '/clientaccesspolicy.xml',
        '/elmah.axd', '/trace.axd',
    ]

    def __init__(self, target: str, wordlist: List[str] = None,
                 timeout: int = 3, threads: int = 5):
        self.target = target.rstrip('/')
        self.wordlist = wordlist or self.DEFAULT_WORDLIST
        self.timeout = timeout
        self.threads = threads
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.results: List[Dict] = []
        self.found_count = 0

    def _check_path(self, path: str) -> Optional[Dict]:
        """Check a single path"""
        url = f"{self.target}{path}"
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                status = resp.status
                size = len(resp.read())
                headers = dict(resp.headers)

                finding = {
                    'path': path,
                    'url': url,
                    'status': status,
                    'size': size,
                    'type': 'directory' if path.endswith('/') else 'file',
                }

                # Classify by status
                if status == 200:
                    finding['classification'] = 'accessible'
                elif status == 301 or status == 302:
                    finding['classification'] = 'redirect'
                    finding['location'] = headers.get('Location', '')
                elif status == 403:
                    finding['classification'] = 'forbidden'
                elif status == 404:
                    finding['classification'] = 'not_found'
                else:
                    finding['classification'] = f'http_{status}'

                return finding

        except urllib.error.HTTPError as e:
            return {
                'path': path,
                'url': url,
                'status': e.code,
                'size': 0,
                'type': 'file',
                'classification': f'http_error_{e.code}',
            }
        except Exception:
            return None

    def scan(self, wordlist: List[str] = None) -> Dict:
        """Run directory scan"""
        words = wordlist or self.wordlist
        print(f"\n  [BUSTER] Scanning {len(words)} paths against {self.target}")
        print(f"  [BUSTER] Timeout: {self.timeout}s")

        found = []
        skipped = 0
        total = len(words)

        for i, path in enumerate(words):
            result = self._check_path(path)
            if result:
                if result['status'] in [200, 301, 302, 403]:
                    found.append(result)
                    self.found_count += 1
                    if self.found_count <= 20:
                        icon = "✅" if result['status'] == 200 else ("🔄" if result['status'] in [301, 302] else "🔒")
                        print(f"    {icon} {path} -> {result['status']} ({result['size']} bytes)")
            else:
                skipped += 1

            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"    Progress: {i+1}/{total} ({skipped} skipped)")

            time.sleep(0.1)  # Rate limiting

        print(f"\n  [BUSTER] Found {self.found_count} paths ({skipped} skipped)")

        return {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'total_paths_tested': total,
            'found_count': self.found_count,
            'skipped': skipped,
            'results': found,
            'by_status': {
                '200': len([r for r in found if r['status'] == 200]),
                '301': len([r for r in found if r['status'] == 301]),
                '302': len([r for r in found if r['status'] == 302]),
                '403': len([r for r in found if r['status'] == 403]),
                '404': len([r for r in found if r['status'] == 404]),
            },
            'sensitive_findings': [
                r for r in found
                if any(s in r['path'].lower() for s in [
                    '.env', '.git', '.svn', 'config', 'backup',
                    '.aws', '.ssh', 'password', 'secret', 'credential'
                ]) and r['status'] == 200
            ],
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Directory Buster')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--wordlist', '-w', help='Custom wordlist file')
    parser.add_argument('--timeout', '-t', type=int, default=3, help='Request timeout')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    wordlist = None
    if args.wordlist:
        with open(args.wordlist, 'r', encoding='utf-8') as f:
            wordlist = [line.strip() for line in f if line.strip()]

    buster = DirectoryBuster(args.target, wordlist=wordlist, timeout=args.timeout)
    result = buster.scan()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
