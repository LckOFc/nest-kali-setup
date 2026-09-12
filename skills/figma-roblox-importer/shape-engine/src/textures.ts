import { showUI, on, emit } from '@create-figma-plugin/utilities';
import {
  ShapeConfig,
  TextureRecipe,
  solidColor,
  gradientLinear,
  applyTextureToShape,
  generateTexturePNG
} from './types';
import * as React from 'react';
import { createRoot } from 'react-dom/client';

showUI({ width: 420, height: 580, display: 'sidebar' });

// ─── Presets de texturas ──────────────────────────────────────────────────────

const TEXTURE_PRESETS: { name: string; recipe: TextureRecipe }[] = [
  {
    name: 'Degradê horizontal',
    recipe: {
      layers: [{
        type: 'gradient',
        x1: 0, y1: 0, x2: 1, y2: 0,
        colors: [
          { offset: 0, r: 0.2, g: 0.4, b: 1.0 },
          { offset: 1, r: 1.0, g: 0.3, b: 0.5 }
        ]
      }]
    }
  },
  {
    name: 'Degradê radial',
    recipe: {
      layers: [{
        type: 'gradient',
        x1: 0.5, y1: 0.5, x2: 0.5, y2: 0.5,
        colors: [
          { offset: 0, r: 1.0, g: 0.8, b: 0.2 },
          { offset: 1, r: 0.1, g: 0.5, b: 0.9 }
        ]
      }]
    }
  },
  {
    name: 'Ruído granulado',
    recipe: {
      background: '#1a1a2e',
      layers: [{ type: 'noise', opacity: 0.4, scale: 3 }]
    }
  },
  {
    name: 'Pontilhado',
    recipe: {
      background: '#0f0f1a',
      layers: [{
        type: 'dots',
        radius: 2,
        spacing: 12,
        color: { r: 0.6, g: 0.8, b: 1.0, a: 0.6 }
      }]
    }
  },
  {
    name: 'Listras diagonais',
    recipe: {
      background: '#1a1a1a',
      layers: [{
        type: 'lines',
        angle: 45,
        spacing: 8,
        thickness: 1.5,
        color: { r: 0.9, g: 0.9, b: 0.9, a: 0.15 }
      }]
    }
  },
  {
    name: 'Grid quadrado',
    recipe: {
      background: '#0d1117',
      layers: [
        {
          type: 'lines',
          angle: 0,
          spacing: 20,
          thickness: 0.5,
          color: { r: 0.3, g: 0.5, b: 1.0, a: 0.3 }
        },
        {
          type: 'lines',
          angle: 90,
          spacing: 20,
          thickness: 0.5,
          color: { r: 0.3, g: 0.5, b: 1.0, a: 0.3 }
        }
      ]
    }
  },
  {
    name: 'Cyberpunk neon',
    recipe: {
      background: '#0a0a14',
      layers: [
        {
          type: 'gradient',
          x1: 0, y1: 0, x2: 1, y2: 1,
          colors: [
            { offset: 0, r: 0.0, g: 1.0, b: 0.8 },
            { offset: 0.5, r: 0.8, g: 0.0, b: 1.0 },
            { offset: 1, r: 1.0, g: 0.2, b: 0.4 }
          ]
        },
        { type: 'noise', opacity: 0.08, scale: 2 }
      ]
    }
  },
  {
    name: 'Sunset dourado',
    recipe: {
      layers: [{
        type: 'gradient',
        x1: 0, y1: 1, x2: 0, y2: 0,
        colors: [
          { offset: 0, r: 0.8, g: 0.2, b: 0.1 },
          { offset: 0.4, r: 1.0, g: 0.5, b: 0.1 },
          { offset: 0.8, r: 1.0, g: 0.8, b: 0.3 },
          { offset: 1, r: 1.0, g: 1.0, b: 0.9 }
        ]
      }]
    }
  }
];

