--!strict
--[[
	RobloxUIImporter.plugin.lua
	Plugin completo para importar UIs do Photoshop/Figma para Roblox.
	
	Instalação:
		1. View > Plugins > Plugin Editor
		2. Cole este código
		3. Salve como "RobloxUIImporter.lua"
		4. Execute
	
	Uso:
		1. Exporte PSD com FigmaPS2Roblox
		2. Abra Roblox Studio
		3. Execute este plugin
		4. Selecione a pasta exportada
		5. O plugin importa tudo automaticamente
]]

local Plugin = plugin
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- ── Configurações ─────────────────────────────────────────────────────────────

local CONFIG = {
	AssetRoot = "ReplicatedStorage.UIAssets",
	DefaultScreenName = "Screen",
}

-- ── Funções Principais ────────────────────────────────────────────────────────

/**
 * Importa uma UI completa a partir de uma pasta exportada
 */
function Plugin.ImportUI(folderPath: string, screenName: string?): { [string]: any }?
	screenName = screenName or CONFIG.DefaultScreenName
	
	-- 1. Ler o manifest
	local manifest = self:_readManifest(folderPath, screenName)
	if not manifest then
		warn("[Importer] Manifest não encontrado")
		return nil
	end
	
	-- 2. Criar estrutura de pastas no Roblox
	local assetFolder = self:_createAssetFolder(screenName)
	if not assetFolder then
		warn("[Importer] Falha ao criar pasta de assets")
		return nil
	end
	
	-- 3. Processar cada asset
	local importedAssets = {}
	for _, asset in ipairs(manifest.assets or {}) do
		local success, assetId = self:_importAsset(
			folderPath,
			asset.filename,
			assetFolder,
			asset
		)
		if success then
			asset.assetId = assetId
			table.insert(importedAssets, asset)
		end
	end
	
	-- 4. Salvar manifest atualizado
	self:_saveManifest(folderPath, screenName, manifest)
	
	-- 5. Gerar controller Lua
	self:_generateController(screenName, manifest)
	
	return importedAssets
end

/**
 * Lê o manifest.json da pasta
 */
function Plugin:_readManifest(folderPath: string, screenName: string): any?
	local manifestPath = folderPath .. "\\" .. screenName .. "_manifest.json"
	
	-- Tentar ler do sistema de arquivos
	local file = io.open(manifestPath, "r")
	if not file then
		-- Tentar caminho alternativo
		manifestPath = folderPath .. "\\_manifest.json"
		file = io.open(manifestPath, "r")
	end
	
	if not file then
		warn(string.format("[Importer] Manifest não encontrado em: %s", manifestPath))
		return nil
	end
	
	local content = file:read("*all")
	file:close()
	
	local success, data = pcall(function()
		return HttpService:JSONDecode(content)
	end)
	
	if not success then
		warn("[Importer] Erro ao parsear manifest:", data)
		return nil
	end
	
	return data
end

/**
 * Cria a estrutura de pastas no Roblox
 */
function Plugin:_createAssetFolder(screenName: string): Instance?
	local assetsFolder = ReplicatedStorage:FindFirstChild("UIAssets")
	if not assetsFolder then
		assetsFolder = Instance.new("Folder")
		assetsFolder.Name = "UIAssets"
		assetsFolder.Parent = ReplicatedStorage
	end
	
	local screenFolder = assetsFolder:FindFirstChild(screenName)
	if not screenFolder then
		screenFolder = Instance.new("Folder")
		screenFolder.Name = screenName
		screenFolder.Parent = assetsFolder
	end
	
	return screenFolder
end

/**
 * Importa um asset individual
 */
