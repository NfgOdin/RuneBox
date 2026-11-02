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


    def test_ts_parameters_isobaric_and_num_drivers(self):
        """
        Test effective_vas_liters, effective_sd_sq_in, effective_sd_sq_m
        for standard, isobaric, and multiple drivers to cover lines 44, 53-60, 64.
        """
        # Standard Single Driver
        ts_std = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=1, is_isobaric=False, sd_sq_cm=500.0)
        self.assertAlmostEqual(ts_std.effective_vas_liters, 50.0)
        self.assertAlmostEqual(ts_std.effective_sd_sq_in, 77.5, places=1) # 500 * 0.155
        self.assertAlmostEqual(ts_std.effective_sd_sq_m, 0.05, places=2)

        # Isobaric Pair (Vas is halved, Sd is that of one driver)
        ts_iso = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=2, is_isobaric=True, sd_sq_cm=500.0)
        self.assertAlmostEqual(ts_iso.effective_vas_liters, 50.0)
        self.assertAlmostEqual(ts_iso.effective_sd_sq_in, 77.5, places=1)

        ts_no_sd = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=0.0, nominal_dia_inch=12.0)
        self.assertTrue(ts_no_sd.effective_sd_sq_in > 0)

        # Non-Isobaric Multi-Driver (Vas multiplied, Sd multiplied)
        ts_multi = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=2, is_isobaric=False, nominal_dia_inch=12.0)
        self.assertAlmostEqual(ts_multi.effective_vas_liters, 100.0)
        # Without sd_sq_cm, it calculates from nominal_dia_inch
        # r_eff = (12 * 0.5) * 0.82 = 4.92
        # sd_in2 = pi * (4.92^2) = ~76.046
        # multiplied by 2 = 152.09
        self.assertAlmostEqual(ts_multi.effective_sd_sq_in, 152.09, places=2)

    def test_ratio_bounds(self):
        """
        Test that solvers handle target_qtc or qtc_rear constraints correctly
        when the ratio of target to derived_qts is <= 1.0 (lines 124, 171).
        """
        ts_high_q = TSParameters(fs=40.0, qts=0.8, qes=0.9, qms=7.0, vas_liters=40.0, xmax_mm=10.0, p_rms=300.0)

        # sealed: target_qtc (default 0.707) / 0.8 is < 1.0, forces ratio = 1.001
        sealed = solve_sealed_alignment(ts_high_q)
        self.assertEqual(sealed['target_qtc'], 0.707)
        self.assertTrue('net_vb_cuft' in sealed)

        # 4th order: qtc_rear (0.707) / 0.8 < 1.0, forces ratio = 1.001
        bp4 = solve_4th_order_bandpass(ts_high_q)
        self.assertTrue('rear_sealed_vb_cuft' in bp4)

    def test_calculate_helmholtz_port_length(self):
        """
        Test calculate_helmholtz_port_length for invalid inputs, different port types,
        and shared walls edge cases to hit coverage lines 226-250.
        """
        from acoustic_math import calculate_helmholtz_port_length

        # Invalid inputs
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=0, fb_hz=35, port_area_sq_in=10), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=-5, port_area_sq_in=10), 0.0)

        # Valid: Flare/Aero
        len_aero = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='aero')
        self.assertTrue(len_aero > 0.25)

        # Valid: Round/Pipe
        len_round = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='round pvc')
        self.assertTrue(len_round > 0.25)

        # Valid: Slot with different shared walls
        len_slot_0 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='slot', shared_walls=0)
        len_slot_1 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='slot', shared_walls=1)
        len_slot_2 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='slot', shared_walls=2)
        len_slot_3 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='slot', shared_walls=3)
        len_slot_4 = calculate_helmholtz_port_length(vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='slot', shared_walls=4)

        self.assertTrue(len_slot_0 > 0.25)
        self.assertTrue(len_slot_1 > 0.25)
        self.assertTrue(len_slot_2 > 0.25)
        self.assertTrue(len_slot_3 > 0.25)
        self.assertTrue(len_slot_4 > 0.25)

    def test_calculate_port_air_velocity(self):
        """
        Test calculate_port_air_velocity invalid bounds and mach number checks
        for Laminar, Moderate, and Chuffing to hit coverage lines 260-291.
        """
        from acoustic_math import calculate_port_air_velocity

        # Invalid Inputs
        invalid = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=0, xmax_mm=10.0, fb_hz=35.0, port_area_sq_in=10.0)
        self.assertEqual(invalid['velocity_mps'], 0.0)
        self.assertEqual(invalid['status'], 'Invalid Inputs')

        # Laminar (very large port area relative to driver/xmax)
        laminar = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=50.0, xmax_mm=5.0, fb_hz=35.0, port_area_sq_in=100.0)
        self.assertTrue('LAMINAR' in laminar['status'])

        # Moderate (medium port area)
        moderate = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=80.0, xmax_mm=15.0, fb_hz=35.0, port_area_sq_in=18.0)
        self.assertTrue('MODERATE' in moderate['status'])

        # Chuffing (tiny port area, high excursion)
        chuffing = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=150.0, xmax_mm=30.0, fb_hz=30.0, port_area_sq_in=2.0)
        self.assertTrue('CHUFFING ALERT' in chuffing['status'])
        self.assertTrue(chuffing['is_warning'])

if __name__ == '__main__':
    unittest.main()
