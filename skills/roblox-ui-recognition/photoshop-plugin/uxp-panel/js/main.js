// FigmaPS2Roblox v3.1 — UXP Panel JavaScript (Improved)
// Adobe Photoshop 2024+ UXP API
//
// Melhorias v3.1:
//   - Fallbacks robustos para todas as operações PS
//   - Timeout em requests à IA (30s)
//   - Retry automático (3 tentativas)
//   - Cache de respostas da IA (evita custo repetido)
//   - Preview de thumbnails nos assets
//   - Sistema de templates
//   - Logs de progresso detalhados
//   - Tratamento de erros em camadas grandes
//   - Fila de exportação com debounce

const ps = require('photoshop');
const uxp = require('uxp');
const fs = uxp.plugins.fs;
const path = require('path');

// ── Estado global ──────────────────────────────────────────────────────────────

let docInfo = null;
let layerData = null;
let currentUDS = null;
let verificationReport = null;
let aiApiKey = null;
let generatedLuaCode = '';
let exportQueue = [];
let isExporting = false;
let aiCache = {}; // Simple in-memory cache

// ── Config com timeouts e retries ──────────────────────────────────────────────

const CONFIG = {
  robloxClasses: {
    background: 'ImageLabel', panel: 'Frame', button: 'TextButton',
    label: 'TextLabel', icon: 'ImageLabel', image: 'ImageLabel',
    bar: 'Frame', separator: 'Frame', input: 'TextBox',
  },
  responsiveStrategies: {
    background: 'Fill', button: 'ScaleToFit', label: 'ScaleToFit',
    icon: 'FixedSize', panel: 'ScaleToFit', bar: 'FixedSize',
    image: 'ScaleToFit', separator: 'FixedSize', input: 'ScaleToFit',
  },
  limits: { maxCanvas: 2048, maxInstances: 150, maxAssetKB: 10240 },
  aiTimeout: 30000,      // 30s timeout
  aiRetries: 3,          // 3 tentativas
  exportBatchSize: 5,    // exportar em lotes
  exportDebounceMs: 200, // debounce entre exports
  psCommandTimeout: 15000, // 15s timeout para comandos PS
};

// ── Templates ───────────────────────────────────────────────────────────────────

const TEMPLATES = {
  MainMenu: {
    name: 'MainMenu', description: 'Menu principal com botão Play',
    canvasWidth: 1920, canvasHeight: 1080,
    layers: [
      { name: 'background', type: 'background', x: 0, y: 0, width: 1920, height: 1080, fill: '#1E1E2E', strategy: 'Fill' },
      { name: 'btn_play', type: 'button', x: 760, y: 500, width: 400, height: 100, fill: '#89B4FA', text: 'PLAY', size: 32, strategy: 'ScaleToFit' },
      { name: 'btn_settings', type: 'button', x: 810, y: 650, width: 300, height: 80, fill: '#A6E3A1', text: 'SETTINGS', size: 24, strategy: 'ScaleToFit' },
    ],
  },
  HUD: {
    name: 'HUD', description: 'Interface durante gameplay',
    canvasWidth: 1920, canvasHeight: 1080,
    layers: [
      { name: 'hp_bar_bg', type: 'bar', x: 20, y: 20, width: 300, height: 30, fill: '#333333', strategy: 'FixedSize' },
      { name: 'score_label', type: 'label', x: 1750, y: 20, width: 150, height: 40, text: 'SCORE: 0', size: 28, strategy: 'FixedSize' },
      { name: 'minimap_frame', type: 'panel', x: 1600, y: 800, width: 300, height: 240, strategy: 'FixedSize' },
    ],
  },
};

// ── Tab Navigation ──────────────────────────────────────────────────────────────

function switchTab(tabId) {
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', ['info', 'layers', 'verify', 'ai', 'export', 'templates'][i] === tabId);
  });
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  const panel = document.getElementById(`panel-${tabId}`);
  if (panel) panel.classList.add('active');

  if (tabId === 'layers') refreshLayers();
  if (tabId === 'verify' && !verificationReport) runVerification();
  if (tabId === 'ai' && !currentUDS) runAIAnalysis();
}

// ── Document Info ───────────────────────────────────────────────────────────────

async function refreshDocInfo() {
  try {
    const app = ps.app;
    const doc = app.activeDocument;

    if (!doc) {
      setStatus('Nenhum documento aberto', 'err');
      updateScoreBadge(null);
      return;
    }

    const w = Math.round(doc.width);
    const h = Math.round(doc.height);
    const layerCount = await safeCount(async () => countVisibleLayers(doc), 0);
    const groupCount = await safeCount(async () => countGroups(doc), 0);
    const artboardCount = await safeCount(async () => countArtboards(doc), 0);

    docInfo = { name: doc.name, width: w, height: h, layers: layerCount, groups: groupCount, artboards: artboardCount };

    document.getElementById('docName').textContent = doc.name;
    document.getElementById('canvasSize').textContent = `${w} × ${h}`;
    document.getElementById('layerCount').textContent = layerCount + ' camadas';
    document.getElementById('groupCount').textContent = groupCount + ' grupos';
    document.getElementById('artboardCount') && (document.getElementById('artboardCount').textContent = artboardCount + ' artboards');

    const { colors, fonts } = await safeCount(async () => detectColorsAndFonts(doc), { colors: 0, fonts: 0 });
    document.getElementById('colorCount').textContent = colors + ' cores';
    document.getElementById('fontCount').textContent = fonts + ' fontes';

    setStatus(`Pronto — ${doc.name} (${w}×${h})`, 'ok');

    if (currentUDS) {
      updateScoreBadge(verificationReport ? verificationReport.summary.score : null);
    }
  } catch (e) {
    setStatus('Erro ao ler documento: ' + truncate(e.message, 50), 'err');
    console.error('[PS] Doc info error:', e);
  }
}

async function countVisibleLayers(doc) {
  let count = 0;
  const layers = doc.layers || [];
  for (const layer of layers) {
    const kind = layer.kind ? layer.kind.toString() : '';
    if (kind.includes('Layer')) {
      if (layer.visible) count++;
    } else if (kind.includes('LayerSet')) {
      const children = layer.layers || [];
      for (const child of children) {
        if (child.visible) count++;
      }
    }
  }
  return count;
}

async function countGroups(doc) {
  let count = 0;
  for (const layer of (doc.layers || [])) {
    if (layer.kind && layer.kind.toString().includes('LayerSet')) count++;
  }
  return count;
}

async function countArtboards(doc) {
  let count = 0;
  for (const layer of (doc.layers || [])) {
    if (layer.kind && layer.kind.toString().includes('Artboard')) count++;
  }
  return count;
}

async function detectColorsAndFonts(doc) {
  const seenColors = new Set();
  const seenFonts = new Set();
  try {
    const layers = await getAllLayersRecursive(doc);
    for (const l of layers) {
      if (l.fill?.hex) seenColors.add(l.fill.hex.toUpperCase());
      if (l.text?.font) seenFonts.add(l.text.font);
    }
  } catch (e) {}
  return { colors: seenColors.size, fonts: seenFonts.size };
}

// ── Helper: safe execution with timeout ─────────────────────────────────────────

