import os
import sys
import glob
import subprocess
import winreg
from pathlib import Path
from typing import Dict, List, Any, Optional
from core.disk_scanner import MultiDiskScanner
from core.system_inspector import SystemInspector
from core.adobe_catalog import ADOBE_APPS_CATALOG, identify_adobe_app_by_path, get_all_target_exe_names

class AdobeDiagnostics:
    def __init__(self, logger=None):
        self.logger = logger
        self.disk_scanner = MultiDiskScanner(self.logger)
        self.inspector = SystemInspector(self.logger)

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)

    def is_ascii(self, text: str) -> bool:
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def get_start_menu_shortcuts(self) -> List[Dict[str, Any]]:
        """Parses Start Menu and Desktop shortcuts for all Adobe applications."""
        shortcuts = []
        search_dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%USERPROFILE%\Desktop"),
            os.path.expandvars(r"%PUBLIC%\Desktop")
        ]

        ps_script = """
        $wsh = New-Object -ComObject WScript.Shell
        $filters = @("*Adobe*.lnk", "*Premiere*.lnk", "*Photoshop*.lnk", "*After*.lnk", "*Illustrator*.lnk", "*Acrobat*.lnk", "*Audition*.lnk", "*Lightroom*.lnk", "*InDesign*.lnk", "*Media Encoder*.lnk", "*Substance*.lnk")
        Get-ChildItem -Path @({search_paths}) -Include $filters -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $sc = $wsh.CreateShortcut($_.FullName)
                [PSCustomObject]@{
                    ShortcutPath = $_.FullName
                    TargetPath = $sc.TargetPath
                    Name = $_.BaseName
                } | ConvertTo-Json -Compress
            } catch {}
        }
        """
        valid_paths = [f'"{d}"' for d in search_dirs if os.path.exists(d)]
        if not valid_paths:
            return shortcuts
        formatted_script = ps_script.replace("{search_paths}", ", ".join(valid_paths))

        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", formatted_script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10
            )
            import json
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        if data.get("TargetPath"):
                            shortcuts.append(data)
                    except Exception:
                        pass
        except Exception as e:
            self.log(f"Error querying Adobe shortcuts: {e}", "WARNING")

        return shortcuts

    def get_registry_app_paths(self) -> List[Dict[str, Any]]:
        """Scans Windows Registry App Paths for registered Adobe executables."""
        results = []
        for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                sub_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
                with winreg.OpenKey(root_key, sub_path, 0, winreg.KEY_READ) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            app_name = winreg.EnumKey(key, i)
                            if any(k in app_name.lower() for k in ["adobe", "photoshop", "premiere", "afterfx", "illustrator", "acrobat", "lightroom", "audition", "ame", "substance"]):
                                with winreg.OpenKey(key, app_name) as app_key:
                                    val, _ = winreg.QueryValueEx(app_key, "")
                                    cleaned = val.strip().strip('"')
                                    if cleaned:
                                        results.append({"name": app_name, "exe_path": cleaned})
                        except Exception:
                            pass
            except Exception:
                pass
        return results

    def find_all_installations(self) -> List[Dict[str, Any]]:
        """
        Locates ALL Adobe applications across shortcuts, registry, and all physical/logical drives.
        """
        found = {}

        # 1. Start Menu & Desktop Shortcuts
        for sc in self.get_start_menu_shortcuts():
            target = sc.get("TargetPath", "").strip().strip('"')
            if not target:
                continue
            meta = identify_adobe_app_by_path(target)
            if meta or any(x in target.lower() for x in ["adobe", "premiere", "photoshop", "afterfx", "illustrator"]):
                exists = os.path.isfile(target)
                key = target.lower()
                app_data = meta["data"] if meta else {}
                found[key] = {
                    "app_id": meta["id"] if meta else "generic_adobe",
                    "name": app_data.get("name", sc.get("Name")),
                    "short_name": app_data.get("short_name", sc.get("Name")),
                    "category": app_data.get("category", "Adobe Application"),
                    "icon": app_data.get("icon", "⚡"),
                    "exe_path": target,
                    "shortcut_path": sc.get("ShortcutPath"),
                    "exists": exists,
                    "is_ascii": self.is_ascii(target),
                    "has_non_ascii_path": not self.is_ascii(target),
                    "source": "shortcut"
                }

        # 2. Windows Registry App Paths
        for reg in self.get_registry_app_paths():
            target = reg["exe_path"]
            key = target.lower()
            if key not in found:
                exists = os.path.isfile(target)
                meta = identify_adobe_app_by_path(target)
                app_data = meta["data"] if meta else {}
                found[key] = {
                    "app_id": meta["id"] if meta else "generic_adobe",
                    "name": app_data.get("name", reg["name"]),
                    "short_name": app_data.get("short_name", reg["name"]),
                    "category": app_data.get("category", "Adobe Application"),
                    "icon": app_data.get("icon", "⚡"),
                    "exe_path": target,
                    "shortcut_path": None,
                    "exists": exists,
                    "is_ascii": self.is_ascii(target),
                    "has_non_ascii_path": not self.is_ascii(target),
                    "source": "registry"
                }

        # 3. Dynamic Deep Multi-Disk Scanner across all drives (C:, D:, F:, etc.)
        try:
            drive_installs = self.disk_scanner.deep_scan_all_drives_for_all_adobe_apps()
            for di in drive_installs:
                key = di["exe_path"].lower()
                if key not in found:
                    found[key] = {
                        "app_id": di["app_id"],
                        "name": di["name"],
                        "short_name": di["short_name"],
                        "category": di["category"],
                        "icon": di["icon"],
                        "exe_path": di["exe_path"],
                        "shortcut_path": None,
                        "exists": True,
                        "is_ascii": di["is_ascii"],
                        "has_non_ascii_path": di["has_non_ascii_path"],
                        "version": di.get("version", "Unknown"),
                        "source": "multi_disk_scan"
                    }
        except Exception as e:
            self.log(f"Multi-disk scan error: {e}", "WARNING")

        # Retrieve file version strings and GPU High-Performance status
        gpu_prefs = self.get_all_gpu_preferences()
        results = []
        for item in found.values():
            if item["exists"]:
                if "version" not in item or item["version"] == "Unknown":
                    item["version"] = self.get_file_version(item["exe_path"])
            else:
                item["version"] = "File Missing"

            # Check if this executable has High-Performance GPU override
            norm_p = os.path.normpath(item["exe_path"]).lower()
            item["gpu_high_performance"] = any(norm_p == p.lower() and "GpuPreference=2" in v for p, v in gpu_prefs.items())
            results.append(item)

        # Sort so existing apps appear first, sorted by name
        return sorted(results, key=lambda x: (not x["exists"], x["name"]))

    def get_file_version(self, filepath: str) -> str:
        """Retrieves file version string via PowerShell."""
        try:
            cmd = f'(Get-Item -LiteralPath "{filepath}").VersionInfo.ProductVersion'
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=4)
            res = proc.stdout.strip()
            if res:
                return res
        except Exception:
            pass
        return "Unknown"

    def get_all_gpu_preferences(self) -> Dict[str, str]:
        """Reads all UserGpuPreferences from Windows DirectX registry."""
        prefs = {}
        try:
            key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    v_name, v_val, _ = winreg.EnumValue(key, i)
                    prefs[v_name] = v_val
        except Exception:
            pass
        return prefs

    def get_gpu_diagnostics(self) -> Dict[str, Any]:
        """Detects GPUs, drivers, dual GPU configuration, and DirectX High Performance registry."""
        gpu_info = {
            "gpus": [],
            "is_dual_gpu": False,
            "has_nvidia": False,
            "has_intel": False,
            "has_amd": False,
            "primary_dgpu": None,
            "high_performance_configured": False,
            "gpu_pref_entries": []
        }

        try:
            ps_cmd = "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, DriverDate | ConvertTo-Json"
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=6)
            import json
            data = json.loads(proc.stdout)
            if isinstance(data, dict):
                data = [data]
            for g in data:
                name = g.get("Name", "Unknown")
                ver = g.get("DriverVersion", "")
                name_l = name.lower()
                is_dgpu = False
                if "nvidia" in name_l or "geforce" in name_l or "rtx" in name_l or "gtx" in name_l:
                    gpu_info["has_nvidia"] = True
                    is_dgpu = True
                    if not gpu_info["primary_dgpu"]:
                        gpu_info["primary_dgpu"] = name
                elif "amd" in name_l or "radeon" in name_l:
                    gpu_info["has_amd"] = True
                    is_dgpu = True
                    if not gpu_info["primary_dgpu"]:
                        gpu_info["primary_dgpu"] = name
                elif "intel" in name_l:
                    gpu_info["has_intel"] = True

                gpu_info["gpus"].append({
                    "name": name,
                    "driver": ver,
                    "driver_date": g.get("DriverDate", ""),
                    "is_dgpu": is_dgpu
                })

            gpu_info["is_dual_gpu"] = ((gpu_info["has_nvidia"] or gpu_info["has_amd"]) and gpu_info["has_intel"])
        except Exception as e:
            self.log(f"GPU check error: {e}", "WARNING")

        # Check UserGpuPreferences in Registry
        prefs = self.get_all_gpu_preferences()
        for p, v in prefs.items():
            gpu_info["gpu_pref_entries"].append({"path": p, "preference": v})
            if any(k in p.lower() for k in ["adobe", "premiere", "photoshop", "afterfx", "illustrator"]) and "GpuPreference=2" in v:
                gpu_info["high_performance_configured"] = True

        return gpu_info

    def get_font_cache_diagnostics(self) -> Dict[str, Any]:
        """Scans for corrupted Adobe font caches (AdobeFnt*.lst and .db)."""
        font_files = []
        total_size = 0
        search_roots = [
            os.path.expandvars(r"%APPDATA%\Adobe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Adobe"),
            os.path.expandvars(r"%PROGRAMDATA%\Adobe"),
            os.path.expandvars(r"%COMMONPROGRAMFILES%\Adobe\Fonts")
        ]
        for s_root in search_roots:
            if os.path.isdir(s_root):
                for root, _, files in os.walk(s_root):
                    for f in files:
                        if f.lower().startswith("adobefnt") and (f.lower().endswith(".lst") or f.lower().endswith(".db")):
                            fp = os.path.join(root, f)
                            try:
                                sz = os.path.getsize(fp)
                                total_size += sz
                                font_files.append({"path": fp, "size": sz})
                            except OSError:
                                pass

        return {
            "total_files": len(font_files),
            "total_size_kb": round(total_size / 1024, 2),
            "files": font_files
        }

    def get_cache_diagnostics(self) -> Dict[str, Any]:
        """Scans Adobe Common Media Cache, Peak files, CameraRaw, and temp caches."""
        appdata = os.getenv("APPDATA", "")
        localappdata = os.getenv("LOCALAPPDATA", "")

        cache_folders = [
            os.path.join(appdata, "Adobe", "Common", "Media Cache Files"),
            os.path.join(appdata, "Adobe", "Common", "Media Cache"),
            os.path.join(appdata, "Adobe", "Common", "Peak Files"),
            os.path.join(appdata, "Adobe", "Common", "Analyzer Cache Files"),
            os.path.join(appdata, "Adobe", "Common", "PTX"),
            os.path.join(appdata, "Adobe", "CameraRaw", "Cache"),
            os.path.join(localappdata, "Adobe", "CameraRaw", "Cache")
        ]

        total_bytes = 0
        total_files = 0
        folder_details = []

        for folder in cache_folders:
            folder_bytes = 0
            folder_count = 0
            if os.path.exists(folder):
                for root, _, files in os.walk(folder):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            folder_bytes += os.path.getsize(fp)
                            folder_count += 1
                        except OSError:
                            pass
            folder_details.append({
                "path": folder,
                "name": os.path.basename(folder),
                "exists": os.path.exists(folder),
                "file_count": folder_count,
                "size_mb": round(folder_bytes / (1024 * 1024), 2)
            })
            total_bytes += folder_bytes
            total_files += folder_count

        return {
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "total_files": total_files,
            "folders": folder_details
        }

    def get_appdata_versions(self) -> List[Dict[str, Any]]:
        """Detects version profile folders across AppData\\Roaming\\Adobe."""
        appdata = os.getenv("APPDATA", "")
        adobe_dir = os.path.join(appdata, "Adobe")
        versions = []

        if os.path.exists(adobe_dir):
            for app_folder in os.listdir(adobe_dir):
                full_app = os.path.join(adobe_dir, app_folder)
                if os.path.isdir(full_app) and app_folder not in ["Common", "CameraRaw", "CRLogs"]:
                    # Check for versioned folders
                    for sub in os.listdir(full_app):
                        sub_p = os.path.join(full_app, sub)
                        if os.path.isdir(sub_p) and any(c.isdigit() for c in sub):
                            plugin_log = os.path.join(sub_p, "Plugin Loading.log")
                            versions.append({
                                "app": app_folder,
                                "version_folder": sub,
                                "path": sub_p,
                                "has_plugin_log": os.path.isfile(plugin_log)
                            })

        return versions

    def get_recent_crash_events(self) -> List[Dict[str, Any]]:
        """Queries Windows Event Log for recent Adobe crash events."""
        events = []
        ps_script = """
        try {
            Get-WinEvent -FilterHashtable @{
                LogName = 'Application'
                ProviderName = @('Application Error', 'Windows Error Reporting')
                StartTime = (Get-Date).AddDays(-7)
            } -MaxEvents 30 -ErrorAction SilentlyContinue |
            Where-Object { $_.Message -like "*Premiere*" -or $_.Message -like "*Photoshop*" -or $_.Message -like "*AfterFX*" -or $_.Message -like "*Adobe*" } |
            Select-Object -First 5 | ForEach-Object {
                [PSCustomObject]@{
                    Time = $_.TimeCreated.ToString("dd/MM/yyyy HH:mm:ss")
                    Provider = $_.ProviderName
                    Id = $_.Id
                    Summary = ($_.Message -split "`n")[0].Trim()
                } | ConvertTo-Json -Compress
            }
        } catch {}
        """
        try:
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
            import json
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        events.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass

        return events

    def run_full_diagnosis(self) -> Dict[str, Any]:
        """
        Runs the complete diagnostic suite for ALL Adobe applications.
        Calculates severity, pinpoints crash vectors, and formulates 1-click solutions.
        """
        installations = self.find_all_installations()
        gpu_info = self.get_gpu_diagnostics()
        cache_info = self.get_cache_diagnostics()
        font_info = self.get_font_cache_diagnostics()
        appdata_versions = self.get_appdata_versions()
        recent_crashes = self.get_recent_crash_events()
        sys_profile = self.inspector.inspect_complete_system()

        issues = []
        critical_count = 0
        warning_count = 0

        # Check 1: Non-ASCII / Localized Greek Path in any Adobe application
        non_ascii_apps = [i for i in installations if i["exists"] and i["has_non_ascii_path"]]
        ascii_repaired = [i for i in installations if i["exists"] and not i["has_non_ascii_path"] and ("AdobePremierePro" in i["exe_path"] or "Repaired" in i["exe_path"])]

        if non_ascii_apps:
            if ascii_repaired:
                issues.append({
                    "severity": "INFO",
                    "category": "PATH_RESOLVED",
                    "title": "Non-ASCII Path Mitigated via Active NTFS Junction",
                    "description": "Original files reside in a folder with non-English characters, but a clean ASCII NTFS Junction is established.",
                    "fix_action": "USE_REPAIRED_SHORTCUT"
                })
            else:
                critical_count += 1
                for bad in non_ascii_apps:
                    issues.append({
                        "severity": "CRITICAL",
                        "category": "PATH_ERROR",
                        "title": f"Non-ASCII Character Path: {bad['name']}",
                        "description": f"Located in '{bad['exe_path']}'. Non-ASCII characters cause immediate silent crashes in Adobe C++ runtime DLLs (MediaCore, DynamicLink, UXP).",
                        "fix_action": "CREATE_ASCII_JUNCTION",
                        "target_path": bad["exe_path"]
                    })

        # Check 2: Dual GPU setup without High-Performance override
        unconfigured_gpu_apps = [i for i in installations if i["exists"] and not i.get("gpu_high_performance")]
        if gpu_info["is_dual_gpu"] and unconfigured_gpu_apps:
            critical_count += 1
            primary_name = gpu_info.get("primary_dgpu") or "Dedicated GPU"
            issues.append({
                "severity": "CRITICAL",
                "category": "GPU_CONFLICT",
                "title": f"Dual-GPU Conflict ({len(unconfigured_gpu_apps)} Apps Unassigned)",
                "description": f"System has dual GPUs ({primary_name} + Integrated Graphics). "
                               "Adobe GPUSniffer and DirectX switch between graphics cards during splash screen startup, triggering silent crash.",
                "fix_action": "FORCE_HIGH_PERFORMANCE_GPU"
            })

        # Check 3: Font cache accumulation (Causes Photoshop & Illustrator crash)
        if font_info["total_files"] > 10:
            warning_count += 1
            issues.append({
                "severity": "WARNING",
                "category": "FONT_CACHE",
                "title": f"Stale/Corrupted Adobe Font Caches ({font_info['total_files']} files)",
                "description": "Corrupted AdobeFnt*.lst files freeze or crash Photoshop, Illustrator, Premiere Pro, and InDesign during font enumeration.",
                "fix_action": "PURGE_FONT_CACHE"
            })

        # Check 4: Media & Scratch Cache Bloat
        if cache_info["total_size_mb"] > 250 or cache_info["total_files"] > 350:
            warning_count += 1
            issues.append({
                "severity": "WARNING",
                "category": "CACHE_BLOAT",
                "title": f"Adobe Cache Overload ({cache_info['total_size_mb']} MB, {cache_info['total_files']} files)",
                "description": "Corrupted or orphaned Media Cache & Peak files cause crashes during project opening or asset playback.",
                "fix_action": "PURGE_CACHE"
            })

        # Check 5: Broken shortcuts
        broken_shortcuts = [i for i in installations if not i["exists"] and i.get("source") == "shortcut"]
        if broken_shortcuts:
            warning_count += 1
            for b in broken_shortcuts:
                issues.append({
                    "severity": "WARNING",
                    "category": "BROKEN_SHORTCUT",
                    "title": f"Dead Adobe Shortcut: {b['name']}",
                    "description": f"Points to missing target: '{b['exe_path']}'.",
                    "fix_action": "REMOVE_BROKEN_SHORTCUT",
                    "target_path": b.get("shortcut_path")
                })

        # Status calculation
        status = "HEALTHY"
        if critical_count > 0:
            status = "CRITICAL"
        elif warning_count > 0:
            status = "WARNING"

        return {
            "status": status,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "issues": issues,
            "installations": installations,
            "gpu_info": gpu_info,
            "font_info": font_info,
            "cache_info": cache_info,
            "appdata_versions": appdata_versions,
            "recent_crashes": recent_crashes,
            "system_profile": sys_profile
        }

# Backwards compatibility alias
PremiereDiagnostics = AdobeDiagnostics
