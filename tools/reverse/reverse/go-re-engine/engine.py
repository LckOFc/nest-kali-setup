"""
Go Reverse Engineering Toolkit v1.0
===================================
Recria funcionalidades do Ghidra/Binary Ninja/IDA para binários Go.

Componentes:
  - go_decompiler.py    : Motor de descompilação (estilo Hex-Rays)
  - go_cfg_analyzer.py  : Análise de fluxo de controle (CFG)
  - go_type_recover.py  : Recovery avançado de tipos
  - go_func_recon.py    : Reconstrução de funções
  - dashboard.py        : Dashboard web interativo
  - main.py            : Orchestrator principal
"""

import os
import sys
import struct
import re
import json
import hashlib
from collections import defaultdict, Counter, OrderedDict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path

# Try importing optional deps
try:
    import lief
except ImportError:
    lief = None

try:
    import capstone
except ImportError:
    capstone = None

try:
    import unicorn
except ImportError:
    unicorn = None

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Instruction:
    address: int
    mnemonic: str
    operands: str
    size: int
    binary: bytes
    is_jump: bool = False
    is_call: bool = False
    is_ret: bool = False
    target: Optional[int] = None
    
@dataclass
class Function:
    name: str
    start_addr: int
    end_addr: int
    size: int
    instructions: List[Instruction] = field(default_factory=list)
    params: List[str] = field(default_factory=list)
    return_types: List[str] = field(default_factory=list)
    callers: List[str] = field(default_factory=list)
    callees: List[str] = field(default_factory=list)
    basic_blocks: List['BasicBlock'] = field(default_factory=list)
    sig: str = ""
    
@dataclass
class BasicBlock:
    start: int
    end: int
    instructions: List[Instruction] = field(default_factory=list)
    predecessors: List[int] = field(default_factory=list)
    successors: List[int] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    
@dataclass 
class Type:
    name: str
    size: int
    fields: Dict[str, 'Type'] = field(default_factory=dict)
    is_struct: bool = False
    is_interface: bool = False
    is_slice: bool = False
    is_pointer: bool = False
    element_type: Optional[str] = None
    
@dataclass
class PseudoInstruction:
    address: int
    lineno: int
    text: str
    is_comment: bool = False
    indent: int = 0
    
@dataclass
class PseudoFunction:
    name: str
    sig: str
    lines: List[PseudoInstruction] = field(default_factory=list)
    attrs: Dict[str, str] = field(default_factory=dict)

# ============================================================
# GO SPECIFIC PATTERNS
# ============================================================

GO_KEYWORDS = {
    'func', 'var', 'const', 'type', 'interface', 'struct', 'map', 'chan',
    'go', 'defer', 'go func', 'select', 'case', 'default', 'switch',
    'if', 'else', 'for', 'range', 'return', 'break', 'continue', 'fallthrough',
    'package', 'import', 'go vet', 'make', 'new', 'append', 'copy', 'delete',
    'close', 'len', 'cap', 'open', 'panic', 'recover', 'nil', 'true', 'false',
    'iota', 'string', 'int', 'int8', 'int16', 'int32', 'int64',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64',
    'float32', 'float64', 'complex64', 'complex128',
    'bool', 'byte', 'rune', 'error', 'any',
}

GO_TYPES = {
    'string', 'int', 'int8', 'int16', 'int32', 'int64',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64',
    'float32', 'float64', 'complex64', 'complex128',
    'bool', 'byte', 'rune', 'error', 'any', 'interface{}',
}

# Go ABI conventions (AMD64)
GO_REGPARAMS = ['DI', 'SI', 'DX', 'CX', 'R8', 'R9']  # First 6 integer params
GO_FPPARAMS = ['X0', 'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7']  # Float params

# ============================================================
# GO DECOMPILER ENGINE (Hex-Rays style)
# ============================================================

