@echo off
echo Instalando plugin Roblox UI para Photoshop...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install-roblox-plugin.ps1" -Install
echo.
echo ========================================
echo   Plugin instalado com sucesso!
echo ========================================
echo.
echo   REINICIE o Photoshop e acesse:
echo   Window > Extensions > Roblox UI
echo.
pause
