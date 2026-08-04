"""Entry point for FaceLock background authentication service."""

import signal
import sys
from pathlib import Path

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Service.auth.auth_service import AuthService
from Core.utils.logger import get_logger

logger = get_logger("ServiceMain")


def main() -> None:
    """Start the FaceLock auth service daemon."""
    service = AuthService()

    def _handle_shutdown(signum, frame):
        logger.info("Shutdown signal received.")
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    logger.info("Starting FaceLock Authentication Service...")
    service.start()


if __name__ == "__main__":
    main()
