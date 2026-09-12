// RobloxUIExport.jsx
// Script de comunicação com o painel CEP
// Instalado em: C:\Program Files\Adobe\Adobe Photoshop 2024\Presets\Scripts\

#target photoshop

function updateDocInfo() {
    if (app.documents.length === 0) return "";
    var doc = app.activeDocument;
    return app.documents.length + "|" + doc.layers.length + "|" + 
           Math.round(doc.width.value) + "x" + Math.round(doc.height.value);
}

function generateSeed() {
    var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    var result = "";
    for (var i = 0; i < 8; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function cleanName(name) {
    return name.replace(/\.[^\.]+$/, "")
               .replace(/[_\-\s]+/g, "_")
               .replace(/[0-9]/g, "")
               .replace(/[^a-zA-ZÀ-ÿ]/g, "")
               .replace(/_+/g, "_");
}

function classifyName(name) {
    var n = name.toLowerCase();
    if (n.indexOf("bg") >= 0 || n.indexOf("back") >= 0 || n.indexOf("base") >= 0) return "background";
    if (n.indexOf("btn") >= 0 || n.indexOf("button") >= 0 || n.indexOf("play") >= 0 || n.indexOf("start") >= 0) return "button";
    if (n.indexOf("title") >= 0 || n.indexOf("label") >= 0 || n.indexOf("text") >= 0 || n.indexOf("score") >= 0) return "label";
    if (n.indexOf("icon") >= 0 || n.indexOf("img") >= 0 || n.indexOf("logo") >= 0) return "icon";
    if (n.indexOf("panel") >= 0 || n.indexOf("frame") >= 0 || n.indexOf("box") >= 0) return "panel";
    if (n.indexOf("bar") >= 0 || n.indexOf("health") >= 0 || n.indexOf("hp") >= 0) return "bar";
    return "image";
}

function sha256Hash(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
        var ch = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + ch;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(8, "0");
}

function exportToRoblox(outputPath, screenName) {
    if (app.documents.length === 0) return "ERRO: Nenhum documento aberto";

    var doc = app.activeDocument;
    var seed = generateSeed();
    var manifest = {
        name: screenName,
        canvasWidth: Math.round(doc.width.value),
        canvasHeight: Math.round(doc.height.value),
        scaleMode: "ScaleToFit",
        assets: []
    };
    var pngIndex = 0;

    function exportLayer(layer) {
        if (!layer.visible) return;
        if (layer.typename === "LayerSet") {
            for (var i = layer.layers.length - 1; i >= 0; i--) {
                if (layer.layers[i].typename !== "LayerSet" && layer.layers[i].visible) {
                    exportLayer(layer.layers[i]);
                }
            }
            return;
        }

        var bounds = layer.visibleBounds;
        var w = Math.round(bounds[2] - bounds[0]);
        var h = Math.round(bounds[3] - bounds[1]);
        if (w <= 0 || h <= 0) return;

        var tempDoc = app.documents.add(w, h, 72, layer.name + "_temp", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
        layer.copy(true);
        tempDoc.paste();
        tempDoc.flatten();

        var safeName = cleanName(layer.name);
        var uid = sha256Hash(seed + layer.name + Date.now());
        var pngFile = new File(outputPath + "/" + safeName + "_" + uid + ".png");
        tempDoc.saveAs(pngFile, new PNGSaveOptions(), true, Extension.LOWERCASE);
        tempDoc.close(SaveOptions.DONOTSAVECHANGES);

        manifest.assets.push({
            uniqueId: uid,
            filename: safeName + "_" + uid + ".png",
            type: classifyName(layer.name),
            name: safeName,
            x: Math.round(bounds[0]),
            y: Math.round(doc.height.value - bounds[3]),
            width: w,
            height: h,
            assetId: "rbxassetid://0"
        });
        pngIndex++;
    }

    for (var i = doc.layers.length - 1; i >= 0; i--) {
        if (doc.layers[i].typename !== "BackgroundLayer") {
            exportLayer(doc.layers[i]);
        }
    }

    // Save manifest
    var mf = new File(outputPath + "/" + screenName + "_manifest.json");
    mf.encoding = "UTF-8";
    mf.open("w");
    mf.write(JSON.stringify(manifest, null, 2));
    mf.close();

    // Save guide
    var gf = new File(outputPath + "/" + screenName + "_upload_guide.txt");
    gf.encoding = "UTF-8";
    gf.open("w");
    gf.write("# Guia de Upload — " + screenName + "\n\n" +
        "📂 Assets: " + pngIndex + " PNGs\n\n" +
        "1️⃣ Abra o Roblox Studio\n" +
        "2️⃣ Importe os PNGs para ReplicatedStorage/UIAssets/" + screenName + "\n" +
        "3️⃣ Copie os Asset IDs (clique direito > Copy Asset ID)\n" +
        "4️⃣ Atualize o manifest substituindo rbxassetid://0\n\n" +
        "🔑 Seed: " + seed);
    gf.close();

    // Open folder
    Folder(outputPath).execute();

    return pngIndex + "|" + seed;
}
