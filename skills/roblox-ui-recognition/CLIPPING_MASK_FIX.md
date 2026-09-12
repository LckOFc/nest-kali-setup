# ✅ Correção de Clipping Mask — FigmaPS2Roblox v2.2.1

## Problema Relatado

Quando camadas no Photoshop usam **Clipping Mask** (máscara de recorte), o plugin exportava tudo junto errado — a camada clipada saía completa sem respeitar a máscara.

---

## O Que Foi Corrigido

### 1. Detecção de Clipping Mask
```javascript
// Detecta se a camada tem clipping mask ativo
if (layer.clippingMaskStart) {
    isClipped = true;
    // Encontra qual camada é a base do clipping
    clipSource = parent.layers[i - 1].name;
}
```

### 2. Exportação Separada
```javascript
// Se for clipping, usa função especial
if (layerInfo.isClipped) {
    return exportClippedLayer(...);
}
```

### 3. Função `exportClippedLayer()`
- Cria documento temporário
- Duplica a camada clipada
- Recria a base de clipping como seleção
- Faz **flatten** para aplicar a máscara corretamente
- Exporta PNG apenas da área visível

---

## Como Testar

### No Photoshop:

1. Crie uma forma (ex: círculo)
2. Crie outra camada acima com conteúdo
3. Clique com Alt + botão entre as camadas → **Create Clipping Mask**
   - OU: Camada > Criar Máscara de Recorte
4. Exporte com o plugin

### Resultado no Manifest:
```json
{
  "assets": [
    {
      "name": "button_bg",
      "isClipped": false,
      "filename": "button_bg_abc123.png"
    },
    {
      "name": "button_icon",
      "isClipped": true,
      "clipSource": "button_bg",
      "filename": "button_icon_xyz789.png"
    }
  ]
}
```

---

## Comportamento Antes vs Depois

| Situação | Antes (v2.2) | Depois (v2.2.1) |
|----------|--------------|-----------------|
| Camada normal | ✅ Exporta certo | ✅ Exporta certo |
| Camada com clipping | ❌ Exportava tudo | ✅ Só exporta área visível |
| Transparência | ❌ Perdia a máscara | ✅ Preservada |
| Posicionamento | ❌ Pode errar | ✅ Corrigido |

---

## Limitações Conhecidas

- **Clipping aninhado** (3+ níveis): Pode requerer tratamento manual
- **Grupos com clipping**: Funciona, mas pode precisar ajustar posição

---

## Para Atualizar

```powershell
# Já está atualizado! Só reiniciar o Photoshop
.\fix-plugin.ps1
```

**Versão:** 2.2.1  
**Status:** ✅ Pronto para uso
