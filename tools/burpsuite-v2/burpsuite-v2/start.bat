@echo off
echo ============================================
echo  CustomBurp Suite v2 - Inicializacao
echo ============================================
echo.

cd /d "%~dp0"

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

REM Verificar dependencias
pip show flask aiohttp cryptography >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt
)

echo.
echo Configuracao:
echo   Proxy:  http://127.0.0.1:8080
echo   Web UI: http://localhost:4000
echo.
echo Para HTTPS: python main.py --generate-ca
echo.
echo Pressione Ctrl+C para parar
echo ============================================
echo.

python main.py %*
pause
