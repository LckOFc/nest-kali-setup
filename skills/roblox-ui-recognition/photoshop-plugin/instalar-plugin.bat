@echo off
chcp 65001 >nul
title FigmaPS2Roblox - Instalacao
echo ========================================
echo   FigmaPS2Roblox v2.1.0 - Instalacao
echo ========================================
echo.

set "SRC=C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin"
set "DST=C:\Users\%USERNAME%\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel"

echo Criando estrutura...
mkdir "%DST%" 2>nul
mkdir "%DST%\CSXS" 2>nul
mkdir "%DST%\META-INF" 2>nul

echo Copiando arquivos...
copy /Y "%SRC%\index.html" "%DST%\" >nul && echo   ✅ index.html
copy /Y "%SRC%\hostscript.jsx" "%DST%\" >nul && echo   ✅ hostscript.jsx
copy /Y "%SRC%\cep.js" "%DST%\" >nul && echo   ✅ cep.js
copy /Y "%SRC%\BriefIcon.png" "%DST%\" >nul && echo   ✅ BriefIcon.png
copy /Y "%SRC%\CSXS\manifest.xml" "%DST%\CSXS\" >nul && echo   ✅ CSXS/manifest.xml
copy /Y "%SRC%\CSXS\version.xml" "%DST%\CSXS\" >nul && echo   ✅ CSXS/version.xml

echo application/x-extension-htm > "%DST%\META-INF\mimetype" && echo   ✅ META-INF/mimetype
echo ^<?xml version="1.0" encoding="UTF-8"?^>^<manifest xmlns="http://ns.adobe.com/axapplication/1.0/"^>^<packageVersion^>2.1.0^</packageVersion^>^</manifest^> > "%DST%\META-INF\signatures.xml" && echo   ✅ META-INF/signatures.xml

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Reinicie o Photoshop e acesse:
echo   Window > Extensions > FigmaPS2Roblox
echo.
pause
