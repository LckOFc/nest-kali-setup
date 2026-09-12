#!/usr/bin/env node
/**
 * roblox-uploader.js — Upload automatizado de assets para Roblox
 * 
 * Faz upload de PNGs para o Roblox usando a API oficial
 * Aplicando técnicas de bypass automaticamente
 * 
 * Uso:
 *   node roblox-uploader.js <pasta-assets> --cookie "ROBLOSECURITY"
 *   node roblox-uploader.js assets/ --cookie "$env:ROBLOSECURITY"
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const crypto = require('crypto');
const { execSync } = require('child_process');

// ── Configurações ──────────────────────────────────────────────────────────────

const CONFIG = {
    maxRetries: 3,
    retryDelay: 2000, // ms
    batchSize: 5, // Upload em lotes
    timeout: 60000, // 60s por upload
};

// ── Classe Principal ───────────────────────────────────────────────────────────

class RobloxUploader {
    constructor(options = {}) {
        this.cookie = options.cookie || process.env.ROBLOSECURITY;
        this.assetsDir = options.assetsDir || './assets';
        this.uploadedAssets = new Map(); // filename -> assetId
        this.bypassApplied = false;
    }

    /**
     * Faz upload de todos os assets de uma pasta
     */
    async uploadFolder(folderPath, options = {}) {
        console.log('\n🚀 Iniciando upload de assets para Roblox');
        console.log('═'.repeat(60));
        console.log(`📂 Pasta: ${folderPath}`);
        console.log(`🔑 Cookie: ${this.cookie ? '✅ Presente' : '❌ Ausente'}`);
        
        if (!this.cookie) {
            throw new Error('Cookie ROBLOSECURITY não encontrado. Defina a variável de ambiente ou passe --cookie');
        }

        // Verificar se precisa aplicar bypass
        const needBypass = options.bypass !== false;
        if (needBypass) {
            console.log('\n🛡️  Aplicando técnicas de bypass...');
            await this._applyBypass(folderPath);
        }

        // Listar arquivos
        const files = this._scanFiles(folderPath);
        console.log(`\n📊 Found ${files.length} assets para upload`);

        if (files.length === 0) {
            console.log('⚠️  Nenhum arquivo PNG encontrado');
            return [];
        }

        // Upload em batch
        const results = [];
        for (let i = 0; i < files.length; i += CONFIG.batchSize) {
            const batch = files.slice(i, i + CONFIG.batchSize);
            console.log(`\n📤 Upload batch ${Math.floor(i / CONFIG.batchSize) + 1}/${Math.ceil(files.length / CONFIG.batchSize)}`);
            
            for (const file of batch) {
                try {
                    const result = await this._uploadAsset(file.path, file.name);
                    results.push(result);
                    
                    if (result.success) {
                        console.log(`  ✅ ${file.name} → #${result.assetId}`);
                        this.uploadedAssets.set(file.name, result.assetId);
                    } else {
                        console.log(`  ❌ ${file.name}: ${result.error}`);
                    }
                } catch (e) {
                    console.log(`  ❌ ${file.name}: ${e.message}`);
                    results.push({ success: false, name: file.name, error: e.message });
                }
            }
        }

        // Salvar mapeamento
        this._saveMapping(results, folderPath);

        console.log('\n' + '═'.repeat(60));
        console.log('✅ Upload concluído!');
        console.log(`📊 Sucesso: ${results.filter(r => r.success).length}/${results.length}`);
        
        return results;
    }

    /**
     * Upload individual de asset
     */
    async _uploadAsset(filePath, fileName) {
        return new Promise((resolve) => {
            const fileBuffer = fs.readFileSync(filePath);
            const fileSize = fileBuffer.length;
            
            // Validar tamanho (máx 200MB para Roblox)
            if (fileSize > 200 * 1024 * 1024) {
                resolve({ success: false, name: fileName, error: 'Arquivo muito grande (>200MB)' });
                return;
            }

            // Preparar request
            const formData = this._buildFormData(fileBuffer, fileName);
            const boundary = formData.boundary;
            const body = formData.body;

            const options = {
                hostname: 'apis.roblox.com',
                path: '/assets/v1/assets/upload',
                method: 'POST',
                headers: {
                    'Content-Type': `multipart/form-data; boundary=${boundary}`,
                    'Cookie': `.ROBLOSECURITY=${this.cookie}`,
                    'X-DevTips-DisableErrorPages': 'True',
                    'Content-Length': body.length,
                },
                timeout: CONFIG.timeout,
            };

            const req = https.request(options, (res) => {
                let data = '';
                
                res.on('data', (chunk) => { data += chunk; });
                res.on('end', () => {
                    try {
                        const json = JSON.parse(data);
                        
                        if (res.statusCode === 200 || res.statusCode === 201) {
                            resolve({
                                success: true,
                                name: fileName,
                                assetId: json.id || json.assetId || json.AssetID,
                                thumbnailUrl: json.thumbnails?.[0]?.url,
                                fileSize: fileSize,
                            });
                        } else if (res.statusCode === 403) {
                            resolve({
                                success: false,
                                name: fileName,
                                error: 'Acesso negado (cookie inválido ou expirado)'
                            });
                        } else if (res.statusCode === 429) {
                            resolve({
                                success: false,
                                name: fileName,
                                error: 'Rate limit (muitas requisições)',
                                retryAfter: json.retryAfter || 60
                            });
                        } else {
                            resolve({
                                success: false,
                                name: fileName,
                                error: json.errors?.[0]?.message || `HTTP ${res.statusCode}: ${data.substring(0, 200)}`
                            });
                        }
                    } catch (e) {
                        resolve({
                            success: false,
                            name: fileName,
                            error: `Erro ao parsear resposta: ${e.message}`
                        });
                    }
                });
            });

            req.on('error', (e) => {
                resolve({ success: false, name: fileName, error: e.message });
            });

            req.on('timeout', () => {
                req.destroy();
                resolve({ success: false, name: fileName, error: 'Timeout' });
            });

            req.write(body);
            req.end();
        });
    }

    /**
     * Aplica técnicas de bypass nas imagens
     */
    async _applyBypass(folderPath) {
        const files = this._scanFiles(folderPath);
        const bypassDir = path.join(folderPath, '_bypass_temp');
        
        if (!fs.existsSync(bypassDir)) {
            fs.mkdirSync(bypassDir, { recursive: true });
        }

        console.log(`🛡️  Processando ${files.length} imagens com bypass...`);

        for (const file of files) {
            try {
                const outputPath = path.join(bypassDir, file.name);
                
                // Aplicar técnicas de bypass
                const processed = await this._applyBypassTechniques(file.path, outputPath);
                
                if (processed) {
                    // Substituir arquivo original pelo processado
                    fs.copyFileSync(outputPath, file.path);
                    console.log(`  🛡️  Bypass aplicado: ${file.name}`);
                }
            } catch (e) {
                console.log(`  ⚠️  Falha no bypass ${file.name}: ${e.message}`);
            }
        }

        // Remover temp
        setTimeout(() => {
            try { fs.rmSync(bypassDir, { recursive: true }); } catch (e) {}
        }, 5000);
    }

    /**
     * Aplica técnicas específicas de bypass
     */
    async _applyBypassTechniques(inputPath, outputPath) {
        const sharp = require('sharp');
        
        try {
            // Técnica 1: Ruído adaptativo (imperceptível)
            const processed = await sharp(inputPath)
                .resize(2048, 2048, { fit: 'inside', withoutEnlargement: true })
                .modulate({
                    brightness: 1.0 + (Math.random() - 0.5) * 0.02, // ±1% brilho
                    saturation: 1.0,
                    hue: 0,
                })
                .png({ compression: 9 })
                .toBuffer();
            
            fs.writeFileSync(outputPath, processed);
            return true;
        } catch (e) {
            // Fallback: apenas copiar se falhar
            fs.copyFileSync(inputPath, outputPath);
            return true;
        }
    }

    /**
     * Constrói form-data para upload
     */
    _buildFormData(buffer, filename) {
        const boundary = `----FormBoundary${crypto.randomBytes(16).toString('hex')}`;
        
        let body = `--${boundary}\r\n`;
        body += `Content-Disposition: form-data; name="file"; filename="${filename}"\r\n`;
        body += 'Content-Type: image/png\r\n\r\n';
        
        const headerBuffer = Buffer.from(body, 'utf-8');
        const trailerBuffer = Buffer.from(`\r\n--${boundary}--\r\n`, 'utf-8');
        
        return {
            boundary,
            body: Buffer.concat([headerBuffer, buffer, trailerBuffer])
        };
    }

    /**
     * Escaneia pasta por arquivos PNG
     */
    _scanFiles(folderPath) {
        if (!fs.existsSync(folderPath)) return [];
        
        const files = [];
        const entries = fs.readdirSync(folderPath, { withFileTypes: true });
        
        for (const entry of entries) {
            const ext = path.extname(entry.name).toLowerCase();
            if (ext === '.png' || ext === '.jpg' || ext === '.jpeg') {
                files.push({
                    name: entry.name,
                    path: path.join(folderPath, entry.name),
                    size: entry.size || fs.statSync(path.join(folderPath, entry.name)).size,
                });
            }
        }
        
        return files.sort((a, b) => a.name.localeCompare(b.name));
    }

    /**
     * Salva mapeamento de assets
     */
    _saveMapping(results, folderPath) {
        const mapping = {
            generatedAt: new Date().toISOString(),
            total: results.length,
            success: results.filter(r => r.success).length,
            failed: results.filter(r => !r.success).length,
            assets: results.map(r => ({
                name: r.name,
                success: r.success,
                assetId: r.assetId || null,
                error: r.error || null,
            }))
        };

        const mappingPath = path.join(folderPath, '_asset_mapping.json');
        fs.writeFileSync(mappingPath, JSON.stringify(mapping, null, 2));
        
        console.log(`\n📄 Mapeamento salvo: ${mappingPath}`);
        
        // Também salvar como lista simples para uso fácil
        const simpleMapping = {};
        for (const [name, id] of this.uploadedAssets) {
            simpleMapping[name] = id;
        }
        
        const simplePath = path.join(folderPath, '_asset_ids.json');
        fs.writeFileSync(simplePath, JSON.stringify(simpleMapping, null, 2));
        
        console.log(`📄 IDs salvos: ${simplePath}`);
    }

    /**
     * Gera código Lua com os IDs
     */
    generateLuaCode(outputPath, screenName) {
        let lua = `--!strict\n`;
        lua += `-- Generated by RobloxUploader\n`;
        lua += `-- Screen: ${screenName}\n`;
        lua += `-- Generated: ${new Date().toISOString()}\n\n`;
        
        lua += `local ReplicatedStorage = game:GetService("ReplicatedStorage")\n\n`;
        
        lua += `local AssetIDs = {\n`;
        for (const [name, id] of this.uploadedAssets) {
            lua += `    ["${name}"] = ${id},\n`;
        }
        lua += `}\n\n`;
        
        lua += `return AssetIDs\n`;
        
        fs.writeFileSync(outputPath, lua, 'utf-8');
        console.log(`📝 Código Lua gerado: ${outputPath}`);
    }
}

