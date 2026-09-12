#!/usr/bin/env node
"use strict";

/**
 * roblox-ui-analyzer — Analisa código Luau/Roblox e extrai estrutura de UI.
 *
 * Uso:
 *   node roblox-ui-analyzer.js <caminho> [--json] [--categories]
 *
 * Examina arquivos .lua/.luau procurando por:
 *   - Instance.new("ScreenGui"), Instance.new("Frame"), etc.
 *   - Variáveis que recebem esses valores
 *   - Chamadas de :Parent, :SetPrimaryPartCFrame, etc. em contexto de UI
 *   - Padrões de controller (Init/Start/Return)
 */

const fs = require("node:fs");
const path = require("node:path");
const { execSync } = require("node:child_process");

// ── Config ──────────────────────────────────────────────────────────────────

const UI_INSTANCE_TYPES = [
	"ScreenGui",
	"Frame",
	"TextLabel",
	"TextButton",
	"ImageButton",
	"ScrollingFrame",
	"UIListLayout",
	"UIPadding",
	"UICorner",
	"UIStroke",
	"UIGridLayout",
	"UIAspectRatioConstraint",
	"UISizeConstraint",
	"UIGradient",
	"TweenInfo",
];

const SCREEN_CATEGORIES = {
	hud: {
		patterns: ["HUD", "Score", "Timer", "Minimap", "HealthBar"],
		description: "Overlay durante gameplay",
	},
	menu: {
		patterns: ["Menu", "Lobby", "Main", "Title"],
		description: "Telas fora do jogo",
	},
	panel: {
		patterns: ["Panel", "Modal", "Dialog", "Popup", "Window"],
		description: "Janelas modais e painéis informativos",
	},
	overlay: {
		patterns: ["Message", "Notification", "Toast", "Banner", "Alert"],
		description: "Mensagens temporárias e feedback",
	},
	inventory: {
		patterns: ["Inventory", "Bag", "Items", "装备"],
		description: "Grid de itens do jogador",
	},
	ranking: {
		patterns: ["Rank", "Leaderboard", "Ranked", "Table"],
		description: "Classificação e rankings",
	},
	shop: {
		patterns: ["Shop", "Store", "Market"],
		description: "Loja de itens",
	},
	gacha: {
		patterns: ["Gacha", "Summon", "Draw"],
		description: "Sistema de gacha/sorteados",
	},
	settings: {
		patterns: ["Settings", "Config", "Options", "Preference"],
		description: "Configurações do jogo",
	},
	result: {
		patterns: ["Result", "Victory", "Defeat", "Winner", "GameEnd"],
		description: "Tela de resultado da partida",
	},
};

// ── Core analysis ───────────────────────────────────────────────────────────

function findLuaFiles(dir) {
	const results = [];
	const entries = fs.readdirSync(dir, { withFileTypes: true });
	for (const entry of entries) {
		const full = path.join(dir, entry.name);
		if (entry.isDirectory()) {
			results.push(...findLuaFiles(full));
		} else if (entry.isFile() && (entry.name.endsWith(".lua") || entry.name.endsWith(".luau"))) {
			results.push(full);
		}
	}
	return results;
}

function extractInstances(content, filePath) {
	const entries = [];
	const lines = content.split("\n");

	for (let i = 0; i < lines.length; i++) {
		const line = lines[i];
		const lineNum = i + 1;

		for (const uiType of UI_INSTANCE_TYPES) {
			const regex = new RegExp(`Instance\\.new\\s*\\(\\s*["\']${uiType}["\']\\s*\\)`, "g");
			let match;
			while ((match = regex.exec(line)) !== null) {
				entries.push({
					type: uiType,
					file: filePath,
					line: lineNum,
					column: match.index + 1,
					raw: match[0],
				});
			}
		}

		// Detect variable assignments: local name = Instance.new(...)
		const assignRegex =
			/^\s*local\s+(\w+)\s*=\s*Instance\.new\s*\(\s*["']([^"']+)["']\s*\)/;
		const assignMatch = assignRegex.exec(line);
		if (assignMatch) {
			const varName = assignMatch[1];
			const instType = assignMatch[2];
			const isUI = UI_INSTANCE_TYPES.includes(instType);
			entries.push({
				type: isUI ? instType : "unknown",
				variable: varName,
				file: filePath,
				line: lineNum,
				instanceType: instType,
				isUI,
				raw: assignMatch[0],
			});
		}

		// Detect screenGui: ScreenGui.Name = "..."
		const nameAssign = /^\s*(\w+)\.Name\s*=\s*["']([^"']+)["']/.exec(line);
		if (nameAssign) {
			const entry = entries.find((e) => e.line === lineNum && e.file === filePath);
			if (entry) {
				entry.name = nameAssign[2];
				entry.variable = nameAssign[1];
			}
		}
	}

	return entries;
}

function classifyByScreen(entries, filePath) {
	const fileName = path.basename(filePath).replace(/\.(lua|luau)$/, "");
	const allNames = entries.map((e) => e.name).filter(Boolean);
	const combined = [...allNames, fileName].join(" ");

	for (const [category, info] of Object.entries(SCREEN_CATEGORIES)) {
		for (const pattern of info.patterns) {
			if (combined.includes(pattern)) {
				return { category, description: info.description };
			}
		}
	}

	// Fallback por tipo de instância
	const hasScreenGui = entries.some((e) => e.type === "ScreenGui");
	const hasButton = entries.some((e) => e.type === "TextButton" || e.type === "ImageButton");
	const hasScrollingFrame = entries.some((e) => e.type === "ScrollingFrame");
	const hasLabel = entries.some((e) => e.type === "TextLabel");

	if (hasScreenGui && hasButton && !hasScrollingFrame) return { category: "menu", description: SCREEN_CATEGORIES.menu.description };
	if (hasScrollingFrame) return { category: "inventory", description: SCREEN_CATEGORIES.inventory.description };
	if (hasLabel && !hasScreenGui) return { category: "overlay", description: SCREEN_CATEGORIES.overlay.description };
	if (hasScreenGui) return { category: "panel", description: SCREEN_CATEGORIES.panel.description };

	return { category: "unknown", description: "Sem classificação automática" };
}

