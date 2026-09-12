--!strict
--[[
	UIBridge.luau
	Biblioteca principal que lê um manifest de UI exportado pelo Photoshop ou Figma
	e reconstrói toda a interface no Roblox automaticamente.

	Formato do manifest (exportado pelos plugins):
	{
		"name": "LobbyScreen",
		"canvasWidth": 1920,
		"canvasHeight": 1080,
		"scaleMode": "ScaleToFit" | "ScaleWithScreenSize" | "PixelPerfect",
		"elements": [
			{
				"type": "ImageLabel",
				"name": "Background",
				"assetId": "rbxassetid://123456789",
				"x": 0, "y": 0,
				"width": 1920, "height": 1080,
				"anchorX": 0, "anchorY": 0,
				"zIndex": 1,
				"visible": true,
				"interactable": false,
				"children": []
			},
			{
				"type": "TextButton",
				"name": "PlayButton",
				"assetId": "rbxassetid://0",
				"text": "JOGAR",
				"x": 810, "y": 500,
				"width": 300, "height": 80,
				"anchorX": 0.5, "anchorY": 0.5,
				"backgroundColor": { "r": 0.2, "g": 0.2, "b": 0.2 },
				"textColor": { "r": 1, "g": 1, "b": 1 },
				"textSize": 24,
				"font": "GothamBold",
				"borderRadius": 12,
				"zIndex": 2,
				"visible": true,
				"interactable": true,
				"events": {
					"Activated": "onPlayPressed"
				},
				"children": []
			}
		],
		"scripts": {
			"onPlayPressed": function(button)
				-- código inline ou referencia a outro módulo
			end
		}
	}
]]

local UIBridge = {}
UIBridge.__index = UIBridge

-- ── Font mapping ─────────────────────────────────────────────────────────────

local FONT_MAP = {
	Gotham = Enum.Font.Gotham,
	GothamBold = Enum.Font.GothamBold,
	GothamBlack = Enum.Font.GothamBlack,
	GothamMedium = Enum.Font.GothamMedium,
	GothamSemibold = Enum.Font.GothamSemibold,
	Baloo2 = Enum.Font.Baloo2,
	Baloo2Bold = Enum.Font.Baloo2Bold,
	Poppins = Enum.Font.Poppins,
	PoppinsBold = Enum.Font.PoppinsBold,
	Roboto = Enum.Font.Roboto,
	RobotoBold = Enum.Font.RobotoBold,
	SourceSans = Enum.Font.SourceSans,
	SourceSansBold = Enum.Font.SourceSansBold,
}

-- ── Color helpers ─────────────────────────────────────────────────────────────

local function hexToColor3(hex: string): Color3?
	if not hex or type(hex) ~= "string" then return nil end
	hex = hex:gsub("#", "")
	if #hex == 6 then
		local r = tonumber(hex:sub(1, 2), 16) / 255
		local g = tonumber(hex:sub(3, 4), 16) / 255
		local b = tonumber(hex:sub(5, 6), 16) / 255
		return Color3.fromRGB(r * 255, g * 255, b * 255)
	end
	if #hex == 8 then
		local r = tonumber(hex:sub(1, 2), 16) / 255
		local g = tonumber(hex:sub(3, 4), 16) / 255
		local b = tonumber(hex:sub(5, 6), 16) / 255
		local a = tonumber(hex:sub(7, 8), 16) / 255
		return Color3.fromRGB(r * 255, g * 255, b * 255)
	end
	return nil
end

local function tableToColor3(c: any): Color3?
	if type(c) == "string" then return hexToColor3(c) end
	if type(c) == "table" then
		return Color3.fromRGB(
			math.floor((c.r or 0) * 255),
			math.floor((c.g or 0) * 255),
			math.floor((c.b or 0) * 255)
		)
	end
	return nil
end

-- ── Scale mode resolver ──────────────────────────────────────────────────────

local function resolveScaleMode(scaleMode: string?, parent: GuiObject?): (UDim2, UDim2, number)
	local canvasW, canvasH = 1920, 1080
	-- Get actual screen size from PlayerGui
	local screenW, screenH: number, number = 1920, 1080
	if parent then
		screenW = parent.AbsoluteSize.X
		screenH = parent.AbsoluteSize.Y
	elseif game:GetService("Players").LocalPlayer and game:GetService("Players").LocalPlayer:FindFirstChild("PlayerGui") then
		screenW = game:GetService("Players").LocalPlayer.PlayerGui.AbsoluteSize.X
		screenH = game:GetService("Players").LocalPlayer.PlayerGui.AbsoluteSize.Y
	end

	local scale = Enum.ScaleMode.ScaleToFit

	if scaleMode == "ScaleWithScreenSize" then
		scale = Enum.ScaleMode.ScaleWithScreenSize
	elseif scaleMode == "PixelPerfect" then
		scale = Enum.ScaleMode.PixelPerfect
	end

	local scaleX = screenW / canvasW
	local scaleY = screenH / canvasH
	local scaleFactor: number
	if scaleMode == "ScaleWithScreenSize" then
		scaleFactor = 1
	else
		scaleFactor = math.min(scaleX, scaleY)
	end

	return UDim2.new(scaleFactor, 0, scaleFactor, 0), UDim2.new(0, 0, 0, 0), scaleFactor
