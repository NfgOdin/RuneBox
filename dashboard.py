"""
RuneBox // Subwoofer Enclosure Lab
dashboard.py - Responsive Card-Based Home Navigation Studio.
Dynamically calculates grid layouts for 1, 2, 3, 4+ cards with smooth hover animations.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable, List, Dict, Any, Optional


class DashboardCard(ctk.CTkFrame):
    """
    Interactive studio card that highlights on hover and navigates on click.
    """
    def __init__(
        self,
        master,
        card_id: str,
        title: str,
        subtitle: str,
        icon: str,
        badge_text: str,
        accent_color: str = "#00E5FF",
        command: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=14,
            fg_color="#181D26",
            border_color="#263238",
            border_width=2,
            cursor="hand2",
            **kwargs
        )
        self.card_id = card_id
        self.command = command
        self.accent_color = accent_color
        self.base_border = "#263238"
        self.hover_border = accent_color
        self.base_bg = "#181D26"
        self.hover_bg = "#1D232E"

        self._build_ui(title, subtitle, icon, badge_text)
        self._bind_hover()

    def _build_ui(self, title: str, subtitle: str, icon: str, badge_text: str):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top Bar: Icon & Badge
        self.top_row = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        self.top_row.pack(fill="x", padx=20, pady=(20, 10))

        self.icon_lbl = ctk.CTkLabel(
            self.top_row, text=icon, font=ctk.CTkFont(size=36), cursor="hand2"
        )
        self.icon_lbl.pack(side="left")

        self.badge_lbl = ctk.CTkLabel(
            self.top_row,
            text=badge_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#101C26",
            text_color=self.accent_color,
            corner_radius=6,
            padx=10,
            pady=4,
            cursor="hand2"
        )
        self.badge_lbl.pack(side="right")

        # Title
        self.title_lbl = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ECEFF1",
            anchor="w",
            cursor="hand2"
        )
        self.title_lbl.pack(fill="x", padx=20, pady=(4, 6))

        # Subtitle / Description
        self.sub_lbl = ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(size=13),
            text_color="#90A4AE",
            justify="left",
            wraplength=340,
            anchor="w",
            cursor="hand2"
        )
        self.sub_lbl.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        # Bottom Action Bar
        self.bot_row = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        self.bot_row.pack(fill="x", padx=20, pady=(0, 18))

        self.btn_open = ctk.CTkButton(
            self.bot_row,
            text="Open Studio ➔",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#212A36",
            hover_color=self.accent_color,
            text_color=self.accent_color,
            height=34,
            corner_radius=8,
            command=self._on_click
        )
        self.btn_open.pack(fill="x")

    def _bind_hover(self):
        widgets = [
            self, self.title_lbl, self.sub_lbl,
            self.icon_lbl, self.badge_lbl,
            self.top_row, self.bot_row
        ]
        for w in widgets:
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", lambda e: self._on_click())

    def _on_enter(self, event=None):
        self.configure(border_color=self.hover_border, fg_color=self.hover_bg)

    def _on_leave(self, event=None):
        self.configure(border_color=self.base_border, fg_color=self.base_bg)

    def _on_click(self):
        if self.command:
            self.command(self.card_id)

    def update_badge(self, text: str):
        self.badge_lbl.configure(text=text)


class DashboardView(ctk.CTkFrame):
    """
    Main responsive dashboard view that holds dynamic studio cards.
    Automatically recalculates card grid columns and sizing on window resize.
    """
    def __init__(self, master, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color="#0D1017", **kwargs)
        self.on_navigate = on_navigate
        self.cards: Dict[str, DashboardCard] = {}

        # Outer Scrollable/Flexible Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40, pady=30)

        # Header Hero Banner
        self._build_header()

        # Dynamic Grid Container
        self.grid_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, pady=(20, 10))

        self._create_cards()
        self.bind("<Configure>", self._on_resize)

    def _build_header(self):
        head = ctk.CTkFrame(self.container, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            head,
            text="WELCOME TO RUNEBOX STUDIO",
            font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
            text_color="#00E5FF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            head,
            text="Select an engineering lab below to begin designing, simulating, and fabricating.",
            font=ctk.CTkFont(size=14),
            text_color="#90A4AE"
        ).pack(anchor="w", pady=(2, 0))

    def _create_cards(self):
        card_defs = [
            {
                "id": "box_builder",
                "title": "📦 Enclosure Studio",
                "subtitle": "Step-by-step custom box designer: T/S alignment, 2D Baffle CAD blueprints, 3D interactive visualizer, port air velocity tuning, and precision table saw cut sheets.",
                "icon": "📐",
                "badge": "Box Lab Active",
                "accent": "#00E5FF"
            },
            {
                "id": "wiring_lab",
                "title": "⚡ Visual Wiring & Amp Lab",
                "subtitle": "Interactive voice coil schematic workbench: Series, parallel, and hybrid multi-sub configurations, impedance solver, and exact wattage distribution.",
                "icon": "⚡",
                "badge": "Wiring Lab",
                "accent": "#FFB300"
            },
            {
                "id": "settings",
                "title": "⚙️ Global Settings",
                "subtitle": "Application preferences: Dark/Light visual themes, Imperial/Metric units, tape measure fraction formatting, default templates, and creator info.",
                "icon": "⚙️",
                "badge": "System Preferences",
                "accent": "#9C27B0"
            }
        ]

        for c_def in card_defs:
            card = DashboardCard(
                self.grid_frame,
                card_id=c_def["id"],
                title=c_def["title"],
                subtitle=c_def["subtitle"],
                icon=c_def["icon"],
                badge_text=c_def["badge"],
                accent_color=c_def["accent"],
                command=self.on_navigate
            )
            self.cards[c_def["id"]] = card

        self._layout_cards()

    def _layout_cards(self):
        """Arranges cards dynamically based on card count and container width."""
        w = self.winfo_width()
        n = len(self.cards)
        if n == 0:
            return

        # Determine number of columns based on width
        if w < 750 or n == 1:
            cols = 1
        elif w < 1150 or n == 2:
            cols = 2
        else:
            cols = min(3, n)

        # Clear existing grid
        for card in self.cards.values():
            card.grid_forget()

        for c_idx in range(cols):
            self.grid_frame.grid_columnconfigure(c_idx, weight=1, uniform="card_col")

        card_list = list(self.cards.values())
        for idx, card in enumerate(card_list):
            row = idx // cols
            col = idx % cols
            card.grid(row=row, column=col, padx=14, pady=14, sticky="nsew")
            self.grid_frame.grid_rowconfigure(row, weight=1)

    def _on_resize(self, event):
        self._layout_cards()

    def update_card_badge(self, card_id: str, badge_text: str):
        if card_id in self.cards:
            self.cards[card_id].update_badge(badge_text)
