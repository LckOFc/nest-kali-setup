/**
 * uds-live-builder.js
 *
 * Construtor de Universal Design Schema em tempo real a partir do PSD aberto.
 * Conectado ao UXP panel via ps.core.executeCommand.
 * Gera UDS completo + UDS otimizado para IA.
 */

const crypto = require("node:crypto");

// ── Classificador de Layers ─────────────────────────────────────────────────────

function inferRole(layerName, width, height) {
    const name = (layerName || "").toLowerCase();
    const ratio = height > 0 ? width / height : 1;
    const area = width * height;

    // Dimensional rules (peso alto)
    if (width > 1500 && height > 800 && ratio > 1.3) return { role: "background", confidence: 0.95 };
    if (area < 6400 && Math.abs(ratio - 1) < 0.3) return { role: "icon", confidence: 0.85 };
    if (height < 60 && width > 100) return { role: "separator", confidence: 0.8 };
    if (height > 200 && width < 100) return { role: "bar", confidence: 0.7 };

    // Semantic rules (peso médio)
    if (/\b(bg|back|base|fundo|wallpaper)\b/.test(name)) return { role: "background", confidence: 0.95 };
    if (/\b(btn|button|play|start|cta|submit)\b/.test(name)) return { role: "button", confidence: 0.9 };
    if (/\b(title|label|text|score|caption|desc|body|info)\b/.test(name)) return { role: "label", confidence: 0.85 };
    if (/\b(icon|img|logo|avatar|sprite|photo)\b/.test(name)) return { role: "icon", confidence: 0.9 };
    if (/\b(panel|frame|box|card|container)\b/.test(name)) return { role: "panel", confidence: 0.85 };
    if (/\b(bar|health|hp|stamina|mana|xp|progress)\b/.test(name)) return { role: "bar", confidence: 0.8 };

    // Fallback dimensional
    if (width > 500 && height > 300) return { role: "panel", confidence: 0.6 };
    if (height < 80 && width > 150) return { role: "button", confidence: 0.6 };
    if (width < 100 && height < 100) return { role: "icon", confidence: 0.6 };

    return { role: "image", confidence: 0.5 };
}

function inferRobloxClass(role) {
    const map = {
        background: "ImageLabel",
        panel: "Frame",
        button: "TextButton",
        label: "TextLabel",
        icon: "ImageLabel",
        image: "ImageLabel",
        bar: "Frame",
        separator: "Frame",
        input: "TextBox",
    };
    return map[role] || "Frame";
}

function inferResponsiveStrategy(role) {
    const map = {
        background: "Fill",
        button: "ScaleToFit",
        label: "ScaleToFit",
        icon: "FixedSize",
        panel: "ScaleToFit",
        bar: "FixedSize",
        image: "ScaleToFit",
        separator: "FixedSize",
        input: "ScaleToFit",
    };
    return map[role] || "ScaleToFit";
}

// ── Live UDS Builder ────────────────────────────────────────────────────────────

class UDSLiveBuilder {
    constructor() {
        this.schemaVersion = "1.0.0";
        this.layers = [];
        this.groups = [];
        this.artboards = [];
        this.assets = [];
        this.colors = new Set();
        this.fonts = new Set();
        this.errors = [];
    }

    /**
     * Adiciona uma layer a partir dos dados extraídos pelo UXP/ExtendScript
     */
    addLayer(data, artboardId = null) {
        const { role, confidence } = inferRole(data.name, data.width, data.height);
        const robloxClass = inferRobloxClass(role);
        const strategy = inferResponsiveStrategy(role);

        const layer = {
            id: this._genId("layer"),
            name: data.name,
            type: data.type || "layer",
            visible: data.visible !== false,
            opacity: data.opacity !== undefined ? data.opacity : 1.0,
            blendMode: data.blendMode || "Normal",
            bounds: {
                x: Math.round(data.x || 0),
                y: Math.round(data.y || 0),
                width: Math.round(data.width || 0),
                height: Math.round(data.height || 0),
            },
            semantic: {
                probableRole: role,
                confidence: confidence,
                robloxClass: robloxClass,
                responsiveStrategy: strategy,
            },
            fill: data.fill || null,
            stroke: data.stroke || null,
            text: data.text || null,
            effects: data.effects || [],
            cornerRadius: data.cornerRadius || 0,
            artboardId: artboardId,
        };

        this.layers.push(layer);

        // Coletar cores e fonts
        if (data.fill?.hex) this.colors.add(data.fill.hex);
        if (data.text?.font) this.fonts.add(data.text.font);

        return layer;
    }

    /**
     * Adiciona um grupo
     */
    addGroup(data, artboardId = null) {
        const group = {
            id: this._genId("group"),
            name: data.name,
            type: "group",
            visible: data.visible !== false,
            opacity: data.opacity !== undefined ? data.opacity : 1.0,
            bounds: {
                x: Math.round(data.x || 0),
                y: Math.round(data.y || 0),
                width: Math.round(data.width || 0),
                height: Math.round(data.height || 0),
            },
            children: data.children || [],
            artboardId: artboardId,
        };
        this.groups.push(group);
        return group;
    }

    /**
     * Adiciona um artboard
     */
    addArtboard(data) {
        const artboard = {
            id: this._genId("artboard"),
            name: data.name,
            x: Math.round(data.x || 0),
            y: Math.round(data.y || 0),
            width: Math.round(data.width || 0),
            height: Math.round(data.height || 0),
            visible: data.visible !== false,
            children: [],
        };
        this.artboards.push(artboard);
        return artboard;
    }

