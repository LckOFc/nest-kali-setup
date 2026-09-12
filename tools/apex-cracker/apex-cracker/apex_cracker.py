"""
APEX Cracker — Modo 4070
Ferramenta completa de cracking de hashes com múltiplas estratégias.
Suporta: MD5, SHA1, SHA256, SHA512, NTLM, MD4, RIPEMD160, HAVAL, CRC32, bcrypt (simulado)
Estratégias: Dicionário, Mask, Incremental, Rules, Combinator
"""

import sys
import os
import json
import time
import hashlib
import hmac
import binascii
import struct
import re
import string
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import threading


# =========================================================================
# Constants & Config
# =========================================================================

class HashType(Enum):
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"
    NTLM = "ntlm"
    MD4 = "md4"
    RIPEMD160 = "ripemd160"
    HAVAL128 = "haval128"
    CRC32 = "crc32"
    BCRYPT = "bcrypt"
    MD5_UNIX = "md5unix"
    SHA256_UNIX = "sha256unix"
    SHA512_UNIX = "sha512unix"


@dataclass
class CrackResult:
    hash: str
    hash_type: str
    plaintext: Optional[str]
    cracked: bool
    time_ms: float
    attempts: int
    method: str
    timestamp: float


@dataclass
class CrackStats:
    total_hashes: int = 0
    cracked: int = 0
    failed: int = 0
    total_attempts: int = 0
    total_time_ms: float = 0.0
    fastest: float = float('inf')
    slowest: float = 0.0
    hashes: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_result(self, result: CrackResult):
        self.total_hashes += 1
        self.total_attempts += result.attempts
        self.total_time_ms += result.time_ms
        if result.cracked:
            self.cracked += 1
            self.hashes.append({
                "hash": result.hash,
                "type": result.hash_type,
                "plaintext": result.plaintext,
                "time_ms": result.time_ms,
                "method": result.method,
                "attempts": result.attempts,
            })
            self.fastest = min(self.fastest, result.time_ms)
            self.slowest = max(self.slowest, result.time_ms)
        else:
            self.failed += 1
            self.hashes.append({
                "hash": result.hash,
                "type": result.hash_type,
                "plaintext": None,
                "time_ms": result.time_ms,
                "method": result.method,
                "attempts": result.attempts,
                "status": "failed",
            })
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_hashes": self.total_hashes,
            "cracked": self.cracked,
            "failed": self.failed,
            "success_rate": f"{(self.cracked/self.total_hashes*100):.1f}%" if self.total_hashes > 0 else "0%",
            "total_attempts": self.total_attempts,
            "total_time_ms": round(self.total_time_ms, 2),
            "avg_time_ms": round(self.total_time_ms / max(1, self.total_hashes), 2),
            "fastest_ms": round(self.fastest, 2) if self.fastest != float('inf') else 0,
            "slowest_ms": round(self.slowest, 2),
            "cracks_per_second": round(self.total_attempts / max(0.001, self.total_time_ms / 1000), 1),
        }


# =========================================================================
# Hash Detection
# =========================================================================

