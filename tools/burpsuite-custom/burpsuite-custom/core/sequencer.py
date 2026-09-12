"""
CustomBurp - Sequencer
Analise de entropia de tokens de sessao
"""

import math
import re
import string
import hashlib
from typing import Dict, List, Tuple
from collections import Counter


class Sequencer:
    """Analisador de entropia de tokens de sessao"""
    
    # Scores de entropia
    ENTROPY_SCORES = {
        'very_high': 9.0,
        'high': 7.0,
        'medium': 5.0,
        'low': 3.0,
        'very_low': 1.0
    }
    
    def __init__(self):
        self.results = []
    
    def analyze(
        self,
        tokens: List[str],
        name: str = '',
        token_type: str = 'session'
    ) -> Dict:
        """
        Analisa a entropia de uma lista de tokens
        
        Args:
            tokens: Lista de strings (tokens)
            name: Nome da analise
            token_type: Tipo ('session', 'csrf', 'api_key', 'jwt', 'other')
        
        Returns:
            Dict com resultados da analise
        """
        if not tokens:
            return {'error': 'Nenhum token fornecido'}
        
        results = {
            'name': name or f'Analise {token_type}',
            'token_type': token_type,
            'count': len(tokens),
            'samples': tokens[:20],  # Primeiros 20 tokens
            'entropy': self._calc_entropy(tokens),
            'uniqueness': self._calc_uniqueness(tokens),
            'patterns': self._detect_patterns(tokens),
            'predictability': self._assess_predictability(tokens),
            'severity': '',
            'recommendation': ''
        }
        
        # Classificar severidade
        entropy_score = results['entropy']['shannon_avg']
        uniqueness_ratio = results['uniqueness']['unique_ratio']
        
        if entropy_score >= 7.0 and uniqueness_ratio > 0.95:
            results['severity'] = 'Safe'
            results['recommendation'] = 'Tokens parecem bem gerados. Entropia alta e baixa previsibilidade.'
        elif entropy_score >= 5.0 and uniqueness_ratio > 0.8:
            results['severity'] = 'Medium'
            results['recommendation'] = 'Entropia aceitavel mas pode melhorar. Verifique padroes detectados.'
        elif entropy_score >= 3.0:
            results['severity'] = 'Low'
            results['recommendation'] = 'Tokens com baixa entropia. Possivel previsibilidade. Considerar fortalecimento.'
        else:
            results['severity'] = 'Critical'
            results['recommendation'] = 'Tokens fracoss! Entropia muito baixa, padroes identificados. Risco alto de previsibilidade.'
        
        self.results.append(results)
        return results
    
    def _calc_entropy(self, tokens: List[str]) -> Dict:
        """Calcula entropia de Shannon"""
        if not tokens:
            return {'shannon_avg': 0, 'shannon_min': 0, 'shannon_max': 0}
        
        shannon_scores = []
        char_sets = []
        
        for token in tokens:
            # Entropia de Shannon
            if not token:
                shannon_scores.append(0)
                continue
            
            length = len(token)
            freq = Counter(token)
            entropy = 0
            for count in freq.values():
                prob = count / length
                if prob > 0:
                    entropy -= prob * math.log2(prob)
            shannon_scores.append(entropy)
            
            # Caracteres unicos
            unique_chars = len(set(token.lower()))
            char_sets.append(unique_chars)
        
        return {
            'shannon_avg': round(sum(shannon_scores) / len(shannon_scores), 4),
            'shannon_min': round(min(shannon_scores), 4),
            'shannon_max': round(max(shannon_scores), 4),
            'avg_unique_chars': round(sum(char_sets) / len(char_sets), 2),
            'token_lengths': [len(t) for t in tokens[:10]]
        }
    
    def _calc_uniqueness(self, tokens: List[str]) -> Dict:
        """Calcula ratio de unicidade"""
        if not tokens:
            return {'unique_count': 0, 'unique_ratio': 0, 'duplicate_tokens': []}
        
        unique = set(tokens)
        duplicate_counter = Counter(tokens)
        duplicates = [(t, c) for t, c in duplicate_counter.items() if c > 1]
        
        return {
            'unique_count': len(unique),
            'unique_ratio': round(len(unique) / len(tokens), 4),
            'duplicate_tokens': duplicates[:10],
            'total': len(tokens)
        }
    
    def _detect_patterns(self, tokens: List[str]) -> List[Dict]:
        """Detecta padroes nos tokens"""
        patterns = []
        
        for i, token in enumerate(tokens[:50]):
            # Verificar padroes comuns
            if re.match(r'^[a-f0-9]{32}$', token):
                patterns.append({'type': 'md5_hex', 'index': i, 'token': token[:20] + '...'})
            elif re.match(r'^[a-f0-9]{64}$', token):
                patterns.append({'type': 'sha256_hex', 'index': i, 'token': token[:20] + '...'})
            elif re.match(r'^[A-Za-z0-9+/=]+$', token) and len(token) > 20:
                patterns.append({'type': 'base64', 'index': i, 'token': token[:20] + '...'})
            elif token.startswith('eyJ'):  # JWT
                patterns.append({'type': 'jwt', 'index': i, 'token': token[:30] + '...'})
            elif re.match(r'^\d+$', token):
                patterns.append({'type': 'numeric', 'index': i, 'token': token[:20]})
            elif any(c in token for c in ['admin', 'test', 'user', '1234']):
                patterns.append({'type': 'dictionary_word', 'index': i, 'token': token[:20] + '...'})
        
        return patterns
    
    def _assess_predictability(self, tokens: List[str]) -> Dict:
        """Avalia previsibilidade"""
        if len(tokens) < 2:
            return {'predictable': False, 'score': 0, 'details': 'Tokens insuficientes'}
        
        issues = []
        
        # Verificar sequenciais
        numeric_tokens = []
        for t in tokens:
            try:
                numeric_tokens.append(int(t))
            except:
                pass
        
        if len(numeric_tokens) >= 3:
            diffs = [numeric_tokens[i+1] - numeric_tokens[i] for i in range(len(numeric_tokens)-1)]
            if len(set(diffs)) <= 2:  # Quase constante
                issues.append({'type': 'sequential', 'detail': 'Tokens numericos sequenciais'})
        
        # Verificar padroes de repeticao
        for i in range(len(tokens) - 1):
            if tokens[i] == tokens[i+1]:
                issues.append({'type': 'repeated', 'detail': f'Token repetido: {tokens[i][:10]}...'})
                break
        
        # Verificar prefixos common
        if len(tokens) >= 5:
            prefix_len = min(10, len(tokens[0]) // 2)
            prefixes = [t[:prefix_len] for t in tokens if len(t) >= prefix_len]
            if len(set(prefixes)) / len(prefixes) < 0.3:
                issues.append({'type': 'common_prefix', 'detail': f'{int((1-len(set(prefixes))/len(prefixes))*100)}% dos tokens compartilham prefixo'})
        
        return {
            'predictable': len(issues) > 0,
            'score': min(len(issues) * 2, 10),
            'issues': issues
        }
    
    def analyze_from_requests(self, db, host: str = None, header_name: str = 'Set-Cookie') -> Dict:
        """Analisa tokens extraidos de requests no DB"""
        from core.engine import CustomBurpDB
        import json
        
        requests = db.get_requests(host=host, limit=500) if isinstance(db, CustomBurpDB) else []
        
        tokens = []
        for req in requests:
            resp = req.get('response', {})
            headers = resp.get('headers', {})
            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except:
                    headers = {}
            
            # Extrair cookie
            cookie_header = headers.get(header_name, '')
            if isinstance(cookie_header, list):
                cookie_header = ', '.join(cookie_header)
            
            if cookie_header:
                # Pode ter varios cookies
                for cookie in cookie_header.split(','):
                    if '=' in cookie:
                        name, value = cookie.split('=', 1)
                        name = name.strip()
                        value = value.strip()
                        if value and len(value) > 4:
                            tokens.append(value)
        
        return self.analyze(tokens, f'Tokens de {header_name} em {host or "todos"}', 'cookie')


if __name__ == '__main__':
    seq = Sequencer()
    
    # Tokens de teste
    good_tokens = [
        'a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4',
        'b7e1f3a5c9d2e4f6a8b0c2d4e6f8a0b2',
        'c1d3e5f7a9b2c4d6e8f0a2b4c6d8e0f2',
        'd5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5',
        'e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9'
    ]
    
    bad_tokens = [
        'token_1',
        'token_2',
        'token_3',
        'token_4',
        'token_5'
    ]
    
    print("=== Token bons ===")
    result1 = seq.analyze(good_tokens, 'Teste Bons', 'session')
    print(f"Entropy: {result1['entropy']['shannon_avg']}")
    print(f"Severity: {result1['severity']}")
    print(f"Recommendation: {result1['recommendation']}")
    
    print("\n=== Tokens ruins ===")
    result2 = seq.analyze(bad_tokens, 'Teste Ruins', 'session')
    print(f"Entropy: {result2['entropy']['shannon_avg']}")
    print(f"Severity: {result2['severity']}")
    print(f"Recommendation: {result2['recommendation']}")
    
    print("\nSequencer OK!")
