/**
 * PSD Intelligence Scanner — UXP Plugin for Adobe Photoshop
 *
 * Extrai informação completa de documentos PSD abertos no Photoshop
 * e gera um Universal Design Schema (UDS) para processamento por IA.
 *
 * Uso:
 *   1. Abra o Photoshop com um PSD
 *   2. Execute este script via UXP Developer Tool
 *   3. O scanner gera:
 *      - UDS JSON (estrutura completa)
 *      - Thumbnails de cada artboard
 *      - Asset exports por camada
 *      - Relatório de compatibilidade Roblox
 *
 * API usada:
 *   - DOM (ps.app) para informações básicas
 *   - batchPlay para informações avançadas
 */

const ps = require("photoshop");
const uxp = require("uxp");
const fs = uxp.plugins.fs;
const path = require("path");
const crypto = require("node:crypto");

// ── Config ────────────────────────────────────────────────────────────────────

const CONFIG = {
    maxExportDimension: 2048,
    thumbnailSize: 400,
    exportFormat: "png",
    compression: 9,
    transparent: true,
};

// ── Classificadores ───────────────────────────────────────────────────────────

function inferRole(layerName, bounds, width, height) {
    const name = (layerName || "").toLowerCase();
    const ratio = width / height;
    const area = width * height;

    // Dimensional rules
    if (width > 1500 && height > 800 && ratio > 1.3) return { role: "background", confidence: 0.9 };
    if (area < 6400 && Math.abs(ratio - 1) < 0.3) return { role: "icon", confidence: 0.85 };
    if (height < 60 && width > 100) return { role: "separator", confidence: 0.8 };
    if (height > 200 && width < 100) return { role: "bar", confidence: 0.7 };

    // Semantic rules
    if (name.includes("bg") || name.includes("back") || name.includes("base") || name.includes("fundo"))
        return { role: "background", confidence: 0.95 };
    if (name.includes("btn") || name.includes("button") || name.includes("play") || name.includes("start"))
        return { role: "button", confidence: 0.9 };
    if (name.includes("title") || name.includes("label") || name.includes("text") || name.includes("score"))
        return { role: "label", confidence: 0.85 };
    if (name.includes("icon") || name.includes("img") || name.includes("logo") || name.includes("avatar"))
        return { role: "icon", confidence: 0.9 };
    if (name.includes("panel") || name.includes("frame") || name.includes("box") || name.includes("card"))
        return { role: "panel", confidence: 0.85 };
    if (name.includes("bar") || name.includes("health") || name.includes("hp") || name.includes("mana"))
        return { role: "bar", confidence: 0.8 };

    // Fallback based on dimensions
    if (width > 500 && height > 300) return { role: "panel", confidence: 0.6 };
    if (height < 80 && width > 150) return { role: "button", confidence: 0.6 };
    if (width < 100 && height < 100) return { role: "icon", confidence: 0.6 };

    return { role: "image", confidence: 0.5 };
}

// ── PSD Intelligence Scanner ──────────────────────────────────────────────────

class PSDIntelligenceScanner {
    constructor() {
        this.app = ps.app;
        this.document = null;
        this.layers = [];
        this.artboards = [];
        this.groups = [];
        this.assets = [];
        this.colors = new Set();
        this.fonts = new Set();
    }

