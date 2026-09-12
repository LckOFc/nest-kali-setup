"""
__init__.py - Advanced RE package
"""
from .ai_orchestrator import AIOrchestrator, run_advanced_re
from .modules.anti_anti_debug import AntiAntiDebug
from .modules.devirtualizer import Devirtualizer
from .modules.anti_sandbox_buster import AntiSandboxBuster
from .modules.go_rust_analyzer import GoRustAnalyzer
from .modules.string_decryptor import StringDecryptor
from .modules.pattern_matcher import PatternMatcher, AIPatternMatcher

__version__ = "1.0.0"
__all__ = [
    "AIOrchestrator",
    "run_advanced_re",
    "AntiAntiDebug",
    "Devirtualizer",
    "AntiSandboxBuster",
    "GoRustAnalyzer",
    "StringDecryptor",
    "PatternMatcher",
    "AIPatternMatcher",
]
