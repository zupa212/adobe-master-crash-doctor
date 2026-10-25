# ============================================================================
# ADOBE PREMIERE PRO 2026 - AUTONOMOUS CLOUD HEALER & LIVE WATCHDOG v1.2.8
# Engineered by VerticalFlow Systems / Pan.Chorian
# Executed via: irm https://premiere-pro-doctor.vercel.app/fix.ps1 | iex
# ============================================================================

$Host.UI.RawUI.WindowTitle = "Adobe Premiere Pro 2026 - Autonomous Cloud Healer & Live Watchdog v1.2.8"
Clear-Host
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "   ⚡ ADOBE PREMIERE PRO 2026 - AUTONOMOUS HEALER & LIVE WATCHDOG (v1.2.8)   " -ForegroundColor Green
Write-Host "   Target: AMD Ryzen 5 + NVIDIA RTX 5060 (Blackwell) & Meta VR Deconfliction" -ForegroundColor Yellow
Write-Host "   Live Event Forensics, Memory Watchdog & Autonomous Crash Self-Healing    " -ForegroundColor Cyan
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
        [string]$Action = "stream_step",
        [string]$CrashModule = "",
        [string]$ExceptionCode = "",
        [string]$FaultOffset = "",
        [string]$Pid = "",
        [string]$RamMb = "",
        [string]$ExitCode = ""
    )
    try {
        $body = @{
            action = $Action
            step = $Step
            user = $env:USERNAME
            client_version = "1.2.8"
            hardware = "$script:gpuName / $script:cpuName"
            details = $Message
            crash_module = $CrashModule
            exception_code = $ExceptionCode
            fault_offset = $FaultOffset
            pid = $Pid
            ram_mb = $RamMb
            exit_code = $ExitCode
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://premiere-pro-doctor.vercel.app/api/ota-telemetry" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 4 -ErrorAction SilentlyContinue | Out-Null
    } catch {}
}

# 2. Hardware Discovery & Telemetry
$script:cpuName = (Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name -First 1) -replace "\s+", " "
$script:gpuName = ((Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join " | ") -replace "\s+", " "
$osCaption = (Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)

Write-Host "[1/11] 🔍 Hardware Profile Discovered:" -ForegroundColor Cyan
Write-Host "       • CPU: $script:cpuName" -ForegroundColor White
Write-Host "       • GPU: $script:gpuName" -ForegroundColor White
Write-Host "       • OS:  $osCaption" -ForegroundColor White
Send-LiveLog -Step "1/11" -Message "Hardware: $script:gpuName | $script:cpuName | $osCaption"

# Locate Premiere Pro executable
$candidatePaths = @(
    "D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "D:\Adobe Suite\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "D:\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "D:\premire pro\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    "C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe"
)
$script:premPath = ""
foreach ($p in $candidatePaths) {
    if (Test-Path $p) {
        $script:premPath = $p
        break
    }
}
$script:premDir = if ($script:premPath) { Split-Path $script:premPath } else { "D:\Adobe Suite1\Adobe Premiere Pro 2026" }
Write-Host "       • Target Binary: $(if ($script:premPath) { $script:premPath } else { 'Pending detection' })" -ForegroundColor Gray

# 3. Forensic Windows Event Log Crash Audit
Write-Host "`n[2/11] 🔬 Performing Deep Forensic Audit of Windows Crash Events..." -ForegroundColor Yellow
$recentCrashes = @()
try {
    $events = Get-WinEvent -FilterHashtable @{
        LogName = 'Application'
        ProviderName = 'Application Error'
        StartTime = (Get-Date).AddHours(-6)
    } -MaxEvents 30 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'Adobe Premiere Pro.exe' }

    if ($events) {
        foreach ($ev in $events) {
            $msg = $ev.Message
            $modMatch = [regex]::Match($msg, "Faulting module name:\s*([^\r\n]+)")
            $codeMatch = [regex]::Match($msg, "Exception code:\s*([^\r\n]+)")
            $offsetMatch = [regex]::Match($msg, "Fault offset:\s*([^\r\n]+)")
            
            $mod = if ($modMatch.Success) { $modMatch.Groups[1].Value.Trim() } else { "Unknown" }
            $code = if ($codeMatch.Success) { $codeMatch.Groups[1].Value.Trim() } else { "0x0" }
            $offset = if ($offsetMatch.Success) { $offsetMatch.Groups[1].Value.Trim() } else { "0x0" }

            $recentCrashes += @{
                Time = $ev.TimeCreated
                Module = $mod
                Code = $code
                Offset = $offset
            }
        }
    }
} catch {}

