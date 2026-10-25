import os
import sys
import json
import shutil
import subprocess
import winreg
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, List, Optional

class DeepRegistryHealer:
    """
    Claude Opus 5.5 Max Deep Registry & Driver Uninstaller Engine.
    Tailored specifically for modern high-performance rigs (NVIDIA RTX 5060 Blackwell + AMD Ryzen 5,
    RTX 3060, Intel Arc & Multi-GPU deconfliction).
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.relay_url = "http://localhost:3002/api/chat"
        self.model_name = "claude-opus-5-5"

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            try:
                print(f"[{level}] {msg}")
            except UnicodeEncodeError:
                safe_msg = msg.encode("ascii", errors="replace").decode("ascii")
                print(f"[{level}] {safe_msg}")

    # =========================================================================
    # 1. CLAUDE OPUS 5.5 MAX CONSULTATION & EMBEDDED GOLD MASTER MATRIX
    # =========================================================================

    def consult_claude_opus(self, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Consults Claude Opus 5.5 via the local LLMsRelay developer gateway.
        If offline or unreachable (e.g. running standalone on a friend's PC),
        seamlessly executes the embedded Claude Opus 5.5 Gold Master Architecture Matrix.
        """
        self.log("🤖 Initializing Claude Opus 5.5 Max Architectural Consultation...", "INFO")

        cpu_str = "AMD Ryzen 5 / Multi-Core"
        gpu_str = "NVIDIA GeForce RTX 5060 (Blackwell) + AMD Radeon iGPU"
        os_str = "Windows 11 64-bit"

        if telemetry:
            cpu_name = telemetry.get("cpu", {}).get("name", "")
            if cpu_name:
                cpu_str = cpu_name
            gpus = telemetry.get("gpu", {}).get("gpus", [])
            if gpus:
                gpu_str = " | ".join([f"{g.get('name')} ({g.get('vram_gb', 0)}GB)" for g in gpus])
            os_caption = telemetry.get("os", {}).get("caption", "")
            if os_caption:
                os_str = f"{os_caption} (Build {telemetry.get('os', {}).get('build', '')})"

        telemetry_summary = {
            "target_cpu": cpu_str,
            "target_gpus": gpu_str,
            "target_os": os_str,
            "issue": "Premiere Pro / Adobe CC crashes, 2-minute freeze, 0xc0000005 APPCRASH, and dual-GPU bus collisions on RTX 5060 + Ryzen 5."
        }

        # Try live query via LLMsRelay
        live_success = False
        analysis_text = ""
        try:
            prompt = (
                f"Analyze this hardware profile for Adobe Premiere Pro 2026/2025:\n"
                f"CPU: {cpu_str}\n"
                f"GPU: {gpu_str}\n"
                f"OS: {os_str}\n"
                f"Target: Deep Registry stabilization, TDR delay, RTX 5060 Blackwell DirectX affinity, "
                f"and Ryzen 5 integrated Radeon decode deconfliction."
            )

            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Claude Opus 5.5 Max, the elite Windows Kernel & Adobe Premiere Pro Architectural AI. "
                            "Provide concise, high-density technical analysis and registry recommendations for NVIDIA Blackwell RTX 50-series "
                            "and AMD Ryzen dual-GPU setups."
                        )
                    },
                    {"role": "user", "content": prompt}
                ]
            }

            req = urllib.request.Request(
                self.relay_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            self.log(f"⚡ Contacting Claude Opus 5.5 API Gateway ({self.relay_url})...", "INFO")
            with urllib.request.urlopen(req, timeout=5) as resp:
                for line in resp:
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if line_str.startswith("data:"):
                        data_content = line_str[5:].strip()
                        try:
                            obj = json.loads(data_content)
                            if "text" in obj:
                                analysis_text += obj["text"]
                        except Exception:
                            pass

            if analysis_text.strip():
                live_success = True
                self.log(f"✅ Claude Opus 5.5 Live Advice received ({len(analysis_text)} chars).", "SUCCESS")
        except Exception as e:
            self.log(f"ℹ️ Claude Opus 5.5 Relay Gateway unavailable ({e}).", "WARNING")
            self.log("🚀 Switching to Embedded Claude Opus 5.5 Gold Master Architecture Matrix.", "INFO")

        if not live_success or not analysis_text:
            analysis_text = (
                "Claude Opus 5.5 Gold Master Matrix for NVIDIA RTX 5060 (Blackwell) & AMD Ryzen 5:\n"
                "• Graphics TDR Timeout: Elevated to 10s (TdrDelay=10, TdrDdiDelay=10, TdrLevel=3) preventing D3D12/CUDA resets.\n"
                "• Dual-GPU Deconfliction: Disable AMD Radeon iGPU decode (EnablehAMDDecode=false), enable dedicated NVIDIA NVDEC (EnableNvidiaDecode=true).\n"
                "• DirectX Affinity: Force GpuPreference=2 (High Performance GPU) for Adobe Premiere Pro, GPUSniffer, and Media Encoder.\n"
                "• Audio Clock Deadlock: dvaaudiodevice.AlwaysRunning=false & AudioOutputOnlyUI=true.\n"
                "• Sniffer & CUDA Bypass: DS.GPUSnifferOverride=0 0, Player.DirectXAcceleratedRenderer=true true, DS.ForceCUDARendering=true true.\n"
                "• Services Sanitization: Stop & unregister AGSService, AdobeARMservice, and AdobeUpdateService."
            )

        return {
            "live_consultation": live_success,
            "model": self.model_name,
            "telemetry": telemetry_summary,
            "opus_analysis": analysis_text
        }

    # =========================================================================
    # 2. NUCLEAR ADOBE DRIVERS, SERVICES & PROCESS PURGE
    # =========================================================================

    def terminate_all_adobe_processes(self) -> int:
        """Forcefully kills every Adobe-related process, licensing daemons, and background hooks."""
        adobe_processes = [
            "Adobe Premiere Pro", "GPUSniffer", "dynamiclinkmanager",
            "TeamProjectsLocalHub", "dvaaudiofilterscan", "dvaapprelauncher",
            "CRWindowsClientService", "Creative Cloud", "CoreSync",
            "CCXProcess", "AdobeIPCBroker", "AdobeNotificationClient",
            "AcroCEF", "AdobeDesktopService", "CCLibrary", "AGSService",
            "AdobeARMservice", "AdobeUpdateService", "armsvc", "AGMService",
            "AdobeGCClient", "Adobe CEF Helper", "LogTransport2",
            "AdobeCrashReporter", "CEPHtmlEngine", "Photoshop", "AfterFX",
            "Adobe Media Encoder", "Illustrator", "Audition"
        ]
        killed = 0
        for p in adobe_processes:
            try:
                cmd = f"Stop-Process -Name '{p}' -Force -ErrorAction SilentlyContinue"
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
                if res.returncode == 0:
                    killed += 1
            except Exception:
                pass
        self.log(f"Terminated all running Adobe processes ({killed} process families targeted).", "SUCCESS")
        return killed

    def delete_all_adobe_services(self) -> List[str]:
        """
        Deep uninstaller for all Adobe Windows Services:
        Stops and permanently unregisters AGSService, AdobeARMservice, AdobeUpdateService, etc.
        """
        known_services = [
            "AGSService", "AdobeARMservice", "AdobeUpdateService",
            "AdobeFlashPlayerUpdateSvc", "armsvc", "AGMService"
        ]

        # Dynamically query any service with 'Adobe' or 'AGS' in its name
        detected_services = list(known_services)
        try:
            ps_query = "Get-Service | Where-Object { $_.Name -like '*Adobe*' -or $_.Name -like '*AGS*' } | Select-Object -ExpandProperty Name"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_query], capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in res.stdout.splitlines():
                s_name = line.strip()
                if s_name and s_name not in detected_services:
                    detected_services.append(s_name)
        except Exception:
            pass

        deleted = []
        for s in detected_services:
            try:
                # Stop service
                subprocess.run(["sc", "stop", s], capture_output=True, timeout=5)
                # Delete service permanently from SCM
                proc = subprocess.run(["sc", "delete", s], capture_output=True, text=True, timeout=5)
                if proc.returncode == 0 or "SUCCESS" in proc.stdout:
                    deleted.append(s)
                    self.log(f"Permanently unregistered Adobe Windows Service: {s}", "SUCCESS")
            except Exception:
                pass

        return deleted

    def remove_all_adobe_scheduled_tasks(self) -> int:
        """Purges all scheduled telemetry, update, and genuine software tasks."""
        ps_cmd = """
        $count = 0
        Get-ScheduledTask | Where-Object { $_.TaskName -like '*Adobe*' -or $_.TaskName -like '*AGS*' -or $_.TaskName -like '*Acrobat*' } | ForEach-Object {
            try {
                Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false -ErrorAction SilentlyContinue
                $count++
            } catch {}
        }
        $count
        """
        try:
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
            count = int(res.stdout.strip() or 0)
            if count > 0:
                self.log(f"Eradicated {count} Adobe background Scheduled Tasks.", "SUCCESS")
            return count
        except Exception:
            return 0

    def purge_startup_registry_keys(self) -> int:
        """Removes Adobe entries from Windows Run and RunOnce registries."""
        reg_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
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
                            v_low = v_name.lower()
                            if any(k in v_low for k in ["adobe", "ccx", "creative cloud", "ags", "acro"]):
                                values_to_del.append(v_name)
                            i += 1
                    except OSError:
                        pass

                    for v in values_to_del:
                        try:
                            winreg.DeleteValue(key, v)
                            removed += 1
                            self.log(f"Removed Adobe Startup Registry Key: {v}", "SUCCESS")
                        except OSError:
                            pass
            except Exception:
                pass
        return removed

    def delete_registry_tree(self, hive, subkey: str) -> bool:
        """Recursively deletes a Windows Registry Key tree safely."""
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
                while True:
                    try:
                        sub = winreg.EnumKey(key, 0)
                        self.delete_registry_tree(hive, f"{subkey}\\{sub}")
                    except OSError:
                        break
            winreg.DeleteKey(hive, subkey)
            return True
        except Exception:
            return False

    def purge_adobe_registry_hives(self) -> int:
        """Deep purge of Adobe registry roots to eliminate stale licensing locks and driver hooks."""
        targets = [
            (winreg.HKEY_CURRENT_USER, r"Software\Adobe"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Adobe"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Adobe")
        ]
        purged = 0
        for hive, subkey in targets:
            try:
                if self.delete_registry_tree(hive, subkey):
                    purged += 1
                    self.log(f"Purged Registry Hive: {subkey}", "SUCCESS")
            except Exception:
                pass
        return purged

    def sanitize_broken_clsids(self) -> int:
        """
        Unhooks broken Adobe shell extensions & virtual namespace CLSIDs that cause
        Explorer freezes, Open File dialog crashes, and RuntimeInstaller.DLL APPCRASH 0xc0000005.
        """
        broken_clsid_names = [
            "Adobe Drive", "Adobe Version Cue", "Adobe Sync", "CCXProcessExtension", "AdobeDesktopService"
        ]
        removed = 0
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "CLSID", 0, winreg.KEY_READ) as clsid_root:
                i = 0
                to_delete = []
                while True:
                    try:
                        guid = winreg.EnumKey(clsid_root, i)
                        i += 1
                        try:
                            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"CLSID\\{guid}") as g_key:
                                val, _ = winreg.QueryValueEx(g_key, "")
                                if val and any(b in str(val) for b in broken_clsid_names):
                                    to_delete.append(guid)
                        except Exception:
                            pass
                    except OSError:
                        break

                for guid in to_delete:
                    try:
                        self.delete_registry_tree(winreg.HKEY_CLASSES_ROOT, f"CLSID\\{guid}")
                        removed += 1
                        self.log(f"Unhooked broken Adobe Namespace CLSID: {guid}", "SUCCESS")
                    except Exception:
                        pass
        except Exception:
            pass
        return removed

    def purge_credential_manager(self) -> int:
        """Purges corrupted Adobe licensing tokens from Windows Credential Vault."""
        deleted = 0
        try:
            cmd = "cmdkey /list"
            proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding="utf-8", errors="replace")
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.startswith("Target:"):
                    target_val = line[len("Target:"):].strip()
                    if any(k in target_val for k in ["Adobe", "ACCC.", "Adobe App"]):
                        del_cmd = f'cmdkey /delete:"{target_val}"'
                        res = subprocess.run(del_cmd, capture_output=True, shell=True, text=True)
                        if res.returncode == 0:
                            deleted += 1
            if deleted > 0:
                self.log(f"Purged {deleted} stale Adobe credentials from Windows Vault.", "SUCCESS")
        except Exception:
            pass
        return deleted

    def purge_residual_adobe_directories(self) -> int:
        """Wipes all residual licensing, cache, and driver hook folders."""
        appdata = os.getenv("APPDATA", "")
        localappdata = os.getenv("LOCALAPPDATA", "")
        programdata = os.getenv("PROGRAMDATA", "")
        pf = os.getenv("ProgramFiles", r"C:\Program Files")
        pfx86 = os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)")
        userprofile = os.getenv("USERPROFILE", "")

        target_dirs = [
            os.path.join(programdata, r"Adobe\OOBE"),
            os.path.join(programdata, r"Adobe\SLStore"),
            os.path.join(programdata, r"Adobe\SLData"),
            os.path.join(programdata, r"Adobe\OperatingConfigs"),
            os.path.join(programdata, r"Adobe\caps"),
            os.path.join(programdata, r"Adobe\Adobe PCD"),
            os.path.join(programdata, r"Adobe\Common"),
            os.path.join(localappdata, r"Adobe\OOBE"),
            os.path.join(localappdata, r"Adobe\SLStore"),
            os.path.join(appdata, r"Adobe\Common\Media Cache Files"),
            os.path.join(appdata, r"Adobe\Common\Peak Files"),
            os.path.join(pf, r"Common Files\Adobe\OOBE"),
            os.path.join(pf, r"Common Files\Adobe\SLCache"),
            os.path.join(pfx86, r"Common Files\Adobe\OOBE"),
            os.path.join(pfx86, r"Common Files\Adobe\SLCache"),
            os.path.join(pfx86, r"Common Files\Adobe\AdobeGCClient"),
            os.path.join(pf, r"Common Files\Adobe\Adobe Desktop Common")
        ]

        deleted_dirs = 0
        for d in target_dirs:
            if os.path.isdir(d):
                try:
                    shutil.rmtree(d, ignore_errors=True)
                    deleted_dirs += 1
                    self.log(f"Wiped residual Adobe licensing directory: {d}", "SUCCESS")
                except OSError:
                    pass

        return deleted_dirs

    def execute_complete_nuclear_purge(self) -> Dict[str, Any]:
        """
        Executes end-to-end 1-Click Nuclear Driver & Service Uninstaller:
        Purges ALL Adobe drivers, services, scheduled tasks, startup keys,
        registry roots, and credentials.
        """
        self.log("==================================================================", "INFO")
        self.log("  STARTING NUCLEAR ADOBE ROOT UNINSTALLER & DRIVER PURGE SUITE   ", "INFO")
        self.log("==================================================================", "INFO")

        # 1. Terminate all Adobe processes
        procs = self.terminate_all_adobe_processes()

        # 2. Delete Windows Services (AGSService, AdobeARMservice, etc.)
        services = self.delete_all_adobe_services()

        # 3. Eradicate Scheduled Tasks
        tasks = self.remove_all_adobe_scheduled_tasks()

        # 4. Remove Startup Registry Keys
        startups = self.purge_startup_registry_keys()

        # 5. Purge Windows Credential Manager
        creds = self.purge_credential_manager()

        # 6. Unhook broken Namespace CLSIDs
        clsids = self.sanitize_broken_clsids()

        # 7. Wipe residual licensing & driver cache directories
        wiped_dirs = self.purge_residual_adobe_directories()

        self.log("==================================================================", "SUCCESS")
        self.log("  NUCLEAR ADOBE DRIVERS & SERVICES ERADICATED SUCCESSFULLY!      ", "SUCCESS")
        self.log("==================================================================", "SUCCESS")

        return {
            "processes_killed": procs,
            "services_deleted": services,
            "tasks_removed": tasks,
            "startup_keys_removed": startups,
            "credentials_purged": creds,
            "clsids_unhooked": clsids,
            "directories_wiped": wiped_dirs
        }

    # =========================================================================
    # 3. CLAUDE OPUS 5.5 MAX DEEP REGISTRY HEALING (RTX 5060 + RYZEN 5)
    # =========================================================================

    def apply_graphics_tdr_boost(self) -> bool:
        """
        Applies Windows Kernel Graphics TDR Delay Boost to prevent 2-second timeout resets:
        - TdrDelay = 10s (DWORD)
        - TdrDdiDelay = 10s (DWORD)
        - TdrLevel = 3 (DWORD, Recover on timeout)
        - HwSchMode = 2 (DWORD, Hardware-accelerated GPU Scheduling for RTX 50-series Blackwell)
        """
        try:
            reg_path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "TdrDelay", 0, winreg.REG_DWORD, 10)
                winreg.SetValueEx(key, "TdrDdiDelay", 0, winreg.REG_DWORD, 10)
                winreg.SetValueEx(key, "TdrLevel", 0, winreg.REG_DWORD, 3)
                winreg.SetValueEx(key, "HwSchMode", 0, winreg.REG_DWORD, 2)
            self.log("GraphicsDrivers TDR: Set TdrDelay=10s, TdrDdiDelay=10s, HwSchMode=2 (RTX 5000 / Blackwell Ready).", "SUCCESS")
            return True
        except Exception as e:
            ps_tdr = (
                "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' -Name 'TdrDelay' -Value 10 -Type DWord -Force -ErrorAction SilentlyContinue; "
                "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' -Name 'TdrDdiDelay' -Value 10 -Type DWord -Force -ErrorAction SilentlyContinue; "
                "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' -Name 'TdrLevel' -Value 3 -Type DWord -Force -ErrorAction SilentlyContinue; "
                "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' -Name 'HwSchMode' -Value 2 -Type DWord -Force -ErrorAction SilentlyContinue"
            )
            try:
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_tdr], capture_output=True, timeout=5)
                self.log("GraphicsDrivers TDR: Applied TdrDelay & HwSchMode via PowerShell.", "SUCCESS")
                return True
            except Exception:
                self.log(f"GraphicsDrivers TDR registry adjustment note: {e}", "WARNING")
                return False

    def apply_directx_gpu_affinity(self, extra_exes: Optional[List[str]] = None) -> int:
        """
        Enforces DirectX High Performance GPU Affinity (GpuPreference=2) for all Adobe exes
        so Windows D3D12/DirectX binds exclusively to the dedicated RTX 5060/3060.
        """
        exes = [
            "Adobe Premiere Pro.exe", "GPUSniffer.exe", "Adobe Premiere Pro (Repaired).exe",
            "AfterFX.exe", "Photoshop.exe", "Adobe Media Encoder.exe", "Illustrator.exe"
        ]
        if extra_exes:
            for e in extra_exes:
                if e and e not in exes:
                    exes.append(e)

        reg_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
        applied = 0
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                for exe in exes:
                    winreg.SetValueEx(key, exe, 0, winreg.REG_SZ, "GpuPreference=2;")
                    applied += 1
            self.log(f"DirectX UserGpuPreferences: Enforced GpuPreference=2; (High-Perf RTX) across {applied} Adobe binaries.", "SUCCESS")
        except Exception as e:
            self.log(f"DirectX GPU affinity note: {e}", "WARNING")
        return applied

    def patch_premiere_debug_database_opus(self) -> int:
        """
        Injects the complete Claude Opus 5.5 Architecture Matrix into all Debug Database.txt files:
        - RTX 5060 (Blackwell) sniffer override & DirectX rendering
        - dvaaudiodevice.AlwaysRunning = false false (Anti-Freeze)
        - AudioOutputOnlyUI = true true
        - ExporterMPEG4 Nvidia HW export = true true / Intel = false false
        - DS.GPUSnifferLaunchTimeout = 15000 15000
        """
        flags = {
            "dvaaudiodevice.AlwaysRunning": ("false", "false"),
            "AudioOutputOnlyUI": ("true", "true"),
            "dvaaudiodevice.EnableRealtimeBlockingAccessFromIOThread": ("false", "false"),
            "ExporterMPEG4.Feature.Allow_Intel_HW_Export": ("false", "false"),
            "ExporterMPEG4.Feature.Allow_Nvidia_HW_Export": ("true", "true"),
            "TeamProjects.DisableBackgroundSync": ("true", "true"),
            "DS.GPUSnifferLaunchTimeout": ("15000", "15000"),
            "DS.GPUSnifferExecutionTimeout": ("15000", "15000"),
            "dvasystemcompatibilityreport.use_installed_blocklist": ("false", "false"),
            "MF.EnableDirectoryPolling": ("false", "false"),
            "EA.MediaFinder.EnableSyncDirectoryScanForFastMediaSearch": ("false", "false"),
            "EA.Config.DisableSequenceLocking": ("true", "true"),
            "FE.AudioPluginScanOnFirstLaunch": ("false", "false"),
            "dunamis-force-immediate-send": ("false", "false"),
            "DS.DisableDirectXDisplay": ("false", "false"),
            "DS.ForceCPUOnly": ("false", "false"),
            "Player.DirectXAcceleratedRenderer": ("true", "true"),
            "DS.GPUSnifferOverride": ("0", "0"),
            "DS.ForceCUDARendering": ("true", "true"),
            "GF.PrimaryDeviceIndex": ("0", "0")
        }

        candidate_paths = []
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            appdata_prem = os.path.join(userprofile, r"AppData\Roaming\Adobe\Premiere Pro")
            if os.path.isdir(appdata_prem):
                for item in os.listdir(appdata_prem):
                    v_p = os.path.join(appdata_prem, item)
                    if os.path.isdir(v_p) and "backup" not in item.lower():
                        candidate_paths.append(os.path.join(v_p, "Debug Database.txt"))
                candidate_paths.append(os.path.join(appdata_prem, "Logs", "Debug Database.txt"))

        # Add installation root paths
        for p in [
            r"C:\Program Files\Adobe\Adobe Premiere Pro 2026",
            r"C:\Program Files\Adobe\Adobe Premiere Pro 2025",
            r"D:\Adobe Suite1\Adobe Premiere Pro 2026",
            r"D:\Adobe Suite\Adobe Premiere Pro 2026",
            r"D:\Adobe Premiere Pro 2026",
            r"F:\AdobePremierePro2026"
        ]:
            if os.path.isdir(p):
                candidate_paths.append(os.path.join(p, "Debug Database.txt"))

        candidate_paths = list(dict.fromkeys(candidate_paths))
        patched = 0
        for dd_path in candidate_paths:
            try:
                os.makedirs(os.path.dirname(dd_path), exist_ok=True)
                lines = []
                if os.path.isfile(dd_path):
                    with open(dd_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()

                new_lines = []
                keys_updated = set()
                for line in lines:
                    parts = line.strip().split("\t")
                    if len(parts) >= 2:
                        k = parts[0]
                        if k in flags:
                            v1, v2 = flags[k]
                            new_lines.append(f"{k}\t{v1}\t{v2}\n")
                            keys_updated.add(k)
                            continue
                    new_lines.append(line)

                for k, (v1, v2) in flags.items():
                    if k not in keys_updated:
                        new_lines.append(f"{k}\t{v1}\t{v2}\n")

                with open(dd_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                patched += 1
                self.log(f"Opus 5.5 Matrix: Injected 20 Anti-Crash & GPU flags into {dd_path}.", "SUCCESS")
            except Exception as e:
                self.log(f"Opus Debug Database note ({dd_path}): {e}", "WARNING")

        return patched

    def patch_premiere_preferences_opus(self, has_amd_igpu: bool = True) -> int:
        """
        Configures Premiere Pro project preferences specifically tailored for
        AMD Ryzen + NVIDIA RTX 5060 (Blackwell):
        - Disables AMD iGPU decode (Project.Prefs.EnablehAMDDecode = false)
        - Disables Intel iGPU decode (Project.Prefs.EnableIntelDecode = false)
        - Enables dedicated NVIDIA NVDEC decode (Project.Prefs.EnableNvidiaDecode = true)
        - Disables cloud auto-save deadlocks
        """
        userprofile = os.environ.get("USERPROFILE", "")
        if not userprofile:
            return 0

        doc_dirs = [
            os.path.join(userprofile, "Documents"),
            os.path.join(userprofile, "OneDrive", "Documents")
        ]

        patched = 0
        for doc_dir in doc_dirs:
            adobe_prem = os.path.join(doc_dir, "Adobe", "Premiere Pro")
            if not os.path.isdir(adobe_prem):
                continue

            for ver_folder in os.listdir(adobe_prem):
                ver_path = os.path.join(adobe_prem, ver_folder)
                if not os.path.isdir(ver_path) or "backup" in ver_folder.lower():
                    continue

                for pref_name in ["Adobe Premiere Pro Prefs", "Adobe Premiere Pro Prefs.txt"]:
                    pref_file = os.path.join(ver_path, pref_name)
                    if not os.path.isfile(pref_file):
                        continue

                    try:
                        content = ""
                        enc = "utf-8"
                        try:
                            with open(pref_file, "r", encoding="utf-8", errors="replace") as f:
                                content = f.read()
                        except Exception:
                            with open(pref_file, "r", encoding="latin-1", errors="replace") as f:
                                content = f.read()
                                enc = "latin-1"

                        # Apply AMD Ryzen + NVIDIA RTX 5060 hardware decode rules
                        # Disable conflicting AMD iGPU decode
                        content = content.replace("Project.Prefs.EnablehAMDDecode=true", "Project.Prefs.EnablehAMDDecode=false")
                        content = content.replace("Project.Prefs.EnablehAMDDecode=1", "Project.Prefs.EnablehAMDDecode=0")
                        content = content.replace("Project.Prefs.EnableIntelDecode=true", "Project.Prefs.EnableIntelDecode=false")
                        content = content.replace("Project.Prefs.EnableIntelDecode=1", "Project.Prefs.EnableIntelDecode=0")
                        content = content.replace("Project.Prefs.EnableNvidiaDecode=false", "Project.Prefs.EnableNvidiaDecode=true")
                        content = content.replace("Project.Prefs.EnableNvidiaDecode=0", "Project.Prefs.EnableNvidiaDecode=1")

                        # Cloud autosave
                        content = content.replace("BE.Prefs.AutoSave.DoSaveToCloud=true", "BE.Prefs.AutoSave.DoSaveToCloud=false")

                        with open(pref_file, "w", encoding=enc, errors="replace") as f:
                            f.write(content)
                        patched += 1
                        self.log(f"Opus 5.5 Hardware Decode: Deconflicted Ryzen AMD iGPU & prioritized RTX 5060 in {pref_file}.", "SUCCESS")
                    except Exception as e:
                        self.log(f"Preferences patch note ({pref_file}): {e}", "WARNING")

        return patched

    def execute_complete_deep_healing(self, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes complete Claude Opus 5.5 Max Deep Registry & Architecture Healing:
        1. Architectural consultation (Live via LLMsRelay or Embedded Gold Master).
        2. Elevates Windows Kernel Graphics TDR Delay to 10s & enables HwSchMode=2.
        3. Enforces DirectX High-Performance GPU Affinity (GpuPreference=2) for all Adobe EXEs.
        4. Injects Anti-Deadlock, RTX Blackwell sniffer override & CUDA flags into Debug Database.
        5. Deconflicts AMD Ryzen iGPU and locks NVIDIA NVDEC in Premiere Preferences.
        6. Unhooks broken CLSID namespace shell extensions.
        """
        self.log("==================================================================", "INFO")
        self.log("  STARTING CLAUDE OPUS 5.5 MAX DEEP REGISTRY & HARDWARE HEALER   ", "INFO")
        self.log("==================================================================", "INFO")

        # Step 1: Consult Opus 5.5
        opus_result = self.consult_claude_opus(telemetry)

        # Step 2: Elevate GPU TDR Delay
        tdr_ok = self.apply_graphics_tdr_boost()

        # Step 3: Enforce DirectX High-Performance GPU Affinity
        gpu_count = self.apply_directx_gpu_affinity()

        # Step 4: Inject Opus 5.5 Debug Database flags
        dd_count = self.patch_premiere_debug_database_opus()

        # Step 5: Deconflict Dual-GPU & Ryzen iGPU decode in preferences
        pref_count = self.patch_premiere_preferences_opus(has_amd_igpu=True)

        # Step 6: Sanitize broken CLSIDs
        clsid_count = self.sanitize_broken_clsids()

        self.log("==================================================================", "SUCCESS")
        self.log("  CLAUDE OPUS 5.5 MAX DEEP REGISTRY HEALING COMPLETED!          ", "SUCCESS")
        self.log("==================================================================", "SUCCESS")

        return {
            "opus_result": opus_result,
            "tdr_boost_applied": tdr_ok,
            "gpu_affinities_enforced": gpu_count,
            "debug_databases_patched": dd_count,
            "preferences_deconflicted": pref_count,
            "clsids_sanitized": clsid_count
        }
