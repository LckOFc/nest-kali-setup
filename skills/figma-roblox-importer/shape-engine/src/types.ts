import type { SceneNode, Paint } from '@figma/plugin-typings';

export type ShapeType =
  | 'rectangle'
  | 'ellipse'
  | 'triangle'
  | 'polygon'
  | 'star'
  | 'line'
  | 'vector'
  | 'frame'
  | 'component';

export interface ShapeConfig {
  type: ShapeType;
  w?: number;
  h?: number;
  sides?: number;
  fill?: Paint | null;
  stroke?: Paint | null;
  radius?: number;
  opacity?: number;
  blendMode?: string;
  name?: string;
}

export type ShapeCommand = 'SHAPE_COMMAND';

// ─── Paint helpers ───────────────────────────────────────────────────────────

export function solidColor(r: number, g: number, b: number, a = 1): Paint {
  return { type: 'SOLID', color: { r, g, b, a }, visible: true, opacity: a };
}

export function gradientLinear(
  stops: { pos: number; r: number; g: number; b: number; a?: number }[],
  handleStart: { x: number; y: number } = { x: 0, y: 0 },
  handleEnd: { x: number; y: number } = { x: 1, y: 1 },
  handleTilt: { x: number; y: number } = { x: 0, y: 0 }
): Paint {
  return {
    type: 'GRADIENT_LINEAR',
    gradientHandlePositions: [
      { x: handleStart.x, y: handleStart.y },
      { x: handleEnd.x, y: handleEnd.y },
      { x: handleTilt.x, y: handleTilt.y }
    ],
    gradientStops: stops.map((s) => ({
      position: s.pos,
      color: { r: s.r, g: s.g, b: s.b, a: s.a ?? 1 }
    }))
  };
}

export function gradientRadial(
  stops: { pos: number; r: number; g: number; b: number; a?: number }[],
  center: { x: number; y: number } = { x: 0.5, y: 0.5 },
  radius: number = 0.5
): Paint {
  return {
    type: 'GRADIENT_RADIAL',
    gradientHandlePositions: [
      center,
      { x: center.x + radius, y: center.y },
      { x: center.x, y: center.y + radius }
    ],
    gradientStops: stops.map((s) => ({
      position: s.pos,
      color: { r: s.r, g: s.g, b: s.b, a: s.a ?? 1 }
    }))
  };
}

// ─── Vector path helpers ──────────────────────────────────────────────────────

export type VecPath = {
  windingRule: 'EVENODD' | 'NONZERO';
  data: string;
};

export function rectPath(x: number, y: number, w: number, h: number, r = 0): VecPath {
  if (r <= 0) return { windingRule: 'EVENODD', data: `M${x},${y} L${x + w},${y} L${x + w},${y + h} L${x},${y + h} Z` };
  const rad = Math.min(r, w / 2, h / 2);
  return {
    windingRule: 'EVENODD',
    data: [
      `M${x + rad},${y}`,
      `L${x + w - rad},${y}`,
      `A${rad},${rad} 0 0 1 ${x + w},${y + rad}`,
      `L${x + w},${y + h - rad}`,
      `A${rad},${rad} 0 0 1 ${x + w - rad},${y + h}`,
      `L${x + rad},${y + h}`,
      `A${rad},${rad} 0 0 1 ${x},${y + h - rad}`,
      `L${x},${y + rad}`,
      `A${rad},${rad} 0 0 1 ${x + rad},${y}`,
      'Z'
    ].join(' ')
  };
}

export function circlePath(cx: number, cy: number, rx: number, ry: number): VecPath {
  return {
    windingRule: 'EVENODD',
    data: `M${cx - rx},${cy} A${rx},${ry} 0 1,1 ${cx + rx},${cy} A${rx},${ry} 0 1,1 ${cx - rx},${cy} Z`
  };
}

export function trianglePath(x: number, y: number, w: number, h: number): VecPath {
  return {
    windingRule: 'EVENODD',
    data: `M${x + w / 2},${y} L${x + w},${y + h} L${x},${y + h} Z`
  };
}

export function polygonPath(cx: number, cy: number, radius: number, sides: number): VecPath {
  const pts = Array.from({ length: sides }, (_, i) => {
    const angle = (Math.PI * 2 * i) / sides - Math.PI / 2;
    return `${cx + radius * Math.cos(angle)},${cy + radius * Math.sin(angle)}`;
  });
  return {
    windingRule: 'EVENODD',
    data: `M${pts[0]} L${pts.slice(1).join(' L')} Z`
  };
}

export function starPath(cx: number, cy: number, outerR: number, innerR: number, points: number): VecPath {
  const pts: string[] = [];
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? outerR : innerR;
    const angle = (Math.PI * i) / points - Math.PI / 2;
    pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
  }
  return { windingRule: 'EVENODD', data: `M${pts[0]} L${pts.slice(1).join(' L')} Z` };
}

export function heartPath(x: number, y: number, size: number): VecPath {
  const s = size / 2;
  return {
    windingRule: 'EVENODD',
    data: `M${x + s},${y + s * 0.3}
      C${x + s},${y} ${x},${y} ${x},${y + s * 0.4}
      C${x},${y + s * 0.8} ${x + s},${y + s * 1.2} ${x + s},${y + s * 1.6}
      C${x + s},${y + s * 1.2} ${x + s * 2},${y + s * 0.8} ${x + s * 2},${y + s * 0.4}
      C${x + s * 2},${y} ${x + s * 2},${y} ${x + s},${y + s * 0.3} Z`
  };
}

