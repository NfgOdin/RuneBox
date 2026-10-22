"""
RuneBox // Subwoofer Enclosure Lab
subwoofer_database.py - Modular, expandable manufacturer and driver specification database.
Created by NfgOdin
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class SubwooferModel:
    """Standardized electro-acoustic driver specification."""
    maker: str
    model: str
    nominal_dia_inch: float
    fs: float
    qts: float
    qes: float
    qms: float
    vas_liters: float
    xmax_mm: float
    p_rms: float
    sd_sq_cm: Optional[float] = None
    sub_cutout_dia_in: float = 11.125
    sub_flush_dia_in: float = 12.5
    sub_displacement_cuft: float = 0.14
    notes: str = ""


# Hierarchical Database: Maker -> Model Dictionary
SUBWOOFER_DB: Dict[str, Dict[str, SubwooferModel]] = {
    "Sundown Audio": {
        "SA-10 V.2 D2 (750W RMS)": SubwooferModel(
            maker="Sundown Audio", model="SA-10 V.2 D2",
            nominal_dia_inch=10.0, fs=35.4, qts=0.42, qes=0.46, qms=4.9,
            vas_liters=17.2, xmax_mm=19.0, p_rms=750.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=8.875, sub_flush_dia_in=10.375, sub_displacement_cuft=0.10,
            notes="Iconic high-output 10-inch competition daily driver."
        ),
        "SA-12 V.2 D2 (750W RMS)": SubwooferModel(
            maker="Sundown Audio", model="SA-12 V.2 D2",
            nominal_dia_inch=12.0, fs=33.7, qts=0.44, qes=0.49, qms=4.7,
            vas_liters=33.4, xmax_mm=19.0, p_rms=750.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.6, sub_displacement_cuft=0.14,
            notes="Benchmark SPL/daily 12-inch standard."
        ),
        "SA-15 V.2 D2 (750W RMS)": SubwooferModel(
            maker="Sundown Audio", model="SA-15 V.2 D2",
            nominal_dia_inch=15.0, fs=29.2, qts=0.46, qes=0.51, qms=4.5,
            vas_liters=88.5, xmax_mm=19.0, p_rms=750.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=13.85, sub_flush_dia_in=15.6, sub_displacement_cuft=0.17,
            notes="High compliance, deep low-bass reach."
        ),
        "U-12 D2 (1500W RMS)": SubwooferModel(
            maker="Sundown Audio", model="U-12 D2",
            nominal_dia_inch=12.0, fs=34.8, qts=0.39, qes=0.43, qms=4.8,
            vas_liters=27.8, xmax_mm=25.0, p_rms=1500.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.75, sub_displacement_cuft=0.21,
            notes="Cast aluminum frame with 3-inch 4-layer coil."
        ),
        "X-12 V.3 D2 (2000W RMS)": SubwooferModel(
            maker="Sundown Audio", model="X-12 V.3 D2",
            nominal_dia_inch=12.0, fs=29.8, qts=0.34, qes=0.37, qms=4.6,
            vas_liters=23.5, xmax_mm=30.0, p_rms=2000.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.8, sub_displacement_cuft=0.22,
            notes="Ultra-high excursion platform with custom tooled high-roll surround."
        ),
        "ZV6-12 D2 (2500W RMS)": SubwooferModel(
            maker="Sundown Audio", model="ZV6-12 D2",
            nominal_dia_inch=12.0, fs=32.0, qts=0.32, qes=0.35, qms=4.4,
            vas_liters=21.0, xmax_mm=35.0, p_rms=2500.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=13.0, sub_displacement_cuft=0.26,
            notes="Flagship SPL competition platform."
        )
    },

    "JL Audio": {
        "10W7AE-3 (750W RMS)": SubwooferModel(
            maker="JL Audio", model="10W7AE-3",
            nominal_dia_inch=10.0, fs=30.6, qts=0.45, qes=0.48, qms=7.0,
            vas_liters=36.1, xmax_mm=23.0, p_rms=750.0, sd_sq_cm=370.0,
            sub_cutout_dia_in=8.75, sub_flush_dia_in=10.5, sub_displacement_cuft=0.09,
            notes="W-Cone, OverRoll surround, reference sound quality."
        ),
        "12W7AE-3 (1000W RMS)": SubwooferModel(
            maker="JL Audio", model="12W7AE-3",
            nominal_dia_inch=12.0, fs=27.2, qts=0.48, qes=0.51, qms=7.8,
            vas_liters=66.0, xmax_mm=29.0, p_rms=1000.0, sd_sq_cm=542.0,
            sub_cutout_dia_in=10.5, sub_flush_dia_in=12.5, sub_displacement_cuft=0.14,
            notes="Ultimate reference SQ/SPL flagship 12-inch."
        ),
        "13W7AE-1.5 (1500W RMS)": SubwooferModel(
            maker="JL Audio", model="13W7AE-1.5",
            nominal_dia_inch=13.5, fs=23.5, qts=0.45, qes=0.48, qms=6.7,
            vas_liters=104.9, xmax_mm=32.0, p_rms=1500.0, sd_sq_cm=737.0,
            sub_cutout_dia_in=11.875, sub_flush_dia_in=14.0, sub_displacement_cuft=0.21,
            notes="Legendary 13.5-inch acoustic monster."
        ),
        "12W6v3-D4 (600W RMS)": SubwooferModel(
            maker="JL Audio", model="12W6v3-D4",
            nominal_dia_inch=12.0, fs=26.9, qts=0.46, qes=0.49, qms=8.5,
            vas_liters=54.4, xmax_mm=19.0, p_rms=600.0, sd_sq_cm=497.0,
            sub_cutout_dia_in=11.06, sub_flush_dia_in=12.5, sub_displacement_cuft=0.10,
            notes="High SQ audiophile daily bass."
        ),
        "10W3v3-4 (500W RMS)": SubwooferModel(
            maker="JL Audio", model="10W3v3-4",
            nominal_dia_inch=10.0, fs=31.5, qts=0.48, qes=0.53, qms=5.4,
            vas_liters=32.3, xmax_mm=15.0, p_rms=500.0, sd_sq_cm=345.0,
            sub_cutout_dia_in=9.125, sub_flush_dia_in=10.5, sub_displacement_cuft=0.06,
            notes="Compact box requirement daily staple."
        )
    },

    "Skar Audio": {
        "SDR-10 D4 (600W RMS)": SubwooferModel(
            maker="Skar Audio", model="SDR-10 D4",
            nominal_dia_inch=10.0, fs=38.0, qts=0.47, qes=0.52, qms=4.8,
            vas_liters=18.5, xmax_mm=13.5, p_rms=600.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.3, sub_flush_dia_in=10.4, sub_displacement_cuft=0.08,
            notes="High value budget daily woofer."
        ),
        "SDR-12 D2 (600W RMS)": SubwooferModel(
            maker="Skar Audio", model="SDR-12 D2",
            nominal_dia_inch=12.0, fs=32.0, qts=0.49, qes=0.55, qms=4.6,
            vas_liters=42.0, xmax_mm=13.5, p_rms=600.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.1, sub_flush_dia_in=12.5, sub_displacement_cuft=0.11,
            notes="High efficiency daily driver."
        ),
        "EVL-12 D2 (1250W RMS)": SubwooferModel(
            maker="Skar Audio", model="EVL-12 D2",
            nominal_dia_inch=12.0, fs=32.0, qts=0.38, qes=0.41, qms=5.1,
            vas_liters=38.0, xmax_mm=23.5, p_rms=1250.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.22, sub_flush_dia_in=12.6, sub_displacement_cuft=0.17,
            notes="Massive motor structure and heavy competition coil."
        ),
        "EVL-15 D2 (1250W RMS)": SubwooferModel(
            maker="Skar Audio", model="EVL-15 D2",
            nominal_dia_inch=15.0, fs=27.5, qts=0.41, qes=0.44, qms=5.3,
            vas_liters=86.0, xmax_mm=23.5, p_rms=1250.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=13.9, sub_flush_dia_in=15.7, sub_displacement_cuft=0.20,
            notes="Deep subterranean low bass SPL."
        ),
        "VXF-12 D2 (1500W RMS)": SubwooferModel(
            maker="Skar Audio", model="VXF-12 D2",
            nominal_dia_inch=12.0, fs=33.0, qts=0.36, qes=0.39, qms=4.9,
            vas_liters=31.0, xmax_mm=25.0, p_rms=1500.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.7, sub_displacement_cuft=0.22,
            notes="Engineered specifically for low tuning bass reflex enclosures."
        )
    },

    "Dayton Audio": {
        "RSS265HO-4 10\" Reference (600W)": SubwooferModel(
            maker="Dayton Audio", model="RSS265HO-4",
            nominal_dia_inch=10.0, fs=29.0, qts=0.34, qes=0.38, qms=3.8,
            vas_liters=27.5, xmax_mm=12.6, p_rms=600.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.25, sub_flush_dia_in=10.5, sub_displacement_cuft=0.07,
            notes="Anodized aluminum cone with extremely low harmonic distortion."
        ),
        "RSS315HO-4 12\" Reference (700W)": SubwooferModel(
            maker="Dayton Audio", model="RSS315HO-4",
            nominal_dia_inch=12.0, fs=28.5, qts=0.36, qes=0.39, qms=4.1,
            vas_liters=48.0, xmax_mm=14.0, p_rms=700.0, sd_sq_cm=505.0,
            sub_cutout_dia_in=11.1, sub_flush_dia_in=12.5, sub_displacement_cuft=0.10,
            notes="Audiophile sound quality benchmark in compact vented or sealed."
        ),
        "RSS390HO-4 15\" Reference (800W)": SubwooferModel(
            maker="Dayton Audio", model="RSS390HO-4",
            nominal_dia_inch=15.0, fs=23.0, qts=0.35, qes=0.38, qms=4.2,
            vas_liters=145.0, xmax_mm=15.0, p_rms=800.0, sd_sq_cm=855.0,
            sub_cutout_dia_in=13.88, sub_flush_dia_in=15.5, sub_displacement_cuft=0.14,
            notes="High acoustic compliance with deep linear travel."
        ),
        "Ultimax UM12-22 12\" DVC (600W)": SubwooferModel(
            maker="Dayton Audio", model="Ultimax UM12-22",
            nominal_dia_inch=12.0, fs=24.9, qts=0.48, qes=0.53, qms=5.3,
            vas_liters=62.0, xmax_mm=19.0, p_rms=600.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.5, sub_displacement_cuft=0.12,
            notes="Massive deep-dish thick carbon-reinforced paper cone."
        ),
        "Ultimax UM15-22 15\" DVC (800W)": SubwooferModel(
            maker="Dayton Audio", model="Ultimax UM15-22",
            nominal_dia_inch=15.0, fs=19.5, qts=0.53, qes=0.58, qms=5.7,
            vas_liters=158.0, xmax_mm=19.0, p_rms=800.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=13.875, sub_flush_dia_in=15.5, sub_displacement_cuft=0.18,
            notes="Ultra-low resonance (19.5 Hz) ideal for deep tuned ground-shaking bass."
        )
    },

    "Kicker": {
        "CompC 10\" (250W RMS)": SubwooferModel(
            maker="Kicker", model="CompC 10",
            nominal_dia_inch=10.0, fs=34.0, qts=0.55, qes=0.61, qms=5.6,
            vas_liters=31.0, xmax_mm=10.3, p_rms=250.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.125, sub_flush_dia_in=10.5, sub_displacement_cuft=0.05,
            notes="Signature yellow stitching with forced air cooling."
        ),
        "CompR 12\" D2 (500W RMS)": SubwooferModel(
            maker="Kicker", model="CompR 12 D2",
            nominal_dia_inch=12.0, fs=30.0, qts=0.50, qes=0.54, qms=6.8,
            vas_liters=64.0, xmax_mm=14.1, p_rms=500.0, sd_sq_cm=520.0,
            sub_cutout_dia_in=11.0, sub_flush_dia_in=12.5, sub_displacement_cuft=0.09,
            notes="All-around daily bass performer with stacked ceramic magnets."
        ),
        "CompVX 12\" D2 (750W RMS)": SubwooferModel(
            maker="Kicker", model="CompVX 12 D2",
            nominal_dia_inch=12.0, fs=28.4, qts=0.38, qes=0.41, qms=5.4,
            vas_liters=55.0, xmax_mm=16.4, p_rms=750.0, sd_sq_cm=520.0,
            sub_cutout_dia_in=11.06, sub_flush_dia_in=12.5, sub_displacement_cuft=0.12,
            notes="Cast aluminum basket with round Solo-Baric motor technology."
        ),
        "Solo-Baric L7S 12\" Square (750W RMS)": SubwooferModel(
            maker="Kicker", model="Solo-Baric L7S 12",
            nominal_dia_inch=12.0, fs=34.1, qts=0.53, qes=0.57, qms=7.1,
            vas_liters=54.3, xmax_mm=16.3, p_rms=750.0, sd_sq_cm=650.0,
            sub_cutout_dia_in=11.06, sub_flush_dia_in=12.5, sub_displacement_cuft=0.13,
            notes="Square cone geometry producing ~20% more radiating area than round 12s."
        )
    },

    "Digital Designs (DD Audio)": {
        "Redline 612 D2 (600W RMS)": SubwooferModel(
            maker="Digital Designs", model="Redline 612 D2",
            nominal_dia_inch=12.0, fs=34.0, qts=0.48, qes=0.52, qms=5.5,
            vas_liters=36.0, xmax_mm=14.0, p_rms=600.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.18, sub_flush_dia_in=12.5, sub_displacement_cuft=0.11,
            notes="Multi-layer EROM surround and high temperature voice coil."
        ),
        "Redline 712 D2 (1200W RMS)": SubwooferModel(
            maker="Digital Designs", model="Redline 712 D2",
            nominal_dia_inch=12.0, fs=33.5, qts=0.42, qes=0.45, qms=4.8,
            vas_liters=31.5, xmax_mm=17.0, p_rms=1200.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.6, sub_displacement_cuft=0.16,
            notes="Heavy duty cast frame competition series."
        ),
        "Power Series 9512 (2000W RMS)": SubwooferModel(
            maker="Digital Designs", model="Power Series 9512",
            nominal_dia_inch=12.0, fs=35.0, qts=0.31, qes=0.33, qms=5.2,
            vas_liters=24.0, xmax_mm=28.0, p_rms=2000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.3, sub_flush_dia_in=12.8, sub_displacement_cuft=0.24,
            notes="Legendary American hand-built SPL monster."
        )
    },

    "Rockford Fosgate": {
        "Punch P2D4-12 (400W RMS)": SubwooferModel(
            maker="Rockford Fosgate", model="Punch P2D4-12",
            nominal_dia_inch=12.0, fs=27.2, qts=0.53, qes=0.58, qms=6.5,
            vas_liters=78.6, xmax_mm=13.3, p_rms=400.0, sd_sq_cm=515.0,
            sub_cutout_dia_in=11.22, sub_flush_dia_in=12.5, sub_displacement_cuft=0.08,
            notes="Kevlar fiber reinforced paper cone with StampCast basket."
        ),
        "Punch P3D4-12 (600W RMS)": SubwooferModel(
            maker="Rockford Fosgate", model="Punch P3D4-12",
            nominal_dia_inch=12.0, fs=27.7, qts=0.49, qes=0.53, qms=6.7,
            vas_liters=57.7, xmax_mm=15.9, p_rms=600.0, sd_sq_cm=515.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.6, sub_displacement_cuft=0.11,
            notes="Anodized aluminum cone and dustcap with VAST surround."
        ),
        "Power T1D412 (800W RMS)": SubwooferModel(
            maker="Rockford Fosgate", model="Power T1D412",
            nominal_dia_inch=12.0, fs=31.5, qts=0.41, qes=0.45, qms=4.8,
            vas_liters=40.0, xmax_mm=16.4, p_rms=800.0, sd_sq_cm=515.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.7, sub_displacement_cuft=0.13,
            notes="Die cast aluminum frame with integrated heat sink fins."
        ),
        "Power T2S1-13 (2000W RMS)": SubwooferModel(
            maker="Rockford Fosgate", model="Power T2S1-13",
            nominal_dia_inch=13.0, fs=28.0, qts=0.37, qes=0.40, qms=4.9,
            vas_liters=52.0, xmax_mm=34.0, p_rms=2000.0, sd_sq_cm=680.0,
            sub_cutout_dia_in=12.2, sub_flush_dia_in=13.8, sub_displacement_cuft=0.23,
            notes="Flagship Power series high-excursion Neodymium motor."
        )
    },

    "Fi Car Audio": {
        "SSD-12 V4 (1000W RMS)": SubwooferModel(
            maker="Fi Car Audio", model="SSD-12 V4",
            nominal_dia_inch=12.0, fs=32.4, qts=0.37, qes=0.40, qms=4.7,
            vas_liters=35.0, xmax_mm=21.0, p_rms=1000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.5, sub_displacement_cuft=0.15,
            notes="Hand-crafted in Las Vegas, NV. Clean SQ/SPL hybrid."
        ),
        "Q-12 Neo (1750W RMS)": SubwooferModel(
            maker="Fi Car Audio", model="Q-12 Neo",
            nominal_dia_inch=12.0, fs=28.6, qts=0.35, qes=0.38, qms=4.9,
            vas_liters=42.0, xmax_mm=28.0, p_rms=1750.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.6, sub_displacement_cuft=0.18,
            notes="High BL Neodymium motor with ultra-flat inductance profile."
        ),
        "BTL-15 Series (2500W RMS)": SubwooferModel(
            maker="Fi Car Audio", model="BTL-15 Series",
            nominal_dia_inch=15.0, fs=31.0, qts=0.31, qes=0.33, qms=5.0,
            vas_liters=68.0, xmax_mm=33.0, p_rms=2500.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=13.875, sub_flush_dia_in=15.6, sub_displacement_cuft=0.25,
            notes="SPL competition hall-of-fame driver."
        )
    },

    "Deaf Bonce / Alphard": {
        "Apocalypse DB-SA252 D2 (1000W RMS)": SubwooferModel(
            maker="Deaf Bonce / Alphard", model="DB-SA252 D2",
            nominal_dia_inch=12.0, fs=33.2, qts=0.38, qes=0.41, qms=4.6,
            vas_liters=34.0, xmax_mm=18.0, p_rms=1000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.15,
            notes="Heavy ribbed surround and high-velocity forced cooling."
        ),
        "Apocalypse DB-SA272 D2 (1500W RMS)": SubwooferModel(
            maker="Deaf Bonce / Alphard", model="DB-SA272 D2",
            nominal_dia_inch=12.0, fs=32.0, qts=0.35, qes=0.38, qms=4.4,
            vas_liters=30.0, xmax_mm=20.0, p_rms=1500.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.2, sub_flush_dia_in=12.6, sub_displacement_cuft=0.19,
            notes="2.75-inch CCAW high-temp voice coil."
        ),
        "Apocalypse DB-SA302 D2 (2000W RMS)": SubwooferModel(
            maker="Deaf Bonce / Alphard", model="DB-SA302 D2",
            nominal_dia_inch=12.0, fs=32.5, qts=0.33, qes=0.35, qms=4.8,
            vas_liters=26.0, xmax_mm=22.0, p_rms=2000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.7, sub_displacement_cuft=0.23,
            notes="Massive 3-inch round wire coil."
        )
    },

    "RE Audio": {
        "RE Series 10\" (175W RMS)": SubwooferModel(
            maker="RE Audio", model="RE 10",
            nominal_dia_inch=10.0, fs=22.8, qts=0.38, qes=0.43, qms=4.1,
            vas_liters=62.2, xmax_mm=12.0, p_rms=175.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.125, sub_flush_dia_in=10.5, sub_displacement_cuft=0.07,
            notes="Original high-efficiency musical entry model."
        ),
        "RE Series 12\" (175W RMS)": SubwooferModel(
            maker="RE Audio", model="RE 12",
            nominal_dia_inch=12.0, fs=20.0, qts=0.39, qes=0.44, qms=4.3,
            vas_liters=138.0, xmax_mm=12.0, p_rms=175.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.0, sub_flush_dia_in=12.5, sub_displacement_cuft=0.09,
            notes="High compliance daily driver with warm low end."
        ),
        "SR Series 10\" D4 (300W RMS)": SubwooferModel(
            maker="RE Audio", model="SR 10 D4",
            nominal_dia_inch=10.0, fs=25.3, qts=0.38, qes=0.42, qms=4.4,
            vas_liters=45.6, xmax_mm=15.0, p_rms=300.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.125, sub_flush_dia_in=10.5, sub_displacement_cuft=0.08,
            notes="Dual voice coil daily driver."
        ),
        "SR Series 12\" D4 (300W RMS)": SubwooferModel(
            maker="RE Audio", model="SR 12 D4",
            nominal_dia_inch=12.0, fs=23.5, qts=0.41, qes=0.46, qms=4.5,
            vas_liters=95.4, xmax_mm=15.0, p_rms=300.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.0, sub_flush_dia_in=12.5, sub_displacement_cuft=0.11,
            notes="Excellent SQ performance in compact ported enclosures."
        ),
        "SRx 12\" D4 (450W RMS)": SubwooferModel(
            maker="RE Audio", model="SRx 12 D4",
            nominal_dia_inch=12.0, fs=24.1, qts=0.43, qes=0.48, qms=4.6,
            vas_liters=88.2, xmax_mm=18.0, p_rms=450.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.0, sub_flush_dia_in=12.5, sub_displacement_cuft=0.12,
            notes="Updated SR platform with higher thermal handling."
        ),
        "SE Series 10\" D4 (600W RMS)": SubwooferModel(
            maker="RE Audio", model="SE 10 D4",
            nominal_dia_inch=10.0, fs=26.5, qts=0.34, qes=0.37, qms=4.2,
            vas_liters=32.8, xmax_mm=18.0, p_rms=600.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.25, sub_flush_dia_in=10.5, sub_displacement_cuft=0.12,
            notes="Legendary daily ground-pounder with cast aluminum basket."
        ),
        "SE Series 12\" D4 (600W RMS)": SubwooferModel(
            maker="RE Audio", model="SE 12 D4",
            nominal_dia_inch=12.0, fs=25.1, qts=0.38, qes=0.42, qms=4.5,
            vas_liters=72.9, xmax_mm=18.0, p_rms=600.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.5, sub_displacement_cuft=0.14,
            notes="One of the most famous car audio street bass drivers ever produced."
        ),
        "SE Series 15\" D4 (600W RMS)": SubwooferModel(
            maker="RE Audio", model="SE 15 D4",
            nominal_dia_inch=15.0, fs=21.4, qts=0.39, qes=0.43, qms=4.8,
            vas_liters=168.0, xmax_mm=18.0, p_rms=600.0, sd_sq_cm=810.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.6, sub_displacement_cuft=0.17,
            notes="Massive acoustic cone radiating area for low tuned vented boxes."
        ),
        "SEX v2 12\" D4 (750W RMS)": SubwooferModel(
            maker="RE Audio", model="SEX v2 12 D4",
            nominal_dia_inch=12.0, fs=26.8, qts=0.42, qes=0.47, qms=4.8,
            vas_liters=59.0, xmax_mm=20.0, p_rms=750.0, sd_sq_cm=490.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.5, sub_displacement_cuft=0.15,
            notes="Upgraded SEX series with FEA-optimized motor and wrap-around gasket."
        ),
        "SX Series 12\" D2 (1000W RMS)": SubwooferModel(
            maker="RE Audio", model="SX 12 D2",
            nominal_dia_inch=12.0, fs=28.0, qts=0.31, qes=0.34, qms=4.4,
            vas_liters=45.0, xmax_mm=22.0, p_rms=1000.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.6, sub_displacement_cuft=0.17,
            notes="Heavy triple stack magnet with 3-inch 8-layer aluminum voice coil."
        ),
        "SX Series 15\" D2 (1000W RMS)": SubwooferModel(
            maker="RE Audio", model="SX 15 D2",
            nominal_dia_inch=15.0, fs=24.5, qts=0.33, qes=0.36, qms=4.7,
            vas_liters=112.0, xmax_mm=22.0, p_rms=1000.0, sd_sq_cm=810.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.7, sub_displacement_cuft=0.20,
            notes="High power handling SPL daily monster."
        ),
        "SXX v2 12\" D2 (1200W RMS)": SubwooferModel(
            maker="RE Audio", model="SXX v2 12 D2",
            nominal_dia_inch=12.0, fs=29.4, qts=0.35, qes=0.39, qms=4.5,
            vas_liters=39.5, xmax_mm=23.0, p_rms=1200.0, sd_sq_cm=490.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.6, sub_displacement_cuft=0.18,
            notes="High excursion motor platform for serious bassheads."
        ),
        "XXX Series 12\" (2000W RMS)": SubwooferModel(
            maker="RE Audio", model="XXX 12",
            nominal_dia_inch=12.0, fs=21.0, qts=0.32, qes=0.35, qms=4.1,
            vas_liters=64.0, xmax_mm=32.0, p_rms=2000.0, sd_sq_cm=480.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.8, sub_displacement_cuft=0.25,
            notes="Legendary XBL^2 linear motor technology with massive linear excursion."
        ),
        "XXX Series 15\" (2000W RMS)": SubwooferModel(
            maker="RE Audio", model="XXX 15",
            nominal_dia_inch=15.0, fs=18.5, qts=0.34, qes=0.37, qms=4.3,
            vas_liters=178.0, xmax_mm=32.0, p_rms=2000.0, sd_sq_cm=810.0,
            sub_cutout_dia_in=14.125, sub_flush_dia_in=15.8, sub_displacement_cuft=0.29,
            notes="Infamous XBL^2 sub-bass earthquake transducer."
        ),
        "XXX Series 18\" (2000W RMS)": SubwooferModel(
            maker="RE Audio", model="XXX 18",
            nominal_dia_inch=18.0, fs=16.8, qts=0.36, qes=0.39, qms=4.5,
            vas_liters=345.0, xmax_mm=32.0, p_rms=2000.0, sd_sq_cm=1210.0,
            sub_cutout_dia_in=16.75, sub_flush_dia_in=18.5, sub_displacement_cuft=0.35,
            notes="Giant 18-inch flagship with extreme low frequency authority."
        ),
        "MT Series 15\" (2500W+ SPL)": SubwooferModel(
            maker="RE Audio", model="MT 15",
            nominal_dia_inch=15.0, fs=34.0, qts=0.28, qes=0.30, qms=4.9,
            vas_liters=75.0, xmax_mm=26.0, p_rms=2500.0, sd_sq_cm=810.0,
            sub_cutout_dia_in=14.125, sub_flush_dia_in=15.8, sub_displacement_cuft=0.28,
            notes="Competition SPL burp legend used in world championship vehicles."
        )
    },

    "DC Audio": {
        "Level 2 12\" (600W RMS)": SubwooferModel(
            maker="DC Audio", model="Level 2 12",
            nominal_dia_inch=12.0, fs=32.4, qts=0.46, qes=0.51, qms=4.8,
            vas_liters=44.0, xmax_mm=16.0, p_rms=600.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.11,
            notes="Entry level daily ground pounder."
        ),
        "Level 3 12\" (900W RMS)": SubwooferModel(
            maker="DC Audio", model="Level 3 12",
            nominal_dia_inch=12.0, fs=31.1, qts=0.41, qes=0.45, qms=5.0,
            vas_liters=39.0, xmax_mm=18.5, p_rms=900.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.14,
            notes="Heavy duty 2.5-inch voice coil street daily driver."
        ),
        "Level 4 12\" (1400W RMS)": SubwooferModel(
            maker="DC Audio", model="Level 4 12",
            nominal_dia_inch=12.0, fs=32.0, qts=0.36, qes=0.39, qms=5.2,
            vas_liters=32.0, xmax_mm=23.5, p_rms=1400.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.6, sub_displacement_cuft=0.18,
            notes="3-inch 8-layer coil; high power daily demo king."
        ),
        "Level 4 15\" (1400W RMS)": SubwooferModel(
            maker="DC Audio", model="Level 4 15",
            nominal_dia_inch=15.0, fs=27.5, qts=0.38, qes=0.41, qms=5.4,
            vas_liters=88.0, xmax_mm=23.5, p_rms=1400.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=13.875, sub_flush_dia_in=15.6, sub_displacement_cuft=0.21,
            notes="Deep low bass authority in vented enclosures."
        ),
        "Level 5 12\" (2000W RMS)": SubwooferModel(
            maker="DC Audio", model="Level 5 12",
            nominal_dia_inch=12.0, fs=33.5, qts=0.32, qes=0.34, qms=5.3,
            vas_liters=25.0, xmax_mm=26.0, p_rms=2000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.2, sub_flush_dia_in=12.7, sub_displacement_cuft=0.23,
            notes="Competition SPL platform with double-stacked 10-inch spiders."
        ),
        "Level 6 15\" (3000W RMS)": SubwooferModel(
            maker="DC Audio", model="Level 6 15",
            nominal_dia_inch=15.0, fs=31.0, qts=0.29, qes=0.31, qms=5.5,
            vas_liters=62.0, xmax_mm=30.0, p_rms=3000.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.8, sub_displacement_cuft=0.30,
            notes="Flagship competition brute with 4-inch voice coil."
        )
    },

    "SoundQubed (Audioque)": {
        "HDS2.1 12\" (600W RMS)": SubwooferModel(
            maker="SoundQubed", model="HDS2.1 12",
            nominal_dia_inch=12.0, fs=35.1, qts=0.49, qes=0.54, qms=5.2,
            vas_liters=37.0, xmax_mm=14.0, p_rms=600.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.10,
            notes="High efficiency high-value daily driver."
        ),
        "HDS3.1 12\" (1200W RMS)": SubwooferModel(
            maker="SoundQubed", model="HDS3.1 12",
            nominal_dia_inch=12.0, fs=34.8, qts=0.41, qes=0.45, qms=4.8,
            vas_liters=28.5, xmax_mm=17.0, p_rms=1200.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.2, sub_flush_dia_in=12.6, sub_displacement_cuft=0.16,
            notes="Heavy cast basket with direct-connect 10AWG leads."
        ),
        "HDC3.1 12\" (1500W RMS)": SubwooferModel(
            maker="SoundQubed", model="HDC3.1 12",
            nominal_dia_inch=12.0, fs=36.0, qts=0.34, qes=0.37, qms=4.6,
            vas_liters=24.0, xmax_mm=21.0, p_rms=1500.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.7, sub_displacement_cuft=0.20,
            notes="Classic high-SPL motor platform based on DD lineage."
        ),
        "HDC4.1 15\" (2000W RMS)": SubwooferModel(
            maker="SoundQubed", model="HDC4.1 15",
            nominal_dia_inch=15.0, fs=32.0, qts=0.32, qes=0.35, qms=4.7,
            vas_liters=65.0, xmax_mm=25.0, p_rms=2000.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.8, sub_displacement_cuft=0.26,
            notes="4-inch flat-wound aluminum voice coil SPL titan."
        )
    },

    "Resilient Sounds": {
        "Gold 12\" (1000W RMS)": SubwooferModel(
            maker="Resilient Sounds", model="Gold 12",
            nominal_dia_inch=12.0, fs=32.5, qts=0.39, qes=0.43, qms=4.6,
            vas_liters=34.5, xmax_mm=20.0, p_rms=1000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.16,
            notes="3-inch 4-layer copper coil; great daily performance."
        ),
        "Platinum 12\" (2000W RMS)": SubwooferModel(
            maker="Resilient Sounds", model="Platinum 12",
            nominal_dia_inch=12.0, fs=31.8, qts=0.35, qes=0.38, qms=4.8,
            vas_liters=27.0, xmax_mm=28.0, p_rms=2000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.75, sub_displacement_cuft=0.22,
            notes="Massive motor structure and stitched high-roll surround."
        ),
        "Onyx 15\" (2500W RMS)": SubwooferModel(
            maker="Resilient Sounds", model="Onyx 15",
            nominal_dia_inch=15.0, fs=28.5, qts=0.33, qes=0.36, qms=4.9,
            vas_liters=72.0, xmax_mm=32.0, p_rms=2500.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.8, sub_displacement_cuft=0.27,
            notes="Ultra-high excursion platform engineered for heavy bass demoing."
        )
    },

    "Stereo Integrity": {
        "SQL-12 (1000W RMS)": SubwooferModel(
            maker="Stereo Integrity", model="SQL-12",
            nominal_dia_inch=12.0, fs=24.5, qts=0.38, qes=0.41, qms=5.4,
            vas_liters=55.0, xmax_mm=28.0, p_rms=1000.0, sd_sq_cm=505.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.5, sub_displacement_cuft=0.16,
            notes="Reference Sound Quality Level with enormous linear excursion."
        ),
        "SQL-15 (1000W RMS)": SubwooferModel(
            maker="Stereo Integrity", model="SQL-15",
            nominal_dia_inch=15.0, fs=19.8, qts=0.36, qes=0.39, qms=5.6,
            vas_liters=155.0, xmax_mm=28.0, p_rms=1000.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=13.875, sub_flush_dia_in=15.5, sub_displacement_cuft=0.20,
            notes="Audiophile-grade sub-20Hz linear transducer."
        ),
        "HT-18 V3 (750W RMS)": SubwooferModel(
            maker="Stereo Integrity", model="HT-18 V3",
            nominal_dia_inch=18.0, fs=17.2, qts=0.42, qes=0.46, qms=4.8,
            vas_liters=360.0, xmax_mm=22.0, p_rms=750.0, sd_sq_cm=1210.0,
            sub_cutout_dia_in=16.65, sub_flush_dia_in=18.4, sub_displacement_cuft=0.24,
            notes="High compliance home theater / car audio ultra-deep platform."
        )
    },

    "Incriminator Audio": {
        "I-Series 12\" (500W RMS)": SubwooferModel(
            maker="Incriminator Audio", model="I-Series 12",
            nominal_dia_inch=12.0, fs=31.2, qts=0.46, qes=0.51, qms=4.9,
            vas_liters=45.0, xmax_mm=15.0, p_rms=500.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.1, sub_flush_dia_in=12.5, sub_displacement_cuft=0.10,
            notes="Punchy and musical entry line."
        ),
        "Lethal Injection 12\" (1000W RMS)": SubwooferModel(
            maker="Incriminator Audio", model="Lethal Injection 12",
            nominal_dia_inch=12.0, fs=32.8, qts=0.39, qes=0.43, qms=4.7,
            vas_liters=35.0, xmax_mm=19.5, p_rms=1000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.15,
            notes="Versatile street daily subwoofer."
        ),
        "Death Row 12\" (1500W RMS)": SubwooferModel(
            maker="Incriminator Audio", model="Death Row 12",
            nominal_dia_inch=12.0, fs=33.5, qts=0.35, qes=0.38, qms=4.5,
            vas_liters=28.0, xmax_mm=24.0, p_rms=1500.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.2, sub_flush_dia_in=12.6, sub_displacement_cuft=0.19,
            notes="Competition proven street SPL design."
        ),
        "Death Penalty 15\" (2000W RMS)": SubwooferModel(
            maker="Incriminator Audio", model="Death Penalty 15",
            nominal_dia_inch=15.0, fs=30.0, qts=0.31, qes=0.34, qms=4.8,
            vas_liters=75.0, xmax_mm=28.0, p_rms=2000.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.7, sub_displacement_cuft=0.25,
            notes="Heavy triple stack magnet with multi-spider pack."
        ),
        "Warden 15\" (3500W+ SPL)": SubwooferModel(
            maker="Incriminator Audio", model="Warden 15",
            nominal_dia_inch=15.0, fs=34.0, qts=0.26, qes=0.28, qms=5.1,
            vas_liters=55.0, xmax_mm=33.0, p_rms=3500.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.125, sub_flush_dia_in=15.8, sub_displacement_cuft=0.32,
            notes="Legendary column-style Neodymium SPL burp motor."
        )
    },

    "B2 Audio": {
        "Rage 12 V2 (1200W RMS)": SubwooferModel(
            maker="B2 Audio", model="Rage 12 V2",
            nominal_dia_inch=12.0, fs=31.5, qts=0.37, qes=0.40, qms=4.6,
            vas_liters=36.0, xmax_mm=22.0, p_rms=1200.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.18, sub_flush_dia_in=12.6, sub_displacement_cuft=0.17,
            notes="Danish engineered street SPL platform."
        ),
        "Rage 15 V2 (1500W RMS)": SubwooferModel(
            maker="B2 Audio", model="Rage 15 V2",
            nominal_dia_inch=15.0, fs=27.0, qts=0.39, qes=0.42, qms=4.8,
            vas_liters=88.0, xmax_mm=22.0, p_rms=1500.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=13.9, sub_flush_dia_in=15.7, sub_displacement_cuft=0.22,
            notes="High power daily driver with tall foam surround."
        ),
        "Rampage 12 (2000W RMS)": SubwooferModel(
            maker="B2 Audio", model="Rampage 12",
            nominal_dia_inch=12.0, fs=32.0, qts=0.33, qes=0.35, qms=4.5,
            vas_liters=27.0, xmax_mm=27.0, p_rms=2000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.25, sub_flush_dia_in=12.75, sub_displacement_cuft=0.24,
            notes="High strength motor assembly designed for low tuning."
        )
    },

    "Alpine": {
        "Type R S-W12D4 (600W RMS)": SubwooferModel(
            maker="Alpine", model="S-W12D4 (Type-S)",
            nominal_dia_inch=12.0, fs=29.0, qts=0.48, qes=0.53, qms=5.5,
            vas_liters=55.0, xmax_mm=15.0, p_rms=600.0, sd_sq_cm=500.0,
            sub_cutout_dia_in=10.9, sub_flush_dia_in=12.4, sub_displacement_cuft=0.08,
            notes="HAMR surround technology for clean high-excursion daily bass."
        ),
        "Type R R2-W12D4 (750W RMS)": SubwooferModel(
            maker="Alpine", model="R2-W12D4 (Type-R)",
            nominal_dia_inch=12.0, fs=28.0, qts=0.43, qes=0.47, qms=5.2,
            vas_liters=48.0, xmax_mm=20.0, p_rms=750.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.0, sub_flush_dia_in=12.5, sub_displacement_cuft=0.10,
            notes="Kevlar reinforced pulp cone; staple daily performer."
        ),
        "Type X X-W12D4 (900W RMS)": SubwooferModel(
            maker="Alpine", model="X-W12D4 (Type-X)",
            nominal_dia_inch=12.0, fs=27.0, qts=0.39, qes=0.43, qms=5.0,
            vas_liters=50.0, xmax_mm=24.0, p_rms=900.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.1, sub_flush_dia_in=12.5, sub_displacement_cuft=0.14,
            notes="Audiophile SQ sound signature with high mechanical excursion."
        )
    },

    "Orion": {
        "Cobalt 12\" (400W RMS)": SubwooferModel(
            maker="Orion", model="Cobalt 12",
            nominal_dia_inch=12.0, fs=33.0, qts=0.58, qes=0.65, qms=5.5,
            vas_liters=52.0, xmax_mm=12.0, p_rms=400.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.0, sub_flush_dia_in=12.5, sub_displacement_cuft=0.08,
            notes="Classic American budget daily subwoofer."
        ),
        "XTR 12\" D2 (750W RMS)": SubwooferModel(
            maker="Orion", model="XTR 12 D2",
            nominal_dia_inch=12.0, fs=31.2, qts=0.44, qes=0.48, qms=5.1,
            vas_liters=42.0, xmax_mm=18.0, p_rms=750.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.13,
            notes="Street series with UV coated paper cone."
        ),
        "HCCA 12\" (2500W RMS)": SubwooferModel(
            maker="Orion", model="HCCA 12",
            nominal_dia_inch=12.0, fs=34.0, qts=0.34, qes=0.37, qms=4.8,
            vas_liters=21.0, xmax_mm=30.0, p_rms=2500.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.35, sub_flush_dia_in=13.0, sub_displacement_cuft=0.28,
            notes="Famous Red surround massive high-power competition SPL driver."
        ),
        "HCCA 15\" (2500W RMS)": SubwooferModel(
            maker="Orion", model="HCCA 15",
            nominal_dia_inch=15.0, fs=29.0, qts=0.36, qes=0.39, qms=5.0,
            vas_liters=58.0, xmax_mm=30.0, p_rms=2500.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.2, sub_flush_dia_in=16.0, sub_displacement_cuft=0.34,
            notes="Gigantic SPL ground shaker."
        )
    },

    "Image Dynamics": {
        "ID 10 V.4 D4 (300W RMS)": SubwooferModel(
            maker="Image Dynamics", model="ID 10 V.4",
            nominal_dia_inch=10.0, fs=26.8, qts=0.38, qes=0.42, qms=4.1,
            vas_liters=45.0, xmax_mm=15.0, p_rms=300.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.125, sub_flush_dia_in=10.5, sub_displacement_cuft=0.06,
            notes="Musical and articulate low power audiophile driver."
        ),
        "IDQ 12 V.4 D4 (750W RMS)": SubwooferModel(
            maker="Image Dynamics", model="IDQ 12 V.4",
            nominal_dia_inch=12.0, fs=25.0, qts=0.42, qes=0.46, qms=4.8,
            vas_liters=75.0, xmax_mm=19.0, p_rms=750.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.0, sub_flush_dia_in=12.5, sub_displacement_cuft=0.09,
            notes="One of the top-rated sound quality car audio subwoofers ever produced."
        ),
        "IDMAX 12 V.4 D2 (1000W RMS)": SubwooferModel(
            maker="Image Dynamics", model="IDMAX 12 V.4",
            nominal_dia_inch=12.0, fs=24.5, qts=0.36, qes=0.39, qms=4.5,
            vas_liters=82.0, xmax_mm=26.0, p_rms=1000.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.6, sub_displacement_cuft=0.15,
            notes="Legendary SQ/SPL heavyweight with removable top assembly."
        )
    },

    "Adire Audio": {
        "Koda 10\" (300W RMS)": SubwooferModel(
            maker="Adire Audio", model="Koda 10",
            nominal_dia_inch=10.0, fs=27.0, qts=0.44, qes=0.49, qms=4.2,
            vas_liters=38.0, xmax_mm=16.0, p_rms=300.0, sd_sq_cm=350.0,
            sub_cutout_dia_in=9.125, sub_flush_dia_in=10.5, sub_displacement_cuft=0.08,
            notes="Compact box SQ bass."
        ),
        "Brahma 12\" Rev 2.5 (1000W RMS)": SubwooferModel(
            maker="Adire Audio", model="Brahma 12 Rev 2.5",
            nominal_dia_inch=12.0, fs=26.0, qts=0.38, qes=0.41, qms=5.2,
            vas_liters=62.0, xmax_mm=28.0, p_rms=1000.0, sd_sq_cm=505.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.6, sub_displacement_cuft=0.17,
            notes="Pioneered XBL^2 split-gap motor geometry for near-zero distortion high excursion."
        ),
        "Tumult 15\" (1500W RMS)": SubwooferModel(
            maker="Adire Audio", model="Tumult 15",
            nominal_dia_inch=15.0, fs=19.5, qts=0.34, qes=0.37, qms=5.4,
            vas_liters=185.0, xmax_mm=34.0, p_rms=1500.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.8, sub_displacement_cuft=0.28,
            notes="Sub-bass reference standard displacement machine."
        )
    },

    "Sound Solutions Audio (SSA)": {
        "Dcon 12\" (400W RMS)": SubwooferModel(
            maker="Sound Solutions Audio", model="Dcon 12",
            nominal_dia_inch=12.0, fs=28.0, qts=0.45, qes=0.49, qms=4.8,
            vas_liters=58.0, xmax_mm=14.0, p_rms=400.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.125, sub_flush_dia_in=12.5, sub_displacement_cuft=0.09,
            notes="High efficiency low wattage sound quality driver."
        ),
        "Gcon 12\" (950W RMS)": SubwooferModel(
            maker="Sound Solutions Audio", model="Gcon 12",
            nominal_dia_inch=12.0, fs=29.2, qts=0.39, qes=0.43, qms=4.6,
            vas_liters=45.0, xmax_mm=20.0, p_rms=950.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.5, sub_displacement_cuft=0.14,
            notes="Musical street daily ground-pounder."
        ),
        "Icon 12\" (1250W RMS)": SubwooferModel(
            maker="Sound Solutions Audio", model="Icon 12",
            nominal_dia_inch=12.0, fs=27.5, qts=0.37, qes=0.40, qms=4.9,
            vas_liters=48.0, xmax_mm=22.0, p_rms=1250.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.15, sub_flush_dia_in=12.6, sub_displacement_cuft=0.17,
            notes="Audiophile SQ with deep low-end daily punch."
        ),
        "Xcon 12\" (1750W RMS)": SubwooferModel(
            maker="Sound Solutions Audio", model="Xcon 12",
            nominal_dia_inch=12.0, fs=30.5, qts=0.33, qes=0.36, qms=5.0,
            vas_liters=34.0, xmax_mm=28.0, p_rms=1750.0, sd_sq_cm=510.0,
            sub_cutout_dia_in=11.2, sub_flush_dia_in=12.7, sub_displacement_cuft=0.22,
            notes="Competition SQL flagship with 3-inch 8-layer flat-wire coil."
        ),
        "Zcon 15\" (2500W RMS)": SubwooferModel(
            maker="Sound Solutions Audio", model="Zcon 15",
            nominal_dia_inch=15.0, fs=29.0, qts=0.31, qes=0.33, qms=5.2,
            vas_liters=75.0, xmax_mm=31.0, p_rms=2500.0, sd_sq_cm=820.0,
            sub_cutout_dia_in=14.0, sub_flush_dia_in=15.8, sub_displacement_cuft=0.29,
            notes="Extreme output ground pounder designed for high thermal abuse."
        )
    }
}


def get_all_manufacturers() -> List[str]:
    """Return sorted list of all available subwoofer manufacturers."""
    return sorted(list(SUBWOOFER_DB))


def extract_series_name(model_name: str) -> str:
    """
    Extract a logical series name from a full model string.
    E.g.:
      'XXX Series 12" (2000W RMS)' -> 'XXX Series'
      'SA-12 V.2 D2 (750W RMS)' -> 'SA Series'
      'CompR 12" D2 (500W RMS)' -> 'CompR Series'
      'Level 4 15" (1400W RMS)' -> 'Level 4 Series'
      '12W7AE-3 (1000W RMS)' -> 'W7 Series'
    """
    cleaned = model_name.strip()
    # Check common standard tokens
    for token in ["Series", "Level", "Apocalypse", "Type R", "Type X", "Comp", "Redline", "Power", "Punch"]:
        if token.lower() in cleaned.lower():
            pass

    # Specific clean mappings
    if "XXX" in cleaned:
        return "XXX Series"
    if "SX" in cleaned or "SXX" in cleaned:
        return "SX / SXX Series"
    if "SE" in cleaned or "SEX" in cleaned:
        return "SE / SEX Series"
    if "SR" in cleaned:
        return "SR / SRx Series"
    if cleaned.startswith("RE "):
        return "RE Series"
    if "MT" in cleaned:
        return "MT Competition Series"
    if "SA-" in cleaned:
        return "SA Series"
    if "U-" in cleaned:
        return "U Series"
    if "X-" in cleaned:
        return "X Series"
    if "ZV" in cleaned:
        return "ZV Series"
    if "W7" in cleaned:
        return "W7 Series"
    if "W6" in cleaned:
        return "W6 Series"
    if "W3" in cleaned:
        return "W3 Series"
    if "Level 2" in cleaned:
        return "Level 2 Series"
    if "Level 3" in cleaned:
        return "Level 3 Series"
    if "Level 4" in cleaned:
        return "Level 4 Series"
    if "Level 5" in cleaned:
        return "Level 5 Series"
    if "Level 6" in cleaned:
        return "Level 6 Series"
    if "HDS" in cleaned:
        return "HDS Series"
    if "HDC" in cleaned:
        return "HDC Series"
    if "EVL" in cleaned:
        return "EVL Series"
    if "SDR" in cleaned:
        return "SDR Series"
    if "VXF" in cleaned:
        return "VXF Series"
    if "RSS" in cleaned:
        return "Reference (RSS) Series"
    if "Ultimax" in cleaned:
        return "Ultimax Series"
    if "Solo-Baric" in cleaned:
        return "Solo-Baric L7 Series"
    if "Comp" in cleaned:
        return "Comp Series"
    if "SQL" in cleaned:
        return "SQL Series"
    if "HT-18" in cleaned:
        return "HT Series"
    if "IDMAX" in cleaned:
        return "IDMAX Series"
    if "IDQ" in cleaned:
        return "IDQ Series"
    if "ID " in cleaned:
        return "ID Series"
    if "Brahma" in cleaned:
        return "Brahma Series"
    if "Tumult" in cleaned:
        return "Tumult Series"
    if "HCCA" in cleaned:
        return "HCCA Series"
    if "XTR" in cleaned:
        return "XTR Series"
    if "Apocalypse" in cleaned:
        return "Apocalypse Series"
    if "Punch" in cleaned:
        return "Punch Series"
    if "Power" in cleaned:
        return "Power Series"

    # Default fallback: take the first word or words before size
    parts = cleaned.split()
    if len(parts) >= 2 and parts[1].lower() in ["series", "v2", "v3", "v4"]:
        return f"{parts[0]} {parts[1]}"
    return f"{parts[0]} Line"


def get_series_for_manufacturer(maker: str) -> List[str]:
    """Return sorted list of model lines/series for a given manufacturer."""
    if maker not in SUBWOOFER_DB:
        return []
    series_set = set()
    for model_name in SUBWOOFER_DB[maker]:
        series_set.add(extract_series_name(model_name))
    return sorted(list(series_set))


def get_models_for_maker_and_series(maker: str, series: str) -> List[str]:
    """Return models belonging to a specific maker and series."""
    if maker not in SUBWOOFER_DB:
        return []
    matched = []
    for model_name in SUBWOOFER_DB[maker]:
        if series == "All Series" or extract_series_name(model_name) == series:
            matched.append(model_name)
    return sorted(matched)


def get_models_for_manufacturer(maker: str) -> List[str]:
    """Return list of models available for a specific maker."""
    if maker in SUBWOOFER_DB:
        return list(SUBWOOFER_DB[maker])
    return []


def get_subwoofer(maker: str, model: str) -> Optional[SubwooferModel]:
    """Retrieve full SubwooferModel specification."""
    if maker in SUBWOOFER_DB and model in SUBWOOFER_DB[maker]:
        return SUBWOOFER_DB[maker][model]
    return None


def search_all_subwoofers(query: str) -> List[Tuple[str, str, SubwooferModel]]:
    """
    Case-insensitive search across all manufacturers, models, and notes.
    Returns list of (maker, model_name, SubwooferModel).
    """
    q = query.strip().lower()
    if not q:
        return []
    results = []
    for maker, models in SUBWOOFER_DB.items():
        for model_name, sub in models.items():
            searchable_text = f"{maker} {model_name} {sub.notes}".lower()
            if q in searchable_text:
                results.append((maker, model_name, sub))
    return results


def add_custom_subwoofer(sub: SubwooferModel) -> None:
    """Dynamically register a new custom subwoofer into the runtime database."""
    if sub.maker not in SUBWOOFER_DB:
        SUBWOOFER_DB[sub.maker] = {}
    SUBWOOFER_DB[sub.maker][sub.model] = sub

import json
import os

CUSTOM_DB_PATH = "custom_subs.json"

def load_custom_subwoofers() -> int:
    """Loads user-persisted subwoofers from custom_subs.json."""
    if not os.path.exists(CUSTOM_DB_PATH):
        return 0
    try:
        with open(CUSTOM_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        for maker, models in data.items():
            if maker not in SUBWOOFER_DB:
                SUBWOOFER_DB[maker] = {}
            for m_name, d in models.items():
                SUBWOOFER_DB[maker][m_name] = SubwooferModel(**d)
                count += 1
        return count
    except Exception as e:
        print(f"Notice: Failed to load custom subwoofers: {e}")
        return 0

def save_custom_subwoofer_to_file(sub: SubwooferModel) -> bool:
    """Persists a new custom subwoofer to custom_subs.json and updates runtime database."""
    add_custom_subwoofer(sub)
    try:
        data = {}
        if os.path.exists(CUSTOM_DB_PATH):
            with open(CUSTOM_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        if sub.maker not in data:
            data[sub.maker] = {}
        data[sub.maker][sub.model] = asdict(sub)
        
        with open(CUSTOM_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving custom subwoofer: {e}")
        return False

# Initialize on import
load_custom_subwoofers()