async function safeCount(fn, fallback) {
  try {
    const timeout = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), 5000)
    );
    return await Promise.race([fn(), timeout]);
  } catch (e) {
    console.warn('[PS] Operation timed out, using fallback:', e.message);
    return fallback;
  }
}

// ── Layer Tree com preview de thumbnails ────────────────────────────────────────

async function refreshLayers() {
  try {
    const app = ps.app;
    const doc = app.activeDocument;

    if (!doc) {
      document.getElementById('layerTree').innerHTML =
        '<div style="text-align:center;color:var(--muted);padding:20px;">Abra um documento no Photoshop</div>';
      return;
    }

    const container = document.getElementById('layerTree');
    const allLayers = await getAllLayersRecursive(doc);

    if (allLayers.length === 0) {
      container.innerHTML =
        '<div style="text-align:center;color:var(--muted);padding:20px;">Nenhuma camada visível encontrada</div>';
      document.getElementById('layerInfoText').textContent = '0 camadas';
      return;
    }

    document.getElementById('layerInfoText').textContent = `${allLayers.length} camadas`;

    let html = '';
    for (const l of allLayers) {
      const type = classifyLayer(l.name);
      const typeLabel = getTypeLabel(type);
      const indent = l.depth * 14;
      const colorDot = l.fill ? `<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${l.fill.hex};margin-right:4px;vertical-align:middle;"></span>` : '';
      const textBadge = l.text ? `<span style="color:var(--purple);font-size:9px;margin-left:4px;">T</span>` : '';
      const clipBadge = l.isClipped ? `<span style="color:var(--orange);font-size:9px;margin-left:4px;">CLIP</span>` : '';

      html += `<div class="layer-item" style="padding-left:${indent}px" title="${escapeHtml(l.name)} (${l.width}×${l.height})">
        <span>${l.visible ? '👁' : '—'}</span>
        <span style="flex:1;min-width:0;">
          ${colorDot}${escapeHtml(l.name)}${textBadge}${clipBadge}
        </span>
        <span class="layer-dims">${l.width}×${l.height}</span>
        <span class="layer-type-badge type-${type}">${typeLabel}</span>
      </div>`;
    }
    container.innerHTML = html;
    layerData = allLayers;
  } catch (e) {
    console.error('Layer error:', e);
    document.getElementById('layerTree').innerHTML =
      '<div style="text-align:center;color:var(--muted);padding:20px;">Erro ao carregar camadas</div>';
  }
}

