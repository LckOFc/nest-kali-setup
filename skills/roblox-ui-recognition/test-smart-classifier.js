#!/usr/bin/env node
"use strict";

/**
 * test-smart-classifier.js — Teste completo do sistema de classificação inteligente
 *
 * Cria imagens de teste sintéticas e valida a classificação
 */

const fs = require("node:fs");
const path = require("path");
const SmartClassifier = require("./smart-classifier");

const TEST_DIR = "C:/Users/devel/.config/opencode/test-ui-assets";
const CANVAS_W = 1920;
const CANVAS_H = 1080;

// ── Gerador de PNGs sintéticos ────────────────────────────────────────────────

async function createSolidPNG(width, height, r, g, b, alpha = 255) {
	const sharp = require("sharp");
	const buffer = await sharp({
		create: { width, height, channels: alpha < 255 ? 4 : 3, background: { r, g, b, alpha: alpha < 255 ? (255 - alpha) / 255 : 0 } },
	}).png().toBuffer();
	return buffer;
}

async function writeTestImage(filename, width, height, color, alpha) {
	const sharp = require("sharp");
	const buf = await sharp({
		create: { width, height, channels: alpha < 255 ? 4 : 3, background: { r: color.r, g: color.g, b: color.b, alpha: alpha < 255 ? (255 - alpha) / 255 : 0 } },
	}).png().toBuffer();
	fs.writeFileSync(path.join(TEST_DIR, filename), buf);
	console.log(`   ✅ ${filename.padEnd(35)} ${width}×${height} rgb(${color.r},${color.g},${color.b})${alpha < 255 ? ' T' : ''}`);
}

// ── Criar imagens de teste ─────────────────────────────────────────────────────

async function createTestImages() {
	console.log("\n🎨 Criando imagens de teste...");
	fs.mkdirSync(TEST_DIR, { recursive: true });

	const images = [
		["background_main.png",     1920, 1080, { r: 18, g: 20, b: 25 }, 255],
		["bg_menu.png",             1920, 1080, { r: 25, g: 28, b: 35 }, 255],
		["telafundo_01.png",         1920, 1080, { r: 10, g: 15, b: 20 }, 255],
		["btn_play.png",             320,   80,   { r: 35, g: 40, b: 50 }, 255],
		["button_settings.png",      280,   70,   { r: 40, g: 45, b: 55 }, 255],
		["btn_submit.png",           200,   60,   { r: 50, g: 55, b: 65 }, 255],
		["cta_start.png",            350,   85,   { r: 20, g: 25, b: 40 }, 255],
		["title_main.png",           800,   50,   { r: 240, g: 240, b: 245 }, 255],
		["label_subtitle.png",       600,   35,   { r: 200, g: 200, b: 210 }, 255],
		["text_description.png",     500,   30,   { r: 180, g: 180, b: 190 }, 255],
		["score_display.png",        200,   40,   { r: 255, g: 255, b: 255 }, 255],
		["icon_coin.png",             48,   48,   { r: 255, g: 200, b: 50 }, 255],
		["img_avatar.png",            64,   64,   { r: 100, g: 150, b: 255 }, 255],
		["logo_app.png",              80,   80,   { r: 50, g: 100, b: 200 }, 255],
		["icon_heart.png",            32,   32,   { r: 255, g: 50, b: 50 }, 255],
		["panel_card.png",           600,  400,   { r: 30, g: 35, b: 45 }, 255],
		["frame_dialog.png",         500,  350,   { r: 25, g: 30, b: 40 }, 255],
		["container_inventory.png",  700,  450,   { r: 28, g: 32, b: 42 }, 255],
		["bar_health.png",           400,   24,   { r: 60, g: 60, b: 60 }, 255],
		["hp_bar_fill.png",          350,   20,   { r: 50, g: 180, b: 50 }, 255],
		["mana_bar.png",             400,   20,   { r: 30, g: 60, b: 150 }, 255],
		["separator_line.png",       600,    4,   { r: 80, g: 80, b: 90 }, 255],
		["divider_vertical.png",       4,  300,   { r: 80, g: 80, b: 90 }, 255],
		["image_decorative.png",     200,  150,   { r: 128, g: 128, b: 128 }, 255],
		["asset_icon_sword.png",      64,   64,   { r: 200, g: 150, b: 50 }, 255],
		["effect_glow.png",          150,  150,   { r: 100, g: 80, b: 200 }, 128],
		["btn.png",                  150,   50,   { r: 50, g: 50, b: 50 }, 255],
		["x.png",                    100,  100,   { r: 100, g: 100, b: 100 }, 255],
		["12345.png",                 80,   80,   { r: 150, g: 150, b: 150 }, 255],
		["empty.png",                   1,    1,   { r: 0, g: 0, b: 0 }, 255],
	];

	for (const [filename, w, h, color, alpha] of images) {
		await writeTestImage(filename, w, h, color, alpha);
	}

	console.log(`   📁 Total: ${fs.readdirSync(TEST_DIR).filter(f => f.endsWith('.png')).length} imagens\n`);
}

// ── Testes de classificação ───────────────────────────────────────────────────

