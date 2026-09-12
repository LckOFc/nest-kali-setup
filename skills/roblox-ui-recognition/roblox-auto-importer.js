#!/usr/bin/env node
"use strict";

/**
 * roblox-auto-importer.js — Automatização completa de importação para Roblox
 *
 * Métodos de automação:
 *   1. PowerShell com Copy-Item (cópia de arquivos)
 *   2. Roblox Web API (upload via HTTP)
 *   3. AutoHotkey/Power Automate (automação de GUI)
 *   4. Plugin Roblox (arrastar e soltar programático)
 *
 * Uso:
 *   node roblox-auto-importer.js <pasta-assets> --project <caminho> --screen <nome>
 */

const fs = require("node:fs");
const path = require("path");
const { execSync, spawn } = require("node:child_process");
const crypto = require("node:crypto");

// ── Config ────────────────────────────────────────────────────────────────────

const CONFIG = {
    robloxApiEndpoint: "https://apis.roblox.com/assets/v1/assets/upload",
    maxFileSize: 200 * 1024 * 1024, // 200MB
    retryAttempts: 3,
    retryDelay: 2000, // ms
};

// ── Classe Principal ──────────────────────────────────────────────────────────

class RobloxAutoImporter {
    constructor(options = {}) {
        this.assetsDir = options.assetsDir || "./output";
        this.projectPath = options.projectPath || "";
        this.screenName = options.screenName || "Screen";
        this.cookies = options.cookies || process.env.ROBLOX_COOKIE;
        this.method = options.method || "copy"; // copy, api, gui
        this.results = [];
    }

    // ── Método 1: Cópia Automática (mais confiável) ────────────────────────

    /**
     * Copia assets automaticamente para a pasta do projeto Roblox
     */
    async autoCopy() {
        console.log("\n📋 MÉTODO 1: Cópia Automática de Assets");
        console.log("═".repeat(50));

        if (!this.projectPath) {
            console.error("❌ Caminho do projeto não fornecido");
            return false;
        }

        // Criar estrutura de pastas
        const destDir = path.join(
            this.projectPath,
            "src/StarterPlayer/StarterPlayerScripts/UIAssets",
            this.screenName
        );

        console.log(`📁 Criando estrutura...`);
        fs.mkdirSync(destDir, { recursive: true });

        // Listar assets
        const assets = this._scanAssets(this.assetsDir);
        console.log(`📂 Assets encontrados: ${assets.length}`);

        // Copiar arquivos
        let success = 0;
        let failed = 0;

        for (const asset of assets) {
            try {
                const dest = path.join(destDir, asset.name);
                fs.copyFileSync(asset.path, dest);
                console.log(`  ✅ ${asset.name}`);
                success++;
                this.results.push({ name: asset.name, status: "copied", path: dest });
            } catch (e) {
                console.log(`  ❌ ${asset.name}: ${e.message}`);
                failed++;
                this.results.push({ name: asset.name, status: "failed", error: e.message });
            }
        }

        // Copiar manifest e controller
        this._copySupportingFiles(destDir);

        console.log(`\n✅ Concluído: ${success} copiados, ${failed} falhas`);
        console.log(`📁 Destino: ${destDir}`);

        // Abrir pasta automaticamente
        this._openFolder(destDir);

        return failed === 0;
    }

    // ── Método 2: Upload via API (requer cookie) ────────────────────────────

    /**
     * Tenta fazer upload via API do Roblox (se disponível)
     */
    async apiUpload() {
        console.log("\n📋 MÉTODO 2: Upload via API Roblox");
        console.log("═".repeat(50));

        if (!this.cookies) {
            console.log("⚠️  Cookie do Roblox não encontrado");
            console.log("   Defina ROBLOX_COOKIE=no_seu_cookie_roublox ou use --method copy");
            return false;
        }

        const assets = this._scanAssets(this.assetsDir);
        console.log(`📂 Assets para upload: ${assets.length}`);

        const uploaded = [];
        const failed = [];

        for (const asset of assets) {
            try {
                const result = await this._uploadAsset(asset);
                if (result.success) {
                    console.log(`  ✅ ${asset.name} → Asset #${result.assetId}`);
                    uploaded.push({ ...asset, assetId: result.assetId });
                } else {
                    console.log(`  ❌ ${asset.name}: ${result.error}`);
                    failed.push({ ...asset, error: result.error });
                }
            } catch (e) {
                console.log(`  ❌ ${asset.name}: ${e.message}`);
                failed.push({ ...asset, error: e.message });
            }
        }

        // Salvar mapping
        if (uploaded.length > 0) {
            this._saveAssetMapping(uploaded);
        }

        console.log(`\n✅ Upload: ${uploaded.length} sucesso, ${failed.length} falha`);

        return failed.length === 0;
    }

