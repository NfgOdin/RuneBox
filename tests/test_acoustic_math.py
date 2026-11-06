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


    def test_effective_vas(self):
        """
        Acoustic Principle: Effective Vas (equivalent compliance volume) scales linearly with the number
        of drivers, but is halved when drivers are arranged in an isobaric (push-pull) configuration,
        as the coupled air mass effectively doubles the suspension stiffness.
        """
        # Standard: 1 driver
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=1, is_isobaric=False)
        self.assertEqual(ts1.effective_vas_liters, 50.0)
        self.assertAlmostEqual(ts1.effective_vas_cuft, 1.7657, places=3)

        # Multi-driver: 2 drivers
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=2, is_isobaric=False)
        self.assertEqual(ts2.effective_vas_liters, 100.0)

        # Isobaric: base_vas * 0.5 * num_drivers (assuming num_drivers=2 for isobaric typically, but if num_drivers=1 it's 25.0)
        ts3 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, num_drivers=1, is_isobaric=True)
        self.assertEqual(ts3.effective_vas_liters, 25.0)

    def test_effective_sd(self):
        """
        Acoustic Principle: Effective Sd (piston area) scales linearly with drivers unless isobaric,
        in which case only one cone's area radiates acoustic energy outward.
        """
        # Fallback to nominal_dia_inch
        ts1 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=0.0, nominal_dia_inch=10.0, num_drivers=1, is_isobaric=False)
        # r_eff = 5.0 * 0.82 = 4.1
        # sd_in2 = pi * (4.1**2) = 52.81017
        self.assertAlmostEqual(ts1.effective_sd_sq_in, 52.8102, places=3)
        self.assertAlmostEqual(ts1.effective_sd_sq_m, 0.03407, places=5)

        # Explicit sd_sq_cm
        ts2 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=1, is_isobaric=False)
        # sd_in2 = 500 * 0.15500031 = 77.500155
        self.assertAlmostEqual(ts2.effective_sd_sq_in, 77.500, places=3)

        # Multi-driver: 2 drivers
        ts3 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=2, is_isobaric=False)
        self.assertAlmostEqual(ts3.effective_sd_sq_in, 155.000, places=3)

        # Isobaric: 2 drivers, multiplier should be 1
        ts4 = TSParameters(fs=30.0, qts=0.4, qes=0.5, qms=4.0, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0, sd_sq_cm=500.0, num_drivers=2, is_isobaric=True)
        self.assertAlmostEqual(ts4.effective_sd_sq_in, 77.500, places=3)

    def test_solve_sealed_alignment_ratio_fallback(self):
        """
        Acoustic Principle: Sealed enclosure Qtc cannot be physically lower than the driver's intrinsic Qts.
        If a target Qtc <= Qts is requested, the mathematical ratio fallback forces a minimum enclosure compliance
        (ratio = 1.001) to prevent undefined infinite volume calculations.
        """
        ts = TSParameters(fs=30.0, qts=0.7, qes=0.8, qms=5.6, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)

        # Target Qtc = 0.6 <= Qts (0.7) -> ratio forced to 1.001
        res = solve_sealed_alignment(ts, target_qtc=0.6)

        # alpha = (1.001**2) - 1.0 = 0.002001
        # vas_cuft = 50 * 0.0353147 = 1.765735
        # gross_vb_cuft = 1.765735 / 0.002001 = 882.426
        self.assertAlmostEqual(res['alpha'], 0.002, places=3)
        self.assertAlmostEqual(res['net_vb_cuft'], 882.426, places=1)
        self.assertAlmostEqual(res['fc_hz'], 30.03, places=1)

    def test_solve_4th_order_bandpass_ratio_fallback(self):
        """
        Acoustic Principle: 4th order bandpass rear chamber tuning uses sealed box mathematics.
        If the required Qtc_rear (0.707) is <= driver Qts, a fallback ratio is applied to ensure
        solvable finite air-spring compliance (Vr).
        """
        ts = TSParameters(fs=30.0, qts=0.8, qes=0.9, qms=7.1, vas_liters=50.0, xmax_mm=10.0, p_rms=500.0)

        # Qts=0.8 > qtc_rear (0.707) -> ratio forced to 1.001
        res = solve_4th_order_bandpass(ts)

        # alpha = (1.001**2) - 1.0 = 0.002001
        # vr_cuft = 1.765735 / 0.002001 = 882.426
        self.assertAlmostEqual(res['rear_sealed_vb_cuft'], 882.426, places=1)

    def test_calculate_helmholtz_port_length(self):
        """
        Acoustic Principle: The physical length of a Helmholtz resonator port depends on the acoustic mass
        required to resonate with the enclosure's compliance volume (Vb) at frequency (Fb). Physical length
        is acoustic length minus end-correction (k), which varies by port geometry (flanged, free-air, slot).
        """
        from acoustic_math import calculate_helmholtz_port_length

        # Invalid inputs
        self.assertEqual(calculate_helmholtz_port_length(0.0, 30.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, -10.0, 10.0), 0.0)
        self.assertEqual(calculate_helmholtz_port_length(2.0, 30.0, 0.0), 0.0)

        # Valid inputs: 2.0 cuft, 35 Hz, 20 sq in area
        # Vb_in3 = 2.0 * 1728 = 3456
        # c = 13504.0
        # L_acoustic = (13504.0^2 * 20) / (4 * pi^2 * 35^2 * 3456)
        # L_acoustic = 3647160320 / (39.4784 * 1225 * 3456) = 3647160320 / 167137256.7 = 21.8213
        # r_eff = sqrt(20 / pi) = 2.5231

        # Flare/Aero: k = 0.614
        # L_physical = 21.8213 - (0.614 * 2.5231) = 21.8213 - 1.549 = 20.27
        self.assertAlmostEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, port_type='flare'), 20.27, places=2)

        # Round/Pipe: k = 0.732
        # L_physical = 21.8213 - (0.732 * 2.5231) = 21.8213 - 1.8469 = 19.97
        self.assertAlmostEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, port_type='round'), 19.97, places=2)

        # Slot (0 shared walls = 0.732)
        self.assertAlmostEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, port_type='slot', shared_walls=0), 19.97, places=2)

        # Slot (1 shared wall = 1.15)
        # L_physical = 21.8213 - (1.15 * 2.5231) = 21.8213 - 2.9015 = 18.92
        self.assertAlmostEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, port_type='slot', shared_walls=1), 18.92, places=2)

        # Slot (2 shared walls = 1.45)
        # L_physical = 21.8213 - (1.45 * 2.5231) = 21.8213 - 3.6585 = 18.16
        self.assertAlmostEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, port_type='slot', shared_walls=2), 18.16, places=2)

        # Slot (3 shared walls = 2.227)
        # L_physical = 21.8213 - (2.227 * 2.5231) = 21.8213 - 5.6189 = 16.20
        self.assertAlmostEqual(calculate_helmholtz_port_length(2.0, 35.0, 20.0, port_type='slot', shared_walls=3), 16.20, places=2)

    def test_calculate_port_air_velocity(self):
        """
        Acoustic Principle: Port air velocity is determined by the volume displacement (Sd * Xmax) pumping
        air through the port area (Ap) at resonance (Fb). High velocity causes chuffing (turbulence) and
        dynamic acoustic compression as the port behaves non-linearly.
        """
        from acoustic_math import calculate_port_air_velocity

        # Invalid inputs
        res_inv = calculate_port_air_velocity(500.0, -10.0, 10.0, 35.0, 20.0)
        self.assertEqual(res_inv['status'], 'Invalid Inputs')
        self.assertEqual(res_inv['velocity_mps'], 0.0)

        # Valid inputs
        # Sd = 77.5 sq in = 0.0500 m2
        # Xmax = 10.0 mm = 0.010 m
        # Fb = 35.0 Hz
        # Ap = 20.0 sq in = 0.0129032 m2
        # Vd = 0.05 * 0.01 = 0.0005 m3
        # Uo = sqrt(2) * 0.0005 * 2 * pi * 35 = 1.4142 * 0.0005 * 219.91 = 0.1555 m3/s
        # Vo_mps = 0.1555 / 0.0129032 = 12.05 m/s

        # LAMINAR case (Vo_mps < 17.0)
        res_lam = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=77.5, xmax_mm=10.0, fb_hz=35.0, port_area_sq_in=20.0)
        self.assertAlmostEqual(res_lam['velocity_mps'], 12.05, places=1)
        self.assertEqual(res_lam['status'], 'LAMINAR (Clean - Inaudible Turbulence)')
        self.assertFalse(res_lam['is_warning'])

        # MODERATE case (Vo_mps between 17.0 and 25.0)
        # Halve port area -> double velocity -> ~24.1 m/s
        res_mod = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=77.5, xmax_mm=10.0, fb_hz=35.0, port_area_sq_in=10.0)
        self.assertAlmostEqual(res_mod['velocity_mps'], 24.1, places=1)
        self.assertEqual(res_mod['status'], 'MODERATE (Slight compression risk at max excursion)')
        self.assertFalse(res_mod['is_warning'])

        # CHUFFING case (Vo_mps > 25.0)
        # Halve port area again -> double velocity -> ~48.2 m/s
        res_chf = calculate_port_air_velocity(p_rms=500.0, sd_sq_in=77.5, xmax_mm=10.0, fb_hz=35.0, port_area_sq_in=5.0)
        self.assertAlmostEqual(res_chf['velocity_mps'], 48.2, places=1)
        self.assertTrue('CHUFFING ALERT' in res_chf['status'])
        self.assertTrue(res_chf['is_warning'])

if __name__ == '__main__':
    unittest.main()
