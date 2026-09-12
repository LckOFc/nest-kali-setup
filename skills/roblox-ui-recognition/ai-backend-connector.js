/**
 * ai-backend-connector.js
 *
 * Conecta o PSD Intelligence Scanner a um backend de IA (OpenAI, Claude, etc.)
 * Envia a estrutura do PSD + imagem para análise e recebe:
 *   - Especificação completa da UI Roblox
 *   - Código Luau gerado
 *   - Recomendações de responsive design
 *
 * Uso:
 *   const AIConnector = require('./ai-backend-connector');
 *   const connector = new AIConnector({ apiKey: 'sk-...' });
 *   const result = await connector.analyze(uds);
 */

const https = require("node:https");
const fs = require("node:fs");
const path = require("path");

// ── Config ────────────────────────────────────────────────────────────────────

const CONFIG = {
    apiEndpoint: "https://api.openai.com/v1/chat/completions",
    model: "gpt-4o",
    maxTokens: 4096,
    temperature: 0.3,
    timeout: 60000, // 60 segundos
};

// ── Sistema Prompt ────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `Você é um especialista em UI/UX para Roblox com 10+ anos de experiência.

Sua tarefa é analisar designs de Photoshop/Figma e converter para interfaces Roblox funcionais.

REGRAS IMPORTANTES:
1. O canvas padrão do Roblox é 1920x1080 (fullscreen HD)
2. Use Scale+Offset para posicionamento responsivo (UDim2)
3. Backgrounds devem usar ScaleType="Fill" e ocupar tela inteira
4. Botões usam TextButton, labels usam TextLabel, imagens usam ImageLabel
5. Use UICorner para bordas arredondadas
6. Use UIListLayout para elementos alinhados em lista
7. Sempre sugira estratégias responsivas (PC, Mobile, Tablet)

