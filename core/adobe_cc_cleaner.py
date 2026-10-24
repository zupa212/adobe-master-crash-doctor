import os
import sys
import shutil
import subprocess
import urllib.request
import winreg
from typing import Dict, Any, List

class AdobeCreativeCloudCleaner:
    def __init__(self, logger=None):
        self.logger = logger
        self.cleaner_tool_url = "https://download.macromedia.com/SupportTools/Cleaner/win/AdobeCreativeCloudCleanerTool.exe"

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}")

    def detect_creative_cloud_presence(self) -> Dict[str, Any]:
        """Detects Creative Cloud app, uninstaller utility, services, and tasks on the machine."""
        program_files_x86 = os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)")
        program_files = os.getenv("ProgramFiles", r"C:\Program Files")

        uninstaller_paths = [
            os.path.join(program_files_x86, r"Adobe\Adobe Creative Cloud\Utils\Creative Cloud Uninstaller.exe"),
            os.path.join(program_files, r"Adobe\Adobe Creative Cloud\Utils\Creative Cloud Uninstaller.exe")
        ]
        found_uninstaller = None
        for p in uninstaller_paths:
            if os.path.isfile(p):
                found_uninstaller = p
                break

        cc_exe_paths = [
            os.path.join(program_files, r"Adobe\Adobe Creative Cloud\ACC\Creative Cloud.exe"),
            os.path.join(program_files_x86, r"Adobe\Adobe Creative Cloud\ACC\Creative Cloud.exe")
        ]
        has_cc_installed = any(os.path.isfile(p) for p in cc_exe_paths)

        # Check Services
        services = ["AdobeUpdateService", "AGSService", "AdobeARMservice"]
        detected_services = []
        for s in services:
            try:
                proc = subprocess.run(["sc", "query", s], capture_output=True, text=True)
                if "RUNNING" in proc.stdout or "STOPPED" in proc.stdout:
                    detected_services.append(s)
            except Exception:
                pass

        # Check Scheduled Tasks
        detected_tasks = []
        try:
            ps_cmd = 'Get-ScheduledTask | Where-Object { $_.TaskName -like "*Adobe*" } | Select-Object -ExpandProperty TaskName'
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout.strip().splitlines():
                if line.strip():
                    detected_tasks.append(line.strip())
        except Exception:
            pass

        return {
            "has_cc_installed": has_cc_installed,
            "uninstaller_path": found_uninstaller,
            "detected_services": detected_services,
            "detected_tasks": detected_tasks
        }

    def terminate_all_adobe_processes(self) -> int:
        """Kills all active Adobe background processes."""
        processes = [
            "Creative Cloud", "CoreSync", "CCXProcess", "AdobeIPCBroker",
            "AdobeNotificationClient", "AcroCEF", "AdobeDesktopService",
            "CCLibrary", "AGSService", "AdobeARMservice", "CRWindowsClientService",
            "Adobe Premiere Pro", "GPUSniffer", "dynamiclinkmanager"
        ]
        killed = 0
        for p in processes:
            try:
                cmd = f"Stop-Process -Name '{p}' -Force -ErrorAction SilentlyContinue"
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
                if res.returncode == 0:
                    killed += 1
            except Exception:
                pass
        self.log(f"Terminated all running Adobe processes ({killed} killed).", "SUCCESS")
        return killed

    def stop_and_delete_adobe_services(self) -> List[str]:
        """Stops and unregisters all background Adobe Windows Services."""
        services = ["AdobeUpdateService", "AGSService", "AdobeARMservice"]
        deleted = []
        for s in services:
            try:
                subprocess.run(["sc", "stop", s], capture_output=True)
                res = subprocess.run(["sc", "delete", s], capture_output=True, text=True)
                if res.returncode == 0:
                    deleted.append(s)
                    self.log(f"Unregistered Adobe Windows Service: {s}", "SUCCESS")
            except Exception:
                pass
        return deleted

    def remove_adobe_scheduled_tasks(self) -> int:
        """Removes all scheduled telemetry and auto-updater tasks from Windows Task Scheduler."""
        ps_cmd = """
        $removed = 0
        Get-ScheduledTask | Where-Object { $_.TaskName -like "*Adobe*" } | ForEach-Object {
            try {
                Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false -ErrorAction SilentlyContinue
                $removed++
            } catch {}
        }
        $removed
        """
        try:
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
            count = int(proc.stdout.strip() or 0)
            if count > 0:
                self.log(f"Removed {count} Adobe background Scheduled Tasks.", "SUCCESS")
            return count
        except Exception:
            return 0

    def remove_adobe_startup_registry(self) -> int:
        """Removes Adobe entries from Windows Run startup registries."""
        reg_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
        ]
        removed = 0
        for hive, subkey in reg_keys:
            try:
                with winreg.OpenKey(hive, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
                    values_to_del = []
                    try:
                        i = 0
                        while True:
                            v_name, _, _ = winreg.EnumValue(key, i)
                            if "adobe" in v_name.lower() or "ccx" in v_name.lower():
                                values_to_del.append(v_name)
                            i += 1
                    except OSError:
                        pass

                    for v in values_to_del:
                        try:
                            winreg.DeleteValue(key, v)
                            removed += 1
                            self.log(f"Removed Startup Registry Key: {v}", "SUCCESS")
                        except OSError:
                            pass
            except Exception:
                pass
        return removed

    def run_built_in_uninstaller(self, uninstaller_path: str = None) -> bool:
        """Executes the local Creative Cloud Uninstaller utility silently (-u switch)."""
        if not uninstaller_path:
            detection = self.detect_creative_cloud_presence()
            uninstaller_path = detection.get("uninstaller_path")

        if not uninstaller_path or not os.path.isfile(uninstaller_path):
            self.log("Local Creative Cloud Uninstaller executable not found.", "WARNING")
            return False

        self.log(f"Triggering Creative Cloud Uninstaller silently: {uninstaller_path} -u", "INFO")
        try:
            # -u means uninstall silently
            cmd = f'"{uninstaller_path}" -u'
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            self.log("Creative Cloud Uninstaller completed.", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Error running Creative Cloud Uninstaller: {e}", "ERROR")
            return False

    def download_and_run_official_cleaner(self, target_dir: str = None, remove_mode: str = "ALL") -> bool:
        """
        Downloads the official Adobe Creative Cloud Cleaner Tool directly from Adobe CDN
        and executes it silently: --eulaAccepted=1 --removeAll=ALL
        """
        if not target_dir:
            target_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        cleaner_exe = os.path.join(target_dir, "AdobeCreativeCloudCleanerTool.exe")

        if not os.path.isfile(cleaner_exe):
            self.log(f"Downloading official Adobe Creative Cloud Cleaner Tool from Adobe CDN...", "INFO")
            try:
                urllib.request.urlretrieve(self.cleaner_tool_url, cleaner_exe)
                self.log(f"Successfully downloaded: {cleaner_exe}", "SUCCESS")
            except Exception as e:
                self.log(f"Failed to download Adobe Cleaner Tool: {e}", "ERROR")
                return False

        self.log(f"Executing Adobe Cleaner Tool silently: --eulaAccepted=1 --removeAll={remove_mode}", "INFO")
        try:
            cmd = f'"{cleaner_exe}" --eulaAccepted=1 --removeAll={remove_mode}'
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
            self.log("Adobe Creative Cloud Cleaner Tool finished root wiping.", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Error during Cleaner Tool execution: {e}", "ERROR")
            return False

    def nuclear_purge_all_cc_directories(self) -> int:
        """Wipes all Creative Cloud residual root directories."""
        appdata = os.getenv("APPDATA", "")
        localappdata = os.getenv("LOCALAPPDATA", "")
        programdata = os.getenv("PROGRAMDATA", "")
        pf = os.getenv("ProgramFiles", r"C:\Program Files")
        pfx86 = os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)")

        target_dirs = [
            os.path.join(programdata, r"Adobe\OOBE"),
            os.path.join(programdata, r"Adobe\SLStore"),
            os.path.join(programdata, r"Adobe\SLData"),
            os.path.join(programdata, r"Adobe\OperatingConfigs"),
            os.path.join(pf, r"Adobe\Adobe Creative Cloud"),
            os.path.join(pfx86, r"Adobe\Adobe Creative Cloud"),
            os.path.join(appdata, r"Adobe\Creative Cloud Libraries"),
            os.path.join(appdata, r"Adobe\CoreSync"),
            os.path.join(appdata, r"Adobe\CCX Welcome"),
            os.path.join(localappdata, r"Adobe\Creative Cloud"),
            os.path.join(localappdata, r"Adobe\OOBE")
        ]

        deleted_dirs = 0
        for d in target_dirs:
            if os.path.isdir(d):
                try:
                    shutil.rmtree(d, ignore_errors=True)
                    deleted_dirs += 1
                    self.log(f"Wiped root CC directory: {d}", "SUCCESS")
                except OSError:
                    pass

        return deleted_dirs

    def execute_complete_cc_uninstaller_suite(self) -> Dict[str, Any]:
        """End-to-end Root Uninstaller for Creative Cloud and all related background services."""
        self.log("=======================================================", "INFO")
        self.log("  STARTING ADOBE CREATIVE CLOUD ROOT UNINSTALLER SUITE", "INFO")
        self.log("=======================================================", "INFO")

        # 1. Kill all processes
        self.terminate_all_adobe_processes()

        # 2. Stop and Delete Windows Services
        deleted_services = self.stop_and_delete_adobe_services()

        # 3. Remove Scheduled Tasks
        tasks_count = self.remove_adobe_scheduled_tasks()

        # 4. Remove Startup Registry Keys
        reg_count = self.remove_adobe_startup_registry()

        # 5. Try local uninstaller if present
        detection = self.detect_creative_cloud_presence()
        uninstalled_local = False
        if detection.get("uninstaller_path"):
            uninstalled_local = self.run_built_in_uninstaller(detection["uninstaller_path"])

        # 6. Run Official Adobe Cleaner Tool silently
        cleaner_ok = self.download_and_run_official_cleaner(remove_mode="CREATIVECLOUDCS6PRODUCTS")

        # 7. Wipe residual root folders
        wiped_dirs_count = self.nuclear_purge_all_cc_directories()

        self.log("=======================================================", "SUCCESS")
        self.log("  CREATIVE CLOUD UNINSTALLATION & ROOT WIPE COMPLETED! ", "SUCCESS")
        self.log("=======================================================", "SUCCESS")

        return {
            "uninstalled_local": uninstalled_local,
            "cleaner_executed": cleaner_ok,
            "deleted_services": deleted_services,
            "tasks_removed": tasks_count,
            "startup_keys_removed": reg_count,
            "wiped_directories": wiped_dirs_count
        }
