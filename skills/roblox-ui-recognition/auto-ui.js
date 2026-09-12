#!/usr/bin/env node
"use strict";

/**
 * AutoUI — Escaneia uma pasta de PNGs exportados do Photoshop/Figma
 * e gera automaticamente um manifest Roblox + controller Lua.
 *
 * O sistema reconhece:
 *   - Backgrounds (nomes: background, bg, base, fondo, tela, screen)
 *   - Botões (nomes: button, btn, play, start, click, store, shop)
 *   - Textos/labels (nomes: title, label, text, name, score, timer)
 *   - Ícones (nomes: icon, img, symbol, emoji, badge)
 *   - Painéis (nomes: panel, frame, box, container, card)
 *   - Barras (nomes: bar, health, hp, mana, stamina, progress)
 *   - Imagens decorativas (resto)
 *
 * Layout automático:
 *   - Canvas fixo 1920×1080
 *   - Elementos posicionados por grid inteligente baseado em tamanho
 *   - Background ocupa todo o espaço
 *   - Botões alinhados verticalmente no centro
 *   - Textos ajustados proporcionalmente
 */

const fs = require("node:fs");
const path = require("path");

// ── Config ───────────────────────────────────────────────────────────────────

const CANVAS_W = 1920;
const CANVAS_H = 1080;
const SCALE = 1; // 1:1 com o canvas

// ── Classifiers ──────────────────────────────────────────────────────────────
const SmartClassifier = require("./smart-classifier");

const CLASSIFIERS = [
	{
		patterns: ["background", "bg", "base", "fundo", "tela", "screen", "telafundo"],
		type: "background",
	},
	{
		patterns: ["button", "btn", "play", "start", "jogar", "click", "store", "shop", "botao"],
		type: "button",
	},
	{
		patterns: ["title", "label", "text", "name", "score", "timer", "rank", "money", "robux", "texto", "titulo"],
		type: "label",
	},
	{
		patterns: ["icon", "img", "symbol", "emoji", "badge", "logo", "avata", "foto", "imagem", "drawable", "drawablenode"],
		type: "icon",
	},
	{
		patterns: ["panel", "frame", "box", "container", "card", "painel", "janela", "menu", "modal"],
		type: "panel",
	},
	{
		patterns: ["bar", "health", "hp", "mana", "stamina", "progress", "barra", "vida", "ener"],
		type: "bar",
	},
	{
		patterns: ["effect", "fx", "glow", "shadow", "blur", "particle", "efeito"],
		type: "effect",
	},
	{
		patterns: ["separator", "line", "divider", "border", "borda", "linha"],
		type: "separator",
	},
	{
		patterns: ["asset", "item", "equip", "weapon", "sword", "paddle", "ball", "racket"],
		type: "item",
	},
];

/**
 * Classificação rápida baseada apenas no nome (sem abrir arquivo).
 * Usada como fallback quando dimensões não estão disponíveis.
 */
function classify(name) {
	const lower = name.toLowerCase();
	for (const c of CLASSIFIERS) {
		for (const p of c.patterns) {
			if (lower.includes(p)) return c.type;
		}
	}
	return "image";
}

/**
 * Classificação inteligente com análise dimensional e de cor.
 * Requer que o arquivo seja acessível no disco.
 */
function classifySmart(filePath, name, dimensions) {
	try {
		const results = SmartClassifier.classifyBatch([{
			path: filePath,
			position: { x: 0, y: 0, width: dimensions.width || 0, height: dimensions.height || 0 },
		}], { canvasW: CANVAS_W, canvasH: CANVAS_H, verbose: false });

		if (results.length > 0 && results[0].confidence > 0.35) {
			return results[0].type;
		}
	} catch (e) {
		// Fall back to keyword classification
	}
	return classify(name);
}

// ── Image dimensions ─────────────────────────────────────────────────────────

