import unittest
from acoustic_math import (
    calculate_ebp,
    TSParameters,
    solve_sealed_alignment,
    solve_ported_optimal_keele,
    solve_4th_order_bandpass,
    solve_6th_order_bandpass_series_and_parallel
)

class TestAcousticMath(unittest.TestCase):

    def test_derived_qts(self):
        # Qts is given
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts1.derived_qts, 0.4)

        # Qts is 0.0, but Qes and Qms are given
        # Qts = (0.5 * 4.0) / (0.5 + 4.0) = 2.0 / 4.5 = 0.4444...
        ts2 = TSParameters(fs=30.0, qts=0.0, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertAlmostEqual(ts2.derived_qts, 0.4444, places=3)

        # Qts is 0.0, and Qes/Qms are 0.0 (fallback)
        ts3 = TSParameters(fs=30.0, qts=0.0, qes=0.0, qms=0.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts3.derived_qts, 0.001)

    def test_sensitivity(self):
        # Based on standard 12-inch sub specs
        ts = TSParameters(fs=33.7, qts=0.44, qes=0.49, qms=4.7, vas_liters=33.4, xmax_mm=19.0, p_rms=750.0)
        sens = ts.sensitivity

        # Expected manual check:
        # n0_pct = (9.64e-10 * (33.7**3) * 33.4) / 0.49 * 100 = ~0.2514
        # spl = 112.2 + 10 * log10(n0) = 86.2 dB
        self.assertTrue('n0_pct' in sens)
        self.assertTrue('spl_1w_1m_db' in sens)
        self.assertTrue(0.1 < sens['n0_pct'] < 1.0)
        self.assertTrue(80.0 < sens['spl_1w_1m_db'] < 95.0)

    def test_solver_fallback_with_zero_qts(self):
        # This tests that the solvers don't crash with ZeroDivisionError when QTS is 0.0
        # It relies on derived_qts correctly substituting the missing qts.
        ts = TSParameters(fs=30.0, qts=0.0, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)

        sealed = solve_sealed_alignment(ts)
        self.assertTrue('net_vb_cuft' in sealed)

        ported = solve_ported_optimal_keele(ts)
        self.assertTrue('recommended_vb_cuft' in ported)

        bp4 = solve_4th_order_bandpass(ts)
        self.assertTrue('front_vented_vb_cuft' in bp4)

        bp6 = solve_6th_order_bandpass_series_and_parallel(ts)
        self.assertTrue('front_chamber_vb_cuft' in bp6)

    def test_calculate_ebp_error_handling(self):
        # Test qes = 0
        result_zero = calculate_ebp(fs=30.0, qes=0.0)
        self.assertEqual(result_zero, (0.0, 'Undefined', 'Qes must be greater than 0.'))

        # Test qes < 0
        result_negative = calculate_ebp(fs=30.0, qes=-1.0)
        self.assertEqual(result_negative, (0.0, 'Undefined', 'Qes must be greater than 0.'))

    def test_calculate_ebp_sealed(self):
        # EBP <= 50
        # fs = 20, qes = 0.5 => ebp = 40.0
        ebp, badge, detail = calculate_ebp(fs=20.0, qes=0.5)
        self.assertEqual(ebp, 40.0)
        self.assertEqual(badge, 'Sealed Enclosure')
        self.assertTrue('<= 50' in detail)

    def test_calculate_ebp_flexible(self):
        # 50 < EBP < 85
        # fs = 35, qes = 0.5 => ebp = 70.0
        ebp, badge, detail = calculate_ebp(fs=35.0, qes=0.5)
        self.assertEqual(ebp, 70.0)
        self.assertEqual(badge, 'Flexible / Hybrid')
        self.assertTrue('50-85' in detail)

    def test_calculate_ebp_ported(self):
        # EBP >= 85
        # fs = 50, qes = 0.5 => ebp = 100.0
        ebp, badge, detail = calculate_ebp(fs=50.0, qes=0.5)
        self.assertEqual(ebp, 100.0)
        self.assertEqual(badge, 'Ported / Bandpass')
        self.assertTrue('>= 85' in detail)

    def test_ts_parameters_isobaric_and_fallback_sd(self):
        """
        Physical Principle:
        Isobaric loading halves the required compliance volume (Vas) as two drivers act as a single unit with double the mass and motor force,
        sharing the same internal air spring. When Sd is not explicitly known, we approximate it from the nominal diameter minus surround width.
        """
        import math
        # Isobaric config with 2 drivers
        ts_iso = TSParameters(fs=30.0, qts=0.5, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0,
                              is_isobaric=True, num_drivers=2, sd_sq_cm=None, nominal_dia_inch=10.0)
        # vas = 50 * 0.5 (isobaric) * 2 = 50.0
        self.assertEqual(ts_iso.effective_vas_liters, 50.0)
        self.assertAlmostEqual(ts_iso.effective_vas_cuft, 50.0 / 28.3168466, places=5)

        # fallback sd: dia=10.0 => r_eff = 5.0 * 0.82 = 4.1. sd = math.pi * 4.1^2 = 52.81017...
        # multiplier = 1 (isobaric) => sd = 52.81017...
        expected_sd_in = math.pi * (4.1 ** 2)
        self.assertAlmostEqual(ts_iso.effective_sd_sq_in, expected_sd_in, places=5)
        self.assertAlmostEqual(ts_iso.effective_sd_sq_m, expected_sd_in * 0.00064516, places=5)

    def test_solver_ratio_clipping(self):
        """
        Physical Principle:
        Enclosures act as a high-pass filter. A driver's Qtc in an enclosure must physically be greater than its free-air Qts.
        If a target Qtc is requested that is equal to or lower than the driver's Qts, an infinite or negative volume would be required.
        The solver intercepts this and clips the alignment ratio to a minimal functional boundary (1.001) to compute a massively infinite baffle equivalent.
        """
        # target_qtc = 0.707. Qts = 0.8 => ratio < 1.0 => ratio clipped to 1.001
        ts_high_qts = TSParameters(fs=30.0, qts=0.8, qes=0.9, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)

        sealed = solve_sealed_alignment(ts_high_qts, target_qtc=0.707)
        # alpha = 1.001^2 - 1 = 0.002001. vas_cuft = 1.7657
        # vb_cuft = 1.7657 / 0.002001 = 882.4...
        self.assertGreater(sealed['net_vb_cuft'], 800.0)
        self.assertAlmostEqual(sealed['alpha'], 0.002, places=3)

        bp4 = solve_4th_order_bandpass(ts_high_qts, s_factor=0.707)
        self.assertGreater(bp4['rear_sealed_vb_cuft'], 800.0)

    def test_calculate_helmholtz_port_length_edges(self):
        """
        Physical Principle:
        Helmholtz resonance length is inversely proportional to enclosure volume and the square of tuning frequency, and directly proportional to port area.
        Physical length subtracts an end correction factor (k * effective_radius) derived from port termination topology (flanged vs free-air) to account for acoustic mass extending past the physical boundaries.
        """
        from acoustic_math import calculate_helmholtz_port_length
        import math
        # Invalid inputs return 0.0
        self.assertEqual(calculate_helmholtz_port_length(0.0, 35.0, 20.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, -10.0, 20.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 0.0), 0.0)

        # Valid calculations for different port types
        vb, fb, ap = 2.0, 35.0, 20.0
        # acoustic length internally:
        # vb_in3 = 2.0 * 1728 = 3456
        # L_ac = (13504^2 * 20) / (4 * math.pi^2 * 35^2 * 3456) = 3647160320 / 167098495.2 = 21.826...
        # r_eff = math.sqrt(20 / math.pi) = 2.523...

        # Slot 3 walls: k = 2.227, end_corr = 5.619 -> ~16.21
        l_slot3 = calculate_helmholtz_port_length(vb, fb, ap, 'slot', 3)
        self.assertAlmostEqual(l_slot3, 16.21, places=1)

        # Slot 2 walls: k = 1.45, end_corr = 3.658 -> ~18.17
        l_slot2 = calculate_helmholtz_port_length(vb, fb, ap, 'slot', 2)
        self.assertAlmostEqual(l_slot2, 18.17, places=1)

        # Slot 1 wall: k = 1.15, end_corr = 2.901 -> ~18.92
        l_slot1 = calculate_helmholtz_port_length(vb, fb, ap, 'slot', 1)
        self.assertAlmostEqual(l_slot1, 18.92, places=1)

        # Slot 0 walls: k = 0.732, end_corr = 1.846 -> ~19.98
        l_slot0 = calculate_helmholtz_port_length(vb, fb, ap, 'slot', 0)
        self.assertAlmostEqual(l_slot0, 19.98, places=1)

        # Aero / flare: k = 0.614, end_corr = 1.549 -> ~20.28
        l_aero = calculate_helmholtz_port_length(vb, fb, ap, 'aero')
        self.assertAlmostEqual(l_aero, 20.28, places=1)

        # Round / pipe: k = 0.732, end_corr = 1.846 -> ~19.98
        l_round = calculate_helmholtz_port_length(vb, fb, ap, 'round')
        self.assertAlmostEqual(l_round, 19.98, places=1)

    def test_calculate_port_air_velocity_states(self):
        """
        Physical Principle:
        Port air velocity is the maximum particle speed at resonance, proportional to driver displacement (Sd * Xmax) and frequency, and inversely proportional to port area.
        Excessive velocity (>17 m/s) induces non-linear turbulent airflow, leading to audible 'chuffing' and acoustic compression.
        """
        from acoustic_math import calculate_port_air_velocity

        # Invalid inputs
        inv = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=0.0, xmax_mm=10.0, fb_hz=30.0, port_area_sq_in=10.0)
        self.assertEqual(inv['velocity_mps'], 0.0)
        self.assertEqual(inv['status'], 'Invalid Inputs')

        # Laminar < 17.0
        # large port, small excursion
        lam = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=5.0, fb_hz=30.0, port_area_sq_in=30.0)
        self.assertLess(lam['velocity_mps'], 17.0)
        self.assertIn('LAMINAR', lam['status'])

        # Moderate 17.0 - 25.0
        mod = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=15.0, fb_hz=30.0, port_area_sq_in=15.0)
        self.assertGreaterEqual(mod['velocity_mps'], 17.0)
        self.assertLessEqual(mod['velocity_mps'], 25.0)
        self.assertIn('MODERATE', mod['status'])

        # Chuffing > 25.0
        chf = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=25.0, fb_hz=30.0, port_area_sq_in=10.0)
        self.assertGreater(chf['velocity_mps'], 25.0)
        self.assertIn('CHUFFING', chf['status'])
        self.assertTrue(chf['is_warning'])


    def test_ts_parameters_sd_provided(self):
        """
        Physical Principle:
        When effective piston area (Sd) is provided directly in square cm, it should convert to square inches using the standard 0.15500031 factor, overriding the fallback nominal diameter calculation.
        """
        ts_sd = TSParameters(fs=30.0, qts=0.5, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0,
                              sd_sq_cm=500.0)
        expected_sd_in = 500.0 * 0.15500031
        self.assertEqual(ts_sd.effective_sd_sq_in, expected_sd_in)


if __name__ == '__main__':
    unittest.main()