class GoDecompiler:
    """
    Motor de descompilação que recria funcionalidades do Hex-Rays/IDA Pro
    para binários Go. Converte assembly x64 em pseudocódigo legível.
    """
    
    def __init__(self, md=None):
        self.md = md
        self.type_cache = {}
        self.var_counter = 0
        self.func_stack = {}
        
    def reset(self):
        self.var_counter = 0
        self.type_cache = {}
        
    def _new_var(self, prefix="var"):
        self.var_counter += 1
        return f"{prefix}_{self.var_counter:03x}"
    
    def _guess_type_from_reg(self, reg: str) -> str:
        """Guess Go type based on register usage patterns."""
        reg = reg.upper()
        if reg in ('RAX', 'EAX', 'AX', 'AH', 'AL'):
            return 'uintptr'  # Return values often in RAX
        elif reg in ('RDIA', 'RDI', 'DIA', 'DI'):
            return 'iface'  # First param (receiver)
        elif reg in ('RSI', 'SI'):
            return 'arg1'
        elif reg in ('RDX', 'DX'):
            return 'arg2'
        elif reg in ('RCX', 'CX'):
            return 'arg3'
        elif reg.startswith('R') and len(reg) == 2:
            return 'reg'
        return 'unknown'
    
    def _analyze_mem_access(self, op: str, addr: int) -> Tuple[str, str]:
        """Analyze memory access to guess type and base."""
        # Patterns like [rip + offset], [rbp - offset], [rsp + offset]
        m = re.match(r'\[(\w+)\s*(?:[-+]\s*0x([0-9a-f]+))?\]', op)
        if m:
            base = m.group(1)
            offset = int(m.group(2), 16) if m.group(2) else 0
            # Stack frame analysis
            if base in ('rbp', 'rbp'):
                if offset > 0x100:
                    return 'local_array', f"[{base}+0x{offset:x}]"
                elif offset > 0x20:
                    return 'local_struct', f"[{base}-0x{offset:x}]"
                else:
                    return 'local_var', f"[{base}-0x{offset:x}]"
            elif base in ('rsp', 'sp'):
                return 'stack', f"[{base}+0x{offset:x}]"
            elif base == 'rip':
                return 'got_entry', f"[rip+0x{offset:x}]"
            elif base in ('rax', 'rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9'):
                return f'ptr_{base}', f"[{base}+0x{offset:x}]"
        return 'unknown', op
    
    def _gen_pseudo_from_inst(self, inst: Instruction, ctx: dict) -> List[PseudoInstruction]:
        """Generate pseudo-code from a single instruction."""
        lines = []
        mnem = inst.mnemonic.lower()
        ops = inst.operands
        
        # Track register assignments
        current_reg = ctx.get('current_reg')
        current_type = ctx.get('current_type', 'unknown')
        
        # RET
        if mnem == 'ret':
            lines.append(PseudoInstruction(inst.address, len(lines)+1, "return", indent=0))
            ctx['in_function'] = False
            return lines
        
        # CALL - analyze what's being called
        elif mnem == 'call':
            target = inst.target
            # Check if target is in known functions
            callee_name = ctx.get('known_funcs', {}).get(target, f"sub__{target:016x}")
            lines.append(PseudoInstruction(inst.address, len(lines)+1, 
                f"// CALL: {callee_name} (0x{target:x})", indent=0, is_comment=True))
            # Generate call pseudo
            if current_reg:
                lines.append(PseudoInstruction(inst.address, len(lines)+1,
                    f"{current_reg} = {callee_name}({ops})", indent=2))
            else:
                var = self._new_var("ret")
                lines.append(PseudoInstruction(inst.address, len(lines)+1,
                    f"{var} = {callee_name}({ops})", indent=2))
                ctx['current_reg'] = var
            return lines
        
        # MOV patterns - track data flow
        elif mnem == 'mov':
            dst = ops.split(',')[0].strip()
            src = ops.split(',')[1].strip() if ',' in ops else ops.split()[1]
            
            # Mov with memory - structure field access
            if '[' in src:
                type_hint, mem_ref = self._analyze_mem_access(src, inst.address)
                lines.append(PseudoInstruction(inst.address, len(lines)+1,
                    f"{dst} = *{mem_ref}  // {type_hint}", indent=2))
            elif '[' in dst:
                type_hint, mem_ref = self._analyze_mem_access(dst, inst.address)
                lines.append(PseudoInstruction(inst.address, len(lines)+1,
                    f"*{mem_ref} = {src}  // {type_hint}", indent=2))
            else:
                lines.append(PseudoInstruction(inst.address, len(lines)+1,
                    f"{dst} = {src}", indent=2))
            ctx['current_reg'] = dst
            return lines
        
        # MOVZX/MOVSX - type conversions
        elif mnem in ('movzx', 'movsx', 'movsxd'):
            dst = ops.split(',')[0]
            src = ops.split(',')[1] if ',' in ops else ops.split()[1]
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"{dst} = ({mnem.upper()}){src}", indent=2))
            ctx['current_reg'] = dst
            return lines
        
        # LEA - address calculation (structure field access)
        elif mnem == 'lea':
            dst = ops.split(',')[0]
            src = ops.split(',')[1]
            type_hint, mem_ref = self._analyze_mem_access(src, inst.address)
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"{dst} = &{mem_ref}  // {type_hint}", indent=2))
            ctx['current_reg'] = dst
            return lines
        
        # CMP + conditional jumps - if/else reconstruction
        elif mnem == 'cmp':
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"// cmp {ops}", indent=2, is_comment=True))
            ctx['last_cmp'] = ops
            return lines
        
        # Conditional jumps
        elif mnem in ('je', 'jne', 'jz', 'jnz', 'jl', 'jle', 'jg', 'jge',
                      'ja', 'jae', 'jb', 'jbe', 'js', 'jns', 'jo', 'jno'):
            cond_map = {
                'je': '==', 'jne': '!=', 'jz': '==0', 'jnz': '!=0',
                'jl': '<', 'jle': '<=', 'jg': '>', 'jge': '>=',
                'ja': '>', 'jae': '>=', 'jb': '<', 'jbe': '<=',
                'js': '<0', 'jns': '>=0',
            }
            cond = cond_map.get(mnem, mnem)
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"// if {ctx.get('last_cmp', '?')} {cond} -> 0x{inst.target:x}", 
                indent=2, is_comment=True))
            return lines
        
        # JMP - unconditional jump
        elif mnem == 'jmp':
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"// goto 0x{inst.target:x}", indent=1, is_comment=True))
            return lines
        
        # Test/and/or/xor - boolean operations
        elif mnem in ('test', 'and', 'or', 'xor', 'not', 'neg'):
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"{mnem.upper()}({ops})", indent=2))
            return lines
        
        # Add/sub - arithmetic
        elif mnem in ('add', 'sub', 'inc', 'dec', 'mul', 'div', 'imul', 'idiv'):
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"{mnem.upper()}({ops})", indent=2))
            return lines
        
        # Shift operations
        elif mnem in ('shl', 'shr', 'sar', 'sal', 'shld', 'shrd', 'rol', 'ror'):
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"{mnem.upper()}({ops})", indent=2))
            return lines
        
        # Push/pop - stack operations
        elif mnem == 'push':
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"// push {ops}", indent=1, is_comment=True))
            return lines
        elif mnem == 'pop':
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"// pop {ops}", indent=1, is_comment=True))
            return lines
        
        # NOP
        elif mnem == 'nop':
            return []
        
        # Default
        else:
            lines.append(PseudoInstruction(inst.address, len(lines)+1,
                f"{mnem.upper()} {ops}", indent=2))
            return lines
    
    def decompile_function(self, func: Function, known_funcs: dict = None) -> PseudoFunction:
        """
        Decompilar uma função Go completa para pseudocódigo.
        Recria a lógica de alto nível a partir do assembly.
        """
        self.reset()
        pseudo = PseudoFunction(
            name=func.name,
            sig=func.sig,
        )
        
        ctx = {
            'known_funcs': known_funcs or {},
            'current_reg': None,
            'current_type': 'unknown',
            'in_function': True,
            'last_cmp': None,
            'stack_depth': 0,
            'loop_depth': 0,
        }
        
        indent = 0
        lineno = 0
        
        # Header
        pseudo.lines.append(PseudoInstruction(func.start_addr, 0, 
            f"// Function: {func.name}", is_comment=True))
        pseudo.lines.append(PseudoInstruction(func.start_addr, 1,
            f"// Range: 0x{func.start_addr:x} - 0x{func.end_addr:x}", is_comment=True))
        pseudo.lines.append(PseudoInstruction(func.start_addr, 2,
            f"// Size: {func.size} bytes", is_comment=True))
        if func.params:
            pseudo.lines.append(PseudoInstruction(func.start_addr, 3,
                f"// Params: {', '.join(func.params)}", is_comment=True))
        if func.return_types:
            pseudo.lines.append(PseudoInstruction(func.start_addr, 4,
                f"// Returns: {', '.join(func.return_types)}", is_comment=True))
        pseudo.lines.append(PseudoInstruction(func.start_addr, 5,
            f"{func.sig.split('(')[0].split()[-1]} {func.sig}", is_comment=False))
        pseudo.lines.append(PseudoInstruction(func.start_addr, 6, "{", indent=0))
        lineno = 7
        
        # Process instructions
        for inst in func.instructions:
            pseudo_lines = self._gen_pseudo_from_inst(inst, ctx)
            for pl in pseudo_lines:
                pl.address = inst.address
                pl.lineno = lineno
                pseudo.lines.append(pl)
                lineno += 1
            
            # Track stack depth
            if inst.mnemonic.lower() == 'sub':
                m = re.search(r'0x([0-9a-f]+)', inst.operands)
                if m:
                    ctx['stack_depth'] += int(m.group(1), 16)
            elif inst.mnemonic.lower() == 'add':
                m = re.search(r'0x([0-9a-f]+)', inst.operands)
                if m:
                    ctx['stack_depth'] -= int(m.group(1), 16)
        
        # Footer
        pseudo.lines.append(PseudoInstruction(func.end_addr, lineno, "}", indent=0))
        
        return pseudo


