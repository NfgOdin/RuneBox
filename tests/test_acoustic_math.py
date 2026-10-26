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


class TestTSParameters(unittest.TestCase):
    def test_effective_vas_isobaric(self):
        """
        Acoustic Principle: Isobaric configurations pair two drivers face-to-face or clam-shell,
        effectively halving the required compliance volume (Vas) for the same low-frequency extension.
        """
        # is_isobaric = True, num_drivers = 1 => vas_liters * 0.5
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, is_isobaric=True)
        self.assertEqual(ts.effective_vas_liters, 25.0)

    def test_effective_sd_with_sq_cm(self):
        """
        Physical Principle: When Sd (cone area) is provided directly in square centimeters,
        it is converted to square inches via the multiplier 0.15500031.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0)
        self.assertAlmostEqual(ts.effective_sd_sq_in, 500.0 * 0.15500031, places=5)

    def test_effective_sd_missing_nominal_dia(self):
        """
        Physical Principle: If nominal_dia_inch is missing and sd_sq_cm is not provided,
        it defaults to a 12.0 inch diameter for calculating cone area (Sd).
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, nominal_dia_inch=None)
        # 12.0 * 0.5 * 0.82 = 4.92
        # pi * 4.92**2 = 76.046
        self.assertAlmostEqual(ts.effective_sd_sq_in, 76.046, places=2)

    def test_effective_sd_sq_m(self):
        """
        Physical Principle: Cone area in square meters is simply square inches * 0.00064516.
        """
        ts = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0)
        expected = (500.0 * 0.15500031) * 0.00064516
        self.assertAlmostEqual(ts.effective_sd_sq_m, expected, places=5)


class TestSolverRatioClamping(unittest.TestCase):
    def test_sealed_ratio_clamp(self):
        """
        Acoustic Principle: In sealed enclosures, the target Qtc must be greater than the driver's Qts.
        If it's not (ratio <= 1.0), the formula would produce infinite or negative volume.
        It is clamped to a ratio of 1.001 to simulate an infinite baffle.
        """
        # target_qtc = 0.707. Derived Qts will be 0.8, so ratio = 0.707/0.8 < 1.0
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        result = solve_sealed_alignment(ts, target_qtc=0.707)
        self.assertAlmostEqual(result['alpha'], (1.001**2) - 1.0, places=5)

    def test_4th_order_ratio_clamp(self):
        """
        Acoustic Principle: Similar to sealed enclosures, the rear chamber of a 4th order bandpass
        must have a Qtc greater than the driver's Qts. Ratio is clamped to 1.001 if needed.
        """
        # qtc_rear = 0.707. Derived Qts will be 0.8.
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)
        result = solve_4th_order_bandpass(ts)
        # Note: round(fo, 1) means we expect 30.0 * 1.001 = 30.03 rounded to 30.0
        self.assertEqual(result['center_fo_hz'], 30.0)


class TestPortFluidDynamics(unittest.TestCase):
    def test_helmholtz_port_length_invalid(self):
        """
        Mathematical Verification: Zero or negative box volumes, tuning frequencies, or port areas
        cannot sustain a Helmholtz resonance. Must return 0.0.
        """
        self.assertEqual(calculate_helmholtz_port_length(0.0, 30.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 0.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 0.0), 0.0)

    def test_helmholtz_port_length_k_factors(self):
        """
        Acoustic Principle: The physical length of a port is shorter than the acoustic length
        due to the mass of air just outside the port vibrating with it (end correction, k).
        Different port geometries and placements (shared walls) have different k factors.
        """
        # Fixed inputs: vb=2.0 cuft, fb=30 Hz, port_area=20 sq in
        # L_acoustic is constant.

        # Flare/aero (k=0.614)
        len_flare = calculate_helmholtz_port_length(2.0, 30.0, 20.0, port_type='flare')
        # Round (k=0.732)
        len_round = calculate_helmholtz_port_length(2.0, 30.0, 20.0, port_type='round')
        # Slot, 0 walls (k=0.732)
        len_slot_0 = calculate_helmholtz_port_length(2.0, 30.0, 20.0, port_type='slot', shared_walls=0)
        # Slot, 1 wall (k=1.15)
        len_slot_1 = calculate_helmholtz_port_length(2.0, 30.0, 20.0, port_type='slot', shared_walls=1)
        # Slot, 2 walls (k=1.45)
        len_slot_2 = calculate_helmholtz_port_length(2.0, 30.0, 20.0, port_type='slot', shared_walls=2)
        # Slot, 3+ walls (k=2.227)
        len_slot_3 = calculate_helmholtz_port_length(2.0, 30.0, 20.0, port_type='slot', shared_walls=3)

        self.assertEqual(len_round, len_slot_0)
        self.assertTrue(len_flare > len_round)
        self.assertTrue(len_round > len_slot_1)
        self.assertTrue(len_slot_1 > len_slot_2)
        self.assertTrue(len_slot_2 > len_slot_3)

    def test_helmholtz_port_length_clamp(self):
        """
        Physical Principle: Minimum physical port length is clamped to 0.25 inches.
        """
        # Use extremely large box and small port area to yield negative physical length after end-correction
        len_clamp = calculate_helmholtz_port_length(1000.0, 10.0, 10.0, port_type='slot', shared_walls=3)
        self.assertEqual(len_clamp, 0.25)

    def test_port_air_velocity_invalid(self):
        """
        Mathematical Verification: Cannot compute velocity for zero/negative port area, fb, or sd.
        """
        result = calculate_port_air_velocity(500.0, 0.0, 15.0, 30.0, 20.0)
        self.assertEqual(result['velocity_mps'], 0.0)
        self.assertEqual(result['status'], 'Invalid Inputs')

    def test_port_air_velocity_laminar(self):
        """
        Acoustic Principle: Port air velocity < 17.0 m/s is considered laminar (inaudible turbulence).
        """
        result = calculate_port_air_velocity(500.0, 75.0, 10.0, 30.0, 30.0) # Huge port, low xmax
        self.assertTrue(result['velocity_mps'] < 17.0)
        self.assertEqual(result['status'], 'LAMINAR (Clean - Inaudible Turbulence)')
        self.assertEqual(result['badge_color'], '#00E676')
        self.assertFalse(result['is_warning'])

    def test_port_air_velocity_moderate(self):
        """
        Acoustic Principle: Port air velocity between 17.0 and 25.0 m/s is considered moderate.
        Slight compression may occur at max excursion.
        """
        # Tuning to hit ~20 m/s
        result = calculate_port_air_velocity(500.0, 75.0, 20.0, 30.0, 20.0)
        self.assertTrue(17.0 <= result['velocity_mps'] <= 25.0)
        self.assertEqual(result['status'], 'MODERATE (Slight compression risk at max excursion)')
        self.assertEqual(result['badge_color'], '#FFD600')
        self.assertFalse(result['is_warning'])

    def test_port_air_velocity_chuffing(self):
        """
        Acoustic Principle: Port air velocity > 25.0 m/s causes audible chuffing, high turbulence, and compression.
        """
        # Small port, high excursion
        result = calculate_port_air_velocity(500.0, 75.0, 30.0, 30.0, 10.0)
        self.assertTrue(result['velocity_mps'] > 25.0)
        self.assertTrue('>17 m/s' in result['status'])
        self.assertEqual(result['badge_color'], '#FF1744')
        self.assertTrue(result['is_warning'])

if __name__ == '__main__':
    unittest.main()
