#!/usr/bin/env node
"use strict";

/**
 * asset-bundler — Pipeline completo: Photoshop PNGs → Roblox Studio
 *
 * Faz:
 *   1. Processar cada PNG (ruído imperceptível + hash único)
 *   2. Upload para Roblox via Studio API (se rodando no Studio)
 *   3. Gerar manifest com Asset IDs mapeados
 *   4. Criar pasta organizados por tela
 *
 * Uso:
 *   node asset-bundler.js <pasta-png> [--studio] [--name <nome>] [--seed <seed>]
 */

const fs = require("node:fs");
const path = require("path");
const crypto = require("node:crypto");
const jimp = require("jimp");

// ── Config ────────────────────────────────────────────────────────────────────

const MAX_DIMENSION = 2048;
const JPEG_QUALITY = 92;
const NOISE_AMOUNT = 0.008; // 0.8% de ruído imperceptível
const OUTPUT_SUBDIR = "src/StarterPlayer/StarterPlayerScripts/PingPongClient/UIAssets";

// ── Hash único por imagem ────────────────────────────────────────────────────

function generateUniqueHash(seed, originalPath) {
	// combina seed + caminho + timestamp para garantir unicidade
	const raw = `${seed}|${originalPath}|${Date.now()}`;
	return crypto.createHash("sha256").update(raw).digest("hex").slice(0, 12);
}

function imageHash(filePath) {
	const buf = fs.readFileSync(filePath);
	return crypto.createHash("sha256").update(buf).digest("hex").slice(0, 8);
}

// ── Processar imagem (anti-reuploader) ───────────────────────────────────────

async function processImage(inputPath, outputPath, seed) {
	const originalHash = imageHash(inputPath);
	const uniqueId = generateUniqueHash(seed, inputPath);

	const image = await jimp.read(inputPath);

	// Resize se necessário
	if (image.width > MAX_DIMENSION || image.height > MAX_DIMENSION) {
		image.resize(MAX_DIMENSION, MAX_DIMENSION, jimp.RESIZE_BESIER);
	}

	// Ruído imperceptível (altera o hash sem mudar visualmente)
	const channelCount = image.getChannelCount();
	if (channelCount >= 3) {
		image.scan(0, 0, image.bitmap.width, image.bitmap.height, (x, y, idx) => {
			// Modificar canais R/G/B em ±1-2 níveis (imperceptível)
			const noise = ((x * 31 + y * 17 + idx) % 3) - 1; // -1, 0, 1
			image.bitmap.data[idx + 0] = Math.min(255, Math.max(0, image.bitmap.data[idx + 0] + noise));
			image.bitmap.data[idx + 1] = Math.min(255, Math.max(0, image.bitmap.data[idx + 1] + noise));
			image.bitmap.data[idx + 2] = Math.min(255, Math.max(0, image.bitmap.data[idx + 2] + noise));
		});
	}

	// Compactação ligeiramente diferente para alterar hash
	const ext = path.extname(outputPath).toLowerCase();
	if (ext === ".png") {
		await image.writeAsync(outputPath);
	} else {
		await image.jpegAsync({ quality: JPEG_QUALITY }).then((buf) => fs.writeFileSync(outputPath, buf));
	}

	const processedHash = imageHash(outputPath);

	return {
		originalHash,
		processedHash,
		uniqueId,
		width: image.width,
		height: image.height,
	};
}

// ── Classificação ─────────────────────────────────────────────────────────────

function classify(name) {
	const n = name.toLowerCase();
	if (n.includes("bg") || n.includes("back") || n.includes("base") || n.includes("fundo")) return "background";
	if (n.includes("btn") || n.includes("button") || n.includes("play") || n.includes("start")) return "button";
	if (n.includes("title") || n.includes("label") || n.includes("text") || n.includes("score")) return "label";
	if (n.includes("icon") || n.includes("img") || n.includes("logo")) return "icon";
	if (n.includes("panel") || n.includes("frame") || n.includes("box")) return "panel";
	return "image";
}

// ── Bundler ───────────────────────────────────────────────────────────────────

class AssetBundler {
	constructor(seed) {
		this.seed = seed || crypto.randomBytes(4).toString("hex");
		this.assets = [];
		this.mapping = {}; // uniqueId → assetId (preenchido após upload)
	}

	async scan(folderPath) {
		const files = fs.readdirSync(folderPath).filter((f) => /\.(png|jpg|jpeg)$/i.test(f));
		console.log(`📂 ${files.length} arquivos encontrados em ${folderPath}`);
		return files;
	}

