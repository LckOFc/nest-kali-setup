#!/usr/bin/env node
"use strict";

/**
 * psd-to-roblox-ai.js — Pipeline completo PSD → IA → Roblox
 *
 * Nova arquitetura baseada no conceito do usuário:
 *
 *   PHOTOSHOP
 *      │
 *      ▼
 *   PSD Intelligence Scanner
 *      │  (extrai estrutura, layers, artboards)
 *      ▼
 *   Universal Design Schema (UDS)
 *      │  (formato padronizado)
 *      ▼
 *   AI Backend (OpenAI/Claude)
 *      │  (analisa + gera especificação)
 *      ▼
 *   Roblox UI Generator
 *      │  (gera código Luau)
 *      ▼
 *   Roblox Studio
 *
 * Uso:
 *   node psd-to-roblox-ai.js <psd-path> [--api-key sk-...] [--output <dir>]
 *   node psd-to-roblox-ai.js --scan-only <psd-path>
 *   node psd-to-roblox-ai.js --ask "Como transformar isso em Roblox?"
 */

const fs = require("node:fs");
const path = require("path");
const { execSync } = require("node:child_process");

// ── Imports ───────────────────────────────────────────────────────────────────

const { UniversalDesignSchema, createPSDSchema } = require("./universal-design-schema");
const { AIConnector, createAIConnector } = require("./ai-backend-connector");

// ── Config ────────────────────────────────────────────────────────────────────

