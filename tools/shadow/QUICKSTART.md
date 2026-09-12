# Shadow Toolkit v36.1 — Quick Start

## Instalação

```bash
cd C:\Users\devel\shadow-toolkit
pip install curl_cffi websockets
python shadow_orchestrator.py
```

## Configuração

1. Edite `accounts.json` com suas credenciais:
```json
{
  "accounts": [
    {
      "account_id": "USER_ID",
      "domain": "example.com",
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "pix_key": "email@example.com",
      "pix_name": "Seu Nome"
    }
  ]
}
```

2. Opcional: Configure Discord webhook em `sombra_config.json`

## Comandos Rápidos

```
shadow status        # Ver estatísticas
shadow scan <domain> # Recon com Cloudflare bypass
shadow tokens        # Listar tokens capturados
shadow vulns         # Mostrar vulnerabilidades
shadow flow <acc>    # Pipeline completo (scan → transfer → withdraw)
shadow export        # Exportar dados
shadow clear         # Limpar dados
```

## Integração com Apex

O Shadow Toolkit é compatível com o Apex v9.0:
- Detecção automática de modelo via ModelFingerprinter
- Drift quântico aplicado em scans multi-turno
- Feedback loop registra resultados para evolução

## Estrutura de Arquivos

```
shadow-toolkit/
├── shadow_orchestrator.py    # Engine principal
├── accounts.json             # Credenciais
├── sombra_config.json        # Configurações
├── payloads/                 # Payloads de ataque
├── results/                  # Resultados de scans
└── sombra_autosave_*.json    # Backups automáticos
```
