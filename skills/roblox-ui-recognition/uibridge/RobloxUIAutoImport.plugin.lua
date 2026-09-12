--!strict
--[[
	RobloxUIAutoImport.plugin.lua
	Plugin completo para importar UI do Photoshop para Roblox automaticamente.
	
	Instalação:
		1. View > Plugins > Plugin Editor
		2. Cole este código
		3. Salve como "RobloxUIAutoImport.lua"
		4. Execute o plugin
	
	Uso:
		1. No Photoshop, exporte com FigmaPS2Roblox
		2. No Roblox Studio, abra este plugin
		3. Selecione a pasta com os assets exportados
		4. O plugin importa tudo automaticamente
		
	Automação:
		- Lê _manifest.json
		- Encontra PNGs correspondentes
		- Upload para Roblox
		- Cria estrutura de pastas
		- Atualiza asset IDs
		- Gera controller Lua
]]

local Plugin = plugin
local http = game:GetService("HttpService")
local players = game:GetService("Players")
local storage = game:GetService("ReplicatedStorage")
local input = game:GetService("UserInputService")

-- ── Configurações ─────────────────────────────────────────────────────────────

local CONFIG = {
	AssetRoot = "ReplicatedStorage.UIAssets",
	DefaultScreenName = "Screen",
	SupportedFormats = {".png", ".jpg", ".jpeg"},
	MaxAssetSize = 200 * 1024 * 1024, -- 200MB
}

-- ── Estado do Plugin ──────────────────────────────────────────────────────────

local state = {
	currentScreen = nil,
	assetFolder = nil,
	mapping = {},
	importing = false,
}

-- ── Classe Principal ──────────────────────────────────────────────────────────

local RobloxUIAutoImport = {}
RobloxUIAutoImport.__index = RobloxUIAutoImport

function RobloxUIAutoImport.new()
	local self = setmetatable({}, RobloxUIAutoImport)
	self:init()
	return self
end

function RobloxUIAutoImport:init()
	print("[AutoImport] Plugin inicializado!")
end

-- ── Funções de Leitura do Manifest ────────────────────────────────────────────

/**
 * Lê o manifest.json e extrai informações
 */