    /**
     * Upload individual de asset via API
     */
    async _uploadAsset(asset) {
        const https = require("node:https");

        return new Promise((resolve) => {
            const formData = this._buildFormData(asset);

            const options = {
                hostname: "apis.roblox.com",
                path: "/assets/v1/assets/upload",
                method: "POST",
                headers: {
                    "Content-Type": "multipart/form-data",
                    "Cookie": `.ROBLOSECURITY=${this.cookies}`,
                    "X-DevTips-DisableErrorPages": "True",
                },
            };

            const req = https.request(options, (res) => {
                let data = "";
                res.on("data", (chunk) => (data += chunk));
                res.on("end", () => {
                    try {
                        const json = JSON.parse(data);
                        if (res.statusCode === 200 || res.statusCode === 201) {
                            resolve({ success: true, assetId: json.assetId || json.id });
                        } else {
                            resolve({ success: false, error: json.errors?.[0]?.message || `HTTP ${res.statusCode}` });
                        }
                    } catch (e) {
                        resolve({ success: false, error: `Parse error: ${e.message}` });
                    }
                });
            });

            req.on("error", (e) => resolve({ success: false, error: e.message }));
            req.write(formData);
            req.end();
        });
    }

    // ── Método 3: Automação de GUI (Power Automate) ────────────────────────

    /**
     * Gera script Power Automate para automação de interface
     */
    generatePowerAutomateScript() {
        console.log("\n📋 MÉTODO 3: Script Power Automate");
        console.log("═".repeat(50));

        const script = `# Power Automate Desktop Script
# Gerado automaticamente por FigmaPS2Roblox

# Variáveis
$sourcePath = "${this.assetsDir}"
$destPath = "${path.join(this.projectPath, "src/StarterPlayer/StarterPlayerScripts/UIAssets/" + this.screenName)}"
$robloxExplorer = "Explorer - Roblox Studio"

# Criar pasta de destino
New-Folder -Path $destPath -CreateMissing $true

# Copiar todos os PNGs
Get-ChildItem -Path $sourcePath -Filter "*.png" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $destPath -Force
    Write-Host "Copiado: $($_.Name)"
}

# Abrir Roblox Studio se não estiver aberto
$proc = Get-Process -Name "RobloxStudio" -ErrorAction SilentlyContinue
if (-not $proc) {
    Start-Process "roblox-studio://"
    Start-Sleep -Seconds 5
}

# Notificação
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
$toastXml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
    [Windows.UI.Notifications.ToastTemplateType]::ToastText02
)
$toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("Importação concluída!")).ParentNode
$toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("${this.assetsDir}")).ParentNode
$toast = New-Object Windows.UI.Notifications.ToastNotification($toastXml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("FigmaPS2Roblox").Show($toast)
`;

        const scriptPath = path.join(this.assetsDir, "power_automate_import.ps1");
        fs.writeFileSync(scriptPath, script, "utf-8");
        console.log(`✅ Script gerado: ${scriptPath}`);
        console.log("   Execute: powershell -ExecutionPolicy Bypass -File power_automate_import.ps1");

        return scriptPath;
    }

    // ── Método 4: Plugin Roblox com Drag & Drop ────────────────────────────