# ============================================================
# CONTROL FLOW GRAPH ANALYZER (Ghidra/Binja style)
# ============================================================

class CFGAnalyzer:
    """
    Analisador de fluxo de controle que recria funcionalidades
    do Ghidra e Binary Ninja para gerar Graphs de Controle.
    """
    
    def __init__(self):
        self.functions = {}
        self.edges = defaultdict(list)
        self.blocks = defaultdict(list)
        
    def analyze_function(self, func: Function, all_funcs: dict = None) -> BasicBlock:
        """Analisar uma função e construir seus basic blocks."""
        # Find control flow boundaries
        blocks = []
        current_block_start = func.start_addr
        
        for i, inst in enumerate(func.instructions):
            mnem = inst.mnemonic.lower()
            
            # Block boundaries: jumps, calls, ret
            if mnem in ('jmp', 'je', 'jne', 'jl', 'jle', 'jg', 'jge',
                        'jb', 'jbe', 'ja', 'jae', 'js', 'jns'):
                # End current block
                if current_block_start < inst.address:
                    blocks.append(BasicBlock(
                        start=current_block_start,
                        end=inst.address,
                        instructions=func.instructions[
                            self._find_inst_index(func, current_block_start):i
                        ]
                    ))
                current_block_start = inst.target if inst.target else inst.address + inst.size
                
            elif mnem == 'ret':
                if current_block_start <= inst.address:
                    blocks.append(BasicBlock(
                        start=current_block_start,
                        end=inst.address + inst.size,
                        instructions=func.instructions[
                            self._find_inst_index(func, current_block_start):i+1
                        ],
                        is_exit=True
                    ))
                break
                
            elif mnem == 'call' and inst.target:
                # Call creates a natural block boundary
                if current_block_start < inst.address:
                    blocks.append(BasicBlock(
                        start=current_block_start,
                        end=inst.address + inst.size,
                        instructions=func.instructions[
                            self._find_inst_index(func, current_block_start):i+1
                        ]
                    ))
                current_block_start = inst.address + inst.size
        
        # Last block
        if current_block_start <= func.end_addr and blocks and blocks[-1].end < func.end_addr:
            blocks.append(BasicBlock(
                start=current_block_start,
                end=func.end_addr,
                instructions=func.instructions[
                    self._find_inst_index(func, current_block_start):
                ]
            ))
        
        if not blocks:
            blocks = [BasicBlock(
                start=func.start_addr,
                end=func.end_addr,
                instructions=func.instructions,
                is_entry=True
            )]
        
        blocks[0].is_entry = True
        
        # Compute predecessors/successors
        for i, block in enumerate(blocks):
            # Successors
            if i < len(blocks) - 1:
                block.successors.append(blocks[i+1].start)
            # Check for explicit jumps
            if block.instructions:
                last = block.instructions[-1]
                if last.is_jump and last.target:
                    if last.target not in block.successors:
                        block.successors.append(last.target)
                if last.is_call:
                    # Call successor is the instruction after call
                    call_end = last.address + last.size
                    for b in blocks:
                        if b.start == call_end:
                            block.successors.append(b.start)
                            break
            
            # Predecessors (computed later)
        
        # Compute predecessors
        for i, block in enumerate(blocks):
            for succ_addr in block.successors:
                for j, other in enumerate(blocks):
                    if other.start == succ_addr and block.start not in other.predecessors:
                        other.predecessors.append(block.start)
        
        return blocks[0] if blocks else None
    
    def _find_inst_index(self, func: Function, addr: int) -> int:
        for i, inst in enumerate(func.instructions):
            if inst.address == addr:
                return i
        return 0
    
    def build_cfg(self, func: Function, all_funcs: dict = None) -> dict:
        """Build complete CFG for a function."""
        blocks = self.analyze_function(func, all_funcs)
        return {
            'function': func.name,
            'entry_block': blocks.start if blocks else func.start_addr,
            'blocks': [
                {
                    'start': b.start,
                    'end': b.end,
                    'inst_count': len(b.instructions),
                    'predecessors': b.predecessors,
                    'successors': b.successors,
                    'is_entry': b.is_entry,
                    'is_exit': b.is_exit,
                }
                for b in ([blocks] if blocks else [])
            ],
            'total_blocks': len([blocks] if blocks else []),
        }


