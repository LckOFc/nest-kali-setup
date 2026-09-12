"""
CustomBurp v2 - Sequencer
Token entropy analysis
"""

import math
import logging
import hashlib
import time
from typing import List, Dict

logger = logging.getLogger('custom_burp.sequencer')


class Sequencer:
    """Token entropy analyzer"""
    
    def __init__(self):
        pass
    
    def analyze(self, tokens: List[str], name: str = '') -> Dict:
        """Analyze token entropy and predictability"""
        if not tokens:
            return {'error': 'No tokens provided'}
        
        results = {
            'name': name or 'Analysis',
            'count': len(tokens),
            'timestamp': time.time(),
        }
        
        # Shannon entropy
        entropies = []
        for token in tokens:
            ent = self._shannon_entropy(token)
            entropies.append(ent)
        
        avg_entropy = sum(entropies) / len(entropies) if entropies else 0
        results['entropy'] = {
            'shannon_avg': round(avg_entropy, 4),
            'shannon_min': round(min(entropies), 4) if entropies else 0,
            'shannon_max': round(max(entropies), 4) if entropies else 0,
            'shannon_values': [round(e, 4) for e in entropies],
        }
        
        # Uniqueness
        unique_tokens = set(tokens)
        results['uniqueness'] = {
            'unique_count': len(unique_tokens),
            'total_count': len(tokens),
            'unique_ratio': round(len(unique_tokens) / len(tokens), 4) if tokens else 0,
        }
        
        # Length analysis
        lengths = [len(t) for t in tokens]
        results['length'] = {
            'avg': round(sum(lengths) / len(lengths), 2) if lengths else 0,
            'min': min(lengths) if lengths else 0,
            'max': max(lengths) if lengths else 0,
            'consistent': len(set(lengths)) == 1,
        }
        
        # Predictability checks
        predictability = self._check_predictability(tokens)
        results['predictability'] = predictability
        
        # Pattern detection
        patterns = self._detect_patterns(tokens)
        results['patterns'] = patterns
        
        # Severity assessment
        severity = self._assess_severity(results)
        results['severity'] = severity
        
        # Recommendation
        results['recommendation'] = self._get_recommendation(results)
        
        return results
    
    def _shannon_entropy(self, data: str) -> float:
        """Calculate Shannon entropy"""
        if not data:
            return 0
        
        freq = {}
        for c in data:
            freq[c] = freq.get(c, 0) + 1
        
        entropy = 0
        length = len(data)
        for count in freq.values():
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)
        
        return entropy
    
    def _check_predictability(self, tokens: List[str]) -> Dict:
        """Check for predictability issues"""
        issues = []
        
        # Check for sequential patterns
        if len(tokens) > 2:
            nums = []
            for t in tokens:
                try:
                    nums.append(int(t))
                except:
                    pass
            
            if len(nums) >= 3:
                diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
                if len(set(diffs)) == 1:
                    issues.append({
                        'type': 'sequential',
                        'detail': f'Tokens appear sequential with step {diffs[0]}',
                        'severity': 'High'
                    })
        
        # Check for low entropy
        for i, token in enumerate(tokens):
            ent = self._shannon_entropy(token)
            if ent < 2.0:
                issues.append({
                    'type': 'low_entropy',
                    'index': i,
                    'detail': f'Token {i+1} has very low entropy ({ent:.2f})',
                    'severity': 'High'
                })
        
        # Check for repetition
        if len(tokens) != len(set(tokens)):
            issues.append({
                'type': 'repetition',
                'detail': f'{len(tokens) - len(set(tokens))} duplicate tokens found',
                'severity': 'Medium'
            })
        
        # Check timestamp patterns
        for i, token in enumerate(tokens):
            try:
                ts = int(token)
                if 1000000000 < ts < 2000000000:
                    issues.append({
                        'type': 'timestamp',
                        'index': i,
                        'detail': f'Token {i+1} appears to be a Unix timestamp',
                        'severity': 'Medium'
                    })
            except:
                pass
        
        return {
            'predictable': len(issues) > 0,
            'issues': issues,
            'issue_count': len(issues),
        }
    
    def _detect_patterns(self, tokens: List[str]) -> List[Dict]:
        """Detect patterns in tokens"""
        patterns = []
        
        # Check for common prefixes
        if len(tokens) > 1:
            prefix_len = min(len(t) for t in tokens)
            for length in range(1, min(prefix_len, 20)):
                prefixes = set(t[:length] for t in tokens)
                if len(prefixes) == 1:
                    patterns.append({
                        'type': 'common_prefix',
                        'length': length,
                        'prefix': tokens[0][:length],
                    })
                    break
        
        # Check for charset patterns
        all_chars = set(''.join(tokens))
        if all_chars.issubset(set('0123456789')):
            patterns.append({'type': 'numeric_only', 'charset': 'digits'})
        elif all_chars.issubset(set('0123456789abcdefABCDEF')):
            patterns.append({'type': 'hex_only', 'charset': 'hex'})
        elif all_chars.issubset(set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=')):
            patterns.append({'type': 'base64_like', 'charset': 'base64'})
        
        return patterns
    
    def _assess_severity(self, results: Dict) -> str:
        """Assess overall severity"""
        score = 0
        
        entropy = results.get('entropy', {}).get('shannon_avg', 0)
        if entropy < 3:
            score += 3
        elif entropy < 4:
            score += 2
        elif entropy < 5:
            score += 1
        
        uniq_ratio = results.get('uniqueness', {}).get('unique_ratio', 1)
        if uniq_ratio < 0.5:
            score += 3
        elif uniq_ratio < 0.8:
            score += 1
        
        predictability = results.get('predictability', {})
        if predictability.get('predictable'):
            score += predictability.get('issue_count', 0)
        
        if score >= 5:
            return 'Critical'
        elif score >= 3:
            return 'High'
        elif score >= 1:
            return 'Medium'
        return 'Low'
    
    def _get_recommendation(self, results: Dict) -> str:
        """Generate recommendation"""
        parts = []
        
        entropy = results.get('entropy', {}).get('shannon_avg', 0)
        if entropy < 4:
            parts.append(f'Low entropy ({entropy:.2f} bits). Use more random tokens.')
        
        predictability = results.get('predictability', {})
        if predictability.get('predictable'):
            for issue in predictability.get('issues', []):
                parts.append(issue['detail'])
        
        uniqueness = results.get('uniqueness', {}).get('unique_ratio', 1)
        if uniqueness < 1.0:
            parts.append(f'{(1-uniqueness)*100:.0f}% of tokens are duplicates.')
        
        if not parts:
            return 'Tokens appear adequately random and unique.'
        
        return ' '.join(parts)
