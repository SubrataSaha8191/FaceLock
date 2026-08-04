"""Unit tests for risk evaluator and adaptive threshold."""

from Core.authentication.risk_evaluator import RiskEvaluator


def test_zero_risk_base_threshold():
    evaluator = RiskEvaluator(base_threshold=0.6, max_threshold=0.85)
    threshold = evaluator.get_adjusted_threshold(failed_attempts=0, liveness_confidence=1.0)
    # With zero risk, threshold should be near the base
    assert abs(threshold - 0.6) < 0.1


def test_high_failure_raises_threshold():
    evaluator = RiskEvaluator(base_threshold=0.6, max_threshold=0.85)
    low_risk = evaluator.get_adjusted_threshold(failed_attempts=0, liveness_confidence=1.0)
    high_risk = evaluator.get_adjusted_threshold(failed_attempts=5, liveness_confidence=1.0)
    assert high_risk > low_risk


def test_low_liveness_raises_threshold():
    evaluator = RiskEvaluator(base_threshold=0.6, max_threshold=0.85)
    confident = evaluator.get_adjusted_threshold(failed_attempts=0, liveness_confidence=1.0)
    uncertain = evaluator.get_adjusted_threshold(failed_attempts=0, liveness_confidence=0.2)
    assert uncertain > confident


def test_threshold_never_exceeds_max():
    evaluator = RiskEvaluator(base_threshold=0.6, max_threshold=0.85)
    threshold = evaluator.get_adjusted_threshold(failed_attempts=100, liveness_confidence=0.0)
    assert threshold <= 0.85


def test_risk_score_range():
    evaluator = RiskEvaluator()
    score = evaluator.compute_risk_score(failed_attempts=3, liveness_confidence=0.5)
    assert 0.0 <= score <= 1.0
