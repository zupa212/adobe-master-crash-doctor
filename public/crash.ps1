# ============================================================================
# ADOBE PREMIERE PRO 2026 - FORENSIC CRASH AUDIT & CODE CAPTURE
# Engineered by VerticalFlow Systems / Pan.Chorian
# Executed via: irm https://premiere-pro-doctor.vercel.app/crash.ps1 | iex
# ============================================================================

$Host.UI.RawUI.WindowTitle = "Adobe Premiere Pro 2026 - Forensic Crash Reader"
Clear-Host
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "   🔍 ADOBE PREMIERE PRO 2026 - FORENSIC CRASH AUDITOR & CODE CAPTURE       " -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$searchHours = 12
Write-Host "[*] Scanning Windows Event Logs (Application & System, last $searchHours hours)..." -ForegroundColor Gray

$crashEvents = @()
try {
    $crashEvents = Get-WinEvent -FilterHashtable @{
        LogName = 'Application'
        ProviderName = 'Application Error'
        StartTime = (Get-Date).AddHours(-$searchHours)
    } -MaxEvents 30 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'Adobe Premiere Pro' -or $_.Message -match 'GPUSniffer' -or $_.Message -match 'dynamiclinkmanager' }
} catch {}

if (-not $crashEvents) {
    try {
        $crashEvents = Get-WinEvent -FilterHashtable @{
            LogName = 'Application'
            Level = 2
            StartTime = (Get-Date).AddHours(-$searchHours)
        } -MaxEvents 50 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'Adobe' -or $_.Message -match 'Premiere' }
    } catch {}
}

