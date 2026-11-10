"""FaceLock system configuration settings schemas."""

from pathlib import Path
from pydantic import BaseModel, Field


class CameraSettings(BaseModel):
    """Configuration options for video capture device."""

    device_id: int = Field(default=0, description="Camera index or ID")
    frame_width: int = Field(default=1280, description="Target frame width")
    frame_height: int = Field(default=720, description="Target frame height")
    fps: int = Field(default=30, description="Target capture FPS")


class LivenessSettings(BaseModel):
    """Configuration for anti-spoofing liveness detection."""

    texture_threshold: float = Field(
        default=15.0, description="Minimum LBP variance for live texture"
    )
    blink_ear_threshold: float = Field(
        default=0.21, description="Eye Aspect Ratio threshold for blink"
    )
    texture_weight: float = Field(default=0.6, description="Weight for texture score")
    blink_weight: float = Field(default=0.4, description="Weight for blink score")
    composite_threshold: float = Field(
        default=0.5, description="Minimum composite liveness score"
    )


class SecuritySettings(BaseModel):
    """Configuration options for security, thresholds, and algorithms."""

    matching_threshold: float = Field(
        default=0.40,
        description="Cosine-similarity threshold for the SFace embedding (0.363 is the "
        "published equal-error point; higher is stricter)",
    )
    required_matches: int = Field(
        default=2, ge=1, le=5,
        description="Matching frames (of the last three) needed to unlock",
    )
    auth_timeout_seconds: float = Field(
        default=6.0, ge=1.0, le=20.0,
        description="How long one unlock attempt keeps looking at the camera",
    )
    min_face_px: int = Field(
        default=70, ge=30, description="Smallest face width (pixels) accepted when unlocking"
    )
    detector_score_threshold: float = Field(
        default=0.7, ge=0.3, le=0.99, description="Minimum face-detector confidence"
    )
    adaptive_learning: bool = Field(
        default=True,
        description="Add strong, confident unlock frames to the template so it follows "
        "gradual changes (lighting, glasses, haircut)",
    )
    max_auth_attempts: int = Field(default=3, description="Max failed attempts before lock")
    liveness_required: bool = Field(default=True, description="Enable liveness verification")
    pbkdf2_iterations: int = Field(default=100_000, description="Iterations for key derivation")
    lockout_duration_seconds: int = Field(default=300, description="Lockout cooldown in seconds")
    password_hash_iterations: int = Field(
        default=100_000, description="Iterations for password hashing"
    )


def get_default_data_dir() -> Path:
    import os
    if "FACELOCK_DATA_DIR" in os.environ: return Path(os.environ["FACELOCK_DATA_DIR"])
    if os.geteuid() == 0 or Path.home() == Path("/root"):
        u = os.environ.get("SUDO_USER") or os.environ.get("DOAS_USER")
        if u and (Path("/home") / u).exists(): return Path("/home") / u / ".facelock"
        homes = [h for h in Path("/home").glob("*") if h.is_dir() and not h.name.startswith(".")]
        if homes: return homes[0] / ".facelock"
    return Path.home() / ".facelock"

CONFIG_VERSION = 2  # 2 = SFace deep-embedding thresholds


class SystemSettings(BaseModel):
    """Global system configuration settings."""

    config_version: int = Field(default=CONFIG_VERSION, description="Settings schema version")
    data_dir: Path = Field(
        default_factory=get_default_data_dir, description="Root directory for application data"
    )
    db_name: str = Field(default="facelock.db", description="Database file name")
    camera: CameraSettings = Field(default_factory=CameraSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    liveness: LivenessSettings = Field(default_factory=LivenessSettings)
    protected_apps: list = Field(default_factory=lambda: [
        {"id": "app_1", "name": "Terminal (sudo)", "cmd": "sudo", "icon": "terminal"},
        {"id": "app_2", "name": "Google Chrome", "cmd": "google-chrome", "icon": "browser"},
        {"id": "app_3", "name": "System Settings", "cmd": "gnome-control-center", "icon": "settings"}
    ])

    @property
    def db_path(self) -> Path:
        """Full path to SQLite database."""
        return self.data_dir / self.db_name

    @property
    def audit_log_path(self) -> Path:
        """Full path to audit log file."""
        return self.data_dir / "audit.log"
