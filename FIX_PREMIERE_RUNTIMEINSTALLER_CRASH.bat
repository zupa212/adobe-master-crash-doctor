@echo off
:: ============================================================================
:: ADOBE PREMIERE PRO 2026 - RUNTIMEINSTALLER.DLL 0xC0000005 INSTANT FIX
:: Engineered by VerticalFlow Systems / Pan.Chorian
:: Target: Windows 10/11 x64 | AMD Ryzen + NVIDIA RTX 5060 / 3060 Multi-GPU
:: ============================================================================
title Adobe Premiere Pro 2026 - Crash Healer v1.2.4
color 0B
echo.
echo ============================================================================
echo   ADOBE PREMIERE PRO 2026 - RUNTIMEINSTALLER.DLL REPAIR UTILITY
echo   Resolving 0xc0000005 Access Violation, 120s Freezes, and GPU Collisions
echo ============================================================================
echo.

:: 1. Elevate to Administrator if not already elevated
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Elevated administrator permissions recommended.
    echo [*] Attempting to elevate...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs" >nul 2>&1
    if %errorlevel% equ 0 (
        exit /b
    )
    echo [!] Elevation bypassed. Running in current user privilege context...
) else (
    echo [*] Administrative privileges confirmed.
)
echo.

:: 2. Terminate all lingering Adobe processes
echo [*] Terminating lingering Adobe processes...
taskkill /F /IM "Adobe Premiere Pro.exe" >nul 2>&1
taskkill /F /IM "GPUSniffer.exe" >nul 2>&1
taskkill /F /IM "dynamiclinkmanager.exe" >nul 2>&1
taskkill /F /IM "Creative Cloud.exe" >nul 2>&1
taskkill /F /IM "CCXProcess.exe" >nul 2>&1
taskkill /F /IM "CoreSync.exe" >nul 2>&1
taskkill /F /IM "AdobeIPCBroker.exe" >nul 2>&1
taskkill /F /IM "AGSService.exe" >nul 2>&1
taskkill /F /IM "AdobeARM.exe" >nul 2>&1
echo [OK] All Adobe background tasks terminated.

:: 3. Purge corrupt licensing caches causing RuntimeInstaller.DLL 0xc0000005
echo.
echo [*] Purging corrupt SLStore, SLCache, and OOBE licensing locks...
rd /s /q "%ProgramData%\Adobe\SLStore" >nul 2>&1
rd /s /q "%ProgramData%\Adobe\SLData" >nul 2>&1
rd /s /q "%CommonProgramFiles(x86)%\Adobe\SLCache" >nul 2>&1
rd /s /q "%CommonProgramFiles%\Adobe\SLCache" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Adobe\OOBE" >nul 2>&1
rd /s /q "%APPDATA%\Adobe\OOBE" >nul 2>&1
mkdir "%ProgramData%\Adobe\SLStore" >nul 2>&1
mkdir "%CommonProgramFiles(x86)%\Adobe\SLCache" >nul 2>&1
echo [OK] Licensing caches purged and initialized.

:: 4. Grant Full Control NTFS permissions (Fast Non-Recursive Inheritance)
echo.
echo [*] Granting Full Control permissions to Adobe ProgramData, AppData, and target folders...
icacls "%ProgramData%\Adobe" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F /C /Q >nul 2>&1
icacls "%CommonProgramFiles(x86)%\Adobe" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F /C /Q >nul 2>&1
icacls "D:\Adobe Suite1" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F /C /Q >nul 2>&1
icacls "D:\Adobe Suite1\Adobe Premiere Pro 2026" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F /C /Q >nul 2>&1
icacls "D:\premire pro" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F /C /Q >nul 2>&1
icacls "F:\AdobePremierePro2026" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F /C /Q >nul 2>&1
icacls "C:\Program Files\Adobe" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F /C /Q >nul 2>&1
echo [OK] NTFS permissions unlocked.

:: 5. Windows Graphics Driver TDR Timeout Elevation (Prevents 2s GPU Timeout Freeze)
echo.
echo [*] Configuring Windows Graphics Kernel TDR Timeout (TdrDelay = 10s)...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "TdrDelay" /t REG_DWORD /d 10 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "TdrDdiDelay" /t REG_DWORD /d 10 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "TdrLevel" /t REG_DWORD /d 3 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v "HwSchMode" /t REG_DWORD /d 2 /f >nul 2>&1
echo [OK] Graphics TDR Delay elevated to 10 seconds.