# ============================================================
# TYPE RECOVERY ENGINE (Ghidra style type analyzer)
# ============================================================

class GoTypeRecovery:
    """
    Engine de recovery de tipos que recria funcionalidades
    do Ghidra e Binary Ninja para inferir tipos Go.
    """
    
    def __init__(self):
        self.known_types = set(GO_TYPES)
        self.recovered_types = {}
        self.type_hints = {}
        
    def analyze_string_patterns(self, data: bytes) -> Dict[str, Type]:
        """Analisar padrões de strings para inferir tipos."""
        types = {}
        
        # Look for Go type names in strings
        type_pattern = rb'\b[A-Z][a-zA-Z0-9_]{2,30}\b'
        for match in re.finditer(type_pattern, data):
            try:
                name = match.group(0).decode('ascii')
                if name not in self.known_types and len(name) > 3:
                    # Check if it looks like a Go type
                    if name[0].isupper() and not any(c in name for c in ' (){}[]'):
                        self.known_types.add(name)
                        types[name] = Type(name=name, size=0, is_struct=True)
            except:
                pass
        
        return types
    
    def analyze_function_signatures(self, func_name: str) -> Optional[Type]:
        """Tentar inferir tipo a partir do nome da função."""
        # Go conventions: New*, New*, Make*, Create*, Get*, Set*
        patterns = {
            r'^New[A-Z]': 'constructor',
            r'^Make[A-Z]': 'factory', 
            r'^Create[A-Z]': 'factory',
            r'^Get[A-Z]': 'accessor',
            r'^Set[A-Z]': 'mutator',
            r'^Is[A-Z]': 'predicate',
            r'^Has[A-Z]': 'predicate',
            r'^Parse[A-Z]': 'parser',
            r'^Decode[A-Z]': 'decoder',
            r'^Encode[A-Z]': 'encoder',
        }
        
        for pattern, kind in patterns.items():
            if re.match(pattern, func_name):
                return Type(name=f"{kind}_result", size=0)
        return None
    
    def infer_struct_from_usage(self, func_name: str, params: List[str]) -> Optional[Type]:
        """Inferir struct a partir de padrões de parâmetros."""
        # Look for common Go struct patterns
        struct_fields = {}
        
        # Common Go struct field names
        field_patterns = {
            'name': 'string',
            'id': 'uint64',
            'count': 'int',
            'size': 'int',
            'length': 'int',
            'data': '[]byte',
            'buffer': '[]byte',
            'content': 'string',
            'value': 'interface{}',
            'key': 'string',
            'status': 'int',
            'error': 'error',
            'err': 'error',
            'done': 'chan struct{}',
            'wg': 'sync.WaitGroup',
            'mu': 'sync.RWMutex',
            'lock': 'sync.Mutex',
            'ctx': 'context.Context',
            'config': 'Config',
            'opts': 'Options',
            'handler': 'Handler',
            'client': 'Client',
            'server': 'Server',
            'req': 'Request',
            'resp': 'Response',
            'r': 'Reader',
            'w': 'Writer',
            'reader': 'io.Reader',
            'writer': 'io.Writer',
        }
        
        for param in params:
            for field_name, field_type in field_patterns.items():
                if field_name in param.lower():
                    struct_fields[field_name] = field_type
        
        if struct_fields:
            t = Type(name=f"{func_name}_args", size=0, is_struct=True)
            t.fields = struct_fields
            return t
        
        return None
    
    def full_analysis(self, data: bytes) -> Dict[str, Type]:
        """Análise completa de tipos."""
        types = {}
        
        # 1. String-based type inference
        types.update(self.analyze_string_patterns(data))
        
        # 2. Look for Go-specific type patterns
        # Interface implementations
        iface_pattern = rb'interface\s*\{[^}]{0,500}'
        for match in re.finditer(iface_pattern, data):
            try:
                content = match.group(0).decode('ascii', errors='replace')
                # Extract method names
                methods = re.findall(r'\w+\([^)]*\)[^{]*\{', content)
                if methods:
                    type_name = f"Interface_{hashlib.md5(content[:100]).hexdigest()[:8]}"
                    types[type_name] = Type(
                        name=type_name, 
                        size=0, 
                        is_interface=True,
                        fields={m.split('(')[0]: 'method' for m in methods[:10]}
                    )
            except:
                pass
        
        # Struct definitions in strings
        struct_pattern = rb'struct\s*\{[^}]{0,500}'
        for match in re.finditer(struct_pattern, data):
            try:
                content = match.group(0).decode('ascii', errors='replace')
                fields = re.findall(r'\w+\s+\w+', content)
                if fields:
                    type_name = f"Struct_{hashlib.md5(content[:100]).hexdigest()[:8]}"
                    types[type_name] = Type(
                        name=type_name,
                        size=0,
                        is_struct=True,
                        fields={f.split()[1]: f.split()[0] for f in fields[:20] if len(f.split()) == 2}
                    )
            except:
                pass
        
        return types