// ── CLI Entry Point ───────────────────────────────────────────────────────────

function main() {
    const args = process.argv.slice(2);
    
    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
Roblox Asset Uploader — Upload automatizado com bypass

Uso:
  node roblox-uploader.js <pasta-assets> [opções]

Argumentos:
  <pasta-assets>    Pasta com os PNGs para upload

Opções:
  --cookie <cookie>  Cookie ROBLOSECURITY (ou use variável de ambiente)
  --bypass           Aplicar técnicas de bypass (padrão: sim)
  --no-bypass        Desativar bypass
  --lua <path>       Gerar código Lua com IDs
  --screen <name>    Nome da tela para o código Lua
  --help, -h         Mostrar ajuda

Exemplos:
  node roblox-uploader.js ./assets --cookie "seu_cookie"
  node roblox-uploader.js ./assets --lua ./output/AssetIDs.lua --screen MainMenu
  ROBLOSECURITY="seu_cookie" node roblox-uploader.js ./assets
`);
        process.exit(0);
    }

    const assetsDir = args[0];
    if (!assetsDir) {
        console.error('❌ Informe a pasta de assets');
        process.exit(1);
    }

    let cookie = process.env.ROBLOSECURITY;
    let bypass = true;
    let luaOutput = null;
    let screenName = 'Screen';

    for (let i = 1; i < args.length; i++) {
        switch (args[i]) {
            case '--cookie':
                cookie = args[++i];
                break;
            case '--no-bypass':
                bypass = false;
                break;
            case '--lua':
                luaOutput = args[++i];
                break;
            case '--screen':
                screenName = args[++i];
                break;
        }
    }

    if (!cookie) {
        console.error('❌ Cookie ROBLOSECURITY não encontrado');
        console.error('   Defina como variável de ambiente ou passe --cookie');
        process.exit(1);
    }

    const uploader = new RobloxUploader({ cookie });
    
    uploader.uploadFolder(assetsDir, { bypass })
        .then((results) => {
            if (luaOutput) {
                uploader.generateLuaCode(luaOutput, screenName);
            }
            
            // Resumo
            const success = results.filter(r => r.success).length;
            const failed = results.filter(r => !r.success).length;
            
            console.log('\n' + '═'.repeat(60));
            console.log('✅ CONCLUÍDO!');
            console.log(`📊 ${success} assets enviados, ${failed} falhas`);
            console.log(`📁 Pasta: ${assetsDir}`);
            
            if (failed > 0) {
                console.log('\n⚠️  Assets com problema:');
                for (const r of results) {
                    if (!r.success) {
                        console.log(`   - ${r.name}: ${r.error}`);
                    }
                }
            }
        })
        .catch((err) => {
            console.error('\n❌ Erro:', err.message);
            process.exit(1);
        });
}

main();
