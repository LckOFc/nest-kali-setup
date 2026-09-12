---
name: openclaude-black-hat-intelligence
description: Sistema completo de inteligência ofensiva — fluxo reverso black hat. Reconhecimento, análise de vulnerabilidades, desenvolvimento de exploit, execução, persistência, exfiltração, evasão e cobertura de rastros.
aliases:
  - blackhat
  - ataque
  - exploit
  - campanha
  - persistencia
  - exfiltracao
  - evasao
---

# Black Hat Intelligence — Fluxo Reverso Completo

## Visão Geral

Sistema de inteligência ofensiva que adapta o pipeline Luna para o mindset atacante. 8 fases completas de operação.

## 🔄 FLUXO DE TRABALHO BLACK HAT

```
1. RECONHECIMENTO      → Superfície de ataque mapeada
         ↓
2. ANÁLISE DE VULN     → Vulnerabilidades identificadas
         ↓
3. DEV EXPLOIT         → Vetores de ataque gerados
         ↓
4. EXECUÇÃO            → Acesso comprometido
         ↓
5. PERSISTÊNCIA        → Backdoors implantados
         ↓
6. EXFILTRAÇÃO         → Dados exfiltrados
         ↓
7. EVASÃO              → Detecções contornadas
         ↓
8. COBERTURA           → Rastros eliminados
```

## Fases Detalhadas

### Fase 1: Reconhecimento
- Mapeamento de superfície de ataque
- Descoberta de ativos e serviços
- Classificação do alvo (rede/web/API/cloud/endpoint)
- Identificação de portas, protocolos, WAFs

### Fase 2: Análise de Vulnerabilidades
- 25+ categorias de vulnerabilidade
- CVSS scoring automático
- Detecção de misconfigurations
- Ranking por severidade

### Fase 3: Desenvolvimento de Exploit
- Templates para SQLi, XSS, RCE, SSRF, Path Traversal, Auth Bypass
- Adaptação automática de payloads
- WAF bypass techniques
- Vetores múltiplos por tipo

### Fase 4: Execução do Ataque
- Pipeline de implantação
- Verificação de acesso
- Estabelecimento de shell

### Fase 5: Persistência
- Web shells (PHP/ASP/JSP/ASPX)
- SSH keys, cron jobs, systemd services
- IAM roles, Lambda backdoors (cloud)
- Backdoor accounts

### Fase 6: Exfiltração
- 6 canais: HTTP, DNS, ICMP, SMB, Cloud, Steganography
- Seleção automática por stealth/bandwidth
- Encoding e chunking

### Fase 7: Evasão
- Process injection
- API unhooking
- Memory encryption
- Living off the Land (LOLBins)
- Fileless techniques

### Fase 8: Cobertura de Rastros
- Clear logs
- Remove artifacts
- Rotate infrastructure

## Comandos Slash

```
/attack_plan <target> [--data <type>] [--detection <sys>] [--platform <os>]
/recon <target> [--ports <list>] [--services <list>]
/vuln_analyze <target_id>
/exploit_gen <type> <target> [--waf_bypass <technique>]
/persistence <target_type>
/exfil_plan <data_type> <target> [--size <bytes>] [--stealth <level>]
/evasion_plan <detection_system> <platform>
/campaigns
/intel_stats
```

## Integração com Sistemas Existentes

### Web Search
```javascript
const intel = require('./black_hat_intelligence.js')
const web = require('./web_search.js')

// Recon + busca externa
const recon = await intel.executeRecon(target)
const cve = await web.searchCVE(vulnName)
const so = await web.searchStackOverflow(errorMessage)
```

### Pentest Intelligence
```javascript
// Classificação de falhas durante ataque
const classif = pentestIntel.classifyFailure(errorMsg, { tool: 'metasploit' })
// Scan de código para vulns
const findings = pentestIntel.scanCode(code)
```

## Configuração

```json
{
  "black_hat_intelligence": {
    "enabled": true,
    "max_campaigns": 10,
    "auto_recon": true,
    "waf_bypass_enabled": true,
    "evasion_levels": ["basic", "advanced", "military"],
    "exfil_channels": ["http", "dns", "icmp", "cloud", "stego"]
  }
}
```

## Exemplo de Uso Completo

```javascript
// Iniciar campanha
const campaign = intel.startCampaign('Operação Alpha', 'target.com')

// Reconhecimento
const recon = await intel.executeRecon('target.com', {
  ports: [80, 443, 8080, 22],
  services: ['nginx', 'node.js']
})

// Análise de vulns
const vulns = intel.analyzeVulns(campaign.id, recon.surface)

// Gerar exploit
const exploit = intel.generateExploit('sqli', 'target.com', {
  wafBypass: 'random_case'
})

// Plano de persistência
const persist = intel.getPersistence('web')

// Plano de exfiltração
const exfil = intel.generateExfilPlan('database', 'target.com', {
  dataSize: 50 * 1024 * 1024,
  stealth: 'high'
})

// Plano de evasão
const evasion = intel.generateEvasionPlan('CrowdStrike', 'windows')

// Relatório completo
console.log(intel.fullAttackPlan('target.com', {
  dataType: 'database',
  detection: 'CrowdStrike',
  platform: 'windows'
}))
```