function getImageSize(filePath) {
	try {
		const buf = fs.readFileSync(filePath);
		// PNG signature check
		if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4E && buf[3] === 0x47) {
			const w = buf.readUInt32BE(16);
			const h = buf.readUInt32BE(20);
			return { width: w, height: h };
		}
		// JPEG
		if (buf[0] === 0xFF && buf[1] === 0xD8) {
			let i = 2;
			while (i < buf.length - 1) {
				if (buf[i] === 0xFF && (buf[i + 1] === 0xC0 || buf[i + 1] === 0xC2)) {
					const w = buf.readUInt16BE(i + 5);
					const h = buf.readUInt16BE(i + 7);
					return { width: w, height: h };
				}
				i++;
			}
		}
	} catch {
		// Fallback to filename-based estimation
	}
	return null;
}

// ── Layout engine ─────────────────────────────────────────────────────────────

function computeLayout(files) {
	const elements = [];
	const byType = { background: [], panel: [], button: [], label: [], icon: [], image: [], bar: [], separator: [], effect: [], item: [] };

	// Smart classification pass: try dimension+color analysis first
	for (const f of files) {
		let cls;
		const dims = f.size && (f.size.width > 0 && f.size.height > 0);
		if (dims) {
			cls = classifySmart(f.path, f.name, f.size);
		} else {
			cls = classify(f.name);
		}
		f.classifiedType = cls;
		byType[cls].push(f);
	}

	// ── Background (always first, fills screen) ──
	for (const f of byType.background) {
		elements.push({
			type: "ImageLabel",
			name: cleanName(f.name),
			assetId: "PLACEHOLDER_" + f.index,
			x: 0, y: 0,
			width: CANVAS_W,
			height: CANVAS_H,
			anchorX: 0, anchorY: 0,
			zIndex: 1,
			scaleType: "Fill",
			children: [],
		});
	}

	// If no background found, add a default one that the user can fill
	if (byType.background.length === 0) {
		elements.push({
			type: "Frame",
			name: "DefaultBackground",
			x: 0, y: 0,
			width: CANVAS_W,
			height: CANVAS_H,
			anchorX: 0, anchorY: 0,
			backgroundColor: { r: 0.09, g: 0.11, b: 0.13 },
			zIndex: 1,
			children: [],
		});
	}

	// ── Panels (background layers for content) ──
	let panelY = 60;
	for (const f of byType.panel) {
		const w = Math.min(f.size.width || 800, CANVAS_W - 100);
		const h = Math.min(f.size.height || 400, CANVAS_H - panelY - 40);
		const x = Math.max(0, (CANVAS_W - w) / 2);
		elements.push({
			type: "Frame",
			name: cleanName(f.name),
			x, y: panelY,
			width: w, height: h,
			anchorX: 0.5, anchorY: 0,
			backgroundColor: { r: 0.09, g: 0.11, b: 0.13 },
			backgroundTransparency: 0.0,
			borderRadius: 12,
			zIndex: 2,
			children: [],
		});
		panelY += h + 30;
	}

	// ── Buttons (centered vertically, stacked) ──
	const buttons = byType.button;
	if (buttons.length > 0) {
		const btnW = Math.min(400, CANVAS_W * 0.4);
		const btnH = 72;
		const totalBtnH = buttons.length * (btnH + 20) - 20;
		let btnStartY = Math.max(200, (CANVAS_H - totalBtnH) / 2);

		for (const f of buttons) {
			const label = extractLabel(f.name);
			elements.push({
				type: "TextButton",
				name: cleanName(f.name),
				text: label,
				x: CANVAS_W / 2,
				y: btnStartY + btnH / 2,
				width: btnW,
				height: btnH,
				anchorX: 0.5, anchorY: 0.5,
				backgroundColor: { r: 0.15, g: 0.17, b: 0.20 },
				borderRadius: 12,
				textColor: { r: 1, g: 1, b: 1 },
				textSize: 22,
				font: "GothamBold",
				zIndex: 5,
				interactable: true,
				events: { Activated: "on" + cleanName(f.name) + "Pressed" },
				children: [
					// Icon child if image matches
					...findMatchingIcons(f, byType.icon, elements),
				],
			});
			btnStartY += btnH + 20;
		}
	}

	// ── Labels ──
	let labelY = 80;
	for (const f of byType.label) {
		const isTitle = f.name.toLowerCase().includes("title") || f.name.toLowerCase().includes("titulo");
		const fontSize = isTitle ? 48 : 24;
		const labelH = isTitle ? 70 : 40;
		elements.push({
			type: "TextLabel",
			name: cleanName(f.name),
			text: extractLabel(f.name),
			x: CANVAS_W / 2,
			y: labelY,
			width: CANVAS_W - 100,
			height: labelH,
			anchorX: 0.5, anchorY: 0,
			textColor: { r: 1, g: 1, b: 1 },
			textSize: fontSize,
			font: isTitle ? "GothamBlack" : "GothamBold",
			zIndex: 4,
			children: [],
		});
		labelY += labelH + 15;
	}

	// ── Icons ──
	for (const f of byType.icon) {
		const size = Math.min(f.size.width || 100, f.size.height || 100);
		elements.push({
			type: "ImageLabel",
			name: cleanName(f.name),
			assetId: "PLACEHOLDER_" + f.index,
			x: CANVAS_W / 2,
			y: CANVAS_H / 2,
			width: size,
			height: size,
			anchorX: 0.5, anchorY: 0.5,
			zIndex: 3,
			scaleType: "Crop",
			children: [],
		});
	}

	// ── Bars (health/mana bars) ──
	for (const f of byType.bar) {
		const barW = Math.min(400, CANVAS_W * 0.3);
		const barH = 24;
		elements.push({
			type: "Frame",
			name: cleanName(f.name) + "_Bg",
			x: 40, y: 30,
			width: barW, height: barH,
			anchorX: 0, anchorY: 0,
			backgroundColor: { r: 0.1, g: 0.1, b: 0.1 },
			borderRadius: 6,
			zIndex: 6,
			children: [
				{
					type: "Frame",
					name: cleanName(f.name) + "_Fill",
					x: 0, y: 0,
					width: barW * 0.7, height: barH,
					anchorX: 0, anchorY: 0,
					backgroundColor: { r: 0.3, g: 0.8, b: 0.3 },
					borderRadius: 6,
					zIndex: 7,
					children: [],
				},
			],
		});
	}

	// ── Remaining images ──
	for (const f of byType.image) {
		const w = Math.min(f.size.width || 200, 300);
		const h = Math.min(f.size.height || 200, 300);
		elements.push({
			type: "ImageLabel",
			name: cleanName(f.name),
			assetId: "PLACEHOLDER_" + f.index,
			x: (CANVAS_W - w) / 2,
			y: CANVAS_H / 2,
			width: w,
			height: h,
			anchorX: 0.5, anchorY: 0.5,
			zIndex: 3,
			scaleType: "Crop",
			children: [],
		});
	}

	// ── Separators ──
	for (const f of byType.separator) {
		const sepW = Math.min(f.size.width || 600, CANVAS_W - 200);
		elements.push({
			type: "Frame",
			name: cleanName(f.name),
			x: CANVAS_W / 2,
			y: CANVAS_H / 2,
			width: sepW,
			height: 4,
			anchorX: 0.5, anchorY: 0.5,
			backgroundColor: { r: 0.4, g: 0.4, b: 0.4 },
			zIndex: 3,
			children: [],
		});
	}

	return elements;
}

