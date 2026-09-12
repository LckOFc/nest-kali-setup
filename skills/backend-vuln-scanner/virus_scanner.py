#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Virus Scanner — Validação de Segurança para URLs e Downloads
Integração com VirusTotal, URLScan.io e análise heurística local
"""

import sys
import json
import time
import hashlib
import urllib.request
import urllib.error
import ssl
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class VirusScanner:
    """Scanner de vírus e malware para URLs e arquivos"""
    
    # Serviços de scanning
    SCANNING_SERVICES = {
        'virustotal': {
            'name': 'VirusTotal',
            'url': 'https://www.virustotal.com/api/v3/urls',
            'requires_key': True,
            'rate_limit': '4 requests per minute',
        },
        'urlscan': {
            'name': 'URLScan.io',
            'url': 'https://urlscan.io/api/v1/search/',
            'requires_key': False,
            'rate_limit': '60 requests per minute',
        },
        'surge': {
            'name': 'Surge Survey',
            'url': 'https://surveymonkey.com',  # Placeholder - não usar
            'requires_key': True,
            'disabled': True,
        },
    }
    
    # Assinaturas conhecidas de malware
    MALWARE_SIGNATURES = {
        'known_malware_domains': [
            'malware', 'phishing', 'scam', 'fraud', 'exploit',
            'ransomware', 'botnet', 'c2', 'command.control',
        ],
        'suspicious_extensions': ['.exe', '.bat', '.cmd', '.scr', '.js', '.vbs', '.ps1'],
        'suspicious_patterns': [
            r'eval\s*\(', r'exec\s*\(', r'system\s*\(',
            r'wget\s+.*\|', r'curl\s+.*\|',
            r'powershell.*-enc', r'powershell.*-encodedcommand',
        ]
    }
    
    def __init__(self, vt_api_key: str = None):
        self.vt_api_key = vt_api_key
        self.cache: Dict[str, Dict] = {}
        self.results: List[Dict] = []
        
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
    
    def scan_url(self, url: str, services: List[str] = None) -> Dict:
        """Scan URL usando múltiplos serviços"""
        services = services or ['urlscan']
        
        # Verificar cache
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        print(f"\n[SCAN] Scanning: {url[:60]}...")
        
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_safe': True,
            'risk_score': 0,
            'threats': [],
        }
        
        # URLScan.io (não requer API key)
        if 'urlscan' in services:
            urlscan_result = self._scan_urlscan(url)
            result['services']['urlscan'] = urlscan_result
            if urlscan_result.get('malicious'):
                result['overall_safe'] = False
                result['risk_score'] += urlscan_result['malicious_score'] * 10
                result['threats'].extend(urlscan_result.get('flags', []))
        
        # VirusTotal (requer API key)
        if 'virustotal' in services and self.vt_api_key:
            vt_result = self._scan_virustotal(url)
            result['services']['virustotal'] = vt_result
            if vt_result.get('malicious', 0) > 0:
                result['overall_safe'] = False
                result['risk_score'] += vt_result['malicious'] * 5
                result['threats'].append(f"VT detected: {vt_result['malicious']} engines")
        
        # Análise heurística local
        heuristic = self._heuristic_scan(url)
        result['services']['heuristic'] = heuristic
        if heuristic.get('threats'):
            result['overall_safe'] = False
            result['risk_score'] += len(heuristic['threats']) * 15
            result['threats'].extend(heuristic['threats'])
        
        # Calcular score final
        result['risk_score'] = min(100, result['risk_score'])
        result['safe'] = result['risk_score'] < 30
        result['severity'] = self._get_severity(result['risk_score'])
        
        # Cache
        self.cache[cache_key] = result
        self.results.append(result)
        
        # Status
        status = "SAFE" if result['safe'] else "THREAT"
        print(f"  [{status}] Score: {result['risk_score']}/100 | Severity: {result['severity']}")
        
        return result
    
    def scan_file(self, file_path: str) -> Dict:
        """Scan arquivo local"""
        print(f"\n[SCAN] Scanning file: {file_path}")
        
        result = {
            'file': file_path,
            'timestamp': datetime.now().isoformat(),
            'hash': {},
            'size': 0,
            'threats': [],
            'safe': True,
            'risk_score': 0,
        }
        
        try:
            # Hash do arquivo
            with open(file_path, 'rb') as f:
                content = f.read()
                result['size'] = len(content)
                result['hash']['md5'] = hashlib.md5(content).hexdigest()
                result['hash']['sha1'] = hashlib.sha1(content).hexdigest()
                result['hash']['sha256'] = hashlib.sha256(content).hexdigest()
            
            # Verificar extensão
            ext = Path(file_path).suffix.lower()
            if ext in self.MALWARE_SIGNATURES['suspicious_extensions']:
                result['threats'].append({
                    'type': 'suspicious_extension',
                    'severity': 'medium',
                    'detail': f'Extension .{ext.strip(".")}'
                })
                result['risk_score'] += 20
            
            # Verificar contra signatures
            content_str = content.decode('utf-8', errors='ignore')[:10000]
            for pattern in self.MALWARE_SIGNATURES['suspicious_patterns']:
                if re.search(pattern, content_str, re.IGNORECASE):
                    result['threats'].append({
                        'type': 'malware_pattern',
                        'severity': 'high',
                        'pattern': pattern
                    })
                    result['risk_score'] += 30
            
            # VirusTotal scan (se API key disponível)
            if self.vt_api_key and result['hash']['sha256']:
                vt_result = self._scan_file_virustotal(result['hash']['sha256'])
                result['services'] = {'virustotal': vt_result}
                if vt_result.get('malicious', 0) > 0:
                    result['threats'].append(f"VT: {vt_result['malicious']} engines")
                    result['risk_score'] += vt_result['malicious'] * 5
        
        except Exception as e:
            result['error'] = str(e)
            result['safe'] = False
            result['risk_score'] = 100
        
        result['safe'] = result['risk_score'] < 30
        result['severity'] = self._get_severity(result['risk_score'])
        
        status = "SAFE" if result['safe'] else "THREAT"
        print(f"  [{status}] Score: {result['risk_score']}/100 | Size: {result['size']} bytes")
        
        return result
    
    def _scan_urlscan(self, url: str) -> Dict:
        """Scan via URLScan.io"""
        try:
            data = json.dumps({'url': url, 'public': 'off'}).encode()
            req = urllib.request.Request(
                'https://urlscan.io/api/v1/scan/',
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=self.ctx) as resp:
                result = json.loads(resp.read().decode())
                task_id = result.get('taskid')
                
                # Aguardar análise
                time.sleep(3)
                
                # Buscar resultado
                if task_id:
                    req2 = urllib.request.Request(
                        f'https://urlscan.io/api/v1/result/{task_id}'
                    )
                    with urllib.request.urlopen(req2, timeout=10, context=self.ctx) as resp2:
                        data = json.loads(resp2.read().decode())
                        return {
                            'malicious': data.get('verdicts', {}).get('overall', 0) > 0,
                            'malicious_score': data.get('verdicts', {}).get('maliceScore', 0),
                            'flags': data.get('verdicts', {}).get('flags', []),
                            'screenshot': data.get('screenshot', ''),
                        }
                
                return {'malicious': False, 'score': 0}
                
        except Exception as e:
            return {'error': str(e), 'malicious': False}
    
    def _scan_virustotal(self, url: str) -> Dict:
        """Scan via VirusTotal API"""
        if not self.vt_api_key:
            return {'error': 'No VirusTotal API key'}
        
        try:
            # Analisar URL
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            req = urllib.request.Request(
                f'https://www.virustotal.com/api/v3/urls',
                data=json.dumps({'url': url}).encode(),
                headers={
                    'x-apikey': self.vt_api_key,
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=self.ctx) as resp:
                result = json.loads(resp.read().decode())
                analysis_id = result['data']['id']
                
                # Aguardar análise
                time.sleep(5)
                
                # Buscar resultado
                req2 = urllib.request.Request(
                    f'https://www.virustotal.com/api/v3/analyses/{analysis_id}',
                    headers={'x-apikey': self.vt_api_key}
                )
                
                with urllib.request.urlopen(req2, timeout=10, context=self.ctx) as resp2:
                    analysis = json.loads(resp2.read().decode())
                    stats = analysis['data']['attributes']['stats']
                    
                    return {
                        'malicious': stats.get('malicious', 0),
                        'suspicious': stats.get('suspicious', 0),
                        'undetected': stats.get('undetected', 0),
                        'harmless': stats.get('harmless', 0),
                        'total': sum(stats.values()),
                    }
                    
        except Exception as e:
            return {'error': str(e), 'malicious': 0}
    
    def _scan_file_virustotal(self, sha256: str) -> Dict:
        """Scan arquivo via VirusTotal"""
        if not self.vt_api_key:
            return {'error': 'No API key'}
        
        try:
            req = urllib.request.Request(
                f'https://www.virustotal.com/api/v3/files/{sha256}',
                headers={'x-apikey': self.vt_api_key}
            )
            
            with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                result = json.loads(resp.read().decode())
                attrs = result['data']['attributes']
                stats = attrs.get('last_analysis_stats', {})
                
                return {
                    'malicious': stats.get('malicious', 0),
                    'suspicious': stats.get('suspicious', 0),
                    'undetected': stats.get('undetected', 0),
                    'harmless': stats.get('harmless', 0),
                    'total': sum(stats.values()),
                }
                
        except Exception as e:
            return {'error': str(e), 'malicious': 0}
    
    def _heuristic_scan(self, url: str) -> Dict:
        """Análise heurística local"""
        threats = []
        
        # Verificar patterns
        url_lower = url.lower()
        
        for pattern in self.MALWARE_SIGNATURES['suspicious_patterns']:
            if re.search(pattern, url_lower):
                threats.append({
                    'type': 'suspicious_pattern',
                    'severity': 'high',
                    'pattern': pattern
                })
        
        # Verificar domínio
        domain_match = re.search(r'https?://([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            for bad_domain in self.MALWARE_SIGNATURES['known_malware_domains']:
                if bad_domain in domain:
                    threats.append({
                        'type': 'malicious_domain',
                        'severity': 'critical',
                        'domain': domain
                    })
        
        return {'threats': threats}
    
    def _get_severity(self, score: int) -> str:
        """Classifica severidade"""
        if score >= 70:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        elif score > 0:
            return 'LOW'
        return 'SAFE'
    
    def get_results(self) -> List[Dict]:
        """Retorna todos os resultados"""
        return self.results
    
    def export_results(self, output_path: str) -> str:
        """Exporta resultados"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Virus Scanner — Validação de segurança')
    parser.add_argument('target', help='URL ou arquivo para scan')
    parser.add_argument('--type', '-t', choices=['url', 'file'], default='url')
    parser.add_argument('--vt-key', '-k', help='VirusTotal API key (opcional)')
    parser.add_argument('--output', '-o', help='Arquivo de saída JSON')
    parser.add_argument('--services', '-s', nargs='+', 
                        choices=['urlscan', 'virustotal', 'heuristic'],
                        default=['urlscan', 'heuristic'])
    
    args = parser.parse_args()
    
    scanner = VirusScanner(vt_api_key=args.vt_key)
    
    if args.type == 'url':
        result = scanner.scan_url(args.target, args.services)
    else:
        result = scanner.scan_file(args.target)
    
    if args.output:
        path = scanner.export_results(args.output)
        print(f"\n[SAVE] Results saved to {path}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
