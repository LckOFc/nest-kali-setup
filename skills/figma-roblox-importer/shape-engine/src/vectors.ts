import { showUI, on } from '@create-figma-plugin/utilities';
import { rectPath, circlePath, trianglePath, polygonPath, starPath, heartPath, arrowPath } from './types';

showUI({ width: 420, height: 620, display: 'sidebar' });

// ─── Edit Vectors ────────────────────────────────────────────────────────────

on<'VECTOR_NEW'>(async (event) => {
  const { shape, size } = event.data;
  const s = size || 200;

  let pathStr = '';
  switch (shape) {
    case 'rect':
      pathStr = rectPath(0, 0, s, s, 0).data;
      break;
    case 'rounded_rect':
      pathStr = rectPath(0, 0, s, s, s * 0.15).data;
      break;
    case 'circle':
      pathStr = circlePath(s / 2, s / 2, s / 2, s / 2).data;
      break;
    case 'ellipse':
      pathStr = circlePath(s / 2, s / 2, s / 2, s / 4).data;
      break;
    case 'triangle':
      pathStr = trianglePath(0, 0, s, s).data;
      break;
    case 'hexagon':
      pathStr = polygonPath(s / 2, s / 2, s / 2, 6).data;
      break;
    case 'octagon':
      pathStr = polygonPath(s / 2, s / 2, s / 2, 8).data;
      break;
    case 'star5':
      pathStr = starPath(s / 2, s / 2, s / 2, s / 5, 5).data;
      break;
    case 'star6':
      pathStr = starPath(s / 2, s / 2, s / 2, s / 4, 6).data;
      break;
    case 'heart':
      pathStr = heartPath(0, 0, s).data;
      break;
    case 'arrow':
      pathStr = arrowPath(0, 0, s, s).data;
      break;
    default:
      pathStr = rectPath(0, 0, s, s).data;
  }

  const vector = figma.createVector();
  vector.resize(s, s);
  vector.x = figma.viewport.center.x - s / 2;
  vector.y = figma.viewport.center.y - s / 2;
  vector.vectorPaths = [{ windingRule: 'EVENODD', data: pathStr }];
  vector.name = shape;
  vector.select();
  figma.notify(`✅ Vetor "${shape}" criado!`);
  figma.closePlugin();
});

on<'VECTOR_MODIFY'>(async (event) => {
  const { shape, operation } = event.data;
  const node = figma.currentPage.selection[0] as VectorNode | null;
  if (!node || node.type !== 'VECTOR') {
    figma.notify('⚠️ Selecione um VectorNode primeiro');
    figma.closePlugin();
    return;
  }

  const s = node.width || 200;
  let pathStr = node.vectorPaths?.[0]?.data || '';

  switch (operation) {
    case 'corner_round': {
      const r = shape as number;
      pathStr = rectPath(0, 0, s, s, r).data;
      break;
    }
    case 'circle_from_rect': {
      pathStr = circlePath(s / 2, s / 2, s / 2, s / 2).data;
      break;
    }
    case 'ellipse_from_rect': {
      pathStr = circlePath(s / 2, s / 2, s / 2, s / 4).data;
      break;
    }
    case 'triangle_from_rect': {
      pathStr = trianglePath(0, 0, s, s).data;
      break;
    }
    case 'hexagon_from_rect': {
      pathStr = polygonPath(s / 2, s / 2, s / 2, 6).data;
      break;
    }
    case 'heart_from_rect': {
      pathStr = heartPath(0, 0, s).data;
      break;
    }
    case 'star_from_rect': {
      const points = parseInt(shape as string) || 5;
      pathStr = starPath(s / 2, s / 2, s / 2, s / 5, points).data;
      break;
    }
    case 'flatten_selection': {
      const sel = figma.currentPage.selection;
      if (sel.length < 2) {
        figma.notify('⚠️ Selecione 2+ formas primeiro');
        figma.closePlugin();
        return;
      }
      const flat = figma.flatten(sel, figma.currentPage);
      sel.forEach(n => n.remove());
      flat.select();
      figma.notify(`✅ ${sel.length} formas fundidas!`);
      figma.closePlugin();
      return;
    }
    default:
      break;
  }

  node.vectorPaths = [{ windingRule: 'EVENODD', data: pathStr }];
  node.name = operation;
  node.select();
  figma.notify(`✅ Vetor modificado: ${operation}`);
  figma.closePlugin();
});

// ─── Add vertices to vector ─────────────────────────────────────────────────

on<'VECTOR_ADD_POINTS'>(async (event) => {
  const node = figma.currentPage.selection[0] as VectorNode | null;
  if (!node || node.type !== 'VECTOR') {
    figma.notify('⚠️ Selecione um VectorNode');
    figma.closePlugin();
    return;
  }

  const { pattern, count } = event.data;
  const s = node.width || 200;
  const cs = s / (count || 4);

  let data = '';
  switch (pattern) {
    case 'grid': {
      const pts = count || 4;
      const step = s / pts;
      const rows: string[] = [];
      for (let row = 0; row <= pts; row++) {
        const rowPts: string[] = [];
        for (let col = 0; col <= pts; col++) {
          rowPts.push(`${col * step},${row * step}`);
        }
        rows.push(rowPts.join(' L '));
      }
      // Build a mesh-like path (simplified: horizontal lines)
      data = rows.map(r => `M${r}`).join(' M');
      break;
    }
    case 'concentric_circles': {
      const pts = count || 5;
      data = Array.from({ length: pts }, (_, i) => {
        const r = (i + 1) * (s / (pts * 2));
        return circlePath(s / 2, s / 2, r, r).data;
      }).join(' ');
      break;
    }
    case 'radial_lines': {
      const pts = count || 12;
      const center = `${s / 2},${s / 2}`;
      data = Array.from({ length: pts }, (_, i) => {
        const angle = (Math.PI * 2 * i) / pts;
        const ex = s / 2 + (s / 2) * Math.cos(angle);
        const ey = s / 2 + (s / 2) * Math.sin(angle);
        return `M${center} L${ex},${ey}`;
      }).join(' ');
      break;
    }
    default:
      break;
  }

  node.vectorPaths = [{ windingRule: 'EVENODD', data }];
  node.select();
  figma.notify(`✅ ${count || 4} pontos adicionados (padrão: ${pattern})`);
  figma.closePlugin();
});

// ─── SVG Import ──────────────────────────────────────────────────────────────

on<'VECTOR_IMPORT_SVG'>(async (event) => {
  const { svg } = event.data;
  try {
    const node = figma.createNodeFromSvg(svg);
    node.x = figma.viewport.center.x - (node.width ?? 200) / 2;
    node.y = figma.viewport.center.y - (node.height ?? 200) / 2;
    node.name = 'svg_import';
    node.select();
    figma.notify('✅ SVG importado!');
  } catch (e) {
    figma.notify('❌ SVG inválido: ' + e);
  }
  figma.closePlugin();
});
