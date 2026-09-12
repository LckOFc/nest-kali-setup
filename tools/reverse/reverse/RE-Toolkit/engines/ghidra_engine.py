#!/usr/bin/env python3
"""
Ghidra Engine - Descompilador estilo Ghidra
============================================
Recria funcionalidades do Ghidra para descompilação de binários.
"""

import re
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

try:
    import capstone
except ImportError:
    capstone = None


@dataclass
class PseudoInstruction:
    """Instrução pseudo-código."""
    address: int
    lineno: int
    text: str
    indent: int = 0
    is_comment: bool = False
    is_label: bool = False
    branch_target: Optional[int] = None


@dataclass
class BasicBlock:
    """Basic block no CFG."""
    block_id: int
    start: int
    end: int
    instructions: List[dict] = field(default_factory=list)
    successors: List[int] = field(default_factory=list)
    predecessors: List[int] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    loop_depth: int = 0


@dataclass
class DecompiledFunction:
    """Função descompilada."""
    name: str
    address: int
    size: int
    signature: str
    pseudo_code: List[PseudoInstruction] = field(default_factory=list)
    basic_blocks: List[BasicBlock] = field(default_factory=list)
    calls: List[dict] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    type_info: Dict[str, str] = field(default_factory=dict)


class GhidraEngine:
    """
    Engine de descompilação estilo Ghidra.
    
    Funcionalidades:
    - Descompilação de funções completas
    - Reconstrução de estrutura de controle
    - Recovery de tipos e variáveis
    - Geração de CFG
    - Anotação de código
    """
    
    # Mapeamento de registradores Go AMD64 ABI
    GO_REG_MAP = {
        'rdi': ('arg0', 'receiver'),
        'rsi': ('arg1', 'arg1'),
        'rdx': ('arg2', 'arg2'),
        'rcx': ('arg3', 'arg3'),
        'r8': ('arg4', 'arg4'),
        'r9': ('arg5', 'arg5'),
        'rax': ('ret0', 'result'),
        'x0': ('fp0', 'float_arg1'),
        'x1': ('fp1', 'float_arg2'),
        'x2': ('fp2', 'float_arg3'),
        'x3': ('fp3', 'float_arg4'),
        'x4': ('fp4', 'float_arg5'),
        'x5': ('fp5', 'float_arg6'),
        'x6': ('fp6', 'float_arg7'),
        'x7': ('fp7', 'float_arg8'),
    }
    
    def __init__(self, toolkit=None):
        self.toolkit = toolkit
        self.md = None
        self._init_capstone()
        self.func_counter = 0
        self.var_counter = 0
        
    def _init_capstone(self):
        """Inicializar Capstone."""
        if capstone:
            self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            self.md.detail = True
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analisar arquivo completo.
        
        Returns:
            Dict com análise completa
        """
        if not self.md:
            return {'error': 'Capstone not available'}
        
        result = {
            'file': file_path,
            'functions': [],
            'types': [],
            'strings': {},
            'cfg_summary': {},
        }
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read(100 * 1024 * 1024)  # First 100MB
            
            # Extract strings
            result['strings'] = self._extract_strings(data)
            
            # Find and analyze functions
            result['functions'] = self._find_and_analyze_functions(data)
            
            # Recover types
            result['types'] = self._recover_types(data)
            
            # Build CFG summary
            result['cfg_summary'] = self._build_cfg_summary(result['functions'])
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def decompile_function(self, file_path: str, function_addr: int) -> Dict[str, Any]:
        """
        Descompilar uma função específica.
        
        Returns:
            Dict com pseudocódigo
        """
        if not self.md:
            return {'error': 'Capstone not available'}
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read(100 * 1024 * 1024)
            
            # Find function
            func_data = self._extract_function(data, function_addr)
            if not func_data:
                return {'error': 'Function not found'}
            
            # Decompile
            func = self._decompile(func_data, function_addr)
            
            return {
                'name': func.name,
                'address': hex(func.address),
                'size': func.size,
                'signature': func.signature,
                'pseudo_code': '\n'.join(instr.text for instr in func.pseudo_code),
                'basic_blocks': len(func.basic_blocks),
                'calls': func.calls,
                'variables': func.variables,
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_strings(self, data: bytes) -> Dict[str, List[str]]:
        """Extrair e categorizar strings."""
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
        
        string_pattern = rb'[\x20-\x7e]{4,}'
        count = 0
        
        for match in re.finditer(string_pattern, data):
            if count >= 50000:
                break
            try:
                s = match.group(0).decode('ascii')
            except:
                continue
            
            sl = s.lower()
            
            if any(sl.startswith(p) for p in ['runtime.', 'sync.', 'reflect.', 'unsafe.']):
                categories['go_runtime'].append(s[:100])
            elif '.' in s and any(sl.startswith(p) for p in ['github.com/', 'google.']):
                categories['go_functions'].append(s[:100])
            elif re.match(r'^[A-Z][a-zA-Z0-9_]{3,30}$', s):
                categories['go_types'].append(s)
            elif 'http' in sl or '://' in s:
                categories['urls'].append(s[:100])
            elif '\\\\' in s or '/home/' in s:
                categories['paths'].append(s[:100])
            elif any(kw in sl for kw in ['error', 'failed', 'unable', 'cannot']):
                categories['errors'].append(s[:100])
            elif 'ANTIGRAVITY_' in s or 'AGY_' in s:
                categories['config'].append(s[:100])
            else:
                categories['other'].append(s[:100])
            
            count += 1
        
        return categories
    
    def _find_and_analyze_functions(self, data: bytes) -> List[Dict]:
        """Encontrar e analisar funções."""
        functions = []
        
        # Find prologues
        prologue = b'\x55\x48\x89\xe5'
        
        for match in re.finditer(re.escape(prologue), data):
            addr = match.start()
            
            # Extract function
            func_data = self._extract_function(data, addr)
            if not func_data:
                continue
            
            func = self._decompile(func_data, addr)
            
            functions.append({
                'name': func.name,
                'address': hex(func.address),
                'size': func.size,
                'signature': func.signature,
                'basic_blocks': len(func.basic_blocks),
                'instructions': func_data['instruction_count'],
                'calls': len(func.calls),
            })
            
            if len(functions) >= 100:
                break
        
        return functions
    
    def _extract_function(self, data: bytes, addr: int) -> Optional[Dict]:
        """Extrair dados de uma função."""
        # Check if address is valid
        if addr >= len(data):
            return None
        
        # Extract function data (up to 4KB)
        func_data = data[addr:addr + 0x1000]
        
        try:
            insts = list(self.md.disasm(func_data, addr))
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
            end_addr = addr + 0x500
        
        # Convert to serializable format
        inst_list = []
        for inst in insts:
            inst_dict = {
                'address': inst.address,
                'mnemonic': inst.mnemonic,
                'operands': inst.op_str,
                'size': inst.size,
            }
            
            # Check for jump targets
            if inst.mnemonic.lower() in ('jmp', 'je', 'jne', 'jl', 'jle', 'jg', 'jge'):
                # Try to resolve target
                try:
                    # Simple heuristic: next instruction or known pattern
                    inst_dict['target'] = inst.address + inst.size
                except:
                    pass
            
            inst_list.append(inst_dict)
        
        return {
            'start_addr': addr,
            'end_addr': end_addr,
            'instructions': inst_list,
            'instruction_count': len(inst_list),
            'raw_data': func_data,
        }
    
    def _decompile(self, func_data: Dict, addr: int) -> DecompiledFunction:
        """Descompilar função para pseudocódigo."""
        insts = func_data['instructions']
        
        # Generate function name
        self.func_counter += 1
        name = f"fn_{addr:04x}_{self.func_counter:04x}"
        
        # Try to find better name from strings
        name = self._guess_func_name(addr, func_data['raw_data'])
        
        # Create function object
        func = DecompiledFunction(
            name=name,
            address=addr,
            size=func_data['end_addr'] - addr,
            signature=f"{name}()",
        )
        
        # Generate pseudo-code
        ctx = {
            'lineno': 0,
            'reg_vars': {},
            'stack_vars': {},
            'current_ret': None,
            'known_funcs': {},
        }
        
        # Header
        func.pseudo_code.append(PseudoInstruction(addr, 0, 
            f"// Function: {name}", is_comment=True))
        func.pseudo_code.append(PseudoInstruction(addr, 1,
            f"// Address: 0x{addr:x}", is_comment=True))
        func.pseudo_code.append(PseudoInstruction(addr, 2,
            f"{name}()", is_comment=False))
        func.pseudo_code.append(PseudoInstruction(addr, 3, "{", indent=0))
        ctx['lineno'] = 4
        
        # Process instructions
        i = 0
        while i < len(insts):
            inst = insts[i]
            mnem = inst['mnemonic'].lower()
            ops = inst['operands']
            
            # Track register assignments
            if mnem == 'mov' and ',' in ops:
                parts = [p.strip() for p in ops.split(',')]
                dst = parts[-1].lower()
                src = parts[0] if len(parts) > 1 else ''
                
                # Map to Go-style vars
                if dst in self.GO_REG_MAP:
                    var_name, var_type = self.GO_REG_MAP[dst]
                    ctx['reg_vars'][dst] = var_name
                    
                    if '[' in src:
                        func.pseudo_code.append(PseudoInstruction(
                            inst['address'], ctx['lineno'],
                            f"{var_name} = *{src}  // {var_type}", indent=2))
                    else:
                        func.pseudo_code.append(PseudoInstruction(
                            inst['address'], ctx['lineno'],
                            f"{var_name} = {src}", indent=2))
                    ctx['lineno'] += 1
                else:
                    func.pseudo_code.append(PseudoInstruction(
                        inst['address'], ctx['lineno'],
                        f"{dst} = {src}", indent=2))
                    ctx['lineno'] += 1
            
            # LEA - pointer arithmetic
            elif mnem == 'lea':
                parts = [p.strip() for p in ops.split(',')]
                dst = parts[-1]
                src = parts[0] if len(parts) > 1 else ''
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"{dst} = &{src}", indent=2))
                ctx['lineno'] += 1
            
            # CMP + conditional jump
            elif mnem == 'cmp':
                ctx['last_cmp'] = ops
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"// cmp {ops}", is_comment=True))
                ctx['lineno'] += 1
            
            elif mnem in ('je', 'jne', 'jl', 'jle', 'jg', 'jge',
                         'ja', 'jae', 'jb', 'jbe', 'js', 'jns'):
                cond = self._cmp_to_cond(mnem)
                target = inst.get('target', 0)
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"// if {ctx.get('last_cmp', '?')} {cond} goto 0x{target:x}",
                    is_comment=True))
                ctx['lineno'] += 1
            
            # Unconditional jump
            elif mnem == 'jmp':
                target = inst.get('target', 0)
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"// goto 0x{target:x}", is_comment=True))
                ctx['lineno'] += 1
            
            # CALL
            elif mnem == 'call':
                target = inst.get('target', 0)
                callee = f"sub_0x{target:x}" if target else "unknown_func"
                ret_var = ctx.get('current_ret', 'ret')
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"{ret_var} = {callee}({ops})", indent=2))
                ctx['lineno'] += 1
                
                # Track call
                func.calls.append({
                    'addr': hex(inst['address']),
                    'target': callee,
                })
            
            # RET
            elif mnem == 'ret':
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    "return", indent=2))
                ctx['lineno'] += 1
                break
            
            # Push/Pop
            elif mnem == 'push':
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"// push {ops}", is_comment=True))
                ctx['lineno'] += 1
            
            elif mnem == 'pop':
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"// pop {ops}", is_comment=True))
                ctx['lineno'] += 1
            
            # NOP
            elif mnem == 'nop':
                pass  # Skip NOPs
            
            # Default
            else:
                func.pseudo_code.append(PseudoInstruction(
                    inst['address'], ctx['lineno'],
                    f"{mnem.upper()}({ops})", indent=2))
                ctx['lineno'] += 1
            
            i += 1
        
        # Footer
        func.pseudo_code.append(PseudoInstruction(
            func_data['end_addr'], ctx['lineno'], "}", indent=0))
        
        # Build basic blocks
        func.basic_blocks = self._build_blocks(insts)
        
        return func
    
    def _build_blocks(self, insts: List[Dict]) -> List[BasicBlock]:
        """Construir basic blocks."""
        blocks = []
        current_start = insts[0]['address'] if insts else 0
        current_insts = []
        
        for i, inst in enumerate(insts):
            current_insts.append(inst)
            mnem = inst['mnemonic'].lower()
            
            if mnem in ('ret', 'jmp') or mnem.startswith('j'):
                block = BasicBlock(
                    block_id=len(blocks),
                    start=current_start,
                    end=inst['address'] + inst['size'],
                    instructions=current_insts,
                    is_entry=(len(blocks) == 0),
                    is_exit=(mnem == 'ret'),
                )
                blocks.append(block)
                current_start = inst['address'] + inst['size']
                current_insts = []
        
        if current_insts:
            blocks.append(BasicBlock(
                block_id=len(blocks),
                start=current_start,
                end=current_start + 0x100,  # Estimate
                instructions=current_insts,
            ))
        
        return blocks
    
    def _guess_func_name(self, addr: int, data: bytes) -> str:
        """Tentar adivinhar nome da função."""
        # Search nearby for function name patterns
        search_range = 0x500
        start = max(0, addr - search_range)
        end = min(len(data), addr + search_range)
        chunk = data[start:end]
        
        # Look for Go function patterns
        patterns = [
            rb'func\s+([a-z][a-z0-9_]*)\s*\(',
            rb'(\w+)\.([a-z][a-z0-9_]*)\s*\(',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, chunk):
                try:
                    return match.group(1).decode('ascii')
                except:
                    pass
        
        return f"fn_{addr:04x}"
    
    def _recover_types(self, data: bytes) -> List[Dict]:
        """Recuperar tipos do binário."""
        types = []
        
        # Structs
        struct_pattern = rb'struct\s*\{([^}]{0,300})\}'
        for match in re.finditer(struct_pattern, data):
            try:
                content = match.group(1).decode('ascii', errors='replace')
                fields = re.findall(r'\s+(\w+)\s+(\w+)', content)
                if fields:
                    type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                    types.append({
                        'kind': 'struct',
                        'name': f'Struct_{type_hash}',
                        'fields': len(fields),
                        'confidence': 0.7,
                    })
            except:
                pass
        
        # Interfaces
        iface_pattern = rb'interface\s*\{([^}]{0,300})\}'
        for match in re.finditer(iface_pattern, data):
            try:
                content = match.group(1).decode('ascii', errors='replace')
                methods = re.findall(r'\s*(\w+)\s*\(', content)
                if methods:
                    type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                    types.append({
                        'kind': 'interface',
                        'name': f'Interface_{type_hash}',
                        'methods': len(methods),
                        'confidence': 0.8,
                    })
            except:
                pass
        
        return types[:100]
    
    def _build_cfg_summary(self, functions: List[Dict]) -> Dict:
        """Construir resumo do CFG."""
        total_blocks = 0
        total_edges = 0
        
        for func in functions:
            total_blocks += func.get('basic_blocks', 0)
        
        return {
            'total_functions': len(functions),
            'total_blocks': total_blocks,
            'avg_blocks_per_func': total_blocks / len(functions) if functions else 0,
        }
    
    def _cmp_to_cond(self, mnem: str) -> str:
        """Converter jump para condição."""
        cond_map = {
            'je': '==', 'jz': '==0',
            'jne': '!=', 'jnz': '!=0',
            'jl': '<', 'jle': '<=',
            'jg': '>', 'jge': '>=',
            'ja': '>', 'jae': '>=',
            'jb': '<', 'jbe': '<=',
            'js': '<0', 'jns': '>=0',
        }
        return cond_map.get(mnem, mnem)
    
    def generate_dot(self, func: DecompiledFunction) -> str:
        """Gerar graph DOT para visualização."""
        lines = [f'digraph "{func.name}" {{',
                 '  rankdir=TB;',
                 '  node [shape=box];',
                 '']
        
        for block in func.basic_blocks:
            label = f"B{block.block_id}"
            if block.is_entry:
                label += " [entry]"
            if block.is_exit:
                label += " [exit]"
            lines.append(f'  B{block.block_id} [label="{label}\\n{len(block.instructions)} insns"];')
        
        lines.append('')
        
        for i, block in enumerate(func.basic_blocks):
            # Simulate successors
            if i < len(func.basic_blocks) - 1:
                lines.append(f'  B{i} -> B{i+1};')
        
        lines.append('}')
        return '\n'.join(lines)


# Quick test
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        engine = GhidraEngine()
        result = engine.analyze_file(sys.argv[1])
        print(f"Functions found: {len(result.get('functions', []))}")
        print(f"Types recovered: {len(result.get('types', []))}")
        print(f"Strings: {sum(len(v) for v in result.get('strings', {}).values())}")
    else:
        print("Usage: python ghidra_engine.py <binary>")
