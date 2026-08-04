"""Unit tests for face detection, feature extraction, and matcher."""

import numpy as np
from Core.detection.cascade_detector import CascadeDetector
from Core.recognition.feature_extractor import FeatureExtractor
from Core.recognition.matcher import VectorMatcher


def test_cascade_detector_empty_frame():
    detector = CascadeDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    faces = detector.detect_faces(frame)
    assert isinstance(faces, list)


def test_feature_extractor():
    extractor = FeatureExtractor()
    frame = np.ones((200, 200, 3), dtype=np.uint8) * 128
    bbox = (20, 20, 100, 100)
    embedding = extractor.extract_embedding(frame, bbox)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (128,)
    # Norm of non-zero extracted vector should be ~1.0
    assert abs(np.linalg.norm(embedding) - 1.0) < 1e-4


def test_vector_matcher():
    matcher = VectorMatcher()
    v1 = np.ones(128, dtype=np.float32) / np.sqrt(128)
    v2 = np.ones(128, dtype=np.float32) / np.sqrt(128)
    v3 = -v1

    assert abs(matcher.cosine_similarity(v1, v2) - 1.0) < 1e-5
    assert abs(matcher.cosine_similarity(v1, v3) - (-1.0)) < 1e-5
    assert matcher.is_match(v1, v2, threshold=0.6) is True
    assert matcher.is_match(v1, v3, threshold=0.6) is False
