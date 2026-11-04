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


    def test_effective_sd_sq_in_and_m(self):
        """
        Acoustic Principle: Calculates effective piston area (Sd).
        When exact Sd is unknown, it's estimated using the nominal diameter and an effective radius multiplier.
        For isobaric configurations, the drivers act as a single unit acoustically, so Sd doesn't increase with the number of drivers.
        """
        # When sd_sq_cm is provided
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=1, is_isobaric=False)
        self.assertAlmostEqual(ts1.effective_sd_sq_in, 77.500155)
        self.assertAlmostEqual(ts1.effective_sd_sq_m, 0.05)

        # When sd_sq_cm is 0 and nominal_dia_inch is provided
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=0.0, nominal_dia_inch=15.0, num_drivers=2, is_isobaric=False)
        r_eff = (15.0 * 0.5) * 0.82
        expected_sd_sq_in = 3.141592653589793 * (r_eff ** 2) * 2
        self.assertAlmostEqual(ts2.effective_sd_sq_in, expected_sd_sq_in)

        # Isobaric
        ts3 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=0.0, nominal_dia_inch=15.0, num_drivers=2, is_isobaric=True)
        r_eff = (15.0 * 0.5) * 0.82
        expected_sd_sq_in_iso = 3.141592653589793 * (r_eff ** 2) * 1
        self.assertAlmostEqual(ts3.effective_sd_sq_in, expected_sd_sq_in_iso)

    def test_solve_4th_order_bandpass_fallback(self):
        """
        Acoustic Principle: A 4th-order bandpass enclosure relies on the ratio of Qtc_rear / Qts.
        If the driver's Qts is too high resulting in a ratio <= 1.0, the calculation would yield infinite or negative volumes.
        A fallback ratio of 1.001 ensures mathematically solvable enclosure volumes.
        """
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.8, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        res = solve_4th_order_bandpass(ts)
        self.assertTrue('front_vented_vb_cuft' in res)

    def test_calculate_helmholtz_port_length_edge_cases(self):
        """
        Acoustic Principle: The physical port length is derived from the acoustic port length minus end corrections.
        End correction factors (k) vary based on port shape (flare vs slot) and boundary loading (shared walls).
        Testing edge cases for minimum volume/tuning values, and validating exact mathematically derived lengths.
        """
        from acoustic_math import calculate_helmholtz_port_length
        # Returns 0.0 for bad inputs
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=0.0, fb_hz=30.0, port_area_sq_in=10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=0.0, port_area_sq_in=10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30.0, port_area_sq_in=0.0), 0.0)

        # vb_cu_in = 2.0 * 1728 = 3456
        # l_acoustic = ((13503.9 ** 2) * 20) / (4 * (pi ** 2) * (30 ** 2) * 3456) = 29.69766
        # r_eff = sqrt(20 / pi) = 2.5231

        # Flare / aero (k = 0.614)
        # l_physical = 29.69766 - (0.614 * 2.5231) = 28.148
        l_flare = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=30.0, port_area_sq_in=20.0, port_type='flare', shared_walls=3)
        self.assertAlmostEqual(l_flare, 28.15, places=2)

        # Round / pipe / pvc (k = 0.732)
        # l_physical = 29.69766 - (0.732 * 2.5231) = 27.8507
        l_round = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=30.0, port_area_sq_in=20.0, port_type='round', shared_walls=3)
        self.assertAlmostEqual(l_round, 27.85, places=2)

        # Slot (shared_walls = 0, k = 0.732)
        l_slot_0 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=30.0, port_area_sq_in=20.0, port_type='slot', shared_walls=0)
        self.assertAlmostEqual(l_slot_0, 27.85, places=2)

        # Slot (shared_walls = 1, k = 1.15)
        # l_physical = 29.69766 - (1.15 * 2.5231) = 26.796
        l_slot_1 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=30.0, port_area_sq_in=20.0, port_type='slot', shared_walls=1)
        self.assertAlmostEqual(l_slot_1, 26.8, places=2)

        # Slot (shared_walls = 2, k = 1.45)
        # l_physical = 29.69766 - (1.45 * 2.5231) = 26.039
        l_slot_2 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=30.0, port_area_sq_in=20.0, port_type='slot', shared_walls=2)
        self.assertAlmostEqual(l_slot_2, 26.04, places=2)

        # Slot (shared_walls = 3, k = 2.227)
        # l_physical = 29.69766 - (2.227 * 2.5231) = 24.0787
        l_slot_3 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=30.0, port_area_sq_in=20.0, port_type='slot', shared_walls=3)
        self.assertAlmostEqual(l_slot_3, 24.08, places=2)

    def test_calculate_port_air_velocity_edge_cases(self):
        """
        Acoustic Principle: Port velocity dictates the risk of chuffing (audible turbulence).
        Calculated using peak cone displacement volume (Sd * Xmax) at tuning frequency (Fb).
        Speeds < 17 m/s are laminar, 17-25 m/s are moderate, and > 25 m/s risks severe compression and chuffing.
        """
        from acoustic_math import calculate_port_air_velocity
        # Invalid inputs
        res_invalid1 = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=0.0, xmax_mm=10.0, fb_hz=30.0, port_area_sq_in=10.0)
        self.assertEqual(res_invalid1['velocity_mps'], 0.0)
        res_invalid2 = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=50.0, xmax_mm=10.0, fb_hz=0.0, port_area_sq_in=10.0)
        self.assertEqual(res_invalid2['velocity_mps'], 0.0)
        res_invalid3 = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=50.0, xmax_mm=10.0, fb_hz=30.0, port_area_sq_in=0.0)
        self.assertEqual(res_invalid3['velocity_mps'], 0.0)

        # Laminar (velocity < 17.0 m/s)
        # Low excursion / small sd / large port
        res_laminar = calculate_port_air_velocity(p_rms=100.0, sd_sq_in=20.0, xmax_mm=2.0, fb_hz=30.0, port_area_sq_in=50.0)
        self.assertFalse(res_laminar['is_warning'])
        self.assertTrue('LAMINAR' in res_laminar['status'])

        # Moderate (17.0 <= velocity <= 25.0)
        res_moderate = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=80.0, xmax_mm=10.0, fb_hz=30.0, port_area_sq_in=10.0)
        self.assertFalse(res_moderate['is_warning'])
        self.assertTrue('MODERATE' in res_moderate['status'])

        # Chuffing (> 25.0)
        res_chuffing = calculate_port_air_velocity(p_rms=1000.0, sd_sq_in=120.0, xmax_mm=25.0, fb_hz=20.0, port_area_sq_in=5.0)
        self.assertTrue(res_chuffing['is_warning'])
        self.assertTrue('CHUFFING ALERT' in res_chuffing['status'])


    def test_effective_vas_isobaric(self):
        """
        Acoustic Principle: Calculates effective equivalent compliance volume (Vas).
        In an isobaric configuration (drivers face-to-face or compound loaded),
        the pair of drivers behaves as a single driver with half the Vas of a single driver.
        Thus, a pair of 50L drivers will yield an effective Vas of 25L.
        """
        ts_iso = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=2, is_isobaric=True)
        # Expected: (base_vas * 0.5) * (num_drivers / 2.0) -> (50.0 * 0.5) * (2 / 2.0) = 25.0
        self.assertEqual(ts_iso.effective_vas_liters, 25.0)

    def test_solve_sealed_alignment_ratio_fallback(self):
        """
        Acoustic Principle: Enclosure calculation requires ratio Qtc / Qts to be > 1.
        If a driver's Qts exceeds the target Qtc, a fallback ratio is enforced to prevent division by zero or negative volumes.
        """
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.8, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        # target_qtc is 0.707 default. ratio = 0.707 / 0.8 = 0.88375 <= 1.0
        # fallback makes it 1.001
        res = solve_sealed_alignment(ts)
        self.assertAlmostEqual(res['alpha'], (1.001 ** 2) - 1.0, places=2)

if __name__ == '__main__':
    unittest.main()