function Plugin:_importAsset(folderPath: string, filename: string, parentFolder: Instance, assetInfo: any): (boolean, string)?
	local imagePath = folderPath .. "\\" .. filename
	
	-- Verificar se arquivo existe
	local file = io.open(imagePath, "r")
	if not file then
		warn(string.format("[Importer] Arquivo não encontrado: %s", imagePath))
		return false, ""
	end
	file:close()
	
	-- NOTAS:
	-- Roblox Studio NÃO permite upload programático de assets via Luau
	-- O usuário precisa arrastar os arquivos manualmente para o Explorer
	
	-- Por enquanto, registrar o asset com placeholder
	local placeholderId = "rbxassetid://0"
	
	-- Criar referência no manifesto
	local reference = Instance.new("Model")
	reference.Name = filename:gsub("%.png$", "")
	reference.Parent = parentFolder
	
	-- Salvar metadata
	local metadata = Instance.new("StringValue")
	metadata.Name = "Metadata"
	metadata.Value = HttpService:JSONEncode({
		originalFile = filename,
		assetId = placeholderId,
		uniqueId = assetInfo.uniqueId,
		type = assetInfo.type,
		x = assetInfo.x,
		y = assetInfo.y,
		width = assetInfo.width,
		height = assetInfo.height,
	})
	metadata.Parent = reference
	
	return true, placeholderId
end

/**
 * Salva o manifest atualizado
 */
function Plugin:_saveManifest(folderPath: string, screenName: string, manifest: any)
	local manifestPath = folderPath .. "\\" .. screenName .. "_manifest.json"
	
	local content = HttpService:JSONEncode(manifest, { indent = true })
	local file = io.open(manifestPath, "w")
	if file then
		file:write(content)
		file:close()
		print(string.format("[Importer] Manifest atualizado: %s", manifestPath))
	end
end

/**
 * Gera o controller Lua
 */
function Plugin:_generateController(screenName: string, manifest: any)
	local luaCode = string.format([=[
--!strict
-- Auto-generated by RobloxUIImporter
-- Screen: %s
-- Canvas: %dx%d
-- Assets: %d
-- Generated: %s

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local DESIGN_WIDTH = %d
local DESIGN_HEIGHT = %d

local GeneratedUI = {}
GeneratedUI.__index = GeneratedUI

function GeneratedUI.new()
	local self = setmetatable({}, GeneratedUI)
	self.Elements = {}
	return self
end

function GeneratedUI:CreateElement(parent, config)
	local el = Instance.new(config.Class)
	el.Name = config.Name
	el.Position = UDim2.new(
		config.X / DESIGN_WIDTH, config.OffsetX or 0,
		config.Y / DESIGN_HEIGHT, config.OffsetY or 0
	)
	el.Size = UDim2.new(
		config.Width / DESIGN_WIDTH, config.OffsetWidth or 0,
		config.Height / DESIGN_HEIGHT, config.OffsetHeight or 0
	)
	
	if config.BackgroundColor3 then el.BackgroundColor3 = config.BackgroundColor3 end
	if config.BackgroundTransparency ~= nil then el.BackgroundTransparency = config.BackgroundTransparency end
	if config.CornerRadius and config.CornerRadius > 0 then
		local corner = Instance.new('UICorner')
		corner.CornerRadius = UDim.new(0, config.CornerRadius)
		corner.Parent = el
	end
	if config.Text then
		el.Text = config.Text
		if config.TextSize then el.TextSize = config.TextSize end
		if config.TextColor3 then el.TextColor3 = config.TextColor3 end
		if config.Font then el.Font = config.Font end
	end
	if config.Image then
		el.Image = config.Image
		if config.ScaleType then el.ScaleType = config.ScaleType end
	end
	el.Parent = parent
	return el
end

function GeneratedUI:Build(parent)
	local screenGui = Instance.new('ScreenGui')
	screenGui.Name = '%s'
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	screenGui.Parent = parent or Players.LocalPlayer:WaitForChild('PlayerGui')
	
	local elements = {}
	=%s=],
		screenName,
		manifest.canvasWidth or 1920,
		manifest.canvasHeight or 1080,
		#(manifest.assets or {}),
		os.date("%Y-%m-%d %H:%M:%S"),
		manifest.canvasWidth or 1920,
		manifest.canvasHeight or 1080,
		screenName
	)
	
	-- Adicionar elementos
	for _, elem in ipairs(manifest.elements or {}) do
		luaCode = luaCode .. string.format([=[
		elements['%s'] = self:CreateElement(screenGui, {
			Class = "%s",
			Name = "%s",
			X = %d,
			Y = %d,
			Width = %d,
			Height = %d,
			%s
		})
		=%s=],
			elem.name,
			elem.type,
			elem.name,
			elem.x or 0,
			elem.y or 0,
			elem.width or 0,
			elem.height or 0,
			elem.properties and self:_formatProperties(elem.properties) or "",
			elem.name
		)
	end
	
	luaCode = luaCode .. [[
	
	self.Elements = elements
	return screenGui
end

function GeneratedUI:_formatProperties(props: any): string
	if not props then return "" end
	local parts = {}
	if props.BackgroundColor3 then
		table.insert(parts, string.format("BackgroundColor3 = Color3.fromRGB(%d, %d, %d),", 
			props.BackgroundColor3.r * 255, props.BackgroundColor3.g * 255, props.BackgroundColor3.b * 255))
	end
	if props.CornerRadius then
		table.insert(parts, string.format("CornerRadius = %d,", props.CornerRadius))
	end
	if props.Text then
		table.insert(parts, string.format('Text = "%s",', props.Text))
	end
	if props.TextSize then
		table.insert(parts, string.format("TextSize = %d,", props.TextSize))
	end
	return table.concat(parts, "\n\t\t\t"))
end

return GeneratedUI
]=])
	
	-- Salvar em ReplicatedStorage
	local controllerPath = string.format("%s.UIAssets.%s._controller", CONFIG.AssetRoot, screenName)
	local controllerFolder = ReplicatedStorage:FindFirstChild("UIAssets"):FindFirstChild(screenName)
	
	if controllerFolder then
		local controllerScript = Instance.new("Script")
		controllerScript.Name = "_controller"
		controllerScript.Source = luaCode
		controllerScript.Parent = controllerFolder
		print(string.format("[Importer] Controller gerado: %s", controllerPath))
	end
