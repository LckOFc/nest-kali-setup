import { showUI, on } from '@create-figma-plugin/utilities';

showUI({ width: 420, height: 520, display: 'sidebar' });

// ─── Transform Operations ───────────────────────────────────────────────────

on<'TRANSFORM_ROTATE'>(async (event) => {
  const { degrees } = event.data;
  const node = figma.currentPage.selection[0];
  if (!node) {
    figma.notify('⚠️ Selecione uma forma');
    figma.closePlugin();
    return;
  }
  node.rotation = (node.rotation ?? 0) + degrees;
  node.select();
  figma.notify(`🔄 Rotacionado ${degrees}°`);
  figma.closePlugin();
});

on<'TRANSFORM_FLIP_H'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node) { figma.notify('⚠️ Selecione uma forma'); figma.closePlugin(); return; }
  node.scaleX = -(node.scaleX ?? 1);
  node.select();
  figma.notify('↔️ Flip horizontal');
  figma.closePlugin();
});

on<'TRANSFORM_FLIP_V'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node) { figma.notify('⚠️ Selecione uma forma'); figma.closePlugin(); return; }
  node.scaleY = -(node.scaleY ?? 1);
  node.select();
  figma.notify('↕️ Flip vertical');
  figma.closePlugin();
});

on<'TRANSFORM_ALIGN_CENTER'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length === 0) {
    // Center viewport
    figma.notify('Nenhuma forma selecionada — move viewport');
    figma.closePlugin();
    return;
  }
  // Find bounding box of selection
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of nodes) {
    const bb = n.absoluteBoundingBox;
    if (!bb) continue;
    minX = Math.min(minX, bb.x);
    minY = Math.min(minY, bb.y);
    maxX = Math.max(maxX, bb.x + bb.width);
    maxY = Math.max(maxY, bb.y + bb.height);
  }
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  for (const n of nodes) {
    const bb = n.absoluteBoundingBox;
    if (!bb) continue;
    const dx = cx - (bb.x + bb.width / 2);
    const dy = cy - (bb.y + bb.height / 2);
    n.x += dx;
    n.y += dy;
  }
  figma.notify(`🎯 ${nodes.length} formas alinhadas ao centro!`);
  figma.closePlugin();
});

on<'TRANSFORM_ALIGN_GRID'>(async (event) => {
  const { gridSize } = event.data;
  const nodes = figma.currentPage.selection;
  for (const n of nodes) {
    n.x = Math.round(n.x / gridSize) * gridSize;
    n.y = Math.round(n.y / gridSize) * gridSize;
  }
  figma.notify(`📐 ${nodes.length} formas snapped pro grid ${gridSize}px`);
  figma.closePlugin();
});

on<'TRANSFORM_RESIZE'>(async (event) => {
  const { w, h, aspect } = event.data;
  const nodes = figma.currentPage.selection;
  for (const n of nodes) {
    if (aspect && ('width' in n) && ('height' in n)) {
      const ratio = (n as SceneNode & RectangleMixin).width / (n as SceneNode & RectangleMixin).height;
      n.resize(w, w / ratio);
    } else {
      n.resize(w, h);
    }
  }
  figma.notify(`📏 Redimensionado: ${w}×${h}`);
  figma.closePlugin();
});

on<'TRANSFORM_SCALE'>(async (event) => {
  const { factor } = event.data;
  const nodes = figma.currentPage.selection;
  for (const n of nodes) {
    n.rescale(factor);
  }
  figma.notify(`🔍 Escalonado ${factor}x`);
  figma.closePlugin();
});

on<'TRANSFORM_CENTER_TO_VIEWPORT'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length === 0) { figma.notify('⚠️ Selecione uma forma'); figma.closePlugin(); return; }
  for (const n of nodes) {
    const bb = n.absoluteBoundingBox;
    if (!bb) continue;
    n.x = figma.viewport.center.x - bb.width / 2;
    n.y = figma.viewport.center.y - bb.height / 2;
  }
  figma.notify('🎯 Centralizado no viewport');
  figma.closePlugin();
});

on<'TRANSFORM_RANDOMIZE'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length === 0) { figma.notify('⚠️ Selecione formas'); figma.closePlugin(); return; }
  for (const n of nodes) {
    n.x += (Math.random() - 0.5) * 40;
    n.y += (Math.random() - 0.5) * 40;
    n.rotation += (Math.random() - 0.5) * 10;
  }
  figma.notify(`🎲 ${nodes.length} formas randomizadas!`);
  figma.closePlugin();
});

on<'TRANSFORM_EXPORT_SELECTION'>(async (event) => {
  const { format } = event.data;
  const nodes = figma.currentPage.selection;
  if (nodes.length === 0) { figma.notify('⚠️ Selecione algo'); figma.closePlugin(); return; }

  for (const n of nodes) {
    if (format === 'svg') {
      try {
        const svg = await n.exportAsync({ type: 'SVG_STRING' });
        figma.ui.postMessage({ type: 'export_svg', nodeId: n.id, svg });
      } catch (e) {
        figma.notify('❌ Erro no export SVG: ' + e);
      }
    } else if (format === 'png') {
      try {
        const bytes = await n.exportAsync({ type: 'PNG' });
        const b64 = btoa(String.fromCharCode(...bytes));
        figma.ui.postMessage({ type: 'export_png', nodeId: n.id, b64 });
      } catch (e) {
        figma.notify('❌ Erro no export PNG: ' + e);
      }
    }
  }
  figma.closePlugin();
});
