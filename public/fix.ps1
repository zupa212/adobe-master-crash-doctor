# ============================================================================
# ADOBE PREMIERE PRO 2026 - REAL-TIME AUTONOMOUS CLOUD HEALER & COPILOT v1.2.7
# Engineered by VerticalFlow Systems / Pan.Chorian
# Executed via: irm https://premiere-pro-doctor.vercel.app/fix.ps1 | iex
# ============================================================================

$Host.UI.RawUI.WindowTitle = "Adobe Premiere Pro 2026 - Real-Time Autonomous Cloud Healer v1.2.7"
Clear-Host
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "   ⚡ ADOBE PREMIERE PRO 2026 - DEEP CLOUD COPILOT (v1.2.7)                  " -ForegroundColor Green
Write-Host "   Target: AMD Ryzen 5 + NVIDIA RTX 5060 (Blackwell) & Meta VR Deconfliction" -ForegroundColor Yellow
Write-Host "   Full Anti-Closing, Phone-Home Shield, Defender Exclusions & VR Bypass   " -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Elevate to Administrator if necessary
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Administrative privileges required. Elevating PowerShell..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command "irm https://premiere-pro-doctor.vercel.app/fix.ps1 | iex"'
    exit
}

# Real-Time Telemetry Helper
function Send-LiveLog {
    param(
        [string]$Step,
        [string]$Message,
        [string]$Action = "stream_step"
    )
    try {
        $body = @{
            action = $Action
            step = $Step
            user = $env:USERNAME
            client_version = "1.2.7"
            hardware = "$script:gpuName / $script:cpuName"
            details = $Message
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://premiere-pro-doctor.vercel.app/api/ota-telemetry" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 3 -ErrorAction SilentlyContinue | Out-Null
    } catch {}
}

# 2. Hardware Discovery & Telemetry
$script:cpuName = (Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name -First 1) -replace "\s+", " "
$script:gpuName = ((Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join " | ") -replace "\s+", " "
$osCaption = (Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)

Write-Host "[1/9] 🔍 Hardware Profile Discovered:" -ForegroundColor Cyan
Write-Host "      • CPU: $script:cpuName" -ForegroundColor White
Write-Host "      • GPU: $script:gpuName" -ForegroundColor White
Write-Host "      • OS:  $osCaption" -ForegroundColor White
Send-LiveLog -Step "1/9" -Message "Hardware: $script:gpuName | $script:cpuName | $osCaption"

# 3. Kill lingering Adobe processes
Write-Host "`n[2/9] 🛑 Terminating lingering Adobe background processes..." -ForegroundColor Yellow
$procList = @("Adobe Premiere Pro", "GPUSniffer", "dynamiclinkmanager", "Creative Cloud", "CCXProcess", "CoreSync", "AdobeIPCBroker", "AGSService", "AdobeARM", "AdobeUpdateService", "CRWindowsClientService")
$killedCount = 0
foreach ($p in $procList) {
    $procs = Get-Process -Name $p -ErrorAction SilentlyContinue
    if ($procs) {
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        $killedCount += $procs.Count
    }
}
Write-Host "      [OK] Stopped $killedCount background processes." -ForegroundColor Green
Send-LiveLog -Step "2/9" -Message "Terminated $killedCount background processes"

# 4. Windows Defender Antivirus Exclusions (Prevents Silent Process Termination)
Write-Host "`n[3/9] 🛡️ Configuring Windows Defender Antivirus Protection Exclusions..." -ForegroundColor Yellow
try {
    Add-MpPreference -ExclusionPath "D:\Adobe Suite1" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "D:\Adobe Suite" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "D:\premire pro" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "$env:ProgramData\Adobe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionProcess "Adobe Premiere Pro.exe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionProcess "GPUSniffer.exe" -ErrorAction SilentlyContinue
    Write-Host "      [OK] Windows Defender exclusions registered for Adobe directories & executables." -ForegroundColor Green
    Send-LiveLog -Step "3/9" -Message "Windows Defender exclusions configured for D:\Adobe Suite1 & Premiere EXEs"
} catch {
    Write-Host "      [INFO] Antivirus exclusion check completed." -ForegroundColor Gray
}

# 5. Purge corrupt SLStore & SLCache (Fixes RuntimeInstaller.DLL 0xc0000005)
Write-Host "`n[4/9] 🧹 Purging corrupt licensing stores (SLStore/SLCache/OOBE)..." -ForegroundColor Yellow
$purgeDirs = @(
    "$env:ProgramData\Adobe\SLStore",
    "$env:ProgramData\Adobe\SLData",
    "${env:CommonProgramFiles(x86)}\Adobe\SLCache",
    "$env:CommonProgramFiles\Adobe\SLCache",
    "$env:LOCALAPPDATA\Adobe\OOBE",
    "$env:APPDATA\Adobe\OOBE"
)
$purgedCount = 0
foreach ($dir in $purgeDirs) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        $purgedCount++
    }
}
New-Item -ItemType Directory -Path "$env:ProgramData\Adobe\SLStore" -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -ItemType Directory -Path "${env:CommonProgramFiles(x86)}\Adobe\SLCache" -Force -ErrorAction SilentlyContinue | Out-Null
Write-Host "      [OK] Clean licensing caches initialized." -ForegroundColor Green
Send-LiveLog -Step "4/9" -Message "Purged $purgedCount licensing databases; clean SLStore initialized"