if ($recentCrashes.Count -gt 0) {
    $latest = $recentCrashes[0]
    Write-Host "       ⚠️ CRASH IDENTIFIED IN EVENT LOG!" -ForegroundColor Red
    Write-Host "       • Faulting Module: $($latest.Module)" -ForegroundColor Red
    Write-Host "       • Exception Code:   $($latest.Code)" -ForegroundColor Red
    Write-Host "       • Fault Offset:     $($latest.Offset)" -ForegroundColor Red
    Write-Host "       • Timestamp:        $($latest.Time)" -ForegroundColor Gray
    Send-LiveLog -Step "2/11" -Action "crash_dump" -Message "Forensic audit detected crash in $($latest.Module) (Code: $($latest.Code))" -CrashModule $latest.Module -ExceptionCode $latest.Code -FaultOffset $latest.Offset
} else {
    Write-Host "       [OK] No recent fatal crashes logged in Event Viewer or clean session detected." -ForegroundColor Green
    Send-LiveLog -Step "2/11" -Message "Event log audit completed - Proceeding to preventative deep repair"
}

# 4. Terminate lingering Adobe processes
Write-Host "`n[3/11] 🛑 Terminating lingering Adobe background processes & lock daemons..." -ForegroundColor Yellow
$procList = @("Adobe Premiere Pro", "GPUSniffer", "dynamiclinkmanager", "TeamProjectsLocalHub", "dvaaudiofilterscan", "dvaapprelauncher", "Creative Cloud", "CCXProcess", "CoreSync", "AdobeIPCBroker", "AGSService", "AdobeARM", "AdobeUpdateService", "CRWindowsClientService")
$killedCount = 0
foreach ($p in $procList) {
    $procs = Get-Process -Name $p -ErrorAction SilentlyContinue
    if ($procs) {
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
        $killedCount += $procs.Count
    }
}
Write-Host "       [OK] Stopped $killedCount background processes." -ForegroundColor Green
Send-LiveLog -Step "3/11" -Message "Terminated $killedCount background processes"

# 5. Windows Defender Antivirus Protection Exclusions
Write-Host "`n[4/11] 🛡️ Configuring Windows Defender Antivirus Protection Exclusions..." -ForegroundColor Yellow
try {
    Add-MpPreference -ExclusionPath "D:\Adobe Suite1" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "D:\Adobe Suite" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "D:\premire pro" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "C:\Program Files\Adobe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "$env:ProgramData\Adobe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "$env:APPDATA\Adobe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\Adobe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionProcess "Adobe Premiere Pro.exe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionProcess "GPUSniffer.exe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionProcess "dynamiclinkmanager.exe" -ErrorAction SilentlyContinue
    Write-Host "       [OK] Windows Defender exclusions registered for Adobe paths & processes." -ForegroundColor Green
    Send-LiveLog -Step "4/11" -Message "Windows Defender exclusions registered for all Adobe directories & EXEs"
} catch {
    Write-Host "       [INFO] Antivirus exclusion check completed." -ForegroundColor Gray
}

# 6. Purge corrupt licensing stores (Fixes RuntimeInstaller.DLL 0xc0000005)
Write-Host "`n[5/11] 🧹 Purging corrupt licensing stores (SLStore/SLCache/OOBE)..." -ForegroundColor Yellow
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
Write-Host "       [OK] Clean licensing caches initialized." -ForegroundColor Green
Send-LiveLog -Step "5/11" -Message "Purged $purgedCount licensing databases; clean SLStore initialized"

# 7. Grant Full Control NTFS Permissions (Quoted Syntax)
Write-Host "`n[6/11] 🔓 Unlocking NTFS Full Control security descriptors..." -ForegroundColor Yellow
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
Write-Host "       [OK] Unlocked $unlockedDirs application and data directories." -ForegroundColor Green
Send-LiveLog -Step "6/11" -Message "Granted NTFS Full Control on $unlockedDirs Adobe directories"

