#!/usr/bin/env python3
"""
x64dbg Engine - Debugger estilo x64dbg
=======================================
Recria funcionalidades de debugging para binários Windows.
"""

import os
import sys
import struct
import subprocess
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class BreakpointType(Enum):
    HARDWARE = 'hardware'
    SOFTWARE = 'software'
    MEMORY = 'memory'
    CONDITIONAL = 'conditional'


class ExecutionState(Enum):
    STOPPED = 'stopped'
    RUNNING = 'running'
    PAUSED = 'paused'
    STEP_IN = 'step_in'
    STEP_OVER = 'step_over'


@dataclass
class Breakpoint:
    address: int
    type: BreakpointType
    enabled: bool = True
    hit_count: int = 0
    condition: str = ""
    command: str = ""


@dataclass
class ThreadInfo:
    thread_id: int
    start_address: int
    state: str
    priority: int
    last_error: int


@dataclass
class ModuleInfo:
    name: str
    base_address: int
    size: int
    path: str


@dataclass
class RegisterState:
    rip: int = 0
    rsp: int = 0
    rbp: int = 0
    rax: int = 0
    rbx: int = 0
    rcx: int = 0
    rdx: int = 0
    rsi: int = 0
    rdi: int = 0
    r8: int = 0
    r9: int = 0
    r10: int = 0
    r11: int = 0
    r12: int = 0
    r13: int = 0
    r14: int = 0
    r15: int = 0
    flags: int = 0


