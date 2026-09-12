# 🛠️ Toolkit Completo de Engenharia Reversa — Lista de Ferramentas
# =================================================================
# Para análise profissional de binários Go (e outros)
# Data: 2026-09-09 | Autor: Sombra
# =================================================================

## 1. DESCOMPILADORES / ANALISADORES ESTATICOS
# =================================================================

TOOLS_STATIC = {
    "Ghidra": {
        "tipo": "Descompilador + Analisador Estatico",
        "custo": "GRATUITO",
        "desenvolvedor": "NSA (agora publico)",
        "url": "https://ghidra-sre.org/",
        "para_queServe": """
  - Descompilacao C/C++/Go/Java/etc com pseudocodigo de alta qualidade
  - Analise de fluxo de controle (CFG automatico)
  - Recovery de tipos e variaveis
  - Scripting em Python e Java
  - Suporte a multiplas arquiteturas (x86, x64, ARM, MIPS, etc)
  - Plugin go2ghidra para reconhecimento especifico de Go
        """,
        "installacao": """
  1. Download: https://github.com/NationalSecurityAgency/ghidra/releases
  2. Extrair: Expand-Archive ghidra_*.zip C:\\Tools\\
  3. Executar: C:\\Tools\\ghidra_*.\\support\\analyzeHeadless.bat
  4. Plugin Go: git clone https://github.com/numenum/ghidra-go
        """,
        "nivelImportancia": "NECESSARIO",
        "alternativa": "None (melhor opcao gratuita)"
    },
    
    "Binary Ninja": {
        "tipo": "Descompilador + Analisador Estatico",
        "custo": "COMERCIAL ($399) | Academic/Free Trial 30 dias",
        "desenvolvedor": "Open Cybersecurity Foundation",
        "url": "https://binary.ninja/",
        "para_queServe": """
  - Decompilador com Melhor UI do mercado
  - Suporte nativo a Go (identifica structs, interfaces, methods)
  - SSA form (Static Single Assignment) para rastreio de variaveis
  - Python API extensa para automacao
  - CFG interativo com visualizacao grafica
  - Analise de memoria e strings integrada
        """,
        "installacao": """
  1. Download: https://binary.ninja/download
  2. Instalar e ativar licenca (ou trial 30 dias)
  3. Ir em View -> Decompiler para ver pseudocodigo
        """,
        "nivelImportancia": "NECESSARIO",
        "alternativa": "Ghidra (gratis)"
    },
    
    "IDA Pro + Hex-Rays": {
        "tipo": "Disassembly + Decompilador Profissional",
        "custo": "COMERCIAL ($2500+/ano) | Versao Demo gratuita limitada",
        "desenvolvedor": "Hex-Rays / IDA Partners",
        "url": "https://hex-rays.com/ida-pro/",
        "para_queServe": """
  - O descompilador MAIS poderoso do mercado
  - Pseudocodigo de qualidade quase-fonte para Go
  - Plugin ida-go para reconhecimento de simbolos Go
  - Automação completa com Python
  - Suporte a plugins de terceiros (Golang loader, etc)
  - Melhor suporte a debugg engine
        """,
        "installacao": """
  1. Download: https://hex-rays.com/idea/evaluation.cfm
  2. Instalar IDA 7.7+
  3. Instalar plugin Hex-Rays (incluso na versao paga)
  4. Plugin Go: https://github.com/Lisitsyan/ida-go
        """,
        "nivelImportancia": "NECESSARIO (para resultados maximos)",
        "alternativa": "Binary Ninja (mais barato)"
    },
    
    "radare2": {
        "tipo": "Framework de RE CLI",
        "custo": "GRATUITO",
        "desenvolvedor": "radare community",
        "url": "https://radare.org/n/radare2/",
        "para_queServe": """
  - Disassembly e analise via linha de comando
  - Scripting em Python, C, Bash
  - Plugin go2r2 para suporte a Go
  - Analise de memoria e debugging
  - Integracao com outros tools ( Cutter, etc)
  - Ideal para automacao e scripts
        """,
        "installacao": """
  # Windows (via winget/choco se disponivel):
  winget install radare2.radare2
  
  # Ou build from source:
  git clone https://github.com/radareorg/radare2
  sys/install.sh
  
  # Plugin Go:
  r2pm install go2r2
        """,
        "nivelImportancia": "OPCIONAL (bonus)",
        "alternativa": "Ghidra (melhor UI)"
    },
    
    "Cutter": {
        "tipo": "GUI para radare2",
        "custo": "GRATUITO",
        "desenvolvedor": "Cutter team",
        "url": "https://cutter.re/",
        "para_queServe": """
  - Interface grafica amigavel para radare2
  - Decompilador integrado (se Hex-Rays disponivel)
  - Visualizacao de CFG grafica
  - Mais facil que usar radare2 puro
        """,
        "installacao": """
  1. Download: https://github.com/RadareOrg/Cutter/releases
  2. Extrair e executar Cutter.exe
        """,
        "nivelImportancia": "OPCIONAL",
        "alternativa": "Ghidra (mais completo)"
    }
}


