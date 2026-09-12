#!/usr/bin/env node
"use strict";

/**
 * smart-classifier.js — Classificação inteligente de UI elements
 *
 * Analisa múltiplos sinais para classificar assets de UI:
 *   1. Dimensional: proporção, tamanho absoluto, área
 *   2. Espacial: posição relativa no canvas 1920x1080
 *   3. Colorido: histograma de cores predominantes
 *   4. Semântico: keywords no nome + contexto
 *   5. Relacional: posição em relação a outros elementos
 *
 * Uso:
 *   node smart-classifier.js <arquivo.png> [--canvas-w 1920] [--canvas-h 1080]
 *   node smart-classifier.js <arquivo.png> --verbose
 */

const fs = require("node:fs");
const path = require("path");

// ── Tipos possíveis ───────────────────────────────────────────────────────────

const TYPES = {
	BACKGROUND: "background",
	PANEL: "panel",
	BUTTON: "button",
	LABEL: "label",
	ICON: "icon",
	IMAGE: "image",
	BAR: "bar",
	SEPARATOR: "separator",
	INPUT: "input",
	EFFECT: "effect",
};

// ── Configurações de pesos ────────────────────────────────────────────────────

const WEIGHTS = {
	dimension: 0.25,    // Proporção e tamanho absoluto
	spatial: 0.15,      // Posição no canvas
	color: 0.10,        // Dominante das cores
	semantic: 0.35,     // Keywords no nome (aumentado — nome é forte indicador)
	contextual: 0.10,   // Relação com outros elementos
};

	// ── Thresholds ────────────────────────────────────────────────────────────────

	const THRESHOLDS = {
		backgroundWidthRatio: 0.90,   // Largura > 90% do canvas → background
		backgroundHeightRatio: 0.90,  // Altura > 90% do canvas → background
		buttonMinW: 60,               // Botão precisa ter pelo menos 60px
		buttonMinH: 25,               // Botão precisa ter pelo menos 25px
		buttonMaxW: 600,              // Botão nunca é maior que 600px
		buttonMaxH: 150,              // Botão nunca é mais alto que 150px
		labelMinW: 100,               // Label precisa ter pelo menos 100px
		labelMaxH: 80,                // Label não pode ser alto demais
		barMinW: 50,                  // Barra precisa ter pelo menos 50px de largura
		barMaxH: 60,                  // Barra horizontal não pode ser alta
		barMinH: 50,                  // Barra vertical precisa ter pelo menos 50px de altura
		barMaxW: 60,                  // Barra vertical não pode ser larga
		iconMaxDim: 80,               // Ícone não passa de 80px
		iconMaxArea: 6400,            // Área máxima para ícone (80x80)
		separatorMaxH: 10,            // Separador é fino (≤10px altura)
		separatorMaxW: 10,            // Ou fininho na horizontal
		tinyArea: 100,                // Área muito pequena → sempre "image"
	};

// ── Classificador Principal ───────────────────────────────────────────────────

class SmartClassifier {
	constructor(filePath, options = {}) {
		this.filePath = filePath;
		this.fileName = path.basename(filePath, path.extname(filePath));
		this.canvasW = options.canvasW || 1920;
		this.canvasH = options.canvasH || 1080;
		this.verbose = options.verbose || false;
		this._cache = null;
	}

	// ── Análise dimensional ──────────────────────────────────────────────────

	_getDimensions() {
		if (this._cache && this._cache.dimensions) return this._cache.dimensions;

		try {
			const buf = fs.readFileSync(this.filePath);
			const dims = this._extractDimensions(buf);
			this._cache = this._cache || {};
			this._cache.dimensions = dims;
			return dims;
		} catch {
			return { width: 0, height: 0, ratio: 1, area: 0, isWide: false, isTall: false, isSquare: false };
		}
	}

