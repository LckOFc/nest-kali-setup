#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Onion Resolver — Resolução segura de endereços .onion
Validação de formato, verificação de conectividade e análise de segurança
"""

import sys
import json
import time
import socket
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class OnionResolver:
    """Resolver e validador de endereços .onion"""
    
    # Domínios .onion válidos
    ONION_V2_PATTERN = r'^[a-z2-7]{16}\.onion$'
    ONION_V3_PATTERN = r'^[a-z2-7]{56}\.onion$'
    
    # Serviços de check de saúde
    HEALTH_CHECKS = {
        'tor_project': 'https://check.torproject.org/',
        'ahmia': 'https://ahmia.fi/',
    }
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.history: List[Dict] = []
    
    def validate_address(self, address: str) -> Dict:
        """Valida formato de endereço .onion"""
        result = {
            'address': address,
            'valid': False,
            'version': None,
            'fingerprint': None,
            'errors': [],
        }
        
        # Remover scheme
        clean = re.sub(r'^https?://', '', address)
        clean = clean.rstrip('/')
        
        # Verificar formato
        if re.match(self.ONION_V2_PATTERN, clean):
            result['valid'] = True
            result['version'] = 'v2'
            result['fingerprint'] = clean[:16]
        elif re.match(self.ONION_V3_PATTERN, clean):
            result['valid'] = True
            result['version'] = 'v3'
            result['fingerprint'] = clean[:56]
        else:
            result['errors'].append('Invalid .onion format')
            
            # Verificar se é um hash conhecido
            if len(clean) == 56:
                result['errors'].append('Looks like v3 but invalid base32')
        
        return result
    
    def resolve(self, address: str, timeout: int = 10) -> Dict:
        """Tenta resolver endereço .onion"""
        cache_key = hashlib.md5(address.encode()).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        print(f"\n[RESOLVE] {address}")
        
        result = {
            'address': address,
            'timestamp': datetime.now().isoformat(),
            'resolved': False,
            'ip': None,
            'port': 9050,
            'tor_accessible': False,
            'health': {},
        }
        
        # Validar primeiro
        validation = self.validate_address(address)
        result['validation'] = validation
        
        if not validation['valid']:
            print(f"  [ERROR] Invalid address: {validation['errors']}")
            return result
        
        # Tentar conexão via Tor
        try:
            # Verificar se Tor está rodando
            tor_check = self._check_tor_running()
            result['tor_accessible'] = tor_check['running']
            
            if tor_check['running']:
                # Tentar conectar ao serviço
                conn_result = self._test_connection(address, tor_check['port'])
                result.update(conn_result)
            else:
                result['errors'] = ['Tor not running. Start Tor Browser or torsocks.']
                
        except Exception as e:
            result['errors'] = [str(e)]
        
        # Check de saúde
        health = self._check_health(address)
        result['health'] = health
        
        # Cache
        self.cache[cache_key] = result
        self.history.append(result)
        
        status = "OK" if result['resolved'] else "FAIL"
        print(f"  [{status}] IP: {result.get('ip') or 'N/A'} | Health: {health.get('status', 'unknown')}")
        
        return result
    
    def _check_tor_running(self) -> Dict:
        """Verifica se Tor está rodando"""
        result = {'running': False, 'port': 9050, 'control_port': 9051}
        
        try:
            # Tentar conectar ao SOCKS port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('127.0.0.1', 9050))
            sock.close()
            result['running'] = True
        except:
            pass
        
        return result
    
    def _test_connection(self, address: str, tor_port: int = 9050) -> Dict:
        """Testa conexão com serviço onion"""
        result = {'resolved': False, 'ip': None, 'latency': 0}
        
        try:
            # Usar pysocks ou conectar diretamente
            import socks
            import socket
            
            socks.setdefaultproxy(socks.SOCKS5, '127.0.0.1', tor_port)
            socket.socket = socks.socksocket
            
            start = time.time()
            
            # Tentar conectar
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((address.replace('.onion', ''), 443))
            s.close()
            
            latency = (time.time() - start) * 1000
            result['resolved'] = True
            result['latency'] = latency
            
        except Exception as e:
            result['errors'] = [str(e)]
        
        return result
    
    def _check_health(self, address: str) -> Dict:
        """Verifica saúde do serviço"""
        result = {'status': 'unknown', 'checks': {}}
        
        # Checar contra listas conhecidas
        known_safe = self._check_known_safe(address)
        result['checks']['known_safe'] = known_safe
        
        if known_safe:
            result['status'] = 'safe'
        else:
            result['status'] = 'unverified'
        
        return result
    
    def _check_known_safe(self, address: str) -> bool:
        """Verifica se está em lista de conhecidos seguros"""
        # Lista de serviços legítimos conhecidos
        safe_list = [
            'protonmailpg6t3vxx.onion',
            'guardi4rvmqdhq6mh.onion',
            'www.nytimesw57leeqby2fpiezt3xkgv7e3w2zqv5mq7ay6gqp2w62hid.onion',
            'bbcnewsv27wkfsn.onion',
            '2gzyxa5umwssngjc.onion',
        ]
        
        for safe in safe_list:
            if safe in address:
                return True
        
        return False
    
    def bulk_resolve(self, addresses: List[str]) -> Dict:
        """Resolve múltiplos endereços"""
        print(f"\n{'='*60}")
        print(f"  BULK RESOLVE — {len(addresses)} addresses")
        print(f"{'='*60}")
        
        results = {
            'total': len(addresses),
            'resolved': 0,
            'failed': 0,
            'details': [],
        }
        
        for addr in addresses:
            result = self.resolve(addr)
            results['details'].append(result)
            
            if result.get('resolved'):
                results['resolved'] += 1
            else:
                results['failed'] += 1
            
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n[RESULT] Resolved: {results['resolved']}, Failed: {results['failed']}")
        
        return results
    
    def get_history(self) -> List[Dict]:
        """Retorna histórico"""
        return self.history


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Onion Resolver — Validação de endereços .onion')
    parser.add_argument('address', help='Endereço .onion para resolver')
    parser.add_argument('--bulk', '-b', nargs='+', help='Múltiplos endereços')
    parser.add_argument('--output', '-o', help='Arquivo de saída JSON')
    
    args = parser.parse_args()
    
    resolver = OnionResolver()
    
    if args.bulk:
        result = resolver.bulk_resolve(args.bulk)
    else:
        result = resolver.resolve(args.address)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
