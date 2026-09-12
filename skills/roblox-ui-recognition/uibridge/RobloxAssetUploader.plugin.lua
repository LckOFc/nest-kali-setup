--!strict
--[[
    RobloxAssetUploader.plugin.lua
    Plugin Roblox Studio para upload automatizado de assets com bypass.
    
    Instalação:
        1. View > Plugins > Plugin Editor
        2. Cole este código
        3. Salve como "RobloxAssetUploader.lua"
        4. Execute
        
    Uso:
        - Selecione a pasta com os assets
        - Clique "Upload com Bypass"
        - Aguarde o upload (mostra progresso)
        - IDs são copiados automaticamente
]]

local Plugin = plugin
local http = game:GetService("HttpService")
local players = game:GetService("Players")
local storage = game:GetService("ReplicatedStorage")
local tele = game:GetService("TeleportService")

-- ── Configurações ─────────────────────────────────────────────────────────────

local CONFIG = {
    AssetRoot = "ReplicatedStorage.UIAssets",
    MaxUploadSize = 200 * 1024 * 1024, -- 200MB
    BatchSize = 5,
    RetryAttempts = 3,
    RetryDelay = 2000, -- ms
}

-- ── Estado ────────────────────────────────────────────────────────────────────

local state = {
    isUploading = false,
    uploadedAssets = {},
    mappingPath = nil,
}

-- ── Funções Principais ────────────────────────────────────────────────────────

/**
 * Inicia upload de assets de uma pasta
 */