	_extractDimensions(buf) {
		let width, height;

		// PNG
		if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4E && buf[3] === 0x47) {
			width = buf.readUInt32BE(16);
			height = buf.readUInt32BE(20);
		}
		// JPEG
		else if (buf[0] === 0xFF && buf[1] === 0xD8) {
			let i = 2;
			while (i < buf.length - 1) {
				if (buf[i] === 0xFF && (buf[i + 1] === 0xC0 || buf[i + 1] === 0xC2)) {
					width = buf.readUInt16BE(i + 5);
					height = buf.readUInt16BE(i + 7);
					break;
				}
				i++;
			}
		}

		if (!width || !height) return { width: 0, height: 0, ratio: 1, area: 0, isWide: false, isTall: false, isSquare: false };

		const ratio = width / height;
		const area = width * height;
		const widthRatio = width / this.canvasW;
		const heightRatio = height / this.canvasH;

		return {
			width, height, ratio, area,
			widthRatio, heightRatio,
			isWide: ratio > 2,           // Largamente retangular
			isTall: ratio < 0.5,          // Altamente vertical
			isSquare: ratio >= 0.8 && ratio <= 1.2,
			isFullbleed: widthRatio > THRESHOLDS.backgroundWidthRatio && heightRatio > THRESHOLDS.backgroundHeightRatio,
		};
	}

	_scoreDimensional(dims) {
		const scores = {};
		const w = dims.width || 1;
		const h = dims.height || 1;
		const ratio = dims.ratio || 1;
		const wr = dims.widthRatio || 0;
		const hr = dims.heightRatio || 0;
		const area = dims.area || 1;

		// Tiny images (area < 100) → always "image", no other category qualifies
		if (area < THRESHOLDS.tinyArea) {
			scores[TYPES.IMAGE] = 0.5;
			return scores;
		}

		// Background: ocupa quase toda a tela
		scores[TYPES.BACKGROUND] = wr > 0.9 && hr > 0.9 ? 0.95 :
								   wr > 0.7 && hr > 0.7 ? 0.70 :
								   wr > 0.5 && hr > 0.5 ? 0.40 : 0;

		// Button: médio, largura > altura, nunca muito grande
		if (w >= THRESHOLDS.buttonMinW && w <= THRESHOLDS.buttonMaxW &&
			h >= THRESHOLDS.buttonMinH && h <= THRESHOLDS.buttonMaxH &&
			ratio > 1.1 && area > 2000) {
			// Preferência por botões que são mais largos que altos (ratio > 1.3)
			const widthPreference = ratio > 1.3 ? 1.0 : (ratio > 1.1 ? 0.6 : 0.3);
			// Score baseado em quão "típico" é o tamanho (ideal: ~250x60)
			const idealW = 250, idealH = 60;
			const sizeScore = Math.max(0, 1 - (Math.abs(w - idealW) / idealW + Math.abs(h - idealH) / idealH) * 0.5);
			scores[TYPES.BUTTON] = Math.max(0.35, widthPreference * sizeScore);
		}

		// Panel: grande mas não tela cheia, área significativa
		if (wr > 0.1 && wr < 0.95 && hr > 0.08 && hr < 0.9 && area > 5000) {
			scores[TYPES.PANEL] = Math.max(0.25, 1 - (Math.abs(wr - 0.35) + Math.abs(hr - 0.3)) * 1.5);
		}

		// Icon: pequeno, quadrado, área limitada
		if (w <= THRESHOLDS.iconMaxDim && h <= THRESHOLDS.iconMaxDim && area <= THRESHOLDS.iconMaxArea) {
			const sqScore = dims.isSquare ? 0.7 : 0.4;
			const sizeScore = 1 - Math.min(w, h) / THRESHOLDS.iconMaxDim * 0.3;
			scores[TYPES.ICON] = Math.max(0.05, sqScore * sizeScore);
		}

		// Label: largo e baixo (texto) — requer área suficiente para ser texto legível
		if (w >= THRESHOLDS.labelMinW && h <= THRESHOLDS.labelMaxH && ratio > 1.5 && area > 1500) {
			scores[TYPES.LABEL] = 0.65;
		} else if (w >= THRESHOLDS.labelMinW && h <= 50 && area > 1500) {
			scores[TYPES.LABEL] = 0.4;
		}

		// Bar: horizontal (muito largo, pouco alto) OU vertical (muito alto, pouco largo)
		if (ratio > 5 && h <= THRESHOLDS.barMaxH && w >= THRESHOLDS.barMinW) {
			scores[TYPES.BAR] = 0.85;
		} else if (h / w > 5 && w <= THRESHOLDS.barMaxW && h >= THRESHOLDS.barMinH) {
			scores[TYPES.BAR] = 0.7;
		}

		// Separator: linha muito fina
		if (h <= THRESHOLDS.separatorMaxH && w > 50) {
			scores[TYPES.SEPARATOR] = 0.9;
		} else if (w <= THRESHOLDS.separatorMaxW && h > 50) {
			scores[TYPES.SEPARATOR] = 0.85;
		}

		// Image genérico
		scores[TYPES.IMAGE] = 0.15;

		return scores;
	}

	// ── Análise espacial ──────────────────────────────────────────────────────

	_scoreSpatial(position, dims) {
		const scores = {};
		const px = (position.x || 0) / this.canvasW;
		const py = (position.y || 0) / this.canvasH;
		const pr = position.radius || 0.5; // 0=centro, 1=canto

		// Background: deve cobrir tudo ou estar no canto superior esquerdo
		if (px <= 0.05 && py <= 0.05) {
			scores[TYPES.BACKGROUND] = Math.max(scores[TYPES.BACKGROUND] || 0, 0.6);
		}

		// Buttons: tendem ao centro vertical, distribuídos horizontalmente
		if (py > 0.3 && py < 0.7 && px > 0.2 && px < 0.8) {
			scores[TYPES.BUTTON] = Math.max(scores[TYPES.BUTTON] || 0, 0.3);
		}

		// Labels: topo da tela
		if (py < 0.2) {
			scores[TYPES.LABEL] = Math.max(scores[TYPES.LABEL] || 0, 0.4);
		}

		// Bars/HUD: cantos superiores
		if ((px < 0.1 && py < 0.1) || (px > 0.9 && py < 0.1)) {
			scores[TYPES.BAR] = Math.max(scores[TYPES.BAR] || 0, 0.5);
		}

		// Icons: centro
		if (px > 0.35 && px < 0.65 && py > 0.35 && py < 0.65) {
			scores[TYPES.ICON] = Math.max(scores[TYPES.ICON] || 0, 0.2);
		}

		return scores;
	}

	// ── Análise de cor ─────────────────────────────────────────────────────────

	_analyzeColors() {
		try {
			const buf = fs.readFileSync(this.filePath);
			// Quick heuristic: sample a few bytes from the buffer
			// For a full implementation, we'd use sharp or similar
			const len = buf.length;
			if (len < 100) return { dominant: "unknown", isDark: false, isLight: false, hasTransparency: false };

			// Check for transparency in PNG (byte 8 = color type, 6 = alpha)
			let hasAlpha = false;
			if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4E && buf[3] === 0x47) {
				hasAlpha = (buf[25] & 0x01) !== 0;
			}

			// Sample colors from the middle of the file
			const mid = Math.floor(len / 2);
			const sample = buf.slice(mid, mid + 100);
			let rSum = 0, gSum = 0, bSum = 0, count = 0;

			for (let i = 0; i < sample.length; i += 3) {
				if (i + 2 < sample.length) {
					rSum += sample[i];
					gSum += sample[i + 1];
					bSum += sample[i + 2];
					count++;
				}
			}

			if (count === 0) return { dominant: "unknown", isDark: false, isLight: false, hasTransparency: hasAlpha };

			const r = Math.round(rSum / count);
			const g = Math.round(gSum / count);
			const b = Math.round(bSum / count);
			const brightness = (r + g + b) / 3;

			let dominant = "neutral";
			if (brightness < 60) dominant = "dark";
			else if (brightness < 128) dominant = "medium";
			else if (brightness < 200) dominant = "light";
			else dominant = "very-light";

			return { dominant, isDark: brightness < 128, isLight: brightness >= 200, hasTransparency: hasAlpha };
		} catch {
			return { dominant: "unknown", isDark: false, isLight: false, hasTransparency: false };
		}
	}

	_scoreColor(colorInfo, dims) {
		const scores = {};

		// Backgrounds tendem a ser escuros ou ter cores sólidas
		if (colorInfo.isDark) {
			scores[TYPES.BACKGROUND] = Math.max(scores[TYPES.BACKGROUND] || 0, 0.3);
			scores[TYPES.PANEL] = Math.max(scores[TYPES.PANEL] || 0, 0.15);
		}

		// Botões com cores escuras de fundo + texto claro
		if (colorInfo.isDark && dims.width > 60 && dims.height > 25 && dims.height < 100) {
			scores[TYPES.BUTTON] = Math.max(scores[TYPES.BUTTON] || 0, 0.2);
		}

		// Ícones podem ter cores variadas, mas geralmente não são totalmente escuros
		if (colorInfo.dominant === "neutral" && dims.width < 150 && dims.height < 150) {
			scores[TYPES.ICON] = Math.max(scores[TYPES.ICON] || 0, 0.15);
		}

		// Separadores são frequentemente cinza ou transparentes
		if (colorInfo.hasTransparency && dims.height < 10) {
			scores[TYPES.SEPARATOR] = Math.max(scores[TYPES.SEPARATOR] || 0, 0.3);
		}

		return scores;
	}

	// ── Análise semântica (nome) ───────────────────────────────────────────────

	_scoreSemantic(name) {
		const n = name.toLowerCase();
		const scores = {};

		// Mapeamento direto de keywords → tipos
		const rules = [
			{ patterns: ["background", "bg_", "base_", "fundo", "telafundo", "screen_bg"], type: TYPES.BACKGROUND, weight: 0.9 },
			{ patterns: ["button", "btn", "play_", "start_", "jogar", "click_", "cta_"], type: TYPES.BUTTON, weight: 0.85 },
			{ patterns: ["title", "label", "text_", "name_", "score", "timer", "rank_", "money", "hud_"], type: TYPES.LABEL, weight: 0.8 },
			{ patterns: ["icon", "img_", "logo", "symbol", "badge", "avatar", "emoji", "star"], type: TYPES.ICON, weight: 0.85 },
			{ patterns: ["panel", "frame_", "box_", "card", "container", "painel", "modal"], type: TYPES.PANEL, weight: 0.75 },
			{ patterns: ["bar", "health", "hp_", "mana", "stamina", "progress", "vida_", "energia"], type: TYPES.BAR, weight: 0.8 },
			{ patterns: ["separator", "line_", "divider", "border", "borda"], type: TYPES.SEPARATOR, weight: 0.85 },
			{ patterns: ["input", "field_", "textbox", "edit_", "search_", "campo"], type: TYPES.INPUT, weight: 0.8 },
			{ patterns: ["effect", "fx_", "glow", "shadow", "blur", "particle"], type: TYPES.EFFECT, weight: 0.7 },
		];

		for (const rule of rules) {
			for (const p of rule.patterns) {
				if (n.includes(p)) {
					scores[rule.type] = Math.max(scores[rule.type] || 0, rule.weight);
					break;
				}
			}
		}

		// Heurísticas adicionais por padrão de nome
		if (/^\d+/.test(name)) scores[TYPES.IMAGE] = Math.max(scores[TYPES.IMAGE] || 0, 0.3); // numérico = genérico
		if (name.includes("_") && name.split("_").length > 3) scores[TYPES.IMAGE] = Math.max(scores[TYPES.IMAGE] || 0, 0.2);
		// Nomes curtos/solos sem context → genérico
		if (name.length <= 3) scores[TYPES.IMAGE] = Math.max(scores[TYPES.IMAGE] || 0, 0.4);
		// Keywords genéricas de imagem (substring match, não word boundary)
		if (/(image|img_|generic|decorat|pattern|texture)/.test(n)) {
			scores[TYPES.IMAGE] = Math.max(scores[TYPES.IMAGE] || 0, 0.5);
		}

		return scores;
	}

	// ── Contexto relacional ────────────────────────────────────────────────────

	_scoreContextual(position, neighbors) {
		const scores = {};
		if (!neighbors || neighbors.length === 0) return scores;

		const px = (position.x || 0) / this.canvasW;
		const py = (position.y || 0) / this.canvasH;

		// Se há vários elementos com mesma Y → possivelmente botões empilhados
		let sameYCount = 0;
		let sameXCount = 0;
		for (const nb of neighbors) {
			const nbPx = (nb.x || 0) / this.canvasW;
			const nbPy = (nb.y || 0) / this.canvasH;
			if (Math.abs(nbPy - py) < 0.05) sameYCount++;
			if (Math.abs(nbPx - px) < 0.05) sameXCount++;
		}

		if (sameYCount >= 2) scores[TYPES.BUTTON] = Math.max(scores[TYPES.BUTTON] || 0, 0.2);
		if (sameXCount >= 2) scores[TYPES.LABEL] = Math.max(scores[TYPES.LABEL] || 0, 0.15);

		// Se todos os vizinhos são menores → possivelmente um painel
		const smallerNeighbors = neighbors.filter(n => (n.width || 0) < (position.width || 999) && (n.height || 0) < (position.height || 999));
		if (smallerNeighbors.length > neighbors.length * 0.7) {
			scores[TYPES.PANEL] = Math.max(scores[TYPES.PANEL] || 0, 0.3);
		}

		return scores;
	}

	// ── Classificação final ────────────────────────────────────────────────────

	_classifyInternal(position, neighbors) {
		const dims = this._getDimensions();
		const colorInfo = this._analyzeColors();

		const rawScores = {
			[TYPES.BACKGROUND]: 0,
			[TYPES.BUTTON]: 0,
			[TYPES.LABEL]: 0,
			[TYPES.ICON]: 0,
			[TYPES.PANEL]: 0,
			[TYPES.BAR]: 0,
			[TYPES.SEPARATOR]: 0,
			[TYPES.INPUT]: 0,
			[TYPES.EFFECT]: 0,
			[TYPES.IMAGE]: 0,
		};

		// Coletar scores de cada维度
		const dimScores = this._scoreDimensional(dims);
		const spatialScores = this._scoreSpatial(position, dims);
		const colorScores = this._scoreColor(colorInfo, dims);
		const semanticScores = this._scoreSemantic(this.fileName);
		const contextualScores = this._scoreContextual(position, neighbors);

		// Pesos combinados
		const combined = {};
		for (const type of Object.keys(rawScores)) {
			combined[type] =
				(dimScores[type] || 0) * WEIGHTS.dimension +
				(spatialScores[type] || 0) * WEIGHTS.spatial +
				(colorScores[type] || 0) * WEIGHTS.color +
				(semanticScores[type] || 0) * WEIGHTS.semantic +
				(contextualScores[type] || 0) * WEIGHTS.contextual;
		}

		// Encontrar o tipo com maior score
		let bestType = TYPES.IMAGE;
		let bestScore = 0;
		for (const [type, score] of Object.entries(combined)) {
			if (score > bestScore) {
				bestScore = score;
				bestType = type;
			}
		}

		const result = {
			type: bestType,
			confidence: Math.min(bestScore, 1.0),
			dimensions: dims,
			colorInfo,
			scores: combined,
		};

		if (this.verbose) {
			result.breakdown = { dimScores, spatialScores, colorScores, semanticScores, contextualScores };
		}

		return result;
	}

	/**
	 * Classifica um único asset.
	 * position: { x, y, width, height } em coordenadas do canvas
	 * neighbors: array de { x, y, width, height, type? } de elementos vizinhos
	 */
	classify(position = { x: 0, y: 0, width: 0, height: 0 }, neighbors = []) {
		return this._classifyInternal(position, neighbors);
	}

	/**
	 * Classifica múltiplos assets considerando contexto relacional.
	 * assets: array de { path, position: { x, y, width, height } }
	 */
	static classifyBatch(assets, options = {}) {
		const verbose = options.verbose || false;
		const results = [];

		// Primeira passada: classificar individualmente
		for (let i = 0; i < assets.length; i++) {
			const asset = assets[i];
			const classifier = new SmartClassifier(asset.path, {
				canvasW: options.canvasW,
				canvasH: options.canvasH,
				verbose,
			});
			const result = classifier.classify(asset.position, []);
			result.index = i;
			result.name = path.basename(asset.path);
			results.push(result);
		}

		// Segunda passada: refined com contexto relacional
		for (let i = 0; i < results.length; i++) {
			const r = results[i];
			const neighbors = results
				.filter((_, j) => j !== i)
				.map(nr => ({
					x: nr.dimensions.widthRatio * options.canvasW || 0,
					y: nr.dimensions.heightRatio * options.canvasH || 0,
					width: nr.dimensions.width || 0,
					height: nr.dimensions.height || 0,
					type: nr.type,
				}));

			// FIX: usar o path original completo, não apenas o nome
			const classifier2 = new SmartClassifier(assets[i].path, {
				canvasW: options.canvasW,
				canvasH: options.canvasH,
				verbose,
			});
			const refined = classifier2.classify(
				{ x: r.dimensions.widthRatio * options.canvasW || 0, y: r.dimensions.heightRatio * options.canvasH || 0, width: r.dimensions.width || 0, height: r.dimensions.height || 0 },
				neighbors
			);
			refined.index = r.index;
			refined.name = r.name;
			results[i] = refined;
		}

		return results;
	}

	/**
	 * Print relatório detalhado
	 */
	printReport(results, options = {}) {
		const pad = (s, n) => String(s).padEnd(n);
		console.log("\n" + "═".repeat(80));
		console.log("  Smart Classifier — Análise Inteligente de Assets de UI");
		console.log("═".repeat(80));

		for (const r of results) {
			const confPct = (r.confidence * 100).toFixed(1);
			console.log(`\n📄 ${r.name}`);
			console.log(`   ↳ Tipo: ${r.type.padEnd(12)}  Confiança: ${confPct}%`);
			console.log(`   ↳ Dimensões: ${r.dimensions.width}px × ${r.dimensions.height}px  (ratio: ${r.dimensions.ratio.toFixed(2)})`);
			console.log(`   ↳ Cor: ${r.colorInfo.dominant}  Transp: ${r.colorInfo.hasTransparency}`);

			if (this.verbose || options.verbose) {
				console.log(`   ↳ Top 3 scores:`);
				const sorted = Object.entries(r.scores)
					.sort((a, b) => b[1] - a[1])
					.slice(0, 3);
				for (const [type, score] of sorted) {
					console.log(`       ${type.padEnd(12)} ${score.toFixed(3)}`);
				}
			}
		}
		console.log("\n" + "═".repeat(80) + "\n");
	}
}

