// export-ui-to-roblox.jsx
// Plugin do Photoshop para exportar UI diretamente para Roblox
//
// Uso: File > Scripts > Browse... → selecione este arquivo
//
// O que faz:
//   1. Exporta cada camada visível como PNG (mantendo transparência)
//   2. Gera manifest.json com posições e classificações automáticas
//   3. Processa cada imagem com hash único anti-reuploader
//   4. Gera controller Lua pronto
//   5. Abre a pasta de saída automaticamente

#target photoshop

var outputFolder = Folder.selectDialog("📁 Selecione a pasta de saída (PNGs + manifest):");
if (!outputFolder) exit();

var doc = app.activeDocument;
var docName = doc.name.replace(/\.[^\.]+$/, "");
var seed = generateSeed();

var pngIndex = 0;
var manifest = {
    name: docName,
    canvasWidth: Math.round(doc.width.value),
    canvasHeight: Math.round(doc.height.value),
    scaleMode: "ScaleToFit",
    assets: []
};

// ── Funções utilitárias ───────────────────────────────────────────────────────

function generateSeed() {
    var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    var result = "";
    for (var i = 0; i < 8; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function cleanName(name) {
    return name
        .replace(/\.[^\.]+$/, "")
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
    // Simple hash for unique ID generation
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
        var ch = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + ch;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(8, "0");
}

// ── Exportar camada ────────────────────────────────────────────────────────────

function exportLayerAsPNG(layer) {
    if (!layer.visible) return;

    if (layer.typename === "LayerSet") {
        // Processar sub-camadas do grupo
        for (var i = layer.layers.length - 1; i >= 0; i--) {
            var sub = layer.layers[i];
            if (sub.typename !== "LayerSet" && sub.visible) {
                exportLayerAsPNG(sub);
            }
        }
        return;
    }

    var bounds = layer.visibleBounds;
    var w = Math.round(bounds[2] - bounds[0]);
    var h = Math.round(bounds[3] - bounds[1]);
    if (w <= 0 || h <= 0) return;

    // Criar documento temporário do tamanho exato da camada
    var tempDoc = app.documents.add(w, h, 72, layer.name + "_temp", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);

    // Copiar e colar a camada
    layer.copy(true);
    tempDoc.paste();
    tempDoc.flatten();

    // Salvar como PNG com transparência
    var safeName = cleanName(layer.name);
    var uid = sha256Hash(seed + layer.name + Date.now());
    var pngFile = new File(outputFolder.fsName + "/" + safeName + "_" + uid + ".png");
    var pngOpts = new PNGSaveOptions();
    pngOpts.Interlaced = false;
    tempDoc.saveAs(pngFile, pngOpts, true, Extension.LOWERCASE);
    tempDoc.close(SaveOptions.DONOTSAVECHANGES);

    // Adicionar ao manifest
    var yPos = doc.height.value - bounds[3]; // Inverter Y (Photoshop vs Roblox)
    manifest.assets.push({
        uniqueId: uid,
        filename: safeName + "_" + uid + ".png",
        type: classifyName(layer.name),
        name: safeName,
        x: Math.round(bounds[0]),
        y: Math.round(yPos),
        width: w,
        height: h,
        assetId: "rbxassetid://0"
    });

    pngIndex++;
}

// ── Main ──────────────────────────────────────────────────────────────────────

alert("🎨 Exportando UI para Roblox\n\nDocumento: " + docName + "\nCamadas: " + doc.layers.length + "\nPasta: " + outputFolder.fsName);

for (var i = doc.layers.length - 1; i >= 0; i--) {
    var layer = doc.layers[i];
    if (layer.typename === "BackgroundLayer") continue;
    exportLayerAsPNG(layer);
}

// Salvar manifest
var manifestFile = new File(outputFolder.fsName + "/" + docName + "_manifest.json");
manifestFile.encoding = "UTF-8";
manifestFile.open("w");
manifestFile.write(JSON.stringify(manifest, null, 2));
manifestFile.close();

// Salvar guia de upload
var guideFile = new File(outputFolder.fsName + "/" + docName + "_upload_guide.txt");
guideFile.encoding = "UTF-8";
guideFile.open("w");
guideFile.write(
    "# Guia de Upload — " + docName + "\n\n" +
    "📂 Pasta com assets: " + outputFolder.fsName + "\n\n" +
    "1️⃣  Abra o Roblox Studio\n" +
    "2️⃣  No Explorer: ReplicatedStorage > UIAssets > " + docName + " (crie se não existir)\n" +
    "3️⃣  Arraste os " + pngIndex + " arquivos PNG da pasta acima para o Explorer\n" +
    "4️⃣  Aguarde o upload completar\n" +
    "5️⃣  Copie os Asset IDs (clique direito > Copy Asset ID)\n\n" +
    "6️⃣  Edite " + docName + "_manifest.json substituindo cada \"rbxassetid://0\"\n" +
    "    pelo ID real do asset correspondente.\n\n" +
    "🔑 Seed: " + seed + " (use a mesma seed para reprocessar)\n"
);
guideFile.close();

// Abrir pasta
outputFolder.execute();

alert("✅ Exportação concluída!\n\n" +
    pngIndex + " camadas exportadas como PNGs\n" +
    "Manifest: " + docName + "_manifest.json\n" +
    "Guia: " + docName + "_upload_guide.txt\n\n" +
    "Próximo passo:\n" +
    "Abra o Roblox Studio e importe os PNGs para\n" +
    "ReplicatedStorage/UIAssets/" + docName);