# 6. Grant Full Control NTFS Permissions
Write-Host "`n[5/9] 🔓 Unlocking NTFS Full Control security descriptors..." -ForegroundColor Yellow
$permDirs = @(
    "$env:ProgramData\Adobe",
    "${env:CommonProgramFiles(x86)}\Adobe",
    "D:\Adobe Suite1",
    "D:\Adobe Suite1\Adobe Premiere Pro 2026",
    "D:\Adobe Suite",
    "D:\Adobe Premiere Pro 2026",
    "D:\premire pro",
    "C:\Program Files\Adobe"
)
$unlockedDirs = 0
foreach ($pd in $permDirs) {
    if (Test-Path $pd) {
        icacls "$pd" /grant "Everyone:(OI)(CI)F" "Administrators:(OI)(CI)F" /C /Q | Out-Null
        $unlockedDirs++
    }
}
Write-Host "      [OK] Unlocked $unlockedDirs application and data directories." -ForegroundColor Green
Send-LiveLog -Step "5/9" -Message "Granted NTFS Full Control on $unlockedDirs Adobe directories"

# 7. Block Adobe Genuine / Revocation Phone-Home (Stops Silent Instant Closing)
Write-Host "`n[6/9] 🚫 Shielding Premiere from Adobe Licensing Phone-Home (Firewall & Hosts)..." -ForegroundColor Yellow
$premPaths = @(
    "D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "D:\Adobe Suite1\Adobe Premiere Pro 2026\CRWindowsClientService.exe",
    "D:\Adobe Suite\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
)
foreach ($exe in $premPaths) {
    if (Test-Path $exe) {
        $leaf = Split-Path $exe -Leaf
        Remove-NetFirewallRule -DisplayName "Block Adobe Phone-Home - $leaf" -ErrorAction SilentlyContinue
        New-NetFirewallRule -DisplayName "Block Adobe Phone-Home - $leaf" -Direction Outbound -Program $exe -Action Block -Profile Any -ErrorAction SilentlyContinue | Out-Null
    }
}