    /**
     * Verifica se há um documento aberto e válido
     */
    async checkDocument() {
        try {
            this.document = this.app.activeDocument;
            if (!this.document) {
                return { success: false, error: "Nenhum documento aberto no Photoshop" };
            }
            return { success: true, doc: this.document };
        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    /**
     * Extrai informações do documento
     */
    async extractDocumentInfo() {
        if (!this.document) await this.checkDocument();

        const info = {
            name: this.document.name,
            width: Math.round(this.document.width),
            height: Math.round(this.document.height),
            resolution: this.document.resolution || 72,
            colorMode: this.document.modeName || "RGB",
            bitDepth: this.document.bitDepth || 8,
        };

        return info;
    }

    /**
     * Extrai artboards do documento
     */
    async extractArtboards() {
        const artboards = [];

        try {
            // Usar batchPlay para acessar artboards (não exposto no DOM)
            const result = await ps.core.executeCommand({
                type: "get",
                _ref: { _class: "artboard" },
                _target: { _index: 0 },
            });

            // Se não funcionar, tentar via layers
            const layers = this.document.layers || [];
            for (let i = 0; i < layers.length; i++) {
                const layer = layers[i];
                if (layer.kind && layer.kind.toString().includes("Artboard")) {
                    try {
                        const bounds = layer.bounds;
                        artboards.push({
                            id: this._genId("artboard"),
                            name: layer.name,
                            x: Math.round(bounds[0]),
                            y: Math.round(bounds[1]),
                            width: Math.round(bounds[2] - bounds[0]),
                            height: Math.round(bounds[3] - bounds[1]),
                            visible: layer.visible,
                            children: [],
                        });
                    } catch (e) {}
                }
            }
        } catch (e) {
            console.warn("[Scanner] Artboard extraction warning:", e.message);
        }

        this.artboards = artboards;
        return artboards;
    }

    /**
     * Extrai todas as layers do documento (recursivo)
     */
    async extractLayers(artboardId = null) {
        const layers = [];

        try {
            const docLayers = this.document.layers || [];

            for (let i = 0; i < docLayers.length; i++) {
                const layer = docLayers[i];
                const kind = layer.kind ? layer.kind.toString() : "";

                // Processar Group
                if (kind.includes("LayerSet") || kind.includes("Group")) {
                    const groupInfo = await this._extractGroup(layer, artboardId);
                    layers.push(groupInfo);
                    this.groups.push(groupInfo);
                }
                // Processar Layer
                else if (kind.includes("Layer")) {
                    const layerInfo = await this._extractLayer(layer, artboardId);
                    if (layerInfo) {
                        layers.push(layerInfo);
                        this.layers.push(layerInfo);
                    }
                }
                // Processar Artboard
                else if (kind.includes("Artboard")) {
                    const abInfo = await this._extractArtboard(layer);
                    if (abInfo) {
                        layers.push(abInfo);
                        this.artboards.push(abInfo);
                    }
                }
            }
        } catch (e) {
            console.error("[Scanner] Layer extraction error:", e);
        }

        return layers;
    }

    /**
     * Extrai informações de um Group
     */
    async _extractGroup(group, artboardId) {
        const children = [];

        try {
            const groupLayers = group.layers || [];
            for (let i = 0; i < groupLayers.length; i++) {
                const child = groupLayers[i];
                const childKind = child.kind ? child.kind.toString() : "";

                if (childKind.includes("Layer")) {
                    const layerInfo = await this._extractLayer(child, artboardId);
                    if (layerInfo) {
                        children.push(layerInfo);
                        this.layers.push(layerInfo);
                    }
                } else if (childKind.includes("LayerSet")) {
                    const groupInfo = await this._extractGroup(child, artboardId);
                    if (groupInfo) {
                        children.push(groupInfo);
                        this.groups.push(groupInfo);
                    }
                }
            }
        } catch (e) {}

        return {
            id: this._genId("group"),
            name: group.name,
            type: "group",
            visible: group.layerSetVisible !== undefined ? group.layerSetVisible : true,
            opacity: Math.round((group.opacity / 100) * 100) / 100,
            bounds: { x: 0, y: 0, width: 0, height: 0 },
            children: children.map((c) => c.id),
            _raw: group,
        };
    }

    /**
     * Extrai informações de uma Layer
     */
    async _extractLayer(layer, artboardId) {
        try {
            if (!layer.visible) return null;

            const bounds = layer.bounds;
            const width = Math.round(bounds[2] - bounds[0]);
            const height = Math.round(bounds[3] - bounds[1]);

            if (width <= 0 || height <= 0) return null;

            // Inferir role
            const { role, confidence } = inferRole(layer.name, bounds, width, height);

            // Extrair cor de fill
            const fill = await this._extractFill(layer);

            // Extrair texto
            const text = await this._extractText(layer);

            // Extrair efeitos
            const effects = await this._extractEffects(layer);

            // Extrair stroke
            const stroke = await this._extractStroke(layer);

            // Coletar cor
            if (fill) this.colors.add(fill.hex);

            // Coletar fonte
            if (text && text.font) this.fonts.add(text.font);

            return {
                id: this._genId("layer"),
                name: layer.name,
                type: "layer",
                visible: layer.visible,
                opacity: Math.round((layer.opacity / 100) * 100) / 100,
                blendMode: this._getBlendMode(layer),
                bounds: {
                    x: Math.round(bounds[0]),
                    y: Math.round(bounds[1]),
                    width: width,
                    height: height,
                },
                semantic: {
                    probableRole: role,
                    confidence: confidence,
                },
                fill: fill,
                stroke: stroke,
                text: text,
                effects: effects,
                artboardId: artboardId,
                _raw: layer,
            };
        } catch (e) {
            console.warn(`[Scanner] Failed to extract layer: ${layer.name}`, e.message);
            return null;
        }
    }

    /**
     * Extrai informações de um Artboard
     */
    async _extractArtboard(artboard) {
        try {
            const bounds = artboard.bounds;
            return {
                id: this._genId("artboard"),
                name: artboard.name,
                type: "artboard",
                visible: artboard.visible,
                bounds: {
                    x: Math.round(bounds[0]),
                    y: Math.round(bounds[1]),
                    width: Math.round(bounds[2] - bounds[0]),
                    height: Math.round(bounds[3] - bounds[1]),
                },
                children: [],
                _raw: artboard,
            };
        } catch (e) {
            return null;
        }
    }

    /**
     * Extrai cor de fill da layer
     */
    async _extractFill(layer) {
        try {
            // Tentar via batchPlay
            const result = await ps.core.executeCommand({
                type: "get",
                _ref: { _class: "solidColorLayer" },
                _target: { _index: 0 },
            });

            if (result && result.color) {
                const c = result.color;
                const hex = this._rgbToHex(c.red, c.green, c.blue);
                this.colors.add(hex);
                return {
                    type: "solid",
                    color: { r: c.red, g: c.green, b: c.blue, a: c.opacity || 1 },
                    hex: hex,
                };
            }
        } catch (e) {}

        return null;
    }

    /**
     * Extrai informações de texto
     */
    async _extractText(layer) {
        try {
            const textItem = layer.textItem;
            if (!textItem) return null;

            const fontInfo = {
                name: textItem.font || "Unknown",
                size: Math.round(textItem.size),
                bold: textItem.bold || false,
                style: textItem.style || "normal",
            };
            this.fonts.add(fontInfo.name);

            return {
                content: textItem.contents,
                size: fontInfo.size,
                font: fontInfo.name,
                bold: fontInfo.bold,
                alignment: textItem.justification || "left",
                color: await this._getTextColor(layer),
            };
        } catch (e) {
            return null;
        }
    }

    /**
     * Extrai cor do texto
     */
    async _getTextColor(layer) {
        try {
            const result = await ps.core.executeCommand({
                type: "get",
                _ref: { _class: "textLayer" },
                _target: { _index: 0 },
            });

            if (result && result.color) {
                const c = result.color;
                return {
                    r: c.red,
                    g: c.green,
                    b: c.blue,
                    hex: this._rgbToHex(c.red, c.green, c.blue),
                };
            }
        } catch (e) {}
        return null;
    }

    /**
     * Extrai efeitos da layer (drop shadow, glow, etc.)
     */
    async _extractEffects(layer) {
        const effects = [];

        try {
            // Drop shadow
            const ds = await ps.core.executeCommand({
                type: "get",
                _ref: { _class: "dropShadowLayer" },
                _target: { _index: 0 },
            });

            if (ds && ds.enabled) {
                effects.push({
                    type: "dropShadow",
                    distance: ds.distance || 0,
                    angle: ds.angle || 0,
                    blur: ds.blur || 0,
                    opacity: ds.opacity || 100,
                    color: ds.color ? this._rgbToHex(ds.color.red, ds.color.green, ds.color.blue) : "#000000",
                });
            }

            // Inner shadow
            const is = await ps.core.executeCommand({
                type: "get",
                _ref: { _class: "innerShadowLayer" },
                _target: { _index: 0 },
            });

            if (is && is.enabled) {
                effects.push({
                    type: "innerShadow",
                    distance: is.distance || 0,
                    blur: is.blur || 0,
                    opacity: is.opacity || 100,
                });
            }

            // Outer glow
            const og = await ps.core.executeCommand({
                type: "get",
                _ref: { _class: "outerGlowLayer" },
                _target: { _index: 0 },
            });

            if (og && og.enabled) {
                effects.push({
                    type: "outerGlow",
                    blur: og.blur || 0,
                    opacity: og.opacity || 100,
                });
            }
        } catch (e) {
            // Efeitos não disponíveis
        }

        return effects;
    }

    /**
     * Extrai stroke da layer
     */
    async _extractStroke(layer) {
        try {
            const result = await ps.core.executeCommand({
                type: "get",
                _ref: { _class: "strokeLayer" },
                _target: { _index: 0 },
            });

            if (result && result.enabled) {
                const c = result.color;
                return {
                    size: result.size || 1,
                    color: {
                        r: c.red,
                        g: c.green,
                        b: c.blue,
                        hex: this._rgbToHex(c.red, c.green, c.blue),
                    },
                };
            }
        } catch (e) {}
        return null;
    }

    /**
     * Obtém blend mode da layer
     */
    _getBlendMode(layer) {
        try {
            return layer.blendMode ? layer.blendMode.toString().replace("BlendMode.", "") : "Normal";
        } catch (e) {
            return "Normal";
        }
    }

    /**
     * Converte RGB para HEX
     */
    _rgbToHex(r, g, b) {
        const toHex = (c) => {
            const hex = Math.round(c * 255).toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        };
        return "#" + toHex(r) + toHex(g) + toHex(b).toUpperCase();
    }

    /**
     * Gera ID único
     */
    _genId(prefix) {
        return `${prefix}_${crypto.randomBytes(3).toString("hex")}`;
    }

    /**
     * Gera thumbnail de uma artboard
     */
    async generateThumbnail(artboard, outputPath) {
        try {
            // Usar batchPlay para exportar artboard como imagem
            await ps.core.executeCommand({
                type: "exportDocument",
                _target: { _ref: "artboard", _index: 0 },
                as: "PNG",
                in: outputPath,
                options: {
                    transparency: true,
                    quality: 100,
                },
            });
            return { success: true, path: outputPath };
        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    /**
     * Gera relatório de compatibilidade Roblox
     */
    generateCompatibilityReport() {
        const report = {
            layers: this.layers.length,
            groups: this.groups.length,
            artboards: this.artboards.length,
            issues: [],
            warnings: [],
        };

        // Verificar problemas comuns
        for (const layer of this.layers) {
            // Fontes não suportadas
            if (layer.text && layer.text.font) {
                const supportedFonts = ["Gotham", "GothamBold", "GothamBlack", "Arial", "Helvetica"];
                if (!supportedFonts.some((f) => layer.text.font.toLowerCase().includes(f.toLowerCase()))) {
                    report.warnings.push(
                        `Fonte não encontrada: "${layer.text.font}" → usar Gotham como fallback`
                    );
                }
            }

            // Opacidade muito baixa
            if (layer.opacity < 0.1) {
                report.issues.push(`Layer "${layer.name}" tem opacidade muito baixa (${layer.opacity})`);
            }

            // Blend modes não suportados
            if (layer.blendMode && layer.blendMode !== "Normal") {
                report.warnings.push(
                    `Blend mode "${layer.blendMode}" não suportado no Roblox → será ignorado`
                );
            }
        }

        // Verificar dimensões
        if (this.document) {
            const docW = Math.round(this.document.width);
            const docH = Math.round(this.document.height);
            if (docW > 2048 || docH > 2048) {
                report.warnings.push(
                    `Canvas ${docW}x${docH} excede limite do Roblox (2048x2048) → será redimensionado`
                );
            }
        }

        report.reportGeneratedAt = new Date().toISOString();
        return report;
    }

    /**
     * Gera UDS completo
     */
    async generateUDS() {
        await this.checkDocument();
        const docInfo = await this.extractDocumentInfo();
        const artboards = await this.extractArtboards();
        const layers = await this.extractLayers();

        return {
            schemaVersion: "1.0.0",
            source: "photoshop",
            document: docInfo,
            artboards: artboards,
            layers: layers,
            groups: this.groups,
            assets: this.assets,
            colors: Array.from(this.colors).map((c) => ({ hex: c, usage: [] })),
            fonts: Array.from(this.fonts),
            metadata: {
                generatedAt: new Date().toISOString(),
                generator: "PSD Intelligence Scanner v1.0",
            },
        };
    }
}

// ── Main Entry Point ──────────────────────────────────────────────────────────

async function main() {
    const scanner = new PSDIntelligenceScanner();

    console.log("\n🔍 PSD Intelligence Scanner v1.0");
    console.log("═".repeat(50));

    // Check document
    const docCheck = await scanner.checkDocument();
    if (!docCheck.success) {
        console.log(`❌ ${docCheck.error}`);
        return;
    }

    console.log(`✅ Documento: ${docCheck.doc.name}`);

    // Generate UDS
    console.log("\n📊 Extraindo estrutura do documento...");
    const uds = await scanner.generateUDS();

    console.log(`   📐 Canvas: ${uds.document.width} × ${uds.document.height}`);
    console.log(`   📑 Artboards: ${uds.artboards.length}`);
    console.log(`   📝 Layers: ${uds.layers.length}`);
    console.log(`   📁 Groups: ${uds.groups.length}`);
    console.log(`   🎨 Cores únicas: ${uds.colors.length}`);
    console.log(`   🔤 Fontes: ${uds.fonts.length}`);

    // Generate compatibility report
    console.log("\n🔍 Verificando compatibilidade com Roblox...");
    const report = scanner.generateCompatibilityReport();
    console.log(`   ⚠️  Warnings: ${report.warnings.length}`);
    console.log(`   ❌ Issues: ${report.issues.length}`);

    for (const w of report.warnings.slice(0, 3)) {
        console.log(`      • ${w}`);
    }

    // Output
    const output = {
        uds: uds,
        compatibilityReport: report,
        aiInput: {
            document: uds.document,
            layers: uds.layers.map((l) => ({
                id: l.id,
                name: l.name,
                type: l.type,
                bounds: l.bounds,
                semantic: l.semantic,
                fill: l.fill ? { hex: l.fill.hex } : null,
                text: l.text
                    ? {
                          content: l.text.content,
                          size: l.text.size,
                          font: l.text.font,
                      }
                    : null,
                effects: l.effects,
            })),
            responsiveStrategy: uds.layers.map((l) => ({
                layerId: l.id,
                layerName: l.name,
                suggestedStrategy: l.semantic.probableRole === "background" ? "Fill" : "ScaleToFit",
                bounds: l.bounds,
            })),
        },
    };

    console.log("\n✅ Scanner concluído!");
    console.log("\n📋 Pronto para envio à IA.");
    console.log("   Use o campo 'aiInput' para processamento.");

    return output;
}

// Exportar para uso externo
module.exports = { PSDIntelligenceScanner, main };

// Executar se for script principal
if (require.main === module) {
    main().catch((e) => {
        console.error("❌ Erro:", e.message);
        process.exit(1);
    });
}
