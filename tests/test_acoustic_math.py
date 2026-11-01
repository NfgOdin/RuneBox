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


    def test_calculate_helmholtz_port_length(self):
        """
        Tests the calculation of Helmholtz port length.
        Acoustic Principle:
        The physical length of a port (L_physical) is derived from the acoustic length (L_acoustic)
        minus an end correction factor. L_acoustic depends on the speed of sound, port area,
        box volume, and tuning frequency.
        """
        from acoustic_math import calculate_helmholtz_port_length

        # Normal usage, 2.0 cuft, 35 Hz, 20 sq in area, slot port with 3 shared walls
        length = calculate_helmholtz_port_length(
            vb_cuft=2.0,
            fb_hz=35.0,
            port_area_sq_in=20.0,
            port_type='slot',
            shared_walls=3
        )
        # Expected manual check:
        # vb_cu_in = 2.0 * 1728 = 3456
        # c = 13504
        # L_ac = (13504^2 * 20) / (4 * pi^2 * 35^2 * 3456) = (3647160320) / (167123999.6) ≈ 21.82
        # r_eff = sqrt(20 / pi) ≈ 2.523
        # k = 2.227 (slot, 3 shared walls)
        # L_phys = 21.82 - (2.227 * 2.523) = 21.82 - 5.62 = 16.2
        self.assertAlmostEqual(length, 16.2, places=1)

        # Flare / aero port
        length_aero = calculate_helmholtz_port_length(
            vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='aero', shared_walls=0
        )
        self.assertAlmostEqual(length_aero, 20.27, places=1)

        # Round port
        length_round = calculate_helmholtz_port_length(
            vb_cuft=2.0, fb_hz=35.0, port_area_sq_in=20.0, port_type='round', shared_walls=0
        )
        self.assertAlmostEqual(length_round, 19.97, places=1)

        # Shared walls edge cases (slot)
        length_sw0 = calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'slot', 0)
        self.assertAlmostEqual(length_sw0, 19.97, places=1)

        length_sw1 = calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'slot', 1)
        self.assertAlmostEqual(length_sw1, 18.9, places=1)

        length_sw2 = calculate_helmholtz_port_length(2.0, 35.0, 20.0, 'slot', 2)
        self.assertAlmostEqual(length_sw2, 18.16, places=1)

        # Zero or negative inputs
        self.assertEqual(calculate_helmholtz_port_length(0.0, 35.0, 20.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 0.0, 20.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 35.0, -5.0), 0.0)


    def test_calculate_port_air_velocity(self):
        """
        Tests calculation of port air velocity.
        Acoustic Principle:
        Velocity relies on cone area (Sd) multiplied by excursion (Xmax) driven at a given frequency,
        forced through the port area. Mach number > 0.05 (~17 m/s) often introduces audible chuffing.
        """
        from acoustic_math import calculate_port_air_velocity

        # Laminar (Clean)
        res_laminar = calculate_port_air_velocity(
            p_rms=1000.0, sd_sq_in=75.0, xmax_mm=10.0, fb_hz=35.0, port_area_sq_in=40.0
        )
        self.assertTrue(res_laminar['velocity_mps'] < 17.0)
        self.assertEqual(res_laminar['status'], 'LAMINAR (Clean - Inaudible Turbulence)')
        self.assertFalse(res_laminar['is_warning'])

        # Moderate
        res_mod = calculate_port_air_velocity(
            p_rms=1000.0, sd_sq_in=75.0, xmax_mm=30.0, fb_hz=35.0, port_area_sq_in=35.0
        )
        self.assertTrue(17.0 <= res_mod['velocity_mps'] <= 25.0)
        self.assertEqual(res_mod['status'], 'MODERATE (Slight compression risk at max excursion)')
        self.assertFalse(res_mod['is_warning'])

        # Chuffing Alert
        res_chuff = calculate_port_air_velocity(
            p_rms=1000.0, sd_sq_in=100.0, xmax_mm=40.0, fb_hz=35.0, port_area_sq_in=20.0
        )
        self.assertTrue(res_chuff['velocity_mps'] > 25.0)
        self.assertTrue('CHUFFING ALERT' in res_chuff['status'])
        self.assertTrue(res_chuff['is_warning'])

        # Zero or negative inputs
        res_invalid = calculate_port_air_velocity(1000.0, 0.0, 10.0, 35.0, 20.0)
        self.assertEqual(res_invalid['velocity_mps'], 0.0)
        self.assertEqual(res_invalid['status'], 'Invalid Inputs')

if __name__ == '__main__':
    unittest.main()
