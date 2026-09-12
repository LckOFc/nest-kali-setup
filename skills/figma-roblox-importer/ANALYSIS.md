# Figma to Roblox LuaU — Engenharia Reversa Completa

## 1. Arquitetura Geral do Plugin

### Pipeline de Processamento (7 etapas)

```
┌─────────────────┐
│ Figma Selection │  ← sceneNodes selecionados pelo usuário
└────────┬────────┘
         ▼
┌─────────────────────────────────────────────────────────────┐
│ [1] Node Parser (nodeParser.ts)                             │
│   • parseSelection() → itera sobre selection[]              │
│   • parseNode() recursivo (profundidade variável)           │
│   • Filtra: invisible (depth>0), SLICE, VECTOR, BOOLEAN     │
│   • Resolve tipo Roblox via resolveInstanceType()           │
│   • Cria ParsedNode com posição/size relativa               │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ [2] Property Extractor (properties.ts)                      │
│   • extractFillColor()       → Solid fill → RobloxColor3    │
│   • extractFillTransparency()→ 1 - opacity                  │
│   • extractGradient()        → UIGradientData               │
│   • extractCornerRadius()    → UICornerData                 │
│   • extractStroke()          → UIStrokeData                 │
│   • extractTextProps()       → TextNode → text props        │
│   • detectAnchorPoint()      → constraints → Vector2        │
│   • hasImageFill()           → IMAGE fill detection         │
│   • isInteractive()          → nome reações → button?       │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ [3] Position Calculator (math.ts)                           │
│   • computeRelativePosition() → UDim2 (scale+offset)        │
│   • computeRelativeSize()     → UDim2 proporcional          │
│   • roundTo(value, 4) → max 4 casas decimais                │
│   • Usa anchorPoint para ajuste de coordenadas              │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ [4] AnchorPoint Detector (properties.ts)                    │
│   • Interpreta constraints Figma: CENTER/MAX                │
│   • Mapeia para Vector2 {x,y} ∈ [0,1]                      │
│   • Default {0,0} (top-left)                                │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ [5] List Layout Detector (listLayoutDetector.ts)            │
│   • analyzeListLayout() → horizontal ou vertical?           │
│   • Tolerância: gaps ≤ 5px = consistente, > 2px = 1.0       │
│   • Cross-axis variance ≤ 5px                               │
│   • Injeta uiListLayout + ordena layoutOrder filhos         │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ [6] Responsive Injector (breakpoints.ts)                    │
│   • Regra 1: fontSize > 20 em mobile → reduz para 70%       │
│   • Regra 2: xOffset > 300 em mobile → centraliza (scale)   │
│   • Gera ResponsiveController Lua singleton                 │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ [7] Exporter (luaExporter / roactExporter / fusionExporter) │
│   • Switch(mode) no index.ts → exporta um dos 3 formatos    │
│   • NameAllocator garante nomes únicos de variáveis         │
│   • Indentação configurável (default 2 espaços)             │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────┐
│  Preview & Copy │  ← ui.html mostra código gerado
└─────────────────┘
```

---

## 2. Diagrama de Fluxo de Dados

```
figma.ui.onmessage
  │
  ├─ msg.type === "export"
  │     │
  │     ├─ validate selection.length > 0
  │     │
  │     ├─ build options: { ...DEFAULT_EXPORT_OPTIONS, ...msg.options }
  │     │
  │     ├─ parseSelection(selection, options)
  │     │       │
  │     │       └─ parseNode() recursivo
  │     │               ├─ resolveInstanceType(node)
  │     │               ├─ detectAnchorPoint(node)
  │     │               ├─ extractFillColor / Transparency / Gradient
  │     │               ├─ extractCornerRadius / Stroke
  │     │               ├─ extractTextProps (se TEXT)
  │     │               ├─ hasImageFill? → ImageLabel/ImageButton
  │     │               ├─ apply node.opacity to backgroundTransparency
  │     │               └─ recurse children
  │     │
  │     ├─ injectListLayouts(root) [if detectListLayouts]
  │     │       └─ analyzeListLayout(parent)
  │     │               ├─ sort children by X or Y
  │     │               ├─ compute gaps between adjacent children
  │     │               ├─ consistency score: avg gap deviation
  │     │               └─ inject UIListLayout + set layoutOrder
  │     │
  │     ├─ injectResponsiveRules(root) [if enableResponsive]
  │     │       └─ generateResponsiveRules(node)
  │     │               ├─ textSize > 20 → mobile override
  │     │               └─ xOffset > 300 → mobile center+scale override
  │     │
  │     ├─ exportNodes(parsed, options)
  │     │       └─ switch(options.mode)
  │     │               ├─ "lua"   → exportToLua()   → Instance.new code
  │     │               ├─ "roact" → exportToRoact() → createElement code
  │     │               └─ "fusion"→ exportToFusion()→ Fusion.New code
  │     │
  │     └─ postMessage({ type:"export-result", code, stats })
  │             ├─ countNodes (recursive total)
  │             ├─ countFrames (recursive Frame count)
  │             └─ lines = code.split("\n").length
  │
  └─ msg.type === "copy"
        └─ figma.notify("Code is shown in the preview. Select all and copy!")
```