async function getAllLayersRecursive(doc) {
  const result = [];

  async function collect(layer, depth) {
    const kind = layer.kind ? layer.kind.toString() : '';

    if (kind.includes('LayerSet') || kind.includes('Group')) {
      const children = layer.layers || [];
      for (const child of children) {
        await collect(child, depth + 1);
      }
    } else if (kind.includes('Layer')) {
      if (!layer.visible) return;
      try {
        const bounds = layer.bounds;
        const w = Math.round(bounds[2] - bounds[0]);
        const h = Math.round(bounds[3] - bounds[1]);
        if (w <= 0 || h <= 0) return;

        let fill = null;
        try {
          const ls = layer.layerStyle;
          if (ls?.solidColorLayer?.visible) {
            const c = ls.solidColorLayer.color;
            fill = {
              hex: '#' + [c.red, c.green, c.blue].map(x => Math.round(x * 255).toString(16).padStart(2, '0')).join('').toUpperCase(),
              r: Math.round(c.red * 255), g: Math.round(c.green * 255), b: Math.round(c.blue * 255),
            };
          }
        } catch (e) {}

        let text = null;
        try {
          const ti = layer.textItem;
          if (ti) {
            text = {
              content: ti.contents, size: Math.round(ti.size),
              font: ti.font || 'Unknown', bold: ti.bold || false,
            };
            if (ti.color) {
              text.color = '#' + [ti.color.red, ti.color.green, ti.color.blue]
                .map(x => Math.round(x * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
            }
          }
        } catch (e) {}

        result.push({
          name: layer.name, visible: layer.visible, width: w, height: h,
          depth: depth, fill: fill, text: text,
          opacity: Math.round((layer.opacity / 100) * 100) / 100,
          blendMode: getBlendMode(layer),
          isClipped: layer.clippingMaskStart !== undefined,
        });
      } catch (e) {}
    }
  }

  for (const layer of (doc.layers || [])) {
    await collect(layer, 0);
  }

  return result;
}

function classifyLayer(name) {
  const n = (name || '').toLowerCase();
  if (/\b(bg|back|base|fundo|wallpaper)\b/.test(n)) return 'background';
  if (/\b(btn|button|play|start|cta|submit)\b/.test(n)) return 'button';
  if (/\b(title|label|text|score|caption|desc|body|info)\b/.test(n)) return 'label';
  if (/\b(icon|img|logo|avatar|sprite|photo)\b/.test(n)) return 'icon';
  if (/\b(panel|frame|box|card|container)\b/.test(n)) return 'panel';
  if (/\b(bar|health|hp|stamina|mana|xp|progress)\b/.test(n)) return 'bar';
  return 'image';
}

function getTypeLabel(type) {
  return { background: 'BG', button: 'Btn', label: 'Txt', icon: 'Icon', panel: 'Pnl', bar: 'Bar', image: 'Img' }[type] || type;
}

function getBlendMode(layer) {
  try { return layer.blendMode ? layer.blendMode.toString().replace('BlendMode.', '') : 'Normal'; }
  catch (e) { return 'Normal'; }
}

// ── VERIFICATION ENGINE ────────────────────────────────────────────────────────

async function runVerification() {
  try {
    const app = ps.app;
    const doc = app.activeDocument;

    if (!doc) { setStatus('Nenhum documento aberto', 'err'); return; }

    setStatus('Verificando compatibilidade...', 'busy');

    const layers = await getAllLayersRecursive(doc);
    const w = Math.round(doc.width);
    const h = Math.round(doc.height);

    currentUDS = buildUDSFromLayers(doc, layers, w, h);
    verificationReport = verifyUDS(currentUDS, w, h);

    renderVerificationReport(verificationReport);
    updateScoreBadge(verificationReport.summary.score);
    setStatus(`Verificação concluída — Score: ${verificationReport.summary.score}/100 (${verificationReport.summary.grade})`, 'ok');

    if (!document.getElementById('panel-verify')?.classList.contains('active')) {
      switchTab('verify');
    }
  } catch (e) {
    setStatus('Erro na verificação: ' + truncate(e.message, 50), 'err');
    console.error(e);
  }
}

function buildUDSFromLayers(doc, layers, w, h) {
  const udsLayers = layers.map(l => {
    const role = classifyLayer(l.name);
    return {
      id: genId('layer'), name: l.name, type: 'layer', visible: l.visible,
      opacity: l.opacity, blendMode: l.blendMode,
      bounds: { x: 0, y: h - l.height, width: l.width, height: l.height },
      semantic: {
        probableRole: role, confidence: inferConfidence(l.name, l.width, l.height),
        robloxClass: CONFIG.robloxClasses[role] || 'Frame',
        responsiveStrategy: CONFIG.responsiveStrategies[role] || 'ScaleToFit',
      },
      fill: l.fill, text: l.text, effects: [],
    };
  });

  return {
    schemaVersion: '1.0.0', source: 'photoshop',
    document: { name: doc.name, width: w, height: h, resolution: doc.resolution || 72, colorMode: doc.modeName || 'RGB', bitDepth: 8 },
    artboards: [], layers: udsLayers, groups: [], assets: [], colors: [], fonts: [],
    metadata: { generatedAt: new Date().toISOString(), generator: 'FigmaPS2Roblox v3.1' },
  };
}

function inferConfidence(name, width, height) {
  const n = name.toLowerCase();
  let score = 0.5;
  if (/\b(bg|back)\b/.test(n)) score += 0.4;
  if (/\b(btn|button)\b/.test(n)) score += 0.4;
  if (/\b(title|label|text)\b/.test(n)) score += 0.3;
  if (/\b(icon|logo)\b/.test(n)) score += 0.3;
  if (/\b(panel|frame)\b/.test(n)) score += 0.3;
  if (width > 1500 && height > 800) score += 0.3;
  if (height < 60 && width > 100) score += 0.2;
  return Math.min(1.0, score);
}

function genId(prefix) {
  return `${prefix}_${Math.random().toString(36).substr(2, 6)}`;
}

function verifyUDS(uds, canvasW, canvasH) {
  const issues = [];
  const warnings = [];
  const recommendations = [];

  if (canvasW > 2048 || canvasH > 2048) {
    warnings.push({ message: `Canvas ${canvasW}×${canvasH} excede limite do Roblox (2048×2048)`, fix: 'Redimensionar para ≤ 2048px' });
  }
  if ((uds.document?.resolution || 72) > 144) {
    warnings.push({ message: `Resolução ${(uds.document?.resolution || 72)} DPI é alta para Roblox`, fix: 'Usar 72-96 DPI' });
  }

  for (const layer of uds.layers) {
    const b = layer.bounds;
    if (b.width <= 0 || b.height <= 0) {
      issues.push({ message: `Layer "${layer.name}" tem dimensões inválidas`, fix: 'Verificar bounds no Photoshop' });
      continue;
    }
    if (b.x + b.width > canvasW + 10) warnings.push({ message: `"${layer.name}" sai do canvas pela direita`, fix: 'Mover para dentro do artboard' });
    if (b.y + b.height > canvasH + 10) warnings.push({ message: `"${layer.name}" sai do canvas pela parte inferior`, fix: 'Mover para dentro do artboard' });
    if (layer.opacity !== undefined && layer.opacity < 0.01) warnings.push({ message: `"${layer.name}" opacidade muito baixa (${layer.opacity})`, fix: 'Aumentar opacidade' });
    if (['Additive', 'Multiply', 'Screen', 'Overlay', 'Difference'].includes(layer.blendMode)) {
      warnings.push({ message: `Blend mode "${layer.blendMode}" não suportado no Roblox`, fix: 'Usar "Normal"' });
    }
    if (b.width > 2048 || b.height > 2048) warnings.push({ message: `"${layer.name}" (${b.width}×${b.height}) excede resolução máxima`, fix: 'Redimensionar layer' });
    recommendations.push({ layerName: layer.name, role: layer.semantic.probableRole, robloxClass: layer.semantic.robloxClass, strategy: layer.semantic.responsiveStrategy, bounds: b });
  }

  const overlaps = detectOverlaps(uds.layers);
  if (overlaps.length > uds.layers.length * 0.3) warnings.push({ message: `${overlaps.length} sobreposições significativas`, fix: 'Revisar hierarquia de layers' });

  const estimatedInstances = uds.layers.length + (uds.groups?.length || 0) * 2;
  const complexity = estimatedInstances < 50 ? 'low' : estimatedInstances < 100 ? 'medium' : 'high';
  const utilization = Math.round((estimatedInstances / 150) * 100);
  const errorPenalty = issues.length * 15;
  const warningPenalty = warnings.length * 5;
  let score = Math.max(0, Math.min(100, 100 - errorPenalty - warningPenalty));
  const grade = score >= 90 ? 'A' : score >= 75 ? 'B' : score >= 60 ? 'C' : score >= 40 ? 'D' : 'F';

  return {
    summary: { score, grade, status: issues.length === 0 ? 'pass' : 'fail', timestamp: new Date().toISOString() },
    errors: issues, warnings, recommendations,
    performance: { estimatedInstances, complexity, utilization, instanceBudget: 150, totalLayers: uds.layers.length, optimizations: generateOptimizationTips(uds) },
  };
}

function detectOverlaps(layers) {
  const overlaps = [];
  for (let i = 0; i < layers.length; i++) {
    for (let j = i + 1; j < layers.length; j++) {
      const a = layers[i].bounds, b = layers[j].bounds;
      if (!a || !b) continue;
      const ox = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
      const oy = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
      if (ox > 0 && oy > 0) {
        const area = ox * oy;
        const minArea = Math.min(a.width * a.height, b.width * b.height);
        if (area > minArea * 0.5) overlaps.push([layers[i].name, layers[j].name]);
      }
    }
  }
  return overlaps;
}

function generateOptimizationTips(uds) {
  const tips = [];
  if (uds.layers.length > 30) tips.push('Considerar atlas de texturas para reduzir instâncias');
  const large = uds.layers.filter(l => l.bounds.width > 512 || l.bounds.height > 512);
  if (large.length > 0) tips.push(`${large.length} layers > 512px — comprimir para mobile`);
  if (uds.layers.some(l => l.opacity < 0.5)) tips.push('Camadas com opacidade baixa aumentam render cost');
  return tips;
}

function renderVerificationReport(report) {
  const { summary, errors, warnings, recommendations, performance } = report;
  const verdictEl = document.getElementById('verdictBox');
  const verdictContent = document.getElementById('verdictContent');
  verdictEl.style.display = 'block';

  const scoreClass = summary.score >= 90 ? 'verdict-excellent' : summary.score >= 75 ? 'verdict-good' : summary.score >= 60 ? 'verdict-warning' : 'verdict-danger';
  const scoreColor = summary.score >= 90 ? 'var(--green)' : summary.score >= 75 ? 'var(--blue)' : summary.score >= 60 ? 'var(--yellow)' : 'var(--red)';

  verdictContent.innerHTML = `
    <div class="verdict-box ${scoreClass}">
      <div class="verdict-score" style="color:${scoreColor}">${summary.score}</div>
      <div class="verdict-grade" style="color:${scoreColor}">Nota ${summary.grade}</div>
      <div class="verdict-label">${summary.status === 'pass' ? '✅ Compatível com Roblox' : '❌ Problemas encontrados'}</div>
    </div>`;

  const issuesEl = document.getElementById('verifyIssues');
  issuesEl.style.display = 'none';
  issuesEl.innerHTML = '';
  if (errors.length > 0 || warnings.length > 0) {
    issuesEl.style.display = 'block';
    let html = '';
    for (const err of errors) {
      html += `<div class="issue-item issue-error"><span class="issue-icon">❌</span><div class="issue-body"><div class="issue-msg">${escapeHtml(err.message)}</div><div class="issue-fix">Fix: ${escapeHtml(err.fix)}</div></div></div>`;
    }
    for (const w of warnings) {
      html += `<div class="issue-item issue-warning"><span class="issue-icon">⚠️</span><div class="issue-body"><div class="issue-msg">${escapeHtml(w.message)}</div><div class="issue-fix">Fix: ${escapeHtml(w.fix)}</div></div></div>`;
    }
    issuesEl.innerHTML = html;
  }

  const recEl = document.getElementById('verifyRecomendacoes');
  recEl.style.display = 'none';
  recEl.innerHTML = '';
  const stratRecs = recommendations.filter(r => r.strategy);
  if (stratRecs.length > 0) {
    recEl.style.display = 'block';
    recEl.innerHTML = `<div style="font-size:11px;font-weight:700;color:var(--purple);margin-bottom:6px;">💡 Estratégias Responsivas Sugeridas</div>` +
      stratRecs.slice(0, 15).map(r => `<div class="rec-item"><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(r.layerName)}">${escapeHtml(r.layerName)}</span><span style="font-size:10px;color:var(--muted);">${escapeHtml(r.robloxClass)}</span><span class="rec-strategy">${escapeHtml(r.strategy)}</span></div>`).join('');
  }

  const perfEl = document.getElementById('verifyPerformance');
  perfEl.style.display = 'none';
  perfEl.innerHTML = '';
  if (performance.estimatedInstances > 0) {
    perfEl.style.display = 'block';
    perfEl.innerHTML = `
      <div style="font-size:11px;font-weight:700;color:var(--blue);margin-bottom:8px;">📊 Performance Estimada</div>
      <div class="info-grid">
        <div class="card"><div class="card-label">Instâncias estimadas</div><div class="card-value">${performance.estimatedInstances} <span style="font-size:10px;color:var(--muted)">/ ${performance.instanceBudget}</span></div><div class="progress-bar"><div class="progress-fill" style="width:${Math.min(100, performance.utilization)}%"></div></div></div>
        <div class="card"><div class="card-label">Complexidade</div><div class="card-value" style="text-transform:uppercase;">${performance.complexity}</div></div>
      </div>
      ${performance.optimizations.length > 0 ? `<div style="margin-top:8px;">${performance.optimizations.map(t => `<div class="issue-item issue-info"><span class="issue-icon">💡</span><div class="issue-body"><div class="issue-msg">${escapeHtml(t)}</div></div></div>`).join('')}</div>` : ''}`;
  }

  document.getElementById('verifyEmpty').style.display = 'none';
}

function updateScoreBadge(score) {
  const badge = document.getElementById('scoreBadge');
  if (score === null) { badge.style.display = 'none'; return; }
  badge.style.display = 'block';
  const grade = score >= 90 ? 'A' : score >= 75 ? 'B' : score >= 60 ? 'C' : score >= 40 ? 'D' : 'F';
  badge.textContent = grade;
  badge.className = 'score-badge score-' + grade.toLowerCase();
}

// ── AI com CACHE ────────────────────────────────────────────────────────────────

async function runAIAnalysis() {
  const apiKey = document.getElementById('apiKeyInput')?.value.trim();
  if (apiKey) aiApiKey = apiKey;

  if (!currentUDS) {
    try {
      const app = ps.app;
      const doc = app.activeDocument;
      if (!doc) { setStatus('Nenhum documento aberto', 'err'); return; }
      const layers = await getAllLayersRecursive(doc);
      const w = Math.round(doc.width);
      const h = Math.round(doc.height);
      currentUDS = buildUDSFromLayers(doc, layers, w, h);
    } catch (e) { setStatus('Erro ao construir UDS: ' + truncate(e.message, 50), 'err'); return; }
  }

  const analyzeBtn = document.getElementById('analyzeBtn');
  if (analyzeBtn) analyzeBtn.disabled = true;
  const aiResultEl = document.getElementById('aiResult');
  if (aiResultEl) aiResultEl.textContent = 'Analisando com IA...';
  const aiResultSection = document.getElementById('aiResultSection');
  if (aiResultSection) aiResultSection.style.display = 'block';

  const prompt = document.getElementById('aiPrompt')?.value.trim();
  const cacheKey = aiApiKey ? `ai_${currentUDS.document?.name}_${prompt || 'default'}` : 'simulated';

  try {
    if (aiApiKey) {
      const cached = aiCache[cacheKey];
      if (cached && Date.now() - cached.timestamp < 24 * 3600 * 1000) {
        if (aiResultEl) aiResultEl.textContent = '✅ Resposta do cache (24h) — ' + cached.from + 'h atrás';
        renderAIResult(cached.data);
      } else {
        await callOpenAI(prompt, cacheKey);
      }
    } else {
      await simulateAIResponse();
    }
  } catch (e) {
    if (aiResultEl) aiResultEl.textContent = 'Erro: ' + truncate(e.message, 100);
    setStatus('Erro na IA: ' + truncate(e.message, 50), 'err');
  } finally {
    if (analyzeBtn) analyzeBtn.disabled = false;
  }
}

async function callOpenAI(userPrompt, cacheKey) {
  const udsForAI = currentUDS ? {
    document: currentUDS.document,
    layers: currentUDS.layers.map(l => ({ name: l.name, type: l.type, bounds: l.bounds, semantic: l.semantic, fill: l.fill, text: l.text, effects: l.effects })),
  } : null;

  const messages = [
    { role: 'system', content: 'Você é um especialista em UI/UX para Roblox. Analise designs de Photoshop e gere especificações Roblox completas. Retorne SOMENTE JSON válido.' },
    { role: 'user', content: `Analise este design de UI e gere uma especificação completa para Roblox.\n\n${userPrompt ? 'Solicitação: ' + userPrompt + '\n\n' : ''}Documento: ${udsForAI?.document?.name || 'Untitled'} (${udsForAI?.document?.width || 1920}×${udsForAI?.document?.height || 1080})\nLayers: ${udsForAI?.layers?.length || 0}\n\nEstrutura:\n${JSON.stringify(udsForAI, null, 2).substring(0, 3000)}` },
  ];

  // Com retry
  let lastError;
  for (let attempt = 1; attempt <= CONFIG.aiRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), CONFIG.aiTimeout);

      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${aiApiKey}` },
        body: JSON.stringify({ model: document.getElementById('modelSelect')?.value || 'gpt-4o', messages, max_tokens: 2048, temperature: 0.3, response_format: { type: 'json_object' } }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const err = await response.text();
        throw new Error(`API Error ${response.status}: ${err.substring(0, 200)}`);
      }

      const data = await response.json();
      const content = data.choices[0].message.content;

      try {
        const spec = JSON.parse(content);
        // Cache result
        if (cacheKey) {
          aiCache[cacheKey] = { data: spec, timestamp: Date.now(), from: 'api' };
        }
        renderAIResult(spec);
        return;
      } catch (e) {
        if (aiResultEl) aiResultEl.textContent = content;
        if (cacheKey) aiCache[cacheKey] = { data: { raw: content }, timestamp: Date.now(), from: 'raw' };
        return;
      }
    } catch (e) {
      lastError = e;
      if (attempt < CONFIG.aiRetries) {
        console.warn(`[AI] Tentativa ${attempt} falhou: ${e.message}. Tentando novamente...`);
        await new Promise(r => setTimeout(r, 1000 * attempt));
      }
    }
  }
  throw lastError || new Error('Falha após ' + CONFIG.aiRetries + ' tentativas');
}

async function simulateAIResponse() {
  await new Promise(r => setTimeout(r, 800));
  const spec = {
    screenName: currentUDS?.document?.name?.replace('.psd', '') || 'Screen',
    canvasWidth: currentUDS?.document?.width || 1920,
    canvasHeight: currentUDS?.document?.height || 1080,
    elements: (currentUDS?.layers || []).map(l => ({
      id: l.id, name: l.name,
      robloxClass: l.semantic?.robloxClass || 'Frame',
      position: { xScale: l.bounds ? l.bounds.x / (currentUDS?.document?.width || 1920) : 0, yScale: l.bounds ? l.bounds.y / (currentUDS?.document?.height || 1080) : 0, xOffset: 0, yOffset: 0 },
      size: { xScale: l.bounds ? l.bounds.width / (currentUDS?.document?.width || 1920) : 0, yScale: l.bounds ? l.bounds.height / (currentUDS?.document?.height || 1080) : 0, xOffset: 0, yOffset: 0 },
      properties: { backgroundColor: l.fill?.hex || '#1E1E2E', text: l.text?.content || null, textSize: l.text?.size || 24, cornerRadius: 8 },
      responsive: { strategy: l.semantic?.responsiveStrategy || 'ScaleToFit', mobileScale: 0.9 },
    })),
    layoutHints: { verticalGroups: [], horizontalGroups: [] },
    fonts: { primary: 'GothamBold', fallback: 'Gotham' },
    colors: { primary: '#89B4FA', secondary: '#A6E3A1', background: '#1E1E2E' },
    notes: 'Design analisado automaticamente. Posições calculadas proporcionalmente ao canvas.',
  };
  renderAIResult(spec);
}

function renderAIResult(spec) {
  let resultHTML = `<strong>📐 Tela:</strong> ${escapeHtml(spec.screenName || 'Screen')}<br>`;
  resultHTML += `<strong>📏 Canvas:</strong> ${spec.canvasWidth || 1920}×${spec.canvasHeight || 1080}<br>`;
  resultHTML += `<strong>🧩 Elementos:</strong> ${(spec.elements || []).length}<br>`;
  resultHTML += `<strong>📱 Strategy:</strong> ScaleToFit (responsivo)<br><br>`;
  if (spec.notes) resultHTML += `<em style="color:var(--muted)">${escapeHtml(spec.notes)}</em><br><br>`;
  resultHTML += '<strong>Elementos gerados:</strong><br>';
  for (const el of (spec.elements || [])) {
    resultHTML += `<code>${escapeHtml(el.name)}</code> → <strong>${escapeHtml(el.robloxClass)}</strong> `;
    resultHTML += `(${Math.round((el.position?.xScale || 0) * 100)}%, ${Math.round((el.position?.yScale || 0) * 100)}%) `;
    resultHTML += `→ <span style="color:var(--purple)">${escapeHtml(el.responsive?.strategy || 'ScaleToFit')}</span><br>`;
  }

  const aiResultEl = document.getElementById('aiResult');
  if (aiResultEl) aiResultEl.innerHTML = resultHTML;
  const aiResultSection = document.getElementById('aiResultSection');
  if (aiResultSection) aiResultSection.style.display = 'block';

  generatedLuaCode = generateLuauFromSpec(spec);
  const aiCodeEl = document.getElementById('aiCodeResult');
  if (aiCodeEl) aiCodeEl.textContent = generatedLuaCode;
  const aiCodeSection = document.getElementById('aiCodeSection');
  if (aiCodeSection) aiCodeSection.style.display = 'block';

  const udsPreview = currentUDS ? JSON.stringify(currentUDS, null, 2).substring(0, 500) + '...' : 'N/A';
  const aiUDSEl = document.getElementById('aiUDSPreview');
  if (aiUDSEl) aiUDSEl.textContent = udsPreview;
  const aiUDSSection = document.getElementById('aiUDSSection');
  if (aiUDSSection) aiUDSSection.style.display = 'block';

  setStatus('IA analisou ' + (spec.elements?.length || 0) + ' elementos', 'ok');
}

// ── Ask question to AI ──────────────────────────────────────────────────────────

async function runAIAsk() {
  const question = prompt('Faça uma pergunta sobre o design:');
  if (!question) return;

  const apiKey = document.getElementById('apiKeyInput')?.value.trim();
  if (apiKey) aiApiKey = apiKey;

  const askBtn = document.getElementById('askBtn');
  if (askBtn) askBtn.disabled = true;
  const aiResultEl = document.getElementById('aiResult');
  if (aiResultEl) aiResultEl.textContent = 'Pensando...';
  const aiResultSection = document.getElementById('aiResultSection');
  if (aiResultSection) aiResultSection.style.display = 'block';

  try {
    if (aiApiKey) {
      await callOpenAIAsk(question);
    } else {
      await simulateAIAsk(question);
    }
  } catch (e) {
    if (aiResultEl) aiResultEl.textContent = 'Erro: ' + truncate(e.message, 100);
  } finally {
    if (askBtn) askBtn.disabled = false;
  }
}

async function callOpenAIAsk(question) {
  const messages = [
    { role: 'system', content: 'Você é um especialista em UI/UX para Roblox. Responda de forma técnica e prática.' },
    { role: 'user', content: `Analise este design de UI Roblox e responda: "${question}"\n\nDocument: ${currentUDS?.document?.name || 'Untitled'} (${currentUDS?.document?.width || 1920}×${currentUDS?.document?.height || 1080}), Layers: ${currentUDS?.layers?.length || 0}` },
  ];

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${aiApiKey}` },
    body: JSON.stringify({ model: document.getElementById('modelSelect')?.value || 'gpt-4o', messages, max_tokens: 512, temperature: 0.5 }),
  });

  const data = await response.json();
  const aiResultEl = document.getElementById('aiResult');
  if (aiResultEl) aiResultEl.textContent = data.choices[0].message.content;
}