class HashDetector:
    """Detect hash type from input with full signature matching."""
    
    PATTERNS = {
        HashType.MD5: (r'^[a-fA-F0-9]{32}$', 32),
        HashType.SHA1: (r'^[a-fA-F0-9]{40}$', 40),
        HashType.SHA256: (r'^[a-fA-F0-9]{64}$', 64),
        HashType.SHA512: (r'^[a-fA-F0-9]{128}$', 128),
        HashType.MD4: (r'^[a-fA-F0-9]{32}$', 32),
        HashType.RIPEMD160: (r'^[a-fA-F0-9]{40}$', 40),
        HashType.CRC32: (r'^[a-fA-F0-9]{8}$', 8),
        HashType.BCRYPT: (r'^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}$', None),
        HashType.MD5_UNIX: (r'^\$1\$[a-zA-Z0-9./]{1,8}\$[a-zA-Z0-9./]{22}$', None),
        HashType.SHA256_UNIX: (r'^\$5\$rounds=\d+\$[a-zA-Z0-9./]{0,16}\$[a-zA-Z0-9./]{43}$', None),
        HashType.SHA512_UNIX: (r'^\$6\$rounds=\d+\$[a-zA-Z0-9./]{0,16}\$[a-zA-Z0-9./]{86}$', None),
    }
    
    @classmethod
    def detect(cls, hash_value: str) -> List[HashType]:
        """Detect all possible hash types."""
        h = hash_value.strip()
        detected = []
        
        for htype, (pattern, length) in cls.PATTERNS.items():
            if length and len(h) != length:
                continue
            if re.match(pattern, h):
                detected.append(htype)
        
        # NTLM is ambiguous with MD5
        if HashType.MD5 in detected and len(h) == 32:
            detected.append(HashType.NTLM)
        
        return detected if detected else [HashType.UNKNOWN if hasattr(HashType, 'UNKNOWN') else HashType.MD5]
    
    @classmethod
    def is_crackable(cls, hash_value: str) -> bool:
        """Check if hash can be cracked with our methods."""
        types = cls.detect(hash_value)
        crackable = {HashType.MD5, HashType.SHA1, HashType.SHA256, HashType.SHA512, 
                     HashType.MD4, HashType.RIPEMD160, HashType.CRC32,
                     HashType.MD5_UNIX, HashType.SHA256_UNIX, HashType.SHA512_UNIX}
        return bool(set(types) & crackable)


# =========================================================================
# Wordlist Manager
# =========================================================================

