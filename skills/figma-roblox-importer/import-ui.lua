-- Figma/Photoshop to Roblox UI Importer
-- ======================================
-- Plugin do Roblox Studio
-- 
-- Instalacao:
--   1. Copie este arquivo para:
--      C:\Program Files\Roblox\Versions\version-Lua\plugins\FigmaPS2Roblox.lua
--   2. Ou use Rojo: adicione ao default.project.json
--   3. Abra o Roblox Studio -> Plugins -> Manager -> Enable
--
-- Uso:
--   Plugins > FigmaPS2Roblox > Importar JSON
--   Plugins > FigmaPS2Roblox > Importar Lua
--   Plugins > FigmaPS2Roblox > Exportar Selecao
--
-- Features:
--   - Importa spec.json gerado pelo Photoshop/Figma
--   - Importa codigo Luau gerado pelo conversor Python
--   - Cria instancias diretamente no Studio
--   - Suporta UIListLayout, UICorner, UIStroke, UIGradient
--   - Exporta selecao de volta para JSON

local FigmaPS2Roblox = {}
local PLUGIN_NAME = "FigmaPS2Roblox"
local TOOLBAR_NAME = "Figma/PS to Roblox"

-- Services
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")
local HttpService = game:GetService("HttpService")
local PluginService = game:GetService("PluginService")

-- Configuration
local CONFIG = {
    CanvasWidth = 1920,
    CanvasHeight = 1080,
    AutoDetectLayouts = true,
    GenerateScripts = true,
    OutputPath = "",
}

-- ============================================================
-- PLUGIN INITIALIZATION
-- ============================================================

function FigmaPS2Roblox:Initialize(p)
    local plugin = p
    local toolbar = plugin:CreateToolbar(TOOLBAR_NAME)
    
    -- Botao Importar JSON
    local importJsonBtn = toolbar:CreateButton(
        "Importar JSON",
        "Importa UI de spec.json (Photoshop/Figma)",
        "rbxasset://plugins/images/cog_icons_refresh.png"
    )
    importJsonBtn.ClickableWhenViewportOutOfFocus = true
    
    -- Botao Importar Lua
    local importLuaBtn = toolbar:CreateButton(
        "Importar Lua",
        "Importa codigo Luau gerado pelo conversor",
        "rbxasset://plugins/images/cog_icons_refresh.png"
    )
    importLuaBtn.ClickableWhenViewportOutOfFocus = true
    
    -- Botao Exportar
    local exportBtn = toolbar:CreateButton(
        "Exportar Selecao",
        "Exporta UI selecionada para JSON",
        "rbxasset://plugins/images/cog_icons_refresh.png"
    )
    exportBtn.ClickableWhenViewportOutOfFocus = true
    
    -- Botao Preview
    local previewBtn = toolbar:CreateButton(
        "Preview",
        "Mostra preview da UI importada",
        "rbxasset://plugins/images/cog_icons_refresh.png"
    )
    previewBtn.ClickableWhenViewportOutOfFocus = true
    
    -- Bindings
    importJsonBtn.Click:SetConnect(function()
        self:ShowFilePicker("json")
    end)
    
    importLuaBtn.Click:SetConnect(function()
        self:ShowFilePicker("lua")
    end)
    
    exportBtn.Click:SetConnect(function()
        self:ExportSelection()
    end)
    
    previewBtn.Click:SetConnect(function()
        self:ShowPreview()
    end)
    
    print("[FigmaPS2Roblox] Plugin initialized")
end

-- ============================================================
-- FILE PICKER
-- ============================================================

function FigmaPS2Roblox:ShowFilePicker(fileType)
    -- Open file picker via OS dialog
    local filePath = PluginService:OpenDialog(
        "Select " .. string.upper(fileType) .. " file",
        "All Files|*.*",
        "",
        false
    )
    
    if not filePath or filePath == "" then
        return
    end
    
    if fileType == "json" then
        self:ImportJSON(filePath)
    elseif fileType == "lua" then
        self:ImportLua(filePath)
    end
