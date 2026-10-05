"""Tests for wave-mode handling and radiation-pattern constants."""
import numpy as np
import pytest

from pynetdesign.modelling.utils import (
    RAD_PATTERN_P_DEFAULT,
    RAD_PATTERN_SH_DEFAULT,
    RAD_PATTERN_SV_DEFAULT,
    S_WAVE_PHASES,
    VALID_WAVE_MODES,
    normalize_wave_mode,
    phase_radiation_pattern,
    resolve_radiation_pattern,
    wave_mode_has_p,
    wave_mode_has_s,
    wave_mode_phases,
    wave_mode_s_phases,
)


class TestNormalizeWaveMode:
    @pytest.mark.parametrize("mode", VALID_WAVE_MODES)
    def test_accepts_all_valid_modes(self, mode):
        assert normalize_wave_mode(mode) == mode

    @pytest.mark.parametrize("given,expected", [
        ("p", "P"), (" ps ", "PS"), ("sv", "SV"), ("Sh", "SH"), ("s", "S"),
    ])
    def test_case_and_whitespace_insensitive(self, given, expected):
        assert normalize_wave_mode(given) == expected

    @pytest.mark.parametrize("mode", ["", "X", "PSV", "P S", None])
    def test_rejects_invalid(self, mode):
        with pytest.raises(ValueError):
            normalize_wave_mode(mode)


class TestWaveModeExpansion:
    @pytest.mark.parametrize("mode,phases", [
        ("P", ("P",)),
        ("SV", ("SV",)),
        ("SH", ("SH",)),
        ("S", ("SV", "SH")),
        ("PS", ("P", "SV", "SH")),
    ])
    def test_phases(self, mode, phases):
        assert wave_mode_phases(mode) == phases

    @pytest.mark.parametrize("mode,has_p,has_s", [
        ("P", True, False),
        ("SV", False, True),
        ("SH", False, True),
        ("S", False, True),
        ("PS", True, True),
    ])
    def test_branch_predicates(self, mode, has_p, has_s):
        assert wave_mode_has_p(mode) is has_p
        assert wave_mode_has_s(mode) is has_s

    def test_s_phases_subset(self):
        assert wave_mode_s_phases("PS") == S_WAVE_PHASES
        assert wave_mode_s_phases("P") == ()
        assert wave_mode_s_phases("SV") == ("SV",)


class TestRadiationPattern:
    def test_rms_values(self):
        """RMS radiation-pattern magnitudes over the focal sphere of a double couple."""
        assert phase_radiation_pattern("P") == pytest.approx(np.sqrt(4 / 15), rel=1e-12)
        assert phase_radiation_pattern("SV") == pytest.approx(np.sqrt(7 / 30), rel=1e-12)
        assert phase_radiation_pattern("SH") == pytest.approx(np.sqrt(1 / 6), rel=1e-12)

    def test_rounded_values(self):
        assert phase_radiation_pattern("P") == pytest.approx(0.52, abs=5e-3)
        assert phase_radiation_pattern("SV") == pytest.approx(0.48, abs=5e-3)
        assert phase_radiation_pattern("SH") == pytest.approx(0.41, abs=5e-3)

    def test_sv_and_sh_combine_to_the_combined_s_value(self):
        """<R_SV^2> + <R_SH^2> = 2/5, so the combined S value is sqrt(2/5) ~ 0.63."""
        combined = np.sqrt(RAD_PATTERN_SV_DEFAULT**2 + RAD_PATTERN_SH_DEFAULT**2)
        assert combined == pytest.approx(np.sqrt(2 / 5), rel=1e-12)
        assert combined == pytest.approx(0.63, abs=3e-3)

    def test_sv_is_more_efficient_than_sh(self):
        assert RAD_PATTERN_SV_DEFAULT > RAD_PATTERN_SH_DEFAULT

    @pytest.mark.parametrize("mode", ["S", "PS"])
    def test_rejects_composite_modes(self, mode):
        with pytest.raises(ValueError):
            phase_radiation_pattern(mode)


class TestResolveRadiationPattern:
    def test_defaults_when_no_override(self):
        for phase in ("P", "SV", "SH"):
            assert resolve_radiation_pattern(phase) == phase_radiation_pattern(phase)

    def test_p_override(self):
        assert resolve_radiation_pattern("P", rad_pattern_p=0.52) == pytest.approx(0.52)
        # An S override must not leak into P
        assert resolve_radiation_pattern("P", rad_pattern_s=0.63) == RAD_PATTERN_P_DEFAULT

    def test_s_override_applies_to_both_s_phases(self):
        """Passing 0.63 reproduces results computed with the combined S value."""
        assert resolve_radiation_pattern("SV", rad_pattern_s=0.63) == pytest.approx(0.63)
        assert resolve_radiation_pattern("SH", rad_pattern_s=0.63) == pytest.approx(0.63)

    def test_dict_takes_precedence(self):
        value = resolve_radiation_pattern("SV", rad_pattern_s=0.63,
                                          rad_patterns={"SV": 0.5})
        assert value == pytest.approx(0.5)
        # Phases absent from the dict fall back to the scalar override
        assert resolve_radiation_pattern("SH", rad_pattern_s=0.63,
                                         rad_patterns={"SV": 0.5}) == pytest.approx(0.63)

    def test_dict_keys_are_normalized(self):
        assert resolve_radiation_pattern("SV", rad_patterns={"sv": 0.4}) == pytest.approx(0.4)

    @pytest.mark.parametrize("bad", [0.0, -0.1, 1.5])
    def test_rejects_out_of_range(self, bad):
        with pytest.raises(ValueError):
            resolve_radiation_pattern("P", rad_pattern_p=bad)

    def test_unity_is_allowed(self):
        assert resolve_radiation_pattern("P", rad_pattern_p=1.0) == pytest.approx(1.0)