**Fluxo de Dados Interno (ParsedNode):**

```
SceneNode (Figma API)
    │
    │  parseNode()
    ▼
ParsedNode
    ├─ id, name (sanitized)
    ├─ instanceType (Frame | TextLabel | ImageLabel | ...)
    ├─ position: UDim2 { xScale, xOffset, yScale, yOffset }
    ├─ size: UDim2 { xScale, xOffset, yScale, yOffset }
    ├─ anchorPoint: Vector2 { x, y }
    ├─ rotation: number
    ├─ backgroundColor: Color3 | null
    ├─ backgroundTransparency: number
    ├─ clipsDescendants: boolean
    ├─ text, textColor, textSize, font, textXAlignment, textYAlignment
    ├─ imageUrl, scaleType
    ├─ uiCorner: UICornerData?
    ├─ uiStroke: UIStrokeData?
    ├─ uiGradient: UIGradientData?
    ├─ uiListLayout: UIListLayoutData?
    ├─ responsiveBreakpoints: ResponsiveRule[]?
    ├─ children: ParsedNode[]
    └─ parent: ParsedNode | null
```

---

## 3. Algoritmos-Chave Explicados

### 3.1 Posição Relativa (Scale + Offset)

**Local:** `src/utils/math.ts:21-41`

O algoritmo converte coordenadas absolutas do Figma para UDim2 do Roblox, usando a combinação **Scale + Offset** (nunca puramente Offset).

```typescript
// Lógica de computeRelativePosition:
relX = childAbsX - parentAbsX          // offset bruto em relação ao pai
relY = childAbsY - parentAbsY
adjustedX = relX + anchorPoint.x * childWidth   // compensação pelo anchor
adjustedY = relY + anchorPoint.y * childHeight

// Formulação Scale + Offset:
xScale = adjustedX / parentWidth            // proporção relativa
yScale = adjustedY / parentHeight
xOffset = adjustedX - xScale * parentWidth   // resto em pixels
yOffset = adjustedY - yScale * parentHeight
```

**Por que essa abordagem?** O Roblox usa `UDim2.new(scale, offset)` onde `scale` é a fração do tamanho do pai e `offset` é pixels absolutos. Usar scale garante que o elemento se redimensione proporcionalmente. O plugin sempre usa essa combinação, nunca apenas offset puro — isso é uma vantagem significativa sobre plugins concorrentes.

### 3.2 Detecção de UIListLayout

**Local:** `src/layout/listLayoutDetector.ts`

O algoritmo verifica se os filhos de um frame estão dispostos de forma regular:

```
1. Filtra children visíveis
2. Se < 2 filhos → retorna null
3. Ordena por X (horizontal) e por Y (vertical) separadamente
4. Para cada direção:
   a. Calcula gaps entre children adjacentes
   b. calcula avgGap e maxDeviation
   c. consistency = 1.0 se deviation≤2, 0.8 se ≤5, 0.5 caso contrário
   d. Se consistency < 0.7 → descarta
   e. Verifica cross-axis variance (alinhamento perpendicular)
5. Escolhe a direção com maior consistency
6. Injeta UIListLayout com padding = avgGap
7. Atribui layoutOrder sequencial aos filhos
```

**Limitação:** O detector não considera AutoLayout do Figma — ele deriva puramente da geometria. Isso pode causar falsos positivos em layouts naturalmente alinhados.

