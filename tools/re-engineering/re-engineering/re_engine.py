"""
Re-Engineering Engine v1 — Analise multi-formato completa
Suporta: .exe, .dll, .bin, .js, .bat, .py, .ps1, .sh, .obj, .so, .elf
"""

import sys
import os
import json
import re
import hashlib
import struct
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter

# Try imports
try:
    import pefile
    HAS_PEFILE = True
except ImportError:
    HAS_PEFILE = False
    pefile = None

try:
    import capstone
    from capstone import *
    HAS_CAPSTONE = True
except ImportError:
    HAS_CAPSTONE = False
    capstone = None

# Config logging
log_dir = Path(__file__).parent / 'log'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 're_engine.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('re_engine')


# =========================================================================
# Base Analyzer
# =========================================================================

class BaseAnalyzer:
    """Base class for all file analyzers"""
    
    extensions = []
    description = ''
    
    def analyze(self, filepath: str) -> Dict:
        raise NotImplementedError
    
    def get_magic(self, data: bytes) -> Optional[str]:
        """Check magic bytes"""
        if data[:2] == b'MZ':
            return 'PE'
        if data[:4] == b'\x7fELF':
            return 'ELF'
        if data[:2] in (b'\xca\xfe', b'\xfe\xca', b'\xce\xfa'):
            return 'MACHO'
        if data[:4] == b'PK\x03\x04':
            return 'ZIP'
        if data[:3] == b'<?x':
            return 'XML'
        return None


# =========================================================================
# PE Analyzer (.exe, .dll)
# =========================================================================

