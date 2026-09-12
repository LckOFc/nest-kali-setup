@echo off
echo ========================================
echo  FigmaPS2Roblox - Fix Plugin
echo ========================================
echo.

set SRC=C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin\uxp-panel
set DST=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\UXP\com.roblox.phototolua.panel
set DST_CEP=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel
set DST_APP=C:\Users\devel\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel

echo [1/4] Instalando icons no UXP...
mkdir "%DST%\icons" 2>nul
copy /Y "%SRC%\icons\dark@1x.png" "%DST%\icons\" >nul
copy /Y "%SRC%\icons\light@1x.png" "%DST%\icons\" >nul
copy /Y "%SRC%\icons\dark@2x.png" "%DST%\icons\" >nul
copy /Y "%SRC%\icons\light@2x.png" "%DST%\icons\" >nul

echo [2/4] Copiando para CEP (Program Files)...
copy /Y "%SRC%\manifest.json" "%DST_CEP%\" >nul
copy /Y "%SRC%\index.html" "%DST_CEP%\" >nul
xcopy /E /I /Y "%SRC%\js" "%DST_CEP%\js\" >nul

echo [3/4] Copiando para CEP (AppData)...
mkdir "%DST_APP%" 2>nul
mkdir "%DST_APP%\js" 2>nul
mkdir "%DST_APP%\icons" 2>nul
copy /Y "%SRC%\manifest.json" "%DST_APP%\" >nul
copy /Y "%SRC%\index.html" "%DST_APP%\" >nul
copy /Y "%SRC%\js\main.js" "%DST_APP%\js\" >nul
copy /Y "%SRC%\icons\dark@1x.png" "%DST_APP%\icons\" >nul
copy /Y "%SRC%\icons\light@1x.png" "%DST_APP%\icons\" >nul
copy /Y "%SRC%\icons\dark@2x.png" "%DST_APP%\icons\" >nul
copy /Y "%SRC%\icons\light@2x.png" "%DST_APP%\icons\" >nul

echo [4/4] Atualizando manifest UXP com icons...
powershell -Command "(Get-Content '%DST%\manifest.json') -replace '\"entrypoints\": \[', '\"icons\": [{\"path\": \"icons/dark@1x.png\",\"width\": 23,\"height\": 23,\"theme\": [\"dark\",\"darkest\"]},{\"path\": \"icons/light@1x.png\",\"width\": 23,\"height\": 23,\"theme\": [\"light\",\"lightest\"]}],\"entrypoints\": [" | Set-Content '%DST%\manifest.json' -Encoding UTF8"

echo.
echo ========================================
echo  INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Reinicie o Photoshop e teste:
echo   Window > Extensions > FigmaPS2Roblox
echo.
pause
