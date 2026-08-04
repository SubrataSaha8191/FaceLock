"""Face recognition and similarity matching package."""

from Core.recognition.recognizer_interface import IFeatureExtractor
from Core.recognition.feature_extractor import FeatureExtractor
from Core.recognition.matcher import VectorMatcher

__all__ = ["IFeatureExtractor", "FeatureExtractor", "VectorMatcher"]