class PEAnalyzer(BaseAnalyzer):
    """Analyze PE files (Windows .exe, .dll)"""
    
    extensions = ['.exe', '.dll', '.sys', '.ocx', '.drv']
    description = 'Windows PE (Executable) analyzer'
    
    def __init__(self):
        if not HAS_PEFILE:
            logger.warning('pefile not installed. PE analysis disabled.')
    
    def analyze(self, filepath: str) -> Dict:
        if not HAS_PEFILE:
            return {'error': 'pefile module not installed. Run: pip install pefile'}
        
        result = {
            'file': filepath,
            'type': 'PE',
            'analyzed_at': datetime.now().isoformat(),
            'pe_info': {},
            'sections': [],
            'imports': [],
            'exports': [],
            'strings': [],
            'interesting_strings': [],
            'hashes': {},
            'risks': [],
        }
        
        try:
            pe = pefile.PE(filepath)
            
            # ---- PE INFO — ALL values explicitly converted to Python primitives ----
            def safe_int(val, default=0):
                """Convert pefile value to int safely"""
                try:
                    return int(val)
                except (TypeError, ValueError, AttributeError):
                    return default
            
            def safe_str(val, default=''):
                """Convert pefile value to str safely"""
                try:
                    if isinstance(val, bytes):
                        return val.decode('utf-8', errors='replace')
                    return str(val)
                except:
                    return default
            
            machine_val = safe_int(getattr(pe.FILE_HEADER, 'Machine', 0))
            result['pe_info'] = {
                'machine': pefile.MACHINE_TYPE.get(machine_val, hex(machine_val)),
                'num_sections': safe_int(pe.FILE_HEADER.NumberOfSections),
                'timestamp': datetime.fromtimestamp(safe_int(pe.FILE_HEADER.TimeDateStamp)).isoformat() if safe_int(pe.FILE_HEADER.TimeDateStamp) else 'N/A',
                'characteristics': self._parse_characteristics(safe_int(getattr(pe.FILE_HEADER, 'Characteristics', 0))),
                'entry_point': hex(safe_int(pe.OPTIONAL_HEADER.AddressOfEntryPoint)),
                'image_base': hex(safe_int(pe.OPTIONAL_HEADER.ImageBase)),
                'image_size': safe_int(pe.OPTIONAL_HEADER.SizeOfImage),
                'headers_size': safe_int(pe.OPTIONAL_HEADER.SizeOfHeaders),
                'checksum': hex(safe_int(pe.OPTIONAL_HEADER.CheckSum)) if safe_int(pe.OPTIONAL_HEADER.CheckSum) else 'N/A',
                'subsystem': pefile.SUBSYSTEM_TYPE.get(safe_int(pe.OPTIONAL_HEADER.Subsystem), hex(safe_int(pe.OPTIONAL_HEADER.Subsystem))),
                'dll_characteristics': self._parse_dll_characteristics(safe_int(getattr(pe.OPTIONAL_HEADER, 'DllCharacteristics', 0))),
                'major_os_version': safe_int(pe.OPTIONAL_HEADER.MajorOperatingSystemVersion),
                'minor_os_version': safe_int(pe.OPTIONAL_HEADER.MinorOperatingSystemVersion),
                'major_image_version': safe_int(pe.OPTIONAL_HEADER.MajorImageVersion),
                'minor_image_version': safe_int(pe.OPTIONAL_HEADER.MinorImageVersion),
                'major_linker_version': safe_int(pe.OPTIONAL_HEADER.MajorLinkerVersion),
                'minor_linker_version': safe_int(pe.OPTIONAL_HEADER.MinorLinkerVersion),
            }
            
            # Detect if DLL or EXE
            dll_chars = safe_int(getattr(pe.OPTIONAL_HEADER, 'DllCharacteristics', 0))
            is_dll = bool(dll_chars & 0x2000)
            result['pe_info']['is_dll'] = is_dll
            result['pe_info']['format'] = 'DLL' if is_dll else 'EXE'
            
            # ---- SECTIONS — explicit type conversion ----
            for section in pe.sections:
                try:
                    sec_name_bytes = getattr(section, 'Name', b'')
                    sec_name = sec_name_bytes.decode('utf-8', errors='replace').strip('\x00') if isinstance(sec_name_bytes, bytes) else str(sec_name_bytes)
                    
                    sec_data = {
                        'name': sec_name,
                        'virtual_size': safe_int(getattr(section, 'Misc_VirtualSize', 0)),
                        'virtual_address': hex(safe_int(getattr(section, 'VirtualAddress', 0))),
                        'raw_size': safe_int(getattr(section, 'SizeOfRawData', 0)),
                        'raw_offset': safe_int(getattr(section, 'PointerToRawData', 0)),
                        'entropy': round(float(self._calc_entropy(section.get_data())), 4),
                        'characteristics': self._parse_section_chars(safe_int(getattr(section, 'Characteristics', 0))),
                    }
                    
                    # Check for suspicious section traits
                    if sec_data['entropy'] > 7.0:
                        sec_data['suspicious'] = True
                        sec_data['reason'] = 'High entropy (possible encryption/compression)'
                        result['risks'].append(f"Section '{sec_name}' has high entropy ({sec_data['entropy']:.2f})")
                    if sec_data['raw_size'] == 0 and sec_data['virtual_size'] > 0:
                        sec_data['suspicious'] = True
                        sec_data['reason'] = 'Empty raw data but has virtual size'
                    result['sections'].append(sec_data)
                except Exception as se:
                    logger.debug(f"Section parse error: {se}")
            
            # ---- IMPORTS — explicit type conversion ----
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                try:
                    for entry in pe.DIRECTORY_ENTRY_IMPORT:
                        imps = []
                        for imp in entry.imports:
                            try:
                                imp_name = '?'
                                if hasattr(imp, 'name') and imp.name:
                                    try:
                                        imp_name = imp.name.decode('utf-8', errors='replace') if isinstance(imp.name, bytes) else str(imp.name)
                                    except:
                                        imp_name = '?'
                                elif hasattr(imp, 'ordinal') and imp.ordinal:
                                    imp_name = f'#{int(imp.ordinal)}'
                                
                                imp_addr = 'N/A'
                                if hasattr(imp, 'address') and imp.address:
                                    try:
                                        imp_addr = hex(int(imp.address))
                                    except:
                                        pass
                                
                                imps.append({'name': str(imp_name), 'address': str(imp_addr)})
                            except:
                                imps.append({'name': '?', 'address': 'N/A'})
                        
                        dll_name = '?'
                        if hasattr(entry, 'dll'):
                            try:
                                raw_dll = entry.dll
                                dll_name = raw_dll.decode('utf-8', errors='replace') if isinstance(raw_dll, bytes) else str(raw_dll)
                            except:
                                dll_name = '?'
                        
                        if imps and dll_name and dll_name != '?':
                            result['imports'].append({
                                'library': str(dll_name),
                                'functions': imps,
                            })
                except Exception as ie:
                    logger.debug(f"Import parse error: {ie}")
            
            # ---- SUSPICIOUS IMPORTS CHECK ----
            suspicious_imports = [
                'WinExec', 'ShellExecute', 'CreateProcess', 'WriteProcessMemory',
                'VirtualAllocEx', 'CreateRemoteThread', 'URLDownloadToFile',
                'InternetOpen', 'HttpSendRequest', 'CryptEncrypt', 'CryptDecrypt',
                'RegSetValue', 'RegCreateKey', 'OpenProcess', 'AdjustTokenPrivileges',
                'IsDebuggerPresent', 'CheckRemoteDebuggerPresent', 'NtQueryInformationProcess',
                'VirtualProtect', 'NtWriteVirtualMemory', 'QueueUserAPC',
            ]
            imported_funcs = []
            for imp_entry in result['imports']:
                for func in imp_entry.get('functions', []):
                    imported_funcs.append(str(func.get('name', '')))
            
            for susp in suspicious_imports:
                if any(susp.lower() in f.lower() for f in imported_funcs):
                    result['risks'].append(f"Suspicious import: {susp}")
            
            # ---- EXPORTS ----
            if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
                try:
                    if hasattr(pe.DIRECTORY_ENTRY_EXPORT, 'symbols'):
                        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                            try:
                                exp_name = '?'
                                if hasattr(exp, 'name') and exp.name:
                                    try:
                                        exp_name = exp.name.decode('utf-8', errors='replace') if isinstance(exp.name, bytes) else str(exp.name)
                                    except:
                                        exp_name = '?'
                                elif hasattr(exp, 'ordinal'):
                                    exp_name = f'ordinal_{int(exp.ordinal)}'
                                
                                exp_addr = 'N/A'
                                if hasattr(exp, 'address') and exp.address:
                                    try:
                                        exp_addr = hex(int(exp.address))
                                    except:
                                        pass
                                
                                result['exports'].append({
                                    'name': str(exp_name),
                                    'ordinal': int(getattr(exp, 'ordinal', 0)),
                                    'address': str(exp_addr),
                                })
                            except:
                                pass
                except Exception as ee:
                    logger.debug(f"Export parse error: {ee}")
            
            # ---- STRINGS ----
            try:
                mapped = pe.get_memory_mapped_image()
                result['strings'] = self._extract_strings(mapped)
                result['interesting_strings'] = self._filter_interesting(result['strings'])
            except Exception as se:
                logger.debug(f"String extraction error: {se}")
                result['strings'] = []
                result['interesting_strings'] = []
            
            # ---- HASHES ----
            try:
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                result['hashes'] = {
                    'md5': hashlib.md5(file_data).hexdigest(),
                    'sha1': hashlib.sha1(file_data).hexdigest(),
                    'sha256': hashlib.sha256(file_data).hexdigest(),
                }
            except Exception as he:
                result['hashes'] = {'error': str(he)}
            
            # ---- VERDICT ----
            result['verdict'] = self._compute_verdict(result)
            
            try:
                pe.close()
            except:
                pass
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"PE analysis error: {e}")
        
        return result
    
    def _calc_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy"""
        if not data:
            return 0.0
        counter = Counter(data)
        length = len(data)
        entropy = 0.0
        for count in counter.values():
            if count > 0:
                p = count / length
                entropy -= p * (p.bit_length() if hasattr(p, 'bit_length') else 0)
                import math
                entropy -= p * math.log2(p)
        return round(entropy, 4)
    
    def _extract_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Extract printable ASCII strings"""
        strings = []
        current = bytearray()
        for byte in data:
            if 32 <= byte <= 126:  # Printable ASCII
                current.append(byte)
            else:
                if len(current) >= min_length:
                    strings.append(current.decode('ascii', errors='replace'))
                current = bytearray()
        if len(current) >= min_length:
            strings.append(current.decode('ascii', errors='replace'))
        return strings
    
    def _filter_interesting(self, strings: List[str]) -> List[Dict]:
        """Filter strings for interesting content"""
        patterns = {
            'URL': r'https?://[^\s\<\">]+',
            'IP': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            'Email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'File_Path': r'[A-Za-z]:\\(?:[\w.]+\\)*[\w.]',
            'Registry': r'HKEY_[A-Z_]+\\[^\s]+',
            'Base64': r'[A-Za-z0-9+/]{20,}={0,2}',
            'MD5': r'[a-fA-F0-9]{32}',
            'SHA1': r'[a-fA-F0-9]{40}',
            'SHA256': r'[a-fA-F0-9]{64}',
            'Crypto_Key': r'(?:AES|RSA|DES|3DES|RC4|ECB|CBC)[_\-\s]*(?:key|KEY|Key)',
            'Password': r'(?:password|pass|passwd|pwd)[\s:=]+"?[^\s"<>]+',
            'API_Key': r'(?:api[_-]?key|apikey|access[_-]?token|secret)[\s:=]+"?[\w\-]{16,}',
            'Hardcoded': r'(?:eval|exec|system|popen|subprocess|os\.system|shell_exec)',
            'Suspicious': r'(?:cmd\.exe|powershell|/bin/sh|/bin/bash|reg\s+add|schtasks)',
        }
        
        found = []
        for s in strings:
            for pattern_name, pattern in patterns.items():
                try:
                    if re.search(pattern, s, re.IGNORECASE):
                        found.append({
                            'type': pattern_name,
                            'value': s[:200],
                            'match': True,
                        })
                        break
                except:
                    pass
        return found
    
    def _compute_verdict(self, result: Dict) -> Dict:
        """Compute security verdict"""
        score = 0
        findings = []
        
        # High entropy sections
        high_entropy = [s for s in result.get('sections', []) if isinstance(s, dict) and s.get('suspicious')]
        if high_entropy:
            score += len(high_entropy) * 15
            findings.append(f"{len(high_entropy)} section(s) with suspicious entropy")
        
        # Suspicious imports
        susp_count = len([r for r in result['risks'] if 'import' in r.lower()])
        if susp_count:
            score += susp_count * 10
            findings.append(f"{susp_count} suspicious import(s) detected")
        
        # Interesting strings
        urls = len([s for s in result['interesting_strings'] if s['type'] == 'URL'])
        if urls > 0:
            score += urls * 5
            findings.append(f"{urls} URL(s) embedded")
        
        # Crypto strings
        crypto = len([s for s in result['interesting_strings'] if s['type'] == 'Crypto_Key'])
        if crypto > 0:
            score += crypto * 8
            findings.append(f"{crypto} potential crypto key reference(s)")
        
        # Shell commands
        shell = len([s for s in result['interesting_strings'] if s['type'] == 'Suspicious'])
        if shell > 0:
            score += shell * 10
            findings.append(f"{shell} potential shell command(s)")
        
        # Determine threat level
        if score >= 50:
            threat = 'HIGH'
        elif score >= 25:
            threat = 'MEDIUM'
        elif score >= 10:
            threat = 'LOW'
        else:
            threat = 'CLEAN'
        
        return {
            'score': score,
            'threat_level': threat,
            'findings': findings,
            'recommendation': 'Investigate further' if threat in ('HIGH', 'MEDIUM') else 'No immediate concerns',
        }
    
    def _parse_characteristics(self, chars: int) -> List[str]:
        flags = []
        if chars & 0x0002: flags.append('IMAGE_FILE_EXECUTABLE_IMAGE')
        if chars & 0x0020: flags.append('IMAGE_FILE_LARGE_ADDRESS_AWARE')
        if chars & 0x0100: flags.append('IMAGE_FILE_DLL')
        if chars & 0x2000: flags.append('IMAGE_FILE_32BIT_MACHINE')
        return flags
    
    def _parse_dll_characteristics(self, chars: int) -> List[str]:
        flags = []
        if chars & 0x0020: flags.append('DYNAMIC_BASE')
        if chars & 0x0040: flags.append('NX_COMPAT')
        if chars & 0x0080: flags.append('NO_SEH')
        if chars & 0x0200: flags.append('HIGH_ENTROPY_VA')
        if chars & 0x0800: flags.append('FORCE_INTEGRITY')
        return flags
    
    def _parse_section_chars(self, chars: int) -> List[str]:
        flags = []
        if chars & 0x00000020: flags.append('EXECUTE')
        if chars & 0x00000040: flags.append('READ')
        if chars & 0x00000080: flags.append('WRITE')
        return flags
    
    def _calc_ssdeep(self, data: bytes) -> str:
        try:
            import ssdeep
            return ssdeep.hash(data)
        except ImportError:
            return 'N/A (pip install ssdeep)'