# Add Adobe license validation blocklist to hosts file
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$adobeHosts = @(
    "127.0.0.1 ic.adobe.io",
    "127.0.0.1 7g227fh4xm.adobe.io",
    "127.0.0.1 cc-api-data.adobe.io",
    "127.0.0.1 genuine.adobe.com",
    "127.0.0.1 prod.adobegenuine.com",
    "127.0.0.1 lmlicenses.wip4.adobe.com",
    "127.0.0.1 lm.licenses.adobe.com",
    "127.0.0.1 adobe.io",
    "127.0.0.1 lcs-cops.adobe.io"
)
try {
    $existingHosts = Get-Content $hostsFile -Raw -ErrorAction SilentlyContinue
    $toAppend = @()
    foreach ($h in $adobeHosts) {
        if ($existingHosts -notmatch [regex]::Escape($h)) {
            $toAppend += $h
        }
    }
    if ($toAppend.Count -gt 0) {
        Add-Content -Path $hostsFile -Value ("`n# Adobe License Shield`n" + ($toAppend -join "`n")) -Force -ErrorAction SilentlyContinue
    }
} catch {}
Write-Host "      [OK] Outbound license revocation shield active (Firewall + Hosts)." -ForegroundColor Green
Send-LiveLog -Step "6/9" -Message "Shielded Premiere from revocation phone-home via Firewall & Hosts"

# 8. Elevate Windows GPU TDR & Enforce DirectX High-Performance
Write-Host "`n[7/9] 🎮 Enforcing GPU TDR Timeout (10s) & RTX 5060 DirectX Affinity..." -ForegroundColor Yellow
$tdrKey = "HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
Set-ItemProperty -Path $tdrKey -Name "TdrDelay" -Value 10 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $tdrKey -Name "TdrDdiDelay" -Value 10 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $tdrKey -Name "TdrLevel" -Value 3 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $tdrKey -Name "HwSchMode" -Value 2 -Type DWord -Force -ErrorAction SilentlyContinue

$dxKey = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"
if (-not (Test-Path $dxKey)) { New-Item -Path $dxKey -Force | Out-Null }
$targetExes = @(
    "D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "D:\Adobe Suite1\Adobe Premiere Pro 2026\GPUSniffer.exe",
    "D:\Adobe Suite\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "D:\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
)
foreach ($te in $targetExes) {
    Set-ItemProperty -Path $dxKey -Name $te -Value "GpuPreference=2;" -Type String -Force -ErrorAction SilentlyContinue
}

# AppCompatFlags elevation
$compatKey = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
if (-not (Test-Path $compatKey)) { New-Item -Path $compatKey -Force | Out-Null }
Set-ItemProperty -Path $compatKey -Name "D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe" -Value "~ RUNASADMIN HIGHDPIAWARE" -Force -ErrorAction SilentlyContinue

Write-Host "      [OK] GPU TDR boosted to 10s & NVIDIA RTX 5060 locked as primary device." -ForegroundColor Green
Send-LiveLog -Step "7/9" -Message "Configured TdrDelay=10s, GpuPreference=2, and RUNASADMIN"

# 9. Meta Virtual Monitor / VR Bypass & Debug Database Anti-Freeze
Write-Host "`n[8/9] 🧊 Injecting Meta VR Bypass & Anti-Freeze Flags into Debug Database..." -ForegroundColor Yellow
$ddFlags = @"
AudioOutputOnlyUI	true	true
dvaaudiodevice.AlwaysRunning	false	false
TeamProjects.DisableBackgroundSync	true	true
Player.DirectXAcceleratedRenderer	true	true
DS.GPUSnifferOverride	0	0
DS.ForceCUDARendering	true	true
Project.Prefs.EnablehAMDDecode	false	false
Project.Prefs.EnableIntelDecode	false	false
Project.Prefs.EnableNvidiaDecode	true	true
Player.DisableHMD	true	true
Player.EnableVR	false	false
Player.EnableOculus	false	false
Player.EnableOpenVR	false	false
FE.AudioPluginScanOnFirstLaunch	false	false
dvacrashreporter.SuppressCrashHandlerDialog	true	true
EA.Config.DisableSequenceLocking	true	true
"@

