--!strict
--[[
	AssetManager.luau
	Sistema de gestão de assets no Roblox Studio.
	Importa PNGs locais e gera Asset IDs únicos automaticamente.

	Uso no Roblox Studio (Execute ou rodar via Plugin):
		local AssetManager = require(game.ReplicatedStorage.UIBridge.AssetManager)
		AssetManager.ImportFolder("C:/caminho/da/pasta/pngs")
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

local AssetManager = {}

-- ── Constants ────────────────────────────────────────────────────────────────

local ASSET_FOLDER_NAME = "UIAssets"
local MANIFEST_FILE = "_manifest.json"

-- ── Local File System Access (Studio only) ───────────────────────────────────

function AssetManager.ImportFolder(localFolderPath: string): { [string]: string }?
	if RunService:IsStudio() == false then
		warn("[AssetManager] ImportFolder só funciona no Roblox Studio")
		return nil
	end

	-- Nota: O Roblox Studio não permite acesso direto ao filesystem via Luau.
	-- Este método espera que os assets já estejam em ReplicatedStorage.
	-- Para importação real, use o plugin abaixo ou o script Node.js.

	warn("[AssetManager] Para importar assets:")
	warn("  1. Crie a pasta ReplicatedStorage > UIAssets > <nome_da_tela>")
	warn("  2. Arraste os PNGs para essa pasta no Explorer")
	warn("  3. Execute: AssetManager.LinkAssets(\"<nome_da_tela>\")")
	return nil
end

function AssetManager.LinkAssets(screenName: string): { [string]: string }
	-- Encontra assets na pasta UIAssets/<screenName> e mapeia para o manifest
	local uiAssets = ReplicatedStorage:FindFirstChild(ASSET_FOLDER_NAME)
	if not uiAssets then
		warn(`[AssetManager] Pasta ${ASSET_FOLDER_NAME} não encontrada`)
		return {}
	end

	local screenFolder = uiAssets:FindFirstChild(screenName)
	if not screenFolder then
		warn(`[AssetManager] Pasta ${screenName} não encontrada em UIAssets`)
		return {}
	end

	local mapping: { [string]: string } = {}
	for _, child in ipairs(screenFolder:GetChildren()) do
		if child:IsA("Image") or child:IsA("Decal") then
			local assetId = tostring(child.AssetId)
			mapping[child.Name] = assetId
		end
	end

	print(`[AssetManager] ${#mapping} assets linkados em ${screenName}`)
	return mapping
end

function AssetManager.UpdateManifest(manifestJson: string, assetMapping: { [string]: string })
	local manifest: any = HttpService:JSONDecode(manifestJson)
	if not manifest or not manifest.assets then
		warn("[AssetManager] Manifest inválido")
		return
	end

	local updated = 0
	for _, asset in ipairs(manifest.assets) do
		local mappedId = assetMapping[asset.uniqueId]
			or assetMapping[asset.filename]
			or assetMapping[asset.originalHash]
		if mappedId and mappedId ~= "0" then
			asset.assetId = "rbxassetid://" .. mappedId
			updated += 1
		end
	end

	print(`[AssetManager] ${updated}/${#manifest.assets} assets atualizados`)
	return manifest
end

-- ── Quick import workflow ─────────────────────────────────────────────────────

function AssetManager.QuickImport(screenName: string)
	-- Workflow completo: link assets + update manifest
	local assets = AssetManager.LinkAssets(screenName)
	if #assets == 0 then
		warn("[AssetManager] Nenhum asset encontrado. Importe os PNGs primeiro.")
		return
	end

	-- Load current manifest
	local bridgeFolder = ReplicatedStorage:FindFirstChild("UIBridge")
	if not bridgeFolder then
		warn("[AssetManager] Pasta UIBridge não encontrada")
		return
	end

	local manifestValue = bridgeFolder:FindFirstChild("CurrentManifest")
	if not manifestValue then
		warn("[AssetManager] Manifest não encontrado")
		return
	end

	local updatedManifest = AssetManager.UpdateManifest(manifestValue.Value, assets)
	if updatedManifest then
		manifestValue.Value = HttpService:JSONEncode(updatedManifest)
		print("[AssetManager] Manifest atualizado!")
	end
end

return AssetManager