# =========================================================================
# Script Analyzers
# =========================================================================

class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyze JavaScript files"""
    
    extensions = ['.js', '.jsx', '.mjs', '.cjs']
    description = 'JavaScript analyzer'
    
    def analyze(self, filepath: str) -> Dict:
        result = {
            'file': filepath,
            'type': 'JavaScript',
            'analyzed_at': datetime.now().isoformat(),
            'lines': 0,
            'size_bytes': 0,
            'strings': [],
            'functions': [],
            'interesting_patterns': [],
            'hashes': {},
            'risks': [],
            'verdict': {},
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            result['size_bytes'] = len(content.encode('utf-8'))
            result['lines'] = content.count('\n') + 1
            
            # Extract strings
            result['strings'] = re.findall(r'["\']([^"\']{4,})["\']', content)
            
            # Find function declarations
            result['functions'] = re.findall(r'(?:function\s+(\w+)|(\w+)\s*=\s*function|const\s+(\w+)\s*=\s*\(|async\s+(\w+)\s*\()', content)
            
            # Dangerous patterns
            dangerous = {
                'eval': r'\beval\s*\(',
                'Function_constructor': r'\bnew\s+Function\s*\(',
                'innerHTML': r'\.innerHTML\s*=',
                'document_write': r'\bdocument\.write\s*\(',
                'setTimeout_string': r'\bsetTimeout\s*\(\s*["\']',
                'setInterval_string': r'\bsetInterval\s*\(\s*["\']',
                'unescape': r'\bunescape\s*\(',
                'fromCharCode': r'\bString\.fromCharCode\s*\(',
                'child_process': r'\brequire\s*\(\s*["\']child_process["\']\s*\)',
                'exec': r'\bexec\s*\(\s*[^)]+',
                'execFile': r'\bexecFile\s*\(',
                'spawn': r'\bspawn\s*\(',
                'spawnSync': r'\bspawnSync\s*\(',
                'execSync': r'\bexecSync\s*\(',
                'childProcess': r'\bchild_process',
                'fs_readFile': r'\brequire\s*\(\s*["\']fs["\']\s*\)',
                'xmlhttprequest': r'\bXMLHttpRequest\b',
                'fetch': r'\bfetch\s*\(',
                'crypto_decrypt': r'\bcrypto\s*.*(?:decrypt|encrypt)',
                'atob': r'\batob\s*\(',
                'btoa': r'\bbtoa\s*\(',
                'socket': r'\bsocket\.io|new\s+Socket|require\s*\(\s*["\']socket["\']',
                'net_connect': r'\bnet\.createConnection|net\.connect',
                'http_request': r'\bhttp\.request|https\.request',
                'cookie_access': r'\bdocument\.cookie',
                'localStorage': r'\blocalStorage\b',
                'sessionStorage': r'\bsessionStorage\b',
                'postMessage': r'\bpostMessage\s*\(',
                'location_hijack': r'\bwindow\.location\s*=',
                'eval_like': r'\bsetTimeout\s*\(\s*[`\'"]|setInterval\s*\(\s*[`\'"]',
            }
            
            for name, pattern in dangerous.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    result['interesting_patterns'].append({
                        'type': name,
                        'count': len(matches),
                        'samples': [str(m)[:100] for m in matches[:3]]
                    })
                    result['risks'].append(f"{name}: {len(matches)} occurrence(s)")
            
            # Hashes
            with open(filepath, 'rb') as f:
                data = f.read()
            result['hashes'] = {
                'md5': hashlib.md5(data).hexdigest(),
                'sha256': hashlib.sha256(data).hexdigest(),
            }
            
            # Verdict
            risk_score = len(result['risks']) * 10
            if risk_score >= 50:
                threat = 'SUSPICIOUS'
            elif risk_score >= 20:
                threat = 'MODERATE'
            else:
                threat = 'CLEAN'
            
            result['verdict'] = {
                'threat_level': threat,
                'risk_score': risk_score,
                'findings': result['risks'],
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result


class BatchAnalyzer(BaseAnalyzer):
    """Analyze Windows batch files (.bat, .cmd)"""
    
    extensions = ['.bat', '.cmd']
    description = 'Windows batch file analyzer'
    
    DANGEROUS_COMMANDS = {
        'del': r'\bdel\s+',
        'erase': r'\berase\s+',
        'format': r'\bformat\s+',
        'rmdir': r'\brmdir\s+',
        'rd\s': r'\brd\s+',
        'shutdown': r'\bshutdown\s+',
        'restart': r'\brestart\s+',
        'attrib': r'\battrib\s+[+-][rhsa]+\s+',
        'net': r'\bnet\s+(user|localgroup|share|start|stop)\s+',
        'sc': r'\bsc\s+(create|delete|config|start|stop)\s+',
        'reg': r'\breg\s+(add|delete|import|export|load|hivelist)\s+',
        'powershell': r'\bpowershell\s+',
        'mshta': r'\bmshta\s+',
        'certutil': r'\bcertutil\s+(-decode|-encode|--decode|--encode)',
        'bitsadmin': r'\bbitsadmin\s+',
        'wmic': r'\bwmic\s+',
        'cipher': r'\bcipher\s+',
        'diskpart': r'\bdiskpart\s+',
        'takeown': r'\btakeown\s+',
        'icacls': r'\bicacls\s+',
        'cacls': r'\bcacls\s+',
        'copy': r'\bcopy\s+.*>\s*',
        'move': r'\bmove\s+.*>\s*',
        'echo': r'\becho\s+.*\|\s*',
        'start': r'\bstart\s+(\/min|\/hidden|\/b)\s+',
        'rundll32': r'\brundll32\s+',
        'msiexec': r'\bmsiexec\s+',
        'ieexec': r'\bieexec\s+',
        'cscript': r'\bcscript\s+',
        'wscript': r'\bwscript\s+',
    }
    
    def analyze(self, filepath: str) -> Dict:
        result = {
            'file': filepath,
            'type': 'Batch',
            'analyzed_at': datetime.now().isoformat(),
            'lines': 0,
            'size_bytes': 0,
            'commands': [],
            'environment_vars': [],
            'risks': [],
            'hashes': {},
            'verdict': {},
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            result['size_bytes'] = sum(len(l.encode('utf-8')) for l in lines)
            result['lines'] = len(lines)
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('@') and 'echo' in line:
                    continue
                
                # Extract command
                cmd_match = re.match(r'^(\w+)', line)
                if cmd_match:
                    cmd = cmd_match.group(1).lower()
                    result['commands'].append({'line': i, 'command': cmd, 'full': line[:200]})
                
                # Check dangerous patterns
                for name, pattern in self.DANGEROUS_COMMANDS.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        result['risks'].append(f"Line {i}: {name} detected — {line[:100]}")
                
                # Environment variables
                env_matches = re.findall(r'%([^%]+)%', line)
                result['environment_vars'].extend(env_matches)
            
            # Hashes
            with open(filepath, 'rb') as f:
                data = f.read()
            result['hashes'] = {
                'md5': hashlib.md5(data).hexdigest(),
                'sha256': hashlib.sha256(data).hexdigest(),
            }
            
            # Verdict
            risk_score = len(result['risks']) * 15
            if risk_score >= 60:
                threat = 'DANGEROUS'
            elif risk_score >= 30:
                threat = 'SUSPICIOUS'
            elif risk_score >= 10:
                threat = 'MODERATE'
            else:
                threat = 'CLEAN'
            
            result['verdict'] = {
                'threat_level': threat,
                'risk_score': risk_score,
                'findings': result['risks'],
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result


class PythonAnalyzer(BaseAnalyzer):
    """Analyze Python source files"""
    
    extensions = ['.py', '.pyw']
    description = 'Python source analyzer'
    
    DANGEROUS_IMPORTS = [
        'os', 'subprocess', 'ctypes', 'socket', 'requests', 'urllib',
        'http', 'urllib.request', 'http.client', 'codecs', 'imp',
        'importlib', 'runpy', 'winreg', 'wmi', 'psutil', 'pty',
        'pickle', 'shelve', 'marshal', 'yaml', 'json', 'xml',
        'base64', 'zlib', 'zipfile', 'tarfile', 'shutil',
        'asyncio', 'aiohttp', 'twisted', 'scapy', 'dpkt',
    ]
    
    DANGEROUS_FUNCTIONS = [
        'eval', 'exec', 'compile', '__import__', 'input', 'open',
        'os.system', 'os.popen', 'os.exec', 'os.spawn',
        'subprocess.call', 'subprocess.run', 'subprocess.Popen',
        'socket.connect', 'socket.bind', 'socket.listen',
        'ctypes.CDLL', 'ctypes.WinDLL', 'ctypes.create_string_buffer',
    ]
    
    def analyze(self, filepath: str) -> Dict:
        result = {
            'file': filepath,
            'type': 'Python',
            'analyzed_at': datetime.now().isoformat(),
            'lines': 0,
            'size_bytes': 0,
            'imports': [],
            'functions': [],
            'classes': [],
            'dangerous_calls': [],
            'strings': [],
            'hashes': {},
            'risks': [],
            'verdict': {},
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.split('\n')
            
            result['size_bytes'] = len(content.encode('utf-8'))
            result['lines'] = len(lines)
            
            # Imports
            for line in lines:
                stripped = line.strip()
                # import X
                m = re.match(r'^import\s+(\w+)', stripped)
                if m:
                    mod = m.group(1)
                    result['imports'].append({'module': mod, 'line': lines.index(line)+1})
                    if mod.lower() in self.DANGEROUS_IMPORTS:
                        result['risks'].append(f"Line {lines.index(line)+1}: Dangerous import: {mod}")
                # from X import Y
                m = re.match(r'^from\s+(\w+)\s+import', stripped)
                if m:
                    mod = m.group(1)
                    result['imports'].append({'module': mod, 'line': lines.index(line)+1, 'type': 'from'})
                    if mod.lower() in self.DANGEROUS_IMPORTS:
                        result['risks'].append(f"Line {lines.index(line)+1}: Dangerous from-import: {mod}")
            
            # Functions
            for i, line in enumerate(lines, 1):
                m = re.match(r'^def\s+(\w+)\s*\(', line)
                if m:
                    result['functions'].append({'name': m.group(1), 'line': i})
                
                m = re.match(r'^class\s+(\w+)', line)
                if m:
                    result['classes'].append({'name': m.group(1), 'line': i})
                
                # Dangerous function calls
                for func in self.DANGEROUS_FUNCTIONS:
                    if re.search(r'\b' + re.escape(func.split('.')[0]) + r'\b', line):
                        if func in line or any(x in line for x in func.split('.')):
                            result['dangerous_calls'].append({
                                'function': func,
                                'line': i,
                                'code': line.strip()[:200]
                            })
            
            # Extract strings
            result['strings'] = re.findall(r'["\']([^"\']{4,})["\']', content)
            
            # Hashes
            with open(filepath, 'rb') as f:
                data = f.read()
            result['hashes'] = {
                'md5': hashlib.md5(data).hexdigest(),
                'sha256': hashlib.sha256(data).hexdigest(),
            }
            
            # Verdict
            risk_score = len(result['risks']) * 10 + len(result['dangerous_calls']) * 5
            if risk_score >= 50:
                threat = 'SUSPICIOUS'
            elif risk_score >= 20:
                threat = 'MODERATE'
            else:
                threat = 'CLEAN'
            
            result['verdict'] = {
                'threat_level': threat,
                'risk_score': risk_score,
                'findings': result['risks'] + [f"Line {c['line']}: {c['function']}" for c in result['dangerous_calls']],
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result


class PowerShellAnalyzer(BaseAnalyzer):
    """Analyze PowerShell scripts"""
    
    extensions = ['.ps1', '.psm1', '.psd1']
    description = 'PowerShell script analyzer'
    
    DANGEROUS_CMDLETS = [
        'Invoke-Expression', 'IEX', 'Invoke-Item', 'Invoke-RestMethod',
        'Invoke-WebRequest', 'iwr', 'wget', 'curl',
        'Start-Process', 'Start-Service', 'Stop-Service',
        'Get-Process', 'Stop-Process', 'Kill',
        'New-Object', 'Assembly', 'Type',
        'Add-Type', 'Reflection',
        'SecretManagement', 'Get-Credential',
        'ConvertTo-SecureString', 'ConvertFrom-SecureString',
        ' Encrypt', 'Decrypt', 'Cipher',
        'DownloadString', 'DownloadFile', 'WebClient',
        'Hide-PSScript', 'Unblock-File',
        'Out-Null', 'Null',
        'Net.WebClient', 'Net.Download',
        'ScriptBlock', 'EncodedCommand',
        ' -enc', '-encodedcommand',
    ]
    
    def analyze(self, filepath: str) -> Dict:
        result = {
            'file': filepath,
            'type': 'PowerShell',
            'analyzed_at': datetime.now().isoformat(),
            'lines': 0,
            'size_bytes': 0,
            'cmdlets': [],
            'functions': [],
            'encoded_commands': [],
            'risks': [],
            'hashes': {},
            'verdict': {},
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.split('\n')
            
            result['size_bytes'] = len(content.encode('utf-8'))
            result['lines'] = len(lines)
            
            for i, line in enumerate(lines, 1):
                # Check for encoded commands
                if '-enc' in line.lower() or '-encodedcommand' in line.lower():
                    result['encoded_commands'].append({'line': i, 'code': line.strip()[:200]})
                    result['risks'].append(f"Line {i}: Encoded command detected (potential obfuscation)")
                
                # Check for dangerous cmdlets
                for cmd in self.DANGEROUS_CMDLETS:
                    if cmd.lower() in line.lower():
                        result['cmdlets'].append({
                            'cmdlet': cmd,
                            'line': i,
                            'context': line.strip()[:200]
                        })
                        result['risks'].append(f"Line {i}: Dangerous cmdlet '{cmd}'")
                
                # Function definitions
                if re.match(r'^\s*function\s+\w+', line):
                    m = re.search(r'function\s+(\w+)', line)
                    if m:
                        result['functions'].append({'name': m.group(1), 'line': i})
            
            # Hashes
            with open(filepath, 'rb') as f:
                data = f.read()
            result['hashes'] = {
                'md5': hashlib.md5(data).hexdigest(),
                'sha256': hashlib.sha256(data).hexdigest(),
            }
            
            # Verdict
            risk_score = len(result['risks']) * 12
            if risk_score >= 60:
                threat = 'MALICIOUS'
            elif risk_score >= 30:
                threat = 'SUSPICIOUS'
            elif risk_score >= 10:
                threat = 'MODERATE'
            else:
                threat = 'CLEAN'
            
            result['verdict'] = {
                'threat_level': threat,
                'risk_score': risk_score,
                'findings': result['risks'],
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result


# =========================================================================
# Binary / Raw Analyzer
# =========================================================================

class BinaryAnalyzer(BaseAnalyzer):
    """Analyze raw binary files"""
    
    extensions = ['.bin', '.raw', '.dat', '.mem', '.dmp']
    description = 'Raw binary file analyzer'
    
    def analyze(self, filepath: str) -> Dict:
        result = {
            'file': filepath,
            'type': 'Binary',
            'analyzed_at': datetime.now().isoformat(),
            'size_bytes': 0,
            'magic': '',
            'entropy': 0.0,
            'strings': [],
            'interesting_strings': [],
            'hex_dump': '',
            'hashes': {},
            'risks': [],
            'verdict': {},
        }
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            result['size_bytes'] = len(data)
            
            # Magic bytes
            result['magic'] = self._identify_magic(data)
            
            # Entropy
            result['entropy'] = self._calc_entropy(data)
            
            # Strings
            result['strings'] = self._extract_strings(data)
            result['interesting_strings'] = self._filter_binary_strings(result['strings'])
            
            # Hex dump (first 512 bytes)
            result['hex_dump'] = self._hex_dump(data[:512])
            
            # Hashes
            result['hashes'] = {
                'md5': hashlib.md5(data).hexdigest(),
                'sha1': hashlib.sha1(data).hexdigest(),
                'sha256': hashlib.sha256(data).hexdigest(),
            }
            
            # Risks
            if result['entropy'] > 7.5:
                result['risks'].append(f"Very high entropy ({result['entropy']:.2f}) — possible encryption/packing")
            if any('http' in s.lower() for s in result['interesting_strings']):
                result['risks'].append("Network-related strings found")
            if any(s.startswith('\\x') or len(s) > 100 for s in result['strings'][:100]):
                result['risks'].append("Possibly encoded/obfuscated content")
            
            # Verdict
            risk_score = len(result['risks']) * 20
            if risk_score >= 50:
                threat = 'SUSPICIOUS'
            elif risk_score >= 20:
                threat = 'MODERATE'
            else:
                threat = 'UNKNOWN'
            
            result['verdict'] = {
                'threat_level': threat,
                'risk_score': risk_score,
                'entropy': result['entropy'],
                'findings': result['risks'],
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _identify_magic(self, data: bytes) -> str:
        if data[:2] == b'MZ':
            return 'PE (MZ header)'
        if data[:4] == b'\x7fELF':
            return 'ELF'
        if data[:2] == b'\xca\xfe':
            return 'Mach-O (fat binary)'
        if data[:4] == b'\x89PNG':
            return 'PNG image'
        if data[:3] == b'\xff\xd8\xff':
            return 'JPEG image'
        if data[:8] == b'PK\x03\x04':
            return 'ZIP archive'
        if data[:2] == b'\xb5\x0f':
            return 'SQLite database'
        return f'Unknown ({data[:8].hex()})'
    
    def _calc_entropy(self, data: bytes) -> float:
        if not data:
            return 0.0
        counter = Counter(data)
        length = len(data)
        import math
        entropy = 0.0
        for count in counter.values():
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)
        return round(entropy, 4)
    
    def _extract_strings(self, data: bytes, min_length: int = 6) -> List[str]:
        strings = []
        current = bytearray()
        for byte in data:
            if 32 <= byte <= 126:
                current.append(byte)
            else:
                if len(current) >= min_length:
                    strings.append(current.decode('ascii', errors='replace'))
                current = bytearray()
        if len(current) >= min_length:
            strings.append(current.decode('ascii', errors='replace'))
        return strings
    
    def _filter_binary_strings(self, strings: List[str]) -> List[Dict]:
        patterns = {
            'URL': r'https?://[^\s\<\">]+',
            'IP': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            'FilePath': r'[A-Za-z]:\\(?:[\w.]+\\)*[\w.]+',
            'Registry': r'HKEY_[A-Z_]+\\[^\s]+',
            'Email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'MD5': r'[a-fA-F0-9]{32}',
            'Base64': r'[A-Za-z0-9+/]{20,}={0,2}',
        }
        found = []
        for s in strings:
            for name, pattern in patterns.items():
                try:
                    if re.search(pattern, s):
                        found.append({'type': name, 'value': s[:200]})
                        break
                except:
                    pass
        return found
    
    def _hex_dump(self, data: bytes, width: int = 16) -> str:
        lines = []
        for i in range(0, len(data), width):
            chunk = data[i:i+width]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            lines.append(f'{i:08x}: {hex_part:<{width*3}}  |{ascii_part}|')
        return '\n'.join(lines)


# =========================================================================
# Disassembler (Capstone)
# =========================================================================

class Disassembler:
    """x86/x64 disassembly using Capstone"""
    
    def __init__(self):
        self.md = None
        self._initialized = False
    
    def _ensure_init(self):
        if not self._initialized and HAS_CAPSTONE:
            try:
                self.md = Cs(CS_ARCH_X86, CS_MODE_64)
                self.md.detail = True
                self._initialized = True
            except:
                try:
                    self.md = Cs(CS_ARCH_X86, CS_MODE_32)
                    self.md.detail = True
                    self._initialized = True
                except:
                    pass
    
    def disassemble(self, data: bytes, offset: int = 0, count: int = 50) -> List[Dict]:
        """Disassemble raw bytes"""
        self._ensure_init()
        if not self.md:
            return []
        
        instructions = []
        try:
            for insn in self.md.disasm(data, offset):
                instructions.append({
                    'address': insn.address,
                    'offset': insn.address - offset,
                    'asm': f'{insn.mnemonic} {insn.op_str}',
                    'bytes': insn.bytes.hex(),
                    'size': insn.size,
                })
                if len(instructions) >= count:
                    break
        except Exception as e:
            logger.debug(f"Disassembly error: {e}")
        
        return instructions
    
    def disassemble_section(self, pe_data: bytes, section_offset: int, 
                            section_size: int, count: int = 100) -> List[Dict]:
        """Disassemble a specific section"""
        start = max(0, section_offset)
        end = min(len(pe_data), section_offset + section_size)
        section_data = pe_data[start:end]
        return self.disassemble(section_data, 0, count)
    
    def find_calls(self, data: bytes, offset: int = 0, count: int = 100) -> List[Dict]:
        """Find CALL instructions"""
        self._ensure_init()
        if not self.md:
            return []
        
        calls = []
        try:
            for insn in self.md.disasm(data, offset):
                if insn.mnemonic == 'call':
                    calls.append({
                        'address': insn.address,
                        'target': insn.op_str,
                        'bytes': insn.bytes.hex(),
                    })
                    if len(calls) >= count:
                        break
        except:
            pass
        return calls
    
    def find_jumps(self, data: bytes, offset: int = 0) -> List[Dict]:
        """Find JMP/JCC instructions"""
        self._ensure_init()
        if not self.md:
            return []
        
        jumps = []
        try:
            for insn in self.md.disasm(data, offset):
                if insn.mnemonic.startswith('j') or insn.mnemonic == 'jmp':
                    jumps.append({
                        'address': insn.address,
                        'type': insn.mnemonic,
                        'target': insn.op_str,
                    })
        except:
            pass
        return jumps
    
    def is_initialized(self) -> bool:
        self._ensure_init()
        return self.md is not None


# =========================================================================
# Main Engine
# =========================================================================

class ReEngineeringEngine:
    """Main reverse engineering engine — dispatches to correct analyzer"""
    
    def __init__(self):
        self.analyzers = []
        self._register_analyzers()
        self.disassembler = Disassembler()
    
    def _register_analyzers(self):
        self.analyzers = [
            PEAnalyzer(),
            JavaScriptAnalyzer(),
            BatchAnalyzer(),
            PythonAnalyzer(),
            PowerShellAnalyzer(),
            BinaryAnalyzer(),
        ]
    
    def analyze(self, filepath: str) -> Dict:
        """Analyze a file — auto-detects type"""
        filepath = str(filepath)
        ext = Path(filepath).suffix.lower()
        
        # Find matching analyzer
        analyzer = None
        for a in self.analyzers:
            if ext in a.extensions:
                analyzer = a
                break
        
        # Fallback: try all analyzers
        if not analyzer:
            # Try PE first (most common)
            try:
                with open(filepath, 'rb') as f:
                    magic = f.read(2)
                if magic == b'MZ':
                    analyzer = PEAnalyzer()
            except:
                pass
            
            # Fallback to binary
            if not analyzer:
                analyzer = BinaryAnalyzer()
        
        logger.info(f"Analyzing {filepath} with {analyzer.__class__.__name__}")
        return analyzer.analyze(filepath)
    
    def batch_analyze(self, filepaths: List[str]) -> Dict:
        """Analyze multiple files"""
        results = []
        for fp in filepaths:
            try:
                result = self.analyze(fp)
                results.append(result)
            except Exception as e:
                results.append({'file': fp, 'error': str(e)})
        
        return {
            'total': len(results),
            'successful': len([r for r in results if 'error' not in r]),
            'failed': len([r for r in results if 'error' in r]),
            'results': results,
        }
    
    def quick_strings(self, filepath: str, min_length: int = 4) -> List[str]:
        """Quick string extraction from any file"""
        with open(filepath, 'rb') as f:
            data = f.read()
        
        strings = []
        current = bytearray()
        for byte in data:
            if 32 <= byte <= 126:
                current.append(byte)
            else:
                if len(current) >= min_length:
                    strings.append(current.decode('ascii', errors='replace'))
                current = bytearray()
        if len(current) >= min_length:
            strings.append(current.decode('ascii', errors='replace'))
        
        return strings
    
    def quick_hash(self, filepath: str) -> Dict:
        """Quick hash calculation"""
        with open(filepath, 'rb') as f:
            data = f.read()
        return {
            'file': filepath,
            'size_bytes': len(data),
            'md5': hashlib.md5(data).hexdigest(),
            'sha1': hashlib.sha1(data).hexdigest(),
            'sha256': hashlib.sha256(data).hexdigest(),
        }
    
    def get_supported_formats(self) -> List[Dict]:
        """List all supported file formats"""
        formats = []
        for a in self.analyzers:
            formats.append({
                'analyzer': a.__class__.__name__,
                'description': a.description,
                'extensions': a.extensions,
            })
        if HAS_CAPSTONE and self.disassembler.is_initialized():
            formats.append({
                'analyzer': 'Disassembler',
                'description': 'x86/x64 assembly disassembly (Capstone)',
                'extensions': ['.exe', '.dll', '.bin', '.sys'],
            })
        return formats
    
    def disassemble(self, filepath: str, offset: int = 0, count: int = 50) -> Dict:
        """Disassemble code at offset"""
        result = {
            'file': filepath,
            'offset': offset,
            'count': count,
            'instructions': [],
            'calls': [],
            'jumps': [],
            'error': None,
        }
        
        if not HAS_CAPSTONE or not self.disassembler.is_initialized():
            result['error'] = 'Capstone not available or x64 mode failed, trying x86'
            # Try 32-bit
            try:
                from capstone import Cs, CS_ARCH_X86, CS_MODE_32
                self.disassembler.md = Cs(CS_ARCH_X86, CS_MODE_32)
                self.disassembler.md.detail = True
            except:
                result['error'] = 'Capstone not installed. Run: pip install capstone'
                return result
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Disassemble
            result['instructions'] = self.disassembler.disassemble(data, offset, count)
            result['calls'] = self.disassembler.find_calls(data, offset, 20)
            result['jumps'] = self.disassembler.find_jumps(data, offset)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result


# =========================================================================
# CLI Entry
# =========================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Re-Engineering Engine v1 — Multi-format binary/script analysis'
    )
    parser.add_argument('file', nargs='?', help='File to analyze')
    parser.add_argument('--dir', '-d', help='Directory to scan recursively')
    parser.add_argument('--format', '-f', choices=['json', 'text', 'table'], default='text')
    parser.add_argument('--strings-only', '-s', action='store_true', help='Only extract strings')
    parser.add_argument('--hash-only', '-H', action='store_true', help='Only compute hashes')
    parser.add_argument('--depth', '-D', type=int, default=1, help='Recursion depth')
    parser.add_argument('--min-string-length', type=int, default=4, help='Min string length')
    parser.add_argument('--list-formats', action='store_true', help='List supported formats')
    
    args = parser.parse_args()
    
    engine = ReEngineeringEngine()
    
    if args.list_formats:
        print("\nSupported Formats:")
        print("=" * 60)
        for fmt in engine.get_supported_formats():
            print(f"\n{fmt['analyzer']}")
            print(f"  {fmt['description']}")
            print(f"  Extensions: {', '.join(fmt['extensions'])}")
        print()
        sys.exit(0)
    
    if args.strings_only and args.file:
        strings = engine.quick_strings(args.file, args.min_string_length)
        if args.format == 'json':
            print(json.dumps(strings, indent=2))
        else:
            print(f"\nStrings from {args.file} ({len(strings)} found):\n")
            for i, s in enumerate(strings[:200], 1):
                print(f"  {i:4d}. {s[:120]}")
            if len(strings) > 200:
                print(f"  ... ({len(strings) - 200} more)")
        sys.exit(0)
    
    if args.hash_only and args.file:
        h = engine.quick_hash(args.file)
        print(json.dumps(h, indent=2))
        sys.exit(0)
    
    if args.file:
        result = engine.analyze(args.file)
        
        if args.format == 'json':
            print(json.dumps(result, indent=2, default=str))
        else:
            _print_text_result(result)
        
        sys.exit(0)
    
    if args.dir:
        import glob
        files = []
        for ext in ['**/*'] * (args.depth + 1):
            files.extend(glob.glob(os.path.join(args.dir, ext)))
        
        # Filter to known extensions
        all_exts = [e for a in engine.analyzers for e in a.extensions]
        all_exts.append('')  # Match everything for binary fallback
        
        target_files = [f for f in files if Path(f).suffix.lower() in all_exts or not Path(f).suffix]
        target_files = [f for f in target_files if os.path.isfile(f) and os.path.getsize(f) < 500 * 1024 * 1024]  # < 500MB
        
        print(f"Scanning {len(target_files)} files in {args.dir}...")
        
        results = engine.batch_analyze(target_files)
        
        if args.format == 'json':
            print(json.dumps(results, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print(f"  Scan Results: {results['successful']}/{results['total']} successful")
            print(f"{'='*60}\n")
            
            for r in results['results']:
                if 'error' in r:
                    print(f"  [ERROR] {r['file']}: {r['error']}")
                    continue
                
                verdict = r.get('verdict', {})
                threat = verdict.get('threat_level', 'UNKNOWN')
                icon = {'CLEAN': '[OK]', 'MODERATE': '[!!]', 'SUSPICIOUS': '[XX]', 'DANGEROUS': '[危险]', 'MALICIOUS': '[危险]'}.get(threat, '[??]')
                
                print(f"  {icon} {threat:12s} | {r.get('file', 'unknown')}")
                if verdict.get('risk_score', 0) > 0:
                    print(f"         Score: {verdict['risk_score']} | Findings: {len(verdict.get('findings', []))}")
        
        sys.exit(0)
    
    # No args — show help
    print("""
