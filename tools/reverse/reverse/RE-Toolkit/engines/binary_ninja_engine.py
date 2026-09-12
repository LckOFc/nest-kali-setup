#!/usr/bin/env python3
"""
Binary Ninja Engine - Análise estilo Binary Ninja
=================================================
Recria funcionalidades de análise de binários.
"""

import os
import re
import struct
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum


class DataType(Enum):
    INTEGER = 'integer'
    FLOAT = 'float'
    DOUBLE = 'double'
    POINTER = 'pointer'
    STRING = 'string'
    STRUCT = 'struct'
    ARRAY = 'array'
    FUNCTION = 'function'
    VOID = 'void'


@dataclass
class TypeInfo:
    """Informação de tipo."""
    name: str
    data_type: DataType
    size: int
    alignment: int
    fields: Dict[str, 'TypeInfo'] = field(default_factory=dict)
    is_complex: bool = False


@dataclass
class FunctionInfo:
    """Informação de função."""
    address: int
    name: str
    size: int
    params: List[TypeInfo] = field(default_factory=list)
    return_type: TypeInfo = None
    callers: List[int] = field(default_factory=list)
    callees: List[int] = field(default_factory=list)
    complexity: int = 0
    is_exported: bool = False
    is_imported: bool = False


@dataclass
class Symbol:
    """Símbolo."""
    name: str
    address: int
    type: str  # function, variable, section, etc
    size: int = 0
    binding: str = 'global'


