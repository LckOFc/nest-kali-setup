"""Test the PE analyzer"""
import sys, traceback
sys.path.insert(0, 'C:/Users/devel/tools/re-engineering')
from re_engine import PEAnalyzer
import pefile

pe = pefile.PE('C:/Windows/System32/notepad.exe')
analyzer = PEAnalyzer()
result = {
    'file': 'test.exe', 'type': 'PE',
    'analyzed_at': 'now',
    'pe_info': {}, 'sections': [], 'imports': [], 'exports': [],
    'strings': [], 'interesting_strings': [], 'hashes': {}, 'risks': [],
}

try:
    # PE info
    machine_val = getattr(pe.FILE_HEADER, 'Machine', 0)
    result['pe_info'] = {
        'machine': pefile.MACHINE_TYPE.get(machine_val, hex(machine_val)),
        'num_sections': pe.FILE_HEADER.NumberOfSections,
        'timestamp': 'test',
        'characteristics': analyzer._parse_characteristics(getattr(pe.FILE_HEADER, 'Characteristics', 0)),
        'entry_point': hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
        'image_base': hex(pe.OPTIONAL_HEADER.ImageBase),
        'image_size': pe.OPTIONAL_HEADER.SizeOfImage,
        'headers_size': pe.OPTIONAL_HEADER.SizeOfHeaders,
        'checksum': 'test',
        'subsystem': pefile.SUBSYSTEM_TYPE.get(pe.OPTIONAL_HEADER.Subsystem, hex(pe.OPTIONAL_HEADER.Subsystem)),
        'dll_characteristics': analyzer._parse_dll_characteristics(getattr(pe.OPTIONAL_HEADER, 'DllCharacteristics', 0)),
        'major_os_version': pe.OPTIONAL_HEADER.MajorOperatingSystemVersion,
        'minor_os_version': pe.OPTIONAL_HEADER.MinorOperatingSystemVersion,
        'major_image_version': pe.OPTIONAL_HEADER.MajorImageVersion,
        'minor_image_version': pe.OPTIONAL_HEADER.MinorImageVersion,
        'major_linker_version': pe.OPTIONAL_HEADER.MajorLinkerVersion,
        'minor_linker_version': pe.OPTIONAL_HEADER.MinorLinkerVersion,
    }
    is_dll = bool(getattr(pe.OPTIONAL_HEADER, 'DllCharacteristics', 0) & 0x2000)
    result['pe_info']['is_dll'] = is_dll
    result['pe_info']['format'] = 'DLL' if is_dll else 'EXE'
    print('PE info OK')

    # Sections
    for section in pe.sections:
        section_data = {
            'name': section.Name.decode('utf-8', errors='replace').strip('\x00'),
            'virtual_size': section.Misc_VirtualSize,
            'virtual_address': hex(section.VirtualAddress),
            'raw_size': section.SizeOfRawData,
            'raw_offset': section.PointerToRawData,
            'entropy': analyzer._calc_entropy(section.get_data()),
            'characteristics': analyzer._parse_section_chars(section.Characteristics),
        }
        if section_data['entropy'] > 7.0:
            section_data['suspicious'] = True
            section_data['reason'] = 'High entropy'
            result['risks'].append(f"Section {section_data['name']} has high entropy")
        result['sections'].append(section_data)
    print(f'Sections OK: {len(result["sections"])}')

    # Imports
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            imports = []
            for imp in entry.imports:
                imp_name = ''
                if hasattr(imp, 'name') and imp.name:
                    try:
                        imp_name = imp.name.decode('utf-8', errors='replace') if isinstance(imp.name, bytes) else str(imp.name)
                    except:
                        imp_name = str(imp.name)
                elif hasattr(imp, 'ordinal') and imp.ordinal:
                    imp_name = f'#{imp.ordinal}'
                else:
                    imp_name = '?'
                imports.append({'name': imp_name, 'address': '0x0'})
            dll_name = ''
            if hasattr(entry, 'dll'):
                try:
                    dll_name = entry.dll.decode('utf-8', errors='replace') if isinstance(entry.dll, bytes) else str(entry.dll)
                except:
                    dll_name = str(entry.dll)
            if imports and dll_name:
                result['imports'].append({'library': dll_name, 'functions': imports})
    print(f'Imports OK: {len(result["imports"])}')

    # Strings
    data = pe.get_memory_mapped_image()
    result['strings'] = analyzer._extract_strings(data)
    result['interesting_strings'] = analyzer._filter_interesting(result['strings'])
    print(f'Strings OK: {len(result["strings"])} total, {len(result["interesting_strings"])} interesting')

    # Hashes
    import hashlib
    with open('C:/Windows/System32/notepad.exe', 'rb') as f:
        file_data = f.read()
    result['hashes'] = {
        'md5': hashlib.md5(file_data).hexdigest(),
        'sha1': hashlib.sha1(file_data).hexdigest(),
        'sha256': hashlib.sha256(file_data).hexdigest(),
    }
    print('Hashes OK')

    # Verdict
    result['verdict'] = analyzer._compute_verdict(result)
    print(f'Verdict OK: {result["verdict"]["threat_level"]}')

    # JSON serialize
    import json
    json.dumps(result, default=str)
    print('JSON serialize OK')

    print('\nALL GOOD!')

except Exception as e:
    traceback.print_exc()
finally:
    pe.close()
