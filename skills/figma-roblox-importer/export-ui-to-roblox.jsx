/**
 * Figma/Photoshop to Roblox UI Converter
 * =======================================
 * Plugin ExtendScript para Adobe Photoshop
 * 
 * Uso:
 *   File > Scripts > Browse... -> selecione este arquivo
 *   OU
 *   Plugins > FigmaPS2Roblox > Export to Roblox
 * 
 * O que faz:
 *   1. Analisa todas as camadas do documento
 *   2. Exporta cada camada como PNG individual
 *   3. Gera spec.json com especificacao completa
 *   4. Gera luau_code.txt pronto para Roblox
 *   5. Gera manifest.json para upload de assets
 */

#target photoshop

var CONFIG = {
    canvasWidth: 1920,
    canvasHeight: 1080,
    layerPrefixes: {
        frame: ["frame", "container", "panel", "bg", "background", "card", "box"],
        button: ["button", "btn", "click", "play", "start", "submit"],
        text: ["text", "label", "title", "caption", "desc", "body", "info"],
        image: ["image", "icon", "img", "sprite", "avatar", "logo"],
        input: ["input", "field", "textbox", "edit", "search"]
    },
    robloxClasses: {
        frame: "Frame",
        button: "TextButton",
        text: "TextLabel",
        image: "ImageLabel",
        input: "TextBox"
    }
};

// ============================================================
// MAIN ENTRY POINT
// ============================================================

function main() {
    if (app.documents.length === 0) {
        alert("Abra um documento no Photoshop primeiro!");
        return;
    }

    var doc = app.activeDocument;
    var outputPath = Folder.selectDialog("Selecione a pasta de saida para exportacao:");
    if (!outputPath) return;

    CONFIG.canvasWidth = Math.round(doc.width.as("px"));
    CONFIG.canvasHeight = Math.round(doc.height.as("px"));

    $.writeln("[FigmaPS2Roblox] Iniciando exportacao...");
    $.writeln("[FigmaPS2Roblox] Canvas: " + CONFIG.canvasWidth + "x" + CONFIG.canvasHeight);

    // Process layers
    var layerTree = processLayers(doc);
    var assets = [];

    for (var i = 0; i < layerTree.length; i++) {
        var asset = exportLayer(layerTree[i], outputPath);
        if (asset) assets.push(asset);
    }

    // Generate spec JSON
    var spec = generateSpec(layerTree, outputPath);
    saveJSON(outputPath + "/spec.json", spec);

    // Generate Luau code
    var luauCode = generateLuauCode(spec, doc);
    saveFile(outputPath + "/luau_code.lua", luauCode);

    // Generate manifest for asset upload
    var manifest = generateManifest(assets, doc.name);
    saveJSON(outputPath + "/manifest.json", manifest);

    $.writeln("[FigmaPS2Roblox] Exportado " + assets.length + " assets");
    $.writeln("[FigmaPS2Roblox] Saida: " + outputPath);

    alert("Exportacao concluida!\n\n" +
          "Assets: " + assets.length + "\n" +
          "Pasta: " + outputPath + "\n\n" +
          "Proximo passo:\n" +
          "1. Abra o Roblox Studio\n" +
          "2. Vá em Plugins > FigmaPS2Roblox > Importar JSON\n" +
          "3. Selecione spec.json na pasta acima",
          "FigmaPS2Roblox - Done");
}

// ============================================================
// LAYER PROCESSING
// ============================================================

function processLayers(doc) {
    var layers = [];
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        if (layer.typename === "Artboard") {
            layers.push({
                name: layer.name,
                type: "group",
                x: Math.round(layer.left),
                y: Math.round(CONFIG.canvasHeight - layer.top - layer.height),
                width: Math.round(layer.width),
                height: Math.round(layer.height),
                visible: layer.visible,
                children: processArtboardContents(layer, doc)
            });
        } else if (layer.typename === "LayerSet") {
            layers.push({
                name: layer.name,
                type: "group",
                x: Math.round(layer.left),
                y: Math.round(CONFIG.canvasHeight - layer.top - layer.height),
                width: Math.round(layer.width),
                height: Math.round(layer.height),
                visible: layer.visible,
                children: processLayerSetContents(layer)
            });
        } else if (layer.typename === "Layer" && layer.visible && !layer.allLocked) {
            layers.push(extractLayerInfo(doc, layer));
        }
    }
    return layers;
}

