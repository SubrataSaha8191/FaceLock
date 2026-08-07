"""FaceLock main application runner and verification utility."""

import sys
import subprocess
from pathlib import Path

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def get_env() -> dict:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    return env

def run_tests() -> bool:
    """Execute the pytest suite and print status."""
    print("==================================================")
    print("      RUNNING FACELOCK SYSTEM VERIFICATION        ")
    print("==================================================")
    
    env = get_env()
    env["QT_QPA_PLATFORM"] = "offscreen"
    res = subprocess.run([sys.executable, "-m", "pytest", "-v"], env=env)
    return res.returncode == 0


def launch_dashboard() -> None:
    """Launch the main QML Desktop Dashboard application."""
    print("\n==================================================")
    print("         LAUNCHING FACELOCK DASHBOARD UI          ")
    print("==================================================")
    
    env = get_env()
    subprocess.run([sys.executable, "Dashboard/main.py"], env=env)


def main():
    """Main runner entrypoint."""
    # If '--verify-only' is passed, run tests and exit
    if "--verify-only" in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)

    # By default, run tests first, then launch dashboard if they pass
    if run_tests():
        launch_dashboard()
    else:
        print("\n[ERROR] Verification tests failed. Aborting dashboard launch.")
        sys.exit(1)


if __name__ == "__main__":
    main()
