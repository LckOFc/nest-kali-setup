"""
__init__.py - Source Extractor Toolkit package
"""
from .source_extractor import SourceExtractor, ExtractionType
from .modules.pe_analyzer import PEAnalyzer
from .modules.dotnet_decompiler import DotNetDecompiler
from .modules.python_unpacker import PythonUnpacker
from .modules.string_miner import StringMiner

__version__ = "1.0.0"
__all__ = [
    "SourceExtractor",
    "ExtractionType",
    "PEAnalyzer",
    "DotNetDecompiler",
    "PythonUnpacker",
    "StringMiner",
]
