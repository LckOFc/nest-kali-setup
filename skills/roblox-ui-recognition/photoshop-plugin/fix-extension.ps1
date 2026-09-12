$dst = "C:\Program Files\Adobe\Adobe Photoshop 2024\Required\CEP\extensions\com.roblox.phototolua.panel"

# Fix mimetype in root
$mimetype = "application/vnd.adobe.air-ucf-package+zip"
[System.IO.File]::WriteAllText((Join-Path $dst "mimetype"), $mimetype, [System.Text.Encoding]::ASCII)
Write-Host "OK: mimetype created"

# Write corrected manifest
$manifest = '<?xml version="1.0" encoding="UTF-8"?>'
$manifest += '<ExtensionManifest ExtensionBundleId="com.roblox.phototolua" ExtensionBundleVersion="2.0.0" Version="5.0">'
$manifest += '<ExtensionList>'
$manifest += '  <Extension Id="com.roblox.phototolua.panel" Version="2.0.0" />'
$manifest += '</ExtensionList>'
$manifest += '<ExecutionEnvironment>'
$manifest += '  <HostList>'
$manifest += '    <Host Name="PHXS" Version="25" />'
$manifest += '    <Host Name="PHSP" Version="25" />'
$manifest += '  </HostList>'
$manifest += '  <LocaleList><Locale Code="All" /></LocaleList>'
$manifest += '  <RequiredRuntimeList>'
$manifest += '    <RequiredRuntime Name="CSXS" Version="5.0" />'
$manifest += '  </RequiredRuntimeList>'
$manifest += '</ExecutionEnvironment>'
$manifest += '<DispatchInfoList>'
$manifest += '  <Extension Id="com.roblox.phototolua.panel">'
$manifest += '    <DispatchInfo>'
$manifest += '      <Resources>'
$manifest += '        <MainPath>./index.html</MainPath>'
$manifest += '        <CEFCommandLine>'
$manifest += '          <Parameter>--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure,NetworkService</Parameter>'
$manifest += '          <Parameter>--enable-nodejs</Parameter>'
$manifest += '        </CEFCommandLine>'
$manifest += '      </Resources>'
$manifest += '      <Lifecycle><AutoVisible>true</AutoVisible></Lifecycle>'
$manifest += '      <UI>'
$manifest += '        <Type>ModalDialog</Type>'
$manifest += '        <Menu>FigmaPS2Roblox</Menu>'
$manifest += '        <Geometry>'
$manifest += '          <Size><Height>620</Height><Width>380</Width></Size>'
$manifest += '          <MaxSize><Height>900</Height><Width>800</Width></MaxSize>'
$manifest += '          <MinSize><Height>500</Height><Width>360</Width></MinSize>'
$manifest += '        </Geometry>'
$manifest += '      </UI>'
$manifest += '    </DispatchInfo>'
$manifest += '  </Extension>'
$manifest += '</DispatchInfoList>'
$manifest += '</ExtensionManifest>'

[System.IO.File]::WriteAllText((Join-Path $dst "CSXS\manifest.xml"), $manifest, [System.Text.Encoding]::UTF8)
Write-Host "OK: manifest.xml updated"

Write-Host ""
Write-Host "CORRECOES APLICADAS!" -ForegroundColor Green
Write-Host "Reinicie o Photoshop e teste: Window > Extensions > FigmaPS2Roblox"
