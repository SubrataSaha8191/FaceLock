# 🔒 FaceLock
**A modern, system-wide biometric facial authentication platform for Linux.**

FaceLock replaces your traditional passwords with lightning-fast, highly secure facial recognition. It integrates deeply into the Linux OS via PAM (Pluggable Authentication Modules), allowing you to authenticate `sudo` commands, unlock your GDM lock screen, and protect sensitive desktop applications using just your face.

## 🌟 Features
- **Works from any angle**: guided Face ID-style enrollment captures you from nine head directions, and unlock accepts any of them, in dim light too.
- **Deep face recognition**: YuNet detector + SFace embeddings (replaces the old Haar-cascade/thumbnail matcher).
- **OS Integration (PAM)**: Works natively with `sudo`, lock screens (GDM/LightDM), and `polkit`.
- **Application Gate**: Protect sensitive apps (like OBS or Chrome) from unauthorized access.
- **Liveness Detection**: Anti-spoofing technology ensures attackers can't bypass it with a photo.
- **Dashboard UI**: A Material-style desktop dashboard with a guided enrollment ring, live detector view, one-click unlock test, and settings.
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

The face models (about 39 MB) ship in `Models/`. If they are missing, fetch and verify them with:
```bash
python3 Scripts/fetch_models.py
```

### 2. Launch the Dashboard to Enroll
Before activating OS authentication, you must enroll your face!
```bash
python3 run.py
```
* Open **Enroll**, enter your details, then look at the camera and slowly move your head in a circle until the ring fills in (about 20 seconds).
* Use **Unlock → Test unlock** to try it before turning on OS integration.
* **Upgrading from an older version?** Profiles made with the old matcher can't be used with the new models. Enroll again, then restart the service (`sudo systemctl restart facelock`, or however you started `Service/auth/auth_service.py`). Until you re-enroll, sudo and the lock screen simply fall back to your password.
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
- `facelock.authenticate_detailed(user_id=None)`: Same, but returns the reason and score for a failure.
- `facelock.is_enrolled(user_id=None)`: Returns `True` if the user has a usable facial profile.
- `facelock.is_available()`: Returns `True` if the service is reachable.

*(Note: The FaceLock background daemon must be installed and running via `install_pam.sh` for the API to work securely without hogging camera resources).*


---

## 🛠 Troubleshooting unlock

| Symptom | Try |
|---|---|
| "Couldn't see your face" | Open **Live view** to see what the camera sees; face a light source, not a window behind you |
| Rejected at an angle | Re-run enrollment in the lighting where you usually unlock; check all nine ring segments filled |
| Still rejected sometimes | **Settings → Match strictness**: lower it a few points (keep liveness on) |
| Slow to unlock | Raise nothing: the service stops as soon as it is sure. Lower **Unlock window** only if failed attempts feel too long |

See [Docs/face_capture_pipeline.md](Docs/face_capture_pipeline.md) for how detection, enrollment and matching work.