Re-Engineering Engine v1 — Multi-format binary/script analysis
Uso:
  python re_engine.py <arquivo>              # Analisar arquivo
  python re_engine.py <arquivo> --format json  # Output JSON
  python re_engine.py <arquivo> --strings-only  # Somente strings
  python re_engine.py <arquivo> --hash-only    # Somente hashes
  python re_engine.py --dir /caminho           # Scan directory
  python re_engine.py --list-formats           # Formatos suportados
""")


def _print_text_result(result: Dict):
    """Print analysis result in human-readable format"""
    print(f"\n{'='*60}")
    print(f"  Analysis: {result.get('file', 'unknown')}")
    print(f"{'='*60}")
    
    if 'error' in result:
        print(f"  [ERROR] {result['error']}")
        return
    
    rtype = result.get('type', 'Unknown')
    print(f"  Type:     {rtype}")
    print(f"  Analyzed: {result.get('analyzed_at', 'N/A')}")
    
    # Hashes
    hashes = result.get('hashes', {})
    if hashes:
        print(f"\n  Hashes:")
        for htype, hval in hashes.items():
            print(f"    {htype:8s}: {hval}")
    
    # PE-specific
    if rtype == 'PE':
        pe = result.get('pe_info', {})
        if pe:
            print(f"\n  PE Info:")
            print(f"    Format:       {pe.get('format', 'N/A')}")
            print(f"    Machine:      {pe.get('machine', 'N/A')}")
            print(f"    Entry Point:  {pe.get('entry_point', 'N/A')}")
            print(f"    Sections:     {pe.get('num_sections', 0)}")
            print(f"    Timestamp:    {pe.get('timestamp', 'N/A')}")
            print(f"    Subsystem:    {pe.get('subsystem', 'N/A')}")
            print(f"    DLL:          {'Yes' if pe.get('is_dll') else 'No'}")
        
        # Sections
        sections = result.get('sections', [])
        if sections:
            print(f"\n  Sections ({len(sections)}):")
            for s in sections[:10]:
                susp = " [!]" if s.get('suspicious') else ""
                print(f"    {s['name']:8s} | vsize={s['virtual_size']:>10} | entropy={s['entropy']:.2f}{susp}")
        
        # Imports
        imports = result.get('imports', [])
        if imports:
            print(f"\n  Imports ({len(imports)} libraries):")
            for imp in imports[:15]:
                funcs = [f['name'] for f in imp.get('functions', [])[:5]]
                print(f"    {imp['library']:30s} -> {', '.join(funcs)}{'...' if len(imp.get('functions',[]))>5 else ''}")
        
        # Exports
        exports = result.get('exports', [])
        if exports:
            print(f"\n  Exports ({len(exports)}):")
            for exp in exports[:15]:
                print(f"    {exp['name']:30s} @ {exp.get('address', 'N/A')}")
    
    # Strings
    strings = result.get('interesting_strings', [])
    if strings:
        print(f"\n  Interesting Strings ({len(strings)}):")
        for s in strings[:20]:
            print(f"    [{s['type']:12s}] {s['value'][:100]}")
    
    # Script-specific
    if rtype in ('JavaScript', 'Python', 'PowerShell', 'Batch'):
        risks = result.get('risks', [])
        if risks:
            print(f"\n  Risks ({len(risks)}):")
            for r in risks[:15]:
                print(f"    [!] {r}")
        
        if rtype == 'JavaScript':
            funcs = result.get('functions', [])
            if funcs:
                print(f"\n  Functions ({len(funcs)}):")
                for f in funcs[:10]:
                    print(f"    def {f[0] or f[1] or f[2] or f[3]}")
    
    # Verdict
    verdict = result.get('verdict', {})
    if verdict:
        print(f"\n  Verdict:")
        print(f"    Threat Level: {verdict.get('threat_level', 'N/A')}")
        print(f"    Risk Score:   {verdict.get('risk_score', 0)}")
        findings = verdict.get('findings', [])
        if findings:
            print(f"    Findings: {len(findings)}")
            for f in findings[:5]:
                print(f"      • {f}")
    
    print()


if __name__ == '__main__':
    main()
