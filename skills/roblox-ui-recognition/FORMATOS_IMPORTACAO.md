# 📋 Formato de Importação — FigmaPS2Roblox vs Figblox

## O que estamos usando

Nós usamos o **Universal Design Schema (UDS)** + **Manifest JSON** para importação.

---

## 📊 Comparação de Formatos

### Nosso Formato (UDS + Manifest)

```json
{
  "schemaVersion": "1.0.0",
  "source": "photoshop",
  "document": {
    "name": "GameUI.psd",
    "width": 1920,
    "height": 1080,
    "resolution": 72,
    "colorMode": "RGB"
  },
  "artboards": [
    {
      "id": "artboard_abc123",
      "name": "Main Menu",
      "x": 0,
      "y": 0,
      "width": 1920,
      "height": 1080,
      "visible": true
    }
  ],
  "layers": [
    {
      "id": "layer_xyz789",
      "name": "Play Button",
      "type": "layer",
      "visible": true,
      "opacity": 100,
      "bounds": {
        "x": 810,
        "y": 500,
        "width": 300,
        "height": 80
      },
      "semantic": {
        "probableRole": "button",
        "confidence": 0.95
      },
      "fill": {
        "hex": "#89B4FA"
      },
      "text": {
        "content": "PLAY",
        "size": 28,
        "font": "GothamBold"
      }
    }
  ],
  "assets": [
    {
      "id": "asset_001",
      "name": "btn_play",
      "path": "btn_play_abc123.png",
      "width": 300,
      "height": 80,
      "format": "png"
    }
  ],
  "colors": [
    { "hex": "#89B4FA", "usage": ["button"] }
  ],
  "fonts": ["Gotham", "GothamBold"]
}
```

### Formato do Manifest (para Roblox)

```json
{
  "name": "MainMenu",
  "canvasWidth": 1920,
  "canvasHeight": 1080,
  "scaleMode": "ScaleToFit",
  "seed": "abc123def456",
  "assets": [
    {
      "uniqueId": "abc123def456",
      "filename": "bg_main_abc123def456.png",
      "type": "background",
      "name": "bg_main",
      "x": 0,
      "y": 0,
      "width": 1920,
      "height": 1080,
      "assetId": "rbxassetid://123456789"
    }
  ],
  "elements": [
    {
      "name": "Play Button",
      "type": "button",
      "robloxClass": "TextButton",
      "x": 810,
      "y": 500,
      "width": 300,
      "height": 80,
      "properties": {
        "text": "PLAY",
        "textSize": 28,
        "backgroundColor": "#89B4FA",
        "cornerRadius": 12
      }
    }
  ],
  "layoutHints": {
    "verticalGroups": [...],
    "horizontalGroups": [...]
  }
}
```

---

## 🎯 Formato do Figblox (Referência)

O figblox usa um formato JSON específico para importar UIs do Figma:

```json
{
  "name": "ScreenGui",
  "resetOnSpawn": false,
  "zIndexBehavior": "Sibling",
  "instances": [
    {
      "classType": "Frame",
      "name": "Container",
      "properties": {
        "Size": {"X": {"Scale": 0.5}, "Y": {"Scale": 0.5}},
        "Position": {"X": {"Scale": 0.25}, "Y": {"Scale": 0.25}},
        "BackgroundColor3": {"R": 0.2, "G": 0.2, "B": 0.2},
        "BorderSizePixel": 0
      },
      "children": [
        {
          "classType": "UICorner",
          "properties": {
            "CornerRadius": {"Scale": 0.1}
          }
        }
      ]
    }
  ]
}
```

---

## 🔍 Comparação Técnica

| Aspecto | Nosso Formato (UDS) | Figblox Format |
|---------|---------------------|----------------|
| **Fonte** | Photoshop/Figma/Sketch/XD | Apenas Figma |
| **Estrutura** | Camadas + Artboards | Hierarquia de instâncias |
| **Assets** | Separado (PNGs + JSON) | Inline (Base64 ou URL) |
| **Semântica** | Rica (roles, confidence) | Básica |
| **Responsividade** | Incluída (strategies) | Não inclusa |
| **IA Ready** | ✅ Sim (estrutura clara) | ❌ Não |
| **Bypass** | ✅ Suportado | ❌ Não |

---

## 📝 Por que Nosso Formato é Melhor

### 1. **Universal Design Schema (UDS)**
- Funciona com **múltiplas fontes**: Photoshop, Figma, Sketch, XD
- Estrutura padronizada que a IA pode entender
- IDs estáveis para tracking de elementos

### 2. **Semântica Rica**
```json
"semantic": {
  "probableRole": "button",
  "confidence": 0.95
}
```
A IA sabe que é um botão com 95% de confiança.

### 3. **Responsividade Incluída**
```json
"responsive": {
  "strategy": "ScaleToFit",
  "mobileScale": 0.9,
  "minWidth": 200
}
```
Estratégia de escala para diferentes dispositivos.

### 4. **Separation of Concerns**
- **UDS**: Estrutura do design (para IA)
- **Manifest**: Especificação Roblox (para importação)
- **Controller**: Código gerado (para uso)

---

## 🔄 Fluxo de Conversão

```
PSD/Figma/Sketch
       │
       ▼
  Universal Design Schema (UDS)
  (estrutura rica + semântica)
       │
       ▼
  AI Analysis (OpenAI/Claude)
  (análise inteligente)
       │
       ▼
  Roblox Manifest JSON
  (especificação para Roblox)
       │
       ▼
  Controller Lua
  (código pronto)
       │
       ▼
  Roblox Studio
  (importação manual dos PNGs)
```

---

## 💡 Vantagens do Nosso Formato

1. **Multi-fonte**: Não preso ao Figma
2. **IA-ready**: Estrutura clara para análise
3. **Responsivo**: Estratégias de escala incluídas
4. **Anti-reuploader**: Hash único nos assets
5. **Bypass**: Técnicas de evasão de moderação
6. **Hierárquico**: Groups e artboards preservados

---

**Resumo:** Nós usamos um formato ** UD (Universal Design) + Manifest Roblox** que é mais rico e flexível que o formato do figblox, com suporte a IA, responsividade e múltiplas fontes de design.
