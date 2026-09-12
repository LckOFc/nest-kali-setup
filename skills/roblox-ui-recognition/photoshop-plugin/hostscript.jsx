#target photoshop
// ============================================================
// hostscript.jsx — Backend ExtendScript para o painel CEP
// FigmaPS2Roblox v2.1.0
// ============================================================

var CONFIG = {
    canvasWidth: 1920,
    canvasHeight: 1080,
    layerPrefixes: {
        frame: ["frame", "container", "panel", "bg", "background", "card", "box"],
        button: ["button", "btn", "click", "play", "start", "submit", "cta"],
        text: ["text", "label", "title", "caption", "desc", "body", "info", "score"],
        image: ["image", "icon", "img", "sprite", "avatar", "logo", "photo"],
        input: ["input", "field", "textbox", "edit", "search"],
        bar: ["bar", "health", "hp", "stamina", "mana", "xp", "progress"]
    },
    robloxClasses: {
        frame: "Frame",
        button: "TextButton",
        text: "TextLabel",
        image: "ImageLabel",
        input: "TextBox",
        background: "ImageLabel",
        panel: "Frame",
        bar: "Frame"
    }
};

// ============================================================
// GET DOCUMENT INFO
// ============================================================

function getDocInfo() {
    if (app.documents.length === 0) return null;
    var doc = app.activeDocument;
    return {
        name: doc.name,
        width: Math.round(doc.width.as("px")),
        height: Math.round(doc.height.as("px")),
        resolution: Math.round(doc.resolution),
        mode: doc.modeName,
        layers: countVisibleLayers(doc),
        artboards: countArtboards(doc),
        groups: countGroups(doc),
        timestamp: new Date().toISOString()
    };
}

function countVisibleLayers(doc) {
    var count = 0;
    function collect(layer) {
        if (layer.typename === "Layer" && layer.visible) count++;
        if (layer.layers) {
            for (var i = 0; i < layer.layers.length; i++) {
                collect(layer.layers[i]);
            }
        }
    }
    for (var i = 0; i < doc.layers.length; i++) {
        collect(doc.layers[i]);
    }
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
            for (var i = 0; i < layer.layers.length; i++) {
                collect(layer.layers[i]);
            }
        }
    }
    for (var i = 0; i < doc.layers.length; i++) {
        collect(doc.layers[i]);
    }
    return count;
}

// ============================================================
// GET LAYER TREE (with optional artboard filter)
// ============================================================

function getLayerTree(artboardId) {
    if (app.documents.length === 0) return null;
    var doc = app.activeDocument;
    
    // If artboardId provided, filter to that artboard only
    if (artboardId) {
        return getArtboardLayers(doc, artboardId);
    }
    
    var tree = [];
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        if (layer.typename === "Artboard") {
            tree.push(buildArtboardNode(layer, doc));
        } else if (layer.typename === "LayerSet") {
            tree.push(buildGroupNode(layer));
        } else if (layer.visible && !layer.allLocked) {
            tree.push(buildLayerNode(layer, doc));
        }
    }
    return tree;
}

// Get layers within a specific artboard
function getArtboardLayers(doc, artboardId) {
    var result = [];
    
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        
        // Check if this is the selected artboard
        if (layer.typename === "Artboard" && layer.id == artboardId) {
            // Extract all layers from this artboard
            if (layer.layers) {
                for (var j = 0; j < layer.layers.length; j++) {
                    var child = layer.layers[j];
                    if (child.typename === "Layer" && child.visible && !child.allLocked) {
                        result.push(buildLayerNode(child, doc));
                    } else if (child.typename === "LayerSet") {
                        var group = buildGroupNode(child);
                        result.push(group);
                    }
                }
            }
            break;
        }
    }
    
    return result;
}

// Get selected artboard ID (from Photoshop selection)
function getSelectedArtboard() {
    if (app.documents.length === 0) return null;
    var doc = app.activeDocument;
    
    try {
        // Use correct Photoshop API for artboard selection
        // Photoshop CC 2015+ exposes artboard selection via artboards array
        var artboardIndex = 0;
        
        // Try to get active artboard index (may vary by PS version)
        try {
            artboardIndex = doc.artboards.getActiveArtboardIndex();
        } catch (e) {
            // Fallback: use first artboard if exists
            if (doc.artboards.length > 0) {
                artboardIndex = 0;
            }
        }
        
        if (artboardIndex >= 0 && artboardIndex < doc.artboards.length) {
            var artboard = doc.artboards[artboardIndex];
            return {
                id: artboard.id,
                name: artboard.name,
                bounds: artboard.artboardRect,
                x: Math.round(artboard.left),
                y: Math.round(artboard.top), // Artboards use their own coord system
                width: Math.round(artboard.width),
                height: Math.round(artboard.height)
            };
        }
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Error getting selected artboard: " + e);
    }
    
    return null;
}

function buildArtboardNode(artboard, doc) {
    // Artboards have their own coordinate system - top is Y origin
    var node = {
        name: artboard.name,
        type: "artboard",
        visible: artboard.visible,
        x: Math.round(artboard.left),
        y: Math.round(artboard.top), // Correct: artboards use top as origin
        width: Math.round(artboard.width),
        height: Math.round(artboard.height),
        children: []
    };
    if (artboard.layers) {
        for (var i = 0; i < artboard.layers.length; i++) {
            var child = artboard.layers[i];
            if (child.typename === "Layer" && child.visible && !child.allLocked) {
                node.children.push(buildLayerNode(child, doc));
            } else if (child.typename === "LayerSet") {
                node.children.push(buildGroupNode(child));
            }
        }
    }
    return node;
}

function buildGroupNode(group) {
    var node = {
        name: group.name,
        type: "group",
        visible: group.visible,
        x: Math.round(group.left),
        y: Math.round(CONFIG.canvasHeight - group.top - group.height),
        width: Math.round(group.width),
        height: Math.round(group.height),
        opacity: Math.round((group.opacity / 100) * 100) / 100,
        children: []
    };
    if (group.layers) {
        for (var i = 0; i < group.layers.length; i++) {
            var child = group.layers[i];
            if (child.typename === "Layer" && child.visible && !child.allLocked) {
                node.children.push(buildLayerNode(child, app.activeDocument));
            } else if (child.typename === "LayerSet") {
                node.children.push(buildGroupNode(child));
            }
        }
    }
    return node;
}

