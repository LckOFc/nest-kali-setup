/**
 * roblox-verification-engine.js
 *
 * Motor de verificação inteligente para designs de UI Roblox.
 * Analisa UDS ou dados de PSD e reporta:
 *   - Problemas críticos (vai quebrar no Roblox)
 *   - Avisos de compatibilidade
 *   - Recomendações de responsividade
 *   - Estimativa de performance
 *
 * Uso:
 *   const { VerificationEngine } = require('./roblox-verification-engine');
 *   const engine = new VerificationEngine();
 *   const report = await engine.analyze(uds);
 */

const fs = require("node:fs");
const path = require("node:path");

// ── Configurações do Roblox ────────────────────────────────────────────────────

const ROBLOX_LIMITS = {
    // Dimensões máximas de canvas (Roblox não suporta > 2048 em nenhum eixo)
    maxCanvasSize: 2048,
    // Número máximo recomendado de instâncias por ScreenGui (performance)
    maxInstances: 150,
    // Opacidade mínima antes de ser invisível pro Roblox
    minOpacity: 0.01,
    // Resolução máxima recomendada por asset PNG
    maxAssetResolution: 2048,
    // Tamanho máximo de arquivo PNG (Roblox CDN)
    maxAssetSizeKB: 10240, // 10MB
    // ZIndex máximo prático
    maxZIndex: 100,
    // Caracteres máximos em nomes de instances
    maxNameLength: 100,
};

const ROBLOX_UNSUPPORTED = {
    blendModes: [
        "Additive", "Multiply", "Screen", "Overlay", "Difference",
        "Exclusion", "Hue", "Saturation", "Color", "Luminosity"
    ],
    effects: ["InnerGlow", "Bevel", "Emboss", "Satin"],
    gradients: ["Radial", "Diagonal"], // Roblox suporta linear mas não radial
    colorModes: ["CMYK", "Indexed"],
};