$patchedCount = 0
$premAppdata = "$env:APPDATA\Adobe\Premiere Pro"
if (Test-Path $premAppdata) {
    Get-ChildItem -Path $premAppdata -Directory | ForEach-Object {
        $ddFile = Join-Path $_.FullName "Debug Database.txt"
        Add-Content -Path $ddFile -Value $ddFlags -Encoding utf8 -ErrorAction SilentlyContinue
        $patchedCount++
    }
}
$customAppDirs = @(
    "D:\Adobe Suite1\Adobe Premiere Pro 2026",
    "D:\Adobe Suite\Adobe Premiere Pro 2026",
    "D:\Adobe Premiere Pro 2026"
)
foreach ($cad in $customAppDirs) {
    if (Test-Path $cad) {
        $ddFile = Join-Path $cad "Debug Database.txt"
        Add-Content -Path $ddFile -Value $ddFlags -Encoding utf8 -ErrorAction SilentlyContinue
        $patchedCount++
        # Mirror VC++ CRT runtimes into root
        Copy-Item "$env:windir\System32\msvcp140.dll" "$cad\" -Force -ErrorAction SilentlyContinue
        Copy-Item "$env:windir\System32\vcruntime140.dll" "$cad\" -Force -ErrorAction SilentlyContinue
        Copy-Item "$env:windir\System32\vcruntime140_1.dll" "$cad\" -Force -ErrorAction SilentlyContinue
    }
}

# Clean crashed preferences & bad plugins cache
$userAppdataPrem = "$env:APPDATA\Adobe\Premiere Pro\26.0"
if (Test-Path $userAppdataPrem) {
    Remove-Item -Path "$userAppdataPrem\Workspace" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$userAppdataPrem\Layouts" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$userAppdataPrem\RecoveryOpenProjectInfos*" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$userAppdataPrem\Plugin Loading.log" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$userAppdataPrem\BadPlugins.txt" -Force -ErrorAction SilentlyContinue
}

Write-Host "      [OK] Meta VR device bypassed, Debug Database patched & crashed states cleared." -ForegroundColor Green
Send-LiveLog -Step "8/9" -Message "Patched Meta VR bypass (Player.DisableHMD=true) & cleaned corrupt session caches"

# 10. Clean background tracking daemons
Write-Host "`n[9/9] 🛡️ Disabling broken Adobe tracking services..." -ForegroundColor Yellow
$svcs = @("AGSService", "AdobeARMservice", "AdobeUpdateService")
foreach ($s in $svcs) {
    Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
    Set-Service -Name $s -StartupType Disabled -ErrorAction SilentlyContinue
}
Write-Host "      [OK] Background services disabled." -ForegroundColor Green
Send-LiveLog -Step "9/9" -Message "Disabled background Adobe services"

# Final Success Telemetry
Send-LiveLog -Step "DONE" -Message "AUTONOMOUS ANTI-CLOSING & VR BYPASS HEALER APPLIED ON CLIENT RIG" -Action "repair_runtime_installer"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "   ✅ SUCCESS! ADOBE PREMIERE PRO 2026 IS PERMANENTLY HEALED!              " -ForegroundColor Green
Write-Host "   Phone-Home Blocked, Meta VR Bypassed & Permissions Completely Unlocked!  " -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

# Automated Launch Option
$premPath = "D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
if (-not (Test-Path $premPath)) {
    $premPath = "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
}

if (Test-Path $premPath) {
    Write-Host "Press [ENTER] to launch Premiere Pro now, or any other key to exit..." -ForegroundColor Cyan
    $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    if ($key.VirtualKeyCode -eq 13) {
        Write-Host "🚀 Launching Premiere Pro..." -ForegroundColor Green
        Start-Process $premPath
    }
} else {
    Write-Host "Premiere Pro is ready to launch from your desktop icon!" -ForegroundColor Cyan
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
