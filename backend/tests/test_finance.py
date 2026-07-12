"""
Boundary-value tests for backend/advisory/finance.py's pure goal-math /
suitability functions. No network calls, no customer data files required.
"""
import pytest

from advisory.finance import (
    future_value_of_lumpsum,
    score_suitability,
    sip_required_for_target,
)


# ---------------------------------------------------------------------------
# future_value_of_lumpsum
# ---------------------------------------------------------------------------
class TestFutureValueOfLumpsum:
    def test_zero_years_returns_present_value_unchanged(self):
        # Boundary: years == 0 -> no growth should be applied at all.
        assert future_value_of_lumpsum(100000, 0.12, 0) == 100000

    def test_zero_rate_returns_present_value_unchanged(self):
        # Boundary: annual_rate == 0 -> no growth regardless of years.
        assert future_value_of_lumpsum(50000, 0.0, 10) == 50000

    def test_positive_growth_compounds(self):
        result = future_value_of_lumpsum(100000, 0.10, 1)
        assert result == pytest.approx(110000)


# ---------------------------------------------------------------------------
# sip_required_for_target
# ---------------------------------------------------------------------------
class TestSipRequiredForTarget:
    def test_current_progress_already_meets_target_returns_zero(self):
        # Boundary: current_progress's future value == target_amount exactly
        # -> remaining_target is 0 -> no further SIP needed.
        target = future_value_of_lumpsum(500000, 0.10, 5)
        sip = sip_required_for_target(target_amount=target, current_progress=500000, years=5, annual_rate=0.10)
        assert sip == 0.0

    def test_current_progress_exceeds_target_returns_zero_not_negative(self):
        # Boundary: current_progress's future value overshoots target ->
        # remaining_target is clamped at 0, never negative.
        target = future_value_of_lumpsum(500000, 0.10, 5)
        sip = sip_required_for_target(target_amount=target - 1, current_progress=500000, years=5, annual_rate=0.10)
        assert sip == 0.0

    def test_zero_rate_uses_simple_division(self):
        # Boundary: annual_rate == 0 hits the monthly_rate == 0 branch, which
        # is a plain division rather than the annuity-due formula.
        sip = sip_required_for_target(target_amount=120000, current_progress=0, years=1, annual_rate=0.0)
        assert sip == 10000.0

    def test_positive_rate_produces_a_positive_sip_below_naive_estimate(self):
        # With growth, the required monthly SIP should be less than the naive
        # (no-growth) estimate of target / months.
        sip = sip_required_for_target(target_amount=1000000, current_progress=0, years=10, annual_rate=0.10)
        naive = 1000000 / (10 * 12)
        assert 0 < sip < naive


# ---------------------------------------------------------------------------
# score_suitability
# ---------------------------------------------------------------------------
def _answers(values: list[int]) -> dict:
    assert len(values) == 10
    return {str(i + 1): v for i, v in enumerate(values)}


class TestScoreSuitability:
    def test_just_below_conservative_moderate_boundary(self):
        # total = 13 -> pct = 0.325, strictly below the 0.35 cutoff -> Conservative.
        answers = _answers([1, 1, 1, 1, 1, 1, 1, 1, 1, 4])
        result = score_suitability(answers)
        assert result["score"] == 13
        assert result["risk_profile"] == "Conservative"

    def test_exactly_at_conservative_moderate_boundary(self):
        # total = 14 -> pct = 0.35 exactly. The cutoff is "< 0.35", so exactly
        # 0.35 falls into Moderate, not Conservative.
        answers = _answers([1, 1, 1, 1, 1, 1, 1, 1, 3, 3])
        result = score_suitability(answers)
        assert result["score"] == 14
        assert result["risk_profile"] == "Moderate"

    def test_just_below_moderate_aggressive_boundary(self):
        # total = 25 -> pct = 0.625, strictly below the 0.65 cutoff -> Moderate.
        answers = _answers([3, 3, 3, 3, 3, 2, 2, 2, 2, 2])
        result = score_suitability(answers)
        assert result["score"] == 25
        assert result["risk_profile"] == "Moderate"

    def test_exactly_at_moderate_aggressive_boundary(self):
        # total = 26 -> pct = 0.65 exactly -> Aggressive (cutoff is "< 0.65").
        answers = _answers([3, 3, 3, 3, 3, 3, 2, 2, 2, 2])
        result = score_suitability(answers)
        assert result["score"] == 26
        assert result["risk_profile"] == "Aggressive"

    def test_missing_answers_default_to_midpoint(self):
        # Undefined question ids default to option index 2 (neutral midpoint).
        result = score_suitability({})
        assert result["score"] == 20  # 10 questions * default idx 2
        assert result["risk_profile"] == "Moderate"

    def test_out_of_range_index_is_clamped(self):
        # idx values outside 0-4 should be clamped, not raise or skew wildly.
        answers = _answers([99, -5, 2, 2, 2, 2, 2, 2, 2, 2])
        result = score_suitability(answers)
        # 99 clamps to 4, -5 clamps to 0, rest are 2*8 = 16 -> total 20.
        assert result["score"] == 4 + 0 + 16
