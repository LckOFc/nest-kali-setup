#!/usr/bin/env node
"use strict";

/**
 * install-photoshop-plugin.js — Instala automaticamente o plugin FigmaPS2Roblox
 * no Photoshop ExtendScript Toolkit.
 *
 * Uso:
 *   node install-photoshop-plugin.js [--photoshop-path <caminho>] [--copy-to-profile]
 *
 * O que faz:
 *   1. Copia export-ui-to-roblox.jsx para a pasta de scripts do Photoshop
 *   2. Registra o plugin no menu File > Scripts
 *   3. Mostra instruções de uso
 */

const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");

// ── Paths ─────────────────────────────────────────────────────────────────────

const PLUGIN_NAME = "FigmaPS2Roblox";
const SCRIPT_NAME = "export-ui-to-roblox.jsx";
const SKILL_DIR = __dirname;

function getPhotoshopScriptPaths() {
	const home = os.homedir();
	const platform = process.platform;
	const results = [];

	if (platform === "win32") {
		// Windows: C:\Program Files\Adobe\Adobe Photoshop <version>\Presets\Scripts\
		const photoshopVersions = [
			"Adobe Photoshop 2024", "Adobe Photoshop 2023", "Adobe Photoshop 2022",
			"Adobe Photoshop 2021", "Adobe Photoshop 2020", "Adobe Photoshop 2019",
			"Adobe Photoshop 2018"
		];
		for (const ver of photoshopVersions) {
			const preset = path.join("C:\\Program Files\\Adobe", ver, "Presets", "Scripts");
			if (fs.existsSync(preset)) {
				results.push(preset);
			}
		}
		// Also check Creative Cloud location
		const ccPath = path.join(home, "AppData", "Roaming", "Adobe", "Creative Cloud", "Presets", "Scripts");
		if (fs.existsSync(ccPath)) results.push(ccPath);
	} else if (platform === "darwin") {
		// macOS: /Applications/Adobe Photoshop <version>/Presets/Scripts/
		const photoshopVersions = [
			"Adobe Photoshop 2024", "Adobe Photoshop 2023", "Adobe Photoshop 2022",
			"Adobe Photoshop 2021", "Adobe Photoshop 2020", "Adobe Photoshop 2019"
		];
		for (const ver of photoshopVersions) {
			const preset = path.join("/Applications", ver, "Presets", "Scripts");
			if (fs.existsSync(preset)) results.push(preset);
		}
		// Creative Cloud
		const ccPath = path.join(home, "Library", "Application Support", "Adobe", "Creative Cloud", "Presets", "Scripts");
		if (fs.existsSync(ccPath)) results.push(ccPath);
	} else {
		// Linux
		const presets = [
			path.join(home, ".adobe", "Photoshop", "Scripts"),
			path.join(home, "Applications", "Adobe Photoshop", "Presets", "Scripts"),
		];
		for (const p of presets) {
			if (fs.existsSync(p)) results.push(p);
		}
	}

	return results;
}

function findTargetPath(photoshopPath) {
	if (photoshopPath) {
		return path.join(photoshopPath, "Presets", "Scripts");
	}
	const paths = getPhotoshopScriptPaths();
	if (paths.length > 0) return paths[0];
	return null;
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
	console.log("═".repeat(60));
	console.log("  Photoshop Plugin Installer — FigmaPS2Roblox");
	console.log("═".repeat(60));
	console.log("");

	// Parse args
	let customPath = null;
	let copyToProfile = false;
	for (let i = 1; i < process.argv.length; i++) {
		if (process.argv[i] === "--photoshop-path" && process.argv[i + 1]) {
			customPath = process.argv[++i];
		} else if (process.argv[i] === "--copy-to-profile") {
			copyToProfile = true;
		}
	}

	// Source file
	const sourceFile = path.join(SKILL_DIR, "export-ui-to-roblox.jsx");
	if (!fs.existsSync(sourceFile)) {
		console.error(`❌ Arquivo fonte não encontrado: ${sourceFile}`);
		console.error("   Execute este script a partir do diretório da skill.");
		process.exit(1);
	}

	// Find target
	const targetScriptDir = findTargetPath(customPath);

	if (!targetScriptDir) {
		console.log("⚠️  Nenhuma instalação do Photoshop encontrada automaticamente.");
		console.log("");
		console.log("📋 Instalação manual:");
		console.log(`   Copie o arquivo: ${sourceFile}`);
		console.log("   Para a pasta:    <Photoshop>/Presets/Scripts/");
		console.log("");
		console.log("   Ou no Photoshop: File > Scripts > Browse... → selecione o arquivo");
		console.log("");
		console.log("💡 Dica: Você também pode usar o instalador do Photoshop CC:");
		console.log("   1. Abra o Photoshop");
		console.log("   2. Edit > Preferences > Plug-ins");
		console.log("   3. Marque 'Allow Scripts to Write Files and Access Network'");
		console.log("");
		console.log("═".repeat(60));
		return;
	}

	// Create directory if needed
	if (!fs.existsSync(targetScriptDir)) {
		fs.mkdirSync(targetScriptDir, { recursive: true });
		console.log(`📁 Criando pasta: ${targetScriptDir}`);
	}

	// Copy plugin
	const destFile = path.join(targetScriptDir, SCRIPT_NAME);
	fs.copyFileSync(sourceFile, destFile);
	const stats = fs.statSync(destFile);

	console.log(`✅ Plugin instalado com sucesso!`);
	console.log(`   Fonte: ${sourceFile}`);
	console.log(`   Destino: ${destFile}`);
	console.log(`   Tamanho: ${(stats.size / 1024).toFixed(1)} KB`);
	console.log("");

	// Show usage
	console.log("═".repeat(60));
	console.log("  COMO USAR O PLUGIN");
	console.log("═".repeat(60));
	console.log("");
	console.log("1️⃣  Abra o Photoshop com um documento (PSD/PNG)");
	console.log("2️⃣  Vá em: File > Scripts > FigmaPS2Roblox > Export to Roblox");
	console.log("   (ou File > Scripts > Browse... → selecione o arquivo)");
	console.log("3️⃣  Selecione a pasta de saída");
	console.log("4️⃣  Aguarde a exportação dos assets PNG");
	console.log("");
	console.log("5️⃣  No terminal, execute o pipeline:");
	console.log(`   node complete-pipeline.js "${path.dirname(destFile)}" --name MinhaTela`);
	console.log("");
	console.log("6️⃣  Abra o Roblox Studio e importe os PNGs como assets");
	console.log("7️⃣  Substitua os rbxassetid://0 pelos IDs reais no controller Lua");
	console.log("");
	console.log("═".repeat(60));
}

main();
