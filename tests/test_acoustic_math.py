import unittest
from acoustic_math import (
    calculate_ebp,
    TSParameters,
    solve_sealed_alignment,
    solve_ported_optimal_keele,
    solve_4th_order_bandpass,
    solve_6th_order_bandpass_series_and_parallel,
    calculate_helmholtz_port_length,
    calculate_helmholtz_tuning_frequency
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

    def test_helmholtz_tuning_frequency_inverse(self):
        # Base setup
        vb_cuft = 2.0
        fb_hz = 32.0
        port_area_sq_in = 30.0

        # Calculate length
        length = calculate_helmholtz_port_length(
            vb_cuft=vb_cuft,
            fb_hz=fb_hz,
            port_area_sq_in=port_area_sq_in,
            port_type='slot',
            shared_walls=3
        )

        # Now back-solve for fb
        fb_calc = calculate_helmholtz_tuning_frequency(
            vb_cuft=vb_cuft,
            port_length_in=length,
            port_area_sq_in=port_area_sq_in,
            port_type='slot',
            shared_walls=3
        )

        # The result should be very close to original fb (32.0)
        # Floating point round trips may have small variance
        self.assertAlmostEqual(fb_hz, fb_calc, delta=0.5)

    def test_helmholtz_tuning_frequency_zero_values(self):
        # Zeros or negative values should return 0.0
        self.assertEqual(calculate_helmholtz_tuning_frequency(0.0, 10.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_tuning_frequency(2.0, -5.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_tuning_frequency(2.0, 10.0, 0.0), 0.0)

    def test_helmholtz_tuning_frequency_different_ports(self):
        # Using a flare port should give a slightly higher tuning due to lower k-factor
        fb_slot = calculate_helmholtz_tuning_frequency(2.0, 20.0, 30.0, 'slot', 3)
        fb_flare = calculate_helmholtz_tuning_frequency(2.0, 20.0, 30.0, 'flare')

        # k = 0.614 for flare, k = 2.227 for slot with 3 shared walls
        # Flare has shorter acoustic length, hence higher tuning freq.
        self.assertTrue(fb_flare > fb_slot)

if __name__ == '__main__':
    unittest.main()