    /**
     * Adiciona um asset exportado
     */
    addAsset(data) {
        const asset = {
            id: this._genId("asset"),
            name: data.name,
            path: data.path,
            width: data.width,
            height: data.height,
            fileSize: data.fileSize || 0,
            format: data.format || "png",
            transparency: data.transparency !== false,
            linkToLayer: data.linkToLayer || null,
        };
        this.assets.push(asset);
        return asset;
    }

    /**
     * Gera UDS completo em JSON
     */
    buildUDS(documentInfo) {
        return {
            schemaVersion: this.schemaVersion,
            source: "photoshop",
            document: documentInfo || {
                name: "Untitled",
                width: 1920,
                height: 1080,
                resolution: 72,
                colorMode: "RGB",
                bitDepth: 8,
            },
            artboards: this.artboards,
            groups: this.groups,
            layers: this.layers,
            assets: this.assets,
            colors: Array.from(this.colors).map(hex => ({ hex, usage: [] })),
            fonts: Array.from(this.fonts),
            metadata: {
                generatedAt: new Date().toISOString(),
                generator: "UDSLiveBuilder v1.0",
            },
        };
    }

    /**
     * Gera UDS otimizado para envio à IA (compactado)
     */
    buildAIInput(documentInfo) {
        return {
            schemaVersion: this.schemaVersion,
            document: {
                name: (documentInfo || {}).name || "Untitled",
                width: (documentInfo || {}).width || 1920,
                height: (documentInfo || {}).height || 1080,
                resolution: (documentInfo || {}).resolution || 72,
            },
            layers: this.layers.map(l => ({
                id: l.id,
                name: l.name,
                type: l.type,
                visible: l.visible,
                opacity: l.opacity,
                bounds: l.bounds,
                semantic: l.semantic,
                fill: l.fill ? { hex: l.fill.hex } : null,
                stroke: l.stroke ? { hex: l.stroke.hex, size: l.stroke.size } : null,
                text: l.text ? {
                    content: l.text.content,
                    size: l.text.size,
                    font: l.text.font,
                    color: l.text.color,
                } : null,
                effects: l.effects,
                cornerRadius: l.cornerRadius,
            })),
            responsiveStrategy: this.layers.map(l => ({
                layerId: l.id,
                layerName: l.name,
                role: l.semantic.probableRole,
                robloxClass: l.semantic.robloxClass,
                strategy: l.semantic.responsiveStrategy,
                bounds: l.bounds,
            })),
            errors: this.errors,
        };
    }

    /**
     * Gera mini-manifest pronto para o plugin Roblox
     */
    buildMiniManifest(screenName) {
        const elements = this.layers.map(l => ({
            name: l.name,
            type: l.type,
            robloxClass: l.semantic.robloxClass,
            x: l.bounds.x,
            y: l.bounds.y,
            width: l.bounds.width,
            height: l.bounds.height,
            opacity: l.opacity,
            fill: l.fill,
            stroke: l.stroke,
            cornerRadius: l.cornerRadius,
            text: l.text,
            effects: l.effects,
            responsiveStrategy: l.semantic.responsiveStrategy,
        }));

        // Detectar grupos verticais/horizontais para layout hints
        const hints = this._detectLayoutHints(elements);

        return {
            version: "1.0.0",
            source: "photoshop",
            name: screenName || "Screen",
            generated: new Date().toISOString(),
            elements: elements,
            layoutHints: hints,
            stats: {
                totalLayers: this.layers.length,
                totalGroups: this.groups.length,
                colors: this.colors.size,
                fonts: this.fonts.size,
            },
        };
    }

    /**
     * Detecta padrões de layout para hints
     */
    _detectLayoutHints(elements) {
        const hints = {
            verticalGroups: [],
            horizontalGroups: [],
            anchoredElements: [],
        };

        // Agrupar por proximidade de Y (grupos verticais)
        const byY = {};
        for (const el of elements) {
            const key = Math.round(el.y / 40) * 40;
            if (!byY[key]) byY[key] = [];
            byY[key].push(el);
        }

        for (const [key, siblings] of Object.entries(byY)) {
            if (siblings.length >= 2) {
                const sorted = siblings.sort((a, b) => a.x - b.x);
                const isH = sorted.every((el, i) => {
                    if (i === 0) return true;
                    return Math.abs(el.y - sorted[i - 1].y) < 20;
                });
                if (isH) {
                    hints.horizontalGroups.push(sorted.map(e => e.name));
                }
            }
        }

        // Agrupar por proximidade de X (grupos horizontais)
        const byX = {};
        for (const el of elements) {
            const key = Math.round(el.x / 40) * 40;
            if (!byX[key]) byX[key] = [];
            byX[key].push(el);
        }

        for (const [key, siblings] of Object.entries(byX)) {
            if (siblings.length >= 2) {
                const sorted = siblings.sort((a, b) => a.y - b.y);
                const isV = sorted.every((el, i) => {
                    if (i === 0) return true;
                    return Math.abs(el.x - sorted[i - 1].x) < 20;
                });
                if (isV) {
                    hints.verticalGroups.push(sorted.map(e => e.name));
                }
            }
        }

        // Elementos fixos (backgrounds)
        for (const el of elements) {
            if (el.type === "background" || (el.width >= 1800 && el.height >= 900)) {
                hints.anchoredElements.push(el.name);
            }
        }

        return hints;
    }

    /**
     * Gera ID único
     */
    _genId(prefix) {
        return `${prefix}_${crypto.randomBytes(3).toString("hex")}`;
    }
}

// ── Factory ─────────────────────────────────────────────────────────────────────

function createUDSLiveBuilder() {
    return new UDSLiveBuilder();
}

// ── Export ──────────────────────────────────────────────────────────────────────

module.exports = {
    UDSLiveBuilder,
    createUDSLiveBuilder,
    inferRole,
    inferRobloxClass,
    inferResponsiveStrategy,
};
