--!strict
--[[
	UIMigrationController.luau
	Controlador genérico que carrega manifests de UI de fontes remotas
	e os aplica dinamicamente no jogo. Útil para atualizações de UI
	sem precisar de redeploy do cliente.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local UIBridge = require(
	ReplicatedStorage:WaitForChild("UIBridge")
		and ReplicatedStorage.UIBridge
		or script.Parent.UIBridge
)

local UIMigrationController = {
	Name = "UIMigrationController",
	_activeScreens = {},
}

-- ── Events ───────────────────────────────────────────────────────────────────
-- Use ReplicatedStorage events for cross-module communication
local ServerEvents = Instance.new("Folder")
ServerEvents.Name = "UIMigrationEvents"
ServerEvents.Parent = ReplicatedStorage

local ScreenShownEvent = Instance.new("RemoteEvent")
ScreenShownEvent.Name = "ScreenShown"
ScreenShownEvent.Parent = ServerEvents

local ScreenHiddenEvent = Instance.new("RemoteEvent")
ScreenHiddenEvent.Name = "ScreenHidden"
ScreenHiddenEvent.Parent = ServerEvents

-- ── Core ─────────────────────────────────────────────────────────────────────

function UIMigrationController.Init()
	-- Connect to server-driven UI events
	local uiEvent = ReplicatedStorage:FindFirstChild("ServerToClient_UIUpdate")
	if uiEvent then
		uiEvent.OnClientEvent:Connect(function(manifestJson: string, screenName: string)
			UIMigrationController.showScreen(manifestJson, screenName)
		end)
	end
end

function UIMigrationController.Start()
	-- Ready to receive UI updates
end

-- ── Screen management ────────────────────────────────────────────────────────

function UIMigrationController.showScreen(manifestJson: string, screenName: string): UIBridge?
	-- Hide current screen if different
	local current = UIMigrationController._activeScreens[screenName]
	if current then
		current:show()
		return current
	end

	-- Destroy previous screen with same name if exists
	local existing = UIMigrationController._activeScreens[screenName]
	if existing then
		existing:destroy()
		UIMigrationController._activeScreens[screenName] = nil
	end

	local bridge = UIBridge.fromJSON(manifestJson, Players.LocalPlayer:WaitForChild("PlayerGui"))
	if not bridge then return nil end

	UIMigrationController._activeScreens[screenName] = bridge
	bridge:show()

		if UIMigrationController.ScreenShown then
			ScreenShownEvent:FireAllClients(screenName)
		end

	return bridge
end

function UIMigrationController.hideScreen(screenName: string)
	local bridge = UIMigrationController._activeScreens[screenName]
	if not bridge then return end
	bridge:hide()
	if UIMigrationController.ScreenHidden then
		ScreenHiddenEvent:FireAllClients(screenName)
	end
end

function UIMigrationController.destroyScreen(screenName: string)
	local bridge = UIMigrationController._activeScreens[screenName]
	if not bridge then return end
	bridge:destroy()
	UIMigrationController._activeScreens[screenName] = nil
end

function UIMigrationController.destroyAll()
	for name, bridge in pairs(UIMigrationController._activeScreens) do
		bridge:destroy()
	end
	UIMigrationController._activeScreens = {}
end

function UIMigrationController.getScreen(screenName: string): UIBridge?
	return UIMigrationController._activeScreens[screenName]
end

function UIMigrationController.listScreens(): {string}
	local names = {}
	for name in pairs(UIMigrationController._activeScreens) do
		table.insert(names, name)
	end
	return names
end

return UIMigrationController
