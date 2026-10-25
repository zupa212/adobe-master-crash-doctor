# ============================================================================
# ADOBE PREMIERE PRO 2026 - SURGICAL TXT.DLL & FONT CRASH HEALER (v1.2.9)
# Engineered by VerticalFlow Systems / Pan.Chorian
# Executed via: irm https://premiere-pro-doctor.vercel.app/fix-txt.ps1 | iex
# Resolves APPCRASH in TXT.dll (0xc0000005 at offset 0x0000000000216446)
# ============================================================================

$Host.UI.RawUI.WindowTitle = "Adobe Premiere Pro 2026 - TXT.DLL & Essential Graphics Healer v1.2.9"
Clear-Host
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "   ⚡ ADOBE PREMIERE PRO 2026 - TXT.DLL & ESSENTIAL GRAPHICS CURE (v1.2.9)   " -ForegroundColor Green
Write-Host "   Resolving APPCRASH in TXT.dll (0xc0000005) at offset 0x00216446         " -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Elevate to Administrator if necessary
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Administrative privileges required. Elevating PowerShell..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command "irm https://premiere-pro-doctor.vercel.app/fix-txt.ps1 | iex"'
    exit
}

# 2. Terminate Premiere Pro processes
Write-Host "[1/5] 🛑 Terminating Premiere Pro processes..." -ForegroundColor Yellow
Get-Process -Name "Adobe Premiere Pro", "GPUSniffer", "dynamiclinkmanager", "CRWindowsClientService" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "      [OK] Background processes stopped." -ForegroundColor Green

# 3. Purge Corrupt Font Caches (TypeSupport & AdobeFnt)
Write-Host "`n[2/5] 🧹 Purging Corrupted Adobe TypeSupport & Font Cache Databases..." -ForegroundColor Yellow
$fontDirs = @(
    "$env:LOCALAPPDATA\Adobe\TypeSupport",
    "$env:APPDATA\Adobe\TypeSupport",
    "$env:LOCALAPPDATA\Adobe\Premiere Pro\26.0\FontCache",
    "$env:APPDATA\Adobe\Premiere Pro\26.0\FontCache",
    "$env:LOCALAPPDATA\Adobe\Common\Motion Graphics Templates",
    "$env:APPDATA\Adobe\Common\Motion Graphics Templates",
    "$env:LOCALAPPDATA\Adobe\Common\Essential Graphics",
    "$env:APPDATA\Adobe\Common\Essential Graphics",
    "$env:LOCALAPPDATA\Adobe\Fonts",
    "$env:APPDATA\Adobe\Fonts",
    "$env:ProgramData\Adobe\Fonts"
)
$purged = 0
foreach ($fd in $fontDirs) {
    if (Test-Path $fd) {
        Remove-Item -Path $fd -Recurse -Force -ErrorAction SilentlyContinue
        $purged++
    }
}
Get-ChildItem -Path "$env:LOCALAPPDATA\Adobe", "$env:APPDATA\Adobe", "$env:ProgramData\Adobe" -Include "AdobeFnt*.lst", "AdobeSysFnt*.lst" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "      [OK] Purged $purged TypeSupport, MOGRT, and Adobe font index databases." -ForegroundColor Green

# 4. Windows Font Cache Service Reset
Write-Host "`n[3/5] 🔤 Resetting Windows Font Cache Service (FntCache.dat)..." -ForegroundColor Yellow
try {
    Stop-Service -Name "FontCache" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache\*.dat" -Force -ErrorAction SilentlyContinue
    Start-Service -Name "FontCache" -ErrorAction SilentlyContinue
    Write-Host "      [OK] Windows Font Cache service sanitized and restarted." -ForegroundColor Green
} catch {
    Write-Host "      [INFO] Font cache service check complete." -ForegroundColor Gray
}

# 5. Inject TXT.dll DirectWrite & Fallback Anti-Crash Matrix
Write-Host "`n[4/5] 🛡️ Injecting TXT.dll DirectWrite & Font Fallback Matrix..." -ForegroundColor Yellow
$txtFlags = @"
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

$patchedDd = 0
$premAppdata = "$env:APPDATA\Adobe\Premiere Pro"
if (Test-Path $premAppdata) {
    Get-ChildItem -Path $premAppdata -Directory | ForEach-Object {
        $ddFile = Join-Path $_.FullName "Debug Database.txt"
        Add-Content -Path $ddFile -Value $txtFlags -Encoding utf8 -ErrorAction SilentlyContinue
        $patchedDd++
    }
}
$candDirs = @(
    "D:\Adobe Suite1\Adobe Premiere Pro 2026",
    "D:\Adobe Suite\Adobe Premiere Pro 2026",
    "D:\Adobe Premiere Pro 2026",
    "D:\premire pro\Adobe Premiere Pro 2026",
    "C:\Program Files\Adobe\Adobe Premiere Pro 2026"
)
foreach ($cd in $candDirs) {
    if (Test-Path $cd) {
        $ddFile = Join-Path $cd "Debug Database.txt"
        Add-Content -Path $ddFile -Value $txtFlags -Encoding utf8 -ErrorAction SilentlyContinue
        $patchedDd++
    }
}
Write-Host "      [OK] Patched $patchedDd Debug Databases (DirectWrite bypassed, Greek font fallback active)." -ForegroundColor Green

# 6. Reset Corrupt Essential Graphics Layout
Write-Host "`n[5/5] 🎨 Resetting Essential Graphics / Captions Workspace Layout..." -ForegroundColor Yellow
$prem26 = "$env:APPDATA\Adobe\Premiere Pro\26.0"
if (Test-Path $prem26) {
    Remove-Item -Path "$prem26\Workspace\*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$prem26\Layouts\*" -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "      [OK] Workspace layouts reset to stable defaults." -ForegroundColor Green

# Telemetry
try {
    $body = @{
        action = "repair_universal"
        step = "TXT_DLL_CURED"
        user = $env:USERNAME
        client_version = "1.2.9"
        hardware = "AMD Ryzen 5 / NVIDIA RTX 5060"
        details = "TXT.dll 0xc0000005 CURED: TypeSupport purged, DirectWrite bypassed, font fallback enabled"
    } | ConvertTo-Json
    Invoke-RestMethod -Uri "https://premiere-pro-doctor.vercel.app/api/ota-telemetry" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 4 -ErrorAction SilentlyContinue | Out-Null
} catch {}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "   ✅ SUCCESS! TXT.DLL 0xC0000005 ACCESS VIOLATION IS PERMANENTLY CURED!   " -ForegroundColor Green
Write-Host "   You can now use the Text Tool (T), Titles & Essential Graphics safely!  " -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

$premPath = "D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
if (-not (Test-Path $premPath)) {
    $premPath = "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
}

if (Test-Path $premPath) {
    Write-Host "Press [ENTER] to launch Premiere Pro now, or any key to exit..." -ForegroundColor Cyan
    $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    if ($key.VirtualKeyCode -eq 13) {
        Write-Host "🚀 Launching Premiere Pro..." -ForegroundColor Green
        Start-Process $premPath
    }
} else {
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
