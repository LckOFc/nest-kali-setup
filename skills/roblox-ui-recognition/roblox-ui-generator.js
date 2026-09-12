#!/usr/bin/env node
"use strict";

/**
 * roblox-ui-generator — Gera controladores UI boilerplate para Roblox/Luau.
 *
 * Uso:
 *   node roblox-ui-generator.js generate <tipo> <nome> [--screen=<tela>] [--output=<caminho>]
 *   node roblox-ui-generator.js template <tipo>
 *
 * Tipos suportados: hud, menu, panel, overlay, inventory, ranking, shop, gacha, settings, result
 */

const fs = require("node:fs");
const path = require("node:path");

// ── Templates ───────────────────────────────────────────────────────────────

const TEMPLATES = {
	hud: {
		suffix: "HUDController",
		comment: "Manages in-match HUD elements (score, timer, health bars).",
		initBody: `	local ScoreLabel = nil
	local TimerLabel = nil

	-- TODO: Reference existing ScreenGui or create dynamically
	-- local playerGui = game.Players.LocalPlayer:WaitForChild("PlayerGui")
	-- local hudGui = playerGui:FindFirstChild("MatchHUD")
`,
		startBody: `	-- TODO: Connect to match events
	-- local MatchController = require(script.Parent.MatchController)
	-- MatchController.MatchStarted:Connect(function()
	-- 	if hudGui then hudGui.Enabled = true end
	-- end)
	-- MatchController.MatchEnded:Connect(function()
	-- 	if hudGui then hudGui.Enabled = false end
	-- end)
`,
		extraFunctions: [
			{
				name: "UpdateScore",
				params: "(player1Score, player2Score)",
				body: `\t-- TODO: Update score labels\n\tif ScoreLabel then\n\t\tScoreLabel.Text = tostring(player1Score) .. " - " .. tostring(player2Score)\n\tend\n`,
			},
			{
				name: "UpdateTimer",
				params: "(seconds)",
				body: `\t-- TODO: Update timer label\n\tif TimerLabel then\n\t\tlocal mins = math.floor(seconds / 60)\n\t\tlocal secs = seconds % 60\n\t\tTimerLabel.Text = string.format("%02d:%02d", mins, secs)\n\tend\n`,
			},
		],
	},

	menu: {
		suffix: "MenuController",
		comment: "Manages main menu / lobby screens.",
		initBody: `	local menuScreenGui = nil

	-- TODO: Reference or create the main menu ScreenGui
	-- local playerGui = game.Players.LocalPlayer:WaitForChild("PlayerGui")
	-- menuScreenGui = playerGui:WaitForChild("MainMenu")
`,
		startBody: `	-- TODO: Show menu on game start
	-- if menuScreenGui then
	-- 	menuScreenGui.Enabled = true
	-- end
`,
		extraFunctions: [
			{
				name: "Show",
				params: "()",
				body: `\tif menuScreenGui then\n\t\tmenuScreenGui.Enabled = true\n\tend\n`,
			},
			{
				name: "Hide",
				params: "()",
				body: `\tif menuScreenGui then\n\t\tmenuScreenGui.Enabled = false\n\tend\n`,
			},
		],
	},

	panel: {
		suffix: "PanelController",
		comment: "Manages modal panels (shop, gacha, settings popup).",
		initBody: `	local panelScreenGui = nil
	local isOpen = false

	-- TODO: Reference or create the panel ScreenGui
`,
		startBody: `	-- TODO: Bind open/close events from other controllers
`,
		extraFunctions: [
			{
				name: "Open",
				params: "()",
				body: `\tif panelScreenGui and not isOpen then\n\t\tisOpen = true\n\t\tpanelScreenGui.Enabled = true\n\tend\n`,
			},
			{
				name: "Close",
			params: "()",
				body: `\tif panelScreenGui and isOpen then\n\t\tisOpen = false\n\t\tpanelScreenGui.Enabled = false\n\tend\n`,
			},
		],
	},

	overlay: {
		suffix: "OverlayController",
		comment: "Manages temporary overlays (messages, notifications, countdowns).",
		initBody: `	local overlays = {}
	local queue = {}

	-- TODO: Pre-create common overlay components if needed
`,
		startBody: `	-- TODO: Listen for overlay triggers from server remotes
`,
		extraFunctions: [
			{
				name: "ShowMessage",
				params: "(message, duration)",
				body: `\t-- TODO: Create or reuse an overlay label\n\t-- Animate in, wait, animate out, then clean up\n`,
			},
			{
				name: "ShowCountdown",
				params: "(seconds)",
				body: `\t-- TODO: Display countdown overlay\n`,
			},
		],
	},

	inventory: {
		suffix: "InventoryUIController",
		comment: "Manages inventory grid display.",
		initBody: `	local gridFrame = nil
	local itemTemplate = nil

	-- TODO: Reference the inventory ScreenGui and item template
`,
		startBody: `	-- TODO: Connect to inventory data updates
`,
		extraFunctions: [
			{
				name: "RenderItems",
				params: "(items)",
				body: `\t-- TODO: Clear old items and render new grid\n\t-- items: array of { itemId, name, rarity, icon }\n`,
			},
			{
				name: "FilterItems",
				params: "(category)",
				body: `\t-- TODO: Apply category filter to displayed items\n`,
			},
		],
	},

	ranking: {
		suffix: "RankedUIController",
		comment: "Manages leaderboard and rank display.",
		initBody: `	local listFrame = nil
	local rowTemplate = nil

	-- TODO: Reference the ranked ScreenGui
`,
		startBody: `	-- TODO: Connect to ranked data updates
`,
		extraFunctions: [
			{
				name: "UpdateLeaderboard",
				params: "(entries)",
				body: `\t-- TODO: Render ranked entries\n\t-- entries: array of { rank, name, stars, wins }\n`,
			},
		],
	},

	shop: {
		suffix: "ShopUIController",
		comment: "Manages shop item display and purchase flow.",
		initBody: `	local shopGrid = nil
	local currencyLabel = nil

	-- TODO: Reference the shop ScreenGui
`,
		startBody: `	-- TODO: Load shop data from server
`,
		extraFunctions: [
			{
				name: "RefreshShop",
				params: "()",
				body: `\t-- TODO: Fetch and render shop items
`,
			},
		],
	},

	gacha: {
		suffix: "GachaUIController",
		comment: "Manages gacha/summon screen and animation.",
		initBody: `	local gachaScreenGui = nil
	local resultLabel = nil

	-- TODO: Reference the gacha ScreenGui
`,
		startBody: `	-- TODO: Connect to gacha remote events
`,
		extraFunctions: [
			{
				name: "PerformPull",
				params: "(count)",
				body: `\t-- TODO: Trigger gacha animation and show results
`,
			},
		],
	},

	settings: {
		suffix: "SettingsUIController",
		comment: "Manages settings panel (keybinds, graphics, audio).",
		initBody: `	local settingsFrame = nil

	-- TODO: Reference the settings ScreenGui
`,
		startBody: `	-- TODO: Load saved settings on start
`,
		extraFunctions: [
			{
				name: "SaveSettings",
				params: "()",
				body: `\t-- TODO: Persist current settings to server
`,
			},
		],
	},

	result: {
		suffix: "ResultUIController",
		comment: "Manages match result screen (victory/defeat display).",
		initBody: `	local resultScreenGui = nil
	local winnerLabel = nil
	local scoreLabel = nil

	-- TODO: Reference the result ScreenGui
`,
		startBody: `	-- TODO: Listen for match ended events
`,
		extraFunctions: [
			{
				name: "ShowResult",
				params: "(winnerName, score1, score2, isVictory)",
				body: `\t-- TODO: Display result with animation
`,
			},
		],
	},
};

