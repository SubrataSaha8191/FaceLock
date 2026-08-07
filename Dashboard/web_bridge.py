
import base64, json, os, sys, subprocess, cv2, numpy as np
from pathlib import Path
from typing import Any, Dict, List
from Core.config.settings import SystemSettings
from Core.config.loader import ConfigLoader
from Core.camera.opencv_camera import OpenCVCamera
from Core.detection.cascade_detector import CascadeDetector
from Core.recognition.feature_extractor import FeatureExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine
from Core.liveness.texture_analyzer import TextureAnalyzer
from Core.utils.audit_logger import AuditLogger
from Linux.desktop_interceptor import install_gate, uninstall_gate, ensure_autostart

class FaceLockWebBridge:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.settings: SystemSettings = self.config_loader.load()
        self.storage = EncryptedSQLiteStorage(self.settings.db_path)
        self.camera = OpenCVCamera(self.settings.camera)
        self.detector = CascadeDetector()
        self.extractor = FeatureExtractor()
        self.liveness = TextureAnalyzer(self.settings.liveness.texture_threshold)
        self.audit = AuditLogger(self.settings.audit_log_path)
        self.engine = AuthenticationEngine(self.settings, self.detector, self.extractor, self.storage, self.liveness)
        self._camera_active = False
        self._start_daemon(); ensure_autostart()

    def get_users(self) -> List[Dict[str, Any]]:
        return [{"userId": u[0], "username": u[1]} for u in self.storage.get_all_users()]

    def get_metrics(self) -> Dict[str, Any]:
        return {"registeredUsersCount": len(self.storage.get_all_users()), "cameraActive": self._camera_active, "livenessEnabled": self.settings.security.liveness_required, "matchingThreshold": self.settings.security.matching_threshold, "daemonActive": True, "socketPath": str(self.settings.data_dir / "facelock.sock")}

    def save_settings(self, matching_threshold: float, liveness_enabled: bool) -> Dict[str, Any]:
        self.settings.security.matching_threshold = float(matching_threshold)
        self.settings.security.liveness_required = bool(liveness_enabled)
        self.config_loader.save(self.settings)
        return {"ok": True}

    def get_logs(self) -> List[Dict[str, Any]]:
        log_file = Path(self.settings.audit_log_path)
        if not log_file.exists(): return []
        records = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        records.append({"event": d.get("event", "UNKNOWN"), "user": d.get("user_id", "system"), "status": "OK" if d.get("success", True) else "FAIL", "ts": d.get("timestamp", "").split("T")[-1][:8] if "timestamp" in d else "--:--:--"})
        except Exception: pass
        return records[-20:]

    def enroll_user(self, user_id: str, name: str, secret: str) -> Dict:
        if not self.camera.is_opened(): self.camera.open()
        ret, frame = self.camera.read_frame()
        if not ret or frame is None: return {"ok": False, "msg": "Camera capture failed"}
        ok = self.engine.enroll_user(user_id, name, "MasterKey123", frame, secret or "MasterKey123")
        return {"ok": ok, "msg": f"'{name}' enrolled" if ok else "Enrollment failed"}

    def delete_user(self, user_id: str) -> Dict:
        ok = self.storage.delete_user(user_id)
        if ok: self.audit.log_event("IDENTITY_DELETED", user_id=user_id, success=True)
        return {"ok": ok, "msg": f"'{user_id}' deleted" if ok else "Delete failed"}

    def update_user(self, old_user_id: str, new_user_id: str, new_name: str) -> Dict:
        ok = self.storage.update_identity(old_user_id, new_user_id, new_name)
        if ok: self.audit.log_event("IDENTITY_UPDATED", user_id=new_user_id, success=True)
        return {"ok": ok, "msg": f"Identity '{new_name}' updated" if ok else "Update failed"}

    def clear_logs(self) -> Dict:
        try:
            lf = Path(self.settings.audit_log_path)
            if lf.exists(): lf.write_text("", encoding="utf-8")
            return {"ok": True}
        except Exception as e: return {"ok": False, "msg": str(e)}

    def get_system_installed_apps(self) -> List[Dict[str, str]]:
        import glob, configparser
        apps, seen = [], set()
        for p in ['/usr/share/applications', os.path.expanduser('~/.local/share/applications'), '/var/lib/snap/desktop/applications', '/var/lib/flatpak/exports/share/applications']:
            for f in glob.glob(os.path.join(p, '*.desktop')):
                try:
                    cp = configparser.ConfigParser(interpolation=None)
                    cp.read(f, encoding='utf-8')
                    if cp.has_section('Desktop Entry') and cp['Desktop Entry'].get('NoDisplay', 'false').lower() != 'true' and cp['Desktop Entry'].get('X-FaceLock-Protected', '') != 'true':
                        n, e = cp['Desktop Entry'].get('Name'), cp['Desktop Entry'].get('Exec')
                        if n and e and n not in seen:
                            seen.add(n)
                            c = ' '.join([a for a in e.split() if not a.startswith('%')])
                            kw = cp['Desktop Entry'].get('Keywords', '') + ' ' + cp['Desktop Entry'].get('Comment', '') + ' ' + cp['Desktop Entry'].get('Categories', '')
                            full = f"{f} {n} {e} {kw}".lower()
                            ic = "code" if any(x in full for x in ["code", "vscode", "studio", "texteditor", "ide", "sublime", "atom"]) else "browser" if any(x in full for x in ["browser", "chrome", "firefox", "brave", "edge"]) else "terminal" if any(x in full for x in ["terminal", "konsole", "cmd", "bash"]) else "settings" if any(x in full for x in ["setting", "control-center", "preference"]) else "media" if any(x in full for x in ["media", "player", "vlc", "spotify", "music"]) else "security" if any(x in full for x in ["burp", "wireshark", "security"]) else "app"
                            apps.append({"name": n, "cmd": c, "icon": ic, "kw": kw})
                except Exception: pass
        apps.sort(key=lambda x: x['name'].lower())
        return apps

    def get_protected_apps(self) -> List[Dict[str, Any]]:
        return getattr(self.settings, "protected_apps", [])

    def add_protected_app(self, name: str, cmd: str, icon: str) -> Dict[str, Any]:
        aid = f"app_{len(self.get_protected_apps()) + 1}"
        apps = list(self.get_protected_apps()) + [{"id": aid, "name": name, "cmd": cmd, "icon": icon or "app"}]
        self.settings.protected_apps = apps
        self.config_loader.save(self.settings)
        install_gate(name, cmd)
        return {"ok": True, "msg": f"App '{name}' protected — OS launcher intercepted"}

    def remove_protected_app(self, app_id: str) -> Dict[str, Any]:
        removed = next((a for a in self.get_protected_apps() if a.get("id") == app_id), None)
        self.settings.protected_apps = [a for a in self.get_protected_apps() if a.get("id") != app_id]
        self.config_loader.save(self.settings)
        if removed: uninstall_gate(removed.get("cmd", ""))
        return {"ok": True, "msg": "App protection removed — OS launcher restored"}

    def launch_protected_app(self, app_id: str) -> Dict[str, Any]:
        apps = {a.get("id"): a for a in self.get_protected_apps()}
        if app_id in apps:
            users = self.get_users()
            u_arg = ["--user", users[0]["userId"]] if users else []
            gate_path = Path(__file__).resolve().parent.parent / "Linux" / "bin" / "facelock-app-gate"
            subprocess.Popen([sys.executable, str(gate_path), "--cmd", apps[app_id]["cmd"]] + u_arg)
            return {"ok": True, "msg": f"Gate engaged for '{apps[app_id]['name']}'"}
        return {"ok": False, "msg": "App not found"}

    def toggle_camera(self, enable: bool) -> Dict:
        if enable: self._camera_active = self.camera.open(); return {"ok": self._camera_active}
        self.camera.release(); self._camera_active = False; return {"ok": True}

    def get_camera_frame(self) -> str:
        if not self.camera.is_opened(): return ""
        ret, frame = self.camera.read_frame()
        if not ret or frame is None: return ""
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return f"data:image/jpeg;base64,{base64.b64encode(buf).decode('ascii')}"

    def _start_daemon(self):
        import socket as sock
        try: s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM); s.connect("/tmp/facelock.sock"); s.close()
        except Exception: subprocess.Popen([sys.executable, str(Path(__file__).resolve().parent.parent / "Service" / "auth" / "auth_service.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
