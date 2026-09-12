"""
CustomBurp - Match & Replace
Substituicao automatica em requests/respostas com suporte a backreferences
"""

import re
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class MatchRule:
    """Regra de match e replace"""
    id: str
    match_pattern: str
    replace_with: str
    target: str  # 'request', 'response', 'both'
    scope: str = ''
    enabled: bool = True
    
    def compile_match(self):
        try:
            return re.compile(self.match_pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Regex invalida '{self.match_pattern}': {e}")
    
    def compile_replace(self) -> str:
        """Compila replacement com suporte a \1, \2 backreferences"""
        # Converter $1, $2 -> \1, \2 para compatibilidade
        return re.sub(r'\$(\d+)', r'\1', self.replace_with)


class MatchReplace:
    """Match and Replace - substituicao automatica"""
    
    def __init__(self):
        self.request_rules: List[MatchRule] = []
        self.response_rules: List[MatchRule] = []
    
    def add_rule(self, pattern: str, replacement: str, target: str = 'both',
                 scope: str = '', enabled: bool = True) -> MatchRule:
        """Adiciona regra"""
        rule = MatchRule(
            id=f"{pattern[:20]}_{len(self.request_rules) + len(self.response_rules)}",
            match_pattern=pattern,
            replace_with=replacement,
            target=target,
            scope=scope,
            enabled=enabled
        )
        
        if target in ('request', 'both'):
            self.request_rules.append(rule)
        if target in ('response', 'both'):
            self.response_rules.append(rule)
        
        return rule
    
    def remove_rule(self, rule_id: str):
        self.request_rules = [r for r in self.request_rules if r.id != rule_id]
        self.response_rules = [r for r in self.response_rules if r.id != rule_id]
    
    def _apply_rule_to_text(self, text, rule: MatchRule) -> str:
        """Aplica uma regra a um texto (path, body, header value)"""
        if not text:
            return text
        
        # Converter bytes para string
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        
        compiled = rule.compile_match()
        replacement = rule.compile_replace()
        result = compiled.sub(replacement, text)
        return result
    
    def process_request(self, request: Dict, host: str = '') -> Dict:
        """Processa request"""
        result = request.copy()
        
        for rule in self.request_rules:
            if not rule.enabled:
                continue
            if rule.scope and rule.scope not in host:
                continue
            
            # Path
            if 'path' in result:
                result['path'] = self._apply_rule_to_text(result['path'], rule)
            
            # Body
            if 'body' in result and result['body']:
                body = result['body'].decode('utf-8', errors='replace') if isinstance(result['body'], bytes) else result['body']
                body = self._apply_rule_to_text(body, rule)
                if isinstance(request.get('body'), bytes):
                    result['body'] = body.encode('utf-8')
                else:
                    result['body'] = body
        
        # Headers
        for key in list(result.get('headers', {}).keys()):
            header_value = result['headers'][key]
            for rule in self.request_rules:
                if not rule.enabled:
                    continue
                if rule.scope and rule.scope not in host:
                    continue
                new_value = self._apply_rule_to_text(header_value, rule)
                if new_value != header_value:
                    result['headers'][key] = new_value
        
        return result
    
    def process_response(self, response: Dict, host: str = '') -> Dict:
        """Processa response"""
        result = response.copy()
        
        for rule in self.response_rules:
            if not rule.enabled:
                continue
            if rule.scope and rule.scope not in host:
                continue
            
            # Body
            if 'body' in result and result['body']:
                body = result['body'].decode('utf-8', errors='replace') if isinstance(result['body'], bytes) else result['body']
                body = self._apply_rule_to_text(body, rule)
                if isinstance(response.get('body'), bytes):
                    result['body'] = body.encode('utf-8')
                else:
                    result['body'] = body
                
                # Atualizar content-length
                if 'headers' in result and 'Content-Length' in result['headers']:
                    result['headers']['Content-Length'] = str(len(body.encode('utf-8')))
        
        # Headers
        for key in list(result.get('headers', {}).keys()):
            header_value = result['headers'][key]
            for rule in self.response_rules:
                if not rule.enabled:
                    continue
                if rule.scope and rule.scope not in host:
                    continue
                new_value = self._apply_rule_to_text(header_value, rule)
                if new_value != header_value:
                    result['headers'][key] = new_value
        
        return result
    
    def list_rules(self) -> List[Dict]:
        rules = []
        for rule in self.request_rules:
            rules.append({'id': rule.id, 'match': rule.match_pattern, 
                         'replace': rule.replace_with, 'target': 'request',
                         'scope': rule.scope, 'enabled': rule.enabled})
        for rule in self.response_rules:
            rules.append({'id': rule.id, 'match': rule.match_pattern,
                         'replace': rule.replace_with, 'target': 'response',
                         'scope': rule.scope, 'enabled': rule.enabled})
        return rules
    
    def clear_rules(self):
        self.request_rules.clear()
        self.response_rules.clear()
    
    def load_rules(self, rules: List[Dict]):
        self.clear_rules()
        for rd in rules:
            self.add_rule(rd['match'], rd['replace'], rd.get('target', 'both'),
                         rd.get('scope', ''), rd.get('enabled', True))


if __name__ == '__main__':
    mr = MatchReplace()
    
    # Test 1: Simple replacement
    mr.add_rule(r'<script[^>]*>.*?</script>', '<!-- REMOVED -->', target='response')
    resp = {'body': b'<html><script>alert(1)</script></html>'}
    result = mr.process_response(resp)
    body_str = result['body'].decode('utf-8') if isinstance(result['body'], bytes) else result['body']
    assert '<!-- REMOVED -->' in body_str, f"Expected removal, got: {body_str}"
    print("Test 1 PASS: Script removal")
    
    # Test 2: Backreference
    mr.add_rule(r'/admin/(.*)', r'/private/\1', target='request', scope='example.com')
    req = {'path': '/admin/settings'}
    result = mr.process_request(req, host='example.com')
    assert result['path'] == '/private/settings', f"Expected /private/settings, got {result['path']}"
    print("Test 2 PASS: Backreference")
    
    # Test 3: Header replacement (pattern matches the full header value)
    mr.add_rule(r'.+', 'X-Removed', target='request', scope='example.com')
    req2 = {'headers': {'X-Custom': 'true', 'Host': 'example.com'}}
    result2 = mr.process_request(req2, host='example.com')
    assert result2['headers']['X-Custom'] == 'X-Removed', f"Expected 'X-Removed', got {result2['headers']['X-Custom']}"
    print("Test 3 PASS: Header replacement")
    
    print("\nAll Match&Replace tests passed!")