if ($crashEvents -and $crashEvents.Count -gt 0) {
    Write-Host "🚨 FOUND $($crashEvents.Count) RECENT CRASH EVENT(S) IN WINDOWS EVENT VIEWER:`n" -ForegroundColor Red
    
    $latest = $crashEvents[0]
    $msg = $latest.Message
    
    $appMatch = [regex]::Match($msg, "Faulting application name:\s*([^\r\n]+)")
    $modMatch = [regex]::Match($msg, "Faulting module name:\s*([^\r\n]+)")
    $codeMatch = [regex]::Match($msg, "Exception code:\s*([^\r\n]+)")
    $offsetMatch = [regex]::Match($msg, "Fault offset:\s*([^\r\n]+)")

    $app = if ($appMatch.Success) { $appMatch.Groups[1].Value.Trim() } else { "Adobe Premiere Pro.exe" }
    $mod = if ($modMatch.Success) { $modMatch.Groups[1].Value.Trim() } else { "Unknown" }
    $code = if ($codeMatch.Success) { $codeMatch.Groups[1].Value.Trim() } else { "0x0" }
    $offset = if ($offsetMatch.Success) { $offsetMatch.Groups[1].Value.Trim() } else { "0x0" }
    $time = $latest.TimeCreated

    Write-Host "┌────────────────────────────────────────────────────────────────────────┐" -ForegroundColor Red
    Write-Host "│                         EXACT CRASH FORENSICS                          │" -ForegroundColor Yellow
    Write-Host "├────────────────────────────────────────────────────────────────────────┤" -ForegroundColor Red
    Write-Host ("│  Application:     " + $app.PadRight(52) + "│") -ForegroundColor White
    Write-Host ("│  Faulting Module: " + $mod.PadRight(52) + "│") -ForegroundColor Red
    Write-Host ("│  Exception Code:  " + $code.PadRight(52) + "│") -ForegroundColor Red
    Write-Host ("│  Fault Offset:    " + $offset.PadRight(52) + "│") -ForegroundColor Yellow
    Write-Host ("│  Crash Time:      " + $time.ToString().PadRight(52) + "│") -ForegroundColor White
    Write-Host "└────────────────────────────────────────────────────────────────────────┘" -ForegroundColor Red
    Write-Host ""

    # Human Diagnosis
    Write-Host "🔬 DIAGNOSIS FOR FAULTING MODULE [$mod]:" -ForegroundColor Cyan
    switch -Wildcard ($mod.ToLower()) {
        "*runtimeinstaller*" {
            Write-Host "   -> SLStore / SLCache licensing corruption. Run the doctor to purge SLStore." -ForegroundColor Yellow
        }
        "*ovr*" {
            Write-Host "   -> Meta Virtual Monitor / Oculus VR plugin conflict. Disable OVR plugins." -ForegroundColor Yellow
        }
        "*openvr*" {
            Write-Host "   -> SteamVR / OpenVR plugin conflict." -ForegroundColor Yellow
        }
        "*nvoglv64*" {
            Write-Host "   -> NVIDIA OpenGL / GPU Driver crash. Update NVIDIA Studio Driver or purge DXCache." -ForegroundColor Yellow
        }
        "*nvcuda*" {
            Write-Host "   -> NVIDIA CUDA driver timeout / VRAM crash. Increase TdrDelay." -ForegroundColor Yellow
        }
        "*ntdll*" {
            Write-Host "   -> Memory heap allocation error or third-party overlay/plugin corruption." -ForegroundColor Yellow
        }
        "*kernelbase*" {
            Write-Host "   -> Unhandled Windows Exception / Out of Memory or missing VC++ Runtime." -ForegroundColor Yellow
        }
        "*dvacore*" {
            Write-Host "   -> Core Adobe Framework crash. Corrupt project media or workspace cache." -ForegroundColor Yellow
        }
        "*imagerenderer*" {
            Write-Host "   -> GPU Mercury Playback Engine render error. Disable hardware decode for offending clip." -ForegroundColor Yellow
        }
        default {
            Write-Host "   -> Module error: $mod (Code: $code). Details copied to clipboard." -ForegroundColor Yellow
        }
    }
    Write-Host ""

    $clipText = "CRASH REPORT: App=$app | FaultingModule=$mod | ExceptionCode=$code | Offset=$offset | Time=$time"
    try { Set-Clipboard -Value $clipText } catch {}
    Write-Host "📋 Crash details copied to Windows Clipboard automatically! Press Ctrl+V to paste." -ForegroundColor Green

    # Send to cloud
    try {
        $body = @{
            action = "crash_dump"
            step = "MANUAL_AUDIT"
            user = $env:USERNAME
            hardware = (Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join " | "
            details = "Manual Crash Capture: $mod ($code)"
            crash_module = $mod
            exception_code = $code
            fault_offset = $offset
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://premiere-pro-doctor.vercel.app/api/ota-telemetry" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 4 -ErrorAction SilentlyContinue | Out-Null
        Write-Host "📡 Crash telemetry broadcast to https://premiere-pro-doctor.vercel.app" -ForegroundColor Cyan
    } catch {}

} else {
    Write-Host "ℹ️ No Application Crash (Event ID 1000) found in Event Viewer in the last $searchHours hours." -ForegroundColor Yellow
    Write-Host "   Checking Windows Defender Protection History..." -ForegroundColor Gray
    
    $defEvents = @()
    try {
        $defEvents = Get-WinEvent -FilterHashtable @{
            LogName = 'Microsoft-Windows-Windows Defender/Operational'
            Id = 1116, 1117
            StartTime = (Get-Date).AddHours(-$searchHours)
        } -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'Adobe' }
    } catch {}
    
    if ($defEvents) {
        Write-Host "`n🛡️ Windows Defender Terminated an Adobe Component!" -ForegroundColor Red
        Write-Host $defEvents[0].Message -ForegroundColor Yellow
    } else {
        Write-Host "`n💡 No crash dump or Defender block detected." -ForegroundColor Cyan
        Write-Host "   If Premiere closed silently, it was likely an ExitProcess(0) call or out-of-memory kill." -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Press any key to close this auditor..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
