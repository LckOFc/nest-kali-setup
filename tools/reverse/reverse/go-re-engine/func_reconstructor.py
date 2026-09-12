#!/usr/bin/env python3
"""
Go Function Reconstructor
==========================
Recria funcionalidades de identificação e reconstrução de funções
do Ghidra e Binary Ninja para binários Go.
"""

import re
import struct
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any


@dataclass
class FunctionSignature:
    """Assinatura de função Go."""
    name: str
    addr: int
    params: List[Tuple[str, str]] = field(default_factory=list)  # (name, type)
    returns: List[str] = field(default_factory=list)
    is_method: bool = False
    receiver: Optional[str] = None
    is_exported: bool = False
    is_constructor: bool = False
    complexity: int = 0  # Cyclomatic complexity


@dataclass
class FunctionAnalysis:
    """Análise completa de função."""
    sig: FunctionSignature
    instructions_count: int = 0
    call_sites: List[Tuple[int, str]] = field(default_factory=list)
    basic_blocks: int = 0
    stack_size: int = 0
    has_runtime_calls: bool = False
    has_allocation: bool = False
    has_channel_ops: bool = False
    has_mutex_ops: bool = False


class GoFuncReconstructor:
    """
    Reconstrutor de funções Go.
    
    Recursos:
    - Detecção de funções a partir de prologues
    - Recovery de signatures (params, returns)
    - Identificação de métodos vs funções livres
    - Detecção de construtores (New*, Make*, Create*)
    - Análise de complexidade ciclomática
    - Identificação de padrões Go (goroutines, channels, etc)
    """
    
    # Nomes comuns de construtores Go
    CONSTRUCTOR_PREFIXES = ['New', 'Make', 'Create', 'Open', 'Connect', 'Start', 'Init']
    
    # Padrões de nomes de métodos Go
    METHOD_PATTERNS = [
        r'func\s+\((\w+)\s+\*?(\w+)\)\s+(\w+)',
        r'func\s+(\w+)\.(\w+)\s*\(',
    ]
    
    # Instruções runtime Go
    RUNTIME_PATTERNS = {
        'alloc': ['runtime.newobject', 'runtime.makeslice', 'runtime.makemap'],
        'channel': ['runtime.chansend', 'runtime.chanrecv', 'runtime.closechan'],
        'mutex': ['runtime.lock', 'runtime.unlock', 'sync.runtime_Semacquire'],
        'goroutine': ['runtime.goexit', 'runtime.schedule', 'runtime.gopark'],
        'panic': ['runtime.panic', 'runtime.throw'],
    }
    
    def __init__(self):
        self.functions: Dict[int, FunctionAnalysis] = {}
        self.type_registry: Dict[str, List[str]] = defaultdict(list)  # type -> function names
        
    def analyze_binary(self, data: bytes, pe_info: dict = None) -> Dict[int, FunctionAnalysis]:
        """
        Analisar binário Go e reconstruir funções.
        
        Args:
            data: Dados brutos do binário
            pe_info: Informações PE (opcional)
            
        Returns:
            Dicionário addr -> FunctionAnalysis
        """
        # 1. Encontrar candidatos a função
        candidates = self._find_function_candidates(data)
        
        # 2. Analisar cada candidato
        for addr, info in candidates.items():
            analysis = self._analyze_function(data, addr, info)
            if analysis:
                self.functions[addr] = analysis
        
        # 3. Registrar tipos
        self._register_types()
        
        return self.functions
    
    def _find_function_candidates(self, data: bytes) -> Dict[int, dict]:
        """Encontrar candidatos a função no binário."""
        candidates = {}
        
        # Go function prologue: push rbp; mov rbp, rsp
        # ASCII: 55 48 89 E5
        prologue = b'\x55\x48\x89\xe5'
        
        for match in re.finditer(re.escape(prologue), data):
            addr = match.start()
            
            # Verify it's likely a function (check for ret within reasonable distance)
            func_data = data[addr:addr + 0x1000]
            if b'\xc3' in func_data:  # RET instruction
                # Estimate function size
                ret_pos = func_data.find(b'\xc3')
                candidates[addr] = {
                    'start': addr,
                    'estimated_end': addr + ret_pos + 1,
                    'size_estimate': ret_pos + 1,
                }
        
        # Also find functions from string references
        # Go embeds function names in the binary
        func_name_pattern = rb'[a-z][a-z0-9_]+\.[a-z][a-z0-9_]+\([a-z0-9_,\s*&]+\)'
        for match in re.finditer(func_name_pattern, data):
            # These are call sites, not function definitions
            pass
        
        return candidates
    
    def _analyze_function(self, data: bytes, addr: int, 
                          info: dict) -> Optional[FunctionAnalysis]:
        """Analisar uma função candidata."""
        func_data = data[addr:info['estimated_end']]
        
        # Disassemble to get instructions
        try:
            import capstone
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            insts = list(md.disasm(func_data, addr))
        except ImportError:
            insts = []
        
        if not insts:
            return None
        
        # Extract signature
        sig = self._extract_signature(addr, insts, data)
        
        # Analyze characteristics
        analysis = FunctionAnalysis(sig=sig)
        analysis.instructions_count = len(insts)
        
        # Check for runtime patterns
        for inst in insts:
            mnem = inst.mnemonic.lower()
            ops = inst.operands.lower()
            
            # Call sites
            if mnem == 'call':
                target = self._resolve_call_target(inst, data, addr)
                if target:
                    analysis.call_sites.append((inst.address, target))
            
            # Runtime calls
            for category, patterns in self.RUNTIME_PATTERNS.items():
                for pattern in patterns:
                    if pattern in ops:
                        if category == 'alloc':
                            analysis.has_allocation = True
                        elif category == 'channel':
                            analysis.has_channel_ops = True
                        elif category == 'mutex':
                            analysis.has_mutex_ops = True
                        elif category == 'goroutine':
                            analysis.has_runtime_calls = True
        
        # Estimate stack size
        max_stack = 0
        current_stack = 0
        for inst in insts:
            if inst.mnemonic.lower() == 'sub' and 'rsp' in inst.operands:
                m = re.search(r'0x([0-9a-f]+)', inst.operands)
                if m:
                    current_stack += int(m.group(1), 16)
                    max_stack = max(max_stack, current_stack)
            elif inst.mnemonic.lower() == 'add' and 'rsp' in inst.operands:
                m = re.search(r'0x([0-9a-f]+)', inst.operands)
                if m:
                    current_stack -= int(m.group(1), 16)
        
        analysis.stack_size = max_stack
        
        # Count basic blocks (simple heuristic)
        analysis.basic_blocks = 1 + sum(1 for inst in insts 
                                         if inst.mnemonic.lower() in ('jmp',) 
                                         and '0x' in inst.operands)
        
        # Calculate complexity
        analysis.sig.complexity = self._calc_complexity(insts)
        
        return analysis
    
    def _extract_signature(self, addr: int, insts: List, data: bytes) -> FunctionSignature:
        """Extrair assinatura da função."""
        # Try to find function name from strings nearby
        name = self._find_func_name(addr, data)
        
        # Determine if it's a method
        is_method = False
        receiver = None
        
        # Check for method receiver pattern (first param in DI)
        if insts and 'rdi' in insts[0].operands.lower():
            is_method = True
            # Try to infer receiver type from context
            receiver = self._infer_receiver_type(addr, data)
        
        # Check for constructor pattern
        is_constructor = any(name.startswith(p) for p in self.CONSTRUCTOR_PREFIXES)
        
        # Determine export status
        is_exported = name[0].isupper() if name else False
        
        return FunctionSignature(
            name=name or f"fn_{addr:08x}",
            addr=addr,
            is_method=is_method,
            receiver=receiver,
            is_exported=is_exported,
            is_constructor=is_constructor,
        )
    
    def _find_func_name(self, addr: int, data: bytes) -> Optional[str]:
        """Tentar encontrar nome da função a partir de strings."""
        # Search in nearby strings
        search_range = 0x1000
        start = max(0, addr - search_range)
        end = min(len(data), addr + search_range)
        
        chunk = data[start:end]
        
        # Look for Go function name patterns
        patterns = [
            rb'([a-z][a-z0-9_]+\.[a-z][a-z0-9_]+)\s*\(',
            rb'func\s+([a-z][a-z0-9_]*)\s*\(',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, chunk):
                try:
                    return match.group(1).decode('ascii')
                except:
                    pass
        
        return None
    
    def _infer_receiver_type(self, addr: int, data: bytes) -> Optional[str]:
        """Inferir tipo do receiver."""
        # Look for type names near the function
        search_range = 0x500
        start = max(0, addr - search_range)
        end = min(len(data), addr + search_range)
        
        chunk = data[start:end]
        
        # Look for struct definitions
        struct_pattern = rb'type\s+(\w+)\s+struct'
        for match in re.finditer(struct_pattern, chunk):
            try:
                return match.group(1).decode('ascii')
            except:
                pass
        
        return None
    
    def _resolve_call_target(self, inst, data: bytes, func_addr: int) -> Optional[str]:
        """Tentar resolver alvo de chamada."""
        # Simple heuristic: check if target is in known ranges
        target = inst.get('target', 0)
        if target == 0:
            return None
        
        # Return mangled name
        return f"sub_{target:08x}"
    
    def _calc_complexity(self, insts: List) -> int:
        """Calcular complexidade ciclomática."""
        complexity = 1  # Base complexity
        
        # Count branch points
        branch_instructions = {
            'je', 'jne', 'jl', 'jle', 'jg', 'jge',
            'jb', 'jbe', 'ja', 'jae',
            'jmp',  # Unconditional also counts
        }
        
        for inst in insts:
            if inst.mnemonic.lower() in branch_instructions:
                complexity += 1
        
        return complexity
    
    def _register_types(self):
        """Registrar tipos usados nas funções."""
        for addr, analysis in self.functions.items():
            sig = analysis.sig
            if sig.receiver:
                self.type_registry[sig.receiver].append(sig.name)
            for param_name, param_type in sig.params:
                self.type_registry[param_type].append(sig.name)
    
    def get_analysis_summary(self) -> dict:
        """Retornar resumo da análise."""
        total = len(self.functions)
        methods = sum(1 for a in self.functions.values() if a.sig.is_method)
        constructors = sum(1 for a in self.functions.values() if a.sig.is_constructor)
        exported = sum(1 for a in self.functions.values() if a.sig.is_exported)
        
        return {
            'total_functions': total,
            'methods': methods,
            'constructors': constructors,
            'exported': exported,
            'with_allocations': sum(1 for a in self.functions.values() if a.has_allocation),
            'with_channels': sum(1 for a in self.functions.values() if a.has_channel_ops),
            'with_mutexes': sum(1 for a in self.functions.values() if a.has_mutex_ops),
            'avg_complexity': sum(a.sig.complexity for a in self.functions.values()) / total if total else 0,
            'max_complexity': max((a.sig.complexity for a in self.functions.values()), default=0),
        }
    
    def get_functions_by_type(self, type_name: str) -> List[str]:
        """Retornar funções que usam um tipo específico."""
        return self.type_registry.get(type_name, [])
    
    def export_analysis(self) -> List[dict]:
        """Exportar análise como lista de dicts."""
        results = []
        for addr, analysis in sorted(self.functions.items()):
            sig = analysis.sig
            results.append({
                'addr': hex(addr),
                'name': sig.name,
                'params': sig.params,
                'returns': sig.returns,
                'is_method': sig.is_method,
                'receiver': sig.receiver,
                'is_exported': sig.is_exported,
                'is_constructor': sig.is_constructor,
                'complexity': sig.complexity,
                'instructions': analysis.instructions_count,
                'basic_blocks': analysis.basic_blocks,
                'stack_size': analysis.stack_size,
                'call_sites': len(analysis.call_sites),
                'has_allocation': analysis.has_allocation,
                'has_channel_ops': analysis.has_channel_ops,
                'has_mutex_ops': analysis.has_mutex_ops,
            })
        return results