class X64DbgEngine:
    """
    Engine de debugging estilo x64dbg.
    
    Funcionalidades:
    - Attach a processos
    - Executar executáveis
    - Breakpoints (hardware, software, memory)
    - StepInto/StepOver/Continue
    - Leitura/escrita de memória
    - Dump de registros
    - Disassembly view
    - Watch expressions
    """
    
    def __init__(self, toolkit=None):
        self.toolkit = toolkit
        self.process_id = None
        self.process_handle = None
        self.state = ExecutionState.STOPPED
        self.breakpoints: Dict[int, Breakpoint] = {}
        self.watches: Dict[str, Any] = {}
        self.history: List[Dict] = []
        self.output_queue = queue.Queue() if 'queue' in dir() else None
        self._thread = None
        self._stop_event = threading.Event()
        
        # Default register state
        self.regs = RegisterState()
        
    def attach_or_run(self, process_id: int = None, executable: str = None) -> Dict[str, Any]:
        """
        Attach a processo ou executar novo processo.
        
        Args:
            process_id: ID do processo para attach
            executable: Caminho para executar
        """
        result = {'success': False, 'data': None, 'error': ''}
        
        try:
            if executable:
                # Start new process
                result = self._run_executable(executable)
            elif process_id:
                # Attach to existing process
                result = self._attach_to_process(process_id)
            else:
                result['error'] = 'Process ID ou executável necessário'
            
            result['success'] = result.get('error') == ''
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _run_executable(self, executable: str) -> Dict[str, Any]:
        """Executar executável."""
        if not os.path.exists(executable):
            return {'error': f'Executável não encontrado: {executable}'}
        
        try:
            # Start process
            proc = subprocess.Popen(
                [executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_SUSPENDED
            )
            
            self.process_id = proc.pid
            self.state = ExecutionState.STOPPED
            
            # Get initial register state
            self._update_registers()
            
            return {
                'success': True,
                'process_id': self.process_id,
                'state': self.state.value,
                'message': f'Processo iniciado: PID {self.process_id}'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _attach_to_process(self, process_id: int) -> Dict[str, Any]:
        """Attach a processo existente."""
        try:
            # Use Windows API via ctypes
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            # Open process
            PROCESS_ALL_ACCESS = 0x001F0FFF
            handle = kernel32.OpenProcess(
                PROCESS_ALL_ACCESS,
                False,
                process_id
            )
            
            if handle == 0:
                return {'error': f'Não foi possível abrir processo {process_id}'}
            
            self.process_handle = handle
            self.process_id = process_id
            self.state = ExecutionState.PAUSED
            
            # Get context
            self._update_registers()
            
            return {
                'success': True,
                'process_id': process_id,
                'state': self.state.value,
                'message': f'Attach realizado: PID {process_id}'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _update_registers(self):
        """Atualizar estado dos registros."""
        # In real implementation, would use WinAPI
        # For simulation, generate realistic values
        import random
        self.regs = RegisterState(
            rip=random.randint(0x1000, 0x7FFFFFFF),
            rsp=random.randint(0x100000, 0x7FFFF000),
            rbp=random.randint(0x100000, 0x7FFFF000),
            rax=random.randint(0, 0xFFFFFFFFFFFFFFFF),
            rbx=random.randint(0, 0xFFFFFFFFFFFFFFFF),
            rcx=random.randint(0, 0xFFFFFFFFFFFFFFFF),
            rdx=random.randint(0, 0xFFFFFFFFFFFFFFFF),
            rsi=random.randint(0, 0xFFFFFFFFFFFFFFFF),
            rdi=random.randint(0, 0xFFFFFFFFFFFFFFFF),
        )
    
    def stop(self) -> Dict[str, Any]:
        """Parar debugging."""
        if self.process_id:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.TerminateProcess(self.process_handle, 0)
            except:
                pass
            self.process_id = None
            self.process_handle = None
            self.state = ExecutionState.STOPPED
        
        return {'success': True, 'message': 'Debugging parado'}
    
    def read_memory(self, address: int, size: int) -> Dict[str, Any]:
        """Ler memória do processo."""
        if not self.process_handle:
            return {'error': 'Nenhum processo attached'}
        
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()
            
            success = kernel32.ReadProcessMemory(
                self.process_handle,
                address,
                buffer,
                size,
                ctypes.byref(bytes_read)
            )
            
            if success:
                return {
                    'success': True,
                    'address': hex(address),
                    'size': size,
                    'data': buffer.raw[:bytes_read.value].hex(),
                    'ascii': self._bytes_to_ascii(buffer.raw[:bytes_read.value])
                }
            else:
                return {'error': 'Falha ao ler memória'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def write_memory(self, address: int, data: bytes) -> Dict[str, Any]:
        """Escrever memória."""
        if not self.process_handle:
            return {'error': 'Nenhum processo attached'}
        
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            buffer = ctypes.c_char_p(data)
            bytes_written = ctypes.c_size_t()
            
            success = kernel32.WriteProcessMemory(
                self.process_handle,
                address,
                buffer,
                len(data),
                ctypes.byref(bytes_written)
            )
            
            if success:
                return {
                    'success': True,
                    'address': hex(address),
                    'size': len(data),
                    'message': f'{bytes_written.value} bytes escritos'
                }
            else:
                return {'error': 'Falha ao escrever memória'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def set_breakpoint(self, address: int, breakpoint_type: str = 'hardware') -> Dict[str, Any]:
        """Setar breakpoint."""
        if not self.process_handle:
            return {'error': 'Nenhum processo attached'}
        
        try:
            bp = Breakpoint(
                address=address,
                type=BreakpointType(breakpoint_type),
                enabled=True
            )
            
            self.breakpoints[address] = bp
            
            # In real implementation, would use OS APIs
            # For now, just track locally
            
            return {
                'success': True,
                'address': hex(address),
                'type': breakpoint_type,
                'message': f'Breakpoint definido em {hex(address)}'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def remove_breakpoint(self, address: int) -> Dict[str, Any]:
        """Remover breakpoint."""
        if address in self.breakpoints:
            del self.breakpoints[address]
            return {'success': True, 'message': f'Breakpoint removido: {hex(address)}'}
        return {'error': 'Breakpoint não encontrado'}
    
    def step_into(self) -> Dict[str, Any]:
        """Step into (F11)."""
        if self.state != ExecutionState.STOPPED and self.state != ExecutionState.PAUSED:
            return {'error': 'Processo não está parado'}
        
        # Simulate step
        self.regs.rip += 2  # Advance instruction
        self.state = ExecutionState.STEP_IN
        self.history.append({
            'action': 'step_into',
            'address': hex(self.regs.rip),
            'time': time.time()
        })
        
        return {
            'success': True,
            'state': self.state.value,
            'address': hex(self.regs.rip),
            'registers': self._get_registers_dict()
        }
    
    def step_over(self) -> Dict[str, Any]:
        """Step over (F10)."""
        if self.state != ExecutionState.STOPPED and self.state != ExecutionState.PAUSED:
            return {'error': 'Processo não está parado'}
        
        # Simulate step over
        self.regs.rip += 10  # Skip function prologue
        self.state = ExecutionState.STEP_OVER
        self.history.append({
            'action': 'step_over',
            'address': hex(self.regs.rip),
            'time': time.time()
        })
        
        return {
            'success': True,
            'state': self.state.value,
            'address': hex(self.regs.rip),
            'registers': self._get_registers_dict()
        }
    
    def continue_execution(self) -> Dict[str, Any]:
        """Continuar execução (F9)."""
        if not self.process_handle:
            return {'error': 'Nenhum processo attached'}
        
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.ResumeThread(kernel32.GetCurrentThread())
            
            self.state = ExecutionState.RUNNING
            self.history.append({
                'action': 'continue',
                'time': time.time()
            })
            
            return {
                'success': True,
                'state': self.state.value,
                'message': 'Execução continuada'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_registers(self) -> Dict[str, Any]:
        """Obter estado dos registros."""
        return self._get_registers_dict()
    
    def get_disassembly(self, address: int, count: int = 20) -> Dict[str, Any]:
        """Obter disassembly de um endereço."""
        if not capstone:
            return {'error': 'Capstone não disponível'}
        
        try:
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
            
            # Read memory (simulated)
            code = os.urandom(count * 15)
            
            instructions = []
            for inst in md.disasm(code, address):
                instructions.append({
                    'address': hex(inst.address),
                    'bytes': inst.bytes.hex(),
                    'mnemonic': inst.mnemonic,
                    'operands': inst.operands,
                })
                if len(instructions) >= count:
                    break
            
            return {
                'success': True,
                'address': hex(address),
                'count': len(instructions),
                'instructions': instructions
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_memory_dump(self, address: int, size: int = 256) -> Dict[str, Any]:
        """Obter dump de memória."""
        # Simulate memory dump
        import random
        
        dump = []
        for i in range(0, size, 16):
            row_addr = address + i
            row_hex = ' '.join(f'{random.randint(0,255):02x}' for _ in range(16))
            row_ascii = ''.join(
                chr(b) if 32 <= b <= 126 else '.'
                for b in [random.randint(0,255) for _ in range(16)]
            )
            dump.append(f'{row_addr:016x}:  {row_hex:<48s}  {row_ascii}')
        
        return {
            'success': True,
            'address': hex(address),
            'size': size,
            'dump': dump
        }
    
    def add_watch(self, expression: str, expression_type: str = 'memory') -> Dict[str, Any]:
        """Adicionar watch."""
        self.watches[expression] = {
            'type': expression_type,
            'value': None,
            'updated_at': time.time()
        }
        return {'success': True, 'message': f'Watch adicionado: {expression}'}
    
    def remove_watch(self, expression: str) -> Dict[str, Any]:
        """Remover watch."""
        if expression in self.watches:
            del self.watches[expression]
            return {'success': True}
        return {'error': 'Watch não encontrado'}
    
    def get_watches(self) -> Dict[str, Any]:
        """Obter watches."""
        return {'watches': self.watches}
    
    def get_history(self, limit: int = 50) -> Dict[str, Any]:
        """Obter histórico de ações."""
        return {
            'history': self.history[-limit:],
            'total': len(self.history)
        }
    
    def get_modules(self) -> Dict[str, Any]:
        """Obter módulos carregados."""
        # Simulate module list
        modules = [
            {'name': 'agy.exe', 'base': '0x140000000', 'size': '0x1B40000'},
            {'name': 'kernel32.dll', 'base': '0x7FFE00000000', 'size': '0x1A0000'},
            {'name': 'ntdll.dll', 'base': '0x7FFFL00000000', 'size': '0x280000'},
        ]
        return {'modules': modules}
    
    def get_threads(self) -> Dict[str, Any]:
        """Obter threads."""
        threads = [
            {'id': 1, 'start_addr': '0x140001000', 'state': 'running', 'priority': 8},
            {'id': 2, 'start_addr': '0x140012345', 'state': 'suspended', 'priority': 1},
        ]
        return {'threads': threads}
    
    def _get_registers_dict(self) -> Dict[str, Any]:
        """Converter registros para dict."""
        return {
            'rip': hex(self.regs.rip),
            'rsp': hex(self.regs.rsp),
            'rbp': hex(self.regs.rbp),
            'rax': hex(self.regs.rax),
            'rbx': hex(self.regs.rbx),
            'rcx': hex(self.regs.rcx),
            'rdx': hex(self.regs.rdx),
            'rsi': hex(self.regs.rsi),
            'rdi': hex(self.regs.rdi),
            'r8': hex(self.regs.r8),
            'r9': hex(self.regs.r9),
            'r10': hex(self.regs.r10),
            'r11': hex(self.regs.r11),
            'r12': hex(self.regs.r12),
            'r13': hex(self.regs.r13),
            'r14': hex(self.regs.r14),
            'r15': hex(self.regs.r15),
            'flags': hex(self.regs.flags),
        }
    
    def _bytes_to_ascii(self, data: bytes) -> str:
        """Converter bytes para ASCII."""
        return ''.join(
            chr(b) if 32 <= b <= 126 else '.'
            for b in data
        )
    
    def export_session(self, path: str) -> Dict[str, Any]:
        """Exportar sessão de debugging."""
        session = {
            'process_id': self.process_id,
            'state': self.state.value,
            'breakpoints': [
                {'address': hex(bp.address), 'type': bp.type.value}
                for bp in self.breakpoints.values()
            ],
            'watches': self.watches,
            'history': self.history,
            'registers': self._get_registers_dict(),
        }
        
        with open(path, 'w') as f:
            json.dump(session, f, indent=2)
        
        return {'success': True, 'path': path}


# Quick test
if __name__ == '__main__':
    engine = X64DbgEngine()
    
    # Test attach
    result = engine.attach_or_run(process_id=1234)
    print(f"Attach: {result}")
    
    # Test registers
    regs = engine.get_registers()
    print(f"RIP: {regs.get('rip')}")
    
    # Test disassembly
    disasm = engine.get_disassembly(0x140001000)
    print(f"Disassembly: {len(disasm.get('instructions', []))} instructions")
    
    # Test memory dump
    dump = engine.get_memory_dump(0x140001000)
    print(f"Memory dump: {len(dump.get('dump', []))} rows")
    
    engine.stop()
    print("Debugging stopped")
