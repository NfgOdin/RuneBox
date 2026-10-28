import unittest
import math
from acoustic_math import (
    calculate_ebp,
    TSParameters,
    solve_sealed_alignment,
    solve_ported_optimal_keele,
    solve_4th_order_bandpass,
    solve_6th_order_bandpass_series_and_parallel,
    calculate_helmholtz_port_length,
    calculate_port_air_velocity,
    LITERS_PER_CUBIC_FOOT
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

    def test_effective_vas(self):
        """
        Acoustic Principle:
        Vas (Equivalent Compliance Volume) scales with the number of drivers.
        In isobaric loading (push-pull), Vas is halved.
        """
        # Standard
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        self.assertEqual(ts.effective_vas_liters, 50.0)
        self.assertAlmostEqual(ts.effective_vas_cuft, 50.0 / LITERS_PER_CUBIC_FOOT, places=3)

        # 2 Drivers
        ts_2 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=2)
        self.assertEqual(ts_2.effective_vas_liters, 100.0)

        # Isobaric (1 pair)
        ts_iso = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=True)
        self.assertEqual(ts_iso.effective_vas_liters, 25.0)

    def test_effective_sd(self):
        """
        Acoustic Principle:
        Effective radiating area (Sd) scales with driver count.
        In isobaric loading, Sd is equivalent to a single driver.
        """
        # With sd_sq_cm given
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0)
        expected_sd_in = 500.0 * 0.15500031
        self.assertAlmostEqual(ts1.effective_sd_sq_in, expected_sd_in, places=3)
        self.assertAlmostEqual(ts1.effective_sd_sq_m, expected_sd_in * 0.00064516, places=4)

        # No sd_sq_cm, nominal dia 12"
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        r_eff = 6.0 * 0.82
        expected_sd_in2 = math.pi * (r_eff ** 2)
        self.assertAlmostEqual(ts2.effective_sd_sq_in, expected_sd_in2, places=3)

        # 2 Drivers
        ts3 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=2)
        self.assertAlmostEqual(ts3.effective_sd_sq_in, expected_sd_in * 2, places=3)

        # Isobaric (1 pair, Sd remains 1x)
        ts4 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, is_isobaric=True, num_drivers=1)
        self.assertAlmostEqual(ts4.effective_sd_sq_in, expected_sd_in, places=3)

    def test_calculate_helmholtz_port_length(self):
        """
        Acoustic Principle:
        Helmholtz resonance calculation incorporates port end correction (k factor)
        depending on port flaring and proximity to enclosure boundaries.
        """
        # Test invalid inputs
        self.assertEqual(calculate_helmholtz_port_length(0, 35.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 0), 0.0)

        vb_cuft = 2.0
        fb_hz = 35.0
        port_area_sq_in = 20.0

        # Test different port types
        l_flare = calculate_helmholtz_port_length(vb_cuft, fb_hz, port_area_sq_in, port_type='flare')
        l_round = calculate_helmholtz_port_length(vb_cuft, fb_hz, port_area_sq_in, port_type='round')
        l_slot_0 = calculate_helmholtz_port_length(vb_cuft, fb_hz, port_area_sq_in, port_type='slot', shared_walls=0)
        l_slot_1 = calculate_helmholtz_port_length(vb_cuft, fb_hz, port_area_sq_in, port_type='slot', shared_walls=1)
        l_slot_2 = calculate_helmholtz_port_length(vb_cuft, fb_hz, port_area_sq_in, port_type='slot', shared_walls=2)
        l_slot_3 = calculate_helmholtz_port_length(vb_cuft, fb_hz, port_area_sq_in, port_type='slot', shared_walls=3)

        # Verify k factors affect length correctly (larger k = shorter physical length)
        # Flare k=0.614, Round k=0.732, Slot 0 k=0.732, Slot 1 k=1.15, Slot 2 k=1.45, Slot 3 k=2.227
        self.assertTrue(l_flare > l_round)
        self.assertEqual(l_round, l_slot_0)
        self.assertTrue(l_slot_0 > l_slot_1 > l_slot_2 > l_slot_3)

    def test_calculate_port_air_velocity(self):
        """
        Acoustic Principle:
        Port air velocity must remain low to prevent audible chuffing (turbulence) and dynamic compression.
        """
        # Test invalid inputs
        res_invalid = calculate_port_air_velocity(500.0, 0.0, 10.0, 35.0, 20.0)
        self.assertEqual(res_invalid['velocity_mps'], 0.0)

        # Test valid inputs - LAMINAR
        # Small xmax, large port area
        res_lam = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=5.0, fb_hz=35.0, port_area_sq_in=40.0)
        self.assertTrue('LAMINAR' in res_lam['status'])
        self.assertFalse(res_lam['is_warning'])

        # Test valid inputs - MODERATE
        # Medium xmax, medium port area (needs to result in > 17 and <= 25 m/s)
        # vo_mps = sqrt(2) * (75 * 0.00064516) * (18 / 1000) * 2 * pi * 35 / (20 * 0.00064516) = ~20 m/s
        res_mod = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=18.0, fb_hz=35.0, port_area_sq_in=20.0)
        self.assertTrue('MODERATE' in res_mod['status'])
        self.assertFalse(res_mod['is_warning'])

        # Test valid inputs - CHUFFING
        # Large xmax, small port area
        res_chuff = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=75.0, xmax_mm=25.0, fb_hz=35.0, port_area_sq_in=15.0)
        self.assertTrue('CHUFFING' in res_chuff['status'])
        self.assertTrue(res_chuff['is_warning'])

if __name__ == '__main__':
    unittest.main()