function runTests() {
	const files = fs.readdirSync(TEST_DIR).filter(f => f.endsWith('.png'));
	if (files.length === 0) {
		console.error("❌ Nenhuma imagem de teste encontrada. Execute o script primeiro.");
		process.exit(1);
	}

	console.log("═".repeat(70));
	console.log("  Smart Classifier — Testes de Classificação");
	console.log("═".repeat(70) + "\n");

	// Prepare assets with mock positions (center of canvas for most, edges for bars)
	const assets = files.map((f, i) => {
		const filePath = path.join(TEST_DIR, f);
		const baseName = f.replace(/\.[^.]+$/, "").toLowerCase();

		// Set realistic positions based on expected type
		let x = CANVAS_W / 2, y = CANVAS_H / 2;
		if (baseName.includes("bar") || baseName.includes("hp") || baseName.includes("mana")) {
			x = 60; y = 40; // HUD corner
		} else if (baseName.includes("title") || baseName.includes("label") || baseName.includes("text")) {
			x = CANVAS_W / 2; y = 100; // Top center
		} else if (baseName.includes("btn") || baseName.includes("button") || baseName.includes("cta")) {
			x = CANVAS_W / 2; y = CANVAS_H / 2 + (i % 3) * 100; // Center, stacked
		}

		return { path: filePath, position: { x, y, width: 0, height: 0 } };
	});

	// Run classification
	const results = SmartClassifier.classifyBatch(assets, {
		canvasW: CANVAS_W,
		canvasH: CANVAS_H,
		verbose: false,
	});

	// Evaluate results
	const EXPECTED = {
		"background_main.png": "background",
		"bg_menu.png": "background",
		"telafundo_01.png": "background",
		"btn_play.png": "button",
		"button_settings.png": "button",
		"btn_submit.png": "button",
		"cta_start.png": "button",
		"title_main.png": "label",
		"label_subtitle.png": "label",
		"text_description.png": "label",
		"score_display.png": "label",
		"icon_coin.png": "icon",
		"img_avatar.png": "icon",
		"logo_app.png": "icon",
		"icon_heart.png": "icon",
		"panel_card.png": "panel",
		"frame_dialog.png": "panel",
		"container_inventory.png": "panel",
		"bar_health.png": "bar",
		"hp_bar_fill.png": "bar",
		"mana_bar.png": "bar",
		"separator_line.png": "separator",
		"divider_vertical.png": "separator",
		"image_decorative.png": "image",
		"asset_icon_sword.png": "icon",
		"effect_glow.png": "effect",
		"btn.png": "button",
		"x.png": "image",
		"12345.png": "image",
		"empty.png": "image",
	};

	const CORRECT = "✅";
	const WRONG = "❌";
	const UNKN  = "⚠️";

	let correct = 0;
	let total = 0;
	const details = [];

	for (const r of results) {
		const expected = EXPECTED[r.name];
		if (!expected) continue;
		total++;
		const isCorrect = r.type === expected;
		if (isCorrect) correct++;
		const mark = isCorrect ? CORRECT : WRONG;
		const conf = (r.confidence * 100).toFixed(1);
		details.push({
			name: r.name,
			actual: r.type,
			expected,
			confidence: r.confidence,
			correct: isCorrect,
			mark,
		});
	}

	// Print results
	console.log(`${CORRECT} = Correto   ${WRONG} = Errado\n`);
	console.log(`${"Arquivo".padEnd(30)} ${"Previsto".padEnd(12)} ${"Obtido".padEnd(12)} ${"Conf.".padEnd(8)} Resultado`);
	console.log("─".repeat(80));

	for (const d of details) {
		console.log(
			`${d.mark} ${d.name.padEnd(28)} ${d.expected.padEnd(12)} ${d.actual.padEnd(12)} ${(d.confidence * 100).toFixed(1).padEnd(7)}%`
		);
	}

	console.log("─".repeat(80));
	const pct = total > 0 ? ((correct / total) * 100).toFixed(1) : 0;
	console.log(`\n📊 Resultado: ${correct}/${total} corretos (${pct}%)`);

	// Category breakdown
	const byType = {};
	for (const d of details) {
		byType[d.expected] = byType[d.expected] || { total: 0, correct: 0 };
		byType[d.expected].total++;
		if (d.correct) byType[d.expected].correct++;
	}

	console.log("\n📈 Precisão por categoria:");
	for (const [type, data] of Object.entries(byType)) {
		const p = ((data.correct / data.total) * 100).toFixed(0);
		console.log(`   ${type.padEnd(12)} ${data.correct}/${data.total} (${p}%)`);
	}

	console.log("\n" + "═".repeat(70) + "\n");

	// Verdict
	if (correct / total >= 0.8) {
		console.log(`🟢 SUCESSO! Taxa de acerto: ${pct}%`);
	} else if (correct / total >= 0.6) {
		console.log(`🟡 PARCIAL: Taxa de acerto ${pct}%. Alguns ajustes podem melhorar.`);
	} else {
		console.log(`🔴 APROXIMAR: Taxa de acerto ${pct}%. Precisa de ajuste nos pesos.`);
	}

	// Save detailed report
	const report = {
		 timestamp: new Date().toISOString(),
		canvasSize: { width: CANVAS_W, height: CANVAS_H },
		total, correct, accuracy: pct,
		byType,
		details,
	};
	const reportPath = path.join(TEST_DIR, "_test_report.json");
	fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
	console.log(`📋 Relatório salvo: ${reportPath}`);

	return correct / total >= 0.7;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
	console.log("\n" + "═".repeat(70));
	console.log("  Smart Classifier — Test Suite");
	console.log("═".repeat(70));

	// Step 1: Create test images
	await createTestImages();

	// Step 2: Run classification tests
	const success = runTests();

	process.exit(success ? 0 : 1);
}

main();
