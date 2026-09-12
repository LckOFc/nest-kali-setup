#!/usr/bin/env node
"use strict";

/**
 * psd-to-roblox — Fluxo completo PSD → Roblox UI.
 *
 * Passo 1: Usar o script Photoshop (export-layers-to-png.jsx) para exportar
 *          as camadas do PSD como PNGs.
 *
 * Passo 2: Executar este script para organizar os PNGs no projeto e gerar
 *          o controller Lua.
 *
 * Uso:
 *   node psd-to-roblox.js <pasta-png-exportados> [--screen <nome>] [--output <pasta-projeto>]
 */

const fs = require("node:fs");
const path = require("path");

const DEFAULT_OUTPUT_SUBDIR = "src/StarterPlayer/StarterPlayerScripts/UIAssets";

// ── Helpers ──────────────────────────────────────────────────────────────────

function resolveProjectRoot(startDir) {
	let dir = startDir;
	for (let i = 0; i < 5; i++) {
		if (fs.existsSync(path.join(dir, "default.project.json"))) return dir;
		const parent = path.dirname(dir);
		if (parent === dir) break;
		dir = parent;
	}
	return startDir;
}

function camelCase(str) {
	return str
		.replace(/[^a-zA-Z0-9]+/g, " ")
		.split(" ")
		.map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
		.join("");
}

function safeVarName(name) {
	return camelCase(name).replace(/^[0-9]/, "_$&");
}

// ── PNG scan ─────────────────────────────────────────────────────────────────

function scanPNGs(dir) {
	const files = fs.readdirSync(dir);
	const pngs = [];
	for (const f of files) {
		if (!f.match(/\.(png|jpg|jpeg)$/i)) continue;
		const full = path.join(dir, f);
		const stat = fs.statSync(full);
		pngs.push({ name: f, path: full, size: stat.size });
	}
	return pngs.sort((a, b) => a.name.localeCompare(b.name));
}

// ── Lua generation ───────────────────────────────────────────────────────────

function generateLua(screenName, pngs) {
	const className = screenName + "ScreenController";
	let lua = `--!strict\n`;
	lua += `-- ${className}\n`;
	lua += `-- Gerado automaticamente de ${pngs.length} assets PNG\n\n`;
	lua += `local ${className} = {\n`;
	lua += `\tName = "${className}",\n`;
	lua += `}\n\n`;

	// Asset constants
	lua += `-- Assets (substituir rbxassetid://0 pelos IDs reais após importação)\n`;
	const assetVars = [];
	for (const png of pngs) {
		const varName = safeVarName(png.name.replace(/\.[^.]+$/, ""));
		assetVars.push(varName);
		lua += `local ${varName} = "rbxassetid://0" -- ${png.name}\n`;
	}
	lua += "\n";

	// Init
	lua += `function ${className}.Init()\n`;
	lua += `\t-- TODO: Upload PNGs no Roblox Studio e substituir os IDs acima\n`;
	for (const v of assetVars) {
		lua += `\t-- ${v}\n`;
	}
	lua += `\t-- TODO: Criar ScreenGui e posicionar elementos\n`;
	lua += `end\n\n`;

	// Start
	lua += `function ${className}.Start()\n`;
	lua += `\t-- TODO: Mostrar/ocultar conforme estado do jogo\n`;
	lua += `end\n\n`;

	// Per-asset show/hide helpers
	for (const png of pngs) {
		const varName = safeVarName(png.name.replace(/\.[^.]+$/, ""));
		const labelName = camelCase(png.name.replace(/\.[^.]+$/, ""));
		lua += `function ${className}.Show${labelName}()\n`;
		lua += `\t-- TODO: Tornar ${varName} visível\n`;
		lua += `end\n\n`;
		lua += `function ${className}.Hide${labelName}()\n`;
		lua += `\t-- TODO: Ocultar ${varName}\n`;
		lua += `end\n\n`;
	}

	lua += `return ${className}\n`;
	return lua;
}

// ── Main ─────────────────────────────────────────────────────────────────────

