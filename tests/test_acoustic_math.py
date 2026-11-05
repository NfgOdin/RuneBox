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


    def test_effective_sd_and_vas(self):
        """
        Acoustic Principle: Verify that the effective cone area (Sd) and equivalent compliance volume (Vas)
        scale correctly depending on the number of drivers and whether the configuration is isobaric
        (where Vas halves, and Sd depends on configuration).
        """
        # Case 1: Base Vas and Sd from sd_sq_cm
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=1, is_isobaric=False)
        self.assertEqual(ts1.effective_vas_liters, 50.0)
        expected_sd_in = 500.0 * 0.15500031
        self.assertAlmostEqual(ts1.effective_sd_sq_in, expected_sd_in, places=4)
        self.assertAlmostEqual(ts1.effective_sd_sq_m, expected_sd_in * 0.00064516, places=4)

        # Case 2: 2 drivers, normal
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=2, is_isobaric=False)
        self.assertEqual(ts2.effective_vas_liters, 100.0)
        self.assertAlmostEqual(ts2.effective_sd_sq_in, expected_sd_in * 2.0, places=4)

        # Case 3: 2 drivers, isobaric (vas is 50.0 * 0.5 * 2 = 50.0)
        # Wait, if is_isobaric is True, base_vas *= 0.5. Then return base_vas * num_drivers
        # Let's check acoustic_math.py logic:
        # base_vas = 50.0, if isobaric -> 25.0. return 25.0 * 2 = 50.0.
        ts3 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=2, is_isobaric=True)
        self.assertEqual(ts3.effective_vas_liters, 50.0)
        # multiplier = 1 if is_isobaric else num_drivers => 1
        self.assertAlmostEqual(ts3.effective_sd_sq_in, expected_sd_in * 1.0, places=4)

        # Case 4: No sd_sq_cm, fallback to nominal_dia_inch = 12.0
        ts4 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, nominal_dia_inch=12.0, num_drivers=1, is_isobaric=False)
        import math
        expected_dia = 12.0
        r_eff = (expected_dia * 0.5) * 0.82
        expected_sd_in4 = math.pi * (r_eff ** 2)
        self.assertAlmostEqual(ts4.effective_sd_sq_in, expected_sd_in4, places=4)

    def test_sealed_alignment_ratio_fallback(self):
        """
        Acoustic Principle: Verify that when solving for a sealed alignment, if the target Qtc is lower
        than the driver's derived Qts, the ratio defaults to a safe fallback (1.001) to prevent undefined
        or negative compliance ratios.
        """
        # driver qts = 0.8, target_qtc = 0.707. ratio = 0.707/0.8 < 1.0 -> should be 1.001
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.9, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        res = solve_sealed_alignment(ts, target_qtc=0.707)
        # alpha = 1.001**2 - 1.0 = 1.002001 - 1.0 = 0.002001
        # vas_cuft = 50.0 / 28.3168466 = 1.76573...
        # gross_vb_cuft = 1.76573... / 0.002001 = ~882.4
        self.assertAlmostEqual(res['net_vb_cuft'], 882.42, places=1)
        self.assertEqual(res['fc_hz'], 30.0)

    def test_4th_order_bandpass_ratio_fallback(self):
        """
        Acoustic Principle: Verify that for a 4th order bandpass design, if the desired rear chamber Qtc
        is less than the driver's Qts, a safe ratio fallback (1.001) is engaged to maintain valid geometry bounds.
        """
        # driver qts = 0.8. internal qtc_rear = 0.707. ratio = 0.707 / 0.8 < 1.0 -> 1.001
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.9, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        res = solve_4th_order_bandpass(ts)

        # vas_cuft = 50.0 / 28.3168466 = 1.76573
        # alpha = 1.001**2 - 1 = 0.002001
        # vr_cuft = vas_cuft / alpha = ~882.42
        self.assertAlmostEqual(res['rear_sealed_vb_cuft'], 882.42, places=1)

    def test_calculate_helmholtz_port_length(self):
        """
        Acoustic Principle: Verify Helmholtz resonance port length calculations for different port types and
        shared walls, factoring in effective end-corrections to predict physical tuning accuracy.
        """
        vb = 2.0
        fb = 35.0
        port_area = 20.0
        # vb_cu_in = 2.0 * 1728 = 3456
        # c = 13504
        # l_acoustic = (13504**2 * 20) / (4 * pi**2 * 35**2 * 3456)
        # = 3647160320 / 167106429.69 = 21.82537...
        # r_eff = sqrt(20 / pi) = 2.5231...

        import math
        l_acoustic = ((13504.0 ** 2) * port_area) / (4.0 * (math.pi ** 2) * (fb ** 2) * (vb * 1728.0))
        r_eff = math.sqrt(port_area / math.pi)

        # Slot, 3 shared walls: k = 2.227
        # l_physical = 21.82537 - (2.227 * 2.5231...) = 21.82537 - 5.6190 = 16.206...
        l_slot_3 = calculate_helmholtz_port_length(vb, fb, port_area, 'slot', 3)
        self.assertAlmostEqual(l_slot_3, round(l_acoustic - 2.227 * r_eff, 2))

        # Aero / Flare: k = 0.614
        l_aero = calculate_helmholtz_port_length(vb, fb, port_area, 'aero', 0)
        self.assertAlmostEqual(l_aero, round(l_acoustic - 0.614 * r_eff, 2))

        # Round / Pipe: k = 0.732
        l_round = calculate_helmholtz_port_length(vb, fb, port_area, 'round', 0)
        self.assertAlmostEqual(l_round, round(l_acoustic - 0.732 * r_eff, 2))

        # Slot, 0 shared walls: k = 0.732
        l_slot_0 = calculate_helmholtz_port_length(vb, fb, port_area, 'slot', 0)
        self.assertAlmostEqual(l_slot_0, round(l_acoustic - 0.732 * r_eff, 2))

        # Slot, 1 shared walls: k = 1.15
        l_slot_1 = calculate_helmholtz_port_length(vb, fb, port_area, 'slot', 1)
        self.assertAlmostEqual(l_slot_1, round(l_acoustic - 1.15 * r_eff, 2))

        # Slot, 2 shared walls: k = 1.45
        l_slot_2 = calculate_helmholtz_port_length(vb, fb, port_area, 'slot', 2)
        self.assertAlmostEqual(l_slot_2, round(l_acoustic - 1.45 * r_eff, 2))

        # Invalid bounds
        self.assertEqual(calculate_helmholtz_port_length(-1.0, 35.0, 20.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, -35.0, 20.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 0.0), 0.0)

    def test_calculate_port_air_velocity(self):
        """
        Acoustic Principle: Verify air velocity in the port to predict aerodynamic noise and compression.
        Classifies speed into Laminar, Moderate, or Chuffing risk.
        """
        p_rms = 500.0
        sd_sq_in = 75.0
        xmax_mm = 15.0
        fb = 35.0

        # Let's test a very large port to get LAMINAR
        # ap = 100.0
        res_lam = calculate_port_air_velocity(p_rms, sd_sq_in, xmax_mm, fb, 100.0)
        self.assertEqual(res_lam['status'], 'LAMINAR (Clean - Inaudible Turbulence)')
        self.assertFalse(res_lam['is_warning'])

        # Check Mach and mps values explicitly for a known port
        # ap = 30.0
        # sd_sq_m = 75.0 * 0.00064516 = 0.048387
        # xmax_m = 0.015
        # vd_m3 = 0.048387 * 0.015 = 0.000725805
        # uo = sqrt(2) * 0.000725805 * 2 * pi * 35 = 0.2257...
        # ap_sq_m = 30.0 * 0.00064516 = 0.0193548
        # vo_mps = uo / ap_sq_m = 11.66...
        import math
        res = calculate_port_air_velocity(p_rms, sd_sq_in, xmax_mm, fb, 30.0)
        expected_uo = math.sqrt(2.0) * (sd_sq_in * 0.00064516 * (xmax_mm / 1000.0)) * 2.0 * math.pi * fb
        expected_vo_mps = expected_uo / (30.0 * 0.00064516)

        self.assertAlmostEqual(res['velocity_mps'], round(expected_vo_mps, 2))
        self.assertAlmostEqual(res['velocity_fps'], round(expected_vo_mps * 3.28084, 1))
        self.assertAlmostEqual(res['mach_number'], round(expected_vo_mps / 343.0, 4))

        # Force a small port for CHUFFING ALERT
        res_chuff = calculate_port_air_velocity(p_rms, sd_sq_in, xmax_mm, fb, 5.0)
        self.assertEqual(res_chuff['status'], 'CHUFFING ALERT (>17 m/s, High Turbulence & Compression)')
        self.assertTrue(res_chuff['is_warning'])

        # Test MODERATE zone (approx 17-25 mps)
        # vo_mps = 11.66 for 30 sq_in. For 20 mps we need ap = 30 * (11.66/20) = 17.5 sq_in
        res_mod = calculate_port_air_velocity(p_rms, sd_sq_in, xmax_mm, fb, 16.0)
        # verify expected vo_mps is between 17 and 25
        self.assertTrue(17.0 <= res_mod['velocity_mps'] <= 25.0)
        self.assertEqual(res_mod['status'], 'MODERATE (Slight compression risk at max excursion)')

        # Invalid bounds
        res_inv1 = calculate_port_air_velocity(p_rms, sd_sq_in, xmax_mm, -35.0, 30.0)
        self.assertEqual(res_inv1['velocity_mps'], 0.0)
        self.assertEqual(res_inv1['status'], 'Invalid Inputs')

        res_inv2 = calculate_port_air_velocity(p_rms, -10.0, xmax_mm, 35.0, 30.0)
        self.assertEqual(res_inv2['velocity_mps'], 0.0)
        self.assertEqual(res_inv2['status'], 'Invalid Inputs')

        res_inv3 = calculate_port_air_velocity(p_rms, sd_sq_in, xmax_mm, 35.0, 0.0)
        self.assertEqual(res_inv3['velocity_mps'], 0.0)
        self.assertEqual(res_inv3['status'], 'Invalid Inputs')

if __name__ == '__main__':
    unittest.main()