end

-- ── Element builder ───────────────────────────────────────────────────────────

local function buildElement(elem: any, parent: GuiObject, scaleUDim: UDim2, screenScale: number)
	local inst: GuiObject

	local t = elem.type or "Frame"

	if t == "ImageLabel" or t == "ImageButton" then
		inst = Instance.new(t)
		if elem.assetId and elem.assetId ~= "rbxassetid://0" then
			inst.Image = elem.assetId
		end
		inst.ScaleType = elem.scaleType == "Fill" and Enum.ScaleType.Fill or Enum.ScaleType.Crop
		inst.ImageTransparency = elem.transparency or 0
		inst.SliceCenter = elem.sliceCenter and Rect.new(unpack(elem.sliceCenter)) or nil

	elseif t == "TextLabel" or t == "TextButton" then
		inst = Instance.new(t)
		inst.Text = elem.text or ""
		inst.TextColor3 = tableToColor3(elem.textColor) or Color3.new(1, 1, 1)
		inst.TextSize = elem.textSize or 18
		inst.Font = FONT_MAP[elem.font] or Enum.Font.Gotham
		inst.TextWrapped = elem.textWrapped == true
		inst.TextXAlignment = elem.textAlignX or Enum.TextXAlignment.Center
		inst.TextYAlignment = elem.textAlignY or Enum.TextYAlignment.Middle
		inst.BackgroundTransparency = 1

		if elem.richText == true then
			inst.RichText = true
		end

	elseif t == "Frame" then
		inst = Instance.new("Frame")
		inst.BackgroundColor3 = tableToColor3(elem.backgroundColor) or Color3.new(0, 0, 0)
		inst.BackgroundTransparency = elem.backgroundTransparency or 0
		inst.BorderSizePixel = 0
		if elem.borderRadius and elem.borderRadius > 0 then
			local corner = Instance.new("UICorner")
			corner.CornerRadius = UDim.new(0, elem.borderRadius)
			corner.Parent = inst
		end
		if elem.borderColor and elem.borderWidth then
			inst.BackgroundColor3 = tableToColor3(elem.borderColor)
			inst.BorderSizePixel = elem.borderWidth or 1
			local stroke = Instance.new("UIStroke")
			stroke.Thickness = UDim.new(0, elem.borderWidth or 1)
			stroke.Color = tableToColor3(elem.borderColor)
			stroke.Parent = inst
		end

	elseif t == "ScrollingFrame" then
		inst = Instance.new("ScrollingFrame")
		inst.BackgroundColor3 = tableToColor3(elem.backgroundColor) or Color3.new(1, 1, 1)
		inst.BackgroundTransparency = elem.backgroundTransparency or 0
		inst.BorderSizePixel = 0
		inst.ScrollBarThickness = elem.scrollbarThickness or 6
		inst.ScrollBarImageColor3 = tableToColor3(elem.scrollbarColor) or Color3.fromRGB(200, 200, 200)
		inst.CanvasSize = elem.canvasSize and UDim2.fromOffset(elem.canvasSize.width or 0, elem.canvasSize.height or 0) or UDim2.new(0, 0, 0, 0)
		inst.ScrollBarInsetContent = elem.scrollbarInset == true and UDim.new(0, 4) or UDim.new(0, 0)
		if elem.borderRadius and elem.borderRadius > 0 then
			local corner = Instance.new("UICorner")
			corner.CornerRadius = UDim.new(0, elem.borderRadius)
			corner.Parent = inst
		end

	elseif t == "UIListLayout" then
		inst = Instance.new("UIListLayout")
		inst.SortOrder = Enum.SortOrder.LayoutOrder
		inst.Padding = UDim.new(0, elem.padding or 8)
		inst.HorizontalWrap = elem.horizontalWrap == true

	elseif t == "UIGridLayout" then
		inst = Instance.new("UIGridLayout")
		inst.CellSize = UDim2.fromOffset(elem.cellSize or 120, elem.cellSize or 120)
		inst.Padding = UDim.new(0, elem.padding or 8)
		inst.CellPadding = UDim.new(0, elem.cellPadding or 4)
		inst.HorizontalAlignment = elem.horizontalAlign or Enum.HorizontalAlignment.Center
		inst.VerticalAlignment = elem.verticalAlign or Enum.VerticalAlignment.Center

	elseif t == "UIPadding" then
		inst = Instance.new("UIPadding")
		inst.PaddingTop = UDim.new(0, elem.paddingTop or elem.padding or 8)
		inst.PaddingBottom = UDim.new(0, elem.paddingBottom or elem.padding or 8)
		inst.PaddingLeft = UDim.new(0, elem.paddingLeft or elem.padding or 8)
		inst.PaddingRight = UDim.new(0, elem.paddingRight or elem.padding or 8)

	elseif t == "UIStroke" then
		inst = Instance.new("UIStroke")
		inst.Thickness = UDim.new(0, elem.thickness or 2)
		inst.Color = tableToColor3(elem.color) or Color3.new(1, 1, 1)
		inst.Transparency = elem.transparency or 0

	elseif t == "UICorner" then
		inst = Instance.new("UICorner")
		inst.CornerRadius = UDim.new(0, elem.cornerRadius or 8)
	else
		inst = Instance.new("Frame")
	end

	inst.Name = elem.name
	inst.Visible = elem.visible != false
	inst.ZIndex = elem.zIndex or 1
	inst.Interactable = elem.interactable == true
	inst.ClipsDescendants = elem.clipsDescendants == true

	-- Position and size with scaling
	local px = elem.x or 0
	local py = elem.y or 0
	local pw = elem.width or 0
	local ph = elem.height or 0

	local anchorX = elem.anchorX ?? 0
	local anchorY = elem.anchorY ?? 0

	-- Support relative positioning (0-1 range) vs pixel
	if elem.relativeX then px = px * screenScale end
	if elem.relativeY then py = py * screenScale end
	if elem.relativeWidth then pw = pw * screenScale end
	if elem.relativeHeight then ph = ph * screenScale end

	inst.Position = UDim2.new(anchorX, -anchorX * px, anchorY, -anchorY * py)
	inst.Size = UDim2.new(0, pw, 0, ph)

	if elem.anchorPoint then
		inst.AnchorPoint = Vector2.new(elem.anchorPoint[1] or 0, elem.anchorPoint[2] or 0)
	end

	inst.Parent = parent

	-- Apply constraints
	if elem.constraints then
		for _, con in ipairs(elem.constraints) do
			if con.type == "Aspect" then
				local ac = Instance.new("UIAspectRatioConstraint")
				ac.AspectRatio = con.ratio
				ac.Parent = inst
			end
			if con.type == "Size" then
				local sc = Instance.new("UISizeConstraint")
				sc.MinValue = con.min and Vector2.new(con.min[1], con.min[2]) or Vector2.zero
				sc.MaxValue = con.max and Vector2.new(con.max[1], con.max[2]) or Vector2.new(9999, 9999)
				sc.Parent = inst
			end
		end
	end

	-- Apply effects
	if elem.effects then
		if elem.effects.dropShadow == true then
			local shadow = Instance.new("UIStroke")
			shadow.Color = Color3.fromRGB(0, 0, 0)
			shadow.Thickness = UDim.new(0, 4)
			shadow.Transparency = 0.7
			shadow.Parent = inst
		end
		if elem.effects.glow then
			-- Glow effect placeholder
		end
	end

	-- Recurse children
	if elem.children and typeof(elem.children) == "table" then
		for _, child in ipairs(elem.children) do
			buildElement(child, inst, scaleUDim, screenScale)
		end
	end

	-- Bind events
	if elem.events and typeof(elem.events) == "table" then
		for eventName, handlerName in pairs(elem.events) do
			local conn
			conn = (inst[eventName] :: Signal).Connect(inst[eventName], function(...)
				if elem.handlers and typeof(elem.handlers) == "table" and elem.handlers[handlerName] then
					elem.handlers[handlerName](inst, ...)
				end
			end)
			-- Store connection reference for cleanup
			(inst :: any)._connections = (inst :: any)._connections or {}
			table.insert((inst :: any)._connections, conn)
		end
	end

	return inst