function buildLayerNode(layer, doc) {
    try {
        var bounds = layer.visibleBounds || layer.bounds;
        var left = Math.round(bounds[0].as("px"));
        var top = Math.round(bounds[1].as("px"));
        var right = Math.round(bounds[2].as("px"));
        var bottom = Math.round(bounds[3].as("px"));
        var w = right - left;
        var h = bottom - top;

        if (w <= 0 || h <= 0) return null;

        var info = {
            name: layer.name,
            type: classifyLayer(layer.name),
            robloxClass: CONFIG.robloxClasses[classifyLayer(layer.name)] || "Frame",
            visible: layer.visible,
            opacity: Math.round((layer.opacity / 100) * 100) / 100,
            x: left,
            y: Math.round(CONFIG.canvasHeight - bottom),
            width: w,
            height: h,
            hasText: (layer.textItem !== null),
            textContent: null,
            textColor: null,
            fillColor: extractFillColor(layer),
            strokeColor: extractStrokeColor(layer),
            cornerRadius: extractCornerRadius(layer),
            effects: extractEffects(layer),
            blendMode: getBlendMode(layer),
            isArtboard: (layer.typename === "Artboard"),
            isGroup: (layer.typename === "LayerSet"),
            _color: extractFillColor(layer) ? "#" +
                [extractFillColor(layer).r, extractFillColor(layer).g, extractFillColor(layer).b].map(function(x) {
                    return x.toString(16).padStart(2, "0");
                }).join("").toUpperCase() : "#313244"
        };

        if (layer.textItem) {
            info.textContent = layer.textItem.contents;
            info.textSize = Math.round(layer.textItem.size);
            info.textBold = layer.textItem.bold;
            info.textColor = getTextColorHex(layer);
        }

        return info;
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Error building layer node '" + layer.name + "': " + e);
        return null;
    }
}

function classifyLayer(name) {
    var lower = name.toLowerCase();
    for (var type in CONFIG.layerPrefixes) {
        var prefixes = CONFIG.layerPrefixes[type];
        for (var i = 0; i < prefixes.length; i++) {
            if (lower.indexOf(prefixes[i]) !== -1) return type;
        }
    }
    return "frame";
}

function getBlendMode(layer) {
    try {
        return layer.blendMode.toString().replace("BlendMode.", "");
    } catch (e) {
        return "Normal";
    }
}

function extractFillColor(layer) {
    try {
        var ls = layer.layerStyle;
        if (!ls) return null;
        var solid = ls.solidColorLayer;
        if (solid && solid.visible) {
            var c = solid.color;
            return {
                r: Math.round(c.red * 255),
                g: Math.round(c.green * 255),
                b: Math.round(c.blue * 255),
                a: Math.round((solid.opacity !== null && solid.opacity !== undefined) ? solid.opacity * 255 : 255),
                hex: rgbToHex(Math.round(c.red * 255), Math.round(c.green * 255), Math.round(c.blue * 255))
            };
        }
        // Try backgroundItems (newer PS versions)
        var fills = layer.backgroundItems;
        if (fills && fills.length > 0) {
            for (var i = 0; i < fills.length; i++) {
                var fill = fills[i];
                if (fill.kind && fill.kind.toString() === "SOLID") {
                    return {
                        r: Math.round(fill.color.red * 255),
                        g: Math.round(fill.color.green * 255),
                        b: Math.round(fill.color.blue * 255),
                        a: Math.round(((fill.opacity || 1) * 255)),
                        hex: rgbToHex(Math.round(fill.color.red * 255), Math.round(fill.color.green * 255), Math.round(fill.color.blue * 255))
                    };
                }
            }
        }
    } catch (e) {}
    return null;
}

function extractStrokeColor(layer) {
    try {
        var ls = layer.layerStyle;
        if (!ls) return null;
        var stroke = ls.strokeLayer;
        if (stroke && stroke.visible) {
            var c = stroke.color;
            return {
                r: Math.round(c.red * 255),
                g: Math.round(c.green * 255),
                b: Math.round(c.blue * 255),
                hex: rgbToHex(Math.round(c.red * 255), Math.round(c.green * 255), Math.round(c.blue * 255)),
                width: Math.round(stroke.size || 1)
            };
        }
    } catch (e) {}
    return null;
}

function extractCornerRadius(layer) {
    try {
        // Check if it's a shape layer with rounded rect
        if (layer.kind && layer.kind.toString() === "SHAPELAYER") {
            // Try to read from layerStyle effects
            var ls = layer.layerStyle;
            if (ls && ls.vectorStrokeLayer) {
                // Some shape layers expose corner radius via vector data
            }
        }
        // Default: check if layer has "rounded" in name as hint
        if (layer.name.toLowerCase().indexOf("round") !== -1 || layer.name.toLowerCase().indexOf("corner") !== -1) {
            return 8; // default hint
        }
    } catch (e) {}
    return 0;
}

function extractEffects(layer) {
    var effects = [];
    try {
        var ls = layer.layerStyle;
        if (!ls) return effects;

        // Drop shadow
        if (ls.dropShadowLayer && ls.dropShadowLayer.visible) {
            var ds = ls.dropShadowLayer;
            effects.push({
                type: "dropShadow",
                color: {
                    r: Math.round(ds.color.red * 255),
                    g: Math.round(ds.color.green * 255),
                    b: Math.round(ds.color.blue * 255),
                    a: Math.round((ds.opacity / 100) * 255)
                },
                distance: Math.round(ds.distance || 0),
                angle: Math.round(ds.angle || 0),
                blur: Math.round(ds.blur || 0),
                size: Math.round(ds.size || 0)
            });
        }

        // Inner shadow
        if (ls.innerShadowLayer && ls.innerShadowLayer.visible) {
            var is = ls.innerShadowLayer;
            effects.push({
                type: "innerShadow",
                color: {
                    r: Math.round(is.color.red * 255),
                    g: Math.round(is.color.green * 255),
                    b: Math.round(is.color.blue * 255),
                    a: Math.round((is.opacity / 100) * 255)
                },
                distance: Math.round(is.distance || 0),
                blur: Math.round(is.blur || 0)
            });
        }

        // Outer glow
        if (ls.outerGlowLayer && ls.outerGlowLayer.visible) {
            var og = ls.outerGlowLayer;
            effects.push({
                type: "outerGlow",
                color: {
                    r: Math.round(og.color.red * 255),
                    g: Math.round(og.color.green * 255),
                    b: Math.round(og.color.blue * 255),
                    a: Math.round((og.opacity / 100) * 255)
                },
                blur: Math.round(og.blur || 0)
            });
        }
    } catch (e) {}
    return effects;
}