function findMatchingIcons(matchFile, iconFiles, elements) {
	const matches = [];
	for (const icon of iconFiles) {
		if (icon.name.toLowerCase().includes(matchFile.name.toLowerCase().split(" ")[0])) {
			matches.push({
				type: "ImageLabel",
				name: cleanName(icon.name),
				assetId: "PLACEHOLDER_" + icon.index,
				x: -30, y: 0,
				width: 40, height: 40,
				anchorX: 0, anchorY: 0.5,
				zIndex: 6,
				scaleType: "Crop",
				children: [],
			});
		}
	}
	return matches;
}

// ── Name helpers ──────────────────────────────────────────────────────────────

function cleanName(name) {
	return name
		.replace(/\.[^.]+$/, "")          // remove extension
		.replace(/[_\-\s]+/g, "")          // remove separators
		.replace(/[0-9]/g, "")             // remove numbers
		.replace(/[^a-zA-ZÀ-ÿ]/g, "")      // keep letters only
		.replace(/(^|_)([a-zA-Z])/g, (_, sep, char) => char.toUpperCase()) // camelCase
		.replace(/^[A-Z]/, (c) => c.toLowerCase());
}

function extractLabel(name) {
	// Try to extract readable label from filename
	const clean = name
		.replace(/\.[^.]+$/, "")
		.replace(/[_\-\s]+/g, " ")
		.replace(/[0-9]+/g, "")
		.trim();
	return clean || "Label";
}