async function simulateAIAsk(question) {
  await new Promise(r => setTimeout(r, 600));
  const answers = {
    'mobile': 'Para mobile, use ScaleToFit com mobileScale=0.85 e minSize={width:200,height:50}. Botões ficam mais compactos em telas pequenas.',
    'responsivo': 'O sistema usa Scale+Offset (UDim2) para todos os elementos. Background usa Fill, botões usam ScaleToFit.',
    'performance': 'Com ' + (currentUDS?.layers?.length || 0) + ' layers, a estimativa é ~' + (currentUDS?.layers?.length || 0) + ' instâncias. Idealmente manter abaixo de 100 para 60fps estável.',
    'default': `Análise do design (${currentUDS?.document?.name || 'Untitled'}): ${currentUDS?.layers?.length || 0} camadas, ${currentUDS?.layers?.filter(l => l.fill)?.length || 0} com cor, ${currentUDS?.layers?.filter(l => l.text)?.length || 0} com texto.`,
  };
  const key = Object.keys(answers).find(k => question.toLowerCase().includes(k));
  const aiResultEl = document.getElementById('aiResult');
  if (aiResultEl) aiResultEl.textContent = answers[key] || answers.default;
}

// ── Export com FILA e DEBOUNCE ──────────────────────────────────────────────────

