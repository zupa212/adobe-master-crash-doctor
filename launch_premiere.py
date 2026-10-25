import os, sys, subprocess, winreg, ctypes, glob

def is_ascii(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False

def get_documents_folders():
    """Returns all candidate Documents folders across standard, OneDrive, and registry paths."""
    candidates = []
    # 1. Windows Shell Registry
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            val, _ = winreg.QueryValueEx(key, "Personal")
            expanded = os.path.expandvars(val)
            if os.path.isdir(expanded) and expanded not in candidates:
                candidates.append(expanded)
    except Exception:
        pass

    userprofile = os.environ.get("USERPROFILE", "")
    if userprofile:
        # 2. Standard Documents
        doc1 = os.path.join(userprofile, "Documents")
        if os.path.isdir(doc1) and doc1 not in candidates:
            candidates.append(doc1)
        # 3. OneDrive Documents
        doc2 = os.path.join(userprofile, "OneDrive", "Documents")
        if os.path.isdir(doc2) and doc2 not in candidates:
            candidates.append(doc2)

    return candidates

def find_premiere_executable():
    # 1. Check registry App Paths first if it points to an existing file
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Premiere Pro.exe") as key:
            val, _ = winreg.QueryValueEx(key, "")
            if val and os.path.isfile(val):
                return val
    except Exception:
        pass

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Premiere Pro.exe") as key:
            val, _ = winreg.QueryValueEx(key, "")
            if val and os.path.isfile(val):
                return val
    except Exception:
        pass

    # 2. Known local paths and active junctions
    prioritized = [
        r"D:\Adobe Suite1\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"D:\Adobe Suite\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"D:\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"D:\AdobePremierePro2026\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2024\Adobe Premiere Pro.exe",
        r"F:\AdobePremierePro2026\Adobe Premiere Pro.exe",
        r"F:\Νέος φάκελος (2)\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
    ]
    for p in prioritized:
        if os.path.isfile(p):
            return p

    # 3. Dynamic scan across all fixed and removable drives
    drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    for drive in drives:
        for root_folder in [
            "Adobe Suite1", "Adobe Suite", "Adobe Suite 2026", "Adobe Suite 2025",
            "Program Files\\Adobe", "Adobe", "Apps\\Adobe", "Master Collection", ""
        ]:
            target_dir = os.path.join(drive, root_folder) if root_folder else drive
            if os.path.isdir(target_dir):
                try:
                    for root, dirs, files in os.walk(target_dir):
                        if "Adobe Premiere Pro.exe" in files:
                            found = os.path.join(root, "Adobe Premiere Pro.exe")
                            return found
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

    work_dir = os.path.dirname(final_exe)

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

    # Inject Anti-Deadlock Debug Database Flags into AppData and Application Directory
    try:
        userprof = os.environ.get("USERPROFILE", "")
        dd_targets = [
            os.path.join(work_dir, "Debug Database.txt")
        ]
        if userprof:
            prem_appdata = os.path.join(userprof, r"AppData\Roaming\Adobe\Premiere Pro")
            if os.path.isdir(prem_appdata):
                for item in os.listdir(prem_appdata):
                    v_p = os.path.join(prem_appdata, item)
                    if os.path.isdir(v_p) and "backup" not in item.lower():
                        dd_targets.append(os.path.join(v_p, "Debug Database.txt"))
                dd_targets.append(os.path.join(prem_appdata, "Logs", "Debug Database.txt"))

        flags_to_enforce = {
            "dvaaudiodevice.AlwaysRunning": ("false", "false"),
            "AudioOutputOnlyUI": ("true", "true"),
            "dvaaudiodevice.EnableRealtimeBlockingAccessFromIOThread": ("false", "false"),
            "TeamProjects.DisableBackgroundSync": ("true", "true"),
            "MF.EnableDirectoryPolling": ("false", "false"),
            "EA.MediaFinder.EnableSyncDirectoryScanForFastMediaSearch": ("false", "false"),
            "EA.Config.DisableSequenceLocking": ("true", "true"),
            "FE.AudioPluginScanOnFirstLaunch": ("false", "false"),
            "ExporterMPEG4.Feature.Allow_Intel_HW_Export": ("false", "false"),
            "ExporterMPEG4.Feature.Allow_Nvidia_HW_Export": ("true", "true"),
            "Player.DirectXAcceleratedRenderer": ("true", "true")
        }
        for dd in dd_targets:
            try:
                os.makedirs(os.path.dirname(dd), exist_ok=True)
                lines = []
                if os.path.isfile(dd):
                    with open(dd, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                updated = {}
                for l in lines:
                    p = l.strip().split("\t")
                    if len(p) >= 3:
                        updated[p[0]] = (p[1], p[2])
                for k, v in flags_to_enforce.items():
                    updated[k] = v
                with open(dd, "w", encoding="utf-8") as f:
                    for k, (v1, v2) in sorted(updated.items()):
                        f.write(f"{k}\t{v1}\t{v2}\n")
            except Exception:
                pass

        # Ensure Prefs file has Sensei AI & MISO disabled across ALL user profiles
        doc_dirs = get_documents_folders()
        for ddir in doc_dirs:
            prem_doc_root = os.path.join(ddir, r"Adobe\Premiere Pro")
            if os.path.isdir(prem_doc_root):
                for root, _, files in os.walk(prem_doc_root):
                    if "backup" in root.lower():
                        continue
                    if "Adobe Premiere Pro Prefs" in files:
                        pfile = os.path.join(root, "Adobe Premiere Pro Prefs")
                        try:
                            with open(pfile, "r", encoding="utf-8", errors="replace") as pf:
                                ptxt = pf.read()
                            ptxt = ptxt.replace("<BE.Prefs.General.AutoAudioCategorizationDuringImport>true<", "<BE.Prefs.General.AutoAudioCategorizationDuringImport>false<")
                            ptxt = ptxt.replace("<BE.Prefs.MediaIntelligence.AnalyzeImportedMediaForMISO>true<", "<BE.Prefs.MediaIntelligence.AnalyzeImportedMediaForMISO>false<")
                            ptxt = ptxt.replace("<BE.Prefs.MediaIntelligence.AnalyzeImportedMediaCacheLocation>1<", "<BE.Prefs.MediaIntelligence.AnalyzeImportedMediaCacheLocation>0<")
                            ptxt = ptxt.replace("<BE.Prefs.AutoSave.Interval>5<", "<BE.Prefs.AutoSave.Interval>15<")
                            ptxt = ptxt.replace("<Project.Prefs.EnableIntelDecode>true<", "<Project.Prefs.EnableIntelDecode>false<")
                            ptxt = ptxt.replace("<Project.Prefs.EnablehAMDDecode>true<", "<Project.Prefs.EnablehAMDDecode>false<")
                            ptxt = ptxt.replace("<Project.Prefs.EnableNvidiaDecode>false<", "<Project.Prefs.EnableNvidiaDecode>true<")
                            with open(pfile, "w", encoding="utf-8") as pf:
                                pf.write(ptxt)
                        except Exception:
                            pass
    except Exception:
        pass

    # 1. Deploy Microsoft Visual C++ 2015-2022 runtimes into app folder if missing
    try:
        sys32 = os.path.expandvars(r"%WINDIR%\System32")
        for dll in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]:
            src_dll = os.path.join(sys32, dll)
            dst_dll = os.path.join(work_dir, dll)
            if os.path.isfile(src_dll) and not os.path.isfile(dst_dll):
                try:
                    import shutil
                    shutil.copy2(src_dll, dst_dll)
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Grant Full Control NTFS permissions on working directory
    try:
        subprocess.run(
            f'icacls "{work_dir}" /grant Everyone:(OI)(CI)F Administrators:(OI)(CI)F Users:(OI)(CI)F /T /C /Q',
            shell=True,
            capture_output=True,
            timeout=3
        )
    except Exception:
        pass

    # 3. Purge corrupt licensing databases (SLStore/SLCache/OOBE) that cause RuntimeInstaller.dll 0xc0000005
    try:
        lic_paths = [
            os.path.expandvars(r"%PROGRAMDATA%\Adobe\SLStore"),
            os.path.expandvars(r"%COMMONPROGRAMFILES(x86)%\Adobe\SLCache"),
            os.path.expandvars(r"%LOCALAPPDATA%\Adobe\OOBE")
        ]
        for lp in lic_paths:
            if os.path.isdir(lp):
                for root, _, files in os.walk(lp):
                    for f in files:
                        try:
                            os.remove(os.path.join(root, f))
                        except Exception:
                            pass
    except Exception:
        pass

    # Ensure missing plugin directory exists
    try:
        os.makedirs(os.path.join(work_dir, r"Plug-ins\Common"), exist_ok=True)
    except Exception:
        pass

    # Fix HKCU & HKLM App Paths and Premiere Pro registry keys to final executable
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Premiere Pro.exe", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, final_exe)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, work_dir + "\\")
    except Exception:
        pass

    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Adobe\Premiere Pro\26.0", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "SequencePresetsPath", 0, winreg.REG_SZ, os.path.join(work_dir, r"Settings\SequencePresets"))
            winreg.SetValueEx(key, "SequencePreviewPresetsPath", 0, winreg.REG_SZ, os.path.join(work_dir, r"Settings\EncoderPresets\SequencePreview"))
            winreg.SetValueEx(key, "PluginInstallPath", 0, winreg.REG_SZ, os.path.join(work_dir, r"Plug-ins\Common"))
            winreg.SetValueEx(key, "RecoveryOpenProjectInfos", 0, winreg.REG_SZ, "")
    except Exception:
        pass

    try:
        app_path_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Premiere Pro.exe"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, app_path_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, final_exe)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, work_dir + "\\")
    except Exception:
        pass

    try:
        prem_key = r"SOFTWARE\Adobe\Premiere Pro\26.0"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, prem_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "SequencePresetsPath", 0, winreg.REG_SZ, os.path.join(work_dir, r"Settings\SequencePresets"))
            winreg.SetValueEx(key, "SequencePreviewPresetsPath", 0, winreg.REG_SZ, os.path.join(work_dir, r"Settings\EncoderPresets\SequencePreview"))
            winreg.SetValueEx(key, "PluginInstallPath", 0, winreg.REG_SZ, os.path.join(work_dir, r"Plug-ins\Common"))
    except Exception:
        pass

    # Fix Start Menu and Desktop shortcuts to point to final executable
    try:
        ps_fix_sc = f"""
        $wsh = New-Object -ComObject WScript.Shell
        $scPaths = @(
            'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Adobe Premiere Pro 2026.lnk',
            "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Adobe Premiere Pro 2026.lnk",
            "$env:USERPROFILE\\Desktop\\Adobe Premiere Pro (Repaired).lnk"
        )
        foreach ($scPath in $scPaths) {{
            try {{
                $sc = $wsh.CreateShortcut($scPath)
                $sc.TargetPath = '{final_exe}'
                $sc.WorkingDirectory = '{work_dir}'
                $sc.Save()
            }} catch {{}}
        }}
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_fix_sc], capture_output=True, timeout=3)
    except Exception:
        pass

    # Launch Premiere Pro in clean detached mode
    subprocess.Popen(
        [final_exe],
        cwd=work_dir,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    )

if __name__ == "__main__":
    ensure_repaired_launch()
