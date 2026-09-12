"""
CustomBurp v2 - Comparer
Compare two HTTP responses side by side
"""

import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger('custom_burp.comparer')


class Comparer:
    """Response comparison tool"""
    
    def __init__(self):
        pass
    
    def compare(self, left: Dict, right: Dict) -> Dict:
        """Compare two responses"""
        differences = []
        
        # Compare status codes
        left_status = left.get('status_code', 0)
        right_status = right.get('status_code', 0)
        if left_status != right_status:
            differences.append({
                'field': 'status_code',
                'left': left_status,
                'right': right_status,
                'type': 'status'
            })
        
        # Compare headers
        left_headers = left.get('headers', {})
        right_headers = right.get('headers', {})
        
        all_header_keys = set(list(left_headers.keys()) + list(right_headers.keys()))
        for key in all_header_keys:
            l_val = left_headers.get(key, '<missing>')
            r_val = right_headers.get(key, '<missing>')
            if l_val != r_val:
                differences.append({
                    'field': f'header:{key}',
                    'left': l_val,
                    'right': r_val,
                    'type': 'header'
                })
        
        # Compare bodies
        left_body = left.get('body', '')
        right_body = right.get('body', '')
        
        if left_body != right_body:
            # Try JSON comparison
            try:
                left_json = json.loads(left_body) if left_body else {}
                right_json = json.loads(right_body) if right_body else {}
                json_diffs = self._compare_json(left_json, right_json, '')
                differences.extend(json_diffs)
            except (json.JSONDecodeError, TypeError):
                # Plain text comparison
                differences.append({
                    'field': 'body',
                    'left_length': len(left_body),
                    'right_length': len(right_body),
                    'type': 'body'
                })
        
        # Content length diff
        left_len = left.get('content_length', len(left_body))
        right_len = right.get('content_length', len(right_body))
        if left_len != right_len:
            differences.append({
                'field': 'content_length',
                'left': left_len,
                'right': right_len,
                'type': 'length'
            })
        
        return {
            'differences': differences,
            'summary': {
                'total_diffs': len(differences),
                'status_diff': left_status != right_status,
                'header_diffs': len([d for d in differences if d.get('type') == 'header']),
                'body_diffs': len([d for d in differences if d.get('type') == 'body' or d.get('type') == 'json']),
                'length_diff': left_len != right_len,
            }
        }
    
    def _compare_json(self, left, right, path: str, depth: int = 0) -> List[Dict]:
        """Recursively compare JSON structures"""
        diffs = []
        if depth > 10:  # Prevent infinite recursion
            return diffs
        
        if isinstance(left, dict) and isinstance(right, dict):
            all_keys = set(list(left.keys()) + list(right.keys()))
            for key in all_keys:
                new_path = f"{path}.{key}" if path else key
                if key not in left:
                    diffs.append({'field': new_path, 'left': '<missing>', 'right': right[key], 'type': 'json'})
                elif key not in right:
                    diffs.append({'field': new_path, 'left': left[key], 'right': '<missing>', 'type': 'json'})
                else:
                    diffs.extend(self._compare_json(left[key], right[key], new_path, depth + 1))
        elif left != right:
            diffs.append({'field': path, 'left': left, 'right': right, 'type': 'json'})
        
        return diffs
    
    def generate_diff(self, left_text: str, right_text: str) -> str:
        """Generate a human-readable diff"""
        left_lines = left_text.split('\n')
        right_lines = right_text.split('\n')
        
        max_len = max(len(left_lines), len(right_lines))
        result = []
        
        for i in range(max_len):
            l = left_lines[i] if i < len(left_lines) else ''
            r = right_lines[i] if i < len(right_lines) else ''
            
            if l == r:
                result.append(f"  {l}")
            else:
                result.append(f"- {l}")
                result.append(f"+ {r}")
        
        return '\n'.join(result)
