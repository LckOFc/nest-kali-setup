--!strict
-- [[
-- TestMenu
-- Gerado automaticamente do pacote: 50 assets
-- Canvas: 1920x1080
-- ]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local UIBridge = require(ReplicatedStorage:WaitForChild("UIBridge"))

-- Asset IDs (substituir PLACEHOLDER_XXX pelos IDs reais do Roblox)
local  = "rbxassetid://0" -- 12345.png
local asseticonswordddcea = "rbxassetid://0" -- asseticonsword_876d8d2ce3a7.png
local asseticonsword = "rbxassetid://0" -- asset_icon_sword.png
local backgroundmainfe = "rbxassetid://0" -- backgroundmain_f1229e728887.png
local backgroundmain = "rbxassetid://0" -- background_main.png
local barhealthaba = "rbxassetid://0" -- barhealth_90a530b86a59.png
local barhealth = "rbxassetid://0" -- bar_health.png
local bgmenucecbe = "rbxassetid://0" -- bgmenu_cec613b268e2.png
local bgmenu = "rbxassetid://0" -- bg_menu.png
local btn = "rbxassetid://0" -- btn.png
local btnplaybaff = "rbxassetid://0" -- btnplay_b0a47f6414f3.png
local btnsubmitbacfb = "rbxassetid://0" -- btnsubmit_9b15ac1f58b6.png
local btncda = "rbxassetid://0" -- btn_8c6da0904080.png
local btnplay = "rbxassetid://0" -- btn_play.png
local btnsubmit = "rbxassetid://0" -- btn_submit.png
local buttonsettingsfaded = "rbxassetid://0" -- buttonsettings_0028f5aded82.png
local buttonsettings = "rbxassetid://0" -- button_settings.png
local containerinventorycfefad = "rbxassetid://0" -- containerinventory_5cfe0f488a3d.png
local containerinventory = "rbxassetid://0" -- container_inventory.png
local ctastartbaff = "rbxassetid://0" -- ctastart_4b0158a44ff4.png
local ctastart = "rbxassetid://0" -- cta_start.png
local dividerverticalfecf = "rbxassetid://0" -- dividervertical_fe1c520871f3.png
local dividervertical = "rbxassetid://0" -- divider_vertical.png
local effectglowddfe = "rbxassetid://0" -- effectglow_568167d67dfe.png
local effectglow = "rbxassetid://0" -- effect_glow.png
local empty = "rbxassetid://0" -- empty.png
local emptycd = "rbxassetid://0" -- empty_c8819084667d.png
local framedialogbfe = "rbxassetid://0" -- framedialog_48b1f9831e54.png
local framedialog = "rbxassetid://0" -- frame_dialog.png
local hpbarfilleeaca = "rbxassetid://0" -- hpbarfill_3ee996a5ca24.png
local hpbarfill = "rbxassetid://0" -- hp_bar_fill.png
local iconcoinefbeb = "rbxassetid://0" -- iconcoin_27efbe00455b.png
local iconheartcabbe = "rbxassetid://0" -- iconheart_c6a7b85208be.png
local iconcoin = "rbxassetid://0" -- icon_coin.png
local iconheart = "rbxassetid://0" -- icon_heart.png
local imagedecorativedc = "rbxassetid://0" -- imagedecorative_8d26c1264232.png
local imagedecorative = "rbxassetid://0" -- image_decorative.png
local imgavatarebf = "rbxassetid://0" -- imgavatar_72e2b488f576.png
local imgavatar = "rbxassetid://0" -- img_avatar.png
local labelsubtitle = "rbxassetid://0" -- label_subtitle.png
local logoapp = "rbxassetid://0" -- logo_app.png
local manabar = "rbxassetid://0" -- mana_bar.png
local panelcard = "rbxassetid://0" -- panel_card.png
local scoredisplay = "rbxassetid://0" -- score_display.png
local separatorline = "rbxassetid://0" -- separator_line.png
local telafundo = "rbxassetid://0" -- telafundo_01.png
local textdescription = "rbxassetid://0" -- text_description.png
local titlemain = "rbxassetid://0" -- title_main.png
local x = "rbxassetid://0" -- x.png
local baf = "rbxassetid://0" -- _b4a0f1885528.png

local _manifest = {
	name = "TestMenu",
	canvasWidth = 1920,
	canvasHeight = 1080,
	scaleMode = "ScaleToFit",
	elements = {
		-- ImageLabel: backgroundmainfe
		-- ImageLabel: backgroundmain
		-- ImageLabel: bgmenucecbe
		-- ImageLabel: bgmenu
		-- ImageLabel: telafundo
		-- Frame: containerinventorycfefad
		-- Frame: containerinventory
		-- Frame: framedialogbfe
		-- Frame: framedialog
		-- Frame: panelcard
		-- TextButton: btn
		-- TextButton: btnplaybaff
		-- TextButton: btnsubmitbacfb
		-- TextButton: btncda
		-- TextButton: btnplay
		-- TextButton: btnsubmit
		-- TextButton: buttonsettingsfaded
		-- TextButton: buttonsettings
		-- TextButton: ctastartbaff
		-- TextButton: ctastart
		-- TextLabel: labelsubtitle
		-- TextLabel: scoredisplay
		-- TextLabel: textdescription
		-- TextLabel: titlemain
		-- ImageLabel: asseticonswordddcea
		-- ImageLabel: asseticonsword
		-- ImageLabel: iconcoinefbeb
		-- ImageLabel: iconheartcabbe
		-- ImageLabel: iconcoin
		-- ImageLabel: iconheart
		-- ImageLabel: imgavatarebf
		-- ImageLabel: imgavatar
		-- ImageLabel: logoapp
		-- Frame: barhealthaba_Bg
		-- Frame: barhealth_Bg
		-- Frame: hpbarfilleeaca_Bg
		-- Frame: hpbarfill_Bg
		-- Frame: manabar_Bg
		-- ImageLabel: 
		-- ImageLabel: empty
		-- ImageLabel: emptycd
		-- ImageLabel: imagedecorativedc
		-- ImageLabel: imagedecorative
		-- ImageLabel: x
		-- ImageLabel: baf
		-- Frame: dividerverticalfecf
		-- Frame: dividervertical
		-- Frame: separatorline
	},
}

local TestMenuController = {
	Name = "TestMenuController",
}

function TestMenuController.Init()
	-- TODO: Substituir PLACEHOLDER_0, PLACEHOLDER_1, etc.
	-- pelos Asset IDs do Roblox Studio
	print("[TestMenuController] Run Init() after setting asset IDs")
end

function TestMenuController.Show()
	-- TODO: Build and show the screen
end

function TestMenuController.Hide()
	-- TODO: Hide the screen
end

return TestMenuController
