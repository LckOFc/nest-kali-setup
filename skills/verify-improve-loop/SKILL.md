---
name: verify-improve-loop
description: Sistema de Verificação e Melhoria Contínua. Antes de finalizar qualquer tarefa, busca automaticamente na internet para validar se está correto. Se encontrar problemas, melhora o resultado e verifica novamente. Loop de verificação e melhoria até satisfatório. V2.1: quality gates, multi-round verification.
aliases:
  - verify
  - improve
  - check
  - validate
  - self-check
  - quality-gate
  - v2.1
---

# Verify & Improve Loop v2.1 — Sistema de Qualidade Automática

## Visão Geral

Sistema inteligente que **NUNCA finaliza uma tarefa sem verificar primeiro**. Antes de marcar como completo, o sistema:
1. Busca na internet para validar a solução
2. Compara com melhores práticas e exemplos atuais
3. Identifica possíveis problemas ou melhorias
4. Aplica correções automaticamente
5. Re-verifica até atingir qualidade satisfatória (score >= 85)

## Quando Usar

- **ANTES** de finalizar qualquer feature
- **ANTES** de entregar código
- **SEMPRE** para tarefas visuais/UI
- **SEMPRE** para integrações complexas
- **QUANDO** houver dúvida sobre correção

## Fluxo de Trabalho (v2.1)

```
┌─────────────────────────────────────────────────────────────┐
│  TAREFA INICIADA                                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  1. EXECUTAR TAREFA                                         │
│     - Implementar solução                                   │
│     - Criar código/arquivos                                 │
│     - Testar localmente                                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2. VERIFICAÇÃO AUTOMÁTICA                                  │
│     - Buscar na internet: "best practices [tarefa]"         │
│     - Buscar exemplos: "[tecnologia] [tarefa] example"      │
│     - Verificar docs oficiais                               │
│     - Checar issues/PRs relacionados                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3. ANÁLISE DE GAPS                                         │
│     - Comparar com referências                              │
│     - Identificar erros potenciais                          │
│     - Encontrar melhorias possíveis                         │
│     - Verificar edge cases                                  │
└─────────────────────────────────────────────────────────────┘
                     ┌─────┴─────┐
                     │           │
               Score >= 85?     Score < 85?
                     │           │
                     ▼           ▼
            ┌──────────┐  ┌─────────────────────┐
            │ FINALIZAR│  │ 4. MELHORIA         │
            │ TAREFA   │  │ - Corrigir erros    │
            └──────────┘  │ - Aplicar best      │
                     │     │   practices         │
                     │     │ - Otimizar código   │
                     │     └─────────────────────┘
                     │              │
                     └──────────────┘
                            ▼
                     Voltar para passo 2 (max 3 rounds)
```

## Métricas de Qualidade (v2.1)

```
Score Final = (Visual 30%) + (Código 30%) + (Segurança 25%) + (Performance 15%)

90-100: Excelente ✓
80-89:  Bom, com melhorias menores
70-79:  Aceitável, precisa ajustar
< 70:   Insuficiente, refazer
```

## Comandos Slash

```
# Verificação geral
/verify [tarefa]              # Verifica implementação atual
/verify auto                  # Verificação automática antes de finalizar
/verify ui --check component  # Verifica componente visual
/verify code --check file     # Verifica arquivo de código
/verify api --check endpoint  # Verifica integração API

# Melhoria contínua
/improve [problema]           # Melhora baseado em problema específico
/improve all                  # Melhoria completa (busca + aplica)
/improve visual               # Melhora apenas aspectos visuais
/improve performance          # Otimiza performance

# Validação
/validate                     # Valida se está pronto para entrega
/validate checklist           # Mostra checklist de qualidade
/validate report              # Gera relatório de qualidade
```

## Configuração

```json
{
  "verify_improve_loop": {
    "enabled": true,
    "auto_verify_before_finish": true,
    "max_verification_rounds": 3,
    "min_quality_score": 85,
    "verbose": true,
    "search_timeout_ms": 10000,
    "preferred_sources": ["github", "stackoverflow", "official_docs"],
    "skip_verify_for": ["docs", "todo", "placeholder"]
  }
}
```

## Regras de Ouro

1. **NUNCA** finalize sem verificar
2. **SEMPRE** busque referências para coisas visuais
3. **REPITA** verificação após melhorias
4. **PARE** quando score >= 85
5. **REGISTRE** o que foi verificado e melhorado