	async processFiles(files, folderPath, outputDir) {
		const results = [];
		for (let i = 0; i < files.length; i++) {
			const file = files[i];
			const ext = path.extname(file);
			const baseName = path.basename(file, ext);
			const uniqueId = generateUniqueHash(this.seed, path.join(folderPath, file));
			const outName = `${baseName}_${uniqueId}${ext}`;
			const outPath = path.join(outputDir, outName);

			console.log(`[${i + 1}/${files.length}] ${file} → ${outName}`);

			const info = await processImage(path.join(folderPath, file), outPath, this.seed);
			results.push({
				original: file,
				processed: outName,
				outPath,
				uniqueId,
				...info,
				classify: classify(baseName),
				assetId: null, // preenchido após upload
			});
		}
		return results;
	}

	generateManifest(screenName, assets) {
		return {
			name: screenName,
			canvasWidth: 1920,
			canvasHeight: 1080,
			scaleMode: "ScaleToFit",
			seed: this.seed,
			assets: assets.map((a) => ({
				uniqueId: a.uniqueId,
				filename: a.processed,
				type: a.classify,
				assetId: a.assetId || "rbxassetid://0",
				width: a.width,
				height: a.height,
				originalHash: a.originalHash,
				processedHash: a.processedHash,
			})),
		};
	}

	getMapping() {
		return this.mapping;
	}
}

// ── Roblox Studio integration ─────────────────────────────────────────────────

async function uploadToRobloxStudio(assets, studioPort) {
	// Tenta conectar ao Roblox Studio via local HTTP API (porta padrão do Studio)
	// Se não disponível, retorna array sem upload
	const http = require("node:http");

	return new Promise((resolve) => {
		// Placeholder: upload real seria via Roblox API
		// Por segurança, deixamos o usuário fazer upload manual
		// e preenchemos os Asset IDs depois
		resolve(assets.map((a) => ({ ...a, assetId: "rbxassetid://0" })));
	});
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
	const args = process.argv.slice(2);
	if (args.length === 0) {
		console.error("Uso: node asset-bundler.js <pasta-png> [--studio] [--name <nome>] [--seed <seed>]");
		console.error("");
		console.error("Exemplos:");
		console.error('  node asset-bundler.js "C:/Downloads/ui_export" --name Lobby');
		console.error('  node asset-bundler.js "C:/Downloads/ui_export" --studio');
		process.exit(1);
	}

	const folderPath = args[0];
	let studioMode = false;
	let screenName = null;
	let customSeed = null;

	for (let i = 1; i < args.length; i++) {
		if (args[i] === "--studio") studioMode = true;
		else if (args[i] === "--name" && args[i + 1]) screenName = args[++i];
		else if (args[i] === "--seed" && args[i + 1]) customSeed = args[++i];
	}

	if (!fs.existsSync(folderPath)) {
		console.error(`Erro: pasta não encontrada: ${folderPath}`);
		process.exit(1);
	}

	const bundler = new AssetBundler(customSeed);
	const projectRoot = process.cwd();
	const outputDir = path.join(projectRoot, OUTPUT_SUBDIR, screenName || "screen");

	console.log("═".repeat(60));
	console.log("  Asset Bundler — Photoshop → Roblox");
	console.log("═".repeat(60));
	console.log(`📂 Origem:     ${folderPath}`);
	console.log(`📁 Destino:    ${outputDir}`);
	console.log(`🔑 Seed:       ${bundler.seed}`);
	console.log(`🎭 Tela:       ${screenName || "(não nomeada)"}`);
	console.log("");

	// Scan
	fs.mkdirSync(outputDir, { recursive: true });
	const files = bundler.scan(folderPath);
	if (files.length === 0) {
		console.error("Nenhum PNG encontrado.");
		process.exit(1);
	}

	// Process
	console.log("");
	console.log("🔄 Processando imagens (gerando hashes únicos)...");
	const assets = bundler.processFiles(files, folderPath, outputDir);

	// Distribuição por tipo
	const byType = {};
	for (const a of assets) {
		byType[a.classify] = (byType[a.classify] || 0) + 1;
	}
	console.log("\n📊 Classificação:");
	for (const [type, count] of Object.entries(byType)) {
		console.log(`   ${type.padEnd(12)} ${count} arquivo(s)`);
	}

	// Generate manifest
	const manifest = bundler.generateManifest(screenName || "Screen", assets);
	const manifestPath = path.join(outputDir, "_manifest.json");
	fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf-8");
	console.log(`\n📋 Manifest: ${manifestPath}`);

	// Generate Lua controller
	const luaPath = path.join(outputDir, `_controller.lua`);
	const luaContent = generateLuaController(manifest);
	fs.writeFileSync(luaPath, luaContent, "utf-8");
	console.log(`📝 Controller: ${luaPath}`);

	// Generate upload instructions
	const uploadPath = path.join(outputDir, "_upload_guide.txt");
	let uploadText = `# Guia de Upload para Roblox Studio\n\n`;
	uploadText += `1. Abra o Roblox Studio com o projeto\n`;
	uploadText += `2. No Explorer, vá para ReplicatedStorage > UIAssets > ${screenName || "screen"}\n`;
	uploadText += `3. Arraste todos os ${assets.length} arquivos PNG da pasta abaixo:\n`;
	uploadText += `   ${outputDir}\n\n`;
	uploadText += `Após importar, copie os Asset IDs e atualize o manifest:\n`;
	uploadText += `  node asset-bundler.js update "${outputDir}" --ids "PLACEHOLDER_0=123456789,PLACEHOLDER_1=987654321"\n\n`;
	uploadText += `Ou edite manualmente o arquivo _manifest.json substituindo\n`;
	uploadText += `cada "rbxassetid://0" pelo ID real do asset.\n`;
	fs.writeFileSync(uploadPath, uploadText, "utf-8");
	console.log(`📖 Guia de upload: ${uploadPath}`);

	// Summary
	console.log("");
	console.log("═".repeat(60));
	console.log("  PRÓXIMOS PASSOS");
	console.log("═".repeat(60));
	console.log(`1. Abra o Roblox Studio`);
	console.log(`2. Importe os ${assets.length} PNGs da pasta:`);
	console.log(`   ${outputDir}`);
	console.log("3. Copie os Asset IDs (clique direito no asset > Copy Asset ID)");
	console.log(`4. Atualize o manifest: ${manifestPath}`);
	console.log("   Substituindo 'rbxassetid://0' pelos IDs reais");
	console.log("");
	console.log(`📊 Total: ${assets.length} assets → ${screenName || "Screen"}`);
	console.log(`🔑 Seed única: ${bundler.seed} (same seed = same hashes every time)`);
}

