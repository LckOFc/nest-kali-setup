#!/usr/bin/env python3
"""
AI Integration Module - RE Toolkit
====================================
Módulo completo para integração com agentes de AI.
Fornece interface unificada para todas as ferramentas de RE.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime


class REAgent:
    """
    Agente de Engenharia Reversa para AI.
    
    Este módulo fornece uma interface completa para que agentes de AI
    possam realizar análise reversa sem depender de ferramentas externas.
    
    Uso:
        agent = REAgent()
        result = agent.analyze("C:\\path\\to\\binary.exe")
        result = agent.debug_start("C:\\path\\to\\exe")
        result = agent.hex_open("C:\\path\\to\\file.bin")
    """
    
    def __init__(self, config: dict = None):
        """
        Inicializar o agente.
        
        Args:
            config: Configurações opcionais
        """
        self.base_dir = Path(__file__).parent
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
        self.start_time = time.time()

        # Status (primeiro para evitar AttributeError)
        self.status = {
            'initialized': False,
            'engines_loaded': 0,
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
        }

        # Carregar configuração
        self.config = config or self._default_config()

        # Importar engines
        self._import_engines()
        
    def _default_config(self) -> dict:
        """Configuração padrão."""
        return {
            'output_dir': str(self.base_dir / 'output'),
            'max_strings': 100000,
            'max_functions': 500,
            'verbose': False,
            'auto_save': True,
        }
    
    def _import_engines(self):
        """Importar todos os engines."""
        try:
            sys.path.insert(0, str(self.base_dir / 'engines'))
            
            from ghidra_engine import GhidraEngine
            from x64dbg_engine import X64DbgEngine
            from hex_editor import HexEditor
            from fiddler_engine import FiddlerEngine
            from binary_ninja_engine import BinaryNinjaEngine
            from ida_engine import IDAEngine
            from flare_vm import FLAREVMManager
            
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
            
            self.status['engines_loaded'] = len(self.engines)
            
        except Exception as e:
            self.status['import_error'] = str(e)
    
    # ============================================================
    # MÉTODOS PRINCIPAIS DE ANÁLISE
    # ============================================================
    
    def analyze(self, binary_path: str, 
                analysis_depth: str = 'full') -> Dict[str, Any]:
        """
        Análise completa de binário.
        
        Args:
            binary_path: Caminho para o binário
            analysis_depth: 'quick', 'full', ou 'deep'
            
        Returns:
            Dict com todos os resultados
        """
        if not os.path.exists(binary_path):
            return {'error': f'Arquivo não encontrado: {binary_path}'}
        
        result = {
            'binary': binary_path,
            'size': os.path.getsize(binary_path),
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'analysis_depth': analysis_depth,
            'results': {},
        }
        
        start = time.time()
        
        # Ghidra analysis
        try:
            result['results']['ghidra'] = self.ghidra.analyze_file(binary_path)
        except Exception as e:
            result['results']['ghidra'] = {'error': str(e)}
        
        # Binary Ninja analysis
        try:
            result['results']['binary_ninja'] = self.binary_ninja.analyze(binary_path)
        except Exception as e:
            result['results']['binary_ninja'] = {'error': str(e)}
        
        # IDA analysis
        try:
            result['results']['ida'] = self.ida.analyze(binary_path)
        except Exception as e:
            result['results']['ida'] = {'error': str(e)}
        
        # Hex editor strings
        try:
            result['results']['strings'] = self.hex_editor.extract_strings(binary_path)
        except Exception as e:
            result['results']['strings'] = {'error': str(e)}
        
        # Timing
        result['analysis_time'] = time.time() - start
        result['success'] = True
        
        # Auto-save
        if self.config.get('auto_save', True):
            self._save_result(binary_path, result)
        
        return result
    
    def decompile(self, binary_path: str, address: int,
                  engine: str = 'ghidra') -> Dict[str, Any]:
        """
        Descompilar função específica.
        
        Args:
            binary_path: Caminho do binário
            address: Endereço da função (int ou hex string)
            engine: Motor para usar
            
        Returns:
            Pseudocódigo da função
        """
        # Convert address
        if isinstance(address, str):
            if address.startswith('0x'):
                address = int(address, 16)
            else:
                address = int(address)
        
        engine_map = {
            'ghidra': self.ghidra,
            'binary_ninja': self.binary_ninja,
            'ida': self.ida,
        }
        
        engine_instance = engine_map.get(engine)
        if not engine_instance:
            return {'error': f'Engine não encontrado: {engine}'}
        
        try:
            return engine_instance.decompile_function(binary_path, address)
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # MÉTODOS DE DEBUGGING
    # ============================================================
    
    def debug_start(self, executable: str = None, process_id: int = None) -> Dict[str, Any]:
        """Iniciar debugging."""
        return self.x64dbg.attach_or_run(process_id, executable)
    
    def debug_stop(self) -> Dict[str, Any]:
        """Parar debugging."""
        return self.x64dbg.stop()
    
    def debug_step(self, step_type: str = 'into') -> Dict[str, Any]:
        """
        Step através do código.
        
        Args:
            step_type: 'into' (F11) ou 'over' (F10)
        """
        if step_type == 'into':
            return self.x64dbg.step_into()
        else:
            return self.x64dbg.step_over()
    
    def debug_continue(self) -> Dict[str, Any]:
        """Continuar execução (F9)."""
        return self.x64dbg.continue_execution()
    
    def debug_breakpoint(self, address: int, type: str = 'hardware') -> Dict[str, Any]:
        """Adicionar breakpoint."""
        if isinstance(address, str) and address.startswith('0x'):
            address = int(address, 16)
        return self.x64dbg.set_breakpoint(address, type)
    
    def debug_memory_read(self, address: int, size: int) -> Dict[str, Any]:
        """Ler memória."""
        if isinstance(address, str) and address.startswith('0x'):
            address = int(address, 16)
        return self.x64dbg.read_memory(address, size)
    
    def debug_memory_write(self, address: int, data: bytes) -> Dict[str, Any]:
        """Escrever memória."""
        if isinstance(address, str) and address.startswith('0x'):
            address = int(address, 16)
        return self.x64dbg.write_memory(address, data)
    
    def debug_get_registers(self) -> Dict[str, Any]:
        """Obter estado dos registros."""
        return self.x64dbg.get_registers()
    
    def debug_get_disassembly(self, address: int, count: int = 20) -> Dict[str, Any]:
        """Obter disassembly."""
        if isinstance(address, str) and address.startswith('0x'):
            address = int(address, 16)
        return self.x64dbg.get_disassembly(address, count)
    
    def debug_get_modules(self) -> Dict[str, Any]:
        """Obter módulos carregados."""
        return self.x64dbg.get_modules()
    
    def debug_get_threads(self) -> Dict[str, Any]:
        """Obter threads."""
        return self.x64dbg.get_threads()
    
    # ============================================================
    # MÉTODOS DE HEX EDITOR
    # ============================================================
    
    def hex_open(self, file_path: str) -> Dict[str, Any]:
        """Abrir arquivo no hex editor."""
        return self.hex_editor.open_file(file_path)
    
    def hex_view(self, offset: int, length: int = 256) -> Dict[str, Any]:
        """Visualizar dados hexadecimais."""
        if isinstance(offset, str) and offset.startswith('0x'):
            offset = int(offset, 16)
        return self.hex_editor.get_hex_view(offset, length)
    
    def hex_edit(self, offset: int, data: bytes) -> Dict[str, Any]:
        """Editar bytes."""
        if isinstance(offset, str) and offset.startswith('0x'):
            offset = int(offset, 16)
        return self.hex_editor.edit_bytes(offset, data)
    
    def hex_search(self, pattern: str, search_type: str = 'exact') -> Dict[str, Any]:
        """Buscar padrão."""
        if isinstance(pattern, str) and pattern.startswith('0x'):
            pattern = bytes.fromhex(pattern[2:])
        return self.hex_editor.search(pattern, search_type)
    
    def hex_extract_strings(self, file_path: str, min_length: int = 4) -> Dict[str, Any]:
        """Extrair strings de arquivo."""
        return self.hex_editor.extract_strings(file_path, min_length)
    
    def hex_compare(self, file1: str, file2: str) -> Dict[str, Any]:
        """Comparar dois arquivos."""
        return self.hex_editor.compare_files(file1, file2)
    
    # ============================================================
    # MÉTODOS HTTP
    # ============================================================
    
    def http_start_capture(self, host: str = None, port: int = None) -> Dict[str, Any]:
        """Iniciar captura HTTP."""
        return self.fiddler.start_capture(host, port)
    
    def http_stop_capture(self) -> Dict[str, Any]:
        """Parar captura HTTP."""
        return self.fiddler.stop_capture()
    
    def http_get_sessions(self, limit: int = 100) -> Dict[str, Any]:
        """Obter sessões HTTP."""
        return self.fiddler.get_sessions(limit=limit)
    
    def http_analyze_jwt(self, token: str) -> Dict[str, Any]:
        """Analisar token JWT."""
        return self.fiddler.analyze_jwt(token)
    
    def http_export(self, format_type: str = 'json') -> Dict[str, Any]:
        """Exportar sessões HTTP."""
        return self.fiddler.export_sessions(format_type)
    
    # ============================================================
    # MÉTODOS VM
    # ============================================================
    
    def vm_create(self, name: str, os_type: str = 'windows',
                  memory_mb: int = 4096) -> Dict[str, Any]:
        """Criar VM."""
        return self.flare_vm.create_vm(name, os_type, memory_mb)
    
    def vm_snapshot(self, vm_name: str, snapshot_name: str = None) -> Dict[str, Any]:
        """Criar snapshot."""
        return self.flare_vm.snapshot(vm_name, snapshot_name)
    
    def vm_list(self) -> Dict[str, Any]:
        """Listar VMs."""
        return self.flare_vm.list_vms()
    
    def vm_run_analysis(self, vm_name: str, binary_path: str) -> Dict[str, Any]:
        """Executar análise em VM."""
        return self.flare_vm.run_analysis(vm_name, binary_path)
    
    # ============================================================
    # MÉTODOS UTILITÁRIOS
    # ============================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Obter status do agente."""
        return {
            **self.status,
            'uptime_seconds': time.time() - self.start_time,
            'session_id': self.session_id,
            'config': self.config,
        }
    
    def get_available_commands(self) -> List[str]:
        """Retornar lista de comandos disponíveis."""
        methods = [m for m in dir(self) if not m.startswith('_')]
        return sorted(methods)
    
    def batch_analyze(self, binary_paths: List[str], 
                      output_format: str = 'json') -> Dict[str, Any]:
        """
        Análise em lote de múltiplos binários.
        
        Args:
            binary_paths: Lista de caminhos
            output_format: 'json', 'text', ou 'html'
            
        Returns:
            Resultados consolidados
        """
        results = {
            'total': len(binary_paths),
            'successful': 0,
            'failed': 0,
            'results': [],
        }
        
        for path in binary_paths:
            try:
                result = self.analyze(path)
                results['results'].append(result)
                results['successful'] += 1
            except Exception as e:
                results['results'].append({
                    'binary': path,
                    'error': str(e),
                    'success': False,
                })
                results['failed'] += 1
        
        # Save consolidated result
        if self.config.get('auto_save', True):
            output_dir = Path(self.config.get('output_dir', '.'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if output_format == 'json':
                output_file = output_dir / f'batch_analysis_{self.session_id}.json'
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
            elif output_format == 'text':
                output_file = output_dir / f'batch_analysis_{self.session_id}.txt'
                with open(output_file, 'w') as f:
                    f.write(f"Batch Analysis Report\n")
                    f.write(f"Total: {results['total']}\n")
                    f.write(f"Successful: {results['successful']}\n")
                    f.write(f"Failed: {results['failed']}\n\n")
                    for r in results['results']:
                        f.write(f"\n{'='*60}\n")
                        f.write(f"Binary: {r.get('binary', 'N/A')}\n")
                        if r.get('success'):
                            f.write(f"Strings: {r.get('results', {}).get('strings', {}).get('total', 0)}\n")
                            f.write(f"Functions: {len(r.get('results', {}).get('ghidra', {}).get('functions', []))}\n")
                        else:
                            f.write(f"Error: {r.get('error', 'Unknown')}\n")
        
        return results
    
    def _save_result(self, binary_path: str, result: dict):
        """Salvar resultado da análise."""
        output_dir = Path(self.config.get('output_dir', '.'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Safe filename
        safe_name = ''.join(c if c.isalnum() or c in '._-' else '_' for c in os.path.basename(binary_path))
        output_file = output_dir / f'{safe_name}_analysis_{self.session_id}.json'
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        return str(output_file)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.debug_stop()
        self.fiddler.stop_capture()
        return False


# ============================================================
# FUNÇÕES DE INTEGRAÇÃO COM OPENCODE/AGENTES
# ============================================================

def create_ai_tool(name: str, description: str, 
                   execute_func: Callable) -> Dict[str, Any]:
    """
    Criar ferramenta para AI.
    
    Args:
        name: Nome da ferramenta
        description: Descrição para o AI
        execute_func: Função a executar
        
    Returns:
        Dict compatível com tools de AI
    """
    return {
        'type': 'function',
        'function': {
            'name': name,
            'description': description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'args': {
                        'type': 'object',
                        'description': 'Argumentos para a ferramenta',
                    }
                },
                'required': ['args'],
            },
            'execute': execute_func,
        }
    }


def get_re_tools() -> List[Dict[str, Any]]:
    """
    Retornar lista completa de ferramentas RE para AI.
    
    Returns:
        Lista de ferramentas formatadas para AI
    """
    tools = []
    
    # Análise
    tools.append(create_ai_tool(
        're_analyze_binary',
        'Analisar binário completo (strings, funções, tipos, CFG)',
        lambda args: agent.analyze(args.get('binary_path'))
    ))
    
    tools.append(create_ai_tool(
        're_decompile_function',
        'Descompilar função específica para pseudocódigo',
        lambda args: agent.decompile(
            args.get('binary_path'),
            args.get('address'),
            args.get('engine', 'ghidra')
        )
    ))
    
    # Debugging
    tools.append(create_ai_tool(
        're_debug_start',
        'Iniciar debugging de executável ou attach a processo',
        lambda args: agent.debug_start(
            args.get('executable'),
            args.get('process_id')
        )
    ))
    
    tools.append(create_ai_tool(
        're_debug_step',
        'Step into/over no debugger',
        lambda args: agent.debug_step(args.get('step_type', 'into'))
    ))
    
    tools.append(create_ai_tool(
        're_debug_get_registers',
        'Obter estado atual dos registros',
        lambda args: agent.debug_get_registers()
    ))
    
    tools.append(create_ai_tool(
        're_debug_set_breakpoint',
        'Adicionar breakpoint em endereço',
        lambda args: agent.debug_breakpoint(args.get('address'))
    ))
    
    tools.append(create_ai_tool(
        're_debug_memory_read',
        'Ler memória do processo debuggeado',
        lambda args: agent.debug_memory_read(args.get('address'), args.get('size', 256))
    ))
    
    # Hex Editor
    tools.append(create_ai_tool(
        're_hex_open',
        'Abrir arquivo no editor hexadecimal',
        lambda args: agent.hex_open(args.get('file_path'))
    ))
    
    tools.append(create_ai_tool(
        're_hex_view',
        'Visualizar dados hexadecimais',
        lambda args: agent.hex_view(args.get('offset'), args.get('length', 256))
    ))
    
    tools.append(create_ai_tool(
        're_hex_search',
        'Buscar padrão no arquivo',
        lambda args: agent.hex_search(args.get('pattern'))
    ))
    
    # HTTP
    tools.append(create_ai_tool(
        're_http_start_capture',
        'Iniciar captura de tráfego HTTP/HTTPS',
        lambda args: agent.http_start_capture()
    ))
    
    tools.append(create_ai_tool(
        're_http_get_sessions',
        'Obter sessões HTTP capturadas',
        lambda args: agent.http_get_sessions()
    ))
    
    tools.append(create_ai_tool(
        're_http_analyze_jwt',
        'Analisar token JWT',
        lambda args: agent.http_analyze_jwt(args.get('token'))
    ))
    
    return tools


# Instância global
agent = REAgent()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='RE Agent for AI')
    parser.add_argument('--tool', help='Tool to test')
    parser.add_argument('--args', help='Arguments as JSON')
    
    args = parser.parse_args()
    
    if args.tool:
        # Get tool function
        tool_func = getattr(agent, args.tool, None)
        if tool_func:
            import json
            tool_args = json.loads(args.args) if args.args else {}
            result = tool_func(**tool_args)
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f'Tool not found: {args.tool}')
            print(f'Available tools: {", ".join([m for m in dir(agent) if not m.startswith("_")])}')
    else:
        print('RE Agent v1.0 - AI Integration Module')
        print()
        print('Available tools:')
        for tool in sorted([m for m in dir(agent) if not m.startswith('_')]):
            print(f'  - {tool}')
        print()
        print('Usage: python ai_integration.py --tool analyze --args \'{"binary_path": "C:\\path\\to\\exe"}\'')