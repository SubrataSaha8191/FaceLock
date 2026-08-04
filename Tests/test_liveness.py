"""Unit tests for liveness detection modules."""

import numpy as np
from Core.liveness.liveness_result import LivenessResult
from Core.liveness.texture_analyzer import TextureAnalyzer
from Core.liveness.composite_liveness import CompositeLiveness
from Core.liveness.liveness_interface import ILivenessDetector


class MockAlwaysLive(ILivenessDetector):
    """Mock detector that always returns live."""
    def check_liveness(self, frame, bbox):
        return LivenessResult(is_live=True, confidence=0.9, method="mock_live")


class MockAlwaysSpoof(ILivenessDetector):
    """Mock detector that always returns spoof."""
    def check_liveness(self, frame, bbox):
        return LivenessResult(is_live=False, confidence=0.1, method="mock_spoof")


def test_liveness_result_str():
    result = LivenessResult(is_live=True, confidence=0.85, method="test")
    assert "LIVE" in str(result)
    result2 = LivenessResult(is_live=False, confidence=0.2, method="test")
    assert "SPOOF" in str(result2)


def test_texture_analyzer_noisy_image():
    analyzer = TextureAnalyzer(variance_threshold=5.0)
    # High-noise image should have high texture variance (live-like)
    frame = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    bbox = (10, 10, 100, 100)
    result = analyzer.check_liveness(frame, bbox)
    assert result.is_live is True
    assert result.confidence > 0.0


def test_texture_analyzer_flat_image():
    analyzer = TextureAnalyzer(variance_threshold=50.0)
    # Flat solid-color image should have very low texture variance (spoof-like)
    frame = np.ones((200, 200, 3), dtype=np.uint8) * 128
    bbox = (10, 10, 100, 100)
    result = analyzer.check_liveness(frame, bbox)
    assert result.is_live is False


def test_composite_liveness_both_live():
    detectors = [MockAlwaysLive(), MockAlwaysLive()]
    composite = CompositeLiveness(detectors, weights=[0.5, 0.5], threshold=0.4)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    result = composite.check_liveness(frame, (0, 0, 50, 50))
    assert result.is_live is True
    assert "composite" in result.method


def test_composite_liveness_mixed():
    detectors = [MockAlwaysLive(), MockAlwaysSpoof()]
    composite = CompositeLiveness(detectors, weights=[0.5, 0.5], threshold=0.7)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    result = composite.check_liveness(frame, (0, 0, 50, 50))
    # (0.9 * 0.5) + (0.1 * 0.5) = 0.5, below 0.7 threshold
    assert result.is_live is False
