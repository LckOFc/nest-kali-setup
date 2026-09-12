#target photoshop
// ============================================================
// verification-bridge.jsx — Verificação + IA para UXP Panel
// FigmaPS2Roblox v3.0
//
// Este script estende o hostscript.jsx com comandos de
// verificação e análise que o painel UXP pode invocar via
// ps.core.executeCommand com scriptEvent.
//
// Comandos suportados:
//   getDocInfo     → Informações do documento
//   getLayers      → Lista de camadas com classificação
//   getArtboards   → Lista de artboards
//   verify         → Executa verificação Roblox completa
//   exportLayer    → Exporta uma camada específica como PNG
//   exportAll      → Exporta todas as camadas
// ============================================================

var CONFIG = {
    canvasWidth: 1920,
    canvasHeight: 1080,
    maxAssetResolution: 2048,
    robloxClasses: {
        background: "ImageLabel",
        panel: "Frame",
        button: "TextButton",
        label: "TextLabel",
        icon: "ImageLabel",
        image: "ImageLabel",
        bar: "Frame",
        separator: "Frame",
        input: "TextBox"
    },
    layerPrefixes: {
        background: ["bg", "back", "base", "fundo", "wallpaper"],
        button: ["btn", "button", "play", "start", "cta", "submit"],
        label: ["title", "label", "text", "score", "caption", "desc", "body", "info"],
        icon: ["icon", "img", "logo", "avatar", "sprite", "photo"],
        panel: ["panel", "frame", "box", "card", "container"],
        bar: ["bar", "health", "hp", "stamina", "mana", "xp", "progress"],
        separator: ["sep", "line", "divider", "separator"]
    }
};

// ============================================================
// GET DOCUMENT INFO
// ============================================================

function getDocInfo() {
    if (app.documents.length === 0) return null;
    var doc = app.activeDocument;
    CONFIG.canvasWidth = Math.round(doc.width.as("px"));
    CONFIG.canvasHeight = Math.round(doc.height.as("px"));

    return {
        name: doc.name,
        width: CONFIG.canvasWidth,
        height: CONFIG.canvasHeight,
        resolution: Math.round(doc.resolution),
        mode: doc.modeName,
        bitDepth: doc.bitDepth,
        layers: countVisibleLayers(doc),
        groups: countGroups(doc),
        artboards: countArtboards(doc),
        timestamp: new Date().toISOString()
    };
}

// ============================================================
// GET LAYERS (with classification)
// ============================================================

function getLayers() {
    if (app.documents.length === 0) return null;
    var doc = app.activeDocument;
    var result = [];

    function collect(layer, depth) {
        var kind = layer.kind ? layer.kind.toString() : "";

        if (kind.includes("LayerSet") || kind.includes("Group")) {
            // Skip group nodes, only return leaf layers
            if (layer.layers) {
                for (var i = 0; i < layer.layers.length; i++) {
                    collect(layer.layers[i], depth + 1);
                }
            }
        } else if (kind.includes("Layer")) {
            if (!layer.visible) return;
            try {
                var bounds = layer.visibleBounds || layer.bounds;
                var left = Math.round(bounds[0].as("px"));
                var top = Math.round(bounds[1].as("px"));
                var right = Math.round(bounds[2].as("px"));
                var bottom = Math.round(bounds[3].as("px"));
                var w = right - left;
                var h = bottom - top;

                if (w <= 0 || h <= 0) return;

                var type = classifyLayer(layer.name);
                var fill = extractFillColor(layer);
                var textInfo = extractTextInfo(layer);

                result.push({
                    name: layer.name,
                    type: type,
                    robloxClass: CONFIG.robloxClasses[type] || "Frame",
                    visible: layer.visible,
                    opacity: Math.round((layer.opacity / 100) * 100) / 100,
                    blendMode: getBlendMode(layer),
                    x: left,
                    y: Math.round(CONFIG.canvasHeight - bottom),
                    width: w,
                    height: h,
                    depth: depth,
                    fill: fill,
                    text: textInfo,
                    cornerRadius: extractCornerRadius(layer),
                    effects: extractEffects(layer),
                    isClipped: layer.clippingMaskStart !== undefined
                });
            } catch (e) {
                $.writeln("[Bridge] Error collecting layer: " + e);
            }
        }
    }

    for (var i = 0; i < doc.layers.length; i++) {
        collect(doc.layers[i], 0);
    }

    return result;
}