---

**Verify & Improve Loop v2.1 — Qualidade garantida, entregas validadas.** 🐀

```
┌─────────────────────────────────────────────────────────────┐
│  TAREFA INICIADA                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  1. EXECUTAR TAREFA                                         │
│     - Implementar solução                                   │
│     - Criar código/arquivos                                 │
│     - Testar localmente                                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  2. VERIFICAÇÃO AUTOMÁTICA                                  │
│     - Buscar na internet: "best practices [tarefa]"         │
│     - Buscar exemplos: "[tecnologia] [tarefa] example"      │
│     - Verificar docs oficiais                               │
│     - Checar issues/PRs relacionados                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  3. ANÁLISE DE GAPS                                         │
│     - Comparar com referências                              │
│     - Identificar erros potenciais                          │
│     - Encontrar melhorias possíveis                         │
│     - Verificar edge cases                                  │
└─────────────────────────────────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │           │
              CORRETO?     PROBLEMAS?
                    │           │
                    ▼           ▼
            ┌──────────┐  ┌─────────────────────┐
            │ FINALIZAR│  │ 4. MELHORIA         │
            │ TAREFA   │  │ - Corrigir erros    │
            └──────────┘  │ - Aplicar best      │
                    │     │   practices         │
                    │     │ - Otimizar código   │
                    │     └─────────────────────┘
                    │              │
                    └──────────────┘
                           ▼
                    Voltar para passo 2
```

## Tipos de Verificação

### 1. Verificação Visual/UI (para interfaces)

```
/verify ui --check [componente]
```

- Busca designs referenciais no Dribbble/Behance/GitHub
- Compara layouts, cores, tipografia
- Verifica responsividade
- Checa acessibilidade (contraste, tamaõ de fonte)
- Valida consistência com design system

**Query automática:**
```
"modern [tipo] UI design 2024 site:github.com"
"[tecnologia] component best practices"
"[feature] UX patterns examples"
```

### 2. Verificação de Código

```
/verify code --check [arquivo]
```

- Busca padrões de segurança
- Verifica performances
- Compara com exemplos da comunidade
- Checa versão mais recente da lib

**Query automática:**
```
"[linguagem] [funcionalidade] security best practices"
"[library] version [x] migration guide"
"[pattern] implementation example site:github.com"
```

### 3. Verificação de Integração

```
/verify api --check [endpoint]
```

- Valida formato de request/response
- Compara com documentação oficial
- Verifica headers necessários
- Checa limites de rate

**Query automática:**
```
"[API] authentication example"
"[service] API best practices 2024"
"[endpoint] curl example"
```

### 4. Verificação de Segurança

```
/verify security --check [feature]
```

- Busca vulnerabilidades conhecidas
- Verifica hardening recommendations
- Compara com OWASP guidelines
- Checa patches recentes

**Query automática:**
```
"[vulnerability] CVE [library] site:cve.org"
"[feature] security best practices OWASP"
"[library] security advisories"
```

## Comandos Slash

```
# Verificação geral
/verify [tarefa]              # Verifica implementação atual
/verify auto                  # Verificação automática antes de finalizar
/verify ui --check component  # Verifica componente visual
/verify code --check file     # Verifica arquivo de código
/verify api --check endpoint  # Verifica integração API

# Melhoria contínua
/improve [problema]           # Melhora baseado em problema específico
/improve all                  # Melhoria completa (busca + aplica)
/improve visual               # Melhora apenas aspectos visuais
/improve performance          # Otimiza performance

# Validação
/validate                     # Valida se está pronto para entrega
/validate checklist           # Mostra checklist de qualidade
/validate report              # Gera relatório de qualidade
```

## Checklists de Qualidade

### Para UI/Visual

- [ ] Layout responsivo em mobile/tablet/desktop
- [ ] Contraste de cores acessível (WCAG AA)
- [ ] Tipografia legível (mínimo 14px body)
- [ ] Espaçamento consistente
- [ ] Estados de hover/focus/active
- [ ] Loading states
- [ ] Error states
- [ ] Empty states
- [ ] Animações suaves (< 300ms)
- [ ] Acessibilidade (ARIA labels)

### Para Código

- [ ] Sem warnings de linter
- [ ] Sem warnings de type checker
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Sem hardcoded secrets
- [ ] Manejo de erros adequado
- [ ] Logging apropriado
- [ ] sem memory leaks
- [ ] Performance ok (< 100ms para ops críticas)
- [ ] Bundle size razoável

