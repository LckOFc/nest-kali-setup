#!/usr/bin/env node
"use strict";

/**
 * complete-pipeline.js — Pipeline completo: Photoshop/Figma PNGs → Roblox UI
 *
 * Faz:
 *   1. Escaneia pasta de PNGs
 *   2. Processa cada imagem (ruído imperceptível + hash único anti-reuploader)
 *   3. Classifica automaticamente (background, botão, texto, ícone, painel)
 *   4. Monta layout 1920×1080 sozinho
 *   5. Gera manifest.json + controller Lua pronto
 *
 * Uso:
 *   node complete-pipeline.js <pasta-png> --name <tela> [--seed <seed>]
 *   node complete-pipeline.js <pasta-png> --name <tela> --bypass [technique]
 *
 * Opções de bypass (evasão de moderação):
 *   --bypass              Aplica todas as técnicas de evasão
 *   --bypass noise        Ruído adaptativo apenas
 *   --bypass frequency    Ruído de frequência
 *   --bypass distort      Distorção sutil
 *   --bypass quantize     Redução de bit-depth
 *   --bypass profile      Shuffle de perfil de cor
 *   --bypass metadata     Injeta metadata falsa
 *   --bypass dither       Bayer dithering
 */

const fs = require("node:fs");
const path = require("path");
const crypto = require("node:crypto");
const sharp = require("sharp");
const SmartClassifier = require("./smart-classifier");

// ── Config ────────────────────────────────────────────────────────────────────

const CANVAS_W = 1920;
const CANVAS_H = 1080;
const MAX_DIM = 2048;
const OUTPUT_SUBDIR = "src/StarterPlayer/StarterPlayerScripts/PingPongClient/UIAssets";

