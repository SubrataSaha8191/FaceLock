#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# FaceLock PAM & Application Authentication Installer for Linux
# ═══════════════════════════════════════════════════════════════════════════

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PAM_HELPER="$PROJECT_ROOT/Linux/pam/pam_facelock.py"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python3"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(which python3)"
fi

echo "=================================================="
echo "    FACELOCK OS & APPLICATION AUTH INSTALLER      "
echo "=================================================="
echo "Project Root: $PROJECT_ROOT"
echo "PAM Helper  : $PAM_HELPER"
echo "Python Bin  : $PYTHON_BIN"

# Check root privileges for system PAM installation
if [ "$EUID" -ne 0 ]; then
    echo "[!] Root privileges required to configure /etc/pam.d/."
    echo "[!] Please run: sudo bash Linux/installer/install_pam.sh"
    exit 1
fi

chmod +x "$PAM_HELPER"

PAM_RULE="auth sufficient pam_exec.so expose_authtok $PYTHON_BIN $PAM_HELPER"

install_pam_target() {
    local target="$1"
    local pam_file="/etc/pam.d/$target"
    if [ -f "$pam_file" ]; then
        if grep -q "pam_facelock.py" "$pam_file"; then
            echo "[✓] FaceLock already configured in $pam_file"
        else
            echo "[+] Injecting FaceLock into $pam_file..."
            sed -i "1a $PAM_RULE" "$pam_file"
            echo "[✓] Successfully updated $pam_file"
        fi
    fi
}

install_pam_target "sudo"
install_pam_target "gdm-password"
install_pam_target "lightdm"
install_pam_target "polkit-1"

echo "=================================================="
echo " FACELOCK OS AUTHENTICATION SUCCESSFULLY INSTALLED!"
echo " FaceLock is now active for: sudo, lockscreen, polkit"
echo "=================================================="