## 2. ANALISE DINAMICA / DEBUGGING
# =================================================================

TOOLS_DYNAMIC = {
    "x64dbg": {
        "tipo": "Debugger grafico Windows",
        "custo": "GRATUITO",
        "url": "https://x64dbg.com/",
        "para_queServe": """
  - Debugging de executaveis Windows (x64/x86)
  - Breakpoints condicionais
  - Analise de memoria em tempo real
  - Plugin system extensivel
  - Ideal para analisar comportamento do agy.exe
        """,
        "installacao": "Download e extrair. Executar como Admin.",
        "nivelImportancia": "NECESSARIO",
        "alternativa": "WinDbg (mais complexo)"
    },
    
    "WinDbg / WinDbg Preview": {
        "tipo": "Debugger avanzado Windows",
        "custo": "GRATUITO",
        "url": "https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/",
        "para_queServe": """
  - Debugger mais poderoso para Windows
  - Simbolos Microsoft e PDB
  - Kernel-mode debugging
  - Extensiones KC (Kernel Debugging)
  - Integracao com VS Code
        """,
        "installacao": """
  1. Instalar Windows SDK
  2. Ou instalar WinDbg Preview da Microsoft Store
        """,
        "nivelImportancia": "OPCIONAL",
        "alternativa": "x64dbg (mais simples)"
    },
    
    "Process Hacker / Process Explorer": {
        "tipo": "Monitor de processos",
        "custo": "GRATUITO",
        "url": "https://processhacker.sourceforge.io/",
        "para_queServe": """
  - Visualizar processos, threads, handles
  - Analisar memória de processos
  - Detecção de injection e hooking
  - Uti para entender como agy.exe funciona
        """,
        "installacao": "Download e instalar.",
        "nivelImportancia": "OPCIONAL",
        "alternativa": "Task Manager (basico demais)"
    }
}


## 3. EXTRAÇÃO DE ARQUIVOS / ANÁLISE DE ASSETS
# =================================================================

TOOLS_EXTRACTION = {
    "7-Zip": {
        "tipo": "Compactação/Extração",
        "custo": "GRATUITO",
        "url": "https://www.7-zip.org/",
        "para_queServe": """
  - Extrair ZIPs embedados no binário
  - Abrir formatos raros (7z, tar, gz, etc)
  - O agy.exe tem 305 ZIPs embedados!
        """,
        "installacao": "Download e instalar.",
        "nivelImportancia": "NECESSARIO"
    },
    
    "Resource Hacker": {
        "tipo": "Editor de recursos PE",
        "custo": "GRATUITO",
        "url": "https://www.realeddie.com/",
        "para_queServe": """
  - Extrair recursos embedados (DLLs, dados, etc)
  - Ver strings, dialogs, icons do binário
  - Modificar recursos (reverse engineering)
        """,
        "installacao": "Download e executar.",
        "nivelImportancia": "OPCIONAL"
    },
    
    "PE Explorer / CFF Explorer": {
        "tipo": "Análise avançada de PE",
        "custo": "GRATUITO",
        "url": "https://ntcore.com/",
        "para_queServe": """
  - Visualizar estrutura PE completa
  - Seções, imports, exports, resources
  - Editar headers PE
  - Análise de DLLs embedadas
        """,
        "nivelImportancia": "OPCIONAL"
    }
}


## 4. ANÁLISE DE REDE / TRÁFEGO
# =================================================================

