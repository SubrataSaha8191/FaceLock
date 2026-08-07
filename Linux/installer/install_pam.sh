#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# FaceLock Systemd Service & PAM OS Integration Installer
# ═══════════════════════════════════════════════════════════════════════════

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PAM_HELPER="$PROJECT_ROOT/Linux/pam/pam_facelock.py"
SERVICE_DAEMON="$PROJECT_ROOT/Service/auth/auth_service.py"
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

if [ "$EUID" -ne 0 ]; then
    echo "[!] Root privileges required to configure systemd and /etc/pam.d/."
    echo "[!] Please run: sudo bash Linux/installer/install_pam.sh"
    exit 1
fi

chmod +x "$PAM_HELPER"
chmod +x "$SERVICE_DAEMON"

# 1. Install & Enable Systemd Background Service (Auto-starts on OS boot)
SERVICE_FILE="/etc/systemd/system/facelock.service"
echo "[+] Installing systemd service: $SERVICE_FILE..."
cat << EOF > "$SERVICE_FILE"
[Unit]
Description=FaceLock Biometric Socket Daemon
After=network.target

[Service]
Type=simple
User=root
ExecStart=$PYTHON_BIN $SERVICE_DAEMON
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable facelock.service
systemctl restart facelock.service
echo "[✓] FaceLock systemd background service active & enabled on boot!"

# 2. Inject FaceLock into PAM Configuration Stack
PAM_RULE="auth sufficient pam_exec.so $PYTHON_BIN $PAM_HELPER"

install_pam_target() {
    local target="$1"
    local pam_file="/etc/pam.d/$target"
    if [ -f "$pam_file" ]; then
        sed -i '/pam_facelock.py/d' "$pam_file"
        echo "[+] Injecting FaceLock into $pam_file..."
        sed -i "1a $PAM_RULE" "$pam_file"
        echo "[✓] Successfully updated $pam_file"
    fi
}

install_pam_target "sudo"
install_pam_target "gdm-password"
install_pam_target "lightdm"
install_pam_target "polkit-1"

echo "=================================================="
echo " FACELOCK OS AUTHENTICATION SUCCESSFULLY INSTALLED!"
echo " FaceLock is now running on boot for: sudo, lockscreen, polkit"
echo "=================================================="
