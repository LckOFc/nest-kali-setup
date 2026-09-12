# Troubleshooting Script - FigmaPS2Roblox
# Run: .\troubleshoot.ps1 [-Fix] [-Reinstall] [-CheckOnly]

param(
    [switch]$Fix,
    [switch]$Reinstall,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$PluginID = "com.roblox.phototolua.panel"
$SourceDir = "C:\Users\devel\.config\opencode\skills\roblox-ui-recognition\photoshop-plugin"
$PluginPath = Join-Path $env:APPDATA "Adobe\CEP\extensions\$PluginID"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FigmaPS2Roblox Troubleshooting v2.1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check functions
function Test-Check($name, $passed, $message = "") {
    $icon = if ($passed) { "[OK]" } else { "[X]" }
    $color = if ($passed) { "Green" } else { "Red" }
    Write-Host "  $icon $name" -ForegroundColor $color
    if ($message -and -not $passed) {
        Write-Host "      -> $message" -ForegroundColor Yellow
    }
}

# Run checks
Write-Host "RUNNING DIAGNOSTICS..." -ForegroundColor Cyan
Write-Host ""

$failed = @()

# Check 1: Plugin installed
if (Test-Path $PluginPath) {
    Test-Check "Plugin installed" $true
} else {
    Test-Check "Plugin installed" $false "Not found at: $PluginPath"
    $failed += "Plugin not installed"
}

# Check 2: Required files
$requiredFiles = @("index.html", "hostscript.jsx", "cep.js", "BriefIcon.png")
foreach ($file in $requiredFiles) {
    $path = Join-Path $PluginPath $file
    if (Test-Path $path) {
        Test-Check $file $true
    } else {
        Test-Check $file $false "Missing in plugin folder"
        $failed += "Missing: $file"
    }
}

# Check 3: CSXS manifest
if (Test-Path (Join-Path $PluginPath "CSXS\manifest.xml")) {
    Test-Check "CSXS/manifest.xml" $true
} else {
    Test-Check "CSXS/manifest.xml" $false "Required for CEP registration"
    $failed += "Missing manifest"
}

# Check 4: META-INF
if (Test-Path (Join-Path $PluginPath "META-INF\mimetype")) {
    Test-Check "META-INF/mimetype" $true
} else {
    Test-Check "META-INF/mimetype" $false "Required for extension recognition"
    $failed += "Missing mimetype"
}

# Check 5: Photoshop running
$psProcess = Get-Process -Name "Photoshop" -ErrorAction SilentlyContinue
if ($psProcess.Count -gt 0) {
    Test-Check "Photoshop running" $true
} else {
    Test-Check "Photoshop running" $false "Open Photoshop first"
}

# Check 6: CEP Runtime
$cepPath = "HKLM:\SOFTWARE\Adobe\CSXS.11"
if (Test-Path $cepPath) {
    Test-Check "CEP Runtime" $true
} else {
    Test-Check "CEP Runtime" $false "Install Adobe CEP Loader"
}

Write-Host ""

# Fix issues
if ($Fix -or $Reinstall) {
    Write-Host "FIXING ISSUES..." -ForegroundColor Yellow
    Write-Host ""
    
    # Remove old installation
    if (Test-Path $PluginPath) {
        Remove-Item $PluginPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] Removed old installation" -ForegroundColor Green
    }
    
    # Create new installation
    New-Item -ItemType Directory -Force -Path $PluginPath | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $PluginPath "CSXS") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $PluginPath "META-INF") | Out-Null
    
    # Copy files
    foreach ($file in $requiredFiles) {
        $src = Join-Path $SourceDir $file
        $dst = Join-Path $PluginPath $file
        if (Test-Path $src) {
            Copy-Item $src $dst -Force
            Write-Host "  [OK] Copied $file" -ForegroundColor Green
        }
    }
    
    # Copy CSXS
    $csxsDst = Join-Path $PluginPath "CSXS"
    if (Test-Path (Join-Path $SourceDir "CSXS")) {
        Copy-Item (Join-Path $SourceDir "CSXS\*") $csxsDst -Recurse -Force
        Write-Host "  [OK] Copied CSXS/" -ForegroundColor Green
    }
    
    # Create mimetype
    "application/x-extension-htm" | Out-File -FilePath (Join-Path $PluginPath "META-INF\mimetype") -Encoding ascii
    Write-Host "  [OK] Created META-INF/mimetype" -ForegroundColor Green
    
    # Create signatures.xml
    $sigXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://ns.adobe.com/axapplication/1.0/">
  <packageVersion>2.1.0</packageVersion>
</manifest>
"@
    $sigXml | Out-File -FilePath (Join-Path $PluginPath "META-INF\signatures.xml") -Encoding utf8
    Write-Host "  [OK] Created META-INF/signatures.xml" -ForegroundColor Green
    
    # Enable Photoshop plugins
    $psPrefs = "HKCU:\Software\Adobe\Photoshop"
    if (Test-Path $psPrefs) {
        $lastVersion = (Get-ChildItem $psPrefs | Sort-Object Name -Descending | Select-Object -First 1).Name
        if ($lastVersion) {
            $configPath = Join-Path $psPrefs $lastVersion "\Configuration"
            if (-not (Test-Path $configPath)) {
                New-Item -ItemType Directory -Force -Path $configPath | Out-Null
            }
            Set-ItemProperty -Path $configPath -Name "AMGeneral_ADOBE_EXTENSIONS_ALLOW_PLUGIN" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $configPath -Name "AMGeneral_ADOBE_EXTENSIONS_ALLOW_PANELS" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Enabled plugins in Photoshop preferences" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  FIX COMPLETE!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "  1. CLOSE PHOTOSHOP COMPLETELY" -ForegroundColor White
    Write-Host "     (Check Task Manager for Photoshop processes)"
    Write-Host ""
    Write-Host "  2. REOPEN PHOTOSHOP" -ForegroundColor White
    Write-Host ""
    Write-Host "  3. Go to: Window > Extensions > FigmaPS2Roblox" -ForegroundColor White
    Write-Host ""
}

# Final status
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  STATUS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($failed.Count -eq 0) {
    Write-Host "  [OK] All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If plugin still shows 'Disconnected':" -ForegroundColor Yellow
    Write-Host "  1. Close Photoshop completely" -ForegroundColor White
    Write-Host "  2. Open Task Manager, kill all Photoshop processes" -ForegroundColor White
    Write-Host "  3. Reopen Photoshop" -ForegroundColor White
    Write-Host "  4. Window > Extensions > FigmaPS2Roblox" -ForegroundColor White
} else {
    Write-Host "  [X] Issues found: $($failed.Count)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run with --fix to auto-repair:" -ForegroundColor Yellow
    Write-Host "  .\troubleshoot.ps1 --fix" -ForegroundColor White
}

Write-Host ""
