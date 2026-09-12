#!/usr/bin/env python3
"""
Go Type Recovery Engine
========================
Recria funcionalidades de inferência de tipos do Ghidra/Binary Ninja.
"""

import re
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any


@dataclass
class GoType:
    """Tipo Go recuperado."""
    name: str
    kind: str  # struct, interface, slice, map, pointer, primitive
    size: Optional[int] = None
    fields: Dict[str, str] = field(default_factory=dict)
    methods: List[str] = field(default_factory=list)
    element_type: Optional[str] = None
    key_type: Optional[str] = None
    value_type: Optional[str] = None
    source: str = ""  # Where this type was found
    confidence: float = 0.0  # 0.0 to 1.0


class GoTypeRecovery:
    """
    Engine de recovery de tipos Go.
    
    Recursos:
    - Detecção de structs a partir de padrões de memória
    - Inferência de interfaces a partir de métodos
    - Recovery de slices, maps, channels
    - Anotação de ponteiros
    - Cálculo de confiança baseado em heurísticas
    """
    
    # Padrões Go para tipos conhecidos
    PRIMITIVE_TYPES = {
        'string', 'int', 'int8', 'int16', 'int32', 'int64',
        'uint', 'uint8', 'uint16', 'uint32', 'uint64',
        'float32', 'float64', 'complex64', 'complex128',
        'bool', 'byte', 'rune', 'error', 'any',
    }
    
    # Padrões para campos comuns
    COMMON_FIELD_PATTERNS = {
        'name': 'string',
        'id': 'int64',
        'count': 'int',
        'size': 'int',
        'length': 'int',
        'data': '[]byte',
        'buffer': '[]byte',
        'content': 'string',
        'value': 'interface{}',
        'key': 'string',
        'status': 'int',
        'err': 'error',
        'error': 'error',
        'done': 'chan struct{}',
        'wg': 'sync.WaitGroup',
        'mu': 'sync.RWMutex',
        'lock': 'sync.Mutex',
        'ctx': 'context.Context',
        'config': 'Config',
        'opts': 'Options',
        'handler': 'interface{}',
        'client': 'Client',
        'server': 'Server',
        'req': 'Request',
        'resp': 'Response',
        'reader': 'io.Reader',
        'writer': 'io.Writer',
    }
    
    def __init__(self):
        self.types: Dict[str, GoType] = {}
        self.type_hints: Dict[int, str] = {}  # addr -> type
        
    def analyze_binary(self, data: bytes) -> Dict[str, GoType]:
        """
        Analisar dados brutos do binário para recuperar tipos.
        
        Args:
            data: Dados brutos do binário
            
        Returns:
            Dicionário nome -> GoType
        """
        # 1. Extrair strings e analisar padrões
        strings = self._extract_strings(data)
        
        # 2. Detectar structs
        structs = self._detect_structs(data, strings)
        
        # 3. Detectar interfaces
        interfaces = self._detect_interfaces(data, strings)
        
        # 4. Detectar tipos genéricos
        generics = self._detect_generics(data)
        
        # 5. Inferir tipos a partir de padrões de uso
        usage_types = self._infer_from_usage(data)
        
        # Consolidar
        all_types = {**structs, **interfaces, **generics, **usage_types}
        
        # Calcular confiança
        for name, typ in all_types.items():
            typ.confidence = self._calc_confidence(typ, data)
        
        self.types = all_types
        return all_types
    
    def _extract_strings(self, data: bytes) -> List[str]:
        """Extrair strings do binário."""
        strings = []
        pattern = rb'[\x20-\x7e]{4,}'
        for match in re.finditer(pattern, data):
            try:
                s = match.group(0).decode('ascii')
                strings.append(s)
            except:
                pass
        return strings
    
    def _detect_structs(self, data: bytes, strings: List[str]) -> Dict[str, GoType]:
        """Detectar structs no binário."""
        structs = {}
        
        # Padrão: struct { field type; ... }
        struct_pattern = rb'struct\s*\{([^}]{0,500})\}'
        
        for match in re.finditer(struct_pattern, data):
            try:
                content = match.group(1).decode('ascii', errors='replace')
                fields = self._parse_struct_fields(content)
                
                if fields:
                    # Generate type name
                    type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                    type_name = f"Struct_{type_hash}"
                    
                    structs[type_name] = GoType(
                        name=type_name,
                        kind='struct',
                        fields=fields,
                        size=len(fields) * 8,  # Estimate
                        source='struct_literal',
                        confidence=0.7
                    )
            except:
                pass
        
        # Also look for PascalCase names that might be struct types
        type_pattern = rb'\b([A-Z][a-zA-Z0-9_]{3,30})\b'
        seen_types = set(structs.keys())
        
        for match in re.finditer(type_pattern, data):
            try:
                name = match.group(1).decode('ascii')
                if name not in seen_types and name not in self.PRIMITIVE_TYPES:
                    # Check if it's used in a struct-like context
                    start = max(0, match.start() - 100)
                    context = data[start:match.start() + 100]
                    
                    if b'struct' in context or b'field' in context.lower():
                        structs[name] = GoType(
                            name=name,
                            kind='struct',
                            source='naming_convention',
                            confidence=0.5
                        )
                        seen_types.add(name)
            except:
                pass
        
        return structs
    
    def _detect_interfaces(self, data: bytes, strings: List[str]) -> Dict[str, GoType]:
        """Detectar interfaces no binário."""
        interfaces = {}
        
        # Padrão: interface { Method(); ... }
        iface_pattern = rb'interface\s*\{([^}]{0,500})\}'
        
        for match in re.finditer(iface_pattern, data):
            try:
                content = match.group(1).decode('ascii', errors='replace')
                methods = re.findall(r'\s*(\w+)\s*\([^)]*\)', content)
                
                if methods:
                    type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                    type_name = f"Interface_{type_hash}"
                    
                    interfaces[type_name] = GoType(
                        name=type_name,
                        kind='interface',
                        methods=methods[:10],
                        source='interface_literal',
                        confidence=0.8
                    )
            except:
                pass
        
        return interfaces
    
    def _detect_generics(self, data: bytes) -> Dict[str, GoType]:
        """Detectar tipos genéricos (slices, maps, channels)."""
        generics = {}
        
        # Slices: []Type
        slice_pattern = rb'\[\]([a-zA-Z_][a-zA-Z0-9_.{}]*)'
        for match in re.finditer(slice_pattern, data):
            try:
                elem_type = match.group(1).decode('ascii')
                type_name = f"[]{elem_type}"
                
                if type_name not in generics:
                    generics[type_name] = GoType(
                        name=type_name,
                        kind='slice',
                        element_type=elem_type,
                        source='slice_pattern',
                        confidence=0.6
                    )
            except:
                pass
        
        # Maps: map[Key]Value
        map_pattern = rb'map\[([a-zA-Z_][a-zA-Z0-9_.]*)\]([a-zA-Z_][a-zA-Z0-9_.]*)'
        for match in re.finditer(map_pattern, data):
            try:
                key_type = match.group(1).decode('ascii')
                val_type = match.group(2).decode('ascii')
                type_name = f"map[{key_type}]{{{val_type}}}"
                
                if type_name not in generics:
                    generics[type_name] = GoType(
                        name=type_name,
                        kind='map',
                        key_type=key_type,
                        value_type=val_type,
                        source='map_pattern',
                        confidence=0.7
                    )
            except:
                pass
        
        # Channels: chan Type
        chan_pattern = rb'chan\s+([a-zA-Z_][a-zA-Z0-9_.{}]*)'
        for match in re.finditer(chan_pattern, data):
            try:
                chan_type = match.group(1).decode('ascii')
                type_name = f"chan {chan_type}"
                
                if type_name not in generics:
                    generics[type_name] = GoType(
                        name=type_name,
                        kind='channel',
                        element_type=chan_type,
                        source='chan_pattern',
                        confidence=0.6
                    )
            except:
                pass
        
        return generics
    
    def _infer_from_usage(self, data: bytes) -> Dict[str, GoType]:
        """Inferir tipos a partir de padrões de uso."""
        inferred = {}
        
        # Look for common Go variable patterns
        var_pattern = rb'(\w+)\s+(:=|=\s*)([^;]{0,100})'
        
        for match in re.finditer(var_pattern, data):
            try:
                var_name = match.group(1).decode('ascii')
                init_value = match.group(3).decode('ascii', errors='replace')
                
                # Infer type from initialization
                if 'make(' in init_value:
                    # make([]Type, ...) -> slice
                    m = re.search(r'make\(\[\](\w+)', init_value)
                    if m:
                        elem = m.group(1)
                        type_name = f"[]{elem}"
                        if type_name not in inferred:
                            inferred[type_name] = GoType(
                                name=type_name,
                                kind='slice',
                                element_type=elem,
                                source='make_usage',
                                confidence=0.8
                            )
                
                elif init_value.startswith('"'):
                    # String literal
                    if var_name.lower() in ('name', 'path', 'url', 'host'):
                        type_name = 'string'
                        if type_name not in inferred:
                            inferred[type_name] = GoType(
                                name=type_name,
                                kind='primitive',
                                source='string_inference',
                                confidence=0.9
                            )
                            
            except:
                pass
        
        return inferred
    
    def _parse_struct_fields(self, content: str) -> Dict[str, str]:
        """Parsear campos de struct."""
        fields = {}
        
        # Pattern: Identifier Type
        field_pattern = r'\s+(\w+)\s+(\w+(?:\[[^\]]*\])?(?:\s*\w+)?)'
        
        for match in re.finditer(field_pattern, content):
            try:
                field_name = match.group(1)
                field_type = match.group(2)
                
                # Skip Go keywords
                if field_name.lower() in ('struct', 'interface', 'func', 'type', 'var', 'const'):
                    continue
                
                fields[field_name] = field_type
            except:
                pass
        
        return fields
    
    def _calc_confidence(self, typ: GoType, data: bytes) -> float:
        """Calcular confiança do tipo recuperado."""
        confidence = typ.confidence
        
        # Boost confidence if type name matches known patterns
        if typ.kind == 'struct':
            # Check if fields match common patterns
            common_matches = sum(1 for f in typ.fields.keys() 
                               if f.lower() in self.COMMON_FIELD_PATTERNS)
            if common_matches > 3:
                confidence = min(1.0, confidence + 0.2)
        
        elif typ.kind == 'interface':
            # More methods = more confident
            if len(typ.methods) > 5:
                confidence = min(1.0, confidence + 0.1)
        
        return round(confidence, 2)
    
    def get_type_hierarchy(self) -> List[dict]:
        """Retornar hierarquia de tipos."""
        types = list(self.types.values())
        
        # Sort by confidence
        types.sort(key=lambda t: t.confidence, reverse=True)
        
        return [
            {
                'name': t.name,
                'kind': t.kind,
                'confidence': t.confidence,
                'source': t.source,
                'fields': len(t.fields) if t.fields else 0,
                'methods': len(t.methods) if t.methods else 0,
            }
            for t in types[:50]
        ]


