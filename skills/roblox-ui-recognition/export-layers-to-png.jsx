// export-layers-to-png.jsx
// Exporta todas as camadas visíveis de um PSD como PNGs separados.
// Uso: File > Scripts > Browse... e selecione este arquivo.
// Ou execute via: cscript //E:jscript "C:\path\to\export-layers-to-png.jsx"

#target photoshop

var outputFolder = Folder.selectDialog("Selecione a pasta de saída para os PNGs:");
if (!outputFolder) exit();

var doc = app.activeDocument;
var fileName = doc.name.replace(/\.[^\.]+$/, "");
var pngCount = 0;

// Exportar toda a arte visível como uma imagem
var exportAll = confirm("Exportar também a versão completa (toda a arte combinada)?");

function exportLayerAsPNG(layer, index) {
    if (!layer.visible) return;
    
    // Criar documento temporário com apenas esta camada
    var tempDoc = app.documents.add(layer.bounds[2], layer.bounds[3], 72, layer.name, NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
    
    // Copiar a camada
    layer.copy(true);
    tempDoc.paste();
    tempDoc.flatten();
    
    // Salvar como PNG
    var pngFile = new File(outputFolder + "/" + fileName + "_" + padIndex(index) + "_" + layer.name.replace(/[^a-zA-Z0-9_\-]/g, "_") + ".png");
    var pngOpts = new PNGSaveOptions();
    pngOpts.Interlaced = false;
    tempDoc.saveAs(pngFile, pngOpts, true, Extension.LOWERCASE);
    tempDoc.close(SaveOptions.DONOTSAVECHANGES);
    pngCount++;
}

function padIndex(n) {
    return String(n).padStart(3, "0");
}

// Processar cada camada
for (var i = doc.layers.length - 1; i >= 0; i--) {
    var layer = doc.layers[i];
    
    // Pular camadas de fundo e grupos vazios
    if (layer.typename === "BackgroundLayer") continue;
    if (layer.typename === "LayerSet") {
        // Processar camadas dentro do grupo
        for (var j = layer.layers.length - 1; j >= 0; j--) {
            var subLayer = layer.layers[j];
            if (subLayer.visible && subLayer.typename !== "LayerSet") {
                exportLayerAsPNG(subLayer, pngCount);
            }
        }
        continue;
    }
    
    exportLayerAsPNG(layer, pngCount);
}

// Exportar versão completa
if (exportAll) {
    var fullPng = new File(outputFolder + "/" + fileName + "_full.png");
    var fullOpts = new PNGSaveOptions();
    fullOpts.Interlaced = false;
    doc.saveAs(fullPng, fullOpts, true, Extension.LOWERCASE);
    pngCount++;
}

alert("Exportação concluída!\n\n" + pngCount + " PNGs salvos em:\n" + outputFolder + "\n\nPróximo passo: use o comando 'node roblox-ui-manage.js import-images " + outputFolder + "' para copiar para o projeto Roblox.");
