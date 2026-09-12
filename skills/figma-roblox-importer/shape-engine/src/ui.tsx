import { showUI, on, emit } from '@create-figma-plugin/utilities';
import * as React from 'react';
import { createRoot } from 'react-dom/client';
import { ShapeConfig, solidColor, gradientLinear, gradientRadial } from './types';

showUI({ width: 420, height: 680, display: 'sidebar' });

// ─── Shape creation ──────────────────────────────────────────────────────────

on<'CREATE_SHAPE'>(async (config: ShapeConfig) => {
  await figma.loadFontAsync([{ family: 'Inter', style: 'Regular' }]);

  const { type, w = 200, h = 200, sides = 6, radius = 0 } = config;
  let node: SceneNode | null = null;

  switch (type) {
    case 'rectangle':
      node = figma.createRectangle();
      if (node) { node.resize(w, h); positionNode(node, w, h); }
      break;
    case 'ellipse':
      node = figma.createEllipse();
      if (node) { node.resize(w, h); positionNode(node, w, h); }
      break;
    case 'triangle':
      node = figma.createPolygon(3);
      if (node) { node.resize(w, h); positionNode(node, w, h); }
      break;
    case 'polygon':
      node = figma.createPolygon(sides);
      if (node) { node.resize(w, h); positionNode(node, w, h); }
      break;
    case 'star':
      node = figma.createStar();
      if (node) { node.resize(w, h); positionNode(node, w, h); }
      break;
    case 'line':
      node = figma.createLine();
      if (node) { node.resize(w, 2); positionNode(node, w, 2); }
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
      if (node) { node.resize(w, h); positionNode(node, w, h); }
      break;
    case 'component':
      node = figma.createComponent();
      if (node) { node.resize(w, h); positionNode(node, w, h); }
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
    if (config.name) node.name = config.name;

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

// ─── UI Root ─────────────────────────────────────────────────────────────────

const root = createRoot(document.getElementById('root')!);
root.render(<App />);

// ─── React App ───────────────────────────────────────────────────────────────

function App() {
  const [tab, setTab] = React.useState<'shapes' | 'modify' | 'export'>('shapes');
  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, sans-serif",
      background: '#1e1e2e',
      color: '#cdd6f4',
      height: '100vh',
      overflowY: 'auto',
      boxSizing: 'border-box',
      padding: '0 0 24px'
    }}>
      {/* Header */}
      <div style={{
        background: '#181825',
        borderBottom: '1px solid #313244',
        padding: '12px 16px',
        position: 'sticky',
        top: 0,
        zIndex: 10
      }}>
        <h1 style={{ fontSize: 15, fontWeight: 700, margin: 0, color: '#89b4fa' }}>
          ⚡ Shape Engine
        </h1>
        <p style={{ fontSize: 11, color: '#a6adc8', margin: '2px 0 0' }}>
          Crie, transforme e aplique texturas em formas
        </p>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: 0,
        background: '#181825',
        borderBottom: '1px solid #313244'
      }}>
        {[
          { key: 'shapes' as const, label: '🔷 Shapes', badge: 'Criar' },
          { key: 'modify' as const, label: '🎨 Texturas', badge: 'Fill' },
          { key: 'export' as const, label: '📐 Exportar', badge: 'SVG/PNG' }
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              flex: 1,
              background: tab === t.key ? '#313244' : 'transparent',
              border: 'none',
              borderBottom: tab === t.key ? '2px solid #89b4fa' : '2px solid transparent',
              color: tab === t.key ? '#89b4fa' : '#a6adc8',
              padding: '10px 4px',
              fontSize: 11,
              cursor: 'pointer',
              borderRadius: '0',
              fontWeight: tab === t.key ? 600 : 400
            }}
          >
            {t.label}
            <span style={{
              background: tab === t.key ? '#89b4fa' : '#45475a',
              color: tab === t.key ? '#1e1e2e' : '#a6adc8',
              borderRadius: 3,
              padding: '1px 4px',
              fontSize: 9,
              marginLeft: 4
            }}>{t.badge}</span>
          </button>
        ))}
      </div>

      <div style={{ padding: '12px 16px' }}>
        {tab === 'shapes' && <ShapesPanel />}
        {tab === 'modify' && <ModifyPanel />}
        {tab === 'export' && <ExportPanel />}
      </div>
    </div>
  );
}

// ─── Shapes Panel ────────────────────────────────────────────────────────────