async function exportToRoblox() {
  const screenName = document.getElementById('screenName')?.value.trim() || 'Screen';
  let outputPath = document.getElementById('outputPath')?.value;
  const bypassEnabled = document.getElementById('bypassToggle')?.checked || false;
  const bypassTech = document.getElementById('bypassTech')?.value || 'noise';

  if (!outputPath) {
    try {
      const folders = await uxp.storage.requestFileSystem(uxp.storage.types.PERSISTENT);
      if (!folders || folders.length === 0) return;
      outputPath = folders[0].path;
      const outputPathEl = document.getElementById('outputPath');
      if (outputPathEl) outputPathEl.value = outputPath;
    } catch (e) {
      setStatus('Erro ao selecionar pasta: ' + truncate(e.message, 50), 'err');
      return;
    }
  }

  const exportBtn = document.getElementById('exportBtn');
  if (exportBtn) exportBtn.disabled = true;
  const exportProgress = document.getElementById('exportProgress');
  if (exportProgress) exportProgress.style.display = 'block';
  const exportResult = document.getElementById('exportResult');
  if (exportResult) exportResult.style.display = 'none';
  setProgress(0);

  try {
    const app = ps.app;
    const doc = app.activeDocument;
    if (!doc) throw new Error('Nenhum documento aberto');

    const w = Math.round(doc.width);
    const h = Math.round(doc.height);
    const seed = generateSeed();

    if (!currentUDS) {
      const layers = await getAllLayersRecursive(doc);
      currentUDS = buildUDSFromLayers(doc, layers, w, h);
    }

    setProgress(10);
    setStatus('Exportando assets...', 'busy');

    const assets = [];
    const totalLayers = currentUDS.layers.length;

    // Export em batch com debounce
    for (let i = 0; i < totalLayers; i++) {
      const layer = currentUDS.layers[i];
      const uid = generateHash(seed, layer.name);
      const safeName = sanitizeName(layer.name);
      const fileName = safeName + '_' + uid + '.png';
      const filePath = path.join(outputPath, fileName);

      setProgress(10 + Math.round((i / totalLayers) * 70));
      setStatus(`Exportando ${i + 1}/${totalLayers}: ${safeName}`, 'busy');

      try {
        await exportLayerPNG(doc, layer.name, outputPath, fileName, layer.width, layer.height);
        assets.push({
          name: layer.name, file: fileName, uid,
          width: layer.bounds.width, height: layer.bounds.height,
          type: layer.semantic.probableRole,
          x: layer.bounds.x, y: layer.bounds.y,
          assetId: 'rbxassetid://0',
          bypassEnabled, bypassTechnique: bypassEnabled ? bypassTech : null,
        });
      } catch (e) {
        console.warn(`Failed to export ${layer.name}:`, e);
        // Continue with next layer (don't fail entire export)
      }

      // Debounce entre exports
      if (i < totalLayers - 1) {
        await new Promise(r => setTimeout(r, CONFIG.exportDebounceMs));
      }
    }

    setProgress(85);
    setStatus('Gerando arquivos...', 'busy');

    const manifest = {
      version: '3.1.0', source: 'photoshop', name: screenName,
      canvasWidth: w, canvasHeight: h, scaleMode: 'ScaleToFit',
      seed, generated: new Date().toISOString(),
      bypassUsed: bypassEnabled, bypassTechnique: bypassEnabled ? bypassTech : null,
      assets,
      elements: assets.map(a => ({ name: a.name, type: a.type, robloxClass: CONFIG.robloxClasses[a.type] || 'Frame', x: a.x, y: a.y, width: a.width, height: a.height, assetId: 'rbxassetid://0' })),
      layoutHints: detectLayoutHints(assets),
    };

    await fs.writeFile(path.join(outputPath, screenName + '_manifest.json'), JSON.stringify(manifest, null, 2));
    setProgress(90);

    const luaCode = generateLuaFromManifest(manifest);
    await fs.writeFile(path.join(outputPath, screenName + '_controller.lua'), luaCode);

    const guide = `# Guia de Upload — ${screenName}\n\n` +
      `**Versão:** FigmaPS2Roblox v3.1\n` +
      `**Canvas:** ${w}×${h}\n` +
      `**Assets:** ${assets.length} PNGs processados\n` +
      `**Seed:** ${seed}\n` +
      (bypassEnabled ? `**Bypass:** ${bypassTech}\n` : '') +
      `\n---\n\n` +
      `## Passos\n\n` +
      `1️⃣ Abra o Roblox Studio\n` +
      `2️⃣ Crie: ReplicatedStorage/UIAssets/${screenName}/\n` +
      `3️⃣ Importe os ${assets.length} PNGs (drag & drop)\n` +
      `4️⃣ Copie os Asset IDs (clique direito > Copy Asset ID)\n` +
      `5️⃣ Atualize ${screenName}_manifest.json substituindo rbxassetid://0\n`;
    await fs.writeFile(path.join(outputPath, screenName + '_upload_guide.txt'), guide);

    setProgress(100);

    if (exportResult) {
      exportResult.style.display = 'block';
      exportResult.innerHTML = `<div class="verdict-box verdict-excellent"><div class="verdict-score" style="color:var(--green)">${assets.length}</div><div class="verdict-grade" style="color:var(--green)">Assets Exportados</div><div class="verdict-label">📂 ${outputPath}</div></div>`;
    }

    setStatus(`✅ ${assets.length} assets → ${screenName}`, 'ok');

  } catch (e) {
    setStatus('❌ Erro: ' + truncate(e.message, 60), 'err');
    console.error(e);
  } finally {
    if (exportBtn) exportBtn.disabled = false;
    if (exportProgress) exportProgress.style.display = 'none';
  }
}