FORMATO DE RESPOSTA:
Você deve retornar UM JSON válido com esta estrutura:
{
  "screenName": "nome_da_tela",
  "canvasWidth": 1920,
  "canvasHeight": 1080,
  "elements": [
    {
      "id": "layer_xxx",
      "name": "NomeElemento",
      "robloxClass": "TextButton",
      "position": { "xScale": 0.5, "yScale": 0.5, "xOffset": 0, "yOffset": 0 },
      "size": { "xScale": 0.2, "yScale": 0.1, "xOffset": 0, "yOffset": 0 },
      "properties": {
        "text": "BUY NOW",
        "textSize": 24,
        "textColor": "#FFFFFF",
        "backgroundColor": "#1E1E2E",
        "cornerRadius": 8
      },
      "responsive": {
        "strategy": "ScaleToFit",
        "mobileScale": 0.8,
        "minSize": { "width": 200, "height": 50 }
      }
    }
  ],
  "layoutHints": {
    "verticalGroups": [...],
    "horizontalGroups": [...],
    "listLayouts": [...]
  },
  "fonts": {
    "primary": "GothamBold",
    "fallback": "Gotham"
  },
  "colors": {
    "primary": "#89B4FA",
    "secondary": "#A6E3A1",
    "background": "#1E1E2E"
  },
  "notes": "Observações sobre o design"
}`;

// ── AI Connector Class ────────────────────────────────────────────────────────

class AIConnector {
    constructor(options = {}) {
        this.apiKey = options.apiKey || process.env.OPENAI_API_KEY;
        this.apiEndpoint = options.apiEndpoint || CONFIG.apiEndpoint;
        this.model = options.model || CONFIG.model;
        this.timeout = options.timeout || CONFIG.timeout;
        this.maxRetries = options.maxRetries || 3;
    }

    /**
     * Analisa o UDS e gera especificação Roblox
     */
    async analyze(uds, userPrompt = null) {
        if (!this.apiKey) {
            throw new Error("API Key não fornecida. Defina OPENAI_API_KEY ou passe apiKey nas opções.");
        }

        // Preparar payload
        const messages = [
            { role: "system", content: SYSTEM_PROMPT },
            {
                role: "user",
                content: this._buildUserMessage(uds, userPrompt),
            },
        ];

        const payload = {
            model: this.model,
            messages: messages,
            max_tokens: CONFIG.maxTokens,
            temperature: CONFIG.temperature,
            response_format: { type: "json_object" },
        };

        // Fazer request com retry
        let lastError;
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await this._request(payload);
                return this._parseResponse(response);
            } catch (e) {
                lastError = e;
                if (attempt < this.maxRetries) {
                    console.warn(`[AI] Tentativa ${attempt} falhou: ${e.message}. Tentando novamente...`);
                    await this._delay(1000 * attempt);
                }
            }
        }

        throw new Error(`Falha após ${this.maxRetries} tentativas: ${lastError.message}`);
    }

    /**
     * Gera código Luau a partir da especificação
     */
    async generateLua(specification, screenName) {
        if (!this.apiKey) {
            throw new Error("API Key não fornecida.");
        }

        const messages = [
            { role: "system", content: this._getLuaSystemPrompt() },
            {
                role: "user",
                content: ` Gere o código Luau completo para a seguinte especificação de UI Roblox:\n\n${JSON.stringify(specification, null, 2)}\n\nNome da tela: ${screenName}`,
            },
        ];

        const payload = {
            model: this.model,
            messages: messages,
            max_tokens: 4096,
            temperature: 0.2,
        };

        try {
            const response = await this._request(payload);
            const content = response.choices[0].message.content;
            // Extrair código Lua do markdown
            const luaCode = content.match(/```lua\n([\s\S]*?)\n```/)?.[1] || content;
            return luaCode.trim();
        } catch (e) {
            throw new Error(`Falha ao gerar código Lua: ${e.message}`);
        }
    }

    /**
     * Responde pergunta sobre o PSD
     */
    async askAboutPSD(uds, question) {
        if (!this.apiKey) {
            throw new Error("API Key não fornecida.");
        }

        const messages = [
            { role: "system", content: this._getQASystemPrompt() },
            {
                role: "user",
                content: `Analise este design de UI e responda: "${question}"\n\nEstrutura do PSD:\n${JSON.stringify(uds, null, 2)}`,
            },
        ];

        const payload = {
            model: this.model,
            messages: messages,
            max_tokens: 1024,
            temperature: 0.5,
        };

        try {
            const response = await this._request(payload);
            return response.choices[0].message.content;
        } catch (e) {
            throw new Error(`Falha na resposta QA: ${e.message}`);
        }
    }

    // ── Private Methods ──────────────────────────────────────────────────────

    _buildUserMessage(uds, userPrompt) {
        let content = `Analise o seguinte design de UI e converta para Roblox.\n\n`;
        content += `## Documento\n`;
        content += `- Nome: ${uds.document?.name || "Untitled"}`;
        content += `- Tamanho: ${uds.document?.width || 1920} × ${uds.document?.height || 1080}`;
        content += `- Resolução: ${uds.document?.resolution || 72} DPI\n\n`;

        content += `## Estrutura de Layers\n`;
        for (const layer of uds.layers || []) {
            content += `- [${layer.semantic?.probableRole || "layer"}] ${layer.name} (${layer.bounds?.width || 0}×${layer.bounds?.height || 0}, posição: ${layer.bounds?.x || 0},${layer.bounds?.y || 0})`;
            if (layer.fill) content += ` | cor: ${layer.fill.hex}`;
            if (layer.text) content += ` | texto: "${layer.text.content}"`;
            content += `\n`;
        }

        content += `\n## Grupos\n`;
        for (const group of uds.groups || []) {
            content += `- ${group.name}\n`;
        }

        if (userPrompt) {
            content += `\n## Solicitação do usuário\n${userPrompt}\n`;
        }

        content += `\nPor favor, gere uma especificação Roblox completa com posições responsivas, tamanhos adequados e propriedades visuais.`;
        return content;
    }

    _getLuaSystemPrompt() {
        return `Você é um desenvolvedor Roblox experiente. Sua tarefa é gerar código Luau limpo, bem estruturado e pronto para uso.

REQUISITOS:
- Usar !strict no início
- Criar classe/module pattern
- Usar UDim2.new(scaleX, offsetX, scaleY, offsetY) para posições
- Usar Instance.new() para criar elementos
- Adicionar comentários explicativos
- Suportar responsive design (detecção de dispositivo)
- Usar Players.LocalPlayer:WaitForChild("PlayerGui") como target

EXEMPLO DE ESTRUTURA:
\`\`\`lua
--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GeneratedUI = {}
GeneratedUI.__index = GeneratedUI

function GeneratedUI.new()
    local self = setmetatable({}, GeneratedUI)
    self.Elements = {}
    return self
end

function GeneratedUI:Build(parent)
    local screenGui = Instance.new("ScreenGui")
    screenGui.Name = "GeneratedUI"
    screenGui.ResetOnSpawn = false
    screenGui.IgnoreGuiInset = true
    screenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")
    
    -- Elementos serão criados aqui
    return screenGui
end

return GeneratedUI
\`\`\``;
    }

    _getQASystemPrompt() {
        return `Você é um analista de UI/UX especializado em Roblox. Responda perguntas sobre designs de interface de forma técnica e prática.

FOCO:
- Compatibilidade com Roblox
- Performance (número de instances)
- Responsividade
- Melhores práticas de organização`;
    }

    _parseResponse(response) {
        try {
            const content = response.choices[0].message.content;
            return JSON.parse(content);
        } catch (e) {
            // Se não for JSON válido, tentar extrair
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
            throw new Error(`Resposta não é JSON válido: ${content.substring(0, 200)}`);
        }
    }

    _request(payload) {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify(payload);

            const options = {
                hostname: new URL(this.apiEndpoint).hostname,
                path: new URL(this.apiEndpoint).pathname,
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${this.apiKey}`,
                    "Content-Length": Buffer.byteLength(data),
                },
            };

            const req = https.request(options, (res) => {
                let responseBody = "";

                res.on("data", (chunk) => {
                    responseBody += chunk;
                });

                res.on("end", () => {
                    if (res.statusCode !== 200) {
                        reject(new Error(`API Error ${res.statusCode}: ${responseBody}`));
                        return;
                    }

                    try {
                        resolve(JSON.parse(responseBody));
                    } catch (e) {
                        reject(new Error(`Failed to parse response: ${e.message}`));
                    }
                });
            });

            req.on("error", (e) => {
                reject(new Error(`Request error: ${e.message}`));
            });

            req.setTimeout(this.timeout, () => {
                req.destroy();
                reject(new Error("Request timeout"));
            });

            req.write(data);
            req.end();
        });
    }

    _delay(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}

// ── Factory ───────────────────────────────────────────────────────────────────

function createAIConnector(options) {
    return new AIConnector(options);
}

// ── Export ─────────────────────────────────────────────────────────────────────

module.exports = {
    AIConnector,
    createAIConnector,
    CONFIG,
};