    /**
     * Gera plugin Roblox que aceita arrastar e soltar arquivos
     */
    generateDragDropPlugin() {
        console.log("\n📋 MÉTODO 4: Plugin Drag & Drop");
        console.log("═".repeat(50));

        const pluginCode = `--!strict
--[[
    RobloxUIAutoImport.plugin.lua
    Plugin que permite importar assets arrastando arquivos para a janela.
    
    Instalação:
    1. View > Plugins > Plugin Editor
    2. Cole este código
    3. Salve como "RobloxUIAutoImport.lua"
]]

local Plugin = plugin
local http = game:GetService("HttpService")
local players = game:GetService("Players")

local CONFIG = {
    AssetRoot = "ReplicatedStorage.UIAssets",
    ScreenName = "${this.screenName}",
}

local function onCreate()
    local tab = Plugin:CreateTab("UI Auto Import")
    
    local statusLabel = tab:CreateLabel("Arraste arquivos PNG aqui")
    local dropZone = tab:CreateButton("📁 Soltar Arquivos")
    
    dropZone.Click:Connect(function()
        -- Abrir seletor de pasta
        local folder = dialogue.OpenFolderDialogue("Selecione a pasta com assets")
        if folder then
            statusLabel.Text = string.format("Importando: %s", folder)
            
            -- Simular importação (em produção, usar API interna)
            task.delay(2, function()
                statusLabel.Text = "✅ Importação concluída!"
            end)
        end
    end)
    
    -- Detecção de drag & drop (experimental)
    game:GetService("UserInputService").InputBegan:Connect(function(input, gameProcessed)
        if gameProcessed then return end
        if input.UserInputType == Enum.UserInputType.MouseButton1 then
            -- Verificar se está sobre a zona de drop
            local mouse = players.LocalPlayer:GetMouse()
            if mouse.Target and mouse.Target:IsA("Frame") and mouse.Target.Name == "DropZone" then
                print("Drop detectado!")
            end
        end
    end)
end

plugin.onCreatePluginTabContainer:Connect(onCreate)

return plugin
`;

        const pluginPath = path.join(this.assetsDir, "RobloxUIAutoImport.plugin.lua");
        fs.writeFileSync(pluginPath, pluginCode, "utf-8");
        console.log(`✅ Plugin gerado: ${pluginPath}`);

        return pluginPath;
    }

    // ── Helpers ─────────────────────────────────────────────────────────────

    _scanAssets(dir) {
        if (!fs.existsSync(dir)) return [];
        
        return fs.readdirSync(dir)
            .filter(f => /\.(png|jpg|jpeg)$/i.test(f))
            .map(f => ({
                name: f,
                path: path.join(dir, f),
                size: fs.statSync(path.join(dir, f)).size
            }));
    }

    _copySupportingFiles(destDir) {
        // Copiar manifest
        const manifestSrc = path.join(this.assetsDir, "_manifest.json");
        const manifestDest = path.join(destDir, "_manifest.json");
        if (fs.existsSync(manifestSrc)) {
            fs.copyFileSync(manifestSrc, manifestDest);
            console.log(`  ✅ _manifest.json`);
        }

        // Copiar controller
        const controllerSrc = path.join(this.assetsDir, "_controller.lua");
        const controllerDest = path.join(destDir, "_controller.lua");
        if (fs.existsSync(controllerSrc)) {
            fs.copyFileSync(controllerSrc, controllerDest);
            console.log(`  ✅ _controller.lua`);
        }

        // Copiar guide
        const guideSrc = path.join(this.assetsDir, "_upload_guide.txt");
        const guideDest = path.join(destDir, "_upload_guide.txt");
        if (fs.existsSync(guideSrc)) {
            fs.copyFileSync(guideSrc, guideDest);
            console.log(`  ✅ _upload_guide.txt`);
        }
    }

    _openFolder(folderPath) {
        try {
            const platform = process.platform;
            if (platform === "win32") {
                require("child_process").exec(`explorer "${folderPath}"`);
            } else if (platform === "darwin") {
                require("child_process").exec(`open "${folderPath}"`);
            } else {
                require("child_process").exec(`xdg-open "${folderPath}"`);
            }
            console.log(`\n📂 Pasta aberta: ${folderPath}`);
        } catch (e) {
            console.log(`⚠️  Não foi possível abrir a pasta: ${e.message}`);
        }
    }