function getTargetDir(outputPath, screen) {
	if (outputPath) return outputPath;
	// Default: look for the project's UI directory
	const defaultPaths = [
		"src/StarterPlayer/StarterPlayerScripts/UI",
		"src/StarterPlayer/StarterPlayerScripts/Controllers",
	];
	for (const p of defaultPaths) {
		if (fs.existsSync(p)) return p;
	}
	return "src/StarterPlayer/StarterPlayerScripts";
}

function generate(type, name, opts) {
	const tpl = TEMPLATES[type];
	if (!tpl) {
		console.error(`Tipo inválido: "${type}"`);
		console.error(`Tipos disponíveis: ${Object.keys(TEMPLATES).join(", ")}`);
		process.exit(1);
	}

	const className = name + tpl.suffix;
	const fileName = className + ".lua";
	const targetDir = getTargetDir(opts.output, opts.screen);

	let body = `--!strict\n`;
	body += `-- ${className} — ${tpl.comment}\n\n`;
	body += `local ${className} = {\n`;
	body += `\tName = "${className}",\n`;
	body += `}\n\n`;
	body += `function ${className}.Init()\n`;
	body += tpl.initBody;
	body += `end\n\n`;
	body += `function ${className}.Start()\n`;
	body += tpl.startBody;
	body += `end\n\n`;

	for (const fn of tpl.extraFunctions) {
		body += `function ${className}.${fn.name}${fn.params}\n`;
		body += fn.body;
		body += `end\n\n`;
	}

	body += `return ${className}\n`;

	const fullPath = path.join(targetDir, fileName);
	fs.mkdirSync(path.dirname(fullPath), { recursive: true });
	fs.writeFileSync(fullPath, body, "utf-8");

	console.log(`✅ Gerado: ${fullPath}`);
	console.log(`   Classe: ${className}`);
	console.log(`   Tela: ${opts.screen || "(não especificada)"}`);
}