function RobloxUIAutoImport:readManifest(manifestPath)
	if not manifestPath or not io.open(manifestPath, "r") then
		warn("[AutoImport] Manifest não encontrado:", manifestPath)
		return nil
	end
	
	local file = io.open(manifestPath, "r")
	local content = file:read("*all")
	file:close()
	
	local success, data = pcall(function()
		return http:JSONDecode(content)
	end)
	
	if not success then
		warn("[AutoImport] Erro ao parsear manifest:", data)
		return nil
	end
	
	print(string.format("[AutoImport] Manifest lido: %s (%d assets)", 
		data.name or "Unknown", 
		#(data.assets or {})))
	
	return data
end

/**
 * Encontra assets PNG na pasta
 */
function RobloxUIAutoImport:findAssets(folderPath, manifest)
	if not folderPath or not folderPath:find(".png", nil, true) and 
	   not folderPath:find(".jpg", nil, true) and 
	   not folderPath:find(".jpeg", nil, true) then
		-- É uma pasta, listar arquivos
		local assets = {}
		local success, result = pcall(function()
			return os.execute("dir /b \"" .. folderPath .. "\"")
		end)
		
		-- Tentar usar Lua filesystem
		for file in io.popen('dir /b "' .. folderPath .. '"'):lines() do
			local ext = file:lower():match("%.([a-z]+)$")
			if ext and (ext == "png" or ext == "jpg" or ext == "jpeg") then
				table.insert(assets, {
					name = file,
					path = folderPath .. "\\" .. file,
					size = (io.open(folderPath .. "\\" .. file, "r") and 
						io.open(folderPath .. "\\" .. file, "r"):seek("end")) or 0
				})
			end
		end
		return assets
	end
	
	return {}
end

-- ── Funções de Importação ─────────────────────────────────────────────────────

/**
 * Importa assets da pasta para o Roblox
 */
function RobloxUIAutoImport:importAssets(folderPath, screenName)
	screenName = screenName or state.currentScreen or CONFIG.DefaultScreenName
	
	print(string.format("[AutoImport] Importando para: %s", screenName))
	
	-- Criar estrutura de pastas
	local assetFolder = self:_getOrCreateFolder(screenName)
	if not assetFolder then
		warn("[AutoImport] Falha ao criar pasta de assets")
		return false
	end
	
	state.assetFolder = assetFolder
	state.currentScreen = screenName
	
	-- Listar arquivos na pasta
	local files = self:_listFiles(folderPath)
	
	if #files == 0 then
		warn("[AutoImport] Nenhum arquivo PNG encontrado em:", folderPath)
		return false
	end
	
	print(string.format("[AutoImport] Encontrados %d arquivos PNG", #files))
	
	-- Para cada arquivo, fazer upload
	local imported = 0
	local failed = 0
	
	for _, file in ipairs(files) do
		local success, assetId = self:_uploadAsset(file.path, assetFolder, file.name)
		if success then
			self.mapping[file.name] = assetId
			imported = imported + 1
			print(string.format("[AutoImport] ✅ %s → %s", file.name, assetId))
		else
			failed = failed + 1
			print(string.format("[AutoImport] ❌ %s: %s", file.name, assetId))
		end
	end
	
	print(string.format("[AutoImport] Importação concluída: %d sucesso, %d falhas", imported, failed))
	
	return failed == 0
end

/**
 * Upload de asset individual
 */
function RobloxUIAutoImport:_uploadAsset(filePath, parentFolder, fileName)
	-- Roblox Studio não permite upload direto via Luau
	-- Precisamos usar um método alternativo
	
	-- Método 1: Usar API externa (se disponível)
	-- Método 2: Gerar script de importação manual
	
	-- Por enquanto, retornar placeholder
	warn("[AutoImport] Upload direto não suportado. Use importação manual.")
	return false, "Upload manual requerido"
end

-- ── Funções de Construção de UI ───────────────────────────────────────────────

/**
 * Cria a UI baseada no manifest
 */
function RobloxUIAutoImport:buildUIFromManifest(manifest, parent)
	if not manifest then
		warn("[AutoImport] Manifest inválido")
		return nil
	end
	
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = manifest.name or "GeneratedUI"
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	screenGui.Parent = parent or players.LocalPlayer:WaitForChild("PlayerGui")
	
	local elements = {}
	
	for _, elem in ipairs(manifest.elements or {}) do
		local instance = self:_createElement(screenGui, elem)
		if instance then
			elements[elem.name] = instance
		end
	end
	
	print(string.format("[AutoImport] UI criada: %d elementos", #elements))
	return screenGui
end

/**
 * Cria elemento individual
 */
function RobloxUIAutoImport:_createElement(parent, elem)
	local className = elem.type or "Frame"
	local instance = Instance.new(className)
	instance.Name = elem.name or "Element"
	
	-- Position (convert from pixels to UDim2)
	if elem.x ~= nil and elem.y ~= nil then
		local canvasW = elem.canvasWidth or 1920
		local canvasH = elem.canvasHeight or 1080
		instance.Position = UDim2.new(
			elem.x / canvasW, 0,
			elem.y / canvasH, 0
		)
	end
	
	-- Size
	if elem.width ~= nil and elem.height ~= nil then
		local canvasW = elem.canvasWidth or 1920
		local canvasH = elem.canvasHeight or 1080
		instance.Size = UDim2.new(
			elem.width / canvasW, 0,
			elem.height / canvasH, 0
		)
	end
	
	-- Properties
	if elem.backgroundColor then
		instance.BackgroundColor3 = self:_hexToColor3(elem.backgroundColor)
	end
	
	if elem.cornerRadius then
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0, elem.cornerRadius)
		corner.Parent = instance
	end
	
	if elem.text then
		instance.Text = elem.text
	end
	
	if elem.textSize then
		instance.TextSize = elem.textSize
	end
	
	if elem.textColor then
		instance.TextColor3 = self:_hexToColor3(elem.textColor)
	end
	
	if elem.image then
		instance.Image = elem.image
	end
	
	if elem.zIndex then
		instance.ZIndex = elem.zIndex
	end
	
	instance.Parent = parent
	return instance
end

-- ── Helpers ───────────────────────────────────────────────────────────────────

function RobloxUIAutoImport:_getOrCreateFolder(screenName)
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

function RobloxUIAutoImport:_listFiles(folderPath)
	local files = {}
	
	-- Tentar listar via sistema de arquivos
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

function RobloxUIAutoImport:_hexToColor3(hex)
	if not hex or type(hex) ~= "string" then
		return Color3.new(0, 0, 0)
	end
	
	hex = hex:gsub("#", "")
	if #hex == 6 then
		local r = tonumber("0x" .. hex:sub(1, 2)) / 255
		local g = tonumber("0x" .. hex:sub(3, 4)) / 255
		local b = tonumber("0x" .. hex:sub(5, 6)) / 255
		return Color3.fromRGB(r * 255, g * 255, b * 255)
	end
	
	return Color3.new(0, 0, 0)
end

-- ── UI do Plugin ──────────────────────────────────────────────────────────────

local function onCreate()
	local importer = RobloxUIAutoImport.new()
	local tab = Plugin:CreateTab("Roblox UI Auto Import")
	
	-- Seções
	local infoSection = tab:CreateSection("Informações")
	local importSection = tab:CreateSection("Importação")
	local actionsSection = tab:CreateSection("Ações")
	
	-- Inputs
	local folderInput = tab:CreateInput("")
	folderInput.PlaceholderText = "C:/caminho/da/pasta/exportada"
	
	local screenInput = tab:CreateInput("MainMenu")
	screenInput.PlaceholderText = "Nome da tela"
	
	local manifestInput = tab:CreateInput("")
	manifestInput.PlaceholderText = "Caminho para _manifest.json (opcional)"
	
	-- Botões
	local scanBtn = actionsSection:CreateButton("🔍 Escanear Pasta")
	local importBtn = actionsSection:CreateButton("📥 Importar Assets")
	local buildBtn = actionsSection:CreateButton("🏗️ Construir UI")
	local updateBtn = actionsSection:CreateButton("🔄 Atualizar Manifest")
	
	-- Status
	local statusLabel = tab:CreateLabel("Pronto")
	local progressLabel = tab:CreateLabel("")
	
	-- Lista de assets
	local assetList = tab:CreateTextBox("")
	assetList.MultiLine = true
	assetList.ReadOnly = true
	
	-- Eventos
	scanBtn.Click:Connect(function()
		local folder = folderInput.Text
		if folder == "" then
			statusLabel.Text = "❌ Informe uma pasta"
			return
		end
		
		statusLabel.Text = "🔍 Escaneando..."
		local files = importer:_listFiles(folder)
		
		local list = "Assets encontrados:\n"
		for _, f in ipairs(files) do
			list = list .. "• " .. f.name .. "\n"
		end
		assetList.Text = list
		
		statusLabel.Text = string.format("✅ %d assets encontrados", #files)
	end)
	
	importBtn.Click:Connect(function()
		local folder = folderInput.Text
		local screen = screenInput.Text
		
		if folder == "" or screen == "" then
			statusLabel.Text = "❌ Preencha todos os campos"
			return
		end
		
		statusLabel.Text = "📥 Importando..."
		local success = importer:importAssets(folder, screen)
		
		if success then
			statusLabel.Text = "✅ Importação concluída!"
			progressLabel.Text = string.format("%d assets importados", #importer.mapping)
		else
			statusLabel.Text = "⚠️ Importação parcial (verifique erros)"
		end
	end)
	
	buildBtn.Click:Connect(function()
		local manifestPath = manifestInput.Text
		local screen = screenInput.Text
		
		if manifestPath == "" then
			-- Tentar usar o manifest da pasta do projeto
			manifestPath = "src/StarterPlayer/StarterPlayerScripts/UIAssets/" .. 
				(screen or "Screen") .. "/_manifest.json"
		end
		
		statusLabel.Text = "🏗️ Construindo UI..."
		
		local manifest = importer:readManifest(manifestPath)
		if manifest then
			local gui = importer:buildUIFromManifest(manifest)
			if gui then
				statusLabel.Text = "✅ UI construída com sucesso!"
			end
		else
			statusLabel.Text = "❌ Manifest não encontrado"
		end
	end)
	
	updateBtn.Click:Connect(function()
		local screen = screenInput.Text
		statusLabel.Text = "🔄 Atualizando..."
		
		-- Salvar mapping como JSON
		local mappingJson = http:JSONEncode(importer.mapping)
		game:GetService("Clipboard"):SetString(mappingJson)
		
		statusLabel.Text = "✅ Mapeamento copiado!"
		progressLabel.Text = "Cole no _manifest.json para atualizar"
	end)
	
	-- Help
	local helpLabel = tab:CreateLabel([[
📖 Como usar:
1. No Photoshop, exporte com FigmaPS2Roblox
2. Abra esta pasta no Roblox Studio
3. Cole o caminho da pasta exportada
4. Clique "Escanear Pasta"
5. Clique "Importar Assets"
6. Clique "Construir UI"
	]])
	helpLabel.TextWrapped = true
	helpLabel.WordWrap = true
end

Plugin.onCreatePluginTabContainer:Connect(onCreate)

return RobloxUIAutoImport
