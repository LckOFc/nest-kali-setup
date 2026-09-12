--!strict
-- [[
-- TestMenu Controller
-- 30 assets processados (hash único anti-reuploader)
-- ]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local UIBridge = require(ReplicatedStorage:WaitForChild("UIBridge"))

-- Assets (substituir rbxassetid://0 pelos IDs reais)
local 6e5d7bacc5d3 = "rbxassetid://0" --  [image]
local 61df0435d1e2 = "rbxassetid://0" -- asseticonsword [icon]
local f1229e728887 = "rbxassetid://0" -- backgroundmain [background]
local a9706fc2708b = "rbxassetid://0" -- barhealth [bar]
local 88bb5e19943a = "rbxassetid://0" -- bgmenu [background]
local 813f4739e274 = "rbxassetid://0" -- btn [button]
local 8d74184bd409 = "rbxassetid://0" -- btnplay [button]
local 9b15ac1f58b6 = "rbxassetid://0" -- btnsubmit [button]
local 0f1198e640a1 = "rbxassetid://0" -- buttonsettings [button]
local 79791d1ae0a5 = "rbxassetid://0" -- containerinventory [panel]
local 4b0158a44ff4 = "rbxassetid://0" -- ctastart [button]
local bafd7ede78ba = "rbxassetid://0" -- dividervertical [separator]
local 00cd15172fdc = "rbxassetid://0" -- effectglow [effect]
local c768d28a3afe = "rbxassetid://0" -- empty [image]
local c2d2e40a04cf = "rbxassetid://0" -- framedialog [panel]
local 6a8a072ed862 = "rbxassetid://0" -- hpbarfill [bar]
local 27efbe00455b = "rbxassetid://0" -- iconcoin [icon]
local eb5fe9c7d394 = "rbxassetid://0" -- iconheart [icon]
local 8d26c1264232 = "rbxassetid://0" -- imagedecorative [image]
local 72e2b488f576 = "rbxassetid://0" -- imgavatar [icon]
local 4ec1116db8ce = "rbxassetid://0" -- labelsubtitle [label]
local 5099a8f66fa2 = "rbxassetid://0" -- logoapp [icon]
local f8e3b3a13438 = "rbxassetid://0" -- manabar [bar]
local 9cbf357ee0fc = "rbxassetid://0" -- panelcard [panel]
local 94957cbf21a0 = "rbxassetid://0" -- scoredisplay [label]
local 3982a3c1617a = "rbxassetid://0" -- separatorline [separator]
local a25f8a226573 = "rbxassetid://0" -- telafundo [background]
local 9832d1d62c4d = "rbxassetid://0" -- textdescription [label]
local 89d85e396910 = "rbxassetid://0" -- titlemain [label]
local e3bd29e731ae = "rbxassetid://0" -- x [image]

local TestMenuController = { Name = "TestMenuController" }

function TestMenuController.Init()
	print("[TestMenuController] Init — substitua os rbxassetid://0 pelos IDs reais]")
end

function TestMenuController.Show()
	local pg = Players.LocalPlayer:WaitForChild("PlayerGui")
	-- TODO: Criar ScreenGui e posicionar elementos
	local sg = Instance.new("ScreenGui")
	sg.Name = "TestMenu"
	sg.ResetOnSpawn = false
	sg.IgnoreGuiInset = true
	sg.Parent = pg
end

function TestMenuController.Hide()
	-- TODO
end

return TestMenuController
