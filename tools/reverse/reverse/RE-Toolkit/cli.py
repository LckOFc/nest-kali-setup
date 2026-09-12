#!/usr/bin/env python3
"""
RE Toolkit v1.0 - Complete Reverse Engineering Suite
=====================================================
Recria todas as ferramentas de RE como Python modules acessíveis por AI.

Módulos:
  - ghidra_engine.py    : Descompilador estilo Ghidra
  - x64dbg_engine.py    : Debugger estilo x64dbg
  - hex_editor.py       : Hex Editor estilo HxD
  - fiddler_engine.py   : HTTP Inspector estilo Fiddler
  - binary_ninja_engine.py : Análise estilo Binary Ninja
  - ida_engine.py       : Análise avançada estilo IDA Pro
  - flare_vm.py         : Gerenciador de VMs estilo FLARE-VM
  - cli.py              : Interface CLI para AI
"""

import os
import sys
import json
import time
import hashlib
import struct
import re
import subprocess
from pathlib import Path
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from datetime import datetime
import threading
import queue

# Add engines to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'engines'))

# Try importing optional dependencies
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

try:
    import keystone
except ImportError:
    keystone = None


@dataclass
class REResult:
    """Resultado padronizado de operações de RE."""
    success: bool
    data: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


class REToolkit:
    """
    Toolkit completo de Engenharia Reversa.
    Acessível por AI via métodos padronizados.
    """
    
    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).parent
        self.config_path = config_path or self.base_dir / 'config' / 'settings.json'
        self.plugins = {}
        self.results = {}
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize engines
        self._init_engines()
        
    def _load_config(self) -> dict:
        """Carregar configuração."""
        default_config = {
            'output_dir': str(self.base_dir / 'output'),
            'log_level': 'INFO',
            'max_strings': 100000,
            'max_functions': 500,
            'enable_debug': False,
            'tools': {
                'ghidra': {'enabled': True, 'path': ''},
                'x64dbg': {'enabled': True, 'path': ''},
                'hex_editor': {'enabled': True},
                'fiddler': {'enabled': True, 'port': 8888},
                'binary_ninja': {'enabled': True},
                'ida': {'enabled': True, 'path': ''},
                'flare_vm': {'enabled': True, 'vm_path': ''},
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    saved = json.load(f)
                    default_config.update(saved)
            except:
                pass
        
        return default_config
    
    def _init_engines(self):
        """Inicializar todos os motores."""
        from engines.ghidra_engine import GhidraEngine
        from engines.x64dbg_engine import X64DbgEngine
        from engines.hex_editor import HexEditor
        from engines.fiddler_engine import FiddlerEngine
        from engines.binary_ninja_engine import BinaryNinjaEngine
        from engines.ida_engine import IDAEngine
        from engines.flare_vm import FLAREVMManager
        
        self.ghidra = GhidraEngine(self)
        self.x64dbg = X64DbgEngine(self)
        self.hex_editor = HexEditor()
        self.fiddler = FiddlerEngine(self)
        self.binary_ninja = BinaryNinjaEngine(self)
        self.ida = IDAEngine(self)
        self.flare_vm = FLAREVMManager(self)
        
        self.engines = {
            'ghidra': self.ghidra,
            'x64dbg': self.x64dbg,
            'hex_editor': self.hex_editor,
            'fiddler': self.fiddler,
            'binary_ninja': self.binary_ninja,
            'ida': self.ida,
            'flare_vm': self.flare_vm,
        }
    
    # ============================================================
    # METHODOS PRINCIPAIS (AI-ACCESSIBLE)
    # ============================================================
    
    def analyze_binary(self, binary_path: str, options: dict = None) -> REResult:
        """
        Analisar binário completo usando todos os engines.
        
        Args:
            binary_path: Caminho para o binário
            options: Opções de análise
            
        Returns:
            REResult com todos os resultados
        """
        start_time = time.time()
        
        if not os.path.exists(binary_path):
            return REResult(success=False, error=f"Binário não encontrado: {binary_path}")
        
        result = REResult(success=True)
        
        try:
            # 1. Análise PE básica
            result.metadata['pe_info'] = self._analyze_pe(binary_path)
            
            # 2. Extração de strings
            result.metadata['strings'] = self.hex_editor.extract_strings(binary_path, 
                                                                          limit=self.config.get('max_strings', 100000))
            
            # 3. Análise com Ghidra engine
            if self.config['tools']['ghidra']['enabled']:
                result.metadata['ghidra_analysis'] = self.ghidra.analyze_file(binary_path)
            
            # 4. Análise com Binary Ninja engine
            if self.config['tools']['binary_ninja']['enabled']:
                result.metadata['binja_analysis'] = self.binary_ninja.analyze(binary_path)
            
            # 5. Análise com IDA engine
            if self.config['tools']['ida']['enabled']:
                result.metadata['ida_analysis'] = self.ida.analyze(binary_path)
            
            # 6. Funções identificadas
            result.metadata['functions'] = self._extract_functions(binary_path)
            
            # 7. Tipos recuperados
            result.metadata['types'] = self._recover_types(binary_path)
            
            # 8. CFG
            result.metadata['cfg'] = self._build_cfg(binary_path)
            
            # Timing
            elapsed = time.time() - start_time
            result.metadata['analysis_time'] = elapsed
            result.metadata['binary_size'] = os.path.getsize(binary_path)
            result.metadata['session_id'] = self.session_id
            
        except Exception as e:
            result.success = False
            result.error = str(e)
        
        # Salvar resultado
        self._save_result(binary_path, result)
        
        return result
    
    def decompile_function(self, binary_path: str, function_addr: int, 
                           engine: str = 'ghidra') -> REResult:
        """
        Descompilar uma função específica.
        
        Args:
            binary_path: Caminho do binário
            function_addr: Endereço da função
            engine: Motor para usar (ghidra, binary_ninja, ida)
        """
        engine_map = {
            'ghidra': self.ghidra,
            'binary_ninja': self.binary_ninja,
            'ida': self.ida,
        }
        
        engine_instance = engine_map.get(engine)
        if not engine_instance:
            return REResult(success=False, error=f"Engine não encontrado: {engine}")
        
        return engine_instance.decompile_function(binary_path, function_addr)
    
    def debug_process(self, process_id: int = None, executable: str = None) -> REResult:
        """
        Iniciar debugging de processo.
        
        Args:
            process_id: ID do processo (para attach)
            executable: Caminho para executar
        """
        return self.x64dbg.attach_or_run(process_id, executable)
    
    def stop_debugger(self) -> REResult:
        """Parar debugger."""
        return self.x64dbg.stop()
    
    def read_memory(self, address: int, size: int) -> REResult:
        """Ler memória do processo debuggeado."""
        return self.x64dbg.read_memory(address, size)
    
    def write_memory(self, address: int, data: bytes) -> REResult:
        """Escrever memória."""
        return self.x64dbg.write_memory(address, data)
    
    def set_breakpoint(self, address: int, breakpoint_type: str = 'hardware') -> REResult:
        """Setar breakpoint."""
        return self.x64dbg.set_breakpoint(address, breakpoint_type)
    
    def remove_breakpoint(self, address: int) -> REResult:
        """Remover breakpoint."""
        return self.x64dbg.remove_breakpoint(address)
    
    def step_into(self) -> REResult:
        """Step into."""
        return self.x64dbg.step_into()
    
    def step_over(self) -> REResult:
        """Step over."""
        return self.x64dbg.step_over()
    
    def continue_execution(self) -> REResult:
        """Continuar execução."""
        return self.x64dbg.continue_execution()
    
    def edit_hex(self, file_path: str, offset: int, data: bytes) -> REResult:
        """Editar dados hexadecimais em arquivo."""
        return self.hex_editor.edit_bytes(file_path, offset, data)
    
    def search_hex(self, file_path: str, pattern: bytes, max_results: int = 100) -> REResult:
        """Buscar padrão em arquivo."""
        return self.hex_editor.search(file_path, pattern, max_results)
    
    def start_http_capture(self, interface: str = None, filter_expr: str = None) -> REResult:
        """Iniciar captura HTTP."""
        return self.fiddler.start_capture(interface, filter_expr)
    
    def stop_http_capture(self) -> REResult:
        """Parar captura HTTP."""
        return self.fiddler.stop_capture()
    
    def get_http_sessions(self) -> REResult:
        """Retornar sessões HTTP capturadas."""
        return self.fiddler.get_sessions()
    
    def create_vm(self, vm_name: str, os_type: str = 'windows', 
                  memory_mb: int = 4096) -> REResult:
        """Criar VM para análise isolada."""
        return self.flare_vm.create_vm(vm_name, os_type, memory_mb)
    
    def snapshot_vm(self, vm_name: str, snapshot_name: str = None) -> REResult:
        """Criar snapshot de VM."""
        return self.flare_vm.snapshot(vm_name, snapshot_name)
    
    def run_analysis_in_vm(self, vm_name: str, binary_path: str, 
                           analysis_script: str = None) -> REResult:
        """Executar análise dentro de VM."""
        return self.flare_vm.run_analysis(vm_name, binary_path, analysis_script)
    
    # ============================================================
    # METODOS AUXILIARES
    # ============================================================
    
    def _analyze_pe(self, binary_path: str) -> dict:
        """Análise PE básica."""
        if not lief:
            return {'error': 'LIEF not available'}
        
        try:
            pe = lief.PE.parse(binary_path)
            
            sections = []
            for s in pe.sections:
                sections.append({
                    'name': s.name,
                    'virtual_size': s.virtual_size,
                    'raw_size': s.sizeof_raw_data,
                    'virtual_address': hex(s.virtual_address),
                })
            
            return {
                'machine': str(pe.header.machine),
                'entry_point': hex(pe.entrypoint),
                'image_base': hex(pe.imagebase),
                'sections': sections,
                'has_debug': pe.has_debug,
                'imports': [lib.name for lib in pe.imports] if pe.has_imports else [],
                'exports': [exp.name for exp in pe.exports] if pe.has_exports else [],
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_functions(self, binary_path: str, max_count: int = 500) -> List[dict]:
        """Extrair funções do binário."""
        functions = []
        
        if not capstone:
            return functions
        
        try:
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            
            with open(binary_path, 'rb') as f:
                data = f.read(50 * 1024 * 1024)  # First 50MB
            
            # Find function prologues
            prologue = b'\x55\x48\x89\xe5'  # push rbp; mov rbp, rsp
            
            for match in re.finditer(re.escape(prologue), data):
                addr = match.start()
                
                # Extract function instructions
                func_data = data[addr:addr + 0x1000]
                try:
                    insts = list(md.disasm(func_data, addr))
                except:
                    continue
                
                if len(insts) < 3:
                    continue
                
                # Find function end
                func_end = addr
                for inst in insts:
                    if inst.mnemonic == 'ret':
                        func_end = inst.address + inst.size
                        break
                else:
                    func_end = addr + 0x500
                
                functions.append({
                    'addr': hex(addr),
                    'end': hex(func_end),
                    'size': func_end - addr,
                    'instructions': len(insts),
                })
                
                if len(functions) >= max_count:
                    break
        
        except Exception as e:
            pass
        
        return functions
    
    def _recover_types(self, binary_path: str, max_count: int = 200) -> List[dict]:
        """Recuperar tipos do binário."""
        types = []
        
        try:
            with open(binary_path, 'rb') as f:
                data = f.read(200 * 1024 * 1024)
            
            # Detect structs
            struct_pattern = rb'struct\s*\{([^}]{0,300})\}'
            for match in re.finditer(struct_pattern, data):
                try:
                    content = match.group(1).decode('ascii', errors='replace')
                    fields = re.findall(r'\s+(\w+)\s+(\w+)', content)
                    if fields and len(types) < max_count:
                        type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                        types.append({
                            'kind': 'struct',
                            'name': f'Struct_{type_hash}',
                            'fields': len(fields),
                            'confidence': 0.7,
                        })
                except:
                    pass
            
            # Detect interfaces
            iface_pattern = rb'interface\s*\{([^}]{0,300})\}'
            for match in re.finditer(iface_pattern, data):
                try:
                    content = match.group(1).decode('ascii', errors='replace')
                    methods = re.findall(r'\s*(\w+)\s*\(', content)
                    if methods and len(types) < max_count:
                        type_hash = hashlib.md5(content.encode()[:100]).hexdigest()[:8]
                        types.append({
                            'kind': 'interface',
                            'name': f'Interface_{type_hash}',
                            'methods': len(methods),
                            'confidence': 0.8,
                        })
                except:
                    pass
        
        except:
            pass
        
        return types
    
    def _build_cfg(self, binary_path: str) -> dict:
        """Construir CFG básico."""
        cfg = {'functions': {}, 'total_blocks': 0}
        
        if not capstone:
            return cfg
        
        try:
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            
            with open(binary_path, 'rb') as f:
                data = f.read(10 * 1024 * 1024)
            
            prologue = b'\x55\x48\x89\xe5'
            
            for match in re.finditer(re.escape(prologue), data):
                addr = match.start()
                func_data = data[addr:addr + 0x800]
                
                try:
                    insts = list(md.disasm(func_data, addr))
                except:
                    continue
                
                if len(insts) < 3:
                    continue
                
                # Build basic blocks
                blocks = []
                current_block = {'start': addr, 'insts': []}
                
                for inst in insts:
                    current_block['insts'].append({
                        'addr': hex(inst.address),
                        'mnemonic': inst.mnemonic,
                        'operands': inst.operands,
                    })
                    
                    mnem = inst.mnemonic.lower()
                    if mnem in ('ret', 'jmp') or mnem.startswith('j'):
                        blocks.append(current_block)
                        current_block = {'start': inst.address + inst.size, 'insts': []}
                
                if current_block['insts']:
                    blocks.append(current_block)
                
                cfg['functions'][hex(addr)] = {
                    'blocks': len(blocks),
                    'instructions': len(insts),
                }
                cfg['total_blocks'] += len(blocks)
                
                if len(cfg['functions']) >= 20:
                    break
        
        except:
            pass
        
        return cfg
    
    def _save_result(self, binary_path: str, result: REResult):
        """Salvar resultado da análise."""
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Safe filename
        safe_name = re.sub(r'[^\w\-\.]', '_', os.path.basename(binary_path))
        output_file = output_dir / f'{safe_name}_analysis_{self.session_id}.json'
        
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        result.metadata['output_file'] = str(output_file)
    
    def get_status(self) -> dict:
        """Retornar status do toolkit."""
        return {
            'version': '1.0.0',
            'session_id': self.session_id,
            'base_dir': str(self.base_dir),
            'config': self.config,
            'engines': {
                name: {'loaded': True} 
                for name in self.engines.keys()
            },
            'timestamp': datetime.now().isoformat(),
        }
    
    def execute_command(self, command: str, args: dict = None) -> REResult:
        """
        Executar comando genérico.
        
        Commands:
          - analyze <binary> [--options]
          - decompile <binary> <address> [--engine]
          - debug <process_id|executable>
          - step
          - continue
          - breakpoint <address>
          - memory read <address> <size>
          - memory write <address> <data>
          - hex_edit <file> <offset> <data>
          - hex_search <file> <pattern>
          - http_start [--filter]
          - http_stop
          - http_sessions
          - vm_create <name> [--os] [--memory]
          - vm_snapshot <name>
          - status
        """
        args = args or {}
        
        parts = command.strip().split()
        if not parts:
            return REResult(success=False, error="Comando vazio")
        
        cmd = parts[0].lower()
        cmd_args = parts[1:] if len(parts) > 1 else []
        
        try:
            if cmd == 'analyze':
                if not cmd_args:
                    return REResult(success=False, error="Caminho do binário necessário")
                return self.analyze_binary(cmd_args[0])
            
            elif cmd == 'decompile':
                if len(cmd_args) < 2:
                    return REResult(success=False, error="Uso: decompile <binary> <address> [--engine]")
                engine = 'ghidra'
                if '--engine' in command:
                    idx = command.index('--engine')
                    engine = command[idx+9:].strip()
                return self.decompile_function(cmd_args[0], int(cmd_args[1], 16), engine)
            
            elif cmd == 'debug':
                process_id = None
                executable = None
                if cmd_args:
                    if cmd_args[0].startswith('0x') or cmd_args[0].isdigit():
                        process_id = int(cmd_args[0], 16 if cmd_args[0].startswith('0x') else 10)
                    else:
                        executable = cmd_args[0]
                return self.debug_process(process_id, executable)
            
            elif cmd == 'step':
                return self.step_into()
            
            elif cmd == 'continue':
                return self.continue_execution()
            
            elif cmd == 'breakpoint':
                if not cmd_args:
                    return REResult(success=False, error="Endereço necessário")
                return self.set_breakpoint(int(cmd_args[0], 16))
            
            elif cmd == 'memory':
                if len(cmd_args) < 3:
                    return REResult(success=False, error="Uso: memory read/write <address> <size/data>")
                if cmd_args[0] == 'read':
                    return self.read_memory(int(cmd_args[1], 16), int(cmd_args[2]))
                elif cmd_args[0] == 'write':
                    data = bytes.fromhex(cmd_args[2])
                    return self.write_memory(int(cmd_args[1], 16), data)
            
            elif cmd == 'hex_edit':
                if len(cmd_args) < 3:
                    return REResult(success=False, error="Uso: hex_edit <file> <offset> <data>")
                data = bytes.fromhex(cmd_args[2])
                return self.edit_hex(cmd_args[0], int(cmd_args[1], 16), data)
            
            elif cmd == 'hex_search':
                if len(cmd_args) < 2:
                    return REResult(success=False, error="Uso: hex_search <file> <pattern>")
                pattern = bytes.fromhex(cmd_args[1])
                return self.search_hex(cmd_args[0], pattern)
            
            elif cmd == 'http_start':
                filter_expr = args.get('filter')
                return self.start_http_capture(filter_expr=filter_expr)
            
            elif cmd == 'http_stop':
                return self.stop_http_capture()
            
            elif cmd == 'http_sessions':
                return self.get_http_sessions()
            
            elif cmd == 'vm_create':
                vm_name = cmd_args[0] if cmd_args else 'analysis_vm'
                os_type = args.get('os', 'windows')
                memory = args.get('memory', 4096)
                return self.create_vm(vm_name, os_type, memory)
            
            elif cmd == 'vm_snapshot':
                if not cmd_args:
                    return REResult(success=False, error="Nome da VM necessário")
                return self.snapshot_vm(cmd_args[0])
            
            elif cmd == 'status':
                return REResult(success=True, data=self.get_status())
            
            else:
                return REResult(success=False, error=f"Comando não reconhecido: {cmd}")
        
        except Exception as e:
            return REResult(success=False, error=str(e))


# ============================================================
# Entry Point
# ============================================================

def main():
    """CLI principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='RE Toolkit v1.0 - Complete Reverse Engineering Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py analyze agy.exe
  python cli.py decompile agy.exe 0x1000
  python cli.py debug agy.exe
  python cli.py status
        """
    )
    
    parser.add_argument('command', help='Comando a executar')
    parser.add_argument('args', nargs='*', help='Argumentos')
    parser.add_argument('--config', '-c', help='Path para config')
    
    args = parser.parse_args()
    
    # Initialize toolkit
    toolkit = REToolkit(args.config)
    
    # Build command string
    command = args.command + (' ' + ' '.join(args.args) if args.args else '')
    
    # Execute
    result = toolkit.execute_command(command)
    
    # Output
    if result.success:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        print(f"ERROR: {result.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
