"""
Password Cracker v1 — Diccionario + Regras + Detecção de Hash
Supporta: MD5, SHA1, SHA256, SHA512, NTLM, bcrypt (simulado), crc32
"""

import sys
import os
import json
import time
import hashlib
import hmac
import logging
import hashlib
import base64
import binascii
import struct
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter

log_dir = Path(__file__).parent / 'log'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'cracker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cracker')


# =========================================================================
# Hash Detection
# =========================================================================

class HashDetector:
    """Detect hash type from input"""
    
    PATTERNS = {
        'MD5': r'^[a-fA-F0-9]{32}$',
        'SHA1': r'^[a-fA-F0-9]{40}$',
        'SHA256': r'^[a-fA-F0-9]{64}$',
        'SHA512': r'^[a-fA-F0-9]{128}$',
        'NTLM': r'^[a-fA-F0-9]{32}$',  # Same as MD5 but context-dependent
        'CRC32': r'^[a-fA-F0-9]{8}$',
        'MySQL': r'^[a-fA-F0-9]{40}$',  # MySQL PASSWORD()
        'bcrypt': r'^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}$',
        'md5unix': r'^\$1\$[a-zA-Z0-9./]{0,8}\$[a-zA-Z0-9./]{22}$',
        'sha256unix': r'^\$5\$[a-zA-Z0-9./]{0,16}\$[a-zA-Z0-9./]{43}$',
        'sha512unix': r'^\$6\$[a-zA-Z0-9./]{0,16}\$[a-zA-Z0-9./]{86}$',
    }
    
    @classmethod
    def detect(cls, hash_value: str) -> List[str]:
        """Detect hash type(s)"""
        h = hash_value.strip()
        types = []
        
        for name, pattern in cls.PATTERNS.items():
            import re
            if re.match(pattern, h):
                types.append(name)
        
        # NTLM vs MD5 ambiguity — return both
        if 'MD5' in types and len(h) == 32:
            if 'NTLM' not in types:
                types.append('NTLM')
        
        return types if types else ['Unknown']
    
    @classmethod
    def is_crackable(cls, hash_value: str) -> bool:
        """Check if hash can be cracked with our methods"""
        types = cls.detect(hash_value)
        crackable = {'MD5', 'SHA1', 'SHA256', 'SHA512', 'crc32', 'md5unix', 'sha256unix', 'sha512unix'}
        return bool(set(types) & crackable)


# =========================================================================
# Wordlist Manager
# =========================================================================

class WordlistManager:
    """Manage wordlists for password cracking"""
    
    DEFAULT_PATHS = [
        Path(__file__).parent / 'wordlists' / 'common.txt',
        Path('/usr/share/wordlists/rockyou.txt'),
        Path('/usr/share/seclists/Passwords/commons.txt'),
        Path.home() / 'wordlists' / 'rockyou.txt',
    ]
    
    BUILTIN_WORDS = [
        'password', '123456', '12345678', 'qwerty', 'abc123', 'monkey', 'master',
        'dragon', '111111', 'baseball', 'iloveyou', 'trustno1', 'sunshine',
        'letmein', 'football', 'shadow', 'michael', 'password1', 'password123',
        'welcome', 'admin', 'login', 'passw0rd', 'hello', 'charlie', 'donald',
        'batman', 'access', 'thunder', 'words', 'love', 'god', 'secret',
        'sex', 'ninja', 'mustang', 'test', 'pass', '1234', '12345', '1234567',
        '123456789', '1234567890', '0000', '1q2w3e', 'qweasd', 'zaq1',
        'abc123', 'asdf', '1qaz', '2wsx', 'pass', 'p@ssw0rd', 'P@ssw0rd',
        'welcome1', 'changeme', 'temp', 'root', 'toor', 'guest', 'default',
    ]
    
    def __init__(self):
        self.paths = list(self.DEFAULT_PATHS)
        self._words = None
        self._loaded_count = 0
    
    def load(self, path: Optional[str] = None) -> int:
        """Load wordlist from file"""
        if path:
            self.paths.insert(0, Path(path))
        
        words = set()
        for p in self.paths:
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8', errors='replace') as f:
                        for line in f:
                            w = line.strip()
                            if w and len(w) >= 1:
                                words.add(w.lower())
                    logger.info(f"Loaded {len(words)} words from {p}")
                    break
                except Exception as e:
                    logger.debug(f"Failed to load {p}: {e}")
        
        # Add builtin if no external wordlist found
        if not words:
            words.update(self.BUILTIN_WORDS)
            logger.info(f"Using builtin wordlist ({len(words)} words)")
        
        self._words = sorted(words)
        self._loaded_count = len(self._words)
        return self._loaded_count
    
    def get_words(self) -> List[str]:
        if self._words is None:
            self.load()
        return self._words
    
    def generate_variations(self, word: str) -> List[str]:
        """Generate common password variations"""
        vars = [word]
        
        # Capitalize first letter
        vars.append(word.capitalize())
        
        # Add numbers
        for n in range(100):
            vars.append(f"{word}{n}")
            vars.append(f"{n}{word}")
        for n in range(1, 51):
            vars.append(f"{word}!{n}")
            vars.append(f"{word}@{n}")
        
        # Common substitutions
        subs = {
            'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7',
            'A': '@', 'E': '3', 'I': '1', 'O': '0', 'S': '5', 'T': '7',
        }
        leetspeak = ''.join(subs.get(c, c) for c in word)
        vars.append(leetspeak)
        
        # Reverse
        vars.append(word[::-1])
        
        # Double
        vars.append(word * 2)
        
        return list(set(vars))
    
    def get_count(self) -> int:
        return self._loaded_count


