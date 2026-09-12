/**
 * templates.js
 *
 * Sistema de templates pré-definidos para exportação rápida.
 * Cada template contém:
 *   - Estrutura de layers esperada
 *   - Posições e tamanhos sugeridos
 *   - Configuração de responsive
 *   - Código Luau boilerplate
 *
 * Templates disponíveis:
 *   - MainMenu      → Menu principal com play/settings
 *   - HUD           → Interface durante gameplay
 *   - Shop          → Loja de itens
 *   - Settings      → Tela de configurações
 *   - Inventory     → Inventário/grid de itens
 *   - Loading       → Tela de carregamento
 */

const TEMPLATES = {
  MainMenu: {
    name: 'MainMenu',
    description: 'Menu principal com botão Play e configurações',
    canvasWidth: 1920,
    canvasHeight: 1080,
    scaleMode: 'ScaleToFit',
    layers: [
      { name: 'background', type: 'background', x: 0, y: 0, width: 1920, height: 1080, fill: '#1E1E2E', strategy: 'Fill' },
      { name: 'title_text', type: 'label', x: 460, y: 200, width: 1000, height: 100, text: 'GAME TITLE', size: 64, strategy: 'ScaleToFit' },
      { name: 'btn_play', type: 'button', x: 760, y: 500, width: 400, height: 100, fill: '#89B4FA', text: 'PLAY', size: 32, strategy: 'ScaleToFit' },
      { name: 'btn_settings', type: 'button', x: 810, y: 650, width: 300, height: 80, fill: '#A6E3A1', text: 'SETTINGS', size: 24, strategy: 'ScaleToFit' },
      { name: 'btn_quit', type: 'button', x: 830, y: 780, width: 260, height: 60, fill: '#F38BA8', text: 'QUIT', size: 20, strategy: 'ScaleToFit' },
      { name: 'version_label', type: 'label', x: 1750, y: 1030, width: 150, height: 30, text: 'v1.0.0', size: 16, strategy: 'FixedSize' },
    ],
    boilerplate: `--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local MainMenu = {}
MainMenu.__index = MainMenu

function MainMenu.new()
    local self = setmetatable({}, MainMenu)
    self.screenGui = nil
    return self
end

function MainMenu:Show()
    if self.screenGui then
        self.screenGui.Enabled = true
        return
    end
    -- Load from ReplicatedStorage or build dynamically
    self.screenGui = Instance.new("ScreenGui")
    self.screenGui.Name = "MainMenu"
    self.screenGui.ResetOnSpawn = false
    self.screenGui.IgnoreGuiInset = true
    self.screenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

function MainMenu:Hide()
    if self.screenGui then
        self.screenGui.Enabled = false
    end
end

function MainMenu:Destroy()
    if self.screenGui then
        self.screenGui:Destroy()
        self.screenGui = nil
    end
end

return MainMenu`,
  },

  HUD: {
    name: 'HUD',
    description: 'Interface durante gameplay (vida, score, minimapa)',
    canvasWidth: 1920,
    canvasHeight: 1080,
    scaleMode: 'ScaleToFit',
    layers: [
      { name: 'hp_bar_bg', type: 'bar', x: 20, y: 20, width: 300, height: 30, fill: '#333333', strategy: 'FixedSize' },
      { name: 'hp_bar_fill', type: 'bar', x: 22, y: 22, width: 296, height: 26, fill: '#F38BA8', strategy: 'FixedSize' },
      { name: 'score_label', type: 'label', x: 1750, y: 20, width: 150, height: 40, text: 'SCORE: 0', size: 28, strategy: 'FixedSize' },
      { name: 'timer_label', type: 'label', x: 900, y: 20, width: 120, height: 40, text: '02:00', size: 32, strategy: 'FixedSize' },
      { name: 'minimap_frame', type: 'panel', x: 1600, y: 800, width: 300, height: 240, strategy: 'FixedSize' },
      { name: 'ammo_label', type: 'label', x: 20, y: 950, width: 200, height: 40, text: 'AMMO: 30/90', size: 24, strategy: 'FixedSize' },
    ],
    boilerplate: `--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local HUD = {}
HUD.__index = HUD

function HUD.new()
    local self = setmetatable({}, HUD)
    self.screenGui = nil
    self.hpValue = 100
    self.score = 0
    return self
end

function HUD:Show()
    if self.screenGui then return end
    self.screenGui = Instance.new("ScreenGui")
    self.screenGui.Name = "HUD"
    self.screenGui.ResetOnSpawn = false
    self.screenGui.IgnoreGuiInset = true
    self.screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    self.screenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
    self:UpdateHealth(100)
end

function HUD:Hide()
    if self.screenGui then
        self.screenGui.Enabled = false
    end
end

function HUD:UpdateHealth(value)
    self.hpValue = math.max(0, math.min(100, value))
    -- Update HP bar fill width proportionally
end

function HUD:UpdateScore(value)
    self.score = value
end

function HUD:Destroy()
    if self.screenGui then
        self.screenGui:Destroy()
        self.screenGui = nil
    end
end

return HUD`,
  },

  Shop: {
    name: 'Shop',
    description: 'Loja de itens com grid de produtos',
    canvasWidth: 1920,
    canvasHeight: 1080,
    scaleMode: 'ScaleToFit',
    layers: [
      { name: 'shop_bg', type: 'background', x: 0, y: 0, width: 1920, height: 1080, fill: '#1E1E2E', strategy: 'Fill' },
      { name: 'shop_title', type: 'label', x: 600, y: 40, width: 800, height: 60, text: 'SHOP', size: 48, strategy: 'ScaleToFit' },
      { name: 'coin_balance', type: 'label', x: 1650, y: 40, width: 250, height: 50, text: '🪙 1,250', size: 28, strategy: 'FixedSize' },
      { name: 'item_1', type: 'panel', x: 100, y: 150, width: 350, height: 400, fill: '#313244', strategy: 'ScaleToFit' },
      { name: 'item_2', type: 'panel', x: 500, y: 150, width: 350, height: 400, fill: '#313244', strategy: 'ScaleToFit' },
      { name: 'item_3', type: 'panel', x: 900, y: 150, width: 350, height: 400, fill: '#313244', strategy: 'ScaleToFit' },
      { name: 'item_4', type: 'panel', x: 1300, y: 150, width: 350, height: 400, fill: '#313244', strategy: 'ScaleToFit' },
      { name: 'btn_back', type: 'button', x: 20, y: 20, width: 120, height: 50, fill: '#6C7086', text: '← BACK', size: 20, strategy: 'FixedSize' },
    ],
    boilerplate: `--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shop = {}
Shop.__index = Shop

function Shop.new()
    local self = setmetatable({}, Shop)
    self.items = {}
    self.selectedItem = nil
    return self
end

function Shop:Show()
    self.screenGui = Instance.new("ScreenGui")
    self.screenGui.Name = "Shop"
    self.screenGui.ResetOnSpawn = false
    self.screenGui.IgnoreGuiInset = true
    self.screenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

function Shop:Hide()
    if self.screenGui then
        self.screenGui.Enabled = false
    end
end

function Shop:RefreshItems(items)
    self.items = items or {}
    -- Rebuild grid from items data
end

function Shop:Purchase(itemId, price)
    -- Handle purchase logic
    local success, result = ReplicatedStorage:WaitForChild("BuyItem"):InvokeServer(itemId, price)
    return success
end

return Shop`,
  },

  Settings: {
    name: 'Settings',
    description: 'Tela de configurações do jogo',
    canvasWidth: 1920,
    canvasHeight: 1080,
    scaleMode: 'ScaleToFit',
    layers: [
      { name: 'settings_bg', type: 'background', x: 0, y: 0, width: 1920, height: 1080, fill: '#1E1E2E', strategy: 'Fill' },
      { name: 'settings_panel', type: 'panel', x: 460, y: 100, width: 1000, height: 800, fill: '#313244', strategy: 'ScaleToFit' },
      { name: 'settings_title', type: 'label', x: 500, y: 120, width: 900, height: 60, text: 'SETTINGS', size: 40, strategy: 'ScaleToFit' },
      { name: 'vol_master', type: 'label', x: 500, y: 220, width: 200, height: 40, text: 'Master Volume', size: 24, strategy: 'ScaleToFit' },
      { name: 'vol_music', type: 'label', x: 500, y: 300, width: 200, height: 40, text: 'Music Volume', size: 24, strategy: 'ScaleToFit' },
      { name: 'vol_sfx', type: 'label', x: 500, y: 380, width: 200, height: 40, text: 'SFX Volume', size: 24, strategy: 'ScaleToFit' },
      { name: 'btn_apply', type: 'button', x: 710, y: 750, width: 200, height: 60, fill: '#89B4FA', text: 'APPLY', size: 24, strategy: 'ScaleToFit' },
      { name: 'btn_cancel', type: 'button', x: 950, y: 750, width: 200, height: 60, fill: '#F38BA8', text: 'CANCEL', size: 24, strategy: 'ScaleToFit' },
    ],
    boilerplate: `--!strict
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local Settings = {}
Settings.__index = Settings

function Settings.new()
    local self = setmetatable({}, Settings)
    self.volume = { master = 1.0, music = 1.0, sfx = 1.0 }
    return self
end

function Settings:Show()
    self.screenGui = Instance.new("ScreenGui")
    self.screenGui.Name = "Settings"
    self.screenGui.ResetOnSpawn = false
    self.screenGui.IgnoreGuiInset = true
    self.screenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

function Settings:Hide()
    if self.screenGui then
        self.screenGui.Enabled = false
    end
end

function Settings:Apply()
    -- Save settings to ReplicatedStorage or LocalPlayer
    game:GetService("ReplicatedStorage"):WaitForChild("SaveSettings"):FireServer(self.volume)
end

return Settings`,
  },

  Inventory: {
    name: 'Inventory',
    description: 'Inventário com grid de itens arrastáveis',
    canvasWidth: 1920,
    canvasHeight: 1080,
    scaleMode: 'ScaleToFit',
    layers: [
      { name: 'inv_bg', type: 'background', x: 0, y: 0, width: 1920, height: 1080, fill: '#1E1E2E', strategy: 'Fill' },
      { name: 'inv_panel', type: 'panel', x: 200, y: 80, width: 1500, height: 900, fill: '#313244', strategy: 'ScaleToFit' },
      { name: 'inv_title', type: 'label', x: 250, y: 100, width: 400, height: 50, text: 'INVENTORY', size: 36, strategy: 'ScaleToFit' },
      { name: 'inv_grid', type: 'panel', x: 250, y: 180, width: 1400, height: 700, strategy: 'ScaleToFit' },
      { name: 'inv_count', type: 'label', x: 1500, y: 100, width: 150, height: 40, text: '0/50', size: 20, strategy: 'FixedSize' },
      { name: 'btn_close', type: 'button', x: 1600, y: 80, width: 80, height: 50, fill: '#F38BA8', text: '×', size: 28, strategy: 'FixedSize' },
    ],
    boilerplate: `--!strict
local Players = game:GetService("Players")
local DragService = game:GetService("DragService")

local Inventory = {}
Inventory.__index = Inventory

function Inventory.new()
    local self = setmetatable({}, Inventory)
    self.slots = {}
    self.maxSlots = 50
    return self
end

function Inventory:Show()
    self.screenGui = Instance.new("ScreenGui")
    self.screenGui.Name = "Inventory"
    self.screenGui.ResetOnSpawn = false
    self.screenGui.IgnoreGuiInset = true
    self.screenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

function Inventory:Hide()
    if self.screenGui then
        self.screenGui.Enabled = false
    end
end

function Inventory:Refresh(slots)
    self.slots = slots or {}
    -- Rebuild grid UI
end

function Inventory:MoveItem(fromSlot, toSlot)
    -- Handle item drag/drop
end

return Inventory`,
  },

  Loading: {
    name: 'Loading',
    description: 'Tela de carregamento com barra de progresso',
    canvasWidth: 1920,
    canvasHeight: 1080,
    scaleMode: 'ScaleToFit',
    layers: [
      { name: 'loading_bg', type: 'background', x: 0, y: 0, width: 1920, height: 1080, fill: '#1E1E2E', strategy: 'Fill' },
      { name: 'loading_logo', type: 'icon', x: 760, y: 300, width: 400, height: 200, strategy: 'ScaleToFit' },
      { name: 'loading_title', type: 'label', x: 660, y: 550, width: 600, height: 60, text: 'LOADING...', size: 36, strategy: 'ScaleToFit' },
      { name: 'progress_bar_bg', type: 'bar', x: 460, y: 700, width: 1000, height: 20, fill: '#45475a', strategy: 'ScaleToFit' },
      { name: 'progress_bar_fill', type: 'bar', x: 462, y: 702, width: 996, height: 16, fill: '#89B4FA', strategy: 'ScaleToFit' },
      { name: 'loading_pct', type: 'label', x: 910, y: 750, width: 100, height: 30, text: '0%', size: 20, strategy: 'FixedSize' },
    ],
    boilerplate: `--!strict
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local Loading = {}
Loading.__index = Loading

function Loading.new()
    local self = setmetatable({}, Loading)
    self.progress = 0
    return self
end

function Loading:Show()
    self.screenGui = Instance.new("ScreenGui")
    self.screenGui.Name = "Loading"
    self.screenGui.ResetOnSpawn = false
    self.screenGui.IgnoreGuiInset = true
    self.screenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

function Loading:Hide()
    if self.screenGui then
        self.screenGui:Destroy()
        self.screenGui = nil
    end
end

function Loading:SetProgress(value)
    self.progress = math.max(0, math.min(100, value))
    -- Update progress bar visual
end

function Loading:UpdateText(text)
    -- Update loading message
end

return Loading`,
  },
};

// ── Factory Functions ────────────────────────────────────────────────────────────

function getTemplate(name) {
    return TEMPLATES[name] || null;
}

function listTemplates() {
    return Object.keys(TEMPLATES).map(key => ({
        id: key,
        name: TEMPLATES[key].name,
        description: TEMPLATES[key].description,
        layerCount: TEMPLATES[key].layers.length,
    }));
}

function buildFromTemplate(templateName, customizations = {}) {
    const template = TEMPLATES[templateName];
    if (!template) return null;

    return {
        ...template,
        layers: template.layers.map(l => ({
            ...l,
            ...customizations[l.name],
        })),
    };
}

// ── Export ───────────────────────────────────────────────────────────────────────

module.exports = { TEMPLATES, getTemplate, listTemplates, buildFromTemplate };
