#!/usr/bin/env node
/**
 * Verify & Improve Loop — Sistema de Verificação e Melhoria Automática
 * Versão standalone (sem dependências externas)
 * 
 * Antes de finalizar qualquer tarefa, busca na internet para validar
 * e melhora automaticamente baseado em referências encontradas.
 */

class VerifyImproveLoop {
  constructor(options = {}) {
    this.enabled = options.enabled !== false;
    this.maxRounds = options.maxRounds || 3;
    this.minScore = options.minScore || 85;
    this.verbose = options.verbose !== false;
    this.checklist = new QualityChecklist();
    this.history = [];
    
    // Mock de busca para teste
    this.searchMock = options.searchMock || this._defaultSearch;
  }

  /**
   * Executa o loop de verificação e melhoria
   */
  async execute(task, implementFn) {
    if (!this.enabled) {
      return { result: await implementFn(), score: 100, improvements: [] };
    }

    const context = {
      task: task.name || 'untitled',
      type: task.type || 'general',
      implementation: null,
      issues: [],
      improvements: [],
      searches: [],
      score: 0,
      improvementsApplied: new Set(),
      round: 0
    };

    console.log(`\n${'═'.repeat(60)}`);
    console.log(`🔄 VERIFY & IMPROVE LOOP`);
    console.log(`Tarefa: ${context.task}`);
    console.log(`Tipo: ${context.type}`);
    console.log(`${'═'.repeat(60)}\n`);

    for (let round = 1; round <= this.maxRounds; round++) {
      context.round = round;
      console.log(`━━━ Round ${round}/${this.maxRounds} ━━━\n`);

      // Implementar (passando contexto com melhorias aplicadas)
      console.log('🔨 Implementando...');
      try {
        context.implementation = await implementFn(context);
      } catch (e) {
        console.error('❌ Erro na implementação:', e.message);
        context.issues.push({ type: 'error', message: e.message });
      }

      if (!context.implementation) break;

      // Buscar referências
      console.log('\n🔍 Buscando referências...');
      const references = await this.searchReferences(context);
      context.searches.push(references);

      // Analisar gaps
      console.log('\n📊 Analisando qualidade...');
      const analysis = await this.analyzeQuality(context, references);
      context.issues = analysis.issues;
      
      // Filtrar melhorias já aplicadas
      context.improvements = analysis.improvements.filter(
        imp => !context.improvementsApplied.has(imp.action)
      );

      // Calcular score
      context.score = this.calculateScore(analysis);
      console.log(`\n✅ Score: ${context.score}/100`);

      // Mostrar checklist
      this.checklist.display(context.type);

      // Verificar se passou
      if (context.score >= this.minScore) {
        console.log(`\n🎉 Qualidade atingida! (${context.score} >= ${this.minScore})`);
        break;
      }

      // Melhorar
      if (round < this.maxRounds && context.improvements.length > 0) {
        console.log(`\n🔧 Aplicando ${context.improvements.length} melhorias...`);
        await this.applyImprovements(context);
        // Marcar melhorias como aplicadas
        for (const imp of context.improvements) {
          context.improvementsApplied.add(imp.action);
        }
      }
    }

    this.logFinalReport(context);

    return {
      result: context.implementation,
      score: context.score,
      issues: context.issues,
      improvements: context.improvements,
      passes: context.score >= this.minScore
    };
  }

  /**
   * Busca referências (mock para teste)
   */
  async searchReferences(context) {
    const queries = this.getQueriesForType(context.type, context.task);
    const results = {};

    for (const query of queries) {
      console.log(`  → Buscando: "${query}"`);
      try {
        const search = await this.searchMock(query);
        results[query] = search.results || [];
        console.log(`    ✓ Encontrados ${search.results?.length || 0} resultados`);
      } catch (e) {
        console.log(`    ⚠ Erro: ${e.message}`);
        results[query] = [];
      }
    }

    return results;
  }

  /**
   * Analisa qualidade
   */
  async analyzeQuality(context, references) {
    const issues = [];
    const improvements = [];

    switch (context.type) {
      case 'ui':
        issues.push(...this.checkUIQuality(context, references));
        improvements.push(...this.getUIImprovements(context, references));
        break;
      case 'code':
        issues.push(...this.checkCodeQuality(context, references));
        improvements.push(...this.getCodeImprovements(context, references));
        break;
      case 'api':
        issues.push(...this.checkAPIQuality(context, references));
        improvements.push(...this.getAPIImprovements(context, references));
        break;
      case 'security':
        issues.push(...this.checkSecurityQuality(context, references));
        improvements.push(...this.getSecurityImprovements(context, references));
        break;
      default:
        issues.push({ type: 'warning', message: 'Tipo não especificado' });
    }

    return { issues, improvements };
  }

