import os, sys, subprocess, winreg

def ensure_premiere_launch():
    junction_path = r"F:\AdobePremierePro2026"
    target_non_ascii = r"F:\Νέος φάκελος (2)\Adobe Premiere Pro 2026"
    exe_path = os.path.join(junction_path, "Adobe Premiere Pro.exe")
    raw_exe_path = os.path.join(target_non_ascii, "Adobe Premiere Pro.exe")

    # 1. Verify/Create NTFS Junction if needed
    if not os.path.exists(exe_path) and os.path.exists(raw_exe_path):
        try:
            if not os.path.exists(junction_path):
                subprocess.run(
                    ["cmd.exe", "/c", f'mklink /J "{junction_path}" "{target_non_ascii}"'],
                    capture_output=True,
                    check=False
                )
        except Exception as e:
            pass

    # 2. Enforce DirectX 12/11 High-Performance GPU Affinity (GpuPreference=2)
    try:
        reg_key = r"Software\Microsoft\DirectX\UserGpuPreferences"
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, exe_path, 0, winreg.REG_SZ, "GpuPreference=2;")
            winreg.SetValueEx(key, raw_exe_path, 0, winreg.REG_SZ, "GpuPreference=2;")
    except Exception as e:
        pass

    # 3. Choose the best executable path
    final_exe = exe_path if os.path.exists(exe_path) else raw_exe_path

    if not os.path.exists(final_exe):
        # Fallback search across standard directories
        possible = [
            r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
            r"C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe",
            r"C:\Program Files\Adobe\Adobe Premiere Pro 2024\Adobe Premiere Pro.exe",
            r"D:\AdobePremierePro2026\Adobe Premiere Pro.exe"
        ]
        for p in possible:
            if os.path.exists(p):
                final_exe = p
                break

    if os.path.exists(final_exe):
        # Launch detached as Administrator
        work_dir = os.path.dirname(final_exe)
        subprocess.Popen(
            [final_exe],
            cwd=work_dir,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # Show alert if not found
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Adobe Premiere Pro executable could not be found at {exe_path}.",
            "Adobe Premiere Pro Launcher",
            0x10 | 0x0
        )

if __name__ == "__main__":
    ensure_premiere_launch()
