--!strict
--[[
	ImportManager.luau
	Gerenciador completo de importação UI para Roblox Studio.
	
	Uso:
		local ImportManager = require(script.Parent.ImportManager)
		ImportManager.ImportFromManifest("MenuPrincipal")
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local ImportManager = {}

-- ── Configurações ──────────────────────────────────────────────────────────────

local CONFIG = {
	AssetFolder = "UIAssets",
	MaxAssetSize = 200 * 1024 * 1024, -- 200MB
	DefaultCanvasWidth = 1920,
	DefaultCanvasHeight = 1080,
}

-- ── Estrutura de Pastas no Roblox ─────────────────────────────────────────────
--
-- ReplicatedStorage/
-- ├── UIBridge/
-- │   ├── UIBridge.luau
-- │   ├── Generator.luau
-- │   ├── AssetManager.luau
-- │   └── ImportManager.luau
-- │
-- ├── UIAssets/
-- │   ├── MainMenu/
-- │   │   ├── _manifest.json
-- │   │   ├── _controller.lua
-- │   │   ├── bg_main_xxx.png    ← Assets importados aqui
-- │   │   ├── btn_play_xxx.png
-- │   │   └── _upload_guide.txt
-- │   └── Shop/
-- │       └── ...
-- │
-- └── UIScreens/
--     ├── MainMenuController.lua
--     └── ShopController.lua

-- ── Funções Principais ────────────────────────────────────────────────────────

/**
 * Importa uma tela completa a partir do manifest
 */
function ImportManager.ImportScreen(screenName: string, parent: Instance?): ScreenGui
	local playerGui = parent or Players.LocalPlayer:WaitForChild("PlayerGui")
	
	-- Verificar se existe controller
	local controllerPath = string.format("ReplicatedStorage.UIAssets.%s._controller", screenName)
	local controller = ReplicatedStorage:FindFirstChild("UIAssets"):FindFirstChild(screenName):FindFirstChild("_controller.lua")
	
	if not controller then
		warn(string.format("[ImportManager] Controller não encontrado: %s", controllerPath))
		return nil
	end
	
	-- Criar ScreenGui
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = screenName
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	screenGui.Parent = playerGui
	
	-- Carregar manifest
	local manifestFile = ReplicatedStorage:FindFirstChild("UIAssets"):FindFirstChild(screenName):FindFirstChild("_manifest.json")
	if manifestFile then
		local manifest = HttpService:JSONDecode(manifestFile.Value)
		ImportManager:_buildFromManifest(screenGui, manifest)
	end
	
	print(string.format("[ImportManager] Tela '%s' importada com sucesso!", screenName))
	return screenGui
end

/**
 * Importa múltiplas telas
 */
function ImportManager.ImportMultipleScreenNames(screenNames: {string}): {string}
	local imported = {}
	local failed = {}
	
	for _, name in ipairs(screenNames) do
		local success = pcall(function()
			ImportManager.ImportScreen(name)
		end)
		
		if success then
			table.insert(imported, name)
		else
			table.insert(failed, name)
		end
	end
	
	if #failed > 0 then
		warn(string.format("[ImportManager] Falhas: %s", table.concat(failed, ", ")))
	end
	
	return imported
end

/**
 * Converte UDS para formato Roblox
 */
function ImportManager.ConvertUDS(udsJson: string): {any}
	local uds = HttpService:JSONDecode(udsJson)
	local elements = {}
	
	for _, layer in ipairs(uds.layers or {}) do
		local element = {
			id = layer.id,
			name = layer.name,
			robloxClass = ImportManager:_layerToRobloxClass(layer),
			position = ImportManager:_boundsToPosition(layer.bounds, uds.document.width, uds.document.height),
			size = ImportManager:_boundsToSize(layer.bounds, uds.document.width, uds.document.height),
			properties = {},
		}
		
		-- Cores
		if layer.fill and layer.fill.hex then
			element.properties.backgroundColor = ImportManager:_hexToColor3(layer.fill.hex)
		end
		
		-- Texto
		if layer.text then
			element.properties.text = layer.text.content
			element.properties.textSize = layer.text.size or 24
			if layer.text.color then
				element.properties.textColor = ImportManager:_hexToColor3(layer.text.color.hex)
			end
		end
		
		-- Efeitos
		if layer.effects then
			element.properties.effects = layer.effects
		end
		
		table.insert(elements, element)
	end
	
	return elements
end

-- ── Helpers ───────────────────────────────────────────────────────────────────

function ImportManager:_buildFromManifest(screenGui: Instance, manifest: any)
	for _, elem in ipairs(manifest.elements or {}) do
		local instance = ImportManager:_createElement(screenGui, elem)
		if instance then
			ImportManager:_applyProperties(instance, elem)
		end
	end
end

function ImportManager:_createElement(parent: Instance, elem: any): Instance?
	local className = elem.robloxClass or "Frame"
	local instance = Instance.new(className)
	instance.Name = elem.name or "Element"
	
	-- Position
	if elem.position then
		instance.Position = UDim2.new(
			elem.position.xScale or 0,
			elem.position.xOffset or 0,
			elem.position.yScale or 0,
			elem.position.yOffset or 0
		)
	end
	
	-- Size
	if elem.size then
		instance.Size = UDim2.new(
			elem.size.xScale or 0,
			elem.size.xOffset or 0,
			elem.size.yScale or 0,
			elem.size.yOffset or 0
		)
	end
	
	instance.Parent = parent
	return instance
end

function ImportManager:_applyProperties(instance: Instance, elem: any)
	local props = elem.properties or {}
	
	-- Background
	if props.backgroundColor then
		instance.BackgroundColor3 = props.backgroundColor
	end
	
	-- Border
	if props.borderSize then
		instance.BorderSizePixel = props.borderSize
	end
	if props.borderColor then
		instance.BorderColor3 = props.borderColor
	end
	
	-- Corner
	if props.cornerRadius and props.cornerRadius > 0 then
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0, props.cornerRadius)
		corner.Parent = instance
	end
	
	-- Text
	if instance:IsA("TextLabel") or instance:IsA("TextButton") then
		if props.text then
			instance.Text = props.text
		end
		if props.textSize then
			instance.TextSize = props.textSize
		end
		if props.textColor then
			instance.TextColor3 = props.textColor
		end
		if props.font then
			instance.Font = ImportManager:_stringToFont(props.font)
		end
		if props.textXAlignment then
			instance.TextXAlignment = props.textXAlignment
		end
	end
	
	-- Image
	if instance:IsA("ImageLabel") then
		if props.image then
			instance.Image = props.image
		end
		if props.scaleType then
			instance.ScaleType = props.scaleType
		end
	end
end

function ImportManager:_layerToRobloxClass(layer: any): string
	local role = (layer.semantic and layer.semantic.probableRole) or "layer"
	
	local classMap = {
		background = "ImageLabel",
		panel = "Frame",
		button = "TextButton",
		label = "TextLabel",
		icon = "ImageLabel",
		image = "ImageLabel",
		bar = "Frame",
		separator = "Frame",
		input = "TextBox",
	}
	
	return classMap[role] or "Frame"
end

function ImportManager:_boundsToPosition(bounds: any, canvasW: number, canvasH: number): any
	return {
		xScale = bounds.x / canvasW,
		yScale = bounds.y / canvasH,
		xOffset = 0,
		yOffset = 0,
	}
end

function ImportManager:_boundsToSize(bounds: any, canvasW: number, canvasH: number): any
	return {
		xScale = bounds.width / canvasW,
		yScale = bounds.height / canvasH,
		xOffset = 0,
		yOffset = 0,
	}
end

function ImportManager:_hexToColor3(hex: string): Color3
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

function ImportManager:_stringToFont(fontName: string): Enum.Font
	local fontMap = {
		["Gotham"] = Enum.Font.Gotham,
		["GothamBold"] = Enum.Font.GothamBold,
		["GothamBlack"] = Enum.Font.GothamBlack,
		["Arial"] = Enum.Font.Arial,
		["Helvetica"] = Enum.Font.Helvetica,
	}
	
	return fontMap[fontName] or Enum.Font.Gotham
end

-- ── Exportações ─────────────────────────────────────────────────────────────────

return ImportManager
