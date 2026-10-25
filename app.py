import os
import sys
import threading
import subprocess
import webbrowser
import customtkinter as ctk
from tkinter import messagebox, filedialog

# Add current dir to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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
from core.ota_updater import OTAUpdateEngine, CURRENT_VERSION, CURRENT_BUILD

class AdobeMasterDoctorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"⚡ Adobe Master Crash Doctor • Creator Edition (v{CURRENT_VERSION} OTA)")
        self.ota = OTAUpdateEngine(self.logger)
        self.ota_info = None
        self.geometry("1160x820")
        self.minsize(1040, 720)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize core engines (Zero LLM Relay / 100% Native)
        self.logger = DoctorLogger(callback=self.append_log)
        self.diag = AdobeDiagnostics(self.logger)
        self.u_repair = UniversalAdobeRepairEngine(self.logger)
        self.repair = PremiereRepairEngine(self.logger)
        self.vmanager = PremiereVersionManager(self.logger)
        self.scanner = MultiDiskScanner(self.logger)
        self.nuclear = NuclearPurgeEngine(self.logger)
        self.cc_cleaner = AdobeCreativeCloudCleaner(self.logger)
        self.inspector = SystemInspector(self.logger)

        self.diag_data = None
        self.is_fixing = False

        # Customizable 1-Click options
        self.opt_kill_procs = ctk.BooleanVar(value=True)
        self.opt_junctions = ctk.BooleanVar(value=True)
        self.opt_gpu_affinity = ctk.BooleanVar(value=True)
        self.opt_purge_fonts = ctk.BooleanVar(value=True)
        self.opt_purge_caches = ctk.BooleanVar(value=True)
        self.opt_reset_plugins = ctk.BooleanVar(value=True)
        self.opt_firewall = ctk.BooleanVar(value=True)
        self.opt_credentials = ctk.BooleanVar(value=True)
        self.opt_shortcuts = ctk.BooleanVar(value=True)
        self.opt_fix_runtime = ctk.BooleanVar(value=True)
        self.opt_fix_freeze = ctk.BooleanVar(value=True)

        self.setup_ui()
        self.run_diagnostics_thread()
        threading.Thread(target=self.silent_startup_ota_check, daemon=True).start()

    def setup_ui(self):
        # Master grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ---------------- SIDEBAR FRAME ---------------- #
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="⚡ ADOBE DOCTOR",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(18, 2))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Creator Edition • Custom 1-Click",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#38bdf8"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 15))

        # Master 1-Click Action in Sidebar
        self.btn_side_1click = ctk.CTkButton(
            self.sidebar_frame,
            text="⚡ 1-CLICK ALL-APP FIX",
            command=self.run_universal_fix_thread,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=36
        )
        self.btn_side_1click.grid(row=2, column=0, padx=15, pady=(0, 6), sticky="ew")

        # Dedicated Premiere Pro 2-Minute Anti-Freeze Button in Sidebar
        self.btn_side_freeze = ctk.CTkButton(
            self.sidebar_frame,
            text="🧊 FIX PREMIERE FREEZE",
            command=self.run_premiere_freeze_thread,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=36
        )
        self.btn_side_freeze.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")

        # Sidebar navigation buttons
        self.btn_nav_diag = ctk.CTkButton(
            self.sidebar_frame,
            text="🔍 Diagnostics & Hardware",
            command=lambda: self.select_frame("diag"),
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_nav_diag.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_fix = ctk.CTkButton(
            self.sidebar_frame,
            text="⚡ Custom 1-Click Fix",
            command=lambda: self.select_frame("fix"),
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_nav_fix.grid(row=5, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_apps = ctk.CTkButton(
            self.sidebar_frame,
            text="🎯 App-Specific Doctor",
            command=lambda: self.select_frame("apps"),
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_nav_apps.grid(row=6, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_nuclear = ctk.CTkButton(
            self.sidebar_frame,
            text="🔥 CC Root Cleaner & Purge",
            command=lambda: self.select_frame("nuclear"),
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_nav_nuclear.grid(row=7, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_versions = ctk.CTkButton(
            self.sidebar_frame,
            text="📦 Versions & Rollback",
            command=lambda: self.select_frame("versions"),
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_nav_versions.grid(row=8, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_console = ctk.CTkButton(
            self.sidebar_frame,
            text="💻 Execution Console",
            command=lambda: self.select_frame("console"),
            fg_color="#1e293b",
            hover_color="#334155"
        )
        self.btn_nav_console.grid(row=9, column=0, padx=15, pady=5, sticky="ew")

        # OTA Auto-Updater Section in Sidebar
        self.ota_card = ctk.CTkFrame(self.sidebar_frame, fg_color="#1e293b", corner_radius=8, border_color="#38bdf8", border_width=1)
        self.ota_card.grid(row=10, column=0, padx=15, pady=(10, 4), sticky="ew")

        self.lbl_ota_status = ctk.CTkLabel(
            self.ota_card,
            text=f"📡 OTA Engine • v{CURRENT_VERSION}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_ota_status.pack(padx=10, pady=(6, 2))

        self.btn_ota_check = ctk.CTkButton(
            self.ota_card,
            text="🔄 Check Updates",
            command=self.manual_check_ota,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=26
        )
        self.btn_ota_check.pack(padx=10, pady=(0, 6), fill="x")

        # Bottom Quick Action in Sidebar
        self.btn_rescan = ctk.CTkButton(
            self.sidebar_frame,
            text="🔄 Re-Scan System",
            command=self.run_diagnostics_thread,
            fg_color="#0284c7",
            hover_color="#0369a1"
        )
        self.btn_rescan.grid(row=11, column=0, padx=15, pady=8, sticky="ew")

        # Creator tag in sidebar
        lbl_creator = ctk.CTkLabel(
            self.sidebar_frame,
            text="🛠️ Custom Creation\nPure Crash Fix Solution",
            font=ctk.CTkFont(size=10),
            text_color="#64748b"
        )
        lbl_creator.grid(row=12, column=0, padx=15, pady=(0, 15))

        # ---------------- CONTENT CONTAINER ---------------- #
        self.content_container = ctk.CTkFrame(self, corner_radius=10, fg_color="#0f172a")
        self.content_container.grid(row=0, column=1, padx=15, pady=(15, 5), sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # ---------------- LEGAL DISCLAIMER FOOTER BAR ---------------- #
        self.footer_frame = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color="#090d16")
        self.footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.lbl_disclaimer = ctk.CTkLabel(
            self.footer_frame,
            text="⚖️ Νομική Δήλωση & Πνευματικά Δικαιώματα: Ανεξάρτητο custom εργαλείο διάγνωσης/επιδιόρθωσης. Όλα τα εμπορικά σήματα και πνευματικά δικαιώματα (Adobe, CC, Premiere, Photoshop κλπ.) ανήκουν αποκλειστικά στην Adobe Inc.",
            font=ctk.CTkFont(size=10),
            text_color="#64748b"
        )
        self.lbl_disclaimer.pack(padx=15, pady=6, anchor="center")

        # Setup Views
        self.setup_diag_view()
        self.setup_fix_view()
        self.setup_apps_view()
        self.setup_nuclear_view()
        self.setup_versions_view()
        self.setup_console_view()

        self.select_frame("diag")

    def select_frame(self, name):
        nav_map = {
            "diag": (self.btn_nav_diag, self.frame_diag),
            "fix": (self.btn_nav_fix, self.frame_fix),
            "apps": (self.btn_nav_apps, self.frame_apps),
            "nuclear": (self.btn_nav_nuclear, self.frame_nuclear),
            "versions": (self.btn_nav_versions, self.frame_versions),
            "console": (self.btn_nav_console, self.frame_console)
        }
        for key, (btn, frame) in nav_map.items():
            if key == name:
                btn.configure(fg_color="#2563eb")
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                btn.configure(fg_color="#1e293b")
                frame.grid_forget()

    # ---------------- VIEW 1: ALL ADOBE DIAGNOSTICS & MULTI-HARDWARE ---------------- #
    def setup_diag_view(self):
        self.frame_diag = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        self.frame_diag.grid_columnconfigure(0, weight=1)

        # Header with status badge
        header_frame = ctk.CTkFrame(self.frame_diag, fg_color="#1e293b", corner_radius=8)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        self.lbl_diag_title = ctk.CTkLabel(
            header_frame,
            text="Autonomous Multi-Disk & Multi-GPU System Audit",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_diag_title.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.badge_status = ctk.CTkLabel(
            header_frame,
            text="SCANNING...",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#475569",
            corner_radius=6,
            padx=12, pady=4
        )
        self.badge_status.grid(row=0, column=1, padx=15, pady=12, sticky="e")

        # Telemetry Quick Metric Cards
        telemetry_frame = ctk.CTkFrame(self.frame_diag, fg_color="transparent")
        telemetry_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        telemetry_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_cpu_os = self.create_metric_card(telemetry_frame, 0, "System & OS", "Detecting...")
        self.card_gpu = self.create_metric_card(telemetry_frame, 1, "GPU Hardware", "Detecting...")
        self.card_cache = self.create_metric_card(telemetry_frame, 2, "Media/Scratch Cache", "Calculating...")
        self.card_fonts = self.create_metric_card(telemetry_frame, 3, "Font Cache DBs", "Scanning...")

        # Multi-GPU Hardware Telemetry Box
        self.gpu_telemetry_frame = ctk.CTkFrame(self.frame_diag, fg_color="#1e293b", corner_radius=8)
        self.gpu_telemetry_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        lbl_gpu_hdr = ctk.CTkLabel(self.gpu_telemetry_frame, text="🎮 Graphics Cards & Display Adapters Telemetry", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
        lbl_gpu_hdr.pack(padx=15, pady=(10, 4), anchor="w")
        self.lbl_gpu_specs = ctk.CTkLabel(
            self.gpu_telemetry_frame,
            text="Querying all installed graphics adapters...",
            font=ctk.CTkFont(size=12, family="Consolas"),
            justify="left",
            text_color="#e2e8f0"
        )
        self.lbl_gpu_specs.pack(padx=15, pady=(0, 10), anchor="w")

        # Multi-Disk Storage Volumes Box
        self.disk_telemetry_frame = ctk.CTkFrame(self.frame_diag, fg_color="#1e293b", corner_radius=8)
        self.disk_telemetry_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        lbl_disk_hdr = ctk.CTkLabel(self.disk_telemetry_frame, text="💾 All Audited Storage Volumes (Dynamic Multi-Disk Scanner)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10b981")
        lbl_disk_hdr.pack(padx=15, pady=(10, 4), anchor="w")
        self.lbl_disk_specs = ctk.CTkLabel(
            self.disk_telemetry_frame,
            text="Scanning all storage drives...",
            font=ctk.CTkFont(size=12, family="Consolas"),
            justify="left",
            text_color="#e2e8f0"
        )
        self.lbl_disk_specs.pack(padx=15, pady=(0, 10), anchor="w")

        # Quick Premiere Anti-Freeze Banner on Diagnostics
        self.p_quick_box = ctk.CTkFrame(self.frame_diag, fg_color="#082f49", corner_radius=8, border_color="#0284c7", border_width=1.5)
        self.p_quick_box.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.p_quick_box.grid_columnconfigure(0, weight=1)
        self.p_quick_box.grid_columnconfigure(1, weight=0)

        lbl_p_quick = ctk.CTkLabel(
            self.p_quick_box,
            text="🧊 Premiere Pro 2-Minute Freeze Detected? (Audio Sleep Deadlock, Dual-GPU & Cloud Timeouts)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        )
        lbl_p_quick.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        btn_p_quick = ctk.CTkButton(
            self.p_quick_box,
            text="🧊 FIX PREMIERE FREEZE NOW",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=32,
            command=self.run_premiere_freeze_thread
        )
        btn_p_quick.grid(row=0, column=1, padx=15, pady=10, sticky="e")

        # Detected Adobe Applications Section
        lbl_apps_hdr = ctk.CTkLabel(
            self.frame_diag,
            text="Detected Adobe Applications Across All Drives",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38bdf8"
        )
        lbl_apps_hdr.grid(row=5, column=0, padx=15, pady=(10, 5), sticky="w")

        self.apps_container = ctk.CTkFrame(self.frame_diag, fg_color="transparent")
        self.apps_container.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        self.apps_container.grid_columnconfigure(0, weight=1)

        # Issues Section
        lbl_issues = ctk.CTkLabel(
            self.frame_diag,
            text="Diagnosed Crash Vectors & Action Plan",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_issues.grid(row=7, column=0, padx=15, pady=(15, 5), sticky="w")

        self.issues_container = ctk.CTkFrame(self.frame_diag, fg_color="transparent")
        self.issues_container.grid(row=8, column=0, padx=10, pady=5, sticky="ew")
        self.issues_container.grid_columnconfigure(0, weight=1)

    def create_metric_card(self, parent, col, title, initial_val):
        frame = ctk.CTkFrame(parent, fg_color="#1e293b", corner_radius=8)
        frame.grid(row=0, column=col, padx=4, pady=5, sticky="nsew")
        t_lbl = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=11), text_color="#94a3b8")
        t_lbl.pack(padx=10, pady=(8, 2), anchor="w")
        v_lbl = ctk.CTkLabel(frame, text=initial_val, font=ctk.CTkFont(size=13, weight="bold"))
        v_lbl.pack(padx=10, pady=(0, 8), anchor="w")
        return v_lbl

    # ---------------- VIEW 2: CUSTOMIZABLE 1-CLICK FIX SUITE ---------------- #
    def setup_fix_view(self):
        self.frame_fix = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        self.frame_fix.grid_columnconfigure(0, weight=1)

        # Master CTA Card
        cta_frame = ctk.CTkFrame(self.frame_fix, fg_color="#064e3b", corner_radius=10, border_color="#10b981", border_width=1)
        cta_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        cta_frame.grid_columnconfigure(0, weight=1)

        cta_title = ctk.CTkLabel(
            cta_frame,
            text="⚡ 1-CLICK UNIVERSAL REPAIR (ALL ADOBE APPS)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff"
        )
        cta_title.pack(padx=20, pady=(15, 5), anchor="w")

        cta_desc = ctk.CTkLabel(
            cta_frame,
            text="Επισκευή με 1 κλικ: Αυτόματη εκτέλεση όλων των φάσεων επιδιόρθωσης για όλες τις εγκατεστημένες εφαρμογές Adobe.",
            font=ctk.CTkFont(size=12),
            text_color="#a7f3d0",
            wraplength=700,
            justify="left"
        )
        cta_desc.pack(padx=20, pady=(0, 10), anchor="w")

        self.btn_run_universal = ctk.CTkButton(
            cta_frame,
            text="⚡ ΕΚΤΕΛΕΣΗ ΠΛΗΡΟΥΣ 1-CLICK ΕΠΙΔΙΟΡΘΩΣΗΣ (DEFAULT REPAIR ALL)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=44,
            command=self.run_universal_fix_thread
        )
        self.btn_run_universal.pack(padx=20, pady=(0, 15), fill="x")

        # ---------------- PREMIERE PRO ANTI-FREEZE HERO CARD ---------------- #
        freeze_card = ctk.CTkFrame(self.frame_fix, fg_color="#0c4a6e", corner_radius=10, border_color="#38bdf8", border_width=1.5)
        freeze_card.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        freeze_card.grid_columnconfigure(0, weight=1)

        freeze_title = ctk.CTkLabel(
            freeze_card,
            text="🧊 1-CLICK FIX PREMIERE PRO FREEZE (2-MINUTE TIMEOUT & AUDIO/GPU ANTI-DEADLOCK)",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#38bdf8"
        )
        freeze_title.pack(padx=20, pady=(12, 4), anchor="w")

        freeze_desc = ctk.CTkLabel(
            freeze_card,
            text="Εξειδικευμένη αποκατάσταση παγώματος Premiere Pro στα 2 λεπτά (Not Responding):\n"
                 "• Αποτροπή Audio Sleep Deadlock (dvaaudiodevice.AlwaysRunning=false & Output-Only UI)\n"
                 "• Επίλυση διένεξης Dual-GPU (Απενεργοποίηση Intel iGPU decode, αποκλειστική ανάθεση στην NVIDIA RTX 3060)\n"
                 "• Τερματισμός 120s IPC Handshake Timeouts (AdobeCollabSync, CCXProcess, DynamicLink)\n"
                 "• Ενίσχυση Windows GPU TDR Registry Delay σε 10s & βαθύς καθαρισμός Media Cache (.pek, .cfa, .mcdb)",
            font=ctk.CTkFont(size=12),
            text_color="#bae6fd",
            wraplength=720,
            justify="left"
        )
        freeze_desc.pack(padx=20, pady=(0, 8), anchor="w")

        self.btn_fix_freeze = ctk.CTkButton(
            freeze_card,
            text="🧊 ΕΠΙΔΙΟΡΘΩΣΗ FREEZE PREMIERE PRO (FIX 2-MIN TIMEOUT & AUDIO/GPU NOW)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=44,
            command=self.run_premiere_freeze_thread
        )
        self.btn_fix_freeze.pack(padx=20, pady=(0, 14), fill="x")

        # ---------------- RUNTIMEINSTALLER.DLL 0xc0000005 HERO CARD ---------------- #
        runtime_card = ctk.CTkFrame(self.frame_fix, fg_color="#312e81", corner_radius=10, border_color="#818cf8", border_width=1.5)
        runtime_card.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        runtime_card.grid_columnconfigure(0, weight=1)

        runtime_title = ctk.CTkLabel(
            runtime_card,
            text="🛡️ 1-CLICK FIX RUNTIMEINSTALLER.DLL (0xc0000005 ACCESS VIOLATION)",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#a5b4fc"
        )
        runtime_title.pack(padx=20, pady=(12, 4), anchor="w")

        runtime_desc = ctk.CTkLabel(
            runtime_card,
            text="Οριστική αποκατάσταση του σφάλματος APPCRASH στο RuntimeInstaller.DLL (Offset 0x000000000010de13):\n"
                 "• Εκκαθάριση corrupt βάσεων δεδομένων αδειών SLStore, SLCache, SLData & OOBE\n"
                 "• Επαναφορά πλήρων δικαιωμάτων NTFS (Full Control) στα runtime directories & φακέλους εφαρμογών\n"
                 "• Αυτόματη μεταφορά και επαλήθευση Microsoft Visual C++ 2015-2022 x64 Runtimes στο app root\n"
                 "• Παράκαμψη broken on-demand codec loops (HEVC, Dolby, MainConcept) μέσω Debug Database\n"
                 "• Ενεργοποίηση DirectX High-Performance GPU Affinity & Windows Firewall Loopback rules",
            font=ctk.CTkFont(size=12),
            text_color="#c7d2fe",
            wraplength=720,
            justify="left"
        )
        runtime_desc.pack(padx=20, pady=(0, 8), anchor="w")

        btn_row = ctk.CTkFrame(runtime_card, fg_color="transparent")
        btn_row.pack(padx=20, pady=(0, 14), fill="x")
        btn_row.grid_columnconfigure(0, weight=3)
        btn_row.grid_columnconfigure(1, weight=1)

        self.btn_fix_runtime = ctk.CTkButton(
            btn_row,
            text="🛡️ ΕΠΙΔΙΟΡΘΩΣΗ RUNTIMEINSTALLER.DLL APPCRASH (0xc0000005)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            height=44,
            command=self.run_runtime_installer_fix_thread
        )
        self.btn_fix_runtime.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_browse_custom = ctk.CTkButton(
            btn_row,
            text="📂 Browse Custom EXE...",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            height=44,
            command=self.browse_custom_exe
        )
        self.btn_browse_custom.grid(row=0, column=1, sticky="ew")

        # Customization Panel
        custom_box = ctk.CTkFrame(self.frame_fix, fg_color="#1e293b", corner_radius=10, border_color="#38bdf8", border_width=1)
        custom_box.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        lbl_c_title = ctk.CTkLabel(custom_box, text="🛠️ Customizable 1-Click Repair Options (Επιλογή Modules & Εφαρμογών)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38bdf8")
        lbl_c_title.pack(padx=15, pady=(15, 5), anchor="w")

        lbl_c_sub = ctk.CTkLabel(custom_box, text="Επιλέξτε ποια συγκεκριμένα βήματα επιδιόρθωσης επιθυμείτε να συμπεριληφθούν στο Custom 1-Click:", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        lbl_c_sub.pack(padx=15, pady=(0, 10), anchor="w")

        # Checkboxes Grid
        chk_grid = ctk.CTkFrame(custom_box, fg_color="transparent")
        chk_grid.pack(padx=15, pady=5, fill="x")
        chk_grid.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkCheckBox(chk_grid, text="1. Kill Lingering Processes", variable=self.opt_kill_procs).grid(row=0, column=0, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(chk_grid, text="2. Create NTFS ASCII Junctions", variable=self.opt_junctions).grid(row=0, column=1, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(chk_grid, text="3. High-Perf GPU Affinity (Registry)", variable=self.opt_gpu_affinity).grid(row=0, column=2, padx=5, pady=6, sticky="w")

        ctk.CTkCheckBox(chk_grid, text="4. Purge Font Caches (AdobeFnt*.lst)", variable=self.opt_purge_fonts).grid(row=1, column=0, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(chk_grid, text="5. Purge Media & Scratch Caches", variable=self.opt_purge_caches).grid(row=1, column=1, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(chk_grid, text="6. Reset Plugin DBs (Auto-Backup)", variable=self.opt_reset_plugins).grid(row=1, column=2, padx=5, pady=6, sticky="w")

        ctk.CTkCheckBox(chk_grid, text="7. Windows Firewall Loopback Rules", variable=self.opt_firewall).grid(row=2, column=0, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(chk_grid, text="8. Purge Stale Credential Vault", variable=self.opt_credentials).grid(row=2, column=1, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(chk_grid, text="9. Create Repaired Desktop Shortcut", variable=self.opt_shortcuts).grid(row=2, column=2, padx=5, pady=6, sticky="w")

        ctk.CTkCheckBox(chk_grid, text="10. Fix RuntimeInstaller (0xc0000005)", variable=self.opt_fix_runtime).grid(row=3, column=0, padx=5, pady=6, sticky="w")
        ctk.CTkCheckBox(chk_grid, text="11. Fix Premiere 2-Min Freeze", variable=self.opt_fix_freeze).grid(row=3, column=1, padx=5, pady=6, sticky="w")

        self.btn_run_custom = ctk.CTkButton(
            custom_box,
            text="🛠️ ΕΚΤΕΛΕΣΗ CUSTOM 1-CLICK ΕΠΙΔΙΟΡΘΩΣΗΣ (RUN MY SELECTION)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=40,
            command=self.run_custom_fix_thread
        )
        self.btn_run_custom.pack(padx=15, pady=(15, 18), fill="x")

        # Modular Individual Quick Cards
        lbl_individual = ctk.CTkLabel(
            self.frame_fix,
            text="Μεμονωμένα Εργαλεία Επιδιόρθωσης (Single-Action Utilities)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_individual.grid(row=3, column=0, padx=15, pady=(15, 10), sticky="w")

        tools_grid = ctk.CTkFrame(self.frame_fix, fg_color="transparent")
        tools_grid.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        tools_grid.grid_columnconfigure((0, 1), weight=1)

        self.create_tool_card(tools_grid, 0, 0, "1. 🔤 Εκκαθάριση Adobe Font Cache", "Διαγράφει αλλοιωμένα αρχεία AdobeFnt*.lst που προκαλούν άμεσο crash κατά την εκκίνηση.", "Purge Font Caches", self.action_purge_fonts)
        self.create_tool_card(tools_grid, 0, 1, "2. 🎮 Κλείδωμα High Performance GPU", "Καταχωρεί GpuPreference=2; στο Windows Registry για όλα τα Adobe exes.", "Lock GPU Affinity", self.action_fix_gpu)
        self.create_tool_card(tools_grid, 1, 0, "3. 📁 Διόρθωση Μη-ASCII / Ελληνικών Φακέλων", "Δημιουργεί αυτόματα καθαρό NTFS Junction στον ίδιο δίσκο για παράκαμψη των C++ crashes.", "Create Dynamic Junctions", self.action_fix_junction)
        self.create_tool_card(tools_grid, 1, 1, "4. 🧹 Εκκαθάριση Media & Scratch Caches", "Διαγράφει αλλοιωμένα αρχεία .ims, .pek, .cfa, CameraRaw και temp αρχεία.", "Purge All Caches", self.action_purge_cache)
        self.create_tool_card(tools_grid, 2, 0, "5. 🔌 Επαναφορά Plugins & Preferences", "Κρατάει αυτόματο backup και μηδενίζει τα Plugin Loading.log και Audio Plugin registries.", "Reset Plugin Databases", self.action_reset_prefs)
        self.create_tool_card(tools_grid, 2, 1, "6. 🛡️ Windows Firewall Loopback Sanitizer", "Επιτρέπει την επικοινωνία 127.0.0.1 (IPC sockets) ώστε να μην παγώνει το splash screen.", "Configure Firewall Rules", self.action_fix_firewall)

    def create_tool_card(self, parent, row, col, title, desc, btn_text, command):
        frame = ctk.CTkFrame(parent, fg_color="#1e293b", corner_radius=8)
        frame.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        lbl_t = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        lbl_t.pack(padx=12, pady=(12, 4), anchor="w")

        lbl_d = ctk.CTkLabel(frame, text=desc, font=ctk.CTkFont(size=12), text_color="#94a3b8", wraplength=310, justify="left")
        lbl_d.pack(padx=12, pady=(0, 12), anchor="w")

        btn = ctk.CTkButton(frame, text=btn_text, fg_color="#334155", hover_color="#475569", command=command)
        btn.pack(padx=12, pady=(0, 12), fill="x")

    # ---------------- VIEW 3: APP-SPECIFIC DOCTOR (TARGETED REPAIR) ---------------- #
    def setup_apps_view(self):
        self.frame_apps = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        self.frame_apps.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self.frame_apps, text="🎯 App-Specific Doctor (Στοχευμένη Επισκευή ανά Εφαρμογή)", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        subtitle = ctk.CTkLabel(self.frame_apps, text="Επιλέξτε συγκεκριμένη εφαρμογή για άμεση μεμονωμένη διάγνωση και αποκατάσταση:", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        subtitle.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        self.apps_grid_container = ctk.CTkFrame(self.frame_apps, fg_color="transparent")
        self.apps_grid_container.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.apps_grid_container.grid_columnconfigure((0, 1), weight=1)

        row = 0
        col = 0
        for app_id, data in ADOBE_APPS_CATALOG.items():
            self.create_app_card(self.apps_grid_container, row, col, app_id, data)
            col += 1
            if col > 1:
                col = 0
                row += 1

    def create_app_card(self, parent, row, col, app_id, data):
        card = ctk.CTkFrame(parent, fg_color="#1e293b", corner_radius=8)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        top_f = ctk.CTkFrame(card, fg_color="transparent")
        top_f.pack(padx=12, pady=(10, 4), fill="x")
        top_f.grid_columnconfigure(0, weight=1)

        t_lbl = ctk.CTkLabel(top_f, text=f"{data['icon']} {data['name']}", font=ctk.CTkFont(size=14, weight="bold"))
        t_lbl.grid(row=0, column=0, sticky="w")

        cat_lbl = ctk.CTkLabel(card, text=f"{data['category']} • {data.get('description', '')}", font=ctk.CTkFont(size=11), text_color="#94a3b8", wraplength=310, justify="left")
        cat_lbl.pack(padx=12, pady=(0, 10), anchor="w")

        btn = ctk.CTkButton(card, text=f"🔧 Fix {data['short_name']}", fg_color="#0284c7", hover_color="#0369a1", command=lambda aid=app_id: self.run_single_app_fix_thread(aid))
        btn.pack(padx=12, pady=(0, 6 if app_id == "premiere" else 12), fill="x")

        if app_id == "premiere":
            btn_freeze = ctk.CTkButton(
                card,
                text="🧊 Fix Premiere Freeze (Anti-Freeze)",
                fg_color="#0c4a6e",
                hover_color="#0284c7",
                border_color="#38bdf8",
                border_width=1,
                command=self.run_premiere_freeze_thread
            )
            btn_freeze.pack(padx=12, pady=(0, 6), fill="x")

            btn_runtime = ctk.CTkButton(
                card,
                text="🛡️ Fix RuntimeInstaller.dll (0xc0000005)",
                fg_color="#334155",
                hover_color="#475569",
                border_color="#94a3b8",
                border_width=1,
                command=self.run_runtime_installer_fix_thread
            )
            btn_runtime.pack(padx=12, pady=(0, 12), fill="x")

    # ---------------- VIEW 4: CC ROOT CLEANER & NUCLEAR PURGE ---------------- #
    def setup_nuclear_view(self):
        self.frame_nuclear = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        self.frame_nuclear.grid_columnconfigure(0, weight=1)

        # CC Root Uninstaller Banner
        cc_banner = ctk.CTkFrame(self.frame_nuclear, fg_color="#450a0a", corner_radius=10, border_color="#ef4444", border_width=1)
        cc_banner.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        cc_title = ctk.CTkLabel(cc_banner, text="🗑️ Adobe Creative Cloud Root Uninstaller & Service Cleaner", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff")
        cc_title.pack(padx=20, pady=(15, 5), anchor="w")

        cc_desc = ctk.CTkLabel(
            cc_banner,
            text="Πλήρης απεγκατάσταση Creative Cloud Desktop, τερματισμός και διαγραφή Windows Services "
                 "(AdobeUpdateService, AGSService, AdobeARMservice), αφαίρεση background Scheduled Tasks, εκτέλεση του επίσημου Adobe Cleaner Tool "
                 "και καθαρισμός όλων των καταλοίπων OOBE, SLStore, SLData και Program Files.",
            font=ctk.CTkFont(size=12), text_color="#fecaca", wraplength=700, justify="left"
        )
        cc_desc.pack(padx=20, pady=(0, 15), anchor="w")

        self.btn_cc_uninstall = ctk.CTkButton(
            cc_banner,
            text="🗑️ UNINSTALL CREATIVE CLOUD & WIPE ALL SERVICES (ΠΛΗΡΗΣ ΑΠΕΓΚΑΤΑΣΤΑΣΗ CC)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#b91c1c", hover_color="#991b1b", height=44,
            command=self.run_cc_uninstaller_thread
        )
        self.btn_cc_uninstall.pack(padx=20, pady=(0, 18), fill="x")

        # Nuclear Purge Banner
        n_banner = ctk.CTkFrame(self.frame_nuclear, fg_color="#7f1d1d", corner_radius=10)
        n_banner.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        n_title = ctk.CTkLabel(n_banner, text="🔥 Complete Nuclear Root Purge (Καθαρισμός Μέχρι τη Ρίζα)", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ffffff")
        n_title.pack(padx=20, pady=(15, 5), anchor="w")

        n_desc = ctk.CTkLabel(
            n_banner,
            text="Σαρώνει και καθαρίζει: Windows Firewall rules (loopback socket access), "
                 "Windows Credential Manager (απαλοιφή stale licensing tokens), Multi-Drive Caches σε όλους τους δίσκους και Registry MRU / Layouts.",
            font=ctk.CTkFont(size=12), text_color="#fecaca", wraplength=700, justify="left"
        )
        n_desc.pack(padx=20, pady=(0, 15), anchor="w")

        self.btn_nuclear_run = ctk.CTkButton(
            n_banner,
            text="🔥 ΕΚΤΕΛΕΣΗ ΠΛΗΡΟΥΣ ΚΑΘΑΡΙΣΜΟΥ ΡΙΖΑΣ (FIREWALL, CREDENTIALS, CACHES)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c", height=40,
            command=self.run_nuclear_purge_thread
        )
        self.btn_nuclear_run.pack(padx=20, pady=(0, 18), fill="x")

        # Telemetry info
        self.cc_info_frame = ctk.CTkFrame(self.frame_nuclear, fg_color="#1e293b", corner_radius=8)
        self.cc_info_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        lbl_inf_t = ctk.CTkLabel(self.cc_info_frame, text="Creative Cloud Machine Telemetry:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        lbl_inf_t.pack(padx=15, pady=(12, 4), anchor="w")

        self.lbl_cc_telemetry = ctk.CTkLabel(
            self.cc_info_frame, text="Scanning Creative Cloud presence...",
            font=ctk.CTkFont(size=12, family="Consolas"), justify="left", text_color="#cbd5e1"
        )
        self.lbl_cc_telemetry.pack(padx=15, pady=(0, 12), anchor="w")

    # ---------------- VIEW 5: VERSIONS & ROLLBACK ---------------- #
    def setup_versions_view(self):
        self.frame_versions = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        self.frame_versions.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self.frame_versions, text="Adobe Versions Stability & Rollback Hub", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.versions_container = ctk.CTkFrame(self.frame_versions, fg_color="transparent")
        self.versions_container.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.versions_container.grid_columnconfigure(0, weight=1)

        help_frame = ctk.CTkFrame(self.frame_versions, fg_color="#1e293b", corner_radius=8)
        help_frame.grid(row=2, column=0, padx=10, pady=15, sticky="ew")
        help_frame.grid_columnconfigure((0, 1), weight=1)

        lbl_actions = ctk.CTkLabel(help_frame, text="External Official Helpers & Cleaners", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_actions.grid(row=0, column=0, columnspan=2, padx=15, pady=(12, 8), sticky="w")

        btn_cleaner = ctk.CTkButton(help_frame, text="Download Official Adobe CC Cleaner Tool", fg_color="#475569", hover_color="#64748b", command=self.vmanager.open_adobe_cleaner_tool)
        btn_cleaner.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")

        btn_driver = ctk.CTkButton(help_frame, text="Download NVIDIA Studio Drivers", fg_color="#475569", hover_color="#64748b", command=self.vmanager.open_nvidia_studio_drivers)
        btn_driver.grid(row=1, column=1, padx=10, pady=(0, 15), sticky="ew")

    # ---------------- VIEW 6: CONSOLE ---------------- #
    def setup_console_view(self):
        self.frame_console = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frame_console.grid_columnconfigure(0, weight=1)
        self.frame_console.grid_rowconfigure(1, weight=1)

        c_top = ctk.CTkFrame(self.frame_console, fg_color="transparent")
        c_top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        c_top.grid_columnconfigure(0, weight=1)

        lbl_log = ctk.CTkLabel(c_top, text="Real-time Execution & Repair Console", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_log.grid(row=0, column=0, sticky="w")

        btn_launch = ctk.CTkButton(
            c_top, text="🚀 Launch Repaired Premiere Pro",
            fg_color="#10b981", hover_color="#059669",
            command=self.launch_repaired_premiere
        )
        btn_launch.grid(row=0, column=1, sticky="e")

        self.txt_console = ctk.CTkTextbox(
            self.frame_console, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#090d16", text_color="#38bdf8"
        )
        self.txt_console.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def append_log(self, text):
        def _update():
            self.txt_console.insert("end", text + "\n")
            self.txt_console.see("end")
        self.after(0, _update)

    # ---------------- BACKGROUND WORKERS ---------------- #
    def run_diagnostics_thread(self):
        self.badge_status.configure(text="DIAGNOSING...", fg_color="#ca8a04")
        threading.Thread(target=self._diagnostics_worker, daemon=True).start()

    def _diagnostics_worker(self):
        self.logger.info("Multi-Disk & Multi-GPU Auditor: Auditing all system hardware and storage drives...")
        res = self.diag.run_full_diagnosis()
        self.diag_data = res
        cc_stat = self.cc_cleaner.detect_creative_cloud_presence()
        self.after(0, lambda: self.render_diagnostics(res, cc_stat))

    def render_diagnostics(self, res, cc_stat):
        if res["status"] == "CRITICAL":
            self.badge_status.configure(text=f"CRITICAL ({res['critical_count']} Issues)", fg_color="#dc2626")
        elif res["status"] == "WARNING":
            self.badge_status.configure(text=f"WARNING ({res['warning_count']} Warnings)", fg_color="#d97706")
        else:
            self.badge_status.configure(text="HEALTHY / ALL CLEAR", fg_color="#16a34a")

        sys_prof = res.get("system_profile", {})
        os_info = sys_prof.get("os", {})
        cpu_info = sys_prof.get("cpu", {})
        gpu_info = sys_prof.get("gpu", {})
        drives = sys_prof.get("drives", [])

        # Top Metric Cards
        self.card_cpu_os.configure(text=f"{os_info.get('caption', 'Windows')}\n{cpu_info.get('name', 'CPU')[:25]}")
        self.card_gpu.configure(text=f"{gpu_info.get('primary_dgpu', 'GPU')[:25]}\nDual-GPU: {gpu_info.get('is_dual_gpu')}")
        cache = res["cache_info"]
        self.card_cache.configure(text=f"{cache['total_size_mb']} MB\n({cache['total_files']} files)")
        font_info = res.get("font_info", {})
        self.card_fonts.configure(text=f"{font_info.get('total_files', 0)} files\n({font_info.get('total_size_kb', 0)} KB)")

        # Detailed Multi-GPU Box
        gpu_lines = []
        for idx, g in enumerate(gpu_info.get("gpus", []), 1):
            tag = " [Dedicated High-Perf dGPU]" if g.get("is_dgpu") else " [Integrated iGPU]"
            disp = " • Active Display Output" if g.get("is_active_display") else ""
            line = f"[{idx}] {g['name']} ({g['vendor']}) | VRAM: {g.get('vram_gb', 0)} GB | Status: {g.get('status')}{tag}{disp}\n    Driver: {g['driver']} ({g['driver_date']}) | Video Mode: {g.get('display_mode')}"
            gpu_lines.append(line)
        self.lbl_gpu_specs.configure(text="\n".join(gpu_lines) or "No GPUs detected.")

        # Detailed Multi-Disk Box
        disk_lines = []
        for d in drives:
            vol = f" [{d.get('VolumeName')}]" if d.get('VolumeName') else ""
            dtype = d.get('DriveType', 'Fixed')
            fs = d.get('FileSystem', 'NTFS')
            line = f"• Drive {d['Name']}{vol} ({dtype}, {fs}) -> {d['FreeGB']} GB Free / {d['TotalGB']} GB Total"
            disk_lines.append(line)
        self.lbl_disk_specs.configure(text="\n".join(disk_lines) or "No logical drives found.")

        # Creative Cloud Telemetry
        cc_text = (
            f"• CC Desktop App Installed: {cc_stat.get('has_cc_installed')}\n"
            f"• Local Uninstaller Path: {cc_stat.get('uninstaller_path') or 'Not Found'}\n"
            f"• Running Background Services ({len(cc_stat.get('detected_services', []))}): {', '.join(cc_stat.get('detected_services', [])) or 'None'}\n"
            f"• Active Scheduled Tasks ({len(cc_stat.get('detected_tasks', []))}): {', '.join(cc_stat.get('detected_tasks', [])) or 'None'}"
        )
        self.lbl_cc_telemetry.configure(text=cc_text)

        # Render Detected Adobe Applications List
        for widget in self.apps_container.winfo_children():
            widget.destroy()

        active_apps = [a for a in res["installations"] if a.get("exists")]
        if not active_apps:
            no_a = ctk.CTkLabel(self.apps_container, text="No Adobe installations found on disk.", text_color="#94a3b8")
            no_a.pack(padx=10, pady=5)
        else:
            for app in active_apps:
                app_card = ctk.CTkFrame(self.apps_container, fg_color="#1e293b", corner_radius=6)
                app_card.pack(padx=2, pady=3, fill="x")
                app_card.grid_columnconfigure(1, weight=1)

                icon_lbl = ctk.CTkLabel(app_card, text=app.get("icon", "⚡"), font=ctk.CTkFont(size=18))
                icon_lbl.grid(row=0, column=0, padx=10, pady=8)

                info_txt = f"{app['name']} (v{app.get('version', 'Unknown')})\n{app['exe_path']}"
                info_lbl = ctk.CTkLabel(app_card, text=info_txt, font=ctk.CTkFont(size=12), justify="left", text_color="#e2e8f0")
                info_lbl.grid(row=0, column=1, padx=5, pady=8, sticky="w")

                badges_frame = ctk.CTkFrame(app_card, fg_color="transparent")
                badges_frame.grid(row=0, column=2, padx=10, pady=8, sticky="e")

                if app.get("has_non_ascii_path"):
                    warn_b = ctk.CTkLabel(badges_frame, text="⚠️ Non-ASCII Path", fg_color="#b91c1c", corner_radius=4, padx=6, font=ctk.CTkFont(size=10, weight="bold"))
                    warn_b.pack(side="left", padx=4)

                gpu_col = "#059669" if app.get("gpu_high_performance") else "#ca8a04"
                gpu_txt = "GPU: High-Perf" if app.get("gpu_high_performance") else "GPU: Unassigned"
                gpu_b = ctk.CTkLabel(badges_frame, text=gpu_txt, fg_color=gpu_col, corner_radius=4, padx=6, font=ctk.CTkFont(size=10, weight="bold"))
                gpu_b.pack(side="left", padx=4)

        # Render Issues list
        for widget in self.issues_container.winfo_children():
            widget.destroy()

        if not res["issues"]:
            no_iss = ctk.CTkLabel(
                self.issues_container, text="✔ No active issues detected! All Adobe applications are configured cleanly.",
                font=ctk.CTkFont(size=14), text_color="#22c55e"
            )
            no_iss.pack(padx=10, pady=10, anchor="w")
        else:
            for issue in res["issues"]:
                is_crit = issue["severity"] == "CRITICAL"
                is_warn = issue["severity"] == "WARNING"
                bg_col = "#451a1a" if is_crit else ("#422006" if is_warn else "#1e293b")
                border_col = "#ef4444" if is_crit else ("#f59e0b" if is_warn else "#3b82f6")

                card = ctk.CTkFrame(self.issues_container, fg_color=bg_col, border_color=border_col, border_width=1, corner_radius=8)
                card.pack(padx=5, pady=5, fill="x")

                hdr = ctk.CTkLabel(card, text=f"[{issue['severity']}] {issue['title']}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff")
                hdr.pack(padx=12, pady=(10, 2), anchor="w")

                desc = ctk.CTkLabel(card, text=issue["description"], font=ctk.CTkFont(size=12), text_color="#e2e8f0", wraplength=720, justify="left")
                desc.pack(padx=12, pady=(0, 10), anchor="w")

    def run_premiere_freeze_thread(self):
        if self.is_fixing:
            return
        self.is_fixing = True
        if hasattr(self, "btn_fix_freeze"):
            self.btn_fix_freeze.configure(state="disabled", text="ΕΠΙΔΙΟΡΘΩΣΗ FREEZE ΣΕ ΕΞΕΛΙΞΗ...")
        if hasattr(self, "btn_side_freeze"):
            self.btn_side_freeze.configure(state="disabled", text="⏳ FIXING FREEZE...")
        self.select_frame("console")

        def _worker():
            try:
                if not self.diag_data:
                    self.diag_data = self.diag.run_full_diagnosis()
                res = self.u_repair.fix_premiere_pro_freeze(self.diag_data.get("installations", []))
                self.logger.success("🧊 Premiere Pro 2-Minute Anti-Freeze protocol executed successfully!")
                self.after(0, lambda: messagebox.showinfo(
                    "Premiere Pro 2-Minute Anti-Freeze Complete",
                    f"Το πάγωμα (2-Minute Freeze) του Premiere Pro επιδιορθώθηκε επιτυχώς!\n\n"
                    f"• Audio Device Sleep Deadlock: dvaaudiodevice.AlwaysRunning=false ({res.get('debug_db_patched', 0)} versions)\n"
                    f"• Dual-GPU Conflict Resolved: Intel iGPU Decode OFF / NVIDIA RTX 3060 NVDEC ({res.get('prefs_patched', 0)} profiles)\n"
                    f"• Windows GPU TDR Delay Boost: {'10 Seconds (Ενεργό)' if res.get('tdr_applied') else 'Standard'}\n"
                    f"• Media & Conforming Cache Purged: {res.get('cache_files_purged', 0)} αρχεία (.pek, .cfa, .mcdb)\n"
                    f"• Orphaned Lockfiles Removed: {res.get('locks_removed', 0)}\n"
                    f"• DirectX High-Perf GPU Affinity: {res.get('gpu_locked', 0)} paths\n\n"
                    f"Μπορείτε τώρα να ανοίξετε το Premiere Pro χωρίς παγώματα στα 2 λεπτά!"
                ))
            except Exception as e:
                self.logger.error(f"Error during Premiere Pro freeze repair: {e}")
            finally:
                self.is_fixing = False
                if hasattr(self, "btn_fix_freeze"):
                    self.after(0, lambda: self.btn_fix_freeze.configure(state="normal", text="🧊 ΕΠΙΔΙΟΡΘΩΣΗ FREEZE PREMIERE PRO (FIX 2-MIN TIMEOUT & AUDIO/GPU NOW)"))
                if hasattr(self, "btn_side_freeze"):
                    self.after(0, lambda: self.btn_side_freeze.configure(state="normal", text="🧊 FIX PREMIERE FREEZE"))
                self.run_diagnostics_thread()

        threading.Thread(target=_worker, daemon=True).start()

    def browse_custom_exe(self):
        chosen = filedialog.askopenfilename(
            title="Επιλογή Εκτελέσιμου Adobe (π.χ. Adobe Premiere Pro.exe)",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if chosen and os.path.isfile(chosen):
            if not hasattr(self, "custom_exes"):
                self.custom_exes = []
            if chosen not in self.custom_exes:
                self.custom_exes.append(chosen)
            self.logger.success(f"📂 Επιλέχθηκε προσαρμοσμένο εκτελέσιμο: {chosen}")
            if messagebox.askyesno(
                "Εκτέλεση Επιδιόρθωσης",
                f"Επιλέξατε το εκτελέσιμο:\n{chosen}\n\n"
                f"Θέλετε να εκτελεστεί άμεσα η πλήρης επιδιόρθωση RuntimeInstaller.dll (0xc0000005) & Anti-Freeze για αυτή την εγκατάσταση;"
            ):
                self.run_runtime_installer_fix_thread(custom_exe=chosen)

    def run_runtime_installer_fix_thread(self, custom_exe=None):
        if self.is_fixing:
            return
        self.is_fixing = True
        self.select_frame("console")

        def _worker():
            try:
                if not self.diag_data:
                    self.diag_data = self.diag.run_full_diagnosis()
                apps = self.diag_data.get("installations", [])
                exes = [a["exe_path"] for a in apps if a.get("exists") and a.get("exe_path")]
                if hasattr(self, "custom_exes"):
                    for ce in self.custom_exes:
                        if ce not in exes and os.path.isfile(ce):
                            exes.append(ce)
                if custom_exe and custom_exe not in exes and os.path.isfile(custom_exe):
                    exes.append(custom_exe)
                res = self.u_repair.fix_runtime_installer_crash(exes)
                self.logger.success("🛡️ RuntimeInstaller.dll (0xc0000005) fix executed successfully!")
                self.after(0, lambda: messagebox.showinfo(
                    "RuntimeInstaller Fix Complete",
                    f"Η επιδιόρθωση του RuntimeInstaller.dll (0xc0000005) ολοκληρώθηκε!\n\n"
                    f"• Καθαρισμός corrupt SLStore/SLCache/OOBE: {res.get("cleared_dirs", 0)} βάσεις δεδομένων\n"
                    f"• Επαναφορά δικαιωμάτων NTFS (Full Control) στα runtime dirs\n"
                    f"• Έλεγχος & ανάπτυξη Visual C++ 2015-2022 runtimes\n"
                    f"• DirectX High-Perf GPU Affinity & Firewall Loopback rules\n\n"
                    f"Εφαρμόστηκε στα εκτελέσιμα:\n" + "\n".join(res.get("resolved_exes", exes)) + "\n\n"
                    f"Μπορείτε τώρα να εκκινήσετε το Premiere Pro!"
                ))
            except Exception as e:
                self.logger.error(f"Error fixing RuntimeInstaller.dll: {e}")
            finally:
                self.is_fixing = False
                self.run_diagnostics_thread()

        threading.Thread(target=_worker, daemon=True).start()

    def run_universal_fix_thread(self):
        if self.is_fixing:
            return
        self.is_fixing = True
        self.btn_run_universal.configure(state="disabled", text="ΕΠΙΔΙΟΡΘΩΣΗ ΣΕ ΕΞΕΛΙΞΗ... (RUNNING DEFAULT 1-CLICK)")
        self.select_frame("console")

        def _worker():
            try:
                if not self.diag_data:
                    self.diag_data = self.diag.run_full_diagnosis()
                drives = self.scanner.get_all_logical_drives()
                res = self.u_repair.execute_complete_universal_repair(self.diag_data.get("installations", []), drives)
                self.logger.success("⚡ Complete 1-Click Universal Fix successfully executed!")
                rt_info = res.get("runtime_installer", {})
                frz_info = res.get("freeze", {})
                self.after(0, lambda: messagebox.showinfo(
                    "Universal Fix Complete",
                    f"Η πλήρης επιδιόρθωση ολοκληρώθηκε επιτυχώς για όλες τις εφαρμογές Adobe!\n\n"
                    f"• 🛡️ RuntimeInstaller.DLL Fix: {rt_info.get('cleared_dirs', 0)} βάσεις SLStore/SLCache/OOBE & δικαιώματα NTFS Full Control\n"
                    f"• 🧊 Premiere 2-Min Anti-Freeze: {frz_info.get('debug_db_patched', 0)} debug databases & MISO audio AI bypass ενεργό\n"
                    f"• 🔗 NTFS ASCII Junctions: {res['junctions_created']}\n"
                    f"• 🎮 High-Performance GPU Overrides: {res['gpu_overrides']}\n"
                    f"• 🔤 Font Cache Files Purged: {res['font_caches_purged']}\n"
                    f"• 💾 Media & Scratch Reclaimed: {res['cache_purged']['freed_mb']} MB\n"
                    f"• 🔌 Plugin & Hardware Registries Reset: {res['plugin_resets']}\n"
                    f"• 🧱 Firewall Loopback Rules Configured: {res['firewall_rules']}\n"
                    f"• 🔑 Stale Credentials Purged: {res['credentials_purged']}\n\n"
                    f"Μπορείτε τώρα να ανοίξετε το Premiere Pro και όλες τις εφαρμογές Adobe χωρίς κανένα κόλλημα!"
                ))
            except Exception as e:
                self.logger.error(f"Error during universal repair: {e}")
            finally:
                self.is_fixing = False
                self.after(0, lambda: self.btn_run_universal.configure(state="normal", text="⚡ ΕΚΤΕΛΕΣΗ ΠΛΗΡΟΥΣ 1-CLICK ΕΠΙΔΙΟΡΘΩΣΗΣ (DEFAULT REPAIR ALL)"))
                self.run_diagnostics_thread()

        threading.Thread(target=_worker, daemon=True).start()

    def run_custom_fix_thread(self):
        if self.is_fixing:
            return
        self.is_fixing = True
        self.btn_run_custom.configure(state="disabled", text="ΕΠΙΔΙΟΡΘΩΣΗ ΣΕ ΕΞΕΛΙΞΗ... (RUNNING CUSTOM 1-CLICK)")
        self.select_frame("console")

        options = {
            "kill_processes": self.opt_kill_procs.get(),
            "create_junctions": self.opt_junctions.get(),
            "gpu_affinity": self.opt_gpu_affinity.get(),
            "purge_fonts": self.opt_purge_fonts.get(),
            "purge_caches": self.opt_purge_caches.get(),
            "reset_plugins": self.opt_reset_plugins.get(),
            "firewall_rules": self.opt_firewall.get(),
            "purge_credentials": self.opt_credentials.get(),
            "create_shortcuts": self.opt_shortcuts.get(),
            "fix_runtime_installer": self.opt_fix_runtime.get(),
            "fix_freeze": self.opt_fix_freeze.get()
        }

        def _worker():
            try:
                if not self.diag_data:
                    self.diag_data = self.diag.run_full_diagnosis()
                drives = self.scanner.get_all_logical_drives()
                res = self.u_repair.execute_custom_repair(
                    all_detected_apps=self.diag_data.get("installations", []),
                    all_drives=drives,
                    options=options
                )
                self.logger.success("🛠️ Custom 1-Click Fix successfully executed!")
                self.after(0, lambda: messagebox.showinfo(
                    "Custom 1-Click Complete",
                    f"Η προσαρμοσμένη επιδιόρθωση ολοκληρώθηκε επιτυχώς!\n\n"
                    f"• Processes Stopped: {res.get('processes_stopped', 0)}\n"
                    f"• NTFS ASCII Junctions: {res['junctions_created']}\n"
                    f"• GPU Overrides: {res['gpu_overrides']}\n"
                    f"• Font Caches Purged: {res['font_caches_purged']}\n"
                    f"• Cache Reclaimed: {res['cache_purged']['freed_mb']} MB\n"
                    f"• Firewall Rules Configured: {res['firewall_rules']}\n"
                    f"• Stale Credentials Purged: {res['credentials_purged']}"
                ))
            except Exception as e:
                self.logger.error(f"Error during custom repair: {e}")
            finally:
                self.is_fixing = False
                self.after(0, lambda: self.btn_run_custom.configure(state="normal", text="🛠️ ΕΚΤΕΛΕΣΗ CUSTOM 1-CLICK ΕΠΙΔΙΟΡΘΩΣΗΣ (RUN MY SELECTION)"))
                self.run_diagnostics_thread()

        threading.Thread(target=_worker, daemon=True).start()

    def run_single_app_fix_thread(self, app_id):
        self.select_frame("console")
        def _worker():
            try:
                if not self.diag_data:
                    self.diag_data = self.diag.run_full_diagnosis()
                app_res = self.u_repair.repair_single_adobe_app(app_id, self.diag_data.get("installations", []))
                self.after(0, lambda: messagebox.showinfo(
                    "Targeted Fix Complete",
                    f"Η στοχευμένη επιδιόρθωση για το {app_id} ολοκληρώθηκε επιτυχώς!"
                ))
            except Exception as e:
                self.logger.error(f"Error during app repair: {e}")
            finally:
                self.run_diagnostics_thread()

        threading.Thread(target=_worker, daemon=True).start()

    def run_nuclear_purge_thread(self):
        self.select_frame("console")
        self.btn_nuclear_run.configure(state="disabled", text="ΕΚΤΕΛΕΣΗ ΚΑΘΑΡΙΣΜΟΥ ΡΙΖΑΣ... (RUNNING)")

        def _worker():
            try:
                if not self.diag_data:
                    self.diag_data = self.diag.run_full_diagnosis()
                exes = [i["exe_path"] for i in self.diag_data.get("installations", []) if i.get("exists")]
                drives = self.scanner.get_all_logical_drives()
                self.nuclear.execute_complete_nuclear_purge(exes, drives)
                self.after(0, lambda: messagebox.showinfo("Nuclear Purge Complete", "Καθαρισμός μέχρι τη ρίζα ολοκληρώθηκε!\nΌλα τα Firewall rules, credentials, caches και registry nodes έχουν εξυγιανθεί."))
            except Exception as e:
                self.logger.error(f"Error during nuclear purge: {e}")
            finally:
                self.after(0, lambda: self.btn_nuclear_run.configure(state="normal", text="🔥 ΕΚΤΕΛΕΣΗ ΠΛΗΡΟΥΣ ΚΑΘΑΡΙΣΜΟΥ ΡΙΖΑΣ (FIREWALL, CREDENTIALS, CACHES)"))
                self.run_diagnostics_thread()

        threading.Thread(target=_worker, daemon=True).start()

    def run_cc_uninstaller_thread(self):
        confirm = messagebox.askyesno(
            "Επιβεβαίωση Απεγκατάστασης Creative Cloud",
            "Είστε βέβαιοι ότι θέλετε να προχωρήσετε σε ΠΛΗΡΗ απεγκατάσταση του Adobe Creative Cloud και διαγραφή όλων των Adobe Services;"
        )
        if not confirm:
            return

        self.select_frame("console")
        self.btn_cc_uninstall.configure(state="disabled", text="ΑΠΕΓΚΑΤΑΣΤΑΣΗ ΣΕ ΕΞΕΛΙΞΗ... (RUNNING)")

        def _worker():
            try:
                res = self.cc_cleaner.execute_complete_cc_uninstaller_suite()
                self.after(0, lambda: messagebox.showinfo(
                    "Creative Cloud Cleaned",
                    f"Η απεγκατάσταση ολοκληρώθηκε!\n\n"
                    f"• Services Removed: {len(res['deleted_services'])}\n"
                    f"• Tasks Removed: {res['tasks_removed']}\n"
                    f"• Startup Keys Removed: {res['startup_keys_removed']}\n"
                    f"• Wiped Directories: {res['wiped_directories']}"
                ))
            except Exception as e:
                self.logger.error(f"Error during Creative Cloud uninstallation: {e}")
            finally:
                self.after(0, lambda: self.btn_cc_uninstall.configure(state="normal", text="🗑️ UNINSTALL CREATIVE CLOUD & WIPE ALL SERVICES"))
                self.run_diagnostics_thread()

        threading.Thread(target=_worker, daemon=True).start()

    def manual_check_ota(self):
        self.btn_ota_check.configure(state="disabled", text="Checking...")

        def _worker():
            try:
                info = self.ota.check_for_updates()
                self.ota_info = info
                self.after(0, lambda: self.btn_ota_check.configure(state="normal", text="🔄 Check Updates"))
                if info.get("update_available"):
                    self.after(0, lambda: self.show_ota_dialog(info))
                else:
                    self.after(0, lambda: messagebox.showinfo(
                        "OTA Updates • Ενημερώσεις",
                        f"✔ Η εφαρμογή είναι πλήρως ενημερωμένη!\n\n"
                        f"Τρέχουσα Έκδοση: v{CURRENT_VERSION}\n"
                        f"Build: {CURRENT_BUILD}\n"
                        f"Δεν υπάρχουν εκκρεμείς ενημερώσεις στο GitHub repository."
                    ))
            except Exception as e:
                self.after(0, lambda: self.btn_ota_check.configure(state="normal", text="🔄 Check Updates"))
                self.after(0, lambda: messagebox.showerror("OTA Error", f"Σφάλμα ελέγχου ενημερώσεων: {e}"))

        threading.Thread(target=_worker, daemon=True).start()

    def silent_startup_ota_check(self):
        import time
        time.sleep(4)
        try:
            info = self.ota.check_for_updates()
            self.ota_info = info
            if info.get("update_available"):
                self.after(0, lambda: self.lbl_ota_status.configure(text="🚀 Update Available!", text_color="#10b981"))
                self.after(0, lambda: self.btn_ota_check.configure(text="⚡ Install Update", fg_color="#10b981", hover_color="#059669"))
        except Exception:
            pass

    def show_ota_dialog(self, update_info):
        import time
        dlg = ctk.CTkToplevel(self)
        dlg.title("⚡ Over-The-Air (OTA) Live Auto-Updater")
        dlg.geometry("560x440")
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        dlg.grab_set()

        lbl_h = ctk.CTkLabel(dlg, text="⚡ Over-The-Air (OTA) Auto-Updater", font=ctk.CTkFont(size=18, weight="bold"), text_color="#38bdf8")
        lbl_h.pack(padx=20, pady=(18, 2))

        lbl_sub = ctk.CTkLabel(dlg, text=f"Τρέχουσα έκδοση: v{CURRENT_VERSION}  ➔  Νέα έκδοση: v{update_info.get('latest_version')}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#10b981")
        lbl_sub.pack(padx=20, pady=(0, 10))

        box = ctk.CTkTextbox(dlg, height=160, corner_radius=8, fg_color="#1e293b")
        box.pack(padx=20, pady=(0, 15), fill="x")
        box.insert("1.0", "📋 ΤΙ ΝΕΟ ΥΠΑΡΧΕΙ ΣΤΗ ΝΕΑ ΕΚΔΟΣΗ:\n\n")
        changelog = update_info.get("changelog", [])
        if isinstance(changelog, list):
            for item in changelog:
                box.insert("end", f"• {item}\n")
        else:
            box.insert("end", str(changelog))
        box.configure(state="disabled")

        lbl_status = ctk.CTkLabel(dlg, text="Έτοιμο για αυτόματη λήψη και εγκατάσταση.", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        lbl_status.pack(padx=20, pady=(0, 4))

        progress = ctk.CTkProgressBar(dlg, height=14)
        progress.pack(padx=20, pady=(0, 15), fill="x")
        progress.set(0)

        btn_action = ctk.CTkButton(dlg, text="🚀 Λήψη & Αυτόματη Εγκατάσταση (OTA)", font=ctk.CTkFont(size=14, weight="bold"), fg_color="#10b981", hover_color="#059669", height=40)
        btn_action.pack(padx=20, pady=(0, 15), fill="x")

        def _start_download():
            btn_action.configure(state="disabled", text="ΛΗΨΗ ΣΕ ΕΞΕΛΙΞΗ...")

            def _worker():
                try:
                    def _on_prog(pct, cur, total):
                        mb_c = round(cur / (1024*1024), 1)
                        mb_t = round(total / (1024*1024), 1)
                        self.after(0, lambda: progress.set(pct / 100.0))
                        self.after(0, lambda: lbl_status.configure(text=f"Λήψη: {pct}% ({mb_c} MB / {mb_t} MB)..."))

                    dl_file = self.ota.download_update(update_info["download_url"], progress_callback=_on_prog)
                    self.after(0, lambda: lbl_status.configure(text="Επαλήθευση αρχείου ΟΚ! Επανεκκίνηση εφαρμογής...", text_color="#10b981"))
                    self.after(0, lambda: progress.set(1.0))
                    time.sleep(1)
                    success = self.ota.apply_update_and_restart(dl_file)
                    if success:
                        self.after(0, self.destroy)
                    else:
                        self.after(0, lambda: messagebox.showerror("OTA Error", "Αποτυχία εκκίνησης του updater script."))
                except Exception as ex:
                    self.after(0, lambda: messagebox.showerror("OTA Error", f"Σφάλμα κατά τη λήψη OTA: {ex}"))
                    self.after(0, lambda: btn_action.configure(state="normal", text="Δοκιμάστε Ξανά"))

            threading.Thread(target=_worker, daemon=True).start()

        btn_action.configure(command=_start_download)

    def action_purge_fonts(self):
        self.select_frame("console")
        threading.Thread(target=lambda: (self.u_repair.purge_adobe_font_caches(), self.run_diagnostics_thread()), daemon=True).start()

    def action_fix_junction(self):
        self.select_frame("console")
        def _w():
            if not self.diag_data:
                self.diag_data = self.diag.run_full_diagnosis()
            for inst in self.diag_data.get("installations", []):
                if inst.get("has_non_ascii_path"):
                    src = os.path.dirname(inst.get("exe_path"))
                    self.repair.create_ascii_junction(src)
            self.run_diagnostics_thread()
        threading.Thread(target=_w, daemon=True).start()

    def action_fix_gpu(self):
        self.select_frame("console")
        def _w():
            if not self.diag_data:
                self.diag_data = self.diag.run_full_diagnosis()
            exes = [inst.get("exe_path") for inst in self.diag_data.get("installations", []) if inst.get("exists")]
            self.u_repair.apply_gpu_high_performance_to_all(exes)
            self.run_diagnostics_thread()
        threading.Thread(target=_w, daemon=True).start()

    def action_purge_cache(self):
        self.select_frame("console")
        threading.Thread(target=lambda: (self.u_repair.purge_all_adobe_scratch_and_media_caches(), self.run_diagnostics_thread()), daemon=True).start()

    def action_reset_prefs(self):
        self.select_frame("console")
        threading.Thread(target=lambda: (self.u_repair.reset_corrupt_plugin_and_preferences_caches(), self.run_diagnostics_thread()), daemon=True).start()

    def action_fix_firewall(self):
        self.select_frame("console")
        def _w():
            if not self.diag_data:
                self.diag_data = self.diag.run_full_diagnosis()
            exes = [inst.get("exe_path") for inst in self.diag_data.get("installations", []) if inst.get("exists")]
            self.u_repair.configure_universal_firewall_rules(exes)
            self.run_diagnostics_thread()
        threading.Thread(target=_w, daemon=True).start()

    def launch_repaired_premiere(self):
        if self.diag_data:
            for inst in self.diag_data.get("installations", []):
                p = inst.get("exe_path")
                if inst.get("exists") and not inst.get("has_non_ascii_path") and os.path.isfile(p):
                    self.logger.info(f"Launching clean Premiere Pro executable: {p}")
                    subprocess.Popen([p], cwd=os.path.dirname(p))
                    return

        # Fallback check
        for inst in self.diag.find_all_installations():
            p = inst.get("exe_path")
            if inst.get("exists") and os.path.isfile(p):
                self.logger.info(f"Launching Premiere Pro: {p}")
                subprocess.Popen([p], cwd=os.path.dirname(p))
                return

        self.logger.error("Could not find Premiere Pro executable to launch.")

# Backwards compatibility alias
PremiereDoctorApp = AdobeMasterDoctorApp

if __name__ == "__main__":
    app = AdobeMasterDoctorApp()
    app.mainloop()
