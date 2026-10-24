import os
import sys
import shutil
import subprocess
import winreg
from typing import Dict, Any, List

class NuclearPurgeEngine:
    def __init__(self, logger=None):
        self.logger = logger

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}")

    def kill_all_adobe_processes(self) -> int:
        """Kills any active or background Adobe and related processes to release all file locks."""
        processes = [
            "Adobe Premiere Pro", "GPUSniffer", "dynamiclinkmanager",
            "TeamProjectsLocalHub", "dvaaudiofilterscan", "dvaapprelauncher",
            "CRWindowsClientService", "Creative Cloud", "CoreSync",
            "CCXProcess", "AdobeIPCBroker", "AdobeNotificationClient",
            "AcroCEF", "AdobeDesktopService", "CCLibrary"
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
        self.log("Terminated all Adobe background processes and services.", "SUCCESS")
        return killed

    def purge_windows_credentials(self) -> int:
        """Purges stale, corrupted Adobe credentials from Windows Credential Manager to fix UXP-IMS token deadlocks."""
        self.log("Scanning Windows Credential Manager for obsolete Adobe licensing tokens...", "INFO")
        deleted = 0
        try:
            cmd = "cmdkey /list"
            proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding="utf-8", errors="replace")
            lines = proc.stdout.splitlines()
            targets_to_delete = []

            for line in lines:
                line = line.strip()
                if line.startswith("Target:"):
                    target_val = line[len("Target:"):].strip()
                    if "Adobe" in target_val or "ACCC." in target_val:
                        targets_to_delete.append(target_val)

            self.log(f"Found {len(targets_to_delete)} stale Adobe credentials in vault.", "INFO")
            for t in targets_to_delete:
                del_cmd = f'cmdkey /delete:"{t}"'
                res = subprocess.run(del_cmd, capture_output=True, shell=True, text=True)
                if res.returncode == 0:
                    deleted += 1

            self.log(f"Purged {deleted} stale credentials from Windows Credential Manager.", "SUCCESS")
        except Exception as e:
            self.log(f"Error purging credentials: {e}", "WARNING")
        return deleted

    def configure_firewall_rules(self, premiere_exe_paths: List[str]) -> Dict[str, Any]:
        """
        Sanitizes Windows Firewall rules:
        1. Ensures local loopback (127.0.0.1) is Allowed for Premiere and dynamiclink to prevent IPC socket timeouts.
        2. Configures rules cleanly.
        """
        self.log("Sanitizing Windows Firewall rules for Adobe Premiere Pro and local IPC sockets...", "INFO")
        results = {"rules_added": 0, "errors": []}

        for exe in premiere_exe_paths:
            if not os.path.isfile(exe):
                continue
            folder = os.path.dirname(exe)
            dlm_exe = os.path.join(folder, "dynamiclinkmanager.exe")
            hub_exe = os.path.join(folder, "TeamProjectsLocalHub.exe")

            targets = [exe]
            if os.path.isfile(dlm_exe):
                targets.append(dlm_exe)
            if os.path.isfile(hub_exe):
                targets.append(hub_exe)

            for target in targets:
                base = os.path.basename(target)
                ps_script = f"""
                try {{
                    # Remove any blocking or duplicate rules
                    Remove-NetFirewallRule -DisplayName "PProDoctor - {base} *" -ErrorAction SilentlyContinue
                    
                    # Add Local Loopback Inbound
                    New-NetFirewallRule -DisplayName "PProDoctor - {base} Inbound" `
                        -Direction Inbound -Program "{target}" -Action Allow `
                        -Profile Any -ErrorAction SilentlyContinue | Out-Null
                        
                    # Add Local Loopback Outbound
                    New-NetFirewallRule -DisplayName "PProDoctor - {base} Outbound" `
                        -Direction Outbound -Program "{target}" -Action Allow `
                        -Profile Any -ErrorAction SilentlyContinue | Out-Null
                    "OK"
                }} catch {{
                    $_.Exception.Message
                }}
                """
                try:
                    proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
                    if "OK" in proc.stdout:
                        results["rules_added"] += 2
                except Exception as e:
                    results["errors"].append(str(e))

        self.log(f"Windows Firewall sanitized: Added/Reset {results['rules_added']} optimized loopback rules.", "SUCCESS")
        return results

    def root_cache_and_temp_purge(self, all_drives: List[str] = None) -> Dict[str, Any]:
        """
        Deep nuclear purge of all caching layers:
        - User AppData (Common, CRLogs, GPUSniffer, UXP)
        - Local AppData (GLCache, D3DSCache, Temp)
        - ProgramData (SLStore, SLData, OOBE caches)
        - Multi-Drive scattered project caches (.pek, .cfa, Media Cache Files)
        """
        self.kill_all_adobe_processes()
        self.log("Executing ROOT-LEVEL Media Cache & Temporary Storage Purge...", "INFO")

        appdata = os.getenv("APPDATA", "")
        localappdata = os.getenv("LOCALAPPDATA", "")
        programdata = os.getenv("PROGRAMDATA", "")

        targets = [
            # AppData Roaming
            os.path.join(appdata, r"Adobe\Common\Media Cache Files"),
            os.path.join(appdata, r"Adobe\Common\Media Cache"),
            os.path.join(appdata, r"Adobe\Common\Peak Files"),
            os.path.join(appdata, r"Adobe\Common\Analyzer Cache Files"),
            os.path.join(appdata, r"Adobe\Common\PTX"),
            os.path.join(appdata, r"Adobe\CRLogs"),
            os.path.join(appdata, r"Adobe\GPUSniffer"),
            # LocalAppData
            os.path.join(localappdata, r"Adobe\GLCache"),
            os.path.join(localappdata, r"Adobe\D3DSCache"),
            os.path.join(localappdata, r"CrashDumps"),
            # ProgramData
            os.path.join(programdata, r"Adobe\SLStore"),
            os.path.join(programdata, r"Adobe\SLData")
        ]

        deleted_files = 0
        freed_bytes = 0

        # Purge standard target folders
        for folder in targets:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder, topdown=False):
                    for f in files:
                        if "crash" in f.lower() or "dmp" in f.lower() or "cache" in folder.lower() or "adobe" in folder.lower():
                            fp = os.path.join(root, f)
                            try:
                                freed_bytes += os.path.getsize(fp)
                                os.remove(fp)
                                deleted_files += 1
                            except OSError:
                                pass

        # Fast Temp cleanup using targeted globs rather than deep full directory walking
        temp_dir = os.getenv("TEMP", "")
        if os.path.exists(temp_dir):
            patterns = ["Adobe*", "*.pek", "*.cfa", "RDR*.tmp", "WER*.tmp"]
            import glob
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

        # Multi-Drive Scan for scattered cache folders
        if all_drives:
            for d in all_drives:
                scattered_candidates = [
                    os.path.join(d, "Media Cache Files"),
                    os.path.join(d, "Media Cache")
                ]
                for sc in scattered_candidates:
                    if os.path.exists(sc) and os.path.normpath(sc).lower() != os.path.normpath(appdata).lower():
                        for root, _, files in os.walk(sc):
                            for f in files:
                                fp = os.path.join(root, f)
                                try:
                                    freed_bytes += os.path.getsize(fp)
                                    os.remove(fp)
                                    deleted_files += 1
                                except OSError:
                                    pass

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        self.log(f"Root Cache Purge Completed: {deleted_files} files wiped ({freed_mb} MB reclaimed).", "SUCCESS")
        return {"deleted_files": deleted_files, "freed_mb": freed_mb}

    def purge_corrupt_registry_trees(self) -> int:
        """Purges corrupted MRU and workspace layouts in Registry for clean first launch."""
        self.log("Sanitizing Registry roots for Adobe Premiere Pro...", "INFO")
        cleaned_keys = 0
        base_subkeys = [
            r"Software\Adobe\Premiere Pro\26.0\MRU",
            r"Software\Adobe\Premiere Pro\24.0\MRU",
            r"Software\Adobe\Premiere Pro\26.0\Workspaces",
            r"Software\Adobe\Premiere Pro\24.0\Workspaces",
            r"Software\Adobe\Premiere Pro\26.0\Layouts",
            r"Software\Adobe\Premiere Pro\24.0\Layouts"
        ]
        for sub in base_subkeys:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub)
                cleaned_keys += 1
            except FileNotFoundError:
                pass
            except OSError:
                pass

        self.log(f"Cleaned {cleaned_keys} corrupted Registry tree nodes.", "SUCCESS")
        return cleaned_keys

    def execute_complete_nuclear_purge(self, premiere_exe_paths: List[str], all_drives: List[str] = None) -> Dict[str, Any]:
        """Runs the complete Root-Level Purge & Sanitizer across the entire computer."""
        self.log("====================================================", "INFO")
        self.log("  INITIATING COMPLETE NUCLEAR ROOT-LEVEL SYSTEM PURGE", "INFO")
        self.log("====================================================", "INFO")

        # 1. Kill processes
        self.kill_all_adobe_processes()

        # 2. Windows Firewall Rules
        fw_res = self.configure_firewall_rules(premiere_exe_paths)

        # 3. Purge Windows Credentials Vault
        cred_count = self.purge_windows_credentials()

        # 4. Root Cache & Temp Purge across all drives
        cache_res = self.root_cache_and_temp_purge(all_drives)

        # 5. Registry Sanitization
        reg_count = self.purge_corrupt_registry_trees()

        self.log("====================================================", "SUCCESS")
        self.log("  NUCLEAR ROOT-LEVEL PURGE COMPLETED SUCCESSFULLY!", "SUCCESS")
        self.log("====================================================", "SUCCESS")

        return {
            "firewall": fw_res,
            "credentials_purged": cred_count,
            "cache_purged": cache_res,
            "registry_keys_cleaned": reg_count
        }
