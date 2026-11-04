"""
RuneBox // Subwoofer Enclosure Lab
geometry.py - 3D Box Shapes, Spatial Constraint Back-Solvers,
Displacement Deductions, and Fabrication Cut Sheet Generation.
"""

import math
import csv
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class CutPanel:
    """Represents an individual fabricated MDF/Birch panel cut."""
    name: str
    qty: int
    width_in: float
    height_in: float
    thickness_in: float
    bevel_angle_deg: float = 0.0
    notes: str = "Square 90 deg cuts"


@dataclass
class EnclosureGeometry:
    """
    Geometric configuration of the subwoofer enclosure.
    """
    shape: str = "cuboid"  # 'cuboid', 'single_wedge', 'double_wedge'
    
    # Exterior dimensions (inches)
    ext_width: float = 32.0
    ext_height: float = 14.0
    ext_depth_bottom: float = 16.0
    ext_depth_top: float = 16.0  # Same as bottom for cuboid
    
    # Material Thickness (inches)
    wall_thickness: float = 0.75
    baffle_thickness: float = 0.75  # Or 1.5 for double baffle
    
    # Subwoofer details
    sub_cutout_dia_in: float = 11.125
    sub_flush_dia_in: float = 12.5
    sub_flush_depth_in: float = 0.75
    sub_displacement_cuft: float = 0.14
    num_subwoofers: int = 1
    
    # Bracing and misc deductions
    bracing_displacement_cuft: float = 0.05
    
    # Enclosure acoustic topology
    enclosure_type: str = "ported"  # 'sealed', 'ported', '4th_bandpass', '6th_bandpass'

    # Port specification
    port_type: str = "slot"  # 'slot', 'round', or 'none'
    port_width_in: float = 2.5
    port_height_in: float = 12.5
    port_dia_in: float = 4.0
    num_ports: int = 1
    port_physical_length_in: float = 24.0
    is_l_port: bool = True
    port_wall_thickness: float = 0.75
    
    # Multi-Chamber Isolation
    is_chamber_isolated: bool = False

    # Subwoofer Inverted ("Ass-Out") Mounting
    is_inverted_sub: bool = False

    @property
    def effective_sub_displacement_cuft(self) -> float:
        """
        Calculates the effective driver displacement accounting for standard vs inverted mounting.
        Physical Principle: Inverted ('ass-out') subwoofers place the motor outside the enclosure,
        meaning their basket and motor do not consume internal gross volume.
        """
        if self.is_inverted_sub:
            return 0.0
        return self.sub_displacement_cuft * self.num_subwoofers

    @property
    def seat_recline_angle_deg(self) -> float:
        """
        Calculate the front/back baffle recline angle in degrees for wedge boxes.
        """
        if self.shape == "cuboid":
            return 0.0
        delta_d = abs(self.ext_depth_bottom - self.ext_depth_top)
        if delta_d <= 0.001 or self.ext_height <= 0:
            return 0.0
        if self.shape == "single_wedge":
            # One vertical wall, one angled wall
            angle_rad = math.atan(delta_d / self.ext_height)
            return round(math.degrees(angle_rad), 1)
        elif self.shape == "double_wedge":
            # Both front and rear walls slope symmetrically
            half_delta = delta_d / 2.0
            angle_rad = math.atan(half_delta / self.ext_height)
            return round(math.degrees(angle_rad), 1)
        return 0.0

    def calculate_exterior_gross_volume_cuft(self) -> float:
        """Calculates total exterior boundary volume in cu.ft."""
        avg_depth = (self.ext_depth_bottom + self.ext_depth_top) / 2.0
        vol_cu_in = self.ext_width * self.ext_height * avg_depth
        return vol_cu_in / 1728.0

    def calculate_internal_gross_volume_cuft(self) -> float:
        """
        Calculates raw internal gross cavity volume inside the walls (before woofer/port deductions).
        """
        int_w = max(0.0, self.ext_width - (2.0 * self.wall_thickness))
        int_h = max(0.0, self.ext_height - (2.0 * self.wall_thickness))
        
        # Front baffle vs rear wall thickness
        front_t = self.baffle_thickness
        rear_t = self.wall_thickness
        total_depth_deduction = front_t + rear_t
        
        int_depth_bottom = max(0.0, self.ext_depth_bottom - total_depth_deduction)
        int_depth_top = max(0.0, self.ext_depth_top - total_depth_deduction)
        
        avg_int_depth = (int_depth_bottom + int_depth_top) / 2.0
        int_vol_cu_in = int_w * int_h * avg_int_depth
        return int_vol_cu_in / 1728.0

    def calculate_port_displacement_cuft(self) -> float:
        """
        Calculates physical volume consumed by port walls and internal air column inside box.
        """
        if self.enclosure_type == "sealed" or self.port_type == "none" or self.port_physical_length_in <= 0:
            return 0.0
            
        if self.port_type == "round":
            # Outer diameter of PVC/aeroport (typically pipe wall is ~0.25")
            r_outer = (self.port_dia_in / 2.0) + 0.22
            vol_cu_in = math.pi * (r_outer ** 2) * self.port_physical_length_in * self.num_ports
            return vol_cu_in / 1728.0
        else:
            # Slot port: consumes the port's internal duct volume + the MDF divider wood volume
            # Outer boundary footprint of the port channel inside the enclosure
            outer_w = self.port_width_in + self.port_wall_thickness
            outer_h = self.port_height_in  # often spans full internal height
            vol_cu_in = outer_w * outer_h * self.port_physical_length_in * self.num_ports
            return vol_cu_in / 1728.0

    def calculate_divider_displacement_cuft(self) -> float:
        """
        Calculates physical volume consumed by internal partition divider walls
        when isolated multi-chambers are selected.
        Each divider wall spans from front baffle to rear wall, and top to bottom.
        Number of dividers = num_subwoofers - 1 (for num_subwoofers > 1).
        """
        if not self.is_chamber_isolated or self.num_subwoofers <= 1:
            return 0.0
        num_dividers = self.num_subwoofers - 1
        int_h = max(0.0, self.ext_height - (2.0 * self.wall_thickness))
        total_depth_deduction = self.baffle_thickness + self.wall_thickness
        avg_int_d = max(0.0, ((self.ext_depth_bottom + self.ext_depth_top) / 2.0) - total_depth_deduction)
        vol_cu_in = num_dividers * self.wall_thickness * int_h * avg_int_d
        return vol_cu_in / 1728.0

    def calculate_net_internal_volume_cuft(self) -> float:
        """
        Calculates actual Net acoustic internal working volume:
        Net Vb = Internal Gross - Driver Displacements - Port Displacements - Bracing Displacements - Divider Displacements.
        When mounted inverted ('ass-out'), subwoofer motor is outside the box, adding the cone volume (sub_disp is 0.0 or added).
        """
        gross = self.calculate_internal_gross_volume_cuft()
        sub_disp = self.effective_sub_displacement_cuft
        port_disp = self.calculate_port_displacement_cuft()
        divider_disp = self.calculate_divider_displacement_cuft()
        net = gross - sub_disp - port_disp - self.bracing_displacement_cuft - divider_disp
        return max(0.01, round(net, 3))

    def solve_depth_for_target_net_volume(
        self,
        target_net_cuft: float,
        locked_height_in: Optional[float] = None,
        locked_width_in: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Spatial Constraint Engine:
        Given locked trunk height and locked trunk width, iteratively or algebraically
        back-solves for required exterior bottom depth (and top depth) to satisfy target Net Vb.
        """
        if locked_height_in is not None:
            self.ext_height = locked_height_in
        if locked_width_in is not None:
            self.ext_width = locked_width_in

        # Target gross needed = Net target + sub_disp + port_disp + bracing + divider_disp
        sub_disp = self.effective_sub_displacement_cuft
        port_disp = self.calculate_port_displacement_cuft()
        divider_disp = self.calculate_divider_displacement_cuft()
        target_gross_cuft = target_net_cuft + sub_disp + port_disp + self.bracing_displacement_cuft + divider_disp
        target_gross_cu_in = target_gross_cuft * 1728.0

        int_w = max(0.5, self.ext_width - (2.0 * self.wall_thickness))
        int_h = max(0.5, self.ext_height - (2.0 * self.wall_thickness))
        total_depth_deduction = self.baffle_thickness + self.wall_thickness

        # Required average internal depth
        req_avg_int_depth = target_gross_cu_in / (int_w * int_h)
        req_avg_ext_depth = req_avg_int_depth + total_depth_deduction

        if self.shape == "cuboid":
            self.ext_depth_bottom = round(req_avg_ext_depth, 2)
            self.ext_depth_top = round(req_avg_ext_depth, 2)
        else:
            # Maintain wedge depth delta or default recline ratio
            delta = max(0.0, self.ext_depth_bottom - self.ext_depth_top)
            if delta < 0.5:
                delta = 4.0  # default 4-inch wedge taper if uninitialized
            self.ext_depth_bottom = round(req_avg_ext_depth + (delta / 2.0), 2)
            self.ext_depth_top = round(max(self.wall_thickness * 2.5, req_avg_ext_depth - (delta / 2.0)), 2)

        return self.ext_depth_bottom, self.ext_depth_top

    def generate_cut_sheet(self) -> List[CutPanel]:
        """
        Generates fabrication cut list with exact panel dimensions and miter angles.
        """
        t = self.wall_thickness
        bt = self.baffle_thickness
        is_double_baffle = (bt > t + 0.1)
        angle = self.seat_recline_angle_deg
        bevel_str = f"{angle:.1f} deg miter / bevel on top & bottom edges" if angle > 0 else "Square 90 deg"

        cuts: List[CutPanel] = []

        if self.shape == "cuboid":
            # Top & Bottom panels
            cuts.append(CutPanel(
                name="Top Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(self.ext_depth_bottom, 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes="Flat square cut"
            ))
            cuts.append(CutPanel(
                name="Bottom Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(self.ext_depth_bottom, 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes="Flat square cut"
            ))

            # Left & Right side panels (seated inside top/bottom)
            side_h = max(0.0, self.ext_height - 2.0 * t)
            cuts.append(CutPanel(
                name="Side Panels (Left & Right)",
                qty=2,
                width_in=round(self.ext_depth_bottom - (bt + t), 2),
                height_in=round(side_h, 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes="Internal fit between baffle, back, top, bottom"
            ))

            # Rear Back Panel
            cuts.append(CutPanel(
                name="Rear Back Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(side_h, 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes="Flush perimeter fit"
            ))

            # Front Subwoofer Baffle
            sub_note = f"Cutout Dia: {self.sub_cutout_dia_in} in."
            if self.sub_flush_dia_in > self.sub_cutout_dia_in:
                sub_note += f" Recess flush ring: {self.sub_flush_dia_in} in (depth: {self.sub_flush_depth_in} in)"

            baffle_qty = 2 if is_double_baffle else 1
            cuts.append(CutPanel(
                name="Front Subwoofer Baffle" + (" (Double Thick)" if is_double_baffle else ""),
                qty=baffle_qty,
                width_in=round(self.ext_width, 2),
                height_in=round(side_h, 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes=sub_note
            ))

        elif self.shape == "single_wedge":
            # Top & Bottom have different depths
            cuts.append(CutPanel(
                name="Top Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(self.ext_depth_top, 2),
                thickness_in=t,
                bevel_angle_deg=angle,
                notes=f"Back edge beveled at {angle:.1f} deg"
            ))
            cuts.append(CutPanel(
                name="Bottom Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(self.ext_depth_bottom, 2),
                thickness_in=t,
                bevel_angle_deg=angle,
                notes=f"Back edge beveled at {angle:.1f} deg"
            ))

            # Angled Rear Panel: hypotenuse along the recline
            delta_d = abs(self.ext_depth_bottom - self.ext_depth_top)
            rear_length = math.sqrt((self.ext_height ** 2) + (delta_d ** 2))
            cuts.append(CutPanel(
                name="Angled Rear Panel (Seatback Recline)",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(rear_length, 2),
                thickness_in=t,
                bevel_angle_deg=angle,
                notes=f"Angled face matching recline. Bevel both long edges at {angle:.1f} deg"
            ))

            # Vertical Front Baffle
            sub_note = f"Cutout Dia: {self.sub_cutout_dia_in} in."
            if self.sub_flush_dia_in > self.sub_cutout_dia_in:
                sub_note += f" Recess: {self.sub_flush_dia_in} in."
            side_h = max(0.0, self.ext_height - 2.0 * t)
            baffle_qty = 2 if is_double_baffle else 1
            cuts.append(CutPanel(
                name="Front Baffle (Vertical)" + (" (Double Thick)" if is_double_baffle else ""),
                qty=baffle_qty,
                width_in=round(self.ext_width, 2),
                height_in=round(side_h, 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes=sub_note
            ))

            # Left & Right Trapezoidal Endplates
            cuts.append(CutPanel(
                name="Trapezoid Side Endplates (L & R)",
                qty=2,
                width_in=round(self.ext_depth_bottom - (bt + t), 2),
                height_in=round(side_h, 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes=f"Cut trapezoid: Top Depth={self.ext_depth_top - (bt + t):.2f} in, Bottom Depth={self.ext_depth_bottom - (bt + t):.2f} in."
            ))

        else:  # double_wedge
            cuts.append(CutPanel(
                name="Top Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(self.ext_depth_top, 2),
                thickness_in=t,
                bevel_angle_deg=angle,
                notes=f"Dual bevel {angle:.1f} deg front and back"
            ))
            cuts.append(CutPanel(
                name="Bottom Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(self.ext_depth_bottom, 2),
                thickness_in=t,
                bevel_angle_deg=angle,
                notes=f"Dual bevel {angle:.1f} deg front and back"
            ))
            half_delta = abs(self.ext_depth_bottom - self.ext_depth_top) / 2.0
            face_length = math.sqrt((self.ext_height ** 2) + (half_delta ** 2))
            cuts.append(CutPanel(
                name="Angled Front Baffle",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(face_length, 2),
                thickness_in=bt,
                bevel_angle_deg=angle,
                notes=f"Beveled top/bottom at {angle:.1f} deg. Sub cutout {self.sub_cutout_dia_in} in."
            ))
            cuts.append(CutPanel(
                name="Angled Rear Panel",
                qty=1,
                width_in=round(self.ext_width, 2),
                height_in=round(face_length, 2),
                thickness_in=t,
                bevel_angle_deg=angle,
                notes=f"Beveled top/bottom at {angle:.1f} deg."
            ))
            cuts.append(CutPanel(
                name="Dual-Symmetric Trapezoid Sides",
                qty=2,
                width_in=round(self.ext_depth_bottom - (2.0 * t), 2),
                height_in=round(max(0.0, self.ext_height - 2.0 * t), 2),
                thickness_in=t,
                bevel_angle_deg=0.0,
                notes=f"Trapezoid: Top={self.ext_depth_top - (2.0 * t):.2f} in, Bottom={self.ext_depth_bottom - (2.0 * t):.2f} in."
            ))

        # Internal Slot Port Panels if applicable (only if not sealed and port_type is slot)
        if self.enclosure_type != "sealed" and self.port_type == "slot" and self.port_physical_length_in > 0:
            port_h = max(0.5, self.ext_height - (2.0 * t))
            if self.is_l_port and self.port_physical_length_in > (self.ext_depth_bottom - 2.0 * t):
                # Split into Primary Entrance Run and L-Bend Corner Extension
                run1_len = max(1.0, (self.ext_depth_bottom - (bt + t)) - self.port_width_in)
                run2_len = max(1.0, self.port_physical_length_in - run1_len)
                cuts.append(CutPanel(
                    name="Slot Port Primary Wall (Run 1)",
                    qty=1,
                    width_in=round(run1_len, 2),
                    height_in=round(port_h, 2),
                    thickness_in=self.port_wall_thickness,
                    bevel_angle_deg=0.0,
                    notes="Main longitudinal port partition wall"
                ))
                cuts.append(CutPanel(
                    name="Slot Port L-Bend Extension (Run 2)",
                    qty=1,
                    width_in=round(run2_len, 2),
                    height_in=round(port_h, 2),
                    thickness_in=self.port_wall_thickness,
                    bevel_angle_deg=0.0,
                    notes="90-deg corner turn inner wall"
                ))
            else:
                cuts.append(CutPanel(
                    name="Straight Slot Port Divider Wall",
                    qty=1,
                    width_in=round(self.port_physical_length_in, 2),
                    height_in=round(port_h, 2),
                    thickness_in=self.port_wall_thickness,
                    bevel_angle_deg=0.0,
                    notes="Single straight internal slot partition"
                ))

        # L-Port 90-degree Corner 45-degree Airflow Deflector (when port wraps around rear wall)
        if self.enclosure_type != "sealed" and self.port_type == "slot" and self.is_l_port and self.port_physical_length_in > (self.ext_depth_bottom - 2.0 * t):
            corner_deflector_w = round(self.port_width_in * 1.414, 2)  # hypotenuse of port corner
            cuts.append(CutPanel(
                name="L-Port 45-deg Airflow Corner Deflector",
                qty=1,
                width_in=corner_deflector_w,
                height_in=round(max(0.5, self.ext_height - 2.0 * t), 2),
                thickness_in=self.port_wall_thickness,
                bevel_angle_deg=45.0,
                notes="45-deg miter at L-bend corner to eliminate vortex chuffing & maintain constant port area"
            ))

        # Corner 45-degree kerf/brace strips (competition standard for clean airflow)
        cuts.append(CutPanel(
            name="Internal 45-deg Corner Kerf / Bracing Cleats",
            qty=4,
            width_in=round(1.5, 2),
            height_in=round(max(0.5, self.ext_height - 2.0 * t), 2),
            thickness_in=t,
            bevel_angle_deg=45.0,
            notes="45-deg internal corner smoothers to reduce turbulence & stiffen joints"
        ))

        # Multi-chamber isolated partition dividers
        if self.is_chamber_isolated and self.num_subwoofers > 1:
            div_qty = self.num_subwoofers - 1
            side_h = max(0.0, self.ext_height - 2.0 * t)
            if self.shape == "cuboid":
                div_w = round(self.ext_depth_bottom - (bt + t), 2)
                cuts.append(CutPanel(
                    name="Chamber Partition Divider Wall",
                    qty=div_qty,
                    width_in=div_w,
                    height_in=round(side_h, 2),
                    thickness_in=t,
                    bevel_angle_deg=0.0,
                    notes=f"Internal isolation wall creating {self.num_subwoofers} separate sealed/ported sub-cavities"
                ))
            elif self.shape == "single_wedge":
                div_w = round(self.ext_depth_bottom - (bt + t), 2)
                cuts.append(CutPanel(
                    name="Chamber Partition Divider Wall (Trapezoid)",
                    qty=div_qty,
                    width_in=div_w,
                    height_in=round(side_h, 2),
                    thickness_in=t,
                    bevel_angle_deg=0.0,
                    notes=f"Internal isolation trapezoid: Top={self.ext_depth_top - (bt + t):.2f} in, Bottom={div_w:.2f} in"
                ))
            else:  # double_wedge
                div_w = round(self.ext_depth_bottom - (2.0 * t), 2)
                cuts.append(CutPanel(
                    name="Chamber Partition Divider Wall (Dual-Angle)",
                    qty=div_qty,
                    width_in=div_w,
                    height_in=round(side_h, 2),
                    thickness_in=t,
                    bevel_angle_deg=0.0,
                    notes=f"Internal isolation dual-trapezoid: Top={self.ext_depth_top - (2.0 * t):.2f} in, Bottom={div_w:.2f} in"
                ))

        return cuts

    def export_cut_sheet_csv(self, filepath: str) -> None:
        """Export cut list to CSV file."""
        panels = self.generate_cut_sheet()
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Panel Name", "Quantity", "Width (in)", "Height/Length (in)", "Thickness (in)", "Bevel / Miter Angle (deg)", "Special Cut Instructions"])
            for p in panels:
                writer.writerow([p.name, p.qty, p.width_in, p.height_in, p.thickness_in, f"{p.bevel_angle_deg:.1f}", p.notes])

    def export_cut_sheet_txt(self, filepath: str) -> None:
        """Export a comprehensive professional build sheet to TXT."""
        panels = self.generate_cut_sheet()
        ext_gross = self.calculate_exterior_gross_volume_cuft()
        int_gross = self.calculate_internal_gross_volume_cuft()
        net_vb = self.calculate_net_internal_volume_cuft()
        port_disp = self.calculate_port_displacement_cuft()
        sub_disp = self.effective_sub_displacement_cuft
        divider_disp = self.calculate_divider_displacement_cuft()

        lines = [
            "=" * 75,
            "  RUNEBOX // SUBWOOFER ENCLOSURE LAB - PROFESSIONAL FABRICATION SHEET",
            "  Engineered by NfgOdin",
            "=" * 75,
            "",
            "[ ENCLOSURE SPECIFICATIONS & VOLUMETRICS ]",
            f"  Shape Profile:            {self.shape.upper()}",
            f"  Chamber Configuration:    {'Isolated Multi-Chamber' if self.is_chamber_isolated and self.num_subwoofers > 1 else 'Shared Common Chamber'}",
            f"  Exterior Dimensions:      {self.ext_width:.2f} in. W x {self.ext_height:.2f} in. H x (Top: {self.ext_depth_top:.2f} in., Bottom: {self.ext_depth_bottom:.2f} in.) D",
            f"  Exterior Footprint Gross: {ext_gross:.3f} cu.ft",
            f"  Raw Internal Gross:       {int_gross:.3f} cu.ft",
            f"  Subwoofer Displacement:   {sub_disp:.3f} cu.ft ({self.num_subwoofers}x subwoofers)",
            f"  Port Displacement:        {port_disp:.3f} cu.ft",
            f"  Divider Displacement:     {divider_disp:.3f} cu.ft",
            f"  Bracing Displacement:     {self.bracing_displacement_cuft:.3f} cu.ft",
            f"  NET INTERNAL VOLUME (Vb): {net_vb:.3f} cu.ft ({net_vb * 28.3168:.2f} Liters)",
            f"  Seat Recline / Miter:     {self.seat_recline_angle_deg:.1f} degrees",
            "",
            "[ MATERIAL SPECIFICATIONS ]",
            f"  Main Wall Material:       {self.wall_thickness:.3f} in. MDF / Birch",
            f"  Front Baffle Material:    {self.baffle_thickness:.3f} in. MDF / Birch" + (" (Double Baffle)" if self.baffle_thickness > 1.0 else ""),
            f"  Sub Cutout Diameter:      {self.sub_cutout_dia_in:.3f} in.",
            f"  Sub Flush Outer Diameter: {self.sub_flush_dia_in:.3f} in. (Flush Depth: {self.sub_flush_depth_in:.3f} in.)",
            "",
            "[ TABLE SAW & CNC CUT LIST ]",
            f"{'Panel Name':<38} | {'Qty':<3} | {'Width':<8} | {'Height':<8} | {'Thick':<6} | {'Bevel':<8} | {'Notes'}",
            "-" * 105
        ]

        for p in panels:
            lines.append(f"{p.name:<38} | {p.qty:<3} | {p.width_in:>6.2f} in | {p.height_in:>6.2f} in | {p.thickness_in:>4.2f} in | {p.bevel_angle_deg:>5.1f} deg | {p.notes}")

        lines.extend([
            "-" * 105,
            "",
            "[ ASSEMBLY GUIDELINES ]",
            "1. Pre-drill and countersink screw holes every 4 to 6 inches to prevent MDF splitting.",
            "2. Use high-grade PVA wood glue (e.g. Titebond II/III) generously on all joint seams.",
            "3. Apply polyurethane sealant or silicone bead along all internal corners for 100% airtight seal.",
            "4. Round over inside port entrance and exit mouth with a 1/2-inch roundover router bit to minimize turbulence.",
            "=" * 75
        ])

        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def calculate_baffle_layout_metrics(
    baffle_w: float,
    baffle_h: float,
    wall_thick: float,
    port_type: str,
    port_w: float,
    port_h: float,
    port_dia: float,
    num_subs: int,
    cutout_dia: float,
    flush_dia: float,
    template: str = "Equidistant Centered",
    flange_dia: Optional[float] = None,
    layout_mode: str = "Horizontal"  # 'Horizontal' or '2x2 Grid'
) -> Dict[str, Any]:
    """
    Computes precise positions, margins, inter-sub clearances, screw pitch circle diameter (PCD),
    and outer frame flange collision checks for CAD-style baffle blueprint rendering.
    Supports both 1xN horizontal inline and 2x2 stacked grid layouts.
    """
    n = max(1, num_subs)
    t = wall_thick
    int_w = max(1.0, baffle_w - 2.0 * t)
    int_h = max(1.0, baffle_h - 2.0 * t)

    # Frame outer flange diameter: defaults to flush diameter or cutout + 1.25" if unspecified
    f_dia = max(cutout_dia + 0.5, flange_dia if flange_dia else (flush_dia if flush_dia > cutout_dia else cutout_dia + 1.25))
    # Screw pitch circle diameter: typically halfway between cutout edge and outer flange rim
    pcd_dia = cutout_dia + ((f_dia - cutout_dia) * 0.52)

    # Determine port footprint along right baffle edge
    if port_type in ("none", "sealed"):
        pw = 0.0
        ph = 0.0
        sub_avail_span = int_w
    elif port_type == "slot":
        pw = port_w
        ph = min(int_h, port_h)
        sub_avail_span = int_w - pw
    else:  # round aeroport
        pw = port_dia
        ph = port_dia
        sub_avail_span = int_w

    is_2x2 = (n == 4 and "2x2" in layout_mode)
    sub_centers: List[Tuple[float, float]] = []

    if is_2x2:
        # 2x2 Stacked Grid Layout (2 columns, 2 rows)
        col_span = sub_avail_span / 2.0
        row_span = int_h / 2.0
        
        has_cutout_collision = (cutout_dia > col_span) or (cutout_dia > row_span)
        has_flange_collision = (f_dia > col_span) or (f_dia > row_span)
        has_collision = has_cutout_collision or has_flange_collision

        c1_x = t + (col_span * 0.5)
        c2_x = t + (col_span * 1.5)
        r1_y = t + (row_span * 0.5)
        r2_y = t + (row_span * 1.5)

        # 4 coordinates: Top-Left, Top-Right, Bot-Left, Bot-Right
        sub_centers = [(c1_x, r1_y), (c2_x, r1_y), (c1_x, r2_y), (c2_x, r2_y)]
        inter_gap = col_span - cutout_dia
        flange_gap = col_span - f_dia
        edge_left = c1_x - (cutout_dia / 2.0) - t
        sub_to_port_gap = (baffle_w - t - (pw if port_type == "slot" else 0.0)) - (c2_x + (cutout_dia / 2.0))
        top_gap = r1_y - (cutout_dia / 2.0) - t
        bottom_gap = baffle_h - t - (r2_y + (cutout_dia / 2.0))

    else:
        # 1xN Horizontal Inline Layout
        total_cutout_span = n * cutout_dia
        total_flange_span = n * f_dia
        surplus_space = sub_avail_span - total_cutout_span
        surplus_flange = sub_avail_span - total_flange_span

        has_cutout_collision = (surplus_space < 0.0) or (cutout_dia > int_h)
        has_flange_collision = (surplus_flange < 0.0) or (f_dia > int_h)
        has_collision = has_cutout_collision or has_flange_collision

        center_y = baffle_h / 2.0
        centers_x: List[float] = []

        if template == "Left Biased":
            edge_left = 1.0
            inter_gap = max(0.25, (surplus_space - edge_left) / max(1, n)) if surplus_space > 1.25 else (surplus_space / (n + 1))
            for i in range(n):
                cx = t + edge_left + (cutout_dia / 2.0) + (i * (cutout_dia + inter_gap))
                centers_x.append(cx)
            sub_to_port_gap = (baffle_w - t - (pw if port_type == "slot" else 0.0)) - (centers_x[-1] + (cutout_dia / 2.0))
        elif template == "Right Biased":
            edge_right = 1.0
            inter_gap = max(0.25, (surplus_space - edge_right) / max(1, n)) if surplus_space > 1.25 else (surplus_space / (n + 1))
            right_boundary = baffle_w - t - (pw if port_type == "slot" else 0.0)
            for i in range(n):
                offset_from_right = edge_right + (cutout_dia / 2.0) + ((n - 1 - i) * (cutout_dia + inter_gap))
                centers_x.append(right_boundary - offset_from_right)
            edge_left = (centers_x[0] - (cutout_dia / 2.0)) - t
            sub_to_port_gap = edge_right
        else:  # Equidistant Centered
            gap = surplus_space / (n + 1)
            inter_gap = gap
            edge_left = gap
            for i in range(n):
                cx = t + (gap * (i + 1)) + (cutout_dia * i) + (cutout_dia / 2.0)
                centers_x.append(cx)
            sub_to_port_gap = gap

        flange_gap = inter_gap - (f_dia - cutout_dia)
        top_gap = max(0.0, ((baffle_h - (2.0 * t)) - cutout_dia) / 2.0)
        bottom_gap = top_gap
        sub_centers = [(cx, center_y) for cx in centers_x]

    if has_cutout_collision:
        msg = "CRITICAL COLLISION: Baffle dimensions too small! Cutouts overlap each other or boundary walls."
    elif has_flange_collision:
        msg = "WARNING: Cutouts fit, but OUTER SPEAKER FLANGES overlap! Expand baffle width or height."
    else:
        msg = "CLEARANCE OK: All cutouts, screw pitch circles, and outer frame flanges fit with proper margins."

    return {
        "sub_centers": [(round(x, 3), round(y, 3)) for x, y in sub_centers],
        "centers_x": [round(x, 3) for x, y in sub_centers],
        "center_y": round(sub_centers[0][1], 3) if sub_centers else round(baffle_h / 2.0, 3),
        "is_2x2": is_2x2,
        "cutout_dia": round(cutout_dia, 3),
        "flush_dia": round(flush_dia, 3),
        "flange_dia": round(f_dia, 3),
        "pcd_dia": round(pcd_dia, 3),
        "edge_left_in": round(edge_left, 3),
        "inter_gap_in": round(inter_gap, 3),
        "flange_gap_in": round(flange_gap, 3),
        "sub_to_port_gap_in": round(sub_to_port_gap, 3),
        "top_gap_in": round(top_gap, 3),
        "bottom_gap_in": round(bottom_gap, 3),
        "port_w_in": round(pw, 3),
        "port_h_in": round(ph, 3),
        "has_collision": has_collision,
        "has_cutout_collision": has_cutout_collision,
        "has_flange_collision": has_flange_collision,
        "collision_message": msg
    }