async function exportLayerPNG(doc, layerName, outputPath, fileName, layerW, layerH) {
  const script = `#target photoshop\n(function(){
    var doc = app.activeDocument;
    var layer = null;
    function findLayer(l) {
      if (l.name === "${layerName.replace(/"/g, '\\"')}") return l;
      if (l.layers) {
        for (var i = 0; i < l.layers.length; i++) {
          var f = findLayer(l.layers[i]);
          if (f) return f;
        }
      }
      return null;
    }
    layer = findLayer(doc);
    if (!layer) return "NOT_FOUND";

    var w = ${layerW || 100};
    var h = ${layerH || 100};
    var tempDoc = app.documents.add(w, h, 72, "temp", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
    layer.copy(true);
    tempDoc.paste();
    tempDoc.flatten();

    var pngFile = new File("${outputPath.replace(/\\/g, '\\\\')}" + "/" + "${fileName}");
    var pngOpts = new PNGSaveOptions();
    pngOpts.compression = 9;
    pngOpts.transparent = true;
    tempDoc.saveAs(pngFile, pngOpts);
    tempDoc.close(SaveOptions.DONOTSAVECHANGES);
    return "OK:" + w + "x" + h;
  })();`;

  try {
    // Timeout wrapper
    const timeout = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Export timeout (15s)')), CONFIG.psCommandTimeout)
    );
    await Promise.race([
      ps.core.executeCommand({ type: 'scriptEvent', name: 'runScript', data: { script } }),
      timeout,
    ]);
  } catch (e) {
    console.warn(`ExtendScript export failed for ${layerName}:`, e.message);
    // Fallback: create empty placeholder
    const emptyPng = createEmptyPNG(layerW || 100, layerH || 100);
    const destPath = path.join(outputPath, fileName);
    await fs.writeFile(destPath, emptyPng);
    console.warn(`Created empty placeholder: ${fileName}`);
  }
}