end

-- ── Main API ──────────────────────────────────────────────────────────────────

function UIBridge.new(manifest: any, parent: GuiObject?)
	local self = setmetatable({}, UIBridge)
	self.manifest = manifest
	self.parent = parent or game.Players.LocalPlayer:WaitForChild("PlayerGui")
	self.elements = {}
	self.connections = {}
	return self
end

function UIBridge:build(): ScreenGui?
	local man = self.manifest
	if not man then return nil end

	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = man.name or "UIBridgeScreen"
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	if man.ignoreContext then
		screenGui.IgnoreContext = true
	end
	if man.zIndexBehavior then
		screenGui.ZIndexBehavior = Enum.ZIndexBehavior[man.zIndexBehavior] or Enum.ZIndexBehavior.Sibling
	end
	screenGui.Parent = self.parent

	-- Get actual screen dimensions
	local screenW, screenH = self.parent.AbsoluteSize.X, self.parent.AbsoluteSize.Y
	local canvasW = man.canvasWidth or 1920
	local canvasH = man.canvasHeight or 1080
	local scaleMode = man.scaleMode or "ScaleToFit"

	-- Compute scale factor based on canvas and screen
	local scaleX = screenW / canvasW
	local scaleY = screenH / canvasH
	local scaleFactor: number
	if scaleMode == "ScaleWithScreenSize" then
		scaleFactor = 1
	else
		scaleFactor = math.min(scaleX, scaleY)
	end

	-- Build root element
	if man.elements and typeof(man.elements) == "table" then
		for _, elem in ipairs(man.elements) do
			local built = buildElement(elem, screenGui, UDim2.new(scaleFactor, 0, scaleFactor, 0), scaleFactor)
			if built then table.insert(self.elements, built) end
		end
	end

	return screenGui