TOOLS_NETWORK = {
    "Wireshark": {
        "tipo": "Analisador de protocolo de rede",
        "custo": "GRATUITO",
        "url": "https://www.wireshark.org/",
        "para_queServe": """
  - Capturar e analizar tráfego de rede
  - Ver comunicações do agy.exe com servidores
  - Decompor protocolos (HTTP, TLS, gRPC, etc)
  - Essencial para entender communication do agente
        """,
        "installacao": "Download e instalar.",
        "nivelImportancia": "NECESSARIO"
    },
    
    "Fiddler Classic / Fiddler Everywhere": {
        "tipo": "HTTP Inspector",
        "custo": "GRATUITO (Classic) / Pago (Everywhere)",
        "url": "https://www.telerik.com/fiddler",
        "para_queServe": """
  - Intercept HTTP/HTTPS traffic
  - Ver requests/responses do agy.exe
  - Decodificar JWT, OAuth tokens
  - Modificar requisições no voo
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "Burp Suite Community": {
        "tipo": "Proxy de teste de vulnerabilidades",
        "custo": "GRATUITO (Community)",
        "url": "https://portswigger.net/burp/communitydownload",
        "para_queServe": """
  - Intercept e modificação de HTTP
  - Scanner de vulnerabilidades (limitado na community)
  - Repeater para testes manuais
  - Extensível com scripts Python
        """,
        "nivelImportancia": "OPCIONAL (mas util)"
    }
}


## 5. ANÁLISE DE MALWARE / COMPORTAMENTAL
# =================================================================

TOOLS_MALWARE = {
    "APIMon / MonitorAPI": {
        "tipo": "Monitor de chamadas de API",
        "custo": "GRATUITO",
        "para_queServe": """
  - Monitorar todas as chamadas de API do Windows
  - Ver o que o agy.exe faz (file ops, registry, network)
  - Detectar comportamento malicioso
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "Process Monitor (ProcMon)": {
        "tipo": "Monitor de sistema Windows",
        "custo": "GRATUITO (Sysinternals)",
        "url": "https://docs.microsoft.com/en-us/sysinternals/downloads/procmon",
        "para_queServe": """
  - Ver todas as operações de arquivo, registro, processo
  - Filtrar por processo (agy.exe)
  - Entender o que o binário acessa
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "Process Explorer": {
        "tipo": "Gerenciador de processos avançado",
        "custo": "GRATUITO (Sysinternals)",
        "url": "https://docs.microsoft.com/en-us/sysinternals/downloads/process-explorer",
        "para_queServe": """
  - Ver DLLs carregadas pelo processo
  - Handles abertos
  - Threads ativas
  - Conexões de rede por processo
        """,
        "nivelImportancia": "NECESSARIO"
    }
}


## 6. FERRAMENTAS DE LINHA DE COMANDO / UTILIDADES
# =================================================================

TOOLS_CLI = {
    "strings (GNU Win32)": {
        "tipo": "Extrator de strings",
        "custo": "GRATUITO",
        "para_queServe": """
  - Extrair strings imprimíveis de binários
  - Analisar padrão de strings
  - Encontrar URLs, paths, senhas
  - Essencial para análise inicial
        """,
        "installacao": "Part of Git for Windows ou GNU Win32"
    },
    
    "CFF Explorer": {
        "tipo": "Analisador PE",
        "custo": "GRATUITO",
        "para_queServe": """
  - Ver estrutura completa PE
  - Análise de seções, imports, exports
  - Identificar packing/obfuscation
        """,
        "nivelImportancia": "OPCIONAL"
    },
    
    "LordPE": {
        "tipo": "Visualizador PE",
        "custo": "GRATUITO",
        "para_queServe": """
  - Ver imports/exports de DLLs
  - Análise rápida de estrutura PE
        """,
        "nivelImportancia": "OPCIONAL"
    }
}


## 7. MÁQUINAS VIRTUAIS / ISOLAMENTO
# =================================================================

TOOLS_VM = {
    "VMware Workstation Player": {
        "tipo": "Virtualização Windows",
        "custo": "GRATUITO (Player) / Pago (Pro)",
        "url": "https://www.vmware.com/products/workstation-player.html",
        "para_queServe": """
  - Executar binários suspeitos em ambiente isolado
  - Snapshots para análise reversa
  - Rede isolada para evitar contaminação
  - Ideal para testar o agy.exe sem risco
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "VirtualBox": {
        "tipo": "Virtualização open-source",
        "custo": "GRATUITO",
        "url": "https://www.virtualbox.org/",
        "para_queServe": """
  - Alternativa gratuita ao VMware
  - Snapshots e isolamento
  - Mais leve que VMware
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "Flare-VM": {
        "tipo": "Distro Windows para RE",
        "custo": "GRATUITO",
        "url": "https://github.com/mandiant/flare-vm",
        "para_queServe": """
  - Windows pré-configurado com FERRAMENTAS DE RE
  - Inclui: Ghidra, x64dbg, Wireshark, Process Monitor, etc
  - Atualizado regularmente pela Mandiant
  - INSTALLAR ISSO É O MAIS RÁPIDO!
        """,
        "installacao": "irm https://mandiant.github.io/flare-vm/setup.ps1 | iex",
        "nivelImportancia": "NECESSARIO (recomendado!)"
    },
    
    " REMnux": {
        "tipo": "Distro Linux para RE",
        "custo": "GRATUITO",
        "url": "https://remnux.org/",
        "para_queServe": """
  - Linux pré-configurado para malware analysis
  - Ferramentas de rede e análise
  - Bom para analizar comunicação
        """,
        "nivelImportancia": "OPCIONAL"
    }
}


## 8. EDITORES / VISUALIZAÇÃO
# =================================================================

TOOLS_EDITORS = {
    "VS Code + Extensões RE": {
        "tipo": "Editor de código",
        "custo": "GRATUITO",
        "extensoes": [
            "Python (para scripts)",
            "Go (para analisar source Go)",
            "JSON Viewer (para relatórios)"
        ],
        "para_queServe": """
  - Editar scripts Python de automação
  - Visualizar JSON de saída
  - Desenvolver extensões
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "WinHex / XWEdit": {
        "tipo": "Hex Editor",
        "custo": "Pago (WinHex) / Gratuito (HxD)",
        "url": "https://mh-nexus.de/en/hxd/",
        "para_queServe": """
  - Editar binários byte-a-byte
  - Buscar padrões hexadecimais
  - Analisar estrutura de dados
  - Recuperar strings de áreas não-mapeadas
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "Notepad++": {
        "tipo": "Editor de texto avançado",
        "custo": "GRATUITO",
        "para_queServe": """
  - Editar arquivos de texto rapidamente
  - Regex search em logs
  - Plugin Hex Editor
        """,
        "nivelImportancia": "OPCIONAL"
    }
}


## 9. AUTOMAÇÃO / SCRIPTING
# =================================================================

TOOLS_AUTO = {
    "Python 3.11+": {
        "tipo": "Linguagem de scripting",
        "custo": "GRATUITO",
        "pacotes_necessarios": [
            "lief (análise PE)",
            "capstone (disassembly)",
            "unicorn (emulação)",
            "keystone (assembly)",
            "pyyaml (config)",
            "rich (output bonito)",
            "click (CLI)",
            "requests (HTTP)",
            "flask (dashboard web)"
        ],
        "para_queServe": """
  - Automatizar análises
  - Criar scripts customizados
  - Processar resultados
  - Integração com outras ferramentas
        """,
        "nivelImportancia": "NECESSARIO"
    },
    
    "PowerShell": {
        "tipo": "Scripting Windows",
        "custo": "GRATUITO",
        "para_queServe": """
  - Automação no Windows
  - Manipulação de arquivos
  - Chamada de APIs Windows
        """,
        "nivelImportancia": "NECESSARIO"
    }
}


## 10. FERRAMENTAS ESPECÍFICAS PARA GO
# =================================================================

TOOLS_GO_SPECIFIC = {
    "go2llvm": {
        "tipo": "Compiler Go -> LLVM IR",
        "custo": "GRATUITO",
        "url": "https://github.com/dunglas/go2llvm",
        "para_queServe": """
  - Converter código Go para LLVM IR
  - Depois usar clang para decomiliar
  - Resultados melhores que disassembly puro
  - Preserva alguns nomes de funções
        """,
        "installacao": "Go install github.com/dunglas/go2llvm@latest",
        "nivelImportancia": "OPCIONAL (avançado)"
    },
    
    "go-decompiler (online)": {
        "tipo": "Descompilador Go online",
        "custo": "GRATUITO",
        "url": "https://go-decompiler.eu/",
        "para_queServe": """
  - Upload do .go file ou binary
  - Tenta reconstroi código fonte
  - Limitado mas útil para trechos
        """,
        "nivelImportancia": "OPCIONAL"
    },
    
    "gtags / ctags": {
        "tipo": "Indexação de código",
        "custo": "GRATUITO",
        "para_queServe": """
  - Criar índices de código Go
  - Navegação rapida em grandes codebases
  - Integracao com vim/emacs
        """,
        "nivelImportancia": "OPCIONAL"
    }
}


## 11. BANCO DE DADOS / ARMAZENAMENTO
# =================================================================

TOOLS_DB = {
    "DB Browser for SQLite": {
        "tipo": "Editor SQLite",
        "custo": "GRATUITO",
        "url": "https://sqlitebrowser.org/",
        "para_queServe": """
  - Analisar bancos SQLite embutidos
  - O agy.exe pode usar SQLite para sessions
  - Visualizar e editar dados
        """,
        "nivelImportancia": "OPCIONAL"
    },
    
    "JSON Viewer/Editor": {
        "tipo": "Visualizador JSON",
        "custo": "GRATUITO",
        "para_queServe": """
  - Visualizar outputs JSON dos scripts
  - Formatagão e validação
  - VS Code já faz isso
        """,
        "nivelImportancia": "OPCIONAL"
    }
}


## 12. DOCUMENTAÇÃO / PESQUISA
# =================================================================

TOOLS_DOCS = {
    "Notion / Obsidian": {
        "tipo": "Taking notas",
        "custo": "GRATUITO",
        "para_queServe": """
  - Documentar achados da RE
  - Organizar informações
  - Manter registro de técnicas
        """,
        "nivelImportancia": "OPCIONAL"
    },
    
    "Draw.io / Excalidraw": {
        "tipo": "Diagramação",
        "custo": "GRATUITO",
        "para_queServe": """
  - Desenhar arquitetura do sistema
  - Mapear fluxo de controle
  - Documentar achados visualmente
        """,
        "nivelImportancia": "OPCIONAL"
    }
}


# =================================================================
# RESUMO EXECUTIVO
# =================================================================

def print_summary():
    print("""
================================================================================
  RESUMO: FERRAMENTAS NECESSÁRIAS PARA ENGENHARIA REVERSA PROFISSIONAL
================================================================================

[ESSENCIAIS - INSTALAR PRIMERO]
--------------------------------------------------------------------------------
  1. FLARE-VM          -> Distro Windows com TUDO instalado
     Download: https://github.com/mandiant/flare-vm
     
  2. Python 3.11       -> Linguagem de scripting
     Already installed: OK
     
  3. Ghidra            -> Descompilador gratuito mais poderoso
     Download: https://ghidra-sre.org/
     
  4. x64dbg            -> Debugger Windows
     Download: https://x64dbg.com/
     
  5. Wireshark         -> Análise de rede
     Download: https://www.wireshark.org/
     
  6. HxD               -> Hex editor
     Download: https://mh-nexus.de/en/hxd/

[CÓSIDO - PARA RESULTADOS MAXIMOS]
--------------------------------------------------------------------------------
  7. Binary Ninja      -> Melhor UI (trial 30 dias ou $399)
     Download: https://binary.ninja/
     
  8. IDA Pro           -> Melhor descompilador ($2500+)
     Download: https://hex-rays.com/
     
  9. Fiddler           -> HTTP inspection
     Download: https://www.telerik.com/fiddler

[UTILS - PARA AUTOMACAO]
--------------------------------------------------------------------------------
  10. GoRE Toolkit     -> Nosso toolkit criado (gratuito)
      Location: C:\\Users\\devel\\tools\\reverse\\go-re-engine\\

[OPCIONAIS - CONTEXTO ESPECIFICO]
--------------------------------------------------------------------------------
  11. Process Monitor  -> Sysinternals, monitoramento de sistema
  12. APIMon          -> Monitor de APIs
  13. Burp Suite      -> Testes web
  14. Cutter          -> GUI para radare2
  15. WinDbg          -> Debugger avanzado

================================================================================
  TOTAL: ~15 ferramentas principais
  Custo total essencial: $0 (tudo gratuito)
  Custo total profissional: ~$3000 (IDA Pro)
================================================================================
""")


if __name__ == "__main__":
    print_summary()
