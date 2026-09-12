--[[
	ExportToRoblox.plugin.lua
	Plugin do Roblox Studio que automatiza a importação de assets UI.

	Instalação:
	 1. Abra o Roblox Studio
	 2. View > Plugins > Plugin Editor
	 3. Cole este código no script principal
	 4. Salve e execute

	Funções:
	  - ImportAssets: importa PNGs de uma pasta local
	  - LinkAssets: conecta assets importados ao manifest
	  - GenerateAssetIDs: gera lista de IDs para cópia
]]

local Plugin = Plugin or {}
local plugin = Plugin

-- ── Plugin setup ──────────────────────────────────────────────────────────────

local function onCreate()
	local tab = plugin:CreateTab("UI Bridge")
	local importBtn = tab:CreateButton("Importar Assets da Pasta")
	local linkBtn = tab:CreateButton("Linkar Assets ao Manifest")
	local copyBtn = tab:CreateButton("Copiar Asset IDs")

	local statusLabel = tab:CreateLabel("Pronto")

	importBtn.Click:Connect(function()
		statusLabel.Text = "Abrindo seletor de pasta..."
		-- Em plugins Roblox, usamos um caminho fixo ou prompt
		local folderPath = "C:/Users/devel/Downloads/ui_export" -- configurável
		local ReplicatedStorage = game:GetService("ReplicatedStorage")
		local AssetManager = require(ReplicatedStorage:WaitForChild("UIBridge").AssetManager)
		local result = AssetManager.ImportFolder(folderPath)
		if result then
			statusLabel.Text = string.format("Importados: %d assets", #result)
		else
			statusLabel.Text = "Use o AssetBundler primeiro"
		end
	end)

	linkBtn.Click:Connect(function()
		local ReplicatedStorage = game:GetService("ReplicatedStorage")
		local AssetManager = require(ReplicatedStorage.UIBridge.AssetManager)
		local mapping = AssetManager.LinkAssets("Lobby") -- mudar nome conforme necessário
		statusLabel.Text = string.format("Linkados: %d assets", #mapping)
	end)

	copyBtn.Click:Connect(function()
		local ReplicatedStorage = game:GetService("ReplicatedStorage")
		local AssetManager = require(ReplicatedStorage.UIBridge.AssetManager)
		local mapping = AssetManager.LinkAssets("Lobby")
		local ids = {}
		for name, id in pairs(mapping) do
			table.insert(ids, name .. "=" .. id)
		end
		game:GetService("Clipboard"):SetString(table.concat(ids, ", "))
		statusLabel.Text = "IDs copiados!"
	end)
end

plugin.onCreatePluginTabContainer:Connect(onCreate)

return plugin
