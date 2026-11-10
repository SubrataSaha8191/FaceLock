# Changelog

## 2.0.0

### Recognition accuracy
- Replaced the Haar-cascade detector and thumbnail "embedding" with YuNet detection and SFace deep embeddings.
- Guided multi-angle enrollment (centre + eight head-direction sectors) with quality gating and pose guidance.
- Unlock now streams frames over a short window with a two-of-three consensus, instead of judging one frame.
- Low-light enhancement, higher capture resolution (1280x720 MJPG), camera auto-exposure settling.
- Optional adaptive learning of confident unlocks.
- Unlock failures now report a reason (`no_face`, `low_quality`, `mismatch`, ...); only real mismatches count toward lockout.

### Dashboard
- Full redesign: Material-style UI with the four-colour palette, original logo and SVG illustrations, light/dark themes.
- Face-ring enrollment, one-click unlock test, live detector view with pose and quality readout.

### Migration
- Old thumbnail profiles must be re-enrolled; until then PAM falls back to the password.
- `matching_threshold` is migrated from the old ~0.6 scale to the new 0.40 default (config version 2).

### Other
- Service reloads settings without a restart, serialises camera access and tolerates probe connections.
- Tests no longer touch the real `~/.facelock` directory.
