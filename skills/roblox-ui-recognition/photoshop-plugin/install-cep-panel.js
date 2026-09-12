#!/usr/bin/env node
"use strict";

/**
 * install-cep-panel.js — Instala/Atualiza o painel CEP do FigmaPS2Roblox
 *
 * Copia os arquivos do plugin para o diretório de extensões do Photoshop.
 *
 * Uso:
 *   node install-cep-panel.js [--photoshop-path <caminho>]
 *   node install-cep-panel.js --install-user    (instala apenas no usuário)
 *   node install-cep-panel.js --install-system  (instala no sistema - precisa admin)
 *
 * Nota: Requer permissão de escrita no diretório do Photoshop.
 */

const fs = require("node:fs");
const path = require("path");
const os = require("node:os");
const { execSync } = require("node:child_process");

// ── Config ────────────────────────────────────────────────────────────────────

const EXTENSION_ID = "com.roblox.phototolua.panel";
const EXTENSION_VERSION = "2.1.0";
const SOURCE_DIR = __dirname;

// ── Detect Photoshop CEP directories ─────────────────────────────────────────

function getCEPPaths() {
  const home = os.homedir();
  const platform = process.platform;
  const results = [];

  if (platform === "win32") {
    // User extensions (no admin needed)
    const userExt = path.join(home, "AppData", "Roaming", "Adobe", "CEP", "extensions");
    if (fs.existsSync(userExt)) results.push({ path: userExt, needAdmin: false });

    // System extensions (need admin)
    const sysExt = "C:\\Program Files\\Adobe\\Common\\Extensions";
    if (fs.existsSync(sysExt)) results.push({ path: sysExt, needAdmin: true });

    // Photoshop 2024+ CEP directory
    const ph24Ext = "C:\\Program Files\\Adobe\\Adobe Photoshop 2024\\Required\\CEP\\extensions";
    if (fs.existsSync(ph24Ext)) results.push({ path: ph24Ext, needAdmin: true });
  } else if (platform === "darwin") {
    // macOS
    const sysExt = "/Library/Application Support/Adobe/CEP/extensions";
    if (fs.existsSync(sysExt)) results.push({ path: sysExt, needAdmin: true });

    const userExt = path.join(home, "Library", "Application Support", "Adobe", "CEP", "extensions");
    if (fs.existsSync(userExt)) results.push({ path: userExt, needAdmin: false });
  } else {
    // Linux
    const extPaths = [
      { p: path.join(home, ".config", "Adobe", "CEP", "extensions"), admin: false },
      { p: "/usr/share/Adobe/CEP/extensions", admin: true },
    ];
    for (const { p, admin } of extPaths) {
      if (fs.existsSync(p)) results.push({ path: p, needAdmin: admin });
    }
  }

  return results;
}

// ── Install ───────────────────────────────────────────────────────────────────

function install(targetDir, options = {}) {
  console.log(`\n📦 Instalando ${EXTENSION_ID} v${EXTENSION_VERSION}...`);
  console.log(`   Destino: ${targetDir}`);

  const extDir = path.join(targetDir, EXTENSION_ID);

  // Create extension directory
  fs.mkdirSync(extDir, { recursive: true });
  fs.mkdirSync(path.join(extDir, "CSXS"), { recursive: true });
  fs.mkdirSync(path.join(extDir, "META-INF"), { recursive: true });

  // Files to copy
  const filesToCopy = [
    { src: "index.html", dst: "index.html" },
    { src: "hostscript.jsx", dst: "hostscript.jsx" },
    { src: "cep.js", dst: "cep.js" },
    { src: "BriefIcon.png", dst: "BriefIcon.png" },
  ];

  let copied = 0;
  for (const { src, dst } of filesToCopy) {
    const srcPath = path.join(SOURCE_DIR, src);
    const dstPath = path.join(extDir, dst);

    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, dstPath);
      console.log(`   ✅ ${src} → ${dst}`);
      copied++;
    } else {
      console.log(`   ⚠️  Não encontrado: ${src}`);
    }
  }

  // Copy CSXS folder
  const csxsSrc = path.join(SOURCE_DIR, "CSXS");
  if (fs.existsSync(csxsSrc)) {
    const csxsDst = path.join(extDir, "CSXS");
    copyDirRecursively(csxsSrc, csxsDst);
    console.log(`   ✅ CSXS/ → CSXS/`);
    copied++;
  }

  // Create META-INF/mimetype
  const mimetype = "application/x-extension-htm";
  fs.writeFileSync(path.join(extDir, "META-INF", "mimetype"), mimetype, "ascii");
  console.log(`   ✅ META-INF/mimetype`);

  // Create META-INF/signatures.xml
  const signaturesXml = `<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://ns.adobe.com/axapplication/1.0/">
  <packageVersion>${EXTENSION_VERSION}</packageVersion>
</manifest>`;
  fs.writeFileSync(path.join(extDir, "META-INF", "signatures.xml"), signaturesXml, "utf8");
  console.log(`   ✅ META-INF/signatures.xml`);

  console.log(`\n✅ Instalado! ${copied} arquivos copiados.`);
  return { success: true, copied };
}

function copyDirRecursively(src, dst) {
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      fs.mkdirSync(dstPath, { recursive: true });
      copyDirRecursively(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  let customPath = null;
  let installMode = "auto"; // auto, user, system

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--photoshop-path" && args[i + 1]) {
      customPath = args[++i];
    } else if (args[i] === "--install-user") {
      installMode = "user";
    } else if (args[i] === "--install-system") {
      installMode = "system";
    } else if (args[i] === "--help" || args[i] === "-h") {
      console.log(`
FigmaPS2Roblox - CEP Panel Installer v${EXTENSION_VERSION}

Usage:
  node install-cep-panel.js              Install to first available directory
  node install-cep-panel.js --install-user   Install to user extensions only
  node install-cep-panel.js --install-system Install to system extensions (need admin)
  node install-cep-panel.js --photoshop-path <path>

Options:
  --help, -h          Show this help
  --install-user      Install to user-level CEP directory (no admin needed)
  --install-system    Install to system-level CEP directory (need admin)
  --photoshop-path    Specify custom CEP directory path
`);
      process.exit(0);
    }
  }

  const cepDirs = getCEPPaths();

  // Filter based on install mode
  let targets = cepDirs;
  if (installMode === "user") {
    targets = cepDirs.filter(d => !d.needAdmin);
  } else if (installMode === "system") {
    targets = cepDirs.filter(d => d.needAdmin);
  }

  const targetDir = customPath || (targets.length > 0 ? targets[0].path : null);

  if (!targetDir) {
    console.log("\n❌ Nenhum diretório de extensões do Photoshop encontrado.");
    console.log("\n📋 Diretórios encontrados:");
    for (const d of cepDirs) {
      console.log(`   ${d.path} ${d.needAdmin ? "(requer admin)" : ""}`);
    }
    console.log("\n💡 Use --install-user para instalar apenas para o usuário.");
    process.exit(1);
  }

  try {
    const result = install(targetDir);
    if (result.success) {
      console.log(`\n📋 Para ativar:`);
      console.log(`   1. Abra o Photoshop`);
      console.log(`   2. Vá em Window > Extensions > FigmaPS2Roblox`);
      console.log(`   Ou: Plugins > FigmaPS2Roblox > Export to Roblox`);
      console.log(`\n💡 Se o painel não aparecer, reinicie o Photoshop.`);
    }
  } catch (e) {
    console.error(`\n❌ Erro: ${e.message}`);
    console.log("\n💡 Tente executar como administrador ou use --install-user");
    process.exit(1);
  }
}

main();