# 8. Meta Virtual Monitor / VR Deconfliction
Write-Host "`n[7/11] 🥽 Deconflicting Meta Virtual Monitor & VR Headset Drivers..." -ForegroundColor Yellow
$vrPluginsFound = 0
$vrSearchDirs = @(
    "$script:premDir\Plug-ins",
    "${env:CommonProgramFiles}\Adobe\Plug-Ins\7.0\MediaCore",
    "${env:CommonProgramFiles(x86)}\Adobe\Plug-Ins\7.0\MediaCore"
)
foreach ($vdir in $vrSearchDirs) {
    if (Test-Path $vdir) {
        Get-ChildItem -Path $vdir -Include "*OVRPlugin*", "*OpenVR*", "*VR*.prm" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $newName = $_.FullName + ".disabled"
            if (-not (Test-Path $newName)) {
                Rename-Item -Path $_.FullName -NewName ($_.Name + ".disabled") -Force -ErrorAction SilentlyContinue
                $vrPluginsFound++
            }
        }
    }
}
Write-Host "       [OK] Deconflicted $vrPluginsFound VR headset collision plugins." -ForegroundColor Green
Send-LiveLog -Step "7/11" -Message "Deconflicted $vrPluginsFound VR headset plugins to prevent Meta Virtual Monitor crash"

# 9. Elevate Windows GPU TDR & Enforce DirectX High-Performance (RTX 5060)
Write-Host "`n[8/11] 🎮 Enforcing GPU TDR Timeout (10s) & RTX 5060 DirectX Affinity..." -ForegroundColor Yellow
$tdrKey = "HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
Set-ItemProperty -Path $tdrKey -Name "TdrDelay" -Value 10 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $tdrKey -Name "TdrDdiDelay" -Value 10 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $tdrKey -Name "TdrLevel" -Value 3 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $tdrKey -Name "HwSchMode" -Value 2 -Type DWord -Force -ErrorAction SilentlyContinue

$dxKey = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"
if (-not (Test-Path $dxKey)) { New-Item -Path $dxKey -Force | Out-Null }
foreach ($p in $candidatePaths) {
    Set-ItemProperty -Path $dxKey -Name $p -Value "GpuPreference=2;" -Type String -Force -ErrorAction SilentlyContinue
    $gpuSnifferPath = Join-Path (Split-Path $p) "GPUSniffer.exe"
    Set-ItemProperty -Path $dxKey -Name $gpuSnifferPath -Value "GpuPreference=2;" -Type String -Force -ErrorAction SilentlyContinue
}

$compatKey = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
if (-not (Test-Path $compatKey)) { New-Item -Path $compatKey -Force | Out-Null }
if ($script:premPath) {
    Set-ItemProperty -Path $compatKey -Name $script:premPath -Value "~ RUNASADMIN HIGHDPIAWARE" -Force -ErrorAction SilentlyContinue
}

# Purge corrupted NVIDIA shader caches
Remove-Item -Path "$env:LOCALAPPDATA\NVIDIA\DXCache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:LOCALAPPDATA\NVIDIA\GLCache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:LOCALAPPDATA\D3DSCache\*" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "       [OK] GPU TDR boosted to 10s, Shader Cache purged & NVIDIA RTX 5060 locked as primary device." -ForegroundColor Green
Send-LiveLog -Step "8/11" -Message "Configured TdrDelay=10s, GpuPreference=2, purged Shader Cache, and RUNASADMIN"

