@echo off
chcp 65001 >nul
title FigmaPS2Roblox - Correcoes v2.1
echo ========================================
echo   FigmaPS2Roblox - Correcoes v2.1.0
echo ========================================
echo.

set "SRC=C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin"
set "DST_USER=C:\Users\%USERNAME%\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel"
set "DST_SYS=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel"

echo [1/4] Copiando arquivos CEP para pasta do usuario...
mkdir "%DST_USER%" 2>nul
copy /Y "%SRC%\index.html" "%DST_USER%\" >nul
copy /Y "%SRC%\hostscript.jsx" "%DST_USER%\" >nul
copy /Y "%SRC%\cep.js" "%DST_USER%\" >nul
copy /Y "%SRC%\BriefIcon.png" "%DST_USER%\" >nul
mkdir "%DST_USER%\CSXS" 2>nul
copy /Y "%SRC%\CSXS\manifest.xml" "%DST_USER%\CSXS\" >nul
copy /Y "%SRC%\CSXS\version.xml" "%DST_USER%\CSXS\" >nul
mkdir "%DST_USER%\META-INF" 2>nul
echo application/x-extension-htm > "%DST_USER%\META-INF\mimetype"
echo ^<?xml version="1.0" encoding="UTF-8"?^>^<manifest xmlns="http://ns.adobe.com/axapplication/1.0/"^>^<packageVersion^>2.1.0^</packageVersion^>^</manifest^> > "%DST_USER%\META-INF\signatures.xml"
echo   ✅ CEP (usuario) atualizado

echo.
echo [2/4] Copiando arquivos CEP para pasta do sistema (admin)...
if exist "%DST_SYS%" (
    mkdir "%DST_SYS%" 2>nul
    copy /Y "%SRC%\index.html" "%DST_SYS%\" >nul
    copy /Y "%SRC%\hostscript.jsx" "%DST_SYS%\" >nul
    copy /Y "%SRC%\cep.js" "%DST_SYS%\" >nul
    copy /Y "%SRC%\BriefIcon.png" "%DST_SYS%\" >nul
    mkdir "%DST_SYS%\CSXS" 2>nul
    copy /Y "%SRC%\CSXS\manifest.xml" "%DST_SYS%\CSXS\" >nul
    copy /Y "%SRC%\CSXS\version.xml" "%DST_SYS%\CSXS\" >nul
    mkdir "%DST_SYS%\META-INF" 2>nul
    echo application/x-extension-htm > "%DST_SYS%\META-INF\mimetype"
    echo ^<?xml version="1.0" encoding="UTF-8"?^>^<manifest xmlns="http://ns.adobe.com/axapplication/1.0/"^>^<packageVersion^>2.1.0^</packageVersion^>^</manifest^> > "%DST_SYS%\META-INF\signatures.xml"
    echo   ✅ CEP (sistema) atualizado
) else (
    echo   ⚠️  Pasta do sistema nao encontrada
)

echo.
echo [3/4] Copiando arquivos UXP...
set "UXP_DST=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\UXP\com.roblox.phototolua.panel"
if exist "%UXP_DST%" (
    mkdir "%UXP_DST%\js" 2>nul
    mkdir "%UXP_DST%\icons" 2>nul
    copy /Y "%SRC%\uxp-panel\manifest.json" "%UXP_DST%\" >nul
    copy /Y "%SRC%\uxp-panel\index.html" "%UXP_DST%\" >nul
    copy /Y "%SRC%\uxp-panel\js\main.js" "%UXP_DST%\js\" >nul
    if exist "%SRC%\uxp-panel\icons\*" (
        copy /Y "%SRC%\uxp-panel\icons\*" "%UXP_DST%\icons\" >nul
    )
    echo   ✅ UXP atualizado
) else (
    echo   ⚠️  Pasta UXP nao encontrada
)

echo.
echo ========================================
echo   CORRECOES APLICADAS!
echo ========================================
echo.
echo  Versao: 2.1.0
echo  CEP: %DST_USER%
echo  UXP: %UXP_DST%
echo.
echo  1. FECHA O PHOTOSHOP COMPLETAMENTE
echo  2. ABRA O PHOTOSHOP NOVAMENTE
echo  3. Vá em: Window > Extensions > FigmaPS2Roblox
echo.
pause
