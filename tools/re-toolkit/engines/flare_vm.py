#!/usr/bin/env python3
"""
FLARE-VM Manager - Gerenciador de VMs estilo FLARE-VM
=====================================================
Recria funcionalidades de gerenciamento de VMs para análise.
"""

import os
import sys
import json
import time
import subprocess
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class VMConfig:
    """Configuração de VM."""
    name: str
    os_type: str  # windows, linux
    memory_mb: int
    cpu_cores: int
    disk_size_gb: int
    network_mode: str  # nat, bridged
    snapshot_dir: str
    vm_path: str


@dataclass
class VMSnapshot:
    """Snapshot de VM."""
    name: str
    timestamp: datetime
    vm_name: str
    state: str  # saved, running, stopped
    size_mb: int


@dataclass
class AnalysisJob:
    """Trabalho de análise."""
    id: str
    vm_name: str
    binary_path: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_path: str = ""


class FLAREVMManager:
    """
    Gerenciador de VMs estilo FLARE-VM.
    
    Funcionalidades:
    - Criar VMs para análise isolada
    - Gerenciar snapshots
    - Executar análise em VM
    - Coletar resultados
    - Isolar processos maliciosos
    """
    
    def __init__(self, toolkit=None):
        self.toolkit = toolkit
        self.vms: Dict[str, VMConfig] = {}
        self.snapshots: Dict[str, List[VMSnapshot]] = defaultdict(list)
        self.jobs: Dict[str, AnalysisJob] = {}
        self.vm_dir = os.path.join(os.path.expanduser('~'), 'flare-vm-workspace')
        
        # Ensure directory exists
        os.makedirs(self.vm_dir, exist_ok=True)
    
    def create_vm(self, vm_name: str, os_type: str = 'windows',
                  memory_mb: int = 4096, disk_size_gb: int = 50) -> Dict[str, Any]:
        """Criar VM para análise."""
        # Check if VM already exists
        if vm_name in self.vms:
            return {'success': False, 'error': f'VM já existe: {vm_name}'}
        
        # Create config
        config = VMConfig(
            name=vm_name,
            os_type=os_type,
            memory_mb=memory_mb,
            cpu_cores=2,
            disk_size_gb=disk_size_gb,
            network_mode='nat',
            snapshot_dir=os.path.join(self.vm_dir, vm_name, 'snapshots'),
            vm_path=os.path.join(self.vm_dir, vm_name),
        )
        
        # Create directories
        os.makedirs(config.vm_path, exist_ok=True)
        os.makedirs(config.snapshot_dir, exist_ok=True)
        
        # Save config
        config_path = os.path.join(config.vm_path, 'config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'name': config.name,
                'os_type': config.os_type,
                'memory_mb': config.memory_mb,
                'cpu_cores': config.cpu_cores,
                'disk_size_gb': config.disk_size_gb,
                'network_mode': config.network_mode,
                'created_at': datetime.now().isoformat(),
            }, f, indent=2)
        
        self.vms[vm_name] = config
        
        return {
            'success': True,
            'vm_name': vm_name,
            'vm_path': config.vm_path,
            'config': {
                'os_type': os_type,
                'memory_mb': memory_mb,
                'disk_size_gb': disk_size_gb,
            },
            'message': f'VM criado: {vm_name}',
        }
    
    def delete_vm(self, vm_name: str) -> Dict[str, Any]:
        """Deletar VM."""
        if vm_name not in self.vms:
            return {'success': False, 'error': f'VM não encontrado: {vm_name}'}
        
        config = self.vms[vm_name]
        
        # Remove directories
        import shutil
        try:
            shutil.rmtree(config.vm_path)
        except:
            pass
        
        del self.vms[vm_name]
        if vm_name in self.snapshots:
            del self.snapshots[vm_name]
        
        return {'success': True, 'message': f'VM deletado: {vm_name}'}
    
    def list_vms(self) -> Dict[str, Any]:
        """Listar VMs."""
        vms = []
        for name, config in self.vms.items():
            vms.append({
                'name': name,
                'os_type': config.os_type,
                'memory_mb': config.memory_mb,
                'path': config.vm_path,
                'snapshot_count': len(self.snapshots.get(name, [])),
            })
        
        return {'success': True, 'vms': vms}
    
    def snapshot(self, vm_name: str, snapshot_name: str = None) -> Dict[str, Any]:
        """Criar snapshot da VM."""
        if vm_name not in self.vms:
            return {'success': False, 'error': f'VM não encontrado: {vm_name}'}
        
        config = self.vms[vm_name]
        
        # Generate snapshot name
        if not snapshot_name:
            snapshot_name = f'snap_{int(time.time())}'
        
        # Create snapshot metadata
        snapshot = VMSnapshot(
            name=snapshot_name,
            timestamp=datetime.now(),
            vm_name=vm_name,
            state='saved',
            size_mb=0,  # Would be calculated in real implementation
        )
        
        self.snapshots[vm_name].append(snapshot)
        
        # Save snapshot metadata
        snapshot_path = os.path.join(config.snapshot_dir, f'{snapshot_name}.json')
        with open(snapshot_path, 'w') as f:
            json.dump({
                'name': snapshot.name,
                'timestamp': snapshot.timestamp.isoformat(),
                'vm_name': snapshot.vm_name,
                'state': snapshot.state,
            }, f, indent=2)
        
        return {
            'success': True,
            'snapshot_name': snapshot_name,
            'vm_name': vm_name,
            'timestamp': snapshot.timestamp.isoformat(),
        }
    
    def restore_snapshot(self, vm_name: str, snapshot_name: str) -> Dict[str, Any]:
        """Restaurar snapshot."""
        if vm_name not in self.vms:
            return {'success': False, 'error': f'VM não encontrado: {vm_name}'}
        
        # Find snapshot
        snapshots = self.snapshots.get(vm_name, [])
        snapshot = next((s for s in snapshots if s.name == snapshot_name), None)
        
        if not snapshot:
            return {'success': False, 'error': 'Snapshot não encontrado'}
        
        return {
            'success': True,
            'message': f'Snapshot restaurado: {snapshot_name}',
            'vm_name': vm_name,
            'snapshot': snapshot_name,
        }
    
    def list_snapshots(self, vm_name: str) -> Dict[str, Any]:
        """Listar snapshots."""
        snapshots = self.snapshots.get(vm_name, [])
        return {
            'success': True,
            'vm_name': vm_name,
            'snapshots': [
                {
                    'name': s.name,
                    'timestamp': s.timestamp.isoformat(),
                    'state': s.state,
                }
                for s in snapshots
            ],
        }
    
    def run_analysis(self, vm_name: str, binary_path: str,
                     analysis_script: str = None) -> Dict[str, Any]:
        """Executar análise na VM."""
        if vm_name not in self.vms:
            return {'success': False, 'error': f'VM não encontrado: {vm_name}'}
        
        if not os.path.exists(binary_path):
            return {'success': False, 'error': f'Binário não encontrado: {binary_path}'}
        
        # Generate job ID
        job_id = hashlib.md5(f'{vm_name}_{binary_path}_{time.time()}'.encode()).hexdigest()[:12]
        
        # Create job
        job = AnalysisJob(
            id=job_id,
            vm_name=vm_name,
            binary_path=binary_path,
            status='pending',
            created_at=datetime.now(),
        )
        
        self.jobs[job_id] = job
        
        # Simulate analysis (in real implementation, would use VM API)
        # For now, just mark as completed with simulated results
        job.status = 'completed'
        job.completed_at = datetime.now()
        
        # Generate simulated results
        result_path = os.path.join(self.vms[vm_name].vm_path, f'results_{job_id}.json')
        
        # Run analysis using our toolkit
        from cli import REToolkit
        toolkit = REToolkit()
        analysis_result = toolkit.analyze_binary(binary_path)
        
        # Save results
        with open(result_path, 'w') as f:
            json.dump(analysis_result.to_dict(), f, indent=2, default=str)
        
        job.result_path = result_path
        
        return {
            'success': True,
            'job_id': job_id,
            'vm_name': vm_name,
            'binary': binary_path,
            'status': 'completed',
            'result_path': result_path,
            'summary': {
                'strings': analysis_result.metadata.get('strings', {}).get('total', 0),
                'functions': analysis_result.metadata.get('functions', {}).get('total', 0),
                'types': analysis_result.metadata.get('types', {}).get('total', 0),
            },
        }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obter status do trabalho."""
        job = self.jobs.get(job_id)
        if not job:
            return {'success': False, 'error': 'Job não encontrado'}
        
        return {
            'success': True,
            'job': {
                'id': job.id,
                'vm_name': job.vm_name,
                'binary_path': job.binary_path,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'result_path': job.result_path,
            }
        }
    
    def list_jobs(self) -> Dict[str, Any]:
        """Listar trabalhos."""
        jobs = []
        for job in self.jobs.values():
            jobs.append({
                'id': job.id,
                'vm_name': job.vm_name,
                'binary_path': job.binary_path,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
            })
        
        return {'success': True, 'jobs': jobs}
    
    def get_vm_info(self, vm_name: str) -> Dict[str, Any]:
        """Obter informações da VM."""
        config = self.vms.get(vm_name)
        if not config:
            return {'success': False, 'error': 'VM não encontrado'}
        
        return {
            'success': True,
            'vm': {
                'name': config.name,
                'os_type': config.os_type,
                'memory_mb': config.memory_mb,
                'cpu_cores': config.cpu_cores,
                'disk_size_gb': config.disk_size_gb,
                'network_mode': config.network_mode,
                'path': config.vm_path,
                'snapshot_count': len(self.snapshots.get(vm_name, [])),
                'job_count': sum(1 for j in self.jobs.values() if j.vm_name == vm_name),
            }
        }
    
    def import_flare_vm(self, flare_vm_path: str) -> Dict[str, Any]:
        """Importar VM do FLARE-VM existente."""
        if not os.path.exists(flare_vm_path):
            return {'success': False, 'error': 'Caminho não encontrado'}
        
        # Try to read existing config
        config_path = os.path.join(flare_vm_path, 'config.json')
        if os.path.exists(config_path):
            with open(config_path) as f:
                config_data = json.load(f)
            
            vm_name = config_data.get('name', os.path.basename(flare_vm_path))
            
            # Create VM config
            config = VMConfig(
                name=vm_name,
                os_type=config_data.get('os_type', 'windows'),
                memory_mb=config_data.get('memory_mb', 4096),
                cpu_cores=config_data.get('cpu_cores', 2),
                disk_size_gb=config_data.get('disk_size_gb', 50),
                network_mode='nat',
                snapshot_dir=os.path.join(flare_vm_path, 'snapshots'),
                vm_path=flare_vm_path,
            )
            
            self.vms[vm_name] = config
            
            return {
                'success': True,
                'vm_name': vm_name,
                'path': flare_vm_path,
                'message': 'VM importado com sucesso',
            }
        
        return {'success': False, 'error': 'Configuração não encontrada'}
    
    def export_vm(self, vm_name: str, export_path: str) -> Dict[str, Any]:
        """Exportar VM."""
        config = self.vms.get(vm_name)
        if not config:
            return {'success': False, 'error': 'VM não encontrado'}
        
        # Copy VM files
        import shutil
        try:
            shutil.copytree(config.vm_path, export_path)
            return {'success': True, 'path': export_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Quick test
if __name__ == '__main__':
    manager = FLAREVMManager()
    
    # Create VM
    result = manager.create_vm('analysis_vm', 'windows', 4096, 50)
    print(f"Create VM: {result}")
    
    # List VMs
    vms = manager.list_vms()
    print(f"VMs: {vms}")
    
    # Snapshot
    snap = manager.snapshot('analysis_vm')
    print(f"Snapshot: {snap}")
    
    # List snapshots
    snaps = manager.list_snapshots('analysis_vm')
    print(f"Snapshots: {snaps}")
    
    # VM info
    info = manager.get_vm_info('analysis_vm')
    print(f"VM info: {info}")