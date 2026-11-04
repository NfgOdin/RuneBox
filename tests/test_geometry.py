import unittest
from geometry import EnclosureGeometry

class TestEnclosureGeometry(unittest.TestCase):

    def test_effective_sub_displacement_standard_mounting(self):
        """
        Acoustic Principle:
        Standard mounting means the subwoofers motor and basket are inside the enclosure.
        Therefore, they consume internal gross volume and displacement should be positive.
        """
        geom = EnclosureGeometry(
            sub_displacement_cuft=0.15,
            num_subwoofers=2,
            is_inverted_sub=False
        )
        self.assertAlmostEqual(geom.effective_sub_displacement_cuft, 0.30, places=3)

    def test_effective_sub_displacement_inverted_mounting(self):
        """
        Acoustic Principle:
        Inverted ('ass-out') mounting means the subwoofers motor and basket are outside the enclosure.
        Therefore, they do not consume internal gross volume and displacement should be 0.
        """
        geom = EnclosureGeometry(
            sub_displacement_cuft=0.15,
            num_subwoofers=2,
            is_inverted_sub=True
        )
        self.assertAlmostEqual(geom.effective_sub_displacement_cuft, 0.0, places=3)

    def test_solve_depth_for_target_net_volume_inverted(self):
        """
        Acoustic Principle:
        When back-solving for physical depth based on a target acoustic net volume,
        inverted subwoofers should require less gross volume because they don't take up space inside.
        """
        # Standard configuration
        geom_standard = EnclosureGeometry(
            shape="cuboid",
            wall_thickness=0.75,
            baffle_thickness=0.75,
            sub_displacement_cuft=0.15,
            num_subwoofers=2,
            is_inverted_sub=False,
            port_type="sealed",  # Keep it simple for testing
            bracing_displacement_cuft=0.0
        )
        d_standard, _ = geom_standard.solve_depth_for_target_net_volume(
            target_net_cuft=2.0,
            locked_height_in=14.0,
            locked_width_in=32.0
        )

        # Inverted configuration
        geom_inverted = EnclosureGeometry(
            shape="cuboid",
            wall_thickness=0.75,
            baffle_thickness=0.75,
            sub_displacement_cuft=0.15,
            num_subwoofers=2,
            is_inverted_sub=True,
            port_type="sealed",  # Keep it simple for testing
            bracing_displacement_cuft=0.0
        )
        d_inverted, _ = geom_inverted.solve_depth_for_target_net_volume(
            target_net_cuft=2.0,
            locked_height_in=14.0,
            locked_width_in=32.0
        )

        # Inverted should require less depth because we don't need to compensate for the 0.3 cuft of subs
        self.assertTrue(d_inverted < d_standard)

if __name__ == '__main__':
    unittest.main()