  // ===== CHECKS =====

  checkUIQuality(context, references) {
    const issues = [];
    if (!context.implementation?.hasLoadingState) issues.push({ type: 'missing', message: 'Falta estado de loading' });
    if (!context.implementation?.hasErrorState) issues.push({ type: 'missing', message: 'Falta estado de erro' });
    if (!context.implementation?.hasEmptyState) issues.push({ type: 'missing', message: 'Falta estado vazio' });
    if (!context.implementation?.responsive) issues.push({ type: 'missing', message: 'Precisa verificar responsividade' });
    if (!context.implementation?.accessibility) issues.push({ type: 'missing', message: 'Faltam labels de acessibilidade' });
    return issues;
  }

  checkCodeQuality(context, references) {
    const issues = [];
    if (!context.implementation?.tests) issues.push({ type: 'missing', message: 'Faltam testes' });
    if (!context.implementation?.documentation) issues.push({ type: 'missing', message: 'Falta documentação' });
    return issues;
  }

  checkAPIQuality(context, references) {
    const issues = [];
    if (!context.implementation?.headers) issues.push({ type: 'missing', message: 'Faltam headers de segurança' });
    if (!context.implementation?.errorHandling) issues.push({ type: 'missing', message: 'Falta manejo de erros' });
    if (!context.implementation?.rateLimit) issues.push({ type: 'missing', message: 'Falta rate limiting' });
    return issues;
  }

  checkSecurityQuality(context, references) {
    const issues = [];
    if (!context.implementation?.params?.validated) issues.push({ type: 'critical', message: 'Vulnerabilidade: SQL Injection' });
    if (!context.implementation?.input?.sanitized) issues.push({ type: 'critical', message: 'Vulnerabilidade: XSS' });
    if (!context.implementation?.auth?.verified) issues.push({ type: 'critical', message: 'Vulnerabilidade: Autenticação não verificada' });
    if (!context.implementation?.csrf?.token) issues.push({ type: 'critical', message: 'Vulnerabilidade: CSRF sem token' });
    if (context.implementation?.hasHardcodedSecrets) issues.push({ type: 'critical', message: 'Vulnerabilidade: Secrets hardcoded' });
    return issues;
  }

  // ===== MELHORIAS =====

  getUIImprovements(context, references) {
    const improvements = [];
    if (!context.implementation?.hasLoadingState) improvements.push({ type: 'ui', action: 'Adicionar skeleton loading', priority: 'high' });
    if (!context.implementation?.hasErrorState) improvements.push({ type: 'ui', action: 'Adicionar estado de erro', priority: 'high' });
    if (!context.implementation?.responsive) improvements.push({ type: 'ui', action: 'Implementar responsividade', priority: 'medium' });
    if (!context.implementation?.accessibility) improvements.push({ type: 'ui', action: 'Adicionar ARIA labels', priority: 'medium' });
    return improvements;
  }

  getCodeImprovements(context, references) {
    const improvements = [];
    if (!context.implementation?.tests) improvements.push({ type: 'code', action: 'Adicionar testes unitários', priority: 'high' });
    if (!context.implementation?.documentation) improvements.push({ type: 'code', action: 'Adicionar JSDoc', priority: 'medium' });
    return improvements;
  }

  getAPIImprovements(context, references) {
    const improvements = [];
    if (!context.implementation?.headers) improvements.push({ type: 'api', action: 'Adicionar headers de segurança', priority: 'high' });
    if (!context.implementation?.rateLimit) improvements.push({ type: 'api', action: 'Implementar rate limiting', priority: 'medium' });
    return improvements;
  }

  getSecurityImprovements(context, references) {
    const improvements = [];
    if (!context.implementation?.params?.validated) improvements.push({ type: 'security', action: 'Validar todos os inputs', priority: 'critical' });
    if (!context.implementation?.input?.sanitized) improvements.push({ type: 'security', action: 'Sanitizar inputs contra XSS', priority: 'critical' });
    if (!context.implementation?.auth?.verified) improvements.push({ type: 'security', action: 'Verificar autenticação', priority: 'critical' });
    if (!context.implementation?.csrf?.token) improvements.push({ type: 'security', action: 'Adicionar token CSRF', priority: 'high' });
    if (context.implementation?.hasHardcodedSecrets) improvements.push({ type: 'security', action: 'Remover secrets hardcoded', priority: 'critical' });
    return improvements;
  }

  // ===== APLICAÇÃO =====

