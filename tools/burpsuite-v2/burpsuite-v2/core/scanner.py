"""
CustomBurp v2 - Active Vulnerability Scanner
Real scanning com requests ativos, não apenas padrões
"""

import asyncio
import hashlib
import json
import time
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, quote
from core.repeater import Repeater

logger = logging.getLogger('custom_burp.scanner')


class VulnScanner:
    """Active vulnerability scanner with real request-based detection"""
    
    # XSS patterns - real detection via reflected input
    XSS_TESTS = [
        {'name': 'Basic XSS', 'payload': '<script>alert(1)</script>', 'param': 'q'},
        {'name': 'IMG XSS', 'payload': '<img src=x onerror=alert(1)>', 'param': 'search'},
        {'name': 'SVG XSS', 'payload': '<svg/onload=alert(1)>', 'param': 'input'},
        {'name': 'iframe XSS', 'payload': '<iframe src="javascript:alert(1)">', 'param': 'data'},
        {'name': 'Event handler', 'payload': '" onmouseover="alert(1)', 'param': 'test'},
        {'name': 'XSS via URL encoding', 'payload': '%3Cscript%3Ealert(1)%3C/script%3E', 'param': 'q'},
    ]
    
    # SQLi patterns
    SQLI_TESTS = [
        {'name': 'Union select', 'payload': "' UNION SELECT 1--", 'param': 'id'},
        {'name': 'OR 1=1', 'payload': "' OR '1'='1", 'param': 'id'},
        {'name': 'DROP TABLE', 'payload': "'; DROP TABLE users--", 'param': 'id'},
        {'name': 'Sleep delay', 'payload': "' AND SLEEP(5)--", 'param': 'id'},
        {'name': 'Waitfor delay', 'payload': "' WAITFOR DELAY '0:0:5'--", 'param': 'id'},
        {'name': 'Boolean blind', 'payload': "' AND 1=1--", 'param': 'id'},
        {'name': 'Error based', 'payload': "' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version())))--", 'param': 'id'},
        {'name': 'Stacked queries', 'payload': "'; SELECT * FROM users--", 'param': 'id'},
    ]
    
    # Path traversal tests
    TRAVERSAL_TESTS = [
        {'name': 'Basic traversal', 'payload': '../../../../etc/passwd', 'param': 'file'},
        {'name': 'URL encoded', 'payload': '..%2F..%2F..%2Fetc%2Fpasswd', 'param': 'file'},
        {'name': 'Double encoded', 'payload': '%252e%252e%252f%252e%252e%252fetc%252fpasswd', 'param': 'file'},
        {'name': 'Null byte', 'payload': '../../../etc/passwd%00', 'param': 'file'},
        {'name': 'Windows path', 'payload': '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts', 'param': 'file'},
    ]
    
    # SSRF tests
    SSRF_TESTS = [
        {'name': 'Local metadata', 'payload': 'http://169.254.169.254/latest/meta-data/', 'param': 'url'},
        {'name': 'Local file', 'payload': 'file:///etc/passwd', 'param': 'url'},
        {'name': 'Local host', 'payload': 'http://127.0.0.1:8080/', 'param': 'url'},
        {'name': 'Gopher SSRF', 'payload': 'gopher://127.0.0.1:6379/_INFO', 'param': 'url'},
    ]
    
    # Command injection patterns
    CMDI_TESTS = [
        {'name': 'Semicolon', 'payload': '; ls', 'param': 'cmd'},
        {'name': 'Pipe', 'payload': '| id', 'param': 'cmd'},
        {'name': 'Backtick', 'payload': '`whoami`', 'param': 'cmd'},
        {'name': 'AND', 'payload': '&& cat /etc/passwd', 'param': 'cmd'},
        {'name': 'Subshell', 'payload': '$(id)', 'param': 'cmd'},
    ]
    
    SEVERITY_MAP = {
        'XSS': 'High',
        'SQLi': 'Critical',
        'Path_Traversal': 'High',
        'SSRF': 'High',
        'Command_Injection': 'Critical',
        'Info_Disclosure': 'Low',
        'Security_Headers': 'Medium',
        'Cookie_Security': 'Medium',
        'CORS': 'Medium',
        'SSL': 'Medium',
    }
    
    def __init__(self, db):
        self.db = db
        self.repeater = Repeater(db)
        self._scan_results: Dict[str, List[Dict]] = {}
        self._is_scanning = False
    
    async def scan_host(self, host: str, paths: Optional[List[str]] = None,
                        max_depth: int = 3, timeout: float = 10.0) -> Dict:
        """Scan a host for vulnerabilities"""
        self._is_scanning = True
        scan_id = hashlib.md5(f"{host}{time.time()}".encode()).hexdigest()[:12]
        results = {
            'scan_id': scan_id,
            'host': host,
            'started_at': time.time(),
            'vulnerabilities': [],
            'requests_made': 0,
            'paths_scanned': 0,
        }
        
        try:
            # Get paths to scan
            if not paths:
                paths = await self._discover_paths(host, max_depth)
            
            logger.info(f"Scan {scan_id} started for {host}: {len(paths)} paths")
            
            for path in paths:
                if not self._is_scanning:
                    break
                
                full_url = f"http://{host}{path}"
                
                # Test each vulnerability category
                for test_type, tests in [
                    ('XSS', self.XSS_TESTS),
                    ('SQLi', self.SQLI_TESTS),
                    ('Path_Traversal', self.TRAVERSAL_TESTS),
                    ('SSRF', self.SSRF_TESTS),
                    ('Command_Injection', self.CMDI_TESTS),
                ]:
                    if not self._is_scanning:
                        break
                    
                    for test in tests:
                        try:
                            vuln = await self._run_test(
                                scan_id, host, path, full_url, test_type, test
                            )
                            if vuln:
                                results['vulnerabilities'].append(vuln)
                                results['requests_made'] += 1
                        except Exception as e:
                            logger.debug(f"Test error {test_type}/{test['name']}: {e}")
            
            # Run passive checks (headers, cookies, etc.)
            passive_results = await self._run_passive_checks(host, paths)
            results['vulnerabilities'].extend(passive_results)
            
            results['finished_at'] = time.time()
            results['duration_seconds'] = results['finished_at'] - results['started_at']
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            results['error'] = str(e)
        
        self._is_scanning = False
        self._scan_results[scan_id] = results
        
        # Save vulnerabilities to DB
        for vuln in results.get('vulnerabilities', []):
            issue_data = {
                'id': hashlib.md5(f"{vuln['type']}{vuln.get('request_id','')}{time.time()}".encode()).hexdigest()[:16],
                'timestamp': time.time(),
                'request_id': vuln.get('request_id', ''),
                'issue_type': vuln['type'],
                'severity': vuln['severity'],
                'confidence': vuln.get('confidence', 'Medium'),
                'description': vuln['description'],
                'evidence': vuln.get('evidence', ''),
                'solution': vuln.get('solution', ''),
            }
            self.db.save_issue(issue_data)
        
        return results
    
    async def _run_test(self, scan_id: str, host: str, path: str,
                        full_url: str, test_type: str, test: Dict) -> Optional[Dict]:
        """Run a single vulnerability test"""
        test_name = test['name']
        payload = test['payload']
        param = test.get('param', 'q')
        
        # Modify URL with payload
        parsed = urlparse(full_url)
        if parsed.query:
            new_query = parsed.query + f"&{param}={quote(payload)}"
        else:
            new_query = f"{param}={quote(payload)}"
        
        test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                               parsed.params, new_query, parsed.fragment))
        
        # Also test in POST body
        post_body = f"{param}={payload}"
        
        requests_to_test = [
            {'method': 'GET', 'url': test_url},
            {'method': 'POST', 'url': full_url, 'body': post_body},
        ]
        
        for req in requests_to_test:
            try:
                result = await asyncio.wait_for(
                    self.repeater.send(req),
                    timeout=10.0
                )
                
                resp = result.get('response', {})
                resp_body = resp.get('body', '')
                resp_headers = resp.get('headers', {})
                
                # Check for reflection in response
                vuln = None
                
                if test_type == 'XSS':
                    vuln = self._check_xss(resp_body, payload, test, result)
                elif test_type == 'SQLi':
                    vuln = self._check_sqli(resp_body, payload, test, result, resp_headers)
                elif test_type == 'Path_Traversal':
                    vuln = self._check_traversal(resp_body, payload, test, result)
                elif test_type == 'SSRF':
                    vuln = self._check_ssrf(resp_body, payload, test, result)
                elif test_type == 'Command_Injection':
                    vuln = self._check_cmdi(resp_body, payload, test, result)
                
                if vuln:
                    return vuln
                
                self.db.save_request({
                    'id': hashlib.md5(f"{scan_id}{test_type}{time.time()}".encode()).hexdigest()[:16],
                    'timestamp': time.time(),
                    'method': req['method'],
                    'host': host,
                    'port': 443 if parsed.scheme == 'https' else 80,
                    'path': parsed.path,
                    'query': new_query if req['method'] == 'GET' else '',
                    'headers': {'User-Agent': 'CustomBurp-Scanner/2.0'},
                    'body': req.get('body', ''),
                    'engine': 'scanner',
                    'tags': ['scan', scan_id],
                    'notes': f'Test: {test_type}/{test_name}',
                    'folder': 'scan:' + scan_id,
                    'is_intercepted': 0,
                    'is_modified': 0,
                    'response': resp,
                })
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Test request error: {e}")
        
        return None
    
    def _check_xss(self, body: str, payload: str, test: Dict, result: Dict) -> Optional[Dict]:
        """Check for reflected XSS"""
        # Check if payload is reflected in response
        if payload in body or payload.replace('<', '&lt;').replace('>', '&gt;') in body:
            # Check for encoding
            if '<script>' in body.lower() or 'onerror' in body.lower() or 'onload' in body.lower():
                return {
                    'type': 'XSS',
                    'subtype': 'Reflected XSS',
                    'severity': 'High',
                    'confidence': 'High',
                    'description': f'Reflected XSS detected: {test["name"]}',
                    'evidence': f'Payload reflected in response body',
                    'solution': 'Implement input sanitization and output encoding',
                    'request_id': result.get('id', ''),
                }
        return None
    
    def _check_sqli(self, body: str, payload: str, test: Dict, result: Dict,
                    headers: Dict) -> Optional[Dict]:
        """Check for SQL injection"""
        error_patterns = [
            r'SQL syntax.*MySQL', r'mysql_fetch', r'valid MySQL result',
            r'Microsoft SQL Server', r'ODBC Driver', r'SQLite3::',
            r'unclosed quotation mark', r'SQL command not properly ended',
            r'ORA-\d{5}', r'PostgreSQL.*ERROR', r'pg_query',
            r'syntax error.*SQL', r'Warning.*mysqli', r'mssql_query',
        ]
        
        for pattern in error_patterns:
            try:
                if re.search(pattern, body, re.IGNORECASE):
                    return {
                        'type': 'SQLi',
                        'subtype': 'Error-Based SQLi',
                        'severity': 'Critical',
                        'confidence': 'High',
                        'description': f'SQL Injection detected: {test["name"]}',
                        'evidence': f'SQL error in response: {pattern}',
                        'solution': 'Use parameterized queries/prepared statements',
                        'request_id': result.get('id', ''),
                    }
            except:
                pass
        
        # Check for time-based (if delay is significant)
        time_ms = result.get('time_ms', 0)
        if time_ms > 3000 and 'SLEEP' in test['payload'].upper():
            return {
                'type': 'SQLi',
                'subtype': 'Time-Based Blind SQLi',
                'severity': 'Critical',
                'confidence': 'Medium',
                'description': f'Potential time-based SQLi: {test["name"]}',
                'evidence': f'Response time: {time_ms:.0f}ms (delay detected)',
                'solution': 'Use parameterized queries/prepared statements',
                'request_id': result.get('id', ''),
            }
        
        return None
    
    def _check_traversal(self, body: str, payload: str, test: Dict, result: Dict) -> Optional[Dict]:
        """Check for path traversal"""
        success_indicators = [
            'root:', 'bin/bash', 'hostname', 'windows.ini',
            'System32', 'boot.ini', 'pagefile.sys',
        ]
        
        for indicator in success_indicators:
            if indicator.lower() in body.lower():
                return {
                    'type': 'Path_Traversal',
                    'subtype': 'Directory Traversal',
                    'severity': 'High',
                    'confidence': 'High',
                    'description': f'Path Traversal detected: {test["name"]}',
                    'evidence': f'Sensitive data found in response containing: {indicator}',
                    'solution': 'Validate and sanitize file paths. Use allowlists.',
                    'request_id': result.get('id', ''),
                }
        return None
    
    def _check_ssrf(self, body: str, payload: str, test: Dict, result: Dict) -> Optional[Dict]:
        """Check for SSRF"""
        ssrf_indicators = [
            '169.254.169.254', 'metadata', 'internal',
            'docker', 'container', 'localhost', '127.0.0.1',
        ]
        
        for indicator in ssrf_indicators:
            if indicator.lower() in body.lower():
                return {
                    'type': 'SSRF',
                    'subtype': 'Server-Side Request Forgery',
                    'severity': 'High',
                    'confidence': 'Medium',
                    'description': f'Potential SSRF: {test["name"]}',
                    'evidence': f'Internal resource accessed: {indicator}',
                    'solution': 'Validate and restrict outbound URLs. Block internal IPs.',
                    'request_id': result.get('id', ''),
                }
        return None
    
    def _check_cmdi(self, body: str, payload: str, test: Dict, result: Dict) -> Optional[Dict]:
        """Check for command injection"""
        cmdi_indicators = [
            'uid=', 'gid=', 'groups=', 'whoami',
            "command not found", '/bin/', 'exit code',
        ]
        
        for indicator in cmdi_indicators:
            if indicator.lower() in body.lower():
                return {
                    'type': 'Command_Injection',
                    'subtype': 'OS Command Injection',
                    'severity': 'Critical',
                    'confidence': 'High',
                    'description': f'Command Injection detected: {test["name"]}',
                    'evidence': f'Command output found in response: {indicator}',
                    'solution': 'Never pass user input to system commands. Use allowlists.',
                    'request_id': result.get('id', ''),
                }
        return None
    
    async def _run_passive_checks(self, host: str, paths: List[str]) -> List[Dict]:
        """Run passive security checks"""
        vulnerabilities = []
        
        # Scan a sample of paths for passive issues
        sample_paths = paths[:10] if len(paths) > 10 else paths
        
        for path in sample_paths:
            try:
                result = await asyncio.wait_for(
                    self.repeater.send({'method': 'GET', 'url': f"http://{host}{path}"}),
                    timeout=5.0
                )
                
                resp = result.get('response', {})
                headers = resp.get('headers', {})
                body = resp.get('body', '')
                
                # Security headers check
                missing_headers = []
                required_headers = [
                    'X-Content-Type-Options',
                    'X-Frame-Options',
                    'Strict-Transport-Security',
                    'Content-Security-Policy',
                    'X-XSS-Protection',
                ]
                
                for h in required_headers:
                    if h.lower() not in headers:
                        missing_headers.append(h)
                
                if missing_headers:
                    vulnerabilities.append({
                        'type': 'Security_Headers',
                        'subtype': 'Missing Security Headers',
                        'severity': 'Low',
                        'confidence': 'High',
                        'description': f'Missing security headers: {", ".join(missing_headers)}',
                        'evidence': f'Path: {path}',
                        'solution': 'Add missing security headers to all responses',
                        'request_id': result.get('id', ''),
                    })
                
                # Cookie security check
                set_cookie = headers.get('Set-Cookie', '')
                if set_cookie:
                    issues = []
                    if 'Secure' not in set_cookie:
                        issues.append('missing Secure flag')
                    if 'HttpOnly' not in set_cookie:
                        issues.append('missing HttpOnly flag')
                    if 'SameSite' not in set_cookie:
                        issues.append('missing SameSite attribute')
                    
                    if issues:
                        vulnerabilities.append({
                            'type': 'Cookie_Security',
                            'subtype': 'Insecure Cookie Configuration',
                            'severity': 'Medium',
                            'confidence': 'High',
                            'description': f'Cookie security issues: {", ".join(issues)}',
                            'evidence': f'Set-Cookie: {set_cookie[:100]}',
                            'solution': 'Add Secure, HttpOnly, and SameSite attributes to cookies',
                            'request_id': result.get('id', ''),
                        })
                
                # CORS check
                cors_origin = headers.get('Access-Control-Allow-Origin', '')
                if cors_origin == '*':
                    credentials = headers.get('Access-Control-Allow-Credentials', '')
                    if credentials.lower() == 'true':
                        vulnerabilities.append({
                            'type': 'CORS',
                            'subtype': 'Wildcard CORS with Credentials',
                            'severity': 'Medium',
                            'confidence': 'High',
                            'description': 'CORS misconfiguration: wildcard origin with credentials',
                            'evidence': 'Access-Control-Allow-Origin: * with Access-Control-Allow-Credentials: true',
                            'solution': 'Restrict CORS origins to specific domains',
                            'request_id': result.get('id', ''),
                        })
                
                # Info disclosure
                info_headers = {
                    'X-Powered-By': 'Technology exposure',
                    'X-AspNet-Version': 'Technology exposure',
                    'Server': 'Server version disclosure',
                }
                for header, desc in info_headers.items():
                    if header.lower() in headers:
                        vulnerabilities.append({
                            'type': 'Info_Disclosure',
                            'subtype': desc,
                            'severity': 'Low',
                            'confidence': 'High',
                            'description': f'{header}: {headers[header][:50]}',
                            'evidence': f'{header}: {headers[header]}',
                            'solution': 'Remove or obfuscate informational headers',
                            'request_id': result.get('id', ''),
                        })
                        
            except Exception as e:
                logger.debug(f"Passive check error on {path}: {e}")
        
        return vulnerabilities
    
    async def _discover_paths(self, host: str, max_depth: int = 3) -> List[str]:
        """Discover paths from database or generate common paths"""
        # Get paths from logged requests
        stored_paths = set()
        requests = self.db.get_requests(host=host, limit=500)
        for req in requests:
            if req.get('path'):
                stored_paths.add(req['path'])
        
        # Common paths to test
        common_paths = [
            '/', '/index.html', '/login', '/admin', '/api/', '/robots.txt',
            '/sitemap.xml', '/.env', '/wp-admin', '/wp-login.php',
            '/phpmyadmin', '/.git/config', '/server-status',
            '/admin/', '/dashboard', '/api/v1/', '/api/v2/',
            '/test', '/debug', '/trace', '/graphql',
            '/console', '/actuator', '/health', '/status',
            '/upload', '/files/', '/assets/', '/static/',
        ]
        
        all_paths = list(stored_paths | set(common_paths))
        return all_paths[:50]  # Limit to avoid too many requests
    
    def get_scan_status(self) -> Dict:
        """Get current scan status"""
        return {
            'is_scanning': self._is_scanning,
            'total_scans': len(self._scan_results),
            'recent_scans': list(self._scan_results.keys())[-5:],
        }
    
    def get_results(self, scan_id: str) -> Optional[Dict]:
        """Get results for a specific scan"""
        return self._scan_results.get(scan_id)
    
    def get_all_results(self) -> Dict[str, Dict]:
        """Get all scan results"""
        return dict(self._scan_results)
    
    def clear_results(self):
        """Clear scan results"""
        self._scan_results.clear()
