--!strict
--[[
	QuickTest.lua
	Script de teste rápido para verificar se o sistema de UI funciona.
	
	Uso:
		Colar no Output do Roblox Studio e executar
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

print("🧪 Teste Rápido do Sistema UI")
print("═".rep(40))

-- Verificar estrutura
local uibridge = ReplicatedStorage:FindFirstChild("UIBridge")
if uibridge then
	print("✅ UIBridge encontrado")
	
	-- Listar módulos
	for _, child in ipairs(uibridge:GetChildren()) do
		if child:IsA("ModuleScript") then
			print(string.format("  • %s", child.Name))
		end
	end
else
	print("❌ UIBridge não encontrado")
end

-- Verificar assets
local uiAssets = ReplicatedStorage:FindFirstChild("UIAssets")
if uiAssets then
	print("\n📁 Telas disponíveis:")
	for _, screen in ipairs(uiAssets:GetChildren()) do
		if screen:IsA("Folder") then
			local hasManifest = screen:FindFirstChild("_manifest_processed")
			local hasController = screen:FindFirstChild("_controller")
			print(string.format("  • %s %s %s", 
				screen.Name,
				hasManifest and "[✓]" or "[ ]",
				hasController and "[✓]" or "[ ]"
			))
		end
	end
else
	print("\n❌ Pasta UIAssets não encontrada")
end

print("\n" .. "═".rep(40))
print("✅ Teste concluído!")