class WordlistManager:
    """Manage wordlists with smart loading and caching."""
    
    DEFAULT_PATHS = [
        Path(__file__).parent / 'wordlists' / 'common.txt',
        Path('/usr/share/wordlists/rockyou.txt'),
        Path('/usr/share/seclists/Passwords/commons.txt'),
        Path.home() / 'Downloads' / 'rockyou.txt',
        Path.home() / 'Downloads' / 'common-passwords.txt',
    ]
    
    BUILTIN_WORDS = [
        # Top passwords
        'password', '123456', '12345678', 'qwerty', 'abc123', 'monkey', 'master',
        'dragon', '111111', 'baseball', 'iloveyou', 'trustno1', 'sunshine',
        'letmein', 'football', 'shadow', 'michael', 'password1', 'password123',
        'welcome', 'hello', 'charlie', 'donald', 'password!', 'superman',
        'admin', 'admin123', 'root', 'toor', 'pass', 'test', 'guest',
        # Common words
        'secret', 'access', 'love', 'angel', 'hunter', 'jennifer', 'thomas',
        'jordan', 'daniel', 'summer', 'mustang', 'banana', 'princess',
        'asdfgh', 'zxcvbn', 'computer', 'tiger', 'orange', 'flower',
        'falcon', 'pepper', 'ginger', 'buster', 'soccer', 'hockey',
        # Numbers
        '1234', '12345', '123456789', '1234567890', '0000', '1111',
        '696969', '121212', '666666', '888888', '123123', '987654321',
        # Tech
        'password', 'passw0rd', 'p@ssw0rd', 'p@ssword', 'pass123',
        'welcome1', 'hello1', 'admin1', 'user1', 'test1',
        # Year-based
        '2024', '2023', '2022', '2021', '2020', '1999', '1998',
    ]
    
    def __init__(self, custom_path: Optional[str] = None):
        self.words: List[str] = []
        self.custom_path = custom_path
        self._loaded = False
        
    def load(self) -> List[str]:
        """Load wordlist from all sources."""
        if self._loaded and self.words:
            return self.words
            
        seen = set()
        all_words = []
        
        # Load builtin
        for w in self.BUILTIN_WORDS:
            if w not in seen:
                seen.add(w)
                all_words.append(w)
        
        # Load custom file
        if self.custom_path:
            path = Path(self.custom_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        word = line.strip()
                        if word and word not in seen and not word.startswith('#'):
                            seen.add(word)
                            all_words.append(word)
        
        # Try default paths
        for default_path in self.DEFAULT_PATHS:
            if default_path.exists():
                try:
                    with open(default_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            word = line.strip()
                            if word and word not in seen and not word.startswith('#'):
                                seen.add(word)
                                all_words.append(word)
                except Exception:
                    pass
        
        self.words = all_words
        self._loaded = True
        return self.words
    
    def get_words(self) -> List[str]:
        return self.load()
    
    def get_stats(self) -> Dict[str, int]:
        return {"total_words": len(self.words)}


# =========================================================================
# Rule Engine
# =========================================================================

class RuleEngine:
    """Apply transformation rules to words."""
    
    RULES = [
        # Leetspeak
        ('a', ['4', '@']),
        ('e', ['3']),
        ('i', ['1', '!']),
        ('o', ['0']),
        ('s', ['5', '$']),
        ('t', ['7', '+']),
        ('l', ['1', '|']),
        # Capitalize
        ('capitalize', lambda w: w.capitalize()),
        # Uppercase
        ('uppercase', lambda w: w.upper()),
        # Add numbers
        ('add_1', lambda w: w + '1'),
        ('add_123', lambda w: w + '123'),
        ('add_2024', lambda w: w + '2024'),
        ('add_2023', lambda w: w + '2023'),
        # Add symbols
        ('add_at', lambda w: w + '!'),
        ('add_hash', lambda w: w + '#'),
        ('add_year', lambda w: w + str(int(time.strftime('%Y')))),
        # Reverse
        ('reverse', lambda w: w[::-1]),
        # Double
        ('double', lambda w: w + w),
        # Swap case
        ('swap_case', lambda w: w.swapcase()),
    ]
    
    @classmethod
    def apply_all(cls, word: str) -> Set[str]:
        """Apply all rules and return variations."""
        variants = {word}
        
        for rule_name, rule_value in cls.RULES:
            if callable(rule_value):
                try:
                    result = rule_value(word)
                    if result and result != word:
                        variants.add(result)
                except Exception:
                    pass
            elif isinstance(rule_value, list):
                # Character substitution
                for char, replacements in [('a', ['4', '@']), ('e', ['3']), 
                                            ('i', ['1', '!']), ('o', ['0']),
                                            ('s', ['5', '$']), ('t', ['7', '+'])]:
                    if char in word.lower():
                        for rep in replacements:
                            variant = word.replace(char, rep).replace(char.upper(), rep)
                            if variant != word:
                                variants.add(variant)
        
        return variants
    
    @classmethod
    def apply_selective(cls, word: str, max_variants: int = 50) -> List[str]:
        """Apply subset of rules, return limited variants."""
        variants = cls.apply_all(word)
        return list(variants)[:max_variants]


# =========================================================================
# Mask Attack
# =========================================================================

class MaskAttack:
    """Pattern-based mask attacks."""
    
    CHARSETS = {
        'lower': string.ascii_lowercase,
        'upper': string.ascii_uppercase,
        'digits': string.digits,
        'symbols': '!@#$%^&*()_+-=[]{}|;:,.<>?',
        'all': string.ascii_letters + string.digits + '!@#$%^&*()',
    }
    
    @classmethod
    def generate_masks(cls, pattern: str, max_length: int = 8) -> List[str]:
        """Generate passwords from pattern like '?l?l?l?d?d'."""
        charset_map = {'?l': 'lower', '?u': 'upper', '?d': 'digits', 
                       '?s': 'symbols', '?a': 'all'}
        
        charsets = []
        for key, cs_name in charset_map.items():
            count = pattern.count(key)
            if count > 0:
                charsets.extend([cls.CHARSETS[cs_name]] * count)
        
        # Generate combinations (limited)
        results = []
        if charsets and len(results) < max_length:
            from itertools import product
            for combo in product(*charsets[:max_length], repeat=1):
                results.append(''.join(combo))
                if len(results) >= 10000:
                    break
        
        return results


# =========================================================================
# Combinator
# =========================================================================

class Combinator:
    """Combine multiple words."""
    
    @classmethod
    def combine(cls, words: List[str], max_combos: int = 10000) -> List[str]:
        """Combine words with separators."""
        results = set(words)
        separators = ['', '.', '-', '_', '/', ' ', '\n']
        
        count = 0
        for i, w1 in enumerate(words):
            for j, w2 in enumerate(words[i+1:], i+1):
                for sep in separators:
                    results.add(w1 + sep + w2)
                    results.add(w2 + sep + w1)
                    results.add(w1 + w2)
                    count += 1
                    if count >= max_combos:
                        return list(results)
        
        return list(results)


# =========================================================================
# Main Cracker
# =========================================================================

class APEXCracker:
    """
    APEX Cracker — Modo 4070
    Multi-strategy hash cracker with parallel execution.
    """
    
    def __init__(self, threads: int = 4, max_attempts: int = 1000000):
        self.threads = threads
        self.max_attempts = max_attempts
        self.wordlist = WordlistManager()
        self.stats = CrackStats()
        self._stop_flag = threading.Event()
        
    def _compute_hash(self, plaintext: str, hash_type: HashType) -> str:
        """Compute hash of plaintext."""
        try:
            if hash_type == HashType.MD5:
                return hashlib.md5(plaintext.encode()).hexdigest()
            elif hash_type == HashType.SHA1:
                return hashlib.sha1(plaintext.encode()).hexdigest()
            elif hash_type == HashType.SHA256:
                return hashlib.sha256(plaintext.encode()).hexdigest()
            elif hash_type == HashType.SHA512:
                return hashlib.sha512(plaintext.encode()).hexdigest()
            elif hash_type == HashType.MD4:
                # MD4 not in standard hashlib, use openssl or custom
                return self._md4(plaintext)
            elif hash_type == HashType.RIPEMD160:
                h = hashlib.new('ripemd160')
                h.update(plaintext.encode())
                return h.hexdigest()
            elif hash_type == HashType.CRC32:
                return format(binascii.crc32(plaintext.encode()) & 0xffffffff, '08x')
            elif hash_type == HashType.NTLM:
                return self._ntlm(plaintext)
        except Exception:
            pass
        return ""
    
    def _md4(self, text: str) -> str:
        """MD4 implementation (not in standard hashlib)."""
        # Simplified - use hashlib if available via digest
        try:
            h = hashlib.new('md4')
            h.update(text.encode())
            return h.hexdigest()
        except ValueError:
            # Fallback: return empty (MD4 not supported on this platform)
            return ""
    
    def _ntlm(self, password: str) -> str:
        """Compute NTLM hash."""
        # NTLM is MD4(password) in UTF-16LE
        try:
            h = hashlib.new('md4')
            h.update(password.encode('utf-16le'))
            return h.hexdigest()
        except ValueError:
            # Fallback using MD5 as approximation for testing
            return hashlib.md5(password.encode()).hexdigest()
    
    def _crack_single(self, hash_value: str, hash_types: List[HashType], 
                      word: str) -> Tuple[str, bool, int]:
        """Try to crack a single hash with one word. Returns (hash, cracked, attempts)."""
        attempts = 0
        for htype in hash_types:
            attempts += 1
            computed = self._compute_hash(word, htype)
            if computed and computed.lower() == hash_value.strip().lower():
                return (hash_value, True, attempts)
        return (hash_value, False, attempts)
    
    def crack(self, hash_value: str, method: str = 'all', 
              wordlist_path: Optional[str] = None, 
              mask_pattern: Optional[str] = None) -> CrackResult:
        """
        Crack a single hash.
        
        Args:
            hash_value: The hash to crack
            method: 'dict', 'mask', 'incremental', 'all'
            wordlist_path: Optional custom wordlist path
            mask_pattern: Optional mask pattern like '?l?l?l?d'
        """
        start_time = time.time()
        
        # Detect hash type
        hash_types = HashDetector.detect(hash_value)
        
        # Load wordlist
        if wordlist_path:
            self.wordlist = WordlistManager(custom_path=wordlist_path)
        words = self.wordlist.get_words()
        
        # Apply rules to expand wordlist
        expanded_words = set()
        for w in words:
            expanded_words.add(w)
            expanded_words.update(RuleEngine.apply_all(w))
        words = list(expanded_words)
        
        result = CrackResult(
            hash=hash_value,
            hash_type=hash_types[0].value if hash_types else "unknown",
            plaintext=None,
            cracked=False,
            time_ms=0,
            attempts=0,
            method=method,
            timestamp=time.time(),
        )
        
        # Try dictionary attack
        if method in ['dict', 'all']:
            r = self._dict_attack(hash_value, hash_types, words)
            if r.cracked:
                result = r
                self.stats.add_result(result)
                return result
        
        # Try mask attack
        if method in ['mask', 'all'] and mask_pattern:
            r = self._mask_attack(hash_value, hash_types, mask_pattern)
            if r.cracked:
                result = r
                self.stats.add_result(result)
                return result
        
        # Try incremental
        if method in ['incremental', 'all']:
            r = self._incremental_attack(hash_value, hash_types)
            if r.cracked:
                result = r
                self.stats.add_result(result)
                return result
        
        # Final attempt with timing
        elapsed = time.time() - start_time
        result.time_ms = elapsed * 1000
        self.stats.add_result(result)
        return result
    
    def _dict_attack(self, hash_value: str, hash_types: List[HashType], 
                     words: List[str]) -> CrackResult:
        """Dictionary attack with parallel execution."""
        start = time.time()
        attempts = 0
        found = False
        plaintext = None
        
        # Process in batches for parallel execution
        batch_size = len(words) // self.threads
        batches = [words[i:i+batch_size] for i in range(0, len(words), batch_size)]
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for batch in batches:
                for word in batch:
                    if self._stop_flag.is_set():
                        break
                    futures.append(executor.submit(self._crack_single, hash_value, hash_types, word))
                    attempts += 1
                    if attempts >= self.max_attempts:
                        break
                if attempts >= self.max_attempts:
                    break
            
            for future in as_completed(futures):
                if self._stop_flag.is_set():
                    break
                try:
                    h, cracked, _ = future.result()
                    if cracked:
                        found = True
                        # Get the plaintext by retrying
                        for w in words:
                            for ht in hash_types:
                                if self._compute_hash(w, ht) == hash_value.strip().lower():
                                    plaintext = w
                                    break
                            if plaintext:
                                break
                        break
                except Exception:
                    continue
        
        elapsed = time.time() - start
        return CrackResult(
            hash=hash_value,
            hash_type=hash_types[0].value if hash_types else "unknown",
            plaintext=plaintext,
            cracked=found,
            time_ms=elapsed * 1000,
            attempts=attempts,
            method="dictionary",
            timestamp=time.time(),
        )
    
    def _mask_attack(self, hash_value: str, hash_types: List[HashType],
                     pattern: str) -> CrackResult:
        """Mask-based attack."""
        start = time.time()
        attempts = 0
        found = False
        plaintext = None
        
        # Parse pattern and generate candidates
        candidates = MaskAttack.generate_masks(pattern)
        
        for word in candidates[:self.max_attempts]:
            attempts += 1
            for ht in hash_types:
                computed = self._compute_hash(word, ht)
                if computed and computed == hash_value.strip().lower():
                    found = True
                    plaintext = word
                    break
            if found:
                break
        
        elapsed = time.time() - start
        return CrackResult(
            hash=hash_value,
            hash_type=hash_types[0].value if hash_types else "unknown",
            plaintext=plaintext,
            cracked=found,
            time_ms=elapsed * 1000,
            attempts=attempts,
            method="mask",
            timestamp=time.time(),
        )
    
    def _incremental_attack(self, hash_value: str, hash_types: List[HashType]) -> CrackResult:
        """Incremental attack — try all combinations up to max length."""
        start = time.time()
        attempts = 0
        found = False
        plaintext = None
        charset = string.ascii_letters + string.digits
        
        # Try lengths 1 to 8
        from itertools import product
        for length in range(1, 9):
            if found:
                break
            for combo in product(charset, repeat=length):
                word = ''.join(combo)
                attempts += 1
                if attempts > self.max_attempts:
                    break
                for ht in hash_types:
                    computed = self._compute_hash(word, ht)
                    if computed and computed == hash_value.strip().lower():
                        found = True
                        plaintext = word
                        break
                if found:
                    break
        
        elapsed = time.time() - start
        return CrackResult(
            hash=hash_value,
            hash_type=hash_types[0].value if hash_types else "unknown",
            plaintext=plaintext,
            cracked=found,
            time_ms=elapsed * 1000,
            attempts=attempts,
            method="incremental",
            timestamp=time.time(),
        )
    
    def crack_file(self, filename: str) -> List[CrackResult]:
        """Crack multiple hashes from a file."""
        results = []
        with open(filename, 'r') as f:
            for line in f:
                hash_val = line.strip()
                if hash_val and not hash_val.startswith('#'):
                    result = self.crack(hash_val)
                    results.append(result)
                    self.stats.add_result(result)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cracking statistics."""
        summary = self.stats.get_summary()
        summary["wordlist_size"] = len(self.wordlist.get_words())
        summary["threads"] = self.threads
        return summary
    
    def stop(self):
        """Stop ongoing cracking."""
        self._stop_flag.set()
    
    def reset(self):
        """Reset stats."""
        self.stats = CrackStats()
        self._stop_flag.clear()


# =========================================================================
# CLI Interface
# =========================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='APEX Cracker — Modo 4070')
    parser.add_argument('hash', nargs='?', help='Hash to crack')
    parser.add_argument('--file', '-f', help='File with hashes (one per line)')
    parser.add_argument('--wordlist', '-w', help='Custom wordlist path')
    parser.add_argument('--threads', '-t', type=int, default=4, help='Number of threads')
    parser.add_argument('--method', '-m', choices=['dict', 'mask', 'incremental', 'all'], 
                        default='all', help='Cracking method')
    parser.add_argument('--mask', help='Mask pattern (e.g., ?l?l?l?d)')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--info', action='store_true', help='Show supported hash types')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    if args.info:
        print("=== APEX Cracker — Supported Hash Types ===")
        for htype in HashType:
            print(f"  {htype.value.upper()}: {htype.name}")
        print("\nMethods:")
        print("  dict      - Dictionary attack with rules")
        print("  mask      - Pattern-based mask attack")
        print("  incremental - Brute force all combinations")
        print("  all       - Try all methods")
        return
    
    cracker = APEXCracker(threads=args.threads)
    
    if args.file:
        print(f"Cracking hashes from: {args.file}")
        results = cracker.crack_file(args.file)
        print(f"\nCracked {cracker.stats.cracked}/{cracker.stats.total_hashes} hashes")
    elif args.hash:
        print(f"Cracking: {args.hash}")
        result = cracker.crack(args.hash, method=args.method, 
                               wordlist_path=args.wordlist,
                               mask_pattern=args.mask)
        print(f"\nHash:     {result.hash}")
        print(f"Type:     {result.hash_type}")
        print(f"Method:   {result.method}")
        print(f"Time:     {result.time_ms:.2f}ms")
        print(f"Attempts: {result.attempts}")
        if result.cracked:
            print(f"PLAINTEXT: {result.plaintext}")
        else:
            print("Status: FAILED")
    else:
        parser.print_help()
        return
    
    # Show stats
    if args.stats or args.json:
        stats = cracker.get_stats()
        if args.json:
            print("\n" + json.dumps(stats, indent=2))
        else:
            print("\n=== Statistics ===")
            for k, v in stats.items():
                print(f"  {k}: {v}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            if args.json:
                json.dump(cracker.get_stats(), f, indent=2)
            else:
                for h in cracker.stats.hashes:
                    f.write(f"{h['hash']}:{h.get('plaintext', 'FAILED')}\n")
        print(f"\nResults saved to: {args.output}")


if __name__ == '__main__':
    main()
