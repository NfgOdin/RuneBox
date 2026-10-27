import unittest
from acoustic_math import (
    calculate_ebp,
    TSParameters,
    solve_sealed_alignment,
    solve_ported_optimal_keele,
    solve_4th_order_bandpass,
    solve_6th_order_bandpass_series_and_parallel,
    calculate_port_air_velocity,
    calculate_helmholtz_port_length,
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



    def test_effective_vas_liters(self):
        """
        Tests the effective Vas calculation based on isobaric configuration and number of drivers.
        Isobaric cuts Vas in half per pair, but we multiply by total drivers.
        """
        ts_iso = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=True, num_drivers=2)
        self.assertEqual(ts_iso.effective_vas_liters, 50.0)

        ts_norm = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=False, num_drivers=3)
        self.assertEqual(ts_norm.effective_vas_liters, 150.0)

    def test_effective_sd_sq_in_and_m(self):
        """
        Tests effective cone area fallback to nominal diameter when sd_sq_cm is absent.
        """
        ts_cm = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500)
        self.assertAlmostEqual(ts_cm.effective_sd_sq_in, 77.500155)
        self.assertAlmostEqual(ts_cm.effective_sd_sq_m, 0.05)

        ts_dia = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, nominal_dia_inch=10.0, num_drivers=3)
        self.assertAlmostEqual(ts_dia.effective_sd_sq_in, 158.4305175)
        self.assertAlmostEqual(ts_dia.effective_sd_sq_m, 0.102213)


class TestAcousticMathAdvanced(unittest.TestCase):

    def test_calculate_helmholtz_port_length_zero_inputs(self):
        """
        Tests zero and negative inputs to calculate_helmholtz_port_length.
        """
        self.assertEqual(calculate_helmholtz_port_length(0.0, 30.0, 12.56), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 0.0, 12.56), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 0.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(-2.0, 30.0, 12.56), 0.0)

    def test_calculate_helmholtz_port_length_port_types(self):
        """
        Tests calculation of port length and end corrections for different port types.
        Flare ports have less end correction, slot ports vary based on shared walls.
        """
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 12.56, port_type='flare'), 17.42)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 12.56, port_type='round'), 17.19)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 12.56, port_type='slot', shared_walls=0), 17.19)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 12.56, port_type='slot', shared_walls=1), 16.35)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 12.56, port_type='slot', shared_walls=2), 15.75)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 12.56, port_type='slot', shared_walls=3), 14.2)

    def test_calculate_port_air_velocity_invalid(self):
        """
        Tests zero and negative inputs to calculate_port_air_velocity.
        """
        res1 = calculate_port_air_velocity(500.0, 75.0, 5.0, 30.0, 0.0)
        self.assertEqual(res1['velocity_mps'], 0.0)
        res2 = calculate_port_air_velocity(500.0, 75.0, 5.0, 0.0, 30.0)
        self.assertEqual(res2['velocity_mps'], 0.0)
        res3 = calculate_port_air_velocity(500.0, 0.0, 5.0, 30.0, 30.0)
        self.assertEqual(res3['velocity_mps'], 0.0)

    def test_calculate_port_air_velocity_laminar(self):
        """
        Tests laminar flow. Velocity < 17 m/s.
        """
        res = calculate_port_air_velocity(500.0, 75.0, 5.0, 30.0, 30.0)
        self.assertEqual(res['velocity_mps'], 3.33)
        self.assertTrue('LAMINAR' in res['status'])
        self.assertFalse(res['is_warning'])

    def test_calculate_port_air_velocity_moderate(self):
        """
        Tests moderate flow. Velocity > 17 m/s and <= 25 m/s.
        """
        res = calculate_port_air_velocity(500.0, 75.0, 15.0, 30.0, 15.0)
        self.assertEqual(res['velocity_mps'], 19.99)
        self.assertTrue('MODERATE' in res['status'])
        self.assertFalse(res['is_warning'])

    def test_calculate_port_air_velocity_chuffing(self):
        """
        Tests chuffing flow. Velocity > 25 m/s. (Also alerts > 17m/s)
        """
        res = calculate_port_air_velocity(500.0, 75.0, 20.0, 30.0, 5.0)
        self.assertEqual(res['velocity_mps'], 79.97)
        self.assertTrue('CHUFFING' in res['status'])
        self.assertTrue(res['is_warning'])

if __name__ == '__main__':
    unittest.main()
