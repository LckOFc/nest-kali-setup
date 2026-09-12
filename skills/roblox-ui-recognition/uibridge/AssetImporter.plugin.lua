--!strict
--[[
	AssetImporter.luau
	Plugin do Roblox Studio para importar assets UI automaticamente.
	
	Instalação:
	 1. View > Plugins > Plugin Editor
	 2. Cole este código
	 3. Salve como "AssetImporter.lua"
	 4. Execute o plugin
	
	Uso:
		AssetImporter.ImportFromFolder("C:/caminho/da/pasta/assets")
		AssetImporter.LinkAssets("MainMenu")
		AssetImporter.UpdateManifest("MainMenu")
]]

local Plugin = plugin or {}
local plugin = Plugin

-- ── Configurações ─────────────────────────────────────────────────────────────

local CONFIG = {
	AssetRoot = "ReplicatedStorage.UIAssets",
	DefaultScreenName = "Screen",
}

-- ── Variáveis Globais ─────────────────────────────────────────────────────────

local assetMapping = {}

-- ── Funções Públicas ──────────────────────────────────────────────────────────

/**
 * Importa todos os PNGs de uma pasta para o Roblox
 * Retorna mapeamento de nome → asset ID
 */
function plugin.ImportFromFolder(localFolderPath: string, screenName: string?): { [string]: string }
	screenName = screenName or CONFIG.DefaultScreenName
	
	local assetFolder = self:_getAssetFolder(screenName)
	local imported = {}
	
	-- Nota: Roblox Studio não permite acesso direto ao filesystem via Luau.
	-- Este plugin guia o usuário passo a passo.
	
	warn(string.format("[AssetImporter] Para importar de: %s", localFolderPath))
	warn(string.format("[AssetImporter] Passos:"))
	warn(string.format("  1. Abra a pasta: %s", localFolderPath))
	warn(string.format("  2. Selecione todos os arquivos PNG"))
	warn(string.format("  3. Arraste para: %s.%s no Explorer", CONFIG.AssetRoot, screenName))
	warn(string.format("  4. Aguarde o upload completar"))
	warn(string.format("  5. Execute: plugin.LinkAssets(\"%s\")", screenName))
	
	return imported
end

/**
 * Linka assets importados ao manifest
 */
