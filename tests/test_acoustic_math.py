import unittest
from acoustic_math import (
    calculate_ebp,
    TSParameters,
    solve_sealed_alignment,
    solve_ported_optimal_keele,
    solve_4th_order_bandpass,
    solve_6th_order_bandpass_series_and_parallel,
    calculate_helmholtz_port_length,
    calculate_port_air_velocity
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

    def test_calculate_helmholtz_port_length_invalid(self):
        """
        Tests fallback to 0.0 when invalid port params (zero or negative) are provided.
        """
        self.assertEqual(calculate_helmholtz_port_length(0.0, 30.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 0.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 0.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(-2.0, 30.0, 10.0), 0.0)

    def test_calculate_helmholtz_port_length_valid(self):
        """
        Tests Helmholtz port length calculations for standard ports.
        """
        # Flare / aero port: k=0.614
        length_flare = calculate_helmholtz_port_length(2.0, 35.0, 12.56, port_type='flare')
        self.assertGreater(length_flare, 0.0)

        # Round / pipe / pvc: k=0.732
        length_round = calculate_helmholtz_port_length(2.0, 35.0, 12.56, port_type='round')
        self.assertGreater(length_round, 0.0)

        # Slot ports with different shared walls
        length_slot_0 = calculate_helmholtz_port_length(2.0, 35.0, 12.56, port_type='slot', shared_walls=0)
        self.assertGreater(length_slot_0, 0.0)

        length_slot_1 = calculate_helmholtz_port_length(2.0, 35.0, 12.56, port_type='slot', shared_walls=1)
        self.assertGreater(length_slot_1, 0.0)

        length_slot_2 = calculate_helmholtz_port_length(2.0, 35.0, 12.56, port_type='slot', shared_walls=2)
        self.assertGreater(length_slot_2, 0.0)

        length_slot_3 = calculate_helmholtz_port_length(2.0, 35.0, 12.56, port_type='slot', shared_walls=3)
        self.assertGreater(length_slot_3, 0.0)

        # Test minimum port length boundary
        length_min = calculate_helmholtz_port_length(100.0, 100.0, 1.0, port_type='slot')
        self.assertEqual(length_min, 0.25)

    def test_calculate_port_air_velocity_invalid(self):
        """
        Tests fallback behavior when invalid input values (<= 0) are provided.
        """
        res1 = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=0.0, xmax_mm=10.0, fb_hz=35.0, port_area_sq_in=15.0)
        self.assertEqual(res1['velocity_mps'], 0.0)
        self.assertEqual(res1['status'], 'Invalid Inputs')

        res2 = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=10.0, fb_hz=0.0, port_area_sq_in=15.0)
        self.assertEqual(res2['velocity_mps'], 0.0)

        res3 = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=10.0, fb_hz=35.0, port_area_sq_in=0.0)
        self.assertEqual(res3['velocity_mps'], 0.0)

    def test_calculate_port_air_velocity_laminar(self):
        """
        Tests calculation triggering the LAMINAR (Clean) branch (< 17.0 m/s).
        """
        # Small xmax and large port area -> low velocity
        res = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=5.0, fb_hz=30.0, port_area_sq_in=40.0)
        self.assertTrue(res['velocity_mps'] < 17.0)
        self.assertIn('LAMINAR', res['status'])
        self.assertFalse(res['is_warning'])

    def test_calculate_port_air_velocity_moderate(self):
        """
        Tests calculation triggering the MODERATE branch (>= 17.0 and <= 25.0 m/s).
        """
        # Medium xmax, smaller port area -> moderate velocity
        # Vo = sqrt(2) * Vd * 2 * pi * fb / Ap
        # We tune it to fall into moderate.
        res = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=15.0, fb_hz=40.0, port_area_sq_in=20.0)
        self.assertTrue(17.0 <= res['velocity_mps'] <= 25.0)
        self.assertIn('MODERATE', res['status'])
        self.assertFalse(res['is_warning'])

    def test_calculate_port_air_velocity_chuffing(self):
        """
        Tests calculation triggering the CHUFFING ALERT branch (> 25.0 m/s).
        """
        # High xmax, high frequency, tiny port area -> very high velocity
        res = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=25.0, fb_hz=45.0, port_area_sq_in=10.0)
        self.assertTrue(res['velocity_mps'] > 25.0)
        self.assertIn('CHUFFING ALERT', res['status'])
        self.assertTrue(res['is_warning'])

    def test_ts_parameters_isobaric(self):
        """
        Tests that setting is_isobaric=True correctly halves the Vas and does not double the Sd for multiple drivers.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=True, num_drivers=2)
        # base = 50, isobaric = 50 * 0.5 = 25, num_drivers = 2 -> 25 * 2 = 50
        self.assertEqual(ts.effective_vas_liters, 50.0)

        # For Isobaric, multiplier is 1 regardless of num_drivers
        # Test requires a base Sd:
        ts.sd_sq_cm = 500.0
        self.assertEqual(ts.effective_sd_sq_in, 500.0 * 0.15500031)

        # Test Isobaric multiplier with nominal dia calculation
        ts.sd_sq_cm = 0.0
        # dia = 12.0, r_eff = 6 * 0.82 = 4.92. Area = pi * 4.92^2 = ~76.046
        import math
        expected_sd_in2 = math.pi * ((12.0 * 0.5 * 0.82) ** 2)
        self.assertAlmostEqual(ts.effective_sd_sq_in, expected_sd_in2, places=3)
        self.assertAlmostEqual(ts.effective_sd_sq_m, expected_sd_in2 * 0.00064516, places=5)

    def test_solver_ratio_less_than_one(self):
        """
        Tests solver ratios where target_qtc is equal or less than derived_qts.
        This forces the code into the `ratio = 1.001` branch.
        """
        # qts = 0.5
        ts = TSParameters(fs=30.0, qts=0.5, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)

        # target_qtc < qts (0.4 < 0.5)
        sealed = solve_sealed_alignment(ts, target_qtc=0.4)
        self.assertTrue('net_vb_cuft' in sealed)
        # Should execute logic using ratio = 1.001

        bp4 = solve_4th_order_bandpass(ts, s_factor=0.707)
        self.assertTrue('front_vented_vb_cuft' in bp4)
        # Should not crash on alpha calculation

        # Line 171 target: 6th order bandpass has hardcoded qtc_rear=0.707
        # Setting Qts=0.8 (> 0.707) triggers `ratio <= 1.0` and fallback to `ratio=1.001`
        ts_high_q = TSParameters(fs=30.0, qts=0.8, qes=0.9, qms=7.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        bp6 = solve_6th_order_bandpass_series_and_parallel(ts_high_q)
        self.assertTrue('front_chamber_vb_cuft' in bp6)

if __name__ == '__main__':
    unittest.main()
