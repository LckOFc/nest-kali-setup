---
name: behavioral-sandbox
description: Sandbox comportamental para execucao segura de binarios suspeitos. Monitora criacao de arquivos, modificacoes de registro, conexoes de rede, processos filhos e atividades criptograficas. Gera score de ameaca e relatorio automatizado. V2.1: async monitoring, improved event tracking.
aliases:
  - sandbox
  - behavior
  - malware-run
  - dynamic-analysis
  - monitor
  - detonation
  - threat-score
---

# Behavioral Sandbox v2.1

Sandbox comportamental para execucao e monitoramento de binarios suspeitos em ambiente controlado.

> **v2.1**: Async monitoring com asyncio tasks, eventos tipados com dataclass, scoring melhorado com severidade por categoria.

## Instalacao

```bash
pip install psutil aiohttp
# Windows apenas: wmi requer PyWin32
# pip install pywin32
```

## O Que o Sandbox Monitora

| Categoria | Eventos Capturados | Severidade Base |
|-----------|-------------------|-----------------|
| **Arquivos** | Criacao/modificacao em paths suspeitos (%TEMP%, Startup, AppData) | Medium-High |
| **Registro** | Escritas em Run/RunOnce, valores de startup | High |
| **Rede** | Conexoes a IPs externos, portas altas, dominios SUSPEITOS | Medium |
| **Processos** | Criacao de processos filhos, spawn de cmd/powershell | High-Critical |
| **Criptografia** | Operacoes com criptoAPI (CryptEncrypt, BCryptEncrypt) | Critical |
| **Injecao** | OpenProcess + WriteProcessMemory + CreateRemoteThread | Critical |

## Comandos

```bash
# Executar e monitorar
python behavioral_sandbox.py C:\suspicious.exe

# Com argumentos e timeout
python behavioral_sandbox.py C:\suspicious.exe --args "param1 param2" --timeout 60

# Modo silencioso (sem stdout/stderr do processo)
python behavioral_sandbox.py C:\suspicious.exe --quiet

# Salvar resultados
python behavioral_sandbox.py C:\suspicious.exe --output result.json

# Analisar multiplas amostras
python behavioral_sandbox.py --batch C:\samples\*.exe
```

## Uso via Python

```python
from skills.behavioral_sandbox.behavioral_sandbox import BehavioralSandbox

sandbox = BehavioralSandbox(timeout_seconds=60)

# Executar amostra
result = await sandbox.run("malware.exe", args="--silent")
# {threat_score, threats_detected, events, summary}

# Verificar eventos coletados
for event in result["events"]:
    print(f"[{event.severity}] {event.event_type}: {event.target}")
```

## Score de Ameaca

```
Score 0-20:   SAFE     — Nenhuma atividade suspeita
Score 21-40:  LOW      — Atividades normais de programa
Score 41-60:  MEDIUM   — Alguma atividade suspeita
Score 61-80:  HIGH     — Múltiplos indicadores maliciosos
Score 81-100: CRITICAL — Comportamento claramente malicioso
```

## Saida JSON

```json
{
  "executable": "C:\\malware.exe",
  "args": "",
  "duration_seconds": 45.2,
  "exit_code": 0,
  "threat_score": 75,
  "threat_level": "HIGH",
  "events_count": 23,
  "threats_detected": [
    {"type": "SUSPICIOUS_FILE_OPERATION", "severity": "high", "count": 3},
    {"type": "EXCESSIVE_NETWORK", "severity": "medium", "count": 8},
    {"type": "PROCESS_SPAWN", "severity": "high", "count": 2}
  ],
  "events": [
    {"timestamp": 1234567890.123, "type": "file_create", "target": "%TEMP%\\payload.dll", "severity": "high"}
  ],
  "summary": "Detectado 3 ameaças: arquivos em paths suspeitos (3x), conexões de rede excessivas (8x), spawns de processos (2x)"
}
```

## Limitacoes

- Requer permissoes de administrador para monitoramento completo
- Alguns packers modernos podem evitar detecção
- Ambiente isolado recomendado (VM)
- Network monitor pode nao capturar trafego encriptado

---

**Behavioral Sandbox v2.1 — Behavior observed, threats scored.** 🐀
