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


    def test_effective_vas_isobaric(self):
        """
        Acoustic Principle:
        Isobaric loading halves the required equivalent compliance volume (Vas)
        because two drivers operate together mechanically coupled.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=True, num_drivers=1)
        self.assertEqual(ts.effective_vas_liters, 25.0)

    def test_effective_sd_fallback(self):
        """
        Acoustic Principle:
        If standard driver radiating area (Sd) is missing, we approximate it using
        nominal diameter, assuming ~82% is radiating cone and the rest is surround.
        """
        # sd_sq_cm is 0
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=0.0, nominal_dia_inch=12.0)

        # r_eff = (12.0 * 0.5) * 0.82 = 4.92
        # sd_in2 = pi * (4.92**2) = 76.046
        self.assertAlmostEqual(ts.effective_sd_sq_in, 76.046, places=2)

        # Fallback to 12.0 if nominal_dia_inch is missing
        ts_no_dia = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=0.0)
        self.assertAlmostEqual(ts_no_dia.effective_sd_sq_in, 76.046, places=2)

    def test_effective_sd_sq_m(self):
        """
        Acoustic Principle:
        Conversion of effective surface area from square inches to square meters.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0)
        # 500 sq cm = 77.5 sq in (500 * 0.15500031)
        # 77.5 sq in = 0.05 sq m (77.5 * 0.00064516)
        self.assertAlmostEqual(ts.effective_sd_sq_m, 0.050, places=3)

    def test_solve_sealed_alignment_ratio_low(self):
        """
        Acoustic Principle:
        Target system Q (Qtc) cannot be lower than the driver's intrinsic Q (Qts)
        without active compensation; we floor the ratio to 1.001 to prevent negative volumes.
        """
        ts = TSParameters(fs=30.0, qts=0.7, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        # target_qtc = 0.5 < qts (0.7), ratio floored to 1.001
        res = solve_sealed_alignment(ts, target_qtc=0.5)
        self.assertAlmostEqual(res['alpha'], (1.001**2) - 1.0, places=4)

    def test_solve_4th_order_bandpass_ratio_low(self):
        """
        Acoustic Principle:
        Rear chamber Qtc ratio flooring in 4th order bandpass to avoid impossible alpha values.
        """
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        # default qtc_rear is 0.707 < qts (0.8), ratio floored to 1.001
        res = solve_4th_order_bandpass(ts)
        # vr_cuft = vas / alpha. alpha = (1.001**2) - 1
        # alpha is approx 0.002
        # vas = 50L = 1.765 cuft
        # vr_cuft = 1.765 / 0.002 = approx 882
        self.assertTrue(res['rear_sealed_vb_cuft'] > 100.0)

    def test_calculate_helmholtz_port_length(self):
        """
        Acoustic Principle:
        Port length calculations account for end correction factors (k),
        which shift depending on the flaring geometry or shared physical boundaries (slot ports).
        """
        from acoustic_math import calculate_helmholtz_port_length

        # Invalid inputs
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=0, fb_hz=30, port_area_sq_in=10), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=-1, port_area_sq_in=10), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30, port_area_sq_in=0), 0.0)

        # Flare/Aero
        # k = 0.614
        length_flare = calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30.0, port_area_sq_in=12.56, port_type='flare')
        self.assertTrue(length_flare > 0)

        # Round/Pipe
        # k = 0.732
        length_round = calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30.0, port_area_sq_in=12.56, port_type='round')
        self.assertTrue(length_flare > length_round) # smaller end correction means longer physical pipe

        # Slot (shared_walls = 0)
        # k = 0.732
        length_slot0 = calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30.0, port_area_sq_in=12.56, port_type='slot', shared_walls=0)
        self.assertEqual(length_round, length_slot0)

        # Slot (shared_walls = 1)
        # k = 1.15
        length_slot1 = calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30.0, port_area_sq_in=12.56, port_type='slot', shared_walls=1)
        self.assertTrue(length_slot0 > length_slot1)

        # Slot (shared_walls = 2)
        # k = 1.45
        length_slot2 = calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30.0, port_area_sq_in=12.56, port_type='slot', shared_walls=2)
        self.assertTrue(length_slot1 > length_slot2)

        # Slot (shared_walls = 3)
        # k = 2.227
        length_slot3 = calculate_helmholtz_port_length(vb_cuft=1.0, fb_hz=30.0, port_area_sq_in=12.56, port_type='slot', shared_walls=3)
        self.assertTrue(length_slot2 > length_slot3)

    def test_calculate_port_air_velocity(self):
        """
        Acoustic Principle:
        Port air velocity is governed by volume displacement (Sd * Xmax) relative to port area.
        High velocity induces turbulent chuffing and dynamic compression.
        """
        from acoustic_math import calculate_port_air_velocity

        # Invalid inputs
        res_invalid = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=70.0, xmax_mm=10.0, fb_hz=30.0, port_area_sq_in=0.0)
        self.assertEqual(res_invalid['status'], 'Invalid Inputs')

        # Laminar (<17 m/s)
        # Large port area, low excursion
        res_laminar = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=70.0, xmax_mm=5.0, fb_hz=30.0, port_area_sq_in=50.0)
        self.assertTrue(res_laminar['velocity_mps'] < 17.0)
        self.assertTrue('LAMINAR' in res_laminar['status'])

        # Moderate (17 - 25 m/s)
        # Medium port area, moderate excursion
        # For moderate: we need velocity between 17 and 25.
        # vo_mps = (sqrt(2) * (sd_sq_m * xmax_m) * 2 * pi * fb_hz) / ap_sq_m
        # For sd_sq_in=70 (~0.045m2), xmax_mm=15, fb_hz=30 => uo = 1.414 * 0.045 * 0.015 * 188.5 = ~0.18 m3/s
        # Need ap_sq_m ~ 0.009 (port_area_sq_in ~ 14) to get ~20 m/s
        res_moderate = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=70.0, xmax_mm=15.0, fb_hz=30.0, port_area_sq_in=14.0)
        self.assertTrue(17.0 <= res_moderate['velocity_mps'] <= 25.0)
        self.assertTrue('MODERATE' in res_moderate['status'])

        # Chuffing (>25 m/s)
        # Very small port area, high excursion
        res_chuffing = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=70.0, xmax_mm=25.0, fb_hz=30.0, port_area_sq_in=5.0)
        self.assertTrue(res_chuffing['velocity_mps'] > 25.0)
        self.assertTrue('CHUFFING ALERT' in res_chuffing['status'])
        self.assertTrue(res_chuffing['is_warning'])


if __name__ == '__main__':
    unittest.main()