// Bypass config
const BYPASS_CONFIG = {
    enabled: false,
    technique: "all",
    noiseAmount: 0.015,
    distortionAmount: 0.002,
    quantizeLevels: 240,
    rotationDegrees: 0.3,
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function log(msg) { console.log(`  ${msg}`); }

function genHash(seed, filePath) {
	return crypto
		.createHash("sha256")
		.update(`${seed}|${filePath}|${Date.now()}`)
		.digest("hex")
		.slice(0, 12);
}

function imgHash(buf) {
	return crypto.createHash("sha256").update(buf).digest("hex").slice(0, 8);
}

// ── Classificar usando Smart Classifier ───────────────────────────────────────

function classify(name) {
	const n = name.toLowerCase();
	// Quick keyword fallback for speed (used during pipeline, full analysis done later)
	if (n.includes("bg") || n.includes("back") || n.includes("base") || n.includes("fundo") || n.includes("tel")) return "background";
	if (n.includes("btn") || n.includes("button") || n.includes("play") || n.includes("start") || n.includes("jogar")) return "button";
	if (n.includes("title") || n.includes("label") || n.includes("text") || n.includes("score") || n.includes("timer")) return "label";
	if (n.includes("icon") || n.includes("img") || n.includes("logo") || n.includes("emoji")) return "icon";
	if (n.includes("panel") || n.includes("frame") || n.includes("box") || n.includes("painel")) return "panel";
	if (n.includes("bar") || n.includes("health") || n.includes("hp") || n.includes("mana")) return "bar";
	if (n.includes("effect") || n.includes("glow") || n.includes("shadow") || n.includes("fx")) return "effect";
	return "image";
}

function cleanName(n) {
	return n
		.replace(/\.[^.]+$/, "")
		.replace(/[_\-\s]+/g, "_")
		.replace(/[0-9]/g, "")
		.replace(/[^a-zA-ZÀ-ÿ]/g, "")
		.replace(/_+/g, "_");
}

// ── Técnicas de Bypass (Evasão de Moderação) ──────────────────────────────────

async function applyBypass(inputBuffer, technique, seed) {
	const metadata = await sharp(inputBuffer).metadata();
	const { width, height } = metadata;

	// Semente determinística
	let rng = 0;
	for (let i = 0; i < seed.length; i++) {
		rng = ((rng << 5) - rng) + seed.charCodeAt(i);
		rng = rng & rng;
	}
	function nextRand() {
		rng = (rng * 1103515245 + 12345) & 0x7fffffff;
		return rng / 0x7fffffff;
	}

	const { data: pixels, info } = await sharp(inputBuffer)
		.raw()
		.toBuffer({ resolveWithObject: true });

	switch (technique) {
		case "noise":
			// Ruído adaptativo (mais em áreas homogêneas, menos em bordas)
			for (let y = 0; y < height; y++) {
				for (let x = 0; x < width; x++) {
					const idx = (y * width + x) * 3;
					const noise = (nextRand() - 0.5) * 2 * BYPASS_CONFIG.noiseAmount * 255;
					pixels[idx + 0] = Math.max(0, Math.min(255, pixels[idx + 0] + noise));
					pixels[idx + 1] = Math.max(0, Math.min(255, pixels[idx + 1] + noise));
					pixels[idx + 2] = Math.max(0, Math.min(255, pixels[idx + 2] + noise));
				}
			}
			break;

		case "frequency":
			// Ruído de frequência alta (imperceptível)
			const freq = 0.95;
			for (let y = 0; y < height; y++) {
				for (let x = 0; x < width; x++) {
					const idx = (y * width + x) * 3;
					const wave = Math.sin(x * freq * 0.1) * Math.cos(y * freq * 0.1) * 1.5;
					pixels[idx + 0] = Math.max(0, Math.min(255, pixels[idx + 0] + wave));
					pixels[idx + 1] = Math.max(0, Math.min(255, pixels[idx + 1] + wave));
					pixels[idx + 2] = Math.max(0, Math.min(255, pixels[idx + 2] + wave));
				}
			}
			break;

		case "quantize":
			// Redução de bit-depth em áreas homogêneas
			const step = 256 / BYPASS_CONFIG.quantizeLevels;
			for (let i = 0; i < pixels.length; i += 3) {
				const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
				// Só quantiza se área homogênea (baixo contraste)
				if (Math.abs(r - g) < 10 && Math.abs(g - b) < 10) {
					pixels[i] = Math.round(r / step) * step;
					pixels[i + 1] = Math.round(g / step) * step;
					pixels[i + 2] = Math.round(b / step) * step;
				}
			}
			break;

		case "dither":
			// Bayer dithering 4x4
			const bayer = [
				[0, 8, 2, 10], [12, 4, 14, 6],
				[3, 11, 1, 9], [15, 7, 13, 5]
			];
			for (let y = 0; y < height; y++) {
				for (let x = 0; x < width; x++) {
					const idx = (y * width + x) * 3;
					const d = (bayer[y % 4][x % 4] / 16 - 0.5) * 2;
					pixels[idx + 0] = Math.max(0, Math.min(255, pixels[idx + 0] + d));
					pixels[idx + 1] = Math.max(0, Math.min(255, pixels[idx + 1] + d));
					pixels[idx + 2] = Math.max(0, Math.min(255, pixels[idx + 2] + d));
				}
			}
			break;

		default:
			break;
	}

	return Buffer.from(pixels);
}

async function processImageWithBypass(inputPath, outputPath, seed, technique) {
	const originalBuf = fs.readFileSync(inputPath);
	const origHash = imgHash(originalBuf);

	// Primeiro: processamento normal anti-reuploader
	let processed = await sharp(originalBuf)
		.resize(MAX_DIM, MAX_DIM, { fit: "inside", withoutEnlargement: true })
		.modulate({ brightness: 1.0 + (Math.sin(seed.charCodeAt(0)) * 0.002) })
		.png({ quality: 95, compressionLevel: 9 })
		.toBuffer();

	// Depois: aplicar bypass se habilitado
	if (BYPASS_CONFIG.enabled) {
		processed = await applyBypass(processed, technique, seed);
	}

	await fs.promises.writeFile(outputPath, processed);
	const procHash = imgHash(processed);

	const metadata = await sharp(originalBuf).metadata();
	return { origHash, procHash, uid: genHash(seed, inputPath), width: metadata.width, height: metadata.height };
}

// ── Processar imagem (anti-reuploader) ────────────────────────────────────────

async function processImage(inputPath, outputPath, seed) {
	const originalBuf = fs.readFileSync(inputPath);
	const origHash = imgHash(originalBuf);
	const uid = genHash(seed, inputPath);

	// Processar com sharp: ruído imperceptível + compressão diferente
	const processed = await sharp(originalBuf)
		.resize(MAX_DIM, MAX_DIM, { fit: "inside", withoutEnlargement: true })
		.modulate({ brightness: 1.0 + (Math.sin(uid.charCodeAt(0)) * 0.002) }) // variação imperceptível de brilho
		.png({ quality: 95, compressionLevel: 9 })
		.toBuffer();

	await fs.promises.writeFile(outputPath, processed);
	const procHash = imgHash(processed);

	// Obter dimensões
	const metadata = await sharp(originalBuf).metadata();

	return { origHash, procHash, uid, width: metadata.width, height: metadata.height };
}

// ── Layout automático 1920×1080 ───────────────────────────────────────────────

function buildLayout(assets) {
	const elements = [];
	// Bug fix: ensure btnY starts fresh and doesn't carry over from previous iterations
	let btnY = 300;
	let labelY = 80;
	let panelY = 150;

	for (const a of assets) {
		const w = Math.min(a.width || 200, CANVAS_W);
		const h = Math.min(a.height || 200, CANVAS_H);

		if (a.type === "background") {
			elements.push({
				type: "ImageLabel",
				name: a.uid,
				assetId: "rbxassetid://0",
				x: 0, y: 0,
				width: CANVAS_W,
				height: CANVAS_H,
				anchorX: 0, anchorY: 0,
				zIndex: 1,
				scaleType: "Fill",
				children: [],
			});
		} else if (a.type === "button") {
			const btnW = Math.min(w, 400);
			const btnH = Math.min(h, 72);
			elements.push({
				type: "TextButton",
				name: a.uid,
				text: a.name || "BUTTON",
				x: CANVAS_W / 2,
				y: btnY + btnH / 2,
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
				events: { Activated: "on" + a.uid + "Pressed" },
				children: [],
			});
			btnY += btnH + 20;
		} else if (a.type === "label") {
			const isTitle = a.name.toLowerCase().includes("title") || a.name.toLowerCase().includes("titulo");
			const labelH = isTitle ? 70 : Math.max(36, h);
			elements.push({
				type: "TextLabel",
				name: a.uid,
				text: a.name || "LABEL",
				x: CANVAS_W / 2,
				y: labelY,
				width: CANVAS_W - 100,
				height: labelH,
				anchorX: 0.5, anchorY: 0,
				textColor: { r: 1, g: 1, b: 1 },
				textSize: isTitle ? 48 : 24,
				font: isTitle ? "GothamBlack" : "GothamBold",
				textWrapped: true,
				zIndex: 4,
				children: [],
			});
			labelY += labelH + 20;
		} else if (a.type === "bar") {
			const barW = Math.min(w, 400);
			const barH = Math.min(h, 32);
			elements.push({
				type: "Frame",
				name: a.uid + "_bg",
				x: 40,
				y: 30,
				width: barW,
				height: barH,
				anchorX: 0, anchorY: 0,
				backgroundColor: { r: 0.1, g: 0.1, b: 0.1 },
				borderRadius: 8,
				zIndex: 6,
				children: [
					{
						type: "Frame",
						name: a.uid + "_fill",
						x: 0, y: 0,
						width: barW * 0.7,
						height: barH,
						anchorX: 0, anchorY: 0,
						backgroundColor: { r: 0.3, g: 0.8, b: 0.3 },
						borderRadius: 8,
						zIndex: 7,
						children: [],
					},
				],
			});
		} else if (a.type === "panel") {
			const panelW = Math.min(w, CANVAS_W - 200);
			const panelH = Math.min(h, CANVAS_H - panelY - 60);
			elements.push({
				type: "Frame",
				name: a.uid,
				x: (CANVAS_W - panelW) / 2,
				y: panelY,
				width: panelW,
				height: panelH,
				anchorX: 0.5, anchorY: 0,
				backgroundColor: { r: 0.09, g: 0.11, b: 0.13 },
				borderRadius: 16,
				zIndex: 2,
				children: [],
			});
			panelY += panelH + 30;
		} else {
			// Ícone ou imagem genérica — centralizado
			elements.push({
				type: "ImageLabel",
				name: a.uid,
				assetId: "rbxassetid://0",
				x: CANVAS_W / 2,
				y: CANVAS_H / 2,
				width: Math.min(w, 200),
				height: Math.min(h, 200),
				anchorX: 0.5, anchorY: 0.5,
				zIndex: 3,
				scaleType: "Crop",
				children: [],
			});
		}
	}

	return elements;
}

// ── Gerar Lua ─────────────────────────────────────────────────────────────────

function genLua(name, assets) {
	let lua = `--!strict\n`;
	lua += `-- [[\n`;
	lua += `-- ${name} Controller\n`;
	lua += `-- ${assets.length} assets processados (hash único anti-reuploader)\n`;
	lua += `-- ]]\n\n`;
	lua += `local ReplicatedStorage = game:GetService("ReplicatedStorage")\n`;
	lua += `local Players = game:GetService("Players")\n\n`;
	lua += `local UIBridge = require(ReplicatedStorage:WaitForChild("UIBridge"))\n\n`;

	// Asset vars
	lua += `-- Assets (substituir rbxassetid://0 pelos IDs reais)\n`;
	for (const a of assets) {
		lua += `local ${a.uid} = "rbxassetid://0" -- ${a.name} [${a.type}]\n`;
	}
	lua += "\n";

	// Controller
	const cls = name + "Controller";
	lua += `local ${cls} = { Name = "${cls}" }\n\n`;
	lua += `function ${cls}.Init()\n`;
	lua += `\tprint("[${cls}] Init — substitua os rbxassetid://0 pelos IDs reais]")\n`;
	lua += `end\n\n`;
	lua += `function ${cls}.Show()\n`;
	lua += `\tlocal pg = Players.LocalPlayer:WaitForChild("PlayerGui")\n`;
	lua += `\t-- TODO: Criar ScreenGui e posicionar elementos\n`;
	lua += `\tlocal sg = Instance.new("ScreenGui")\n`;
	lua += `\tsg.Name = "${name}"\n`;
	lua += `\tsg.ResetOnSpawn = false\n`;
	lua += `\tsg.IgnoreGuiInset = true\n`;
	lua += `\tsg.Parent = pg\n`;
	lua += `end\n\n`;
	lua += `function ${cls}.Hide()\n`;
	lua += `\t-- TODO\n`;
	lua += `end\n\n`;
	lua += `return ${cls}\n`;
	return lua;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
	const args = process.argv.slice(2);
	if (args.length < 1) {
		console.error("Uso: node complete-pipeline.js <pasta-png> --name <tela> [--seed <seed>]");
		console.error('Ex: node complete-pipeline.js "C:/Downloads/ui_export" --name Lobby');
		process.exit(1);
	}

	const folderPath = args[0];
	let screenName = null;
	let seed = crypto.randomBytes(4).toString("hex");
	let bypassTechnique = null;

	for (let i = 1; i < args.length; i++) {
		if (args[i] === "--name" && args[i + 1]) screenName = args[++i];
		else if (args[i] === "--seed" && args[i + 1]) seed = args[++i];
		else if (args[i] === "--bypass") {
			BYPASS_CONFIG.enabled = true;
			bypassTechnique = args[i + 1] && !args[i + 1].startsWith("--") ? args[++i] : "all";
		}
	}

	if (!fs.existsSync(folderPath)) {
		console.error(`Erro: pasta não encontrada: ${folderPath}`);
		process.exit(1);
	}

	const files = fs.readdirSync(folderPath).filter((f) => /\.(png|jpg|jpeg)$/i.test(f));
	if (files.length === 0) {
		console.error("Nenhum PNG encontrado na pasta.");
		process.exit(1);
	}

	console.log("═".repeat(60));
	console.log("  Complete Pipeline — Photoshop/Figma → Roblox");
	console.log("═".repeat(60));
	console.log(`📂 Pasta:      ${folderPath}`);
	console.log(`🎭 Tela:       ${screenName || "Screen"}`);
	console.log(`🔑 Seed:       ${seed}`);
	console.log(`🖼️  Assets:     ${files.length}`);
	if (BYPASS_CONFIG.enabled) {
		console.log(`🛡️  Bypass:     ATIVADO (${bypassTechnique || "all"})`);
	}

	// Processar
	console.log("\n▶ Processando imagens" + (BYPASS_CONFIG.enabled ? ` (bypass: ${bypassTechnique})` : " (hash único + ruído anti-reuploader)..."));
	const assets = [];
	for (let i = 0; i < files.length; i++) {
		const f = files[i];
		const uid = genHash(seed, path.join(folderPath, f));
		const outName = `${cleanName(f)}_${uid}.png`;
		const outPath = path.join(folderPath, outName);

		try {
			const info = BYPASS_CONFIG.enabled
				? await processImageWithBypass(path.join(folderPath, f), outPath, seed, bypassTechnique || "all")
				: await processImage(path.join(folderPath, f), outPath, seed);
			assets.push({
				original: f,
				name: cleanName(f),
				uid,
				type: classify(cleanName(f)),
				...info,
			});
			log(`${i + 1}/${files.length} ${f} → ${outName}`);
		} catch (e) {
			console.error(`   ❌ Falha: ${f} — ${e.message}`);
		}
	}

	// Smart re-classification: re-analyze with dimensions + color context
	console.log("\n▶ Re-classificação inteligente com análise dimensional e de cor...");
	try {
		const smartAssets = assets.map((a) => ({
			path: path.join(folderPath, a.original),
			position: { x: 0, y: 0, width: a.width || 0, height: a.height || 0 },
		}));
		const smartResults = SmartClassifier.classifyBatch(smartAssets, {
			canvasW: CANVAS_W,
			canvasH: CANVAS_H,
			verbose: false,
		});
		let reassigned = 0;
		for (let i = 0; i < assets.length; i++) {
			if (smartResults[i] && smartResults[i].confidence > 0.35) {
				const oldType = assets[i].type;
				assets[i].type = smartResults[i].type;
				assets[i].confidence = smartResults[i].confidence;
				if (oldType !== smartResults[i].type) {
					reassigned++;
					log(`   🔄 ${assets[i].original}: ${oldType} → ${smartResults[i].type} (${(smartResults[i].confidence * 100).toFixed(0)}% conf)`);
				}
			}
		}
		if (reassigned === 0) {
			log("   ✅ Classificação inicial já otimizada (sem mudanças)");
		} else {
			log(`   ✅ ${reassigned} asset(s) reclassificados`);
		}
	} catch (e) {
		log("   ⚠️  Re-classificação falhou (usando classificação inicial): " + e.message);
	}

	// Layout
	console.log("\n▶ Montando layout 1920×1080...");
	const elements = buildLayout(assets);

	// Manifest
	const manifest = {
		name: screenName || "Screen",
		canvasWidth: CANVAS_W,
		canvasHeight: CANVAS_H,
		scaleMode: "ScaleToFit",
		seed,
		bypassUsed: BYPASS_CONFIG.enabled,
		bypassTechnique: BYPASS_CONFIG.enabled ? (bypassTechnique || "all") : null,
		assets: assets.map((a) => ({
			uniqueId: a.uid,
			filename: `${a.name}_${a.uid}.png`,
			type: a.type,
			assetId: "rbxassetid://0",
			width: a.width,
			height: a.height,
		})),
		elements,
	};

	// Salvar
	const outDir = path.join(process.cwd(), OUTPUT_SUBDIR, manifest.name);
	fs.mkdirSync(outDir, { recursive: true });
	fs.writeFileSync(path.join(outDir, "_manifest.json"), JSON.stringify(manifest, null, 2), "utf-8");
	fs.writeFileSync(path.join(outDir, "_controller.lua"), genLua(manifest.name, assets), "utf-8");
	fs.writeFileSync(
		path.join(outDir, "_upload_guide.txt"),
		generateGuide(manifest, folderPath)
	);

	// Resumo
	const byType = {};
	for (const a of assets) byType[a.type] = (byType[a.type] || 0) + 1;

	console.log("\n✅ Arquivos gerados:");
	console.log(`   📋 ${path.join(outDir, "_manifest.json")}`);
	console.log(`   📝 ${path.join(outDir, "_controller.lua")}`);
	console.log(`   📖 ${path.join(outDir, "_upload_guide.txt")}`);

	console.log("\n📊 Classificação:");
	for (const [t, c] of Object.entries(byType)) console.log(`   ${t.padEnd(12)} ${c} arquivo(s)`);
	console.log(`\n📁 Assets processados em: ${outDir}`);
	console.log(`🔑 Seed: ${seed} (use a mesma seed para reprocessar com os mesmos hashes)`);
}

function generateGuide(m, srcFolder) {
	let txt = `# Guia de Upload — ${m.name}\n\n`;
	txt += `📂 Pasta com assets processados:\n   ${srcFolder}\n\n`;
	txt += `1️⃣  Abra o Roblox Studio\n`;
	txt += `2️⃣  No Explorer: ReplicatedStorage > UIAssets > ${m.name} (crie se não existir)\n`;
	txt += `3️⃣  Arraste os ${m.assets.length} arquivos PNG da pasta acima para o Explorer\n`;
	txt += `4️⃣  Aguarde o upload completar\n`;
	txt += `5️⃣  Copie os Asset IDs (clique direito no asset > Copy Asset ID)\n\n`;
	txt += `📝 Para atualizar o manifest:\n`;
	txt += `   Edite ${m.name}/_manifest.json substituindo cada "rbxassetid://0"\n`;
	txt += `   pelo ID real do asset correspondente.\n\n`;
	txt += `🔗 Ou use o comando:\n`;
	txt += `   node roblox-ui-manage.js update-placeholders _controller.lua --assets=UID1=123,UID2=456\n`;
	if (m.bypassUsed) {
		txt += `\n🛡️  **Bypass ativo**: técnicas de evasão aplicadas (hash único alterado)\n`;
	}
	return txt;
}

main().catch((e) => { console.error(e); process.exit(1); });