/**
 * Processa conteudo de um Artboard — colige todas as camadas filhas recursivamente.
 */
function processArtboardContents(artboard, doc) {
    var children = [];
    try {
        // Artboards têm layers acessíveis via artboard.layers no ExtendScript
        if (artboard.layers && artboard.layers.length > 0) {
            for (var i = 0; i < artboard.layers.length; i++) {
                var child = artboard.layers[i];
                if (child.typename === "Layer" && child.visible && !child.allLocked) {
                    var info = extractLayerInfo(doc, child);
                    if (info) children.push(info);
                } else if (child.typename === "LayerSet") {
                    var nested = processLayerSetContents(child);
                    for (var j = 0; j < nested.length; j++) {
                        children.push(nested[j]);
                    }
                }
            }
        }
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Aviso ao processar Artboard '" + artboard.name + "': " + e);
    }
    return children;
}

/**
 * Processa conteudo de um LayerSet (grupo) — colige todas as camadas filhas.
 */
function processLayerSetContents(layerSet) {
    var children = [];
    try {
        if (!layerSet.layers) return children;
        for (var i = 0; i < layerSet.layers.length; i++) {
            var child = layerSet.layers[i];
            if (child.typename === "Layer" && child.visible && !child.allLocked) {
                var info = extractLayerInfo(child.document || app.activeDocument, child);
                if (info) children.push(info);
            } else if (child.typename === "LayerSet") {
                var nested = processLayerSetContents(child);
                for (var j = 0; j < nested.length; j++) {
                    children.push(nested[j]);
                }
            }
        }
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Aviso ao processar grupo '" + layerSet.name + "': " + e);
    }
    return children;
}