# ============================================================
# FUNCTION RECONSTRUCTION ENGINE
# ============================================================

class GoFuncReconstructor:
    """
    Reconstrutor de funções que recria funcionalidades
    do Ghidra e Binary Ninja para identificar funções Go.
    """
    
    def __init__(self, md=None):
        self.md = md
        self.functions = {}
        self.known_imports = set()
        
    def find_function_boundaries(self, data: bytes, pe=None) -> List[Tuple[int, int]]:
        """Encontrar limites de funções no binário."""
        functions = []
        
        if not self.md:
            return functions
        
        # Get .text section
        text_section = None
        if pe:
            for s in pe.sections:
                if '.text' in s.name:
                    text_section = s
                    break
        
        if not text_section:
            return functions
        
        raw = bytes(text_section.content)
        entry = pe.entrypoint if pe else 0
        
        # Find function prologues (Go-specific)
        # Go uses: PUSHRBP; MOV RBP,RSP; SUB rsp, imm
        prologue_patterns = [
            b'\x55\x48\x89\xe5\x48\x83\xec',  # push rbp; mov rbp,rsp; sub rsp,
        ]
        
        # Scan for function boundaries
        i = 0
        while i < len(raw) - 10:
            # Look for RET at end of potential function
            if raw[i] == 0xC3:  # RET
                # Look backwards for function start
                # Simple heuristic: find previous RET or beginning
                start = i
                for j in range(i-1, max(0, i-0x1000), -1):
                    if raw[j] == 0xC3:  # Previous RET
                        start = j + 1
                        break
                    # Check for another function prologue
                    if j > 0 and raw[j] == 0x55 and raw[j+1:j+3] == b'\x48\x89\xe5':
                        start = j
                        break
                
                if start != i:
                    functions.append((start, i + 1))
            i += 1
        
        # Also use known entry points
        if pe:
            functions.append((entry, entry + 0x1000))  # Initial function
        
        return functions
    
    def extract_function(self, start: int, end: int, data: bytes, pe=None) -> Optional[Function]:
        """Extrair uma função completa."""
        if not self.md:
            return None
        
        # Get .text section
        text_section = None
        if pe:
            for s in pe.sections:
                if '.text' in s.name:
                    text_section = s
                    break
        
        if not text_section:
            return None
        
        # Adjust to section-relative
        section_offset = start - text_section.virtual_address + text_section.pointerto_raw_data
        if section_offset < 0 or section_offset + (end - start) > len(bytes(text_section.content)):
            return None
        
        raw = bytes(text_section.content)
        insts = list(self.md.disasm(raw[start - text_section.virtual_address:end - text_section.virtual_address], start))
        
        if not insts:
            return None
        
        # Extract name from strings
        name = self._guess_func_name(start, data)
        
        # Extract params from register usage
        params = self._extract_params(insts)
        
        # Extract return types
        returns = self._extract_returns(insts)
        
        return Function(
            name=name,
            start_addr=start,
            end_addr=end,
            size=end - start,
            instructions=[
                Instruction(
                    address=i.address,
                    mnemonic=i.mnemonic,
                    operands=i.op_str,
                    size=i.size,
                    binary=i.bytes
                )
                for i in insts
            ],
            params=params,
            return_types=returns,
            sig=self._generate_sig(name, params, returns)
        )
    
    def _guess_func_name(self, addr: int, data: bytes) -> str:
        """Adivinhar nome da função baseado em strings próximas."""
        # Search for function name strings near the address
        search_range = 0x1000
        start = max(0, addr - search_range)
        end = min(len(data), addr + search_range)
        
        chunk = data[start:end]
        
        # Look for Go-style function names
        names = re.findall(rb'[a-z][a-z0-9_]+\.[a-z][a-z0-9_]+', chunk)
        if names:
            return names[0].decode('ascii', errors='replace')
        
        # Look for PascalCase types (possible receiver type)
        types = re.findall(rb'[A-Z][a-zA-Z0-9_]{2,20}', chunk)
        if types:
            return f"{types[0].decode()}_method"
        
        return f"sub_{addr:016x}"
    
    def _extract_params(self, instructions: List) -> List[str]:
        """Extrair parâmetros da função."""
        params = []
        
        # Check for register-based param loading (Go AMD64 ABI)
        reg_params = {'rdi': 'p1', 'rsi': 'p2', 'rdx': 'p3', 'rcx': 'p4', 'r8': 'p5', 'r9': 'p6'}
        
        for inst in instructions[:20]:  # First 20 instructions
            try:
                mnem = inst.mnemonic.lower() if hasattr(inst, 'mnemonic') else str(inst).split()[0].lower()
                ops = str(inst.operands if hasattr(inst, 'operands') else inst).lower()
                
                for reg, pname in reg_params.items():
                    if reg in ops and mnem in ('mov', 'lea', 'movq'):
                        if pname not in params:
                            params.append(pname)
            except:
                pass
        
        return params
    
    def _extract_returns(self, instructions: List) -> List[str]:
        """Extrair tipos de retorno."""
        returns = []
        
        # Check for return value patterns
        for inst in instructions:
            try:
                if inst.mnemonic.lower() == 'ret':
                    # Look backwards for mov rax, ...
                    for prev in reversed(instructions):
                        try:
                            if prev.mnemonic.lower() in ('mov', 'movq', 'movabs'):
                                if 'rax' in prev.operands.lower():
                                    returns.append('uintptr')
                                    break
                            elif prev.mnemonic.lower() not in ('nop', 'lea', 'test', 'cmp'):
                                break
                        except:
                            break
                    break
            except:
                continue
        
        return returns
    
    def _generate_sig(self, name: str, params: List[str], returns: List[str]) -> str:
        """Gerar signature da função."""
        param_str = ', '.join(params) if params else ''
        return_str = ', '.join(returns) if returns else 'void'
        return f"{name}({param_str}) {return_str}"
    
    def reconstruct_all(self, data: bytes, pe=None) -> Dict[int, Function]:
        """Reconstruir todas as funções."""
        self.functions = {}
        
        # Find function boundaries
        boundaries = self.find_function_boundaries(data, pe)
        
        for start, end in boundaries:
            func = self.extract_function(start, end, data, pe)
            if func and func.size > 10:  # Minimum function size
                self.functions[start] = func
        
        return self.functions


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

