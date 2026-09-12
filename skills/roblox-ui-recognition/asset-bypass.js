#!/usr/bin/env node
"use strict";

/**
 * asset-bypass.js — Técnicas avançadas de evasão de moderação Roblox
 *
 * Aplica transformações imperceptíveis que alteram o hash SHA-256
 * sem alterar a aparência visual percebida.
 *
 * Uso:
 *   node asset-bypass.js <input.png> --output <output.png> [--technique adaptive]
 *   node asset-bypass.js pasta/ --recursive [--technique all]
 *
 * Técnicas disponíveis:
 *   noise      — Ruído RGB adaptativo (default)
 *   frequency  — Ruído de frequência específica
 *   distort    — Distorção não-linear sutil
 *   quantize   — Redução de bit-depth seletiva
 *   profile    — Shuffle de perfil de cor
 *   all        — Todas as técnicas combinadas
 */

const fs = require("node:fs");
const path = require("path");
const crypto = require("node:crypto");
const sharp = require("sharp");

// ── Config ────────────────────────────────────────────────────────────────────

const CONFIG = {
    maxDimension: 2048,
    quality: 95,
    noiseAmount: 0.015,      // 1.5% de ruído (mais alto que o padrão)
    distortionAmount: 0.002, // 0.2% de distorção
    quantizeLevels: 240,     // Reduzir para 240 níveis (de 256)
    rotationDegrees: 0.3,    // Rotação mínima
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function log(msg, color = "white") {
    const colors = {
        white: "\x1b[37m",
        green: "\x1b[32m",
        yellow: "\x1b[33m",
        red: "\x1b[31m",
        cyan: "\x1b[36m",
        reset: "\x1b[0m"
    };
    console.log(`${colors[color] || colors.white}  ${msg}${colors.reset}`);
}

function genHash(data) {
    return crypto.createHash("sha256").update(data).digest("hex").slice(0, 16);
}

function clamp(val, min = 0, max = 255) {
    return Math.max(min, Math.min(max, val));
}

// ── Técnica 1: Ruído Adaptativo por Regiões ───────────────────────────────────

/**
 * Detecta bordas usando kernel Sobel simples
 * Retorna matriz de força de borda (0-1)
 */
async function detectEdges(buffer) {
    const metadata = await sharp(buffer).metadata();
    const { width, height } = metadata;

    // Processar para grayscale e detectar bordas
    const { data, info } = await sharp(buffer)
        .grayscale()
        .raw()
        .toBuffer({ resolveWithObject: true });

    const edges = new Float32Array(width * height);

    // Kernel Sobel horizontal
    const gx = [-1, 0, 1, -2, 0, 2, -1, 0, 1];
    // Kernel Sobel vertical
    const gy = [-1, -2, -1, 0, 0, 0, 1, 2, 1];

    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            let gxSum = 0, gySum = 0;

            for (let ky = -1; ky <= 1; ky++) {
                for (let kx = -1; kx <= 1; kx++) {
                    const idx = ((y + ky) * width + (x + kx)) * 3;
                    const pixel = data[idx]; // grayscale value

                    gxSum += pixel * gx[(ky + 1) * 3 + (kx + 1)];
                    gySum += pixel * gy[(ky + 1) * 3 + (kx + 1)];
                }
            }

            const magnitude = Math.sqrt(gxSum * gxSum + gySum * gySum);
            edges[y * width + x] = magnitude / (255 * 3); // normalize 0-1
        }
    }

    return edges;
}

/**
 * Aplica ruído adaptativo: menos ruído em bordas, mais em áreas homogêneas
 */
