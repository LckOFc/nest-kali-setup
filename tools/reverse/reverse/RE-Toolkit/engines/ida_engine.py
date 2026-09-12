#!/usr/bin/env python3
"""
IDA Pro Engine - Análise avançada estilo IDA Pro
=================================================
Recria funcionalidades avançadas de análise de binários.
"""

import os
import re
import struct
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum


class InstructionType(Enum):
    CONTROL_FLOW = 'control_flow'
    DATA_ACCESS = 'data_access'
    ARITHMETIC = 'arithmetic'
    LOGIC = 'logic'
    CALL = 'call'
    RETURN = 'return'
    LOAD_STORE = 'load_store'
    COMPARISON = 'comparison'
    SHIFT = 'shift'
    OTHER = 'other'


@dataclass
class IDAFunction:
    """Função no estilo IDA."""
    start_ea: int
    end_ea: int
    name: str
    type: str  # function type
    args: List[str] = field(default_factory=list)
    ret_type: str = 'void'
    flags: int = 0
    extra: List[str] = field(default_factory=list)
    margin: int = 0
    frame: dict = field(default_factory=dict)


@dataclass
class IDAItem:
    """Item no banco de dados IDA."""
    ea: int
    name: str
    type: str
    size: int = 0
    value: Any = None
    comments: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class IDAEngine:
    """
    Engine de análise avançada estilo IDA Pro.
    
    Funcionalidades:
    - Análise de funções com detalhes
    - Identificação de estrutura de dados
    - Análise de tipos complexos
    - Geração de pseudocódigo avançado
    - Cross-references
    - Funções de utilidade
    """
    
    def __init__(self, toolkit=None):
        self.toolkit = toolkit
        self.functions: Dict[int, IDAFunction] = {}
        self.items: Dict[int, IDAItem] = {}
        self.type_database: Dict[str, Any] = {}
        self._md = None
        
        try:
            import capstone
            self._md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            self._md.detail = True
        except:
            pass
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Analisar arquivo com IDA-style analysis."""
        result = {
            'file': file_path,
            'functions': [],
            'structures': [],
            'enums': [],
            'imports': [],
            'exports': [],
            'entry_points': [],
            'analysis_info': {},
        }
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read(100 * 1024 * 1024)
            
            # Analyze PE structure
            pe_info = self._analyze_pe(data)
            result['analysis_info'] = pe_info
            
            # Find entry points
            result['entry_points'] = pe_info.get('entry_points', [])
            
            # Analyze imports
            result['imports'] = pe_info.get('imports', [])
            
            # Analyze exports
            result['exports'] = pe_info.get('exports', [])
            
            # Analyze functions
            result['functions'] = self._ida_analyze_functions(data)
            
            # Analyze structures
            result['structures'] = self._ida_analyze_structures(data)
            
            # Create IDA items
            self._create_ida_items(result)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_function_at(self, file_path: str, ea: int) -> Dict[str, Any]:
        """Obter função em endereço específico."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read(50 * 1024 * 1024)
            
            # Find function
            func = None
            for func_ea, f in self.functions.items():
                if func_ea == ea:
                    func = f
                    break
            
            if not func:
                # Try to find nearby function
                for func_ea, f in self.functions.items():
                    if abs(func_ea - ea) < 0x100:
                        func = f
                        break
            
            if func:
                return {
                    'success': True,
                    'function': {
                        'start_ea': hex(func.start_ea),
                        'end_ea': hex(func.end_ea),
                        'name': func.name,
                        'type': func.type,
                        'args': func.args,
                        'ret_type': func.ret_type,
                        'flags': func.flags,
                    }
                }
            
            return {'success': False, 'error': 'Função não encontrada'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_item_at(self, file_path: str, ea: int) -> Dict[str, Any]:
        """Obter item no endereço."""
        item = self.items.get(ea)
        if item:
            return {'success': True, 'item': self._item_to_dict(item)}
        return {'success': False, 'error': 'Item não encontrado'}
    
    def get_xrefs_to(self, file_path: str, ea: int) -> Dict[str, Any]:
        """Obter cross-references para endereço."""
        xrefs = []
        
        for item_ea, item in self.items.items():
            if item.value == ea or (isinstance(item.value, int) and item.value == ea):
                xrefs.append({
                    'from': hex(item_ea),
                    'type': 'data_ref',
                    'item_name': item.name,
                })
        
        # Also check functions
        for func_ea, func in self.functions.items():
            for arg in func.args:
                try:
                    if int(arg, 16) == ea:
                        xrefs.append({
                            'from': hex(func_ea),
                            'type': 'call_ref',
                            'item_name': func.name,
                        })
                except:
                    pass
        
        return {
            'success': True,
            'target': hex(ea),
            'xrefs': xrefs[:50],
            'count': len(xrefs),
        }
    
    def get_xrefs_from(self, file_path: str, ea: int) -> Dict[str, Any]:
        """Obter cross-references de endereço."""
        xrefs = []
        
        func = self.functions.get(ea)
        if func:
            # Function calls
            for arg in func.args:
                try:
                    target = int(arg, 16)
                    xrefs.append({
                        'to': hex(target),
                        'type': 'call',
                        'arg': arg,
                    })
                except:
                    pass
        
        return {
            'success': True,
            'source': hex(ea),
            'xrefs': xrefs[:50],
            'count': len(xrefs),
        }
    
    def create_structure(self, name: str, fields: List[Dict]) -> Dict[str, Any]:
        """Criar estrutura."""
        self.type_database[name] = {
            'type': 'struct',
            'fields': fields,
            'size': sum(f.get('size', 8) for f in fields),
        }
        return {'success': True, 'name': name}
    
    def create_enum(self, name: str, values: Dict[str, int]) -> Dict[str, Any]:
        """Criar enumeração."""
        self.type_database[name] = {
            'type': 'enum',
            'values': values,
        }
        return {'success': True, 'name': name}
    
    def set_comment(self, ea: int, comment: str, repeatable: bool = False) -> Dict[str, Any]:
        """Adicionar comentário."""
        item = self.items.get(ea)
        if item:
            item.comments.append(comment)
        else:
            self.items[ea] = IDAItem(ea=ea, name=f'unnamed_{ea:x}', type='code', comments=[comment])
        return {'success': True}
    
    def set_name(self, ea: int, name: str) -> Dict[str, Any]:
        """Definir nome."""
        item = self.items.get(ea)
        if item:
            item.name = name
        else:
            self.items[ea] = IDAItem(ea=ea, name=name, type='code')
        return {'success': True}
    
    # ============================================================
    # METODOS INTERNOS
    # ============================================================
    
    def _analyze_pe(self, data: bytes) -> Dict:
        """Analisar estrutura PE."""
        result = {
            'entry_points': [],
            'imports': [],
            'exports': [],
            'sections': [],
        }
        
        # Check MZ header
        if data[:2] != b'MZ':
            return result
        
        # Get PE offset
        pe_offset = struct.unpack('<I', data[60:64])[0]
        
        # Check PE signature
        if data[pe_offset:pe_offset+4] != b'PE\x00\x00':
            return result
        
        # Parse COFF header
        coff_offset = pe_offset + 4
        machine = struct.unpack('<H', data[coff_offset:coff_offset+2])[0]
        num_sections = struct.unpack('<H', data[coff_offset+2:coff_offset+4])[0]
        
        result['machine'] = 'AMD64' if machine == 0x8664 else 'x86'
        
        # Parse optional header
        opt_offset = coff_offset + 20
        magic = struct.unpack('<H', data[opt_offset:opt_offset+2])[0]
        
        if magic == 0x20b:  # PE32+
            entry_point = struct.unpack('<I', data[opt_offset+16:opt_offset+20])[0]
            result['entry_points'] = [entry_point]
        elif magic == 0x10b:  # PE32
            entry_point = struct.unpack('<I', data[opt_offset+16:opt_offset+20])[0]
            result['entry_points'] = [entry_point]
        
        # Parse sections
        section_offset = opt_offset + 24 + (240 if magic == 0x20b else 224)
        for i in range(min(num_sections, 20)):
            sec_offset = section_offset + i * 40
            sec_name = data[sec_offset:sec_offset+8].split(b'\x00')[0].decode('ascii', errors='replace')
            sec_vsize = struct.unpack('<I', data[sec_offset+8:sec_offset+12])[0]
            sec_vaddr = struct.unpack('<I', data[sec_offset+12:sec_offset+16])[0]
            sec_rawsize = struct.unpack('<I', data[sec_offset+16:sec_offset+20])[0]
            sec_rawptr = struct.unpack('<I', data[sec_offset+20:sec_offset+24])[0]
            
            result['sections'].append({
                'name': sec_name,
                'virtual_size': sec_vsize,
                'virtual_address': sec_vaddr,
                'raw_size': sec_rawsize,
                'raw_address': sec_rawptr,
            })
        
        # Parse imports (simplified)
        # Look for common DLL names
        dll_patterns = [
            (b'KERNEL32.dll', 'kernel32'),
            (b'ntdll.dll', 'ntdll'),
            (b'USER32.dll', 'user32'),
            (b'advapi32.dll', 'advapi32'),
        ]
        
        for pattern, name in dll_patterns:
            if pattern in data:
                result['imports'].append({
                    'name': name,
                    'address': data.find(pattern),
                })
        
        return result
    
    def _ida_analyze_functions(self, data: bytes) -> List[Dict]:
        """Analisar funções no estilo IDA."""
        functions = []
        
        if not self._md:
            return functions
        
        # Find function prologues
        prologue = b'\x55\x48\x89\xe5'
        
        for match in re.finditer(re.escape(prologue), data):
            addr = match.start()
            
            # Extract instructions
            func_data = data[addr:addr + 0x2000]
            try:
                insts = list(self._md.disasm(func_data, addr))
            except:
                continue
            
            if len(insts) < 3:
                continue
            
            # Find function end
            end_addr = addr
            for inst in insts:
                if inst.mnemonic == 'ret':
                    end_addr = inst.address + inst.size
                    break
            else:
                end_addr = addr + 0x1000
            
            # Generate function name
            name = self._ida_generate_name(addr, data)
            
            # Analyze function type
            func_type = self._ida_analyze_function_type(insts)
            
            # Extract args
            args = self._ida_extract_args(insts)
            
            func = IDAFunction(
                start_ea=addr,
                end_ea=end_addr,
                name=name,
                type=func_type,
                args=args,
            )
            
            functions.append({
                'start_ea': hex(addr),
                'end_ea': hex(end_addr),
                'name': name,
                'type': func_type,
                'args': args,
                'size': end_addr - addr,
                'instructions': len(insts),
            })
            
            self.functions[addr] = func
            
            if len(functions) >= 100:
                break
        
        return functions
    
    def _ida_analyze_structures(self, data: bytes) -> List[Dict]:
        """Analisar estruturas."""
        structures = []
        
        # Look for struct patterns
        struct_pattern = rb'struct\s*\{([^}]{0,500})\}'
        
        for match in re.finditer(struct_pattern, data):
            try:
                content = match.group(1).decode('ascii', errors='replace')
                fields = re.findall(r'\s+(\w+)\s+(\w+)', content)
                
                if fields and len(structures) < 50:
                    # Generate name
                    type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                    name = f'struct_{type_hash}'
                    
                    structures.append({
                        'name': name,
                        'fields': len(fields),
                        'field_names': [f[1] for f in fields[:10]],
                        'sample': content[:200],
                    })
                    
            except:
                pass
        
        return structures
    
    def _ida_generate_name(self, addr: int, data: bytes) -> str:
        """Gerar nome IDA-style."""
        # Look for name strings nearby
        search_range = 0x200
        start = max(0, addr - search_range)
        end = min(len(data), addr + search_range)
        chunk = data[start:end]
        
        # Try to find function name
        patterns = [
            rb'(\w+)\s*=\s*\(.*?\)\s*0x' + hex(addr)[2:].encode(),
            rb'0x' + hex(addr)[2:].encode() + rb'\s*;\s*(\w+)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, chunk):
                try:
                    return match.group(1).decode('ascii')
                except:
                    pass
        
        # Default IDA-style name
        return f' sub_{addr:08X}'
    
    def _ida_analyze_function_type(self, insts: List) -> str:
        """Analisar tipo de função."""
        # Check first instruction
        if insts and insts[0].mnemonic == 'push' and 'rbp' in insts[0].operands:
            return 'int'  # Standard function
        
        return 'void'
    
    def _ida_extract_args(self, insts: List) -> List[str]:
        """Extrair argumentos."""
        args = []
        
        # Go ABI: DI, SI, DX, CX, R8, R9
        reg_args = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        
        for inst in insts[:20]:
            for reg in reg_args:
                if reg in inst.operands.lower() and inst.mnemonic in ('mov', 'lea'):
                    args.append(reg)
        
        return args[:6]
    
    def _create_ida_items(self, result: Dict):
        """Criar itens IDA."""
        # Create items for functions
        for func in result.get('functions', []):
            ea = int(func['start_ea'], 16)
            self.items[ea] = IDAItem(
                ea=ea,
                name=func['name'],
                type='function',
                size=func.get('size', 0),
            )
        
        # Create items for entry points
        for ea in result.get('entry_points', []):
            self.items[ea] = IDAItem(
                ea=ea,
                name='entry',
                type='entry_point',
            )
    
    def _item_to_dict(self, item: IDAItem) -> Dict:
        """Converter item para dict."""
        return {
            'ea': hex(item.ea),
            'name': item.name,
            'type': item.type,
            'size': item.size,
            'comments': item.comments,
            'tags': item.tags,
        }


# Quick test
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        engine = IDAEngine()
        result = engine.analyze(sys.argv[1])
        print(f"Functions: {len(result.get('functions', []))}")
        print(f"Structures: {len(result.get('structures', []))}")
        print(f"Entry points: {result.get('entry_points', [])}")
    else:
        print("Usage: python ida_engine.py <binary>")