class GoREEngine:
    """
    Orchestrator principal que integra todos os componentes
    de engenharia reversa para binários Go.
    """
    
    def __init__(self, exe_path: str):
        self.exe_path = exe_path
        self.file_size = os.path.getsize(exe_path)
        
        # Read file
        with open(exe_path, 'rb') as f:
            self.data = f.read(min(self.file_size, 500 * 1024 * 1024))
        
        # Initialize components
        self.pe = None
        self.md = None
        self.decompiler = GoDecompiler()
        self.cfg_analyzer = CFGAnalyzer()
        self.type_recovery = GoTypeRecovery()
        self.func_reconstructor = GoFuncReconstructor()
        
        # Results
        self.functions = {}
        self.types = {}
        self.cfgs = {}
        self.strings = {}
        
    def initialize(self):
        """Inicializar componentes."""
        print("[*] Initializing Go RE Engine...")
        
        # Load PE
        if lief:
            self.pe = lief.PE.parse(self.exe_path)
            print(f"[+] PE loaded: {self.pe.header}")
        else:
            print("[-] LIEF not available")
        
        # Initialize Capstone
        if capstone:
            self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            self.md.detail = True
            print("[+] Capstone initialized (x64)")
        else:
            print("[-] Capstone not available")
        
        # Find .text section
        self.text_section = None
        if self.pe:
            for s in self.pe.sections:
                if '.text' in s.name:
                    self.text_section = s
                    print(f"[+] .text section: VA=0x{s.virtual_address:x} size={s.virtual_size:,}")
                    break
    
    def analyze_strings(self):
        """Análise completa de strings."""
        print("\n[*] Analyzing strings...")
        
        # Extract all printable strings
        string_pattern = rb'[\x20-\x7e]{4,}'
        strings = re.findall(string_pattern, self.data)
        
        self.strings = {
            'total': len(strings),
            'go_runtime': [],
            'go_functions': [],
            'go_types': [],
            'urls': [],
            'paths': [],
            'errors': [],
            'config': [],
            'other': [],
        }
        
        for s_bytes in strings:
            try:
                s = s_bytes.decode('ascii')
            except:
                continue
            
            sl = s.lower()
            
            if any(sl.startswith(p) for p in ['runtime.', 'sync.', 'reflect.', 'unsafe.']):
                self.strings['go_runtime'].append(s)
            elif '.' in s and any(sl.startswith(p) for p in ['github.com/', 'google.']):
                self.strings['go_functions'].append(s)
            elif re.match(r'^[A-Z][a-zA-Z0-9_]{3,30}$', s):
                self.strings['go_types'].append(s)
            elif 'http' in sl or '://' in s:
                self.strings['urls'].append(s)
            elif '\\\\' in s or '/home/' in s or '/go/' in s:
                self.strings['paths'].append(s)
            elif any(kw in sl for kw in ['error', 'failed', 'unable', 'cannot']):
                self.strings['errors'].append(s)
            elif 'ANTIGRAVITY_' in s or 'AGY_' in s:
                self.strings['config'].append(s)
            else:
                self.strings['other'].append(s)
        
        print(f"[+] Found {self.strings['total']} strings")
        print(f"    - Go runtime: {len(self.strings['go_runtime'])}")
        print(f"    - Go functions: {len(self.strings['go_functions'])}")
        print(f"    - Go types: {len(self.strings['go_types'])}")
        print(f"    - URLs: {len(self.strings['urls'])}")
        print(f"    - Paths: {len(self.strings['paths'])}")
        print(f"    - Errors: {len(self.strings['errors'])}")
        print(f"    - Config: {len(self.strings['config'])}")
    
    def analyze_functions(self):
        """Análise e reconstrução de funções."""
        print("\n[*] Analyzing functions...")
        
        if not self.md or not self.pe:
            print("[-] Cannot analyze functions without Capstone/LIEF")
            return
        
        self.func_reconstructor = GoFuncReconstructor(self.md)
        self.functions = self.func_reconstructor.reconstruct_all(self.data, self.pe)
        
        print(f"[+] Reconstructed {len(self.functions)} functions")
        
        # Sort by address
        sorted_funcs = sorted(self.functions.items())
        for addr, func in sorted_funcs[:20]:
            print(f"    0x{addr:08x}: {func.name} ({func.size} bytes)")
        if len(self.functions) > 20:
            print(f"    ... and {len(self.functions)-20} more")
    
    def analyze_types(self):
        """Análise e recovery de tipos."""
        print("\n[*] Analyzing types...")
        
        self.types = self.type_recovery.full_analysis(self.data)
        
        print(f"[+] Recovered {len(self.types)} types")
        for name, typ in list(self.types.items())[:20]:
            fields = len(typ.fields) if typ.fields else 0
            print(f"    {name}: {'struct' if typ.is_struct else 'interface'} ({fields} fields)")
    
    def analyze_cfg(self):
        """Análise de fluxo de controle."""
        print("\n[*] Analyzing control flow...")
        
        if not self.md or not self.pe:
            print("[-] Cannot analyze CFG without Capstone/LIEF")
            return
        
        self.cfgs = {}
        for addr, func in list(self.functions.items())[:10]:  # First 10 functions
            cfg = self.cfg_analyzer.build_cfg(func, self.functions)
            self.cfgs[addr] = cfg
        
        print(f"[+] Analyzed CFG for {len(self.cfgs)} functions")
    
    def generate_report(self, output_dir: str):
        """Gerar relatório completo."""
        print(f"\n[*] Generating report to {output_dir}...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Main report
        report = {
            'binary': self.exe_path,
            'size': self.file_size,
            'timestamp': '2026-09-09',
            'engine': 'Go RE Toolkit v1.0',
            'strings': {
                'total': self.strings.get('total', 0),
                'categories': {
                    k: len(v) for k, v in self.strings.items() if k != 'total'
                }
            },
            'functions': {
                'total': len(self.functions),
                'sample': [
                    {
                        'addr': hex(addr),
                        'name': func.name,
                        'sig': func.sig,
                        'size': func.size,
                        'params': func.params,
                        'returns': func.return_types,
                    }
                    for addr, func in list(self.functions.items())[:50]
                ]
            },
            'types': {
                'total': len(self.types),
                'sample': [
                    {'name': name, 'is_struct': t.is_struct, 'is_interface': t.is_interface, 'fields': len(t.fields)}
                    for name, t in list(self.types.items())[:50]
                ]
            },
            'cfg': {
                'analyzed': len(self.cfgs),
            }
        }
        
        # Save JSON report
        report_path = os.path.join(output_dir, 'analysis_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"[+] Report saved: {report_path}")
        
        # Save strings
        strings_path = os.path.join(output_dir, 'strings.json')
        with open(strings_path, 'w') as f:
            json.dump({k: v[:100] for k, v in self.strings.items() if k != 'total'}, f, indent=2)
        print(f"[+] Strings saved: {strings_path}")
        
        # Save functions
        funcs_path = os.path.join(output_dir, 'functions.json')
        with open(funcs_path, 'w') as f:
            json.dump({
                hex(addr): {
                    'name': func.name,
                    'sig': func.sig,
                    'size': func.size,
                    'params': func.params,
                    'returns': func.return_types,
                    'instructions_count': len(func.instructions),
                }
                for addr, func in self.functions.items()
            }, f, indent=2, default=str)
        print(f"[+] Functions saved: {funcs_path}")
        
        return report
    
    def run_full_analysis(self, output_dir: str):
        """Executar análise completa."""
        print("=" * 60)
        print("  GO RE ENGINE v1.0 - Full Analysis")
        print("=" * 60)
        
        self.initialize()
        self.analyze_strings()
        self.analyze_functions()
        self.analyze_types()
        self.analyze_cfg()
        report = self.generate_report(output_dir)
        
        print("\n" + "=" * 60)
        print("  ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"\n  Binary:      {self.exe_path}")
        print(f"  Size:        {report['size']:,} bytes")
        print(f"  Strings:     {report['strings']['total']:,}")
        print(f"  Functions:   {report['functions']['total']}")
        print(f"  Types:       {report['types']['total']}")
        print(f"  CFG analyzed:{report['cfg']['analyzed']}")
        print(f"\n  Output:      {output_dir}/")
        
        return report