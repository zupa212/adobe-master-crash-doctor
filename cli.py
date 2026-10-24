import sys
import argparse

# Force UTF-8 stdout encoding on Windows to prevent charmap decode/encode errors
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from core.logger import DoctorLogger
from core.diagnostics import AdobeDiagnostics
from core.universal_repair import UniversalAdobeRepairEngine
from core.repair import PremiereRepairEngine
from core.versions import PremiereVersionManager
from core.disk_scanner import MultiDiskScanner
from core.nuclear_purge import NuclearPurgeEngine
from core.adobe_cc_cleaner import AdobeCreativeCloudCleaner
from core.system_inspector import SystemInspector
from core.adobe_catalog import ADOBE_APPS_CATALOG

BANNER = """
========================================================================================
   ⚡ ADOBE MASTER CRASH DOCTOR • CREATOR EDITION
   Δημιουργία & Ανάπτυξη: Custom Crash Fix Engine
   Σκοπός: Αυτόνομη διάγνωση & 1-Click διόρθωση Instant Startup Crashes για ΟΛΑ τα Adobe Apps
========================================================================================
"""

DISCLAIMER = """
----------------------------------------------------------------------------------------
 ⚖️ ΝΟΜΙΚΗ ΔΗΛΩΣΗ & ΠΝΕΥΜΑΤΙΚΑ ΔΙΚΑΙΩΜΑΤΑ:
 Το λογισμικό αυτό αποτελεί ανεξάρτητο custom εργαλείο εντοπισμού και επιδιόρθωσης
 σφαλμάτων (crashes). Όλα τα εμπορικά σήματα, λογότυπα και πνευματικά δικαιώματα
 (Adobe, Creative Cloud, Premiere Pro, Photoshop, After Effects, Illustrator κ.α.)
 ανήκουν αποκλειστικά στην Adobe Inc.
----------------------------------------------------------------------------------------
"""

