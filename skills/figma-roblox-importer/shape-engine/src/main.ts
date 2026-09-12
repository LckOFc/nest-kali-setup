import { showUI, on, emit } from '@create-figma-plugin/utilities';
import { ShapeCommand, ShapeConfig } from './types';

showUI({ width: 420, height: 680, display: 'sidebar' });

on<ShapeCommand>('SHAPE_COMMAND', async (config) => {
  await figma.loadFontAsync([{ family: 'Inter', style: 'Regular' }]);
  await figma.loadFontAsync([{ family: 'Inter', style: 'SemiBold' }]);

  const { type, w, h, sides, fill, stroke, radius, opacity, blendMode } = config;

  let node: SceneNode | null = null;

  switch (type) {
    case 'rectangle':
      node = figma.createRectangle();
      if (node) {
        node.resize(w ?? 200, h ?? 200);
        applyStyle(node, fill, stroke, radius ?? 0, opacity, blendMode);
      }
      break;

    case 'ellipse':
      node = figma.createEllipse();
      if (node) {
        node.resize(w ?? 200, h ?? 200);
        applyStyle(node, fill, stroke, 0, opacity, blendMode);
      }
      break;

    case 'triangle':
      node = figma.createPolygon(3);
      if (node) {
        const size = w ?? 200;
        node.resize(size, size);
        node.x = figma.viewport.center.x - size / 2;
        node.y = figma.viewport.center.y - size / 2;
        applyStyle(node, fill, stroke, 0, opacity, blendMode);
      }
      break;

    case 'polygon':
      node = figma.createPolygon(sides ?? 6);
      if (node) {
        const size = w ?? 200;
        node.resize(size, size);
        node.x = figma.viewport.center.x - size / 2;
        node.y = figma.viewport.center.y - size / 2;
        applyStyle(node, fill, stroke, 0, opacity, blendMode);
      }
      break;

    case 'star':
      node = figma.createStar();
      if (node) {
        const size = w ?? 200;
        node.resize(size, size);
        node.x = figma.viewport.center.x - size / 2;
        node.y = figma.viewport.center.y - size / 2;
        applyStyle(node, fill, stroke, 0, opacity, blendMode);
      }
      break;

    case 'line':
      node = figma.createLine();
      if (node) {
        node.resize(w ?? 200, h ?? 2);
        node.x = figma.viewport.center.x - (w ?? 200) / 2;
        node.y = figma.viewport.center.y - 1;
        applyStyle(node, fill ?? { type: 'SOLID', color: { r: 0, g: 0, b: 0, a: 1 } }, stroke, 0, opacity ?? 1, blendMode);
      }
      break;

    case 'vector':
      node = figma.createVector();
      if (node) {
        const size = w ?? 200;
        node.resize(size, size);
        node.x = figma.viewport.center.x - size / 2;
        node.y = figma.viewport.center.y - size / 2;

        // Default square vector path
        node.vectorPaths = [{
          windingRule: 'EVENODD',
          data: 'M0,0 L1,0 L1,1 L0,1 Z'
        }];
        applyStyle(node, fill, stroke, 0, opacity, blendMode);
      }
      break;

    case 'frame':
      node = figma.createFrame();
      if (node) {
        node.resize(w ?? 400, h ?? 300);
        node.x = figma.viewport.center.x - (w ?? 400) / 2;
        node.y = figma.viewport.center.y - (h ?? 300) / 2;
        applyStyle(node, fill, stroke, radius ?? 0, opacity, blendMode);
      }
      break;

    case 'component':
      node = figma.createComponent();
      if (node) {
        node.resize(w ?? 200, h ?? 200);
        applyStyle(node, fill, stroke, radius ?? 0, opacity, blendMode);
      }
      break;
  }

  if (node) {
    node.name = config.name || type;
    emit('SHAPE_CREATED', { id: node.id, type: node.type, name: node.name });
    figma.notify(`✅ ${type} criado!`);
  } else {
    figma.notify('❌ Erro ao criar shape');
  }

  figma.closePlugin();
});

function applyStyle(
  node: SceneNode,
  fill?: Paint | null,
  stroke?: Paint | null,
  cornerRadius?: number,
  opacity?: number,
  blendMode?: string
) {
  if (fill !== undefined && 'fills' in node) {
    (node as RectangleMixin & SceneNode).fills = fill ? [fill] : [];
  }
  if (stroke !== undefined && 'strokes' in node) {
    (node as RectangleMixin & SceneNode).strokes = stroke ? [stroke] : [];
  }
  if (cornerRadius !== undefined && 'cornerRadius' in node) {
    (node as RectangleMixin & SceneNode).cornerRadius = cornerRadius;
  }
  if (opacity !== undefined && 'opacity' in node) {
    (node as SceneNode).opacity = opacity;
  }
  if (blendMode && 'blendMode' in node) {
    (node as SceneNode).blendMode = blendMode as BlendMode;
  }
}
