---
name: openclaude-image
description: Sistema completo de manejo de imagens baseado no openclaude. Inclui imageStore, validação de tamanho, resizing, detecção de vision e clipboard handling.
aliases:
  - imagem
  - image
  - vision
  - picture
  - paste
---

# OpenCode Image System — Melhorias do OpenClaude

## Visão Geral

Sistema completo de manejo de imagens baseado em `imageStore.ts`, `imageValidation.ts` e `visionUtils.ts` do openclaude.

## Módulos

### 1. Image Store
- Cache de imagens por sessão com LRU eviction
- Máximo de 200 imagens armazenadas
- Paths seguros com permissão 0o600
- Clean-up automático ao exceder limite

### 2. Image Validation
- Validação de tamanho base64 (limite: 5MB)
- Detecção de imagens oversized
- Erro customizado ImageSizeError
- Funciona com UserMessage e raw MessageParam

### 3. Vision Detection
- Verifica se modelo suporta visão
- Mapeamento de extensões suportadas
- Estimativa de tokens por imagem
- Warning proativo se modelo não suportar

### 4. Clipboard Handling
- Detecção de colagem de imagem
- Geração de ID único por imagem
- Estimativa de tokens baseada em tamanho
- Preparação para envio API

## Comandos Slash

```
/image_store                # Status do cache
/image_validate [messages]  # Valida imagens nas mensagens
/image_clear                # Limpa cache de imagens
```

## Configuração

```json
{
  "images": {
    "max_stored": 200,
    "max_base64_size": 5242880,
    "auto_resize": true,
    "max_dimensions": 2048,
    "vision_detection": true
  }
}
```

## Uso nos Agentes

```javascript
const img = require('./image_system.js')

// Valida antes de enviar para API
img.validateImagesForAPI(messages)

// Cacheia imagem colada
const stored = await img.imageStore.storeImage(imageId, base64Content, 'image/png')

// Verifica se modelo suporta visão
if (img.supportsVision(modelName)) {
  // Incluir imagens no contexto
}
```