### 3.3 Conversão de Cores

**Local:** `src/utils/color.ts`

```typescript
figmaColorToRoblox(color): RGB → { r, g, b } ∈ [0, 1]
  r = Math.round(color.r * 1000) / 1000   // 3 casas decimais
  g = Math.round(color.g * 1000) / 1000
  b = Math.round(color.b * 1000) / 1000

color3FromRGBString(color): RobloxColor3 → string
  return `Color3.fromRGB(${Math.round(c.r*255)}, ${...}, ${...})`
```

O Figma usa `RGB` com valores em [0,1] (float), enquanto o Roblox usa `Color3.fromRGB(r,g,b)` com inteiros em [0,255]. A conversão multiplica por 255 e faz round.

**Problema identificado:** A conversão de Figma RGB [0,1] para Roblox `fromRGB` é feita com `Math.round(c.r * 255)`, mas o valor `c.r` já foi arredondado para 3 casas decimais antes. Isso pode causar small errors de cor (ex: `(0.502 * 255) = 127.99 → 128` vs `0.502 * 255 = 128.01 → 128`). O efeito é mínimo mas existe.

### 3.4 Detecção de AnchorPoint

**Local:** `src/parser/properties.ts:143-155`

```typescript
detectAnchorPoint(node):
  if constraints.horizontal === "CENTER" → x = 0.5
  if constraints.horizontal === "MAX"    → x = 1.0
  if constraints.vertical === "CENTER"   → y = 0.5
  if constraints.vertical === "MAX"      → y = 1.0
  default → { x: 0, y: 0 }
```

Mapeamento direto das constraints do Figma para o AnchorPoint do Roblox. Importante notar que `MIN` no Figma corresponde a `0` (top-left) no Roblox, que é o default — então não precisa ser explicitado.

### 3.5 Detecção de Interatividade

**Local:** `src/parser/properties.ts:157-164`

```typescript
isInteractive(node):
  name.toLowerCase().includes("button" || "btn" || "cta" || "clickable")
  OR "reactions" in node && reactions.length > 0
```

Heurística baseada em naming convention + presença de protótipo interativo no Figma. Pode gerar falsos positivos/negativos.

---

## 4. Mapeamento Figma → Roblox Completo

### 4.1 Tipos de Nó

| Figma Type | Condição Especial | Roblox Tipo |
|---|---|---|
| `TEXT` | isInteractive() | `TextButton` |
| `TEXT` | otherwise | `TextLabel` |
| `FRAME` | hasImageFill() | `ImageLabel` ou `ImageButton` |
| `FRAME` | isInteractive() | `TextButton` |
| `FRAME` | otherwise | `Frame` |
| `GROUP` | same as FRAME | `Frame` / `ImageLabel` |
| `COMPONENT` | same as FRAME | `Frame` / `ImageLabel` |
| `RECTANGLE` | hasImageFill() | `ImageLabel` |
| `RECTANGLE` | otherwise | `Frame` |
| `ELLIPSE` | same as RECTANGLE | `ImageLabel` / `Frame` |
| `POLYGON` | same as RECTANGLE | `ImageLabel` / `Frame` |
| `STAR` | same as RECTANGLE | `ImageLabel` / `Frame` |
| `LINE` | same as RECTANGLE | `ImageLabel` / `Frame` |
| `SLICE` | — | **Ignorado** |
| `VECTOR` | — | **Ignorado** |
| `BOOLEAN_OPERATION` | — | **Ignorado** |

### 4.2 Propriedades de Estilo