async function adaptiveNoise(inputBuffer, seed = "bypass") {
    log("🎨 Aplicando ruído adaptativo...", "cyan");

    const metadata = await sharp(inputBuffer).metadata();
    const { width, height } = metadata;

    // Detectar bordas
    const edges = await detectEdges(inputBuffer);

    // Processar com ruído adaptativo
    const { data: pixels, info } = await sharp(inputBuffer)
        .raw()
        .toBuffer({ resolveWithObject: true });

    // Semente determinística baseada no seed
    let seedVal = 0;
    for (let i = 0; i < seed.length; i++) {
        seedVal = ((seedVal << 5) - seedVal) + seed.charCodeAt(i);
        seedVal = seedVal & seedVal;
    }

    let rng = seedVal;
    function nextRandom() {
        rng = (rng * 1103515245 + 12345) & 0x7fffffff;
        return rng / 0x7fffffff;
    }

    // Aplicar ruído
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 3;
            const edgeStrength = edges[y * width + x] || 0;

            // Menos ruído em bordas (preservar detalhes), mais em áreas lisas
            const noiseFactor = CONFIG.noiseAmount * (1 - edgeStrength * 0.7);
            const noise = (nextRandom() - 0.5) * 2 * noiseFactor * 255;

            pixels[idx + 0] = clamp(pixels[idx + 0] + noise);     // R
            pixels[idx + 1] = clamp(pixels[idx + 1] + noise);     // G
            pixels[idx + 2] = clamp(pixels[idx + 2] + noise);     // B
        }
    }

    return Buffer.from(pixels);
}

// ── Técnica 2: Ruído de Frequência Específica ─────────────────────────────────

/**
 * Aplica ruído em frequências altas (imperceptível ao olho humano)
 */
async function frequencyNoise(inputBuffer) {
    log("📊 Aplicando ruído de frequência...", "cyan");

    const metadata = await sharp(inputBuffer).metadata();
    const { width, height } = metadata;
    const freq = 0.95; // Frequência alta

    const { data: pixels, info } = await sharp(inputBuffer)
        .raw()
        .toBuffer({ resolveWithObject: true });

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 3;

            // Ond senoidal de alta frequência
            const wave = Math.sin(x * freq * 0.1) * Math.cos(y * freq * 0.1);
            const noise = wave * 1.5; // ±1.5 níveis

            pixels[idx + 0] = clamp(pixels[idx + 0] + noise);
            pixels[idx + 1] = clamp(pixels[idx + 1] + noise);
            pixels[idx + 2] = clamp(pixels[idx + 2] + noise);
        }
    }

    return Buffer.from(pixels);
}

// ── Técnica 3: Distorção Não-Linear Sutil ─────────────────────────────────────

/**
 * Aplica distorção radial mínima (imperceptível)
 */
async function subtleDistortion(inputBuffer, amount = CONFIG.distortionAmount) {
    log("🌀 Aplicando distorção sutil...", "cyan");

    const metadata = await sharp(inputBuffer).metadata();
    const { width, height } = metadata;
    const centerX = width / 2;
    const centerY = height / 2;
    const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);

    // Criar mapa de distorção
    const map = [];
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const dx = x - centerX;
            const dy = y - centerY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const normDist = dist / maxDist;

            // Distorção radial
            const distort = 1 + amount * Math.sin(normDist * Math.PI * 2);
            const newX = centerX + dx * distort;
            const newY = centerY + dy * distort;

            map.push({ x: newX, y: newY });
        }
    }

    // Aplicar warp
    const result = await sharp(inputBuffer)
        .kernel(map, width, height, {
            interpolation: 'bilinear'
        })
        .toBuffer();

    return result;
}

// ── Técnica 4: Redução de Bit-Depth Seletiva ─────────────────────────────────

/**
 * Reduz precisão de cores em áreas menos importantes
 */
async function selectiveQuantize(inputBuffer, levels = CONFIG.quantizeLevels) {
    log("🎚️ Aplicando quantização seletiva...", "cyan");

    const metadata = await sharp(inputBuffer).metadata();
    const { width, height } = metadata;

    const { data: pixels, info } = await sharp(inputBuffer)
        .raw()
        .toBuffer({ resolveWithObject: true });

    const step = 256 / levels;

    for (let i = 0; i < pixels.length; i += 3) {
        // Quantizar apenas se diferença for pequena (preservar gradientes suaves)
        const r = pixels[i];
        const g = pixels[i + 1];
        const b = pixels[i + 2];

        // Verificar se é área homogênea (baixo contraste local)
        const isHomogeneous = Math.abs(r - g) < 10 && Math.abs(g - b) < 10;

        if (isHomogeneous) {
            // Aplicar quantização em áreas homogêneas
            pixels[i] = Math.round(r / step) * step;
            pixels[i + 1] = Math.round(g / step) * step;
            pixels[i + 2] = Math.round(b / step) * step;
        }
        // Áreas com alto contraste (bordas, texto) permanecem intocadas
    }

    return Buffer.from(pixels);
}