// ============================================================
// GET ARTBOARDS
// ============================================================

function getArtboards() {
    if (app.documents.length === 0) return [];
    var doc = app.activeDocument;
    var result = [];

    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        if (layer.typename === "Artboard") {
            result.push({
                id: layer.id,
                name: layer.name,
                x: Math.round(layer.left),
                y: Math.round(layer.top),
                width: Math.round(layer.width),
                height: Math.round(layer.height),
                visible: layer.visible
            });
        }
    }

    return result;
}

// ============================================================
// VERIFICATION ENGINE (ExtendScript)
// ============================================================

function verifyDocument() {
    if (app.documents.length === 0) {
        return JSON.stringify({ success: false, error: "Nenhum documento aberto" });
    }

    var doc = app.activeDocument;
    var w = Math.round(doc.width.as("px"));
    var h = Math.round(doc.height.as("px"));
    var layers = getLayers();
    var issues = [];
    var warnings = [];
    var recommendations = [];

    // Document checks
    if (w > 2048 || h > 2048) {
        warnings.push({ message: "Canvas " + w + "×" + h + " excede limite Roblox (2048×2048)", fix: "Redimensionar para ≤ 2048px" });
    }
    if (doc.resolution > 144) {
        warnings.push({ message: "Resolução " + doc.resolution + " DPI alta para Roblox", fix: "Usar 72-96 DPI" });
    }
    if (doc.modeName !== "RGB") {
        issues.push({ message: "Modo de cor " + doc.modeName + " não suportado. Roblox exige RGB.", fix: "Converter para RGB" });
    }

    // Layer checks
    var estimatedInstances = 0;
    var unsupportedBlends = ["Additive", "Multiply", "Screen", "Overlay", "Difference", "Exclusion"];
    var hasLowOpacity = false;
    var hasTransparentBg = false;

    for (var i = 0; i < layers.length; i++) {
        var l = layers[i];
        estimatedInstances++;

        // Out of bounds
        if (l.x + l.width > w + 10) {
            warnings.push({ message: '"' + l.name + '" sai do canvas pela direita', fix: "Mover para dentro do artboard" });
        }
        if (l.y + l.height > h + 10) {
            warnings.push({ message: '"' + l.name + '" sai do canvas pela parte inferior', fix: "Mover para dentro do artboard" });
        }

        // Low opacity
        if (l.opacity < 0.01) {
            warnings.push({ message: '"' + l.name + '" opacidade muito baixa (' + l.opacity + ')', fix: "Aumentar opacidade" });
        }

        // Blend mode
        if (unsupportedBlends.indexOf(l.blendMode) !== -1) {
            warnings.push({ message: 'Blend mode "' + l.blendMode + '" não suportado no Roblox', fix: "Usar Normal" });
        }

        // Oversized
        if (l.width > 2048 || l.height > 2048) {
            warnings.push({ message: '"' + l.name + '" (' + l.width + "×" + l.height + ') excede resolução máxima', fix: "Redimensionar" });
        }

        // Track for recommendations
        if (l.opacity < 0.5) hasLowOpacity = true;
        if (l.type === "background") hasTransparentBg = true;

        // Add recommendation
        recommendations.push({
            layerName: l.name,
            role: l.type,
            robloxClass: l.robloxClass,
            strategy: getResponsiveStrategy(l.type),
            bounds: { x: l.x, y: l.y, width: l.width, height: l.height }
        });
    }

    // Layout hints
    var verticalGroups = detectVerticalGroups(layers);
    for (var g = 0; g < verticalGroups.length; g++) {
        if (verticalGroups[g].count >= 3) {
            recommendations.push({
                type: "layout-hint",
                message: 'Grupo vertical "' + verticalGroups[g].name + '" com ' + verticalGroups[g].count + ' elementos → usar UIListLayout'
            });
        }
    }

    // Performance
    var complexity = estimatedInstances < 50 ? "low" : estimatedInstances < 100 ? "medium" : "high";
    var utilization = Math.round((estimatedInstances / 150) * 100);

    // Score
    var errorPenalty = issues.length * 15;
    var warningPenalty = warnings.length * 5;
    var score = Math.max(0, Math.min(100, 100 - errorPenalty - warningPenalty));
    var grade = score >= 90 ? "A" : score >= 75 ? "B" : score >= 60 ? "C" : score >= 40 ? "D" : "F";

    var report = {
        summary: {
            score: score,
            grade: grade,
            status: issues.length === 0 ? "pass" : "fail",
            totalLayers: layers.length,
            timestamp: new Date().toISOString()
        },
        errors: issues,
        warnings: warnings,
        recommendations: recommendations,
        performance: {
            estimatedInstances: estimatedInstances,
            complexity: complexity,
            utilization: utilization,
            instanceBudget: 150,
            optimizations: generateOptimizationTips(layers, hasLowOpacity)
        }
    };

    return JSON.stringify(report);
}