class BinaryNinjaEngine:
    """
    Engine de análise estilo Binary Ninja.
    
    Funcionalidades:
    - Análise de funções
    - Inferência de tipos
    - Construção de CFG
    - Análise de chamadas
    - Identificação de estruturas
    - SSA form (simples)
    """
    
    def __init__(self, toolkit=None):
        self.toolkit = toolkit
        self.functions: Dict[int, FunctionInfo] = {}
        self.types: Dict[str, TypeInfo] = {}
        self.symbols: List[Symbol] = []
        self.cfgs: Dict[int, dict] = {}
        self._md = None
        
        try:
            import capstone
            self._md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            self._md.detail = True
        except:
            pass
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Analisar arquivo completo."""
        result = {
            'file': file_path,
            'functions': [],
            'types': [],
            'symbols': [],
            'cfg_summary': {},
            'analysis_time': 0,
        }
        
        start_time = os.path.getmtime(file_path)
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read(100 * 1024 * 1024)  # First 100MB
            
            # Analyze functions
            result['functions'] = self._analyze_functions(data)
            
            # Analyze types
            result['types'] = self._analyze_types(data)
            
            # Extract symbols
            result['symbols'] = self._extract_symbols(data)
            
            # Build CFG
            result['cfg_summary'] = self._build_cfg_summary(result['functions'])
            
        except Exception as e:
            result['error'] = str(e)
        
        result['analysis_time'] = os.path.getmtime(file_path) - start_time
        return result
    
    def get_function_at(self, file_path: str, address: int) -> Dict[str, Any]:
        """Obter função em endereço específico."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(50 * 1024 * 1024)
            
            func_data = self._extract_function(data, address)
            if not func_data:
                return {'error': 'Função não encontrada'}
            
            # Analyze
            func_info = self._analyze_function_data(func_data, address)
            
            return {
                'success': True,
                'function': func_info,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_type_at(self, file_path: str, type_name: str) -> Dict[str, Any]:
        """Obter tipo por nome."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(100 * 1024 * 1024)
            
            # Find type
            for t in self._analyze_types(data):
                if t['name'] == type_name:
                    return {'success': True, 'type': t}
            
            return {'success': False, 'error': 'Tipo não encontrado'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_call_graph(self, file_path: str, func_address: int) -> Dict[str, Any]:
        """Obter graph de chamadas."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(50 * 1024 * 1024)
            
            # Find function
            func = None
            for addr, f in self.functions.items():
                if addr == func_address:
                    func = f
                    break
            
            if not func:
                return {'error': 'Função não encontrada'}
            
            # Build call graph
            callers = []
            callees = []
            
            # Find callers (functions that call this one)
            for addr, other_func in self.functions.items():
                for callee_addr in other_func.callees:
                    if callee_addr == func_address:
                        callers.append(addr)
            
            # Get callees from analysis
            callees = func.callees
            
            return {
                'success': True,
                'function': hex(func_address),
                'callers': [hex(c) for c in callers],
                'callees': [hex(c) for c in callees],
                'caller_count': len(callers),
                'callee_count': len(callees),
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_cross_references(self, file_path: str, address: int) -> Dict[str, Any]:
        """Obter cross-references."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(100 * 1024 * 1024)
            
            xrefs = []
            
            # Search for references to address
            addr_bytes = struct.pack('<Q', address)
            for match in re.finditer(re.escape(addr_bytes), data):
                xrefs.append({
                    'address': hex(match.start()),
                    'type': 'data_ref',
                })
            
            return {
                'success': True,
                'address': hex(address),
                'xrefs': xrefs[:50],
                'count': len(xrefs),
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # METODOS INTERNOS
    # ============================================================
    
    def _analyze_functions(self, data: bytes) -> List[Dict]:
        """Analisar funções."""
        functions = []
        
        if not self._md:
            return functions
        
        # Find function prologues
        prologue = b'\x55\x48\x89\xe5'
        
        for match in re.finditer(re.escape(prologue), data):
            addr = match.start()
            
            # Extract function
            func_data = self._extract_function(data, addr)
            if not func_data:
                continue
            
            # Analyze
            func_info = self._analyze_function_data(func_data, addr)
            
            functions.append({
                'address': hex(addr),
                'name': func_info.name,
                'size': func_info.size,
                'params': len(func_info.params),
                'complexity': func_info.complexity,
                'is_exported': func_info.is_exported,
                'calls': len(func_info.callees),
            })
            
            # Store for later use
            self.functions[addr] = func_info
            
            if len(functions) >= 200:
                break
        
        return functions
    
    def _analyze_types(self, data: bytes) -> List[Dict]:
        """Analisar tipos."""
        types = []
        
        # Look for struct patterns
        struct_pattern = rb'struct\s*\{([^}]{0,500})\}'
        for match in re.finditer(struct_pattern, data):
            try:
                content = match.group(1).decode('ascii', errors='replace')
                fields = re.findall(r'\s+(\w+)\s+(\w+)', content)
                
                if fields and len(types) < 200:
                    type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                    type_name = f'Struct_{type_hash}'
                    
                    type_info = TypeInfo(
                        name=type_name,
                        data_type=DataType.STRUCT,
                        size=len(fields) * 8,  # Estimate
                        fields={f[1]: TypeInfo(f[1], DataType.INTEGER, 8) for f in fields[:10]},
                    )
                    
                    types.append({
                        'name': type_name,
                        'kind': 'struct',
                        'fields': len(fields),
                        'size_estimate': type_info.size,
                        'confidence': 0.7,
                    })
                    
                    self.types[type_name] = type_info
                    
            except:
                pass
        
        # Look for function pointer patterns
        func_ptr_pattern = rb'\(\*?(\w+)\s*\)\s*\([^)]*\)'
        for match in re.finditer(func_ptr_pattern, data):
            try:
                name = match.group(1).decode('ascii')
                if name and len(types) < 200:
                    types.append({
                        'name': name,
                        'kind': 'function_pointer',
                        'confidence': 0.5,
                    })
            except:
                pass
        
        return types[:200]
    
    def _extract_symbols(self, data: bytes) -> List[Dict]:
        """Extrair símbolos."""
        symbols = []
        
        # Look for exported function names
        export_pattern = rb'([a-zA-Z_][a-zA-Z0-9_]{3,50})\s*\('
        for match in re.finditer(export_pattern, data):
            try:
                name = match.group(1).decode('ascii')
                addr = match.start()
                
                symbols.append({
                    'name': name,
                    'address': hex(addr),
                    'type': 'function',
                    'binding': 'global',
                })
            except:
                pass
        
        return symbols[:100]
    
    def _extract_function(self, data: bytes, addr: int) -> Optional[Dict]:
        """Extrair dados de função."""
        if not self._md:
            return None
        
        if addr >= len(data):
            return None
        
        # Extract function data
        func_data = data[addr:addr + 0x2000]
        
        try:
            insts = list(self._md.disasm(func_data, addr))
        except:
            return None
        
        if len(insts) < 3:
            return None
        
        # Find function end
        end_addr = addr
        for inst in insts:
            if inst.mnemonic == 'ret':
                end_addr = inst.address + inst.size
                break
        else:
            end_addr = addr + 0x1000
        
        return {
            'start_addr': addr,
            'end_addr': end_addr,
            'instructions': insts,
            'instruction_count': len(insts),
        }
    
    def _analyze_function_data(self, func_data: Dict, addr: int) -> FunctionInfo:
        """Analisar dados de função."""
        insts = func_data['instructions']
        
        # Generate name
        name = f'func_{addr:08x}'
        
        # Analyze parameters (Go ABI: DI, SI, DX, CX, R8, R9)
        params = []
        reg_params = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        
        for inst in insts[:10]:
            ops = inst.operands.lower()
            for reg in reg_params:
                if reg in ops and inst.mnemonic in ('mov', 'lea', 'movq'):
                    params.append(TypeInfo(reg, DataType.POINTER, 8))
                    break
        
        # Analyze return type
        return_type = TypeInfo('void', DataType.VOID, 0)
        for inst in reversed(insts[:20]):
            if inst.mnemonic == 'ret':
                # Check for mov rax, ...
                for prev in reversed(insts):
                    if 'rax' in prev.operands.lower() and prev.mnemonic in ('mov', 'movq'):
                        return_type = TypeInfo('uintptr', DataType.INTEGER, 8)
                        break
                break
        
        # Calculate complexity
        complexity = 1
        for inst in insts:
            if inst.mnemonic.lower().startswith('j'):
                complexity += 1
        
        # Find callees
        callees = []
        for inst in insts:
            if inst.mnemonic == 'call':
                target = inst.address + inst.size  # Approximate
                callees.append(target)
        
        return FunctionInfo(
            address=addr,
            name=name,
            size=func_data['end_addr'] - addr,
            params=params,
            return_type=return_type,
            callees=callees,
            complexity=complexity,
        )
    
    def _build_cfg_summary(self, functions: List[Dict]) -> Dict:
        """Construir resumo do CFG."""
        total_blocks = 0
        total_edges = 0
        
        for func in functions:
            # Estimate blocks based on jumps
            total_blocks += max(1, func.get('calls', 0) // 3 + 1)
            total_edges += func.get('calls', 0) + 1  # Each call + fall-through
        
        return {
            'total_functions': len(functions),
            'total_blocks': total_blocks,
            'total_edges': total_edges,
            'avg_blocks_per_func': total_blocks / len(functions) if functions else 0,
        }


# Quick test
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        engine = BinaryNinjaEngine()
        result = engine.analyze(sys.argv[1])
        print(f"Functions: {len(result.get('functions', []))}")
        print(f"Types: {len(result.get('types', []))}")
        print(f"CFG summary: {result.get('cfg_summary', {})}")
    else:
        print("Usage: python binary_ninja_engine.py <binary>")