# ============================================================
# Main analysis function
# ============================================================

def analyze_types(exe_path: str, output_dir: str = None) -> dict:
    """
    Analisar tipos em binário Go.
    """
    import os
    import json
    
    result = {
        'binary': exe_path,
        'types': [],
        'summary': {},
    }
    
    # Read binary
    with open(exe_path, 'rb') as f:
        data = f.read(200 * 1024 * 1024)  # First 200MB
    
    # Run analysis
    recovery = GoTypeRecovery()
    types = recovery.analyze_binary(data)
    
    result['types'] = recovery.get_type_hierarchy()
    result['summary'] = {
        'total_types': len(types),
        'by_kind': {
            'struct': sum(1 for t in types.values() if t.kind == 'struct'),
            'interface': sum(1 for t in types.values() if t.kind == 'interface'),
            'slice': sum(1 for t in types.values() if t.kind == 'slice'),
            'map': sum(1 for t in types.values() if t.kind == 'map'),
            'channel': sum(1 for t in types.values() if t.kind == 'channel'),
            'primitive': sum(1 for t in types.values() if t.kind == 'primitive'),
        }
    }
    
    # Save
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, 'types_analysis.json'), 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"[+] Types analysis saved: {os.path.join(output_dir, 'types_analysis.json')}")
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Go Type Recovery Engine')
    parser.add_argument('binary', help='Path to Go binary')
    parser.add_argument('--output', '-o', default='./output')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Go Type Recovery Engine v1.0")
    print("=" * 60)
    print(f"\n  Binary: {args.binary}")
    print()
    
    result = analyze_types(args.binary, args.output)
    
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Total types recovered: {result['summary']['total_types']}")
    print(f"  By kind:")
    for kind, count in result['summary']['by_kind'].items():
        print(f"    {kind}: {count}")