function showTemplate(type) {
	const tpl = TEMPLATES[type];
	if (!tpl) {
		console.error(`Tipo inválido: "${type}"`);
		console.error(`Tipos disponíveis: ${Object.keys(TEMPLATES).join(", ")}`);
		process.exit(1);
	}
	console.log(`\n── Template: ${type} ──`);
	console.log(`Descrição: ${tpl.comment}`);
	console.log(`Suffix: ${tpl.suffix}`);
	console.log(`Funções extras: ${tpl.extraFunctions.map((f) => f.name).join(", ")}`);
	console.log();
	console.log("Body Init():");
	console.log(tpl.initBody);
	console.log("Body Start():");
	console.log(tpl.startBody);
}

function main() {
	const args = process.argv.slice(2);
	if (args.length === 0) {
		console.error("Uso: node roblox-ui-generator.js <command> [args...]");
		console.error("");
		console.error("Comandos:");
		console.error("  generate <tipo> <nome> [--screen=<tela>] [--output=<caminho>]");
		console.error("  template <tipo>");
		console.error("");
		console.error("Tipos: " + Object.keys(TEMPLATES).join(", "));
		process.exit(1);
	}

	const command = args[0];

	if (command === "generate") {
		const type = args[1];
		const name = args[2];
		if (!type || !name) {
			console.error("Uso: generate <tipo> <nome> [--screen=<tela>] [--output=<caminho>]");
			process.exit(1);
		}
		const opts = { screen: null, output: null };
		for (let i = 3; i < args.length; i++) {
			if (args[i].startsWith("--screen=")) opts.screen = args[i].slice(9);
			else if (args[i].startsWith("--output=")) opts.output = args[i].slice(9);
		}
		generate(type, name, opts);
	} else if (command === "template") {
		showTemplate(args[1]);
	} else {
		console.error(`Comando desconhecido: ${command}`);
		process.exit(1);
	}
}

main();