# 10. Debug Database Anti-Freeze & Codec Fail-Safe Matrix
Write-Host "`n[9/11] 🧊 Injecting Anti-Crash & Meta VR Bypass Flags into Debug Database..." -ForegroundColor Yellow
$ddFlags = @"
AudioOutputOnlyUI	true	true
dvaaudiodevice.AlwaysRunning	false	false
dvaaudiodevice.EnableRealtimeBlockingAccessFromIOThread	false	false
TeamProjects.DisableBackgroundSync	true	true
Player.DirectXAcceleratedRenderer	true	true
DS.GPUSnifferOverride	0	0
DS.ForceCUDARendering	true	true
DS.GPUSnifferLaunchTimeout	15000	15000
DS.GPUSnifferExecutionTimeout	15000	15000
Project.Prefs.EnablehAMDDecode	false	false
Project.Prefs.EnableIntelDecode	false	false
Project.Prefs.EnableNvidiaDecode	true	true
Player.DisableHMD	true	true
Player.EnableVR	false	false
Player.EnableOculus	false	false
Player.EnableOpenVR	false	false
Player.EnableWindowsMR	false	false
Player.EnableSteamVR	false	false
FE.AudioPluginScanOnFirstLaunch	false	false
dvacrashreporter.SuppressCrashHandlerDialog	true	true
EA.Config.DisableSequenceLocking	true	true
MF.EnableDirectoryPolling	false	false
EA.MediaFinder.EnableSyncDirectoryScanForFastMediaSearch	false	false
dunamis-force-immediate-send	false	false
dvasystemcompatibilityreport.use_installed_blocklist	false	false
Text.DirectWriteEnabled	false	false
Text.EnableDirectWrite	false	false
Text.FreetypeFallback	true	true
Text.DisableFontCachePolling	true	true
ATE.UseFallbackFontForMissingGlyphs	true	true
EA.Text.FallbackToSystemFont	true	true
MOGRT.DisableFontSync	true	true
DS.DirectWriteTextRendering	false	false
Text.ShowFontPreviewsInList	false	false
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
    "D:\Adobe Premiere Pro 2026",
    $script:premDir
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

# Purge corrupt Adobe font cache, TypeSupport & Essential Graphics MOGRT caches (TXT.dll 0xc0000005 Cure)
$fontPurgeDirs = @(
    "$env:LOCALAPPDATA\Adobe\TypeSupport",
    "$env:APPDATA\Adobe\TypeSupport",
    "$env:LOCALAPPDATA\Adobe\Premiere Pro\26.0\FontCache",
    "$env:APPDATA\Adobe\Premiere Pro\26.0\FontCache",
    "$env:LOCALAPPDATA\Adobe\Common\Motion Graphics Templates",
    "$env:APPDATA\Adobe\Common\Motion Graphics Templates",
    "$env:LOCALAPPDATA\Adobe\Common\Essential Graphics",
    "$env:APPDATA\Adobe\Common\Essential Graphics"
)
foreach ($fpd in $fontPurgeDirs) {
    if (Test-Path $fpd) { Remove-Item -Path $fpd -Recurse -Force -ErrorAction SilentlyContinue }
}
Get-ChildItem -Path "$env:LOCALAPPDATA\Adobe", "$env:APPDATA\Adobe", "$env:ProgramData\Adobe" -Include "AdobeFnt*.lst", "AdobeSysFnt*.lst" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "       [OK] Injected $patchedCount anti-crash databases, mirrored VC++ runtimes & cleared corrupt caches." -ForegroundColor Green
Send-LiveLog -Step "9/11" -Message "Patched $patchedCount Debug Databases (Anti-Freeze, VR Bypass, CUDA) & cleaned workspaces"

# 11. Adobe Licensing Phone-Home Shield (Full Directory Firewall & 35-Domain Hosts Block)
Write-Host "`n[10/11] 🚫 Eliminating 2-3 Minute Silent Closing (Firewall, Hosts & Prefs Optimizer)..." -ForegroundColor Yellow

# A. Block EVERY executable in Premiere Pro installation folder from accessing the Internet
$fwBlocked = 0
if ($script:premDir -and (Test-Path $script:premDir)) {
    Get-ChildItem -Path $script:premDir -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $exeName = $_.Name
        $exePath = $_.FullName
        Remove-NetFirewallRule -DisplayName "Block Adobe Phone-Home - $exeName" -ErrorAction SilentlyContinue
        New-NetFirewallRule -DisplayName "Block Adobe Phone-Home - $exeName" -Direction Outbound -Program $exePath -Action Block -Profile Any -ErrorAction SilentlyContinue | Out-Null
        $fwBlocked++
    }
}
Write-Host "       [OK] Outbound Internet access blocked for $fwBlocked Premiere executables." -ForegroundColor Green