function ShapesPanel() {
  const [shapeType, setShapeType] = React.useState<'rectangle' | 'ellipse' | 'triangle' | 'polygon' | 'star' | 'line' | 'vector' | 'frame' | 'component'>('rectangle');
  const [w, setW] = React.useState(200);
  const [h, setH] = React.useState(200);
  const [sides, setSides] = React.useState(6);
  const [radius, setRadius] = React.useState(0);
  const [fillColor, setFillColor] = React.useState('#89b4fa');
  const [strokeColor, setStrokeColor] = React.useState('#000000');
  const [strokeW, setStrokeW] = React.useState(0);
  const [opacity, setOpacity] = React.useState(1);
  const [name, setName] = React.useState('');
  const [blendMode, setBlendMode] = React.useState('NORMAL');

  const shapes: { type: typeof shapeType; label: string; icon: string }[] = [
    { type: 'rectangle', label: 'Retângulo', icon: '▭' },
    { type: 'ellipse', label: 'Elipse', icon: '●' },
    { type: 'triangle', label: 'Triângulo', icon: '▲' },
    { type: 'polygon', label: 'Polígono', icon: '⬡' },
    { type: 'star', label: 'Estrela', icon: '★' },
    { type: 'line', label: 'Linha', icon: '━' },
    { type: 'vector', label: 'Vetor', icon: '⬢' },
    { type: 'frame', label: 'Frame', icon: '▢' },
    { type: 'component', label: 'Component', icon: '◇' }
  ];

  const blendModes = ['NORMAL', 'MULTIPLY', 'SCREEN', 'OVERLAY', 'DARKEN', 'LIGHTEN', 'COLOR_BURN', 'LINEAR_BURN', 'COLOR_DODGE', 'LINEAR_DODGE', 'DIFFERENCE', 'EXCLUSION', 'HUE', 'SATURATION', 'COLOR', 'LUMINOSITY'];

  function hexToPaint(hex: string): import('./types').Paint {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    return solidColor(r, g, b, 1);
  }

  function create() {
    const cfg: ShapeConfig = {
      type: shapeType,
      w: shapeType === 'line' ? w : undefined,
      h: shapeType === 'line' ? 2 : h,
      sides: shapeType === 'polygon' ? sides : undefined,
      fill: hexToPaint(fillColor),
      stroke: strokeW > 0 ? hexToPaint(strokeColor) : undefined,
      radius: shapeType === 'rectangle' || shapeType === 'frame' ? radius : undefined,
      opacity,
      name: name || undefined,
      blendMode
    };
    emit('CREATE_SHAPE', cfg);
  }

  return (
    <>
      {/* Shape type selector */}
      <div style={{ marginBottom: 12 }}>
        <label style={labelStyle}>Tipo de forma</label>
        <div style={{ ...grid2, marginTop: 6 }}>
          {shapes.map(s => (
            <button key={s.type} onClick={() => setShapeType(s.type)}
              style={{
                ...btn,
                background: shapeType === s.type ? '#89b4fa' : '#313244',
                color: shapeType === s.type ? '#1e1e2e' : '#cdd6f4',
                flexDirection: 'column',
                gap: 4,
                padding: '10px 4px'
              }}>
              <span style={{ fontSize: 20 }}>{s.icon}</span>
              <span style={{ fontSize: 10 }}>{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      <hr style={{ borderColor: '#313244', margin: '12px 0' }} />

      {/* Dimensions */}
      <div className="prop-group">
        <label style={labelStyle}>Dimensões</label>
        <div className="row-input">
          <div><label>W</label><input type="number" value={w} onChange={e => setW(+e.target.value)} style={input} /></div>
          <div><label>H</label><input type="number" value={shapeType === 'line' ? 2 : h} onChange={e => setH(+e.target.value)} style={input} /></div>
          {shapeType === 'polygon' && <div><label>Lados</label><input type="number" value={sides} onChange={e => setSides(Math.max(3, Math.min(24, +e.target.value)))} min={3} max={24} style={input} /></div>}
          {(shapeType === 'rectangle' || shapeType === 'frame') && <div><label>R</label><input type="number" value={radius} onChange={e => setRadius(+e.target.value)} min={0} style={input} /></div>}
        </div>
      </div>

      <hr style={{ borderColor: '#313244', margin: '12px 0' }} />

      {/* Fill */}
      <div className="prop-group">
        <label style={labelStyle}>Preenchimento</label>
        <div className="row-input">
          <input type="color" value={fillColor} onChange={e => setFillColor(e.target.value)} style={{ width: 40, height: 32, border: 'none', background: 'transparent', cursor: 'pointer' }} />
          <input type="text" value={fillColor} onChange={e => setFillColor(e.target.value)} style={{ ...input, flex: 1 }} />
          <label style={{ marginLeft: 'auto' }}>Opacidade</label>
          <input type="number" min={0} max={1} step={0.05} value={opacity} onChange={e => setOpacity(+e.target.value)} style={{ ...input, width: 50 }} />
        </div>
      </div>

      {/* Stroke */}
      <div className="prop-group">
        <label style={labelStyle}>Borda (Stroke)</label>
        <div className="row-input">
          <input type="color" value={strokeColor} onChange={e => setStrokeColor(e.target.value)} style={{ width: 40, height: 32, border: 'none', background: 'transparent', cursor: 'pointer' }} />
          <input type="text" value={strokeColor} onChange={e => setStrokeColor(e.target.value)} style={{ ...input, flex: 1 }} />
          <div><label>Spess.</label><input type="number" value={strokeW} onChange={e => setStrokeW(+e.target.value)} min={0} max={50} style={{ ...input, width: 50 }} /></div>
        </div>
      </div>

      {/* Blend mode */}
      <div className="prop-group">
        <label style={labelStyle}>Blend Mode</label>
        <select value={blendMode} onChange={e => setBlendMode(e.target.value)} style={{ ...input, width: '100%', padding: '6px 8px' }}>
          {blendModes.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {/* Name */}
      <div className="prop-group">
        <label style={labelStyle}>Nome da camada</label>
        <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder={`shape_${shapeType}`} style={{ ...input, width: '100%' }} />
      </div>

      <button onClick={create} style={{ ...btnPrimary, width: '100%', marginTop: 12, padding: '12px' }}>
        ⚡ Criar {shapes.find(s => s.type === shapeType)?.label}
      </button>
    </>
  );
}

// ─── Modify Panel ────────────────────────────────────────────────────────────

function ModifyPanel() {
  const [mode, setMode] = React.useState<'texture' | 'boolean' | 'layer'>('texture');

  return (
    <>
      <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
        {[
          { key: 'texture' as const, label: '🎨 Texturas' },
          { key: 'boolean' as const, label: '⚡ Booleanas' },
          { key: 'layer' as const, label: '📑 Camadas' }
        ].map(m => (
          <button key={m.key} onClick={() => setMode(m.key)}
            style={{ ...btn, flex: 1, background: mode === m.key ? '#89b4fa' : '#313244', color: mode === m.key ? '#1e1e2e' : '#cdd6f4' }}>
            {m.label}
          </button>
        ))}
      </div>

      {mode === 'texture' && <TexturePanel />}
      {mode === 'boolean' && <BooleanPanel />}
      {mode === 'layer' && <LayerPanel />}
    </>
  );
}

function TexturePanel() {
  const presets = [
    { name: 'Degradê Horizontal', type: 'gradient', x1: 0, y1: 0, x2: 1, y2: 0, colors: [{ offset: 0, r: 0.2, g: 0.4, b: 1 }, { offset: 1, r: 1, g: 0.3, b: 0.5 }] },
    { name: 'Degradê Vertical', type: 'gradient', x1: 0, y1: 1, x2: 0, y2: 0, colors: [{ offset: 0, r: 0.1, g: 0.1, b: 0.2 }, { offset: 1, r: 0.8, g: 0.2, b: 0.4 }] },
    { name: 'Radial', type: 'gradient', x1: 0.5, y1: 0.5, x2: 0.5, y2: 0.5, colors: [{ offset: 0, r: 1, g: 0.8, b: 0.2 }, { offset: 1, r: 0.1, g: 0.5, b: 0.9 }] },
    { name: 'Cyberpunk', type: 'gradient', x1: 0, y1: 0, x2: 1, y2: 1, colors: [{ offset: 0, r: 0, g: 1, b: 0.8 }, { offset: 0.5, r: 0.8, g: 0, b: 1 }, { offset: 1, r: 1, g: 0.2, b: 0.4 }] },
    { name: 'Sunset', type: 'gradient', x1: 0, y1: 1, x2: 0, y2: 0, colors: [{ offset: 0, r: 0.8, g: 0.2, b: 0.1 }, { offset: 0.4, r: 1, g: 0.5, b: 0.1 }, { offset: 1, r: 1, g: 1, b: 0.9 }] },
    { name: 'Ruído', type: 'noise', opacity: 0.3, scale: 4 },
    { name: 'Pontilhado', type: 'dots', radius: 2, spacing: 12, color: { r: 0.6, g: 0.8, b: 1, a: 0.6 } },
    { name: 'Listras 45°', type: 'lines', angle: 45, spacing: 8, thickness: 1.5, color: { r: 0.9, g: 0.9, b: 0.9, a: 0.15 } },
    { name: 'Grid', type: 'grid', spacing: 20, color: { r: 0.3, g: 0.5, b: 1, a: 0.3 } }
  ];

  const selected = presets.find(p => p.name === 'Degradê Horizontal')!;

  return (
    <>
      <p style={{ marginBottom: 10 }}>
        Selecione uma forma no canvas e clique numa textura. A textura será injetada como fill IMAGE.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {presets.map((p, i) => (
          <button key={i} onClick={() => applyTexture(i)} style={{ ...btn, padding: '10px 6px', textAlign: 'center', flexDirection: 'column', gap: 4 }}>
            <TexturePreview recipe={p} />
            <span style={{ fontSize: 10 }}>{p.name}</span>
          </button>
        ))}
      </div>
    </>
  );

  function applyTexture(idx: number) {
    const selected = presets[idx];
    const node = figma.currentPage.selection[0];
    if (!node || !('fills' in node)) {
      figma.notify('⚠️ Selecione uma forma com fills');
      return;
    }
    // Apply directly via Figma API
    let paint: import('@figma/plugin-typings').Paint;
    switch (selected.type) {
      case 'gradient':
        paint = {
          type: 'GRADIENT_LINEAR',
          gradientHandlePositions: [
            { x: selected.x1, y: selected.y1 },
            { x: selected.x2, y: selected.y2 },
            { x: selected.x1, y: selected.y2 }
          ],
          gradientStops: selected.colors.map((c: any) => ({ position: c.offset, color: { r: c.r, g: c.g, b: c.b, a: c.a ?? 1 } }))
        };
        break;
      case 'noise':
      case 'dots':
      case 'lines':
      case 'grid':
        // For complex textures, we use the textures.ts plugin
        emit('TEXTURE_CUSTOM', { recipe: selected as any, shapeType: node.type });
        return;
      default:
        paint = solidColor(0.5, 0.5, 0.5);
    }
    (node as any).fills = [paint];
    figma.notify(`🎨 "${selected.name}" aplicado!`);
    figma.closePlugin();
  }
}

function TexturePreview({ recipe }: { recipe: any }) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    const w = 100, h = 60;
    canvas.width = w;
    canvas.height = h;

    if (recipe.type === 'gradient') {
      const g = ctx.createLinearGradient(recipe.x1 * w, recipe.y1 * h, recipe.x2 * w, recipe.y2 * h);
      for (const c of recipe.colors) g.addColorStop(c.offset, `rgb(${Math.round(c.r*255)},${Math.round(c.g*255)},${Math.round(c.b*255)})`);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
    } else if (recipe.type === 'noise') {
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, 0, w, h);
      const s = recipe.scale || 4;
      for (let y = 0; y < h; y += s) for (let x = 0; x < w; x += s) {
        const v = Math.random() * 255;
        ctx.fillStyle = `rgba(${v},${v},${v},${recipe.opacity ?? 0.3})`;
        ctx.fillRect(x, y, s, s);
      }
    } else if (recipe.type === 'dots') {
      ctx.fillStyle = '#0f0f1a';
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = `rgba(${Math.round(recipe.color.r*255)},${Math.round(recipe.color.g*255)},${Math.round(recipe.color.b*255)},${recipe.color.a ?? 1})`;
      for (let y = 0; y < h; y += recipe.spacing) for (let x = 0; x < w; x += recipe.spacing) {
        ctx.beginPath(); ctx.arc(x, y, recipe.radius, 0, Math.PI * 2); ctx.fill();
      }
    } else if (recipe.type === 'lines') {
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, w, h);
      const angle = (recipe.angle * Math.PI) / 180;
      ctx.strokeStyle = `rgba(${Math.round(recipe.color.r*255)},${Math.round(recipe.color.g*255)},${Math.round(recipe.color.b*255)},${recipe.color.a ?? 1})`;
      ctx.lineWidth = recipe.thickness;
      const cos = Math.cos(angle), sin = Math.sin(angle);
      const diag = 200;
      for (let t = -diag; t < diag; t += recipe.spacing) {
        ctx.beginPath();
        ctx.moveTo(t * cos - diag * sin, t * sin + diag * cos);
        ctx.lineTo(t * cos + diag * sin, t * sin - diag * cos);
        ctx.stroke();
      }
    } else if (recipe.type === 'grid') {
      ctx.fillStyle = '#0d1117';
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = `rgba(${Math.round(recipe.color.r*255)},${Math.round(recipe.color.g*255)},${Math.round(recipe.color.b*255)},${recipe.color.a ?? 1})`;
      ctx.lineWidth = 0.5;
      for (let x = 0; x <= w; x += recipe.spacing) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
      for (let y = 0; y <= h; y += recipe.spacing) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
    }
  }, [recipe]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: 40, borderRadius: 4, display: 'block' }} />;
}