// ── Técnica 5: Shuffle de Perfil de Cor ───────────────────────────────────────

/**
 * Altera perfil de cor sem mudar visualmente
 */
async function colorProfileShuffle(inputBuffer) {
    log("🎨 Shuffle de perfil de cor...", "cyan");

    // Sequência de perfis para criar variação
    const profiles = [
        'srgb',
        'adobergb',
        'coloutrhodes',
        'emfcolor',
        'kodakcolor',
        'ecirommrgb',
        'srgb' // volta ao original ao final
    ];

    let result = inputBuffer;

    for (const profile of profiles) {
        try {
            result = await sharp(result)
                .profile(profile)
                .toBuffer();
        } catch (e) {
            // Ignorar perfis não suportados
        }
    }

    return result;
}

// ── Técnica 6: Rotação Micro ─────────────────────────────────────────────────

/**
 * Rotação de ângulo mínimo (imperceptível)
 */
async function microRotation(inputBuffer, degrees = CONFIG.rotationDegrees) {
    log("🔄 Aplicando micro-rotação...", "cyan");

    const result = await sharp(inputBuffer)
        .rotate(degrees)
        .toBuffer();

    return result;
}

// ── Técnica 7: Injeção de Metadata Falsa ─────────────────────────────────────

/**
 * Injeta metadata falsa para confundir detecção por hash
 */
async function injectFakeMetadata(inputBuffer, seed) {
    log("📝 Injetando metadata falsa...", "cyan");

    const fakeEXIF = {
        exif: {
            Make: "GenericCamera",
            Model: "TestDevice",
            DateTime: "2024:01:01 00:00:00",
            GPSAltitude: 0,
            GPSCoordinates: { Latitude: 0, Longitude: 0 },
            Software: "FigmaPS2Roblox Bypass v1.0",
            Rating: 0,
            UserComment: `Seed: ${seed} | ${Date.now()}`
        }
    };

    const result = await sharp(inputBuffer)
        .withExif(fakeEXIF)
        .toBuffer();

    return result;
}

// ── Técnica 8: Bayer Dithering ────────────────────────────────────────────────

/**
 * Adiciona dithering padrão Bayer 4x4 (imperceptível)
 */
async function bayerDither(inputBuffer) {
    log("🔲 Aplicando Bayer dithering...", "cyan");

    // Mapa Bayer 4x4 clássico
    const bayer4x4 = [
        [ 0,  8,  2, 10],
        [12,  4, 14,  6],
        [ 3, 11,  1,  9],
        [15,  7, 13,  5]
    ];

    const metadata = await sharp(inputBuffer).metadata();
    const { width, height } = metadata;

    const { data: pixels, info } = await sharp(inputBuffer)
        .raw()
        .toBuffer({ resolveWithObject: true });

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 3;
            const ditherValue = (bayer4x4[y % 4][x % 4] / 16 - 0.5) * 2; // -1 a +1

            pixels[idx + 0] = clamp(pixels[idx + 0] + ditherValue);
            pixels[idx + 1] = clamp(pixels[idx + 1] + ditherValue);
            pixels[idx + 2] = clamp(pixels[idx + 2] + ditherValue);
        }
    }

    return Buffer.from(pixels);
}

// ── Processador Principal ─────────────────────────────────────────────────────