function main() {
	const args = process.argv.slice(2);
	if (args.length === 0) {
		console.error("Uso: node psd-to-roblox.js <pasta-png> [--screen <nome>] [--output <pasta>]");
		console.error("");
		console.error("Fluxo completo:");
		console.error("  1. No Photoshop: File > Scripts > Browse... → export-ui-to-roblox.jsx");
		console.error("  2. Após exportar: node psd-to-roblox.js <pasta-saída> --screen lobby");
		console.error("");
		console.error("Exemplo:");
		console.error('  node psd-to-roblox.js "C:/Downloads/ui_exported" --screen lobby');
		process.exit(1);
	}

	const pngDir = args[0];
	let screenName = null;
	let outputPath = null;

	for (let i = 1; i < args.length; i++) {
		if (args[i] === "--screen" && args[i + 1]) screenName = args[++i];
		else if (args[i] === "--output" && args[i + 1]) outputPath = args[++i];
	}

	if (!fs.existsSync(pngDir)) {
		console.error(`Erro: pasta não encontrada: ${pngDir}`);
		console.error("Exporte as camadas do PSD primeiro usando o script Photoshop.");
		process.exit(1);
	}

	const projectRoot = outputPath || resolveProjectRoot(process.cwd());
	const assetDir = path.join(projectRoot, DEFAULT_OUTPUT_SUBDIR, screenName || "screen");

	console.log("═".repeat(60));
	console.log("  PSD → Roblox UI Pipeline");
	console.log("═".repeat(60));
	console.log(`📂 Projeto:  ${projectRoot}`);
	console.log(`📁 Assets:   ${assetDir}`);
	console.log(`🎭 Screen:   ${screenName || "(não nomeada)"}`);
	console.log("");

	// Scan PNGs
	const pngs = scanPNGs(pngDir);
	if (pngs.length === 0) {
		console.error("Nenhum PNG encontrado na pasta. Execute o script Photoshop primeiro.");
		process.exit(1);
	}

	console.log(`🖼️  Encontrados ${pngs.length} PNGs:`);
	for (const png of pngs) {
		console.log(`   ${png.name} (${(png.size / 1024).toFixed(1)} KB)`);
	}
	console.log("");

	// Copy PNGs to project
	console.log("📋 Copiando assets para o projeto...");
	fs.mkdirSync(assetDir, { recursive: true });
	for (const png of pngs) {
		const dest = path.join(assetDir, png.name);
		fs.copyFileSync(png.path, dest);
	}
	console.log(`   ✅ ${pngs.length} assets copiados para ${assetDir}\n`);

	// Generate Lua controller
	console.log("📝 Gerando controller Lua...");
	const luaContent = generateLua(screenName || "Screen", pngs);
	const luaFileName = (screenName || "Screen") + "ScreenController.lua";
	const luaPath = path.join(projectRoot, "src/StarterPlayer/StarterPlayerScripts/UI", luaFileName);
	fs.mkdirSync(path.dirname(luaPath), { recursive: true });
	fs.writeFileSync(luaPath, luaContent, "utf-8");
	console.log(`   ✅ ${luaPath}\n`);

	// Summary
	console.log("═".repeat(60));
	console.log("  PRÓXIMOS PASSOS");
	console.log("═".repeat(60));
	console.log("");
	console.log("1️⃣  Abra o Roblox Studio com o projeto");
	console.log(`2️⃣  No Explorer, navegue até: StarterPlayer > StarterPlayerScripts > UIAssets > ${screenName || "screen"}`);
	console.log(`3️⃣  Arraste a pasta ${assetDir} para o Explorer do Roblox (ou use Insert > Image para cada PNG)`);
	console.log("4️⃣  Anote os Asset IDs que o Roblox gerar (clique direito no asset > Copy Asset ID)");
	console.log(`5️⃣  Edite o controller gerado em:`);
	console.log(`      ${luaPath}`);
	console.log("   Substituindo cada 'rbxassetid://0' pelo ID real do asset");
	console.log("");
	console.log("6️⃣  Adicione ao Bootstrap.client.lua:");
	const controllerModule = luaFileName.replace(".lua", "");
	console.log(`   local ${controllerModule} = require(script.Parent.UI.${controllerModule})`);
	console.log(`   ${controllerModule}.Init()`);
	console.log(`   ${controllerModule}.Start()`);
	console.log("");
	console.log(`📊 Resumo: ${pngs.length} assets → ${luaFileName}`);
}

main();