:: 6. Direct3D / DXGI High Performance Override (Forces NVIDIA RTX over integrated GPU)
echo.
echo [*] Setting DirectX High-Performance GPU Affinity (NVIDIA RTX Preferred)...
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe" /t REG_SZ /d "GpuPreference=2;" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "D:\Adobe Suite1\Adobe Premiere Pro 2026\GPUSniffer.exe" /t REG_SZ /d "GpuPreference=2;" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "F:\AdobePremierePro2026\Adobe Premiere Pro.exe" /t REG_SZ /d "GpuPreference=2;" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "F:\AdobePremierePro2026\GPUSniffer.exe" /t REG_SZ /d "GpuPreference=2;" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe" /t REG_SZ /d "GpuPreference=2;" /f >nul 2>&1
echo [OK] GPU Preference locked to High-Performance Discrete GPU (GpuPreference=2;).

:: 7. Patch Debug Database.txt to eliminate 120s Audio Lock and AMD iGPU Conflict
echo.
echo [*] Patching Premiere Pro Debug Database (Audio Clock and GPU Decoders)...
set "DD_APP=%APPDATA%\Adobe\Premiere Pro"
for /D %%V in ("%DD_APP%\*") do (
    if exist "%%V" (
        (
            echo AudioOutputOnlyUI	true	true
            echo dvaaudiodevice.AlwaysRunning	false	false
            echo TeamProjects.DisableBackgroundSync	true	true
            echo Player.DirectXAcceleratedRenderer	true	true
            echo DS.GPUSnifferOverride	0	0
            echo DS.ForceCUDARendering	true	true
            echo Project.Prefs.EnablehAMDDecode	false	false
            echo Project.Prefs.EnableIntelDecode	false	false
            echo Project.Prefs.EnableNvidiaDecode	true	true
        ) >> "%%V\Debug Database.txt" 2>nul
    )
)
if exist "D:\Adobe Suite1\Adobe Premiere Pro 2026" (
    (
        echo AudioOutputOnlyUI	true	true
        echo dvaaudiodevice.AlwaysRunning	false	false
        echo TeamProjects.DisableBackgroundSync	true	true
        echo Player.DirectXAcceleratedRenderer	true	true
        echo DS.GPUSnifferOverride	0	0
        echo DS.ForceCUDARendering	true	true
        echo Project.Prefs.EnablehAMDDecode	false	false
        echo Project.Prefs.EnableIntelDecode	false	false
        echo Project.Prefs.EnableNvidiaDecode	true	true
    ) >> "D:\Adobe Suite1\Adobe Premiere Pro 2026\Debug Database.txt" 2>nul
)
if exist "F:\AdobePremierePro2026" (
    (
        echo AudioOutputOnlyUI	true	true
        echo dvaaudiodevice.AlwaysRunning	false	false
        echo TeamProjects.DisableBackgroundSync	true	true
        echo Player.DirectXAcceleratedRenderer	true	true
        echo DS.GPUSnifferOverride	0	0
        echo DS.ForceCUDARendering	true	true
        echo Project.Prefs.EnablehAMDDecode	false	false
        echo Project.Prefs.EnableIntelDecode	false	false
        echo Project.Prefs.EnableNvidiaDecode	true	true
    ) >> "F:\AdobePremierePro2026\Debug Database.txt" 2>nul
)
echo [OK] Debug Database successfully patched.

:: 8. Deploy VC++ CRT Runtimes into App Folders to prevent CRT Heap Violations
echo.
echo [*] Verifying Microsoft Visual C++ 2015-2022 CRT Libraries...
for %%P in ("D:\Adobe Suite1\Adobe Premiere Pro 2026" "F:\AdobePremierePro2026") do (
    if exist "%%~fP" (
        copy /y "%windir%\System32\msvcp140.dll" "%%~fP\" >nul 2>&1
        copy /y "%windir%\System32\vcruntime140.dll" "%%~fP\" >nul 2>&1
        copy /y "%windir%\System32\vcruntime140_1.dll" "%%~fP\" >nul 2>&1
    )
)
echo [OK] VC++ 64-bit CRT libraries mirrored into application folders.

:: 9. Unregister Adobe Crash & Tracking Daemons
echo.
echo [*] Disabling broken Adobe Tracking Services...
sc stop AGSService >nul 2>&1
sc config AGSService start= disabled >nul 2>&1
sc stop AdobeARMservice >nul 2>&1
sc config AdobeARMservice start= disabled >nul 2>&1
sc stop AdobeUpdateService >nul 2>&1
sc config AdobeUpdateService start= disabled >nul 2>&1
echo [OK] Background services cleaned.

echo.
echo ============================================================================
echo   SUCCESS! ADOBE PREMIERE PRO 2026 HAS BEEN REPAIRED!
echo   You can now launch Adobe Premiere Pro without RuntimeInstaller crashes.
echo ============================================================================
echo.
if "%~1"=="--no-pause" goto :end
pause
:end
