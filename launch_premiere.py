import os, sys, subprocess, winreg, ctypes

def is_ascii(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False

def find_premiere_executable():
    # 1. Check registry App Paths
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Premiere Pro.exe") as key:
            val, _ = winreg.QueryValueEx(key, "")
            if val and os.path.isfile(val):
                return val
    except Exception:
        pass

    # 2. Known local paths and active junctions
    prioritized = [
        r"F:\AdobePremierePro2026\Adobe Premiere Pro.exe",
        r"F:\Νέος φάκελος (2)\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2024\Adobe Premiere Pro.exe",
        r"D:\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"D:\AdobePremierePro2026\Adobe Premiere Pro.exe"
    ]
    for p in prioritized:
        if os.path.isfile(p):
            return p

    # 3. Dynamic scan across all fixed and removable drives
    drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    for drive in drives:
        for root_folder in ["Program Files\\Adobe", "Adobe", ""]:
            target_dir = os.path.join(drive, root_folder) if root_folder else drive
            if os.path.isdir(target_dir):
                try:
                    for root, dirs, files in os.walk(target_dir):
                        if "Adobe Premiere Pro.exe" in files:
                            found = os.path.join(root, "Adobe Premiere Pro.exe")
                            return found
                        # Limit depth to 3 for fast scan
                        rel = os.path.relpath(root, target_dir)
                        if rel.count(os.sep) >= 3:
                            dirs.clear()
                except Exception:
                    continue

    return None

def ensure_repaired_launch():
    exe = find_premiere_executable()
    if not exe or not os.path.isfile(exe):
        ctypes.windll.user32.MessageBoxW(
            0,
            "Could not locate Adobe Premiere Pro installation on any physical drive.\n\nPlease run Adobe Master Crash Doctor to perform a full system scan.",
            "Adobe Premiere Pro (Repaired Launcher)",
            0x10 | 0x0
        )
        return

    final_exe = exe
    exe_dir = os.path.dirname(exe)
    drive = os.path.splitdrive(exe)[0]

    # If the executable path contains non-ASCII characters (e.g. Greek folders)
    if not is_ascii(exe):
        ascii_junction = f"{drive}\\AdobePremierePro2026"
        junction_exe = os.path.join(ascii_junction, "Adobe Premiere Pro.exe")
        
        if not os.path.exists(ascii_junction):
            try:
                subprocess.run(
                    ["cmd.exe", "/c", f'mklink /J "{ascii_junction}" "{exe_dir}"'],
                    capture_output=True,
                    check=False
                )
            except Exception:
                pass

        if os.path.isfile(junction_exe):
            final_exe = junction_exe

    # Enforce DirectX High-Performance GPU Affinity (GpuPreference=2)
    try:
        reg_key = r"Software\Microsoft\DirectX\UserGpuPreferences"
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, final_exe, 0, winreg.REG_SZ, "GpuPreference=2;")
            if final_exe != exe:
                winreg.SetValueEx(key, exe, 0, winreg.REG_SZ, "GpuPreference=2;")
    except Exception:
        pass

    # Enforce Windows GPU TDR Delay Boost (Anti-Freeze: 10 seconds timeout instead of 2 seconds)
    try:
        tdr_key = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, tdr_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "TdrDelay", 0, winreg.REG_DWORD, 10)
            winreg.SetValueEx(key, "TdrDdiDelay", 0, winreg.REG_DWORD, 10)
            winreg.SetValueEx(key, "TdrLevel", 0, winreg.REG_DWORD, 3)
    except Exception:
        pass

    # Quick Anti-Freeze Pre-Flight: Terminate deadlocked background sync & fix audio sleep flag
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Process -Name 'AdobeCollabSync', 'dynamiclinkmanager', 'CEPHtmlEngine' -ErrorAction SilentlyContinue | Stop-Process -Force"],
            capture_output=True,
            timeout=3
        )
    except Exception:
        pass

    try:
        userprof = os.environ.get("USERPROFILE", r"C:\Users\marth")
        for v in ["26.0", "25.0", "24.0"]:
            dd = os.path.join(userprof, rf"AppData\Roaming\Adobe\Premiere Pro\{v}\Debug Database.txt")
            if os.path.isfile(dd):
                with open(dd, "r", encoding="utf-8", errors="replace") as f:
                    txt = f.read()
                if "dvaaudiodevice.AlwaysRunning\ttrue" in txt:
                    txt = txt.replace("dvaaudiodevice.AlwaysRunning\ttrue\ttrue", "dvaaudiodevice.AlwaysRunning\tfalse\tfalse")
                    with open(dd, "w", encoding="utf-8") as f:
                        f.write(txt)
    except Exception:
        pass

    # Launch Premiere Pro in clean detached mode
    work_dir = os.path.dirname(final_exe)
    subprocess.Popen(
        [final_exe],
        cwd=work_dir,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    )

if __name__ == "__main__":
    ensure_repaired_launch()