// ── CLI ───────────────────────────────────────────────────────────────────────

function main() {
	const args = process.argv.slice(2);
	if (args.length === 0) {
		console.log(`
Smart Classifier — Classificação inteligente de UI assets

Uso:
  node smart-classifier.js <arquivo.png> [--canvas-w 1920] [--canvas-h 1080] [--verbose]
  node smart-classifier.js <arquivo.png> <arquivo2.png> --batch
  node smart-classifier.js . --batch --canvas-w 1920 --canvas-h 1080

Exemplos:
  node smart-classifier.js btn_play.png
  node smart-classifier.js assets/ --batch --verbose
  node smart-classifier.js background.png --canvas-w 1280 --canvas-h 720
`);
		process.exit(0);
	}

	const options = {
		canvasW: 1920,
		canvasH: 1080,
		verbose: false,
		batch: false,
		directory: null,
	};

	const files = [];
	for (let i = 0; i < args.length; i++) {
		switch (args[i]) {
			case "--canvas-w": options.canvasW = parseInt(args[++i]) || 1920; break;
			case "--canvas-h": options.canvasH = parseInt(args[++i]) || 1080; break;
			case "--verbose": options.verbose = true; break;
			case "--batch": options.batch = true; break;
			case "--dir": options.directory = args[++i]; break;
			default:
				if (!args[i].startsWith("-")) files.push(args[i]);
		}
	}

	// Expandir diretório
	if (options.directory) {
		const entries = fs.readdirSync(options.directory);
		for (const e of entries) {
			if (/\.(png|jpg|jpeg)$/i.test(e)) {
				files.push(path.join(options.directory, e));
			}
		}
	}

	if (files.length === 0) {
		console.error("Nenhum arquivo de imagem encontrado.");
		process.exit(1);
	}

	if (options.batch && files.length > 1) {
		const assets = files.map(f => ({
			path: f,
			position: { x: 0, y: 0, width: 0, height: 0 },
		}));
		const results = SmartClassifier.classifyBatch(assets, {
			canvasW: options.canvasW,
			canvasH: options.canvasH,
			verbose: options.verbose,
		});

		// Update positions from actual image dimensions
		for (const r of results) {
			const classifier = new SmartClassifier(r.name, { canvasW: options.canvasW, canvasH: options.canvasH });
			const dims = classifier._getDimensions();
			r.dimensions = dims;
		}

		results.sort((a, b) => b.confidence - a.confidence);
		const classifier = new SmartClassifier("", { verbose: options.verbose });
		classifier.printReport(results, { verbose: options.verbose });

		// Summary
		const byType = {};
		for (const r of results) {
			byType[r.type] = (byType[r.type] || 0) + 1;
		}
		console.log("📊 Resumo por tipo:");
		for (const [type, count] of Object.entries(byType)) {
			console.log(`   ${type.padEnd(12)} ${count} arquivo(s)`);
		}
	} else if (files.length === 1) {
		const c = new SmartClassifier(files[0], { canvasW: options.canvasW, canvasH: options.canvasH, verbose: options.verbose });
		const dims = c._getDimensions();
		const result = c.classify({
			x: 0, y: 0,
			width: dims.width,
			height: dims.height,
		});
		console.log(`\n📄 ${path.basename(files[0])}`);
		console.log(`   Tipo:     ${result.type}`);
		console.log(`   Confiança: ${(result.confidence * 100).toFixed(1)}%`);
		console.log(`   Dimensões: ${dims.width}×${dims.height} (ratio: ${dims.ratio.toFixed(2)})`);
		console.log(`   Cor:      ${result.colorInfo.dominant}`);
		console.log(`   Fullbleed: ${dims.isFullbleed}`);
		if (options.verbose) {
			console.log(`   Scores:`, JSON.stringify(result.scores, null, 2));
		}
	} else {
		console.error("Para múltiplos arquivos, use --batch");
		process.exit(1);
	}
}

// ── Module Export ──────────────────────────────────────────────────────────────
if (require.main === module) {
	main();
}

module.exports = SmartClassifier;
