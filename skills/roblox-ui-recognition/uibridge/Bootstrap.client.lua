--!strict
--[[
	Bootstrap.client.lua
	Script principal que inicializa o sistema de UI.
	
	Uso:
		Colocar em StarterPlayerScripts/Bootstrap.client.lua
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")

-- Aguardar ReplicatedStorage carregar
repeat task.wait() until ReplicatedStorage

-- Carregar UIBridge
local uibridge = ReplicatedStorage:WaitForChild("UIBridge")

-- Carregar módulos
local UIBridge = require(uibridge.UIBridge)
local GameUIManager = require(uibridge.GameUIManager)

-- Configurar UI inicial
local function bootstrap()
	local player = Players.LocalPlayer
	
	-- Mostrar tela inicial ( MainMenu )
	local mainMenu = GameUIManager:Show("MainMenu")
	
	if mainMenu then
		print("[Bootstrap] UI inicializada com sucesso!")
		
		-- Exemplo: ouvir botão de play
		local playButton = mainMenu:FindFirstChild("PlayButton")
		if playButton and playButton:IsA("TextButton") then
			playButton.Activated:Connect(function()
				print("[Bootstrap] Botão Play pressionado!")
				GameUIManager:Switch("MainMenu", "GameHUD")
			end)
		end
	end
end

-- Iniciar quando player entrar
Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function()
		task.delay(1, bootstrap)
	end)
end)

-- Iniciar imediatamente se já estiver logado
if Players.LocalPlayer then
	bootstrap()
end

print("[Bootstrap] Sistema de UI carregado!")