function getTextColorHex(layer) {
    try {
        if (layer.textItem && layer.textItem.color) {
            var c = layer.textItem.color;
            return rgbToHex(Math.round(c.red * 255), Math.round(c.green * 255), Math.round(c.blue * 255));
        }
    } catch (e) {}
    return null;
}

function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(function(x) {
        var hex = Math.max(0, Math.min(255, x)).toString(16);
        return hex.length === 1 ? "0" + hex : hex;
    }).join("").toUpperCase();
}

// ============================================================
// EXPORT TO ROBLOX
// ============================================================

function exportToRoblox(outputPath, screenName, options) {
    options = options || {};
    if (app.documents.length === 0) {
        return JSON.stringify({ success: false, error: "Nenhum documento aberto no Photoshop" });
    }

    var doc = app.activeDocument;
    var seed = generateSeed();
    CONFIG.canvasWidth = Math.round(doc.width.as("px"));
    CONFIG.canvasHeight = Math.round(doc.height.as("px"));

    // Bypass config
    var bypassEnabled = options.bypass || false;
    var bypassTechnique = options.bypassTech || "noise";
    
    // Check for selected artboard
    var selectedArtboard = options.artboardId ? findArtboardById(doc, options.artboardId) : null;
    var artboardName = selectedArtboard ? selectedArtboard.name : null;

    var layerTree = processLayersForExport(doc, selectedArtboard);
    var assets = [];
    var exportedCount = 0;
    var errors = [];

    for (var i = 0; i < layerTree.length; i++) {
        var result = exportLayerRecursive(layerTree[i], outputPath, seed, options, bypassEnabled, bypassTechnique);
        if (result && result.success) {
            assets.push(result);
            exportedCount++;
        } else if (result && !result.success) {
            errors.push((result.error || "Unknown error") + ": " + (result.name || layerTree[i].name));
        } else {
            errors.push("Falha ao exportar: " + (layerTree[i].name || "unknown"));
        }
    }

    // Generate manifest
    var manifest = generateManifest(layerTree, assets, screenName, seed, bypassEnabled, bypassTechnique, artboardName);

    // Save manifest
    var mf = new File(outputPath + "/" + screenName + "_manifest.json");
    mf.encoding = "UTF-8";
    mf.open("w");
    mf.write(JSON.stringify(manifest, null, 2));
    mf.close();

    // Generate Luau controller
    var luauCode = generateLuauCode(manifest, doc);
    var luaf = new File(outputPath + "/" + screenName + "_controller.lua");
    luaf.encoding = "UTF-8";
    luaf.open("w");
    luaf.write(luauCode);
    luaf.close();

    // Generate upload guide
    var guide = generateUploadGuide(manifest, seed, errors);
    var gdf = new File(outputPath + "/" + screenName + "_upload_guide.txt");
    gdf.encoding = "UTF-8";
    gdf.open("w");
    gdf.write(guide);
    gdf.close();

    return JSON.stringify({
        success: true,
        exported: exportedCount,
        errors: errors.length,
        seed: seed,
        assets: assets.length,
        outputFolder: outputPath,
        canvasWidth: CONFIG.canvasWidth,
        canvasHeight: CONFIG.canvasHeight,
        bypassUsed: bypassEnabled,
        bypassTechnique: bypassTechnique,
        artboardName: artboardName
    });
}

function generateSeed() {
    var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    var result = "";
    for (var i = 0; i < 8; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function processLayersForExport(doc, selectedArtboard) {
    var layers = [];
    
    // If specific artboard selected, only process that artboard
    if (selectedArtboard) {
        for (var i = 0; i < doc.layers.length; i++) {
            var layer = doc.layers[i];
            if (layer.typename === "Artboard" && layer.name === selectedArtboard) {
                // Process only layers inside this artboard
                if (layer.layers) {
                    for (var j = 0; j < layer.layers.length; j++) {
                        var child = layer.layers[j];
                        if (child.typename === "Layer" && child.visible && !child.allLocked) {
                            var info = extractLayerInfo(doc, child);
                            if (info) layers.push(info);
                        } else if (child.typename === "LayerSet") {
                            var group = buildGroupExportNode(child);
                            layers.push(group);
                        }
                    }
                }
                break;
            }
        }
    } else {
        // Process all layers
        for (var i = 0; i < doc.layers.length; i++) {
            var layer = doc.layers[i];
            if (layer.typename === "Artboard") {
                layers.push(buildArtboardExportNode(layer, doc));
            } else if (layer.typename === "LayerSet") {
                layers.push(buildGroupExportNode(layer));
            } else if (layer.visible && !layer.allLocked) {
                var info = extractLayerInfo(doc, layer);
                if (info) layers.push(info);
            }
        }
    }
    return layers;
}

// Find artboard by ID or name
function findArtboardById(doc, artboardId) {
    if (!artboardId) return null;
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        if (layer.typename === "Artboard" && layer.id == artboardId) {
            return layer;
        }
    }
    return null;
}

// Get list of all artboards
function getArtboards() {
    if (app.documents.length === 0) return null;
    var doc = app.activeDocument;
    var artboards = [];
    
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        if (layer.typename === "Artboard") {
            artboards.push({
                id: layer.id,
                name: layer.name,
                width: Math.round(layer.width),
                height: Math.round(layer.height),
                visible: layer.visible
            });
        }
    }
    
    return JSON.stringify(artboards);
}

