@echo off
echo ========================================
echo  FigmaPS2Roblox UXP Installer
echo ========================================
echo.

set SRC=C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin\uxp-panel
set DST=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\UXP\com.roblox.phototolua.panel

echo Creating destination directory...
mkdir "%DST%" 2>nul
mkdir "%DST%\js" 2>nul

echo Copying files...
copy /Y "%SRC%\manifest.json" "%DST%\" >nul
copy /Y "%SRC%\index.html" "%DST%\" >nul
copy /Y "%SRC%\js\main.js" "%DST%\js\" >nul

echo.
echo ========================================
echo  INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Reinicie o Photoshop e vá em:
echo   Window > Extensions > FigmaPS2Roblox
echo.
pause
