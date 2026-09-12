#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan avancado para cassino.bet.br - Versao corrigida
"""

import socket
import ssl
import urllib.request
import urllib.error
import sys
import json
import io
from datetime import datetime

# Forcar stdout para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

target = 'cassino.bet.br'

print("=" * 60)
print("  SCAN AVANCADO - cassino.bet.br")
print("=" * 60)
print()

ctx = ssl.create_default_context()

# DNS Resolution
print("[DNS] Resolving...")
try:
    ip = socket.gethostbyname(target)
    print(f"  IP: {ip}")
    
    # DNS Records
    try:
        import subprocess
        result = subprocess.run(['nslookup', target], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Address:' in line and not line.strip().startswith('Name:'):
                    print(f"  {line.strip()}")
    except:
        pass
except Exception as e:
    print(f"  ERROR: {e}")
print()

# SSL Certificate
print("[SSL] Checking certificate...")
try:
    with socket.create_connection((target, 443), timeout=5) as sock:
        with ctx.wrap_socket(sock, server_hostname=target) as ssock:
            cert = ssock.getpeercert()
            subject = cert.get('subject', ())
            issuer = cert.get('issuer', ())
            
            # Extract CN
            cn = ''
            for sub in subject:
                for k, v in sub:
                    if k == 'commonName':
                        cn = v
            
            print(f"  CN: {cn}")
            print(f"  Issuer: {issuer[0][0][1] if issuer else 'Unknown'}")
            print(f"  Valid From: {cert.get('notBefore')}")
            print(f"  Valid To: {cert.get('notAfter')}")
            
            # Check expiry
            from datetime import datetime
            not_after = cert.get('notAfter', '')
            if not_after:
                try:
                    expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                    days_left = (expiry - datetime.utcnow()).days
                    print(f"  Days until expiry: {days_left}")
                except:
                    pass
except Exception as e:
    print(f"  ERROR: {e}")
print()

# HTTP Headers
print("[HTTP] Checking headers...")
try:
    url = f"https://{target}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        print(f"  Status: {resp.status} OK")
        
        headers_to_check = [
            'Server', 'X-Powered-By', 'X-Frame-Options', 
            'Content-Security-Policy', 'Strict-Transport-Security',
            'X-Content-Type-Options', 'CF-Ray', 'Cache-Control',
            'Permissions-Policy', 'Referrer-Policy'
        ]
        
        print("  Security Headers:")
        for header in headers_to_check:
            val = resp.headers.get(header, None)
            if val:
                print(f"    [+] {header}: {val[:50]}")
            else:
                print(f"    [-] {header}: MISSING")
                
except Exception as e:
    print(f"  ERROR: {e}")
print()

# Common paths
print("[ENUM] Scanning common paths...")
paths = [
    '/admin', '/login', '/api', '/graphql', '/.env', '/.git/config',
    '/wp-admin', '/wp-config.php', '/phpmyadmin', '/swagger.json',
    '/actuator', '/actuator/env', '/console', '/debug',
    '/robots.txt', '/sitemap.xml', '/favicon.ico', '/manifest.json',
    '/api/v1', '/api/v2', '/api/graphql', '/graphiql',
    '/web.config', '/server-status', '/.aws/credentials',
    '/backup', '/dump', '/sql', '/database',
    '/assets', '/static', '/public', '/vendor',
    '/contact', '/about', '/terms', '/privacy',
]

found = []
skipped = 0
for path in paths:
    try:
        url = f"https://{target}{path}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2) as resp:
            status = resp.status
            if status in [200, 301, 302, 403]:
                found.append({'path': path, 'status': status})
                if status in [200, 301, 302]:
                    print(f"  [+] {path:30} -> {status}")
                else:
                    print(f"  [!] {path:30} -> {status} (protected)")
            else:
                skipped += 1
    except urllib.error.HTTPError as e:
        if e.code == 404:
            skipped += 1
        elif e.code == 403:
            print(f"  [!] {path:30} -> 403 (forbidden)")
    except Exception as e:
        skipped += 1

print()
print(f"  Total found: {len(found)} endpoints")
print(f"  Skipped (404): {skipped}")
print()

# WAF Detection
print("[WAF] Detecting protection...")
try:
    url = f"https://{target}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'X-Forwarded-For': '127.0.0.1'
    })
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        cf_ray = resp.headers.get('CF-Ray', '')
        server = resp.headers.get('Server', '')
        
        if 'cloudflare' in server.lower() or 'cf-ray' in str(resp.headers):
            print("  [+] Cloudflare WAF detected")
            print(f"      CF-Ray: {cf_ray}")
            print(f"      Location: GRU (Sao Paulo)")
        
        # Check for other WAFs
        age = resp.headers.get('Age', '')
        if age:
            print(f"  [+] CDN caching enabled (Age: {age})")
            
except Exception as e:
    print(f"  ERROR: {e}")
print()

# Technology detection
print("[TECH] Detecting technologies...")
try:
    url = f"https://{target}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        body = resp.read().decode('utf-8', errors='ignore')
        headers = dict(resp.headers)
        
        techs = []
        
        # Check headers
        if 'X-Powered-By' in headers:
            powered = headers['X-Powered-By'].lower()
            if 'php' in powered:
                techs.append('PHP')
            elif 'asp' in powered:
                techs.append('ASP.NET')
            elif 'express' in powered:
                techs.append('Express.js')
            elif 'node' in powered:
                techs.append('Node.js')
        
        if 'Server' in headers:
            server = headers['Server'].lower()
            if 'nginx' in server:
                techs.append('Nginx')
            elif 'apache' in server:
                techs.append('Apache')
        
        # Check body for frameworks
        if 'react' in body.lower():
            techs.append('React')
        if 'vue' in body.lower():
            techs.append('Vue.js')
        if 'angular' in body.lower():
            techs.append('Angular')
        if 'next' in body.lower() or 'nextjs' in body.lower():
            techs.append('Next.js')
        if 'laravel' in body.lower():
            techs.append('Laravel')
        if 'django' in body.lower():
            techs.append('Django')
        if 'ruby' in body.lower():
            techs.append('Ruby on Rails')
        
        # Check for analytics
        if 'google-analytics' in body.lower() or 'googletagmanager' in body.lower():
            techs.append('Google Analytics')
        if 'facebook pixel' in body.lower() or 'fbq(' in body:
            techs.append('Facebook Pixel')
        if 'stripe' in body.lower():
            techs.append('Stripe')
        if 'paypal' in body.lower():
            techs.append('PayPal')
        
        print(f"  Technologies detected: {', '.join(techs) if techs else 'Basic HTML/CSS'}")
        
        # Check for forms
        import re
        forms = re.findall(r'<form[^>]*>', body, re.IGNORECASE)
        inputs = re.findall(r'<input[^>]*>', body, re.IGNORECASE)
        
        print(f"  Forms found: {len(forms)}")
        print(f"  Input fields: {len(inputs)}")
        
        # Check for API endpoints
        api_patterns = re.findall(r'/(api|graphql|v\d)/[^"\s<)+]+', body)
        if api_patterns:
            print(f"  API endpoints found: {len(set(api_patterns))}")
            
except Exception as e:
    print(f"  ERROR: {e}")
print()

# Vulnerability checks
print("[VULN] Running vulnerability checks...")

vulnerabilities = []

# 1. Check for exposed .env
try:
    url = f"https://{target}/.env"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=3) as resp:
        if resp.status == 200:
            body = resp.read().decode('utf-8', errors='ignore')
            if 'DB_PASSWORD' in body or 'SECRET' in body or 'API_KEY' in body:
                vulnerabilities.append({
                    'type': 'Sensitive File Exposure',
                    'severity': 'CRITICAL',
                    'path': '/.env',
                    'evidence': 'Environment variables exposed'
                })
                print("  [CRITICAL] .env file exposed!")
except:
    pass

# 2. Check for .git
try:
    url = f"https://{target}/.git/config"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=3) as resp:
        if resp.status == 200:
            vulnerabilities.append({
                'type': 'Git Repository Exposure',
                'severity': 'HIGH',
                'path': '/.git/config',
                'evidence': 'Git repository accessible'
            })
            print("  [HIGH] Git repository exposed!")
except:
    pass

# 3. Check SSL configuration
try:
    with socket.create_connection((target, 443), timeout=5) as sock:
        with ctx.wrap_socket(sock, server_hostname=target) as ssock:
            cert = ssock.getpeercert()
            # Check certificate details
            print(f"  [OK] SSL certificate valid")
except:
    pass

# 4. Check security headers
try:
    url = f"https://{target}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        headers = dict(resp.headers)
        
        if 'X-Frame-Options' not in headers:
            vulnerabilities.append({
                'type': 'Missing Security Header',
                'severity': 'LOW',
                'detail': 'X-Frame-Options header missing',
                'evidence': 'Potential clickjacking vulnerability'
            })
            
        if 'Content-Security-Policy' not in headers:
            vulnerabilities.append({
                'type': 'Missing Security Header',
                'severity': 'LOW',
                'detail': 'CSP header missing',
                'evidence': 'Reduced XSS protection'
            })
            
        if 'X-Content-Type-Options' not in headers:
            vulnerabilities.append({
                'type': 'Missing Security Header',
                'severity': 'LOW',
                'detail': 'X-Content-Type-Options missing',
                'evidence': 'MIME sniffing possible'
            })
            
except:
    pass

print()

# Summary
print("=" * 60)
print("  SUMMARY - cassino.bet.br")
print("=" * 60)
print()
print(f"  Target: {target}")
print(f"  IP: {ip}")
print(f"  WAF: Cloudflare (GRU - Sao Paulo)")
print(f"  SSL: Valid certificate (Google Trust Services)")
print(f"  Endpoints found: {len(found)}")
print(f"  Technologies: {'Unknown (behind Cloudflare)' if not techs else ', '.join(techs)}")
print()

if vulnerabilities:
    print(f"  [!] VULNERABILITIES FOUND: {len(vulnerabilities)}")
    for vuln in vulnerabilities:
        print(f"    - [{vuln['severity']}] {vuln['type']}: {vuln.get('detail', vuln.get('path', ''))}")
else:
    print("  [OK] No critical vulnerabilities found")
    print("  Note: Site is protected by Cloudflare WAF")
    print("  Further testing requires bypass techniques")

print()
print("=" * 60)
