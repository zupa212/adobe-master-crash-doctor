import os
import sys
import json
import time
import shutil
import urllib.request
import urllib.parse
import subprocess
from typing import Dict, Any, Optional, Callable

CURRENT_VERSION = "1.2.4"
CURRENT_BUILD = 124
PRIMARY_OTA_URL = "https://premiere-pro-doctor.vercel.app/api/version"
TELEMETRY_URL = "https://premiere-pro-doctor.vercel.app/api/ota-telemetry"
FALLBACK_MANIFEST_URL = "https://raw.githubusercontent.com/zupa212/adobe-master-crash-doctor/main/version.json"
REPO_API_URL = "https://api.github.com/repos/zupa212/adobe-master-crash-doctor/releases/latest"
REPO_URL = "https://github.com/zupa212/adobe-master-crash-doctor"

class OTAUpdateEngine:
    def __init__(self, logger=None):
        self.logger = logger
        self.current_version = CURRENT_VERSION
        self.current_build = CURRENT_BUILD

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}", flush=True)

    def send_telemetry(self, action: str, extra: Optional[Dict[str, Any]] = None):
        """Sends telemetry ping to Vercel so activity is recorded live in Vercel Dashboard logs."""
        try:
            payload = {
                "action": action,
                "user": os.environ.get("USERNAME", "Creator"),
                "client_version": self.current_version,
                "client_build": self.current_build,
                "target_version": CURRENT_VERSION,
                "os": f"Windows {os.environ.get('PROCESSOR_ARCHITECTURE', 'x64')}"
            }
            if extra:
                payload.update(extra)

            url = f"{TELEMETRY_URL}?t={int(time.time())}"
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "AdobeMasterCrashDoctor-OTA"}
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass

    def check_for_updates(self, hardware_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Polls Vercel / GitHub for OTA manifest or latest release.
        Includes hardware telemetry in request to populate Vercel Dashboard logs.
        """
        self.log("OTA Engine: Checking for live updates...", "INFO")
        manifest_data = None

        user = os.environ.get("USERNAME", "Creator")
        gpu_name = "NVIDIA / Dedicated GPU"
        cpu_name = "Multi-Core CPU"
        if hardware_profile:
            gpu_name = hardware_profile.get("gpu", {}).get("primary_dgpu", gpu_name)
            cpu_name = hardware_profile.get("cpu", {}).get("name", cpu_name)

        params = urllib.parse.urlencode({
            "client_version": self.current_version,
            "build": self.current_build,
            "user": user,
            "gpu": gpu_name[:40],
            "cpu": cpu_name[:40],
            "nocache": int(time.time())
        })

        # 1. Primary: Vercel Serverless Function (Provides rich Vercel Dashboard logging)
        try:
            req = urllib.request.Request(
                f"{PRIMARY_OTA_URL}?{params}",
                headers={"User-Agent": f"AdobeMasterCrashDoctor-OTA/{self.current_version}"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    manifest_data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            self.log(f"Vercel OTA Note: {e}. Falling back to GitHub raw manifest...", "DEBUG")

        # 2. Fallback: GitHub raw manifest file (version.json)
        if not manifest_data:
            try:
                req = urllib.request.Request(
                    FALLBACK_MANIFEST_URL + f"?nocache={int(time.time())}",
                    headers={"User-Agent": "AdobeMasterCrashDoctor-OTA"}
                )
                with urllib.request.urlopen(req, timeout=6) as response:
                    if response.status == 200:
                        manifest_data = json.loads(response.read().decode("utf-8"))
            except Exception as e:
                self.log(f"GitHub OTA Note: {e}. Falling back to GitHub Releases API...", "DEBUG")

        # 3. Fallback: GitHub Releases API
        if not manifest_data:
            try:
                req = urllib.request.Request(
                    REPO_API_URL,
                    headers={"User-Agent": "AdobeMasterCrashDoctor-OTA"}
                )
                with urllib.request.urlopen(req, timeout=6) as response:
                    if response.status == 200:
                        rel = json.loads(response.read().decode("utf-8"))
                        tag = rel.get("tag_name", "").lstrip("v")
                        dl_url = None
                        for asset in rel.get("assets", []):
                            if asset.get("name", "").endswith(".exe"):
                                dl_url = asset.get("browser_download_url")
                                break
                        if not dl_url:
                            dl_url = "https://github.com/zupa212/adobe-master-crash-doctor/raw/main/Adobe%20Master%20Crash%20Doctor.exe"

                        manifest_data = {
                            "version": tag or "1.2.4",
                            "build_number": 124,
                            "release_date": rel.get("published_at", "")[:10],
                            "download_url": dl_url,
                            "changelog": [rel.get("body", "General performance and repair updates.")]
                        }
            except Exception as e:
                self.log(f"OTA GitHub API Note: {e}", "WARNING")

        if not manifest_data:
            return {
                "update_available": False,
                "current_version": self.current_version,
                "latest_version": self.current_version,
                "error": "Could not connect to OTA server."
            }

        remote_ver_str = str(manifest_data.get("version", self.current_version))
        remote_build = int(manifest_data.get("build_number", 0))

        # Version comparison
        def parse_v(v_str):
            parts = []
            for p in v_str.replace("v", "").split("."):
                if p.isdigit():
                    parts.append(int(p))
            return parts

        local_parts = parse_v(self.current_version)
        remote_parts = parse_v(remote_ver_str)

        update_available = (remote_parts > local_parts) or (remote_build > self.current_build)

        result = {
            "update_available": update_available,
            "current_version": self.current_version,
            "latest_version": remote_ver_str,
            "release_date": manifest_data.get("release_date", "Today"),
            "download_url": manifest_data.get("download_url", "https://github.com/zupa212/adobe-master-crash-doctor/raw/main/Adobe%20Master%20Crash%20Doctor.exe"),
            "changelog": manifest_data.get("changelog", []),
            "manifest": manifest_data
        }

        if update_available:
            self.log(f"OTA Engine: New version detected! Available: v{remote_ver_str} (Current: v{self.current_version}).", "SUCCESS")
        else:
            self.log(f"OTA Engine: Application is up to date (v{self.current_version}).", "SUCCESS")

        return result

    def download_update(
        self,
        download_url: str,
        progress_callback: Optional[Callable[[float, int, int], None]] = None
    ) -> str:
        """
        Downloads the latest executable from GitHub/Vercel with real-time streaming progress.
        Notifies Vercel telemetry live so dashboard registers download start & completion.
        """
        temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
        dest_path = os.path.join(temp_dir, f"Adobe_Master_Crash_Doctor_vUpdate_{int(time.time())}.exe")

        self.log(f"OTA Engine: Initiating download from: {download_url}", "INFO")

        # Telemetry: download started
        self.send_telemetry("download_started", {"target_url": download_url})

        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": f"AdobeMasterCrashDoctor-OTA/{self.current_version}"}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64KB chunks

            with open(dest_path, "wb") as f_out:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_callback:
                        percent = round((downloaded / total_size) * 100, 1)
                        progress_callback(percent, downloaded, total_size)

        # Integrity verification
        if not os.path.isfile(dest_path):
            raise RuntimeError("Downloaded file does not exist on disk.")

        file_size = os.path.getsize(dest_path)
        if file_size < 5 * 1024 * 1024:
            raise RuntimeError(f"Downloaded file size too small ({round(file_size/(1024*1024), 2)} MB). Download may be corrupted.")

        # Check PE signature (MZ header)
        with open(dest_path, "rb") as f_check:
            magic = f_check.read(2)
            if magic != b"MZ":
                raise RuntimeError("Downloaded file is not a valid Windows executable (Missing MZ header).")

        # Telemetry: download completed
        self.send_telemetry("download_completed", {
            "target_url": download_url,
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        })

        self.log(f"OTA Engine: Download verified successfully ({round(file_size / (1024*1024), 2)} MB).", "SUCCESS")
        return dest_path

    def apply_update_and_restart(self, new_exe_path: str, target_exe_path: Optional[str] = None) -> bool:
        """
        Safely swaps the running executable with the new version and relaunches the application.
        Works seamlessly on Windows using a detached launcher script.
        """
        # Telemetry: update applied
        self.send_telemetry("update_applied", {"new_exe": new_exe_path})

        if not target_exe_path:
            if getattr(sys, "frozen", False):
                target_exe_path = sys.executable
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                target_exe_path = os.path.join(base_dir, "Adobe Master Crash Doctor.exe")
                target_exe_path = os.path.join(base_dir, "Adobe Master Crash Doctor.exe")

        current_pid = os.getpid()
        temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
        batch_script_path = os.path.join(temp_dir, f"ota_patcher_{int(time.time())}.bat")

        bat_content = f"""@echo off
setlocal
title Adobe Master Crash Doctor OTA Updater
echo [*] Applying Over-The-Air Update...
echo [*] Waiting for process PID {current_pid} to close...

:WAIT_LOOP
tasklist /fi "PID eq {current_pid}" 2>nul | find "{current_pid}" >nul
if %ERRORLEVEL% equ 0 (
    timeout /t 1 /nobreak >nul
    goto WAIT_LOOP
)

echo [*] Replacing binary with new OTA version...
copy /y "{new_exe_path}" "{target_exe_path}" >nul
if %ERRORLEVEL% neq 0 (
    move /y "{target_exe_path}" "{target_exe_path}.old" >nul
    copy /y "{new_exe_path}" "{target_exe_path}" >nul
)

:: Also update Desktop copy if target is not on Desktop
set DESKTOP_EXE=%USERPROFILE%\\Desktop\\Adobe Master Crash Doctor.exe
if exist "%DESKTOP_EXE%" (
    copy /y "{new_exe_path}" "%DESKTOP_EXE%" >nul
)

:: Cleanup
del "{new_exe_path}" 2>nul

echo [*] Relaunching Adobe Master Crash Doctor...
start "" "{target_exe_path}"

:: Self delete this batch script
del "%~f0" 2>nul
exit
"""
        try:
            with open(batch_script_path, "w", encoding="utf-8") as f_bat:
                f_bat.write(bat_content)

            self.log(f"OTA Engine: Spawning background updater process: {batch_script_path}", "INFO")

            # Spawn detached batch script
            subprocess.Popen(
                ["cmd.exe", "/c", batch_script_path],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
            return True
        except Exception as e:
            self.log(f"Error initiating OTA restart: {e}", "ERROR")
            return False