| Propriedade Figma | Propriedade Roblox | Conversão |
|---|---|---|
| `fills` (SOLID) | `BackgroundColor3` | `figmaColorToRoblox()` |
| `fills` (SOLID) opacity | `BackgroundTransparency` | `1 - opacity` |
| `fills` (IMAGE) | `Image` + `ScaleType` | `"rbxassetid://0"` |
| `strokes` (SOLID) | `UIStroke.Color` | figmaColorToRoblox |
| `strokes` (SOLID) | `UIStroke.Thickness` | `Math.round(strokeWeight)` |
| `strokes` (SOLID) opacity | `UIStroke.Transparency` | `1 - opacity` |
| `cornerRadius` | `UICorner.CornerRadius` | `Math.round(radius)` |
| `fills` (GRADIENT_LINEAR/RADIAL) | `UIGradient` | extrai stops + rotation |
| `rotation` | `Rotation` | `roundTo(node.rotation, 2)` |
| `clipsContent` | `ClipsDescendants` | boolean pass-through |
| `opacity` (node-level) | `BackgroundTransparency` | compost com fill transparency |
| `constraints` | `AnchorPoint` | CENTER→0.5, MAX→1.0 |
| `characters` | `Text` | raw string escape |
| `fontSize` | `TextSize` | `Math.round(fontSize)` |
| `fontName` | `Font` | mapping dict |
| `textAlignHorizontal` | `TextXAlignment` | Left/Center/Right |
| `textAlignVertical` | `TextYAlignment` | Top/Center/Bottom |
| `textAutoResize` | `TextScaled` / `TextWrapped` | WIDTH_AND_HEIGHT→scaled |

### 4.3 Mapeamento de Fontes

| Figma Font Family | Roblox Font Enum |
|---|---|
| `Roboto` | `Enum.Font.Roboto` |
| `Inter` | `Enum.Font.Gotham` |
| `Arial` | `Enum.Font.Arial` |
| `Open Sans` | `Enum.Font.Gotham` |
| `Source Sans Pro` | `Enum.Font.SourceSans` |
| `Montserrat` | `Enum.Font.GothamBold` |
| `Poppins` | `Enum.Font.GothamMedium` |
| (qualquer outro) | `Enum.Font.Gotham` |

### 4.4 Posição e Tamanho

| Métrica Figma | Saída Roblox | Fórmula |
|---|---|---|
| `absoluteTransform[0][2]` (X absoluto) | `UDim2.xScale` + `UDim2.xOffset` | `(absX - parentAbsX + anchorX * width) / parentWidth` |
| `absoluteTransform[1][2]` (Y absoluto) | `UDim2.yScale` + `UDim2.yOffset` | `(absY - parentAbsY + anchorY * height) / parentHeight` |
| `width` | `UDim2.xScale` + `UDim2.xOffset` | `width / parentWidth` |
| `height` | `UDim2.yScale` + `UDim2.yOffset` | `height / parentHeight` |
| `rotation` | `Rotation` | `roundTo(rotation, 2)` |

### 4.5 Opacity Composited

Quando um nó tem `opacity < 1`, o plugin compõe com a transparência do fill:

```typescript
// nodeOpacity = node.opacity ?? 1
// bgTransparency = 1 - (1 - backgroundTransparency) * nodeOpacity
// Exemplo: fill opacity=0.8, node opacity=0.5
// → final transparency = 1 - (0.2 * 0.5) = 1 - 0.1 = 0.9
```

---

## 5. Limitações e Gaps Identificados

### 5.1 Críticas Estruturais

| # | Gap | Descrição |
|---|---|---|
| 1 | **Exportador Fusion Incompleto** | O modo "fusion" na UI é referenciado mas pouco testado |
| 2 | **Image URL Fixo** | Todos usam `rbxassetid://0`. Nenhuma extração real de assets |
| 3 | **UIListLayout — Falsos Positivos** | Tolerância fixa de 5px em designs grandes causa detecções erradas |
| 4 | **Responsive Rules Limitadas** | Só age em fontSize > 20 e xOffset > 300. Ignora largura proporcional |
| 5 | **Sem Suporte a AutoLayout do Figma** | `isAutoLayout` é capturado mas nunca usado na geração |
| 6 | **Nome de Variáveis Poluído** | "Help (FAQ)" → "Help___FAQ_" em vez de "HelpFAQ" |
| 7 | **Sem Tratamento de Blend Modes** | Multiply, Overlay, etc. ignorados |
| 8 | **Sem Suporte a Mask/Clip Groups** | Apenas `clipsContent` mapeado, masks não processados |
| 9 | **UIStroke LineJoinMode Sempre "Round"** | Não considera configurações reais do Figma |
| 10 | **Sem suporte a Text Fitting/Truncation** | Propriedades `textMatchCase` e `textCase` ignoradas |

### 5.2 Bugs Potenciais

