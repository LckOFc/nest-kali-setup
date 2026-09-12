--!strict
--[[
	GameUIManager.luau
	Gerenciador completo de telas UI para Roblox.
	
	Uso:
		local UIManager = require(script.Parent.GameUIManager)
		UIManager:Show("MainMenu")
		UIManager:Hide("MainMenu")
		UIManager:Destroy("MainMenu")
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local GameUIManager = {}
GameUIManager.__index = GameUIManager

-- ── Configurações ─────────────────────────────────────────────────────────────

local CONFIG = {
	DefaultCanvasWidth = 1920,
	DefaultCanvasHeight = 1080,
	AnimationDuration = 0.3,
	AssetRoot = "ReplicatedStorage.UIAssets",
}

-- ── Estado ─────────────────────────────────────────────────────────────────────

local screens = {} -- name -> ScreenGui
local controllers = {} -- name -> controller module

-- ── Construtor ────────────────────────────────────────────────────────────────

function GameUIManager.new()
	local self = setmetatable({}, GameUIManager)
	self:singleton()
	return self
end

function GameUIManager:singleton()
	if GameUIManager.instance then
		return GameUIManager.instance
	end
	GameUIManager.instance = self
	return self
end

-- ── Métodos Principais ────────────────────────────────────────────────────────

/**
 * Mostra uma tela
 */
function GameUIManager:Show(screenName: string, parent: Instance?)
	if screens[screenName] then
		screens[screenName].Enabled = true
		print(string.format("[UIManager] Tela '%s' exibida", screenName))
		return screens[screenName]
	end
	
	-- Tentar carregar do ReplicatedStorage
	local screenGui = self:_loadScreen(screenName, parent)
	if screenGui then
		screens[screenName] = screenGui
		screenGui.Enabled = true
		print(string.format("[UIManager] Tela '%s' carregada e exibida", screenName))
		return screenGui
	end
	
	warn(string.format("[UIManager] Tela '%s' não encontrada", screenName))
	return nil
end

/**
 * Esconde uma tela
 */
function GameUIManager:Hide(screenName: string)
	local screen = screens[screenName]
	if screen then
		screen.Enabled = false
		print(string.format("[UIManager] Tela '%s' ocultada", screenName))
	end
end

/**
 * Destrói uma tela
 */
function GameUIManager:Destroy(screenName: string)
	local screen = screens[screenName]
	if screen then
		screen:Destroy()
		screens[screenName] = nil
		print(string.format("[UIManager] Tela '%s' destruída", screenName))
	end
end

/**
 * Alterna entre telas (mostra uma, esconde outras)
 */
function GameUIManager:Switch(fromScreen: string, toScreen: string)
	self:Hide(fromScreen)
	self:Show(toScreen)
end

/**
 * Verifica se uma tela está visível
 */
function GameUIManager:IsVisible(screenName: string): boolean
	local screen = screens[screenName]
	return screen and screen.Enabled or false
end

/**
 * Lista todas as telas carregadas
 */
function GameUIManager:ListScreens(): { string }
	local result = {}
	for name, screen in pairs(screens) do
		table.insert(result, name)
	end
	return result
end

-- ── Métodos Internos ──────────────────────────────────────────────────────────

/**
 * Carrega uma tela do ReplicatedStorage
 */
function GameUIManager:_loadScreen(screenName: string, parent: Instance?): ScreenGui?
	local assetFolder = ReplicatedStorage:FindFirstChild(CONFIG.AssetRoot):FindFirstChild(screenName)
	if not assetFolder then
		warn(string.format("[UIManager] Pasta de assets não encontrada: %s", screenName))
		return nil
	end
	
	-- Verificar se tem controller
	local controllerScript = assetFolder:FindFirstChild("_controller")
	if not controllerScript then
		warn(string.format("[UIManager] Controller não encontrado: %s", screenName))
		return nil
	end
	
	-- Criar ScreenGui
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = screenName
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	screenGui.Parent = parent or Players.LocalPlayer:WaitForChild("PlayerGui")
	
	-- Carregar controller e construir UI
	local success, controller = pcall(function()
		return require(controllerScript)
	end)
	
	if success and controller then
		controllers[screenName] = controller
		controller.new():Build(screenGui)
		return screenGui
	else
		warn(string.format("[UIManager] Erro ao carregar controller: %s", controller))
		screenGui:Destroy()
		return nil
	end
end

-- ── Funções de Conveniência ───────────────────────────────────────────────────

/**
 * Mostra tela e espera interação do usuário
 */
function GameUIManager:ShowAndWait(screenName: string, signal: RBXScriptSignal)
	self:Show(screenName)
	signal:Wait()
	self:Hide(screenName)
end

/**
 * Anima transição entre telas
 */
function GameUIManager:AnimatedSwitch(fromScreen: string, toScreen: string)
	local from = screens[fromScreen]
	local to = screens[toScreen]
	
	if from and to then
		-- Animar fade out
		local tweenInfo = TweenInfo.new(CONFIG.AnimationDuration, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
		local tween = TweenService:Create(from, tweenInfo, { BackgroundTransparency = 1 })
		tween:Play()
		tween.Completed:Wait()
		
		from.Enabled = false
		
		-- Animar fade in
		to.Enabled = true
		to.BackgroundTransparency = 1
		local tween2 = TweenService:Create(to, tweenInfo, { BackgroundTransparency = 0 })
		tween2:Play()
	end
end

-- ── Exportações ─────────────────────────────────────────────────────────────────

return GameUIManager
