param([switch]$Install, [switch]$Remove, [switch]$Force)

$pluginName = "com.roblox.ui.export"
$sourceDir = "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin"
$targetDir = "C:\Users\devel\AppData\Roaming\Adobe\CEP\extensions\$pluginName"
$zxpPath = "C:\Users\devel\Desktop\RobloxUIExport.zxp"

if ($Install) {
    # Criar pasta
    if (Test-Path $targetDir) { Remove-Item $targetDir -Recurse -Force -Confirm:$false }
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    
    # Copiar arquivos
    Copy-Item "$sourceDir\*" $targetDir -Recurse -Force
    
    # Habilitar modo desenvolvedor
    $cepPath = "HKCU:\Software\Adobe\CS6.0_64\CEP"
    if (-not (Test-Path $cepPath)) { New-Item $cepPath -Force | Out-Null }
    New-ItemProperty -Path $cepPath -Name "CTFEnabled" -Value 1 -PropertyType DWORD -Force -ErrorAction SilentlyContinue | Out-Null
    New-ItemProperty -Path $cepPath -Name "ExtensionsDebugMode" -Value 1 -PropertyType DWORD -Force -ErrorAction SilentlyContinue | Out-Null
    
    Write-Host "✅ Plugin instalado!"
    Write-Host ""
    Write-Host "📁 Local: $targetDir"
    Write-Host "🔧 Modo desenvolvedor: ON"
    Write-Host ""
    Write-Host "⚠️  REINICIE O PHOTOSHOP"
    Write-Host "   Depois: Window > Extensions > Roblox UI"
}

if ($Remove) {
    if (Test-Path $targetDir) {
        Remove-Item $targetDir -Recurse -Force -Confirm:$false
        Write-Host "🗑️  Plugin removido"
    }
}