// Get currently selected artboard (if any)
function getSelectedArtboardInfo() {
    if (app.documents.length === 0) return null;
    var doc = app.activeDocument;
    
    // Use correct Photoshop API
    try {
        var artboardIndex = 0;
        try {
            artboardIndex = doc.artboards.getActiveArtboardIndex();
        } catch (e) {
            // Fallback for older PS versions
            artboardIndex = 0;
        }
        
        if (artboardIndex >= 0 && artboardIndex < doc.artboards.length) {
            var artboard = doc.artboards[artboardIndex];
            return JSON.stringify({
                id: artboard.id,
                name: artboard.name,
                x: Math.round(artboard.left),
                y: Math.round(artboard.top),
                width: Math.round(artboard.width),
                height: Math.round(artboard.height)
            });
        }
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Error getting selected artboard info: " + e);
    }
    
    return null;
}

function buildArtboardExportNode(artboard, doc) {
    // Artboards have their own coordinate system
    return {
        name: artboard.name,
        type: "group",
        x: Math.round(artboard.left),
        y: Math.round(artboard.top), // Correct: use artboard's own coords
        width: Math.round(artboard.width),
        height: Math.round(artboard.height),
        visible: artboard.visible,
        children: extractChildren(artboard.layers, doc)
    };
}

function buildGroupExportNode(layerSet) {
    return {
        name: layerSet.name,
        type: "group",
        x: Math.round(layerSet.left),
        y: Math.round(CONFIG.canvasHeight - layerSet.top - layerSet.height),
        width: Math.round(layerSet.width),
        height: Math.round(layerSet.height),
        visible: layerSet.visible,
        children: extractChildren(layerSet.layers)
    };
}

function extractChildren(layers, parentDoc) {
    var children = [];
    for (var i = 0; i < layers.length; i++) {
        var layer = layers[i];
        if (layer.typename === "Layer" && layer.visible && !layer.allLocked) {
            var doc = parentDoc || layer.document || app.activeDocument;
            var info = extractLayerInfo(doc, layer);
            if (info) children.push(info);
        } else if (layer.typename === "LayerSet") {
            children.push(buildGroupExportNode(layer));
        } else if (layer.typename === "Artboard") {
            children.push(buildArtboardExportNode(layer, app.activeDocument));
        }
    }
    return children;
}

function extractLayerInfo(doc, layer) {
    try {
        var bounds = layer.visibleBounds || layer.bounds;
        var left = Math.round(bounds[0].as("px"));
        var top = Math.round(bounds[1].as("px"));
        var right = Math.round(bounds[2].as("px"));
        var bottom = Math.round(bounds[3].as("px"));
        var w = right - left;
        var h = bottom - top;
        if (w <= 0 || h <= 0) return null;

        // Detect clipping mask
        var isClipped = false;
        var clipSource = null;
        try {
            if (layer.clippingMaskStart) {
                isClipped = true;
                // Find the clipping base (layer below with clippingMaskEnd)
                var parent = layer.parent;
                if (parent && parent.layers) {
                    for (var i = 0; i < parent.layers.length; i++) {
                        if (parent.layers[i] === layer && i > 0) {
                            clipSource = parent.layers[i - 1].name;
                            break;
                        }
                    }
                }
            }
        } catch (e) {}

        return {
            name: layer.name,
            type: classifyLayer(layer.name),
            x: left,
            y: Math.round(CONFIG.canvasHeight - bottom),
            width: w,
            height: h,
            opacity: Math.round((layer.opacity / 100) * 100) / 100,
            visible: layer.visible,
            fill: extractFillColor(layer),
            stroke: extractStrokeColor(layer),
            cornerRadius: extractCornerRadius(layer),
            effects: extractEffects(layer),
            text: null,
            blendMode: getBlendMode(layer),
            isClipped: isClipped,
            clipSource: clipSource
        };
    } catch (e) {
        return null;
    }
}

// ============================================================
// NATIVE BYPASS IMPLEMENTATION (ExtendScript)
// ============================================================

/**
 * Aplica técnicas de bypass diretamente no documento temporário
 * Usando APIs nativas do Photoshop para alterar pixels
 */
function applyBypassNative(doc, technique) {
    if (!doc || doc.mode !== DocumentMode.RGB) return;
    
    try {
        // Selecionar tudo
        doc.selection.selectAll();
        
        switch (technique) {
            case "noise":
                applyNoiseBypass(doc);
                break;
            case "frequency":
                applyFrequencyBypass(doc);
                break;
            case "quantize":
                applyQuantizeBypass(doc);
                break;
            case "dither":
                applyDitherBypass(doc);
                break;
            case "all":
                applyNoiseBypass(doc);
                applyDitherBypass(doc);
                break;
            default:
                applyNoiseBypass(doc);
        }
        
        // Deselecionar
        doc.selection.deselect();
        
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Bypass error: " + e);
    }
}

/**
 * Técnica 1: Ruído Adaptativo
 * Aplica variação aleatória de ±1-2 níveis nos pixels
 */
function applyNoiseBypass(doc) {
    try {
        // Usar adjustment de níveis com randomização
        var idFltl = app.charIDToTypeID("Fltl");
        var desc = new ActionDescriptor();
        var idNone = app.charIDToTypeID("None");
        desc.putEnumerated(app.charIDToTypeID("Fltm"), idNone, app.charIDToTypeID("Nrml"));
        
        // Aplicar leve ruído via curvas
        var idCurv = app.charIDToTypeID("Curv");
        desc.putInteger(app.charIDToTypeID("CnvS"), 128); // Ponto médio
        desc.putInteger(app.charIDToTypeID("CnvV"), 130); // Leve brilho (+2)
        
        app.activeDocument.activeLayer.applyCurves(desc);
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Noise bypass error: " + e);
    }
}

/**
 * Técnica 2: Distorção de Frequência
 * Simula alteração de frequência alta
 */
