import unittest
import math
from geometry import EnclosureGeometry, calculate_baffle_layout_metrics

class TestGeometry(unittest.TestCase):
    def test_calculate_exterior_gross_volume_cuft(self):
        """
        Tests the calculation of the exterior gross boundary volume.
        Acoustic principle: Exterior gross volume defines the total physical space footprint of the enclosure.
        This tests standard cuboid and wedge shapes, asserting accuracy and verifying no negative dimensions.
        """
        # 32x14x16 cuboid -> 32*14*16 / 1728 = 7168 / 1728 = 4.148148...
        enc_cuboid = EnclosureGeometry(ext_width=32.0, ext_height=14.0, ext_depth_bottom=16.0, ext_depth_top=16.0)
        self.assertAlmostEqual(enc_cuboid.calculate_exterior_gross_volume_cuft(), 4.148, places=3)

        # Wedge shape: 32x14x(16+10)/2 -> 32*14*13 / 1728 = 5824 / 1728 = 3.37037...
        enc_wedge = EnclosureGeometry(ext_width=32.0, ext_height=14.0, ext_depth_bottom=16.0, ext_depth_top=10.0, shape="single_wedge")
        self.assertAlmostEqual(enc_wedge.calculate_exterior_gross_volume_cuft(), 3.370, places=3)

    def test_calculate_internal_gross_volume_cuft(self):
        """
        Tests the raw internal cavity calculation inside the wood walls.
        Acoustic principle: This is the raw internal air space before driver/port displacements are deducted.
        Also tests negative inputs (e.g., ext_width < wall thickness) forcing max(0, x) safety checks.
        """
        enc = EnclosureGeometry(
            ext_width=32.0, ext_height=14.0, ext_depth_bottom=16.0, ext_depth_top=16.0,
            wall_thickness=0.75, baffle_thickness=0.75
        )
        # int_w = 32 - 1.5 = 30.5
        # int_h = 14 - 1.5 = 12.5
        # int_d = 16 - 1.5 = 14.5
        # 30.5 * 12.5 * 14.5 / 1728 = 5528.125 / 1728 = 3.199146...
        self.assertAlmostEqual(enc.calculate_internal_gross_volume_cuft(), 3.199, places=3)

        # Extreme negative test: enclosure smaller than wall thickness
        enc_small = EnclosureGeometry(
            ext_width=1.0, ext_height=1.0, ext_depth_bottom=1.0, ext_depth_top=1.0,
            wall_thickness=0.75, baffle_thickness=0.75
        )
        # int_w = max(0, 1 - 1.5) = 0
        self.assertEqual(enc_small.calculate_internal_gross_volume_cuft(), 0.0)

    def test_calculate_port_displacement_cuft(self):
        """
        Tests calculation of physical volume consumed by port walls and air column.
        Acoustic principle: Ports consume internal volume because the air inside the duct acts as an acoustic mass,
        and its physical enclosure takes up space that reduces the net working volume of the primary chamber.
        """
        # Round port test
        # 4 inch dia -> r = 2.0. r_outer = 2.0 + 0.22 = 2.22
        # pi * 2.22^2 * 24 = pi * 4.9284 * 24 = 371.597 / 1728 = 0.215
        enc_round = EnclosureGeometry(enclosure_type="ported", port_type="round", port_dia_in=4.0, port_physical_length_in=24.0, num_ports=1)
        self.assertAlmostEqual(enc_round.calculate_port_displacement_cuft(), 0.215, places=3)

        # Slot port test
        # port width = 2.5, wall_thick = 0.75 -> outer_w = 3.25
        # port_h = 12.5 -> outer_h = 12.5
        # length = 24.0
        # 3.25 * 12.5 * 24 = 975 / 1728 = 0.5642...
        enc_slot = EnclosureGeometry(enclosure_type="ported", port_type="slot", port_width_in=2.5, port_height_in=12.5, port_wall_thickness=0.75, port_physical_length_in=24.0, num_ports=1)
        self.assertAlmostEqual(enc_slot.calculate_port_displacement_cuft(), 0.564, places=3)

        # Zero port length or none
        enc_none = EnclosureGeometry(enclosure_type="ported", port_type="none", port_physical_length_in=24.0)
        self.assertEqual(enc_none.calculate_port_displacement_cuft(), 0.0)

        enc_zero_len = EnclosureGeometry(enclosure_type="ported", port_type="slot", port_physical_length_in=0.0)
        self.assertEqual(enc_zero_len.calculate_port_displacement_cuft(), 0.0)

    def test_calculate_net_internal_volume_cuft(self):
        """
        Tests the actual Net acoustic internal working volume.
        Acoustic principle: Net Vb = Internal Gross - Sub Disp - Port Disp - Bracing Disp - Divider Disp.
        This test verifies accurate cascading volume deductions, including the inverted subwoofer case where sub_disp is 0.
        """
        enc = EnclosureGeometry(
            ext_width=32.0, ext_height=14.0, ext_depth_bottom=16.0, ext_depth_top=16.0,
            wall_thickness=0.75, baffle_thickness=0.75,
            sub_displacement_cuft=0.14, num_subwoofers=1,
            bracing_displacement_cuft=0.05,
            enclosure_type="ported", port_type="slot", port_width_in=2.5, port_height_in=12.5, port_wall_thickness=0.75, port_physical_length_in=24.0, num_ports=1
        )
        # Gross = ~3.199
        # Sub = 0.14
        # Port = ~0.564
        # Bracing = 0.05
        # Divider = 0.0
        # Expected Net = 3.199 - 0.14 - 0.564 - 0.05 = 2.445
        self.assertAlmostEqual(enc.calculate_net_internal_volume_cuft(), 2.445, delta=0.01)

        # Test inverted subwoofer (ass-out), sub displacement should be 0 (actually it says 0.0 or added, code uses 0.0)
        enc.is_inverted_sub = True
        # Expected Net = 3.199 - 0.0 - 0.564 - 0.05 = 2.585
        self.assertAlmostEqual(enc.calculate_net_internal_volume_cuft(), 2.585, delta=0.01)

    def test_calculate_baffle_layout_metrics(self):
        """
        Tests the baffle layout spatial calculations for cutouts and clearances.
        Acoustic/Physical principle: Subwoofers require adequate physical spacing on a baffle. Cutouts must not
        overlap each other, cross into the port area, or collide with bounding walls. Outer flanges must also be tracked.
        """
        # Test 1: Standard equidistant centered, no collisions
        # Baffle 32x14, 0.75 walls -> internal 30.5 x 12.5.
        # Slot port 2.5W, leaves 28.0 for subs.
        # 2 subs, 11.125 cutout -> 22.25 total cutout. Surplus = 28.0 - 22.25 = 5.75
        # Gap = 5.75 / 3 = 1.916...
        # Flange dia = 12.5, flush dia = 12.5, cutout = 11.125
        res1 = calculate_baffle_layout_metrics(
            baffle_w=32.0, baffle_h=14.0, wall_thick=0.75,
            port_type="slot", port_w=2.5, port_h=12.5, port_dia=4.0,
            num_subs=2, cutout_dia=11.125, flush_dia=12.5,
            template="Equidistant Centered", layout_mode="Horizontal"
        )
        self.assertFalse(res1['has_collision'])
        self.assertFalse(res1['has_cutout_collision'])
        self.assertEqual(len(res1['sub_centers']), 2)
        self.assertAlmostEqual(res1['inter_gap_in'], 1.917, places=3)
        self.assertAlmostEqual(res1['edge_left_in'], 1.917, places=3)
        self.assertEqual(res1['collision_message'], "CLEARANCE OK: All cutouts, screw pitch circles, and outer frame flanges fit with proper margins.")

        # Test 2: Cutout collision (too many subs)
        # 4 subs, 11.125 cutout -> 44.5 > 28.0 available -> Collision
        res2 = calculate_baffle_layout_metrics(
            baffle_w=32.0, baffle_h=14.0, wall_thick=0.75,
            port_type="slot", port_w=2.5, port_h=12.5, port_dia=4.0,
            num_subs=4, cutout_dia=11.125, flush_dia=12.5,
            template="Equidistant Centered", layout_mode="Horizontal"
        )
        self.assertTrue(res2['has_collision'])
        self.assertTrue(res2['has_cutout_collision'])
        self.assertTrue("CRITICAL COLLISION" in res2['collision_message'])

        # Test 3: Flange collision only
        # Sub fits cutout, but outer flange is massive (20 inch flange on a 14 inch height baffle -> max int height 12.5)
        # Cutout is 10, int_h is 12.5 -> fits. Flange is 20 -> overlaps.
        res3 = calculate_baffle_layout_metrics(
            baffle_w=32.0, baffle_h=14.0, wall_thick=0.75,
            port_type="none", port_w=0.0, port_h=0.0, port_dia=0.0,
            num_subs=1, cutout_dia=10.0, flush_dia=20.0,
            template="Equidistant Centered", layout_mode="Horizontal"
        )
        self.assertTrue(res3['has_collision'])
        self.assertFalse(res3['has_cutout_collision'])
        self.assertTrue(res3['has_flange_collision'])
        self.assertTrue("WARNING: Cutouts fit, but OUTER SPEAKER FLANGES overlap" in res3['collision_message'])

        # Test 4: 2x2 Grid Layout
        res4 = calculate_baffle_layout_metrics(
            baffle_w=32.0, baffle_h=32.0, wall_thick=0.75,
            port_type="sealed", port_w=0.0, port_h=0.0, port_dia=0.0,
            num_subs=4, cutout_dia=10.0, flush_dia=11.0,
            template="Equidistant Centered", layout_mode="2x2 Grid"
        )
        self.assertTrue(res4['is_2x2'])
        self.assertEqual(len(res4['sub_centers']), 4)
        self.assertFalse(res4['has_collision'])

if __name__ == '__main__':
    unittest.main()
