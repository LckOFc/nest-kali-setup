#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Crawler — Descoberta recursiva de paginas e endpoints
Descobre URLs, formularios, links e pontos de entrada para testar
"""

import sys
import re
import time
import ssl
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlencode


class WebCrawler:
    """Crawler web para descoberta de endpoints e formularios"""

    def __init__(self, base_url: str, max_depth: int = 3, max_pages: int = 100,
                 timeout: int = 5, rate_limit: float = 0.5):
        self.base_url = base_url.rstrip('/')
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

        self.visited: Set[str] = set()
        self.endpoints: List[Dict] = []
        self.forms: List[Dict] = []
        self.js_files: List[str] = []
        self.params: List[Dict] = []
        self.sensitive_data: List[Dict] = []

        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.session = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor()
        )
        self.session.addheaders = [('User-Agent', self.user_agent)]

    def _fetch(self, url: str) -> Tuple[int, str, dict]:
        """Fetch URL and return (status, body, headers)"""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/json,*/*',
            })
            with self.session.open(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')[:50000]
                headers = dict(resp.headers)
                return resp.status, body, headers
        except urllib.error.HTTPError as e:
            return e.code, '', dict(e.headers) if e.headers else {}
        except Exception:
            return 0, '', {}

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is on same domain"""
        try:
            parsed_base = urlparse(self.base_url)
            parsed_url = urlparse(url)
            return parsed_url.netloc == parsed_base.netloc
        except:
            return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        url = url.split('#')[0]  # Remove fragment
        url = url.split('?')[0]  # Remove query for base
        return url.rstrip('/')

    def _extract_links(self, body: str, base_url: str) -> List[str]:
        """Extract all links from HTML"""
        links = []
        patterns = [
            r'<a\s[^>]*href=["\']([^"\']+)["\']',
            r'<link\s[^>]*href=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+\.(?:js|css|png|jpg|jpeg|gif|svg))["\']',
            r'href=["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    full_url = match
                elif match.startswith('//'):
                    full_url = f"https:{match}"
                else:
                    full_url = urljoin(base_url, match)
                links.append(full_url)

        # Extract JavaScript variable assignments
        js_patterns = [
            r'(?:const|let|var)\s+(\w+)\s*=\s*["\']([^"\']{10,})["\']',
            r'window\.(\w+)\s*=\s*["\']([^"\']{10,})["\']',
        ]
        for pattern in js_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for key, value in matches:
                if self._is_same_domain(value) or value.startswith('/'):
                    links.append(urljoin(base_url, value) if value.startswith('/') else value)

        return list(set(links))

    def _extract_forms(self, body: str, base_url: str) -> List[Dict]:
        """Extract forms from HTML"""
        forms = []
        form_pattern = r'<form\s([^>]*?)>(.*?)</form>'
        for match in re.finditer(form_pattern, body, re.DOTALL | re.IGNORECASE):
            attrs = match.group(1)
            content = match.group(2)

            # Parse form attributes
            action_match = re.search(r'action=["\']?([^"\'>\s]+)', attrs)
            method_match = re.search(r'method=["\']?([^"\'>\s]+)', attrs, re.IGNORECASE)
            enctype_match = re.search(r'enctype=["\']?([^"\'>\s]+)', attrs, re.IGNORECASE)

            action = urljoin(base_url, action_match.group(1)) if action_match else base_url
            method = (method_match.group(1) or 'GET').upper()
            enctype = enctype_match.group(1) or 'application/x-www-form-urlencoded'

            # Extract inputs
            inputs = []
            input_patterns = [
                r'<input\s[^>]*?name=["\']([^"\']+)["\'][^>]*?(?:value=["\']([^"\']*)["\'])?',
                r'<input\s[^>]*?value=["\']([^"\']*)["\'][^>]*?name=["\']([^"\']+)["\']',
            ]
            for pattern in input_patterns:
                for inp in re.finditer(pattern, content, re.IGNORECASE):
                    val = inp.group(1) if inp.group(1) else ''
                    name = inp.group(2) if inp.group(2) else inp.group(1)
                    inputs.append({'name': name, 'value': val, 'type': 'input'})

            # Extract textareas
            for ta in re.finditer(r'<textarea\s[^>]*?name=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE):
                inputs.append({'name': ta.group(1), 'value': '', 'type': 'textarea'})

            # Extract selects
            for sel in re.finditer(r'<select\s[^>]*?name=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE):
                inputs.append({'name': sel.group(1), 'value': '', 'type': 'select'})

            forms.append({
                'action': action,
                'method': method,
                'enctype': enctype,
                'inputs': inputs,
                'input_count': len(inputs),
            })

        return forms

    def _extract_params(self, body: str, base_url: str) -> List[Dict]:
        """Extract URL parameters"""
        params = []
        # Find URLs with query params
        url_pattern = r'(?:href|src|action)=["\']([^"\']*?\?.*?)["\']'
        for match in re.finditer(url_pattern, body, re.IGNORECASE):
            url = match.group(1)
            if '?' in url and self._is_same_domain(url):
                parsed = urlparse(url)
                for key in parsed.query.split('&'):
                    if '=' in key:
                        k, v = key.split('=', 1)
                        params.append({'url': url, 'param': k, 'example_value': v[:20]})

        # Find JS variables that look like API params
        js_params = re.findall(r'(?:api|endpoint|url)\s*[=:]\s*["\']([^"\']+)["\']', body, re.IGNORECASE)
        for p in js_params:
            if '?' in p:
                parsed = urlparse(p)
                for key in parsed.query.split('&'):
                    if '=' in key:
                        k, v = key.split('=', 1)
                        params.append({'url': p, 'param': k, 'example_value': v[:20]})

        return params

    def _find_sensitive_data(self, body: str, url: str) -> List[Dict]:
        """Find sensitive data in response"""
        findings = []

        # API Keys
        api_patterns = [
            (r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?', 'API Key'),
            (r'(?:secret|password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\'&]{8,})["\']?', 'Secret'),
            (r'eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+', 'JWT Token'),
            (r'(?:aws_|amazon_)?access[_-]?key[_-]?id\s*[:=]\s*["\']?([A-Z0-9]{20})["\']?', 'AWS Key'),
            (r'(?:sk-|sk_live_|sk_test_)[A-Za-z0-9]{20,}', 'Stripe Key'),
            (r'AKIA[A-Z0-9]{16}', 'AWS Access Key'),
        ]

        for pattern, vtype in api_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                findings.append({'type': vtype, 'value': match[:50], 'url': url})

        # Email addresses
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body)
        for email in set(emails[:5]):
            findings.append({'type': 'Email', 'value': email, 'url': url})

        return findings

    def crawl(self, start_url: str = None) -> Dict:
        """Execute crawl"""
        start = start_url or self.base_url
        self.visited.add(self._normalize_url(start))

        queue = [(start, 0)]  # (url, depth)
        stats = {'pages_crawled': 0, 'endpoints_found': 0, 'forms_found': 0}

        print(f"\n  [CRAWL] Starting from {start}")
        print(f"  [CRAWL] Max depth: {self.max_depth}, Max pages: {self.max_pages}")

        while queue and stats['pages_crawled'] < self.max_pages:
            url, depth = queue.pop(0)

            if depth > self.max_depth:
                continue

            print(f"  [{depth}] Crawling: {url[:80]}...")

            status, body, headers = self._fetch(url)
            stats['pages_crawled'] += 1

            if status == 0:
                continue

            # Store endpoint
            self.endpoints.append({
                'url': url,
                'status': status,
                'size': len(body),
                'depth': depth,
                'content_type': headers.get('Content-Type', ''),
            })
            stats['endpoints_found'] += 1

            # Extract forms
            forms = self._extract_forms(body, url)
            for form in forms:
                self.forms.append({**form, 'source_url': url})
            stats['forms_found'] += len(forms)

            # Extract params
            params = self._extract_params(body, url)
            self.params.extend(params)

            # Find sensitive data
            sensitive = self._find_sensitive_data(body, url)
            self.sensitive_data.extend(sensitive)

            # Extract links for next iteration
            if depth < self.max_depth:
                links = self._extract_links(body, url)
                for link in links:
                    norm = self._normalize_url(link)
                    if (self._is_same_domain(link) and
                            norm not in self.visited and
                            not any(ext in link.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif',
                                                                      '.svg', '.ico', '.pdf', '.zip',
                                                                      '.tar', '.gz', '.mp4', '.mp3',
                                                                      '.woff', '.ttf', '.eot'])):
                        self.visited.add(norm)
                        queue.append((link, depth + 1))

            time.sleep(self.rate_limit)

        # Deduplicate
        self.params = list({p['url'] + p['param']: p for p in self.params}.values())
        self.sensitive_data = list({s['value']: s for s in self.sensitive_data}.values())

        print(f"\n  [CRAWL] Complete: {stats['pages_crawled']} pages, "
              f"{stats['endpoints_found']} endpoints, "
              f"{stats['forms_found']} forms")

        return {
            'target': self.base_url,
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'endpoints': self.endpoints[:50],
            'forms': self.forms[:20],
            'params': self.params[:30],
            'sensitive_data': self.sensitive_data,
            'total_visited': len(self.visited),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Web Crawler for recon')
    parser.add_argument('target', help='Base URL')
    parser.add_argument('--depth', '-d', type=int, default=2, help='Max crawl depth')
    parser.add_argument('--max-pages', '-m', type=int, default=50, help='Max pages to crawl')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    crawler = WebCrawler(
        args.target,
        max_depth=args.depth,
        max_pages=args.max_pages,
    )

    result = crawler.crawl()

    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