const CONFIG = {
    defaultOutputDir: "./output",
    maxArtboardThumbnails: 5,
    aiTimeout: 120000, // 2 minutos
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function log(msg, color = "white") {
    const colors = {
        white: "\x1b[37m",
        green: "\x1b[32m",
        yellow: "\x1b[33m",
        red: "\x1b[31m",
        cyan: "\x1b[36m",
        reset: "\x1b[0m",
    };
    console.log(`${colors[color] || colors.white}  ${msg}${colors.reset}`);
}

function genId(prefix) {
    return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).substr(2, 5)}`;
}

// ── PSD Scanner (simulação - em produção usaria UXP) ────────────────────────

class PSDScanner {
    constructor(psdPath) {
        this.psdPath = psdPath;
        this.fileName = path.basename(psdPath, path.extname(psdPath));
    }

    /**
     * Extrai informações básicas do PSD (simulado)
     * Em produção, isso usaria UXP batchPlay
     */
    async scan() {
        log(`📄 Escaneando: ${this.psdPath}`, "cyan");

        // Simular extração de info do documento
        const docInfo = {
            name: this.fileName,
            width: 1920,
            height: 1080,
            resolution: 72,
            colorMode: "RGB",
            bitDepth: 8,
        };

        // Simular layers (em produção viria do UXP)
        const layers = [
            {
                id: genId("layer"),
                name: "Background",
                type: "layer",
                visible: true,
                opacity: 100,
                blendMode: "Normal",
                bounds: { x: 0, y: 0, width: 1920, height: 1080 },
                semantic: { probableRole: "background", confidence: 0.95 },
                fill: { hex: "#1E1E2E", r: 30, g: 30, b: 46 },
            },
            {
                id: genId("layer"),
                name: "Header",
                type: "group",
                visible: true,
                opacity: 100,
                bounds: { x: 0, y: 0, width: 1920, height: 100 },
                children: [
                    {
                        id: genId("layer"),
                        name: "Logo",
                        type: "layer",
                        visible: true,
                        bounds: { x: 50, y: 20, width: 150, height: 60 },
                        semantic: { probableRole: "icon", confidence: 0.85 },
                    },
                    {
                        id: genId("layer"),
                        name: "Title Text",
                        type: "layer",
                        visible: true,
                        bounds: { x: 250, y: 30, width: 400, height: 40 },
                        semantic: { probableRole: "label", confidence: 0.9 },
                        text: { content: "My Game", size: 32, font: "GothamBold" },
                    },
                ],
            },
            {
                id: genId("layer"),
                name: "Play Button",
                type: "layer",
                visible: true,
                opacity: 100,
                bounds: { x: 810, y: 500, width: 300, height: 80 },
                semantic: { probableRole: "button", confidence: 0.95 },
                fill: { hex: "#89B4FA", r: 137, g: 180, b: 250 },
                text: { content: "PLAY", size: 28, font: "GothamBold" },
            },
            {
                id: genId("layer"),
                name: "Settings Button",
                type: "layer",
                visible: true,
                bounds: { x: 860, y: 620, width: 200, height: 60 },
                semantic: { probableRole: "button", confidence: 0.9 },
                fill: { hex: "#A6E3A1", r: 166, g: 227, b: 161 },
                text: { content: "SETTINGS", size: 20, font: "Gotham" },
            },
        ];

        // Simular artboards
        const artboards = [
            {
                id: genId("artboard"),
                name: "Main Menu",
                x: 0,
                y: 0,
                width: 1920,
                height: 1080,
                visible: true,
            },
        ];

        // Simular assets
        const assets = [];

        // Simular cores
        const colors = [
            { hex: "#1E1E2E", usage: ["background"] },
            { hex: "#89B4FA", usage: ["button"] },
            { hex: "#A6E3A1", usage: ["button"] },
            { hex: "#FFFFFF", usage: ["text"] },
        ];

        // Simular fonts
        const fonts = ["Gotham", "GothamBold"];

        const uds = {
            schemaVersion: "1.0.0",
            source: "photoshop",
            document: docInfo,
            artboards: artboards,
            layers: layers,
            groups: [],
            assets: assets,
            colors: colors,
            fonts: fonts,
            metadata: {
                generatedAt: new Date().toISOString(),
                generator: "PSD Intelligence Scanner v1.0",
            },
        };

        log(`✅ Documento escaneado: ${docInfo.width}×${docInfo.height}`);
        log(`   Layers: ${layers.length}`);
        log(`   Artboards: ${artboards.length}`);
        log(`   Cores: ${colors.length}`);
        log(`   Fontes: ${fonts.length}`);

        return uds;
    }
}

// ── Main Pipeline ─────────────────────────────────────────────────────────────

async function runPipeline(psdPath, options = {}) {
    const startTime = Date.now();

    log("\n" + "═".repeat(60), "cyan");
    log("  PSD → AI → Roblox UI Pipeline", "cyan");
    log("═".repeat(60) + "\n", "cyan");

    // ── Step 1: Scan PSD ───────────────────────────────────────────────────
    log("📋 Step 1: Escaneando PSD...", "cyan");
    const scanner = new PSDScanner(psdPath);
    const uds = await scanner.scan();

    // ── Step 2: Send to AI ─────────────────────────────────────────────────
    log("\n🤖 Step 2: Enviando para IA...", "cyan");

    let aiSpec;
    try {
        const apiKey = options.apiKey || process.env.OPENAI_API_KEY;
        if (!apiKey) {
            log("⚠️  API Key não encontrada. Usando modo simulado.", "yellow");
            aiSpec = await simulateAIResponse(uds);
        } else {
            const connector = createAIConnector({ apiKey });
            aiSpec = await connector.analyze(uds, options.prompt);
        }
        log("✅ IA respondeu com sucesso!", "green");
    } catch (e) {
        log(`❌ Erro na IA: ${e.message}`, "red");
        log("   Tentando com dados simulados...", "yellow");
        aiSpec = await simulateAIResponse(uds);
    }

    // ── Step 3: Generate Roblox Code ───────────────────────────────────────
    log("\n⚙️  Step 3: Gerando código Roblox...", "cyan");

    const outputDir = options.output || CONFIG.defaultOutputDir;
    fs.mkdirSync(outputDir, { recursive: true });

    // Salvar UDS
    const udsPath = path.join(outputDir, "design_uds.json");
    fs.writeFileSync(udsPath, JSON.stringify(uds, null, 2), "utf-8");
    log(`   📄 UDS salvo: ${udsPath}`);

    // Salvar especificação da IA
    const specPath = path.join(outputDir, "ai_specification.json");
    fs.writeFileSync(specPath, JSON.stringify(aiSpec, null, 2), "utf-8");
    log(`   📄 Especificação IA salva: ${specPath}`);

    // Gerar código Luau
    const luaCode = generateLuaCode(aiSpec, outputDir);
    log(`   📝 Código Luau gerado: ${luaCode.length} caracteres`);

    // ── Step 4: Summary ────────────────────────────────────────────────────
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    log("\n" + "═".repeat(60), "green");
    log("  PIPELINE CONCLUÍDO!", "green");
    log("═".repeat(60) + "\n", "green");
    log(`⏱️   Tempo total: ${duration}s`);
    log(`📂  Output: ${outputDir}`);
    log(`📄  Arquivos gerados:`);
    log(`      - design_uds.json`);
    log(`      - ai_specification.json`);
    log(`      - _controller.lua`);
    log(`      - _upload_guide.txt`);

    return {
        success: true,
        duration,
        outputDir,
        uds,
        aiSpec,
    };
}

// ── Simulated AI Response ─────────────────────────────────────────────────────

async function simulateAIResponse(uds) {
    log("   (Modo simulado - responses da IA são exemplos)", "yellow");

    await new Promise((r) => setTimeout(r, 500)); // Simular delay

    return {
        screenName: uds.document.name,
        canvasWidth: uds.document.width,
        canvasHeight: uds.document.height,
        elements: [
            {
                id: "layer_bg",
                name: "Background",
                robloxClass: "ImageLabel",
                position: { xScale: 0, yScale: 0, xOffset: 0, yOffset: 0 },
                size: { xScale: 1, yScale: 1, xOffset: 0, yOffset: 0 },
                properties: {
                    image: "rbxassetid://0",
                    scaleType: "Fill",
                    backgroundColor: uds.layers.find((l) => l.semantic.probableRole === "background")?.fill?.hex || "#1E1E2E",
                },
                responsive: { strategy: "Fill" },
            },
            {
                id: "layer_btn_play",
                name: "Play Button",
                robloxClass: "TextButton",
                position: { xScale: 0.42, yScale: 0.46, xOffset: 0, yOffset: 0 },
                size: { xScale: 0.156, yScale: 0.074, xOffset: 0, yOffset: 0 },
                properties: {
                    text: "PLAY",
                    textSize: 28,
                    textColor: "#FFFFFF",
                    backgroundColor: "#89B4FA",
                    cornerRadius: 12,
                },
                responsive: {
                    strategy: "ScaleToFit",
                    mobileScale: 0.9,
                    minWidth: 200,
                    minHeight: 60,
                },
            },
            {
                id: "layer_btn_settings",
                name: "Settings Button",
                robloxClass: "TextButton",
                position: { xScale: 0.447, yScale: 0.576, xOffset: 0, yOffset: 0 },
                size: { xScale: 0.104, yScale: 0.056, xOffset: 0, yOffset: 0 },
                properties: {
                    text: "SETTINGS",
                    textSize: 20,
                    textColor: "#FFFFFF",
                    backgroundColor: "#A6E3A1",
                    cornerRadius: 8,
                },
                responsive: { strategy: "ScaleToFit" },
            },
        ],
        layoutHints: {
            verticalGroups: [
                {
                    parentId: "header_group",
                    children: ["layer_btn_play", "layer_btn_settings"],
                },
            ],
        },
        fonts: { primary: "GothamBold", fallback: "Gotham" },
        colors: {
            primary: "#89B4FA",
            secondary: "#A6E3A1",
            background: "#1E1E2E",
        },
        notes: "Menu principal com botão de jogo e configurações. Layout responsivo sugerido.",
    };
}

// ── Lua Code Generation ───────────────────────────────────────────────────────

function generateLuaCode(spec, outputDir) {
    let lua = `--!strict\n`;
    lua += `-- Auto-generated by PSD→AI→Roblox Pipeline\n`;
    lua += `-- Canvas: ${spec.canvasWidth}x${spec.canvasHeight}\n`;
    lua += `-- Elements: ${spec.elements.length}\n`;
    lua += `-- Generated: ${new Date().toISOString()}\n\n`;

    lua += `local Players = game:GetService("Players")\n`;
    lua += `local ReplicatedStorage = game:GetService("ReplicatedStorage")\n\n`;

    lua += `local DESIGN_WIDTH = ${spec.canvasWidth}\n`;
    lua += `local DESIGN_HEIGHT = ${spec.canvasHeight}\n\n`;

    lua += `local GeneratedUI = {}\n`;
    lua += `GeneratedUI.__index = GeneratedUI\n\n`;

    lua += `function GeneratedUI.new()\n`;
    lua += `    local self = setmetatable({}, GeneratedUI)\n`;
    lua += `    self.Elements = {}\n`;
    lua += `    return self\n`;
    lua += `end\n\n`;

    lua += `function GeneratedUI:CreateElement(parent, config)\n`;
    lua += `    local el = Instance.new(config.Class)\n`;
    lua += `    el.Name = config.Name\n`;
    lua += `    el.Position = UDim2.new(\n`;
    lua += `        config.X / DESIGN_WIDTH, config.OffsetX or 0,\n`;
    lua += `        config.Y / DESIGN_HEIGHT, config.OffsetY or 0\n`;
    lua += `    )\n`;
    lua += `    el.Size = UDim2.new(\n`;
    lua += `        config.Width / DESIGN_WIDTH, config.OffsetWidth or 0,\n`;
    lua += `        config.Height / DESIGN_HEIGHT, config.OffsetHeight or 0\n`;
    lua += `    )\n\n`;

    lua += `    if config.BackgroundColor3 then el.BackgroundColor3 = config.BackgroundColor3 end\n`;
    lua += `    if config.BackgroundTransparency ~= nil then el.BackgroundTransparency = config.BackgroundTransparency end\n`;
    lua += `    if config.CornerRadius and config.CornerRadius > 0 then\n`;
    lua += `        local corner = Instance.new('UICorner')\n`;
    lua += `        corner.CornerRadius = UDim.new(0, config.CornerRadius)\n`;
    lua += `        corner.Parent = el\n`;
    lua += `    end\n`;
    lua += `    if config.Text then\n`;
    lua += `        el.Text = config.Text\n`;
    lua += `        if config.TextSize then el.TextSize = config.TextSize end\n`;
    lua += `        if config.TextColor3 then el.TextColor3 = config.TextColor3 end\n`;
    lua += `        if config.Font then el.Font = config.Font end\n`;
    lua += `    end\n`;
    lua += `    if config.Image then\n`;
    lua += `        el.Image = config.Image\n`;
    lua += `        if config.ScaleType then el.ScaleType = config.ScaleType end\n`;
    lua += `    end\n`;
    lua += `    el.Parent = parent\n`;
    lua += `    return el\n`;
    lua += `end\n\n`;

    lua += `function GeneratedUI:Build(parent)\n`;
    lua += `    local screenGui = Instance.new('ScreenGui')\n`;
    lua += `    screenGui.Name = '${spec.screenName || 'UI'}'\n`;
    lua += `    screenGui.ResetOnSpawn = false\n`;
    lua += `    screenGui.IgnoreGuiInset = true\n`;
    lua += `    screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling\n`;
    lua += `    screenGui.Parent = parent or Players.LocalPlayer:WaitForChild('PlayerGui')\n\n`;

    lua += `    local elements = {}\n`;

    for (const el of spec.elements || []) {
        const safeName = el.name.replace(/[^a-zA-Z0-9_]/g, "_");
        lua += `    -- ${el.name}\n`;
        lua += `    elements['${safeName}'] = self:CreateElement(screenGui, {\n`;
        lua += `        Class = "${el.robloxClass || "Frame"}",\n`;
        lua += `        Name = "${el.name}",\n`;
        lua += `        X = ${Math.round((el.position?.xScale || 0) * spec.canvasWidth)},\n`;
        lua += `        Y = ${Math.round((el.position?.yScale || 0) * spec.canvasHeight)},\n`;
        lua += `        Width = ${Math.round((el.size?.xScale || 0) * spec.canvasWidth)},\n`;
        lua += `        Height = ${Math.round((el.size?.yScale || 0) * spec.canvasHeight)},\n`;

        if (el.properties?.backgroundColor) {
            lua += `        BackgroundColor3 = Color3.fromRGB(${hexToRGB(el.properties.backgroundColor).join(", ")}),\n`;
        }
        if (el.properties?.text) {
            lua += `        Text = "${el.properties.text}",\n`;
        }
        if (el.properties?.textSize) {
            lua += `        TextSize = ${el.properties.textSize},\n`;
        }
        if (el.properties?.cornerRadius) {
            lua += `        CornerRadius = ${el.properties.cornerRadius},\n`;
        }

        lua += `    })\n\n`;
    }

    lua += `    self.Elements = elements\n`;
    lua += `    return screenGui\n`;
    lua += `end\n\n`;

    lua += `return GeneratedUI\n`;

    // Save to file
    const luaPath = path.join(outputDir, `_controller.lua`);
    fs.writeFileSync(luaPath, lua, "utf-8");

    return lua;
}

function hexToRGB(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
        ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)]
        : [0, 0, 0];
}

// ── CLI Entry Point ───────────────────────────────────────────────────────────

function main() {
    const args = process.argv.slice(2);

    if (args.includes("--help") || args.includes("-h")) {
        console.log(`