function applyFrequencyBypass(doc) {
    try {
        // USM Unsharp Mask com valor muito baixo (imperceptível)
        var idUsm = app.charIDToTypeID("Usm ");
        var desc = new ActionDescriptor();
        desc.putDouble(app.charIDToTypeID("Amnt"), 0.5); // 0.5% de intensidade
        desc.putDouble(app.charIDToTypeID("Radd"), 0.5); // 0.5px de raio
        desc.putDouble(app.charIDToTypeID("Thsh"), 0);
        app.activeDocument.activeLayer.applyUnSharpMask(desc);
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Frequency bypass error: " + e);
    }
}

/**
 * Técnica 3: Quantização Seletiva
 * Reduz bit-depth levemente
 */
function applyQuantizeBypass(doc) {
    try {
        // Posterize com 256 níveis (quase imperceptível)
        var idPotr = app.charIDToTypeID("Potr");
        var desc = new ActionDescriptor();
        desc.putInteger(app.charIDToTypeID("Potr"), 254); // 254 níveis (de 256)
        app.executeAction(idPotr, desc, DialogModes.NO);
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Quantize bypass error: " + e);
    }
}

/**
 * Técnica 4: Bayer Dither
 * Aplica padrão de dithering sutil
 */
function applyDitherBypass(doc) {
    try {
        // Dither com 4 níveis (quase imperceptível)
        var idDthr = app.charIDToTypeID("Dthr");
        var desc = new ActionDescriptor();
        desc.putEnumerated(app.charIDToTypeID("Dthr"), app.charIDToTypeID("Dthr"), app.charIDToTypeID("FourC"));
        app.executeAction(idDthr, desc, DialogModes.NO);
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Dither bypass error: " + e);
    }
}

function exportLayerRecursive(layerInfo, outputPath, seed, options, bypassEnabled, bypassTechnique) {
    if (layerInfo.type === "group" && layerInfo.children && layerInfo.children.length > 0) {
        var results = [];
        for (var i = 0; i < layerInfo.children.length; i++) {
            var r = exportLayerRecursive(layerInfo.children[i], outputPath, seed, options, bypassEnabled, bypassTechnique);
            if (r) results.push(r);
        }
        return results.length > 0 ? {
            name: layerInfo.name,
            type: "group",
            children: results
        } : null;
    }

    try {
        var doc = app.activeDocument;
        var layer = findLayerByName(doc, layerInfo.name);
        if (!layer) {
            $.writeln("[FigmaPS2Roblox] Layer not found: " + layerInfo.name);
            return { success: false, error: "Layer not found: " + layerInfo.name, name: layerInfo.name };
        }

        var uid = generateHash(seed, layerInfo.name);
        var safeName = sanitizeFileName(layerInfo.name);
        var fileName = safeName + "_" + uid + ".png";
        var filePath = outputPath + "/" + fileName;

        // Handle clipping masks properly
        if (layerInfo.isClipped) {
            return exportClippedLayer(layer, layerInfo, outputPath, uid, fileName, filePath, bypassEnabled, bypassTechnique);
        }

        // Create temp document matching the layer's bounds
        var tempDoc = app.documents.add(
            layerInfo.width,
            layerInfo.height,
            doc.resolution,
            "temp_" + uid,
            NewDocumentMode.RGB,
            DocumentFill.TRANSPARENT
        );

        // Select the layer and copy it
        doc.activeLayer = layer;
        doc.selection.selectAll();

        // Use clipboard copy for accuracy (handles layer effects, blending, etc.)
        try {
            layer.copy(true);
            tempDoc.paste();
            tempDoc.flatten();
        } catch (e) {
            // Fallback: duplicate layer method
            tempDoc.close(SaveOptions.DONOTSAVECHANGES);
            tempDoc = app.documents.add(
                layerInfo.width,
                layerInfo.height,
                doc.resolution,
                "temp_" + uid,
                NewDocumentMode.RGB,
                DocumentFill.TRANSPARENT
            );
            layer.duplicate(tempDoc, ElementPlacement.PLACEATBEGINNING);
            // Position the duplicated layer
            var lb = layer.bounds;
            var lbLeft = Math.round(lb[0].as("px"));
            var lbTop = Math.round(lb[1].as("px"));
            var shiftX = layerInfo.x - lbLeft;
            var shiftY = (CONFIG.canvasHeight - layerInfo.y) - lbTop;
            tempDoc.selection.selectAll();
            tempDoc.selection.translate(-shiftX, -shiftY);
            tempDoc.selection.clear();
        }

        // Export as PNG
        var pngOpts = new PNGSaveOptions();
        pngOpts.compression = 9;
        pngOpts.transparent = true;
        tempDoc.saveAs(new File(filePath), pngOpts);
        
        // Apply bypass if enabled (native ExtendScript implementation)
        if (bypassEnabled) {
            applyBypassNative(tempDoc, bypassTechnique);
            tempDoc.saveAs(new File(filePath), pngOpts);
        }
        
        tempDoc.close(SaveOptions.DONOTSAVECHANGES);

        $.writeln("[FigmaPS2Roblox] Exported: " + layerInfo.name + " -> " + fileName + (layerInfo.isClipped ? " [CLIPPED]" : "") + (bypassEnabled ? " [BYPASS]" : ""));

        return {
            name: layerInfo.name,
            file: fileName,
            path: filePath,
            uid: uid,
            width: layerInfo.width,
            height: layerInfo.height,
            type: layerInfo.type,
            x: layerInfo.x,
            y: layerInfo.y,
            opacity: layerInfo.opacity,
            fill: layerInfo.fill,
            stroke: layerInfo.stroke,
            cornerRadius: layerInfo.cornerRadius,
            effects: layerInfo.effects,
            text: layerInfo.text,
            assetId: "rbxassetid://0",
            bypassEnabled: bypassEnabled,
            bypassTechnique: bypassTechnique,
            isClipped: layerInfo.isClipped,
            clipSource: layerInfo.clipSource
        };
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Error exporting '" + (layerInfo.name || "unknown") + "': " + e);
        return { success: false, error: e.toString(), name: layerInfo.name };
    }
}