function BooleanPanel() {
  const ops: { op: string; label: string; icon: string }[] = [
    { op: 'BOOLEAN_UNION', label: 'Union', icon: '🔗' },
    { op: 'BOOLEAN_SUBTRACT', label: 'Subtract', icon: '➖' },
    { op: 'BOOLEAN_INTERSECT', label: 'Intersect', icon: '🔲' },
    { op: 'BOOLEAN_EXCLUDE', label: 'Exclude', icon: '🚫' }
  ];
  return (
    <>
      <p>Selecione 2+ formas e escolha uma operação booleana.</p>
      <div style={grid2}>
        {ops.map(o => (
          <button key={o.op} onClick={() => emit(o.op)} style={{ ...btn, flexDirection: 'column', gap: 4, padding: '12px 6px' }}>
            <span style={{ fontSize: 20 }}>{o.icon}</span>
            <span style={{ fontSize: 11 }}>{o.label}</span>
          </button>
        ))}
      </div>
      <hr style={{ borderColor: '#313244', margin: '12px 0' }} />
      <p style={{ fontSize: 11, color: '#a6adc8' }}>
        💡 Dica: A ordem de seleção importa. No Subtract, o primeiro nó é a base.
      </p>
    </>
  );
}

function LayerPanel() {
  const actions: { op: string; label: string; icon: string; desc: string }[] = [
    { op: 'LAYER_FLATTEN', label: 'Flatten', icon: '📐', desc: 'Fundir seleção em vector' },
    { op: 'LAYER_GROUP', label: 'Group', icon: '📁', desc: 'Agrupar seleções' },
    { op: 'LAYER_UNGROUP', label: 'Ungroup', icon: '📂', desc: 'Desagrupar' },
    { op: 'LAYER_DUPLICATE', label: 'Duplicate', icon: '📋', desc: 'Duplicar selecionado' },
    { op: 'LAYER_DELETE', label: 'Delete', icon: '🗑️', desc: 'Remover selecionado' },
    { op: 'LAYER_OUTLINE_STROKE', label: 'Outline Stroke', icon: '✏️', desc: 'Converter stroke em vetor' },
    { op: 'LAYER_COMPONENT', label: 'Create Component', icon: '💎', desc: 'Virar componente' },
    { op: 'LAYER_REORDER_UP', label: 'Mover ↑', icon: '⬆️', desc: 'Trazer pra frente' },
    { op: 'LAYER_REORDER_DOWN', label: 'Mover ↓', icon: '⬇️', desc: 'Enviar pro fundo' }
  ];
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {actions.map(a => (
          <button key={a.op} onClick={() => emit(a.op)} style={{ ...btn, flexDirection: 'column', gap: 3, padding: '10px 6px' }}>
            <span style={{ fontSize: 18 }}>{a.icon}</span>
            <span style={{ fontSize: 11, fontWeight: 600 }}>{a.label}</span>
            <span style={{ fontSize: 9, color: '#a6adc8' }}>{a.desc}</span>
          </button>
        ))}
      </div>
    </>
  );
}