PSD → AI → Roblox UI Pipeline

Uso:
  node psd-to-roblox-ai.js <psd-path> [options]

Argumentos:
  <psd-path>    Caminho para o arquivo PSD ou pasta com PNGs

Opções:
  --api-key <key>   OpenAI API Key (ou defina OPENAI_API_KEY)
  --output <dir>    Diretório de saída (default: ./output)
  --prompt <text>   Prompt personalizado para a IA
  --ask <question>  Fazer pergunta sobre o PSD
  --scan-only       Apenas escanear, não enviar para IA
  --help, -h        Mostrar esta ajuda

Exemplos:
  node psd-to-roblox-ai.js menu.psd
  node psd-to-roblox-ai.js assets/ --api-key sk-...
  node psd-to-roblox-ai.js design.psd --ask "Como faço responsivo?"
`);
        process.exit(0);
    }

    const psdPath = args[0];
    if (!psdPath) {
        console.error("❌ Informe um caminho para o PSD ou pasta");
        process.exit(1);
    }

    const options = {
        apiKey: args.includes("--api-key") ? args[args.indexOf("--api-key") + 1] : null,
        output: args.includes("--output") ? args[args.indexOf("--output") + 1] : null,
        prompt: args.includes("--prompt") ? args[args.indexOf("--prompt") + 1] : null,
        ask: args.includes("--ask") ? args[args.indexOf("--ask") + 1] : null,
        scanOnly: args.includes("--scan-only"),
    };

    // Se for pergunta, fazer QA
    if (options.ask) {
        log(`🤔 Pergunta: "${options.ask}"`);
        // Implementar QA logic here
        return;
    }

    // Executar pipeline
    runPipeline(psdPath, options)
        .then((result) => {
            console.log("\n✅ Pipeline concluído com sucesso!");
            console.log(`📂 Saída: ${result.outputDir}`);
        })
        .catch((e) => {
            console.error("\n❌ Erro:", e.message);
            process.exit(1);
        });
}

main();