end

function UIBridge:show()
	for _, el in ipairs(self.elements) do
		if el:IsA("GuiObject") then el.Visible = true end
	end
end

function UIBridge:hide()
	for _, el in ipairs(self.elements) do
		if el:IsA("GuiObject") then el.Visible = false end
	end
end

function UIBridge:destroy()
	for _, conn in ipairs(self.connections) do
		pcall(function() conn:Disconnect() end)
	end
	for _, el in ipairs(self.elements) do
		pcall(function() el:Destroy() end)
	end
	self.elements = {}
	self.connections = {}
end

function UIBridge:get(name: string): GuiObject?
	for _, el in ipairs(self.elements) do
		if el.Name == name then return el end
	end
	return nil
end

-- ── Manifest builder (convenience) ───────────────────────────────────────────

function UIBridge.Manifest:new(name: string, opts: any?)
	return setmetatable({
		name = name,
		canvasWidth = opts and opts.canvasWidth or 1920,
		canvasHeight = opts and opts.canvasHeight or 1080,
		scaleMode = opts and opts.scaleMode or "ScaleToFit",
		elements = {},
		_ignore = opts and opts.ignoreContext or false,
	}, { __index = UIBridge.Manifest })
end

local M = {}
M.__index = M

function M:addElement(elem: any)
	table.insert(self.elements, elem)
	return self
end

function M:toJSON(): string
	return game:GetService("HttpService"):JSONEncode(self)
end

UIBridge.Manifest = M

-- ── Export helper ─────────────────────────────────────────────────────────────

function UIBridge.exportManifest(screenGui: ScreenGui): any
	local function walk(node: GuiObject, depth: number): any
		if depth > 8 then return nil end
		local elem: any = {
			type = node.ClassName,
			name = node.Name,
			x = node.Position.X.Offset,
			y = node.Position.Y.Offset,
			width = node.Size.X.Offset or 0,
			height = node.Size.Y.Offset or 0,
			anchorX = node.AnchorPoint.X,
			anchorY = node.AnchorPoint.Y,
			visible = node.Visible,
			zIndex = node.ZIndex,
			children = {},
		}

		if node:IsA("ImageLabel") or node:IsA("ImageButton") then
			elem.assetId = node.Image:gsub("rbxasset://", "rbxassetid://0"):gsub("rbxassetid://", "")
			elem.assetId = node.Image
		end
		if node:IsA("TextLabel") or node:IsA("TextButton") then
			elem.text = node.Text
			elem.textColor = { r = node.TextColor3.R, g = node.TextColor3.G, b = node.TextColor3.B }
			elem.textSize = node.TextSize
			elem.font = node.Font.Name
			elem.textWrapped = node.TextWrapped
			elem.textAlignX = node.TextXAlignment.Name
		end
		if node:IsA("Frame") or node:IsA("ScrollingFrame") then
			elem.backgroundColor = { r = node.BackgroundColor3.R, g = node.BackgroundColor3.G, b = node.BackgroundColor3.B }
		end

		for _, child in ipairs(node:GetChildren()) do
			if child:IsA("GuiObject") then
				local childElem = walk(child, depth + 1)
				if childElem then table.insert(elem.children, childElem) end
			end
		end

		return elem
	end

	return walk(screenGui, 0)
end

return UIBridge
