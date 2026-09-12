--!strict
/**
 * AIUIGenerator.luau — Gerador de UI Roblox a partir de especificação IA
 *
 * Usa a especificação gerada pela IA (via PSD Intelligence Scanner)
 * para criar automaticamente uma interface Roblox completa.
 *
 * Uso:
 *   local Generator = require(script.Parent.AIUIGenerator)
 *   local spec = require(script.Parent.AISpecification)
 *   local ui = Generator.build(spec, screenGuiParent)
 */

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

-- ============================================================
-- CONFIGURAÇÕES GLOBAIS
-- ============================================================

local CONFIG = {
	DefaultCanvasWidth = 1920,
	DefaultCanvasHeight = 1080,
	MinButtonHeight = 50,
	MinButtonTextSize = 18,
	DefaultFontSize = 24,
	DefaultCornerRadius = 8,
	SupportedFonts = {
		"Gotham" = Enum.Font.Gotham,
		"GothamBold" = Enum.Font.GothamBold,
		"GothamBlack" = Enum.Font.GothamBlack,
		"Arial" = Enum.Font.Arial,
		"Helvetica" = Enum.Font.Helvetica,
	},
}

-- ============================================================
-- CLASS: AIUIGenerator
-- ============================================================

local AIUIGenerator = {}
AIUIGenerator.__index = AIUIGenerator

function AIUIGenerator.new()
	local self = setmetatable({}, AIUIGenerator)
	self.Elements = {}
	self.ScreenGui = nil
	self.DesignWidth = CONFIG.DefaultCanvasWidth
	self.DesignHeight = CONFIG.DefaultCanvasHeight
	return self
end

-- ============================================================
-- MÉTODOS PRINCIPAIS
-- ============================================================

/**
 * Constrói a UI a partir da especificação da IA
 */
function AIUIGenerator:build(spec, parent)
	self.DesignWidth = spec.canvasWidth or CONFIG.DefaultCanvasWidth
	self.DesignHeight = spec.canvasHeight or CONFIG.DefaultCanvasHeight

	-- Criar ScreenGui
	self.ScreenGui = Instance.new("ScreenGui")
	self.ScreenGui.Name = spec.screenName or "GeneratedUI"
	self.ScreenGui.ResetOnSpawn = false
	self.ScreenGui.IgnoreGuiInset = true
	self.ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	self.ScreenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")

	-- Build elements
	for _, elementSpec in ipairs(spec.elements or {}) do
		self:_buildElement(elementSpec)
	end

	-- Apply layout hints
	if spec.layoutHints then
		self:_applyLayoutHints(spec.layoutHints)
	end

	return self.ScreenGui
end

/**
 * Constrói um elemento individual
 */
function AIUIGenerator:_buildElement(elementSpec)
	local robloxClass = elementSpec.robloxClass or "Frame"
	local el = Instance.new(robloxClass)
	el.Name = elementSpec.name or "Element"

	-- Position (Scale+Offset)
	local posSpec = elementSpec.position or {}
	el.Position = UDim2.new(
		posSpec.xScale or 0,
		posSpec.xOffset or 0,
		posSpec.yScale or 0,
		posSpec.yOffset or 0
	)

	-- Size (Scale+Offset)
	local sizeSpec = elementSpec.size or {}
	el.Size = UDim2.new(
		sizeSpec.xScale or 0,
		sizeSpec.xOffset or 0,
		sizeSpec.yScale or 0,
		sizeSpec.yOffset or 0
	)

	-- Properties
	local props = elementSpec.properties or {}

	if props.text then
		el.Text = props.text
	end

	if props.textSize then
		el.TextSize = props.textSize
	elseif robloxClass == "TextButton" or robloxClass == "TextLabel" then
		el.TextSize = CONFIG.DefaultFontSize
	end

	if props.textColor then
		el.TextColor3 = self:_hexToColor3(props.textColor)
	end

	if props.backgroundColor then
		el.BackgroundColor3 = self:_hexToColor3(props.backgroundColor)
	end

	if props.cornerRadius and props.cornerRadius > 0 then
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0, props.cornerRadius)
		corner.Parent = el
	end

	if props.borderSize then
		el.BorderSizePixel = props.borderSize
	end

	if props.borderColor then
		el.BorderColor3 = self:_hexToColor3(props.borderColor)
	end

	-- Font
	if props.font and CONFIG.SupportedFonts[props.font] then
		el.Font = CONFIG.SupportedFonts[props.font]
	elseif robloxClass == "TextButton" or robloxClass == "TextLabel" then
		el.Font = Enum.Font.GothamBold
	end

	-- Image
	if elementSpec.imagePath then
		el.Image = elementSpec.imagePath
		if props.scaleType then
			el.ScaleType = props.scaleType
		end
	end

	-- Effects
	if elementSpec.effects then
		self:_applyEffects(el, elementSpec.effects)
	end

	el.Parent = self.ScreenGui
	self.Elements[elementSpec.id] = el

	return el