| Bug | Localização | Descrição |
|---|---|---|
| `parentWidth/Height === 0` não tratado em `parseNode` | `nodeParser.ts:25-27` | Posicionamento errado se frame tiver dimensão 0 |
| `nodeCounter` global mutável | `nodeParser.ts:8` | Se houver erro中途, counter pode ficar desincronizado |
| `wrapInScreenGui` cria duplo ScreenGui | `luaExporter.ts:18-22` | Hardcoded "GeneratedUI" pode conflitar |
| `escapeLuaString` não escapa `\0` | `luaExporter.ts:112` | Strings com null bytes quebram o parser Lua |
| `color3FromRGBString` arredonda 3× | `color.ts:12-15` | Erro de 1-2 unidades de cor por arredondamento acumulado |
| `generateResponsiveController` usa `workspace.CurrentCamera` | `breakpoints.ts:17` | Falha se `workspace` for nulo |

---

## 6. Código Melhorado (Implementação Completa)

### 6.1 NameAllocator Melhorado

```typescript
// src/utils/naming.ts — versão melhorada
const RESERVED_WORDS = new Set([
  "and", "break", "do", "else", "elseif", "end", "false", "for",
  "function", "if", "in", "local", "nil", "not", "or", "repeat",
  "return", "then", "true", "until", "while", "continue",
]);

export function sanitizeName(name: string): string {
  // Preserve word boundaries mais limpo
  let clean = name
    .replace(/[^a-zA-Z0-9_]/g, "_")    // special chars → _
    .replace(/_{2,}/g, "_")             // collapse multiple underscores
    .replace(/^_+|_+$/g, "");            // trim leading/trailing
  
  if (clean.length === 0) clean = "unnamed";
  if (/^[0-9]/.test(clean)) clean = "_" + clean;
  if (RESERVED_WORDS.has(clean.toLowerCase())) clean = "_" + clean;
  
  return clean;
}

export class NameAllocator {
  private used = new Map<string, number>();

  allocate(baseName: string): string {
    const clean = sanitizeName(baseName);
    const count = this.used.get(clean) || 0;
    this.used.set(clean, count + 1);
    return count === 0 ? clean : `${clean}_${count}`;
  }

  reset(): void {
    this.used.clear();
  }
}
```

### 6.2 Detecção de AutoLayout do Figma

```typescript
// src/layout/autoLayoutDetector.ts
import { ParsedNode, UIListLayoutData } from "../types";

function mapFigmaAlign(align: string): string {
  const map: Record<string, string> = {
    "MIN": "Left", "CENTER": "Center", "MAX": "Right",
    "BASELINE": "Top",
  };
  return map[align] ?? "Left";
}

export function injectAutoLayouts(root: ParsedNode, figmaNodeMap: Map<string, any>): void {
  for (const child of root.children) {
    if (child.isAutoLayout) {
      const figmaNode = figmaNodeMap.get(child.id);
      if (figmaNode && figmaNode.layoutMode !== "NONE") {
        child.uiListLayout = {
          fillDirection: figmaNode.layoutMode === "HORIZONTAL" ? "Horizontal" : "Vertical",
          padding: Math.round(figmaNode.itemSpacing ?? 0),
          horizontalAlignment: mapFigmaAlign(figmaNode.horizontalAlignContents ?? "MIN"),
          verticalAlignment: mapFigmaAlign(figmaNode.verticalAlignContents ?? "MIN"),
          sortOrder: "LayoutOrder",
        };
      }
    }
    injectAutoLayouts(child, figmaNodeMap);
  }
}
```

### 6.3 Responsividade Aprimorada

