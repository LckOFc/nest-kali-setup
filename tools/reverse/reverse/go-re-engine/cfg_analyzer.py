#!/usr/bin/env python3
"""
Go CFG Analyzer - Control Flow Graph Analysis
===============================================
Recria funcionalidades do Ghidra/Binary Ninja para análise de fluxo.
"""

import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any


@dataclass
class CFGNode:
    """Node no graph de fluxo de controle."""
    block_id: int
    address: int
    instructions: List[dict] = field(default_factory=list)
    successors: List[int] = field(field(default_factory=list))
    predecessors: List[int] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    dominator: Optional[int] = None
    dominated_by: Set[int] = field(default_factory=set)
    
    # Loop analysis
    is_loop_header: bool = False
    loop_depth: int = 0
    back_edge: bool = False


@dataclass
class CFG:
    """Control Flow Graph completo."""
    func_name: str
    func_addr: int
    nodes: Dict[int, CFGNode] = field(default_factory=dict)
    entry_block: int = 0
    exit_blocks: Set[int] = field(default_factory=set)
    loops: List[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


class GoCFGAnalyzer:
    """
    Analisador de fluxo de controle Go.
    
    Recursos:
    - Construção automática de CFG a partir de assembly
    - Detecção de loops (back edges)
    - Cálculo de dominadores (dominance frontier)
    - Análise de basic blocks
    - Visualização em DOT/graphviz
    """
    
    # Jump instructions que criam arestas
    CONDITIONAL_JUMPS = {
        'je', 'jne', 'jz', 'jnz', 'jl', 'jle', 'jg', 'jge',
        'ja', 'jae', 'jb', 'jbe', 'js', 'jns', 'jo', 'jno',
        'jrcxz', 'jecxz'
    }
    UNCONDITIONAL_JUMPS = {'jmp'}
    CALLS = {'call'}
    RETURNS = {'ret'}
    
    def __init__(self):
        self.cfgs: Dict[int, CFG] = {}
        
    def analyze_function(self, insts: List[dict], func_addr: int,
                         func_name: str = "func") -> CFG:
        """
        Analisar uma função e construir seu CFG.
        
        Args:
            insts: Lista de instruções assembly
            func_addr: Endereço inicial da função
            func_name: Nome da função
            
        Returns:
            CFG object com grafo completo
        """
        cfg = CFG(func_name=func_name, func_addr=func_addr)
        
        if not insts:
            return cfg
        
        # Build basic blocks
        blocks = self._build_blocks(insts)
        
        # Create nodes
        for i, block in enumerate(blocks):
            node = CFGNode(
                block_id=i,
                address=block['start'],
                instructions=block['instructions'],
                is_entry=(i == 0),
                is_exit=(i == len(blocks) - 1 and block.get('is_terminal', False))
            )
            cfg.nodes[i] = node
        
        # Set entry/exit
        if blocks:
            cfg.entry_block = 0
            # Find exit blocks (blocks ending with ret)
            for i, block in enumerate(blocks):
                if block.get('is_terminal'):
                    cfg.exit_blocks.add(i)
        
        # Build edges
        self._build_edges(cfg, blocks)
        
        # Analyze loops
        cfg.loops = self._find_loops(cfg)
        
        # Calculate dominators
        self._calculate_dominators(cfg)
        
        # Stats
        cfg.stats = {
            'total_blocks': len(blocks),
            'total_instructions': sum(len(b['instructions']) for b in blocks),
            'entry_block': cfg.entry_block,
            'exit_blocks': list(cfg.exit_blocks),
            'loops_found': len(cfg.loops),
            'avg_block_size': sum(len(b['instructions']) for b in blocks) / len(blocks) if blocks else 0,
        }
        
        self.cfgs[func_addr] = cfg
        return cfg
    
    def _build_blocks(self, insts: List[dict]) -> List[dict]:
        """Dividir instruções em basic blocks."""
        blocks = []
        current_block = {'start': insts[0]['address'] if insts else 0, 
                        'instructions': [], 'is_terminal': False}
        
        for inst in insts:
            current_block['instructions'].append(inst)
            mnem = inst['mnemonic'].lower()
            
            # Terminal instructions end a block
            if mnem in self.RETURNS:
                current_block['is_terminal'] = True
                blocks.append(current_block)
                current_block = {'start': inst['address'] + inst.get('size', 1),
                                'instructions': [], 'is_terminal': False}
            elif mnem in self.UNCONDITIONAL_JUMPS:
                current_block['is_terminal'] = True
                blocks.append(current_block)
                # New block starts at jump target
                target = inst.get('target', inst['address'] + inst.get('size', 1))
                current_block = {'start': target, 'instructions': [], 'is_terminal': False}
            elif mnem in self.CONDITIONAL_JUMPS:
                current_block['is_terminal'] = True
                blocks.append(current_block)
                # Fall-through block
                fallthrough = inst['address'] + inst.get('size', 1)
                target = inst.get('target', fallthrough)
                blocks.append({'start': fallthrough, 'instructions': [], 'is_terminal': False})
                current_block = {'start': target, 'instructions': [], 'is_terminal': False}
            elif mnem in self.CALLS and inst.get('target'):
                # Calls don't necessarily end blocks, but we track them
                pass
        
        # Last block
        if current_block['instructions']:
            blocks.append(current_block)
        
        return blocks
    
    def _build_edges(self, cfg: CFG, blocks: List[dict]):
        """Construir arestas do CFG."""
        for i, block in enumerate(blocks):
            node = cfg.nodes.get(i)
            if not node:
                continue
            
            mnem = block['instructions'][-1]['mnemonic'].lower() if block['instructions'] else ''
            last_inst = block['instructions'][-1] if block['instructions'] else None
            
            # Conditional jump: two successors
            if mnem in self.CONDITIONAL_JUMPS and last_inst:
                target = last_inst.get('target')
                fallthrough = block['start'] + last_inst.get('size', 1)
                
                if target is not None and i + 1 < len(blocks):
                    node.successors.append(target)
                    cfg.nodes[target]['predecessors'].append(i)
                
                if fallthrough is not None and i + 1 < len(blocks):
                    # Find block containing fallthrough
                    for j, b in enumerate(blocks):
                        if b['start'] == fallthrough:
                            node.successors.append(j)
                            cfg.nodes[j]['predecessors'].append(i)
                            break
            
            # Unconditional jump
            elif mnem in self.UNCONDITIONAL_JUMPS and last_inst:
                target = last_inst.get('target')
                if target is not None:
                    for j, b in enumerate(blocks):
                        if b['start'] == target:
                            node.successors.append(j)
                            cfg.nodes[j]['predecessors'].append(i)
                            break
            
            # Fall-through to next block
            elif i + 1 < len(blocks):
                node.successors.append(i + 1)
                cfg.nodes[i + 1]['predecessors'].append(i)
            
            # Return
            elif mnem in self.RETURNS:
                node.is_exit = True
    
    def _find_loops(self, cfg: CFG) -> List[dict]:
        """Encontrar loops no CFG (back edges)."""
        loops = []
        
        for node_id, node in cfg.nodes.items():
            for succ_id in node.successors:
                succ = cfg.nodes.get(succ_id)
                if not succ:
                    continue
                
                # Back edge: successor dominates current node
                if node_id in succ.dominated_by or succ_id <= node_id:
                    # Found a back edge - potential loop
                    loop = {
                        'header': succ_id,
                        'back_edge_from': node_id,
                        'depth': self._calc_loop_depth(cfg, succ_id),
                    }
                    loops.append(loop)
                    succ.is_loop_header = True
                    node.back_edge = True
        
        return loops
    
    def _calc_loop_depth(self, cfg: CFG, header: int) -> int:
        """Calcular profundidade do loop."""
        depth = 0
        for loop in cfg.loops:
            if loop['header'] == header:
                depth = 1 + loop.get('depth', 0)
        return depth
    
    def _calculate_dominators(self, cfg: CFG):
        """Calcular dominadores para cada bloco (algoritmo de Cytron)."""
        if not cfg.nodes:
            return
        
        entry = cfg.entry_block
        nodes = list(cfg.nodes.keys())
        
        # Initialize
        dom = {n: set(nodes) for n in nodes}
        dom[entry] = {entry}
        
        # Iterate until fixed point
        changed = True
        while changed:
            changed = False
            for n in nodes:
                if n == entry:
                    continue
                preds = cfg.nodes[n].predecessors
                if not preds:
                    continue
                
                # Dom(n) = {n} ∪ (∩ Dom(p) for p in preds)
                new_dom = set(dom[preds[0]]) if preds else {n}
                for p in preds[1:]:
                    new_dom &= dom.get(p, set())
                new_dom.add(n)
                
                if new_dom != dom.get(n):
                    dom[n] = new_dom
                    changed = True
        
        # Set dominators
        for n, preds in dom.items():
            cfg.nodes[n].dominator = list(preds - {n})[0] if preds - {n} else None
            for p in preds:
                if p != n:
                    cfg.nodes[p].dominated_by.add(n)
    
    def generate_dot(self, cfg: CFG) -> str:
        """Gerar formato DOT para visualização."""
        lines = [f'digraph "{cfg.func_name}" {{',
                 '  rankdir=TB;',
                 '  node [shape=box];',
                 '']
        
        for node_id, node in cfg.nodes.items():
            # Node label
            label = f"B{n}"
            if node.is_entry:
                label += " [entry]"
            if node.is_exit:
                label += " [exit]"
            if node.is_loop_header:
                label += " [loop]"
            
            lines.append(f'  B{node_id} [label="{label}\\n{len(node.instructions)} insns"];')
        
        lines.append('')
        
        # Edges
        for node_id, node in cfg.nodes.items():
            for succ_id in node.successors:
                edge_label = ''
                if cfg.nodes[node_id].back_edge:
                    edge_label = ' [color=red, label="back"]'
                lines.append(f'  B{node_id} -> B{succ_id}{edge_label};')
        
        lines.append('}')
        return '\n'.join(lines)
    
    def generate_report(self, cfg: CFG) -> dict:
        """Gerar relatório em JSON."""
        return {
            'function': cfg.func_name,
            'address': hex(cfg.func_addr),
            'stats': cfg.stats,
            'blocks': {
                str(k): {
                    'addr': hex(v.address),
                    'insns': len(v.instructions),
                    'successors': v.successors,
                    'predecessors': v.predecessors,
                    'is_entry': v.is_entry,
                    'is_exit': v.is_exit,
                    'is_loop_header': v.is_loop_header,
                }
                for k, v in cfg.nodes.items()
            },
            'loops': cfg.loops,
            'dot': self.generate_dot(cfg),
        }


# ============================================================
# Main analysis function
# ============================================================

def analyze_cfg(exe_path: str, output_dir: str = None) -> dict:
    """
    Analisar CFG de todas as funções no binário.
    """
    import os
    import json
    import capstone
    
    result = {
        'binary': exe_path,
        'cfgs': [],
        'summary': {},
    }
    
    try:
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        md.detail = True
    except ImportError:
        result['error'] = 'Capstone not installed'
        return result
    
    # Simple function detection
    with open(exe_path, 'rb') as f:
        data = f.read(10 * 1024 * 1024)  # First 10MB
    
    # Find prologues
    prologue_pattern = b'\x55\x48\x89\xe5'  # push rbp; mov rbp, rsp
    functions = []
    
    for match in re.finditer(re.escape(prologue_pattern), data):
        addr = match.start()
        # Extract function instructions
        func_data = data[addr:addr + 0x500]
        try:
            insts = list(md.disasm(func_data, addr))
            if insts:
                functions.append({
                    'addr': addr,
                    'insts': [
                        {'address': i.address, 'mnemonic': i.mnemonic,
                         'operands': i.op_str, 'size': i.size}
                        for i in insts[:50]  # Limit instructions
                    ]
                })
        except:
            pass
    
    # Analyze each function
    analyzer = GoCFGAnalyzer()
    
    for func in functions[:20]:  # Analyze first 20 functions
        cfg = analyzer.analyze_function(func['insts'], func['addr'], 
                                         f"fn_{func['addr']:04x}")
        report = analyzer.generate_report(cfg)
        result['cfgs'].append(report)
    
    # Summary
    result['summary'] = {
        'functions_analyzed': len(result['cfgs']),
        'total_blocks': sum(c['stats']['total_blocks'] for c in result['cfgs']),
        'total_loops': sum(c['stats']['loops_found'] for c in result['cfgs']),
    }
    
    # Save
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, 'cfg_analysis.json'), 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"[+] CFG analysis saved: {os.path.join(output_dir, 'cfg_analysis.json')}")
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Go CFG Analyzer')
    parser.add_argument('binary', help='Path to Go binary')
    parser.add_argument('--output', '-o', default='./output')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Go CFG Analyzer v1.0")
    print("=" * 60)
    print(f"\n  Binary: {args.binary}")
    print()
    
    result = analyze_cfg(args.binary, args.output)
    
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Functions analyzed: {result['summary']['functions_analyzed']}")
    print(f"  Total blocks: {result['summary']['total_blocks']}")
    print(f"  Total loops: {result['summary']['total_loops']}")