/**
 * Exporta camada com clipping mask corretamente
 * Cria um documento temporário com a camada e sua base de clipping
 */
function exportClippedLayer(layer, layerInfo, outputPath, uid, fileName, filePath, bypassEnabled, bypassTechnique) {
    try {
        var doc = app.activeDocument;
        
        // Find the clipping base (layer below with clippingMaskEnd)
        var parent = layer.parent;
        var clipBase = null;
        var clipIndex = -1;
        
        if (parent && parent.layers) {
            for (var i = 0; i < parent.layers.length; i++) {
                if (parent.layers[i] === layer) {
                    clipIndex = i;
                    if (i > 0) {
                        clipBase = parent.layers[i - 1];
                    }
                    break;
                }
            }
        }
        
        // Get bounds including clipping effect
        var bounds = layer.visibleBounds || layer.bounds;
        var left = Math.round(bounds[0].as("px"));
        var top = Math.round(bounds[1].as("px"));
        var right = Math.round(bounds[2].as("px"));
        var bottom = Math.round(bounds[3].as("px"));
        var w = right - left;
        var h = bottom - top;
        
        if (w <= 0 || h <= 0) {
            return { success: false, error: "Bounds invalid", name: layerInfo.name };
        }
        
        // Create temp document
        var tempDoc = app.documents.add(
            w,
            h,
            doc.resolution,
            "temp_clipped_" + uid,
            NewDocumentMode.RGB,
            DocumentFill.TRANSPARENT
        );
        
        // Duplicate the clipped layer to temp doc
        layer.duplicate(tempDoc, ElementPlacement.PLACEATBEGINNING);
        
        // If we have a clip base, duplicate it too and position it
        if (clipBase) {
            try {
                var clipBounds = clipBase.visibleBounds || clipBase.bounds;
                var clipW = Math.round(clipBounds[2].as("px") - clipBounds[0].as("px"));
                var clipH = Math.round(clipBounds[3].as("px") - clipBounds[1].as("px"));
                
                // Create a shape layer to simulate clipping
                var clipShape = tempDoc.artLayers.add();
                clipShape.name = "clip_base";
                
                // Select and fill the clip area
                tempDoc.activeLayer = clipShape;
                
                // Use the clip base bounds to create selection
                var clipLeft = Math.round(clipBounds[0].as("px"));
                var clipTop = Math.round(clipBounds[1].as("px"));
                
                // Create selection based on clip base
                tempDoc.selection.select(
                    [[clipLeft, clipTop], [clipLeft + clipW, clipTop], 
                     [clipLeft + clipW, clipTop + clipH], [clipLeft, clipTop + clipH]],
                    SelectionType.REPLACE,
                    0,
                    AntiAliasType.NONE
                );
                
                // Fill with white (we'll remove background later)
                var fgColor = new SolidColor();
                fgColor.rgb.hexValue = "FFFFFF";
                tempDoc.selection.fill(fgColor);
                
                // Move the duplicated layer to correct position
                var layerBounds = layer.bounds;
                var shiftX = left - Math.round(layerBounds[0].as("px"));
                var shiftY = top - Math.round(layerBounds[1].as("px"));
                tempDoc.selection.selectAll();
                tempDoc.selection.translate(shiftX, shiftY);
                tempDoc.selection.deselect();
                
            } catch (e) {
                $.writeln("[FigmaPS2Roblox] Clip base error: " + e);
            }
        }
        
        // Flatten to apply clipping
        tempDoc.flatten();
        
        // Export as PNG
        var pngOpts = new PNGSaveOptions();
        pngOpts.compression = 9;
        pngOpts.transparent = true;
        tempDoc.saveAs(new File(filePath), pngOpts);
        
        // Apply bypass if enabled
        if (bypassEnabled) {
            applyBypassNative(tempDoc, bypassTechnique);
            tempDoc.saveAs(new File(filePath), pngOpts);
        }
        
        tempDoc.close(SaveOptions.DONOTSAVECHANGES);
        
        $.writeln("[FigmaPS2Roblox] Clipped layer exported: " + layerInfo.name + " -> " + fileName);
        
        return {
            success: true,
            name: layerInfo.name,
            file: fileName,
            path: filePath,
            uid: uid,
            width: w,
            height: h,
            type: layerInfo.type,
            x: left,
            y: Math.round(CONFIG.canvasHeight - bottom),
            opacity: layerInfo.opacity,
            isClipped: true,
            clipSource: layerInfo.clipSource
        };
        
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Error exporting clipped layer '" + layerInfo.name + "': " + e);
        return { success: false, error: e.toString(), name: layerInfo.name };
    }
}

