"""Risk evaluator for adaptive security threshold adjustment."""

from datetime import datetime


class RiskEvaluator:
    """Computes a dynamic risk score to adjust authentication thresholds.

    Higher risk raises the effective matching threshold, requiring
    stronger similarity for authentication to pass.
    """

    def __init__(self, base_threshold: float = 0.6, max_threshold: float = 0.85):
        self.base_threshold = base_threshold
        self.max_threshold = max_threshold

    def compute_risk_score(
        self,
        failed_attempts: int,
        liveness_confidence: float = 1.0,
    ) -> float:
        """Return risk score between 0.0 (safe) and 1.0 (high risk)."""
        # Factor 1: Consecutive failures increase risk
        failure_risk = min(failed_attempts / 5.0, 1.0)

        # Factor 2: Low liveness confidence increases risk
        liveness_risk = max(0.0, 1.0 - liveness_confidence)

        # Factor 3: Unusual hour access (midnight to 5 AM)
        hour = datetime.now().hour
        time_risk = 0.3 if 0 <= hour < 5 else 0.0

        # Weighted combination
        risk = (failure_risk * 0.4) + (liveness_risk * 0.4) + (time_risk * 0.2)
        return min(risk, 1.0)

    def get_adjusted_threshold(
        self,
        failed_attempts: int,
        liveness_confidence: float = 1.0,
    ) -> float:
        """Return elevated matching threshold based on current risk."""
        risk = self.compute_risk_score(failed_attempts, liveness_confidence)
        adjusted = self.base_threshold + risk * (self.max_threshold - self.base_threshold)
        return min(adjusted, self.max_threshold)
