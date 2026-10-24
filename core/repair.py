import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class PremiereRepairEngine:
    def __init__(self, logger=None):
        self.logger = logger

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}")

    def kill_lingering_adobe_processes(self) -> int:
        """Terminates hanging Adobe Premiere, GPUSniffer, dynamiclink processes."""
        adobe_procs = [
            "Adobe Premiere Pro", "GPUSniffer", "dynamiclinkmanager",
            "TeamProjectsLocalHub", "dvaaudiofilterscan", "dvaapprelauncher"
        ]
        killed = 0
        for p in adobe_procs:
            try:
                cmd = f"Stop-Process -Name '{p}' -Force -ErrorAction SilentlyContinue"
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
                if res.returncode == 0:
                    killed += 1
            except Exception:
                pass
        self.log(f"Cleaned up background Adobe processes.", "SUCCESS")
        return killed

    def create_ascii_junction(self, non_ascii_dir: str, ascii_target_dir: str = None) -> Dict[str, Any]:
        """
        Creates an NTFS directory junction with a clean ASCII path pointing to the non-ASCII directory.
        Updates shortcuts and GPU registry to use the clean path.
        """
        try:
            non_ascii_dir = os.path.normpath(non_ascii_dir)
            if not os.path.isdir(non_ascii_dir):
                return {"success": False, "error": f"Source directory does not exist: {non_ascii_dir}"}

            drive = os.path.splitdrive(non_ascii_dir)[0]
            if not ascii_target_dir:
                # Dynamically derive a clean ASCII path on the exact drive where the folder is located
                base_name = os.path.basename(non_ascii_dir)
                ascii_clean = "".join(c for c in base_name if ord(c) < 128 and (c.isalnum() or c in "._-")).strip()
                if not ascii_clean:
                    ascii_clean = "AdobePremierePro_Repaired"
                ascii_target_dir = os.path.join(drive, "\\" + ascii_clean)
            ascii_target_dir = os.path.normpath(ascii_target_dir)

            # If junction already exists and points to source, good
            if os.path.exists(ascii_target_dir):
                self.log(f"Target junction path already exists: {ascii_target_dir}", "INFO")
            else:
                self.log(f"Creating clean ASCII NTFS Junction: '{ascii_target_dir}' -> '{non_ascii_dir}'", "INFO")
                # Using cmd mklink /J
                cmd = f'cmd /c mklink /J "{ascii_target_dir}" "{non_ascii_dir}"'
                proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding="utf-8", errors="replace")
                if proc.returncode != 0:
                    # Try powershell New-Item
                    ps_cmd = f'New-Item -ItemType Junction -Path "{ascii_target_dir}" -Target "{non_ascii_dir}"'
                    proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
                    if proc.returncode != 0:
                        return {"success": False, "error": f"Failed to create junction: {proc.stderr}"}

            clean_exe = os.path.join(ascii_target_dir, "Adobe Premiere Pro.exe")
            if os.path.isfile(clean_exe):
                self.log(f"ASCII Junction verified successfully: {clean_exe}", "SUCCESS")
                # Configure High Performance GPU for the new clean path
                self.set_gpu_high_performance(clean_exe)
                # Create/Update Desktop Shortcut
                self.create_desktop_shortcut(clean_exe, "Adobe Premiere Pro (Repaired)")
                return {"success": True, "clean_exe": clean_exe, "junction_dir": ascii_target_dir}
            else:
                return {"success": False, "error": f"Executable not found in junction: {clean_exe}"}

        except Exception as e:
            self.log(f"Exception during junction creation: {e}", "ERROR")
            return {"success": False, "error": str(e)}

    def set_gpu_high_performance(self, exe_path: str) -> bool:
        """Forces High-Performance GPU (NVIDIA RTX) in Windows Graphics Settings registry."""
        try:
            exe_path = os.path.normpath(exe_path)
            key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                # GpuPreference=2; means High Performance (dGPU / NVIDIA)
                winreg.SetValueEx(key, exe_path, 0, winreg.REG_SZ, "GpuPreference=2;")
            self.log(f"Forced High-Performance GPU Preference in Registry for: {exe_path}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to set GPU High-Performance in Registry: {e}", "ERROR")
            return False

    def purge_media_cache(self) -> Dict[str, Any]:
        """Deep purges Adobe Common Media Cache, Peak Files, and Temp files."""
        self.kill_lingering_adobe_processes()

        appdata = os.getenv("APPDATA", "")
        common_dir = os.path.join(appdata, "Adobe", "Common")
        cache_folders = [
            os.path.join(common_dir, "Media Cache Files"),
            os.path.join(common_dir, "Media Cache"),
            os.path.join(common_dir, "Peak Files"),
            os.path.join(common_dir, "Analyzer Cache Files"),
            os.path.join(common_dir, "PTX")
        ]

        deleted_files = 0
        freed_bytes = 0

        for folder in cache_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder, topdown=False):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            freed_bytes += os.path.getsize(fp)
                            os.remove(fp)
                            deleted_files += 1
                        except OSError:
                            pass
                    for d in dirs:
                        dp = os.path.join(root, d)
                        try:
                            os.rmdir(dp)
                        except OSError:
                            pass

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        self.log(f"Purged Media Cache: {deleted_files} files deleted ({freed_mb} MB freed).", "SUCCESS")
        return {"deleted_files": deleted_files, "freed_mb": freed_mb}

    def reset_preferences_and_plugin_cache(self, backup: bool = True) -> Dict[str, Any]:
        """Resets plugin caches (Plugin Loading.log, AudioPluginManager) and creates auto-backup."""
        self.kill_lingering_adobe_processes()

        appdata = os.getenv("APPDATA", "")
        ppro_dir = os.path.join(appdata, "Adobe", "Premiere Pro")
        if not os.path.exists(ppro_dir):
            return {"success": False, "error": "Premiere Pro AppData folder not found."}

        # Backup existing preferences if requested
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(ppro_dir, f"Preferences_Backup_{timestamp}")
            try:
                for item in os.listdir(ppro_dir):
                    if item.startswith("2") or item in ["DVADialogPrefs", "ControlSurface"]:
                        src = os.path.join(ppro_dir, item)
                        dst = os.path.join(backup_dir, item)
                        if os.path.isdir(src):
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                self.log(f"Created automatic Preferences Backup at: {backup_dir}", "SUCCESS")
            except Exception as e:
                self.log(f"Warning during backup creation: {e}", "WARNING")

        # Files to remove to force safe clean startup
        files_to_clean = [
            "Plugin Loading.log",
            "AudioPluginManagerSettings.xml",
            "AudioPlugInsScannedOnFirstLaunch_x64",
            "SCRPriorState.json",
            "Trace Database.txt"
        ]

        cleaned_count = 0
        for root, _, files in os.walk(ppro_dir):
            for f in files:
                if f in files_to_clean:
                    fp = os.path.join(root, f)
                    try:
                        os.remove(fp)
                        cleaned_count += 1
                    except OSError:
                        pass

        self.log(f"Cleaned {cleaned_count} corrupted plugin cache/state files.", "SUCCESS")
        return {"success": True, "cleaned_files": cleaned_count}

    def remove_dead_shortcuts(self) -> int:
        """Removes dead Premiere Pro shortcuts that point to missing paths."""
        search_dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%USERPROFILE%\Desktop")
        ]

        ps_script = """
        $wsh = New-Object -ComObject WScript.Shell
        $removed = 0
        Get-ChildItem -Path @({search_paths}) -Filter "*Premiere*.lnk" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $sc = $wsh.CreateShortcut($_.FullName)
                if ($sc.TargetPath -and (-not (Test-Path -LiteralPath $sc.TargetPath))) {
                    Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
                    $removed++
                }
            } catch {}
        }
        $removed
        """
        paths_str = ", ".join([f'"{d}"' for d in search_dirs if os.path.exists(d)])
        formatted_script = ps_script.replace("{search_paths}", paths_str)

        try:
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", formatted_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
            res = int(proc.stdout.strip() or 0)
            if res > 0:
                self.log(f"Removed {res} broken/dead shortcuts.", "SUCCESS")
            return res
        except Exception as e:
            self.log(f"Error removing dead shortcuts: {e}", "WARNING")
            return 0

    def create_desktop_shortcut(self, target_exe: str, shortcut_name: str = "Adobe Premiere Pro (Repaired)") -> bool:
        """Creates a clean desktop shortcut for the repaired Premiere Pro executable."""
        desktop = os.path.expandvars(r"%USERPROFILE%\Desktop")
        lnk_path = os.path.join(desktop, f"{shortcut_name}.lnk")
        work_dir = os.path.dirname(target_exe)

        ps_script = f"""
        $wsh = New-Object -ComObject WScript.Shell
        $sc = $wsh.CreateShortcut('{lnk_path}')
        $sc.TargetPath = '{target_exe}'
        $sc.WorkingDirectory = '{work_dir}'
        $sc.Description = 'Adobe Premiere Pro (Auto-Repaired by Doctor)'
        $sc.Save()
        """
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
            self.log(f"Created clean Desktop shortcut: '{shortcut_name}.lnk'", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to create desktop shortcut: {e}", "ERROR")
            return False

    def run_complete_auto_fix(self, diagnostics_result: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the complete end-to-end auto-repair suite."""
        self.log("=== STARTING PREMIERE PRO AUTO-REPAIR SUITE ===", "INFO")
        results = {}

        # 1. Kill background processes
        self.kill_lingering_adobe_processes()

        # 2. Check for Non-ASCII installations and create clean ASCII Junction
        repaired_exe = None
        for inst in diagnostics_result.get("installations", []):
            if inst.get("exists"):
                exe_p = inst.get("exe_path")
                if inst.get("has_non_ascii_path"):
                    source_dir = os.path.dirname(exe_p)
                    drive = os.path.splitdrive(exe_p)[0]
                    base_name = os.path.basename(source_dir)
                    ascii_clean = "".join(c for c in base_name if ord(c) < 128 and (c.isalnum() or c in "._-")).strip()
                    if not ascii_clean:
                        ascii_clean = "AdobePremierePro_Repaired"
                    target_junc = os.path.join(drive, "\\" + ascii_clean)
                    junc_res = self.create_ascii_junction(source_dir, target_junc)
                    results["junction"] = junc_res
                    if junc_res.get("success"):
                        repaired_exe = junc_res.get("clean_exe")
                else:
                    repaired_exe = exe_p

        # 3. Force High Performance GPU in Registry
        if repaired_exe:
            self.set_gpu_high_performance(repaired_exe)
        for inst in diagnostics_result.get("installations", []):
            if inst.get("exists") and inst.get("exe_path"):
                self.set_gpu_high_performance(inst.get("exe_path"))
        results["gpu_high_performance"] = True

        # 4. Purge corrupted media cache
        cache_res = self.purge_media_cache()
        results["cache_purge"] = cache_res

        # 5. Reset preferences and plugin cache
        pref_res = self.reset_preferences_and_plugin_cache(backup=True)
        results["prefs_reset"] = pref_res

        # 6. Clean dead shortcuts
        dead_sc_count = self.remove_dead_shortcuts()
        results["removed_dead_shortcuts"] = dead_sc_count

        # 7. Create/Update Desktop Shortcut
        if repaired_exe:
            self.create_desktop_shortcut(repaired_exe, "Adobe Premiere Pro (Repaired)")

        self.log("=== AUTO-REPAIR COMPLETED SUCCESSFULLY! ===", "SUCCESS")
        return results
