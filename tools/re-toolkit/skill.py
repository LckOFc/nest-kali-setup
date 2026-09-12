#!/usr/bin/env python3
"""
RE Toolkit - Skill para AI
============================
Integração completa para uso por agentes de IA.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'engines'))

from cli import REToolkit, REResult


class RESkill:
    """
    Skill completa de Engenharia Reversa para AI.
    
    Este módulo fornece uma interface unificada para todas as
    ferramentas de RE, acessível por comandos simples.
    """
    
    def __init__(self, config_path: str = None):
        self.toolkit = REToolkit(config_path)
        self.command_history = []
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Executar comando de RE.
        
        Comandos disponíveis:
        
        ANALISE:
          analyze <binary_path>          - Analisar binário completo
          decompile <binary> <addr>      - Descompilar função
          functions <binary>             - Listar funções
          types <binary>                 - Listar tipos
          strings <binary>               - Listar strings
          cfg <binary>                   - Análise de fluxo
          
        DEBUGGING:
          debug_start <exe_or_pid>       - Iniciar debugging
          debug_stop                     - Parar debugging
          debug_step                     - Step into
          debug_continue                 - Continuar execução
          debug_breakpoint <addr>        - Adicionar breakpoint
          debug_memory_read <addr> <size> - Ler memória
          debug_memory_write <addr> <data> - Escrever memória
          debug_registers                - Ver registros
          debug_disasm <addr>            - Disassembly
          
        HEX EDITOR:
          hex_open <file>                - Abrir arquivo
          hex_view <offset> <length>     - Visualizar hex
          hex_edit <offset> <data>       - Editar bytes
          hex_search <pattern>           - Buscar padrão
          hex_strings <file>             - Extrair strings
          
        HTTP:
          http_start                     - Iniciar captura
          http_stop                      - Parar captura
          http_sessions                  - Ver sessões
          http_analyze_jwt <token>       - Analisar JWT
          http_export <format>           - Exportar sessões
          
        VM:
          vm_create <name>               - Criar VM
          vm_snapshot <name>             - Snapshot
          vm_list                        - Listar VMs
          vm_run <vm> <binary>           - Executar análise
          
        UTILS:
          status                         - Status do toolkit
          history                        - Histórico de comandos
        """
        # Record command
        self.command_history.append({
            'timestamp': time.time(),
            'command': command,
            'session_id': self.session_id,
        })
        
        # Parse command
        parts = command.strip().split()
        if not parts:
            return {'success': False, 'error': 'Comando vazio'}
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        try:
            if cmd == 'analyze':
                if not args:
                    return {'error': 'Caminho do binário necessário'}
                return self.toolkit.analyze_binary(args[0])
                
            elif cmd == 'decompile':
                if len(args) < 2:
                    return {'error': 'Uso: decompile <binary> <address>'}
                addr = int(args[1], 16) if args[1].startswith('0x') else int(args[1])
                return self.toolkit.decompile_function(args[0], addr)
                
            elif cmd == 'functions':
                if not args:
                    return {'error': 'Caminho do binário necessário'}
                result = self.toolkit.analyze_binary(args[0])
                return {'functions': result.get('metadata', {}).get('functions', {})}
                
            elif cmd == 'types':
                if not args:
                    return {'error': 'Caminho do binário necessário'}
                result = self.toolkit.analyze_binary(args[0])
                return {'types': result.get('metadata', {}).get('types', {})}
                
            elif cmd == 'strings':
                if not args:
                    return {'error': 'Caminho do binário necessário'}
                # Use hex editor for strings
                from engines.hex_editor import HexEditor
                editor = HexEditor()
                return editor.extract_strings(args[0])
                
            elif cmd == 'debug_start':
                if not args:
                    return {'error': 'Executável ou PID necessário'}
                exe = args[0]
                if exe.startswith('0x') or exe.isdigit():
                    return self.toolkit.debug_process(process_id=int(exe, 16 if exe.startswith('0x') else 10))
                else:
                    return self.toolkit.debug_process(executable=exe)
                    
            elif cmd == 'debug_stop':
                return self.toolkit.stop_debugger()
                
            elif cmd == 'debug_step':
                return self.toolkit.step_into()
                
            elif cmd == 'debug_continue':
                return self.toolkit.continue_execution()
                
            elif cmd == 'debug_breakpoint':
                if not args:
                    return {'error': 'Endereço necessário'}
                addr = int(args[0], 16) if args[0].startswith('0x') else int(args[0])
                return self.toolkit.set_breakpoint(addr)
                
            elif cmd == 'debug_memory_read':
                if len(args) < 2:
                    return {'error': 'Uso: debug_memory_read <addr> <size>'}
                addr = int(args[0], 16)
                size = int(args[1])
                return self.toolkit.read_memory(addr, size)
                
            elif cmd == 'debug_memory_write':
                if len(args) < 2:
                    return {'error': 'Uso: debug_memory_write <addr> <data>'}
                addr = int(args[0], 16)
                data = bytes.fromhex(args[1])
                return self.toolkit.write_memory(addr, data)
                
            elif cmd == 'debug_registers':
                return self.toolkit.x64dbg.get_registers()
                
            elif cmd == 'debug_disasm':
                if not args:
                    return {'error': 'Endereço necessário'}
                addr = int(args[0], 16)
                return self.toolkit.x64dbg.get_disassembly(addr)
                
            elif cmd == 'hex_open':
                if not args:
                    return {'error': 'Caminho do arquivo necessário'}
                return self.toolkit.hex_editor.open_file(args[0])
                
            elif cmd == 'hex_view':
                if not args:
                    return {'error': 'Offset necessário'}
                offset = int(args[0], 16) if args[0].startswith('0x') else int(args[0])
                length = int(args[1]) if len(args) > 1 else 256
                return self.toolkit.hex_editor.get_hex_view(offset, length)
                
            elif cmd == 'hex_search':
                if not args:
                    return {'error': 'Padrão hexadecial necessário'}
                pattern = bytes.fromhex(args[0])
                return self.toolkit.hex_editor.search(args[0], 'exact')
                
            elif cmd == 'http_start':
                return self.toolkit.start_http_capture()
                
            elif cmd == 'http_stop':
                return self.toolkit.stop_http_capture()
                
            elif cmd == 'http_sessions':
                return self.toolkit.get_http_sessions()
                
            elif cmd == 'http_analyze_jwt':
                if not args:
                    return {'error': 'Token JWT necessário'}
                return self.toolkit.fiddler.analyze_jwt(args[0])
                
            elif cmd == 'http_export':
                fmt = args[0] if args else 'json'
                return self.toolkit.fiddler.export_sessions(fmt)
                
            elif cmd == 'vm_create':
                if not args:
                    return {'error': 'Nome da VM necessário'}
                return self.toolkit.flare_vm.create_vm(args[0])
                
            elif cmd == 'vm_snapshot':
                if not args:
                    return {'error': 'Nome da VM necessário'}
                return self.toolkit.flare_vm.snapshot(args[0])
                
            elif cmd == 'vm_list':
                return self.toolkit.flare_vm.list_vms()
                
            elif cmd == 'vm_run':
                if len(args) < 2:
                    return {'error': 'Uso: vm_run <vm_name> <binary_path>'}
                return self.toolkit.flare_vm.run_analysis(args[0], args[1])
                
            elif cmd == 'status':
                return self.toolkit.get_status()
                
            elif cmd == 'history':
                return {
                    'history': self.command_history[-50:],
                    'total': len(self.command_history),
                }
                
            else:
                return {'error': f'Comando não reconhecido: {cmd}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def batch_analyze(self, binary_path: str, 
                      analysis_type: str = 'full') -> Dict[str, Any]:
        """
        Análise em lote.
        
        Tipos:
          full    - Análise completa (tudo)
          quick   - Análise rápida (strings + funções)
          deep    - Análise profunda (completa + debugging simulado)
        """
        results = {}
        
        if analysis_type in ('full', 'deep'):
            results['main'] = self.execute(f'analyze {binary_path}')
        
        if analysis_type in ('full', 'deep'):
            results['strings'] = self.execute(f'strings {binary_path}')
            results['functions'] = self.execute(f'functions {binary_path}')
            results['types'] = self.execute(f'types {binary_path}')
        
        if analysis_type == 'deep':
            # Simulate debugging
            results['debug'] = self.execute('debug_start dummy')
            results['registers'] = self.execute('debug_registers')
        
        return {
            'binary': binary_path,
            'type': analysis_type,
            'results': results,
            'session_id': self.session_id,
        }
    
    def get_help(self, command: str = None) -> str:
        """Retornar ajuda."""
        help_text = """
RE Toolkit - Comandos Disponíveis
==================================

ANÁLISE:
  analyze <binary>          Analisar binário completo
  decompile <binary> <addr> Descompilar função
  functions <binary>        Listar funções identificadas
  types <binary>            Listar tipos recuperados
  strings <binary>          Extrair e categorizar strings
  cfg <binary>              Análise de fluxo de controle

DEBUGGING:
  debug_start <exe|pid>     Iniciar debugging
  debug_stop                Parar debugging
  debug_step                Step into
  debug_continue            Continuar execução
  debug_breakpoint <addr>   Adicionar breakpoint
  debug_memory_read <a> <s> Ler memória
  debug_memory_write <a> <d> Escrever memória
  debug_registers           Ver registros
  debug_disasm <addr>       Disassembly

HEX EDITOR:
  hex_open <file>           Abrir arquivo
  hex_view <offset> [len]   Visualizar hex
  hex_search <pattern>      Buscar padrão
  hex_strings <file>        Extrair strings

HTTP:
  http_start                Iniciar captura
  http_stop                 Parar captura
  http_sessions             Ver sessões
  http_analyze_jwt <token>  Analisar JWT
  http_export <format>      Exportar

VM:
  vm_create <name>          Criar VM
  vm_snapshot <name>        Snapshot
  vm_list                   Listar VMs
  vm_run <vm> <binary>      Executar análise

UTILS:
  status                    Status do toolkit
  history                   Histórico de comandos
  help [command]            Esta ajuda
"""
        return help_text


# Quick test
if __name__ == '__main__':
    skill = RESkill()
    
    # Test help
    print(skill.get_help())
    
    # Test status
    result = skill.execute('status')
    print(f"\nStatus: {result}")
    
    # Test with agy.exe if available
    agy_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
    if os.path.exists(agy_path):
        print(f"\nAnalyzing: {agy_path}")
        result = skill.execute(f'analyze {agy_path}')
        if hasattr(result, 'success'):
            print(f"Analysis complete: {result.success}")
            if hasattr(result, 'metadata') and result.metadata:
                print(f"Strings: {result.metadata.get('strings', {}).get('total', 0)}")
                print(f"Functions: {result.metadata.get('functions', {}).get('total', 0)}")
        else:
            print(f"Analysis: {result}")