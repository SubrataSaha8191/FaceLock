"""Main entry point for FaceLock Web Desktop Dashboard application."""

import sys
from pathlib import Path

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Dashboard.web_bridge import FaceLockWebBridge
import webview


def main() -> int:
    """Launch PyWebView Desktop Dashboard Application."""
    if "--test-mode" in sys.argv:
        print("Test mode load successful.")
        return 0

    api = FaceLockWebBridge()
    html_file = Path(__file__).parent / "web" / "index.html"

    window = webview.create_window(
        title="FaceLock",
        url=str(html_file.resolve()),
        js_api=api,
        width=1240,
        height=780,
        min_size=(820, 620),
        background_color="#F8FAFD",
    )

    webview.start(gui="qt", debug=False)
    return 0



if __name__ == "__main__":
    sys.exit(main())