// ─── Export Panel ─────────────────────────────────────────────────────────────

function ExportPanel() {
  const [format, setFormat] = React.useState<'svg' | 'png'>('svg');
  const [scale, setScale] = React.useState(2);

  function exportSelected() {
    const nodes = figma.currentPage.selection;
    if (nodes.length === 0) {
      figma.notify('⚠️ Selecione algo pra exportar');
      return;
    }
    emit('TRANSFORM_EXPORT_SELECTION', { format, scale });
  }

  return (
    <>
      <div className="prop-group">
        <label style={labelStyle}>Formato</label>
        <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
          <button onClick={() => setFormat('svg')} style={{ ...btn, flex: 1, background: format === 'svg' ? '#89b4fa' : '#313244', color: format === 'svg' ? '#1e1e2e' : '#cdd6f4' }}>
            SVG
          </button>
          <button onClick={() => setFormat('png')} style={{ ...btn, flex: 1, background: format === 'png' ? '#89b4fa' : '#313244', color: format === 'png' ? '#1e1e2e' : '#cdd6f4' }}>
            PNG
          </button>
        </div>
      </div>

      <div className="prop-group" style={{ marginTop: 10 }}>
        <label style={labelStyle}>Escala: {scale}x</label>
        <input type="range" min={1} max={4} step={1} value={scale} onChange={e => setScale(+e.target.value)} style={{ width: '100%' }} />
      </div>

      <button onClick={exportSelected} style={{ ...btnPrimary, width: '100%', marginTop: 16, padding: '12px' }}>
        📥 Exportar Seleção ({format.toUpperCase()})
      </button>

      <hr style={{ borderColor: '#313244', margin: '16px 0' }} />

      {/* Transform panel */}
      <h3 style={{ ...heading3, marginBottom: 10 }}>📐 Transformações Rápidas</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginBottom: 10 }}>
        {[
          { op: "TRANSFORM_ROTATE", label: '↻ +90°', data: { degrees: 90 } },
          { op: "TRANSFORM_FLIP_H", label: '↔ Flip H' },
          { op: "TRANSFORM_FLIP_V", label: '↕ Flip V' },
          { op: "TRANSFORM_ALIGN_CENTER", label: '🎯 Centro' },
          { op: "TRANSFORM_CENTER_TO_VIEWPORT", label: '📍 Viewport' },
          { op: "TRANSFORM_RANDOMIZE", label: '🎲 Random' }
        ].map(t => (
          <button key={t.op} onClick={() => emit(t.op, (t as any).data || {})} style={{ ...btn, padding: '8px 4px', fontSize: 10 }}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="prop-group">
        <label style={labelStyle}>Snapping pro Grid (px)</label>
        <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
          {[10, 20, 50, 100].map(g => (
            <button key={g} onClick={() => emit("TRANSFORM_ALIGN_GRID", { gridSize: g })} style={{ ...btn, flex: 1 }}>{g}px</button>
          ))}
        </div>
      </div>

      <div className="prop-group" style={{ marginTop: 10 }}>
        <label style={labelStyle}>Redimensionar todos (W × H)</label>
        <div className="row-input">
          <input type="number" placeholder="W" style={{ ...input, flex: 1 }} id="resize-w" />
          <input type="number" placeholder="H" style={{ ...input, flex: 1 }} id="resize-h" />
          <button onClick={() => {
            const w = (+document.getElementById('resize-w')?.value) || 200;
            const h = (+document.getElementById('resize-h')?.value) || 200;
            emit("TRANSFORM_RESIZE", { w, h, aspect: false });
          }} style={{ ...btnPrimary, padding: '6px 12px' }}>Aplicar</button>
        </div>
      </div>

      <div className="prop-group" style={{ marginTop: 10 }}>
        <label style={labelStyle}>Escalonar (scale factor)</label>
        <div className="row-input">
          <input type="number" placeholder="1.5" step={0.1} style={{ ...input, flex: 1 }} id="scale-factor" />
          <button onClick={() => {
            const f = (+document.getElementById('scale-factor')?.value) || 1;
            emit("TRANSFORM_SCALE", { factor: f });
          }} style={{ ...btnPrimary, padding: '6px 12px' }}>Aplicar</button>
        </div>
      </div>
    </>
  );
}

// ─── Shared Styles ───────────────────────────────────────────────────────────

const labelStyle: React.CSSProperties = { fontSize: 11, color: '#a6adc8', display: 'block', marginBottom: 4 };
const input: React.CSSProperties = {
  background: '#313244',
  border: '1px solid #45475a',
  color: '#cdd6f4',
  borderRadius: 4,
  padding: '4px 8px',
  fontSize: 12,
  width: 60
};
const btn: React.CSSProperties = {
  background: '#313244',
  border: '1px solid #45475a',
  borderRadius: 6,
  color: '#cdd6f4',
  padding: '8px 10px',
  fontSize: 11,
  cursor: 'pointer',
  transition: 'all 0.12s',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontFamily: 'inherit'
};
const btnPrimary: React.CSSProperties = {
  ...btn,
  background: '#89b4fa',
  color: '#1e1e2e',
  border: 'none',
  fontWeight: 600,
  fontSize: 13
};
const grid2: React.CSSProperties = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 };
const heading3: React.CSSProperties = { fontSize: 13, color: '#f9e2af', margin: '16px 0 8px' };
