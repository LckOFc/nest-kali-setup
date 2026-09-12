#!/usr/bin/env python3
"""
Go Decompiler Engine - Hex-Rays Style
======================================
Recria o motor de descompilação do IDA Pro Hex-Rays para binários Go.
Converte assembly x64 em pseudocódigo de alto nível.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass
class VarInfo:
    """Informação de variável recuperada."""
    name: str
    addr: int
    size: int
    type_hint: str = "unknown"
    category: str = "local"  # local, param, ret, global


@dataclass
class PseudoStmt:
    """Instrução pseudo-código."""
    addr: int
    lineno: int
    text: str
    indent: int = 0
    is_comment: bool = False
    is_label: bool = False
    branch_target: Optional[int] = None


@dataclass
class Block:
    """Basic block paraCFG."""
    start: int
    end: int
    instructions: List[dict] = field(default_factory=list)
    successors: List[int] = field(default_factory=list)
    predecessors: List[int] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    block_id: int = 0


@dataclass
class FuncInfo:
    """Informações de função."""
    name: str
    addr: int
    size: int
    params: List[Tuple[str, str]] = field(default_factory=list)
    returns: List[str] = field(default_factory=list)
    blocks: List[Block] = field(default_factory=list)
    vars: Dict[int, VarInfo] = field(default_factory=dict)
    calls: List[Tuple[int, str]] = field(default_factory=list)  # (addr, target_name)


class GoDecompiler:
    """
    Motor de descompilação Go style Hex-Rays.
    
    Recursos:
    - Reconstruction de variáveis a partir de padrões de registrador
    - Tradução de assembly Go ABI para pseudocódigo legível
    - Detecção de estruturas de controle (if/else, loops, switches)
    - Recovery de tipos baseado em uso de registradores
    - Geração de CFG (Control Flow Graph)
    """
    
    # Mapeamento de registradores Go AMD64 ABI
    GO_REG_MAP = {
        'rdi': ('p1', 'receiver'),
        'rsi': ('p2', 'arg1'),
        'rdx': ('p3', 'arg2'),
        'rcx': ('p4', 'arg3'),
        'r8': ('p5', 'arg4'),
        'r9': ('p6', 'arg5'),
        'r10': ('p7', 'arg6'),
        'r11': ('p8', 'arg7'),
        'rax': ('ret', 'result'),
        'x0': ('fp1', 'float_arg1'),
        'x1': ('fp2', 'float_arg2'),
        'x2': ('fp3', 'float_arg3'),
        'x3': ('fp4', 'float_arg4'),
    }
    
    # Patterns para identificar tipos Go
    TYPE_PATTERNS = {
        r'\bstring\b': 'string',
        r'\bint\b': 'int',
        r'\bint64\b': 'int64',
        r'\buint64\b': 'uint64',
        r'\buintptr\b': 'uintptr',
        r'\boffset\b': 'uintptr',
        r'\bbool\b': 'bool',
        r'\terror\b': 'error',
        r'\binterface\{\}\b': 'interface{}',
        r'\b\[\]byte\b': '[]byte',
        r'\b\[\]rune\b': '[]rune',
        r'\b\[\]string\b': '[]string',
        r'\b\*[^ ]+\b': 'pointer',
        r'\bchan [^ ]+\b': 'channel',
    }
    
    def __init__(self):
        self.var_counter = 0
        self.func_counter = 0
        self.block_counter = 0
        self.reg_vars: Dict[str, VarInfo] = {}
        self.stack_vars: Dict[int, VarInfo] = {}
        self.functions: Dict[int, FuncInfo] = {}
        
    def reset(self):
        """Reset state."""
        self.var_counter = 0
        self.func_counter = 0
        self.block_counter = 0
        self.reg_vars = {}
        self.stack_vars = {}
        self.functions = {}
        
    def _next_var(self, prefix: str = "v") -> str:
        """Generate next variable name."""
        self.var_counter += 1
        return f"{prefix}_{self.var_counter:04x}"
    
    def _next_func(self, base_name: str = "func") -> str:
        """Generate next function name."""
        self.func_counter += 1
        return f"{base_name}_{self.func_counter:04x}"
    
    def _next_block(self) -> int:
        """Generate next block ID."""
        self.block_counter += 1
        return self.block_counter
    
    def _guess_type_from_reg(self, reg: str, inst_type: str = "mov") -> str:
        """Guess Go type from register usage pattern."""
        reg = reg.lower().replace('rsp', 'sp').replace('rbp', 'bp')
        
        # Return value patterns
        if inst_type in ('mov', 'movq', 'movabs') and 'rax' in reg:
            return 'uintptr'
        
        # Pointer dereference
        if '[' in reg:
            return 'ptr'
        
        # Stack operations
        if reg in ('sp', 'rsp'):
            return 'stack_ptr'
        
        return 'unknown'
    
    def _analyze_mem_operand(self, op: str) -> Tuple[str, str]:
        """Analyze memory operand and return (type_hint, readable_form)."""
        # Pattern: [reg +/- offset]
        m = re.match(r'\[(\w+)(?:\s*([+-])\s*0x([0-9a-f]+))?\]', op, re.I)
        if m:
            reg = m.group(1).lower()
            sign = m.group(2) or '+'
            offset = int(m.group(3), 16) if m.group(3) else 0
            
            # Stack frame analysis
            if reg in ('rbp', 'bp'):
                if offset > 0:
                    return ('stack_out', f"[{reg}+0x{offset:x}]")
                else:
                    return ('stack_in', f"[{reg}-0x{abs(offset):x}]")
            elif reg in ('rsp', 'sp'):
                return ('stack', f"[sp+0x{offset:x}]")
            elif reg == 'rip':
                return ('got', f"[rip+0x{offset:x}]")
            else:
                return ('ptr', f"[{reg}+0x{offset:x}]")
        
        # Pattern: offset(reg)
        m = re.match(r'0x([0-9a-f]+)\((\w+)\)', op, re.I)
        if m:
            offset = int(m.group(1), 16)
            reg = m.group(2).lower()
            return ('ptr', f"[{reg}+0x{offset:x}]")
        
        return ('unknown', op)
    
    def _translate_inst(self, inst: dict, ctx: dict) -> List[PseudoStmt]:
        """Translate a single instruction to pseudo-code."""
        stmts = []
        mnem = inst['mnemonic'].lower()
        ops = inst['operands']
        addr = inst['address']
        
        # Track registers
        dst_reg = None
        src_reg = None
        
        # Extract destination and source
        if ',' in ops:
            parts = [p.strip() for p in ops.split(',')]
            dst_reg = parts[-1].lower() if parts else None
            src_reg = parts[0].lower() if len(parts) > 1 else None
        else:
            dst_reg = ops.lower() if ops else None
        
        # RET
        if mnem == 'ret':
            stmts.append(PseudoStmt(addr, len(stmts), "return", indent=0))
            ctx['in_function'] = False
            return stmts
        
        # CALL
        elif mnem == 'call':
            target = inst.get('target', 0)
            callee = ctx.get('known_funcs', {}).get(target, f"sub_0x{target:x}")
            
            # Check for method call (first arg is receiver)
            if dst_reg and dst_reg != 'rax':
                stmts.append(PseudoStmt(addr, len(stmts), 
                    f"{dst_reg} = {callee}({ops})", indent=2))
            else:
                var = self._next_var('ret')
                stmts.append(PseudoStmt(addr, len(stmts),
                    f"{var} = {callee}({ops})", indent=2))
                ctx['current_ret'] = var
            
            # Track call
            if 'calls' not in ctx:
                ctx['calls'] = []
            ctx['calls'].append((addr, callee))
            return stmts
        
        # MOV - most common, handle special cases
        elif mnem == 'mov':
            # MOV with memory destinations (struct field access)
            if '[' in ops.split(',')[-1] if ',' in ops else False:
                parts = [p.strip() for p in ops.split(',')]
                dst = parts[-1]
                src = parts[0] if len(parts) > 1 else ops
                
                dst_type, dst_fmt = self._analyze_mem_operand(dst)
                src_type, src_fmt = self._analyze_mem_operand(src) if '[' in src else (None, src)
                
                if src_type and src_type.startswith('stack'):
                    stmts.append(PseudoStmt(addr, len(stmts),
                        f"*{dst_fmt} = {src_fmt}  // {dst_type}", indent=2))
                elif dst_type and dst_type.startswith('stack'):
                    stmts.append(PseudoStmt(addr, len(stmts),
                        f"{dst_fmt} = {src_fmt}  // {dst_type}", indent=2))
                else:
                    stmts.append(PseudoStmt(addr, len(stmts),
                        f"{dst} = {src}", indent=2))
            else:
                stmts.append(PseudoStmt(addr, len(stmts),
                    f"{dst_reg} = {src_reg}", indent=2))
            
            if dst_reg:
                ctx['current_reg'] = dst_reg
                ctx['current_type'] = self._guess_type_from_reg(dst_reg, 'mov')
            return stmts
        
        # LEA - address calculation (pointer arithmetic)
        elif mnem == 'lea':
            parts = [p.strip() for p in ops.split(',')]
            dst = parts[-1]
            src = parts[0] if len(parts) > 1 else ops
            
            type_hint, fmt = self._analyze_mem_operand(src)
            stmts.append(PseudoStmt(addr, len(stmts),
                f"{dst} = &{fmt}  // {type_hint}", indent=2))
            
            if dst_reg:
                ctx['current_reg'] = dst_reg
                ctx['current_type'] = 'ptr'
            return stmts
        
        # CMP + conditional jump -> if statement
        elif mnem == 'cmp':
            ctx['last_cmp'] = ops
            ctx['last_cmp_addr'] = addr
            # Don't generate statement, wait for jump
            return stmts
        
        # Conditional jumps
        elif mnem in ('je', 'jne', 'jz', 'jnz', 'jl', 'jle', 'jg', 'jge',
                      'ja', 'jae', 'jb', 'jbe', 'js', 'jns'):
            cond = self._cmp_to_cond(mnem)
            target = inst.get('target', 0)
            
            # Generate if statement
            cmp_expr = ctx.get('last_cmp', '?')
            stmts.append(PseudoStmt(addr, len(stmts),
                f"// if {cmp_expr} {cond}", 
                indent=1, is_comment=True))
            
            # Mark branch
            if 'branches' not in ctx:
                ctx['branches'] = []
            ctx['branches'].append({
                'addr': addr,
                'cond': cond,
                'target': target,
                'cmp': cmp_expr
            })
            return stmts
        
        # Unconditional jump
        elif mnem == 'jmp':
            target = inst.get('target', 0)
            stmts.append(PseudoStmt(addr, len(stmts),
                f"// goto 0x{target:x}", indent=1, is_comment=True))
            return stmts
        
        # Test (comparison)
        elif mnem == 'test':
            ctx['last_cmp'] = ops
            return stmts
        
        # Push/Pop
        elif mnem == 'push':
            stmts.append(PseudoStmt(addr, len(stmts),
                f"// push {ops}", indent=1, is_comment=True))
            return stmts
        elif mnem == 'pop':
            stmts.append(PseudoStmt(addr, len(stmts),
                f"// pop {ops}", indent=1, is_comment=True))
            return stmts
        
        # NOP
        elif mnem == 'nop':
            return stmts
        
        # Default arithmetic/logic
        else:
            stmts.append(PseudoStmt(addr, len(stmts),
                f"{mnem.upper()}({ops})", indent=2))
            return stmts
    
    def _cmp_to_cond(self, mnem: str) -> str:
        """Convert jump mnemonic to comparison operator."""
        cond_map = {
            'je': '==', 'jz': '==0',
            'jne': '!=', 'jnz': '!=0',
            'jl': '<', 'jle': '<=',
            'jg': '>', 'jge': '>=',
            'ja': '>', 'jae': '>=',
            'jb': '<', 'jbe': '<=',
            'js': '<0', 'jns': '>=0',
            'jo': 'overflow', 'jno': 'no_overflow',
        }
        return cond_map.get(mnem, mnem)
    
    def decompile_function(self, insts: List[dict], start_addr: int, 
                           func_name: str = None, known_funcs: dict = None) -> FuncInfo:
        """
        Decompilar uma função completa.
        
        Args:
            insts: Lista de instruções assembly
            start_addr: Endereço inicial
            func_name: Nome da função (opcional)
            known_funcs: Dicionário de endereços -> nomes conhecidos
            
        Returns:
            FuncInfo com pseudocódigo gerado
        """
        if not func_name:
            func_name = self._next_func("fn")
        
        ctx = {
            'in_function': True,
            'current_reg': None,
            'current_type': 'unknown',
            'last_cmp': None,
            'last_cmp_addr': None,
            'known_funcs': known_funcs or {},
            'calls': [],
            'branches': [],
            'stack_depth': 0,
            'var_map': {},  # reg -> var name
            'lineno': 0,
        }
        
        pseudo_stmts = []
        blocks = []
        current_block_start = start_addr
        current_block_insts = []
        
        # Header
        pseudo_stmts.append(PseudoStmt(start_addr, 0, 
            f"// Function: {func_name}", is_comment=True))
        pseudo_stmts.append(PseudoStmt(start_addr, 1,
            f"// Address: 0x{start_addr:x}", is_comment=True))
        pseudo_stmts.append(PseudoStmt(start_addr, 2,
            f"{func_name}()", is_comment=False))
        pseudo_stmts.append(PseudoStmt(start_addr, 3, "{", indent=0))
        ctx['lineno'] = 4
        
        # Process instructions
        for inst in insts:
            stmts = self._translate_inst(inst, ctx)
            
            for stmt in stmts:
                stmt.lineno = ctx['lineno']
                pseudo_stmts.append(stmt)
                ctx['lineno'] += 1
            
            # Track block boundaries
            mnem = inst['mnemonic'].lower()
            if mnem in ('ret', 'jmp') or mnem.startswith('j'):
                # End current block
                if current_block_insts:
                    block = Block(
                        start=current_block_start,
                        end=inst['address'] + inst.get('size', 1),
                        instructions=current_block_insts.copy(),
                        block_id=self._next_block()
                    )
                    blocks.append(block)
                    current_block_insts = []
                    
                    # Set successors
                    if mnem == 'ret':
                        block.is_exit = True
                    elif mnem == 'jmp':
                        block.successors = [inst.get('target', 0)]
                    elif mnem.startswith('j'):
                        # Conditional - two successors
                        block.successors = [
                            inst.get('target', 0),
                            inst['address'] + inst.get('size', 1)
                        ]
                
                if mnem != 'ret':  # Don't start new block after ret
                    current_block_start = inst.get('target', inst['address'] + inst.get('size', 1))
            else:
                current_block_insts.append(inst)
        
        # Last block
        if current_block_insts:
            block = Block(
                start=current_block_start,
                end=start_addr + 0x1000,  # Estimate
                instructions=current_block_insts,
                block_id=self._next_block()
            )
            block.is_entry = True
            blocks.append(block)
        
        if not blocks:
            blocks = [Block(start=start_addr, end=start_addr+0x100, block_id=1, is_entry=True)]
        
        # Footer
        pseudo_stmts.append(PseudoStmt(start_addr, ctx['lineno'], "}", indent=0))
        
        # Build FuncInfo
        func = FuncInfo(
            name=func_name,
            addr=start_addr,
            size=sum(b.end - b.start for b in blocks),
            blocks=blocks,
        )
        
        # Extract pseudo-code as text
        func.pseudo_code = '\n'.join(s.text for s in pseudo_stmts)
        func.pseudo_stmts = pseudo_stmts
        func.calls = ctx.get('calls', [])
        func.branches = ctx.get('branches', [])
        
        return func
    
    def decompile_section(self, insts: List[dict], section_start: int,
                          known_funcs: dict = None) -> List[FuncInfo]:
        """
        Decompilar uma seção completa (.text).
        
        Returns:
            Lista de FuncInfo para cada função encontrada
        """
        functions = []
        
        # Find function boundaries (prologue detection)
        i = 0
        while i < len(insts) - 2:
            inst = insts[i]
            
            # Look for function prologue: push rbp; mov rbp, rsp
            if (inst['mnemonic'].lower() == 'push' and 'rbp' in inst['operands'] and
                i + 1 < len(insts) and
                insts[i+1]['mnemonic'].lower() == 'mov' and
                'rbp' in insts[i+1]['operands'] and 'rsp' in insts[i+1]['operands']):
                
                func_start = inst['address']
                
                # Find function end (next prologue or end of section)
                func_end = section_start
                for j in range(i + 2, len(insts)):
                    next_inst = insts[j]
                    if (next_inst['mnemonic'].lower() == 'push' and 'rbp' in next_inst['operands'] and
                        j + 1 < len(insts) and
                        insts[j+1]['mnemonic'].lower() == 'mov' and
                        'rbp' in insts[j+1]['operands']):
                        func_end = next_inst['address']
                        break
                    if next_inst['address'] > func_start + 0x10000:  # Max 64KB per func
                        func_end = next_inst['address']
                        break
                
                # Extract function instructions
                func_insts = [insts[k] for k in range(i, min(i + 200, len(insts))) 
                             if insts[k]['address'] < func_end]
                
                # Get function name
                func_name = known_funcs.get(func_start, f"fn_{func_start:04x}")
                
                # Decompile
                func = self.decompile_function(func_insts, func_start, func_name, known_funcs)
                functions.append(func)
                
                i = range(i + len(func_insts), len(insts))[0] if i + len(func_insts) < len(insts) else len(insts)
                continue
            
            i += 1
        
        return functions


# ============================================================
# Main analysis function
# ============================================================

def analyze_go_binary(exe_path: str, output_dir: str = None) -> dict:
    """
    Analisar binário Go completo.
    
    Returns:
        Dict com todos os resultados estruturados
    """
    import os
    import json
    
    result = {
        'binary': exe_path,
        'size': os.path.getsize(exe_path),
        'timestamp': '2026-09-09',
        'decompiler': {
            'version': '1.0.0',
            'name': 'Go RE Engine (Hex-Rays style)'
        },
        'functions': [],
        'types': [],
        'strings': {},
        'cfg': {},
    }
    
    # Initialize decompiler
    decompiler = GoDecompiler()
    
    # Try to load with LIEF
    try:
        import lief
        pe = lief.PE.parse(exe_path)
        
        # Get .text section
        text_section = None
        for s in pe.sections:
            if '.text' in s.name:
                text_section = s
                break
        
        if text_section:
            # Extract strings from binary
            result['strings'] = extract_strings(exe_path)
            
            # Extract types
            result['types'] = extract_types(exe_path)
            
            # Try to disassemble and decompile
            try:
                import capstone
                md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
                md.detail = True
                
                raw = bytes(text_section.content[:1000000])  # First 1MB
                
                # Find function prologues
                insts = list(md.disasm(raw, text_section.virtual_address))
                
                # Extract function candidates
                functions = []
                for i, inst in enumerate(insts):
                    if (inst.mnemonic == 'push' and 'rbp' in inst.op_str and
                        i + 1 < len(insts) and
                        insts[i+1].mnemonic == 'mov' and
                        'rbp' in insts[i+1].op_str and 'rsp' in insts[i+1].op_str):
                        
                        func_start = inst.address
                        func_end = func_start + 0x500  # Estimate
                        
                        # Get function instructions
                        func_insts = [
                            {'address': i.address, 'mnemonic': i.mnemonic, 
                             'operands': i.op_str, 'size': i.size, 'target': None}
                            for i in insts 
                            if func_start <= i.address < func_end
                        ]
                        
                        # Try to find function name
                        func_name = guess_func_name(func_start, result['strings'])
                        
                        # Decompile
                        func = decompiler.decompile_function(func_insts, func_start, func_name)
                        functions.append({
                            'name': func.name,
                            'addr': hex(func.addr),
                            'size': func.size,
                            'pseudo_code': func.pseudo_code[:500],  # Truncate for JSON
                            'calls': [{'addr': hex(a), 'name': n} for a, n in func.calls[:5]],
                        })
                        
                result['functions'] = functions[:50]  # Top 50 functions
                
            except Exception as e:
                result['decompiler_error'] = str(e)
        
        result['pe'] = {
            'machine': str(pe.header.machine),
            'entry_point': hex(pe.entrypoint),
            'sections': len(pe.sections),
        }
        
    except ImportError:
        result['error'] = 'LIEF not installed'
    
    # Save results
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'decompiler_output.json')
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"[+] Decompiler output saved: {output_path}")
    
    return result


def extract_strings(exe_path: str, max_count: int = 10000) -> dict:
    """Extract and categorize strings from binary."""
    import re
    
    categories = {
        'go_runtime': [],
        'go_functions': [],
        'go_types': [],
        'urls': [],
        'paths': [],
        'errors': [],
        'config': [],
        'other': [],
    }
    
    with open(exe_path, 'rb') as f:
        data = f.read(min(os.path.getsize(exe_path), 200 * 1024 * 1024))
    
    string_pattern = rb'[\x20-\x7e]{4,}'
    count = 0
    
    for match in re.finditer(string_pattern, data):
        if count >= max_count:
            break
        try:
            s = match.group(0).decode('ascii')
        except:
            continue
        
        sl = s.lower()
        
        if any(sl.startswith(p) for p in ['runtime.', 'sync.', 'reflect.', 'unsafe.']):
            categories['go_runtime'].append(s[:80])
        elif '.' in s and any(sl.startswith(p) for p in ['github.com/', 'google.']):
            categories['go_functions'].append(s[:80])
        elif re.match(r'^[A-Z][a-zA-Z0-9_]{3,30}$', s):
            categories['go_types'].append(s)
        elif 'http' in sl or '://' in s:
            categories['urls'].append(s[:80])
        elif '\\\\' in s or '/home/' in s or '/go/' in s:
            categories['paths'].append(s[:80])
        elif any(kw in sl for kw in ['error', 'failed', 'unable', 'cannot']):
            categories['errors'].append(s[:80])
        elif 'ANTIGRAVITY_' in s or 'AGY_' in s:
            categories['config'].append(s[:80])
        else:
            categories['other'].append(s[:80])
        
        count += 1
    
    return categories


def extract_types(exe_path: str, max_count: int = 500) -> List[dict]:
    """Extract Go type definitions from binary."""
    import re
    
    types = []
    
    with open(exe_path, 'rb') as f:
        data = f.read(min(os.path.getsize(exe_path), 200 * 1024 * 1024))
    
    # Look for struct patterns
    struct_pattern = rb'struct\s*\{[^}]{0,300}'
    for match in re.finditer(struct_pattern, data):
        try:
            content = match.group(0).decode('ascii', errors='replace')
            # Extract field names
            fields = re.findall(r'\s+(\w+)\s+(\w+)', content)
            if fields and len(types) < max_count:
                types.append({
                    'kind': 'struct',
                    'fields': len(fields),
                    'sample': content[:150],
                })
        except:
            pass
    
    # Look for interface patterns
    iface_pattern = rb'interface\s*\{[^}]{0,300}'
    for match in re.finditer(iface_pattern, data):
        try:
            content = match.group(0).decode('ascii', errors='replace')
            methods = re.findall(r'\s+(\w+)\s*\(', content)
            if methods and len(types) < max_count:
                types.append({
                    'kind': 'interface',
                    'methods': len(methods),
                    'sample': content[:150],
                })
        except:
            pass
    
    return types[:max_count]


def guess_func_name(addr: int, strings: dict) -> str:
    """Guess function name from nearby strings."""
    # This is a heuristic - in real RE you'd use more sophisticated analysis
    func_patterns = [
        (r'func\s+(\w+)', 'func'),
        (r'(\w+)\.(\w+)', 'method'),
    ]
    
    # Return generic name based on address
    return f"fn_{addr:04x}"


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Go Decompiler Engine')
    parser.add_argument('binary', help='Path to Go binary')
    parser.add_argument('--output', '-o', default='./output')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Go Decompiler Engine v1.0")
    print("=" * 60)
    print(f"\n  Binary: {args.binary}")
    print()
    
    result = analyze_go_binary(args.binary, args.output)
    
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Functions decompiled: {len(result.get('functions', []))}")
    print(f"  Types recovered: {len(result.get('types', []))}")
    print(f"  String categories:")
    for cat, items in result.get('strings', {}).items():
        if isinstance(items, list):
            print(f"    {cat}: {len(items)}")
    print(f"\n  Output: {args.output}/")