function getResponsiveStrategy(type) {
    var strategies = {
        background: "Fill",
        button: "ScaleToFit",
        label: "ScaleToFit",
        icon: "FixedSize",
        panel: "ScaleToFit",
        bar: "FixedSize",
        image: "ScaleToFit",
        separator: "FixedSize",
        input: "ScaleToFit"
    };
    return strategies[type] || "ScaleToFit";
}

function detectVerticalGroups(layers) {
    var groups = [];
    var byY = {};

    for (var i = 0; i < layers.length; i++) {
        var key = Math.round(layers[i].y / 30) * 30;
        if (!byY[key]) byY[key] = [];
        byY[key].push(layers[i]);
    }

    for (var key in byY) {
        var members = byY[key];
        if (members.length >= 2) {
            members.sort(function(a, b) { return a.x - b.x; });
            var isV = true;
            for (var j = 1; j < members.length; j++) {
                if (Math.abs(members[j].y - members[j - 1].y) > 20) { isV = false; break; }
            }
            if (isV) groups.push({ name: "vgroup-" + key, count: members.length });
        }
    }
    return groups;
}

function generateOptimizationTips(layers, hasLowOpacity) {
    var tips = [];
    if (layers.length > 30) tips.push("Considerar atlas de texturas para reduzir instâncias");
    var large = 0;
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].width > 512 || layers[i].height > 512) large++;
    }
    if (large > 0) tips.push(large + " layers > 512px — comprimir para mobile");
    if (hasLowOpacity) tips.push("Camadas com opacidade baixa aumentam render cost");
    return tips;
}

// ============================================================
// EXPORT SINGLE LAYER AS PNG
// ============================================================

function exportLayer(layerName, outputPath, fileName) {
    if (app.documents.length === 0) return JSON.stringify({ success: false, error: "Nenhum documento" });

    var doc = app.activeDocument;
    var layer = findLayerByName(doc, layerName);
    if (!layer) return JSON.stringify({ success: false, error: "Layer not found: " + layerName });

    try {
        var bounds = layer.visibleBounds || layer.bounds;
        var left = Math.round(bounds[0].as("px"));
        var top = Math.round(bounds[1].as("px"));
        var right = Math.round(bounds[2].as("px"));
        var bottom = Math.round(bounds[3].as("px"));
        var w = right - left;
        var h = bottom - top;

        if (w <= 0 || h <= 0) return JSON.stringify({ success: false, error: "Bounds inválidos" });

        // Create temp document
        var tempDoc = app.documents.add(w, h, 72, "temp_" + layerName, NewDocumentMode.RGB, DocumentFill.TRANSPARENT);

        // Duplicate layer
        layer.duplicate(tempDoc, ElementPlacement.PLACEATBEGINNING);

        // Shift to origin
        var shiftX = -left;
        var shiftY = -top;
        tempDoc.selection.selectAll();
        tempDoc.selection.translate(shiftX, shiftY);
        tempDoc.selection.deselect();

        // Flatten and export
        tempDoc.flatten();

        var pngFile = new File(outputPath + "/" + fileName);
        var pngOpts = new PNGSaveOptions();
        pngOpts.compression = 9;
        pngOpts.transparent = true;
        tempDoc.saveAs(pngFile, pngOpts);
        tempDoc.close(SaveOptions.DONOTSAVECHANGES);

        return JSON.stringify({
            success: true,
            name: layerName,
            file: fileName,
            width: w,
            height: h
        });
    } catch (e) {
        return JSON.stringify({ success: false, error: e.toString() });
    }
}