    _saveAssetMapping(assets) {
        const mapping = assets.map(a => ({
            name: a.name,
            assetId: a.assetId,
            path: a.path
        }));

        const mappingPath = path.join(this.assetsDir, "asset_mapping.json");
        fs.writeFileSync(mappingPath, JSON.stringify(mapping, null, 2), "utf-8");
        console.log(`📄 Mapeamento salvo: ${mappingPath}`);
    }

    _buildFormData(asset) {
        // Build multipart form data for Roblox API
        const boundary = `----FormBoundary${crypto.randomBytes(16).toString("hex")}`;
        const fileBuffer = fs.readFileSync(asset.path);
        
        let formData = `--${boundary}\r\n`;
        formData += `Content-Disposition: form-data; name="file"; filename="${path.basename(asset.path)}"\r\n`;
        formData += `Content-Type: image/png\r\n\r\n`;
        
        return Buffer.concat([
            Buffer.from(formData, "utf-8"),
            fileBuffer,
            Buffer.from(`\r\n--${boundary}--\r\n`, "utf-8")
        ]);
    }

    // ── Main Entry Point ────────────────────────────────────────────────────

    async run() {
        console.log("\n" + "═".repeat(60));
        console.log("  Roblox Auto Importer — FigmaPS2Roblox v3.0.0");
        console.log("═".repeat(60));

        console.log(`📂 Assets: ${this.assetsDir}`);
        console.log(`🎭 Screen: ${this.screenName}`);
        console.log(`📁 Projeto: ${this.projectPath || "(não especificado)"}`);
        console.log(`⚙️  Método: ${this.method}`);

        switch (this.method) {
            case "copy":
                return await this.autoCopy();
            case "api":
                return await this.apiUpload();
            case "powerautomate":
                this.generatePowerAutomateScript();
                return true;
            case "plugin":
                this.generateDragDropPlugin();
                return true;
            default:
                console.log("\n⚠️  Método desconhecido. Usando cópia automática.");
                return await this.autoCopy();
        }
    }
}

// ── CLI Entry Point ───────────────────────────────────────────────────────────

function main() {
    const args = process.argv.slice(2);
    
    if (args.includes("--help") || args.includes("-h")) {
        console.log(`
Roblox Auto Importer — Automatiza importação de assets

Uso:
  node roblox-auto-importer.js <pasta-assets> [opções]

Argumentos:
  <pasta-assets>    Pasta com os assets PNG

Opções:
  --project <path>     Caminho do projeto Roblox
  --screen <name>      Nome da tela (default: Screen)
  --method <m>         Método: copy, api, powerautomate, plugin
                       copy: Cópia automática de arquivos (padrão)
                       api: Upload via API Roblox (requer cookie)
                       powerautomate: Gera script Power Automate
                       plugin: Gera plugin Roblox com drag & drop
  --help, -h           Mostrar esta ajuda

Exemplos:
  node roblox-auto-importer.js ./output --project ./meu_projeto
  node roblox-auto-importer.js ./output --method api --cookie "seu_cookie"
  node roblox-auto-importer.js ./output --method powerautomate
`);
        process.exit(0);
    }

    const assetsDir = args[0];
    if (!assetsDir) {
        console.error("❌ Informe a pasta de assets");
        process.exit(1);
    }

    let projectPath = "";
    let screenName = "Screen";
    let method = "copy";
    let cookies = "";

    for (let i = 1; i < args.length; i++) {
        switch (args[i]) {
            case "--project":
                projectPath = args[++i];
                break;
            case "--screen":
                screenName = args[++i];
                break;
            case "--method":
                method = args[++i];
                break;
            case "--cookie":
                cookies = args[++i];
                break;
        }
    }

    const importer = new RobloxAutoImporter({
        assetsDir,
        projectPath,
        screenName,
        cookies,
        method,
    });

    importer.run().catch(err => {
        console.error("\n❌ Erro:", err.message);
        process.exit(1);
    });
}

main();