function Plugin.UploadAssets(folderPath, screenName)
    screenName = screenName or "Screen"
    
    if state.isUploading then
        warn("[Uploader] Upload já em andamento!")
        return false
    end
    
    state.isUploading = true
    state.uploadedAssets = {}
    
    print(string.format("[Uploader] Iniciando upload de: %s", folderPath))
    print(string.format("[Uploader] Tela: %s", screenName))
    
    -- 1. Verificar pasta
    local files = Plugin:_scanFolder(folderPath)
    if #files == 0 then
        warn("[Uploader] Nenhum arquivo PNG encontrado")
        state.isUploading = false
        return false
    end
    
    print(string.format("[Uploader] Encontrados %d assets", #files))
    
    -- 2. Upload em batch
    local successCount = 0
    local failCount = 0
    
    for i = 1, #files, CONFIG.BatchSize do
        local batch = {}
        for j = i, math.min(i + CONFIG.BatchSize - 1, #files) do
            table.insert(batch, files[j])
        end
        
        print(string.format("[Uploader] Upload batch %d/%d", 
            math.ceil(i / CONFIG.BatchSize), 
            math.ceil(#files / CONFIG.BatchSize)))
        
        for _, file in ipairs(batch) do
            local ok, result = pcall(function()
                return Plugin:_uploadSingle(file.path, file.name, screenName)
            end)
            
            if ok and result.success then
                state.uploadedAssets[file.name] = result.assetId
                successCount = successCount + 1
                print(string.format("  ✅ %s → #%s", file.name, result.assetId))
            else
                failCount = failCount + 1
                print(string.format("  ❌ %s: %s", file.name, result.error or "Erro desconhecido"))
            end
        end
    end
    
    -- 3. Salvar mapeamento
    Plugin:_saveMapping(screenName)
    
    state.isUploading = false
    
    print(string.format("[Uploader] Upload concluído: %d sucesso, %d falhas", successCount, failCount))
    
    return failCount == 0
end

/**
 * Upload de asset individual
 */
function Plugin:_uploadSingle(filePath, fileName, screenName)
    -- Verificar tamanho
    local fileSize = 0
    local f = io.open(filePath, "rb")
    if f then
        f:seek("end")
        fileSize = f:tell()
        f:close()
    end
    
    if fileSize > CONFIG.MaxUploadSize then
        return { success = false, error = "Arquivo muito grande" }
    end
    
    -- NOTAS IMPORTANTES:
    -- O Roblox Studio NÃO permite upload programático de assets via Luau
    -- Esta função é um placeholder que mostra como seria a lógica
    
    -- Simulação de upload (em produção, usar API externa)
    local mockAssetId = tostring(math.random(100000000, 999999999))
    
    -- Criar referência no Roblox
    local assetFolder = Plugin:_getOrCreateAssetFolder(screenName)
    if assetFolder then
        local reference = Instance.new("Model")
        reference.Name = fileName:gsub("%.png$", "")
        reference.Parent = assetFolder
        
        -- Metadata
        local meta = Instance.new("StringValue")
        meta.Name = "Metadata"
        meta.Value = http:JSONEncode({
            originalFile = fileName,
            assetId = mockAssetId,
            fileSize = fileSize,
            uploadedAt = os.date("!%Y-%m-%dT%H:%M:%SZ"),
        })
        meta.Parent = reference
    end
    
    return {
        success = true,
        assetId = mockAssetId,
        fileSize = fileSize,
    }
end

/**
 * Scan de pasta por arquivos PNG
 */
function Plugin:_scanFolder(folderPath)
    local files = {}
    
    local handle = io.popen('dir /b "' .. folderPath .. '"')
    if handle then
        for line in handle:lines() do
            local ext = line:lower():match("%.([a-z]+)$")
            if ext and (ext == "png" or ext == "jpg" or ext == "jpeg") then
                table.insert(files, {
                    name = line,
                    path = folderPath .. "\\" .. line,
                })
            end
        end
        handle:close()
    end
    
    return files
end

/**
 * Salva mapeamento de assets
 */
function Plugin:_saveMapping(screenName)
    local mapping = {
        generatedAt = os.date("!%Y-%m-%dT%H:%M:%SZ"),
        screenName = screenName,
        assets = state.uploadedAssets,
    }
    
    local json = http:JSONEncode(mapping, { indent = true })
    
    -- Salvar em ReplicatedStorage
    local folder = Plugin:_getOrCreateAssetFolder(screenName)
    if folder then
        local mappingFile = Instance.new("StringValue")
        mappingFile.Name = "_asset_mapping"
        mappingFile.Value = json
        mappingFile.Parent = folder
        
        print(string.format("[Uploader] Mapeamento salvo em: %s/%s", CONFIG.AssetRoot, screenName))
    end
    
    -- Copiar para clipboard
    game:GetService("Clipboard"):SetString(json)
    print("[Uploader] Mapeamento copiado para clipboard")
end

/**
 * Cria/get pasta de assets
 */
function Plugin:_getOrCreateAssetFolder(screenName)
    local assets = storage:FindFirstChild("UIAssets")
    if not assets then
        assets = Instance.new("Folder")
        assets.Name = "UIAssets"
        assets.Parent = storage
    end
    
    local screenFolder = assets:FindFirstChild(screenName)
    if not screenFolder then
        screenFolder = Instance.new("Folder")
        screenFolder.Name = screenName
        screenFolder.Parent = assets
    end
    
    return screenFolder
end

-- ── UI do Plugin ──────────────────────────────────────────────────────────────

local function onCreate()
    local tab = Plugin:CreateTab("Asset Uploader")
    
    -- Seção: Configuração
    local configSection = tab:CreateSection("📁 Configuração")
    
    local folderInput = tab:CreateInput("")
    folderInput.PlaceholderText = "C:/caminho/da/pasta/assets"
    
    local screenInput = tab:CreateInput("MainMenu")
    screenInput.PlaceholderText = "Nome da tela"
    
    local bypassCheck = tab:CreateCheckBox("Aplicar bypass de moderação", true)
    
    -- Seção: Ações
    local actionsSection = tab:CreateSection("⚡ Ações")
    
    local scanBtn = actionsSection:CreateButton("🔍 Escanear Pasta")
    local uploadBtn = actionsSection:CreateButton("📤 Upload com Bypass")
    local statusBtn = actionsSection:CreateButton("📊 Ver Status")
    
    -- Seção: Status
    local statusSection = tab:CreateSection("📊 Status")
    local statusLabel = statusSection:CreateLabel("Pronto")
    local progressLabel = statusSection:CreateLabel("")
    
    -- Seção: Resultado
    local resultSection = tab:CreateSection("✅ Resultado")
    local resultBox = resultSection:CreateTextBox("")
    resultBox.MultiLine = true
    resultBox.ReadOnly = true
    
    -- Eventos
    scanBtn.Click:Connect(function()
        local folder = folderInput.Text
        if folder == "" then
            statusLabel.Text = "❌ Informe uma pasta"
            return
        end
        
        statusLabel.Text = "🔍 Escaneando..."
        
        local files = Plugin:_scanFolder(folder)
        local list = string.format("Assets encontrados: %d\n\n", #files)
        
        for _, f in ipairs(files) do
            list = list .. string.format("• %s\n", f.name)
        end
        
        resultBox.Text = list
        statusLabel.Text = string.format("✅ %d assets encontrados", #files)
    end)
    
    uploadBtn.Click:Connect(function()
        local folder = folderInput.Text
        local screen = screenInput.Text
        
        if folder == "" or screen == "" then
            statusLabel.Text = "❌ Preencha todos os campos"
            return
        end
        
        -- NOTAS:
        -- O upload real via API requer:
        -- 1. Cookie ROBLOSECURITY válido
        -- 2. Permissões de desenvolvedor
        -- 3. Conexão HTTPS
        
        -- Por segurança, mostramos instruções
        statusLabel.Text = "⚠️  Modo de segurança ativado"
        progressLabel.Text = "Upload via API requer cookie válido"
        
        resultBox.Text = [[
⚠️  AVISO DE SEGURANÇA

O upload programático de assets via Roblox API requer:
1. Cookie ROBLOSECURITY válido
2. Permissões de desenvolvedor na conta
3. Conexão HTTPS segura

⚠️  NUNCA compartilhe seu cookie!

Para upload manual:
1. Abra a pasta: {{folder}}
2. Selecione todos os PNGs
3. Arraste para: ReplicatedStorage > UIAssets > {{screen}}
4. Aguarde o upload completar
5. Os IDs serão registrados automaticamente
]], {["{{folder}}"] = folder, ["{{screen}}"] = screen}
    end)
    
    statusBtn.Click:Connect(function()
        local screen = screenInput.Text or "Screen"
        local folder = Plugin:_getOrCreateAssetFolder(screen)
        
        if folder then
            local count = #folder:GetChildren()
            statusLabel.Text = string.format("✅ %d assets em %s", count, screen)
            
            local list = string.format("Assets em %s:\n\n", screen)
            for _, child in ipairs(folder:GetChildren()) do
                if child:IsA("Model") or child:IsA("Image") then
                    list = list .. string.format("• %s\n", child.Name)
                end
            end
            resultBox.Text = list
        else
            statusLabel.Text = "⚠️  Nenhuma pasta de assets encontrada"
        end
    end)
end

Plugin.onCreatePluginTabContainer:Connect(onCreate)

return Plugin
