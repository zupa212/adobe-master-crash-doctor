import os
import subprocess
import webbrowser
from typing import Dict, List, Any

class PremiereVersionManager:
    def __init__(self, logger=None):
        self.logger = logger

    def log(self, msg: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(msg, level)
        else:
            print(f"[{level}] {msg}")

    def get_version_analysis(self, installations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes installed and archived Premiere Pro versions and provides stability ratings."""
        versions = []

        # Known stability knowledge base
        stability_map = {
            "2026": {
                "name": "Premiere Pro 2026 (v26.x)",
                "rating": "2/5 (High Crash Risk - Unstable)",
                "status": "Beta / Experimental Repack",
                "verdict": "Causes silent crash on startup (RADAR_PRE_LEAK_64, UXP-IMS token failures, Unicode path crash). Not recommended for serious production.",
                "color": "#ef4444"
            },
            "2025": {
                "name": "Premiere Pro 2025 (v25.x)",
                "rating": "4/5 (Good Stability)",
                "status": "Current Release",
                "verdict": "Solid performance, improved speech-to-text. Requires NVIDIA Studio Driver 555+ or higher.",
                "color": "#eab308"
            },
            "2024": {
                "name": "Premiere Pro 2024 (v24.6.1)",
                "rating": "5/5 (Rock Solid - Gold Standard)",
                "status": "Battle-Tested Stable",
                "verdict": "Highest reliability, lowest crash rate on dual-GPU and Windows 11 systems. Best choice for uninterrupted editing.",
                "color": "#22c55e"
            }
        }

        # Check detected installations
        for inst in installations:
            name = inst.get("name", "")
            ver = str(inst.get("version", ""))
            exe = inst.get("exe_path", "")
            exists = inst.get("exists", False)

            matched_year = None
            if "2026" in name or "26." in ver or "2026" in exe:
                matched_year = "2026"
            elif "2025" in name or "25." in ver or "2025" in exe:
                matched_year = "2025"
            elif "2024" in name or "24." in ver or "2024" in exe:
                matched_year = "2024"

            info = stability_map.get(matched_year, {
                "name": f"Premiere Pro {name}",
                "rating": "3/5 (Unknown)",
                "status": "Custom Build",
                "verdict": "Check GPU and cache before launch.",
                "color": "#94a3b8"
            })

            versions.append({
                "exe_path": exe,
                "exists": exists,
                "version_string": ver,
                "year": matched_year,
                "stability": info
            })

        # Check for archive folders on other drives (e.g. D:\premire pro)
        archive_candidates = [
            r"D:\premire pro\AdobePremierePro2026.V26.2.2Win",
            r"D:\premire pro",
        ]
        archives = [p for p in archive_candidates if os.path.exists(p)]

        recommendation = (
            "If Premiere Pro 2026 continues to silently crash after the Junction & GPU auto-repair, "
            "it is strongly advised to roll back to Adobe Premiere Pro 2024 (v24.6.1) or 2025 (v25.0). "
            "Version 2024 is the global gold standard for stability on Windows 11."
        )

        return {
            "detected_versions": versions,
            "archives": archives,
            "recommendation": recommendation,
            "recommended_version": "Adobe Premiere Pro 2024 (v24.6.1)"
        }

    def open_adobe_cleaner_tool(self):
        """Opens official Adobe Creative Cloud Cleaner Tool documentation and download."""
        url = "https://helpx.adobe.com/creative-cloud/kb/cc-cleaner-tool-installation-problems.html"
        webbrowser.open(url)
        self.log(f"Opened Adobe Cleaner Tool download: {url}", "INFO")

    def open_nvidia_studio_drivers(self):
        """Opens NVIDIA Studio Drivers download page (Studio driver is far more stable than Game Ready for Premiere)."""
        url = "https://www.nvidia.com/Download/index.aspx"
        webbrowser.open(url)
        self.log(f"Opened NVIDIA Studio Driver download: {url}", "INFO")

    def downgrade_project_guide(self) -> str:
        """Returns step-by-step guidance on how to downgrade .prproj projects to open in older versions."""
        return """
How to open Premiere Pro 2026 projects in 2024 / 2025:
1. Export your project as Final Cut Pro XML (File > Export > Final Cut Pro XML).
2. Open Premiere Pro 2024/2025, create a new project, and import the .xml file.
   - All clips, cuts, multi-tracks, and basic transitions will be preserved!
3. Alternatively, rename your .prproj file to .zip, extract it, open the inner XML in Notepad, 
   change the Version attribute in the <Project> tag (e.g., from 42 to 40), and save.
"""
