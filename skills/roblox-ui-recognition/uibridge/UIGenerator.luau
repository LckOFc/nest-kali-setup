--!strict
--[[
	UIGenerator.luau
	Módulo para construir UIs a partir de manifests JSON.
	
	Uso:
		local UIGenerator = require(script.Parent.UIGenerator)
		local ui = UIGenerator.build(manifest, parent)
]]

local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")

local UIGenerator = {}

-- ── Configurações ─────────────────────────────────────────────────────────────

local CONFIG = {
	DefaultCanvasWidth = 1920,
	DefaultCanvasHeight = 1080,
	SupportedFonts = {
		["Gotham"] = Enum.Font.Gotham,
		["GothamBold"] = Enum.Font.GothamBold,
		["GothamBlack"] = Enum.Font.GothamBlack,
		["Arial"] = Enum.Font.Arial,
	},
}

-- ── Funções Principais ────────────────────────────────────────────────────────

/**
 * Constrói uma UI a partir de um manifest JSON
 */
function UIGenerator.build(manifest: any, parent: Instance?): ScreenGui
	if not manifest then
		warn("[UIGenerator] Manifest inválido")
		return nil
	end
	
	local screenName = manifest.name or "GeneratedUI"
	local canvasWidth = manifest.canvasWidth or CONFIG.DefaultCanvasWidth
	local canvasHeight = manifest.canvasHeight or CONFIG.DefaultCanvasHeight
	
	-- Criar ScreenGui
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = screenName
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	screenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")
	
	-- Processar elementos
	local elements = {}
	for _, elem in ipairs(manifest.elements or {}) do
		local instance = UIGenerator:_createElement(screenGui, elem, canvasWidth, canvasHeight)
		if instance then
			elements[elem.name] = instance
		end
	end
	
	-- Aplicar layout hints
	UIGenerator:_applyLayoutHints(screenGui, manifest)
	
	print(string.format("[UIGenerator] UI '%s' construída: %d elementos", screenName, #elements))
	return screenGui
end

/**
 * Cria um elemento individual
 */
function UIGenerator:_createElement(parent: Instance, elem: any, canvasW: number, canvasH: number): Instance?
	local className = elem.type or "Frame"
	local instance = Instance.new(className)
	instance.Name = elem.name or "Element"
	
	-- Position (converter pixels para UDim2)
	if elem.x ~= nil and elem.y ~= nil then
		instance.Position = UDim2.new(
			elem.x / canvasW, 0,
			elem.y / canvasH, 0
		)
	end
	
	-- Size
	if elem.width ~= nil and elem.height ~= nil then
		instance.Size = UDim2.new(
			elem.width / canvasW, 0,
			elem.height / canvasH, 0
		)
	end
	
	-- Properties
	if elem.properties then
		UIGenerator:_applyProperties(instance, elem.properties)
	end
	
	-- AnchorPoint
	if elem.anchorX ~= nil or elem.anchorY ~= nil then
		instance.AnchorPoint = Vector2.new(
			elem.anchorX or 0,
			elem.anchorY or 0
		)
	end
	
	-- ZIndex
	if elem.zIndex then
		instance.ZIndex = elem.zIndex
	end
	
	instance.Parent = parent
	return instance
end

/**
 * Aplica propriedades de styling
 */
function UIGenerator:_applyProperties(instance: Instance, props: any)
	-- Background
	if props.backgroundColor then
		instance.BackgroundColor3 = UIGenerator:_hexToColor3(props.backgroundColor)
	end
	
	if props.backgroundTransparency ~= nil then
		instance.BackgroundTransparency = props.backgroundTransparency
	end
	
	-- Border
	if props.borderSize then
		instance.BorderSizePixel = props.borderSize
	end
	
	if props.borderColor then
		instance.BorderColor3 = UIGenerator:_hexToColor3(props.borderColor)
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
			instance.TextColor3 = UIGenerator:_hexToColor3(props.textColor)
		end
		if props.font and CONFIG.SupportedFonts[props.font] then
			instance.Font = CONFIG.SupportedFonts[props.font]
		end
		if props.textXAlignment then
			instance.TextXAlignment = props.textXAlignment
		end
		if props.textYAlignment then
			instance.TextYAlignment = props.textYAlignment
		end
		if props.textWrapped then
			instance.TextWrapped = props.textWrapped
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

/**
 * Aplica hints de layout (UIListLayout, etc.)
 */
function UIGenerator:_applyLayoutHints(parent: Instance, manifest: any)
	local hints = manifest.layoutHints
	if not hints then return end
	
	-- Vertical groups
	for _, group in ipairs(hints.verticalGroups or {}) do
		local container = parent:FindFirstChild(group.parent)
		if container then
			local layout = Instance.new("UIListLayout")
			layout.Parent = container
			layout.Direction = Enum.Direction.Vertical
			layout.HorizontalAlignment = Enum.HorizontalAlignment.Left
			layout.SortOrder = Enum.SortOrder.LayoutOrder
		end
	end
	
	-- Horizontal groups
	for _, group in ipairs(hints.horizontalGroups or {}) do
		local container = parent:FindFirstChild(group.parent)
		if container then
			local layout = Instance.new("UIListLayout")
			layout.Parent = container
			layout.Direction = Enum.Direction.Horizontal
			layout.HorizontalAlignment = Enum.HorizontalAlignment.Left
			layout.SortOrder = Enum.SortOrder.LayoutOrder
		end
	end
end

-- ── Helpers ───────────────────────────────────────────────────────────────────

function UIGenerator:_hexToColor3(hex: string): Color3
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

-- ── Exportações ─────────────────────────────────────────────────────────────────

return UIGenerator
