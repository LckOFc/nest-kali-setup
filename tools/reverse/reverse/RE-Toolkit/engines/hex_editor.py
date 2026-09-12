#!/usr/bin/env python3
"""
Hex Editor Engine - Editor estilo HxD
=====================================
Recria funcionalidades de editor hexadecimal.
"""

import os
import struct
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


@dataclass
class HexView:
    """Visualização hexadecal."""
    file_path: str
    offset: int
    data: bytes
    width: int = 16


@dataclass
class Selection:
    """Seleção de dados."""
    start: int
    end: int
    data: bytes = b''


@dataclass
class SearchResult:
    """Resultado de busca."""
    offset: int
    data: bytes
    ascii: str


class HexEditor:
    """
    Editor hexadecimal estilo HxD.
    
    Funcionalidades:
    - Visualização hex + ASCII
    - Edição de bytes
    - Busca por valor/regex/texto
    - Comparação de arquivos
    - Colar de clipboard
    - Conversão de formatos (bin, hex, dec, oct)
    """
    
    def __init__(self):
        self.current_file = None
        self.current_data = None
        self.selection = None
        self.history = []
        self.history_index = -1
        self.max_history = 100
        
    def open_file(self, file_path: str) -> Dict[str, Any]:
        """Abrir arquivo."""
        if not os.path.exists(file_path):
            return {'success': False, 'error': f'Arquivo não encontrado: {file_path}'}
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            self.current_file = file_path
            self.current_data = bytearray(data)
            self.history = [bytearray(data)]
            self.history_index = 0
            
            return {
                'success': True,
                'path': file_path,
                'size': len(data),
                'size_human': self._format_size(len(data)),
                'modification_time': os.path.getmtime(file_path),
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def close_file(self) -> Dict[str, Any]:
        """Fechar arquivo."""
        self.current_file = None
        self.current_data = None
        self.selection = None
        return {'success': True}
    
    def get_hex_view(self, offset: int = 0, length: int = 256) -> Dict[str, Any]:
        """Obter visualização hex."""
        if not self.current_data:
            return {'error': 'Nenhum arquivo aberto'}
        
        offset = max(0, min(offset, len(self.current_data)))
        length = min(length, len(self.current_data) - offset)
        
        data = self.current_data[offset:offset + length]
        lines = self._format_hex_view(data, offset)
        
        return {
            'success': True,
            'offset': offset,
            'length': length,
            'lines': lines,
            'total_lines': (len(self.current_data) + 15) // 16,
        }
    
    def edit_bytes(self, offset: int, data: bytes) -> Dict[str, Any]:
        """Editar bytes."""
        if not self.current_data:
            return {'error': 'Nenhum arquivo aberto'}
        
        try:
            # Save to history
            self._save_history()
            
            # Apply edit
            data_len = len(data)
            if offset + data_len > len(self.current_data):
                return {'error': 'Offset fora do range'}
            
            self.current_data[offset:offset + data_len] = data
            
            return {
                'success': True,
                'offset': offset,
                'bytes_written': data_len,
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def insert_bytes(self, offset: int, data: bytes) -> Dict[str, Any]:
        """Inserir bytes."""
        if not self.current_data:
            return {'error': 'Nenhum arquivo aberto'}
        
        try:
            self._save_history()
            self.current_data[offset:offset] = data
            return {'success': True, 'bytes_inserted': len(data)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_bytes(self, offset: int, count: int) -> Dict[str, Any]:
        """Deletar bytes."""
        if not self.current_data:
            return {'error': 'Nenhum arquivo aberto'}
        
        try:
            self._save_history()
            del self.current_data[offset:offset + count]
            return {'success': True, 'bytes_deleted': count}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def undo(self) -> Dict[str, Any]:
        """Desfazer."""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_data = bytearray(self.history[self.history_index])
            return {'success': True}
        return {'success': False, 'error': 'Nada para desfazer'}
    
    def redo(self) -> Dict[str, Any]:
        """Refazer."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_data = bytearray(self.history[self.history_index])
            return {'success': True}
        return {'success': False, 'error': 'Nada para refazer'}
    
    def search(self, pattern: bytes, search_type: str = 'exact', 
               max_results: int = 100) -> Dict[str, Any]:
        """Buscar padrão."""
        if not self.current_data:
            return {'error': 'Nenhum arquivo aberto'}
        
        results = []
        
        if search_type == 'exact':
            # Exact byte sequence
            i = 0
            while i <= len(self.current_data) - len(pattern) and len(results) < max_results:
                pos = self.current_data.find(pattern, i)
                if pos == -1:
                    break
                results.append(SearchResult(pos, pattern, self._bytes_to_ascii(pattern)))
                i = pos + 1
                
        elif search_type == 'wildcard':
            # Wildcard search (? = any byte)
            results = self._search_wildcard(pattern, max_results)
            
        elif search_type == 'string':
            # String search
            pattern_str = pattern.decode('ascii', errors='replace')
            i = 0
            while i <= len(self.current_data) - len(pattern) and len(results) < max_results:
                pos = self.current_data.find(pattern, i)
                if pos == -1:
                    break
                results.append(SearchResult(pos, pattern, pattern_str))
                i = pos + 1
                
        elif search_type == 'regex':
            # Regex search
            try:
                regex = re.compile(pattern)
                for match in regex.finditer(self.current_data):
                    if len(results) >= max_results:
                        break
                    results.append(SearchResult(match.start(), match.group(), 
                                              self._bytes_to_ascii(match.group())))
            except:
                return {'error': 'Regex inválido'}
                
        elif search_type == 'sequence':
            # Value sequence (auto, word, dword, qword)
            results = self._search_sequence(pattern, max_results)
        
        return {
            'success': True,
            'count': len(results),
            'results': [
                {'offset': hex(r.offset), 'data': r.data.hex(), 'ascii': r.ascii}
                for r in results[:20]  # Return first 20
            ]
        }
    
    def convert_selection(self, format_type: str) -> Dict[str, Any]:
        """Converter seleção para outro formato."""
        if not self.selection:
            return {'error': 'Nenhuma seleção ativa'}
        
        data = self.selection.data
        result = {'format': format_type, 'value': ''}
        
        if format_type == 'decimal':
            if len(data) == 1:
                result['value'] = str(data[0])
            elif len(data) == 2:
                result['value'] = str(struct.unpack('<H', data)[0])
            elif len(data) == 4:
                result['value'] = str(struct.unpack('<I', data)[0])
            elif len(data) == 8:
                result['value'] = str(struct.unpack('<Q', data)[0])
                
        elif format_type == 'hex':
            result['value'] = data.hex()
            
        elif format_type == 'ascii':
            result['value'] = self._bytes_to_ascii(data)
            
        elif format_type == 'float':
            if len(data) == 4:
                result['value'] = str(struct.unpack('<f', data)[0])
            elif len(data) == 8:
                result['value'] = str(struct.unpack('<d', data)[0])
                
        elif format_type == 'double':
            if len(data) == 8:
                result['value'] = str(struct.unpack('<d', data)[0])
        
        return result
    
    def compare_files(self, file1: str, file2: str) -> Dict[str, Any]:
        """Comparar dois arquivos."""
        try:
            with open(file1, 'rb') as f:
                data1 = f.read()
            with open(file2, 'rb') as f:
                data2 = f.read()
            
            # Find differences
            diffs = []
            min_len = min(len(data1), len(data2))
            
            for i in range(min_len):
                if data1[i] != data2[i]:
                    diffs.append({
                        'offset': i,
                        'file1_byte': hex(data1[i]),
                        'file2_byte': hex(data2[i]),
                    })
                    if len(diffs) >= 100:
                        break
            
            if len(data1) != len(data2):
                diffs.append({
                    'offset': min_len,
                    'note': 'Size difference',
                    'file1_size': len(data1),
                    'file2_size': len(data2),
                })
            
            return {
                'success': True,
                'file1': file1,
                'file2': file2,
                'same': len(diffs) == 0,
                'diffs': diffs[:20],
                'total_diffs': len(diffs),
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_strings(self, file_path: str, min_length: int = 4) -> Dict[str, Any]:
        """Extrair strings de arquivo."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Extract printable strings
            string_pattern = rb'[\x20-\x7e]{' + str(min_length).encode() + rb',}'
            strings = re.findall(string_pattern, data)
            
            # Categorize
            categories = {
                'ascii': [],
                'unicode': [],
                'urls': [],
                'paths': [],
                'errors': [],
            }
            
            for s_bytes in strings[:50000]:
                try:
                    s = s_bytes.decode('ascii')
                except:
                    continue
                
                sl = s.lower()
                
                if 'http' in sl or '://' in s:
                    categories['urls'].append(s[:100])
                elif '\\\\' in s or '/home/' in s or '.exe' in s or '.dll' in s:
                    categories['paths'].append(s[:100])
                elif any(kw in sl for kw in ['error', 'failed', 'cannot']):
                    categories['errors'].append(s[:100])
                else:
                    categories['ascii'].append(s[:100])
            
            return {
                'success': True,
                'total': len(strings),
                'categories': {k: v[:20] for k, v in categories.items()},
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_file_info(self) -> Dict[str, Any]:
        """Obter informações do arquivo atual."""
        if not self.current_file:
            return {'error': 'Nenhum arquivo aberto'}
        
        stat = os.stat(self.current_file)
        
        return {
            'success': True,
            'path': self.current_file,
            'size': stat.st_size,
            'size_human': self._format_size(stat.st_size),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'is_modified': self._is_modified(),
        }
    
    def save_file(self, path: str = None) -> Dict[str, Any]:
        """Salvar arquivo."""
        if not self.current_data:
            return {'error': 'Nenhum arquivo aberto'}
        
        try:
            save_path = path or self.current_file
            with open(save_path, 'wb') as f:
                f.write(self.current_data)
            
            return {'success': True, 'path': save_path, 'bytes_written': len(self.current_data)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def selection_set(self, start: int, end: int) -> Dict[str, Any]:
        """Definir seleção."""
        if not self.current_data:
            return {'error': 'Nenhum arquivo aberto'}
        
        start = max(0, min(start, len(self.current_data)))
        end = max(start, min(end, len(self.current_data)))
        
        self.selection = Selection(start, end, bytes(self.current_data[start:end]))
        
        return {
            'success': True,
            'start': start,
            'end': end,
            'size': end - start,
            'size_human': self._format_size(end - start),
        }
    
    def selection_clear(self) -> Dict[str, Any]:
        """Limpar seleção."""
        self.selection = None
        return {'success': True}
    
    # ============================================================
    # METODOS INTERNOS
    # ============================================================
    
    def _format_hex_view(self, data: bytes, offset: int) -> List[str]:
        """Formatar visualização hex."""
        lines = []
        
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            chunk_offset = offset + i
            
            # Hex part
            hex_parts = [f'{b:02x}' for b in chunk]
            hex_str = ' '.join(hex_parts)
            
            # Gap at 8 bytes
            if len(hex_parts) > 8:
                hex_str = hex_str[:47] + '  ' + hex_str[48:]
            
            # ASCII part
            ascii_str = ''.join(
                chr(b) if 32 <= b <= 126 else '.'
                for b in chunk
            )
            
            # Line
            line = f'{chunk_offset:012x}:  {hex_str:<49s}  |{ascii_str}|'
            lines.append(line)
        
        return lines
    
    def _save_history(self):
        """Salvar estado atual no history."""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append(bytearray(self.current_data))
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1
    
    def _is_modified(self) -> bool:
        """Verificar se arquivo foi modificado."""
        if not self.current_file or not self.current_data:
            return False
        
        try:
            with open(self.current_file, 'rb') as f:
                original = f.read()
            return bytes(self.current_data) != original
        except:
            return False
    
    def _bytes_to_ascii(self, data: bytes) -> str:
        """Converter bytes para ASCII."""
        return ''.join(
            chr(b) if 32 <= b <= 126 else '.'
            for b in data
        )
    
    def _format_size(self, size: int) -> str:
        """Formatar tamanho."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} PB'
    
    def _search_wildcard(self, pattern: bytes, max_results: int) -> List[SearchResult]:
        """Buscar com wildcard."""
        results = []
        pattern_len = len(pattern)
        
        i = 0
        while i <= len(self.current_data) - pattern_len and len(results) < max_results:
            match = True
            for j in range(pattern_len):
                if pattern[j] != ord('?') and pattern[j] != self.current_data[i + j]:
                    match = False
                    break
            
            if match:
                found = bytes(self.current_data[i:i+pattern_len])
                results.append(SearchResult(i, found, self._bytes_to_ascii(found)))
            
            i += 1
        
        return results
    
    def _search_sequence(self, pattern: bytes, max_results: int) -> List[SearchResult]:
        """Buscar sequência de valores."""
        results = []
        
        if len(pattern) == 1:
            # Single byte
            value = pattern[0]
            for i in range(len(self.current_data) - 1):
                if self.current_data[i] == value:
                    if i + 1 < len(self.current_data) and self.current_data[i+1] == value:
                        results.append(SearchResult(i, bytes([value, value]), self._bytes_to_ascii(bytes([value, value]))))
                        if len(results) >= max_results:
                            break
        
        return results


# Quick test
if __name__ == '__main__':
    editor = HexEditor()
    
    # Test with agy.exe
    test_file = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
    if os.path.exists(test_file):
        result = editor.open_file(test_file)
        print(f"Open: {result}")
        
        # Get hex view
        view = editor.get_hex_view(0, 256)
        print(f"Hex view: {len(view.get('lines', []))} lines")
        
        # Search
        search = editor.search(b'\x55\x48\x89\xe5')  # push rbp; mov rbp, rsp
        print(f"Search: {search.get('count', 0)} results")
        
        # Extract strings
        strings = editor.extract_strings(test_file)
        print(f"Strings: {strings.get('total', 0)} total")
        
        editor.close_file()