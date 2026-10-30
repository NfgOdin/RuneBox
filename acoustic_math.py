"""
RuneBox // Subwoofer Enclosure Lab
acoustic_math.py - Acoustic physics, Thiele/Small modeling, Helmholtz equations,
and port fluid dynamics.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

LITERS_PER_CUBIC_FOOT = 28.3168466
CUBIC_FEET_PER_LITER = 1.0 / LITERS_PER_CUBIC_FOOT
SPEED_OF_SOUND_MPS = 343.0  # Speed of sound at 20 degrees Celsius in dry air (m/s)
SPEED_OF_SOUND_INCHES_PER_SEC = 13504.0  # 343 m/s in inches/sec
AIR_DENSITY_KG_M3 = 1.2041  # Air density at 20 deg C (kg/m^3)


def liters_to_cuft(liters: float) -> float:
    return liters * CUBIC_FEET_PER_LITER


def cuft_to_liters(cuft: float) -> float:
    return cuft * LITERS_PER_CUBIC_FOOT


@dataclass
class TSParameters:
    fs: float
    qts: float
    qes: float
    qms: float
    vas_liters: float
    xmax_mm: float
    p_rms: float
    sd_sq_cm: Optional[float] = None
    nominal_dia_inch: Optional[float] = 12.0
    is_isobaric: bool = False
    num_drivers: int = 1

    @property
    def effective_vas_liters(self) -> float:
        base_vas = self.vas_liters
        if self.is_isobaric:
            base_vas *= 0.5
        return base_vas * self.num_drivers

    @property
    def effective_vas_cuft(self) -> float:
        return liters_to_cuft(self.effective_vas_liters)

    @property
    def effective_sd_sq_in(self) -> float:
        if self.sd_sq_cm and self.sd_sq_cm > 0:
            sd_in2 = self.sd_sq_cm * 0.15500031
        else:
            dia = self.nominal_dia_inch if self.nominal_dia_inch else 12.0
            r_eff = (dia * 0.5) * 0.82
            sd_in2 = math.pi * (r_eff ** 2)
        multiplier = 1 if self.is_isobaric else self.num_drivers
        return sd_in2 * multiplier

    @property
    def effective_sd_sq_m(self) -> float:
        return self.effective_sd_sq_in * 0.00064516

    @property
    def derived_qts(self) -> float:
        """
        Auto-derives total Q (Qts) if it is missing or 0.0.
        Acoustic Principle:
        Total damping (Qts) is the parallel combination of electrical damping (Qes)
        and mechanical damping (Qms). Formula: Qts = (Qes * Qms) / (Qes + Qms).
        Provides a safe fallback of 0.001 to prevent ZeroDivisionErrors in solver loops.
        """
        if self.qts > 0.0:
            return self.qts
        if self.qes > 0.0 and self.qms > 0.0:
            return (self.qes * self.qms) / (self.qes + self.qms)
        return 0.001

    @property
    def derived_qes(self) -> float:
        """
        Auto-derives electrical Q (Qes) if it is missing or 0.0.
        Acoustic Principle:
        Qes can be mathematically isolated from Qts and Qms.
        Formula: Qes = (Qts * Qms) / (Qms - Qts).
        Requires Qms to be strictly greater than Qts to prevent negative damping.
        """
        if self.qes > 0.0:
            return self.qes
        if self.qts > 0.0 and self.qms > 0.0 and self.qms > self.qts:
            return (self.qts * self.qms) / (self.qms - self.qts)
        return 0.001

    @property
    def derived_qms(self) -> float:
        """
        Auto-derives mechanical Q (Qms) if it is missing or 0.0.
        Acoustic Principle:
        Qms can be mathematically isolated from Qts and Qes.
        Formula: Qms = (Qts * Qes) / (Qes - Qts).
        Requires Qes to be strictly greater than Qts.
        """
        if self.qms > 0.0:
            return self.qms
        if self.qts > 0.0 and self.qes > 0.0 and self.qes > self.qts:
            return (self.qts * self.qes) / (self.qes - self.qts)
        return 0.001

    @property
    def ebp(self) -> float:
        """
        Auto-derives Efficiency Bandwidth Product (EBP).
        Acoustic Principle:
        EBP is an objective indicator of motor force suitability for sealed vs ported alignments.
        Formula: EBP = Fs / Qes.
        """
        return self.fs / max(self.derived_qes, 0.001)

    @property
    def cms_m_per_n(self) -> float:
        """
        Auto-derives suspension mechanical compliance (Cms) in Meters per Newton (m/N).
        Physical Principle:
        Compliance dictates how 'soft' or 'stiff' the spider and surround are.
        It is derived from the acoustic compliance volume (Vas) and piston area (Sd).
        Formula: Cms = Vas_m3 / (rho * c^2 * Sd_m2^2)
        """
        vas_m3 = self.effective_vas_liters / 1000.0
        sd_m2 = self.effective_sd_sq_m
        if sd_m2 <= 0.0:
            return 0.0001

        # rho * c^2
        air_density = AIR_DENSITY_KG_M3
        speed_sound = SPEED_OF_SOUND_MPS
        restoring_force_factor = air_density * (speed_sound ** 2) * (sd_m2 ** 2)

        if restoring_force_factor <= 0.0:
            return 0.0001

        return vas_m3 / restoring_force_factor

    @property
    def mms_kg(self) -> float:
        """
        Auto-derives moving mass (Mms) in Kilograms (kg).
        Physical Principle:
        The resonant frequency (Fs) of a driver is dictated by the interaction between
        the suspension compliance (Cms) and the moving mass (Mms) of the cone assembly.
        Formula: Mms = 1 / ((2 * pi * Fs)^2 * Cms)
        """
        if self.fs <= 0.0:
            return 0.1

        cms = self.cms_m_per_n
        if cms <= 0.0:
            return 0.1

        omega_sq = (2.0 * math.pi * self.fs) ** 2
        return 1.0 / (omega_sq * cms)

    @property
    def sensitivity(self) -> Dict[str, float]:
        """
        Derives reference efficiency (n0) and 1W/1m SPL sensitivity.
        Physical Principle:
        Reference efficiency determines the acoustic power radiated relative to electrical input.
        n0 = (9.64 * 10^-10 * Fs^3 * Vas) / Qes.
        SPL at 1W/1m is calculated via standard logarithmic conversion:
        SPL_1W_1m = 112.2 + 10 * log10(n0).
        """
        qes_safe = max(self.qes, 0.001)
        n0_pct = (9.64 * (10 ** -10) * (self.fs ** 3) * self.vas_liters) / qes_safe * 100.0
        n0 = max(n0_pct / 100.0, 1e-12)
        spl_1w_1m = 112.2 + 10.0 * math.log10(n0)
        return {
            'n0_pct': round(n0_pct, 4),
            'spl_1w_1m_db': round(spl_1w_1m, 1)
        }


def calculate_ebp(fs: float, qes: float) -> Tuple[float, str, str]:
    if qes <= 0:
        return 0.0, 'Undefined', 'Qes must be greater than 0.'
    ebp = fs / qes
    if ebp <= 50.0:
        badge = 'Sealed Enclosure'
        detail = f'EBP is {ebp:.1f} (<= 50). Driver has high electrical damping / compliance suspension, ideal for tight sealed enclosures.'
    elif ebp < 85.0:
        badge = 'Flexible / Hybrid'
        detail = f'EBP is {ebp:.1f} (50-85). Highly versatile motor; performs reliably in sealed, low-tuned ported, or 4th-order bandpass.'
    else:
        badge = 'Ported / Bandpass'
        detail = f'EBP is {ebp:.1f} (>= 85). Strong motor force factor (Bl); engineered for high-efficiency vented, slotted, or 4th/6th order bandpass.'
    return round(ebp, 1), badge, detail


def solve_sealed_alignment(
    ts: TSParameters,
    target_qtc: float = 0.707,
    polyfill_boost_pct: float = 0.0
) -> Dict[str, Any]:
    ratio = target_qtc / ts.derived_qts
    if ratio <= 1.0:
        ratio = 1.001

    alpha = (ratio ** 2) - 1.0
    vas_cuft = ts.effective_vas_cuft
    gross_vb_cuft = vas_cuft / alpha
    fc = ts.fs * ratio

    term1 = (1.0 / (target_qtc ** 2)) - 2.0
    term2 = math.sqrt((term1 ** 2) + 4.0)
    f3_factor = math.sqrt(0.5 * (term1 + term2))
    f3 = fc * f3_factor

    polyfill_factor = 1.0 + (max(0.0, polyfill_boost_pct) / 100.0)
    net_vb_cuft = gross_vb_cuft / polyfill_factor

    return {
        'target_qtc': target_qtc,
        'net_vb_cuft': round(net_vb_cuft, 3),
        'net_vb_liters': round(cuft_to_liters(net_vb_cuft), 2),
        'fc_hz': round(fc, 1),
        'f3_hz': round(f3, 1),
        'alpha': round(alpha, 3),
        'polyfill_boost_pct': polyfill_boost_pct
    }


def solve_ported_optimal_keele(ts: TSParameters) -> Dict[str, Any]:
    vas_cuft = ts.effective_vas_cuft
    vb_cuft = 15.0 * vas_cuft * (ts.derived_qts ** 2.87)
    fb_hz = 0.42 * ts.fs * (ts.derived_qts ** -0.9)
    f3_hz = 0.26 * ts.fs * (ts.derived_qts ** -1.4)

    return {
        'recommended_vb_cuft': round(vb_cuft, 3),
        'recommended_vb_liters': round(cuft_to_liters(vb_cuft), 2),
        'recommended_fb_hz': round(fb_hz, 1),
        'f3_hz': round(f3_hz, 1)
    }


def solve_4th_order_bandpass(
    ts: TSParameters,
    s_factor: float = 0.707
) -> Dict[str, Any]:
    qtc_rear = 0.707
    ratio = qtc_rear / ts.derived_qts
    if ratio <= 1.0:
        ratio = 1.001
    alpha = (ratio ** 2) - 1.0
    vr_cuft = ts.effective_vas_cuft / alpha

    vf_cuft = 2.0 * (s_factor ** 2) * (ts.derived_qts ** 2) * ts.effective_vas_cuft
    fo = ts.fs * ratio
    bw = (ts.fs / ts.derived_qts) * s_factor
    fl = max(10.0, fo - (bw * 0.5))
    fh = fo + (bw * 0.5)

    gain_ratio = 2.0 * s_factor * (ts.derived_qts / qtc_rear)
    gain_db = 20.0 * math.log10(max(gain_ratio, 0.01))

    return {
        'rear_sealed_vb_cuft': round(vr_cuft, 3),
        'rear_sealed_vb_liters': round(cuft_to_liters(vr_cuft), 2),
        'front_vented_vb_cuft': round(vf_cuft, 3),
        'front_vented_vb_liters': round(cuft_to_liters(vf_cuft), 2),
        'center_fo_hz': round(fo, 1),
        'front_tuning_fb_hz': round(fo, 1),
        'low_cutoff_fl_hz': round(fl, 1),
        'high_cutoff_fh_hz': round(fh, 1),
        'gain_db': round(gain_db, 2)
    }


def solve_6th_order_bandpass_series_and_parallel(
    ts: TSParameters,
    rear_ratio_vas: float = 0.5,
    front_ratio_vas: float = 0.75
) -> Dict[str, Any]:
    vas_cuft = ts.effective_vas_cuft
    vr_cuft = rear_ratio_vas * vas_cuft * (ts.derived_qts ** 2.0)
    vf_cuft = front_ratio_vas * vas_cuft * ts.derived_qts

    fl_hz = 0.65 * ts.fs * (ts.derived_qts ** -0.3)
    fh_hz = 1.45 * ts.fs * (ts.derived_qts ** -0.3)

    return {
        'rear_chamber_vb_cuft': round(max(0.1, vr_cuft), 3),
        'rear_chamber_vb_liters': round(cuft_to_liters(max(0.1, vr_cuft)), 2),
        'rear_tuning_fl_hz': round(fl_hz, 1),
        'front_chamber_vb_cuft': round(max(0.1, vf_cuft), 3),
        'front_chamber_vb_liters': round(cuft_to_liters(max(0.1, vf_cuft)), 2),
        'front_tuning_fh_hz': round(fh_hz, 1)
    }


def calculate_helmholtz_port_length(
    vb_cuft: float,
    fb_hz: float,
    port_area_sq_in: float,
    port_type: str = 'slot',
    shared_walls: int = 3
) -> float:
    if vb_cuft <= 0 or fb_hz <= 0 or port_area_sq_in <= 0:
        return 0.0

    vb_cu_in = vb_cuft * 1728.0
    c = SPEED_OF_SOUND_INCHES_PER_SEC
    l_acoustic = ((c ** 2) * port_area_sq_in) / (4.0 * (math.pi ** 2) * (fb_hz ** 2) * vb_cu_in)
    r_eff = math.sqrt(port_area_sq_in / math.pi)

    p_type = port_type.lower()
    if 'flare' in p_type or 'aero' in p_type:
        k = 0.614
    elif 'round' in p_type or 'pipe' in p_type or 'pvc' in p_type:
        k = 0.732
    else:
        if shared_walls <= 0:
            k = 0.732
        elif shared_walls == 1:
            k = 1.15
        elif shared_walls == 2:
            k = 1.45
        else:
            k = 2.227

    l_physical = l_acoustic - (k * r_eff)
    return max(0.25, round(l_physical, 2))


def calculate_port_air_velocity(
    p_rms: float,
    sd_sq_in: float,
    xmax_mm: float,
    fb_hz: float,
    port_area_sq_in: float
) -> Dict[str, Any]:
    if port_area_sq_in <= 0 or fb_hz <= 0 or sd_sq_in <= 0:
        return {
            'velocity_mps': 0.0,
            'velocity_fps': 0.0,
            'mach_number': 0.0,
            'status': 'Invalid Inputs',
            'is_warning': False
        }

    sd_sq_m = sd_sq_in * 0.00064516
    xmax_m = (xmax_mm / 1000.0)
    ap_sq_m = port_area_sq_in * 0.00064516

    vd_m3 = sd_sq_m * xmax_m
    uo = math.sqrt(2.0) * vd_m3 * 2.0 * math.pi * fb_hz
    vo_mps = uo / ap_sq_m
    vo_fps = vo_mps * 3.28084
    mach = vo_mps / SPEED_OF_SOUND_MPS

    is_warning = False
    if vo_mps < 17.0:
        status = 'LAMINAR (Clean - Inaudible Turbulence)'
        badge_color = '#00E676'
    elif vo_mps <= 25.0:
        status = 'MODERATE (Slight compression risk at max excursion)'
        badge_color = '#FFD600'
    else:
        status = 'CHUFFING ALERT (>17 m/s, High Turbulence & Compression)'
        badge_color = '#FF1744'
        is_warning = True

    return {
        'velocity_mps': round(vo_mps, 2),
        'velocity_fps': round(vo_fps, 1),
        'mach_number': round(mach, 4),
        'status': status,
        'badge_color': badge_color,
        'is_warning': is_warning
    }
