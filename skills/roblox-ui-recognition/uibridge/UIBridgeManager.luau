--!strict
--[[
	UIBridgeManager.luau
	Gerencia a importação e atualização de assets UI no Roblox Studio.
	Uso: execute este script no Roblox Studio para importar PNGs de uma pasta local
	e gerar automaticamente os Asset IDs.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

local UIBridgeManager = {}

local PLACEHOLDER_PREFIX = "PLACEHOLDER_"
local ASSET_DIR = "UIAssets"

-- ── Local file scan (only works in Studio, not in-game) ──────────────────────

function UIBridgeManager.ScanLocalFolder(folderPath: string): { [string]: string }?
	-- Returns a map of placeholder → assetId for each PNG found
	if RunService:IsStudio() == false then
		warn("[UIBridgeManager] ScanLocalFolder só funciona no Roblox Studio")
		return nil
	end

	-- In Studio we can't directly read the filesystem, so we use a web-based approach
	-- or the user manually imports the PNGs and we match by filename
	warn("[UIBridgeManager] Para importar assets, arraste os PNGs da pasta para o Explorer do Roblox")
	warn("[UIBridgeManager] Depois execute: UIBridgeManager.UpdateFromManifest(manifestData)")
	return nil
end

-- ── Manifest-based update ─────────────────────────────────────────────────────

function UIBridgeManager.UpdateFromManifest(manifest: any, assetMap: { [string]: string })
	-- assetMap: { ["PLACEHOLDER_0"] = "rbxassetid://123456789", ... }
	if not manifest or not manifest.placeholders then
		warn("[UIBridgeManager] Manifest inválido")
		return
	end

	for _, ph in ipairs(manifest.placeholders) do
		local assetId = assetMap[ph.placeholder]
		if assetId then
			ph.assetId = assetId
		end
	end

	-- Save updated manifest to ReplicatedStorage
	local UpdatedFolder = ReplicatedStorage:FindFirstChild("UIBridge")
		if or Instance.new("Folder", ReplicatedStorage)
	UpdatedFolder.Name = "UIBridge"

	local manifestData = Instance.new("StringValue", UpdatedFolder)
	manifestData.Name = "CurrentManifest"
	manifestData.Value = HttpService:JSONEncode(manifest)

	print("[UIBridgeManager] Manifest atualizado com sucesso!")
	print("[UIBridgeManager] Use o Controller para aplicar a UI:")
	print('  local UIBridge = require(game.ReplicatedStorage.UIBridge.UIBridge)')
	print('  local bridge = UIBridge.fromJSON(manifestData.Value)')
	print("  bridge:build()")
end

-- ── Auto-detect from imported assets ─────────────────────────────────────────

function UIBridgeManager.DetectFromAssets(manifest: any): { [string]: string }
	-- Scans ReplicatedStorage for assets matching manifest placeholders
	local assetMap: { [string]: string } = {}

	local assetsFolder = ReplicatedStorage:FindFirstChild(ASSET_DIR)
	if not assetsFolder then
		warn("[UIBridgeManager] Pasta UIAssets não encontrada em ReplicatedStorage")
		return assetMap
	end

	for _, placeholder in ipairs(manifest.placeholders) do
		for _, asset in ipairs(assetsFolder:GetChildren()) do
			if asset:IsA("Image") or asset:IsA("Decal") then
				local assetName = asset.Name:gsub("%.[^.]+$", "")
				local phName = placeholder.name:gsub("%.[^.]+$", "")
				if assetName == phName then
					assetMap[placeholder.placeholder] = tostring(asset.AssetId)
					break
				end
			end
		end
	end

	return assetMap
end

-- ── One-liner usage ───────────────────────────────────────────────────────────

function UIBridgeManager.ImportAndBuild(manifestJson: string, assetFolder: string?)
	-- Quick import: load manifest, detect assets, build UI
	local HttpService = game:GetService("HttpService")
	local manifest: any = HttpService:JSONDecode(manifestJson)

	local detected = UIBridgeManager.DetectFromAssets(manifest)
	UIBridgeManager.UpdateFromManifest(manifest, detected)

	-- Build the UI
	local UIBridge = require(ReplicatedStorage:WaitForChild("UIBridge"))
	local bridge = UIBridge.fromJSON(HttpService:JSONEncode(manifest),
		Players.LocalPlayer:WaitForChild("PlayerGui"))
	bridge:build()
	bridge:show()

	print("[UIBridgeManager] UI construída com sucesso!")
	return bridge
end

return UIBridgeManager