// ── Manifest generator ────────────────────────────────────────────────────────

function generateManifest(folderPath) {
	// Scan files
	const rawFiles = fs.readdirSync(folderPath).filter((f) => /\.(png|jpg|jpeg)$/i.test(f));

	const files = rawFiles.map((name, i) => {
		const filePath = path.join(folderPath, name);
		const size = getImageSize(filePath);
		return { name, path: filePath, index: i, size: size || { width: 200, height: 200 } };
	});

	const elements = computeLayout(files);

	const manifest = {
		name: path.basename(folderPath) + "Screen",
		canvasWidth: CANVAS_W,
		canvasHeight: CANVAS_H,
		scaleMode: "ScaleToFit",
		elements: elements,
		// Placeholder map for asset ID replacement
		placeholders: files.map((f, i) => ({
			placeholder: "PLACEHOLDER_" + i,
			filename: f.name,
			assetId: "rbxassetid://0",
		})),
	};

	return { manifest, files };
}

// ── Lua generation ────────────────────────────────────────────────────────────

function generateLua(manifest, files) {
	let lua = `--!strict\n`;
	lua += `-- [[\n`;
	lua += `-- ${manifest.name}\n`;
	lua += `-- Gerado automaticamente do pacote: ${files.length} assets\n`;
	lua += `-- Canvas: ${manifest.canvasWidth}x${manifest.canvasHeight}\n`;
	lua += `-- ]]\n\n`;

	lua += `local ReplicatedStorage = game:GetService("ReplicatedStorage")\n`;
	lua += `local Players = game:GetService("Players")\n\n`;

	// Check for UIBridge
	lua += `local UIBridge = require(ReplicatedStorage:WaitForChild("UIBridge"))\n\n`;

	// Asset IDs
	lua += `-- Asset IDs (substituir PLACEHOLDER_XXX pelos IDs reais do Roblox)\n`;
	for (const ph of manifest.placeholders) {
		lua += `local ${cleanName(ph.filename.replace(/\.[^.]+$/, ""))} = "${ph.assetId}" -- ${ph.filename}\n`;
	}
	lua += "\n";

	// Manifest data
	lua += `local _manifest = {\n`;
	lua += `\tname = "${manifest.name}",\n`;
	lua += `\tcanvasWidth = ${manifest.canvasWidth},\n`;
	lua += `\tcanvasHeight = ${manifest.canvasHeight},\n`;
	lua += `\tscaleMode = "${manifest.scaleMode}",\n`;
	lua += `\telements = {\n`;

	for (const elem of manifest.elements) {
		lua += `\t\t-- ${elem.type}: ${elem.name}\n`;
	}
	lua += `\t},\n`;
	lua += "}\n\n";

	// Controller
	const className = manifest.name + "Controller";
	lua += `local ${className} = {\n`;
	lua += `\tName = "${className}",\n`;
	lua += `}\n\n`;

	lua += `function ${className}.Init()\n`;
	lua += `\t-- TODO: Substituir PLACEHOLDER_0, PLACEHOLDER_1, etc.\n`;
	lua += `\t-- pelos Asset IDs do Roblox Studio\n`;
	lua += `\tprint("[${className}] Run Init() after setting asset IDs")\n`;
	lua += `end\n\n`;

	lua += `function ${className}.Show()\n`;
	lua += `\t-- TODO: Build and show the screen\n`;
	lua += `end\n\n`;

	lua += `function ${className}.Hide()\n`;
	lua += `\t-- TODO: Hide the screen\n`;
	lua += `end\n\n`;

	lua += `return ${className}\n`;

	return lua;
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
	const args = process.argv.slice(2);
	if (args.length === 0) {
		console.error("Uso: node auto-ui.js <pasta-png> [--output <pasta>] [--name <nome>]");
		console.error("");
		console.error("Exemplo:");
		console.error('  node auto-ui.js "C:/Users/me/Downloads/ui_export"');
		console.error('  node auto-ui.js "C:/Users/me/Downloads/ui_export" --output ./src/UI --name Lobby');
		process.exit(1);
	}

	const folderPath = args[0];
	let outputDir = null;
	let screenName = null;

	for (let i = 1; i < args.length; i++) {
		if (args[i] === "--output" && args[i + 1]) outputDir = args[++i];
		else if (args[i] === "--name" && args[i + 1]) screenName = args[++i];
	}

	if (!fs.existsSync(folderPath)) {
		console.error(`Erro: pasta não encontrada: ${folderPath}`);
		process.exit(1);
	}

	console.log("═".repeat(60));
	console.log("  AutoUI — Scanner de Assets → Roblox UI");
	console.log("═".repeat(60));
	console.log(`📂 Pasta:    ${folderPath}`);
	console.log(`📐 Canvas:   ${CANVAS_W} × ${CANVAS_H}`);
	console.log("");

	// Generate
	const { manifest, files } = generateManifest(folderPath);
	manifest.name = screenName || manifest.name;

	console.log(`🖼️  Assets encontrados: ${files.length}`);
	console.log("");

	// Classify summary
	const byType = {};
	for (const f of files) {
		const t = f.classifiedType || classify(f.name);
		byType[t] = (byType[t] || 0) + 1;
	}
	console.log("📊 Classificação automática:");
	for (const [type, count] of Object.entries(byType)) {
		console.log(`   ${type.padEnd(12)} ${count} arquivo(s)`);
	}
	console.log("");

	// Write manifest
	const outBase = outputDir || process.cwd();
	const manifestPath = path.join(outBase, `${manifest.name}_manifest.json`);
	fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf-8");
	console.log(`📋 Manifest: ${manifestPath}`);

	// Write Lua
	const luaPath = path.join(outBase, `${manifest.name}Controller.lua`);
	const luaContent = generateLua(manifest, files);
	fs.writeFileSync(luaPath, luaContent, "utf-8");
	console.log(`📝 Controller: ${luaPath}`);

	// Placeholder map
	const placehPath = path.join(outBase, `${manifest.name}_placeholders.txt`);
	let phText = "-- Substitua estes placeholders pelos Asset IDs do Roblox Studio\n";
	for (const ph of manifest.placeholders) {
		phText += `${ph.placeholder}  →  ${ph.filename}\n`;
	}
	fs.writeFileSync(placehPath, phText, "utf-8");
	console.log(`🔑 Placeholders: ${placehPath}`);

	console.log("");
	console.log("═".repeat(60));
	console.log("  PRÓXIMOS PASSOS");
	console.log("═".repeat(60));
	console.log(`1. Abra o Roblox Studio`);
	console.log(`2. Importe os ${files.length} PNGs para ReplicatedStorage/UIAssets`);
	console.log("3. Copie os Asset IDs (clique direito no asset → Copy Asset ID)");
	console.log(`4. Edite ${luaPath} substituindo cada "rbxassetid://0"`);
	console.log("   pelo ID real correspondente ao placeholder");
	console.log("");
	console.log(`Ou use o manager para atualizar automaticamente:`);
	console.log(`  node roblox-ui-manage.js update-placeholders ${luaPath} --assets=id1=name1,id2=name2`);
	console.log("");
	console.log(`📊 Total: ${files.length} assets → ${manifest.name}`);
}

main();