on<'TEXTURE_APPLY'>(async (event) => {
  const { presetIndex, shapeType, width, height } = event.data;
  const preset = TEXTURE_PRESETS[presetIndex];
  if (!preset) return;

  const nodes = figma.currentPage.selection.filter(n => n.type === shapeType);
  if (nodes.length === 0) {
    // Criar novo se não tiver selecionado
    let node: SceneNode;
    if (shapeType === 'RECTANGLE') {
      node = figma.createRectangle();
    } else if (shapeType === 'ELLIPSE') {
      node = figma.createEllipse();
    } else {
      node = figma.createFrame();
    }
    if (width && height) node.resize(width, height);
    node.name = 'textura';

    const sz = width ?? height ?? 256;
    const bytes = await generateTexturePNG(sz, sz, preset.recipe);
    const img = figma.createImage(bytes);
    if ('fills' in node) {
      (node as RectangleMixin & SceneNode).fills = [{
        type: 'IMAGE',
        imageHash: img.hash,
        scaleMode: 'FILL'
      }];
    }
    figma.notify(`🎨 Textura "${preset.name}" aplicada!`);
    figma.closePlugin();
    return;
  }

  for (const node of nodes) {
    if (!('fills' in node)) continue;
    const sz = Math.max((node as SceneNode).width, (node as SceneNode).height, 256);
    const ok = await applyTextureToShape(node as SceneNode, preset.recipe, sz);
    if (ok) figma.notify(`🎨 Textura "${preset.name}" aplicada!`);
  }
  figma.closePlugin();
});

on<'TEXTURE_CUSTOM'>(async (event) => {
  const { recipe, shapeType } = event.data;
  const nodes = figma.currentPage.selection.filter(n => n.type === shapeType);

  for (const node of nodes) {
    if (!('fills' in node)) continue;
    const sz = Math.max(node.width, node.height, 256);
    const bytes = await generateTexturePNG(sz, sz, recipe);
    const img = figma.createImage(bytes);
    (node as RectangleMixin & SceneNode).fills = [{
      type: 'IMAGE',
      imageHash: img.hash,
      scaleMode: 'FILL'
    }];
  }
  figma.notify('🎨 Textura customizada aplicada!');
  figma.closePlugin();
});

on<'TEXTURE_EXPORT'>(async (event) => {
  const { recipe, size } = event.data;
  const bytes = await generateTexturePNG(size, size, recipe);
  // Copia pra clipboard como base64
  const b64 = btoa(String.fromCharCode(...bytes));
  figma.ui.postMessage({ type: 'texture_export', b64, size });
  figma.notify('📋 Textura copiada como base64!');
  figma.closePlugin();
});

// Inicializa UI
const root = createRoot(document.getElementById('root')!);
root.render(<TexturePanel />);

function TexturePanel() {
  return (
    <div style={{
      fontFamily: 'Inter, sans-serif',
      padding: '16px',
      background: '#1e1e2e',
      color: '#cdd6f4',
      height: '100%',
      overflowY: 'auto',
      boxSizing: 'border-box'
    }}>
      <h2 style={{ margin: '0 0 12px', fontSize: 16, color: '#89b4fa' }}>
        🎨 Texturas & Preenchimentos
      </h2>

      <p style={{ fontSize: 12, color: '#a6adc8', margin: '0 0 16px' }}>
        Selecione uma forma no canvas e clique numa textura.
        A textura será injetada como fill IMAGE.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        {TEXTURE_PRESETS.map((preset, i) => (
          <TextureCard
            key={i}
            name={preset.name}
            recipe={preset.recipe}
            onClick={() => {
              const selected = figma.currentPage.selection[0];
              if (!selected) {
                figma.notify('⚠️ Selecione uma forma primeiro');
                return;
              }
              const shapeType = selected.type;
              emit('TEXTURE_APPLY', { presetIndex: i, shapeType });
            }}
          />
        ))}
      </div>

      <hr style={{ borderColor: '#313244', margin: '16px 0' }} />

      <CustomTextureBuilder />
    </div>
  );
}