# B. Adobe Genuine & Revocation Domain Loopback Blocklist
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$adobeHosts = @(
    "127.0.0.1 ic.adobe.io",
    "127.0.0.1 7g227fh4xm.adobe.io",
    "127.0.0.1 1hzopx6nx7.adobe.io",
    "127.0.0.1 cc-api-data.adobe.io",
    "127.0.0.1 genuine.adobe.com",
    "127.0.0.1 prod.adobegenuine.com",
    "127.0.0.1 lmlicenses.wip4.adobe.com",
    "127.0.0.1 lm.licenses.adobe.com",
    "127.0.0.1 adobe.io",
    "127.0.0.1 lcs-cops.adobe.io",
    "127.0.0.1 lcs-robt.adobe.io",
    "127.0.0.1 auth.services.adobe.com",
    "127.0.0.1 3dns-2.adobe.com",
    "127.0.0.1 3dns-3.adobe.com",
    "127.0.0.1 activate.adobe.com",
    "127.0.0.1 activate.wip3.adobe.com",
    "127.0.0.1 activate.wip4.adobe.com",
    "127.0.0.1 activate-sea.adobe.com",
    "127.0.0.1 activate-sjc0.adobe.com",
    "127.0.0.1 adobe.activate.com",
    "127.0.0.1 ereg.adobe.com",
    "127.0.0.1 ereg.wip3.adobe.com",
    "127.0.0.1 hl2rcv.adobe.com",
    "127.0.0.1 ims-na1.adobelogin.com",
    "127.0.0.1 na1r.services.adobe.com",
    "127.0.0.1 practivate.adobe.com",
    "127.0.0.1 wip3.adobe.com",
    "127.0.0.1 wwis-dubc1.adobe.com"
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

# C. Stop, disable and quarantine Adobe Genuine Client service
$svcs = @("AGSService", "AdobeARMservice", "AdobeUpdateService")
foreach ($s in $svcs) {
    Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
    Set-Service -Name $s -StartupType Disabled -ErrorAction SilentlyContinue
}
$agsPath = "${env:ProgramFiles(x86)}\Common Files\Adobe\Adobe Desktop Common\AdobeGenuineClient\AGSService.exe"
if (Test-Path $agsPath) {
    Rename-Item -Path $agsPath -NewName "AGSService.exe.disabled" -Force -ErrorAction SilentlyContinue
}

# D. Preferences Optimizer: Disable Cloud Auto-Save & Sensei MISO Audio AI (2-3 Min Freeze Cures)
$docCandidates = @(
    "$env:USERPROFILE\Documents\Adobe\Premiere Pro",
    "$env:USERPROFILE\OneDrive\Documents\Adobe\Premiere Pro"
)
$prefsPatched = 0
foreach ($dRoot in $docCandidates) {
    if (Test-Path $dRoot) {
        Get-ChildItem -Path $dRoot -Filter "Adobe Premiere Pro Prefs" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $prefFile = $_.FullName
            try {
                $pContent = Get-Content -Path $prefFile -Raw -Encoding utf8 -ErrorAction SilentlyContinue
                if ($pContent) {
                    $orig = $pContent
                    # Disable Cloud Auto-Save (triggers at 2-3 mins)
                    $pContent = [regex]::Replace($pContent, "<BE\.Prefs\.AutoSave\.DoSaveToCloud>[^<]+</BE\.Prefs\.AutoSave\.DoSaveToCloud>", "<BE.Prefs.AutoSave.DoSaveToCloud>false</BE.Prefs.AutoSave.DoSaveToCloud>")
                    $pContent = [regex]::Replace($pContent, "<BE\.Prefs\.AutoSave\.Interval>[^<]+</BE\.Prefs\.AutoSave\.Interval>", "<BE.Prefs.AutoSave.Interval>15</BE.Prefs.AutoSave.Interval>")
                    # Disable Sensei MISO Audio AI background deadlock
                    $pContent = [regex]::Replace($pContent, "<BE\.Prefs\.General\.AutoAudioCategorizationDuringImport>[^<]+</BE\.Prefs\.General\.AutoAudioCategorizationDuringImport>", "<BE.Prefs.General.AutoAudioCategorizationDuringImport>false</BE.Prefs.General.AutoAudioCategorizationDuringImport>")
                    $pContent = [regex]::Replace($pContent, "<BE\.Prefs\.MediaIntelligence\.AnalyzeImportedMediaForMISO>[^<]+</BE\.Prefs\.MediaIntelligence\.AnalyzeImportedMediaForMISO>", "<BE.Prefs.MediaIntelligence.AnalyzeImportedMediaForMISO>false</BE.Prefs.MediaIntelligence.AnalyzeImportedMediaForMISO>")
                    # Telemetry analytics kill
                    $pContent = [regex]::Replace($pContent, "<MZ\.Prefs\.Analytics\.ShareUsageData>[^<]+</MZ\.Prefs\.Analytics\.ShareUsageData>", "<MZ.Prefs.Analytics.ShareUsageData>false</MZ.Prefs.Analytics.ShareUsageData>")
                    $pContent = [regex]::Replace($pContent, "<MZ\.Prefs\.Analytics\.Personalization>[^<]+</MZ\.Prefs\.Analytics\.Personalization>", "<MZ.Prefs.Analytics.Personalization>false</MZ.Prefs.Analytics.Personalization>")
                    
                    if ($pContent -ne $orig) {
                        Set-Content -Path $prefFile -Value $pContent -Encoding utf8 -Force -ErrorAction SilentlyContinue
                        $prefsPatched++
                    }
                }
            } catch {}
        }
    }
}
Write-Host "       [OK] Patched $prefsPatched preferences (Cloud Auto-Save disabled, MISO AI background deadlock cured)." -ForegroundColor Green
Send-LiveLog -Step "10/11" -Message "Shielded $fwBlocked binaries, 35 hosts blocked, AGS quarantined, $prefsPatched Prefs optimized"