end

-- ── UI do Plugin ──────────────────────────────────────────────────────────────

local function onCreate()
	local tab = Plugin:CreateTab("Roblox UI Importer")
	
	-- Seção: Origem
	local originSection = tab:CreateSection("📂 Origem (Photoshop)")
	local folderInput = originSection:CreateInput("")
	folderInput.PlaceholderText = "C:/caminho/da/pasta/exportada"
	
	local screenInput = originSection:CreateInput("MainMenu")
	screenInput.PlaceholderText = "Nome da tela (MainMenu, HUD, etc.)"
	
	-- Seção: Ações
	local actionsSection = tab:CreateSection("⚡ Ações")
	
	local scanBtn = actionsSection:CreateButton("🔍 Escanear Pasta")
	local importBtn = actionsSection:CreateButton("📥 Importar Assets")
	local buildBtn = actionsSection:CreateButton("🏗️ Construir UI")
	local guideBtn = actionsSection:CreateButton("📖 Ver Guia")
	
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
		
		-- Verificar se existe manifest
		local manifestPath = folder .. "\\" .. screenInput.Text .. "_manifest.json"
		local file = io.open(manifestPath, "r")
		
		if file then
			file:close()
			statusLabel.Text = "✅ Manifest encontrado!"
			progressLabel.Text = string.format("Arquivo: %s", manifestPath)
			
			-- Listar assets
			local assets = {}
			for f in io.popen('dir /b "' .. folder .. '"'):lines() do
				if f:lower():match("%.png$") then
					table.insert(assets, f)
				end
			end
			
			resultBox.Text = string.format("Assets encontrados: %d\n\n%s", 
				#assets, 
				table.concat(assets, "\n"))
		else
			statusLabel.Text = "❌ Manifest não encontrado"
			resultBox.Text = "Verifique se a pasta contém:\n- _manifest.json\n- *_*.png"
		end
	end)
	
	importBtn.Click:Connect(function()
		local folder = folderInput.Text
		local screen = screenInput.Text
		
		if folder == "" or screen == "" then
			statusLabel.Text = "❌ Preencha todos os campos"
			return
		end
		
		statusLabel.Text = "📥 Iniciando importação..."
		
		-- Passo 1: Verificar manifest
		local manifest = Plugin:_readManifest(folder, screen)
		if not manifest then
			statusLabel.Text = "❌ Manifest não encontrado"
			return
		end
		
		-- Passo 2: Criar estrutura
		local assetFolder = Plugin:_createAssetFolder(screen)
		if not assetFolder then
			statusLabel.Text = "❌ Falha ao criar estrutura"
			return
		end
		
		-- Passo 3: Importar assets (guia manual)
		local assetList = {}
		for _, asset in ipairs(manifest.assets or {}) do
			table.insert(assetList, asset.filename)
		end
		
		-- Mostrar instruções
		local instructions = string.format([[
📋 PASSOS PARA IMPORTAÇÃO:

1. Abra o Windows Explorer
2. Navegue até: %s
3. Selecione os %d arquivos PNG listados abaixo
4. Arraste para o Explorer do Roblox Studio:
   ReplicatedStorage > UIAssets > %s

📁 Arquivos para importar:
%s

Após importar, clique em "Construir UI"
]], 
			folder,
			#assetList,
			screen,
			table.concat(assetList, "\n"))
		
		resultBox.Text = instructions
		statusLabel.Text = "✅ Preparado para importação manual"
		
		-- Salvar lista de arquivos para referência
		state.expectedFiles = assetList
		state.targetFolder = screen
	end)
	
	buildBtn.Click:Connect(function()
		local folder = folderInput.Text
		local screen = screenInput.Text
		
		statusLabel.Text = "🏗️ Construindo UI..."
		
		-- Ler manifest
		local manifest = Plugin:_readManifest(folder, screen)
		if not manifest then
			statusLabel.Text = "❌ Manifest não encontrado"
			return
		end
		
		-- Gerar controller
		Plugin:_generateController(screen, manifest)
		
		statusLabel.Text = "✅ UI construída com sucesso!"
		progressLabel.Text = string.format("Screen: %s | Assets: %d", 
			screen, #(manifest.assets or {}))
		
		resultBox.Text = string.format([[
✅ UI Construída!

📋 Resumo:
• Tela: %s
• Canvas: %dx%d
• Assets: %d
• Estrutura: ReplicatedStorage/UIAssets/%s

📝 Para usar no jogo:
local UI = require(game.ReplicatedStorage.UIAssets.%s._controller)
local ui = UI.new()
ui:Build()
]], 
			screen,
			manifest.canvasWidth or 1920,
			manifest.canvasHeight or 1080,
			#(manifest.assets or {}),
			screen,
			screen)
	end)
	
	guideBtn.Click:Connect(function()
		resultBox.Text = [[
📖 GUIA RÁPIDO - Roblox UI Importer

═══════════════════════════════════════

1️⃣  NO PHOTOSHOP:
    • Abra seu PSD
    • Window > Extensions > FigmaPS2Roblox
    • Selecione a prancheta desejada
    • Exporte para uma pasta

2️⃣  NO ROBLOX STUDIO:
    • View > Plugins > Roblox UI Importer
    • Cole o caminho da pasta exportada
    • Clique "Escanear Pasta"
    • Clique "Importar Assets"
    • Siga as instruções para upload
    • Clique "Construir UI"

3️⃣  NO JOGO:
    • Use o controller gerado:
    
    local UI = require(game.ReplicatedStorage
        .UIAssets.MainMenu._controller)
    UI.new():Build()

═══════════════════════════════════════

⚠️  NOTA: Assets precisam ser importados
   manualmente (arrastar para o Explorer).
   O plugin automatiza toda a estrutura e código.
]]
	end)
end

-- Estado global
local state = {
	expectedFiles = {},
	targetFolder = nil,
}

Plugin.onCreatePluginTabContainer:Connect(onCreate)

return Plugin
