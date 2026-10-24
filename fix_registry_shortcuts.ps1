# Ensure directory
New-Item -ItemType Directory -Path "F:\AdobePremierePro2026\Plug-ins\Common" -Force -ErrorAction SilentlyContinue | Out-Null

# Fix App Paths
$appPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Premiere Pro.exe"
if (Test-Path $appPath) {
    Set-ItemProperty -Path $appPath -Name "(default)" -Value "F:\AdobePremierePro2026\Adobe Premiere Pro.exe" -Force
    Set-ItemProperty -Path $appPath -Name "Path" -Value "F:\AdobePremierePro2026\" -Force
}

# Fix Premiere Pro 26.0 Registry
$premReg = "HKLM:\SOFTWARE\Adobe\Premiere Pro\26.0"
if (Test-Path $premReg) {
    Set-ItemProperty -Path $premReg -Name "SequencePresetsPath" -Value "F:\AdobePremierePro2026\Settings\SequencePresets" -Force
    Set-ItemProperty -Path $premReg -Name "SequencePreviewPresetsPath" -Value "F:\AdobePremierePro2026\Settings\EncoderPresets\SequencePreview" -Force
    Set-ItemProperty -Path $premReg -Name "PluginInstallPath" -Value "F:\AdobePremierePro2026\Plug-ins\Common" -Force
}

# Fix Start Menu Shortcut
$wsh = New-Object -ComObject WScript.Shell
$scPath = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Adobe Premiere Pro 2026.lnk"
if (Test-Path $scPath) {
    $sc = $wsh.CreateShortcut($scPath)
    $sc.TargetPath = "F:\AdobePremierePro2026\Adobe Premiere Pro.exe"
    $sc.WorkingDirectory = "F:\AdobePremierePro2026"
    $sc.Save()
}

# Create / Update Desktop Shortcut
$desktopSc = "$env:USERPROFILE\Desktop\Adobe Premiere Pro (Repaired).lnk"
$sc2 = $wsh.CreateShortcut($desktopSc)
$sc2.TargetPath = "F:\AdobePremierePro2026\Adobe Premiere Pro.exe"
$sc2.WorkingDirectory = "F:\AdobePremierePro2026"
$sc2.Description = "Repaired Premiere Pro 2026"
$sc2.Save()
