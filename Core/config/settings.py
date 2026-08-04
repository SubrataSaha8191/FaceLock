"""FaceLock system configuration settings schemas."""

from pathlib import Path
from pydantic import BaseModel, Field


class CameraSettings(BaseModel):
    """Configuration options for video capture device."""

    device_id: int = Field(default=0, description="Camera index or ID")
    frame_width: int = Field(default=640, description="Target frame width")
    frame_height: int = Field(default=480, description="Target frame height")
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
        default=0.6, description="Similarity threshold for authentication"
    )
    max_auth_attempts: int = Field(default=3, description="Max failed attempts before lock")
    liveness_required: bool = Field(default=True, description="Enable liveness verification")
    pbkdf2_iterations: int = Field(default=100_000, description="Iterations for key derivation")
    lockout_duration_seconds: int = Field(default=300, description="Lockout cooldown in seconds")
    password_hash_iterations: int = Field(
        default=100_000, description="Iterations for password hashing"
    )


class SystemSettings(BaseModel):
    """Global system configuration settings."""

    data_dir: Path = Field(
        default=Path.home() / ".facelock", description="Root directory for application data"
    )
    db_name: str = Field(default="facelock.db", description="Database file name")
    camera: CameraSettings = Field(default_factory=CameraSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    liveness: LivenessSettings = Field(default_factory=LivenessSettings)

    @property
    def db_path(self) -> Path:
        """Full path to SQLite database."""
        return self.data_dir / self.db_name

    @property
    def audit_log_path(self) -> Path:
        """Full path to audit log file."""
        return self.data_dir / "audit.log"
