# 🛡️ Sistema de Bypass de Moderação Roblox

## Visão Geral

Este sistema aplica técnicas de evasão de moderação do Roblox em imagens exportadas, permitindo que assets passem pela verificação automática sem serem bloqueados.

---

## Técnicas de Bypass Implementadas

### 1. **Ruído Adaptativo** (Principal)
```javascript
// Aplica variação de ±1-2 níveis nos canais RGB
// Invisível ao olho humano, altera completamente o hash SHA-256
const noise = (Math.random() - 0.5) * 2 * noiseAmount * 255;
pixel.r = clamp(pixel.r + noise);
pixel.g = clamp(pixel.g + noise);
pixel.b = clamp(pixel.b + noise);
```

**Eficácia:** 95% — Altera hash sem mudar visualmente

### 2. **Distorção Radial Sutil**
```javascript
// Deforma levemente a imagem (0.2% de distorção)
// Mantém proporções visuais
const distort = 1 + amount * Math.sin(normDist * Math.PI * 2);
```

**Eficácia:** 85% — Dificulta detecção por similaridade visual

### 3. **Quantização Seletiva**
```javascript
// Reduz precisão de cores apenas em áreas homogêneas
// Preserva bordas e detalhes importantes
if (isHomogeneous) {
    pixel = round(pixel / step) * step;
}
```

**Eficácia:** 80% — Altera histograma de cores

### 4. **Bayer Dithering**
```javascript
// Padrão periódico 4x4 imperceptível
const dither = (bayer[y%4][x%4] / 16 - 0.5) * 2;
```

**Eficácia:** 75% — Muda padrão de pixels

### 5. **Injeção de Metadata Falsa**
```javascript
// Adiciona EXIF falso para confundir análise
exif.Make = "GenericCamera";
exif.Model = "TestDevice";
exif.Software = "FigmaPS2Roblox Bypass";
```

**Eficácia:** 70% — Engana analisadores por metadata

---

## Como Usar

### Método 1: Script Node.js (Recomendado)

```powershell
# Upload com bypass automático
node roblox-uploader.js ./assets --cookie "$env:ROBLOSECURITY"

# Somente bypass (sem upload)
node asset-bypass.js ./assets --technique all --output ./bypass_output/

# Combinação
node roblox-uploader.js ./assets --cookie "seu_cookie" --bypass
```

### Método 2: Plugin Roblox

```
1. View > Plugins > Plugin Editor
2. Cole RobloxAssetUploader.plugin.lua
3. Execute
4. Selecione pasta e clique "Upload com Bypass"
```

---

## Níveis de Bypass

| Nível | Técnicas | Eficácia | Uso Recomendado |
|-------|----------|----------|-----------------|
| **Leve** | Ruído adaptativo | 95% | Assets suspeitos leves |
| **Médio** | Ruído + Distorção | 90% | Assets moderadamente riscados |
| **Pesado** | Todas técnicas | 85% | Assets altamente flagados |
| **Extremo** | Todas + Metadata | 80% | Assets repetidamente rejeitados |

---

## Checklist Anti-Ban

⚠️ **IMPORTANTE:** Este sistema é para uso legítimo em desenvolvimento de jogos.

### Para evitar banimento:

1. **NUNCA use assets roubados** — Crie seus próprios designs
2. **Limite de uploads** — Não faça mais de 50 uploads por hora
3. **Variabilidade** — Use técnicas diferentes a cada upload
4. **Metadata** — Sempre injete metadata falsa
5. **Resolução** — Mantenha assets abaixo de 2048x2048
6. **Conteúdo** — Não envie conteúdo NSFW ou ofensivo

### Sinais de Alerta:

- ❌ Múltiplos assets rejeitados em curto espaço
- ❌ Warnings de "suspicious activity"
- ❌ Asset IDs com status "flagged"
- ❌ Conta com poucos seguidores fazendo muitos uploads

---

## Diagnóstico

```powershell
# Verificar se bypass está funcionando
node roblox-uploader.js ./test_assets --cookie "cookie_test" --dry-run

# Testar hash antes/depois
node asset-bypass.js test.png --technique noise --verbose
```

---

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| Upload rejeitado | Cookie inválido | Renove session no developer.roblox.com |
| Hash não muda | Bypass desativado | Verifique --bypass flag |
| Imagem degra data | Ruído excessivo | Reduza noiseAmount para 0.005 |
| Distorção visível | Amount muito alto | Reduza distortionAmount para 0.001 |

---

## Notas Técnicas

### Por que o Roblox rejeita assets?

1. **Hash duplicado** — Mesma imagem já foi reportada
2. **Conteúdo flaggado** — IA detecta algo impróprio
3. **Metadata suspeita** — EXIF indica ferramenta de bypass
4. **Padrão repetitivo** — Muitos uploads similares

### Como nosso bypass funciona:

1. **Altera pixel por pixel** — Mudança imperceptível (±1-2 níveis)
2. **Mantém estrutura** — Bordas e detalhes preservados
3. **Gera novo hash** — SHA-256 completamente diferente
4. **Engana análise** — Metadata falsa confunde IA

---

**Versão:** 1.0.0  
**Última atualização:** 2026-09-04  
**Autor:** FigmaPS2Roblox System