const SUPPORTED_ROBLOX_CLASSES = {
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

const RESPONSIVE_STRATEGIES = {
    background: { strategy: "Fill", desc: "Preenche tela inteira, sem escala" },
    button: { strategy: "ScaleToFit", desc: "Mantém proporção, escala proporcional" },
    label: { strategy: "ScaleToFit", desc: "Escala proporcional ao viewport" },
    icon: { strategy: "FixedSize", desc: "Tamanho fixo em pixels" },
    panel: { strategy: "ScaleToFit", desc: "Proporcional ao canvas" },
    bar: { strategy: "FixedSize", desc: "Altura fixa, largura adaptável" },
    image: { strategy: "ScaleToFit", desc: "Escala proporcional" },
    separator: { strategy: "FixedSize", desc: "Linha fina fixa" },
    input: { strategy: "ScaleToFit", desc: "Proporcional ao container" },
};

// ── Classe Principal ──────────────────────────────────────────────────────────

class VerificationEngine {
    constructor(options = {}) {
        this.limits = { ...ROBLOX_LIMITS, ...options.limits };
        this.unsupported = { ...ROBLOX_UNSUPPORTED };
        this.issues = [];
        this.warnings = [];
        this.recommendations = [];
        this.performance = {};
    }

    /**
     * Analisa um UDS completo e retorna relatório de compatibilidade
     */
    async analyze(uds) {
        this.issues = [];
        this.warnings = [];
        this.recommendations = [];
        this.performance = {};

        // Fase 1: Verificação do documento
        this._checkDocument(uds.document);

        // Fase 2: Verificação de cada layer
        for (const layer of uds.layers || []) {
            this._checkLayer(layer, uds.document);
        }

        // Fase 3: Verificação de artboards
        for (const artboard of uds.artboards || []) {
            this._checkArtboard(artboard, uds.document);
        }

        // Fase 4: Verificação de assets
        for (const asset of uds.assets || []) {
            await this._checkAsset(asset);
        }

        // Fase 5: Análise de layout e responsive
        this._analyzeLayout(uds.layers, uds.document);

        // Fase 6: Estimativa de performance
        this._estimatePerformance(uds);

        // Fase 7: Geração de score global
        this._calculateScore(uds);

        return this._buildReport(uds);
    }

    /**
     * Analisa documento principal
     */
    _checkDocument(doc) {
        if (!doc) return;

        // Canvas过大
        if (doc.width > this.limits.maxCanvasSize || doc.height > this.limits.maxCanvasSize) {
            this.warnings.push({
                type: "canvas-size",
                message: `Canvas ${doc.width}×${doc.height} excede limite do Roblox (2048×2048). Será redimensionado.`,
                severity: "warning",
                fix: "Redimensionar documento para ≤ 2048×2048 no Photoshop",
            });
        }

        // Modo de cor
        if (doc.colorMode && this.unsupported.colorModes.includes(doc.colorMode)) {
            this.issues.push({
                type: "color-mode",
                message: `Modo de cor "${doc.colorMode}" não suportado. Roblox exige RGB.`,
                severity: "error",
                fix: "Converter para RGB (Image > Mode > RGB Color)",
            });
        }

        // Resolução
        if (doc.resolution && doc.resolution > 144) {
            this.warnings.push({
                type: "resolution",
                message: `Resolução ${doc.resolution} DPI é alta para Roblox. Recomenda-se 72-96 DPI.`,
                severity: "warning",
                fix: "Reduzir resolução para 72-96 DPI (Image > Image Size)",
            });
        }

        // Bit depth
        if (doc.bitDepth && doc.bitDepth > 8) {
            this.warnings.push({
                type: "bit-depth",
                message: `Bit depth ${doc.bitDepth} pode causar problemas. Roblox usa 8-bit por canal.`,
                severity: "info",
                fix: "Manter em 8-bit (Image > Mode > 8/16/32 Bits Channel)",
            });
        }
    }

    /**
     * Analisa cada layer individualmente
     */
    _checkLayer(layer, doc) {
        if (!layer.bounds) return;
        const { width, height } = layer.bounds;

        // Dimensões zeradas
        if (width <= 0 || height <= 0) {
            this.issues.push({
                type: "empty-layer",
                message: `Layer "${layer.name}" tem dimensões inválidas (${width}×${height})`,
                severity: "error",
                fix: "Verificar bounds da layer no Photoshop",
            });
            return;
        }

        // Opacidade muito baixa
        if (layer.opacity !== undefined && layer.opacity < this.limits.minOpacity) {
            this.warnings.push({
                type: "low-opacity",
                message: `Layer "${layer.name}" tem opacidade ${layer.opacity} (muito baixa para Roblox)`,
                severity: "warning",
                fix: "Aumentar opacidade para ≥ 0.01",
            });
        }

        // Blend modes não suportados
        if (layer.blendMode && this.unsupported.blendModes.includes(layer.blendMode)) {
            this.warnings.push({
                type: "blend-mode",
                message: `Blend mode "${layer.blendMode}" não suportado no Roblox. Será ignorado.`,
                severity: "warning",
                fix: 'Alterar blend mode para "Normal"',
            });
        }

        // Dimensões excessivamente grandes
        if (width > this.limits.maxAssetResolution || height > this.limits.maxAssetResolution) {
            this.warnings.push({
                type: "oversized-layer",
                message: `Layer "${layer.name}" (${width}×${height}) excede resolução máxima do Roblox`,
                severity: "warning",
                fix: "Redimensionar layer para ≤ 2048×2048",
            });
        }

        // Nomes excessivamente longos
        if (layer.name && layer.name.length > this.limits.maxNameLength) {
            this.warnings.push({
                type: "long-name",
                message: `Nome "${layer.name}" excede ${this.limits.maxNameLength} caracteres`,
                severity: "info",
                fix: "Encurtar nome da layer",
            });
        }

        // Efeitos não suportados
        if (layer.effects) {
            for (const effect of layer.effects) {
                if (this.unsupported.effects.includes(effect.type)) {
                    this.warnings.push({
                        type: "unsupported-effect",
                        message: `Efeito "${effect.type}" não suportado no Roblox`,
                        severity: "info",
                        fix: "Remover efeito ou pre-renderizar na layer",
                    });
                }
            }
        }

        // Recomendação de responsive strategy
        const role = layer.semantic?.probableRole || "image";
        const strategy = RESPONSIVE_STRATEGIES[role] || RESPONSIVE_STRATEGIES.image;
        this.recommendations.push({
            layerId: layer.id,
            layerName: layer.name,
            role: role,
            strategy: strategy.strategy,
            desc: strategy.desc,
        });
    }

    /**
     * Analisa artboards
     */
    _checkArtboard(artboard, doc) {
        if (artboard.width > this.limits.maxCanvasSize || artboard.height > this.limits.maxCanvasSize) {
            this.warnings.push({
                type: "artboard-size",
                message: `Artboard "${artboard.name}" (${artboard.width}×${artboard.height}) excede limite`,
                severity: "warning",
                fix: "Redimensionar artboard para ≤ 2048×2048",
            });
        }

        // Contar layers dentro do artboard
        const artboardLayers = (doc.layers || []).filter(l => l.artboardId === artboard.id);
        if (artboardLayers.length > this.limits.maxInstances) {
            this.warnings.push({
                type: "artboard-overload",
                message: `Artboard "${artboard.name}" tem ${artboardLayers.length} layers (> ${this.limits.maxInstances})`,
                severity: "warning",
                fix: "Dividir em múltiplos artboards ou simplificar",
            });
        }
    }

    /**
     * Analisa assets exportados
     */
    async _checkAsset(asset) {
        if (!asset.path || !fs.existsSync(asset.path)) return;

        try {
            const stats = fs.statSync(asset.path);
            const sizeKB = stats.size / 1024;

            if (sizeKB > this.limits.maxAssetSizeKB) {
                this.warnings.push({
                    type: "asset-too-large",
                    message: `Asset "${asset.name}" (${sizeKB.toFixed(0)}KB) excede limite de 10MB`,
                    severity: "warning",
                    fix: "Comprimir imagem (File > Export > Save for Web)",
                });
            }

            // Verificar transparência
            if (!asset.transparency && asset.format === "png") {
                this.warnings.push({
                    type: "no-transparency",
                    message: `Asset "${asset.name}" não tem transparência. Considerar usar PNG com alpha.`,
                    severity: "info",
                    fix: "Exportar como PNG com transparência",
                });
            }
        } catch (e) {
            this.warnings.push({
                type: "asset-read-error",
                message: `Não foi possível ler asset "${asset.name}": ${e.message}`,
                severity: "info",
            });
        }
    }

    /**
     * Analisa layout geral e posicionamento
     */
    _analyzeLayout(layers, doc) {
        if (!doc || !layers || layers.length === 0) return;

        const { width: canvasW, height: canvasH } = doc;

        // Verificar se algum layer sai do canvas
        for (const layer of layers) {
            if (!layer.bounds) continue;
            const { x, y, width, height } = layer.bounds;

            // Fora do canvas à direita
            if (x + width > canvasW + 10) {
                this.warnings.push({
                    type: "out-of-bounds-right",
                    message: `Layer "${layer.name}" sai do canvas pela direita (${x + width} > ${canvasW})`,
                    severity: "warning",
                    fix: "Mover layer para dentro do artboard/canvas",
                });
            }

            // Fora do canvas abaixo
            if (y + height > canvasH + 10) {
                this.warnings.push({
                    type: "out-of-bounds-bottom",
                    message: `Layer "${layer.name}" sai do canvas pela parte inferior (${y + height} > ${canvasH})`,
                    severity: "warning",
                    fix: "Mover layer para dentro do artboard/canvas",
                });
            }
        }

        // Detectar sobreposição excessiva
        const overlaps = this._detectOverlaps(layers);
        if (overlaps.length > 0 && overlaps.length > layers.length * 0.3) {
            this.warnings.push({
                type: "excessive-overlap",
                message: `${overlaps.length} pares de layers sobrepostos detectados (>30% do total)`,
                severity: "info",
                fix: "Revisar hierarquia de layers no Photoshop",
            });
        }

        // Detectar grupos que deveriam ter UIListLayout
        const verticalGroups = this._detectVerticalGroups(layers);
        for (const group of verticalGroups) {
            if (group.children.length >= 3) {
                this.recommendations.push({
                    type: "layout-hint",
                    message: `Grupo vertical "${group.name}" com ${group.children.length} elementos → usar UIListLayout`,
                    suggestion: "Adicionar UIListLayout no Frame pai no Roblox",
                });
            }
        }
    }

    /**
     * Detecta camadas sobrepostas
     */
    _detectOverlaps(layers) {
        const overlaps = [];
        for (let i = 0; i < layers.length; i++) {
            for (let j = i + 1; j < layers.length; j++) {
                const a = layers[i].bounds;
                const b = layers[j].bounds;
                if (!a || !b) continue;

                const overlapX = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
                const overlapY = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);

                if (overlapX > 0 && overlapY > 0) {
                    const overlapArea = overlapX * overlapY;
                    const minArea = Math.min(a.width * a.height, b.width * b.height);
                    if (overlapArea > minArea * 0.5) {
                        overlaps.push([layers[i].name, layers[j].name]);
                    }
                }
            }
        }
        return overlaps;
    }

    /**
     * Detecta grupos verticais (elementos alinhados)
     */
    _detectVerticalGroups(layers) {
        const groups = [];
        const byY = {};

        for (const layer of layers) {
            if (!layer.bounds) continue;
            const key = Math.round(layer.bounds.y / 30) * 30;
            if (!byY[key]) byY[key] = [];
            byY[key].push(layer);
        }

        for (const [key, members] of Object.entries(byY)) {
            if (members.length >= 2) {
                const sorted = members.sort((a, b) => (a.bounds?.x || 0) - (b.bounds?.x || 0));
                const isVertical = sorted.every((l, i) => {
                    if (i === 0) return true;
                    return Math.abs((l.bounds?.y || 0) - (sorted[i - 1].bounds?.y || 0)) < 30;
                });

                if (isVertical) {
                    groups.push({
                        name: `vertical-group-${key}`,
                        children: sorted.map(l => l.name),
                        y: parseInt(key),
                    });
                }
            }
        }
        return groups;
    }

    /**
     * Estima performance para Roblox
     */
    _estimatePerformance(uds) {
        const totalLayers = uds.layers.length;
        const totalGroups = (uds.groups || []).length;
        const totalAssets = uds.assets.length;

        // Estimativa de instâncias no Roblox
        const estimatedInstances = totalLayers + totalGroups * 2; // groups viram Frames + layouts
        const zIndexOverhead = Math.min(totalLayers, 50); // Roblox limita ZIndex prático

        this.performance = {
            estimatedInstances,
            estimatedZIndexMax: zIndexOverhead,
            instanceBudget: this.limits.maxInstances,
            instanceUtilization: Math.round((estimatedInstances / this.limits.maxInstances) * 100),
            assetCount: totalAssets,
            totalLayers,
            totalGroups,
            complexity: estimatedInstances < 50 ? "low" : estimatedInstances < 100 ? "medium" : "high",
            recommendedOptimization: this._getOptimizationTips(uds),
        };
    }

    /**
     * Gera dicas de otimização
     */
    _getOptimizationTips(uds) {
        const tips = [];
        const totalAssets = uds.assets.length;
        const largeAssets = uds.assets.filter(a => a.width > 512 || a.height > 512);

        if (totalAssets > 30) {
            tips.push("Considerar atlas de texturas para reduzir número de assets");
        }
        if (largeAssets.length > 0) {
            tips.push(`${largeAssets.length} assets > 512px — considerar compressão para mobile`);
        }
        if (uds.layers.some(l => l.opacity < 0.5)) {
            tips.push("Camadas com opacidade baixa aumentam render cost — verificar se são necessárias");
        }

        return tips;
    }

    /**
     * Calcula score de compatibilidade global
     */
    _calculateScore(uds) {
        const errors = this.issues.length;
        const warnings = this.warnings.length;
        const recommendations = this.recommendations.length;
        const totalChecks = uds.layers.length * 3; // ~3 checks por layer

        const errorPenalty = errors * 15;
        const warningPenalty = warnings * 5;
        const recommendationBonus = Math.min(recommendations * 2, 20);

        let score = Math.max(0, 100 - errorPenalty - warningPenalty + recommendationBonus);
        score = Math.min(100, score);

        this.performance.score = score;
        this.performance.grade = score >= 90 ? "A" : score >= 75 ? "B" : score >= 60 ? "C" : score >= 40 ? "D" : "F";
        this.performance.status = errors === 0 ? "pass" : "fail";
    }

    /**
     * Constrói relatório final
     */
    _buildReport(uds) {
        return {
            summary: {
                score: this.performance.score,
                grade: this.performance.grade,
                status: this.performance.status,
                totalChecks: uds.layers.length,
                timestamp: new Date().toISOString(),
            },
            errors: this.issues,
            warnings: this.warnings,
            recommendations: this.recommendations,
            performance: this.performance,
            udsSnapshot: {
                document: uds.document,
                layers: uds.layers.length,
                groups: (uds.groups || []).length,
                assets: uds.assets.length,
                colors: uds.colors.length,
                fonts: uds.fonts.length,
            },
        };
    }

    /**
     * Gera relatório em texto legível
     */
    toTextReport() {
        const lines = [];
        const s = this.performance;

        lines.push("═".repeat(60));
        lines.push(`  Roblox UI Verification Report  Score: ${s.score}/100 (${s.grade})`);
        lines.push("═".repeat(60));
        lines.push("");

        if (this.issues.length > 0) {
            lines.push(`❌ ERROS (${this.issues.length}):`);
            for (const issue of this.issues) {
                lines.push(`   • ${issue.message}`);
                lines.push(`     Fix: ${issue.fix}`);
            }
            lines.push("");
        }

        if (this.warnings.length > 0) {
            lines.push(`⚠️  AVISOS (${this.warnings.length}):`);
            for (const w of this.warnings) {
                lines.push(`   • ${w.message}`);
            }
            lines.push("");
        }

        if (this.recommendations.length > 0) {
            lines.push(`💡 RECOMENDAÇÕES (${this.recommendations.length}):`);
            for (const r of this.recommendations.slice(0, 10)) {
                lines.push(`   • ${r.desc || r.message}`);
            }
            lines.push("");
        }

        lines.push("── Performance ──");
        lines.push(`   Instâncias estimadas: ${s.estimatedInstances} / ${s.instanceBudget}`);
        lines.push(`   Complexidade: ${s.complexity}`);
        lines.push(`   Assets: ${s.assetCount}`);
        if (s.recommendedOptimization) {
            for (const tip of s.recommendedOptimization) {
                lines.push(`   • ${tip}`);
            }
        }

        return lines.join("\n");
    }

    /**
     * Salva relatório em arquivo
     */
    saveReport(report, outputPath) {
        const reportPath = path.join(outputPath, "verification_report.json");
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
        return reportPath;
    }
}

// ── Factory ─────────────────────────────────────────────────────────────────────

function createVerificationEngine(options = {}) {
    return new VerificationEngine(options);
}

// ── Export ──────────────────────────────────────────────────────────────────────

module.exports = {
    VerificationEngine,
    createVerificationEngine,
    ROBLOX_LIMITS,
    ROBLOX_UNSUPPORTED,
    SUPPORTED_ROBLOX_CLASSES,
    RESPONSIVE_STRATEGIES,
};