function extractControllers(content, filePath) {
	const controllers = [];
	const lines = content.split("\n");

	let currentController = null;
	for (let i = 0; i < lines.length; i++) {
		const line = lines[i];

		// Detect: local FooController = { Name = "FooController" }
		const ctrlMatch = /local\s+(\w+Controller)\s*=\s*\{[\s\S]*?Name\s*=\s*["'](\w+Controller)["']/.exec(line);
		if (ctrlMatch) {
			currentController = {
				name: ctrlMatch[1],
				className: ctrlMatch[2],
				file: filePath,
				line: i + 1,
				functions: [],
			};
			controllers.push(currentController);
			continue;
		}

		// Detect function definitions within controller
		if (currentController) {
			const funcMatch = /^function\s+\w+\.(Init|Start|Show|Hide|Update|Destroy|Close|Open)\s*\(/.exec(line);
			if (funcMatch) {
				currentController.functions.push({
					name: funcMatch[1],
					line: i + 1,
					full: line.trim(),
				});
			}
			// End of controller block
			if (line.trim() === "return" || line.match(/^\s*return\s+\w+/)) {
				currentController = null;
			}
		}
	}

	return controllers;
}

// ── Output formatters ───────────────────────────────────────────────────────

function formatTextReport(results) {
	const lines = [];
	lines.push("═".repeat(70));
	lines.push("  Roblox UI Analysis Report");
	lines.push("═".repeat(70));
	lines.push("");

	for (const result of results) {
		const relPath = path.relative(process.cwd(), result.file);
		lines.push(`📄 ${relPath}`);
		lines.push(`   Categoria: ${result.classification.category} — ${result.classification.description}`);
		lines.push(`   Instâncias UI: ${result.instances.length}`);
		lines.push("");

		// Group by type
		const byType = {};
		for (const inst of result.instances) {
			if (!byType[inst.type]) byType[inst.type] = [];
			byType[inst.type].push(inst);
		}

		for (const [type, items] of Object.entries(byType)) {
			const names = items
				.map((i) => (i.name ? `"${i.name}"` : i.variable || "<unnamed>"))
				.filter(Boolean)
				.join(", ");
			lines.push(`   [${type}] ${names || "(sem nome)"}`);
		}

		if (result.controllers.length > 0) {
			lines.push("");
			lines.push("   🎮 Controllers:");
			for (const ctrl of result.controllers) {
				lines.push(`     • ${ctrl.className} (${ctrl.file})`);
				for (const fn of ctrl.functions) {
					lines.push(`       - ${fn.name} (line ${fn.line})`);
				}
			}
		}

		lines.push("");
		lines.push("─".repeat(70));
	}

	return lines.join("\n");
}

function formatJSON(results) {
	return JSON.stringify(results, null, 2);
}

// ── Main ────────────────────────────────────────────────────────────────────

function main() {
	const args = process.argv.slice(2);
	if (args.length === 0) {
		console.error("Uso: node roblox-ui-analyzer.js <diretorio> [--json] [--categories]");
		console.error("");
		console.error("Exemplos:");
		console.error("  node roblox-ui-analyzer.js /caminho/projeto");
		console.error("  node roblox-ui-analyzer.js /caminho/projeto --json");
		console.error("  node roblox-ui-analyzer.js /caminho/projeto --categories");
		process.exit(1);
	}

	const targetDir = args[0];
	const flags = args.slice(1);
	const jsonOutput = flags.includes("--json");
	const categoriesOnly = flags.includes("--categories");

	if (!fs.existsSync(targetDir)) {
		console.error(`Erro: diretório não encontrado: ${targetDir}`);
		process.exit(1);
	}

	const files = findLuaFiles(targetDir);
	const results = [];

	for (const file of files) {
		const content = fs.readFileSync(file, "utf-8");
		const instances = extractInstances(content, file);
		if (instances.length === 0) continue;

		const classification = classifyByScreen(instances, file);
		const controllers = extractControllers(content, file);

		results.push({
			file,
			instanceCount: instances.length,
			classification,
			instances,
			controllers,
		});
	}

	if (categoriesOnly) {
		const catMap = {};
		for (const r of results) {
			const rel = path.relative(process.cwd(), r.file);
			catMap[rel] = r.classification;
		}
		if (jsonOutput) {
			console.log(JSON.stringify(catMap, null, 2));
		} else {
			for (const [file, cat] of Object.entries(catMap)) {
				console.log(`${cat.category.padEnd(12)}  ${file}`);
			}
		}
		return;
	}

	if (jsonOutput) {
		console.log(formatJSON(results));
	} else {
		console.log(formatTextReport(results));
	}

	// Summary
	const total = results.length;
	const byCategory = {};
	for (const r of results) {
		byCategory[r.classification.category] = (byCategory[r.classification.category] || 0) + 1;
	}

	console.log("");
	console.log(`Total de arquivos com UI: ${total}`);
	console.log("Categorias encontradas:");
	for (const [cat, count] of Object.entries(byCategory).sort()) {
		console.log(`  ${cat}: ${count}`);
	}
}

main();