function plugin.LinkAssets(screenName: string): { [string]: string }
	local assetFolder = self:_getAssetFolder(screenName)
	local mapping = {}
	
	for _, child in ipairs(assetFolder:GetChildren()) do
		if child:IsA("Image") or child:IsA("Decal") or child:IsA("Texture") then
			mapping[child.Name] = tostring(child.AssetId)
		end
	end
	
	assetMapping[screenName] = mapping
	
	print(string.format("[AssetImporter] %d assets linkados em '%s'", #mapping, screenName))
	return mapping
end

/**
 * Atualiza o manifest com os asset IDs
 */
function plugin.UpdateManifest(screenName: string): boolean
	local manifestFile = self:_getManifestFile(screenName)
	if not manifestFile then
		warn(string.format("[AssetImporter] Manifest não encontrado para '%s'", screenName))
		return false
	end
	
	local mapping = assetMapping[screenName] or {}
	if #mapping == 0 then
		warn(string.format("[AssetImporter] Nenhum asset linkado. Execute LinkAssets primeiro."))
		return false
	end
	
	local success, manifest = pcall(function()
		return game:GetService("HttpService"):JSONDecode(manifestFile.Value)
	end)
	
	if not success then
		warn("[AssetImporter] Erro ao decodificar manifest")
		return false
	end
	
	local updated = 0
	for _, asset in ipairs(manifest.assets or {}) do
		local mappedId = mapping[asset.uniqueId] 
			or mapping[asset.filename]
			or mapping[asset.name]
		
		if mappedId and mappedId ~= "0" then
			asset.assetId = "rbxassetid://" .. mappedId
			updated += 1
		end
	end
	
	manifestFile.Value = game:GetService("HttpService"):JSONEncode(manifest)
	print(string.format("[AssetImporter] Manifest atualizado: %d/%d assets", updated, #manifest.assets))
	
	return true
end

/**
 * Gera script Lua a partir do manifest
 */
function plugin.GenerateController(screenName: string): string
	local manifestFile = self:_getManifestFile(screenName)
	if not manifestFile then
		return ""
	end
	
	local manifest = game:GetService("HttpService"):JSONDecode(manifestFile.Value)
	local luaCode = string.format([=[
--!strict
-- Gerado automaticamente por AssetImporter
-- Tela: %s
-- Canvas: %dx%d
-- Assets: %d
-- Gerado em: %s

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

function GeneratedUI:Build(parent)
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = "%s"
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	screenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")

	-- Assets
	=%s=],
		screenName,
		manifest.canvasWidth or 1920,
		manifest.canvasHeight or 1080,
		#manifest.assets,
		os.date("%Y-%m-%d %H:%M:%S"),
		manifest.canvasWidth or 1920,
		manifest.canvasHeight or 1080,
		screenName
	)
	
	-- Adicionar assets
	for _, asset in ipairs(manifest.assets or {}) do
		luaCode = luaCode .. string.format([=[
	local %s = Instance.new("ImageLabel")
	%s.Name = "%s"
	%s.Image = "%s"
	%s.Parent = screenGui
	=%s=],
			self:_safeVarName(asset.name),
			self:_safeVarName(asset.name),
			asset.name,
			self:_safeVarName(asset.name),
			asset.assetId or "rbxassetid://0",
			self:_safeVarName(asset.name),
			self:_safeVarName(asset.name)
		)
	end
	
	luaCode = luaCode .. [[
	
	return screenGui
end

return GeneratedUI
]]
	
	return luaCode
end

-- ── Helpers Privadas ──────────────────────────────────────────────────────────

function plugin:_getAssetFolder(screenName: string): Instance
	local assets = ReplicatedStorage:FindFirstChild("UIAssets")
	if not assets then
		assets = Instance.new("Folder")
		assets.Name = "UIAssets"
		assets.Parent = ReplicatedStorage
	end
	
	local screenFolder = assets:FindFirstChild(screenName)
	if not screenFolder then
		screenFolder = Instance.new("Folder")
		screenFolder.Name = screenName
		screenFolder.Parent = assets
	end
	
	return screenFolder
end

function plugin:_getManifestFile(screenName: string): Instance?
	local assets = ReplicatedStorage:FindFirstChild("UIAssets")
	if not assets then return nil end
	
	local screenFolder = assets:FindFirstChild(screenName)
	if not screenFolder then return nil end
	
	return screenFolder:FindFirstChild("_manifest.json")
end

function plugin:_safeVarName(name: string): string
	return name
		:gsub("[^a-zA-Z0-9_]", "_")
		:gsub("^%d", "_%1")
end

-- ── Plugin UI ─────────────────────────────────────────────────────────────────

local function onCreate()
	local tab = plugin:CreateTab("UI Importer")
	
	-- Input de pasta
	local folderLabel = tab:CreateLabel("Pasta de Assets:")
	local folderInput = tab:CreateInput("")
	folderInput.PlaceholderText = "C:/caminho/da/pasta"
	
	-- Input de nome da tela
	local screenLabel = tab:CreateLabel("Nome da Tela:")
	local screenInput = tab:CreateInput("Screen")
	screenInput.PlaceholderText = "MainMenu, HUD, etc."
	
	-- Botões
	local importBtn = tab:CreateButton("📁 Importar Assets")
	local linkBtn = tab:CreateButton("🔗 Linkar Assets")
	local updateBtn = tab:CreateButton("📝 Atualizar Manifest")
	local generateBtn = tab:CreateButton("⚡ Gerar Controller")
	
	local statusLabel = tab:CreateLabel("Pronto")
	
	importBtn.Click:Connect(function()
		local folder = folderInput.Text
		local screen = screenInput.Text or "Screen"
		
		if folder == "" then
			statusLabel.Text = "❌ Informe uma pasta"
			return
		end
		
		statusLabel.Text = "📂 Importando..."
		plugin:ImportFromFolder(folder, screen)
		statusLabel.Text = "✅ Concluído! Arraste os arquivos no Explorer"
	end)
	
	linkBtn.Click:Connect(function()
		local screen = screenInput.Text or "Screen"
		local mapping = plugin:LinkAssets(screen)
		statusLabel.Text = string.format("✅ %d assets linkados", #mapping)
	end)
	
	updateBtn.Click:Connect(function()
		local screen = screenInput.Text or "Screen"
		local success = plugin:UpdateManifest(screen)
		statusLabel.Text = success and "✅ Manifest atualizado!" or "❌ Falha"
	end)
	
	generateBtn.Click:Connect(function()
		local screen = screenInput.Text or "Screen"
		local luaCode = plugin:GenerateController(screen)
		
		if luaCode ~= "" then
			game:GetService("Clipboard"):SetString(luaCode)
			statusLabel.Text = "✅ Controller copiado para clipboard!"
		else
			statusLabel.Text = "❌ Erro ao gerar controller"
		end
	end)
end

plugin.onCreatePluginTabContainer:Connect(onCreate)

return plugin
