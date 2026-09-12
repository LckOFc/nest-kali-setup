"""
APEX Cracker — Modo 4070
Multi-strategy hash cracker with parallel execution.

Usage:
    python apex_cracker.py <hash> [--wordlist file] [--threads N] [--method all]
    python apex_cracker.py --file hashes.txt
    python apex_cracker.py --info
    python apex_cracker.py --stats
"""

from .apex_cracker import APEXCracker, HashDetector, WordlistManager, RuleEngine

__version__ = "4070-APEX"
