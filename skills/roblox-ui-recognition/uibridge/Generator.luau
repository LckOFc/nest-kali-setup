--!strict
--[[
	UIBridgeGenerator.luau
	Gera um controller a partir de um manifest JSON exportado pelos plugins
	do Photoshop ou Figma.

	Uso:
		local Generator = require(game.ReplicatedStorage.UIBridge.Generator)
		local controller = Generator.fromManifest(manifestData, "LobbyScreen")
		controller.Init()
		controller.Start()
]]

local UIBridge = require(script.Parent.UIBridge)

local Generator = {}

-- ── JSON loader ───────────────────────────────────────────────────────────────

local function loadManifest(jsonString: string): any
	local HttpService = game:GetService("HttpService")
	local ok, result = pcall(HttpService.JSONDecode, HttpService, jsonString)
	if not ok then
		warn("[UIBridge] Failed to parse manifest:", result)
		return nil
	end
	return result
end

-- ── Generator ─────────────────────────────────────────────────────────────────

function Generator.fromManifest(manifest: any, parent: GuiObject?): UIBridge
	local bridge = UIBridge.new(manifest, parent)
	bridge:build()
	return bridge
end

function Generator.fromJSON(jsonString: string, parent: GuiObject?): UIBridge
	local manifest = loadManifest(jsonString)
	if not manifest then
		warn("[UIBridge] Invalid manifest JSON")
		return nil
	end
	return Generator.fromManifest(manifest, parent)
end

function Generator.fromRemote(remote: RemoteEvent): UIBridge
	-- Waits for server to send manifest, then builds UI
	local HttpService = game:GetService("HttpService")
	local ok, jsonString: string? = pcall(remote.WaitForChild, remote, 10)
	if not ok or not jsonString then
		warn("[UIBridge] Failed to receive manifest from server")
		return nil
	end
	return Generator.fromJSON(jsonString)
end

-- ── Manifest builders (programmatic) ─────────────────────────────────────────

local function img(name: string, opts: any): any
	return {
		type = "ImageLabel",
		name = name,
		assetId = opts.assetId or "rbxassetid://0",
		x = opts.x or 0,
		y = opts.y or 0,
		width = opts.width or 100,
		height = opts.height or 100,
		anchorX = opts.anchorX ?? 0,
		anchorY = opts.anchorY ?? 0,
		scaleType = opts.scaleType or "Crop",
		visible = opts.visible != false,
		zIndex = opts.zIndex or 1,
		children = opts.children or {},
	}
end

local function lbl(name: string, opts: any): any
	return {
		type = "TextLabel",
		name = name,
		text = opts.text or "",
		x = opts.x or 0,
		y = opts.y or 0,
		width = opts.width or 100,
		height = opts.height or 30,
		anchorX = opts.anchorX ?? 0,
		anchorY = opts.anchorY ?? 0,
		textColor = opts.textColor or { r = 1, g = 1, b = 1 },
		textSize = opts.textSize or 18,
		font = opts.font or "Gotham",
		textWrapped = opts.textWrapped or false,
		textAlignX = opts.alignX or "Center",
		visible = opts.visible != false,
		zIndex = opts.zIndex or 1,
		children = opts.children or {},
	}
end

local function btn(name: string, opts: any): any
	return {
		type = "TextButton",
		name = name,
		text = opts.text or "Button",
		x = opts.x or 0,
		y = opts.y or 0,
		width = opts.width or 100,
		height = opts.height or 40,
		anchorX = opts.anchorX ?? 0,
		anchorY = opts.anchorY ?? 0,
		backgroundColor = opts.backgroundColor or { r = 0.2, g = 0.2, b = 0.2 },
		textColor = opts.textColor or { r = 1, g = 1, b = 1 },
		textSize = opts.textSize or 16,
		font = opts.font or "GothamBold",
		borderRadius = opts.borderRadius or 8,
		visible = opts.visible != false,
		interactable = opts.interactable != false,
		zIndex = opts.zIndex or 1,
		events = opts.events or {},
		children = opts.children or {},
	}
end

local function frame(name: string, opts: any): any
	return {
		type = "Frame",
		name = name,
		x = opts.x or 0,
		y = opts.y or 0,
		width = opts.width or 100,
		height = opts.height or 100,
		anchorX = opts.anchorX ?? 0,
		anchorY = opts.anchorY ?? 0,
		backgroundColor = opts.backgroundColor or { r = 0, g = 0, b = 0 },
		backgroundTransparency = opts.backgroundTransparency or 0,
		borderRadius = opts.borderRadius or 0,
		borderColor = opts.borderColor,
		borderWidth = opts.borderWidth,
		visible = opts.visible != false,
		zIndex = opts.zIndex or 1,
		children = opts.children or {},
	}
end

local function layout(listLayout: boolean, opts: any): any
	return {
		type = listLayout and "UIListLayout" or "UIGridLayout",
		padding = opts.padding or 8,
		horizontalWrap = opts.horizontalWrap or false,
		cellSize = opts.cellSize or 120,
		cellPadding = opts.cellPadding or 4,
		horizontalAlign = opts.horizontalAlign or "Center",
		verticalAlign = opts.verticalAlign or "Center",
	}
end

local function padding(opts: any): any
	return {
		type = "UIPadding",
		paddingTop = opts.top or opts.all or 8,
		paddingBottom = opts.bottom or opts.all or 8,
		paddingLeft = opts.left or opts.all or 8,
		paddingRight = opts.right or opts.all or 8,
	}
end

-- ── DSL: build a full manifest ───────────────────────────────────────────────

function Generator.build(name: string, opts: any): any
	opts = opts or {}
	return {
		name = name,
		canvasWidth = opts.canvasWidth or 1920,
		canvasHeight = opts.canvasHeight or 1080,
		scaleMode = opts.scaleMode or "ScaleToFit",
		ignoreContext = opts.ignoreContext or false,
		elements = opts.elements or {},
	}
end

-- ── Return ────────────────────────────────────────────────────────────────────

return setmetatable(Generator, {
	__call = function(_self, manifest: any, parent: GuiObject?): UIBridge
		return Generator.fromManifest(manifest, parent)
	end,
}) :: any

-- ── Exported helpers for convenience ──────────────────────────────────────────
-- Usar assim no código do jogo:
--   local U = require(game.ReplicatedStorage.UIBridge.Generator)
--   local myUI = U(build("MyScreen", {
--       elements = {
--           img("Bg", { x=0, y=0, width=1920, height=1080, assetId="rbxassetid://..." }),
--           btn("Play", { x=810, y=500, width=300, height=80, text="JOGAR",
--               events = { Activated = "onPlay" },
--               handlers = { onPlay = function() print("clicked!") end } }),
--       }
--   }))
--   myUI:build()