end

/**
 * Aplica hints de layout (UIListLayout, etc.)
 */
function AIUIGenerator:_applyLayoutHints(hints)
	-- Vertical groups → UIListLayout vertical
	if hints.verticalGroups then
		for _, group in ipairs(hints.verticalGroups) do
			local parent = self.Elements[group.parentId]
			if parent then
				local layout = Instance.new("UIListLayout")
				layout.Parent = parent
				layout.Direction = Enum.Direction.Vertical
				layout.HorizontalAlignment = Enum.HorizontalAlignment.Left
				layout.SortOrder = Enum.SortOrder.LayoutOrder
			end
		end
	end

	-- Horizontal groups → UIListLayout horizontal
	if hints.horizontalGroups then
		for _, group in ipairs(hints.horizontalGroups) do
			local parent = self.Elements[group.parentId]
			if parent then
				local layout = Instance.new("UIListLayout")
				layout.Parent = parent
				layout.Direction = Enum.Direction.Horizontal
				layout.HorizontalAlignment = Enum.HorizontalAlignment.Left
				layout.SortOrder = Enum.SortOrder.LayoutOrder
			end
		end
	end

	-- List layouts (sugestões explícitas)
	if hints.listLayouts then
		for _, listLayout in ipairs(hints.listLayouts) do
			local parent = self.Elements[listLayout.parentId]
			if parent then
				local layout = Instance.new("UIListLayout")
				layout.Parent = parent
				if listLayout.direction == "Vertical" then
					layout.Direction = Enum.Direction.Vertical
				else
					layout.Direction = Enum.Direction.Horizontal
				end
				layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
				layout.SortOrder = Enum.SortOrder.LayoutOrder
				if listLayout.padding then
					layout.Padding = UDim.new(0, listLayout.padding)
				end
			end
		end
	end
end

/**
 * Aplica efeitos (shadow, glow, etc.)
 */
function AIUIGenerator:_applyEffects(element, effects)
	for _, effect in ipairs(effects) do
		if effect.type == "dropShadow" then
			self:_createDropShadow(element, effect)
		elseif effect.type == "innerShadow" then
			-- Inner shadow não tem equivalente direto no Roblox
			-- Podemos simular com UIGradient
		end
	end
end

function AIUIGenerator:_createDropShadow(element, effect)
	-- Simular drop shadow com Frame semi-transparente deslocado
	local shadow = Instance.new("Frame")
	shadow.Name = element.Name .. "_Shadow"
	shadow.Position = UDim2.new(
		element.Position.X.Scale,
		element.Position.X.Offset + (effect.distance or 4),
		element.Position.Y.Scale,
		element.Position.Y.Offset + (effect.distance or 4)
	)
	shadow.Size = element.Size
	shadow.BackgroundColor3 = self:_hexToColor3(effect.color or "#000000")
	shadow.BackgroundTransparency = 1 - ((effect.opacity or 45) / 100)
	shadow.BorderSizePixel = 0
	shadow.Parent = element
end

-- ============================================================
-- MÉTODOS UTILITÁRIOS
-- ============================================================

function AIUIGenerator:_hexToColor3(hex)
	if not hex or type(hex) ~= "string" then
		return Color3.new(0, 0, 0)
	end

	hex = hex:gsub("#", "")
	if #hex == 6 then
		local r = tonumber("0x" .. hex:sub(1, 2)) / 255
		local g = tonumber("0x" .. hex:sub(3, 4)) / 255
		local b = tonumber("0x" .. hex:sub(5, 6)) / 255
		return Color3.fromRGB(r * 255, g * 255, b * 255)
	elseif #hex == 8 then
		local r = tonumber("0x" .. hex:sub(1, 2)) / 255
		local g = tonumber("0x" .. hex:sub(3, 4)) / 255
		local b = tonumber("0x" .. hex:sub(5, 6)) / 255
		local a = tonumber("0x" .. hex:sub(7, 8)) / 255
		return Color3.fromRGB(r * 255, g * 255, b * 255)
	end

	return Color3.new(0, 0, 0)
end

function AIUIGenerator:getElement(id)
	return self.Elements[id]
end

