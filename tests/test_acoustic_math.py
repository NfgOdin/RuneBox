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

    def test_derived_qes(self):
        # Qes is given
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts1.derived_qes, 0.5)

        # Qes is 0.0, but Qts and Qms are given
        # Qes = (0.4 * 4.0) / (4.0 - 0.4) = 1.6 / 3.6 = 0.4444...
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.0, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertAlmostEqual(ts2.derived_qes, 0.4444, places=3)

        # Qes is 0.0, and Qms <= Qts (fallback)
        ts3 = TSParameters(fs=30.0, qts=0.4, qes=0.0, qms=0.3, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts3.derived_qes, 0.001)

    def test_derived_qms(self):
        # Qms is given
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts1.derived_qms, 4.0)

        # Qms is 0.0, but Qts and Qes are given
        # Qms = (0.4 * 0.5) / (0.5 - 0.4) = 0.2 / 0.1 = 2.0
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=0.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertAlmostEqual(ts2.derived_qms, 2.0, places=3)

        # Qms is 0.0, and Qes <= Qts (fallback)
        ts3 = TSParameters(fs=30.0, qts=0.4, qes=0.3, qms=0.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts3.derived_qms, 0.001)

    def test_ebp_property(self):
        # ebp = Fs / Qes = 30.0 / 0.5 = 60.0
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts1.ebp, 60.0)

        # ebp with derived Qes = 30.0 / 0.4444... = 67.5
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.0, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertAlmostEqual(ts2.ebp, 67.5, places=1)

    def test_cms_and_mms(self):
        # Reference driver: Fs=33.7, Vas=33.4L, Qes=0.49, Qms=4.7
        # We also need Sd to compute Cms and Mms.
        # Typically a 12-inch sub has Sd around 480 sq cm (approx 0.048 sq m).
        ts = TSParameters(
            fs=33.7,
            qts=0.44,
            qes=0.49,
            qms=4.7,
            vas_liters=33.4,
            xmax_mm=19.0,
            p_rms=750.0,
            sd_sq_cm=480.0
        )

        cms = ts.cms_m_per_n
        mms = ts.mms_kg

        # Vas = 33.4 L = 0.0334 m^3
        # Sd = 480 cm^2 = 0.048 m^2
        # rho = 1.2041, c = 343
        # Restoring force = 1.2041 * 343^2 * 0.048^2 = 1.2041 * 117649 * 0.002304 = 326.39
        # Cms = 0.0334 / 326.39 = 0.0001023 m/N
        # Mms = 1 / ((2 * pi * 33.7)^2 * 0.0001023) = 1 / (44820 * 0.0001023) = 1 / 4.586 = 0.218 kg (approx)
        self.assertAlmostEqual(cms, 0.0001023, places=6)
        self.assertTrue(0.15 < mms < 0.3)

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

if __name__ == '__main__':
    unittest.main()