### Para Segurança

- [ ] Inputs validados/sanitizados
- [ ] Authentication verificada
- [ ] Authorization implementada
- [ ] SQL injection prevenido
- [ ] XSS prevenido
- [ ] CSRF tokens
- [ ] Rate limiting
- [ ] Headers de segurança
- [ ] Dependências atualizadas
- [ ] Sem sensitive data em logs

## Exemplo de Uso

### Cena 1: Criando um componente UI

```
Usuário: "Crie um card de produto com imagem, título, preço e botão de compra"

System:
  1. ✓ Cria o componente React
  2. 🔄 Verificando na internet...
     - Busca: "product card UI design 2024"
     - Busca: "ecommerce card best practices"
     - Busca: "product card responsive"
  3. 📊 Análise:
     - Encontrou 3 exemplos modernos
     - Nota: falta estado de loading
     - Nota: contraste do preço pode melhorar
     - Nota: falta accessibility labels
  4. 🔧 Melhorando:
     - Adiciona skeleton loading
     - Ajusta cores para WCAG AA
     - Adiciona aria-labels
     - Adiciona alt text na imagem
  5. 🔄 Verificando novamente...
     - PASS: Todos os checklists OK
  6. ✓ Entregue! Componente pronto e validado
```

### Cena 2: Implementando API

```
Usuário: "Implemente autenticação JWT"

System:
  1. ✓ Cria endpoints de auth
  2. 🔄 Verificando segurança...
     - Busca: "JWT authentication best practices 2024"
     - Busca: "JWT security vulnerabilities"
     - Busca: "JWT refresh token implementation"
  3. 📊 Análise:
     - Encontrou 5 vulnerabilidades comuns
     - Nota: faltando rotation de secret
     - Nota: faltando blacklist de tokens
     - Nota: expiração muito longa (7 dias)
  4. 🔧 Melhorando:
     - Reduz expiry para 1h (access) + 7d (refresh)
     - Adiciona token rotation
     - Implementa blacklist via Redis
     - Adiciona JTI (JWT ID)
  5. 🔄 Re-verificando...
     - PASS: Todas as vulnerabilidades mitigadas
  6. ✓ Entregue! Auth seguro e validado
```

## Integração com Web Search

Este skill usa o `openclaude-websearch` para:

```javascript
// Busca referências antes de finalizar
const refs = await webSearch({
  query: `best practices ${task} implementation`,
  sources: ['github', 'stackoverflow', 'reddit'],
  maxResults: 10
})

// Busca exemplos específicos
const examples = await webSearch({
  query: `${technology} ${feature} example`,
  sources: ['github'],
  maxResults: 15
})

// Busca problemas/vulnerabilidades
const issues = await webSearch({
  query: `${library} security vulnerabilities`,
  sources: ['cve', 'exploitdb'],
  maxResults: 5
})
```

## Métricas de Qualidade

Após cada verificação, calcula score:

```
Score Final = (Visual 30%) + (Código 30%) + (Segurança 25%) + (Performance 15%)

90-100: Excelente ✓
80-89:  Bom, com melhorias menores
70-79:  Aceitável, precisa ajustar
< 70:   Insuficiente, refazer
```

## Configuração

```json
{
  "verify_improve_loop": {
    "enabled": true,
    "auto_verify_before_finish": true,
    "max_verification_rounds": 3,
    "min_quality_score": 85,
    "verbose": true,
    "search_timeout_ms": 10000,
    "preferred_sources": ["github", "stackoverflow", "official_docs"],
    "skip_verify_for": ["docs", "todo", "placeholder"]
  }
}
```

## Regras de Ouro

1. **NUNCA** finalize sem verificar
2. **SEMPRE** busque referências para coisas visuais
3. **REPITA** verificação após melhorias
4. **PARE** quando score >= 85
5. **REGISTRE** o que foi verificado e melhorado

## Logs de Verificação

```
[VERIFY] Starting verification for: ProductCard
[VERIFY] Searching: "product card UI design 2024"
[VERIFY] Found 12 results from GitHub
[VERIFY] Analyzing patterns...
[FIX] Added loading state (skeleton)
[FIX] Improved contrast ratio (4.5:1 → 7.2:1)
[FIX] Added ARIA labels
[VERIFY] Re-checking...
[VERIFY] Quality Score: 92/100 ✓
[VERIFY] Done! Ready for delivery.
```