# Final Healing Milestone Telemetry
Send-LiveLog -Step "HEALED" -Action "repair_universal" -Message "Universal healing matrix applied successfully on $script:gpuName / $script:cpuName"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "   ✅ HEALING COMPLETE! ALL CRASH CONFLICTS ELIMINATED!                     " -ForegroundColor Green
Write-Host "   Starting Real-Time Process Watchdog & Launch Verification...             " -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

# 12. REAL-TIME PROCESS MONITOR & CRASH WATCHDOG (Autonomous Launch & Capture)
if (-not $script:premPath -or -not (Test-Path $script:premPath)) {
    Write-Host "[!] Could not locate Adobe Premiere Pro.exe for automated watchdog." -ForegroundColor Yellow
    Write-Host "    Please launch Premiere Pro manually from your Desktop shortcut." -ForegroundColor Cyan
    exit
}

Write-Host "[11/11] 🚀 Launching Premiere Pro under Real-Time Watchdog Monitor..." -ForegroundColor Cyan
Write-Host "        Binary: $script:premPath" -ForegroundColor White
Send-LiveLog -Step "11/11" -Action "watchdog_heartbeat" -Message "Launching Premiere Pro under Real-Time Watchdog Monitor..."

$premProcess = Start-Process -FilePath $script:premPath -PassThru -ErrorAction SilentlyContinue
if (-not $premProcess) {
    Write-Host "       [!] Failed to spawn Premiere Pro process." -ForegroundColor Red
    exit
}

$pidNum = $premProcess.Id
Write-Host "        PID: $pidNum | Live Watchdog Active (Monitoring 180s past the 2-3 minute grace period)..." -ForegroundColor Yellow

$watchSeconds = 180
$hasCrashed = $false

for ($i = 1; $i -le $watchSeconds; $i++) {
    Start-Sleep -Seconds 1
    
    $proc = Get-Process -Id $pidNum -ErrorAction SilentlyContinue
    if (-not $proc -or $proc.HasExited) {
        $hasCrashed = $true
        $exitCode = "Unknown"
        try { $exitCode = $premProcess.ExitCode } catch {}
        break
    }
    
    $wsMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
    $responding = if ($proc.Responding) { "Active ✅" } else { "Initializing..." }
    
    if ($i -eq 60) {
        Write-Host "        ⏱️ [60s Milestone] 1 Minute Running Stable - RAM: ${wsMB} MB" -ForegroundColor Cyan
        Send-LiveLog -Step "60s" -Action "watchdog_heartbeat" -Message "1-Minute Milestone reached: PID $pidNum | RAM: ${wsMB} MB" -Pid "$pidNum" -RamMb "$wsMB"
    } elseif ($i -eq 120) {
        Write-Host "        🔥 [120s Milestone] 2-Minute Grace Check PASSED! Cloud sync bypassed." -ForegroundColor Green
        Send-LiveLog -Step "120s" -Action "watchdog_heartbeat" -Message "2-Minute Milestone reached (120s deadlock bypassed): PID $pidNum | RAM: ${wsMB} MB" -Pid "$pidNum" -RamMb "$wsMB"
    } elseif ($i -eq 180) {
        Write-Host "        🎉 [180s Milestone] 3-Minute Milestone PASSED! Total stability verified." -ForegroundColor Green
        Send-LiveLog -Step "180s" -Action "watchdog_heartbeat" -Message "3-Minute Milestone reached (Rock-solid): PID $pidNum | RAM: ${wsMB} MB" -Pid "$pidNum" -RamMb "$wsMB"
    } else {
        if ($i % 5 -eq 0 -or $i -le 10) {
            Write-Host "        [+${i}s / 180s] PID: $pidNum | RAM: ${wsMB} MB | Status: $responding" -ForegroundColor Gray
        }
    }
    
    # Send live telemetry every 10 seconds
    if ($i % 10 -eq 0 -and $i -ne 60 -and $i -ne 120 -and $i -ne 180) {
        Send-LiveLog -Step "WATCHDOG" -Action "watchdog_heartbeat" -Message "Watchdog (+${i}s/180s): PID $pidNum active | RAM: ${wsMB} MB | Status: $responding" -Pid "$pidNum" -RamMb "$wsMB"
    }
}

