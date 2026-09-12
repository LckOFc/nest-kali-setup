#!/usr/bin/env node
"use strict";

/**
 * roblox-asset-uploader — Upload real de PNGs para Roblox via API.
 *
 * Usa a API pública do Roblox (web) para fazer upload de imagens
 * e obter Asset IDs únicos, evitando reuploader detection.
 *
 * Pré-requisitos:
 *   - Cookie de sessão Roblox (`.ROBLOSECURITY`)
 *   - node-fetch ou similar
 *
 * Uso:
 *   node roblox-asset-uploader.js upload <pasta-png> --cookie "<cookie>"
 *   node roblox-asset-uploader.js list --cookie "<cookie>"
 */

const fs = require("node:fs");
const path = require("path");
const https = require("node:https");
const crypto = require("node:crypto");

// ── Config ────────────────────────────────────────────────────────────────────

const ROBLOX_API_BASE = "https://apis.roblox.com";
const UPLOAD_ENDPOINT = "/content/upload-v2";

// ── Helpers ───────────────────────────────────────────────────────────────────

function log(msg) {
	console.log(`  ${msg}`);
}

function error(msg) {
	console.error(`  ❌ ${msg}`);
}

// ── Upload functions ──────────────────────────────────────────────────────────

async function uploadImage(filePath, cookie) {
	return new Promise((resolve, reject) => {
		const buffer = fs.readFileSync(filePath);
		const filename = path.basename(filePath);
		const ext = path.extname(filePath).toLowerCase();
		const contentType = ext === ".png" ? "image/png" : "image/jpeg";

		const formData = Buffer.concat([
			Buffer.from(`--boundary\r\n`),
			Buffer.from(`Content-Disposition: form-data; name="file"; filename="${filename}"\r\n`),
			Buffer.from(`Content-Type: ${contentType}\r\n\r\n`),
			buffer,
			Buffer.from(`\r\n--boundary--\r\n`),
		]);

		const options = {
			hostname: "apis.roblox.com",
			path: "/content/upload-v2",
			method: "POST",
			headers: {
				"Content-Type": "multipart/form-data; boundary=boundary",
				"Content-Length": formData.length,
				Cookie: cookie,
				"User-Agent": "Roblox/Win",
			},
		};

		const req = https.request(options, (res) => {
			let data = "";
			res.on("data", (chunk) => (data += chunk));
			res.on("end", () => {
				try {
					const json = JSON.parse(data);
					if (json.data && json.data.assetId) {
						resolve({ success: true, assetId: json.data.assetId, filename });
					} else {
						resolve({ success: false, error: data });
					}
				} catch {
					resolve({ success: false, error: data });
				}
			});
		});

		req.on("error", (e) => reject(e));
		req.write(formData);
		req.end();
	});
}

async function uploadFolder(folderPath, cookie) {
	const files = fs
		.readdirSync(folderPath)
		.filter((f) => /\.(png|jpg|jpeg)$/i.test(f))
		.map((f) => path.join(folderPath, f));

	log(`Encontrados ${files.length} arquivos para upload`);

	const results = [];
	for (let i = 0; i < files.length; i++) {
		const file = files[i];
		log(`[${i + 1}/${files.length}] ${path.basename(file)}`);
		try {
			const result = await uploadImage(file, cookie);
			if (result.success) {
				log(`   ✅ Asset ID: ${result.assetId}`);
				results.push({ filename: path.basename(file), assetId: result.assetId, success: true });
			} else {
				error(`   Falha: ${result.error?.slice(0, 100)}`);
				results.push({ filename: path.basename(file), success: false });
			}
		} catch (e) {
			error(`   Erro: ${e.message}`);
			results.push({ filename: path.basename(file), success: false, error: e.message });
		}
	}

	return results;
}

function listAssets(cookie) {
	// List existing assets (placeholder - requires pagination)
	console.log("Listando assets... (implementação requer paginação)");
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
	const args = process.argv.slice(2);
	if (args.length < 2) {
		console.error("Uso: node roblox-asset-uploader.js <comando> [args...]");
		console.error("");
		console.error("Comandos:");
		console.error("  upload <pasta-png> --cookie '<cookie>'");
		console.error("  list --cookie '<cookie>'");
		console.error("");
		console.error("Obter cookie: copie .ROBLOSECURITY do navegador");
		process.exit(1);
	}

	const command = args[0];
	const folderPath = args[1];
	let cookie = null;

	for (let i = 2; i < args.length; i++) {
		if (args[i] === "--cookie" && args[i + 1]) {
			cookie = args[++i];
		}
	}

	if (!cookie) {
		console.error("Erro: cookie do Roblox é obrigatório (--cookie '<value>')");
		process.exit(1);
	}

	if (command === "upload") {
		if (!fs.existsSync(folderPath)) {
			console.error(`Erro: pasta não encontrada: ${folderPath}`);
			process.exit(1);
		}
		uploadFolder(folderPath, cookie).then((results) => {
			const success = results.filter((r) => r.success).length;
			console.log(`\n✅ ${success}/${results.length} assets enviados com sucesso`);

			// Save mapping
			const mapping = results.filter((r) => r.success).map((r) => ({
				filename: r.filename,
				assetId: r.assetId,
			}));
			const mapPath = path.join(folderPath, "_asset_mapping.json");
			fs.writeFileSync(mapPath, JSON.stringify(mapping, null, 2), "utf-8");
			console.log(`📋 Mapeamento salvo: ${mapPath}`);
		});
	} else if (command === "list") {
		listAssets(cookie);
	} else {
		console.error(`Comando desconhecido: ${command}`);
		process.exit(1);
	}
}

main();
