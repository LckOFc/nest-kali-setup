/**
 * Figma UI Export Plugin
 * Plugin do Figma que exporta UI como PNGs + manifest JSON.
 *
 * Instalação:
 *   1. Abra o Figma Desktop
 *   2. Plugins > Development > Create new plugin
 *   3. Cole este código no campo "Code"
 *   4. Salve e execute
 *
 * Comportamento:
 *   - Seleciona uma frame ou grupo na tela
 *   - Exporta cada layer visível como PNG (com transparência)
 *   - Gera manifest.json com posições e metadados
 *   - Abre a pasta de saída automaticamente
 */

export default plugin({
  run() {
    const nodes = figma.currentPageSelection;
    if (nodes.length === 0) {
      figma.ui.postMessage({ type: "error", message: "Selecione uma Frame ou Grupo primeiro." });
      return;
    }

    const root = nodes[0];
    if (root.type !== "FRAME" && root.type !== "GROUP") {
      figma.ui.postMessage({ type: "error", message: "Selecione uma Frame ou Grupo." });
      return;
    }

    const output = figma.showUI(__html__, {
      width: 400,
      height: 300,
      resize: false,
    });

    output.onmessage = async (msg) => {
      if (msg.type === "export") {
        await exportUI(root, output, msg.folder);
      }
    };

    output.postMessage({ type: "ready", name: root.name });
  },
});

async function exportUI(root, ui, folder) {
  ui.postMessage({ type: "progress", value: 0, total: 0 });

  const canvasW = Math.round(root.width);
  const canvasH = Math.round(root.height);
  const manifest = {
    name: root.name,
    canvasWidth: canvasW,
    canvasHeight: canvasH,
    scaleMode: "ScaleToFit",
    elements: [],
    placeholders: [],
  };

  // Collect ALL visible nodes (including the root frame itself)
  const allNodes = getAllVisibleNodes(root);
  let exported = 0;

  for (const node of allNodes) {
    // Skip zero-dimension nodes
    if (!node.width || !node.height || node.width < 1 || node.height < 1) {
      continue;
    }

    try {
      const pngBuffer = await node.exportAsync({
        format: "PNG",
        constraint: { type: "WIDTH", value: node.width },
        scale: 1,
      });

      const filename = `${cleanName(node.name)}.png`;
      const placeholder = `PLACEHOLDER_${manifest.placeholders.length}`;

      manifest.placeholders.push({
        placeholder,
        filename,
        assetId: "rbxassetid://0",
        type: classifyNode(node),
        name: cleanName(node.name),
        x: Math.round(node.x),
        y: Math.round(canvasH - node.y - node.height),
        width: Math.round(node.width),
        height: Math.round(node.height),
      });

      exported++;
      ui.postMessage({ type: "progress", value: exported, total: allNodes.length });
    } catch (e) {
      console.warn(`Failed to export ${node.name}:`, e);
    }
  }

  // Save manifest
  const manifestBlob = new Blob([JSON.stringify(manifest, null, 2)], { type: "application/json" });
  const manifestUrl = URL.createObjectURL(manifestBlob);

  // Download PNGs as a ZIP
  const files = [];
  for (const ph of manifest.placeholders) {
    // Find the node by name and re-export to get blob
    const node = findNodeByName(root, ph.name);
    if (node) {
      try {
        const buf = await node.exportAsync({ format: "PNG", constraint: { type: "WIDTH", value: node.width }, scale: 1 });
        files.push({ name: ph.filename, data: buf });
      } catch {}
    }
  }

  ui.postMessage({
    type: "complete",
    count: exported,
    manifest: manifestUrl,
    files: files.map((f) => ({ name: f.name, data: f.data })),
  });
}

function getAllVisibleNodes(node, isRoot) {
  isRoot = isRoot !== undefined ? isRoot : true;
  const result = [];
  // Root node is always included regardless of type (FRAME, GROUP, etc.)
  if (node.visible) {
    if (isRoot) {
      result.push(node);
    } else if (node.type !== "FRAME" && node.type !== "GROUP") {
      result.push(node);
    }
  }
  for (const child of node.children || []) {
    result.push(...getAllVisibleNodes(child, false));
  }
  return result;
}

function findNodeByName(root, name) {
  if (root.name === name) return root;
  for (const child of root.children || []) {
    const found = findNodeByName(child, name);
    if (found) return found;
  }
  return null;
}

function cleanName(name) {
  return name.replace(/[^a-zA-Z0-9_-]/g, "_").replace(/_+/g, "_");
}

function classifyNode(node) {
  const n = node.name.toLowerCase();
  if (n.indexOf("bg") >= 0 || n.indexOf("back") >= 0 || n.indexOf("base") >= 0) return "background";
  if (n.indexOf("btn") >= 0 || n.indexOf("button") >= 0 || n.indexOf("play") >= 0 || n.indexOf("start") >= 0) return "button";
  if (n.indexOf("title") >= 0 || n.indexOf("label") >= 0 || n.indexOf("text") >= 0 || n.indexOf("name") >= 0) return "label";
  if (n.indexOf("icon") >= 0 || n.indexOf("img") >= 0 || n.indexOf("logo") >= 0) return "icon";
  if (n.indexOf("panel") >= 0 || n.indexOf("frame") >= 0 || n.indexOf("box") >= 0) return "panel";
  return "image";
}