// ============================================================
// EXPORT ALL LAYERS
// ============================================================

function exportAllLayers(outputPath, screenName, options) {
    options = options || {};
    if (app.documents.length === 0) return JSON.stringify({ success: false, error: "Nenhum documento" });

    var doc = app.activeDocument;
    CONFIG.canvasWidth = Math.round(doc.width.as("px"));
    CONFIG.canvasHeight = Math.round(doc.height.as("px"));

    var layers = getLayers();
    var seed = generateSeed();
    var assets = [];
    var errors = [];
    var exported = 0;

    for (var i = 0; i < layers.length; i++) {
        var l = layers[i];
        var uid = generateHash(seed, l.name);
        var safeName = sanitizeName(l.name);
        var fileName = safeName + "_" + uid + ".png";
        var filePath = outputPath + "/" + fileName;

        var result = exportLayer(l.name, outputPath, fileName);
        var parsed = JSON.parse(result);

        if (parsed.success) {
            exported++;
            assets.push({
                name: l.name,
                file: fileName,
                uid: uid,
                width: l.width,
                height: l.height,
                type: l.type,
                x: l.x,
                y: l.y,
                opacity: l.opacity,
                fill: l.fill,
                stroke: l.stroke,
                cornerRadius: l.cornerRadius,
                effects: l.effects,
                text: l.text,
                assetId: "rbxassetid://0",
                robloxClass: l.robloxClass,
                bypassEnabled: options.bypass || false,
                bypassTechnique: options.bypassTech || null,
                isClipped: l.isClipped || false,
            });
        } else {
            errors.push(parsed.error || ("Failed: " + l.name));
        }
    }

    // Generate manifest
    var manifest = {
        version: "3.0.0",
        source: "photoshop",
        name: screenName,
        canvasWidth: CONFIG.canvasWidth,
        canvasHeight: CONFIG.canvasHeight,
        scaleMode: "ScaleToFit",
        seed: seed,
        generated: new Date().toISOString(),
        bypassUsed: options.bypass || false,
        bypassTechnique: options.bypassTech || null,
        assets: assets,
        elements: assets.map(function(a) {
            return {
                name: a.name,
                type: a.type,
                robloxClass: a.robloxClass || "Frame",
                x: a.x,
                y: a.y,
                width: a.width,
                height: a.height,
                assetId: "rbxassetid://0"
            };
        }),
        layoutHints: detectLayoutHints(assets)
    };

    // Write files
    writeJSON(outputPath + "/" + screenName + "_manifest.json", manifest);
    writeLua(outputPath + "/" + screenName + "_controller.lua", manifest);
    writeGuide(outputPath + "/" + screenName + "_upload_guide.txt", manifest, seed, errors);

    return JSON.stringify({
        success: true,
        exported: exported,
        errors: errors.length,
        seed: seed,
        assets: assets.length,
        outputFolder: outputPath,
        canvasWidth: CONFIG.canvasWidth,
        canvasHeight: CONFIG.canvasHeight,
        bypassUsed: options.bypass || false,
        artboardName: null
    });
}

// ============================================================
// HELPERS
// ============================================================

function findLayerByName(doc, name) {
    var all = getAllLayers(doc);
    for (var i = 0; i < all.length; i++) {
        if (all[i].name === name) return all[i];
    }
    return null;
}

function getAllLayers(doc) {
    var layers = [];
    function collect(layer) {
        layers.push(layer);
        if (layer.typename === "LayerSet" && layer.layers) {
            for (var i = 0; i < layer.layers.length; i++) collect(layer.layers[i]);
        }
        if (layer.typename === "Artboard" && layer.layers) {
            for (var i = 0; i < layer.layers.length; i++) collect(layer.layers[i]);
        }
    }
    for (var i = 0; i < doc.layers.length; i++) collect(doc.layers[i]);
    return layers;
}

function classifyLayer(name) {
    var lower = (name || "").toLowerCase();
    for (var type in CONFIG.layerPrefixes) {
        var prefixes = CONFIG.layerPrefixes[type];
        for (var i = 0; i < prefixes.length; i++) {
            if (lower.indexOf(prefixes[i]) !== -1) return type;
        }
    }
    return "image";
}

