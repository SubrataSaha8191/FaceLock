# 🔒 FaceLock
**A modern, system-wide biometric facial authentication platform for Linux.**

FaceLock replaces your traditional passwords with lightning-fast, highly secure facial recognition. It integrates deeply into the Linux OS via PAM (Pluggable Authentication Modules), allowing you to authenticate `sudo` commands, unlock your GDM lock screen, and protect sensitive desktop applications using just your face.

## 🌟 Features
- **OS Integration (PAM)**: Works natively with `sudo`, lock screens (GDM/LightDM), and `polkit`.
- **Application Gate**: Protect sensitive apps (like OBS or Chrome) from unauthorized access.
- **Liveness Detection**: Anti-spoofing technology ensures attackers can't bypass it with a photo.
- **Dashboard UI**: A sleek, modern Chromium-based web dashboard to manage identities, view metrics, and configure settings.
- **Python Developer API**: Embed FaceLock directly into your own Python applications!

---

## 🚀 Installation & Setup

If you have just cloned or downloaded this repository, follow these steps to get FaceLock running:

### 1. Setup the Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/FaceLock.git
cd FaceLock

# Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Launch the Dashboard to Enroll
Before activating OS authentication, you must enroll your face!
```bash
python3 run.py
```
* Navigate to the **Enrollment** tab in the dashboard and capture your face profile.
* After running it once, you can also launch FaceLock directly from your system's Desktop Application Menu!

### 3. Install OS Integration (PAM)
Once enrolled, run the installer to enable system-wide authentication. This will configure the background daemon and inject FaceLock into the OS stack:
```bash
sudo bash Linux/installer/install_pam.sh
```

That's it! Now open a new terminal, type `sudo echo "hello"`, and watch the magic happen.

---

## 💻 Developer API

FaceLock isn't just for the OS—it's a full Python library you can use in **any of your own Python projects**! Want to build a high-security admin panel, a sensitive data vault, or a custom biometric captcha?

Just import the `facelock` library!

### Example Usage:

```python
import facelock

try:
    print("Looking for admin face...")
    
    # This automatically triggers the camera and verifies against the fast background daemon
    if facelock.authenticate():
        print("✅ Access Granted: Welcome Admin!")
        # Proceed with sensitive operations...
    else:
        print("❌ Access Denied: Face did not match.")
        
except ValueError as e:
    print(f"User is not enrolled: {e}")
```

### Available Methods:
- `facelock.authenticate(user_id=None)`: Triggers face capture and returns `True` if it matches.
- `facelock.is_enrolled(user_id=None)`: Returns `True` if the user has an enrolled facial profile.

*(Note: The FaceLock background daemon must be installed and running via `install_pam.sh` for the API to work securely without hogging camera resources).*