# =========================================================================
# Cracker Engine
# =========================================================================

class PasswordCracker:
    """Main password cracking engine"""
    
    def __init__(self):
        self.wordlist = WordlistManager()
        self._results = []
        self._stats = {'tried': 0, 'found': 0, 'time_ms': 0}
    
    def crack(self, hash_value: str, wordlist_path: Optional[str] = None) -> Dict:
        """Crack a single hash"""
        hash_value = hash_value.strip()
        
        # Validate
        if not hash_value:
            return {'error': 'Empty hash'}
        
        # Detect type
        hash_types = HashDetector.detect(hash_value)
        crackable = HashDetector.is_crackable(hash_value)
        
        result = {
            'hash': hash_value,
            'types': hash_types,
            'crackable': crackable,
            'status': 'pending',
            'plaintext': None,
            'time_ms': 0,
            'tried': 0,
        }
        
        if not crackable:
            result['status'] = 'uncrackable'
            result['note'] = 'Hash type not supported by offline cracker. Use online services or hardware.'
            return result
        
        # Load wordlist
        start = time.time()
        count = self.wordlist.load(wordlist_path)
        
        # Try each word
        plaintext = None
        tried = 0
        
        for word in self.wordlist.get_words():
            tried += 1
            result['tried'] = tried
            
            for h_type in hash_types:
                if plaintext:
                    break
                
                computed = self._compute_hash(word, h_type)
                if computed and computed.lower() == hash_value.lower():
                    plaintext = word
                    result['matched_type'] = h_type
                    break
            
            # Progress every 10000 tries
            if tried % 10000 == 0:
                elapsed = (time.time() - start) * 1000
                rate = tried / (elapsed / 1000) if elapsed > 0 else 0
                logger.info(f"  Tried {tried:,} words @ {rate:.0f}/s")
        
        elapsed_ms = (time.time() - start) * 1000
        result['time_ms'] = round(elapsed_ms, 0)
        result['tried'] = tried
        result['rate_per_sec'] = round(tried / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0
        
        if plaintext:
            result['status'] = 'cracked'
            result['plaintext'] = plaintext
            logger.info(f"  CRACKED: {hash_value[:20]}... → {plaintext}")
        else:
            result['status'] = 'not_found'
            result['note'] = f'Tried {tried:,} passwords. Hash not in wordlist.'
            logger.info(f"  NOT FOUND after {tried:,} attempts")
        
        self._results.append(result)
        return result
    
    def crack_multiple(self, hashes: List[str], wordlist_path: Optional[str] = None) -> Dict:
        """Crack multiple hashes"""
        results = []
        total_start = time.time()
        
        for i, h in enumerate(hashes):
            logger.info(f"[{i+1}/{len(hashes)}] Cracking {h[:30]}...")
            r = self.crack(h, wordlist_path)
            results.append(r)
        
        total_ms = (time.time() - total_start) * 1000
        
        return {
            'total_hashes': len(hashes),
            'cracked': sum(1 for r in results if r['status'] == 'cracked'),
            'failed': sum(1 for r in results if r['status'] == 'not_found'),
            'skipped': sum(1 for r in results if r['status'] == 'uncrackable'),
            'total_time_ms': round(total_ms),
            'results': results,
        }
    
    def _compute_hash(self, password: str, hash_type: str) -> Optional[str]:
        """Compute hash for comparison"""
        try:
            if hash_type == 'MD5':
                return hashlib.md5(password.encode('utf-8')).hexdigest()
            elif hash_type == 'SHA1':
                return hashlib.sha1(password.encode('utf-8')).hexdigest()
            elif hash_type == 'SHA256':
                return hashlib.sha256(password.encode('utf-8')).hexdigest()
            elif hash_type == 'SHA512':
                return hashlib.sha512(password.encode('utf-8')).hexdigest()
            elif hash_type == 'crc32':
                return format(binascii.crc32(password.encode()) & 0xffffffff, '08x')
            elif hash_type == 'NTLM':
                # NTLM = MD4 of UTF-16LE password
                return hashlib.new('md4', password.encode('utf-16le')).hexdigest()
            elif hash_type == 'md5unix':
                # MD5 crypt: $1$salt$hash
                # Simplified — just try common patterns
                return None
            elif hash_type == 'sha256unix':
                return None
            elif hash_type == 'sha512unix':
                return None
        except Exception as e:
            logger.debug(f"Hash compute error for {hash_type}: {e}")
        return None
    
    def get_results(self) -> List[Dict]:
        return self._results
    
    def get_stats(self) -> Dict:
        return {
            **self._stats,
            'wordlist_size': self.wordlist.get_count(),
            'total_cracked': len([r for r in self._results if r['status'] == 'cracked']),
        }


# =========================================================================
# CLI Entry
# =========================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Password Cracker v1 — Offline hash cracking')
    parser.add_argument('hash', nargs='?', help='Hash to crack')
    parser.add_argument('--file', '-f', help='File with one hash per line')
    parser.add_argument('--wordlist', '-w', help='Custom wordlist file')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    parser.add_argument('--show-all', action='store_true', help='Show all attempts (not just results)')
    parser.add_argument('--info', '-i', action='store_true', help='Show hash type info')
    parser.add_argument('--stats', '-s', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    cracker = PasswordCracker()
    
    if args.info:
        print("\nSupported hash types:")
        for name, pat in HashDetector.PATTERNS.items():
            print(f"  {name:12s} — regex: {pat}")
        
        print("\nWordlist locations checked:")
        for p in WordlistManager.DEFAULT_PATHS:
            exists = '[OK]' if p.exists() else '[X]'
            print(f"  {exists} {p}")
        print()
        sys.exit(0)
    
    if args.stats:
        stats = cracker.get_stats()
        print(f"\n{'='*50}")
        print(f"  Password Cracker Stats")
        print(f"{'='*50}")
        print(f"  Wordlist size: {stats['wordlist_size']:,}")
        print(f"  Total cracked: {stats['total_cracked']}")
        print(f"  Total tried (this session): {stats['tried']:,}")
        print()
        sys.exit(0)
    
    if not args.hash and not args.file:
        print("""
Password Cracker v1 — Offline hash cracking
Uso:
  python password_cracker.py <hash>
  python password_cracker.py <hash> --wordlist custom.txt
  python password_cracker.py --file hashes.txt
  python password_cracker.py --info
  python password_cracker.py --stats
""")
        sys.exit(0)
    
    # Single hash
    if args.hash and not args.file:
        result = cracker.crack(args.hash, wordlist_path=args.wordlist)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*50}")
            print(f"  Hash Analysis")
            print(f"{'='*50}")
            print(f"  Hash:     {result['hash'][:50]}{'...' if len(result['hash']) > 50 else ''}")
            print(f"  Types:    {', '.join(result['types'])}")
            print(f"  Status:   {result['status'].upper()}")
            
            if result['status'] == 'cracked':
                print(f"  [OK] PLAINTEXT: {result['plaintext']}")
            elif result.get('note'):
                print(f"  ⚠️  {result['note']}")
            
            print(f"  Tried:    {result['tried']:,} passwords")
            print(f"  Time:     {result['time_ms']:.0f}ms ({result.get('rate_per_sec', 0):,}/s)")
            print()
        
        sys.exit(0 if result['status'] == 'cracked' else 1)
    
    # Multiple hashes from file
    if args.file:
        with open(args.file, 'r', encoding='utf-8', errors='replace') as f:
            hashes = [line.strip() for line in f if line.strip()]
        
        result = cracker.crack_multiple(hashes, wordlist_path=args.wordlist)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n{'='*50}")
            print(f"  Batch Results")
            print(f"{'='*50}")
            print(f"  Total:     {result['total_hashes']}")
            print(f"  Cracked:   {result['cracked']} ✅")
            print(f"  Failed:    {result['failed']} ❌")
            print(f"  Skipped:   {result['skipped']} ⏭")
            print(f"  Time:      {result['total_time_ms']:.0f}ms")
            
            for r in result['results']:
                icon = '[OK]' if r['status'] == 'cracked' else ('[FAIL]' if r['status'] == 'not_found' else '[SKIP]')
                hash_preview = r['hash'][:40] + '...' if len(r['hash']) > 40 else r['hash']
                if r['status'] == 'cracked':
                    print(f"  {icon} {hash_preview} → {r['plaintext']}")
                elif r['status'] == 'not_found':
                    print(f"  {icon} {hash_preview} (not in wordlist)")
                else:
                    print(f"  {icon} {hash_preview} ({', '.join(r['types'])})")
            print()
        
        sys.exit(0 if result['cracked'] > 0 else 1)


if __name__ == '__main__':
    main()