function getBlendMode(layer) {
    try { return layer.blendMode.toString().replace("BlendMode.", ""); } catch (e) { return "Normal"; }
}

function extractFillColor(layer) {
    try {
        var ls = layer.layerStyle;
        if (!ls) return null;
        var solid = ls.solidColorLayer;
        if (solid && solid.visible) {
            var c = solid.color;
            return {
                r: Math.round(c.red * 255), g: Math.round(c.green * 255), b: Math.round(c.blue * 255),
                hex: rgbToHex(Math.round(c.red * 255), Math.round(c.green * 255), Math.round(c.blue * 255))
            };
        }
    } catch (e) {}
    return null;
}

function extractTextInfo(layer) {
    try {
        var ti = layer.textItem;
        if (!ti) return null;
        return {
            content: ti.contents,
            size: Math.round(ti.size),
            font: ti.font || "Unknown",
            bold: ti.bold || false,
            color: ti.color ? rgbToHex(Math.round(ti.color.red * 255), Math.round(ti.color.green * 255), Math.round(ti.color.blue * 255)) : null
        };
    } catch (e) { return null; }
}

function extractEffects(layer) {
    var effects = [];
    try {
        var ls = layer.layerStyle;
        if (!ls) return effects;
        if (ls.dropShadowLayer && ls.dropShadowLayer.visible) {
            var ds = ls.dropShadowLayer;
            effects.push({
                type: "dropShadow",
                distance: Math.round(ds.distance || 0),
                blur: Math.round(ds.blur || 0),
                opacity: Math.round(ds.opacity || 100),
                color: rgbToHex(Math.round(ds.color.red * 255), Math.round(ds.color.green * 255), Math.round(ds.color.blue * 255))
            });
        }
    } catch (e) {}
    return effects;
}

function extractCornerRadius(layer) {
    if ((layer.name || "").toLowerCase().indexOf("round") !== -1) return 8;
    return 0;
}

function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(function(x) {
        var hex = Math.max(0, Math.min(255, x)).toString(16);
        return hex.length === 1 ? "0" + hex : hex;
    }).join("").toUpperCase();
}

function generateSeed() {
    var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    var result = "";
    for (var i = 0; i < 8; i++) result += chars.charAt(Math.floor(Math.random() * chars.length));
    return result;
}

