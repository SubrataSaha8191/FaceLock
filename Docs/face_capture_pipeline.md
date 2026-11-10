# Face capture pipeline

## Why the previous version failed often

- **Detection:** OpenCV's frontal Haar cascade finds almost nothing once the head turns, tilts or the light changes.
- **Recognition:** the "embedding" was a 16x8 grayscale thumbnail of the crop. A small pose or lighting shift moves that thumbnail far from the enrolled one. Because the vectors are all-positive, unrelated faces also scored high (a different person scored 0.78 against a 0.6 threshold in testing).
- **Enrollment** stored one frame. **Unlock** compared only the last of eight frames grabbed before auto-exposure settled.

## Now

| Stage | What | Where |
|---|---|---|
| Detect | YuNet: finds rotated and small faces, returns 5 landmarks; retried on a low-light-enhanced frame | `Core/detection/yunet_detector.py` |
| Pose | Yaw/pitch/roll from landmarks (`solvePnP`) | `Core/detection/pose.py` |
| Quality | Size, brightness, sharpness, framing, with a human hint | `Core/detection/quality.py` |
| Embed | Landmark-aligned SFace, 128-d, averaged with its mirror image | `Core/recognition/sface_extractor.py` |
| Template | Gallery of embeddings tagged by head direction (up to 48) | `Core/recognition/template.py` |
| Enroll | Centre pose, then eight head-direction sectors | `Core/enrollment/session.py` |
| Unlock | Streams frames for up to the configured window; unlocks on 2 of the last 3 frames matching (or one very strong frame) | `Core/authentication/auth_engine.py` |

### Matching

A probe is scored against the gallery as the mean of its two best template matches (one when
fewer than three exist), so a single odd template can't carry a stranger over the threshold.
The default cosine threshold is **0.40** (the published SFace equal-error point is 0.363);
failed attempts raise it by up to 0.15, and it is adjustable in Settings.

### What counts against you

Only frames that were actually compared and failed (or failed liveness) count toward lockout, and
once per attempt, not once per frame. No face in view, bad light or a blurry frame never lock you out.

### Adaptive learning

When a frame matches strongly (>= 0.55) but looks different from every stored template
(similarity < 0.90), it is added to the gallery, so the profile follows gradual changes. Disable it in Settings.

### Storage

Templates are AES-256-GCM encrypted. Storage records a `template_format` (1 = old thumbnail,
2 = gallery); format 1 profiles report `re_enroll_required` and PAM falls back to the password.

## Limits

- Liveness is still the lightweight texture check. A good-quality screen replay or printed photo
  is not reliably rejected by an RGB webcam alone; an IR/depth camera or a trained
  presentation-attack model would be needed for that.
- Pose estimation uses a generic 3D head model, so angles are approximate (good for guiding
  enrollment, not for measurement).
