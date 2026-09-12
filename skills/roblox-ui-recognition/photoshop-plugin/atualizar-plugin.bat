@echo off
chcp 65001 >nul
title FigmaPS2Roblox - Atualizar
echo ========================================
echo   FigmaPS2Roblox v2.1.0 - Atualizar
echo ========================================
echo.

set "SRC=C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin"
set "DST_USER=C:\Users\%USERNAME%\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel"
set "DST_SYS=C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel"

echo Atualizando para v2.1.0...
echo.

echo [1] Atualizando CEP (Usuario)...
if exist "%DST_USER%" (
    copy /Y "%SRC%\index.html" "%DST_USER%\" >nul && echo   ✅ index.html
    copy /Y "%SRC%\hostscript.jsx" "%DST_USER%\" >nul && echo   ✅ hostscript.jsx
    copy /Y "%SRC%\cep.js" "%DST_USER%\" >nul && echo   ✅ cep.js
    copy /Y "%SRC%\CSXS\manifest.xml" "%DST_USER%\CSXS\" >nul && echo   ✅ CSXS/manifest.xml
    copy /Y "%SRC%\CSXS\version.xml" "%DST_USER%\CSXS\" >nul && echo   ✅ CSXS/version.xml
) else (
    echo   ⚠️  Pasta do usuario nao encontrada
)

echo.
echo [2] Atualizando CEP (Sistema)...
if exist "%DST_SYS%" (
    copy /Y "%SRC%\index.html" "%DST_SYS%\" >nul && echo   ✅ index.html
    copy /Y "%SRC%\hostscript.jsx" "%DST_SYS%\" >nul && echo   ✅ hostscript.jsx
    copy /Y "%SRC%\cep.js" "%DST_SYS%\" >nul && echo   ✅ cep.js
    copy /Y "%SRC%\CSXS\manifest.xml" "%DST_SYS%\CSXS\" >nul && echo   ✅ CSXS/manifest.xml
    copy /Y "%SRC%\CSXS\version.xml" "%DST_SYS%\CSXS\" >nul && echo   ✅ CSXS/version.xml
) else (
    echo   ⚠️  Pasta do sistema nao encontrada
)

echo.
echo ========================================
echo   ATUALIZACAO CONCLUIDA!
echo ========================================
echo.
echo Reinicie o Photoshop e teste:
echo   Window > Extensions > FigmaPS2Roblox
echo.
pause