end

-- ============================================================
-- JSON IMPORTER
-- ============================================================

function FigmaPS2Roblox:ImportJSON(filePath)
    local content = self:ReadFile(filePath)
    if not content then
        warn("[FigmaPS2Roblox] Could not read file: " .. filePath)
        return
    end
    
    local spec
    local success, result = pcall(function()
        return HttpService:JSONDecode(content)
    end)
    
    if not success then
        warn("[FigmaPS2Roblox] Invalid JSON: " .. tostring(result))
        return
    end
    
    spec = result
    
    -- Update config from spec
    if spec.canvas then
        CONFIG.CanvasWidth = spec.canvas.width or CONFIG.CanvasWidth
        CONFIG.CanvasHeight = spec.canvas.height or CONFIG.CanvasHeight
    end
    
    -- Build UI
    self:BuildFromSpec(spec)
    
    print("[FigmaPS2Roblox] Imported " .. tostring(#(spec.elements or {})) .. " elements from " .. filePath)
end

function FigmaPS2Roblox:BuildFromSpec(spec)
    local root = Instance.new("ScreenGui")
    root.Name = spec.name or "GeneratedUI"
    root.ResetOnSpawn = false
    root.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    root.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
    
    local elements = {}
    self:ProcessElementTree(spec.elements or {}, root, elements)
    
    -- Apply layouts
    if CONFIG.AutoDetectLayouts and spec.layoutHints then
        self:ApplyLayoutHints(spec.layoutHints, elements)
    end
    
    -- Generate and insert script
    if CONFIG.GenerateScripts then
        self:GenerateAndInsertScript(spec, root)
    end
    
    print("[FigmaPS2Roblox] Built UI: " .. root.Name .. " (" .. tostring(#elements) .. " elements)")
    return root
end

function FigmaPS2Roblox:ProcessElementTree(elements, parent, container)
    local scaleW = CONFIG.CanvasWidth
    local scaleH = CONFIG.CanvasHeight
    
    for _, element in ipairs(elements) do
        local robloxClass = self:GetRobloxClass(element.type or "frame")
        local el = Instance.new(robloxClass)
        el.Name = element.name or "Unnamed"
        
        -- Position (Scale + Offset conversion)
        local scaleX = element.x / scaleW
        local scaleY = element.y / scaleH
        local scaleWidth = element.width / scaleW
        local scaleHeight = element.height / scaleH
        
        el.Position = UDim2.new(scaleX, 0, scaleY, 0)
        el.Size = UDim2.new(scaleWidth, 0, scaleHeight, 0)
        
        -- Appearance
        if element.fill then
            el.BackgroundColor3 = Color3.fromRGB(
                element.fill.r or 0,
                element.fill.g or 0,
                element.fill.b or 0
            )
        end
        
        -- Corner radius
        if element.cornerRadius and element.cornerRadius > 0 then
            local corner = Instance.new("UICorner")
            corner.CornerRadius = UDim.new(0, element.cornerRadius)
            corner.Parent = el
        end
        
        -- Border
        if element.stroke then
            el.BorderSizePixel = element.stroke.width or 0
            if element.stroke.color then
                local stroke = Instance.new("UIStroke")
                stroke.Color = Color3.fromRGB(
                    element.stroke.color.r or 0,
                    element.stroke.color.g or 0,
                    element.stroke.color.b or 0
                )
                stroke.Thickness = element.stroke.width or 1
                stroke.Parent = el
            end
        end
        
        -- Transparency
        if element.opacity ~= nil then
            el.BackgroundTransparency = 1 - element.opacity
        end
        
        -- Text
        if element.text then
            if el:IsA("TextLabel") or el:IsA("TextButton") or el:IsA("TextBox") then
                el.Text = element.text.content or ""
                el.TextSize = element.text.size or 16
                if element.text.color then
                    el.TextColor3 = Color3.fromRGB(
                        element.text.color.r,
                        element.text.color.g,
                        element.text.color.b
                    )
                end
                el.Font = element.text.bold and Enum.Font.GothamBold or Enum.Font.Gotham
                el.TextWrapped = element.text.wrapped or false
            end
        end
        
        -- Image
        if element.type == "image" or element.type == "icon" then
            el.Image = element.assetId and ("rbxassetid://" .. element.assetId) or "rbxassetid://0"
            el.ScaleType = Enum.ScaleType.Crop
        end
        
        -- Effects
        if element.effects then
            for _, effect in ipairs(element.effects) do
                self:AddEffect(el, effect)
            end
        end
        
        el.Parent = parent
        container[element.name] = el
        
        -- Recurse children
        if element.children and #element.children > 0 then
            self:ProcessElementTree(element.children, el, container)
        end
    end
end

function FigmaPS2Roblox:GetRobloxClass(type)
    local classMap = {
        frame = "Frame",
        button = "TextButton",
        btn = "TextButton",
        text = "TextLabel",
        label = "TextLabel",
        title = "TextLabel",
        image = "ImageLabel",
        icon = "ImageLabel",
        img = "ImageLabel",
        input = "TextBox",
        field = "TextBox",
        scrollframe = "ScrollingFrame",
    }
    return classMap[type] or "Frame"
end

function FigmaPS2Roblox:AddEffect(parent, effect)
    if effect.type == "dropShadow" then
        local shadow = Instance.new("Shadow")
        shadow.Color = effect.color and 
            Color3.fromRGB(effect.color.r or 0, effect.color.g or 0, effect.color.b or 0) 
            or Color3.fromRGB(0, 0, 0)
        shadow.Offset = Vector2.new(
            effect.distance * math.cos(math.rad(effect.angle or 0)),
            effect.distance * math.sin(math.rad(effect.angle or 0))
        )
        shadow.Size = effect.size or 0
        shadow.Transparency = effect.color and (1 - (effect.color.a or 255) / 255) or 0.5
        shadow.Parent = parent
    end
end

function FigmaPS2Roblox:ApplyLayoutHints(hints, elements)
    if not hints then return end
    
    for _, group in ipairs(hints.horizontalGroups or {}) do
        local parent = elements[group.parent]
        if parent then
            local layout = Instance.new("UIListLayout")
            layout.Parent = parent
            layout.Direction = Enum.FillDirection.Horizontal
            layout.Alignment = Enum.HorizontalAlignment.Left
            layout.SortOrder = Enum.SortOrder.LayoutOrder
        end
    end
    
    for _, group in ipairs(hints.verticalGroups or {}) do
        local parent = elements[group.parent]
        if parent then
            local layout = Instance.new("UIListLayout")
            layout.Parent = parent
            layout.Direction = Enum.FillDirection.Vertical
            layout.Alignment = Enum.HorizontalAlignment.Left
            layout.SortOrder = Enum.SortOrder.LayoutOrder
        end
    end
end

-- ============================================================
-- LUAU CODE IMPORTER
-- ============================================================

function FigmaPS2Roblox:ImportLua(filePath)
    local content = self:ReadFile(filePath)
    if not content then
        warn("[FigmaPS2Roblox] Could not read file: " .. filePath)
        return
    end
    
    -- Execute the Luau code
    local success, fn = loadstring(content)
    if not success then
        warn("[FigmaPS2Roblox] Failed to load Lua code: " .. tostring(fn))
        return
    end
    
    local result = fn()
    if result and typeof(result) == "table" then
        print("[FigmaPS2Roblox] Loaded UI module from " .. filePath)
    else
        print("[FigmaPS2Roblox] Executed Lua code from " .. filePath)
    end
end

-- ============================================================
-- EXPORT
-- ============================================================

function FigmaPS2Roblox:ExportSelection()
    local selection = game.Selection:Get()
    if #selection == 0 then
        warn("[FigmaPS2Roblox] Nothing selected. Select GUI objects first.")
        return
    end
    
    local spec = {
        version = "1.0.0",
        source = "roblox_studio",
        canvas = {
            width = CONFIG.CanvasWidth,
            height = CONFIG.CanvasHeight,
        },
        elements = {},
    }
    
    for _, instance in ipairs(selection) do
        if instance:IsA("GuiObject") then
            table.insert(spec.elements, self:ElementToJSON(instance))
        end
    end
    
    local json = HttpService:JSONEncode(spec, { indent = true })
    
    -- Save to file
    local filePath = PluginService:SaveDialog(
        "Save UI Spec",
        "JSON Files|*.json",
        "ui_spec.json",
        false
    )
    
    if filePath and filePath ~= "" then
        self:WriteFile(filePath, json)
        print("[FigmaPS2Roblox] Exported to: " .. filePath)
    end
end

function FigmaPS2Roblox:ElementToJSON(element)
    local json = {
        name = element.Name,
        type = self:GetTypeFromClass(element.ClassName),
        x = element.Position.X.Scale * CONFIG.CanvasWidth,
        y = element.Position.Y.Scale * CONFIG.CanvasHeight,
        width = element.Size.X.Scale * CONFIG.CanvasWidth,
        height = element.Size.Y.Scale * CONFIG.CanvasHeight,
        opacity = element.BackgroundTransparency or 0,
        visible = element.Visible,
    }
    
    if element.BackgroundColor3 then
        json.fill = {
            r = math.floor(element.BackgroundColor3.R * 255),
            g = math.floor(element.BackgroundColor3.G * 255),
            b = math.floor(element.BackgroundColor3.B * 255),
        }
    end
    
    if element:FindFirstChildOfClass("UICorner") then
        json.cornerRadius = element:FindFirstChildOfClass("UICorner").CornerRadius.Offset
    end
    
    if element:FindFirstChildOfClass("UIStroke") then
        local stroke = element:FindFirstChildOfClass("UIStroke")
        json.stroke = {
            width = stroke.Thickness,
            color = {
                r = math.floor(stroke.Color.R * 255),
                g = math.floor(stroke.Color.G * 255),
                b = math.floor(stroke.Color.B * 255),
            }
        }
    end
    
    if element.Text then
        json.text = {
            content = element.Text,
            size = element.TextSize,
        }
    end
    
    if element:FindFirstChildOfClass("UIListLayout") then
        local layout = element:FindFirstChildOfClass("UIListLayout")
        json._layout_suggestion = {
            type = "UIListLayout",
            direction = layout.Direction == Enum.FillDirection.Horizontal and "Horizontal" or "Vertical",
        }
    end
    
    -- Children
    local children = {}
    for _, child in ipairs(element:GetChildren()) do
        if child:IsA("GuiObject") then
            table.insert(children, self:ElementToJSON(child))
        end
    end
    if #children > 0 then
        json.children = children
    end
    
    return json
end

function FigmaPS2Roblox:GetTypeFromClass(className)
    local typeMap = {
        ["Frame"] = "frame",
        ["TextButton"] = "button",
        ["TextLabel"] = "text",
        ["ImageLabel"] = "image",
        ["TextBox"] = "input",
        ["ScrollingFrame"] = "scrollframe",
    }
    return typeMap[className] or "frame"
end

-- ============================================================
-- PREVIEW
-- ============================================================

function FigmaPS2Roblox:ShowPreview()
    local previewRoot = Instance.new("ScreenGui")
    previewRoot.Name = "UIPreview"
    previewRoot.ResetOnSpawn = false
    previewRoot.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
    
    local testPanel = Instance.new("Frame")
    testPanel.Name = "TestPanel"
    testPanel.Size = UDim2.new(0.5, 0, 0.5, 0)
    testPanel.Position = UDim2.new(0.25, 0, 0.25, 0)
    testPanel.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    testPanel.BorderSizePixel = 0
    testPanel.Parent = previewRoot
    
    local testLabel = Instance.new("TextLabel")
    testLabel.Name = "TestLabel"
    testLabel.Size = UDim2.new(1, 0, 0, 40)
    testLabel.BackgroundColor3 = Color3.fromRGB(0, 100, 200)
    testLabel.Text = "FigmaPS2Roblox - Import JSON to preview"
    testLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    testLabel.TextSize = 18
    testLabel.Parent = testPanel
    
    Debris:AddItem(previewRoot, 10)
    
    print("[FigmaPS2Roblox] Preview shown for 10 seconds")
end

-- ============================================================
-- UTILITY FUNCTIONS
-- ============================================================

function FigmaPS2Roblox:ReadFile(filePath)
    local file = io.open(filePath, "r")
    if not file then
        return nil
    end
    local content = file:read("*a")
    file:close()
    return content
end

function FigmaPS2Roblox:WriteFile(filePath, content)
    local file = io.open(filePath, "w")
    if not file then
        return false
    end
    file:write(content)
    file:close()
    return true
end

-- ============================================================
-- SCRIPT GENERATOR
-- ============================================================

function FigmaPS2Roblox:GenerateAndInsertScript(spec, root)
    local script = Instance.new("LocalScript")
    script.Name = "UIBuilder"
    
    local scaleW = CONFIG.CanvasWidth
    local scaleH = CONFIG.CanvasHeight
    
    local elementsJson = HttpService:JSONEncode(spec.elements or {}, { indent = false })
    
    local code = string.format([[%s
-- Generated by FigmaPS2Roblox
-- Canvas: %dx%d
-- Elements: %d

local Players = game:GetService("Players")
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local screenGui = playerGui:WaitForChild("%s")

local SCALE_W = %d
local SCALE_H = %d

local function createElement(parent, config)
    local el = Instance.new(config.Class)
    el.Name = config.Name
    el.Position = UDim2.new(
        config.X / SCALE_W, config.OffsetX or 0,
        config.Y / SCALE_H, config.OffsetY or 0
    )
    el.Size = UDim2.new(
        config.Width / SCALE_W, config.OffsetWidth or 0,
        config.Height / SCALE_H, config.OffsetHeight or 0
    )
    
    if config.BackgroundColor3 then
        el.BackgroundColor3 = config.BackgroundColor3
    end
    if config.BorderSizePixel then
        el.BorderSizePixel = config.BorderSizePixel
    end
    if config.BackgroundTransparency ~= nil then
        el.BackgroundTransparency = config.BackgroundTransparency
    end
    if config.CornerRadius then
        local corner = Instance.new("UICorner")
        corner.CornerRadius = UDim.new(0, config.CornerRadius)
        corner.Parent = el
    end
    
    if config.Text then
        el.Text = config.Text
        el.TextSize = config.TextSize or 16
        if config.TextColor3 then
            el.TextColor3 = config.TextColor3
        end
        el.Font = config.Font or Enum.Font.Gotham
    end
    
    if config.Image then
        el.Image = config.Image
        el.ScaleType = config.ScaleType or Enum.ScaleType.Crop
    end
    
    el.Parent = parent
    return el
end

local spec = %s
for _, config in ipairs(spec) do
    createElement(screenGui, config)
end
]],
        "-- Auto-generated by FigmaPS2Roblox",
        scaleW, scaleH,
        #(spec.elements or {}),
        root.Name,
        scaleW, scaleH,
        elementsJson
    )
    
    script.Source = code
    script.Parent = root
end

-- ============================================================
-- RETURN
-- ============================================================

return FigmaPS2Roblox
