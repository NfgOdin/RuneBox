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


    def test_effective_vas_liters_isobaric(self):
        """
        Acoustic Principle:
        Isobaric loading halves the Vas because the two drivers act as a single unit with double the moving mass, halving compliance.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=True, num_drivers=2, sd_sq_cm=0)
        self.assertEqual(ts.effective_vas_liters, 50.0) # (50 * 0.5) * 2 = 50.0

    def test_effective_sd_sq_in_isobaric(self):
        """
        Acoustic Principle:
        In an isobaric configuration, only one driver's cone area radiates outward, so Sd is not multiplied by the number of drivers.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=True, num_drivers=2, sd_sq_cm=0)
        self.assertAlmostEqual(ts.effective_sd_sq_in, 76.047, places=3) # calculated as math.pi * ((12.0 * 0.5) * 0.82)**2 = 76.0466...

    def test_solve_sealed_alignment_qtc_fallback(self):
        """
        Acoustic Principle:
        Target Qtc must be strictly greater than the driver's derived Qts to ensure the box volume remains positive and mathematically valid.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        # target_qtc 0.2 < derived_qts 0.4, ratio is <= 1.0, falls back to ratio = 1.001
        res = solve_sealed_alignment(ts, target_qtc=0.2)
        self.assertAlmostEqual(res['alpha'], 0.002, places=3) # (1.001**2) - 1.0 = 0.002001

    def test_solve_4th_order_bandpass_qtc_fallback(self):
        """
        Acoustic Principle:
        Similar to sealed, the rear chamber Qtc must be strictly greater than derived Qts to ensure valid rear chamber volume calculation.
        """
        # Qts is high enough to trigger ratio <= 1.0 with rear Qtc of 0.707
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.9, qms=7.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        from acoustic_math import solve_4th_order_bandpass
        res = solve_4th_order_bandpass(ts)
        self.assertAlmostEqual(res['rear_sealed_vb_cuft'], 882.425, places=3) # using fallback ratio 1.001

    def test_calculate_helmholtz_port_length_bounds_and_types(self):
        """
        Acoustic Principle:
        Calculates physical port length by subtracting end correction from acoustic port length.
        Invalid sizes must return 0.0. End correction factor depends on port termination type and shared walls.
        """
        from acoustic_math import calculate_helmholtz_port_length
        # Test zero/negative bounds
        self.assertEqual(calculate_helmholtz_port_length(-2.0, 35.0, 20.0, 'slot', 3), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, -35.0, 20.0, 'slot', 3), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, -20.0, 'slot', 3), 0.0)

        # Test normal slot port with shared walls
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'slot', 3), 16.2)

        # Test aero/flare port
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'flare', 0), 20.27)

        # Test round port with 0 shared walls
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'round', 0), 19.97)

        # Test slot with 1 shared wall
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'slot', 1), 18.92)

        # Test slot with 2 shared walls
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'slot', 2), 18.16)

    def test_calculate_port_air_velocity_bounds_and_warnings(self):
        """
        Acoustic Principle:
        Evaluates the peak port air velocity relative to Mach number.
        Velocities over 17 m/s exhibit high turbulence and chuffing, while those under are laminar. Invalid inputs return 0.0.
        """
        from acoustic_math import calculate_port_air_velocity
        # Test zero/negative bounds
        res_zero = calculate_port_air_velocity(500.0, -50.0, 5.0, 35.0, 20.0)
        self.assertEqual(res_zero['velocity_mps'], 0.0)
        self.assertEqual(res_zero['status'], 'Invalid Inputs')

        # Test laminar
        res_laminar = calculate_port_air_velocity(500.0, 50.0, 5.0, 35.0, 20.0)
        self.assertEqual(res_laminar['velocity_mps'], 3.89)
        self.assertEqual(res_laminar['status'], 'LAMINAR (Clean - Inaudible Turbulence)')

        # Test moderate
        res_mod = calculate_port_air_velocity(500.0, 80.0, 15.0, 35.0, 15.0)
        self.assertEqual(res_mod['velocity_mps'], 24.88)
        self.assertEqual(res_mod['status'], 'MODERATE (Slight compression risk at max excursion)')

        # Test chuffing
        res_chuff = calculate_port_air_velocity(500.0, 80.0, 20.0, 35.0, 10.0)
        self.assertEqual(res_chuff['velocity_mps'], 49.76)
        self.assertEqual(res_chuff['status'], 'CHUFFING ALERT (>17 m/s, High Turbulence & Compression)')
        self.assertTrue(res_chuff['is_warning'])



    def test_effective_sd_with_sq_cm(self):
        """
        Acoustic Principle:
        When standard cone area (Sd) is provided directly in square cm, it overrides derived Sd calculation and is correctly converted to square inches and meters.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0)
        self.assertAlmostEqual(ts.effective_sd_sq_in, 77.5, places=1)
        self.assertAlmostEqual(ts.effective_sd_sq_m, 0.05, places=2)

    def test_calculate_helmholtz_port_length_shared_walls_zero(self):
        """
        Acoustic Principle:
        A slot port with zero shared walls behaves similarly to a round port in terms of end correction, using a constant k-factor of 0.732 instead of higher boundary loading factors.
        """
        from acoustic_math import calculate_helmholtz_port_length
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'slot', 0), 19.97)


if __name__ == '__main__':
    unittest.main()
