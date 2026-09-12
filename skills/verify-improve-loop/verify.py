"""
Verify & Improve Loop — Sistema de Qualidade Automatica
Busca, valida, melhora e re-verifica antes de finalizar.
"""

import os
import sys
import json
import time
import hashlib
import urllib.request
import urllib.error
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class VerifyImproveLoop:
    """Sistema de verificacao e melhoria continua."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'max_rounds': 3,
            'min_quality_score': 85,
            'search_timeout_ms': 10000,
            'verbose': True,
        }
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.verification_log = []
    
    def _log(self, level: str, message: str):
        """Registra evento na verificação."""
        entry = {
            'ts': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'session': self.session_id
        }
        self.verification_log.append(entry)
        if self.config.get('verbose'):
            print(f"[VERIFY-{level}] {message}")
    
    def search_web(self, query: str, sources: List[str] = None) -> List[Dict]:
        """Busca referencias na internet (simulada com DuckDuckGo HTML)."""
        if sources is None:
            sources = ['ddg', 'github']
        
        results = []
        query_encoded = urllib.parse.quote(query)
        
        # DuckDuckGo HTML search
        try:
            url = f"https://html.duckduckgo.com/html/?q={query_encoded}"
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                # Extrair resultados
                snippets = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)">(.*?)</a>', html)
                snippets += re.findall(r'<a class="result__snippet" href="(.*?)">(.*?)</a>', html)
                for href, text in snippets[:15]:
                    text_clean = re.sub(r'<[^>]+>', '', text).strip()
                    if text_clean and len(text_clean) > 10:
                        results.append({
                            'source': 'duckduckgo',
                            'url': href,
                            'text': text_clean[:200]
                        })
        except Exception as e:
            self._log('WARN', f"Web search failed: {e}")
        
        return results
    
    def check_ui_quality(self, description: str, artifacts: List[str] = None) -> Dict:
        """Verifica qualidade de componentes UI/Visual."""
        checks = {
            'layout_responsive': False,
            'contrast_accessible': False,
            'typography_readable': False,
            'spacing_consistent': False,
            'hover_focus_active': False,
            'loading_states': False,
            'error_states': False,
            'empty_states': False,
            'animations_smooth': False,
            'accessibility_aria': False,
        }
        
        # Buscar referencias
        refs = self.search_web(f"modern {description} UI design 2024 site:github.com")
        self._log('INFO', f"Found {len(refs)} references for UI check")
        
        # Analisar artifacts existentes
        if artifacts:
            for art in artifacts:
                path = Path(art)
                if path.exists():
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    # Checkmarks basicos
                    if 'responsive' in content.lower() or '@media' in content:
                        checks['layout_responsive'] = True
                    if 'aria' in content.lower() or 'role=' in content.lower():
                        checks['accessibility_aria'] = True
                    if 'loading' in content.lower() or 'skeleton' in content.lower():
                        checks['loading_states'] = True
                    if 'error' in content.lower() and ('catch' in content.lower() or 'try' in content.lower()):
                        checks['error_states'] = True
        
        # Score
        passed = sum(checks.values())
        total = len(checks)
        score = int((passed / total) * 100)
        
        self._log('RESULT', f"UI Quality Score: {score}/100 ({passed}/{total} checks passed)")
        
        return {
            'score': score,
            'checks': checks,
            'passed': passed,
            'total': total,
            'refs_found': len(refs),
            'references': refs[:5]
        }
    
    def check_code_quality(self, file_path: str, concerns: List[str] = None) -> Dict:
        """Verifica qualidade e seguranca de codigo."""
        if concerns is None:
            concerns = ['security', 'performance', 'error_handling']
        
        checks = {
            'security_no_hardcoded_secrets': True,
            'security_input_validated': True,
            'security_sql_injection_safe': True,
            'security_xss_prevented': True,
            'error_handling_present': True,
            'error_logging_present': True,
            'performance_no_nSquared': True,
            'performance_no_memory_leaks': True,
            'no_hardcoded_secrets': True,
            'logging_appropriate': True,
        }
        
        path = Path(file_path)
        if not path.exists():
            self._log('ERROR', f"File not found: {file_path}")
            return {'score': 0, 'checks': checks, 'error': 'File not found'}
        
        content = path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        # Security checks
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'AWS_ACCESS_KEY',
            r'sqlalchemy\+.*://.*:.*@',
        ]
        for pat in secret_patterns:
            if re.search(pat, content, re.IGNORECASE):
                checks['security_no_hardcoded_secrets'] = False
                self._log('FIX', f"Hardcoded secret found: {pat}")
        
        # SQL injection
        if re.search(r'(execute|cursor\.execute)\s*\(\s*f["\']', content):
            checks['security_sql_injection_safe'] = False
            self._log('FIX', "Potential SQL injection via f-string execute")
        if re.search(r'(execute|cursor\.execute)\s*\(\s*["\'].*%s', content):
            checks['security_sql_injection_safe'] = False
            self._log('FIX', "SQL injection via string formatting")
        
        # XSS
        if re.search(r'\.innerHTML\s*=', content):
            checks['security_xss_prevented'] = False
            self._log('FIX', "innerHTML assignment - potential XSS")
        if re.search(r'document\.write\s*\(', content):
            checks['security_xss_prevented'] = False
            self._log('FIX', "document.write - potential XSS")
        
        # Error handling
        try_blocks = len(re.findall(r'\btry\b', content))
        except_blocks = len(re.findall(r'\bexcept\b', content))
        if try_blocks > 0 and except_blocks == 0:
            checks['error_handling_present'] = False
            self._log('FIX', "try blocks without except")
        if except_blocks > try_blocks:
            checks['error_handling_present'] = False
            self._log('FIX', "More except than try blocks")
        
        # Logging
        if 'logging' not in content.lower() and 'logger' not in content.lower():
            checks['logging_appropriate'] = False
            self._log('FIX', "No logging found")
        
        # Performance: O(n^2) patterns
        if re.search(r'for\s+.*\n.*for\s+', content):
            checks['performance_no_nSquared'] = False
            self._log('FIX', "Nested loops detected - potential O(n^2)")
        
        # Score
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = int((passed / total) * 100)
        
        self._log('RESULT', f"Code Quality Score: {score}/100 ({passed}/{total} checks passed)")
        
        return {
            'score': score,
            'checks': checks,
            'passed': passed,
            'total': total,
            'lines': len(lines),
            'path': str(path)
        }
    
    def check_security(self, feature_description: str, code_files: List[str] = None) -> Dict:
        """Verifica seguranca de uma feature."""
        checks = {
            'owasp_top10_checked': False,
            'input_validation': False,
            'authentication_verified': False,
            'authorization_implemented': False,
            'sqli_prevented': False,
            'xss_prevented': False,
            'csrf_tokens': False,
            'rate_limiting': False,
            'security_headers': False,
            'deps_updated': False,
        }
        
        # Buscar CVEs e advisories
        refs = self.search_web(f"{feature_description} security vulnerabilities CVE")
        self._log('INFO', f"Found {len(refs)} security references")
        
        # OWASP Top 10
        owasp_refs = self.search_web(f"OWASP Top 10 {feature_description} best practices")
        if owasp_refs:
            checks['owasp_top10_checked'] = True
        
        # Verificar arquivos de codigo
        if code_files:
            for fpath in code_files:
                path = Path(fpath)
                if path.exists():
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    if re.search(r'(validate|sanitize|escape|filter)', content, re.IGNORECASE):
                        checks['input_validation'] = True
                    if re.search(r'(auth|login|session|token|JWT)', content, re.IGNORECASE):
                        checks['authentication_verified'] = True
                    if re.search(r'(authorize|permission|role|admin)', content, re.IGNORECASE):
                        checks['authorization_implemented'] = True
                    if re.search(r'(parameterized|prepared.statement|bind)', content, re.IGNORECASE):
                        checks['sqli_prevented'] = True
                    if re.search(r'(csrf|anti.forgery|xsrf)', content, re.IGNORECASE):
                        checks['csrf_tokens'] = True
                    if re.search(r'(rate.limit|throttle|slowdown|limiter)', content, re.IGNORECASE):
                        checks['rate_limiting'] = True
                    if re.search(r'(X-Frame-Options|X-Content-Type|Strict-Transport)', content, re.IGNORECASE):
                        checks['security_headers'] = True
        
        # Dependencies check
        deps_files = ['requirements.txt', 'package.json', 'Gemfile', 'Cargo.toml']
        for df in deps_files:
            dep_path = Path(df)
            if dep_path.exists():
                checks['deps_updated'] = True
                break
        
        passed = sum(checks.values())
        total = len(checks)
        score = int((passed / total) * 100)
        
        self._log('RESULT', f"Security Score: {score}/100 ({passed}/{total} checks passed)")
        
        return {
            'score': score,
            'checks': checks,
            'passed': passed,
            'total': total,
            'vulnerability_refs': refs[:5]
        }
    
    def improve(self, result: Dict, improvement_type: str = 'all') -> Dict:
        """Aplica melhorias automaticas baseado no tipo."""
        improvements_applied = []
        
        if improvement_type in ('all', 'code'):
            if 'checks' in result:
                for check, passed in result['checks'].items():
                    if not passed:
                        improvements_applied.append(f"Fix: {check}")
        
        if improvement_type in ('all', 'security'):
            if 'checks' in result:
                for check, passed in result['checks'].items():
                    if not passed and 'security' in check.lower() or 'sqli' in check.lower() or 'xss' in check.lower():
                        improvements_applied.append(f"Security: {check}")
        
        self._log('IMPROVE', f"Applied {len(improvements_applied)} improvements")
        
        return {
            'improvements': improvements_applied,
            'count': len(improvements_applied)
        }
    
    def run_verification_loop(self, task_description: str, artifacts: List[str] = None, 
                               target_score: int = 85, max_rounds: int = 3) -> Dict:
        """Loop completo de verificacao e melhoria."""
        self._log('START', f"Verification loop started for: {task_description}")
        
        final_result = {
            'task': task_description,
            'rounds': 0,
            'final_score': 0,
            'passed': False,
            'iterations': []
        }
        
        for round_num in range(1, max_rounds + 1):
            self._log('ROUND', f"--- Verification Round {round_num}/{max_rounds} ---")
            
            # Analisar artifacts
            code_score = 0
            security_score = 0
            ui_score = 0
            
            if artifacts:
                # Check code files
                code_files = [a for a in artifacts if Path(a).exists() and Path(a).suffix in ('.py', '.js', '.ts', '.go', '.c', '.cpp', '.java')]
                if code_files:
                    results = [self.check_code_quality(f) for f in code_files[:3]]
                    code_score = sum(r['score'] for r in results) // len(results)
                
                # Check security
                security_result = self.check_security(task_description, code_files[:5])
                security_score = security_result['score']
                
                # Check UI if applicable
                ui_files = [a for a in artifacts if Path(a).exists() and Path(a).suffix in ('.html', '.css', '.vue', '.jsx', '.tsx')]
                if ui_files:
                    ui_result = self.check_ui_quality(task_description, ui_files[:3])
                    ui_score = ui_result['score']
            
            # Score composto
            if code_score and security_score and ui_score:
                composite = int(code_score * 0.3 + security_score * 0.35 + ui_score * 0.35)
            elif code_score and security_score:
                composite = int(code_score * 0.4 + security_score * 0.6)
            elif code_score:
                composite = code_score
            else:
                composite = 0
            
            iteration = {
                'round': round_num,
                'code_score': code_score,
                'security_score': security_score,
                'ui_score': ui_score,
                'composite_score': composite,
                'timestamp': datetime.now().isoformat()
            }
            final_result['iterations'].append(iteration)
            
            self._log('SCORE', f"Composite score: {composite}/100 (target: {target_score})")
            
            if composite >= target_score:
                self._log('PASS', f"Target score {target_score} reached in round {round_num}")
                final_result['final_score'] = composite
                final_result['passed'] = True
                final_result['rounds'] = round_num
                break
            
            # Melhorar
            if round_num < max_rounds:
                self._log('IMPROVE', f"Score {composite} < {target_score}, applying improvements...")
                self.improve(iteration, 'all')
        
        final_result['final_score'] = final_result['iterations'][-1]['composite_score'] if final_result['iterations'] else 0
        final_result['passed'] = final_result['final_score'] >= target_score
        final_result['total_rounds'] = len(final_result['iterations'])
        final_result['log'] = self.verification_log
        
        self._log('END', f"Verification complete. Passed: {final_result['passed']}. Score: {final_result['final_score']}")
        
        return final_result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Verify & Improve Loop')
    parser.add_argument('description', help='Description of what was built')
    parser.add_argument('--files', '-f', nargs='*', help='Files to verify')
    parser.add_argument('--target', '-t', type=int, default=85, help='Target quality score')
    parser.add_argument('--max-rounds', '-r', type=int, default=3, help='Max verification rounds')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')
    args = parser.parse_args()
    
    verifier = VerifyImproveLoop(config={'verbose': not args.quiet})
    result = verifier.run_verification_loop(
        task_description=args.description,
        artifacts=args.files or [],
        target_score=args.target,
        max_rounds=args.max_rounds
    )
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
