# DarkWeb Intel — Modo 4070
Ferramenta de inteligência e pesquisa na darkweb para threat intelligence.

## Funcionalidades

- **Base de Conhecimento**: 11 categorias TTP, 8 exploits conhecidos, 12 famílias de malware, 8 ferramentas
- **Análise de Indicadores**: CVE, IOCs, nomes de malware/ferramentas
- **Fontes**: Gateways Tor, paste sites, fóruns underground
- **Exportação**: JSON, TXT

## Instalação

```bash
pip install aiohttp
```

## Uso CLI

```bash
# Analisar indicador/threat
python darkweb_intel.py analyze "CVE-2021-44228"
python darkweb_intel.py analyze "emotet"
python darkweb_intel.py analyze "cobalt_strike"

# Buscar na darkweb
python darkweb_intel.py search "ransomware"
python darkweb_intel.py search "credential_dump" --source all

# Ver base de conhecimento
python darkweb_intel.py knowledge

# Estatísticas
python darkweb_intel.py stats

# Exportar resultados
python darkweb_intel.py search "exploit" --output results.json
```

## Uso Python

```python
from tools.darkweb_intel import DarkWebIntelligence, ThreatKnowledgeDB

# Inicializar
intel = DarkWebIntelligence()

# Analisar threat
result = await intel.analyze_threat("CVE-2021-44228")
print(result["risk_level"])  # "medium"
print(result["matches"])     # Lista de matches

# Buscar na darkweb
items = await intel.search("ransomware")
for item in items:
    print(f"[{item.category.value}] {item.title}")

# Base de conhecimento
kb = ThreatKnowledgeDB()
exploit = kb.get_exploit_info("log4j")
malware = kb.get_malware_info("lockbit")
tool = kb.get_tool_info("cobalt_strike")
```

## Categorias de Ameaça

| Categoria | Descrição |
|-----------|-----------|
| MALWARE | Malware em geral |
| RANSOMWARE | Ransomware e famílias |
| CREDENTIALS | Credenciais e dumping |
| AUTH_BYPASS | Bypass de autenticação |
| SQLi/XSS/LFI/SSRF | Tipos de exploit web |
| RCE | Remote Code Execution |
| C2 | Command & Control |
| STEALER | Credential stealers |
| LOADER | Malware loaders |
| DATA_BREACH | Vazamentos de dados |

## TTPs (MITRE ATT&CK)

- initial_access
- execution
- persistence
- privilege_escalation
- defense_evasion
- credential_access
- discovery
- lateral_movement
- collection
- command_control
- exfiltration

## Fontes de Inteligência

| Fonte | Tipo | Status | Descrição |
|-------|------|--------|-----------|
| HackerNews | Blog/Forum | ✅ ONLINE | Artigos de segurança em tempo real |
| Reddit r/netsec | Forum | ✅ ONLINE | Discussões de segurança |
| Exploit-DB | Exploit | ✅ ONLINE | Base de exploits públicos |
| Paste Sites | Paste | ⚠️ Fallback | psbdmp.ws, Pastebin, sopha.me |
| Tor Gateway | Onion | 🔧 Opcional | Requer Tor rodando localmente |

> **Nota**: Configurar Tor para acesso a .onion sites:
> ```bash
> # Instalar Tor
> sudo apt install tor
> sudo systemctl start tor
> 
> # Usar com --tor flag
> python darkweb_intel.py search "query" --tor
> ```

---

**DarkWeb Intel v4070 — Intelligence gathered, threats identified.** 🐀
