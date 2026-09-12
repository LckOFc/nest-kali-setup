#!/usr/bin/env node
"use strict";

/**
 * roblox-ui-manage — Gerencia importação de assets UI para Roblox.
 *
 * Comandos:
 *   import-images <pasta-png> [--screen <nome>]
 *   list-assets
 *   update-placeholders <arquivo-lua>
 */

const fs = require("node:fs");
const path = require("node:path");

const PHRASEHOLDER_ID = "rbxassetid://0";

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

async function importImages(pngDir, screenName) {
	const projectRoot = resolveProjectRoot(process.cwd());
	const assetDir = path.join(projectRoot, "src/StarterPlayer/StarterPlayerScripts/UIAssets", screenName || "shared");

	console.log(`📂 Projeto: ${projectRoot}`);
	console.log(`📁 Destino: ${assetDir}`);
	console.log("");

	if (!fs.existsSync(pngDir)) {
		console.error(`Erro: pasta não encontrada: ${pngDir}`);
		process.exit(1);
	}

	const files = fs.readdirSync(pngDir).filter((f) => f.endsWith(".png") || f.endsWith(".jpg") || f.endsWith(".jpeg"));
	console.log(`Encontrados ${files.length} arquivos de imagem`);

	for (const file of files) {
		const src = path.join(pngDir, file);
		const dest = path.join(assetDir, file);
		fs.mkdirSync(path.dirname(dest), { recursive: true });
		fs.copyFileSync(src, dest);
		const stats = fs.statSync(src);
		console.log(`   ✅ ${file} (${(stats.size / 1024).toFixed(1)} KB)`);
	}

	console.log("");
	console.log("Próximo passo:");
	console.log("1. Abra o Roblox Studio");
	console.log(`2. Arraste os arquivos de ${assetDir} para o Explorer (ReplicatedStorage ou StarterGui)`);
	console.log("3. Anote os Asset IDs gerados pelo Roblox");
	console.log("4. Use 'update-placeholders' para atualizar o código Lua automaticamente");
}

function listAssets() {
	const projectRoot = resolveProjectRoot(process.cwd());
	const assetDir = path.join(projectRoot, "src/StarterPlayer/StarterPlayerScripts/UIAssets");

	if (!fs.existsSync(assetDir)) {
		console.log("Nenhum diretório de assets UI encontrado no projeto.");
		return;
	}

	console.log("Assets UI no projeto:");
	console.log("─".repeat(60));

	function walk(dir, depth = 0) {
		const entries = fs.readdirSync(dir, { withFileTypes: true });
		for (const entry of entries) {
			const full = path.join(dir, entry.name);
			const indent = "  ".repeat(depth);
			if (entry.isDirectory()) {
				console.log(`${indent}📁 ${entry.name}/`);
				walk(full, depth + 1);
			} else if (entry.name.endsWith(".png") || entry.name.endsWith(".jpg")) {
				const stats = fs.statSync(full);
				console.log(`${indent}🖼️  ${entry.name} (${(stats.size / 1024).toFixed(1)} KB)`);
			}
		}
	}

	walk(assetDir);
}

function updatePlaceholders(luaFile, assetMap) {
	const filePath = path.resolve(luaFile);
	if (!fs.existsSync(filePath)) {
		console.error(`Erro: arquivo não encontrado: ${filePath}`);
		process.exit(1);
	}

	let content = fs.readFileSync(filePath, "utf-8");
	let updated = false;

	for (const [layerName, assetId] of Object.entries(assetMap)) {
		const escapedName = layerName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
		const regex = new RegExp(`("${PHRASEHOLDER_ID}"[\\s\\S]*?${escapedName}[\\s\\S]*?)`, "g");
		// Simple replacement: find lines with placeholder and the layer name
		const lines = content.split("\n");
		let inBlock = false;
		for (let i = 0; i < lines.length; i++) {
			if (lines[i].includes(layerName) && lines[i + 1] && lines[i + 1].includes(PHRASEHOLDER_ID)) {
				lines[i + 1] = lines[i + 1].replace(PHRASEHOLDER_ID, `rbxassetid://${assetId}`);
				updated = true;
			}
		}
	}

	if (updated) {
		fs.writeFileSync(filePath, lines.join("\n"), "utf-8");
		console.log(`✅ Atualizado: ${filePath}`);
	} else {
		console.log("Nenhuma substituição feita. Verifique se os nomes das camadas correspondem.");
	}
}

function main() {
	const args = process.argv.slice(2);
	if (args.length === 0) {
		console.error("Uso: node roblox-ui-manage.js <comando> [args...]");
		console.error("");
		console.error("Comandos:");
		console.error("  import-images <pasta-png> [--screen <nome>]");
		console.error("  list-assets");
		console.error("  update-placeholders <arquivo.lua> --assets=name=id,name2=id2");
		process.exit(1);
	}

	const command = args[0];

	if (command === "import-images") {
		const pngDir = args[1];
		let screenName = null;
		for (let i = 2; i < args.length; i++) {
			if (args[i] === "--screen" && args[i + 1]) screenName = args[++i];
		}
		importImages(pngDir, screenName);
	} else if (command === "list-assets") {
		listAssets();
	} else if (command === "update-placeholders") {
		const luaFile = args[1];
		const assetsArg = args.find((a) => a.startsWith("--assets="));
		const assetMap = {};
		if (assetsArg) {
			const pairs = assetsArg.slice(9).split(",");
			for (const pair of pairs) {
				const [name, id] = pair.split("=");
				if (name && id) assetMap[name] = id;
			}
		}
		updatePlaceholders(luaFile, assetMap);
	} else {
		console.error(`Comando desconhecido: ${command}`);
		process.exit(1);
	}
}

main();