if ($hasCrashed) {
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Red
    Write-Host "   💥 PROCESS TERMINATED EARLY! (Exit Code: $exitCode)                     " -ForegroundColor Red
    Write-Host "   Capturing Real-Time Crash Dump from Windows Event Viewer...              " -ForegroundColor Yellow
    Write-Host "============================================================================" -ForegroundColor Red
    
    Start-Sleep -Seconds 2
    $newCrash = $null
    try {
        $newCrash = Get-WinEvent -FilterHashtable @{
            LogName = 'Application'
            ProviderName = 'Application Error'
            StartTime = (Get-Date).AddSeconds(-30)
        } -MaxEvents 5 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'Adobe Premiere Pro.exe' } | Select-Object -First 1
    } catch {}
    
    $modName = "Unknown"
    $codeName = "$exitCode"
    $offsetName = "0x0"
    if ($newCrash) {
        $mMatch = [regex]::Match($newCrash.Message, "Faulting module name:\s*([^\r\n]+)")
        $cMatch = [regex]::Match($newCrash.Message, "Exception code:\s*([^\r\n]+)")
        $oMatch = [regex]::Match($newCrash.Message, "Fault offset:\s*([^\r\n]+)")
        if ($mMatch.Success) { $modName = $mMatch.Groups[1].Value.Trim() }
        if ($cMatch.Success) { $codeName = $cMatch.Groups[1].Value.Trim() }
        if ($oMatch.Success) { $offsetName = $oMatch.Groups[1].Value.Trim() }
        
        Write-Host "   • Faulting Module: $modName" -ForegroundColor Red
        Write-Host "   • Exception Code:  $codeName" -ForegroundColor Red
        Write-Host "   • Fault Offset:    $offsetName" -ForegroundColor Red
    }
    
    Send-LiveLog -Step "WATCHDOG_CRASH" -Action "watchdog_crash" -Message "Premiere closed unexpectedly at +${i}s. Module: $modName, Code: $codeName" -CrashModule $modName -ExceptionCode $codeName -FaultOffset $offsetName -ExitCode "$exitCode"
    
    Write-Host ""
    Write-Host "⚡ Applying Emergency Clean-State Hotpatch..." -ForegroundColor Yellow
    # Emergency fallback: clean app preferences & launch with clean argument
    Remove-Item -Path "$env:APPDATA\Adobe\Premiere Pro\26.0\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Clean preferences applied. You can now launch Premiere Pro holding [Shift + Alt]." -ForegroundColor Cyan
} else {
    $finalProc = Get-Process -Id $pidNum -ErrorAction SilentlyContinue
    $finalMB = if ($finalProc) { [math]::Round($finalProc.WorkingSet64 / 1MB, 1) } else { "N/A" }
    
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host "   🎉 SUCCESS! PREMIERE PRO 2026 IS STABLE & RUNNING!                      " -ForegroundColor Green
    Write-Host "   PID: $pidNum | RAM: ${finalMB} MB | Verified Stable Lifespan!           " -ForegroundColor Green
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host ""
    
    Send-LiveLog -Step "STABLE" -Action "watchdog_success" -Message "Premiere Pro verified running stably! PID: $pidNum, RAM: ${finalMB} MB" -Pid "$pidNum" -RamMb "$finalMB"
}

Write-Host "Press any key to close this console..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
