"""
RuneBox // Subwoofer Enclosure Lab
gui.py - Modern Dark CustomTkinter Graphical User Interface
Created by NfgOdin
"""

import os
import sys
import math
import json
from fractions import Fraction
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from typing import Dict, Any, List, Optional, Tuple

import acoustic_math as am
import geometry as gm
import subwoofer_database as sdb
import wiring_math as wm
import visualizer_3d as viz3d
import dashboard as db
import webbrowser


def get_asset_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller _MEIPASS.
    """
    try:
        base_path = sys._MEIPASS # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def decimal_to_fraction_str(val_inches: float, precision: int = 16) -> str:
    """
    Convert decimal inches to nearest shop tape measure fraction (e.g. 14.625 -> 14 5/8").
    """
    if val_inches is None:
        return "-"
    val = float(val_inches)
    is_neg = val < 0
    val = abs(val)
    whole = int(val)
    remainder = val - whole
    step = 1.0 / precision
    frac_units = round(remainder / step)
    if frac_units == precision:
        whole += 1
        frac_units = 0

    prefix = "-" if is_neg else ""
    if frac_units == 0:
        return f'{prefix}{whole}"'

    frac = Fraction(frac_units, precision)
    if whole > 0:
        return f'{prefix}{whole} {frac.numerator}/{frac.denominator}"'
    else:
        return f'{prefix}{frac.numerator}/{frac.denominator}"'


# Set application appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class RuneBoxApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RuneBox // Subwoofer Enclosure Lab — by NfgOdin")
        self.geometry("1320x900")
        self.minsize(1100, 760)

        # QOL Flags & State
        self.display_mode = "decimal"  # "decimal" or "fraction"
        self.unit_system = "imperial"  # "imperial" or "metric"
        self._updating_lock = False

        # Initialize core data models
        self.ts_params = am.TSParameters(
            fs=31.5,
            qts=0.45,
            qes=0.49,
            qms=5.2,
            vas_liters=45.0,
            xmax_mm=19.0,
            p_rms=750.0,
            sd_sq_cm=510.0,
            nominal_dia_inch=12.0,
            is_isobaric=False,
            num_drivers=1
        )

        self.enclosure = gm.EnclosureGeometry(
            shape="cuboid",
            ext_width=32.0,
            ext_height=14.5,
            ext_depth_bottom=16.0,
            ext_depth_top=16.0,
            wall_thickness=0.75,
            baffle_thickness=0.75,
            sub_cutout_dia_in=11.125,
            sub_flush_dia_in=12.5,
            sub_flush_depth_in=0.75,
            sub_displacement_cuft=0.14,
            num_subwoofers=1,
            is_chamber_isolated=False,
            bracing_displacement_cuft=0.06,
            port_type="slot",
            port_width_in=2.5,
            port_height_in=13.0,
            port_dia_in=4.0,
            num_ports=1,
            port_physical_length_in=26.0,
            is_l_port=True,
            port_wall_thickness=0.75
        )

        # Preset database loaded from modular subwoofer_database.py
        self.makers = ["Custom / Manual Entry"] + sdb.get_all_manufacturers()
        # Navigation state
        self.current_view = "home"
        self.nav_history: List[str] = ["home"]

        self._build_layout()
        self.update_all_calculations()

    def _build_layout(self):
        # Top Persistent Header Banner
        self.header_frame = ctk.CTkFrame(self, height=62, corner_radius=0, fg_color="#111318")
        self.header_frame.pack(side="top", fill="x")

        # Left: Navigation buttons (Back / Home)
        self.nav_left_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.nav_left_frame.pack(side="left", padx=12, pady=10)

        self.btn_nav_home = ctk.CTkButton(self.nav_left_frame, cursor="hand2", text="🏠 Home", width=74, height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1F2937", hover_color="#374151", text_color="#00E5FF",
            command=lambda: self.navigate_to("home")
        )

        self.btn_nav_back = ctk.CTkButton(self.nav_left_frame, cursor="hand2", text="⬅ Back", width=70, height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1F2937", hover_color="#374151", text_color="#ECEFF1",
            command=self.navigate_back
        )

        # Title & Dynamic Breadcrumb
        self.title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_box.pack(side="left", padx=10, pady=10)

        self.title_lbl = ctk.CTkLabel(
            self.title_box,
            text="RUNEBOX // SUBWOOFER ENCLOSURE LAB",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#00E5FF"
        )
        self.title_lbl.pack(anchor="w")

        self.breadcrumb_lbl = ctk.CTkLabel(
            self.title_box,
            text="HOME DASHBOARD",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#80D8FF"
        )
        self.breadcrumb_lbl.pack(anchor="w")

        # Right: Quick Global Action Buttons
        header_actions = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_actions.pack(side="right", padx=16, pady=10)

        self.btn_save_proj = ctk.CTkButton(header_actions, cursor="hand2", text="💾 Save", width=68, height=28,
            fg_color="#1E3A5F", hover_color="#2B4C7E", command=self._save_project
        )
        self.btn_save_proj.pack(side="left", padx=3)

        self.btn_load_proj = ctk.CTkButton(header_actions, cursor="hand2", text="📂 Load", width=68, height=28,
            fg_color="#1E3A5F", hover_color="#2B4C7E", command=self._load_project
        )
        self.btn_load_proj.pack(side="left", padx=3)

        self.btn_toggle_units = ctk.CTkButton(header_actions, cursor="hand2", text="Unit: Imperial", width=95, height=28,
            fg_color="#37474F", hover_color="#455A64", command=self._toggle_unit_system
        )
        self.btn_toggle_units.pack(side="left", padx=3)

        self.btn_toggle_fraction = ctk.CTkButton(header_actions, cursor="hand2", text="Tape: Decimals", width=105, height=28,
            fg_color="#263238", hover_color="#37474F", command=self._toggle_tape_fractions
        )
        self.btn_toggle_fraction.pack(side="left", padx=3)

        self.ebp_badge = ctk.CTkLabel(
            header_actions,
            text="EBP: 64.3 (Flexible)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#182834",
            text_color="#80D8FF",
            corner_radius=6,
            padx=8,
            pady=4
        )
        self.ebp_badge.pack(side="left", padx=6)

        # Main Workspace Host Container
        self.main_container = ctk.CTkFrame(self, fg_color="#0D1017", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # 1. Home Dashboard View
        self.view_dashboard = db.DashboardView(self.main_container, on_navigate=self.navigate_to)

        # 2. Enclosure Studio (Step-by-Step Box Builder with 5 stages)
        self.view_box_builder = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._build_enclosure_studio_view()

        # 3. Dedicated Wiring Lab View
        self.view_wiring_lab = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._build_wiring_lab_view()

        # 4. Global Settings View
        self.view_settings = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._build_settings_view()

        # Show initial view (Home)
        self._update_navigation_ui()

    def _build_enclosure_studio_view(self):
        """Constructs Enclosure Studio with step tabs and bottom Next/Previous buttons."""
        # Top Step Bar / Tabs
        self.studio_tabs = ctk.CTkTabview(
            self.view_box_builder, fg_color="#181B20",
            segmented_button_selected_color="#0091EA",
            command=self._on_studio_tab_changed
        )
        self.studio_tabs.pack(fill="both", expand=True, padx=14, pady=(8, 4))

        self.tab_ts = self.studio_tabs.add("1. Woofer & T/S Specs")
        self.tab_align = self.studio_tabs.add("2. Enclosure Alignment")
        self.tab_geom = self.studio_tabs.add("3. Dimensions & 3D Shape")
        self.tab_port = self.studio_tabs.add("4. Port Dynamics")
        self.tab_cut = self.studio_tabs.add("5. Fabrication Cut Sheet")

        self.studio_tab_names = [
            "1. Woofer & T/S Specs",
            "2. Enclosure Alignment",
            "3. Dimensions & 3D Shape",
            "4. Port Dynamics",
            "5. Fabrication Cut Sheet"
        ]

        self._build_ts_tab()
        self._build_align_tab()
        self._build_geom_tab()
        self._build_port_tab()
        self._build_cut_tab()

        # Bottom Studio Action Bar (Previous / Step Indicator / Next)
        bot_bar = ctk.CTkFrame(self.view_box_builder, height=44, fg_color="#11151C", corner_radius=8)
        bot_bar.pack(fill="x", padx=14, pady=(0, 10))

        self.btn_step_prev = ctk.CTkButton(bot_bar, cursor="hand2", text="⬅ Previous Step", width=130, height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#212A36", hover_color="#37474F", text_color="#ECEFF1",
            command=self._studio_prev_step
        )
        self.btn_step_prev.pack(side="left", padx=12, pady=6)

        self.lbl_step_indicator = ctk.CTkLabel(
            bot_bar, text="Step 1 of 5: Woofer & T/S Specs",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#00E5FF"
        )
        self.lbl_step_indicator.pack(side="left", expand=True)

        self.btn_step_next = ctk.CTkButton(bot_bar, cursor="hand2", text="Next Step ➡", width=130, height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0091EA", hover_color="#00B0FF", text_color="#FFFFFF",
            command=self._studio_next_step
        )
        self.btn_step_next.pack(side="right", padx=12, pady=6)

    def _build_wiring_lab_view(self):
        """Constructs dedicated full-screen Visual Wiring Lab."""
        self.tab_wire = self.view_wiring_lab
        self._build_wiring_tab()

    def _studio_prev_step(self):
        curr = self.studio_tabs.get()
        if curr in self.studio_tab_names:
            idx = self.studio_tab_names.index(curr)
            if idx > 0:
                self.studio_tabs.set(self.studio_tab_names[idx - 1])
                self._on_studio_tab_changed()

    def _studio_next_step(self):
        curr = self.studio_tabs.get()
        if curr in self.studio_tab_names:
            idx = self.studio_tab_names.index(curr)
            if idx < len(self.studio_tab_names) - 1:
                self.studio_tabs.set(self.studio_tab_names[idx + 1])
                self._on_studio_tab_changed()

    def _on_studio_tab_changed(self):
        curr = self.studio_tabs.get()
        if curr in self.studio_tab_names:
            idx = self.studio_tab_names.index(curr)
            self.lbl_step_indicator.configure(text=f"Step {idx + 1} of 5: {curr.split('. ')[-1]}")
            self.btn_step_prev.configure(state="normal" if idx > 0 else "disabled")
            if idx == len(self.studio_tab_names) - 1:
                self.btn_step_next.configure(text="✔ Final Cut Sheet", state="disabled")
            else:
                self.btn_step_next.configure(text="Next Step ➡", state="normal")

    def navigate_to(self, view_name: str):
        if view_name == self.current_view:
            return
        self.nav_history.append(view_name)
        self.current_view = view_name
        self._update_navigation_ui()

    def navigate_back(self):
        if len(self.nav_history) > 1:
            self.nav_history.pop()
            self.current_view = self.nav_history[-1]
        else:
            self.current_view = "home"
            self.nav_history = ["home"]
        self._update_navigation_ui()

    def _update_navigation_ui(self):
        # Hide all view panels
        self.view_dashboard.pack_forget()
        self.view_box_builder.pack_forget()
        self.view_wiring_lab.pack_forget()
        self.view_settings.pack_forget()

        # Update Back/Home button states
        if self.current_view == "home":
            self.btn_nav_home.pack_forget()
            self.btn_nav_back.pack_forget()
            self.breadcrumb_lbl.configure(text="HOME DASHBOARD")
            self.view_dashboard.pack(fill="both", expand=True)
        else:
            self.btn_nav_home.pack(side="left", padx=(0, 4))
            self.btn_nav_back.pack(side="left", padx=(0, 6))

            if self.current_view == "box_builder":
                self.breadcrumb_lbl.configure(text="ENCLOSURE STUDIO (BOX BUILDER)")
                self.view_box_builder.pack(fill="both", expand=True)
                self._redraw_visualizers()
            elif self.current_view == "wiring_lab":
                self.breadcrumb_lbl.configure(text="VISUAL WIRING & AMP LAB")
                self.view_wiring_lab.pack(fill="both", expand=True)
                self._update_wiring_calculations()
            elif self.current_view == "settings":
                self.breadcrumb_lbl.configure(text="GLOBAL APPLICATION SETTINGS")
                self.view_settings.pack(fill="both", expand=True)

    # -------------------------------------------------------------
    # TAB 1: Woofer & T/S Specs
    # -------------------------------------------------------------
    def _build_ts_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_ts, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Search Card
        search_card = ctk.CTkFrame(container, fg_color="#1A202C")
        search_card.pack(fill="x", pady=(0, 10), padx=4, ipady=4)

        ctk.CTkLabel(
            search_card, text="🔍 Instant Subwoofer Search:",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#00E5FF"
        ).pack(side="left", padx=14, pady=8)

        self.search_entry = ctk.CTkEntry(
            search_card, placeholder_text="Type brand or model (e.g. 'XXX 12', 'Sundown SA', 'Kicker L7', 'P3')...",
            width=360, fg_color="#10141D", border_color="#37474F"
        )
        self.search_entry.pack(side="left", padx=8, pady=8)
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)

        self.search_results_combo = ctk.CTkComboBox(
            search_card, values=["(Type to search database...)"],
            width=380, command=self._on_search_result_picked
        )
        self.search_results_combo.pack(side="left", padx=8, pady=8)

        # Hierarchical Subwoofer Selection
        preset_frame = ctk.CTkFrame(container, fg_color="#21252D")
        preset_frame.pack(fill="x", pady=(0, 10), padx=4, ipady=6)

        ctk.CTkLabel(preset_frame, text="1. Brand / Maker:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00E5FF").grid(row=0, column=0, padx=12, pady=(8, 2), sticky="w")
        self.maker_combo = ctk.CTkComboBox(preset_frame, values=self.makers, width=220, command=self._on_maker_selected)
        self.maker_combo.set("Custom / Manual Entry")
        self.maker_combo.grid(row=1, column=0, padx=10, pady=(2, 6), sticky="w")

        ctk.CTkLabel(preset_frame, text="2. Model Series Line:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00E5FF").grid(row=0, column=1, padx=12, pady=(8, 2), sticky="w")
        self.series_combo = ctk.CTkComboBox(preset_frame, values=["(Select Brand first)"], width=220, command=self._on_series_selected)
        self.series_combo.set("(Select Brand first)")
        self.series_combo.grid(row=1, column=1, padx=10, pady=(2, 6), sticky="w")

        ctk.CTkLabel(preset_frame, text="3. Exact Subwoofer Model:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00E5FF").grid(row=0, column=2, padx=12, pady=(8, 2), sticky="w")
        self.model_combo = ctk.CTkComboBox(preset_frame, values=["(Select Series first)"], width=340, command=self._on_model_selected)
        self.model_combo.set("(Select Series first)")
        self.model_combo.grid(row=1, column=2, padx=10, pady=(2, 6), sticky="w")

        self.btn_browse_menu = ctk.CTkButton(preset_frame, cursor="hand2", text="☰ Browse Full Tree", width=160,
            fg_color="#37474F", hover_color="#455A64", command=self._popup_hierarchical_menu
        )
        self.btn_browse_menu.grid(row=1, column=3, padx=12, pady=(2, 6), sticky="w")

        self.driver_desc_lbl = ctk.CTkLabel(
            preset_frame,
            text="Browse 96+ drivers across 21 car audio manufacturers (e.g. RE Audio -> XXX Series -> XXX 12, XXX 15, XXX 18).",
            font=ctk.CTkFont(size=12, slant="italic"), text_color="#90A4AE"
        )
        self.driver_desc_lbl.grid(row=2, column=0, columnspan=3, padx=16, pady=(4, 8), sticky="w")

        self.btn_save_custom_sub = ctk.CTkButton(preset_frame, cursor="hand2", text="💾 Save Custom Sub", width=160,
            fg_color="#00796B", hover_color="#00897B", command=self._on_save_custom_subwoofer_clicked
        )
        self.btn_save_custom_sub.grid(row=2, column=3, padx=12, pady=(4, 8), sticky="w")

        # Subwoofer Setup Banner (Subwoofer Count & Chamber Isolation)
        sub_setup_frame = ctk.CTkFrame(container, fg_color="#1E2838", border_color="#00E5FF", border_width=1)
        sub_setup_frame.pack(fill="x", pady=6, padx=4, ipady=6)

        ctk.CTkLabel(
            sub_setup_frame, text="SUBWOOFER QUANTITY & CHAMBER ARCHITECTURE",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF"
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=(8, 4), sticky="w")

        ctk.CTkLabel(
            sub_setup_frame, text="Woofer Count:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ECEFF1"
        ).grid(row=1, column=0, padx=16, pady=4, sticky="w")

        self.woofer_count_var = tk.StringVar(value="1")
        self.woofer_count_seg = ctk.CTkSegmentedButton(
            sub_setup_frame,
            values=["1x Single", "2x Dual", "3x Triple", "4x Quad"],
            command=self._on_segmented_woofer_count
        )
        self.woofer_count_seg.set("1x Single")
        self.woofer_count_seg.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ctk.CTkLabel(
            sub_setup_frame, text="Exact Count Entry:", font=ctk.CTkFont(size=12), text_color="#B0BEC5"
        ).grid(row=1, column=2, padx=12, pady=4, sticky="w")

        self.entry_num_subs = ctk.CTkEntry(sub_setup_frame, width=60, fg_color="#10141D")
        self.entry_num_subs.insert(0, "1")
        self.entry_num_subs.grid(row=1, column=3, padx=8, pady=4, sticky="w")
        self.entry_num_subs.bind("<KeyRelease>", lambda e: self.update_all_calculations())

        self.var_chamber_isolated = tk.BooleanVar(value=False)
        self.chk_chamber_isolated = ctk.CTkCheckBox(
            sub_setup_frame,
            text="Isolated Multi-Chamber (MDF Divider walls separating each sub) [vs. Shared Common Chamber]",
            variable=self.var_chamber_isolated,
            command=self._on_chamber_isolation_toggled,
            fg_color="#00B0FF",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.chk_chamber_isolated.grid(row=2, column=0, columnspan=4, padx=16, pady=(6, 8), sticky="w")

        # T/S Inputs Grid
        inputs_frame = ctk.CTkFrame(container, fg_color="#21252D")
        inputs_frame.pack(fill="x", pady=6, padx=4)

        ctk.CTkLabel(
            inputs_frame, text="Thiele/Small Electro-Acoustic Parameters",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#00E5FF"
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=10, sticky="w")

        self.entry_fs = self._create_labeled_entry(inputs_frame, "Free-Air Resonance (Fs) [Hz]:", "31.5", 1, 0)
        self.entry_qts = self._create_labeled_entry(inputs_frame, "Total Q (Qts):", "0.45", 1, 2)
        self.entry_qes = self._create_labeled_entry(inputs_frame, "Electrical Q (Qes):", "0.49", 2, 0)
        self.entry_qms = self._create_labeled_entry(inputs_frame, "Mechanical Q (Qms):", "5.2", 2, 2)
        self.entry_vas = self._create_labeled_entry(inputs_frame, "Equivalent Vol (Vas) [Liters]:", "45.0", 3, 0)
        self.entry_xmax = self._create_labeled_entry(inputs_frame, "Peak Excursion (Xmax) [mm]:", "19.0", 3, 2)
        self.entry_prms = self._create_labeled_entry(inputs_frame, "Continuous Power (P_RMS) [Watts]:", "750", 4, 0)
        self.entry_dia = self._create_labeled_entry(inputs_frame, "Nominal Diameter [Inches]:", "12.0", 4, 2)
        self.entry_sd = self._create_labeled_entry(inputs_frame, "Cone Area (Sd) [cm^2] (opt):", "510.0", 5, 0)

        self.var_isobaric = tk.BooleanVar(value=False)
        self.chk_isobaric = ctk.CTkCheckBox(
            inputs_frame,
            text="Isobaric Compound Mode (Push-Pull / Halves Required Vas)",
            variable=self.var_isobaric,
            command=self.update_all_calculations,
            fg_color="#00B0FF",
            font=ctk.CTkFont(size=11)
        )
        self.chk_isobaric.grid(row=5, column=2, padx=12, pady=6, sticky="w")

        self.var_inverted_sub = tk.BooleanVar(value=False)
        self.chk_inverted_sub = ctk.CTkCheckBox(
            inputs_frame,
            text="Inverted Sub Mounting ('Ass-Out' Magnet External; 0L sub disp)",
            variable=self.var_inverted_sub,
            command=self.update_all_calculations,
            fg_color="#00E5FF",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.chk_inverted_sub.grid(row=5, column=3, padx=12, pady=6, sticky="w")

        # Auto EBP Analysis Card
        self.ebp_result_frame = ctk.CTkFrame(container, fg_color="#1A232E", border_color="#0091EA", border_width=1)
        self.ebp_result_frame.pack(fill="x", pady=10, padx=4)

        ctk.CTkLabel(
            self.ebp_result_frame,
            text="EFFICIENCY BANDWIDTH PRODUCT (EBP) ENCLOSURE SUITABILITY ANALYSIS",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#40C4FF"
        ).pack(anchor="w", padx=16, pady=(10, 4))

        self.ebp_details_lbl = ctk.CTkLabel(
            self.ebp_result_frame, text="Analyzing...", font=ctk.CTkFont(size=12),
            justify="left", wraplength=950
        )
        self.ebp_details_lbl.pack(anchor="w", padx=16, pady=(0, 10))

    # -------------------------------------------------------------
    # TAB 2: Enclosure Alignment
    # -------------------------------------------------------------
    def _build_align_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_align, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        topo_frame = ctk.CTkFrame(container, fg_color="#21252D")
        topo_frame.pack(fill="x", pady=(0, 10), padx=4)

        ctk.CTkLabel(
            topo_frame, text="Target Enclosure Acoustic Topology:",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#00E5FF"
        ).grid(row=0, column=0, padx=16, pady=8, sticky="w")

        self.topo_var = tk.StringVar(value="ported")
        topos = [
            ("Sealed (Acoustic Suspension)", "sealed"),
            ("Ported / Vented (Bass Reflex)", "ported"),
            ("4th-Order Bandpass (Sealed Rear + Vented Front)", "4th_bandpass"),
            ("6th-Order Bandpass (Dual Ported Series/Parallel)", "6th_bandpass")
        ]
        for idx, (label, val) in enumerate(topos):
            ctk.CTkRadioButton(
                topo_frame, text=label, variable=self.topo_var, value=val,
                command=self.update_all_calculations, fg_color="#00B0FF"
            ).grid(row=1 + (idx // 2), column=idx % 2, padx=16, pady=4, sticky="w")

        self.align_cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.align_cards_frame.pack(fill="both", expand=True, pady=4)

        self.card_sealed = ctk.CTkFrame(self.align_cards_frame, fg_color="#21252D")
        self.card_sealed.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        ctk.CTkLabel(self.card_sealed, text="Sealed Alignment (Qtc = 0.707 Flat)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#80D8FF").pack(anchor="w", padx=12, pady=8)
        self.lbl_sealed_res = ctk.CTkLabel(self.card_sealed, text="Calculating...", justify="left", font=ctk.CTkFont(family="Consolas", size=12))
        self.lbl_sealed_res.pack(anchor="w", padx=12, pady=(0, 10))

        self.card_ported = ctk.CTkFrame(self.align_cards_frame, fg_color="#21252D")
        self.card_ported.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        ctk.CTkLabel(self.card_ported, text="Optimal Vented (Keele / Hoge Alignment)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#80D8FF").pack(anchor="w", padx=12, pady=8)
        self.lbl_ported_res = ctk.CTkLabel(self.card_ported, text="Calculating...", justify="left", font=ctk.CTkFont(family="Consolas", size=12))
        self.lbl_ported_res.pack(anchor="w", padx=12, pady=(0, 10))

        self.card_bandpass = ctk.CTkFrame(container, fg_color="#21252D")
        self.card_bandpass.pack(fill="x", padx=4, pady=8)
        ctk.CTkLabel(self.card_bandpass, text="Bandpass Synthesis (4th & 6th Order Projections)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").pack(anchor="w", padx=12, pady=8)
        self.lbl_bandpass_res = ctk.CTkLabel(self.card_bandpass, text="Calculating...", justify="left", font=ctk.CTkFont(family="Consolas", size=12))
        self.lbl_bandpass_res.pack(anchor="w", padx=12, pady=(0, 10))

        self.align_cards_frame.grid_columnconfigure(0, weight=1)
        self.align_cards_frame.grid_columnconfigure(1, weight=1)

    # -------------------------------------------------------------
    # TAB 3: Vehicle Constraints & 3D Shape
    # -------------------------------------------------------------
    def _build_geom_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_geom, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        shape_frame = ctk.CTkFrame(container, fg_color="#21252D")
        shape_frame.pack(fill="x", pady=(0, 8), padx=4)

        ctk.CTkLabel(shape_frame, text="Enclosure 3D Profile:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").grid(row=0, column=0, padx=16, pady=8, sticky="w")
        self.shape_var = tk.StringVar(value="cuboid")
        shapes = [
            ("Standard Rectangular Cuboid", "cuboid"),
            ("Single Angled Wedge (Seatback Recline / Truck Cab)", "single_wedge"),
            ("Double Angled Wedge / Symmetrical Trapezoid", "double_wedge")
        ]
        for idx, (label, val) in enumerate(shapes):
            ctk.CTkRadioButton(
                shape_frame, text=label, variable=self.shape_var, value=val,
                command=self.update_all_calculations, fg_color="#00B0FF"
            ).grid(row=1 + idx, column=0, columnspan=2, padx=16, pady=3, sticky="w")

        # Dimensions & Sliders
        dim_frame = ctk.CTkFrame(container, fg_color="#21252D")
        dim_frame.pack(fill="x", pady=6, padx=4)

        ctk.CTkLabel(
            dim_frame, text="Vehicle Trunk Clearance & Boundary Dimensions",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF"
        ).grid(row=0, column=0, columnspan=6, padx=16, pady=8, sticky="w")

        self.entry_width = self._create_labeled_entry(dim_frame, "Max Exterior Width (in):", "32.0", 1, 0)
        self.slider_width = ctk.CTkSlider(dim_frame, from_=10.0, to=60.0, width=150, command=lambda v: self._on_slider_change(self.entry_width, v))
        self.slider_width.set(32.0)
        self.slider_width.grid(row=1, column=2, padx=6, pady=4)

        self.entry_height = self._create_labeled_entry(dim_frame, "Max Exterior Height (in):", "14.5", 1, 3)
        self.slider_height = ctk.CTkSlider(dim_frame, from_=8.0, to=36.0, width=150, command=lambda v: self._on_slider_change(self.entry_height, v))
        self.slider_height.set(14.5)
        self.slider_height.grid(row=1, column=5, padx=6, pady=4)

        self.entry_depth_bot = self._create_labeled_entry(dim_frame, "Exterior Bottom Depth (in):", "16.0", 2, 0)
        self.slider_depth_bot = ctk.CTkSlider(dim_frame, from_=8.0, to=48.0, width=150, command=lambda v: self._on_slider_change(self.entry_depth_bot, v))
        self.slider_depth_bot.set(16.0)
        self.slider_depth_bot.grid(row=2, column=2, padx=6, pady=4)

        self.entry_depth_top = self._create_labeled_entry(dim_frame, "Exterior Top Depth (Wedge) (in):", "16.0", 2, 3)
        self.slider_depth_top = ctk.CTkSlider(dim_frame, from_=4.0, to=48.0, width=150, command=lambda v: self._on_slider_change(self.entry_depth_top, v))
        self.slider_depth_top.set(16.0)
        self.slider_depth_top.grid(row=2, column=5, padx=6, pady=4)

        # Back Solve Depth Frame
        solve_frame = ctk.CTkFrame(container, fg_color="#1E2738", border_color="#00E5FF", border_width=1)
        solve_frame.pack(fill="x", pady=6, padx=4)

        ctk.CTkLabel(
            solve_frame,
            text="Dynamic Spatial Constraint Solver: Lock Max Trunk Height & Width and back-solve Depth for target volume!",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#80D8FF"
        ).pack(side="left", padx=16, pady=8)

        self.btn_solve_depth = ctk.CTkButton(solve_frame, cursor="hand2", text="Back-Solve Required Depth", fg_color="#0091EA", hover_color="#00B0FF",
            command=self._on_back_solve_depth
        )
        self.btn_solve_depth.pack(side="right", padx=16, pady=8)

        # Split Container: Materials on Left, Blueprint / 3D Visualizer Canvas on Right
        vis_row = ctk.CTkFrame(container, fg_color="transparent")
        vis_row.pack(fill="x", pady=6, padx=4)
        vis_row.grid_columnconfigure(0, weight=1)
        vis_row.grid_columnconfigure(1, weight=1)

        mat_frame = ctk.CTkFrame(vis_row, fg_color="#21252D")
        mat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        ctk.CTkLabel(mat_frame, text="Materials, Baffle Thickness & Deductions", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").grid(row=0, column=0, columnspan=4, padx=12, pady=6, sticky="w")
        self.entry_mdf = self._create_labeled_entry(mat_frame, "MDF Wall Thick (in):", "0.75", 1, 0)
        self.entry_baffle_thick = self._create_labeled_entry(mat_frame, "Front Baffle Thick (in):", "0.75", 1, 2)
        self.entry_sub_disp = self._create_labeled_entry(mat_frame, "Sub Displacement (cu.ft):", "0.14", 2, 0)
        self.entry_brace_disp = self._create_labeled_entry(mat_frame, "Bracing / Kerf (cu.ft):", "0.06", 2, 2)
        self.entry_sub_cutout = self._create_labeled_entry(mat_frame, "Sub Cutout Dia (in):", "11.125", 3, 0)
        self.entry_sub_flush = self._create_labeled_entry(mat_frame, "Flush Mount Ring (in):", "12.50", 3, 2)

        ctk.CTkLabel(mat_frame, text="Baffle Arrangement Template:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ECEFF1").grid(row=4, column=0, padx=12, pady=6, sticky="w")
        self.baffle_layout_var = tk.StringVar(value="Equidistant Centered")
        self.baffle_layout_combo = ctk.CTkComboBox(
            mat_frame,
            values=["Equidistant Centered", "Left Biased", "Right Biased", "2x2 Stacked Grid (4 Subs)"],
            command=lambda v: self._redraw_visualizers(), width=210
        )
        self.baffle_layout_combo.grid(row=4, column=1, columnspan=2, padx=8, pady=6, sticky="w")

        # Visualizer Frame: 2D Baffle Blueprint & 3D Interactive Enclosure
        canvas_frame = ctk.CTkFrame(vis_row, fg_color="#18202A", border_color="#37474F", border_width=1)
        canvas_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        canvas_header = ctk.CTkFrame(canvas_frame, fg_color="transparent")
        canvas_header.pack(fill="x", padx=8, pady=(4, 2))

        # View Mode Switcher: 2D vs 3D
        self.vis_mode_segmented = ctk.CTkSegmentedButton(
            canvas_header,
            values=["📐 2D Baffle", "📦 3D Box Visualizer"],
            command=self._on_vis_mode_changed,
            selected_color="#0091EA", selected_hover_color="#00B0FF",
            height=26, font=ctk.CTkFont(size=11, weight="bold")
        )
        self.vis_mode_segmented.set("📐 2D Baffle")
        self.vis_mode_segmented.pack(side="left", padx=2)

        self.lbl_canvas_collision = ctk.CTkLabel(
            canvas_header, text="CLEARANCE OK", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00E676"
        )
        self.lbl_canvas_collision.pack(side="right", padx=6)

        # 3D Tool Strip (Camera presets, Shading, Exploded View) - shown when 3D is active
        self.frame_3d_controls = ctk.CTkFrame(canvas_frame, fg_color="#12161E", height=30)
        
        # Camera angle presets
        ctk.CTkButton(self.frame_3d_controls, cursor="hand2", text="Iso", width=36, height=22, font=ctk.CTkFont(size=10), fg_color="#263238", hover_color="#37474F", command=lambda: self.box_3d.set_view("iso")).pack(side="left", padx=2, pady=4)
        ctk.CTkButton(self.frame_3d_controls, cursor="hand2", text="Front", width=42, height=22, font=ctk.CTkFont(size=10), fg_color="#263238", hover_color="#37474F", command=lambda: self.box_3d.set_view("front")).pack(side="left", padx=2, pady=4)
        ctk.CTkButton(self.frame_3d_controls, cursor="hand2", text="Side", width=38, height=22, font=ctk.CTkFont(size=10), fg_color="#263238", hover_color="#37474F", command=lambda: self.box_3d.set_view("side")).pack(side="left", padx=2, pady=4)
        ctk.CTkButton(self.frame_3d_controls, cursor="hand2", text="Top", width=36, height=22, font=ctk.CTkFont(size=10), fg_color="#263238", hover_color="#37474F", command=lambda: self.box_3d.set_view("top")).pack(side="left", padx=2, pady=4)

        # Shading mode toggle
        self.btn_3d_render_mode = ctk.CTkButton(self.frame_3d_controls, cursor="hand2", text="Solid MDF", width=72, height=22, font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#00838F", hover_color="#0097A7", command=self._toggle_3d_shading
        )
        self.btn_3d_render_mode.pack(side="left", padx=6, pady=4)

        # Exploded view slider
        ctk.CTkLabel(self.frame_3d_controls, text="Explode:", font=ctk.CTkFont(size=10), text_color="#90A4AE").pack(side="left", padx=(6, 2), pady=4)
        self.slider_3d_explode = ctk.CTkSlider(
            self.frame_3d_controls, from_=0.0, to=1.0, width=80, height=16,
            command=self._on_3d_explode_slider
        )
        self.slider_3d_explode.set(0.0)
        self.slider_3d_explode.pack(side="left", padx=2, pady=4)

        # Zoom buttons
        ctk.CTkButton(self.frame_3d_controls, cursor="hand2", text="🔍+", width=28, height=22, font=ctk.CTkFont(size=10), fg_color="#37474F", hover_color="#455A64", command=lambda: self.box_3d.adjust_zoom(1.15)).pack(side="right", padx=2, pady=4)
        ctk.CTkButton(self.frame_3d_controls, cursor="hand2", text="🔍-", width=28, height=22, font=ctk.CTkFont(size=10), fg_color="#37474F", hover_color="#455A64", command=lambda: self.box_3d.adjust_zoom(0.85)).pack(side="right", padx=2, pady=4)

        # 2D Baffle Canvas
        self.baffle_canvas = tk.Canvas(
            canvas_frame, bg="#0A0E14", height=240, highlightthickness=0
        )
        self.baffle_canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # 3D Enclosure Canvas
        self.canvas_3d = tk.Canvas(
            canvas_frame, bg="#0B0E14", height=240, highlightthickness=0
        )
        self.box_3d = viz3d.BoxVisualizer3D(self.canvas_3d)

        # Volumetric Breakdown Display
        self.vol_result_frame = ctk.CTkFrame(container, fg_color="#18202A")
        self.vol_result_frame.pack(fill="x", pady=6, padx=4)

        self.lbl_geom_summary = ctk.CTkLabel(
            self.vol_result_frame, text="Volumetrics...",
            font=ctk.CTkFont(family="Consolas", size=12), justify="left"
        )
        self.lbl_geom_summary.pack(anchor="w", padx=16, pady=10)

    # -------------------------------------------------------------
    # TAB 4: Port Dynamics & Chuffing Guard
    # -------------------------------------------------------------
    def _build_port_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_port, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        cfg_frame = ctk.CTkFrame(container, fg_color="#21252D")
        cfg_frame.pack(fill="x", pady=(0, 8), padx=4)

        ctk.CTkLabel(cfg_frame, text="Port Geometry & Acoustic Configuration", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").grid(row=0, column=0, columnspan=6, padx=16, pady=8, sticky="w")

        self.port_type_var = tk.StringVar(value="slot")
        ctk.CTkRadioButton(cfg_frame, text="MDF Slot Port (Internal Shared Walls)", variable=self.port_type_var, value="slot", command=self.update_all_calculations, fg_color="#00B0FF").grid(row=1, column=0, columnspan=2, padx=16, pady=4, sticky="w")
        ctk.CTkRadioButton(cfg_frame, text="Round PVC / Flared Aeroport", variable=self.port_type_var, value="round", command=self.update_all_calculations, fg_color="#00B0FF").grid(row=1, column=2, columnspan=2, padx=16, pady=4, sticky="w")

        self.entry_fb = self._create_labeled_entry(cfg_frame, "Target Tuning (Fb) [Hz]:", "32.0", 2, 0)
        self.slider_fb = ctk.CTkSlider(cfg_frame, from_=20.0, to=55.0, width=150, command=lambda v: self._on_slider_change(self.entry_fb, v))
        self.slider_fb.set(32.0)
        self.slider_fb.grid(row=2, column=2, padx=6, pady=4)

        self.entry_slot_w = self._create_labeled_entry(cfg_frame, "Slot Port Width (in):", "2.5", 3, 0)
        self.entry_slot_h = self._create_labeled_entry(cfg_frame, "Slot Port Height (in):", "13.0", 3, 2)
        self.entry_round_dia = self._create_labeled_entry(cfg_frame, "Round Port Dia (in):", "4.0", 4, 0)
        self.entry_num_ports = self._create_labeled_entry(cfg_frame, "Number of Ports:", "1", 4, 2)
        self.entry_shared_walls = self._create_labeled_entry(cfg_frame, "Shared Boundary Walls (0-3):", "3", 5, 0)

        # Chuffing Safe Guard Live Gauge
        self.port_gauge_frame = ctk.CTkFrame(container, fg_color="#1B232E", border_color="#00B0FF", border_width=1)
        self.port_gauge_frame.pack(fill="x", pady=8, padx=4)

        ctk.CTkLabel(self.port_gauge_frame, text="PORT AIR VELOCITY & CHUFFING SAFEGUARD (MACH RATING)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#40C4FF").pack(anchor="w", padx=16, pady=(10, 4))
        self.lbl_port_status = ctk.CTkLabel(self.port_gauge_frame, text="LAMINAR", font=ctk.CTkFont(family="Consolas", size=17, weight="bold"), text_color="#00E676")
        self.lbl_port_status.pack(anchor="w", padx=16, pady=2)
        self.lbl_port_details = ctk.CTkLabel(self.port_gauge_frame, text="Calculating...", justify="left", font=ctk.CTkFont(family="Consolas", size=12))
        self.lbl_port_details.pack(anchor="w", padx=16, pady=(0, 10))

        # Health Meters Frame
        health_frame = ctk.CTkFrame(container, fg_color="#18202A")
        health_frame.pack(fill="x", pady=6, padx=4, ipady=4)

        ctk.CTkLabel(health_frame, text="⚡ ACOUSTIC HEALTH & VELOCITY METERS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00E5FF").grid(row=0, column=0, columnspan=3, padx=16, pady=(8, 4), sticky="w")
        ctk.CTkLabel(health_frame, text="Air Velocity Safe Bar (<17 m/s safe, >25 m/s turbulent):", font=ctk.CTkFont(size=11), text_color="#B0BEC5").grid(row=1, column=0, padx=16, pady=2, sticky="w")
        self.bar_velocity = ctk.CTkProgressBar(health_frame, width=320, progress_color="#00E676")
        self.bar_velocity.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        self.lbl_meter_velo = ctk.CTkLabel(health_frame, text="0.0 m/s", font=ctk.CTkFont(family="Consolas", size=11))
        self.lbl_meter_velo.grid(row=1, column=2, padx=8, pady=2, sticky="w")

        ctk.CTkLabel(health_frame, text="Port Area Ratio (Target 12-16 sq.in/cu.ft):", font=ctk.CTkFont(size=11), text_color="#B0BEC5").grid(row=2, column=0, padx=16, pady=2, sticky="w")
        self.bar_port_ratio = ctk.CTkProgressBar(health_frame, width=320, progress_color="#00B0FF")
        self.bar_port_ratio.grid(row=2, column=1, padx=10, pady=2, sticky="w")
        self.lbl_meter_ratio = ctk.CTkLabel(health_frame, text="0.0 sq.in/ft³", font=ctk.CTkFont(family="Consolas", size=11))
        self.lbl_meter_ratio.grid(row=2, column=2, padx=8, pady=2, sticky="w")

    # -------------------------------------------------------------
    # TAB 5: Fabrication Cut Sheet & Export
    # -------------------------------------------------------------
    def _build_cut_tab(self):
        container = ctk.CTkFrame(self.tab_cut, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        action_bar = ctk.CTkFrame(container, fg_color="#21252D")
        action_bar.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(action_bar, text="Table Saw & CNC Fabrication Cut List", font=ctk.CTkFont(size=15, weight="bold"), text_color="#00E5FF").pack(side="left", padx=14, pady=10)

        self.btn_export_txt = ctk.CTkButton(action_bar, cursor="hand2", text="💾 Export TXT", width=95, fg_color="#00838F", hover_color="#0097A7", command=self._export_txt)
        self.btn_export_txt.pack(side="right", padx=6, pady=10)

        self.btn_export_csv = ctk.CTkButton(action_bar, cursor="hand2", text="📊 Export CSV", width=95, fg_color="#2E7D32", hover_color="#388E3C", command=self._export_csv)
        self.btn_export_csv.pack(side="right", padx=6, pady=10)

        self.btn_copy_summary = ctk.CTkButton(action_bar, cursor="hand2", text="📋 Copy Summary", width=110, fg_color="#37474F", hover_color="#455A64", command=self._copy_summary_to_clipboard)
        self.btn_copy_summary.pack(side="right", padx=6, pady=10)

        self.btn_copy_cuts = ctk.CTkButton(action_bar, cursor="hand2", text="📋 Copy Cut List", width=110, fg_color="#37474F", hover_color="#455A64", command=self._copy_cuts_to_clipboard)
        self.btn_copy_cuts.pack(side="right", padx=6, pady=10)

        self.btn_print_shop = ctk.CTkButton(action_bar, cursor="hand2", text="🖨️ Shop Order View", width=120, fg_color="#5D4037", hover_color="#6D4C41", command=self._open_shop_work_order)
        self.btn_print_shop.pack(side="right", padx=6, pady=10)

        tree_frame = ctk.CTkFrame(container, fg_color="#181B20")
        tree_frame.pack(fill="both", expand=True)

        columns = ("name", "qty", "width", "height", "thick", "bevel", "notes")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1E222A", foreground="#ECEFF1", fieldbackground="#1E222A", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#263238", foreground="#80D8FF", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#0091EA")])

        headings = [
            ("name", "Panel Name", 250),
            ("qty", "Qty", 45),
            ("width", "Width", 90),
            ("height", "Height", 90),
            ("thick", "Thick", 75),
            ("bevel", "Bevel Angle", 100),
            ("notes", "Special Cuts / Sub Details", 380)
        ]
        for col_id, title, width in headings:
            self.tree.heading(col_id, text=title)
            self.tree.column(col_id, width=width, anchor="center" if col_id in {"qty", "width", "height", "thick", "bevel"} else "w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scrollbar.pack(side="right", fill="y", pady=4)

    # -------------------------------------------------------------
    # NEW TAB 6: Visual Wiring & Amp Lab
    # -------------------------------------------------------------
    def _build_wiring_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_wire, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Top Control Row
        wire_ctrl_row = ctk.CTkFrame(container, fg_color="transparent")
        wire_ctrl_row.pack(fill="x", pady=(0, 8))
        wire_ctrl_row.grid_columnconfigure(0, weight=1)
        wire_ctrl_row.grid_columnconfigure(1, weight=1)

        # Left Card: Subwoofer & Voice Coil Architecture
        sub_card = ctk.CTkFrame(wire_ctrl_row, fg_color="#21252D")
        sub_card.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        ctk.CTkLabel(sub_card, text="🔊 Speaker & Voice Coil Specs", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").pack(anchor="w", padx=14, pady=(10, 6))

        cfg_sub_grid = ctk.CTkFrame(sub_card, fg_color="transparent")
        cfg_sub_grid.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(cfg_sub_grid, text="Speaker Count:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self.wire_num_subs_var = tk.StringVar(value="1")
        self.wire_num_subs_combo = ctk.CTkComboBox(
            cfg_sub_grid, values=["1 Subwoofer", "2 Subwoofers", "3 Subwoofers", "4 Subwoofers"],
            width=150, command=self._on_wire_count_changed
        )
        self.wire_num_subs_combo.set("1 Subwoofer")
        self.wire_num_subs_combo.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ctk.CTkLabel(cfg_sub_grid, text="Config Mode:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=1, column=0, padx=8, pady=4, sticky="w")
        self.wire_cfg_mode_seg = ctk.CTkSegmentedButton(
            cfg_sub_grid, values=["Unified (All Same)", "Custom Per-Speaker"],
            command=self._on_wire_mode_changed
        )
        self.wire_cfg_mode_seg.set("Unified (All Same)")
        self.wire_cfg_mode_seg.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        # Unified Frame
        self.unified_cfg_frame = ctk.CTkFrame(sub_card, fg_color="transparent")
        self.unified_cfg_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(self.unified_cfg_frame, text="Voice Coils per Sub:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=0, column=0, padx=8, pady=3, sticky="w")
        self.wire_coils_var = tk.StringVar(value="Dual Voice Coil (DVC)")
        self.wire_coils_combo = ctk.CTkComboBox(
            self.unified_cfg_frame, values=["Single Voice Coil (SVC)", "Dual Voice Coil (DVC)"],
            width=175, command=self._on_wire_setting_changed
        )
        self.wire_coils_combo.set("Dual Voice Coil (DVC)")
        self.wire_coils_combo.grid(row=0, column=1, padx=8, pady=3, sticky="w")

        ctk.CTkLabel(self.unified_cfg_frame, text="Nominal Coil Ohms:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=1, column=0, padx=8, pady=3, sticky="w")
        self.wire_ohms_var = tk.StringVar(value="4.0 Ω")
        self.wire_ohms_combo = ctk.CTkComboBox(
            self.unified_cfg_frame, values=["1.0 Ω", "2.0 Ω", "4.0 Ω", "8.0 Ω"],
            width=150, command=self._on_wire_setting_changed
        )
        self.wire_ohms_combo.set("4.0 Ω")
        self.wire_ohms_combo.grid(row=1, column=1, padx=8, pady=3, sticky="w")

        ctk.CTkLabel(self.unified_cfg_frame, text="Coil-to-Coil (On Speaker):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=2, column=0, padx=8, pady=3, sticky="w")
        self.wire_intra_var = tk.StringVar(value="Parallel")
        self.wire_intra_seg = ctk.CTkSegmentedButton(
            self.unified_cfg_frame, values=["Parallel", "Series"],
            command=lambda v: self._on_wire_setting_changed(None)
        )
        self.wire_intra_seg.set("Parallel")
        self.wire_intra_seg.grid(row=2, column=1, padx=8, pady=3, sticky="w")

        # Dynamic Per-Speaker Frame (for Sub 1..N custom ohms/coils)
        self.per_sub_frame = ctk.CTkFrame(sub_card, fg_color="#181D26", corner_radius=6)
        self.sub_config_rows = []  # List of dicts for sub 0..3: {"frame": ..., "coils": ..., "ohms": ..., "intra": ...}

        for s_i in range(4):
            sf = ctk.CTkFrame(self.per_sub_frame, fg_color="transparent")
            ctk.CTkLabel(sf, text=f"Sub {s_i+1}:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00E5FF", width=44, anchor="w").pack(side="left", padx=(4, 6))
            
            c_combo = ctk.CTkComboBox(sf, values=["DVC", "SVC"], width=72, command=self._on_wire_setting_changed)
            c_combo.set("DVC")
            c_combo.pack(side="left", padx=4)

            o_combo = ctk.CTkComboBox(sf, values=["1.0 Ω", "2.0 Ω", "4.0 Ω", "8.0 Ω"], width=82, command=self._on_wire_setting_changed)
            o_combo.set("4.0 Ω")
            o_combo.pack(side="left", padx=4)

            i_seg = ctk.CTkSegmentedButton(sf, values=["Parallel", "Series"], width=110, command=lambda v: self._on_wire_setting_changed(None))
            i_seg.set("Parallel")
            i_seg.pack(side="left", padx=4)

            self.sub_config_rows.append({
                "frame": sf,
                "coils": c_combo,
                "ohms": o_combo,
                "intra": i_seg
            })

        # Inter-Speaker Topology Section
        inter_box = ctk.CTkFrame(sub_card, fg_color="transparent")
        inter_box.pack(fill="x", padx=10, pady=(2, 6))

        ctk.CTkLabel(inter_box, text="Speaker-to-Speaker (To Amp):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self.wire_inter_var = tk.StringVar(value="All Parallel")
        self.wire_inter_combo = ctk.CTkComboBox(
            inter_box, values=["All Parallel", "All Series"],
            width=260, command=self._on_wire_setting_changed
        )
        self.wire_inter_combo.set("All Parallel")
        self.wire_inter_combo.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        # Right Card: Amplifier Configuration & Power Delivery
        amp_card = ctk.CTkFrame(wire_ctrl_row, fg_color="#21252D")
        amp_card.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        ctk.CTkLabel(amp_card, text="⚡ Monoblock / Multi-Channel Amplifier", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").pack(anchor="w", padx=14, pady=(10, 6))

        cfg_amp_grid = ctk.CTkFrame(amp_card, fg_color="transparent")
        cfg_amp_grid.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(cfg_amp_grid, text="Amp Topology:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self.amp_topo_combo = ctk.CTkComboBox(
            cfg_amp_grid, values=[
                "Monoblock (Class D Sub Amp)",
                "2-Channel Bridged (Mono)",
                "2-Channel Independent (Stereo / Dual-Mono)",
                "4-Channel Dual Bridged (2x Mono Subwoofers)",
                "4-Channel Rear Bridged (3-Ch Mode: Front Mids + Sub)",
                "4-Channel Independent (4x Discrete Sub Channels)"
            ],
            width=270, command=self._on_wire_topology_changed
        )
        self.amp_topo_combo.set("Monoblock (Class D Sub Amp)")
        self.amp_topo_combo.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        self.lbl_amp_p1 = ctk.CTkLabel(cfg_amp_grid, text="Rated RMS @ 1Ω (W):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5")
        self.lbl_amp_p1.grid(row=1, column=0, padx=8, pady=4, sticky="w")
        self.entry_amp_1ohm = ctk.CTkEntry(cfg_amp_grid, width=110, fg_color="#10141D")
        self.entry_amp_1ohm.insert(0, "1500")
        self.entry_amp_1ohm.grid(row=1, column=1, padx=8, pady=4, sticky="w")
        self.entry_amp_1ohm.bind("<KeyRelease>", lambda e: self._on_wire_setting_changed(None))

        self.lbl_amp_p2 = ctk.CTkLabel(cfg_amp_grid, text="Rated RMS @ 2Ω (W):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5")
        self.lbl_amp_p2.grid(row=2, column=0, padx=8, pady=4, sticky="w")
        self.entry_amp_2ohm = ctk.CTkEntry(cfg_amp_grid, width=110, fg_color="#10141D")
        self.entry_amp_2ohm.insert(0, "900")
        self.entry_amp_2ohm.grid(row=2, column=1, padx=8, pady=4, sticky="w")
        self.entry_amp_2ohm.bind("<KeyRelease>", lambda e: self._on_wire_setting_changed(None))

        self.lbl_amp_p4 = ctk.CTkLabel(cfg_amp_grid, text="Rated RMS @ 4Ω (W):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5")
        self.lbl_amp_p4.grid(row=3, column=0, padx=8, pady=4, sticky="w")
        self.entry_amp_4ohm = ctk.CTkEntry(cfg_amp_grid, width=110, fg_color="#10141D")
        self.entry_amp_4ohm.insert(0, "500")
        self.entry_amp_4ohm.grid(row=3, column=1, padx=8, pady=4, sticky="w")
        self.entry_amp_4ohm.bind("<KeyRelease>", lambda e: self._on_wire_setting_changed(None))

        ctk.CTkLabel(cfg_amp_grid, text="Min Stable Load:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#B0BEC5").grid(row=4, column=0, padx=8, pady=4, sticky="w")
        self.amp_min_stable_combo = ctk.CTkComboBox(
            cfg_amp_grid, values=["1.0 Ω Stable", "2.0 Ω Stable", "0.5 Ω Competition"],
            width=160, command=self._on_wire_setting_changed
        )
        self.amp_min_stable_combo.set("1.0 Ω Stable")
        self.amp_min_stable_combo.grid(row=4, column=1, padx=8, pady=4, sticky="w")

        # Digital Power & Impedance Summary Banner
        self.wire_summary_banner = ctk.CTkFrame(container, fg_color="#141E28", border_color="#00E5FF", border_width=1)
        self.wire_summary_banner.pack(fill="x", pady=6, padx=4, ipady=4)

        self.lbl_wire_ohm_badge = ctk.CTkLabel(
            self.wire_summary_banner, text="FINAL LOAD: 1.00 Ω",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), text_color="#00E676"
        )
        self.lbl_wire_ohm_badge.pack(side="left", padx=16, pady=8)

        self.lbl_wire_power_badge = ctk.CTkLabel(
            self.wire_summary_banner, text="TOTAL POWER: 1,500W RMS  |  750W RMS / SPEAKER",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color="#40C4FF"
        )
        self.lbl_wire_power_badge.pack(side="left", padx=12, pady=8)

        self.lbl_wire_status_badge = ctk.CTkLabel(
            self.wire_summary_banner, text="SAFE LOAD",
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#1E3A28", text_color="#00E676", corner_radius=6, padx=10, pady=4
        )
        self.lbl_wire_status_badge.pack(side="right", padx=16, pady=8)

        # Dedicated Electrical Sizing & Diagnostic Row
        self.wire_elec_row = ctk.CTkFrame(container, fg_color="#16202A", border_color="#263238", border_width=1)
        self.wire_elec_row.pack(fill="x", pady=(0, 6), padx=4)

        self.lbl_wire_elec_details = ctk.CTkLabel(
            self.wire_elec_row, text="⚡ 12V Battery Power Cable: 1/0 AWG OFC  |  Inline Fuse: 150A ANL  |  Speaker Leads: 12 AWG OFC",
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#80D8FF", justify="left"
        )
        self.lbl_wire_elec_details.pack(side="left", padx=16, pady=6)

        # Interactive Wiring Diagram Canvas
        schematic_frame = ctk.CTkFrame(container, fg_color="#161B22", border_color="#37474F", border_width=1)
        schematic_frame.pack(fill="both", expand=True, pady=6, padx=4)

        sch_header = ctk.CTkFrame(schematic_frame, fg_color="transparent")
        sch_header.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            sch_header, text="🔌 Visual Hookup Schematic (Speaker Voice Coils to Amplifier Terminals)",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF"
        ).pack(side="left")

        ctk.CTkLabel(
            sch_header, text="Legend:  ■ Red Wire = Positive (+)   ■ Black Wire = Negative (-)   ■ Yellow Wire = Series Jumper",
            font=ctk.CTkFont(size=11), text_color="#B0BEC5"
        ).pack(side="right")

        self.wiring_canvas = tk.Canvas(schematic_frame, bg="#0A0E14", height=390, highlightthickness=0)
        self.wiring_canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # -------------------------------------------------------------
    # Helper & Event Handlers
    # -------------------------------------------------------------
    def _create_labeled_entry(self, parent, label_text: str, default_val: str, row: int, col: int) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=12), text_color="#B0BEC5").grid(row=row, column=col, padx=12, pady=(4, 2), sticky="w")
        entry = ctk.CTkEntry(parent, width=140, fg_color="#181B20", border_color="#37474F")
        entry.insert(0, default_val)
        entry.grid(row=row, column=col + 1, padx=8, pady=(2, 4), sticky="w")
        entry.bind("<KeyRelease>", lambda event: self.update_all_calculations())
        return entry

    def _get_float(self, entry: ctk.CTkEntry, fallback: float = 0.0) -> float:
        val_str = entry.get().strip()
        if not val_str:
            entry.configure(border_color="#37474F")
            return fallback
        try:
            val = float(val_str)
            entry.configure(border_color="#37474F")
            return val
        except ValueError:
            entry.configure(border_color="#FF1744")
            return fallback

    def _get_int(self, entry: ctk.CTkEntry, fallback: int = 1) -> int:
        val_str = entry.get().strip()
        if not val_str:
            entry.configure(border_color="#37474F")
            return fallback
        try:
            val = int(val_str)
            entry.configure(border_color="#37474F")
            return val
        except ValueError:
            entry.configure(border_color="#FF1744")
            return fallback

    def _on_slider_change(self, entry_widget: ctk.CTkEntry, slider_val: float):
        if self._updating_lock:
            return
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, f"{slider_val:.2f}")
        self.update_all_calculations()

    def _on_segmented_woofer_count(self, choice: str):
        count_map = {"1x Single": 1, "2x Dual": 2, "3x Triple": 3, "4x Quad": 4}
        c = count_map.get(choice, 1)
        self.entry_num_subs.delete(0, tk.END)
        self.entry_num_subs.insert(0, str(c))
        # Also sync to wiring tab combo
        self.wire_num_subs_combo.set(f"{c} Subwoofer" if c == 1 else f"{c} Subwoofers")
        self.update_all_calculations()

    def _on_chamber_isolation_toggled(self):
        self.update_all_calculations()

    def _toggle_unit_system(self):
        if self.unit_system == "imperial":
            self.unit_system = "metric"
            self.btn_toggle_units.configure(text="Unit: Metric")
        else:
            self.unit_system = "imperial"
            self.btn_toggle_units.configure(text="Unit: Imperial")
        self.update_all_calculations()

    def _toggle_tape_fractions(self):
        if self.display_mode == "decimal":
            self.display_mode = "fraction"
            self.btn_toggle_fraction.configure(text='Tape: 1/16"')
        else:
            self.display_mode = "decimal"
            self.btn_toggle_fraction.configure(text="Tape: Decimals")
        self._refresh_cut_sheet_tree()

    # -------------------------------------------------------------
    # Search Engine & Database
    # -------------------------------------------------------------
    def _on_search_keyrelease(self, event):
        query = self.search_entry.get().strip()
        if len(query) < 2:
            self.search_results_combo.configure(values=["(Type at least 2 characters...)"])
            self.search_results_combo.set("(Type at least 2 characters...)")
            return
        matches = sdb.search_all_subwoofers(query)
        if matches:
            labels = [f"{m[0]} — {m[1]}" for m in matches[:30]]
            self.search_results_combo.configure(values=labels)
            self.search_results_combo.set(labels[0])
        else:
            self.search_results_combo.configure(values=["No matches found"])
            self.search_results_combo.set("No matches found")

    def _on_search_result_picked(self, choice: str):
        if "—" not in choice:
            return
        parts = choice.split("—", 1)
        maker = parts[0].strip()
        model = parts[1].strip()
        self._load_from_tree(maker, "All Series", model)

    def _on_maker_selected(self, maker_choice: str):
        self.selected_maker = maker_choice
        if maker_choice == "Custom / Manual Entry":
            self.series_combo.configure(values=["Custom / Manual Entry"])
            self.series_combo.set("Custom / Manual Entry")
            self.model_combo.configure(values=["Custom / Manual Entry"])
            self.model_combo.set("Custom / Manual Entry")
            return

        series_list = sdb.get_series_for_manufacturer(maker_choice)
        if series_list:
            options = ["All Series"] + series_list
            self.series_combo.configure(values=options)
            self.series_combo.set(options[0])
            self._on_series_selected(options[0])
        else:
            self.series_combo.configure(values=["Standard Line"])
            self.series_combo.set("Standard Line")
            self._on_series_selected("Standard Line")

    def _on_series_selected(self, series_choice: str):
        models = sdb.get_models_for_maker_and_series(self.selected_maker, series_choice)
        if models:
            self.model_combo.configure(values=models)
            self.model_combo.set(models[0])
            self._on_model_selected(models[0])
        else:
            self.model_combo.configure(values=["No models found"])
            self.model_combo.set("No models found")

    def _on_model_selected(self, model_choice: str):
        sub = sdb.get_subwoofer(self.selected_maker, model_choice)
        if not sub:
            return

        self.entry_fs.delete(0, tk.END); self.entry_fs.insert(0, str(sub.fs))
        self.entry_qts.delete(0, tk.END); self.entry_qts.insert(0, str(sub.qts))
        self.entry_qes.delete(0, tk.END); self.entry_qes.insert(0, str(sub.qes))
        self.entry_qms.delete(0, tk.END); self.entry_qms.insert(0, str(sub.qms))
        self.entry_vas.delete(0, tk.END); self.entry_vas.insert(0, str(sub.vas_liters))
        self.entry_xmax.delete(0, tk.END); self.entry_xmax.insert(0, str(sub.xmax_mm))
        self.entry_prms.delete(0, tk.END); self.entry_prms.insert(0, str(sub.p_rms))
        self.entry_dia.delete(0, tk.END); self.entry_dia.insert(0, str(sub.nominal_dia_inch))
        if sub.sd_sq_cm:
            self.entry_sd.delete(0, tk.END); self.entry_sd.insert(0, str(sub.sd_sq_cm))
        self.entry_sub_cutout.delete(0, tk.END); self.entry_sub_cutout.insert(0, str(sub.sub_cutout_dia_in))
        self.entry_sub_flush.delete(0, tk.END); self.entry_sub_flush.insert(0, str(sub.sub_flush_dia_in))
        self.entry_sub_disp.delete(0, tk.END); self.entry_sub_disp.insert(0, str(sub.sub_displacement_cuft))

        info_text = f"Loaded {sub.maker} {sub.model} ({sub.p_rms:.0f}W RMS, Xmax: {sub.xmax_mm:.1f}mm, Fs: {sub.fs:.1f}Hz)."
        if sub.notes:
            info_text += f" Note: {sub.notes}"
        self.driver_desc_lbl.configure(text=info_text, text_color="#80D8FF")
        self.update_all_calculations()

    def _popup_hierarchical_menu(self):
        menu = tk.Menu(self, tearoff=0, bg="#1E222A", fg="#ECEFF1", activebackground="#0091EA", activeforeground="#FFFFFF")
        makers = sdb.get_all_manufacturers()
        for maker in makers:
            maker_menu = tk.Menu(menu, tearoff=0, bg="#1E222A", fg="#ECEFF1", activebackground="#0091EA", activeforeground="#FFFFFF")
            series_list = sdb.get_series_for_manufacturer(maker)
            for s_name in series_list:
                series_menu = tk.Menu(maker_menu, tearoff=0, bg="#1E222A", fg="#ECEFF1", activebackground="#0091EA", activeforeground="#FFFFFF")
                models = sdb.get_models_for_maker_and_series(maker, s_name)
                for m_name in models:
                    series_menu.add_command(
                        label=m_name,
                        command=lambda mk=maker, sr=s_name, md=m_name: self._load_from_tree(mk, sr, md)
                    )
                maker_menu.add_cascade(label=s_name, menu=series_menu)
            menu.add_cascade(label=maker, menu=maker_menu)

        try:
            x = self.btn_browse_menu.winfo_rootx()
            y = self.btn_browse_menu.winfo_rooty() + self.btn_browse_menu.winfo_height()
            menu.post(x, y)
        except Exception:
            menu.post(self.winfo_pointerx(), self.winfo_pointery())

    def _load_from_tree(self, maker: str, series: str, model: str):
        self.selected_maker = maker
        self.maker_combo.set(maker)
        series_list = ["All Series"] + sdb.get_series_for_manufacturer(maker)
        self.series_combo.configure(values=series_list)
        self.series_combo.set(series)
        models = sdb.get_models_for_maker_and_series(maker, series)
        self.model_combo.configure(values=models)
        self.model_combo.set(model)
        self._on_model_selected(model)

    def _on_back_solve_depth(self):
        target_net = self.enclosure.calculate_net_internal_volume_cuft()
        if self.topo_var.get() == "sealed":
            sealed_res = am.solve_sealed_alignment(self.ts_params)
            target_net = sealed_res["net_vb_cuft"]
        elif self.topo_var.get() == "ported":
            ported_res = am.solve_ported_optimal_keele(self.ts_params)
            target_net = ported_res["recommended_vb_cuft"]

        locked_h = self._get_float(self.entry_height, 14.5)
        locked_w = self._get_float(self.entry_width, 32.0)
        bot_d, top_d = self.enclosure.solve_depth_for_target_net_volume(
            target_net_cuft=target_net,
            locked_height_in=locked_h,
            locked_width_in=locked_w
        )
        self.entry_depth_bot.delete(0, tk.END); self.entry_depth_bot.insert(0, str(bot_d))
        self.entry_depth_top.delete(0, tk.END); self.entry_depth_top.insert(0, str(top_d))
        self.update_all_calculations()

    # -------------------------------------------------------------
    # Wiring Tab Handlers
    # -------------------------------------------------------------
    def _on_wire_mode_changed(self, mode=None):
        if not hasattr(self, 'wire_cfg_mode_seg'):
            return
        is_custom = "Custom" in self.wire_cfg_mode_seg.get()
        if is_custom:
            self.unified_cfg_frame.pack_forget()
            self.per_sub_frame.pack(fill="x", padx=10, pady=4)
        else:
            self.per_sub_frame.pack_forget()
            self.unified_cfg_frame.pack(fill="x", padx=10, pady=2)
        self._update_per_sub_rows()
        self._update_wiring_calculations()

    def _update_per_sub_rows(self):
        if not hasattr(self, 'wire_num_subs_combo') or not hasattr(self, 'sub_config_rows'):
            return
        txt = self.wire_num_subs_combo.get()
        n_subs = int(txt.split()[0])
        for i, row in enumerate(self.sub_config_rows):
            if i < n_subs:
                row["frame"].pack(fill="x", padx=6, pady=2)
            else:
                row["frame"].pack_forget()

    def _on_wire_count_changed(self, choice):
        txt = self.wire_num_subs_combo.get()
        count = int(txt.split()[0])

        # Dynamically populate inter-wiring choices according to subwoofer count
        current_inter = self.wire_inter_combo.get()
        if count == 1:
            avail = ["Single Subwoofer Direct"]
        elif count == 2:
            avail = ["All Parallel", "All Series"]
        elif count == 3:
            avail = [
                "All Parallel",
                "All Series",
                "2 in Series, 1 in Parallel",
                "2 in Parallel, 1 in Series"
            ]
        else:  # count == 4
            avail = [
                "All Parallel",
                "All Series",
                "Series-Parallel (Pairs in Series, Paralleled)",
                "Parallel-Series (Pairs in Parallel, Series)"
            ]

        self.wire_inter_combo.configure(values=avail)
        if current_inter in avail:
            self.wire_inter_combo.set(current_inter)
        else:
            self.wire_inter_combo.set(avail[0])

        self._update_per_sub_rows()

        if count != self.enclosure.num_subwoofers:
            self.entry_num_subs.delete(0, tk.END)
            self.entry_num_subs.insert(0, str(count))
            self.update_all_calculations()
        else:
            self._update_wiring_calculations()

    def _on_wire_setting_changed(self, choice=None):
        self._update_wiring_calculations()

    # -------------------------------------------------------------
    # Master Calculation Loop
    # -------------------------------------------------------------
    def update_all_calculations(self):
        self._updating_lock = True
        try:
            fs = self._get_float(self.entry_fs, 31.5)
            qts = self._get_float(self.entry_qts, 0.45)
            qes = self._get_float(self.entry_qes, 0.49)
            qms = self._get_float(self.entry_qms, 5.2)
            vas = self._get_float(self.entry_vas, 45.0)
            xmax = self._get_float(self.entry_xmax, 19.0)
            prms = self._get_float(self.entry_prms, 750.0)
            dia = self._get_float(self.entry_dia, 12.0)
            sd = self._get_float(self.entry_sd, 510.0)
            num_subs = max(1, self._get_int(self.entry_num_subs, 1))
            is_isobaric = self.var_isobaric.get()
            is_isolated = self.var_chamber_isolated.get()

            # Sync segmented button if it matches 1-4
            if num_subs == 1:
                self.woofer_count_seg.set("1x Single")
            elif num_subs == 2:
                self.woofer_count_seg.set("2x Dual")
            elif num_subs == 3:
                self.woofer_count_seg.set("3x Triple")
            elif num_subs == 4:
                self.woofer_count_seg.set("4x Quad")

            # Sync to wiring combo if initialized
            if hasattr(self, 'wire_num_subs_combo'):
                self.wire_num_subs_combo.set(f"{num_subs} Subwoofer" if num_subs == 1 else f"{num_subs} Subwoofers")

            self.ts_params = am.TSParameters(
                fs=fs, qts=qts, qes=qes, qms=qms, vas_liters=vas,
                xmax_mm=xmax, p_rms=prms, sd_sq_cm=sd, nominal_dia_inch=dia,
                is_isobaric=is_isobaric, num_drivers=num_subs
            )

            # EBP calculation
            ebp, badge_name, ebp_detail = am.calculate_ebp(fs, qes)
            self.ebp_badge.configure(text=f"EBP: {ebp} ({badge_name})")
            self.ebp_details_lbl.configure(
                text=f"• {ebp_detail}\n"
                     f"• Total Active Drivers: {num_subs}x Subwoofers ({'Isolated Chambers' if is_isolated and num_subs > 1 else 'Shared Common Chamber'})\n"
                     f"• Total Effective Vas: {self.ts_params.effective_vas_cuft:.2f} ft³ ({self.ts_params.effective_vas_liters:.1f} L)  |  Combined Sd: {self.ts_params.effective_sd_sq_in:.1f} in²"
            )

            # Enclosure alignment synthesis
            sealed_res = am.solve_sealed_alignment(self.ts_params, target_qtc=0.707)
            self.lbl_sealed_res.configure(
                text=f"Net Volume (Vb):    {sealed_res['net_vb_cuft']} cu.ft  ({sealed_res['net_vb_liters']} Liters)\n"
                     f"Resonance (Fc):     {sealed_res['fc_hz']} Hz\n"
                     f"-3dB Cutoff (F3):    {sealed_res['f3_hz']} Hz\n"
                     f"System Alpha:       {sealed_res['alpha']}"
            )

            ported_res = am.solve_ported_optimal_keele(self.ts_params)
            self.lbl_ported_res.configure(
                text=f"Optimal Net Vb:     {ported_res['recommended_vb_cuft']} cu.ft  ({ported_res['recommended_vb_liters']} Liters)\n"
                     f"Optimal Tuning Fb:  {ported_res['recommended_fb_hz']} Hz\n"
                     f"-3dB Cutoff (F3):    {ported_res['f3_hz']} Hz\n"
                     f"Driver Efficiency:  Keele / Small Standard"
            )

            bp4_res = am.solve_4th_order_bandpass(self.ts_params)
            bp6_res = am.solve_6th_order_bandpass_series_and_parallel(self.ts_params)
            self.lbl_bandpass_res.configure(
                text=f"[ 4th-Order Bandpass ]\n"
                     f"  Rear Sealed Vb:   {bp4_res['rear_sealed_vb_cuft']} cu.ft ({bp4_res['rear_sealed_vb_liters']} L)  |  Front Vented Vb: {bp4_res['front_vented_vb_cuft']} cu.ft ({bp4_res['front_vented_vb_liters']} L)\n"
                     f"  Center Tuning Fo: {bp4_res['center_fo_hz']} Hz  |  Passband: {bp4_res['low_cutoff_fl_hz']} Hz - {bp4_res['high_cutoff_fh_hz']} Hz  |  Acoustic Gain: +{bp4_res['gain_db']} dB\n\n"
                     f"[ 6th-Order Bandpass (Parallel Dual Ported) ]\n"
                     f"  Rear Cavity:      {bp6_res['rear_chamber_vb_cuft']} cu.ft @ {bp6_res['rear_tuning_fl_hz']} Hz (Low)  |  Front Cavity: {bp6_res['front_chamber_vb_cuft']} cu.ft @ {bp6_res['front_tuning_fh_hz']} Hz (High)"
            )

            # Update Enclosure Geometry model
            self.enclosure.shape = self.shape_var.get()
            self.enclosure.ext_width = self._get_float(self.entry_width, 32.0)
            self.enclosure.ext_height = self._get_float(self.entry_height, 14.5)
            self.enclosure.ext_depth_bottom = self._get_float(self.entry_depth_bot, 16.0)
            if self.enclosure.shape == "cuboid":
                self.enclosure.ext_depth_top = self.enclosure.ext_depth_bottom
            else:
                self.enclosure.ext_depth_top = self._get_float(self.entry_depth_top, 16.0)

            self.enclosure.wall_thickness = self._get_float(self.entry_mdf, 0.75)
            self.enclosure.baffle_thickness = self._get_float(self.entry_baffle_thick, 0.75)
            self.enclosure.sub_displacement_cuft = self._get_float(self.entry_sub_disp, 0.14)
            self.enclosure.bracing_displacement_cuft = self._get_float(self.entry_brace_disp, 0.06)
            self.enclosure.sub_cutout_dia_in = self._get_float(self.entry_sub_cutout, 11.125)
            self.enclosure.sub_flush_dia_in = self._get_float(self.entry_sub_flush, 12.5)
            self.enclosure.num_subwoofers = num_subs
            self.enclosure.is_chamber_isolated = is_isolated
            self.enclosure.is_inverted_sub = getattr(self, 'var_inverted_sub', tk.BooleanVar(value=False)).get()

            # Port calculations
            is_sealed = (self.topo_var.get() == "sealed")
            self.enclosure.enclosure_type = self.topo_var.get()
            self.enclosure.port_type = "none" if is_sealed else self.port_type_var.get()
            fb = self._get_float(self.entry_fb, 32.0)
            slot_w = self._get_float(self.entry_slot_w, 2.5)
            slot_h = self._get_float(self.entry_slot_h, 13.0)
            round_dia = self._get_float(self.entry_round_dia, 4.0)
            num_ports = max(1, self._get_int(self.entry_num_ports, 1))
            shared_walls = max(0, min(3, self._get_int(self.entry_shared_walls, 3)))

            self.enclosure.port_width_in = slot_w
            self.enclosure.port_height_in = slot_h
            self.enclosure.port_dia_in = round_dia
            self.enclosure.num_ports = num_ports

            if is_sealed:
                port_area = 0.0
                port_len = 0.0
            elif self.enclosure.port_type == "slot":
                port_area = slot_w * slot_h * num_ports
            else:
                port_area = math.pi * ((round_dia / 2.0) ** 2) * num_ports

            net_vb = self.enclosure.calculate_net_internal_volume_cuft()
            if not is_sealed:
                port_len = am.calculate_helmholtz_port_length(
                    vb_cuft=net_vb, fb_hz=fb, port_area_sq_in=port_area,
                    port_type=self.enclosure.port_type, shared_walls=shared_walls
                )
            self.enclosure.port_physical_length_in = port_len

            # Volumetrics
            ext_gross = self.enclosure.calculate_exterior_gross_volume_cuft()
            int_gross = self.enclosure.calculate_internal_gross_volume_cuft()
            net_vb = self.enclosure.calculate_net_internal_volume_cuft()
            port_disp = self.enclosure.calculate_port_displacement_cuft()
            sub_disp = self.enclosure.sub_displacement_cuft * num_subs
            div_disp = self.enclosure.calculate_divider_displacement_cuft()

            recline_deg = self.enclosure.seat_recline_angle_deg
            unit_mode = getattr(self, 'unit_system', 'imperial')
            if unit_mode == "imperial":
                vol_str = (
                    f"External Gross:           {ext_gross:.3f} cu.ft ({ext_gross * 1728.0:.1f} cu.in)\n"
                    f"Internal Gross:           {int_gross:.3f} cu.ft ({int_gross * 1728.0:.1f} cu.in)\n"
                    f"--------------------------------------------------------------------------------\n"
                    f"Subwoofer Displacement:   {sub_disp:.3f} cu.ft ({num_subs}x subwoofers)\n"
                    f"Chamber Isolation Walls:  {div_disp:.3f} cu.ft ({num_subs - 1 if is_isolated and num_subs > 1 else 0} dividers)\n"
                    f"Port Displacement:        {port_disp:.3f} cu.ft\n"
                    f"Bracing & Kerfs:          {self.enclosure.bracing_displacement_cuft:.3f} cu.ft\n"
                    f"--------------------------------------------------------------------------------\n"
                    f"NET INTERNAL VOLUME (Vb): {net_vb:.3f} cu.ft ({net_vb * 1728.0:.1f} cu.in)\n"
                    f"Net Volume Per Subwoofer: {net_vb / num_subs:.3f} cu.ft / sub\n"
                    f"Seat Recline Angle:       {recline_deg:.1f} degrees"
                )
            else:
                vol_str = (
                    f"External Gross:           {ext_gross * 28.3168:.1f} Liters\n"
                    f"Internal Gross:           {int_gross * 28.3168:.1f} Liters\n"
                    f"--------------------------------------------------------------------------------\n"
                    f"Subwoofer Displacement:   {sub_disp * 28.3168:.1f} Liters ({num_subs}x subwoofers)\n"
                    f"Chamber Isolation Walls:  {div_disp * 28.3168:.1f} Liters ({num_subs - 1 if is_isolated and num_subs > 1 else 0} dividers)\n"
                    f"Port Displacement:        {port_disp * 28.3168:.1f} Liters\n"
                    f"Bracing & Kerfs:          {self.enclosure.bracing_displacement_cuft * 28.3168:.1f} Liters\n"
                    f"--------------------------------------------------------------------------------\n"
                    f"NET INTERNAL VOLUME (Vb): {net_vb * 28.3168:.1f} Liters ({net_vb:.3f} cu.ft)\n"
                    f"Net Volume Per Subwoofer: {(net_vb / num_subs) * 28.3168:.1f} Liters / sub\n"
                    f"Seat Recline Angle:       {recline_deg:.1f} degrees"
                )
            self.lbl_geom_summary.configure(text=vol_str)

            # Port fluid dynamics & chuffing velocity
            if is_sealed:
                self.lbl_port_status.configure(
                    text="SEALED ENCLOSURE — Acoustic Suspension",
                    text_color="#00E5FF"
                )
                self.lbl_port_details.configure(
                    text="• 100% Airtight Acoustic Suspension: Zero port / vent required.\n"
                         "• Transients: Outstanding group delay, ultra-tight transient impulse response.\n"
                         "• Port Air Velocity: 0.0 m/s (No chuffing or vent resonance possible).\n"
                         "• Power Handling: Air spring controls cone excursion below tuning frequency."
                )
                self.bar_velocity.set(0.0)
                self.lbl_meter_velo.configure(text="0.0 m/s (N/A)")
                self.bar_velocity.configure(progress_color="#00E676")
                self.bar_port_ratio.set(0.0)
                self.lbl_meter_ratio.configure(text="N/A (Sealed)")
                self.bar_port_ratio.configure(progress_color="#00B0FF")
            else:
                velo_res = am.calculate_port_air_velocity(
                    p_rms=prms, sd_sq_in=self.ts_params.effective_sd_sq_in,
                    xmax_mm=xmax, fb_hz=fb, port_area_sq_in=port_area
                )

                self.lbl_port_status.configure(
                    text=f"{velo_res['status']} — {velo_res['velocity_mps']} m/s",
                    text_color=velo_res["badge_color"]
                )
                self.lbl_port_details.configure(
                    text=f"• Total Port Vent Area:      {port_area:.2f} sq.in ({port_area / net_vb:.2f} sq.in / cu.ft)\n"
                         f"• Required Physical Length: {port_len:.2f} inches (Tuned to {fb:.1f} Hz)\n"
                         f"• Peak Air Velocity:        {velo_res['velocity_mps']} m/s ({velo_res['velocity_fps']} ft/s)  |  Mach: {velo_res['mach_number']:.4f}\n"
                         f"• Acoustic Guideline:       Air velocity < 17 m/s guarantees 100% laminar airflow with zero port chuffing."
                )

                # Health meters
                v_val = velo_res['velocity_mps']
                self.bar_velocity.set(min(1.0, max(0.0, v_val / 34.0)))
                self.lbl_meter_velo.configure(text=f"{v_val:.1f} m/s")
                if v_val < 17.0:
                    self.bar_velocity.configure(progress_color="#00E676")
                elif v_val < 25.0:
                    self.bar_velocity.configure(progress_color="#FFD600")
                else:
                    self.bar_velocity.configure(progress_color="#FF1744")

                ratio_val = port_area / net_vb if net_vb > 0 else 0
                self.bar_port_ratio.set(min(1.0, max(0.0, ratio_val / 24.0)))
                self.lbl_meter_ratio.configure(text=f"{ratio_val:.1f} sq.in/ft³")
                if ratio_val >= 12.0 and ratio_val <= 18.0:
                    self.bar_port_ratio.configure(progress_color="#00E676")
                elif ratio_val < 10.0:
                    self.bar_port_ratio.configure(progress_color="#FF9100")
                else:
                    self.bar_port_ratio.configure(progress_color="#00B0FF")

            # Redraw 2D Canvas with CAD dimension arrows
            self._redraw_baffle_canvas()
            self._refresh_cut_sheet_tree()

            # Update Wiring Tab
            self._update_wiring_calculations()

            # Update Dashboard live card badges
            if hasattr(self, 'view_dashboard'):
                box_status = f"{net_vb:.2f} ft³" + (f" @ {fb:.1f}Hz" if not is_sealed else " (Sealed)")
                self.view_dashboard.update_card_badge("box_builder", box_status)
                self.view_dashboard.update_card_badge("settings", f"{self.unit_system.capitalize()} | {self.display_mode.capitalize()}")

        finally:
            self._updating_lock = False

    # -------------------------------------------------------------
    # 2D Front Baffle Blueprint Canvas Rendering (With CAD Arrows)
    # -------------------------------------------------------------
    def _redraw_baffle_canvas(self):
        if not hasattr(self, 'baffle_canvas'):
            return
        c = self.baffle_canvas
        c.delete("all")

        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw <= 10 or ch <= 10:
            cw, ch = 480, 240

        b_w = max(1.0, self.enclosure.ext_width)
        b_h = max(1.0, self.enclosure.ext_height)
        t = self.enclosure.wall_thickness
        n_subs = max(1, self.enclosure.num_subwoofers)
        cutout_dia = self.enclosure.sub_cutout_dia_in
        flush_dia = self.enclosure.sub_flush_dia_in
        template = self.baffle_layout_var.get() if hasattr(self, 'baffle_layout_var') else "Equidistant Centered"

        # Compute accurate fitment metrics & clearances
        flange_dia = max(cutout_dia + 0.6, flush_dia if flush_dia > cutout_dia else cutout_dia + 1.25)
        layout_mode = self.baffle_layout_combo.get() if hasattr(self, 'baffle_layout_combo') else "Horizontal"

        metrics = gm.calculate_baffle_layout_metrics(
            baffle_w=b_w,
            baffle_h=b_h,
            wall_thick=t,
            port_type=self.enclosure.port_type,
            port_w=self.enclosure.port_width_in,
            port_h=self.enclosure.port_height_in,
            port_dia=self.enclosure.port_dia_in,
            num_subs=n_subs,
            cutout_dia=cutout_dia,
            flush_dia=flush_dia,
            template=template,
            flange_dia=flange_dia,
            layout_mode=layout_mode
        )

        has_collision = metrics["has_collision"]
        has_flange_col = metrics.get("has_flange_collision", False)
        if hasattr(self, 'lbl_canvas_collision'):
            if metrics.get("has_cutout_collision"):
                self.lbl_canvas_collision.configure(text="⚠️ COLLISION: Cutout Overlap!", text_color="#FF1744")
            elif has_flange_col:
                self.lbl_canvas_collision.configure(text="⚠️ FLANGE COLLISION: Outer Rims Overlap!", text_color="#FF9100")
            else:
                self.lbl_canvas_collision.configure(text="✓ CLEARANCE OK: Rims & PCD Fit", text_color="#00E676")

        # Layout scaling with margins for top/bottom dimension arrows
        dim_margin_top = 28
        dim_margin_bot = 22
        avail_w = cw - 36
        avail_h = ch - (dim_margin_top + dim_margin_bot + 16)
        scale = min(avail_w / b_w, avail_h / b_h)

        draw_w = b_w * scale
        draw_h = b_h * scale
        ox = (cw - draw_w) / 2
        oy = dim_margin_top + ((avail_h - draw_h) / 2)

        # Draw Enclosure Perimeter
        box_border_col = "#FF1744" if has_collision else "#00E5FF"
        c.create_rectangle(ox, oy, ox + draw_w, oy + draw_h, outline=box_border_col, width=2, fill="#13171F")

        # Inner Wall Boundary (wall thickness)
        iw = max(0.0, (b_w - 2 * t) * scale)
        ih = max(0.0, (b_h - 2 * t) * scale)
        iox = ox + (t * scale)
        ioy = oy + (t * scale)
        c.create_rectangle(iox, ioy, iox + iw, ioy + ih, outline="#263238", dash=(2, 2))

        # Port Rendering (only if not sealed and port is active)
        is_sealed = (getattr(self.enclosure, 'enclosure_type', 'ported') == "sealed" or self.enclosure.port_type == "none")
        port_left_edge_x = None

        if not is_sealed:
            if self.enclosure.port_type == "slot":
                pw = self.enclosure.port_width_in * scale
                ph = min(ih, self.enclosure.port_height_in * scale)
                px = ox + draw_w - (t * scale) - pw
                py = ioy
                c.create_rectangle(px, py, px + pw, py + ph, fill="#1B2A38", outline="#00B0FF", width=1)
                c.create_text(px + (pw / 2), py + (ph / 2), text=f"SLOT PORT\n{self.enclosure.port_width_in:.1f}\" x {self.enclosure.port_height_in:.1f}\"", fill="#80D8FF", font=("Segoe UI", 7, "bold"), angle=90)
                port_left_edge_x = px
            elif self.enclosure.port_type == "round":
                r_dia = self.enclosure.port_dia_in * scale
                prx = ox + draw_w - (t * scale) - r_dia - 6
                pry = ioy + 6
                c.create_oval(prx, pry, prx + r_dia, pry + r_dia, fill="#1B2A38", outline="#00B0FF", width=1)
                c.create_text(prx + (r_dia / 2), pry + (r_dia / 2), text=f"VENT\n{self.enclosure.port_dia_in:.1f}\"", fill="#80D8FF", font=("Segoe UI", 7, "bold"))
                port_left_edge_x = prx

        # Multi-Subwoofer Rendering with PCD Screw Holes & Outer Flange
        sub_centers_coords = metrics.get("sub_centers", [(x, metrics["center_y"]) for x in metrics.get("centers_x", [])])
        f_dia = metrics.get("flange_dia", cutout_dia + 1.25)
        pcd_dia = metrics.get("pcd_dia", cutout_dia + 0.65)
        sub_screen_coords = []

        for i, (cx_in, cy_in) in enumerate(sub_centers_coords):
            cx = ox + (cx_in * scale)
            cy = oy + (cy_in * scale)
            sub_screen_coords.append(cx)

            # 1. Outer Frame Flange Circle
            flange_rad = (f_dia / 2.0) * scale
            flange_border = "#FF9100" if metrics.get("has_flange_collision") else "#263238"
            c.create_oval(cx - flange_rad, cy - flange_rad, cx + flange_rad, cy + flange_rad, outline=flange_border, width=1)

            # 2. Flush Ring (if routed)
            if flush_dia > cutout_dia:
                fr_rad = (flush_dia / 2.0) * scale
                c.create_oval(cx - fr_rad, cy - fr_rad, cx + fr_rad, cy + fr_rad, outline="#37474F", width=1, dash=(2, 2))

            # 3. Inner Cutout Hole
            c_rad = (cutout_dia / 2.0) * scale
            hole_col = "#2B171A" if metrics.get("has_cutout_collision") else "#17202C"
            c_outline = "#FF5252" if metrics.get("has_cutout_collision") else "#00E5FF"
            c.create_oval(cx - c_rad, cy - c_rad, cx + c_rad, cy + c_rad, fill=hole_col, outline=c_outline, width=2)

            # 4. Screw Pitch Circle (PCD) & 8x Mounting Screw Holes
            pcd_rad = (pcd_dia / 2.0) * scale
            c.create_oval(cx - pcd_rad, cy - pcd_rad, cx + pcd_rad, cy + pcd_rad, outline="#455A64", width=1, dash=(1, 3))
            for screw_i in range(8):
                angle_rad = (math.pi * 2.0 / 8.0) * screw_i
                sx = cx + (pcd_rad * math.cos(angle_rad))
                sy = cy + (pcd_rad * math.sin(angle_rad))
                c.create_oval(sx - 2, sy - 2, sx + 2, sy + 2, fill="#B0BEC5", outline="#37474F")

            # Crosshairs & Label
            c.create_line(cx - 5, cy, cx + 5, cy, fill="#80D8FF", width=1)
            c.create_line(cx, cy - 5, cx, cy + 5, fill="#80D8FF", width=1)
            c.create_text(cx, cy + (c_rad * 0.35), text="Sub #" + str(i+1) + "\n" + f"{cutout_dia:.2f}\"", fill="#ECEFF1", font=("Segoe UI", 7, "bold"), justify="center")

        # ---------------------------------------------------------
        # CAD-STYLE DIMENSION ARROWS & CLEARANCE LABELS (TOP RUN)
        # ---------------------------------------------------------
        arr_y = oy - 14

        def draw_dim_arrow(x1: float, x2: float, y: float, label: str, col: str = "#80D8FF"):
            if abs(x2 - x1) < 4:
                return
            # Baseline & Ticks
            c.create_line(x1, y - 4, x1, y + 4, fill=col, width=1)
            c.create_line(x2, y - 4, x2, y + 4, fill=col, width=1)
            c.create_line(x1, y, x2, y, fill=col, width=1)
            # Arrow heads
            if (x2 - x1) > 16:
                c.create_line(x1, y, x1 + 4, y - 3, fill=col, width=1)
                c.create_line(x1, y, x1 + 4, y + 3, fill=col, width=1)
                c.create_line(x2, y, x2 - 4, y - 3, fill=col, width=1)
                c.create_line(x2, y, x2 - 4, y + 3, fill=col, width=1)
            c.create_text((x1 + x2) / 2, y - 7, text=label, fill=col, font=("Segoe UI", 7, "bold"))

        # 1. Margin from Left Inner Wall to Sub 1
        sub1_left_x = sub_screen_coords[0] - ((cutout_dia / 2.0) * scale)
        draw_dim_arrow(iox, sub1_left_x, arr_y, f"{metrics['edge_left_in']:.2f}\"")

        # 2. Sub Cutout Diameters & Inter-Sub Spacings
        for i in range(n_subs):
            s_left = sub_screen_coords[i] - ((cutout_dia / 2.0) * scale)
            s_right = sub_screen_coords[i] + ((cutout_dia / 2.0) * scale)
            draw_dim_arrow(s_left, s_right, arr_y, f"{cutout_dia:.2f}\"")

            if i < n_subs - 1:
                next_left = sub_screen_coords[i + 1] - ((cutout_dia / 2.0) * scale)
                gap_col = "#FF5252" if metrics["inter_gap_in"] < 0 else "#00E676"
                draw_dim_arrow(s_right, next_left, arr_y, f"gap: {metrics['inter_gap_in']:.2f}\"", col=gap_col)

        # 3. Space from Last Sub to Port (or Right Inner Wall if sealed)
        last_right = sub_screen_coords[-1] + ((cutout_dia / 2.0) * scale)
        if port_left_edge_x is not None and port_left_edge_x > last_right:
            draw_dim_arrow(last_right, port_left_edge_x, arr_y, f"{metrics['sub_to_port_gap_in']:.2f}\" to port")
        else:
            right_inner_wall = ox + draw_w - (t * scale)
            if right_inner_wall > last_right:
                draw_dim_arrow(last_right, right_inner_wall, arr_y, f"{metrics['sub_to_port_gap_in']:.2f}\"")

        # Bottom Overall Dimension
        bot_arr_y = oy + draw_h + 12
        draw_dim_arrow(ox, ox + draw_w, bot_arr_y, f"Total Baffle: {b_w:.2f}\" W  (Height: {b_h:.2f}\" H)", col="#00E5FF")

        # Vertical Top & Bottom Clearances (drawn on left side)
        vert_x = ox - 14
        top_sub_y = cy - ((cutout_dia / 2.0) * scale)
        if top_sub_y > ioy:
            c.create_line(vert_x - 3, ioy, vert_x + 3, ioy, fill="#80D8FF", width=1)
            c.create_line(vert_x - 3, top_sub_y, vert_x + 3, top_sub_y, fill="#80D8FF", width=1)
            c.create_line(vert_x, ioy, vert_x, top_sub_y, fill="#80D8FF", width=1)
            c.create_text(vert_x - 6, (ioy + top_sub_y) / 2, text=f"{metrics['top_gap_in']:.2f}\"", fill="#80D8FF", font=("Segoe UI", 7), angle=90)

        # Cache metrics for 3D visualizer
        self._last_baffle_metrics = metrics
        if hasattr(self, 'box_3d') and hasattr(self, 'vis_mode_segmented') and "3D" in self.vis_mode_segmented.get():
            self.box_3d.redraw(self.enclosure, metrics)

    def _redraw_visualizers(self):
        self._redraw_baffle_canvas()
        if hasattr(self, 'box_3d'):
            met = getattr(self, '_last_baffle_metrics', None)
            self.box_3d.redraw(self.enclosure, met)

    def _on_vis_mode_changed(self, mode_str: str):
        if "3D" in mode_str:
            if hasattr(self, 'baffle_canvas'):
                self.baffle_canvas.pack_forget()
            if hasattr(self, 'frame_3d_controls'):
                self.frame_3d_controls.pack(fill="x", padx=8, pady=(0, 4))
            if hasattr(self, 'canvas_3d'):
                self.canvas_3d.pack(fill="both", expand=True, padx=8, pady=(0, 8))
                met = getattr(self, '_last_baffle_metrics', None)
                self.box_3d.redraw(self.enclosure, met)
        else:
            if hasattr(self, 'canvas_3d'):
                self.canvas_3d.pack_forget()
            if hasattr(self, 'frame_3d_controls'):
                self.frame_3d_controls.pack_forget()
            if hasattr(self, 'baffle_canvas'):
                self.baffle_canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))
                self._redraw_baffle_canvas()

    def _toggle_3d_shading(self):
        if not hasattr(self, 'box_3d'):
            return
        curr = self.box_3d.render_mode
        if curr == "solid":
            self.box_3d.set_render_mode("xray")
            self.btn_3d_render_mode.configure(text="X-Ray Ghost", fg_color="#0097A7")
        elif curr == "xray":
            self.box_3d.set_render_mode("wireframe")
            self.btn_3d_render_mode.configure(text="Wireframe", fg_color="#37474F")
        else:
            self.box_3d.set_render_mode("solid")
            self.btn_3d_render_mode.configure(text="Solid MDF", fg_color="#00838F")

    def _on_3d_explode_slider(self, val):
        if hasattr(self, 'box_3d'):
            self.box_3d.set_exploded(float(val))

    # -------------------------------------------------------------
    # Visual Wiring & Amplifier Calculation Engine
    # -------------------------------------------------------------
    def _on_wire_topology_changed(self, choice):
        topo = self.amp_topo_combo.get()
        # Adapt input labels and default values based on selected topology
        if "Independent" in topo or "Stereo" in topo:
            self.lbl_amp_p1.configure(text="Per-Ch RMS @ 1Ω (W):")
            self.lbl_amp_p2.configure(text="Per-Ch RMS @ 2Ω (W):")
            self.lbl_amp_p4.configure(text="Per-Ch RMS @ 4Ω (W):")
            if self.entry_amp_1ohm.get() == "1500":
                self.entry_amp_1ohm.delete(0, tk.END); self.entry_amp_1ohm.insert(0, "400")
                self.entry_amp_2ohm.delete(0, tk.END); self.entry_amp_2ohm.insert(0, "250")
                self.entry_amp_4ohm.delete(0, tk.END); self.entry_amp_4ohm.insert(0, "150")
        elif "Bridged" in topo:
            self.lbl_amp_p1.configure(text="Bridged RMS @ 1Ω (W):")
            self.lbl_amp_p2.configure(text="Bridged RMS @ 2Ω (W):")
            self.lbl_amp_p4.configure(text="Bridged RMS @ 4Ω (W):")
            if self.entry_amp_1ohm.get() == "400":
                self.entry_amp_1ohm.delete(0, tk.END); self.entry_amp_1ohm.insert(0, "1200")
                self.entry_amp_2ohm.delete(0, tk.END); self.entry_amp_2ohm.insert(0, "800")
                self.entry_amp_4ohm.delete(0, tk.END); self.entry_amp_4ohm.insert(0, "500")
        else:
            self.lbl_amp_p1.configure(text="Rated RMS @ 1Ω (W):")
            self.lbl_amp_p2.configure(text="Rated RMS @ 2Ω (W):")
            self.lbl_amp_p4.configure(text="Rated RMS @ 4Ω (W):")
        self._update_wiring_calculations()

    def _update_wiring_calculations(self):
        if not hasattr(self, 'wiring_canvas'):
            return

        # Read controls
        txt = self.wire_num_subs_combo.get()
        n_subs = int(txt.split()[0])
        is_custom = hasattr(self, 'wire_cfg_mode_seg') and "Custom" in self.wire_cfg_mode_seg.get()

        is_dvc_default = "DVC" in self.wire_coils_combo.get()
        coils_default = 2 if is_dvc_default else 1
        ohms_txt = self.wire_ohms_combo.get().replace("Ω", "").strip()
        try:
            coil_ohms_default = float(ohms_txt)
        except ValueError:
            coil_ohms_default = 4.0
        intra_default = self.wire_intra_seg.get().lower()

        per_sub_configs = []
        for i in range(n_subs):
            if is_custom and hasattr(self, 'sub_config_rows') and i < len(self.sub_config_rows):
                r = self.sub_config_rows[i]
                c_cnt = 2 if "DVC" in r["coils"].get() else 1
                o_val = float(r["ohms"].get().replace("Ω", "").strip())
                i_val = r["intra"].get().lower()
                per_sub_configs.append({"coils": c_cnt, "ohms": o_val, "intra": i_val})
            else:
                per_sub_configs.append({"coils": coils_default, "ohms": coil_ohms_default, "intra": intra_default})

        raw_inter = self.wire_inter_combo.get().lower()
        if "series-parallel" in raw_inter or "pairs in series" in raw_inter or "2 in series" in raw_inter:
            inter = "series_parallel"
        elif "parallel-series" in raw_inter or "pairs in parallel" in raw_inter or "2 in parallel" in raw_inter:
            inter = "parallel_series"
        elif "series" in raw_inter:
            inter = "series"
        else:
            inter = "parallel"

        topo = self.amp_topo_combo.get()

        # Visual aid for single vs multi-sub inter-wiring
        if n_subs == 1 or "Independent" in topo:
            self.wire_inter_combo.configure(state="disabled")
        else:
            self.wire_inter_combo.configure(state="normal")

        p_1 = self._get_float(self.entry_amp_1ohm, 1500.0)
        p_2 = self._get_float(self.entry_amp_2ohm, 900.0)
        p_4 = self._get_float(self.entry_amp_4ohm, 500.0)

        min_ohm_str = self.amp_min_stable_combo.get().split()[0]
        min_stable = float(min_ohm_str)

        calc = wm.calculate_wiring_and_amplifier_power(
            num_subs=n_subs,
            coils_per_sub=coils_default,
            coil_ohms=coil_ohms_default,
            intra_wiring=intra_default,
            inter_wiring=inter,
            topology=topo,
            amp_rated_1ohm=p_1,
            amp_rated_2ohm=p_2,
            amp_rated_4ohm=p_4,
            min_stable_ohm=min_stable,
            per_sub_configs=per_sub_configs
        )

        z_tot = calc["z_total_ohms"]
        p_tot = calc["delivered_total_rms"]
        p_sub = calc["power_per_sub_rms"]
        p_list = calc.get("sub_power_list", [p_sub] * n_subs)
        has_imbalance = calc.get("has_imbalance", False)

        # Build detailed power string showing individual speaker wattages if imbalanced
        if has_imbalance and len(set(p_list)) > 1:
            p_split_str = "  ".join([f"S{i+1}: {w:.0f}W" for i, w in enumerate(p_list)])
            power_display_str = f"TOTAL: {p_tot:,.0f}W RMS  |  SPLIT: [{p_split_str}]"
        elif "Independent" in topo or "Stereo" in topo:
            power_display_str = f"TOTAL: {p_tot:,.0f}W RMS  |  {p_sub:,.0f}W / SUB (PER-CH)"
        elif "Dual Bridged" in topo:
            power_display_str = f"TOTAL: {p_tot:,.0f}W RMS  |  {p_sub:,.0f}W / SUB"
        else:
            power_display_str = f"TOTAL: {p_tot:,.0f}W RMS  |  {p_sub:,.0f}W RMS / SPEAKER"

        if "Independent" in topo or "Stereo" in topo:
            self.lbl_wire_ohm_badge.configure(text=f"PER-CH LOAD: {z_tot:.2f} Ω", text_color=calc["color"])
        elif "Dual Bridged" in topo:
            self.lbl_wire_ohm_badge.configure(text=f"BRIDGED LOAD: {z_tot:.2f} Ω / PAIR", text_color=calc["color"])
        else:
            self.lbl_wire_ohm_badge.configure(text=f"FINAL LOAD: {z_tot:.2f} Ω", text_color=calc["color"])

        self.lbl_wire_power_badge.configure(text=power_display_str)
        self.lbl_wire_status_badge.configure(text=calc["status"], text_color=calc["color"])

        if hasattr(self, 'lbl_wire_elec_details') and "electrical" in calc:
            elec = calc["electrical"]
            diag_prefix = f"⚠️ {calc['diagnostic']} | " if calc.get("has_imbalance") else ""
            self.lbl_wire_elec_details.configure(
                text=f"{diag_prefix}⚡ Battery Run: {elec['recommended_power_cable']}  |  Fuse: {elec['recommended_fuse_amps']}A ANL  |  Speaker Leads: {elec['recommended_speaker_cable']} (Draw: {elec['ac_speaker_amps']:.1f}A RMS)",
                text_color="#FF9100" if calc.get("has_imbalance") else "#80D8FF"
            )

        # Update Dashboard card badge for Wiring Lab
        if hasattr(self, 'view_dashboard'):
            self.view_dashboard.update_card_badge("wiring_lab", f"{z_tot:.2f} ohms | {p_tot:,.0f}W RMS")

        self._draw_wiring_schematic(n_subs, per_sub_configs, intra_default, inter, topo, z_tot, p_list)

    def _draw_wiring_schematic(self, n_subs: int, per_sub_configs: Any, intra: str, inter: str, topo: str, z_tot: float, p_list: Optional[List[float]] = None):
        c = self.wiring_canvas
        c.delete("all")

        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw <= 20 or ch <= 20:
            cw, ch = 860, 390

        # Normalize per_sub_configs
        if isinstance(per_sub_configs, list) and len(per_sub_configs) >= n_subs:
            cfg_list = per_sub_configs[:n_subs]
        else:
            cfg_list = [{"coils": 2, "ohms": 4.0, "intra": intra} for _ in range(n_subs)]

        # Helper: Draw wire with dark border for realism and point-to-point clarity
        def draw_wire(coords, fill_color, width=3, outline_color="#080C10", dash=None):
            if outline_color:
                c.create_line(*coords, fill=outline_color, width=width + 2, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            if dash:
                c.create_line(*coords, fill=fill_color, width=width, dash=dash, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            else:
                c.create_line(*coords, fill=fill_color, width=width, capstyle=tk.ROUND, joinstyle=tk.ROUND)

        def draw_junction_dot(x, y, color="#00E5FF"):
            c.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline="#FFFFFF", width=1)

        # -------------------------------------------------------------
        # 1. DRAW AMPLIFIER CHASSIS & REALISTIC TERMINAL BLOCK
        # -------------------------------------------------------------
        amp_w, amp_h = 160, 220
        amp_x1, amp_y1 = 20, (ch - amp_h) / 2
        amp_x2, amp_y2 = amp_x1 + amp_w, amp_y1 + amp_h

        # Amp chassis body with heatsink fins
        c.create_rectangle(amp_x1, amp_y1, amp_x2, amp_y2, fill="#0F141C", outline="#00E5FF", width=2)
        # Heat sink accent bars on left
        for fin_y in range(int(amp_y1 + 10), int(amp_y2 - 10), 12):
            c.create_line(amp_x1 + 4, fin_y, amp_x1 + 18, fin_y, fill="#263238", width=2)

        amp_title = "MONOBLOCK"
        if "2-Channel" in topo:
            amp_title = "2-CHANNEL AMP"
        elif "4-Channel" in topo:
            amp_title = "4-CHANNEL AMP"

        c.create_text(amp_x1 + 85, amp_y1 + 16, text=amp_title, fill="#00E5FF", font=("Segoe UI", 9, "bold"))
        c.create_text(amp_x1 + 85, amp_y1 + 30, text=f"Active Load: {z_tot:.2f} Ω", fill="#80D8FF", font=("Segoe UI", 8))

        # Build physical screw terminal blocks on the right edge of the amplifier
        # We will collect active connection points:
        # amp_ch1_pos, amp_ch1_neg, amp_ch2_pos, amp_ch2_neg, etc.
        amp_term_blocks: Dict[str, Tuple[float, float]] = {}  # key -> (term_x, term_y)

        if "Monoblock" in topo:
            # Monoblock: SPK (+) and SPK (-)
            terms = [
                ("SPK +", "#D50000", True, amp_y1 + 80),
                ("SPK -", "#212121", True, amp_y1 + 140)
            ]
            for label, bg_col, is_active, t_y in terms:
                tx = amp_x2
                c.create_rectangle(tx - 18, t_y - 12, tx, t_y + 12, fill=bg_col, outline="#FF5252" if "D5" in bg_col else "#90A4AE")
                c.create_oval(tx - 13, t_y - 4, tx - 5, t_y + 4, fill="#B0BEC5", outline="#37474F")
                c.create_text(tx - 38, t_y, text=label, fill="#FFFFFF" if is_active else "#546E7A", font=("Segoe UI", 8, "bold"), anchor="e")
                amp_term_blocks[label] = (tx, t_y)

        elif "2-Channel" in topo:
            # 2-Channel: CH1 (+), CH1 (-), CH2 (+), CH2 (-)
            is_bridged = "Bridged" in topo
            terms = [
                ("CH1 +", "#D50000", True, amp_y1 + 60),
                ("CH1 -", "#212121", not is_bridged, amp_y1 + 95),
                ("CH2 +", "#D50000", not is_bridged, amp_y1 + 135),
                ("CH2 -", "#212121", True, amp_y1 + 170)
            ]
            for label, bg_col, is_active, t_y in terms:
                tx = amp_x2
                border_col = "#FF5252" if "D5" in bg_col else "#90A4AE"
                fill_col = bg_col if is_active else "#182026"
                c.create_rectangle(tx - 18, t_y - 10, tx, t_y + 10, fill=fill_col, outline=border_col if is_active else "#37474F")
                c.create_oval(tx - 13, t_y - 4, tx - 5, t_y + 4, fill="#B0BEC5" if is_active else "#455A64", outline="#263238")
                lbl_color = "#FFFFFF" if is_active else "#546E7A"
                c.create_text(tx - 24, t_y, text=label, fill=lbl_color, font=("Segoe UI", 7, "bold"), anchor="e")
                amp_term_blocks[label] = (tx, t_y)

            if is_bridged:
                # Draw high-vis bracket showing Bridged connection across CH1+ and CH2-
                c.create_line(amp_x2 - 8, amp_y1 + 60, amp_x2 + 10, amp_y1 + 60, amp_x2 + 10, amp_y1 + 170, amp_x2 - 8, amp_y1 + 170, fill="#FFD600", width=2, dash=(3, 2))
                c.create_text(amp_x2 + 14, amp_y1 + 115, text="BRIDGED", fill="#FFD600", font=("Segoe UI", 7, "bold"), anchor="w")

        elif "4-Channel Rear Bridged" in topo:
            # 4-Channel 3-Ch Mode: CH1/2 Front Stage (NC to subs), CH3(+) and CH4(-) Bridged to subs
            terms = [
                ("CH1/2", "#1E2A38", False, amp_y1 + 55),
                ("CH3 +", "#D50000", True, amp_y1 + 95),
                ("CH3 -", "#212121", False, amp_y1 + 125),
                ("CH4 +", "#D50000", False, amp_y1 + 155),
                ("CH4 -", "#212121", True, amp_y1 + 185)
            ]
            for label, bg_col, is_active, t_y in terms:
                tx = amp_x2
                border_col = "#FF5252" if "D5" in bg_col else ("#90A4AE" if is_active else "#37474F")
                c.create_rectangle(tx - 18, t_y - 9, tx, t_y + 9, fill=bg_col, outline=border_col)
                c.create_oval(tx - 13, t_y - 4, tx - 5, t_y + 4, fill="#B0BEC5" if is_active else "#455A64", outline="#263238")
                c.create_text(tx - 24, t_y, text=label, fill="#FFFFFF" if is_active else "#607D8B", font=("Segoe UI", 7, "bold"), anchor="e")
                amp_term_blocks[label] = (tx, t_y)

            # Bridged bracket for CH3/CH4
            c.create_line(amp_x2 - 8, amp_y1 + 95, amp_x2 + 10, amp_y1 + 95, amp_x2 + 10, amp_y1 + 185, amp_x2 - 8, amp_y1 + 185, fill="#FFD600", width=2, dash=(3, 2))
            c.create_text(amp_x2 + 14, amp_y1 + 140, text="REAR BRIDGED", fill="#FFD600", font=("Segoe UI", 7, "bold"), anchor="w")

        elif "4-Channel Dual Bridged" in topo:
            # Dual Bridged: Pair 1 (CH1+ / CH2-), Pair 2 (CH3+ / CH4-)
            terms = [
                ("CH1 +", "#D50000", True, amp_y1 + 50),
                ("CH1 -", "#212121", False, amp_y1 + 75),
                ("CH2 +", "#D50000", False, amp_y1 + 100),
                ("CH2 -", "#212121", True, amp_y1 + 125),
                ("CH3 +", "#D50000", True, amp_y1 + 150),
                ("CH3 -", "#212121", False, amp_y1 + 175),
                ("CH4 +", "#D50000", False, amp_y1 + 200),
                ("CH4 -", "#212121", True, amp_y1 + 225)
            ]
            for label, bg_col, is_active, t_y in terms:
                tx = amp_x2
                border_col = "#FF5252" if "D5" in bg_col else ("#90A4AE" if is_active else "#37474F")
                c.create_rectangle(tx - 16, t_y - 8, tx, t_y + 8, fill=bg_col if is_active else "#182026", outline=border_col)
                c.create_oval(tx - 12, t_y - 3, tx - 4, t_y + 3, fill="#B0BEC5" if is_active else "#455A64", outline="#263238")
                c.create_text(tx - 20, t_y, text=label, fill="#FFFFFF" if is_active else "#546E7A", font=("Segoe UI", 6, "bold"), anchor="e")
                amp_term_blocks[label] = (tx, t_y)

            # Bridged brackets
            c.create_line(amp_x2 + 6, amp_y1 + 50, amp_x2 + 12, amp_y1 + 50, amp_x2 + 12, amp_y1 + 125, amp_x2 + 6, amp_y1 + 125, fill="#FFD600", width=1.5)
            c.create_line(amp_x2 + 6, amp_y1 + 150, amp_x2 + 12, amp_y1 + 150, amp_x2 + 12, amp_y1 + 225, amp_x2 + 6, amp_y1 + 225, fill="#FF9100", width=1.5)

        else:
            # 4-Channel Independent: CH1 (+/-), CH2 (+/-), CH3 (+/-), CH4 (+/-)
            terms = [
                ("CH1 +", "#D50000", True, amp_y1 + 50),
                ("CH1 -", "#212121", True, amp_y1 + 75),
                ("CH2 +", "#D50000", True, amp_y1 + 100),
                ("CH2 -", "#212121", True, amp_y1 + 125),
                ("CH3 +", "#D50000", True, amp_y1 + 150),
                ("CH3 -", "#212121", True, amp_y1 + 175),
                ("CH4 +", "#D50000", True, amp_y1 + 200),
                ("CH4 -", "#212121", True, amp_y1 + 225)
            ]
            for label, bg_col, is_active, t_y in terms:
                tx = amp_x2
                border_col = "#FF5252" if "D5" in bg_col else "#90A4AE"
                c.create_rectangle(tx - 16, t_y - 8, tx, t_y + 8, fill=bg_col, outline=border_col)
                c.create_oval(tx - 12, t_y - 3, tx - 4, t_y + 3, fill="#B0BEC5", outline="#263238")
                c.create_text(tx - 20, t_y, text=label, fill="#FFFFFF", font=("Segoe UI", 6, "bold"), anchor="e")
                amp_term_blocks[label] = (tx, t_y)

        # -------------------------------------------------------------
        # 2. DRAW SUBWOOFERS ON RIGHT
        # -------------------------------------------------------------
        start_subs_x = amp_x2 + 55
        subs_avail_w = cw - start_subs_x - 20
        sub_slot_w = subs_avail_w / n_subs
        sub_r = min(48.0, (sub_slot_w - 28) / 2.0)
        sub_y = ch / 2

        speaker_terminals: List[Tuple[Tuple[float, float], Tuple[float, float], Optional[Tuple[float, float]], Optional[Tuple[float, float]]]] = []  # [((c1_p), (c1_n), (c2_p), (c2_n)), ...]

        for i in range(n_subs):
            sub_cx = start_subs_x + (sub_slot_w * i) + (sub_slot_w / 2.0)
            s_cfg = cfg_list[i]
            s_coils = s_cfg.get("coils", 2)
            s_ohms = s_cfg.get("ohms", 4.0)

            # Sub basket outer surround & cone
            sub_w_text = f"\n{p_list[i]:.0f}W" if p_list and i < len(p_list) else ""
            sub_col = "#FF9100" if (p_list and len(set(p_list)) > 1) else "#40C4FF"
            c.create_oval(sub_cx - sub_r, sub_y - sub_r, sub_cx + sub_r, sub_y + sub_r, fill="#141820", outline=sub_col, width=2)
            c.create_oval(sub_cx - (sub_r * 0.52), sub_y - (sub_r * 0.52), sub_cx + (sub_r * 0.52), sub_y + (sub_r * 0.52), fill="#0E1217", outline="#263238")
            c.create_text(sub_cx, sub_y, text=f"SUB {i+1}\n{'DVC' if s_coils == 2 else 'SVC'} ({s_ohms:.0f}Ω){sub_w_text}", fill="#ECEFF1", font=("Segoe UI", 7, "bold"), justify="center")

            # Coil 1 Terminals (Left side of sub)
            c1_px = sub_cx - sub_r - 4
            c1_py = sub_y - 14
            c1_nx = sub_cx - sub_r - 4
            c1_ny = sub_y + 14

            c.create_rectangle(c1_px - 7, c1_py - 5, c1_px + 2, c1_py + 5, fill="#D50000", outline="#FF5252")
            c.create_text(c1_px - 2, c1_py, text="+", fill="#FFFFFF", font=("Segoe UI", 8, "bold"))

            c.create_rectangle(c1_nx - 7, c1_ny - 5, c1_nx + 2, c1_ny + 5, fill="#212121", outline="#90A4AE")
            c.create_text(c1_nx - 2, c1_ny, text="-", fill="#FFFFFF", font=("Segoe UI", 8, "bold"))

            c.create_text(c1_px - 14, sub_y, text=f"C1\n{s_ohms:.0f}Ω", fill="#80D8FF", font=("Segoe UI", 7), justify="center")

            if s_coils == 2:
                # Coil 2 Terminals (Right side of sub)
                c2_px = sub_cx + sub_r + 4
                c2_py = sub_y - 14
                c2_nx = sub_cx + sub_r + 4
                c2_ny = sub_y + 14

                c.create_rectangle(c2_px - 2, c2_py - 5, c2_px + 7, c2_py + 5, fill="#D50000", outline="#FF5252")
                c.create_text(c2_px + 3, c2_py, text="+", fill="#FFFFFF", font=("Segoe UI", 8, "bold"))

                c.create_rectangle(c2_nx - 2, c2_ny - 5, c2_nx + 7, c2_ny + 5, fill="#212121", outline="#90A4AE")
                c.create_text(c2_nx + 3, c2_ny, text="-", fill="#FFFFFF", font=("Segoe UI", 8, "bold"))

                c.create_text(c2_px + 14, sub_y, text=f"C2\n{s_ohms:.0f}Ω", fill="#80D8FF", font=("Segoe UI", 7), justify="center")
                speaker_terminals.append(((c1_px, c1_py), (c1_nx, c1_ny), (c2_px, c2_py), (c2_nx, c2_ny)))
            else:
                speaker_terminals.append(((c1_px, c1_py), (c1_nx, c1_ny), None, None))

        # -------------------------------------------------------------
        # 3. INTRA-SPEAKER COIL WIRING (DVC Parallel or Series Jumpers)
        # -------------------------------------------------------------
        driver_entry_terms: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []  # [(pos_pt, neg_pt), ...] for each sub

        for i, spk_terms in enumerate(speaker_terminals):
            sub_cx = start_subs_x + (sub_slot_w * i) + (sub_slot_w / 2.0)
            c1_pos, c1_neg, c2_pos, c2_neg = spk_terms
            s_coils = cfg_list[i].get("coils", 2)
            s_intra = cfg_list[i].get("intra", intra)

            if s_coils == 1:
                driver_entry_terms.append((c1_pos, c1_neg))
            elif s_coils == 2 and s_intra == "parallel" and c2_pos is not None and c2_neg is not None:
                # DVC PARALLEL:
                # Coil 1 (+) to Coil 2 (+) runs horizontally across the upper cone face directly between (+) terminals
                draw_wire([c1_pos[0], c1_pos[1], c2_pos[0], c2_pos[1]], fill_color="#FF1744", width=3)
                draw_junction_dot(c1_pos[0], c1_pos[1], "#FF5252")
                draw_junction_dot(c2_pos[0], c2_pos[1], "#FF5252")
                c.create_text(sub_cx, c1_pos[1] - 8, text="COIL PARALLEL (+)", fill="#FF8A80", font=("Segoe UI", 7, "bold"))

                # Coil 1 (-) to Coil 2 (-) runs horizontally across the lower cone face directly between (-) terminals
                draw_wire([c1_neg[0], c1_neg[1], c2_neg[0], c2_neg[1]], fill_color="#37474F", width=3)
                draw_junction_dot(c1_neg[0], c1_neg[1], "#90A4AE")
                draw_junction_dot(c2_neg[0], c2_neg[1], "#90A4AE")
                c.create_text(sub_cx, c1_neg[1] + 8, text="COIL PARALLEL (-)", fill="#B0BEC5", font=("Segoe UI", 7, "bold"))

                # In DVC parallel, both coils are tied: C1(+) is the left (+) feed and C2(-) is the right (-) tap
                driver_entry_terms.append((c1_pos, c2_neg))

            elif s_coils == 2 and s_intra == "series" and c2_pos is not None and c2_neg is not None:
                # DVC SERIES:
                # Coil 1 (-) jumpers to Coil 2 (+) across the voice-coil former / cone.
                # Staying inside the driver face eliminates all collisions with bottom return rails or outer jumpers.
                draw_wire([
                    c1_neg[0], c1_neg[1],
                    sub_cx, c1_neg[1],
                    sub_cx, c2_pos[1],
                    c2_pos[0], c2_pos[1]
                ], fill_color="#FFD600", width=3, dash=(4, 2))
                draw_junction_dot(c1_neg[0], c1_neg[1], "#FFEA00")
                draw_junction_dot(sub_cx, c1_neg[1], "#FFEA00")
                draw_junction_dot(sub_cx, c2_pos[1], "#FFEA00")
                draw_junction_dot(c2_pos[0], c2_pos[1], "#FFEA00")
                c.create_text(sub_cx, sub_y + 9, text="COIL SERIES JUMPER", fill="#FFD600", font=("Segoe UI", 7, "bold"))

                # External connection: POS is C1(+), NEG is C2(-)
                driver_entry_terms.append((c1_pos, c2_neg))

        # -------------------------------------------------------------
        # 4. POINT-TO-POINT WIRING FROM AMPLIFIER TO SUBWOOFERS
        # (Strictly terminate at terminal posts — NO infinite lines!)
        # -------------------------------------------------------------
        # Determine source amplifier terminals based on topology
        amp_pairs: List[Tuple[Tuple[float, float], Tuple[float, float], str]] = []
        if "Monoblock" in topo:
            src_pos = amp_term_blocks["SPK +"]
            src_neg = amp_term_blocks["SPK -"]
            amp_pairs = [(src_pos, src_neg, "AMP")]
        elif "2-Channel Bridged" in topo:
            src_pos = amp_term_blocks["CH1 +"]
            src_neg = amp_term_blocks["CH2 -"]
            amp_pairs = [(src_pos, src_neg, "CH1+/CH2- BRIDGED")]
        elif "2-Channel Independent" in topo:
            amp_pairs = [
                (amp_term_blocks["CH1 +"], amp_term_blocks["CH1 -"], "CH1"),
                (amp_term_blocks["CH2 +"], amp_term_blocks["CH2 -"], "CH2")
            ]
        elif "4-Channel Rear Bridged" in topo:
            src_pos = amp_term_blocks["CH3 +"]
            src_neg = amp_term_blocks["CH4 -"]
            amp_pairs = [(src_pos, src_neg, "CH3+/CH4- BRIDGED")]
        elif "4-Channel Dual Bridged" in topo:
            amp_pairs = [
                (amp_term_blocks["CH1 +"], amp_term_blocks["CH2 -"], "BRIDGE 1 (CH1/2)"),
                (amp_term_blocks["CH3 +"], amp_term_blocks["CH4 -"], "BRIDGE 2 (CH3/4)")
            ]
        else:
            # 4-Channel Independent
            amp_pairs = [
                (amp_term_blocks["CH1 +"], amp_term_blocks["CH1 -"], "CH1"),
                (amp_term_blocks["CH2 +"], amp_term_blocks["CH2 -"], "CH2"),
                (amp_term_blocks["CH3 +"], amp_term_blocks["CH3 -"], "CH3"),
                (amp_term_blocks["CH4 +"], amp_term_blocks["CH4 -"], "CH4")
            ]

        # Case A: Independent Multi-Channel Mode (1 Channel wired directly to 1 Subwoofer)
        if "Independent" in topo or ("Dual Bridged" in topo and n_subs >= 2):
            for sub_idx in range(n_subs):
                pair_idx = sub_idx % len(amp_pairs)
                a_pos, a_neg, p_lbl = amp_pairs[pair_idx]
                d_pos, d_neg = driver_entry_terms[sub_idx]

                wire_offset_y = (pair_idx * 14)

                # Positive wire from amp channel (+) straight to this sub's (+)
                w_top_y = 26 + wire_offset_y
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 16 + (pair_idx * 6), a_pos[1], a_pos[0] + 16 + (pair_idx * 6), w_top_y, d_pos[0], w_top_y, d_pos[0], d_pos[1]], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                draw_junction_dot(d_pos[0], d_pos[1], "#FF5252")

                # Negative wire from amp channel (-) straight to this sub's (-)
                w_bot_y = ch - 26 - wire_offset_y
                draw_wire([a_neg[0], a_neg[1], a_neg[0] + 16 + (pair_idx * 6), a_neg[1], a_neg[0] + 16 + (pair_idx * 6), w_bot_y, d_neg[0], w_bot_y, d_neg[0], d_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                draw_junction_dot(d_neg[0], d_neg[1], "#90A4AE")

                c.create_text(d_pos[0], w_top_y - 8, text=f"{p_lbl} (+)", fill="#FF5252", font=("Segoe UI", 7, "bold"))
                c.create_text(d_neg[0], w_bot_y + 8, text=f"{p_lbl} (-)", fill="#90A4AE", font=("Segoe UI", 7, "bold"))

        # Case B: Single Combined Subwoofer Channel (Monoblock or Bridged Mono)
        else:
            a_pos, a_neg, p_lbl = amp_pairs[0]

            if n_subs == 1:
                # Direct single sub hookup
                d_pos, d_neg = driver_entry_terms[0]

                # Direct (+) wire from amp (+) to sub (+)
                w_top_y = 26
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 20, a_pos[1], a_pos[0] + 20, w_top_y, d_pos[0], w_top_y, d_pos[0], d_pos[1]], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                draw_junction_dot(d_pos[0], d_pos[1], "#FF5252")
                c.create_text((a_pos[0] + d_pos[0]) / 2, w_top_y - 8, text=f"{p_lbl} (+) DIRECT", fill="#FF5252", font=("Segoe UI", 7, "bold"))

                # Direct (-) wire from amp (-) to sub (-)
                w_bot_y = ch - 26
                draw_wire([a_neg[0], a_neg[1], a_neg[0] + 20, a_neg[1], a_neg[0] + 20, w_bot_y, d_neg[0], w_bot_y, d_neg[0], d_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                draw_junction_dot(d_neg[0], d_neg[1], "#90A4AE")
                c.create_text((a_neg[0] + d_neg[0]) / 2, w_bot_y + 8, text=f"{p_lbl} (-) RETURN", fill="#90A4AE", font=("Segoe UI", 7, "bold"))

            elif inter == "parallel":
                # Parallel multi-sub:
                # Clean distribution bus starting at amp and ending strictly at the last subwoofer
                last_pos = driver_entry_terms[-1][0]
                last_neg = driver_entry_terms[-1][1]

                w_top_y = 26
                w_bot_y = ch - 26

                # Top positive distribution rail: runs along uppermost corridor
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 20, a_pos[1], a_pos[0] + 20, w_top_y, last_pos[0], w_top_y], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                c.create_text(a_pos[0] + 30, w_top_y - 8, text=f"{p_lbl} POSITIVE (+)", fill="#FF5252", font=("Segoe UI", 7, "bold"), anchor="w")

                # Bottom negative distribution rail: runs along lowermost corridor
                draw_wire([last_neg[0], w_bot_y, a_neg[0] + 20, w_bot_y, a_neg[0] + 20, a_neg[1], a_neg[0], a_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                c.create_text(a_neg[0] + 30, w_bot_y + 8, text=f"{p_lbl} GROUND / RETURN (-)", fill="#90A4AE", font=("Segoe UI", 7, "bold"), anchor="w")

                # Each sub drops down into the positive and negative rails
                for i, (d_pos, d_neg) in enumerate(driver_entry_terms):
                    draw_wire([d_pos[0], d_pos[1], d_pos[0], w_top_y], fill_color="#FF1744", width=3)
                    draw_junction_dot(d_pos[0], w_top_y, "#FF1744")
                    draw_junction_dot(d_pos[0], d_pos[1], "#FF5252")

                    draw_wire([d_neg[0], d_neg[1], d_neg[0], w_bot_y], fill_color="#455A64", width=3)
                    draw_junction_dot(d_neg[0], w_bot_y, "#78909C")
                    draw_junction_dot(d_neg[0], d_neg[1], "#90A4AE")

            elif inter == "series_parallel" and n_subs == 3:
                # -------------------------------------------------------------
                # 3 SUBS: 2 IN SERIES, 1 IN PARALLEL
                # Branch 1: Sub 1 & Sub 2 in series. (Sub 1 (+) to Amp (+), Sub 1 (-) jumpers to Sub 2 (+), Sub 2 (-) to Amp (-))
                # Branch 2: Sub 3 in parallel with the branch. (Sub 3 (+) to Amp (+), Sub 3 (-) to Amp (-))
                # 100% Planar, zero wire overlap.
                # -------------------------------------------------------------
                w_top_y = 26
                w_bot_y = ch - 26

                s1_pos, s1_neg = driver_entry_terms[0]
                s2_pos, s2_neg = driver_entry_terms[1]
                s3_pos, s3_neg = driver_entry_terms[2]

                # Top Positive Rail: from Amp (+) across to Sub 1 (+) and all the way to Sub 3 (+)
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 20, a_pos[1], a_pos[0] + 20, w_top_y, s3_pos[0], w_top_y], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                c.create_text(a_pos[0] + 30, w_top_y - 8, text=f"{p_lbl} (+) HYBRID FEED", fill="#FF5252", font=("Segoe UI", 7, "bold"), anchor="w")

                # Drop (+) into Sub 1 and Sub 3
                for dp in (s1_pos, s3_pos):
                    draw_wire([dp[0], dp[1], dp[0], w_top_y], fill_color="#FF1744", width=3)
                    draw_junction_dot(dp[0], w_top_y, "#FF1744")
                    draw_junction_dot(dp[0], dp[1], "#FF5252")

                # Bottom Negative Return Rail: from Sub 3 (-) and Sub 2 (-) back to Amp (-)
                draw_wire([s3_neg[0], w_bot_y, a_neg[0] + 20, w_bot_y, a_neg[0] + 20, a_neg[1], a_neg[0], a_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                c.create_text(a_neg[0] + 30, w_bot_y + 8, text=f"{p_lbl} (-) RETURN", fill="#90A4AE", font=("Segoe UI", 7, "bold"), anchor="w")

                # Tap (-) from Sub 2 and Sub 3 into bottom return rail
                for dn in (s2_neg, s3_neg):
                    draw_wire([dn[0], dn[1], dn[0], w_bot_y], fill_color="#455A64", width=3)
                    draw_junction_dot(dn[0], w_bot_y, "#78909C")
                    draw_junction_dot(dn[0], dn[1], "#90A4AE")

                # Series Jumper for Sub 1 (-) -> Sub 2 (+) routed cleanly in the gap between Sub 1 & Sub 2
                mid_x = (s1_neg[0] + s2_pos[0]) / 2.0
                draw_wire([s1_neg[0], s1_neg[1], mid_x, s1_neg[1], mid_x, s2_pos[1], s2_pos[0], s2_pos[1]], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(s1_neg[0], s1_neg[1], "#FFAB40")
                draw_junction_dot(mid_x, s1_neg[1], "#FFAB40")
                draw_junction_dot(mid_x, s2_pos[1], "#FFAB40")
                draw_junction_dot(s2_pos[0], s2_pos[1], "#FFAB40")
                c.create_text(mid_x, (s1_neg[1] + s2_pos[1]) / 2.0 - 12, text="SERIES JUMPER (1→2)", fill="#FF9100", font=("Segoe UI", 7, "bold"))

            elif inter == "parallel_series" and n_subs == 3:
                # -------------------------------------------------------------
                # 3 SUBS: 2 IN PARALLEL, 1 IN SERIES
                # Bank 1: Sub 1 & Sub 2 in parallel.
                # In Series with: Sub 3.
                # Amp (+) -> Sub 1 (+) and Sub 2 (+)
                # (Sub 1 (-) & Sub 2 (-)) -> Lower bridge bus -> Riser in gap 2-3 -> Sub 3 (+)
                # Sub 3 (-) -> Amp (-)
                # 100% Planar, zero wire overlap.
                # -------------------------------------------------------------
                w_top_y = 26
                w_bot_y = ch - 26

                s1_pos, s1_neg = driver_entry_terms[0]
                s2_pos, s2_neg = driver_entry_terms[1]
                s3_pos, s3_neg = driver_entry_terms[2]

                # Top rail feeds Bank 1 Positives (Sub 1 & Sub 2)
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 20, a_pos[1], a_pos[0] + 20, w_top_y, s2_pos[0], w_top_y], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                c.create_text(a_pos[0] + 30, w_top_y - 8, text=f"{p_lbl} (+) BANK 1 FEED", fill="#FF5252", font=("Segoe UI", 7, "bold"), anchor="w")

                for dp in (s1_pos, s2_pos):
                    draw_wire([dp[0], dp[1], dp[0], w_top_y], fill_color="#FF1744", width=3)
                    draw_junction_dot(dp[0], w_top_y, "#FF1744")
                    draw_junction_dot(dp[0], dp[1], "#FF5252")

                # Sub 3 (-) returns to Amp (-) along bottom rail
                draw_wire([s3_neg[0], s3_neg[1], s3_neg[0], w_bot_y, a_neg[0] + 20, w_bot_y, a_neg[0] + 20, a_neg[1], a_neg[0], a_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(s3_neg[0], s3_neg[1], "#90A4AE")
                draw_junction_dot(s3_neg[0], w_bot_y, "#78909C")
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                c.create_text(a_neg[0] + 30, w_bot_y + 8, text=f"{p_lbl} (-) RETURN FROM SUB 3", fill="#90A4AE", font=("Segoe UI", 7, "bold"), anchor="w")

                # Series Bridge linking Bank 1 Negatives (Sub 1 & 2) to Sub 3 (+)
                # Lower bus ties Sub 1 (-) and Sub 2 (-) below woofers,
                # then rises through the gap between Sub 2 & Sub 3 and enters Sub 3 (+)
                gap_23_x = (s2_neg[0] + s3_pos[0]) / 2.0
                bridge_bot_y = sub_y + sub_r + 28

                draw_wire([s1_neg[0], s1_neg[1], s1_neg[0], bridge_bot_y, gap_23_x, bridge_bot_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_wire([s2_neg[0], s2_neg[1], s2_neg[0], bridge_bot_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(s1_neg[0], s1_neg[1], "#FFAB40")
                draw_junction_dot(s2_neg[0], s2_neg[1], "#FFAB40")
                draw_junction_dot(s1_neg[0], bridge_bot_y, "#FFAB40")
                draw_junction_dot(s2_neg[0], bridge_bot_y, "#FFAB40")

                # Riser from bridge_bot_y up to s3_pos height and into s3_pos
                draw_wire([gap_23_x, bridge_bot_y, gap_23_x, s3_pos[1], s3_pos[0], s3_pos[1]], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(gap_23_x, bridge_bot_y, "#FFAB40")
                draw_junction_dot(gap_23_x, s3_pos[1], "#FFAB40")
                draw_junction_dot(s3_pos[0], s3_pos[1], "#FFAB40")
                c.create_text(gap_23_x, (bridge_bot_y + s3_pos[1]) / 2.0, text="BANK 1→SUB 3\nSERIES BRIDGE", fill="#FF9100", font=("Segoe UI", 7, "bold"), justify="center")

            elif inter == "series_parallel" and n_subs == 4:
                # -------------------------------------------------------------
                # 4 SUBS: SERIES-PARALLEL (Pair 1 in series, Pair 2 in series, both pairs in parallel)
                # Pair 1: Sub 1 (+) to Amp (+), Sub 1 (-) jumpers to Sub 2 (+), Sub 2 (-) to Amp (-)
                # Pair 2: Sub 3 (+) to Amp (+), Sub 3 (-) jumpers to Sub 4 (+), Sub 4 (-) to Amp (-)
                # -------------------------------------------------------------
                w_top_y = 26
                w_bot_y = ch - 26

                # Amp (+) rail to Sub 1 (+) and Sub 3 (+)
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 20, a_pos[1], a_pos[0] + 20, w_top_y, driver_entry_terms[2][0][0], w_top_y], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                c.create_text(a_pos[0] + 30, w_top_y - 8, text=f"{p_lbl} (+) SERIES-PARALLEL FEED", fill="#FF5252", font=("Segoe UI", 7, "bold"), anchor="w")

                # Drop (+) into Sub 1 and Sub 3
                for s_idx in (0, 2):
                    dp = driver_entry_terms[s_idx][0]
                    draw_wire([dp[0], dp[1], dp[0], w_top_y], fill_color="#FF1744", width=3)
                    draw_junction_dot(dp[0], w_top_y, "#FF1744")
                    draw_junction_dot(dp[0], dp[1], "#FF5252")

                # Amp (-) return rail from Sub 2 (-) and Sub 4 (-)
                draw_wire([driver_entry_terms[3][1][0], w_bot_y, a_neg[0] + 20, w_bot_y, a_neg[0] + 20, a_neg[1], a_neg[0], a_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                c.create_text(a_neg[0] + 30, w_bot_y + 8, text=f"{p_lbl} (-) RETURN", fill="#90A4AE", font=("Segoe UI", 7, "bold"), anchor="w")

                # Tap (-) into Sub 2 and Sub 4
                for s_idx in (1, 3):
                    dn = driver_entry_terms[s_idx][1]
                    draw_wire([dn[0], dn[1], dn[0], w_bot_y], fill_color="#455A64", width=3)
                    draw_junction_dot(dn[0], w_bot_y, "#78909C")
                    draw_junction_dot(dn[0], dn[1], "#90A4AE")

                # Series Jumper for Pair 1 (Sub 1 (-) -> Sub 2 (+))
                # Routed strictly in the clearance gap between Sub 1 and Sub 2 to prevent any crossing
                p1_neg = driver_entry_terms[0][1]
                p1_pos = driver_entry_terms[1][0]
                mid_x1 = (p1_neg[0] + p1_pos[0]) / 2.0
                draw_wire([p1_neg[0], p1_neg[1], mid_x1, p1_neg[1], mid_x1, p1_pos[1], p1_pos[0], p1_pos[1]], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(p1_neg[0], p1_neg[1], "#FFAB40")
                draw_junction_dot(mid_x1, p1_neg[1], "#FFAB40")
                draw_junction_dot(mid_x1, p1_pos[1], "#FFAB40")
                draw_junction_dot(p1_pos[0], p1_pos[1], "#FFAB40")
                c.create_text(mid_x1, (p1_neg[1] + p1_pos[1]) / 2.0 - 12, text="PAIR 1 JUMPER", fill="#FF9100", font=("Segoe UI", 7, "bold"))

                # Series Jumper for Pair 2 (Sub 3 (-) -> Sub 4 (+))
                # Routed strictly in the clearance gap between Sub 3 and Sub 4
                p2_neg = driver_entry_terms[2][1]
                p2_pos = driver_entry_terms[3][0]
                mid_x2 = (p2_neg[0] + p2_pos[0]) / 2.0
                draw_wire([p2_neg[0], p2_neg[1], mid_x2, p2_neg[1], mid_x2, p2_pos[1], p2_pos[0], p2_pos[1]], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(p2_neg[0], p2_neg[1], "#FFAB40")
                draw_junction_dot(mid_x2, p2_neg[1], "#FFAB40")
                draw_junction_dot(mid_x2, p2_pos[1], "#FFAB40")
                draw_junction_dot(p2_pos[0], p2_pos[1], "#FFAB40")
                c.create_text(mid_x2, (p2_neg[1] + p2_pos[1]) / 2.0 - 12, text="PAIR 2 JUMPER", fill="#FF9100", font=("Segoe UI", 7, "bold"))

            elif inter == "parallel_series" and n_subs == 4:
                # -------------------------------------------------------------
                # 4 SUBS: PARALLEL-SERIES (Sub 1 & 2 in parallel, Sub 3 & 4 in parallel, bank in series)
                # Amp (+) -> (Sub 1 (+) & Sub 2 (+))
                # (Sub 1 (-) & Sub 2 (-)) -> Series Jump -> (Sub 3 (+) & Sub 4 (+))
                # (Sub 3 (-) & Sub 4 (-)) -> Amp (-)
                # -------------------------------------------------------------
                w_top_y = 26
                w_bot_y = ch - 26

                # Amp (+) to Bank 1 (Sub 1 and Sub 2 (+)) along top rail
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 20, a_pos[1], a_pos[0] + 20, w_top_y, driver_entry_terms[1][0][0], w_top_y], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                c.create_text(a_pos[0] + 30, w_top_y - 8, text=f"{p_lbl} (+) BANK 1 FEED", fill="#FF5252", font=("Segoe UI", 7, "bold"), anchor="w")
                for s_idx in (0, 1):
                    dp = driver_entry_terms[s_idx][0]
                    draw_wire([dp[0], dp[1], dp[0], w_top_y], fill_color="#FF1744", width=3)
                    draw_junction_dot(dp[0], w_top_y, "#FF1744")
                    draw_junction_dot(dp[0], dp[1], "#FF5252")

                # Bank 2 Negatives (Sub 3 & Sub 4 (-)) to Amp (-) along bottom rail
                draw_wire([driver_entry_terms[3][1][0], w_bot_y, a_neg[0] + 20, w_bot_y, a_neg[0] + 20, a_neg[1], a_neg[0], a_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                c.create_text(a_neg[0] + 30, w_bot_y + 8, text=f"{p_lbl} (-) RETURN", fill="#90A4AE", font=("Segoe UI", 7, "bold"), anchor="w")
                for s_idx in (2, 3):
                    dn = driver_entry_terms[s_idx][1]
                    draw_wire([dn[0], dn[1], dn[0], w_bot_y], fill_color="#455A64", width=3)
                    draw_junction_dot(dn[0], w_bot_y, "#78909C")
                    draw_junction_dot(dn[0], dn[1], "#90A4AE")

                # Inter-Bank Series Jumper linking Bank 1 Negatives to Bank 2 Positives:
                # Bank 1 Negatives connect to a lower bus (below subs 1 & 2).
                # Bank 2 Positives connect to an upper bus (above subs 3 & 4).
                # The riser runs precisely through the open center gap between Sub 2 and Sub 3!
                s1_cx = start_subs_x + (sub_slot_w * 1) + (sub_slot_w / 2.0)
                s2_cx = start_subs_x + (sub_slot_w * 2) + (sub_slot_w / 2.0)
                gap_x = (s1_cx + s2_cx) / 2.0  # open gap between Sub 2 and Sub 3

                b1_n1 = driver_entry_terms[0][1]
                b1_n2 = driver_entry_terms[1][1]
                b2_p1 = driver_entry_terms[2][0]
                b2_p2 = driver_entry_terms[3][0]

                bridge_bot_y = sub_y + sub_r + 28
                bridge_top_y = w_top_y + 14

                # Bank 1 lower bus
                draw_wire([b1_n1[0], b1_n1[1], b1_n1[0], bridge_bot_y, gap_x, bridge_bot_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_wire([b1_n2[0], b1_n2[1], b1_n2[0], bridge_bot_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(b1_n1[0], b1_n1[1], "#FFAB40")
                draw_junction_dot(b1_n2[0], b1_n2[1], "#FFAB40")
                draw_junction_dot(b1_n1[0], bridge_bot_y, "#FFAB40")
                draw_junction_dot(b1_n2[0], bridge_bot_y, "#FFAB40")

                # Center riser in gap
                draw_wire([gap_x, bridge_bot_y, gap_x, bridge_top_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(gap_x, bridge_bot_y, "#FFAB40")
                draw_junction_dot(gap_x, bridge_top_y, "#FFAB40")
                c.create_text(gap_x, (bridge_bot_y + bridge_top_y) / 2.0, text="INTER-BANK\nSERIES JUMP", fill="#FF9100", font=("Segoe UI", 7, "bold"), justify="center")

                # Bank 2 upper bus
                draw_wire([gap_x, bridge_top_y, b2_p2[0], bridge_top_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_wire([b2_p1[0], b2_p1[1], b2_p1[0], bridge_top_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_wire([b2_p2[0], b2_p2[1], b2_p2[0], bridge_top_y], fill_color="#FF9100", width=3, dash=(5, 2))
                draw_junction_dot(b2_p1[0], b2_p1[1], "#FFAB40")
                draw_junction_dot(b2_p2[0], b2_p2[1], "#FFAB40")
                draw_junction_dot(b2_p1[0], bridge_top_y, "#FFAB40")
                draw_junction_dot(b2_p2[0], bridge_top_y, "#FFAB40")

            else:
                # All Series multi-sub:
                # Amp (+) -> Sub 1 (+)
                # Sub 1 (-) -> Sub 2 (+) -> Sub N (+)
                # Sub N (-) -> Amp (-)
                s1_pos = driver_entry_terms[0][0]
                w_top_y = 26
                draw_wire([a_pos[0], a_pos[1], a_pos[0] + 20, a_pos[1], a_pos[0] + 20, w_top_y, s1_pos[0], w_top_y, s1_pos[0], s1_pos[1]], fill_color="#FF1744", width=3)
                draw_junction_dot(a_pos[0], a_pos[1], "#FF1744")
                draw_junction_dot(s1_pos[0], s1_pos[1], "#FF5252")
                c.create_text((a_pos[0] + s1_pos[0]) / 2, w_top_y - 8, text=f"{p_lbl} (+) TO SUB 1", fill="#FF5252", font=("Segoe UI", 7, "bold"))

                # Inter-speaker series jumpers:
                # Each jumper routes strictly through the open clearance gap between Sub i and Sub i+1.
                # From Sub i (-) across to mid gap, up to positive terminal height, then into Sub i+1 (+).
                # Because each jumper stays strictly in its own inter-sub gap, they never overlap each other!
                for i in range(n_subs - 1):
                    cur_neg = driver_entry_terms[i][1]
                    next_pos = driver_entry_terms[i + 1][0]
                    mid_x = (cur_neg[0] + next_pos[0]) / 2.0
                    draw_wire([
                        cur_neg[0], cur_neg[1],
                        mid_x, cur_neg[1],
                        mid_x, next_pos[1],
                        next_pos[0], next_pos[1]
                    ], fill_color="#FF9100", width=3, dash=(5, 2))
                    draw_junction_dot(cur_neg[0], cur_neg[1], "#FFAB40")
                    draw_junction_dot(mid_x, cur_neg[1], "#FFAB40")
                    draw_junction_dot(mid_x, next_pos[1], "#FFAB40")
                    draw_junction_dot(next_pos[0], next_pos[1], "#FFAB40")
                    c.create_text(mid_x, (cur_neg[1] + next_pos[1]) / 2.0 - 12, text=f"JUMPER {i+1}→{i+2}", fill="#FF9100", font=("Segoe UI", 7, "bold"))

                # Final sub (-) returns to amp (-)
                sn_neg = driver_entry_terms[-1][1]
                w_bot_y = ch - 26
                draw_wire([sn_neg[0], sn_neg[1], sn_neg[0], w_bot_y, a_neg[0] + 20, w_bot_y, a_neg[0] + 20, a_neg[1], a_neg[0], a_neg[1]], fill_color="#455A64", width=3)
                draw_junction_dot(sn_neg[0], sn_neg[1], "#90A4AE")
                draw_junction_dot(a_neg[0], a_neg[1], "#78909C")
                c.create_text((a_neg[0] + sn_neg[0]) / 2, w_bot_y + 8, text=f"{p_lbl} (-) RETURN FROM LAST SUB", fill="#90A4AE", font=("Segoe UI", 7, "bold"))

    def _on_save_custom_subwoofer_clicked(self):
        # Dialog to prompt for Model Name
        dialog = ctk.CTkInputDialog(text="Enter custom model name (e.g. 'Custom Beast 12'):", title="Save Custom Subwoofer")
        model_name = dialog.get_input()
        if not model_name or not model_name.strip():
            return
        model_name = model_name.strip()

        fs = self._get_float(self.entry_fs, 32.0)
        qts = self._get_float(self.entry_qts, 0.45)
        qes = self._get_float(self.entry_qes, 0.49)
        qms = self._get_float(self.entry_qms, 5.0)
        vas = self._get_float(self.entry_vas, 45.0)
        xmax = self._get_float(self.entry_xmax, 19.0)
        prms = self._get_float(self.entry_prms, 750.0)
        dia = self._get_float(self.entry_dia, 12.0)
        sd = self._get_float(self.entry_sd, 510.0)
        cutout = self._get_float(self.entry_sub_cutout, 11.125)
        flush = self._get_float(self.entry_sub_flush, 12.5)
        disp = self._get_float(self.entry_sub_disp, 0.14)

        custom_sub = sub_db.SubwooferModel(
            maker="Custom User Drivers",
            model=model_name,
            nominal_dia_inch=dia,
            fs=fs, qts=qts, qes=qes, qms=qms,
            vas_liters=vas, xmax_mm=xmax, p_rms=prms, sd_sq_cm=sd,
            sub_cutout_dia_in=cutout, sub_flush_dia_in=flush, sub_displacement_cuft=disp,
            notes=f"User customized {dia:.0f}-inch driver ({prms:.0f}W RMS)."
        )

        success = sub_db.save_custom_subwoofer_to_file(custom_sub)
        if success:
            # Refresh makers and models
            self.makers = sub_db.get_all_manufacturers()
            self.maker_combo.configure(values=self.makers)
            self.maker_combo.set("Custom User Drivers")
            self._on_maker_selected("Custom User Drivers")
            self.model_combo.set(model_name)
            self._on_model_selected(model_name)
            messagebox.showinfo("Custom Subwoofer Saved", f"Successfully saved '{model_name}' to custom_subs.json!")
        else:
            messagebox.showerror("Save Failed", "Failed to save custom subwoofer to disk.")

    def _refresh_cut_sheet_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        panels = self.enclosure.generate_cut_sheet()
        for p in panels:
            if self.display_mode == "fraction":
                w_str = decimal_to_fraction_str(p.width_in)
                h_str = decimal_to_fraction_str(p.height_in)
                t_str = decimal_to_fraction_str(p.thickness_in)
            else:
                if self.unit_system == "metric":
                    w_str = f"{p.width_in * 25.4:.1f} mm"
                    h_str = f"{p.height_in * 25.4:.1f} mm"
                    t_str = f"{p.thickness_in * 25.4:.1f} mm"
                else:
                    w_str = f'{p.width_in:.2f}"'
                    h_str = f'{p.height_in:.2f}"'
                    t_str = f'{p.thickness_in:.2f}"'

            self.tree.insert("", "end", values=(
                p.name, p.qty, w_str, h_str, t_str, f"{p.bevel_angle_deg:.1f} deg", p.notes
            ))

    # -------------------------------------------------------------
    # Clipboard & Shop Order
    # -------------------------------------------------------------
    def _copy_cuts_to_clipboard(self):
        panels = self.enclosure.generate_cut_sheet()
        lines = ["RuneBox Fabrication Cut List", "Panel Name | Qty | Width | Height | Thick | Bevel | Notes", "-" * 75]
        for p in panels:
            lines.append(f'{p.name} | {p.qty}x | {p.width_in:.2f}" | {p.height_in:.2f}" | {p.thickness_in:.2f}" | {p.bevel_angle_deg:.1f}° | {p.notes}')
        self.clipboard_clear(); self.clipboard_append("\n".join(lines))
        messagebox.showinfo("Copied to Clipboard", "Complete fabrication cut list copied to clipboard!")

    def _copy_summary_to_clipboard(self):
        net_vb = self.enclosure.calculate_net_internal_volume_cuft()
        sub_desc = f"{self.selected_maker} {self.selected_model}"
        summary = (
            f"--- RuneBox Build Summary ---\n"
            f"Subwoofer: {sub_desc} ({self.enclosure.num_subwoofers}x)\n"
            f"Chamber: {'Isolated Multi-Chamber' if self.enclosure.is_chamber_isolated and self.enclosure.num_subwoofers > 1 else 'Shared Common Chamber'}\n"
            f'Exterior Dimensions: {self.enclosure.ext_width:.2f}" W x {self.enclosure.ext_height:.2f}" H x {self.enclosure.ext_depth_bottom:.2f}" D\n'
            f"Net Working Volume: {net_vb:.3f} cu.ft ({net_vb * 28.3168:.1f} Liters)\n"
            f"Tuning Frequency: {self.entry_fb.get()} Hz\n"
            f'Port: {self.enclosure.port_type.upper()} ({self.enclosure.port_physical_length_in:.2f}" length)'
        )
        self.clipboard_clear(); self.clipboard_append(summary)
        messagebox.showinfo("Copied to Clipboard", "Enclosure build summary copied to clipboard!")

    def _open_shop_work_order(self):
        order_win = ctk.CTkToplevel(self)
        order_win.title("RuneBox // Shop Work Order & Cut Ticket")
        order_win.geometry("780x640")
        order_win.minsize(680, 500)

        txt_frame = ctk.CTkFrame(order_win, fg_color="transparent")
        txt_frame.pack(fill="both", expand=True, padx=12, pady=12)

        panels = self.enclosure.generate_cut_sheet()
        net_vb = self.enclosure.calculate_net_internal_volume_cuft()

        content = [
            "=" * 80,
            "                     RUNEBOX CAR AUDIO FABRICATION WORK ORDER",
            "                           Engineered by NfgOdin",
            "=" * 80,
            f"PROJECT: {self.selected_maker} {self.selected_model}",
            f"WOOFER QUANTITY: {self.enclosure.num_subwoofers}x Subwoofers  |  CHAMBER: {'Isolated Dividers' if self.enclosure.is_chamber_isolated and self.enclosure.num_subwoofers > 1 else 'Shared Common'}",
            f'EXTERIOR DIMS:   {self.enclosure.ext_width:.2f}" W x {self.enclosure.ext_height:.2f}" H x {self.enclosure.ext_depth_bottom:.2f}" D',
            f"NET VOLUME:      {net_vb:.3f} cu.ft ({net_vb * 28.3168:.1f} Liters)  |  TUNING: {self.entry_fb.get()} Hz",
            "-" * 80,
            f"{'PANEL NAME':<34} | {'QTY':<4} | {'WIDTH':<9} | {'HEIGHT':<9} | {'THICK':<6} | {'BEVEL':<6}",
            "-" * 80
        ]

        for p in panels:
            w_str = decimal_to_fraction_str(p.width_in)
            h_str = decimal_to_fraction_str(p.height_in)
            t_str = decimal_to_fraction_str(p.thickness_in)
            content.append(f"{p.name:<34} | {p.qty:<4} | {w_str:<9} | {h_str:<9} | {t_str:<6} | {p.bevel_angle_deg:.1f}°")

        content.extend([
            "-" * 80,
            "CRITICAL SHOP CHECKLIST:",
            "[ ] 1. Double check speaker cutout hole diameter with calipers before cutting.",
            "[ ] 2. Apply generous wood glue to all butt joints and clamp securely.",
            "[ ] 3. Seal internal seams with 100% silicone / polyurethane sealant.",
            "[ ] 4. Route port mouth with 1/2\" roundover router bit to eliminate air chuffing.",
            "=" * 80
        ])

        work_order_str = "\n".join(content)
        text_box = ctk.CTkTextbox(txt_frame, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#14181F")
        text_box.insert("1.0", work_order_str)
        text_box.pack(fill="both", expand=True, pady=(0, 8))

        btn_copy = ctk.CTkButton(txt_frame, cursor="hand2", text="📋 Copy Ticket to Clipboard", fg_color="#00838F",
            command=lambda: [self.clipboard_clear(), self.clipboard_append(work_order_str), messagebox.showinfo("Copied", "Work ticket copied!")]
        )
        btn_copy.pack(side="right")

    # -------------------------------------------------------------
    # Project Save / Load
    # -------------------------------------------------------------
    def _save_project(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".runebox",
            filetypes=[("RuneBox Project (*.runebox)", "*.runebox"), ("JSON Files (*.json)", "*.json"), ("All Files", "*.*")],
            initialfile="MySubBox.runebox"
        )
        if not filepath:
            return

        state = {
            "version": "2.1",
            "maker": self.selected_maker,
            "model": self.selected_model,
            "ts_inputs": {
                "fs": self.entry_fs.get(),
                "qts": self.entry_qts.get(),
                "qes": self.entry_qes.get(),
                "qms": self.entry_qms.get(),
                "vas": self.entry_vas.get(),
                "xmax": self.entry_xmax.get(),
                "prms": self.entry_prms.get(),
                "dia": self.entry_dia.get(),
                "sd": self.entry_sd.get(),
                "num_subs": self.entry_num_subs.get(),
                "is_isobaric": self.var_isobaric.get(),
                "is_chamber_isolated": self.var_chamber_isolated.get()
            },
            "geometry_inputs": {
                "topology": self.topo_var.get(),
                "shape": self.shape_var.get(),
                "width": self.entry_width.get(),
                "height": self.entry_height.get(),
                "depth_bottom": self.entry_depth_bot.get(),
                "depth_top": self.entry_depth_top.get(),
                "mdf_thick": self.entry_mdf.get(),
                "baffle_thick": self.entry_baffle_thick.get(),
                "sub_disp": self.entry_sub_disp.get(),
                "brace_disp": self.entry_brace_disp.get(),
                "sub_cutout": self.entry_sub_cutout.get(),
                "sub_flush": self.entry_sub_flush.get()
            },
            "port_inputs": {
                "port_type": self.port_type_var.get(),
                "fb": self.entry_fb.get(),
                "slot_w": self.entry_slot_w.get(),
                "slot_h": self.entry_slot_h.get(),
                "round_dia": self.entry_round_dia.get(),
                "num_ports": self.entry_num_ports.get(),
                "shared_walls": self.entry_shared_walls.get()
            }
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
            messagebox.showinfo("Project Saved", f"Project successfully saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")

    def _load_project(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("RuneBox Project (*.runebox)", "*.runebox"), ("JSON Files (*.json)", "*.json"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)

            ts_in = state.get("ts_inputs", {})
            self._set_entry(self.entry_fs, ts_in.get("fs", "31.5"))
            self._set_entry(self.entry_qts, ts_in.get("qts", "0.45"))
            self._set_entry(self.entry_qes, ts_in.get("qes", "0.49"))
            self._set_entry(self.entry_qms, ts_in.get("qms", "5.2"))
            self._set_entry(self.entry_vas, ts_in.get("vas", "45.0"))
            self._set_entry(self.entry_xmax, ts_in.get("xmax", "19.0"))
            self._set_entry(self.entry_prms, ts_in.get("prms", "750"))
            self._set_entry(self.entry_dia, ts_in.get("dia", "12.0"))
            self._set_entry(self.entry_sd, ts_in.get("sd", "510.0"))
            self._set_entry(self.entry_num_subs, ts_in.get("num_subs", "1"))
            self.var_isobaric.set(ts_in.get("is_isobaric", False))
            self.var_chamber_isolated.set(ts_in.get("is_chamber_isolated", False))

            geo_in = state.get("geometry_inputs", {})
            self.topo_var.set(geo_in.get("topology", "ported"))
            self.shape_var.set(geo_in.get("shape", "cuboid"))
            self._set_entry(self.entry_width, geo_in.get("width", "32.0"))
            self._set_entry(self.entry_height, geo_in.get("height", "14.5"))
            self._set_entry(self.entry_depth_bot, geo_in.get("depth_bottom", "16.0"))
            self._set_entry(self.entry_depth_top, geo_in.get("depth_top", "16.0"))
            self._set_entry(self.entry_mdf, geo_in.get("mdf_thick", "0.75"))
            self._set_entry(self.entry_baffle_thick, geo_in.get("baffle_thick", "0.75"))
            self._set_entry(self.entry_sub_disp, geo_in.get("sub_disp", "0.14"))
            self._set_entry(self.entry_brace_disp, geo_in.get("brace_disp", "0.06"))
            self._set_entry(self.entry_sub_cutout, geo_in.get("sub_cutout", "11.125"))
            self._set_entry(self.entry_sub_flush, geo_in.get("sub_flush", "12.5"))

            port_in = state.get("port_inputs", {})
            self.port_type_var.set(port_in.get("port_type", "slot"))
            self._set_entry(self.entry_fb, port_in.get("fb", "32.0"))
            self._set_entry(self.entry_slot_w, port_in.get("slot_w", "2.5"))
            self._set_entry(self.entry_slot_h, port_in.get("slot_h", "13.0"))
            self._set_entry(self.entry_round_dia, port_in.get("round_dia", "4.0"))
            self._set_entry(self.entry_num_ports, port_in.get("num_ports", "1"))
            self._set_entry(self.entry_shared_walls, port_in.get("shared_walls", "3"))

            maker = state.get("maker", "Custom / Manual Entry")
            model = state.get("model", "Custom / Manual Entry")
            self.selected_maker = maker
            self.selected_model = model
            self.maker_combo.set(maker)
            self.model_combo.set(model)

            self.update_all_calculations()
            messagebox.showinfo("Project Loaded", f"Successfully loaded project:\n{os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load project: {str(e)}")

    def _set_entry(self, entry: ctk.CTkEntry, val: str):
        entry.delete(0, tk.END)
        entry.insert(0, str(val))

    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files (*.csv)", "*.csv"), ("All Files", "*.*")], initialfile="RuneBox_Cut_Sheet.csv"
        )
        if filepath:
            try:
                self.enclosure.export_cut_sheet_csv(filepath)
                messagebox.showinfo("Export Success", f"Fabrication cut list successfully saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export CSV: {str(e)}")

    def _export_txt(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files (*.txt)", "*.txt"), ("All Files", "*.*")], initialfile="RuneBox_Build_Specification.txt"
        )
        if filepath:
            try:
                self.enclosure.export_cut_sheet_txt(filepath)
                messagebox.showinfo("Export Success", f"Build specifications successfully saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export TXT: {str(e)}")

    # -------------------------------------------------------------
    # Global Settings View & Executive Business Card About Modal
    # -------------------------------------------------------------
    def _build_settings_view(self):
        """Constructs Global Application Settings Screen."""
        container = ctk.CTkScrollableFrame(self.view_settings, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=24)

        # Title
        ctk.CTkLabel(
            container, text="⚙️ GLOBAL APPLICATION PREFERENCES",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), text_color="#00E5FF"
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            container, text="Configure global behavior, measurement formats, aesthetics, and default calculations.",
            font=ctk.CTkFont(size=13), text_color="#90A4AE"
        ).pack(anchor="w", pady=(0, 20))

        # 1. UI Appearance Section
        app_card = ctk.CTkFrame(container, fg_color="#181D26", corner_radius=10, border_color="#263238", border_width=1)
        app_card.pack(fill="x", pady=(0, 14), padx=2, ipady=8)

        ctk.CTkLabel(app_card, text="🎨 Appearance & Visual Theme", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").pack(anchor="w", padx=16, pady=(10, 6))

        theme_row = ctk.CTkFrame(app_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(theme_row, text="Color Mode:", font=ctk.CTkFont(size=12), text_color="#ECEFF1", width=140, anchor="w").pack(side="left")
        self.theme_segmented = ctk.CTkSegmentedButton(
            theme_row, values=["Dark", "Light", "System"],
            command=self._on_theme_changed, selected_color="#0091EA", height=28
        )
        self.theme_segmented.set("Dark")
        self.theme_segmented.pack(side="left", padx=10)

        # 2. Measurement & Units Section
        unit_card = ctk.CTkFrame(container, fg_color="#181D26", corner_radius=10, border_color="#263238", border_width=1)
        unit_card.pack(fill="x", pady=(0, 14), padx=2, ipady=8)

        ctk.CTkLabel(unit_card, text="📏 Measurement Units & Tape Reading", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").pack(anchor="w", padx=16, pady=(10, 6))

        unit_row = ctk.CTkFrame(unit_card, fg_color="transparent")
        unit_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(unit_row, text="Unit System:", font=ctk.CTkFont(size=12), text_color="#ECEFF1", width=140, anchor="w").pack(side="left")
        self.seg_settings_units = ctk.CTkSegmentedButton(
            unit_row, values=["Imperial (inches, cu.ft)", "Metric (cm, Liters)"],
            command=self._on_settings_unit_toggle, selected_color="#0091EA", height=28
        )
        self.seg_settings_units.set("Imperial (inches, cu.ft)" if self.unit_system == "imperial" else "Metric (cm, Liters)")
        self.seg_settings_units.pack(side="left", padx=10)

        tape_row = ctk.CTkFrame(unit_card, fg_color="transparent")
        tape_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(tape_row, text="Cut Sheet Readout:", font=ctk.CTkFont(size=12), text_color="#ECEFF1", width=140, anchor="w").pack(side="left")
        self.seg_settings_tape = ctk.CTkSegmentedButton(
            tape_row, values=["Decimals (e.g. 14.625\")", "Fractions (e.g. 14 5/8\")"],
            command=self._on_settings_tape_toggle, selected_color="#0091EA", height=28
        )
        self.seg_settings_tape.set("Decimals (e.g. 14.625\")" if self.display_mode == "decimal" else "Fractions (e.g. 14 5/8\")")
        self.seg_settings_tape.pack(side="left", padx=10)

        # 3. Default Material Presets
        mat_card = ctk.CTkFrame(container, fg_color="#181D26", corner_radius=10, border_color="#263238", border_width=1)
        mat_card.pack(fill="x", pady=(0, 14), padx=2, ipady=8)

        ctk.CTkLabel(mat_card, text="🪵 Enclosure Fabrication Defaults", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00E5FF").pack(anchor="w", padx=16, pady=(10, 6))

        mdf_row = ctk.CTkFrame(mat_card, fg_color="transparent")
        mdf_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(mdf_row, text="Standard Sheet Stock:", font=ctk.CTkFont(size=12), text_color="#ECEFF1", width=140, anchor="w").pack(side="left")
        self.combo_def_mdf = ctk.CTkComboBox(
            mdf_row, values=["0.75\" (3/4 MDF / Baltic Birch)", "0.50\" (1/2 Sheet)", "1.00\" (1 inch Heavy HDF)"],
            width=240, command=self._on_def_mdf_changed
        )
        self.combo_def_mdf.set("0.75\" (3/4 MDF / Baltic Birch)")
        self.combo_def_mdf.pack(side="left", padx=10)

        # Bottom Bar with About Button Anchored in Corner
        bot_action_row = ctk.CTkFrame(container, fg_color="transparent")
        bot_action_row.pack(fill="x", pady=(16, 10))

        self.btn_about = ctk.CTkButton(bot_action_row, cursor="hand2",
            text="ℹ️ About RuneBox & Creator",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1F2A38", hover_color="#00E5FF", text_color="#00E5FF",
            border_color="#00B0FF", border_width=1,
            height=36, corner_radius=8,
            command=self._open_about_window
        )
        self.btn_about.pack(side="right", padx=4)

    def _on_theme_changed(self, choice: str):
        ctk.set_appearance_mode(choice.lower())

    def _on_settings_unit_toggle(self, choice: str):
        if "Metric" in choice:
            self.unit_system = "metric"
            self.btn_toggle_units.configure(text="Unit: Metric")
        else:
            self.unit_system = "imperial"
            self.btn_toggle_units.configure(text="Unit: Imperial")
        self.update_all_calculations()

    def _on_settings_tape_toggle(self, choice: str):
        if "Fractions" in choice:
            self.display_mode = "fraction"
            self.btn_toggle_fraction.configure(text='Tape: 1/16"')
        else:
            self.display_mode = "decimal"
            self.btn_toggle_fraction.configure(text="Tape: Decimals")
        self._refresh_cut_sheet_tree()

    def _on_def_mdf_changed(self, choice: str):
        val = "0.75" if "0.75" in choice else ("0.50" if "0.50" in choice else "1.00")
        self.entry_mdf.delete(0, tk.END)
        self.entry_mdf.insert(0, val)
        self.update_all_calculations()

    def _open_about_window(self):
        """
        Pops up a sleek modal window designed like an executive cyber/audio business card.
        """
        about_win = ctk.CTkToplevel(self)
        about_win.title("About RuneBox // Creator Card")
        about_win.geometry("520x460")
        about_win.resizable(False, False)
        about_win.transient(self)
        about_win.grab_set()

        # Center on parent window
        x = self.winfo_x() + (self.winfo_width() // 2) - 260
        y = self.winfo_y() + (self.winfo_height() // 2) - 230
        about_win.geometry(f"+{x}+{y}")

        # Business Card Outer Container with Neon Accent Border
        card = ctk.CTkFrame(
            about_win, fg_color="#121620", border_color="#00E5FF", border_width=2, corner_radius=16
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Top Metallic Accent Strip
        top_strip = ctk.CTkFrame(card, height=6, fg_color="#00E5FF", corner_radius=0)
        top_strip.pack(fill="x", padx=2, pady=(2, 10))

        # Geometric Logo & Title
        logo_frame = ctk.CTkFrame(card, fg_color="transparent")
        logo_frame.pack(fill="x", padx=24, pady=(6, 4))

        ctk.CTkLabel(
            logo_frame, text="⚡ ᚱᚢᚾᛖ ⚡",
            font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color="#00E5FF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame, text="RUNEBOX // ACOUSTIC SUITE",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), text_color="#ECEFF1"
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame, text="High-SPL Subwoofer Engineering & Fabrication Studio",
            font=ctk.CTkFont(size=12), text_color="#90A4AE"
        ).pack(anchor="w", pady=(2, 8))

        # Divider
        ctk.CTkFrame(card, height=1, fg_color="#263238").pack(fill="x", padx=24, pady=6)

        # Creator / Developer Information
        dev_frame = ctk.CTkFrame(card, fg_color="transparent")
        dev_frame.pack(fill="x", padx=24, pady=6)

        ctk.CTkLabel(
            dev_frame, text="ENGINEERED BY:",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748B"
        ).pack(anchor="w")

        ctk.CTkLabel(
            dev_frame, text="NfgOdin",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color="#00E676"
        ).pack(anchor="w")

        ctk.CTkLabel(
            dev_frame, text="System Architect & Audio DSP / Subwoofer Box Specialist",
            font=ctk.CTkFont(size=11), text_color="#B0BEC5"
        ).pack(anchor="w", pady=(1, 6))

        # Build Version & Specs
        spec_frame = ctk.CTkFrame(card, fg_color="#18202A", corner_radius=8)
        spec_frame.pack(fill="x", padx=24, pady=8, ipady=4)

        specs_text = (
            "• Version: 2.2-Studio (Overhaul Edition)\n"
            "• Engine: Python 3.14 + CustomTkinter + Pure Canvas 3D Vector Engine\n"
            "• Capabilities: T/S Alignments, CAD 2D/3D Blueprinting, Ohms Solver, Shop Orders"
        )
        ctk.CTkLabel(
            spec_frame, text=specs_text, font=ctk.CTkFont(family="Consolas", size=10),
            justify="left", text_color="#80D8FF"
        ).pack(anchor="w", padx=12, pady=6)

        # Action Buttons (GitHub / Feedback / Close)
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(10, 16))

        btn_git = ctk.CTkButton(actions, cursor="hand2", text="🌐 GitHub Repo", width=120, height=32,
            fg_color="#24292E", hover_color="#37474F", text_color="#ECEFF1",
            command=lambda: webbrowser.open("https://github.com/NfgOdin")
        )
        btn_git.pack(side="left", padx=(0, 6))

        btn_feedback = ctk.CTkButton(actions, cursor="hand2", text="✉️ Send Feedback", width=130, height=32,
            fg_color="#00838F", hover_color="#00ACC1", text_color="#FFFFFF",
            command=lambda: webbrowser.open("mailto:feedback@runebox.local?subject=RuneBox%20Feedback")
        )
        btn_feedback.pack(side="left", padx=4)

        btn_close = ctk.CTkButton(actions, cursor="hand2", text="Close", width=80, height=32,
            fg_color="#37474F", hover_color="#455A64", text_color="#ECEFF1",
            command=about_win.destroy
        )
        btn_close.pack(side="right")


def main():
    app = RuneBoxApp()
    app.mainloop()


if __name__ == "__main__":
    main()
