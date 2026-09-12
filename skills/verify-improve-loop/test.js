#!/usr/bin/env node
/**
 * Teste do sistema Verify & Improve Loop
 * Versão corrigida com persistência de melhorias
 */

const { VerifyImproveLoop } = require('./verify');

async function testUITask() {
  console.log('\n' + '='.repeat(70));
  console.log('TESTE 1: TAREFA UI - Criar componente ProductCard');
  console.log('='.repeat(70));

  const loop = new VerifyImproveLoop({ maxRounds: 3, verbose: true });
  
  // Estado persistente entre rounds
  let state = {
    component: 'ProductCard',
    hasLoadingState: false,
    hasErrorState: false,
    hasEmptyState: false,
    responsive: false,
    accessibility: false
  };

  const result = await loop.execute(
    { name: 'ProductCard Component', type: 'ui' },
    async (context) => {
      // Simula aplicação de melhorias do round anterior
      if (context.improvementsApplied?.has('Adicionar skeleton loading')) state.hasLoadingState = true;
      if (context.improvementsApplied?.has('Adicionar estado de erro')) state.hasErrorState = true;
      if (context.improvementsApplied?.has('Implementar responsividade')) state.responsive = true;
      if (context.improvementsApplied?.has('Adicionar ARIA labels')) state.accessibility = true;
      
      return { ...state };
    }
  );

  console.log('\n📊 RESULTADO:');
  console.log(`   Score: ${result.score}/100`);
  console.log(`   Aprovado: ${result.passes ? 'SIM ✅' : 'NÃO ❌'}`);
  console.log(`   Problemas: ${result.issues.length}`);
  console.log(`   Melhorias: ${result.improvements.length}`);
  
  return result;
}

async function testSecurityTask() {
  console.log('\n' + '='.repeat(70));
  console.log('TESTE 2: TAREFA SEGURANÇA - Implementar JWT Auth');
  console.log('='.repeat(70));

  const loop = new VerifyImproveLoop({ maxRounds: 3, verbose: true });
  
  let state = {
    endpoint: '/api/auth/login',
    params: { validated: false },
    input: { sanitized: false },
    auth: { verified: false },
    csrf: { token: false },
    hasHardcodedSecrets: true
  };

  const result = await loop.execute(
    { name: 'JWT Authentication', type: 'security' },
    async (context) => {
      // Simula aplicação de melhorias
      if (context.improvementsApplied?.has('Validar todos os inputs')) state.params = { validated: true };
      if (context.improvementsApplied?.has('Sanitizar inputs contra XSS')) state.input = { sanitized: true };
      if (context.improvementsApplied?.has('Verificar autenticação')) state.auth = { verified: true };
      if (context.improvementsApplied?.has('Adicionar token CSRF')) state.csrf = { token: true };
      if (context.improvementsApplied?.has('Remover secrets hardcoded')) state.hasHardcodedSecrets = false;
      
      return { ...state };
    }
  );

  console.log('\n📊 RESULTADO:');
  console.log(`   Score: ${result.score}/100`);
  console.log(`   Aprovado: ${result.passes ? 'SIM ✅' : 'NÃO ❌'}`);
  console.log(`   Problemas críticos: ${result.issues.filter(i => i.type === 'critical').length}`);
  
  return result;
}

async function runAllTests() {
  console.log('\n╔══════════════════════════════════════════════════════════════╗');
  console.log('║     TESTE DO SISTEMA VERIFY & IMPROVE LOOP v1.0            ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  const results = [];
  
  results.push(await testUITask());
  results.push(await testSecurityTask());

  // Resumo
  console.log('\n' + '='.repeat(70));
  console.log('RESUMO DOS TESTES');
  console.log('='.repeat(70));
  
  const passed = results.filter(r => r.passes).length;
  const total = results.length;
  const avgScore = results.reduce((sum, r) => sum + r.score, 0) / total;

  console.log(`\n   Testes executados: ${total}`);
  console.log(`   Aprovados: ${passed}`);
  console.log(`   Reprovados: ${total - passed}`);
  console.log(`   Score médio: ${avgScore.toFixed(1)}/100`);
  
  if (passed === total) {
    console.log('\n   ✅ TODOS OS TESTES PASSARAM!');
  } else {
    console.log('\n   ⚠️  Alguns testes precisam de atenção');
  }
  
  console.log('='.repeat(70) + '\n');
}

runAllTests().catch(console.error);