function generateHash(seed, name) {
    var hash = 0;
    var str = seed + name + new Date().getTime();
    for (var i = 0; i < str.length; i++) {
        var ch = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + ch;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(12, "0");
}

function sanitizeName(name) {
    return (name || "")
        .replace(/\.[^\.]+$/, "")
        .replace(/[<>:"\/\\|?*\x00-\x1f]/g, "_")
        .replace(/\s+/g, "_")
        .replace(/_+/g, "_")
        .substring(0, 50);
}

function countVisibleLayers(doc) {
    var count = 0;
    function collect(layer) {
        if (layer.typename === "Layer" && layer.visible) count++;
        if (layer.layers) {
            for (var i = 0; i < layer.layers.length; i++) collect(layer.layers[i]);
        }
    }
    for (var i = 0; i < doc.layers.length; i++) collect(doc.layers[i]);
    return count;
}

function countArtboards(doc) {
    var count = 0;
    for (var i = 0; i < doc.layers.length; i++) {
        if (doc.layers[i].typename === "Artboard") count++;
    }
    return count;
}

function countGroups(doc) {
    var count = 0;
    function collect(layer) {
        if (layer.typename === "LayerSet") count++;
        if (layer.layers) {
            for (var i = 0; i < layer.layers.length; i++) collect(layer.layers[i]);
        }
    }
    for (var i = 0; i < doc.layers.length; i++) collect(doc.layers[i]);
    return count;
}

function detectLayoutHints(assets) {
    var hints = { verticalGroups: [], horizontalGroups: [] };
    var byY = {};
    for (var i = 0; i < assets.length; i++) {
        var key = Math.round(assets[i].y / 40) * 40;
        if (!byY[key]) byY[key] = [];
        byY[key].push(assets[i]);
    }
    for (var key in byY) {
        var members = byY[key];
        if (members.length >= 2) {
            members.sort(function(a, b) { return a.x - b.x; });
            var isH = true;
            for (var j = 1; j < members.length; j++) {
                if (Math.abs(members[j].y - members[j - 1].y) > 20) { isH = false; break; }
            }
            if (isH) hints.horizontalGroups.push(members.map(function(l) { return l.name; }));
        }
    }
    var byX = {};
    for (var i = 0; i < assets.length; i++) {
        var key = Math.round(assets[i].x / 40) * 40;
        if (!byX[key]) byX[key] = [];
        byX[key].push(assets[i]);
    }
    for (var key in byX) {
        var members = byX[key];
        if (members.length >= 2) {
            members.sort(function(a, b) { return a.y - b.y; });
            var isV = true;
            for (var j = 1; j < members.length; j++) {
                if (Math.abs(members[j].x - members[j - 1].x) > 20) { isV = false; break; }
            }
            if (isV) hints.verticalGroups.push(members.map(function(l) { return l.name; }));
        }
    }
    return hints;
}

function writeJSON(filePath, obj) {
    var f = new File(filePath);
    f.encoding = "UTF-8";
    f.open("w");
    f.write(JSON.stringify(obj, null, 2));
    f.close();
}

function writeLua(filePath, manifest) {
    var w = manifest.canvasWidth;
    var h = manifest.canvasHeight;
    var lines = [];
    lines.push("--!strict");
    lines.push("-- Auto-generated by FigmaPS2Roblox v3.0");
    lines.push("-- Screen: " + manifest.name);
    lines.push("-- Canvas: " + w + "x" + h);
    lines.push("-- Generated: " + manifest.generated);
    lines.push("");
    lines.push("local Players = game:GetService('Players')");
    lines.push("local GeneratedUI = {}");
    lines.push("GeneratedUI.__index = GeneratedUI");
    lines.push("");
    lines.push("function GeneratedUI.new()");
    lines.push("    local self = setmetatable({}, GeneratedUI)");
    lines.push("    self.Elements = {}");
    lines.push("    return self");
    lines.push("end");
    lines.push("");
    lines.push("function GeneratedUI:CreateElement(parent, config)");
    lines.push("    local el = Instance.new(config.Class)");
    lines.push("    el.Name = config.Name");
    lines.push("    el.Position = UDim2.new(config.X/" + w + ", config.OffsetX or 0, config.Y/" + h + ", config.OffsetY or 0)");
    lines.push("    el.Size = UDim2.new(config.Width/" + w + ", config.OffsetWidth or 0, config.Height/" + h + ", config.OffsetHeight or 0)");
    lines.push("    if config.BackgroundColor3 then el.BackgroundColor3 = config.BackgroundColor3 end");
    lines.push("    if config.CornerRadius and config.CornerRadius > 0 then");
    lines.push("        local corner = Instance.new('UICorner')");
    lines.push("        corner.CornerRadius = UDim.new(0, config.CornerRadius)");
    lines.push("        corner.Parent = el");
    lines.push("    end");
    lines.push("    if config.Text then el.Text = config.Text end");
    lines.push("    if config.Image then el.Image = config.Image end");
    lines.push("    el.Parent = parent");
    lines.push("    return el");
    lines.push("end");
    lines.push("");
    lines.push("function GeneratedUI:Build(parent)");
    lines.push("    local screenGui = Instance.new('ScreenGui')");
    lines.push("    screenGui.Name = '" + manifest.name + "'");
    lines.push("    screenGui.ResetOnSpawn = false");
    lines.push("    screenGui.IgnoreGuiInset = true");
    lines.push("    screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling");
    lines.push("    screenGui.Parent = parent or Players.LocalPlayer:WaitForChild('PlayerGui')");
    lines.push("");

    for (var i = 0; i < manifest.assets.length; i++) {
        var a = manifest.assets[i];
        var safeVar = sanitizeName(a.name);
        lines.push("    local " + safeVar + " = self:CreateElement(screenGui, {");
        lines.push("        Class = '" + (a.robloxClass || 'Frame') + "',");
        lines.push("        Name = '" + escapeLua(a.name) + "',");
        lines.push("        X = " + a.x + ", Y = " + a.y + ",");
        lines.push("        Width = " + a.width + ", Height = " + a.height + ",");
        if (a.fill) {
            lines.push("        BackgroundColor3 = Color3.fromRGB(" + a.fill.r + ", " + a.fill.g + ", " + a.fill.b + "),");
        }
        if (a.cornerRadius) lines.push("        CornerRadius = " + a.cornerRadius + ",");
        if (a.text && a.text.content) lines.push("        Text = '" + escapeLua(a.text.content) + "',");
        lines.push("    })");
        lines.push("");
    }

    lines.push("    self.Elements = {}");
    lines.push("    return screenGui");
    lines.push("end");
    lines.push("");
    lines.push("return GeneratedUI");

    var f = new File(filePath);
    f.encoding = "UTF-8";
    f.open("w");
    f.write(lines.join("\n"));
    f.close();
}

function writeGuide(filePath, manifest, seed, errors) {
    var txt = "# Guia de Upload — " + manifest.name + "\n\n";
    txt += "**Versão:** FigmaPS2Roblox v3.0\n";
    txt += "**Canvas:** " + manifest.canvasWidth + "×" + manifest.canvasHeight + "\n";
    txt += "**Assets:** " + manifest.assets.length + " PNGs processados\n";
    txt += "**Seed:** " + seed + "\n";
    if (manifest.bypassUsed) txt += "**Bypass:** " + (manifest.bypassTechnique || "all") + "\n";
    txt += "\n---\n\n";
    txt += "## Passos para Roblox Studio\n\n";
    txt += "1️⃣  Abra o Roblox Studio\n";
    txt += "2️⃣  No Explorer: `ReplicatedStorage > UIAssets > " + manifest.name + "` (crie se não existir)\n";
    txt += "3️⃣  Arraste os " + manifest.assets.length + " arquivos PNG da pasta de saída para o Explorer\n";
    txt += "4️⃣  Aguarde o upload completar\n";
    txt += "5️⃣  Copie os Asset IDs (clique direito no asset > Copy Asset ID)\n\n";
    txt += "## Atualizar o manifest\n\n";
    txt += "Edite `" + manifest.name + "_manifest.json` substituindo cada `'rbxassetid://0'`\n";
    txt += "pelo ID real do asset correspondente.\n\n";
    txt += "## Controller gerado\n\n";
    txt += "- `" + manifest.name + "_controller.lua` — Script principal\n\n";
    if (errors.length > 0) {
        txt += "## ⚠️ Erros durante exportação\n\n";
        for (var i = 0; i < errors.length; i++) {
            txt += "- " + errors[i] + "\n";
        }
    }
    txt += "\n## Uso no jogo\n\n";
    txt += "```lua\n";
    txt += "local ReplicatedStorage = game:GetService('ReplicatedStorage')\n";
    txt += "local Players = game:GetService('Players')\n\n";
    txt += "local GeneratedUI = require(ReplicatedStorage:WaitForChild('" + manifest.name + "._controller'))\n";
    txt += "local ui = GeneratedUI.new()\n";
    txt += "ui:Build(Players.LocalPlayer:WaitForChild('PlayerGui'))\n";
    txt += "```\n";

    var f = new File(filePath);
    f.encoding = "UTF-8";
    f.open("w");
    f.write(txt);
    f.close();
}

function escapeLua(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

// ============================================================
// MAIN (for direct execution)
// ============================================================

function main() {
    if (app.documents.length === 0) {
        alert("Abra um documento no Photoshop primeiro!");
        return;
    }

    var outputPath = Folder.selectDialog("Selecione a pasta de saída:");
    if (!outputPath) return;

    var doc = app.activeDocument;
    CONFIG.canvasWidth = Math.round(doc.width.as("px"));
    CONFIG.canvasHeight = Math.round(doc.height.as("px"));

    var screenName = prompt("Nome da tela (ex: MainMenu, HUD):", doc.name.replace(/\.[^\.]+$/, ""));
    if (!screenName) return;

    var result = JSON.parse(exportAllLayers(outputPath.fsName, screenName, {}));
    if (result.success) {
        alert("✅ Exportação concluída!\n\nAssets: " + result.exported + "\nErros: " + result.errors + "\nSeed: " + result.seed + "\nPasta: " + result.outputFolder);
    } else {
        alert("❌ Erro: " + result.error);
    }
}

if (typeof cep === "undefined") {
    main();
}
