---
name: agent-activation
description: Skill de ativação de agentes Kuroko e Sombra. Use para alternar entre modos, verificar status, ou reiniciar agentes.
aliases:
  - kuroko
  - sombra
  - shadow
  - agents
  - agente
references:
  - kuroko
  - sombra
---

# Agent Activation Skill

Controla a ativação e o estado dos agentes **Kuroko** (benchmark de segurança cibernética) e **Sombra** (desenvolvimento e segurança ofensiva).

## Comandos

| Comando            | Ação                                           |
|--------------------|------------------------------------------------|
| `ativar kuroko`    | Ativa o agente Kuroko                          |
| `ativar sombra`    | Ativa o agente Sombra                          |
| `modo kuroko`      | Muda para o modo Kuroko                        |
| `modo sombra`      | Muda para o modo Sombra                        |
| `status`           | Mostra o estado atual dos agentes              |
| `desativar [nome]` | Desativa um agente específico                  |
| `lista`            | Lista todos os agentes disponíveis             |

## Como Usar

### Ativar Kuroko

O agente Kuroko é especializado em benchmark de segurança cibernética, análise de malware, engenharia reversa, exploração de vulnerabilidades e desenvolvimento de PoCs.

```
ativar kuroko
ou
modo kuroko
```

Resposta esperada: confirmação com prefixo `[Kuroko]`.

### Ativar Sombra

O agente Sombra é especializado em desenvolvimento de software, captura de tokens, bypass, engenharia reversa de APIs e automação.

```
ativar sombra
ou
modo sombra
```

Resposta esperada: confirmação do agente Sombra.

### Ver Status

```
status
ou
!status
```

Mostra quais agentes estão ativos e seu modelo atual.

### Listar Agentes

```
lista
ou
!lista
```

Exibe todos os agentes configurados no sistema.

## Configuração

Os agentes são definidos em:

- `~/.config/opencode/opencode.jsonc` — configuração principal
- `~/.config/opencode/agents/Kuroko.md` — instruções do Kuroko
- `~/.config/opencode/agents/prompt.md` — instruções do Sombra

## Notas

- Cada agente usa o modelo `agnes/agnes-2.5-flash` por padrão
- Kuroko responde sempre com `[Kuroko]` no início
- Sombra responde em português com tom direto
- Ambos têm acesso a: read, grep, glob, edit, bash, lsp