function TextureCard({ name, recipe, onClick }: {
  name: string;
  recipe: TextureRecipe;
  onClick: () => void;
}) {
  const [preview, setPreview] = React.useState<string | null>(null);

  React.useEffect(() => {
    generateThumbnail(recipe).then(setPreview);
  }, []);

  return (
    <button
      onClick={onClick}
      style={{
        background: '#313244',
        border: '1px solid #45475a',
        borderRadius: 8,
        padding: '8px',
        cursor: 'pointer',
        color: '#cdd6f4',
        textAlign: 'center',
        transition: 'all 0.15s'
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = '#89b4fa')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = '#45475a')}
    >
      {preview ? (
        <img src={preview} alt={name} style={{
          width: '100%', height: 60, objectFit: 'cover',
          borderRadius: 4, marginBottom: 4
        }} />
      ) : (
        <div style={{ width: '100%', height: 60, background: '#1e1e2e', borderRadius: 4, marginBottom: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>🎨</div>
      )}
      <span style={{ fontSize: 11 }}>{name}</span>
    </button>
  );
}

async function generateThumbnail(recipe: TextureRecipe): Promise<string> {
  const canvas = document.createElement('canvas');
  canvas.width = 120;
  canvas.height = 120;
  const ctx = canvas.getContext('2d')!;
  // Recreate simple preview
  if (recipe.background) {
    ctx.fillStyle = recipe.background;
    ctx.fillRect(0, 0, 120, 120);
  }
  for (const layer of recipe.layers) {
    switch (layer.type) {
      case 'gradient': {
        const g = ctx.createLinearGradient(
          layer.x1 * 120, layer.y1 * 120,
          layer.x2 * 120, layer.y2 * 120
        );
        for (const c of layer.colors) {
          g.addColorStop(c.offset, `rgba(${Math.round(c.r*255)},${Math.round(c.g*255)},${Math.round(c.b*255)},${c.a??1})`);
        }
        ctx.globalAlpha = layer.opacity ?? 1;
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, 120, 120);
        break;
      }
      case 'noise': {
        const s = layer.scale ?? 4;
        ctx.globalAlpha = layer.opacity ?? 0.15;
        for (let y = 0; y < 120; y += s) {
          for (let x = 0; x < 120; x += s) {
            const v = Math.random() * 255;
            ctx.fillStyle = `rgb(${v},${v},${v})`;
            ctx.fillRect(x, y, s, s);
          }
        }
        break;
      }
      case 'dots': {
        ctx.globalAlpha = layer.opacity ?? 1;
        ctx.fillStyle = `rgba(${Math.round(layer.color.r*255)},${Math.round(layer.color.g*255)},${Math.round(layer.color.b*255)},${layer.color.a??1})`;
        for (let y = 0; y < 120; y += layer.spacing) {
          for (let x = 0; x < 120; x += layer.spacing) {
            ctx.beginPath();
            ctx.arc(x, y, layer.radius, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        break;
      }
      case 'lines': {
        const angle = (layer.angle * Math.PI) / 180;
        ctx.strokeStyle = `rgba(${Math.round(layer.color.r*255)},${Math.round(layer.color.g*255)},${Math.round(layer.color.b*255)},${layer.color.a??1})`;
        ctx.lineWidth = layer.thickness;
        ctx.globalAlpha = layer.opacity ?? 1;
        const cos = Math.cos(angle), sin = Math.sin(angle);
        const diag = 300;
        for (let t = -diag; t < diag; t += layer.spacing) {
          ctx.beginPath();
          ctx.moveTo(t*cos - diag*sin, t*sin + diag*cos);
          ctx.lineTo(t*cos + diag*sin, t*sin - diag*cos);
          ctx.stroke();
        }
        break;
      }
    }
  }
  ctx.globalAlpha = 1;
  return canvas.toDataURL();
}

function CustomTextureBuilder() {
  const [colors, setColors] = React.useState<{ offset: number; r: number; g: number; b: number }[]>([
    { offset: 0, r: 0.2, g: 0.4, b: 1.0 },
    { offset: 1, r: 1.0, g: 0.3, b: 0.5 }
  ]);
  const [angle, setAngle] = React.useState(0);

  return (
    <div>
      <h3 style={{ fontSize: 13, color: '#f9e2af', margin: '0 0 8px' }}>
        ✏️ Criar Degradê Customizado
      </h3>
      <div style={{ display: 'flex', gap: 4, marginBottom: 8, flexWrap: 'wrap' }}>
        {colors.map((c, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <input
              type="color"
              value={`#${Math.round(c.r*255).toString(16).padStart(2,'0')}${Math.round(c.g*255).toString(16).padStart(2,'0')}${Math.round(c.b*255).toString(16).padStart(2,'0')}`}
              onChange={e => {
                const hex = e.target.value.slice(1);
                const nr = parseInt(hex.slice(0,2),16)/255;
                const ng = parseInt(hex.slice(2,4),16)/255;
                const nb = parseInt(hex.slice(4,6),16)/255;
                const next = [...colors];
                next[i] = { ...next[i], r: nr, g: ng, b: nb };
                setColors(next);
              }}
              style={{ width: 28, height: 28, border: 'none', cursor: 'pointer', background: 'transparent' }}
            />
            <input
              type="range" min={0} max={1} step={0.05}
              value={c.offset}
              onChange={e => {
                const next = [...colors];
                next[i] = { ...next[i], offset: parseFloat(e.target.value) };
                setColors(next);
              }}
              style={{ width: 60 }}
            />
            {colors.length > 2 && (
              <button onClick={() => setColors(colors.filter((_, idx) => idx !== i))}
                style={{ background: '#f38ba8', border: 'none', borderRadius: 4, color: '#1e1e2e', cursor: 'pointer', padding: '2 4px' }}>✕</button>
            )}
          </div>
        ))}
        <button
          onClick={() => setColors([...colors, { offset: colors.length === 0 ? 0 : 1, r: 1, g: 1, b: 1 }])}
          style={{ background: '#a6e3a1', border: 'none', borderRadius: 4, color: '#1e1e2e', cursor: 'pointer', padding: '4 8px', fontSize: 11 }}
        >+ Cor</button>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
        <label style={{ fontSize: 11 }}>Ângulo:</label>
        <input type="range" min={0} max={360} value={angle}
          onChange={e => setAngle(parseInt(e.target.value))}
          style={{ flex: 1 }} />
        <span style={{ fontSize: 11, minWidth: 30 }}>{angle}°</span>
      </div>

      <button
        onClick={() => {
          const rad = (angle * Math.PI) / 180;
          const cos = Math.cos(rad), sin = Math.sin(rad);
          const recipe: TextureRecipe = {
            layers: [{
              type: 'gradient',
              x1: 0.5 - cos * 0.5,
              y1: 0.5 - sin * 0.5,
              x2: 0.5 + cos * 0.5,
              y2: 0.5 + sin * 0.5,
              colors: colors.map(c => ({ offset: c.offset, r: c.r, g: c.g, b: c.b }))
            }]
          };
          const selected = figma.currentPage.selection[0];
          if (!selected) {
            figma.notify('⚠️ Selecione uma forma primeiro');
            return;
          }
          emit('TEXTURE_CUSTOM', { recipe, shapeType: selected.type });
        }}
        style={{
          width: '100%',
          background: '#89b4fa',
          border: 'none',
          borderRadius: 6,
          color: '#1e1e2e',
          padding: '8px',
          cursor: 'pointer',
          fontWeight: 600,
          fontSize: 13
        }}
      >
        Aplicar Degradê
      </button>
    </div>
  );
}
