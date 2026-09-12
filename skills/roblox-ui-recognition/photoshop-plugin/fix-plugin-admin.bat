@echo off
echo ========================================
echo  FigmaPS2Roblox - Fix Plugin (Admin)
echo ========================================
echo.

set SRC=C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin\uxp-panel
set DST=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\UXP\com.roblox.phototolua.panel

echo [1] Criando pastas...
mkdir "%DST%\icons" 2>nul
mkdir "%DST%\js" 2>nul

echo [2] Copiando arquivos...
copy /Y "%SRC%\manifest.json" "%DST%\" >nul
copy /Y "%SRC%\index.html" "%DST%\" >nul
copy /Y "%SRC%\js\main.js" "%DST%\js\" >nul
copy /Y "%SRC%\icons\dark@1x.png" "%DST%\icons\" >nul
copy /Y "%SRC%\icons\light@1x.png" "%DST%\icons\" >nul
copy /Y "%SRC%\icons\dark@2x.png" "%DST%\icons\" >nul
copy /Y "%SRC%\icons\light@2x.png" "%DST%\icons\" >nul

echo [3] Instalando no CEP (Program Files)...
set CEP_DST=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel
mkdir "%CEP_DST%" 2>nul
copy /Y "%SRC%\manifest.json" "%CEP_DST%\" >nul
copy /Y "%SRC%\index.html" "%CEP_DST%\" >nul
xcopy /E /I /Y "%SRC%\js" "%CEP_DST%\js\" >nul
xcopy /E /I /Y "%SRC%\icons" "%CEP_DST%\icons\" >nul

echo [4] Instalando no CEP (AppData)...
set CEP_APP=C:\Users\devel\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel
mkdir "%CEP_APP%" 2>nul
mkdir "%CEP_APP%\js" 2>nul
mkdir "%CEP_APP%\icons" 2>nul
mkdir "%CEP_APP%\CSXS" 2>nul
copy /Y "%SRC%\manifest.json" "%CEP_APP%\" >nul
copy /Y "%SRC%\index.html" "%CEP_APP%\" >nul
copy /Y "%SRC%\js\main.js" "%CEP_APP%\js\" >nul
copy /Y "%SRC%\icons\dark@1x.png" "%CEP_APP%\icons\" >nul
copy /Y "%SRC%\icons\light@1x.png" "%CEP_APP%\icons\" >nul
copy /Y "%SRC%\icons\dark@2x.png" "%CEP_APP%\icons\" >nul
copy /Y "%SRC%\icons\light@2x.png" "%CEP_APP%\icons\" >nul

echo.
echo ========================================
echo  INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Arquivos instalados:
echo   - UXP: %DST%\
echo   - CEP: %CEP_DST%\
echo   - CEP: %CEP_APP%\
echo.
echo Reinicie o Photoshop e teste:
echo   Window > Extensions > FigmaPS2Roblox
echo.
pause
