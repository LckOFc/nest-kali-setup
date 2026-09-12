"""Debug the PE analyzer error"""
import sys, traceback
sys.path.insert(0, 'C:/Users/devel/tools/re-engineering')
import re_engine
import pefile

pe = pefile.PE('C:/Windows/System32/notepad.exe')
analyzer = re_engine.PEAnalyzer()

result = {
    'file': 'test.exe', 'type': 'PE',
    'analyzed_at': 'now',
    'pe_info': {}, 'sections': [], 'imports': [], 'exports': [],
    'strings': [], 'interesting_strings': [], 'hashes': {}, 'risks': [],
}

try:
    print('=== Step 1: PE Info ===')
    machine_val = getattr(pe.FILE_HEADER, 'Machine', 0)
    result['pe_info']['machine'] = pefile.MACHINE_TYPE.get(machine_val, hex(machine_val))
    result['pe_info']['num_sections'] = pe.FILE_HEADER.NumberOfSections
    result['pe_info']['entry_point'] = hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)
    result['pe_info']['image_base'] = hex(pe.OPTIONAL_HEADER.ImageBase)
    result['pe_info']['image_size'] = pe.OPTIONAL_HEADER.SizeOfImage
    result['pe_info']['subsystem'] = pefile.SUBSYSTEM_TYPE.get(pe.OPTIONAL_HEADER.Subsystem, hex(pe.OPTIONAL_HEADER.Subsystem))
    result['pe_info']['is_dll'] = bool(getattr(pe.OPTIONAL_HEADER, 'DllCharacteristics', 0) & 0x2000)
    fmt = 'DLL' if result['pe_info']['is_dll'] else 'EXE'
    result['pe_info']['format'] = fmt
    print(f"  OK - format={fmt}, machine={result['pe_info']['machine']}")

    print('=== Step 2: Sections ===')
    for section in pe.sections:
        sec = {
            'name': section.Name.decode('utf-8', errors='replace').strip('\x00'),
            'virtual_size': section.Misc_VirtualSize,
            'virtual_address': hex(section.VirtualAddress),
            'raw_size': section.SizeOfRawData,
            'raw_offset': section.PointerToRawData,
            'entropy': analyzer._calc_entropy(section.get_data()),
            'characteristics': analyzer._parse_section_chars(section.Characteristics),
        }
        if sec['entropy'] > 7.0:
            sec['suspicious'] = True
            sec['reason'] = 'High entropy'
            result['risks'].append(f"Section {sec['name']} high entropy")
        result['sections'].append(sec)
    print(f"  OK - {len(result['sections'])} sections")

    print('=== Step 3: Imports ===')
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            imps = []
            for imp in entry.imports:
                name = ''
                if hasattr(imp, 'name') and imp.name:
                    try:
                        name = imp.name.decode('utf-8', errors='replace') if isinstance(imp.name, bytes) else str(imp.name)
                    except:
                        name = str(imp.name)
                elif hasattr(imp, 'ordinal') and imp.ordinal:
                    name = f'#{imp.ordinal}'
                else:
                    name = '?'
                imps.append({'name': name})
            dll = ''
            if hasattr(entry, 'dll'):
                try:
                    dll = entry.dll.decode('utf-8', errors='replace') if isinstance(entry.dll, bytes) else str(entry.dll)
                except:
                    dll = str(entry.dll)
            if imps and dll:
                result['imports'].append({'library': dll, 'functions': imps})
    print(f"  OK - {len(result['imports'])} libraries")

    print('=== Step 4: Suspicious imports ===')
    susp_list = ['WinExec', 'ShellExecute', 'CreateProcess', 'WriteProcessMemory',
                 'VirtualAllocEx', 'CreateRemoteThread', 'URLDownloadToFile']
    imported_funcs = []
    for imp_entry in result['imports']:
        for func in imp_entry['functions']:
            imported_funcs.append(func['name'])
    for s in susp_list:
        if any(s.lower() in f.lower() for f in imported_funcs):
            result['risks'].append(f"Suspicious import: {s}")
    print(f"  OK - {len(result['risks'])} risks so far")

    print('=== Step 5: Strings ===')
    data = pe.get_memory_mapped_image()
    result['strings'] = analyzer._extract_strings(data)
    result['interesting_strings'] = analyzer._filter_interesting(result['strings'])
    print(f"  OK - {len(result['strings'])} strings, {len(result['interesting_strings'])} interesting")

    print('=== Step 6: Hashes ===')
    import hashlib
    with open('C:/Windows/System32/notepad.exe', 'rb') as f:
        file_data = f.read()
    result['hashes'] = {
        'md5': hashlib.md5(file_data).hexdigest(),
        'sha1': hashlib.sha1(file_data).hexdigest(),
        'sha256': hashlib.sha256(file_data).hexdigest(),
    }
    print("  OK")

    print('=== Step 7: Verdict ===')
    result['verdict'] = analyzer._compute_verdict(result)
    print(f"  OK - threat={result['verdict']['threat_level']}")

    print('=== Step 8: JSON serialize ===')
    import json
    json.dumps(result, default=str)
    print("  OK")

    print("\n=== ALL STEPS PASSED ===")

except Exception as e:
    print(f"\n=== ERROR at step above ===")
    traceback.print_exc()
finally:
    pe.close()