# ============================================================
# Main analysis function
# ============================================================

def analyze_functions(exe_path: str, output_dir: str = None) -> dict:
    """
    Analisar funções em binário Go.
    """
    import os
    import json
    import capstone
    
    result = {
        'binary': exe_path,
        'functions': [],
        'summary': {},
        'type_registry': {},
    }
    
    # Read binary
    with open(exe_path, 'rb') as f:
        data = f.read(50 * 1024 * 1024)  # First 50MB
    
    # Initialize reconstructor
    reconstructor = GoFuncReconstructor()
    
    # Analyze
    functions = reconstructor.analyze_binary(data)
    
    result['functions'] = reconstructor.export_analysis()
    result['summary'] = reconstructor.get_analysis_summary()
    result['type_registry'] = dict(reconstructor.type_registry)
    
    # Save
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, 'functions_analysis.json'), 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"[+] Functions analysis saved: {os.path.join(output_dir, 'functions_analysis.json')}")
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Go Function Reconstructor')
    parser.add_argument('binary', help='Path to Go binary')
    parser.add_argument('--output', '-o', default='./output')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Go Function Reconstructor v1.0")
    print("=" * 60)
    print(f"\n  Binary: {args.binary}")
    print()
    
    result = analyze_functions(args.binary, args.output)
    
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Total functions: {result['summary']['total_functions']}")
    print(f"  Methods: {result['summary']['methods']}")
    print(f"  Constructors: {result['summary']['constructors']}")
    print(f"  Exported: {result['summary']['exported']}")
    print(f"  Avg complexity: {result['summary']['avg_complexity']:.1f}")