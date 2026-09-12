$dst = "C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel"
$src = "C:\Users\devel\AppData\Roaming\Adobe\CEP\extensions\com.roblox.phototolua.panel"

Write-Host "Corrigindo instalacao do FigmaPS2Roblox..." -ForegroundColor Cyan

# Criar mimetype na raiz (correto para PS 2024)
$mimetype = "application/vnd.adobe.air-ucf-package+zip"
[System.IO.File]::WriteAllText((Join-Path $dst "mimetype"), $mimetype, [System.Text.Encoding]::ASCII)
Write-Host "  OK: mimetype (corrigido)" -ForegroundColor Green

# Atualizar manifesto para usar ModalDialog em vez de Panel
$manifestXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<ExtensionManifest ExtensionBundleId="com.roblox.phototolua" ExtensionBundleVersion="2.0.0" Version="5.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ExtensionList>
    <Extension Id="com.roblox.phototolua.panel" Version="2.0.0" />
  </ExtensionList>
  <ExecutionEnvironment>
    <HostList>
      <Host Name="PHXS" Version="25" />
      <Host Name="PHSP" Version="25" />
    </HostList>
    <LocaleList>
      <Locale Code="All" />
    </LocaleList>
    <RequiredRuntimeList>
      <RequiredRuntime Name="CSXS" Version="5.0" />
    </RequiredRuntimeList>
  </ExecutionEnvironment>
  <DispatchInfoList>
    <Extension Id="com.roblox.phototolua.panel">
      <DispatchInfo>
        <Resources>
          <MainPath>./index.html</MainPath>
          <CEFCommandLine>
            <Parameter>--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure,NetworkService