import { showUI, on } from '@create-figma-plugin/utilities';

showUI({ width: 420, height: 500, display: 'sidebar' });

// ─── Boolean Operations ──────────────────────────────────────────────────────

on<'BOOLEAN_UNION'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length < 2) {
    figma.notify('⚠️ Selecione 2+ formas para union');
    figma.closePlugin();
    return;
  }
  try {
    const result = figma.union(nodes as BaseNode[], figma.currentPage);
    result.name = 'union';
    nodes.forEach(n => n.remove());
    result.select();
    figma.notify('✅ Union aplicado!');
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'BOOLEAN_SUBTRACT'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length < 2) {
    figma.notify('⚠️ Selecione 2+ formas para subtract');
    figma.closePlugin();
    return;
  }
  try {
    // First node is the base, rest are subtracted
    const base = nodes[0];
    const others = nodes.slice(1);
    const result = figma.subtract(others, base.parent as BaseNode & ChildrenMixin, base.index);
    result.name = 'subtract';
    nodes.forEach(n => n.remove());
    result.select();
    figma.notify('✅ Subtract aplicado!');
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'BOOLEAN_INTERSECT'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length < 2) {
    figma.notify('⚠️ Selecione 2+ formas para intersect');
    figma.closePlugin();
    return;
  }
  try {
    const result = figma.intersect(nodes as BaseNode[], figma.currentPage);
    result.name = 'intersect';
    nodes.forEach(n => n.remove());
    result.select();
    figma.notify('✅ Intersect aplicado!');
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'BOOLEAN_EXCLUDE'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length < 2) {
    figma.notify('⚠️ Selecione 2+ formas para exclude');
    figma.closePlugin();
    return;
  }
  try {
    const result = figma.exclude(nodes as BaseNode[], figma.currentPage);
    result.name = 'exclude';
    nodes.forEach(n => n.remove());
    result.select();
    figma.notify('✅ Exclude aplicado!');
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

// ─── Layer Management ────────────────────────────────────────────────────────

on<'LAYER_FLATTEN'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length === 0) {
    figma.notify('⚠️ Selecione formas para flatten');
    figma.closePlugin();
    return;
  }
  try {
    const result = figma.flatten(nodes, figma.currentPage);
    result.name = 'flattened';
    nodes.forEach(n => n.remove());
    result.select();
    figma.notify(`✅ ${nodes.length} formas fundidas em vector!`);
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'LAYER_GROUP'>(async () => {
  const nodes = figma.currentPage.selection;
  if (nodes.length < 2) {
    figma.notify('⚠️ Selecione 2+ formas para group');
    figma.closePlugin();
    return;
  }
  try {
    const group = figma.group(nodes, figma.currentPage);
    group.name = 'group';
    group.select();
    figma.notify(`✅ ${nodes.length} formas agrupadas!`);
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'LAYER_UNGROUP'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node || node.type !== 'GROUP') {
    figma.notify('⚠️ Selecione um GROUP para ungroup');
    figma.closePlugin();
    return;
  }
  try {
    const children = figma.ungroup(node as GroupNode);
    children.forEach(c => c.select());
    figma.notify(`✅ ${children.length} formas desagrupadas!`);
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'LAYER_REORDER_UP'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node || !node.parent || !('insertChild' in node.parent)) return;
  const parent = node.parent as DocumentNode | PageNode | FrameNode | GroupNode;
  const idx = node.index;
  if (idx < parent.children.length - 1) {
    const temp = parent.children[idx + 1];
    parent.insertChild(idx, node);
    parent.insertChild(idx + 1, temp);
    figma.notify('↑ Camada movida pra cima');
  }
  figma.closePlugin();
});

on<'LAYER_REORDER_DOWN'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node || node.index <= 0) return;
  const parent = node.parent as DocumentNode | PageNode | FrameNode | GroupNode;
  const idx = node.index;
  const temp = parent.children[idx - 1];
  parent.insertChild(idx, node);
  parent.insertChild(idx - 1, temp);
  figma.notify('↓ Camada movida pra baixo');
  figma.closePlugin();
});

on<'LAYER_DUPLICATE'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node) {
    figma.notify('⚠️ Selecione uma forma para duplicar');
    figma.closePlugin();
    return;
  }
  try {
    const clone = node.clone() as SceneNode;
    clone.x += 20;
    clone.y += 20;
    clone.name = node.name + ' copy';
    clone.select();
    figma.notify(`✅ Duplicado: ${clone.name}`);
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'LAYER_DELETE'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node) {
    figma.notify('⚠️ Selecione uma forma para deletar');
    figma.closePlugin();
    return;
  }
  const name = node.name;
  node.remove();
  figma.notify(`🗑️ ${name} removido`);
  figma.closePlugin();
});

on<'LAYER_OUTLINE_STROKE'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node || !('outlineStroke' in node)) {
    figma.notify('⚠️ Selecione uma forma com stroke');
    figma.closePlugin();
    return;
  }
  try {
    const outline = (node as any).outlineStroke();
    if (outline) {
      outline.select();
      figma.notify('✅ Stroke outlineado!');
    }
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});

on<'LAYER_COMPONENT'>(async () => {
  const node = figma.currentPage.selection[0];
  if (!node) {
    figma.notify('⚠️ Selecione uma forma para virar componente');
    figma.closePlugin();
    return;
  }
  try {
    const comp = figma.createComponentFromNode(node as SceneNode);
    comp.select();
    figma.notify(`✅ "${comp.name}" criado como componente!`);
  } catch (e) {
    figma.notify('❌ Erro: ' + e);
  }
  figma.closePlugin();
});