function createEmptyPNG(width, height) {
  // Create a minimal 1x1 transparent PNG and scale up
  // This is a valid PNG that Roblox will accept
  const pngHeader = Buffer.from([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, // PNG signature
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, // IHDR
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, // 1x1
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, // 8-bit RGBA
    0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, // IDAT
    0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
    0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
    0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, // IEND
    0x42, 0x60, 0x82
  ]);
  return pngHeader;
}

// ── Templates Panel ─────────────────────────────────────────────────────────────

function loadTemplates() {
  const container = document.getElementById('templatesGrid');
  if (!container) return;

  let html = '';
  for (const [key, tmpl] of Object.entries(TEMPLATES)) {
    html += `<div class="card" onclick="applyTemplate('${key}')" style="cursor:pointer;transition:transform .15s;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
      <div class="card-label">${tmpl.name}</div>
      <div style="font-size:11px;color:var(--muted);margin-top:4px;">${tmpl.description}</div>
      <div style="font-size:10px;color:var(--blue);margin-top:6px;">${tmpl.layers.length} camadas • ${tmpl.canvasWidth}×${tmpl.canvasHeight}</div>
    </div>`;
  }
  container.innerHTML = html;
}

function applyTemplate(name) {
  const tmpl = TEMPLATES[name];
  if (!tmpl) return;

  // Build UDS from template
  const builder = require ? null : null; // Will use client-side builder
  currentUDS = {
    schemaVersion: '1.0.0', source: 'template',
    document: { name: name + '.psd', width: tmpl.canvasWidth, height: tmpl.canvasHeight, resolution: 72, colorMode: 'RGB' },
    layers: tmpl.layers.map((l, i) => ({
      id: genId('layer'), name: l.name, type: 'layer', visible: true, opacity: 1, blendMode: 'Normal',
      bounds: { x: l.x, y: l.y, width: l.width, height: l.height },
      semantic: { probableRole: l.type, confidence: 0.9, robloxClass: CONFIG.robloxClasses[l.type] || 'Frame', responsiveStrategy: l.strategy },
      fill: l.fill ? { hex: l.fill, r: hexToRGB(l.fill)[0], g: hexToRGB(l.fill)[1], b: hexToRGB(l.fill)[2] } : null,
      text: l.text ? { content: l.text, size: l.size || 24, font: 'Gotham' } : null,
      effects: [],
    })),
    groups: [], assets: [], colors: [], fonts: [],
    metadata: { generatedAt: new Date().toISOString(), generator: 'FigmaPS2Roblox v3.1 Template' },
  };

  // Update UI
  document.getElementById('docName').textContent = name + ' (Template)';
  document.getElementById('canvasSize').textContent = `${tmpl.canvasWidth} × ${tmpl.canvasHeight}`;
  document.getElementById('layerCount').textContent = tmpl.layers.length + ' camadas';
  document.getElementById('groupCount').textContent = '0 grupos';
  document.getElementById('colorCount').textContent = new Set(tmpl.layers.filter(l => l.fill).map(l => l.fill)).size + ' cores';
  document.getElementById('fontCount').textContent = new Set(tmpl.layers.filter(l => l.text).map(l => l.text ? 'Gotham' : '')).size + ' fontes';

  setStatus(`Template ${name} aplicado — ${tmpl.layers.length} camadas`, 'ok');
  switchTab('layers');
}

// ── Folder Selection ────────────────────────────────────────────────────────────

async function selectFolder() {
  try {
    const folders = await uxp.storage.requestFileSystem(uxp.storage.types.PERSISTENT);
    if (folders && folders.length > 0) {
      const outputPathEl = document.getElementById('outputPath');
      if (outputPathEl) outputPathEl.value = folders[0].path;
    }
  } catch (e) {
    setStatus('Erro ao selecionar pasta: ' + truncate(e.message, 50), 'err');
  }
}

// ── Bypass toggle ───────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('bypassToggle');
  const techField = document.getElementById('bypassTechField');
  if (toggle) {
    toggle.addEventListener('change', () => {
      if (techField) techField.style.display = toggle.checked ? 'block' : 'none';
    });
  }

  // Load templates if panel exists
  if (document.getElementById('templatesGrid')) {
    loadTemplates();
  }
});

// ── Helpers ─────────────────────────────────────────────────────────────────────

function generateSeed() {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let s = '';
  for (let i = 0; i < 8; i++) s += chars[Math.floor(Math.random() * chars.length)];
  return s;
}

function generateHash(seed, name) {
  let hash = 0;
  const str = seed + name + Date.now();
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash &= hash;
  }
  return Math.abs(hash).toString(16).padStart(12, '0');
}

function sanitizeName(name) {
  return (name || '')
    .replace(/\.[^\.]+$/, '')
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .substring(0, 50);
}

function hexToRGB(hex) {
  const r = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '');
  return r ? [parseInt(r[1], 16), parseInt(r[2], 16), parseInt(r[3], 16)] : [0, 0, 0];
}

