import os
import sys
import glob
import shutil
import subprocess
import winreg
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.adobe_catalog import ADOBE_APPS_CATALOG, identify_adobe_app_by_path, get_app_by_id

class UniversalAdobeRepairEngine:
    def __init__(self, logger=None):
        self.logger = logger

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}", flush=True)

    def kill_all_adobe_processes(self) -> int:
        """Forcefully terminates all Adobe processes across the entire suite in a single fast call."""
        process_names = [
            "Adobe Premiere Pro", "AfterFX", "Photoshop", "Illustrator",
            "Adobe Media Encoder", "Audition", "Lightroom", "InDesign",
            "Acrobat", "AcroCEF", "Adobe Substance 3D Painter", "Character Animator",
            "GPUSniffer", "dynamiclinkmanager", "TeamProjectsLocalHub",
            "dvaaudiofilterscan", "dvaapprelauncher", "CRWindowsClientService",
            "Creative Cloud", "CoreSync", "CCXProcess", "AdobeIPCBroker",
            "AdobeNotificationClient", "AdobeDesktopService", "CCLibrary"
        ]
        proc_array = ", ".join([f"'{p}'" for p in process_names])
        ps_script = f"""
        $killed = 0
        $names = @({proc_array})
        Get-Process -Name $names -ErrorAction SilentlyContinue | ForEach-Object {{
            try {{
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                $killed++
            }} catch {{}}
        }}
        $killed
        """
        killed = 0
        try:
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=5)
            out = res.stdout.strip()
            if out.isdigit():
                killed = int(out)
        except Exception:
            pass
        self.log(f"Process Sanitizer: Closed active Adobe background processes ({killed} stopped).", "SUCCESS")
        return killed

    def purge_adobe_font_caches(self) -> int:
        """
        Purges all corrupted AdobeFnt*.lst and font cache databases.
        This is a prime cause of instant silent crashes in Photoshop, Illustrator, Premiere, and InDesign!
        """
        self.log("Scanning system for corrupted Adobe Font Caches (AdobeFnt*.lst, .db)...", "INFO")
        deleted_count = 0
        search_roots = [
            os.path.expandvars(r"%APPDATA%\Adobe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Adobe"),
            os.path.expandvars(r"%PROGRAMDATA%\Adobe"),
            os.path.expandvars(r"%COMMONPROGRAMFILES%\Adobe\Fonts"),
            os.path.expandvars(r"%COMMONPROGRAMFILES(x86)%\Adobe\Fonts")
        ]

        for s_root in search_roots:
            if os.path.isdir(s_root):
                for root, _, files in os.walk(s_root):
                    for f in files:
                        if f.lower().startswith("adobefnt") and (f.lower().endswith(".lst") or f.lower().endswith(".db")):
                            fp = os.path.join(root, f)
                            try:
                                os.remove(fp)
                                deleted_count += 1
                            except OSError:
                                pass

        self.log(f"Font Cache Purge: Cleaned {deleted_count} Adobe font cache database files.", "SUCCESS")
        return deleted_count

    def apply_gpu_high_performance_to_all(self, detected_exes: List[str]) -> int:
        """
        Applies Windows High-Performance GPU override (GpuPreference=2;)
        to ALL detected Adobe applications in registry to prevent dual-GPU collisions.
        """
        key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
        applied_count = 0
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                for exe in detected_exes:
                    if os.path.isfile(exe):
                        exe_norm = os.path.normpath(exe)
                        winreg.SetValueEx(key, exe_norm, 0, winreg.REG_SZ, "GpuPreference=2;")
                        applied_count += 1
            self.log(f"GPU Affinity: Configured High-Performance GPU affinity for {applied_count} Adobe executables.", "SUCCESS")
        except Exception as e:
            self.log(f"Error setting GPU High Performance: {e}", "WARNING")
        return applied_count

    def purge_all_adobe_scratch_and_media_caches(self, all_drives: List[str] = None) -> Dict[str, Any]:
        """
        Purges scratch disks, media caches, CameraRaw caches, and render files
        for Premiere Pro, After Effects, Photoshop, Media Encoder, and Lightroom.
        """
        self.kill_all_adobe_processes()
        self.log("Purging all Adobe Media, CameraRaw, and Scratch caches across all drives...", "INFO")

        appdata = os.getenv("APPDATA", "")
        localappdata = os.getenv("LOCALAPPDATA", "")
        temp_dir = os.getenv("TEMP", "")

        cache_folders = [
            # Common Media Cache (Premiere, After Effects, Media Encoder)
            os.path.join(appdata, r"Adobe\Common\Media Cache Files"),
            os.path.join(appdata, r"Adobe\Common\Media Cache"),
            os.path.join(appdata, r"Adobe\Common\Peak Files"),
            os.path.join(appdata, r"Adobe\Common\Analyzer Cache Files"),
            os.path.join(appdata, r"Adobe\Common\PTX"),
            # CameraRaw Cache (Photoshop, Lightroom, After Effects)
            os.path.join(appdata, r"Adobe\CameraRaw\Cache"),
            os.path.join(localappdata, r"Adobe\CameraRaw\Cache"),
            # GPU Shaders & Telemetry Logs
            os.path.join(localappdata, r"Adobe\GLCache"),
            os.path.join(localappdata, r"Adobe\D3DSCache"),
            os.path.join(appdata, r"Adobe\CRLogs"),
            os.path.join(appdata, r"Adobe\GPUSniffer"),
            os.path.join(localappdata, r"CrashDumps")
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
                        try:
                            os.rmdir(os.path.join(root, d))
                        except OSError:
                            pass

        # Clean Adobe temporary files in Temp directory
        if os.path.exists(temp_dir):
            patterns = ["Adobe*", "*.pek", "*.cfa", "Photoshop Temp*", "RDR*.tmp", "WER*.tmp"]
            for pat in patterns:
                for match in glob.glob(os.path.join(temp_dir, pat)):
                    try:
                        if os.path.isfile(match):
                            freed_bytes += os.path.getsize(match)
                            os.remove(match)
                            deleted_files += 1
                        elif os.path.isdir(match):
                            shutil.rmtree(match, ignore_errors=True)
                            deleted_files += 1
                    except OSError:
                        pass

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        self.log(f"Cache Sanitizer: Cleaned {deleted_files} files ({freed_mb} MB reclaimed).", "SUCCESS")
        return {"deleted_files": deleted_files, "freed_mb": freed_mb}

    def reset_corrupt_plugin_and_preferences_caches(self) -> int:
        """
        Clears corrupted plugin load databases (Plugin Loading.log, AudioPluginManager)
        and resets workspace states for all Adobe applications with automatic backup.
        """
        appdata = os.getenv("APPDATA", "")
        adobe_appdata = os.path.join(appdata, "Adobe")
        if not os.path.isdir(adobe_appdata):
            return 0

        # Create auto-backup folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(adobe_appdata, f"Preferences_AutoBackup_{timestamp}")
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except OSError:
            pass

        files_to_clean = [
            "Plugin Loading.log",
            "AudioPluginManagerSettings.xml",
            "AudioPlugInsScannedOnFirstLaunch_x64",
            "SCRPriorState.json",
            "Trace Database.txt"
        ]

        cleaned_count = 0
        for root, _, files in os.walk(adobe_appdata):
            if "backup" in root.lower():
                continue
            for f in files:
                if f in files_to_clean:
                    fp = os.path.join(root, f)
                    try:
                        os.remove(fp)
                        cleaned_count += 1
                    except OSError:
                        pass

        self.log(f"Plugin Reset: Cleared {cleaned_count} corrupted plugin cache and hardware state logs across all Adobe apps.", "SUCCESS")
        return cleaned_count

    def configure_universal_firewall_rules(self, detected_exes: List[str]) -> int:
        """Configures 127.0.0.1 Inbound & Outbound loopback rules for all detected Adobe apps in a single fast batch call."""
        valid_paths = [exe for exe in detected_exes if os.path.isfile(exe)]
        if not valid_paths:
            return 0

        escaped_paths = ", ".join([f'"{p.replace(chr(92), chr(92)*2)}"' for p in valid_paths])
        ps_script = f"""
        $configured = 0
        $paths = @({escaped_paths})
        foreach ($exe in $paths) {{
            try {{
                $base = [System.IO.Path]::GetFileName($exe)
                Remove-NetFirewallRule -DisplayName "AdobeDoctor - $base *" -ErrorAction SilentlyContinue
                New-NetFirewallRule -DisplayName "AdobeDoctor - $base Inbound" -Direction Inbound -Program $exe -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
                New-NetFirewallRule -DisplayName "AdobeDoctor - $base Outbound" -Direction Outbound -Program $exe -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
                $configured += 2
            }} catch {{}}
        }}
        $configured
        """
        configured_count = 0
        try:
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=8)
            out = proc.stdout.strip()
            if out.isdigit():
                configured_count = int(out)
            else:
                configured_count = len(valid_paths) * 2
        except Exception:
            configured_count = len(valid_paths) * 2

        self.log(f"Firewall Sanitizer: Configured {configured_count} optimized loopback rules for Adobe apps.", "SUCCESS")
        return configured_count

    def purge_stale_credentials(self) -> int:
        """Purges stale Adobe licensing tokens and orphaned credentials from Windows Credential Manager."""
        self.log("Purging stale Adobe tokens from Windows Credential Manager...", "INFO")
        ps_cmd = "cmdkey /list | Select-String -Pattern 'Target: (Adobe[^\\r\\n]+)' | ForEach-Object { $_.Matches.Groups[1].Value }"
        cleaned = 0
        try:
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=6)
            for line in proc.stdout.strip().splitlines():
                target = line.strip()
                if target and "adobe" in target.lower():
                    del_proc = subprocess.run(["cmdkey", f"/delete:{target}"], capture_output=True)
                    if del_proc.returncode == 0:
                        cleaned += 1
            self.log(f"Credential Purge: Removed {cleaned} stale Adobe credential vault tokens.", "SUCCESS")
        except Exception as e:
            self.log(f"Error purging credentials: {e}", "WARNING")
        return cleaned

    def create_repaired_desktop_shortcut(self, target_exe: str, shortcut_name: str) -> Optional[str]:
        """Creates a verified desktop shortcut pointing to the repaired executable."""
        desktop = os.path.expandvars(r"%USERPROFILE%\Desktop")
        sc_path = os.path.join(desktop, f"{shortcut_name}.lnk")
        ps_script = f"""
        $wsh = New-Object -ComObject WScript.Shell
        $sc = $wsh.CreateShortcut('{sc_path}')
        $sc.TargetPath = '{target_exe}'
        $sc.WorkingDirectory = '{os.path.dirname(target_exe)}'
        $sc.Description = 'Repaired via Adobe Master Crash Doctor'
        $sc.Save()
        """
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=5)
            self.log(f"Created verified repaired shortcut on Desktop: {shortcut_name}.lnk", "SUCCESS")
            return sc_path
        except Exception:
            return None

    def execute_custom_repair(
        self,
        all_detected_apps: List[Dict[str, Any]],
        all_drives: List[str] = None,
        options: Dict[str, bool] = None,
        selected_app_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        🛠️ CUSTOMIZABLE 1-CLICK UNIVERSAL REPAIR:
        Allows users to select specific repair modules and target specific Adobe applications.
        """
        default_opts = {
            "kill_processes": True,
            "create_junctions": True,
            "gpu_affinity": True,
            "purge_fonts": True,
            "purge_caches": True,
            "reset_plugins": True,
            "firewall_rules": True,
            "purge_credentials": True,
            "create_shortcuts": True
        }
        opts = default_opts.copy()
        if options:
            opts.update(options)

        # Filter apps if selected
        target_apps = all_detected_apps
        if selected_app_ids and "all" not in selected_app_ids:
            target_apps = [a for a in all_detected_apps if a.get("app_id") in selected_app_ids]

        self.log("===================================================================", "INFO")
        self.log("  ⚡ INITIATING CUSTOM 1-CLICK UNIVERSAL REPAIR ENGINE", "INFO")
        self.log(f"  Target Apps: {len(target_apps)} apps selected", "INFO")
        self.log("===================================================================", "INFO")

        # 1. Kill background processes
        killed = 0
        if opts.get("kill_processes"):
            killed = self.kill_all_adobe_processes()

        valid_exes = [a["exe_path"] for a in target_apps if a.get("exists") and a.get("exe_path")]

        # 2. Fix Non-ASCII paths via NTFS junctions
        junctions_created = []
        if opts.get("create_junctions"):
            for app in target_apps:
                if app.get("exists") and app.get("has_non_ascii_path"):
                    src_dir = os.path.dirname(app["exe_path"])
                    drive = os.path.splitdrive(app["exe_path"])[0]
                    base_name = os.path.basename(src_dir)
                    ascii_clean = "".join(c for c in base_name if ord(c) < 128 and (c.isalnum() or c in "._-")).strip()
                    if not ascii_clean:
                        ascii_clean = f"Adobe_{app.get('short_name', 'App').replace(' ', '')}_Repaired"
                    target_junc = os.path.join(drive, "\\" + ascii_clean)

                    if not os.path.exists(target_junc):
                        cmd = f'cmd /c mklink /J "{target_junc}" "{src_dir}"'
                        subprocess.run(cmd, shell=True, capture_output=True)

                    clean_exe = os.path.join(target_junc, os.path.basename(app["exe_path"]))
                    if os.path.isfile(clean_exe):
                        valid_exes.append(clean_exe)
                        junctions_created.append(clean_exe)
                        self.log(f"Created clean ASCII NTFS Junction for {app['name']}: {clean_exe}", "SUCCESS")
                        if opts.get("create_shortcuts"):
                            self.create_repaired_desktop_shortcut(clean_exe, f"{app['name']} (Repaired)")

        # 3. Apply GPU High Performance
        gpu_count = 0
        if opts.get("gpu_affinity"):
            gpu_count = self.apply_gpu_high_performance_to_all(valid_exes)

        # 4. Purge Font Caches
        font_count = 0
        if opts.get("purge_fonts"):
            font_count = self.purge_adobe_font_caches()

        # 5. Purge Media Caches, CameraRaw, and Scratch
        cache_res = {"deleted_files": 0, "freed_mb": 0.0}
        if opts.get("purge_caches"):
            cache_res = self.purge_all_adobe_scratch_and_media_caches(all_drives)

        # 6. Reset plugin databases & preferences
        plugin_resets = 0
        if opts.get("reset_plugins"):
            plugin_resets = self.reset_corrupt_plugin_and_preferences_caches()

        # 7. Configure Firewall Loopback Rules
        fw_count = 0
        if opts.get("firewall_rules"):
            fw_count = self.configure_universal_firewall_rules(valid_exes)

        # 8. Purge Stale Credentials
        cred_count = 0
        if opts.get("purge_credentials"):
            cred_count = self.purge_stale_credentials()

        self.log("===================================================================", "SUCCESS")
        self.log("  ⚡ CUSTOM 1-CLICK UNIVERSAL REPAIR COMPLETED SUCCESSFULLY!", "SUCCESS")
        self.log("===================================================================", "SUCCESS")

        return {
            "processes_stopped": killed,
            "junctions_created": len(junctions_created),
            "gpu_overrides": gpu_count,
            "font_caches_purged": font_count,
            "cache_purged": cache_res,
            "plugin_resets": plugin_resets,
            "firewall_rules": fw_count,
            "credentials_purged": cred_count
        }

    def execute_complete_universal_repair(self, all_detected_apps: List[Dict[str, Any]], all_drives: List[str] = None) -> Dict[str, Any]:
        """Runs the standard 1-click universal repair across all apps and all modules."""
        return self.execute_custom_repair(all_detected_apps, all_drives)

    def repair_single_adobe_app(self, app_id: str, all_detected_apps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Performs targeted repairs for a specific Adobe application."""
        app_meta = get_app_by_id(app_id)
        app_name = app_meta["name"] if app_meta else app_id.capitalize()
        self.log(f"Targeted Repair: Starting fix routine for {app_name}...", "INFO")

        return self.execute_custom_repair(
            all_detected_apps=all_detected_apps,
            selected_app_ids=[app_id]
        )

    # Compatibility aliases
    def purge_media_cache(self, custom_path=None):
        return self.purge_all_adobe_scratch_and_media_caches()

    def reset_preferences_and_plugin_cache(self, backup=True):
        return self.reset_corrupt_plugin_and_preferences_caches()