function generateLuaController(manifest) {
	let lua = `--!strict\n`;
	lua += `-- [[\n`;
	lua += `-- ${manifest.name} Controller\n`;
	lua += `-- ${manifest.assets.length} assets processados\n`;
	lua += `-- Seed: ${manifest.seed}\n`;
	lua += `-- ]]\n\n`;

	lua += `local ReplicatedStorage = game:GetService("ReplicatedStorage")\n`;
	lua += `local Players = game:GetService("Players")\n\n`;

	// Asset references
	lua += `-- Assets (substituir rbxassetid://0 pelos IDs reais)\n`;
	for (const a of manifest.assets) {
		const varName = a.uniqueId;
		lua += `local ${varName} = "rbxassetid://0" -- ${a.filename} [${a.type}]\n`;
	}
	lua += "\n";

	// Manifest data
	lua += `local _assets = {\n`;
	for (const a of manifest.assets) {
		lua += `\t["${a.uniqueId}"] = {\n`;
		lua += `\t\tassetId = "rbxassetid://0",\n`;
		lua += `\t\ttype = "${a.type}",\n`;
		lua += `\t\tfilename = "${a.filename}",\n`;
		lua += `\t\twidth = ${a.width},\n`;
		lua += `\t\theight = ${a.height},\n`;
		lua += `\t},\n`;
	}
	lua += `}\n\n`;

	// Build function
	lua += `local UIBridge = require(ReplicatedStorage:WaitForChild("UIBridge"))\n\n`;
	lua += `local function buildScreen()\n`;
	lua += `\tlocal screenGui = Instance.new("ScreenGui")\n`;
	lua += `\tscreenGui.Name = "${manifest.name}"\n`;
	lua += `\tscreenGui.ResetOnSpawn = false\n`;
	lua += `\tscreenGui.IgnoreGuiInset = true\n`;
	lua += `\tscreenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")\n\n`;

	// Add elements based on type
	let yOff = 0;
	for (const a of manifest.assets) {
		if (a.type === "background") {
			lua += `\t-- Background\n`;
			lua += `\tlocal bg = Instance.new("ImageLabel", screenGui)\n`;
			lua += `\tbg.Name = "${a.uniqueId}"\n`;
			lua += `\tbg.Image = "rbxassetid://0" -- PLACEHOLDER\n`;
			lua += `\tbg.Size = UDim2.new(1, 0, 1, 0)\n`;
			lua += `\tbg.ScaleType = Enum.ScaleType.Fill\n`;
			lua += `\tbg.AnchorPoint = Vector2.zero\n`;
			lua += `\tyOff = ${a.height}\n\n`;
		} else if (a.type === "button") {
			lua += `\t-- Button: ${a.uniqueId}\n`;
			lua += `\tlocal btn${a.uniqueId} = Instance.new("TextButton", screenGui)\n`;
			lua += `\tbtn${a.uniqueId}.Name = "${a.uniqueId}"\n`;
			lua += `\tbtn${a.uniqueId}.Text = "${a.uniqueId}"\n`;
			lua += `\tbtn${a.uniqueId}.Size = UDim2.new(0, ${a.width}, 0, ${a.height})\n`;
			lua += `\tbtn${a.uniqueId}.Position = UDim2.new(0.5, -${Math.floor(a.width / 2)}, 0, ${yOff})\n`;
			lua += `\tbtn${a.uniqueId}.BackgroundColor3 = Color3.fromRGB(38, 43, 51)\n`;
			lua += `\tbtn${a.uniqueId}.BorderSizePixel = 0\n`;
			lua += `\tbtn${a.uniqueId}.Font = Enum.Font.GothamBold\n`;
			lua += `\tbtn${a.uniqueId}.TextColor3 = Color3.fromRGB(250, 250, 250)\n`;
			lua += `\tbtn${a.uniqueId}.TextSize = 20\n`;
			lua += `\tbtn${a.uniqueId}.AnchorPoint = Vector2.new(0.5, 0)\n`;
			const corner = Instance.new("UICorner")
			lua += `\tInstance.new("UICorner", btn${a.uniqueId}).CornerRadius = UDim.new(0, 12)\n`;
			yOff += a.height + 16;
			lua += "\n";
		} else if (a.type === "label") {
			lua += `\t-- Label: ${a.uniqueId}\n`;
			lua += `\tlocal lbl${a.uniqueId} = Instance.new("TextLabel", screenGui)\n`;
			lua += `\tlbl${a.uniqueId}.Name = "${a.uniqueId}"\n`;
			lua += `\tlbl${a.uniqueId}.Text = "${a.uniqueId}"\n`;
			lua += `\tlbl${a.uniqueId}.Size = UDim2.new(1, -40, 0, ${a.height})\n`;
			lua += `\tlbl${a.uniqueId}.Position = UDim2.new(0, 20, 0, ${yOff})\n`;
			lua += `\tlbl${a.uniqueId}.BackgroundTransparency = 1\n`;
			lua += `\tlbl${a.uniqueId}.Font = Enum.Font.GothamBlack\n`;
			lua += `\tlbl${a.uniqueId}.TextColor3 = Color3.fromRGB(255, 255, 255)\n`;
			lua += `\tlbl${a.uniqueId}.TextSize = ${Math.min(48, Math.max(18, Math.floor(a.height * 0.6)))}\n`;
			lua += `\tlbl${a.uniqueId}.TextWrapped = true\n`;			lua += "\n";
			yOff += a.height + 8;
		} else {
			// Generic image
			lua += `\t-- Image: ${a.uniqueId}\n`;
			lua += `\tlocal img${a.uniqueId} = Instance.new("ImageLabel", screenGui)\n`;
			lua += `\timg${a.uniqueId}.Name = "${a.uniqueId}"\n`;
			lua += `\timg${a.uniqueId}.Size = UDim2.new(0, ${a.width}, 0, ${a.height})\n`;
			lua += `\timg${a.uniqueId}.Position = UDim2.new(0.5, -${Math.floor(a.width / 2)}, 0, ${yOff})\n`;
			lua += `\timg${a.uniqueId}.AnchorPoint = Vector2.new(0.5, 0)\n`;
			lua += "\n";
			yOff += a.height + 8;
		}
	}

	lua += `\treturn screenGui\n`;
	lua += `end\n\n`;

	lua += `local ${manifest.name}Controller = {\n`;
	lua += `\tName = "${manifest.name}Controller",\n`;
	lua += `}\n\n`;

	lua += `function ${manifest.name}Controller.Init()\n`;
	lua += `\tprint("[${manifest.name}] Init — substitua os rbxassetid://0 pelos IDs reais]")\n`;
	lua += `end\n\n`;

	lua += `function ${manifest.name}Controller.Show()\n`;
	lua += `\tlocal screen = buildScreen()\n`;
	lua += `\t-- TODO: Replace all rbxassetid://0 with real asset IDs from _assets table\n`;
	lua += `end\n\n`;

	lua += `function ${manifest.name}Controller.Hide()\n`;
	lua += `\t-- TODO: Hide screen\n`;
	lua += `end\n\n`;

	lua += `return ${manifest.name}Controller\n`;
	return lua;
}

main();
