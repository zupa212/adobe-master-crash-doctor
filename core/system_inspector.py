import os
import sys
import subprocess
import json
from typing import Dict, Any, List

class SystemInspector:
    def __init__(self, logger=None):
        self.logger = logger
        self._cached_profile = None

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}")

    def inspect_complete_system(self) -> Dict[str, Any]:
        """
        Autonomously inspects any Windows computer completely dynamically:
        - OS Version, Build, Architecture, Memory (Total & Free RAM)
        - CPU Model, Hardware Cores & Logical Threads
        - ALL GPUs in detail (Name, VRAM, Driver, Status, Video Processor, Resolution, dGPU vs iGPU)
        - ALL Storage Volumes (Type, Volume Name, Filesystem, Free & Total GB)
        """
        ps_script = """
        try {
            $os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture, TotalVisibleMemorySize, FreePhysicalMemory
            $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name, NumberOfCores, NumberOfLogicalProcessors
            
            $gpus = Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, DriverDate, AdapterRAM, VideoProcessor, VideoModeDescription, PNPDeviceID, Status
            
            $drives = Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID, DriveType, FileSystem, FreeSpace, Size, VolumeName | ForEach-Object {
                $typeStr = switch ($_.DriveType) {
                    2 { "Removable USB" }
                    3 { "Fixed SSD/HDD" }
                    4 { "Network Drive" }
                    5 { "Optical Drive" }
                    default { "Logical Volume" }
                }
                [PSCustomObject]@{
                    Name = $_.DeviceID
                    Root = ($_.DeviceID + [char]92)
                    VolumeName = if ($_.VolumeName) { $_.VolumeName } else { "Local Disk" }
                    DriveType = $typeStr
                    FileSystem = $_.FileSystem
                    FreeGB = if ($_.FreeSpace) { [math]::Round($_.FreeSpace / 1GB, 2) } else { 0 }
                    TotalGB = if ($_.Size) { [math]::Round($_.Size / 1GB, 2) } else { 0 }
                    UsedGB = if ($_.Size -and $_.FreeSpace) { [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 2) } else { 0 }
                }
            }

            [PSCustomObject]@{
                OS = $os
                CPU = $cpu
                GPUs = $gpus
                Drives = $drives
            } | ConvertTo-Json -Depth 5
        } catch {
            "{}"
        }
        """
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=12
            )
            data = json.loads(proc.stdout.strip() or "{}")
        except Exception as e:
            self.log(f"System inspection fallback error: {e}", "WARNING")
            data = {}

        # Format OS Info
        raw_os = data.get("OS", {})
        total_ram_gb = round((raw_os.get("TotalVisibleMemorySize") or 0) / (1024 * 1024), 2)
        free_ram_gb = round((raw_os.get("FreePhysicalMemory") or 0) / (1024 * 1024), 2)

        os_info = {
            "caption": raw_os.get("Caption", "Microsoft Windows"),
            "version": raw_os.get("Version", ""),
            "build": str(raw_os.get("BuildNumber", "Unknown")),
            "arch": raw_os.get("OSArchitecture", "64-bit"),
            "total_ram_gb": total_ram_gb,
            "free_ram_gb": free_ram_gb
        }

        # Format CPU Info
        raw_cpu = data.get("CPU", {})
        cpu_info = {
            "name": (raw_cpu.get("Name") or "Generic Multi-Core CPU").strip(),
            "cores": raw_cpu.get("NumberOfCores", 4),
            "threads": raw_cpu.get("NumberOfLogicalProcessors", 8)
        }

        # Format GPUs (Multi-GPU deep inspection)
        raw_gpus = data.get("GPUs", [])
        if isinstance(raw_gpus, dict):
            raw_gpus = [raw_gpus]

        gpus_list = []
        has_nvidia = False
        has_amd = False
        has_intel = False
        primary_dgpu = None

        for g in raw_gpus:
            name = (g.get("Name") or "Unknown Graphics Adapter").strip()
            driver = g.get("DriverVersion", "Unknown")
            date_raw = str(g.get("DriverDate", ""))
            raw_vram = g.get("AdapterRAM") or 0
            vram_mb = round(raw_vram / (1024 * 1024), 0)
            vram_gb = round(raw_vram / (1024 * 1024 * 1024), 2)
            video_proc = g.get("VideoProcessor") or name
            display_mode = g.get("VideoModeDescription")
            is_active_display = bool(display_mode and ("x" in str(display_mode)))

            name_lower = name.lower()
            is_dgpu = False
            vendor = "Other"

            if any(k in name_lower for k in ["nvidia", "geforce", "quadro", "rtx", "gtx"]):
                has_nvidia = True
                is_dgpu = True
                vendor = "NVIDIA"
                if not primary_dgpu:
                    primary_dgpu = name
            elif any(k in name_lower for k in ["amd", "radeon", "firepro"]):
                has_amd = True
                vendor = "AMD"
                if "integrated" not in name_lower and vram_mb > 1024:
                    is_dgpu = True
                    if not primary_dgpu:
                        primary_dgpu = name
            elif "intel" in name_lower:
                has_intel = True
                vendor = "Intel"
                if "arc" in name_lower:
                    is_dgpu = True
                    if not primary_dgpu:
                        primary_dgpu = name

            gpus_list.append({
                "name": name,
                "vendor": vendor,
                "driver": driver,
                "driver_date": date_raw.split("T")[0] if "T" in date_raw else date_raw,
                "vram_mb": vram_mb,
                "vram_gb": vram_gb,
                "video_processor": video_proc,
                "display_mode": display_mode or "Secondary / Headless",
                "is_active_display": is_active_display,
                "is_dgpu": is_dgpu,
                "status": g.get("Status", "OK"),
                "pnp_id": g.get("PNPDeviceID", "")
            })

        is_dual_gpu = len(gpus_list) > 1 and (has_nvidia or has_amd) and has_intel

        gpu_summary = {
            "gpus": gpus_list,
            "total_gpus": len(gpus_list),
            "is_dual_gpu": is_dual_gpu,
            "primary_dgpu": primary_dgpu or (gpus_list[0]["name"] if gpus_list else "Default Adapter"),
            "has_nvidia": has_nvidia,
            "has_amd": has_amd,
            "has_intel": has_intel
        }

        # Format Storage Drives (Multi-Disk deep scanner)
        raw_drives = data.get("Drives", [])
        if isinstance(raw_drives, dict):
            raw_drives = [raw_drives]
        drives_list = [d for d in raw_drives if d.get("Root")]

        profile = {
            "os": os_info,
            "cpu": cpu_info,
            "gpu": gpu_summary,
            "drives": drives_list
        }
        self._cached_profile = profile
        return profile