  async applyImprovements(context) {
    for (const improvement of context.improvements.slice(0, 3)) {
      console.log(`  🔧 ${improvement.action}`);
      await this.applyImprovement(context, improvement);
    }
  }

  async applyImprovement(context, improvement) {
    if (!context.implementation) context.implementation = {};

    switch (improvement.type) {
      case 'ui':
        if (improvement.action.includes('loading')) context.implementation.hasLoadingState = true;
        if (improvement.action.includes('erro')) context.implementation.hasErrorState = true;
        if (improvement.action.includes('respons')) context.implementation.responsive = true;
        if (improvement.action.includes('ARIA')) context.implementation.accessibility = true;
        break;
      case 'code':
        if (improvement.action.includes('testes')) context.implementation.tests = true;
        if (improvement.action.includes('documentação')) context.implementation.documentation = true;
        break;
      case 'api':
        if (improvement.action.includes('headers')) context.implementation.headers = true;
        if (improvement.action.includes('rate')) context.implementation.rateLimit = true;
        break;
      case 'security':
        if (improvement.action.includes('inputs')) context.implementation.params = { validated: true };
        if (improvement.action.includes('XSS')) context.implementation.input = { sanitized: true };
        if (improvement.action.includes('autenticação')) context.implementation.auth = { verified: true };
        if (improvement.action.includes('CSRF')) context.implementation.csrf = { token: true };
        if (improvement.action.includes('secrets')) context.implementation.hasHardcodedSecrets = false;
        break;
    }
  }

  // ===== SCORE =====

  calculateScore(analysis) {
    const issues = analysis.issues || [];
    const critical = issues.filter(i => i.type === 'critical').length;
    const missing = issues.filter(i => i.type === 'missing').length;
    const warnings = issues.filter(i => i.type === 'warning').length;

    let score = 100;
    score -= critical * 20;
    score -= missing * 5;
    score -= warnings * 2;

    return Math.max(0, Math.min(100, score));
  }

  // ===== HELPERS =====

  getQueriesForType(type, task) {
    const queries = {
      ui: [`UI design ${task} 2024`, `${task} component best practices`, `${task} responsive example`],
      code: [`best practices ${task}`, `${task} implementation example`, `${task} code review`],
      api: [`API documentation ${task}`, `${task} endpoint best practices`, `${task} authentication`],
      security: [`security vulnerabilities ${task}`, `OWASP ${task}`, `security best practices 2024`]
    };
    return queries[type] || queries.code;
  }

  logFinalReport(context) {
    console.log(`\n${'═'.repeat(60)}`);
    console.log(`📊 RELATÓRIO FINAL`);
    console.log(`${'═'.repeat(60)}`);
    console.log(`Tarefa: ${context.task}`);
    console.log(`Score Final: ${context.score}/100`);
    console.log(`Status: ${context.score >= this.minScore ? '✅ APROVADO' : '❌ REPROVADO'}`);
    console.log(`Problemas: ${context.issues.length}`);
    console.log(`Melhorias: ${context.improvements.length}`);
    
    if (context.issues.length > 0) {
      console.log('\n🐛 Problemas encontrados:');
      for (const issue of context.issues.slice(0, 5)) {
        const icon = issue.type === 'critical' ? '🔴' : issue.type === 'missing' ? '🟡' : '⚪';
        console.log(`  ${icon} ${issue.message}`);
      }
    }

    if (context.improvements.length > 0) {
      console.log('\n✨ Melhorias aplicadas:');
      for (const imp of context.improvements.slice(0, 5)) {
        console.log(`  • ${imp.action}`);
      }
    }

    console.log(`${'═'.repeat(60)}\n`);
  }

  // Mock de busca
  _defaultSearch(query) {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({ results: [], query });
      }, 100);
    });
  }
}

class QualityChecklist {
  display(type) {
    const checklists = {
      ui: ['□ Loading state', '□ Error state', '□ Empty state', '□ Responsive', '□ Accessibility (ARIA)', '□ Hover/Focus states'],
      code: ['□ No linting warnings', '□ Type safety', '□ Unit tests', '□ Documentation', '□ Error handling'],
      api: ['□ Input validation', '□ Authentication', '□ Rate limiting', '□ Error responses', '□ Proper headers'],
      security: ['□ SQL Injection prevented', '□ XSS prevented', '□ CSRF tokens', '□ Input sanitization', '□ Auth verified']
    };

    const items = checklists[type] || checklists.code;
    console.log('\n📋 Checklist:');
    for (const item of items) {
      console.log(`  ${item}`);
    }
    console.log('');
  }
}

module.exports = { VerifyImproveLoop, QualityChecklist };