function AIUIGenerator:getAllElements()
	return self.Elements
end

function AIUIGenerator:show()
	if self.ScreenGui then
		self.ScreenGui.Enabled = true
	end
end

function AIUIGenerator:hide()
	if self.ScreenGui then
		self.ScreenGui.Enabled = false
	end
end

function AIUIGenerator:destroy()
	if self.ScreenGui then
		self.ScreenGui:Destroy()
		self.ScreenGui = nil
		self.Elements = {}
	end
end

-- ============================================================
-- FUNÇÕES DE CONVERSÃO DE FORMATOS
-- ============================================================

/**
 * Converte especificação da IA para formato interno
 */
function AIUIGenerator.convertAISpec(aiSpec)
	local converted = {
		screenName = aiSpec.screenName or "UI",
		canvasWidth = aiSpec.canvasWidth or 1920,
		canvasHeight = aiSpec.canvasHeight or 1080,
		elements = {},
		layoutHints = aiSpec.layoutHints or {},
	}

	for _, el in ipairs(aiSpec.elements or {}) do
		table.insert(converted.elements, {
			id = el.id,
			name = el.name,
			robloxClass = el.robloxClass,
			position = el.position,
			size = el.size,
			properties = el.properties,
			effects = el.effects,
			imagePath = el.imagePath,
			responsive = el.responsive,
		})
	end

	return converted
end

/**
 * Gera código Lua boilerplate baseado na especificação
 */
function AIUIGenerator.generateLuaCode(spec, screenName)
	local lua = {}
	table.insert(lua, "--!strict")
	table.insert(lua, "-- Auto-generated by AIUIGenerator")
	table.insert(lua, "-- Canvas: " .. tostring(spec.canvasWidth) .. "x" .. tostring(spec.canvasHeight))
	table.insert(lua, "-- Generated: " .. os.date("%Y-%m-%d %H:%M:%S"))
	table.insert(lua, "")
	table.insert(lua, 'local Players = game:GetService("Players")')
	table.insert(lua, 'local GeneratedUI = {}')
	table.insert(lua, 'GeneratedUI.__index = GeneratedUI')
	table.insert(lua, "")
	table.insert(lua, "function GeneratedUI.new()")
	table.insert(lua, "    local self = setmetatable({}, GeneratedUI)")
	table.insert(lua, "    self.Elements = {}")
	table.insert(lua, "    return self")
	table.insert(lua, "end")
	table.insert(lua, "")
	table.insert(lua, "function GeneratedUI:Build(parent)")
	table.insert(lua, '    local screenGui = Instance.new("ScreenGui")')
	table.insert(lua, '    screenGui.Name = "' .. tostring(screenName) .. '"')
	table.insert(lua, "    screenGui.ResetOnSpawn = false")
	table.insert(lua, "    screenGui.IgnoreGuiInset = true")
	table.insert(lua, '    screenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")')
	table.insert(lua, "")

	for _, el in ipairs(spec.elements or {}) do
		table.insert(lua, "    -- " .. el.name)
		table.insert(lua, '    local ' .. el.name:gsub("%W", "_") .. " = Instance.new(\"" .. el.robloxClass .. "\")")
		table.insert(lua, '    ' .. el.name:gsub("%W", "_") .. ".Name = \"" .. el.name .. "\"")

		if el.position then
			table.insert(lua, '    ' .. el.name:gsub("%W", "_") .. ".Position = UDim2.new(")
			table.insert(lua, "        " .. tostring(el.position.xScale or 0) .. ", " .. tostring(el.position.xOffset or 0) .. ",")
			table.insert(lua, "        " .. tostring(el.position.yScale or 0) .. ", " .. tostring(el.position.yOffset or 0) .. ")")
		end

		if el.size then
			table.insert(lua, '    ' .. el.name:gsub("%W", "_") .. ".Size = UDim2.new(")
			table.insert(lua, "        " .. tostring(el.size.xScale or 0) .. ", " .. tostring(el.size.xOffset or 0) .. ",")
			table.insert(lua, "        " .. tostring(el.size.yScale or 0) .. ", " .. tostring(el.size.yOffset or 0) .. ")")
		end

		table.insert(lua, "    " .. el.name:gsub("%W", "_") .. ".Parent = screenGui")
		table.insert(lua, "")
	end

	table.insert(lua, "    return screenGui")
	table.insert(lua, "end")
	table.insert(lua, "")
	table.insert(lua, "return GeneratedUI")

	return table.concat(lua, "\n")
end

-- ============================================================
-- EXPORTAÇÃO
-- ============================================================

return AIUIGenerator