function extractLayerInfo(doc, layer) {
    try {
        var left = Math.round(layer.left);
        var top = Math.round(layer.top);
        var right = Math.round(layer.right);
        var bottom = Math.round(layer.bottom);

        var width = right - left;
        var height = bottom - top;

        if (width <= 0 || height <= 0) return null;

        // Inverter Y: Photoshop Y=0 no topo, Roblox Y=0 em baixo
        var y = CONFIG.canvasHeight - bottom;

        var info = {
            name: layer.name,
            type: classifyLayer(layer.name),
            x: left,
            y: y,
            width: width,
            height: height,
            opacity: Math.round((layer.opacity / 100) * 100) / 100,
            visible: layer.visible,
            fill: extractFill(layer),
            stroke: extractStroke(layer),
            cornerRadius: extractCornerRadius(layer),
            text: null,
            effects: extractEffects(layer),
            children: []
        };

        // Extract text
        if (layer.textItem) {
            info.text = {
                content: layer.textItem.contents,
                size: Math.round(layer.textItem.size),
                bold: layer.textItem.bold,
                color: getTextColor(layer),
                align: layer.textItem.justification
            };
        }

        return info;
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Erro processando camada '" + layer.name + "': " + e);
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

/**
 * Extrai a cor de preenchimento da camada usando sampling de pixels.
 * O ExtendScript não expõe fills diretamente — usamos sampling do centro da camada.
 */
function extractFill(layer) {
    try {
        // Tenta usar a API de layer effects (CS6+)
        // Para shapes com fill sólido, sampleamos o pixel central
        var doc = app.activeDocument;
        var sel = doc.selection;
        
        // Salvar seleção atual
        var savedBounds = null;
        try {
            savedBounds = sel.bounds;
        } catch(e) {}

        // Selecionar a camada
        layer.selected = true;
        
        try {
            var bounds = layer.bounds;
            var cx = Math.round((bounds[0].as("px") + bounds[2].as("px")) / 2);
            var cy = Math.round((bounds[1].as("px") + bounds[3].as("px")) / 2);
            
            // Sample do pixel central
            var color = doc.pixelColor(cmToUnits(cx), cmToUnits(cy));
            if (color && color.kind == ColorKind.SOLID) {
                return {
                    r: Math.round(color.red * 255),
                    g: Math.round(color.green * 255),
                    b: Math.round(color.blue * 255),
                    a: 255,
                    hex: rgbToHex(color.red, color.green, color.blue)
                };
            }
        } catch(e) {
            // Fallback: tentar extrair do layer effects
        }

        // Fallback: usar o fill color do documento se existir
        // (funciona para camadas com fill sólido em versões modernas)
        try {
            if (layer.kind && layer.kind.toString() === "ShapeLayer") {
                var fills = layer.fillSettings;
                if (fills && fills.disable === false && fills.contents) {
                    var fillContent = fills.contents;
                    if (fillContent && fillContent.kind === "SolidFill") {
                        var sc = fillContent.solidColor;
                        return {
                            r: Math.round(sc.red * 255),
                            g: Math.round(sc.green * 255),
                            b: Math.round(sc.blue * 255),
                            a: Math.round((fillContent.opacity || 1) * 255),
                            hex: rgbToHex(sc.red, sc.green, sc.blue)
                        };
                    }
                }
            }
        } catch(e) {}

        // Reset selection
        if (savedBounds) {
            try { sel.changeSelect(savedBounds); } catch(e) {}
        }
        layer.selected = false;
        return null;
    } catch (e) {
        try { layer.selected = false; } catch(e2) {}
        return null;
    }
}

/**
 * Converte pixels para centímetros (usado no sampling de cor).
 */
function cmToUnits(val) {
    return val / app.preferences.rulerUnits;
}

/**
 * Extrai informações do stroke (borda) da camada.
 */
function extractStroke(layer) {
    try {
        // Tenta acessar via layer effects (CS6+)
        if (layer.kind && layer.kind.toString() === "ShapeLayer") {
            var strokes = layer.strokeSettings;
            if (strokes && strokes.disable === false && strokes.contents) {
                var strokeContent = strokes.contents;
                if (strokeContent) {
                    if (strokeContent.kind === "SolidFill") {
                        var sc = strokeContent.solidColor;
                        return {
                            r: Math.round(sc.red * 255),
                            g: Math.round(sc.green * 255),
                            b: Math.round(sc.blue * 255),
                            width: Math.round(strokeContent.weight || 1),
                            hex: rgbToHex(sc.red, sc.green, sc.blue)
                        };
                    }
                }
            }
        }
        
        // Fallback para layer style panel
        if (layer.layerEffects && layer.layerEffects.strokeLayer) {
            var ls = layer.layerEffects.strokeLayer;
            if (ls.visible) {
                var c = ls.color;
                return {
                    r: Math.round(c.red * 255),
                    g: Math.round(c.green * 255),
                    b: Math.round(c.blue * 255),
                    width: Math.round(ls.size || 1),
                    hex: rgbToHex(c.red, c.green, c.blue)
                };
            }
        }
    } catch (e) {}
    return null;
}

/**
 * Extrai o raio dos cantos arredondados.
 * Funciona para Smart Objects e Shape Layers com rounded corners.
 */
function extractCornerRadius(layer) {
    try {
        // Método 1: Verificar se é um ShapeLayer com corners arredondados
        if (layer.kind && layer.kind.toString() === "ShapeLayer") {
            // Tenta acessar path options para corner radius
            try {
                var pathInfo = layer.pathItems;
                if (pathInfo && pathInfo.length > 0) {
                    // Path items podem ter corner radius em shape layers
                    var fill = layer.fillSettings;
                    if (fill && fill.contents) {
                        var contents = fill.contents;
                        if (contents.cornerRadius) {
                            return Math.round(contents.cornerRadius);
                        }
                    }
                }
            } catch(e) {}
        }

        // Método 2: Verificar Smart Object com corner radius
        if (layer.typename === "Layer" && layer.smartObject) {
            // Smart objects podem ter transformações que indicam arredondamento
            // Não podemos detectar diretamente, mas marcamos como 0
        }

        // Método 3: Verificar se a camada tem layer effects com rounded corners
        if (layer.layerEffects) {
            try {
                var blendOpts = layer.layerEffects.blendingOptions;
                if (blendOpts && blendOpts.cornerRadius) {
                    return Math.round(blendOpts.cornerRadius);
                }
            } catch(e) {}
        }

        // Método 4: Amostragem — verificar se os cantos têm transparência
        // Isso é pesado, então só fazemos para layers pequenas
        if (layer.width < 200 && layer.height < 200) {
            try {
                var corners = checkRoundedCorners(layer);
                if (corners) return corners;
            } catch(e) {}
        }
    } catch (e) {}
    return 0;
}

/**
 * Verifica se os cantos de uma camada são arredondados por sampling.
 * Retorna o raio estimado ou null.
 */
function checkRoundedCorners(layer) {
    try {
        var bounds = layer.bounds;
        var w = Math.round((bounds[2] - bounds[0]).as("px"));
        var h = Math.round((bounds[3] - bounds[1]).as("px"));
        
        if (w < 4 || h < 4) return null;

        // Sampling dos 4 cantos (2px de cada lado)
        var corners = [
            { x: 1, y: 1 },           // top-left
            { x: w - 2, y: 1 },       // top-right
            { x: 1, y: h - 2 },      // bottom-left
            { x: w - 2, y: h - 2 }   // bottom-right
        ];

        var transparentCorners = 0;
        for (var i = 0; i < corners.length; i++) {
            var px = corners[i].x;
            var py = corners[i].y;
            var c = layer.getPixel(px, py);
            if (c && c.opacity < 0.5) {
                transparentCorners++;
            }
        }

        // Se 2+ cantos são transparentes, provavelmente tem corner radius
        if (transparentCorners >= 2) {
            return Math.min(Math.floor(w / 4), Math.floor(h / 4), 20);
        }
    } catch (e) {}
    return null;
}

/**
 * Extrai efeitos da camada (drop shadow, glow, etc).
 */
function extractEffects(layer) {
    var effects = [];
    try {
        // Drop shadow
        if (layer.layerEffects && layer.layerEffects.dropShadowLayer) {
            var ds = layer.layerEffects.dropShadowLayer;
            if (ds.visible) {
                var c = ds.color;
                effects.push({
                    type: "dropShadow",
                    color: {
                        r: Math.round(c.red * 255),
                        g: Math.round(c.green * 255),
                        b: Math.round(c.blue * 255),
                        a: Math.round(ds.opacity * 255)
                    },
                    distance: Math.round(ds.distance || 0),
                    angle: Math.round(ds.angle || 0),
                    size: Math.round(ds.blur || 0)
                });
            }
        }
        
        // Outer glow
        if (layer.layerEffects && layer.layerEffects.outerGlow) {
            var og = layer.layerEffects.outerGlow;
            if (og.visible) {
                var c = og.color;
                effects.push({
                    type: "outerGlow",
                    color: {
                        r: Math.round(c.red * 255),
                        g: Math.round(c.green * 255),
                        b: Math.round(c.blue * 255),
                        a: Math.round(og.opacity * 255)
                    },
                    size: Math.round(og.blur || 0)
                });
            }
        }
    } catch (e) {}
    return effects;
}

/**
 * Extrai a cor do texto de uma camada de texto.
 */
function getTextColor(layer) {
    try {
        if (layer.textItem) {
            var color = layer.textItem.color;
            if (color) {
                return {
                    r: Math.round(color.red * 255),
                    g: Math.round(color.green * 255),
                    b: Math.round(color.blue * 255),
                    hex: rgbToHex(color.red, color.green, color.blue)
                };
            }
        }
    } catch (e) {}
    return null;
}

// ============================================================
// ASSET EXPORT
// ============================================================

function exportLayer(layerInfo, outputPath) {
    if (layerInfo.type === "group" && layerInfo.children.length > 0) {
        var exports = [];
        for (var i = 0; i < layerInfo.children.length; i++) {
            var exported = exportLayer(layerInfo.children[i], outputPath);
            if (exported) {
                if (Array.isArray(exported)) {
                    for (var j = 0; j < exported.length; j++) exports.push(exported[j]);
                } else {
                    exports.push(exported);
                }
            }
        }
        return exports.length > 0 ? exports : null;
    }

    try {
        var doc = app.activeDocument;
        var layer = findLayerByName(doc, layerInfo.name);
        if (!layer) return null;

        var fileName = sanitizeFileName(layerInfo.name) + ".png";
        var filePath = outputPath + "/" + fileName;

        // Criar documento temporário
        var tempDoc = app.documents.add(
            layerInfo.width,
            layerInfo.height,
            doc.resolution,
            layerInfo.name + "_temp",
            NewDocumentMode.RGB,
            DocumentFill.TRANSPARENT
        );

        // Duplicar a camada
        layer.duplicate(tempDoc, ElementPlacement.PLACEATBEGINNING);

        // Posicionar a camada no canvas temporário
        var layerBounds = layer.bounds;
        var layerLeft = layerBounds[0].as("px");
        var layerTop = layerBounds[1].as("px");
        
        // Calcular offset para posicionar corretamente
        var offsetX = -(layerInfo.x - layerLeft);
        var offsetY = -((CONFIG.canvasHeight - layerInfo.y) - layerTop);
        
        tempDoc.selection.selectAll();
        tempDoc.selection.translate(offsetX, offsetY);
        tempDoc.selection.clear();

        // Exportar
        var pngOpts = new PNGSaveOptions();
        pngOpts.compression = 9;
        pngOpts.transparent = true;
        tempDoc.saveAs(new File(filePath), pngOpts);
        tempDoc.close(SaveOptions.DONOTSAVECHANGES);

        return {
            name: layerInfo.name,
            file: fileName,
            path: filePath,
            width: layerInfo.width,
            height: layerInfo.height,
            type: layerInfo.type,
            x: layerInfo.x,
            y: layerInfo.y
        };
    } catch (e) {
        $.writeln("[FigmaPS2Roblox] Erro exportando '" + layerInfo.name + "': " + e);
        return null;
    }
}

function findLayerByName(doc, name) {
    var allLayers = getAllLayers(doc);
    for (var i = 0; i < allLayers.length; i++) {
        if (allLayers[i].name === name) return allLayers[i];
    }
    return null;
}

function getAllLayers(doc) {
    var layers = [];
    function collect(layerNode) {
        layers.push(layerNode);
        if (layerNode.typename === "LayerSet" && layerNode.layers) {
            for (var i = 0; i < layerNode.layers.length; i++) {
                collect(layerNode.layers[i]);
            }
        }
        // Artboards também têm layers
        if (layerNode.typename === "Artboard" && layerNode.layers) {
            for (var i = 0; i < layerNode.layers.length; i++) {
                collect(layerNode.layers[i]);
            }
        }
    }
    for (var i = 0; i < doc.layers.length; i++) {
        collect(doc.layers[i]);
    }
    return layers;
}

// ============================================================
// SPEC GENERATION
// ============================================================

function generateSpec(layerTree, outputPath) {
    var spec = {
        version: "2.0.0",
        source: "photoshop",
        canvas: {
            width: CONFIG.canvasWidth,
            height: CONFIG.canvasHeight
        },
        elements: [],
        assets: [],
        hierarchy: [],
        styles: {},
        layoutHints: {
            horizontalGroups: [],
            verticalGroups: []
        }
    };

    // Collect elements
    for (var i = 0; i < layerTree.length; i++) {
        spec.elements.push(buildNode(layerTree[i]));
    }

    // Collect assets
    collectAssets(layerTree, spec.assets);

    // Detect layout hints
    spec.layoutHints = detectLayoutHints(spec.elements);

    // Collect styles
    spec.styles = collectStyles(spec.elements);

    return spec;
}

function buildNode(layer) {
    var node = {
        name: layer.name,
        type: layer.type,
        x: layer.x,
        y: layer.y,
        width: layer.width,
        height: layer.height,
        opacity: layer.opacity,
        visible: layer.visible,
        fill: layer.fill,
        stroke: layer.stroke,
        cornerRadius: layer.cornerRadius,
        text: layer.text,
        effects: layer.effects,
        children: []
    };

    if (layer.children) {
        for (var i = 0; i < layer.children.length; i++) {
            node.children.push(buildNode(layer.children[i]));
        }
    }

    return node;
}

function collectAssets(layers, assets) {
    for (var i = 0; i < layers.length; i++) {
        var layer = layers[i];
        if (layer.type === "image" || layer.type === "icon") {
            assets.push({
                name: layer.name,
                file: sanitizeFileName(layer.name) + ".png",
                width: layer.width,
                height: layer.height,
                type: layer.type
            });
        }
        if (layer.children) {
            collectAssets(layer.children, assets);
        }
    }
}

function collectStyles(elements) {
    var styles = {};
    for (var i = 0; i < elements.length; i++) {
        var elem = elements[i];
        if (elem.fill) {
            var key = elem.fill.hex;
            if (!styles[key]) {
                styles[key] = {
                    token: "Color." + key.replace("#", ""),
                    value: elem.fill,
                    usage: []
                };
            }
            styles[key].usage.push(elem.name);
        }
        if (elem.children) {
            var childStyles = collectStyles(elem.children);
            for (var k in childStyles) {
                if (!styles[k]) styles[k] = childStyles[k];
            }
        }
    }
    return styles;
}

function detectLayoutHints(elements) {
    var hints = {
        horizontalGroups: [],
        verticalGroups: []
    };

    // Group by parent name proximity
    var byY = {};
    for (var i = 0; i < elements.length; i++) {
        var elem = elements[i];
        var yKey = Math.round(elem.y / 10) * 10; // Agrupar por faixas de 10px
        if (!byY[yKey]) byY[yKey] = [];
        byY[yKey].push(elem);
    }

    for (var yKey in byY) {
        var siblings = byY[yKey];
        if (siblings.length >= 2) {
            // Check horizontal alignment (same Y within 10px)
            var sortedByX = siblings.slice().sort(function(a, b) { return a.x - b.x; });
            var isH = true;
            for (var j = 1; j < sortedByX.length; j++) {
                if (Math.abs(sortedByX[j].y - sortedByX[j-1].y) > 10) {
                    isH = false;
                    break;
                }
            }
            if (isH) {
                hints.horizontalGroups.push({
                    parent: "root",
                    children: sortedByX.map(function(l) { return l.name; })
                });
            }
        }
    }

    // Group by X for vertical stacks
    var byX = {};
    for (var i = 0; i < elements.length; i++) {
        var elem = elements[i];
        var xKey = Math.round(elem.x / 10) * 10;
        if (!byX[xKey]) byX[xKey] = [];
        byX[xKey].push(elem);
    }

    for (var xKey in byX) {
        var siblings = byX[xKey];
        if (siblings.length >= 2) {
            var sortedByY = siblings.slice().sort(function(a, b) { return a.y - b.y; });
            var isV = true;
            for (var j = 1; j < sortedByY.length; j++) {
                if (Math.abs(sortedByY[j].x - sortedByY[j-1].x) > 10) {
                    isV = false;
                    break;
                }
            }
            if (isV) {
                hints.verticalGroups.push({
                    parent: "root",
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

function generateLuauCode(spec, doc) {
    var lines = [];
    var w = spec.canvas.width;
    var h = spec.canvas.height;

    lines.push("--!strict");
    lines.push("-- Auto-generated by FigmaPS2Roblox (Photoshop Plugin)");
    lines.push("-- Source: " + doc.name);
    lines.push("-- Canvas: " + w + "x" + h);
    lines.push("-- Generated: " + new Date().toISOString());
    lines.push("");
    lines.push("local Players = game:GetService(\"Players\")");
    lines.push("local ReplicatedStorage = game:GetService(\"ReplicatedStorage\")");
    lines.push("");
    lines.push("local DESIGN_WIDTH = " + w + "");
    lines.push("local DESIGN_HEIGHT = " + h + "");
    lines.push("");
    lines.push("local GeneratedUI = {}");
    lines.push("GeneratedUI.__index = GeneratedUI");
    lines.push("");

    // Styles
    lines.push("-- ====================================================================");
    lines.push("-- Style Tokens");
    lines.push("-- ====================================================================");
    lines.push("local Styles = {");
    for (var token in spec.styles) {
        var style = spec.styles[token];
        var c = style.value;
        if (c) {
            lines.push("\t[" + toJSONStr(token) + "] = Color3.fromRGB(" + c.r + ", " + c.g + ", " + c.b + "),");
        }
    }
    lines.push("}");
    lines.push("");

    // Builder class
    lines.push("-- ====================================================================");
    lines.push("-- UI Builder Class");
    lines.push("-- ====================================================================");
    lines.push("function GeneratedUI.new()");
    lines.push("\tlocal self = setmetatable({}, GeneratedUI)");
    lines.push("\tself.Elements = {}");
    lines.push("\treturn self");
    lines.push("end");
    lines.push("");

    lines.push("function GeneratedUI:CreateElement(parent, config)");
    lines.push("\tlocal el = Instance.new(config.Class)");
    lines.push("\tel.Name = config.Name");
    lines.push("\tel.Position = UDim2.new(");
    lines.push("\t\tconfig.X / DESIGN_WIDTH, config.OffsetX or 0,");
    lines.push("\t\tconfig.Y / DESIGN_HEIGHT, config.OffsetY or 0");
    lines.push("\t)");
    lines.push("\tel.Size = UDim2.new(");
    lines.push("\t\tconfig.Width / DESIGN_WIDTH, config.OffsetWidth or 0,");
    lines.push("\t\tconfig.Height / DESIGN_HEIGHT, config.OffsetHeight or 0");
    lines.push("\t)");
    lines.push("");
    lines.push("\tif config.BackgroundColor3 then");
    lines.push("\t\tel.BackgroundColor3 = config.BackgroundColor3");
    lines.push("\tend");
    lines.push("\tif config.BorderSizePixel then");
    lines.push("\t\tel.BorderSizePixel = config.BorderSizePixel");
    lines.push("\tend");
    lines.push("\tif config.BackgroundTransparency ~= nil then");
    lines.push("\t\tel.BackgroundTransparency = config.BackgroundTransparency");
    lines.push("\tend");
    lines.push("\tif config.CornerRadius and config.CornerRadius > 0 then");
    lines.push("\t\tlocal corner = Instance.new(\"UICorner\")");
    lines.push("\t\tcorner.CornerRadius = UDim.new(0, config.CornerRadius)");
    lines.push("\t\tcorner.Parent = el");  // FIX: was 'sel', now 'el'
    lines.push("\tend");
    lines.push("");
    lines.push("\tif config.Text then");
    lines.push("\t\tel.Text = config.Text");
    lines.push("\t\tif config.TextSize then el.TextSize = config.TextSize end");
    lines.push("\t\tif config.TextColor3 then el.TextColor3 = config.TextColor3 end");
    lines.push("\t\tif config.Font then el.Font = config.Font end");
    lines.push("\tend");
    lines.push("");
    lines.push("\tif config.Image then");
    lines.push("\t\tel.Image = config.Image");
    lines.push("\t\tif config.ScaleType then el.ScaleType = config.ScaleType end");
    lines.push("\tend");
    lines.push("");
    lines.push("\tel.Parent = parent");
    lines.push("\treturn el");  // FIX: was 'sel', now 'el'
    lines.push("end");
    lines.push("");

    // Build function
    lines.push("-- ====================================================================");
    lines.push("-- Main Builder");
    lines.push("-- ====================================================================");
    lines.push("function GeneratedUI:Build(parent)");
    lines.push("\tlocal screenGui = Instance.new(\"ScreenGui\")");
    lines.push("\tscreenGui.Name = \"GeneratedUI\"");
    lines.push("\tscreenGui.ResetOnSpawn = false");
    lines.push("\tscreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling");
    lines.push("\tscreenGui.Parent = parent or Players.LocalPlayer:WaitForChild(\"PlayerGui\")");
    lines.push("");
    lines.push("\tlocal elements = {}");
    lines.push("");

    // Generate element creation
    for (var i = 0; i < spec.elements.length; i++) {
        var elem = spec.elements[i];
        lines.push("\t-- " + elem.name);
        lines.push("\telements['" + elem.name + "'] = self:CreateElement(screenGui, {");
        lines.push("\t\tClass = \"" + CONFIG.robloxClasses[elem.type] || "Frame" + "\",");
        lines.push("\t\tName = \"" + escapeLua(elem.name) + "\",");
        lines.push("\t\tX = " + elem.x + ",");
        lines.push("\t\tY = " + elem.y + ",");
        lines.push("\t\tWidth = " + elem.width + ",");
        lines.push("\t\tHeight = " + elem.height + ",");
        if (elem.fill) {
            lines.push("\t\tBackgroundColor3 = Color3.fromRGB(" + elem.fill.r + ", " + elem.fill.g + ", " + elem.fill.b + "),");
        }
        if (elem.cornerRadius > 0) {
            lines.push("\t\tCornerRadius = " + elem.cornerRadius + ",");
        }
        if (elem.text) {
            lines.push("\t\tText = \"" + escapeLua(elem.text.content) + "\",");
            lines.push("\t\tTextSize = " + elem.text.size + ",");
            if (elem.text.color) {
                lines.push("\t\tTextColor3 = Color3.fromRGB(" + elem.text.color.r + ", " + elem.text.color.g + ", " + elem.text.color.b + "),");
            }
            lines.push("\t\tFont = Enum.Font." + (elem.text.bold ? "GothamBold" : "Gotham") + ",");
        }
        lines.push("\t})");
        lines.push("");
    }

    lines.push("\tself.Elements = elements");
    lines.push("\treturn screenGui");
    lines.push("end");
    lines.push("");
    lines.push("return GeneratedUI");

    return lines.join("\n");
}

// ============================================================
// MANIFEST GENERATION
// ============================================================

function generateManifest(assets, docName) {
    var manifest = {
        version: "2.0.0",
        source: docName,
        generated: new Date().toISOString(),
        assets: []
    };

    for (var i = 0; i < assets.length; i++) {
        manifest.assets.push({
            name: assets[i].name,
            file: assets[i].file,
            width: assets[i].width,
            height: assets[i].height,
            type: assets[i].type,
            assetId: "rbxassetid://0"
        });
    }

    return manifest;
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function sanitizeFileName(name) {
    return name
        .replace(/[<>:"\/\\|?*\x00-\x1f]/g, "_")
        .replace(/\s+/g, "_")
        .replace(/_+/g, "_")
        .substring(0, 50);
}

function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(function(x) {
        var hex = Math.round(x * 255).toString(16);
        return hex.length === 1 ? "0" + hex : hex;
    }).join("").toUpperCase();
}

function toJSONStr(s) {
    return "\"" + s.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + "\"";
}

function escapeLua(s) {
    return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n");
}

function saveJSON(path, data) {
    var file = new File(path);
    file.open("w");
    file.encoding = "UTF-8";
    file.write(JSON.stringify(data, null, 2));
    file.close();
    $.writeln("[FigmaPS2Roblox] Saved: " + path);
}

function saveFile(path, content) {
    var file = new File(path);
    file.open("w");
    file.encoding = "UTF-8";
    file.write(content);
    file.close();
    $.writeln("[FigmaPS2Roblox] Saved: " + path);
}

// ============================================================
// AUTO-REGISTRATION: Adiciona entrada no menu File > Scripts
// ============================================================

function registerInMenu() {
    try {
        var id = "figmaRobloxExport";
        var menuItem = app.menus.itemByID(String(id));
        if (menuItem) {
            menuItem.remove();
        }
        var scriptsMenu = app.menus.itemByID("Scripts");
        if (scriptsMenu) {
            var menuBar = app.menus.itemByID("MenuBar");
            var scriptsItem = menuBar.submenus.itemByID("File");
            if (scriptsItem) {
                scriptsItem.submenus.itemByID("Scripts").insertionPoint = insertionPoint.AT_END;
            }
        }
    } catch (e) {
        // Menu registration is optional
    }
}

// ============================================================
// RUN
// ============================================================

registerInMenu();
main();