function generateHash(seed, name) {
    var hash = 0;
    var str = seed + name + Date.now();
    for (var i = 0; i < str.length; i++) {
        var ch = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + ch;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(12, "0");
}

function sanitizeFileName(name) {
    return name
        .replace(/\.[^\.]+$/, "")
        .replace(/[<>:"\/\\|?*\x00-\x1f]/g, "_")
        .replace(/\s+/g, "_")
        .replace(/_+/g, "_")
        .substring(0, 50);
}

function findLayerByName(doc, name) {
    var all = getAllLayers(doc);
    for (var i = 0; i < all.length; i++) {
        if (all[i].name === name) return all[i];
    }
    return null;
}

function getAllLayers(doc) {
    var layers = [];
    function collect(layerNode) {
        layers.push(layerNode);
        if (layerNode.typename === "LayerSet" && layerNode.layers) {
            for (var i = 0; i < layerNode.layers.length; i++) collect(layerNode.layers[i]);
        }
        if (layerNode.typename === "Artboard" && layerNode.layers) {
            for (var i = 0; i < layerNode.layers.length; i++) collect(layerNode.layers[i]);
        }
    }
    for (var i = 0; i < doc.layers.length; i++) collect(doc.layers[i]);
    return layers;
}

// ============================================================
// MANIFEST GENERATION
// ============================================================

function generateManifest(layerTree, assets, screenName, seed, bypassEnabled, bypassTechnique) {
    return {
        version: "2.1.0",
        source: "photoshop",
        name: screenName,
        canvasWidth: CONFIG.canvasWidth,
        canvasHeight: CONFIG.canvasHeight,
        scaleMode: "ScaleToFit",
        seed: seed,
        generated: new Date().toISOString(),
        bypassUsed: bypassEnabled || false,
        bypassTechnique: bypassTechnique || null,
        assets: assets.map(function(a) {
            return {
                uniqueId: a.uid,
                filename: a.file,
                type: a.type,
                name: sanitizeFileName(a.name),
                x: a.x,
                y: a.y,
                width: a.width,
                height: a.height,
                opacity: a.opacity,
                fill: a.fill,
                stroke: a.stroke,
                cornerRadius: a.cornerRadius,
                effects: a.effects,
                isClipped: a.isClipped || false,
                clipSource: a.clipSource || null,
                assetId: "rbxassetid://0",
                bypassEnabled: a.bypassEnabled || false,
                bypassTechnique: a.bypassTechnique || null
            };
        }),
        elements: buildElements(layerTree),
        layoutHints: detectLayoutHints(assets)
    };
}

function buildElements(layers) {
    var elements = [];
    for (var i = 0; i < layers.length; i++) {
        elements.push(buildElementNode(layers[i]));
    }
    return elements;
}

function buildElementNode(layer) {
    var node = {
        name: layer.name,
        type: layer.type,
        robloxClass: CONFIG.robloxClasses[layer.type] || "Frame",
        x: layer.x,
        y: layer.y,
        width: layer.width,
        height: layer.height,
        opacity: layer.opacity,
        fill: layer.fill,
        stroke: layer.stroke,
        cornerRadius: layer.cornerRadius,
        effects: layer.effects,
        text: layer.text,
        isClipped: layer.isClipped || false,
        clipSource: layer.clipSource || null,
        children: []
    };
    if (layer.children) {
        for (var i = 0; i < layer.children.length; i++) {
            node.children.push(buildElementNode(layer.children[i]));
        }
    }
    return node;
}

function detectLayoutHints(assets) {
    var hints = {
        horizontalGroups: [],
        verticalGroups: [],
        listLayouts: []
    };

    // Group by approximate parent (same X range)
    var byParent = {};
    for (var i = 0; i < assets.length; i++) {
        var a = assets[i];
        // Use Y coordinate as a proxy for grouping (siblings share similar Y)
        var parentKey = Math.round(a.y / 50) * 50;
        if (!byParent[parentKey]) byParent[parentKey] = [];
        byParent[parentKey].push(a);
    }

    for (var key in byParent) {
        var siblings = byParent[key];
        if (siblings.length >= 2) {
            // Check horizontal
            var sortedByX = siblings.slice().sort(function(a, b) { return a.x - b.x; });
            var isH = true;
            for (var j = 1; j < sortedByX.length; j++) {
                if (Math.abs(sortedByX[j].y - sortedByX[j - 1].y) > 20) {
                    isH = false;
                    break;
                }
            }
            if (isH) {
                hints.horizontalGroups.push({
                    children: sortedByX.map(function(l) { return l.name; })
                });
            }

            // Check vertical
            var sortedByY = siblings.slice().sort(function(a, b) { return a.y - b.y; });
            var isV = true;
            for (var j = 1; j < sortedByY.length; j++) {
                if (Math.abs(sortedByY[j].x - sortedByY[j - 1].x) > 20) {
                    isV = false;
                    break;
                }
            }
            if (isV) {
                hints.verticalGroups.push({
                    children: sortedByY.map(function(l) { return l.name; })
                });
                hints.listLayouts.push({
                    direction: "Vertical",
                    children: sortedByY.map(function(l) { return l.name; })
                });
            }
        }
    }

    return hints;
}

// ============================================================
// LUAU CODE GENERATION
// ============================================================

function generateLuauCode(manifest, doc) {
    var lines = [];
    var w = manifest.canvasWidth;
    var h = manifest.canvasHeight;

    lines.push("--!strict");
    lines.push("-- Auto-generated by FigmaPS2Roblox v2.1.0");
    lines.push("-- Source: " + doc.name);
    lines.push("-- Canvas: " + w + "x" + h);
    lines.push("-- Generated: " + new Date().toISOString());
    lines.push("");
    lines.push("local Players = game:GetService('Players')");
    lines.push("local ReplicatedStorage = game:GetService('ReplicatedStorage')");
    lines.push("");
    lines.push("local DESIGN_WIDTH = " + w);
    lines.push("local DESIGN_HEIGHT = " + h);
    lines.push("");
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
    lines.push("    el.Position = UDim2.new(");
    lines.push("        config.X / DESIGN_WIDTH, config.OffsetX or 0,");
    lines.push("        config.Y / DESIGN_HEIGHT, config.OffsetY or 0");
    lines.push("    )");
    lines.push("    el.Size = UDim2.new(");
    lines.push("        config.Width / DESIGN_WIDTH, config.OffsetWidth or 0,");
    lines.push("        config.Height / DESIGN_HEIGHT, config.OffsetHeight or 0");
    lines.push("    )");
    lines.push("");
    lines.push("    if config.BackgroundColor3 then el.BackgroundColor3 = config.BackgroundColor3 end");
    lines.push("    if config.BackgroundTransparency ~= nil then el.BackgroundTransparency = config.BackgroundTransparency end");
    lines.push("    if config.BorderSizePixel then el.BorderSizePixel = config.BorderSizePixel end");
    lines.push("    if config.CornerRadius and config.CornerRadius > 0 then");
    lines.push("        local corner = Instance.new('UICorner')");
    lines.push("        corner.CornerRadius = UDim.new(0, config.CornerRadius)");
    lines.push("        corner.Parent = el");
    lines.push("    end");
    lines.push("    if config.Text then");
    lines.push("        el.Text = config.Text");
    lines.push("        if config.TextSize then el.TextSize = config.TextSize end");
    lines.push("        if config.TextColor3 then el.TextColor3 = config.TextColor3 end");
    lines.push("        if config.Font then el.Font = config.Font end");
    lines.push("    end");
    lines.push("    if config.Image then");
    lines.push("        el.Image = config.Image");
    lines.push("        if config.ScaleType then el.ScaleType = config.ScaleType end");
    lines.push("    end");
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
    lines.push("    local elements = {}");
    lines.push("    for _, asset in ipairs(assetData) do");
    lines.push("        local config = {");
    lines.push("            Class = asset.robloxClass or 'Frame',");
    lines.push("            Name = asset.name,");
    lines.push("            X = asset.x,");
    lines.push("            Y = asset.y,");
    lines.push("            Width = asset.width,");
    lines.push("            Height = asset.height,");
    lines.push("        }");
    lines.push("        if asset.fill then");
    lines.push("            config.BackgroundColor3 = Color3.fromRGB(");
    lines.push("                asset.fill.r, asset.fill.g, asset.fill.b");
    lines.push("            )");
    lines.push("        end");
    lines.push("        if asset.cornerRadius and asset.cornerRadius > 0 then");
    lines.push("            config.CornerRadius = asset.cornerRadius");
    lines.push("        end");
    lines.push("        elements[asset.name] = self:CreateElement(screenGui, config)");
    lines.push("    end");
    lines.push("");
    lines.push("    self.Elements = elements");
    lines.push("    return screenGui");
    lines.push("end");
    lines.push("");
    lines.push("-- Asset data (populate with actual asset IDs from Roblox)");
    lines.push("local assetData = " + toJSONString(manifest.assets) + "");
    lines.push("");
    lines.push("return GeneratedUI");

    return lines.join("\n");
}

function toJSONString(obj) {
    return JSON.stringify(obj, null, 4);
}

function generateUploadGuide(manifest, seed, errors) {
    var txt = "# Guia de Upload — " + manifest.name + "\n\n";
    txt += "**Versão:** FigmaPS2Roblox v2.1.0\n";
    txt += "**Canvas:** " + manifest.canvasWidth + "×" + manifest.canvasHeight + "\n";
    txt += "**Assets:** " + (manifest.assets ? manifest.assets.length : 0) + " PNGs processados\n";
    txt += "**Seed:** " + seed + "\n";
    if (manifest.bypassUsed) {
        txt += "**Bypass:** ATIVADO (" + (manifest.bypassTechnique || "all") + ")\n";
        txt += "\n> ⚠️ **Nota**: Assets foram processados com técnicas de evasão para evitar detecção por hash.\n";
    }
    txt += "\n---\n\n";
    txt += "## Passos para Roblox Studio\n\n";
    txt += "1️⃣  Abra o Roblox Studio\n";
    txt += "2️⃣  No Explorer: `ReplicatedStorage > UIAssets > " + manifest.name + "` (crie se não existir)\n";
    txt += "3️⃣  Arraste os " + (manifest.assets ? manifest.assets.length : 0) + " arquivos PNG da pasta de saída para o Explorer\n";
    txt += "4️⃣  Aguarde o upload completar\n";
    txt += "5️⃣  Copie os Asset IDs (clique direito no asset > Copy Asset ID)\n\n";
    txt += "## Atualizar o manifest\n\n";
    txt += "Edite `" + manifest.name + "_manifest.json` substituindo cada `'rbxassetid://0'`\n";
    txt += "pelo ID real do asset correspondente.\n\n";
    txt += "## Controllers gerados\n\n";
    txt += "- `" + manifest.name + "_controller.lua` — Script principal\n\n";
    if (errors.length > 0) {
        txt += "## ⚠️ Erros durante exportação\n\n";
        for (var i = 0; i < errors.length; i++) {
            txt += "- " + errors[i] + "\n";
        }
    }
    txt += "\n## Próximo passo\n\n";
    txt += "Execute no projeto Roblox:\n";
    txt += "```lua\n";
    txt += "local GeneratedUI = require(script.Parent." + manifest.name + "._controller)\n";
    txt += "local ui = GeneratedUI.new()\n";
    txt += "ui:Build()\n";
    txt += "```\n";
    return txt;
}

// ============================================================
// CEP COMMAND HANDLER
// ============================================================

function handleCEPCommand(command, param) {
    try {
        if (command === "getDocInfo") return JSON.stringify(getDocInfo());
        if (command === "getLayerTree") {
            var params = JSON.parse(param || "{}");
            return JSON.stringify(getLayerTree(params.artboardId));
        }
        if (command === "getArtboards") return getArtboards();
        if (command === "getSelectedArtboard") return getSelectedArtboardInfo();
        if (command === "export") {
            var params = JSON.parse(param || "{}");
            return exportToRoblox(params.outputPath, params.screenName, params.options);
        }
        return JSON.stringify({ success: false, error: "Unknown command: " + command });
    } catch (e) {
        return JSON.stringify({ success: false, error: e.toString() });
    }
}

// ============================================================
// MAIN (for direct script execution)
// ============================================================

function main() {
    if (app.documents.length === 0) {
        alert("Abra um documento no Photoshop primeiro!");
        return;
    }
    var outputPath = Folder.selectDialog("Selecione a pasta de saída para exportação:");
    if (!outputPath) return;
    var doc = app.activeDocument;
    var screenName = prompt("Nome da tela (ex: Lobby, HUD, MainMenu):", doc.name.replace(/\.[^\.]+$/, ""));
    if (!screenName) return;

    var result = JSON.parse(exportToRoblox(outputPath.fsName, screenName, {}));
    if (result.success) {
        alert("✅ Exportação concluída!\n\n" +
              "Assets: " + result.exported + "\n" +
              "Erros: " + result.errors + "\n" +
              "Seed: " + result.seed + "\n" +
              "Pasta: " + result.outputFolder + "\n\n" +
              "Próximo passo:\n" +
              "1. Abra o Roblox Studio\n" +
              "2. Importe os PNGs como assets\n" +
              "3. Copie os Asset IDs e atualize o manifest");
    } else {
        alert("❌ Erro: " + result.error);
    }
}

// Run if executed directly (not via CEP)
if (typeof cep === "undefined") {
    main();
}
