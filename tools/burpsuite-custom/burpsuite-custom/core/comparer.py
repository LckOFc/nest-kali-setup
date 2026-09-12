"""
CustomBurp - Comparer
Diff visual entre duas respostas HTTP
"""

import difflib
import html
from typing import Dict, List, Tuple


class Comparer:
    """Comparador visual de requests/respostas HTTP"""
    
    def __init__(self):
        self.comparisons = []
    
    def compare(
        self,
        left: Dict,
        right: Dict,
        mode: str = 'response'
    ) -> Dict:
        """
        Compara dois items (requests ou responses)
        
        Args:
            left: Primeiro item {status_code, headers, body, ...}
            right: Segundo item {status_code, headers, body, ...}
            mode: 'response' ou 'request'
        
        Returns:
            Dict com diff detalhado
        """
        result = {
            'left': left,
            'right': right,
            'differences': [],
            'summary': {},
            'html_diff': ''
        }
        
        # Comparar status code
        left_status = left.get('status_code', 0)
        right_status = right.get('status_code', 0)
        if left_status != right_status:
            result['differences'].append({
                'field': 'status_code',
                'left': left_status,
                'right': right_status,
                'type': 'status'
            })
        
        # Comparar headers
        left_headers = left.get('headers', {})
        right_headers = right.get('headers', {})
        header_diffs = self._diff_headers(left_headers, right_headers)
        result['differences'].extend(header_diffs)
        
        # Comparar body
        left_body = left.get('body', '')
        right_body = right.get('body', '')
        body_diff = self._diff_body(left_body, right_body)
        result['body_diff'] = body_diff
        
        # Resumo
        result['summary'] = {
            'total_diffs': len(result['differences']) + (1 if body_diff['has_diff'] else 0),
            'status_diff': left_status != right_status,
            'header_diffs': len(header_diffs),
            'body_diffs': body_diff['lines_changed'],
            'left_length': len(left_body) if isinstance(left_body, str) else len(left_body or b''),
            'right_length': len(right_body) if isinstance(right_body, str) else len(right_body or b''),
            'length_diff': abs(len(left_body or '') - len(right_body or ''))
        }
        
        # Gerar HTML diff
        result['html_diff'] = self._generate_html_diff(body_diff, header_diffs)
        
        self.comparisons.append(result)
        return result
    
    def _diff_headers(
        self, left: Dict, right: Dict
    ) -> List[Dict]:
        """Compara headers e retorna diferencas"""
        diffs = []
        
        all_keys = set(left.keys()) | set(right.keys())
        for key in sorted(all_keys):
            lval = left.get(key, '<missing>')
            rval = right.get(key, '<missing>')
            
            if lval != rval:
                diffs.append({
                    'field': f'header:{key}',
                    'left': lval,
                    'right': rval,
                    'type': 'header'
                })
        
        return diffs
    
    def _diff_body(self, left: str, right: str) -> Dict:
        """Compara bodies e retorna diff"""
        if not left and not right:
            return {'has_diff': False, 'lines_changed': 0, 'unified_diff': ''}
        
        left_lines = left.split('\n') if isinstance(left, str) else left.decode('utf-8', errors='replace').split('\n')
        right_lines = right.split('\n') if isinstance(right, str) else right.decode('utf-8', errors='replace').split('\n')
        
        # Unified diff
        diff = list(difflib.unified_diff(
            left_lines, right_lines,
            fromfile='left', tofile='right',
            lineterm=''
        ))
        
        # Contar linhas alteradas
        changed = sum(1 for line in diff if line.startswith('+') or line.startswith('-'))
        
        return {
            'has_diff': len(diff) > 3,  # 3 linhas de cabecalho + conteudo
            'lines_changed': changed,
            'unified_diff': '\n'.join(diff[:200]),  # Limitar tamanho
            'left_lines': len(left_lines),
            'right_lines': len(right_lines)
        }
    
    def _generate_html_diff(
        self, body_diff: Dict, header_diffs: List[Dict]
    ) -> str:
        """Gera HTML para exibicao do diff"""
        html_parts = []
        
        # Header diffs
        if header_diffs:
            html_parts.append('<div class="diff-section">')
            html_parts.append('<h4>Diferencas nos Headers</h4>')
            html_parts.append('<table>')
            html_parts.append('<tr><th>Header</th><th>Left</th><th>Right</th></tr>')
            for d in header_diffs[:20]:
                html_parts.append(f'<tr>')
                html_parts.append(f'<td>{html.escape(d["field"])}</td>')
                html_parts.append(f'<td class="diff-left">{html.escape(str(d["left"])[:100])}</td>')
                html_parts.append(f'<td class="diff-right">{html.escape(str(d["right"])[:100])}</td>')
                html_parts.append(f'</tr>')
            html_parts.append('</table>')
            html_parts.append('</div>')
        
        # Body diff
        if body_diff['has_diff']:
            html_parts.append('<div class="diff-section">')
            html_parts.append('<h4>Diferencas no Body</h4>')
            html_parts.append(f'<p>Linhas alteradas: {body_diff["lines_changed"]} | '
                            f'Left: {body_diff["left_lines"]}L | Right: {body_diff["right_lines"]}L</p>')
            
            # Linhas lado a lado
            left_lines = body_diff.get('left_lines_list', [])
            right_lines = body_diff.get('right_lines_list', [])
            
            html_parts.append('<div class="diff-body">')
            max_lines = max(len(left_lines), len(right_lines), 50)
            for i in range(min(max_lines, 100)):
                ll = html.escape(left_lines[i]) if i < len(left_lines) else ''
                rl = html.escape(right_lines[i]) if i < len(right_lines) else ''
                
                if ll != rl:
                    html_parts.append(f'<div class="diff-line">')
                    html_parts.append(f'<span class="line-num">{i+1}</span>')
                    html_parts.append(f'<span class="line-left diff-left">{ll or " "}</span>')
                    html_parts.append(f'<span class="line-right diff-right">{rl or " "}</span>')
                    html_parts.append(f'</div>')
                else:
                    html_parts.append(f'<div class="diff-line">')
                    html_parts.append(f'<span class="line-num">{i+1}</span>')
                    html_parts.append(f'<span class="line-left">{ll}</span>')
                    html_parts.append(f'<span class="line-right">{rl}</span>')
                    html_parts.append(f'</div>')
            html_parts.append('</div>')
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def save_comparison(self, name: str, left_id: str, right_id: str, result: Dict):
        """Salva comparacao no historico"""
        comparison = {
            'name': name,
            'left_id': left_id,
            'right_id': right_id,
            'result': result,
            'saved_at': __import__('time').time()
        }
        self.comparisons.append(comparison)
        return comparison


if __name__ == '__main__':
    comp = Comparer()
    
    left_resp = {
        'status_code': 200,
        'headers': {'Content-Type': 'text/html', 'Server': 'Apache'},
        'body': '<html><body>Hello World</body></html>'
    }
    
    right_resp = {
        'status_code': 200,
        'headers': {'Content-Type': 'text/html', 'Server': 'nginx'},
        'body': '<html><body>Hello Modified World</body></html>'
    }
    
    result = comp.compare(left_resp, right_resp)
    print(f"Summary: {result['summary']}")
    print(f"Differences: {len(result['differences'])}")
    print(f"Body has diff: {result['body_diff']['has_diff']}")
    print(f"HTML diff length: {len(result['html_diff'])}")
    print("Comparer OK!")