```typescript
// src/responsive/breakpoints.ts — versão estendida
export const BREAKPOINTS = {
  mobile: { minWidth: 0, maxWidth: 500 },
  tablet: { minWidth: 501, maxWidth: 1000 },
  desktop: { minWidth: 1001, maxWidth: Infinity },
};

export function generateResponsiveRules(node: ParsedNode): ResponsiveRule[] {
  const rules: ResponsiveRule[] = [];

  // Regra existente: fontSize grande → menor em mobile
  if (node.textSize && node.textSize > 20) {
    rules.push({
      minWidth: BREAKPOINTS.mobile.minWidth,
      maxWidth: BREAKPOINTS.mobile.maxWidth,
      overrides: { textSize: Math.max(12, Math.round(node.textSize * 0.7)) },
    });
  }

  // NOVA: Elementos largos → full-width em mobile
  if (node.size.xScale > 0.5 && node.position.xOffset === 0) {
    rules.push({
      minWidth: BREAKPOINTS.mobile.minWidth,
      maxWidth: BREAKPOINTS.mobile.maxWidth,
      overrides: {
        size: { xScale: 0.95, xOffset: 0, yScale: node.size.yScale, yOffset: node.size.yOffset },
      },
    });
  }

  // NOVA: Vários filhos horizontais → empilhar em mobile
  if (node.children.length >= 2) {
    const allSameY = node.children.every(
      c => Math.abs(c.position.yScale - node.children[0].position.yScale) < 0.01
    );
    if (allSameY) {
      rules.push({
        minWidth: BREAKPOINTS.mobile.minWidth,
        maxWidth: BREAKPOINTS.mobile.maxWidth,
        overrides: {
          position: { xScale: 0, xOffset: 0, yScale: 0, yOffset: 0 },
          size: { xScale: 0.95, xOffset: 0, yScale: node.size.yScale, yOffset: node.size.yOffset },
        },
      });
    }
  }

  return rules;
}
```

### 6.4 Correção de Escape de Strings Lua

```typescript
// src/exporters/luaExporter.ts — correção
function escapeLuaString(s: string): string {
  return s
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r")
    .replace(/\t/g, "\\t")
    .replace(/\0/g, "\\0");  // CORREÇÃO: null byte escape
}
```

---

## 7. Comparação com Plugins Similares

### MiaGobble / Figma-Import-Assistant

| Aspecto | Figma-to-Roblox-LuaU | Figma-Import-Assistant |
|---|---|---|
| **Formato de saída** | LuaU puro (`Instance.new`, Roact, Fusion) | JSON intermediário + plugin Roblox que lê JSON |
| **Posicionamento** | Scale + Offset (proporcional) | Predominantemente Offset puro |
| **AutoLayout detection** | Geométrico (heurística de gaps) | Não possui |
| **Responsividade** | Breakpoints mobile/tablet/desktop | Não possui |
| **Gradientes** | Suportados (UIGradient) | Depende do conversor JSON |
| **Interface** | HTML custom com preview em tempo real | Interface Figma nativa padrão |

### Rawblocky / RobloxPlugin-FigmaToRoblox (Descontinuado)

| Aspecto | Figma-to-Roblox-LuaU | RobloxPlugin-FigmaToRoblox |
|---|---|---|
| **Formato de saída** | Código LuaU legível | Inserção direta de instâncias no Roblox |
| **Posicionamento** | Scale + Offset inteligente | **Puramente Offset** (conforme README do próprio autor) |
| **AutoLayout** | Detecção automática de UIListLayout | Não possui |
| **Responsividade** | Sim, com controller Lua | Não possui |
| **Estado** | Ativo | ❌ Descontinuado |

### Resumo Comparativo

| Feature | Figma-to-Roblox-LuaU | Figma-Import-Assistant | RobloxPlugin-FigmaToRoblox |
|---|---|---|---|
| Escala/Offset | ✅ Inteligente | ⚠️ Via JSON | ❌ Offset only |
| UIListLayout auto | ✅ Detecção geométrica | ❌ | ❌ |
| Gradientes | ✅ UIGradient | ⚠️ Via conversor | ⚠️ Parcial |
| Responsividade | ✅ Breakpoints + controller | ❌ | ❌ |
| Roact/Fusion | ✅ | ❌ | ❌ |
| Inserção direta no Roblox | ❌ (gera código) | ⚠️ (via JSON import) | ✅ (plugin Roblox) |

---

## 8. Conclusão

O plugin **Figma to Roblox LuaU** é uma implementação sólida e bem arquitetada para exportação de UI do Figma para Roblox. Seus pontos fortes principais são:

1. **Posicionamento Scale+Offset inteligente** — muito superior a soluções puramente em offset
2. **Multi-formato de export** (Lua, Roact, Fusion) em um único pipeline
3. **Detecção automática de UIListLayout** — economiza trabalho manual
4. **Suporte a responsividade** com breakpoint controller integrado
5. **Código gerado limpo e legível** com comentários e indentação adequada

Os principais gaps a endereçar são: extração real de assets de imagem, uso efetivo do AutoLayout nativo do Figma, responsividade mais rica (empilhamento em mobile), e sanitização de nomes mais inteligente.