export function arrowPath(x: number, y: number, w: number, h: number): VecPath {
  const headW = w * 0.3;
  const headH = h * 0.35;
  return {
    windingRule: 'EVENODD',
    data: [
      `M${x},${y + h * 0.4}`,
      `L${x + w * 0.6},${y + h * 0.4}`,
      `L${x + w * 0.6},${y}`,
      `L${x + w},${y + h * 0.5}`,
      `L${x + w * 0.6},${y + h}`,
      `L${x + w * 0.6},${y + h * 0.6}`,
      `L${x},${y + h * 0.6}`,
      'Z'
    ].join(' ')
  };
}

// ─── Texture generators ───────────────────────────────────────────────────────

/**
 * Gera bytes PNG de textura procedural via Canvas 2D.
 * Retorna Uint8Array pronto pra figma.createImage().
 */
export async function generateTexturePNG(
  width: number,
  height: number,
  recipe: TextureRecipe
): Promise<Uint8Array> {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d')!;

  // Fundo
  if (recipe.background) {
    ctx.fillStyle = recipe.background;
    ctx.fillRect(0, 0, width, height);
  } else {
    ctx.clearRect(0, 0, width, height);
  }

  for (const layer of recipe.layers) {
    switch (layer.type) {
      case 'gradient':
        drawGradient(ctx, layer, width, height);
        break;
      case 'noise':
        drawNoise(ctx, layer, width, height);
        break;
      case 'dots':
        drawDots(ctx, layer, width, height);
        break;
      case 'lines':
        drawLines(ctx, layer, width, height);
        break;
      case 'gradient':
        break;
    }
  }

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) return reject(new Error('Canvas toBlob failed'));
      blob.arrayBuffer().then((buf) => resolve(new Uint8Array(buf)));
    }, 'image/png');
  });
}

export interface TextureRecipe {
  background?: string;
  layers: TextureLayer[];
}

export type TextureLayer =
  | GradientLayer
  | NoiseLayer
  | DotsLayer
  | LinesLayer;

export interface GradientLayer {
  type: 'gradient';
  x1: number; y1: number;
  x2: number; y2: number;
  colors: { offset: number; r: number; g: number; b: number; a?: number }[];
  opacity?: number;
}

export interface NoiseLayer {
  type: 'noise';
  opacity?: number;
  scale?: number;
}

export interface DotsLayer {
  type: 'dots';
  radius: number;
  spacing: number;
  color: { r: number; g: number; b: number; a?: number };
  offsetX?: number;
  offsetY?: number;
  opacity?: number;
}

export interface LinesLayer {
  type: 'lines';
  angle: number;
  spacing: number;
  thickness: number;
  color: { r: number; g: number; b: number; a?: number };
  opacity?: number;
}

function drawGradient(ctx: CanvasRenderingContext2D, layer: GradientLayer, w: number, h: number) {
  const grad = ctx.createLinearGradient(
    layer.x1 * w, layer.y1 * h,
    layer.x2 * w, layer.y2 * h
  );
  for (const c of layer.colors) {
    grad.addColorStop(c.offset, `rgba(${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)},${c.a ?? 1})`);
  }
  ctx.globalAlpha = layer.opacity ?? 1;
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);
}

function drawNoise(ctx: CanvasRenderingContext2D, layer: NoiseLayer, w: number, h: number) {
  const scale = layer.scale ?? 4;
  const op = layer.opacity ?? 0.15;
  ctx.globalAlpha = op;
  for (let y = 0; y < h; y += scale) {
    for (let x = 0; x < w; x += scale) {
      const v = Math.random() * 255;
      ctx.fillStyle = `rgb(${v},${v},${v})`;
      ctx.fillRect(x, y, scale, scale);
    }
  }
  ctx.globalAlpha = 1;
}

function drawDots(ctx: CanvasRenderingContext2D, layer: DotsLayer, w: number, h: number) {
  const r = layer.radius;
  const sp = layer.spacing;
  const ox = layer.offsetX ?? 0;
  const oy = layer.offsetY ?? 0;
  ctx.fillStyle = `rgba(${Math.round(layer.color.r * 255)},${Math.round(layer.color.g * 255)},${Math.round(layer.color.b * 255)},${layer.color.a ?? 1})`;
  ctx.globalAlpha = layer.opacity ?? 1;
  for (let y = oy; y < h + sp; y += sp) {
    for (let x = ox; x < w + sp; x += sp) {
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  ctx.globalAlpha = 1;
}

function drawLines(ctx: CanvasRenderingContext2D, layer: LinesLayer, w: number, h: number) {
  const angle = (layer.angle * Math.PI) / 180;
  const sp = layer.spacing;
  const th = layer.thickness;
  ctx.strokeStyle = `rgba(${Math.round(layer.color.r * 255)},${Math.round(layer.color.g * 255)},${Math.round(layer.color.b * 255)},${layer.color.a ?? 1})`;
  ctx.lineWidth = th;
  ctx.globalAlpha = layer.opacity ?? 1;

  const diag = Math.sqrt(w * w + h * h) * 2;
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);

  for (let t = -diag; t < diag; t += sp) {
    ctx.beginPath();
    ctx.moveTo(t * cos - diag * sin, t * sin + diag * cos);
    ctx.lineTo(t * cos + diag * sin, t * sin - diag * cos);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

// ─── Apply texture to shape ──────────────────────────────────────────────────

export async function applyTextureToShape(
  node: SceneNode,
  recipe: TextureRecipe,
  size?: number
): Promise<boolean> {
  const sz = size ?? Math.max(node.width, node.height, 256);
  const bytes = await generateTexturePNG(sz, sz, recipe);
  const image = figma.createImage(bytes);

  if ('fills' in node) {
    (node as RectangleMixin & SceneNode).fills = [{
      type: 'IMAGE',
      imageHash: image.hash,
      scaleMode: 'FILL'
    }];
    return true;
  }
  return false;
}
