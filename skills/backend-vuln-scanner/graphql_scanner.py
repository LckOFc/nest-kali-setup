#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphQL Scanner and Exploitation Module
Test GraphQL endpoints for introspection, batch queries, and nested exploits
"""

import sys
import json
import time
import urllib.request
import urllib.error
import ssl
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GraphQLResult:
    """Resultado de teste GraphQL"""
    technique: str
    success: bool
    severity: str
    details: str = ""
    query: str = ""
    response: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'technique': self.technique,
            'success': self.success,
            'severity': self.severity,
            'details': self.details,
            'query': self.query[:200],
            'response_preview': self.response[:200] if self.response else ''
        }


class GraphQLScanner:
    """Scanner e explorador de GraphQL APIs"""
    
    # Queries padrão para teste
    INTROSPECTION_QUERY = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        types {
          kind
          name
          fields {
            name
            args {
              name
              type { name }
            }
          }
        }
      }
    }
    """
    
    BASIC_QUERY = """
    {
      __typename
    }
    """
    
    # Queries suspeitas para detecção
    SUSPICIOUS_QUERIES = [
        # Batch queries
        """
        {
          a: user(id: 1) { id name email }
          b: user(id: 2) { id name email }
          c: user(id: 3) { id name email }
          d: user(id: 4) { id name email }
          e: user(id: 5) { id name email }
        }
        """,
        # Deep nesting
        """
        {
          user(id: 1) {
            orders {
              items {
                product {
                  reviews {
                    user {
                      orders {
                        items {
                          product {
                            id
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """,
        # Field duplication
        """
        {
          user(id: 1) {
            id
            id
            id
            name
            name
            email
            email
          }
        }
        """,
        # Aliased queries
        """
        {
          admin: user(id: 1) { id role isAdmin }
          user1: user(id: 2) { id role isAdmin }
          user2: user(id: 3) { id role isAdmin }
        }
        """,
    ]
    
    # Introspection types para buscar
    TYPE_SEARCH_QUERIES = {
        'User': """
        {
          __type(name: "User") {
            name
            fields {
              name
              type {
                name
                kind
              }
            }
          }
        }
        """,
        'Query': """
        {
          __type(name: "Query") {
            name
            fields {
              name
              args {
                name
                type { name }
              }
            }
          }
        }
        """,
        'Mutation': """
        {
          __type(name: "Mutation") {
            name
            fields {
              name
              args {
                name
                type { name }
              }
            }
          }
        }
        """,
    }
    
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.endpoints = []
        self.schema = None
        self.results = []
        
    def _make_request(self, url: str, data: dict, headers: dict = None) -> Tuple[int, dict, str]:
        """Faz requisição POST GraphQL"""
        if headers is None:
            headers = {}
        
        headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore')
                return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore') if e.fp else ''
            return e.code, dict(e.headers), body
        except Exception as e:
            return 0, {}, str(e)
    
    def discover_endpoints(self) -> List[str]:
        """Descobre endpoints GraphQL"""
        print("[1] Discovering GraphQL endpoints...")
        
        common_paths = [
            '/graphql', '/graphQL', '/GraphQL',
            '/api/graphql', '/api/graphQL',
            '/v1/graphql', '/v2/graphql',
            '/dev/graphql', '/test/graphql',
            '/api/v1/graphql', '/api/v2/graphql',
            '/gql', '/query',
            '/graphql-introspection',
            '/graphql-explorer', '/graphiql',
            '/playground', '/apollo',
            '/sandstorm', '/altair',
        ]
        
        discovered = []
        
        for path in common_paths:
            url = f"https://{self.target}{path}"
            
            # Testar com GET (alguns servers respondem com UI)
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0'
                })
                with urllib.request.urlopen(req, timeout=3, context=self.ctx) as resp:
                    if resp.status == 200:
                        body = resp.read().decode('utf-8', errors='ignore')
                        # Verificar se é GraphQL
                        if 'graphql' in body.lower() or '__schema' in body:
                            discovered.append({'url': url, 'type': 'GET', 'ui': True})
                            print(f"  [+] {url} (GraphQL UI)")
            except:
                pass
            
            # Testar com POST (introspection)
            data = {'query': self.BASIC_QUERY}
            status, headers, body = self._make_request(url, data)
            
            if status == 200 and 'data' in body:
                discovered.append({'url': url, 'type': 'POST', 'ui': False})
                print(f"  [+] {url} (GraphQL API)")
            elif status == 400 and 'query' in body.lower():
                discovered.append({'url': url, 'type': 'POST', 'ui': False})
                print(f"  [+] {url} (GraphQL API - requires query)")
        
        self.endpoints = discovered
        return discovered
    
    def test_introspection(self, endpoint: str) -> Optional[Dict]:
        """Testa introspecção do schema"""
        print(f"\n[2] Testing introspection: {endpoint}")
        
        data = {'query': self.INTROSPECTION_QUERY}
        status, headers, body = self._make_request(endpoint, data)
        
        if status == 200:
            try:
                response = json.loads(body)
                if 'data' in response and response['data']:
                    print("  [+] Introspection ENABLED - Schema accessible!")
                    self.schema = response['data']
                    return response['data']
            except:
                pass
        
        print("  [-] Introspection disabled or blocked")
        return None
    
    def test_batch_query(self, endpoint: str) -> GraphQLResult:
        """Testa batch query (DoS)"""
        print("\n[3] Testing batch query attack...")
        
        for i, query in enumerate(self.SUSPICIOUS_QUERIES[:2], 1):
            data = {'query': query}
            start = time.time()
            status, headers, body = self._make_request(endpoint, data)
            elapsed = time.time() - start
            
            # Verificar se há limitação
            if 'extensions' in body and 'duration' in body:
                duration = json.loads(body)['extensions'].get('duration', 0)
                if duration > 1000:  # Mais de 1 segundo
                    return GraphQLResult(
                        technique="Batch Query DoS",
                        success=True,
                        severity="HIGH",
                        details=f"Query demorou {elapsed:.2f}s - possivel DoS",
                        query=query[:100],
                        response=body[:200]
                    )
        
        return GraphQLResult(
            technique="Batch Query",
            success=False,
            severity="LOW",
            details="Batch queries blocked or rate limited"
        )
    
    def test_deep_nesting(self, endpoint: str) -> GraphQLResult:
        """Testa deep nesting attack"""
        print("\n[4] Testing deep nesting attack...")
        
        # Query com aninhamento profundo
        deep_query = """
        {
          user(id: 1) {
            orders {
              items {
                product {
                  categories {
                    products {
                      reviews {
                        user {
                          orders {
                            items {
                              product {
                                id
                                name
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        data = {'query': deep_query}
        status, headers, body = self._make_request(endpoint, data)
        
        if status == 200:
            try:
                response = json.loads(body)
                # Verificar se retorna dados (vulnerável)
                if 'data' in response and response['data']:
                    return GraphQLResult(
                        technique="Deep Nesting",
                        success=True,
                        severity="MEDIUM",
                        details="Deep nesting allowed - possible DoS",
                        query=deep_query[:100]
                    )
            except:
                pass
        
        return GraphQLResult(
            technique="Deep Nesting",
            success=False,
            severity="LOW",
            details="Deep nesting blocked by server"
        )
    
    def test_field_duplication(self, endpoint: str) -> GraphQLResult:
        """Testa field duplication attack"""
        print("\n[5] Testing field duplication...")
        
        dup_query = """
        {
          user(id: 1) {
            id
            id
            id
            id
            id
            name
            name
            name
            email
            email
          }
        }
        """
        
        data = {'query': dup_query}
        status, headers, body = self._make_request(endpoint, data)
        
        if status == 200:
            try:
                response = json.loads(body)
                # Se o servidor processa duplicação, pode haver problema
                if 'data' in response:
                    return GraphQLResult(
                        technique="Field Duplication",
                        success=True,
                        severity="LOW",
                        details="Field duplication accepted - check for cache poisoning"
                    )
            except:
                pass
        
        return GraphQLResult(
            technique="Field Duplication",
            success=False,
            severity="LOW",
            details="Field duplication rejected"
        )
    
    def search_types(self, endpoint: str, types: List[str] = None) -> List[GraphQLResult]:
        """Busca tipos específicos no schema"""
        if types is None:
            types = ['User', 'Admin', 'Order', 'Product', 'Payment', 'Transaction']
        
        results = []
        
        for type_name in types:
            query = self.TYPE_SEARCH_QUERIES.get(type_name, f'{{ __type(name: "{type_name}") {{"name" }} }}')
            data = {'query': query}
            status, headers, body = self._make_request(endpoint, data)
            
            if status == 200:
                try:
                    response = json.loads(body)
                    if response.get('data', {}).get('__type'):
                        results.append(GraphQLResult(
                            technique=f"Type Discovery: {type_name}",
                            success=True,
                            severity="INFO",
                            details=f"Type '{type_name}' exists in schema"
                        ))
                except:
                    pass
        
        return results
    
    def test_subscription(self, endpoint: str) -> GraphQLResult:
        """Testa WebSocket subscriptions"""
        print("\n[6] Testing subscriptions...")
        
        # GraphQL subscriptions usam WebSocket
        # Tentar verificar se há endpoint ws/wss
        ws_endpoints = [
            f"wss://{self.target}/graphql",
            f"ws://{self.target}/graphql",
            f"wss://{self.target}/api/graphql",
            f"ws://{self.target}/api/graphql",
        ]
        
        for ws_url in ws_endpoints:
            # Não podemos testar WebSocket facilmente sem biblioteca
            # Mas podemos verificar se o endpoint existe
            http_url = ws_url.replace('wss://', 'https://').replace('ws://', 'http://')
            try:
                req = urllib.request.Request(http_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3, context=self.ctx) as resp:
                    if resp.status == 101:  # Switching Protocols
                        return GraphQLResult(
                            technique="WebSocket Subscription",
                            success=True,
                            severity="HIGH",
                            details=f"WebSocket endpoint found: {ws_url}"
                        )
            except:
                pass
        
        return GraphQLResult(
            technique="WebSocket Subscription",
            success=False,
            severity="LOW",
            details="No WebSocket endpoint found"
        )
    
    def run_full_scan(self) -> Dict:
        """Executa scan completo GraphQL"""
        print("=" * 60)
        print("  GRAPHQL SCANNER")
        print("=" * 60)
        print()
        
        all_results = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'endpoints': [],
            'schema': None,
            'tests': [],
            'summary': {}
        }
        
        # Descobrir endpoints
        endpoints = self.discover_endpoints()
        all_results['endpoints'] = endpoints
        
        if not endpoints:
            print("\n[-] No GraphQL endpoints found")
            all_results['summary'] = {'status': 'not_found', 'vulnerabilities': 0}
            return all_results
        
        # Testar cada endpoint
        for ep in endpoints[:3]:  # Limitar a 3 endpoints
            endpoint_url = ep['url']
            print(f"\n[Testing: {endpoint_url}]")
            
            # Introspecção
            schema = self.test_introspection(endpoint_url)
            if schema:
                all_results['schema'] = schema
            
            # Testes de vulnerabilidade
            tests = [
                self.test_batch_query(endpoint_url),
                self.test_deep_nesting(endpoint_url),
                self.test_field_duplication(endpoint_url),
                self.test_subscription(endpoint_url),
            ]
            
            # Buscar tipos
            type_results = self.search_types(endpoint_url)
            tests.extend(type_results)
            
            all_results['tests'].extend(tests)
        
        # Resumo
        vulns = [r for r in all_results['tests'] if r.success and r.severity in ['HIGH', 'MEDIUM']]
        all_results['summary'] = {
            'status': 'scanned',
            'endpoints_found': len(endpoints),
            'introspection_enabled': all_results['schema'] is not None,
            'vulnerabilities': len(vulns),
            'high_severity': len([v for v in vulns if v.severity == 'HIGH']),
            'medium_severity': len([v for v in vulns if v.severity == 'MEDIUM'])
        }
        
        print("\n" + "=" * 60)
        print("  GRAPHQL SCAN SUMMARY")
        print("=" * 60)
        print(f"  Endpoints found: {all_results['summary']['endpoints_found']}")
        print(f"  Introspection: {'ENABLED' if all_results['summary']['introspection_enabled'] else 'DISABLED'}")
        print(f"  Vulnerabilities: {all_results['summary']['vulnerabilities']}")
        print(f"    - High: {all_results['summary']['high_severity']}")
        print(f"    - Medium: {all_results['summary']['medium_severity']}")
        print("=" * 60)
        
        return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='GraphQL Scanner')
    parser.add_argument('target', help='Target domain')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    scanner = GraphQLScanner(args.target)
    result = scanner.run_full_scan()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n[SAVE] Results saved to {args.output}")
    
    return result


if __name__ == "__main__":
    main()