async function processImage(inputPath, outputDir, technique = "all", seed = null) {
    const fileName = path.basename(inputPath);
    const ext = path.extname(fileName).toLowerCase();
    const baseName = path.basename(fileName, ext);

    // Gerar seed se não fornecido
    if (!seed) {
        seed = crypto.randomBytes(4).toString("hex");
    }

    log(`\n📄 Processando: ${fileName}`);
    log(`   Seed: ${seed}`);

    // Ler imagem original
    const originalBuffer = fs.readFileSync(inputPath);
    const originalHash = genHash(originalBuffer);
    log(`   Hash original: ${originalHash}`);

    let processedBuffer = originalBuffer;

    // Aplicar técnicas
    const techniques = technique === "all"
        ? ["noise", "frequency", "dither", "profile", "metadata"]
        : [technique];

    for (const tech of techniques) {
        try {
            switch (tech) {
                case "noise":
                    processedBuffer = await adaptiveNoise(processedBuffer, seed);
                    break;
                case "frequency":
                    processedBuffer = await frequencyNoise(processedBuffer);
                    break;
                case "distort":
                    processedBuffer = await subtleDistortion(processedBuffer);
                    break;
                case "quantize":
                    processedBuffer = await selectiveQuantize(processedBuffer);
                    break;
                case "profile":
                    processedBuffer = await colorProfileShuffle(processedBuffer);
                    break;
                case "rotate":
                    processedBuffer = await microRotation(processedBuffer);
                    break;
                case "metadata":
                    processedBuffer = await injectFakeMetadata(processedBuffer, seed);
                    break;
                case "dither":
                    processedBuffer = await bayerDither(processedBuffer);
                    break;
            }
        } catch (e) {
            log(`   ⚠️  Técnica ${tech} falhou: ${e.message}`, "yellow");
        }
    }

    // Salvar com nome único
    const uniqueId = crypto.createHash("sha256")
        .update(`${seed}|${inputPath}|${Date.now()}`)
        .digest("hex")
        .slice(0, 12);

    const outputPath = path.join(outputDir, `${baseName}_${uniqueId}${ext}`);
    fs.writeFileSync(outputPath, processedBuffer);

    const processedHash = genHash(processedBuffer);
    log(`   Hash processado: ${processedHash}`);
    log(`   → ${outputPath}`);

    return {
        originalHash,
        processedHash,
        outputPath,
        uniqueId,
        seed
    };
}

// ── Batch Processing ──────────────────────────────────────────────────────────

async function processFolder(inputPath, outputDir, technique = "all") {
    const isFile = fs.statSync(inputPath).isFile();

    if (isFile) {
        return await processImage(inputPath, outputDir, technique);
    }

    // É uma pasta
    const files = fs.readdirSync(inputPath)
        .filter(f => /\.(png|jpg|jpeg)$/i.test(f))
        .map(f => path.join(inputPath, f));

    log(`\n📂 Processando ${files.length} imagens...`, "cyan");

    const results = [];
    for (const file of files) {
        try {
            const result = await processImage(file, outputDir, technique);
            results.push(result);
        } catch (e) {
            log(`   ❌ Falha: ${path.basename(file)} - ${e.message}`, "red");
        }
    }

    return results;
}

// ── CLI Entry Point ───────────────────────────────────────────────────────────

function main() {
    const args = process.argv.slice(2);

    if (args.includes("--help") || args.includes("-h")) {
        console.log(`
asset-bypass.js — Técnicas de evasão de moderação Roblox

Uso:
  node asset-bypass.js <input> [options]

Argumentos:
  <input>           Arquivo PNG/JPG ou pasta com imagens

Opções:
  --output <dir>    Diretório de saída (default: ./bypass_output/)
  --technique <t>   Técnica: noise, frequency, distort, quantize,
                    profile, rotate, metadata, dither, all (default: all)
  --seed <s>        Seed para hash (default: aleatório)
  --recursive       Processar subpastas
  --help, -h        Mostrar ajuda

Exemplos:
  node asset-bypass.js assets/ --technique all
  node asset-bypass.js button.png --technique noise --seed abc123
  node asset-bypass.js assets/ --output ./processed --recursive
`);
        process.exit(0);
    }

    const input = args[0];
    if (!input) {
        console.error("❌ Informe um arquivo ou pasta de entrada");
        process.exit(1);
    }

    let outputDir = "./bypass_output";
    let technique = "all";
    let seed = null;
    let recursive = false;

    for (let i = 1; i < args.length; i++) {
        switch (args[i]) {
            case "--output":
                outputDir = args[++i];
                break;
            case "--technique":
                technique = args[++i];
                break;
            case "--seed":
                seed = args[++i];
                break;
            case "--recursive":
                recursive = true;
                break;
        }
    }

    // Criar diretório de saída
    fs.mkdirSync(outputDir, { recursive: true });

    // Processar
    const startTime = Date.now();
    const result = processFolder(input, outputDir, technique);

    result.then(results => {
        const duration = ((Date.now() - startTime) / 1000).toFixed(2);
        const count = Array.isArray(results) ? results.length : 1;

        console.log(`\n✅ Concluído! ${count} imagem(s) processada(s) em ${duration}s`);
        console.log(`📁 Saída: ${outputDir}`);
    }).catch(err => {
        console.error(`❌ Erro: ${err.message}`);
        process.exit(1);
    });
}

main();
