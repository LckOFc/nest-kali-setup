# 🎨 Filtro de Pranchetas — FigmaPS2Roblox v2.2

## O que foi adicionado

Agora você pode **selecionar uma prancheta (artboard)** específica no Photoshop e o plugin só processará as camadas **dentro dessa prancheta**, igual ao Figma.

---

## Como Usar

### 1. No Photoshop

1. Abra seu documento PSD
2. **Selecione uma prancheta** na tela (clique na artboard que deseja exportar)
   - Ou selecione camadas específicas dentro de uma prancheta

### 2. No Plugin FigmaPS2Roblox

1. Vá para a aba **Camadas**
2. Veja o seletor de pranchetas no topo:
   ```
   🎯 SELECIONAR PRANCHETA:
   [Todas] [Main Menu] [Shop] [HUD] [Mobile]
   ```
3. Clique no nome da prancheta que deseja exportar
4. A lista de camadas será atualizada mostrando **apenas** as camadas daquela prancheta
5. Configure e exporte normalmente

---

## Comportamento

| Seleção | O que é exportado |
|---------|-------------------|
| **Todas** | Todas as camadas do documento (comportamento anterior) |
| **Main Menu** | Apenas camadas dentro da prancheta "Main Menu" |
| **Shop** | Apenas camadas dentro da prancheta "Shop" |
| **HUD** | Apenas camadas dentro da prancheta "HUD" |

---

## Exemplo de Uso

```
Documento: GameUI.psd
├── 📐 Main Menu (1920×1080)
│   ├── Background
│   ├── Play Button
│   └── Settings Button
├── 📐 Shop (1920×1080)
│   ├── Shop Background
│   ├── Item Card 1
│   ├── Item Card 2
│   └── Buy Button
└── 📐 HUD (1920×1080)
    ├── Health Bar
    └── Score Display
```

**Cenário:** Você quer exportar apenas a tela de Shop

**Passos:**
1. No Photoshop, clique na prancheta "Shop"
2. No plugin, clique no botão "Shop" no seletor
3. A lista de camadas mostra apenas:
   - Shop Background
   - Item Card 1
   - Item Card 2
   - Buy Button
4. Exporte → Apenas esses 4 assets serão gerados

---

## Requisitos

- Photoshop CC 2020 ou superior
- Document com Artboards (não apenas camadas normais)
- Plugin FigmaPS2Roblox v2.2+

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Botões de prancheta não aparecem | Verifique se o PSD tem artboards |
| Prancheta selecionada mas camadas não filtram | Reinicie o Photoshop e reabra o plugin |
| "Desconectado" após seleção | Execute `.\troubleshoot.ps1 --fix` |

---

**Versão:** 2.2.0
**Data:** 2026-09-04