def main():
    parser = argparse.ArgumentParser(description="Adobe Master Crash Doctor • Creator Edition")
    parser.add_argument("--diagnose", action="store_true", help="Run comprehensive autonomous system & all-Adobe apps scan")
    parser.add_argument("--fix-all", action="store_true", help="1-Click Universal Fix for ALL Adobe applications")
    parser.add_argument("--fix", action="store_true", help="Run complete auto-fix repair suite")
    parser.add_argument("--custom-fix", action="store_true", help="Run customizable 1-Click fix with chosen modules and apps")
    parser.add_argument("--modules", type=str, default="all", help="Comma-separated repair modules (e.g. junction,gpu,fonts,cache,plugins,firewall,credentials,shortcuts)")
    parser.add_argument("--apps", type=str, default="all", help="Comma-separated target Adobe apps (e.g. premiere,photoshop,aftereffects,all)")
    parser.add_argument("--fix-app", type=str, help="Targeted fix for a specific app (e.g. premiere, photoshop, aftereffects, illustrator, acrobat)")
    parser.add_argument("--nuclear-purge", action="store_true", help="Nuclear wipe: Firewall rules, AppData, Credentials, Registry down to the root")
    parser.add_argument("--uninstall-cc", action="store_true", help="Completely uninstall Adobe Creative Cloud, stop all services & wipe CC roots")
    parser.add_argument("--purge-cache", action="store_true", help="Purge media & scratch cache files only")
    parser.add_argument("--purge-fonts", action="store_true", help="Purge corrupted Adobe font caches (AdobeFnt*.lst)")
    parser.add_argument("--reset-prefs", action="store_true", help="Reset preferences & plugin cache only")
    parser.add_argument("--versions", action="store_true", help="Display version analysis & rollback recommendations")
    parser.add_argument("--fix-freeze-premiere", "--anti-freeze", action="store_true", help="Fix Premiere Pro timeline freeze & GPU TDR timeout deadlock")
    parser.add_argument("--fix-runtime-installer", action="store_true", help="Fix RuntimeInstaller.dll APPCRASH (0xc0000005 Access Violation)")
    parser.add_argument("--check-ota", action="store_true", help="Check for Over-The-Air (OTA) updates on GitHub")
    parser.add_argument("--ota-update", action="store_true", help="Download and apply the latest OTA update directly from GitHub")

    args = parser.parse_args()
    logger = DoctorLogger()
    diag = AdobeDiagnostics(logger)
    u_repair = UniversalAdobeRepairEngine(logger)
    repair = PremiereRepairEngine(logger)
    vmanager = PremiereVersionManager(logger)
    scanner = MultiDiskScanner(logger)
    nuclear = NuclearPurgeEngine(logger)
    cc_cleaner = AdobeCreativeCloudCleaner(logger)
    inspector = SystemInspector(logger)
    from core.ota_updater import OTAUpdateEngine
    ota = OTAUpdateEngine(logger)

    print(BANNER)

    if args.check_ota:
        print("\n[*] Checking GitHub for Over-The-Air (OTA) Updates...")
        info = ota.check_for_updates()
        if info.get("update_available"):
            logger.success(f"Update Available: v{info['latest_version']} (Current: v{info['current_version']})")
            print("Release Date:", info.get("release_date"))
            print("Download URL:", info.get("download_url"))
            print("Changelog:")
            for item in info.get("changelog", []):
                print(f" - {item}")
        else:
            logger.success(f"You are running the latest version (v{info['current_version']}).")
        return

    if args.ota_update:
        print("\n[*] Starting Live Over-The-Air (OTA) Auto-Update...")
        info = ota.check_for_updates()
        if not info.get("update_available"):
            logger.success(f"Already up to date (v{info['current_version']}). No update required.")
            return

        logger.info(f"Downloading v{info['latest_version']}...")
        def _prog(pct, cur, total):
            mb_cur = round(cur / (1024 * 1024), 1)
            mb_tot = round(total / (1024 * 1024), 1)
            sys.stdout.write(f"\rProgress: {pct}% ({mb_cur}MB / {mb_tot}MB)")
            sys.stdout.flush()

        dl_path = ota.download_update(info["download_url"], progress_callback=_prog)
        print("\nDownload complete. Applying update and restarting...")
        ota.apply_update_and_restart(dl_path)
        logger.success("OTA update process dispatched. Application will restart.")
        return

    if args.fix_runtime_installer:
        print("\n[*] Executing RuntimeInstaller.DLL 0xc0000005 Repair Engine...")
        apps = diag.find_all_installations()
        exes = [a["exe_path"] for a in apps if a.get("exists") and a.get("exe_path")]
        res = u_repair.fix_runtime_installer_crash(exes)
        logger.success("RuntimeInstaller.DLL repair protocol complete!")
        return

    if args.fix_freeze_premiere:
        print("\n[*] Executing Surgical Premiere Pro Anti-Freeze & Timeline Engine...")
        apps = diag.find_all_installations()
        res = u_repair.fix_premiere_pro_freeze(apps)
        logger.success("Premiere Pro Anti-Freeze protocol complete!")
        return

    if args.custom_fix:
        print("\n[*] Running Customizable 1-Click Repair Suite...")
        res = diag.run_full_diagnosis()
        drives = scanner.get_all_logical_drives()
        
        # Parse modules
        mod_arg = [m.strip().lower() for m in args.modules.split(",")]
        is_all_mods = "all" in mod_arg
        options = {
            "kill_processes": True,
            "create_junctions": is_all_mods or "junction" in mod_arg,
            "gpu_affinity": is_all_mods or "gpu" in mod_arg,
            "purge_fonts": is_all_mods or "fonts" in mod_arg,
            "purge_caches": is_all_mods or "cache" in mod_arg,
            "reset_plugins": is_all_mods or "plugins" in mod_arg,
            "firewall_rules": is_all_mods or "firewall" in mod_arg,
            "purge_credentials": is_all_mods or "credentials" in mod_arg,
            "create_shortcuts": is_all_mods or "shortcuts" in mod_arg
        }
        selected_apps = [a.strip().lower() for a in args.apps.split(",")]

        fix_res = u_repair.execute_custom_repair(
            all_detected_apps=res.get("installations", []),
            all_drives=drives,
            options=options,
            selected_app_ids=selected_apps
        )
        print("\n[+] Custom 1-Click Repair Summary:")
        print(f"  • Processes stopped: {fix_res.get('processes_stopped', 0)}")
        print(f"  • NTFS ASCII Junctions created: {fix_res['junctions_created']}")
        print(f"  • High-Performance GPU overrides applied: {fix_res['gpu_overrides']}")
        print(f"  • Font Cache files purged: {fix_res['font_caches_purged']}")
        print(f"  • Media & Scratch files deleted: {fix_res['cache_purged']['deleted_files']} ({fix_res['cache_purged']['freed_mb']} MB)")
        print(f"  • Plugin & Hardware databases reset: {fix_res['plugin_resets']}")
        print(f"  • Firewall loopback rules configured: {fix_res['firewall_rules']}")
        print(f"  • Stale Adobe credentials wiped: {fix_res['credentials_purged']}")
        print(DISCLAIMER)

    elif args.fix_all or args.fix:
        print("\n[*] Running 1-Click Universal Repair Suite for ALL Adobe Applications...")
        res = diag.run_full_diagnosis()
        drives = scanner.get_all_logical_drives()
        fix_res = u_repair.execute_complete_universal_repair(res.get("installations", []), drives)
        print("\n[+] 1-Click Universal Repair Summary:")
        print(f"  • NTFS ASCII Junctions created: {fix_res['junctions_created']}")
        print(f"  • High-Performance GPU overrides applied: {fix_res['gpu_overrides']}")
        print(f"  • Font Cache files purged: {fix_res['font_caches_purged']}")
        print(f"  • Media & Scratch files deleted: {fix_res['cache_purged']['deleted_files']} ({fix_res['cache_purged']['freed_mb']} MB)")
        print(f"  • Plugin & Hardware databases reset: {fix_res['plugin_resets']}")
        print(f"  • Firewall loopback rules configured: {fix_res['firewall_rules']}")
        print(f"  • Stale Adobe credentials wiped: {fix_res['credentials_purged']}")
        print(DISCLAIMER)

    elif args.fix_app:
        app_id = args.fix_app.lower().strip()
        print(f"\n[*] Running Targeted Fix for Adobe App: {app_id}...")
        res = diag.run_full_diagnosis()
        app_res = u_repair.repair_single_adobe_app(app_id, res.get("installations", []))
        print(f"\n[+] Targeted Repair Completed for {app_id}:")
        print(f"  • GPU Overrides: {app_res['gpu_overrides']}")
        print(f"  • Font Caches Purged: {app_res['font_caches_purged']}")
        print(f"  • Firewall Rules: {app_res['firewall_rules']}")
        print(DISCLAIMER)

    elif args.nuclear_purge:
        print("\n[*] INITIATING COMPLETE NUCLEAR ROOT PURGE...")
        res = diag.run_full_diagnosis()
        exe_paths = [i["exe_path"] for i in res.get("installations", []) if i.get("exists")]
        drives = scanner.get_all_logical_drives()
        n_res = nuclear.execute_complete_nuclear_purge(exe_paths, drives)
        print(f"\n[+] Nuclear Purge Finished:")
        print(f"  • Firewall rules configured: {n_res['firewall']['rules_added']}")
        print(f"  • Stale Adobe credentials wiped: {n_res['credentials_purged']}")
        print(f"  • Cache files deleted: {n_res['cache_purged']['deleted_files']} ({n_res['cache_purged']['freed_mb']} MB)")
        print(f"  • Registry tree nodes sanitized: {n_res['registry_keys_cleaned']}")
        print(DISCLAIMER)

    elif args.uninstall_cc:
        print("\n[*] INITIATING ADOBE CREATIVE CLOUD ROOT UNINSTALLATION...")
        cc_res = cc_cleaner.execute_complete_cc_uninstaller_suite()
        print(f"\n[+] Creative Cloud Root Uninstallation Finished:")
        print(f"  • Local Uninstaller executed: {cc_res['uninstalled_local']}")
        print(f"  • Official Adobe Cleaner executed: {cc_res['cleaner_executed']}")
        print(f"  • Windows Services removed: {len(cc_res['deleted_services'])}")
        print(f"  • Scheduled Tasks removed: {cc_res['tasks_removed']}")
        print(f"  • Startup Registry entries removed: {cc_res['startup_keys_removed']}")
        print(f"  • Root Directories wiped: {cc_res['wiped_directories']}")
        print(DISCLAIMER)

    elif args.purge_cache:
        u_repair.purge_all_adobe_scratch_and_media_caches()
    elif args.purge_fonts:
        u_repair.purge_adobe_font_caches()
    elif args.reset_prefs:
        u_repair.reset_corrupt_plugin_and_preferences_caches()
    elif args.versions:
        res = diag.run_full_diagnosis()
        v_info = vmanager.get_version_analysis(res.get("installations", []))
        print("\n=== VERSION ANALYSIS ===")
        for v in v_info["detected_versions"]:
            stab = v["stability"]
            print(f"- {stab['name']} (Path: {v['exe_path']})")
            print(f"  Rating: {stab['rating']} | Status: {stab['status']}")
            print(f"  Verdict: {stab['verdict']}\n")
        print(f"Recommended Stable Version: {v_info['recommended_version']}")
    else:
        # Default action: run full dynamic diagnosis
        res = diag.run_full_diagnosis()
        sys_prof = res.get("system_profile", {})

        print("\n--- AUTONOMOUS SYSTEM HARDWARE AUDIT ---")
        os_info = sys_prof.get("os", {})
        cpu_info = sys_prof.get("cpu", {})
        gpu_info = sys_prof.get("gpu", {})
        print(f"• OS: {os_info.get('caption')} (Build {os_info.get('build')}, {os_info.get('arch')})")
        print(f"• CPU: {cpu_info.get('name')} ({cpu_info.get('cores')} Cores, {cpu_info.get('threads')} Threads)")
        print(f"• RAM: {os_info.get('total_ram_gb')} GB (Available: {os_info.get('free_ram_gb')} GB)")

        print(f"\n--- MULTI-GPU TELEMETRY ({gpu_info.get('total_gpus', len(gpu_info.get('gpus', [])))} ADAPTERS DETECTED) ---")
        for idx, g in enumerate(gpu_info.get("gpus", []), 1):
            dgpu_tag = " [Dedicated High-Perf dGPU]" if g.get("is_dgpu") else " [Integrated iGPU]"
            disp_tag = " • Active Display Output" if g.get("is_active_display") else ""
            print(f"[{idx}] {g.get('name')} ({g.get('vendor')})")
            print(f"    VRAM: {g.get('vram_gb', 0)} GB ({g.get('vram_mb', 0)} MB) | Status: {g.get('status')}{dgpu_tag}{disp_tag}")
            print(f"    Driver Version: {g.get('driver')} (Released: {g.get('driver_date')})")
            print(f"    Video Mode: {g.get('display_mode')}")
        print(f"• Dual-GPU Setup Active: {gpu_info.get('is_dual_gpu')}")
        print(f"• Primary Performance GPU: {gpu_info.get('primary_dgpu')}")

        print("\n--- MULTI-DISK STORAGE VOLUMES AUDITED ---")
        for d in sys_prof.get("drives", []):
            vol_name = f" [{d.get('VolumeName')}]" if d.get('VolumeName') else ""
            d_type = d.get('DriveType', 'Fixed')
            fs = d.get('FileSystem', 'NTFS')
            print(f"• Drive {d.get('Name')}{vol_name} ({d_type}, {fs}): {d.get('FreeGB')} GB Free / {d.get('TotalGB')} GB Total")

        print(f"\nSystem Adobe Health: [{res['status']}]")
        print(f"Critical Issues: {res['critical_count']} | Warnings: {res['warning_count']}\n")

        print("--- DETECTED ADOBE APPLICATIONS ---")
        existing_apps = [a for a in res["installations"] if a.get("exists")]
        orphaned_apps = [a for a in res["installations"] if not a.get("exists")]

        print(f"Active / Installed Adobe Apps ({len(existing_apps)} found):")
        for inst in existing_apps:
            gpu_tag = " [High-Perf GPU: OK]" if inst.get("gpu_high_performance") else " [High-Perf GPU: MISSING]"
            non_ascii = " ⚠️ NON-ASCII PATH!" if inst.get("has_non_ascii_path") else ""
            print(f"  {inst.get('icon', '⚡')} {inst['name']} (v{inst.get('version', 'Unknown')}) -> {inst['exe_path']}{gpu_tag}{non_ascii}")

        if orphaned_apps:
            print(f"\nOrphaned Registry / Broken Shortcuts ({len(orphaned_apps)} found):")
            for inst in orphaned_apps[:6]:
                print(f"  ❌ {inst['name']} -> {inst['exe_path']} [File Missing]")

        print("\n--- CACHE & FONT TELEMETRY ---")
        print(f"• Font Cache Files (AdobeFnt*.lst): {res.get('font_info', {}).get('total_files', 0)} files")
        print(f"• Media & Scratch Cache: {res['cache_info']['total_size_mb']} MB ({res['cache_info']['total_files']} files)")

        cc_stat = cc_cleaner.detect_creative_cloud_presence()
        print(f"• Creative Cloud Desktop Installed: {cc_stat['has_cc_installed']}")
        print(f"• Adobe Background Services: {len(cc_stat['detected_services'])} running")

        print("\n--- DIAGNOSED CRASH VECTORS & ISSUES ---")
        if not res["issues"]:
            print("✔ No issues detected! All Adobe applications are configured cleanly.")
        else:
            for idx, issue in enumerate(res["issues"], 1):
                print(f"[{idx}] [{issue['severity']}] {issue['title']}")
                print(f"    {issue['description']}")
                print(f"    Fix: {issue['fix_action']}\n")

        print("Available Action Commands:")
        print("  --fix-all       : ⚡ 1-Click Universal Repair (All Adobe Apps)")
        print("  --custom-fix    : 🛠️ Customizable 1-Click Repair (--modules ... --apps ...)")
        print("  --fix-app <id>  : 🎯 Targeted fix (e.g. --fix-app premiere, --fix-app photoshop)")
        print("  --nuclear-purge : 🔥 Deep root clean (Firewall, Vault, Registry, Cache)")
        print("  --uninstall-cc  : 🗑️ CC Root Uninstaller & background services removal")
        print(DISCLAIMER)

if __name__ == "__main__":
    main()
