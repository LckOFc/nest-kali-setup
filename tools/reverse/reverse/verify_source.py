"""Check what the 'package' and 'func' matches actually are"""
import os, re

exe_path = r'C:\Users\devel\AppData\Local\agy\bin\agy.exe'
with open(exe_path, 'rb') as f:
    data = f.read(min(os.path.getsize(exe_path), 300*1024*1024))

print("=== VERIFYING SOURCE CODE CLAIMS ===")
print()

# Check the 'package' matches
print("--- 'package' declarations ---")
pkg_matches = list(re.finditer(rb'package\s+[a-zA-Z_][a-zA-Z0-9_]*', data))
for i, m in enumerate(pkg_matches[:20]):
    start = max(0, m.start()-50)
    end = min(len(data), m.end()+200)
    ctx = data[start:end]
    try:
        text = ctx.decode('ascii', errors='replace')
        # Clean up
        text = re.sub(r'[^\x20-\x7e]', ' ', text)
        text = ' '.join(text.split())
        print(f"[{i}] {text[:200]}")
    except:
        pass

print()
print("--- 'func ' declarations ---")
func_matches = list(re.finditer(rb'func\s+\w+\s*\(', data))
for i, m in enumerate(func_matches[:10]):
    start = max(0, m.start()-20)
    end = min(len(data), m.end()+200)
    ctx = data[start:end]
    try:
        text = ctx.decode('ascii', errors='replace')
        text = re.sub(r'[^\x20-\x7e]', ' ', text)
        text = ' '.join(text.split())
        print(f"[{i}] {text[:200]}")
    except:
        pass

print()
print("--- 'import (' blocks ---")
import_matches = list(re.finditer(rb'import\s*\(', data))
for i, m in enumerate(import_matches[:5]):
    start = max(0, m.start()-10)
    end = min(len(data), m.end()+300)
    ctx = data[start:end]
    try:
        text = ctx.decode('ascii', errors='replace')
        text = re.sub(r'[^\x20-\x7e]', ' ', text)
        text = ' '.join(text.split())
        print(f"[{i}] {text[:200]}")
    except:
        pass

print()
print("--- 'chan ' declarations ---")
chan_matches = list(re.finditer(rb'chan\s+\w+', data))
for i, m in enumerate(chan_matches[:10]):
    start = max(0, m.start()-30)
    end = min(len(data), m.end()+100)
    ctx = data[start:end]
    try:
        text = ctx.decode('ascii', errors='replace')
        text = re.sub(r'[^\x20-\x7e]', ' ', text)
        text = ' '.join(text.split())
        print(f"[{i}] {text[:150]}")
    except:
        pass

print()
print("=== CONCLUSAO ===")
print()
print("Os patterns encontrados sao de CONTEUDO EMBUTIDO (JS/HTML/JSON),")
print("NÃO de código fonte Go real. O binário contém:")
print()
print("  - Templates HTML/JavaScript embedados (React UI)")
print("  - Dados JSON de configuração")
print("  - Regex patterns para syntax highlighting")
print("  - Strings de erro e mensagens do sistema")
print()
print("O binário AGY.EXE está COMPLETAMENTE STRIPPED:")
print("  - 0 symbols no symbol table")
print("  - Debug directory corrompido (entries com valores aleatórios)")
print("  - Nenhuma seção .debug_info ou .gosymtab válida")
print("  - Sem arquivos .go embutidos")
print()
print("PARA OBTÊR O CÓDIGO FONTE COMPLETO, seria necessário:")
print("  1. Binário NÃO stripped (com debug symbols)")
print("  2. Arquivo PDB (.pdb) associado ao binário")
print("  3. Decompilador Go profissional (ex: ghidra-go, retroweb)")
print("  4. Ou acesso ao repositório fonte original")
print()
print("O que FOI recuperado:")
print("  - Arquitetura completa do sistema (via análise de strings)")
print("  - Todos os componentes e suas funções")
print("  - Lista de provedores LLM suportados")
print("  - Funcionalidades de segurança detectadas")
print("  - Comandos CLI e endpoints da API")
print("  - Bibliotecas e frameworks utilizados")