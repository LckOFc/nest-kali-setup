import { showUI, on, emit } from '@create-figma-plugin/utilities';
import { ShapeCommand, ShapeConfig, solidColor, gradientLinear, gradientRadial } from './types';

showUI({ path: 'ui.html', width: 420, height: 680, display: 'sidebar' });

// ─── Shape creation command ──────────────────────────────────────────────────

on<ShapeCommand>('SHAPE_COMMAND', async (config) => {
  await figma.loadFontAsync([{ family: 'Inter', style: 'Regular' }]);

  const { type, w = 200, h = 200, sides = 6, radius = 0, name } = config;

  let node: SceneNode | null = null;

  switch (type) {
    case 'rectangle':
      node = figma.createRectangle();
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
      }
      break;

    case 'ellipse':
      node = figma.createEllipse();
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
      }
      break;

    case 'triangle':
      node = figma.createPolygon(3);
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
      }
      break;

    case 'polygon':
      node = figma.createPolygon(sides);
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
      }
      break;

    case 'star':
      node = figma.createStar();
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
      }
      break;

    case 'line':
      node = figma.createLine();
      if (node) {
        node.resize(w, 2);
        positionNode(node, w, 2);
      }
      break;

    case 'vector':
      node = figma.createVector();
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
        node.vectorPaths = [{ windingRule: 'EVENODD', data: `M0,0 L${w},0 L${w},${h} L0,${h} Z` }];
      }
      break;

    case 'frame':
      node = figma.createFrame();
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
      }
      break;

    case 'component':
      node = figma.createComponent();
      if (node) {
        node.resize(w, h);
        positionNode(node, w, h);
      }
      break;
  }

  if (node) {
    if (config.fill) node.fills = [config.fill];
    if (config.stroke) node.strokes = [config.stroke];
    if ('cornerRadius' in node && radius !== undefined) {
      (node as RectangleMixin & SceneNode).cornerRadius = radius;
    }
    if (config.opacity !== undefined) node.opacity = config.opacity;
    if (config.blendMode) (node as SceneNode).blendMode = config.blendMode as BlendMode;
    if (name) node.name = name;

    emit('SHAPE_CREATED', { id: node.id, type: node.type, name: node.name });
    node.select();
    figma.notify(`✅ ${type} criado!`);
  }

  figma.closePlugin();
});

function positionNode(node: SceneNode, w: number, h: number) {
  node.x = figma.viewport.center.x - w / 2;
  node.y = figma.viewport.center.y - h / 2;
}