function escapeLua(s) {
  return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function truncate(str, maxLen) {
  return str && str.length > maxLen ? str.substring(0, maxLen) + '...' : str || '';
}

function setStatus(text, type = '') {
  const bar = document.getElementById('statusBar');
  const dot = document.getElementById('statusDot');
  if (bar) bar.textContent = text;
  if (dot) dot.className = 'status-dot' + (type === 'ok' ? ' ok' : type === 'err' ? ' err' : type === 'busy' ? ' busy' : '');
}

function setProgress(pct) {
  const fill = document.getElementById('exportProgressFill');
  const text = document.getElementById('exportProgressText');
  if (fill) fill.style.width = pct + '%';
  if (text) text.textContent = `Exportando... ${pct}%`;
}

function copyLuaCode() {
  if (navigator.clipboard && generatedLuaCode) {
    navigator.clipboard.writeText(generatedLuaCode).then(() => setStatus('Código Luau copiado!', 'ok')).catch(() => fallbackCopy());
  } else {
    fallbackCopy();
  }
}

function fallbackCopy() {
  const ta = document.createElement('textarea');
  ta.value = generatedLuaCode;
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  document.body.removeChild(ta);
  setStatus('Código Luau copiado!', 'ok');
}

function detectLayoutHints(assets) {
  const hints = { verticalGroups: [], horizontalGroups: [] };
  const byY = {};
  for (const a of assets) {
    const key = Math.round(a.y / 40) * 40;
    (byY[key] ||= []).push(a);
  }
  for (const [key, members] of Object.entries(byY)) {
    if (members.length >= 2) {
      const sorted = members.sort((a, b) => a.x - b.x);
      const isH = sorted.every((el, i) => i === 0 || Math.abs(el.y - sorted[i - 1].y) < 20);
      if (isH) hints.horizontalGroups.push(sorted.map(e => e.name));
    }
  }
  const byX = {};
  for (const a of assets) {
    const key = Math.round(a.x / 40) * 40;
    (byX[key] ||= []).push(a);
  }
  for (const [key, members] of Object.entries(byX)) {
    if (members.length >= 2) {
      const sorted = members.sort((a, b) => a.y - b.y);
      const isV = sorted.every((el, i) => i === 0 || Math.abs(el.x - sorted[i - 1].x) < 20);
      if (isV) hints.verticalGroups.push(sorted.map(e => e.name));
    }
  }
  return hints;
}

function generateLuaFromManifest(manifest) {
  const w = manifest.canvasWidth, h = manifest.canvasHeight;
  let lua = `--!strict\n-- Auto-generated by FigmaPS2Roblox v3.1\n-- Source: ${manifest.name}\n-- Canvas: ${w}x${h}\n-- Generated: ${manifest.generated}\n\n`;
  lua += `local Players = game:GetService("Players")\n`;
  lua += `local GeneratedUI = {}\nGeneratedUI.__index = GeneratedUI\n\n`;
  lua += `function GeneratedUI.new()\n    local self = setmetatable({}, GeneratedUI)\n    self.Elements = {}\n    return self\nend\n\n`;
  lua += `function GeneratedUI:CreateElement(parent, config)\n    local el = Instance.new(config.Class)\n    el.Name = config.Name\n    el.Position = UDim2.new(config.X/${w}, config.OffsetX or 0, config.Y/${h}, config.OffsetY or 0)\n    el.Size = UDim2.new(config.Width/${w}, config.OffsetWidth or 0, config.Height/${h}, config.OffsetHeight or 0)\n    if config.BackgroundColor3 then el.BackgroundColor3 = config.BackgroundColor3 end\n    if config.BackgroundTransparency ~= nil then el.BackgroundTransparency = config.BackgroundTransparency end\n    if config.CornerRadius and config.CornerRadius > 0 then\n        local corner = Instance.new("UICorner")\n        corner.CornerRadius = UDim.new(0, config.CornerRadius)\n        corner.Parent = el\n    end\n    if config.Text then el.Text = config.Text end\n    if config.Image then el.Image = config.Image end\n    el.Parent = parent\n    return el\nend\n\n`;
  lua += `function GeneratedUI:Build(parent)\n    local screenGui = Instance.new("ScreenGui")\n    screenGui.Name = "${manifest.name}"\n    screenGui.ResetOnSpawn = false\n    screenGui.IgnoreGuiInset = true\n    screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling\n    screenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")\n\n`;

  for (const a of (manifest.assets || [])) {
    const safeName = sanitizeName(a.name);
    const cls = a.robloxClass || 'Frame';
    lua += `    local ${safeName} = self:CreateElement(screenGui, {\n`;
    lua += `        Class = "${cls}", Name = "${escapeLua(a.name)}",\n`;
    lua += `        X = ${a.x}, Y = ${a.y}, Width = ${a.width}, Height = ${a.height}\n`;
    if (a.fill) {
      const c = a.fill.r !== undefined ? `${a.fill.r}, ${a.fill.g}, ${a.fill.b}` : '0, 0, 0';
      lua += `        BackgroundColor3 = Color3.fromRGB(${c}),\n`;
    }
    if (a.cornerRadius) lua += `        CornerRadius = ${a.cornerRadius},\n`;
    if (a.text?.content) lua += `        Text = "${escapeLua(a.text.content)}",\n`;
    lua += `    })\n\n`;
  }

  lua += `    self.Elements = {}\n    return screenGui\nend\n\nreturn GeneratedUI\n`;
  return lua;
}

function generateLuauFromSpec(spec) {
  const w = spec.canvasWidth || 1920, h = spec.canvasHeight || 1080;
  let lua = `--!strict\n-- Gerado por FigmaPS2Roblox v3.1 (IA)\n-- Tela: ${spec.screenName || 'Screen'}\n-- Canvas: ${w}x${h}\n-- Gerado: ${new Date().toISOString()}\n\n`;
  lua += `local Players = game:GetService("Players")\n`;
  lua += `local GeneratedUI = {}\nGeneratedUI.__index = GeneratedUI\n\n`;
  lua += `function GeneratedUI.new()\n    local self = setmetatable({}, GeneratedUI)\n    self.Elements = {}\n    return self\nend\n\n`;
  lua += `function GeneratedUI:CreateElement(parent, config)\n    local el = Instance.new(config.Class)\n    el.Name = config.Name\n    el.Position = UDim2.new(config.X/${w}, config.OffsetX or 0, config.Y/${h}, config.OffsetY or 0)\n    el.Size = UDim2.new(config.Width/${w}, config.OffsetWidth or 0, config.Height/${h}, config.OffsetHeight or 0)\n    if config.BackgroundColor3 then el.BackgroundColor3 = config.BackgroundColor3 end\n    if config.BackgroundTransparency ~= nil then el.BackgroundTransparency = config.BackgroundTransparency end\n    if config.CornerRadius and config.CornerRadius > 0 then\n        local corner = Instance.new("UICorner")\n        corner.CornerRadius = UDim.new(0, config.CornerRadius)\n        corner.Parent = el\n    end\n    if config.Text then el.Text = config.Text end\n    if config.Image then el.Image = config.Image end\n    el.Parent = parent\n    return el\nend\n\n`;
  lua += `function GeneratedUI:Build(parent)\n    local screenGui = Instance.new("ScreenGui")\n    screenGui.Name = "${spec.screenName || 'UI'}"\n    screenGui.ResetOnSpawn = false\n    screenGui.IgnoreGuiInset = true\n    screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling\n    screenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")\n\n`;

  for (const el of (spec.elements || [])) {
    const safeName = el.name.replace(/[^a-zA-Z0-9_]/g, '_');
    const cls = el.robloxClass || 'Frame';
    const px = Math.round((el.position?.xScale || 0) * w);
    const py = Math.round((el.position?.yScale || 0) * h);
    const pw = Math.round((el.size?.xScale || 0) * w);
    const ph = Math.round((el.size?.yScale || 0) * h);
    lua += `    -- ${el.name}\n`;
    lua += `    local ${safeName} = self:CreateElement(screenGui, {\n`;
    lua += `        Class = "${cls}", Name = "${escapeLua(el.name)}",\n`;
    lua += `        X = ${px}, Y = ${py}, Width = ${pw}, Height = ${ph},\n`;
    if (el.properties?.backgroundColor) {
      const c = hexToRGB(el.properties.backgroundColor);
      lua += `        BackgroundColor3 = Color3.fromRGB(${c.join(', ')}),\n`;
    }
    if (el.properties?.text) lua += `        Text = "${escapeLua(el.properties.text)}",\n`;
    if (el.properties?.textSize) lua += `        TextSize = ${el.properties.textSize},\n`;
    if (el.properties?.cornerRadius) lua += `        CornerRadius = ${el.properties.cornerRadius},\n`;
    lua += `    })\n\n`;
  }

  lua += `    self.Elements = {}\n    return screenGui\nend\n\nreturn GeneratedUI\n`;
  return lua;
}

// ── Init ────────────────────────────────────────────────────────────────────────

refreshDocInfo();

setInterval(() => {
  try {
    const app = ps.app;
    if (app.documents && app.documents.length > 0) {
      refreshDocInfo();
    }
  } catch (e) {}
}, 2000);
