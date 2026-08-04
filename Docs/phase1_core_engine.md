# Phase 1: Core AI Engine Specification

## Overview
Phase 1 delivers the fundamental building blocks of FaceLock: frame acquisition, face detection, feature extraction, similarity matching, encrypted storage, and high-level authentication workflow.

## Component Responsibilities

1. **`Core.camera`**: Captures raw frames from hardware webcams via OpenCV with graceful fallback and frame scaling.
2. **`Core.detection`**: Locates human faces within frames using Haar Cascades / DNN models and returns bounding boxes.
3. **`Core.recognition`**:
   - `feature_extractor`: Normalizes cropped face regions and generates facial feature vectors/embeddings.
   - `matcher`: Computes cosine distance or Euclidean distance between feature vectors.
4. **`Core.encryption`**: AES-GCM encryption engine for encrypting and decrypting embedding vectors.
5. **`Core.storage`**: SQLite database storing encrypted user templates, salts, and metadata.
6. **`Core.authentication`**: Orchestrates the multi-stage authentication pipeline.

## Flow Diagram

```text
[ Camera Frame ] ---> [ Detection ] ---> [ Feature Extractor ] ---> Vector
                                                                       |
[ Encrypted DB ] ---> [ Key Decrypt ] ---> [ Template Vector ] --------+
                                                                       |
                                                                       v
[ Auth Result ] <--- [ Pass / Fail Threshold ] <--- [ Vector Matcher ]
```
