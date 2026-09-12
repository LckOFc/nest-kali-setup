/**
 * universal-design-schema.js
 *
 * Schema universal para representar designs de UI de múltiplas fontes:
 *   - Photoshop (PSD via UXP API)
 *   - Figma (via API REST)
 *   - Sketch (via export JSON)
 *   - XD (via export)
 *
 * Objetivo: Servir como entrada padronizada para a IA analisar
 *           e gerar código Roblox.
 *
 * Uso:
 *   const UDS = require('./universal-design-schema');
 *   const schema = UDS.create({ source: 'photoshop', ... });
 *   const aiInput = schema.toAIInput(); // JSON + thumbnails
 */

const fs = require("node:fs");
const path = require("path");
const crypto = require("node:crypto");
const sharp = require("sharp");

// ── Schema Version ───────────────────────────────────────────────────────────

const SCHEMA_VERSION = "1.0.0";

// ── Types Mapping ─────────────────────────────────────────────────────────────

const PHOTOSHOP_TYPES = {
  Layer: "layer",
  LayerSet: "group",
  Artboard: "artboard",
  BackgroundLayer: "background",
};

const ROBLOX_CLASS_MAP = {
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

// ── Generator Principal ───────────────────────────────────────────────────────

class UniversalDesignSchema {
  constructor(options = {}) {
    this.version = SCHEMA_VERSION;
    this.source = options.source || "unknown";
    this.document = {
      name: options.name || "Untitled",
      width: options.width || 1920,
      height: options.height || 1080,
      resolution: options.resolution || 72,
      colorMode: options.colorMode || "RGB",
      bitDepth: options.bitDepth || 8,
    };
    this.artboards = [];
    this.layers = [];
    this.groups = [];
    this.assets = [];
    this.colors = [];
    this.fonts = [];
    this.metadata = {
      generatedAt: new Date().toISOString(),
      generator: "FigmaPS2Roblox UDS",
      version: SCHEMA_VERSION,
    };
  }

  // ── Document ──────────────────────────────────────────────────────────────

  setDocument(info) {
    this.document = { ...this.document, ...info };
    return this;
  }

  // ── Artboards ─────────────────────────────────────────────────────────────

  addArtboard(artboard) {
    this.artboards.push({
      id: artboard.id || this._genId("artboard"),
      name: artboard.name || "Artboard",
      x: artboard.x || 0,
      y: artboard.y || 0,
      width: artboard.width || this.document.width,
      height: artboard.height || this.document.height,
      visible: artboard.visible !== undefined ? artboard.visible : true,
      children: [],
      _raw: artboard,
    });
    return this;
  }

  // ── Layers ────────────────────────────────────────────────────────────────

  addLayer(layer, artboardId = null) {
    const layerData = {
      id: layer.id || this._genId("layer"),
      name: layer.name || "Layer",
      type: layer.type || "layer",
      visible: layer.visible !== undefined ? layer.visible : true,
      opacity: layer.opacity !== undefined ? layer.opacity : 100,
      blendMode: layer.blendMode || "normal",
      bounds: {
        x: layer.x || 0,
        y: layer.y || 0,
        width: layer.width || 0,
        height: layer.height || 0,
      },
      semantic: {
        probableRole: layer.probableRole || this._inferRole(layer),
        confidence: layer.confidence || 0.5,
      },
      effects: layer.effects || [],
      fill: layer.fill || null,
      stroke: layer.stroke || null,
      text: layer.text || null,
      children: [],
      _raw: layer,
    };

    this.layers.push(layerData);

    // Add to artboard if specified
    if (artboardId) {
      const artboard = this.artboards.find((a) => a.id === artboardId);
      if (artboard) {
        artboard.children.push(layerData.id);
      }
    }

    return layerData;
  }

  // ── Groups ────────────────────────────────────────────────────────────────

  addGroup(group) {
    const groupData = {
      id: group.id || this._genId("group"),
      name: group.name || "Group",
      type: "group",
      visible: group.visible !== undefined ? group.visible : true,
      opacity: group.opacity !== undefined ? group.opacity : 100,
      bounds: {
        x: group.x || 0,
        y: group.y || 0,
        width: group.width || 0,
        height: group.height || 0,
      },
      children: [],
      _raw: group,
    };

    this.groups.push(groupData);
    return groupData;
  }

  // ── Assets (exported images) ─────────────────────────────────────────────

  addAsset(asset) {
    this.assets.push({
      id: asset.id || this._genId("asset"),
      name: asset.name,
      path: asset.path,
      width: asset.width,
      height: asset.height,
      fileSize: asset.fileSize || 0,
      format: asset.format || "png",
      transparency: asset.transparency !== undefined ? asset.transparency : true,
      linkToLayer: asset.linkToLayer || null,
      _raw: asset,
    });
    return this;
  }

  // ── Colors ────────────────────────────────────────────────────────────────

  addColor(color, usage = []) {
    this.colors.push({
      id: color.id || this._genId("color"),
      hex: color.hex,
      rgb: color.rgb,
      usage: usage,
    });
    return this;
  }

  // ── Fonts ─────────────────────────────────────────────────────────────────

  addFont(font) {
    this.fonts.push({
      id: font.id || this._genId("font"),
      name: font.name,
      size: font.size,
      weight: font.weight || "regular",
      style: font.style || "normal",
    });
    return this;
  }

  // ── Metadata ──────────────────────────────────────────────────────────────

  setMetadata(meta) {
    this.metadata = { ...this.metadata, ...meta };
    return this;
  }

  // ── To JSON ───────────────────────────────────────────────────────────────

  toJSON() {
    return {
      schemaVersion: this.version,
      source: this.source,
      document: this.document,
      artboards: this.artboards.map((a) => ({
        id: a.id,
        name: a.name,
        x: a.x,
        y: a.y,
        width: a.width,
        height: a.height,
        visible: a.visible,
        children: a.children,
      })),
      layers: this.layers.map((l) => ({
        id: l.id,
        name: l.name,
        type: l.type,
        visible: l.visible,
        opacity: l.opacity,
        blendMode: l.blendMode,
        bounds: l.bounds,
        semantic: l.semantic,
        effects: l.effects,
        fill: l.fill,
        stroke: l.stroke,
        text: l.text,
      })),
      groups: this.groups.map((g) => ({
        id: g.id,
        name: g.name,
        visible: g.visible,
        opacity: g.opacity,
        bounds: g.bounds,
      })),
      assets: this.assets.map((a) => ({
        id: a.id,
        name: a.name,
        path: a.path,
        width: a.width,
        height: a.height,
        fileSize: a.fileSize,
        format: a.format,
        transparency: a.transparency,
        linkToLayer: a.linkToLayer,
      })),
      colors: this.colors,
      fonts: this.fonts,
      metadata: this.metadata,
    };
  }

  // ── AI Input Format ───────────────────────────────────────────────────────
  // Estrutura otimizada para envio à IA (JSON + referências visuais)

  toAIInput() {
    const layersForAI = this.layers.map((l) => ({
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
            color: l.text.color ? l.text.color.hex : null,
          }
        : null,
      effects: l.effects.map((e) => ({
        type: e.type,
        ...(e.type === "dropShadow" && {
          distance: e.distance,
          blur: e.blur,
          color: e.color ? e.color.hex : null,
        }),
      })),
    }));

    return {
      schemaVersion: this.version,
      document: {
        name: this.document.name,
        width: this.document.width,
        height: this.document.height,
        resolution: this.document.resolution,
      },
      layers: layersForAI,
      assets: this.assets.map((a) => ({
        id: a.id,
        name: a.name,
        width: a.width,
        height: a.height,
        path: a.path, // Path relativo para thumbnail
      })),
      responsiveStrategy: this._suggestResponsiveStrategy(),
    };
  }

  // ── Generate Thumbnails ───────────────────────────────────────────────────

  async generateThumbnails(outputDir, maxDimension = 400) {
    const thumbs = [];
    for (const asset of this.assets) {
      if (!asset.path || !fs.existsSync(asset.path)) continue;

      const thumbPath = path.join(
        outputDir,
        `${path.basename(asset.path, path.extname(asset.path))}_thumb.png`
      );

      try {
        await sharp(asset.path)
          .resize(maxDimension, maxDimension, {
            fit: "inside",
            withoutEnlargement: true,
          })
          .toFile(thumbPath);

        thumbs.push({
          assetId: asset.id,
          assetName: asset.name,
          thumbPath: thumbPath,
          thumbWidth: maxDimension,
          thumbHeight: maxDimension,
        });
      } catch (e) {
        console.warn(`[UDS] Failed to generate thumbnail for ${asset.name}: ${e.message}`);
      }
    }
    return thumbs;
  }

  // ── Responsive Strategy ───────────────────────────────────────────────────

  _suggestResponsiveStrategy() {
    const strategies = {
      background: "Fill",
      button: "FixedSize",
      label: "ScaleToFit",
      icon: "FixedSize",
      panel: "ScaleToFit",
      bar: "FixedSize",
      image: "ScaleToFit",
    };

    return this.layers.map((l) => ({
      layerId: l.id,
      layerName: l.name,
      suggestedStrategy: strategies[l.semantic.probableRole] || "FixedSize",
      bounds: l.bounds,
    }));
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  _genId(prefix) {
    return `${prefix}_${crypto.randomBytes(3).toString("hex")}`;
  }

  _inferRole(layer) {
    const name = (layer.name || "").toLowerCase();
    if (name.includes("bg") || name.includes("back")) return "background";
    if (name.includes("btn") || name.includes("button")) return "button";
    if (name.includes("title") || name.includes("label") || name.includes("text")) return "label";
    if (name.includes("icon") || name.includes("img") || name.includes("logo")) return "icon";
    if (name.includes("panel") || name.includes("frame") || name.includes("box")) return "panel";
    if (name.includes("bar") || name.includes("health") || name.includes("hp")) return "bar";
    return "image";
  }
}

// ── Factory Functions ─────────────────────────────────────────────────────────

function createPSDSchema(psdData) {
  const schema = new UniversalDesignSchema({
    source: "photoshop",
    name: psdData.name,
    width: psdData.width,
    height: psdData.height,
    resolution: psdData.resolution,
    colorMode: psdData.colorMode,
  });

  // Add artboards
  if (psdData.artboards) {
    for (const ab of psdData.artboards) {
      schema.addArtboard(ab);
    }
  }

  // Add layers
  if (psdData.layers) {
    for (const layer of psdData.layers) {
      schema.addLayer(layer);
    }
  }

  return schema;
}

function createFigmaschema(figmaData) {
  const schema = new UniversalDesignSchema({
    source: "figma",
    name: figmaData.name,
    width: figmaData.width,
    height: figmaData.height,
  });

  if (figmaData.nodes) {
    for (const node of figmaData.nodes) {
      schema.addLayer({
        id: node.id,
        name: node.name,
        type: node.type,
        visible: node.visible !== false,
        x: node.x || 0,
        y: node.y || 0,
        width: node.width || 0,
        height: node.height || 0,
        probableRole: node.role || "layer",
        confidence: node.confidence || 0.7,
      });
    }
  }

  return schema;
}

// ── Export ─────────────────────────────────────────────────────────────────────

module.exports = {
  UniversalDesignSchema,
  createPSDSchema,
  createFigmaschema,
  SCHEMA_VERSION,
  ROBLOX_CLASS_MAP,
};
