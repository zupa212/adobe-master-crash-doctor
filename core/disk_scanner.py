import os
import sys
import subprocess
import string
from pathlib import Path
from typing import List, Dict, Any
from core.adobe_catalog import ADOBE_APPS_CATALOG, get_all_target_exe_names, identify_adobe_app_by_path

class MultiDiskScanner:
    def __init__(self, logger=None):
        self.logger = logger
        self.target_exe_names = {x.lower(): x for x in get_all_target_exe_names()}

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}")

    def is_ascii(self, text: str) -> bool:
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def get_all_logical_drives(self) -> List[str]:
        """Dynamically retrieves all active filesystem drives on Windows (C:, D:, F:, etc.)."""
        drives = []
        try:
            ps_cmd = "Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name.Length -eq 1 } | Select-Object -ExpandProperty Root"
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if line and os.path.exists(line) and len(line) <= 3:
                    drives.append(line)
        except Exception:
            # Fallback drive letter iteration
            for letter in string.ascii_uppercase:
                root = f"{letter}:\\"
                if os.path.exists(root):
                    drives.append(root)

        return drives

    def deep_scan_all_drives_for_premiere(self) -> List[Dict[str, Any]]:
        """Deep scans all drives for Premiere Pro installations."""
        all_apps = self.deep_scan_all_drives_for_all_adobe_apps()
        return [a for a in all_apps if "premiere" in a.get("exe_path", "").lower()]

    def deep_scan_all_drives_for_all_adobe_apps(self) -> List[Dict[str, Any]]:
        """
        Deep scans all active drives for ALL Adobe suite applications:
        Premiere Pro, Photoshop, After Effects, Illustrator, Media Encoder,
        Audition, Lightroom, InDesign, Acrobat DC, Substance 3D, Character Animator.
        """
        drives = self.get_all_logical_drives()
        found_exes = []
        self.log(f"Multi-Disk Scanner: Scanning {len(drives)} active drives ({', '.join(drives)}) for all Adobe apps...", "INFO")

        # High-probability folders per drive
        subdirs_to_check = [
            r"Program Files\Adobe",
            r"Program Files (x86)\Adobe",
            r"Adobe",
            r"Adobe Premiere Pro",
            r"AdobePremierePro",
            r"Apps\Adobe",
            r"Software\Adobe",
            r"Portable\Adobe",
            r"ProgramData\Adobe"
        ]

        for d in drives:
            # 1. Check known directories
            for sub in subdirs_to_check:
                target_p = os.path.join(d, sub)
                if os.path.isdir(target_p):
                    for root, dirs, files in os.walk(target_p):
                        depth = root[len(target_p):].count(os.sep)
                        if depth > 3:
                            del dirs[:]
                            continue
                        for f in files:
                            fl = f.lower()
                            if fl in self.target_exe_names:
                                full_p = os.path.join(root, f)
                                found_exes.append(self._build_install_info(full_p))

            # 2. Check top-level directories on drive for Adobe keywords or repacks
            try:
                top_items = os.listdir(d)
                for item in top_items:
                    item_path = os.path.join(d, item)
                    if os.path.isdir(item_path):
                        item_lower = item.lower()
                        # If folder has "adobe" or non-ascii Greek name or app names
                        if any(k in item_lower for k in ["adobe", "premiere", "photoshop", "after effects", "illustrator"]) or not self.is_ascii(item):
                            for root, dirs, files in os.walk(item_path):
                                depth = root[len(item_path):].count(os.sep)
                                if depth > 3:
                                    del dirs[:]
                                    continue
                                for f in files:
                                    fl = f.lower()
                                    if fl in self.target_exe_names:
                                        full_p = os.path.join(root, f)
                                        found_exes.append(self._build_install_info(full_p))
            except (OSError, PermissionError):
                pass

        # Deduplicate results
        unique = {}
        for item in found_exes:
            key = item["exe_path"].lower()
            if key not in unique:
                unique[key] = item

        self.log(f"Multi-Disk Scanner: Discovered {len(unique)} Adobe application executables across drives.", "SUCCESS")
        return list(unique.values())

    def _build_install_info(self, exe_path: str) -> Dict[str, Any]:
        exe_path = os.path.normpath(exe_path)
        is_clean_ascii = self.is_ascii(exe_path)
        drive = os.path.splitdrive(exe_path)[0]
        parent_dir = os.path.dirname(exe_path)
        folder_name = os.path.basename(parent_dir)

        # Identify app metadata
        app_meta = identify_adobe_app_by_path(exe_path)
        app_id = app_meta["id"] if app_meta else "adobe_generic"
        app_data = app_meta["data"] if app_meta else {}
        display_name = app_data.get("name", os.path.splitext(os.path.basename(exe_path))[0])

        # Get file version via PowerShell
        version = "Unknown"
        try:
            cmd = f'(Get-Item -LiteralPath "{exe_path}").VersionInfo.ProductVersion'
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
            ver_str = proc.stdout.strip()
            if ver_str:
                version = ver_str
        except Exception:
            pass

        return {
            "app_id": app_id,
            "name": display_name,
            "short_name": app_data.get("short_name", display_name),
            "category": app_data.get("category", "Adobe Application"),
            "icon": app_data.get("icon", "⚡"),
            "exe_path": exe_path,
            "folder_path": parent_dir,
            "folder_name": folder_name,
            "drive": drive,
            "version": version,
            "exists": True,
            "is_ascii": is_clean_ascii,
            "has_non_ascii_path": not is_clean_ascii
        }

    def scan_all_drives_for_scattered_caches(self) -> Dict[str, Any]:
        """Scans all drives for scattered video cache, peak files (.pek, .cfa) and temp files."""
        drives = self.get_all_logical_drives()
        results = {"total_files": 0, "total_mb": 0.0, "locations": []}

        for d in drives:
            candidates = [
                os.path.join(d, "Media Cache Files"),
                os.path.join(d, "Media Cache"),
                os.path.join(d, "Adobe Premiere Pro Video Previews"),
                os.path.join(d, "Adobe Premiere Pro Audio Previews"),
                os.path.join(d, "CameraRaw"),
                os.path.join(d, "Adobe Temp")
            ]
            for cand in candidates:
                if os.path.exists(cand):
                    count = 0
                    size_b = 0
                    for root, _, files in os.walk(cand):
                        for f in files:
                            fp = os.path.join(root, f)
                            try:
                                size_b += os.path.getsize(fp)
                                count += 1
                            except OSError:
                                pass
                    if count > 0:
                        mb = round(size_b / (1024 * 1024), 2)
                        results["locations"].append({"path": cand, "files": count, "size_mb": mb})
                        results["total_files"] += count
                        results["total_mb"] += mb

        return results
