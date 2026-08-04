"""Liveness detection package for anti-spoofing."""

from Core.liveness.liveness_result import LivenessResult
from Core.liveness.liveness_interface import ILivenessDetector
from Core.liveness.texture_analyzer import TextureAnalyzer
from Core.liveness.blink_detector import BlinkDetector
from Core.liveness.composite_liveness import CompositeLiveness

__all__ = [
    "LivenessResult",
    "ILivenessDetector",
    "TextureAnalyzer",
    "BlinkDetector",
    "CompositeLiveness",
]
