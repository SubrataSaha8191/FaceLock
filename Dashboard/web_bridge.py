
import base64, getpass, json, os, re, sys, subprocess, cv2, numpy as np
from pathlib import Path
from typing import Any, Dict, List
from Core.config.settings import SystemSettings
from Core.config.loader import ConfigLoader
from Core.camera.opencv_camera import OpenCVCamera
from Core.detection.yunet_detector import YuNetDetector
from Core.recognition.sface_extractor import SFaceExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine
from Core.liveness.texture_analyzer import TextureAnalyzer
from Core.utils.audit_logger import AuditLogger
from Core.enrollment import EnrollmentSession
from Core.utils.icon_resolver import IconResolver
from Core.account import AccountStore, GoogleSignIn, GoogleOAuthError
from Core.detection.quality import assess_face
from Core.camera.enhance import mean_luma
from Linux.desktop_interceptor import install_gate, uninstall_gate, ensure_autostart

class FaceLockWebBridge:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.settings: SystemSettings = self.config_loader.load()
        self.storage = EncryptedSQLiteStorage(self.settings.db_path)
        self.camera = OpenCVCamera(self.settings.camera)
        self.detector = YuNetDetector(score_threshold=self.settings.security.detector_score_threshold)
        self.extractor = SFaceExtractor()
        self.liveness = TextureAnalyzer(self.settings.liveness.texture_threshold)
        self.audit = AuditLogger(self.settings.audit_log_path)
        self.engine = AuthenticationEngine(self.settings, self.detector, self.extractor, self.storage, self.liveness)
        self.account = AccountStore(self.settings.data_dir)
        self._icons = IconResolver()
        self._google = GoogleSignIn(self.account)
        self._camera_active = False
        self._enroll = None
        self._verify = None
        self._verify_user = None
        self._start_daemon(); ensure_autostart()

    def get_users(self) -> List[Dict[str, Any]]:
        out = []
        all_users = self.storage.get_all_users()
        if len(all_users) == 1:
            self._ensure_os_link(all_users[0][0])  # a lone profile is the obvious owner of this account
        for u in self.storage.get_all_users():
            info = self.engine.template_info(u[0], "MasterKey123")
            out.append({
                "userId": u[0], "username": u[1],
                "templateFormat": info.get("format", 0), "templates": info.get("count", 0),
                "poseCoverage": info.get("coverage", 0), "learned": info.get("learned", 0),
                "needsReenroll": info.get("format", 0) < 2,
            })
        return out

    def get_metrics(self) -> Dict[str, Any]:
        sec = self.settings.security
        return {
            "registeredUsersCount": len(self.storage.get_all_users()),
            "cameraActive": self._camera_active,
            "livenessEnabled": sec.liveness_required,
            "matchingThreshold": sec.matching_threshold,
            "adaptiveLearning": sec.adaptive_learning,
            "authTimeout": sec.auth_timeout_seconds,
            "requiredMatches": sec.required_matches,
            "daemonActive": self._daemon_alive(), "daemonCurrent": self._daemon_info()["current"],
            "socketPath": "/tmp/facelock.sock",
            "detector": "YuNet", "recognizer": "SFace 128-d",
        }

    def save_settings(self, matching_threshold: float, liveness_enabled: bool,
                      adaptive_learning: bool = True, auth_timeout: float = 6.0) -> Dict[str, Any]:
        sec = self.settings.security
        sec.matching_threshold = min(0.70, max(0.25, float(matching_threshold)))
        sec.liveness_required = bool(liveness_enabled)
        sec.adaptive_learning = bool(adaptive_learning)
        sec.auth_timeout_seconds = min(20.0, max(1.0, float(auth_timeout)))
        self.config_loader.save(self.settings)
        self.engine.apply_settings(self.settings)
        return {"ok": True, "msg": "Settings saved. The unlock service picks them up automatically."}

    def get_logs(self) -> List[Dict[str, Any]]:
        log_file = Path(self.settings.audit_log_path)
        if not log_file.exists(): return []
        records = []
        names = {u[0]: u[1] for u in self.storage.get_all_users()}
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        records.append({"event": d.get("event", "UNKNOWN"), "user": names.get(d.get("user_id"), d.get("user_id", "system")), "status": "OK" if d.get("success", True) else "FAIL", "ts": d.get("timestamp", "").split("T")[-1][:8] if "timestamp" in d else "--:--:--"})
        except Exception: pass
        return records[-20:]

    # ---- guided multi-angle enrollment --------------------------------------------------

    def enroll_begin(self) -> Dict:
        if not self.camera.is_opened() and not self.camera.open():
            return {"ok": False, "msg": "Camera unavailable"}
        self._camera_active = True
        self._enroll = EnrollmentSession(self.detector, self.extractor)
        return {"ok": True}

    def enroll_tick(self) -> Dict:
        if self._enroll is None:
            return {"ok": False, "msg": "No enrollment in progress"}
        ret, frame = self.camera.read_frame()
        if not ret or frame is None:
            return {"ok": False, "msg": "Camera frame capture failed"}
        status = self._enroll.process(frame)
        h, w = frame.shape[:2]
        data = status.to_dict((w, h))
        data.update({"ok": True, "frame": self._encode(frame), "size": [w, h]})
        return data

    @staticmethod
    def _os_account() -> str:
        return os.environ.get("SUDO_USER") or getpass.getuser()

    def _ensure_os_link(self, user_id: str) -> None:
        """Make this face profile the one that unlocks the current OS account, if none is yet."""
        acct = self._os_account()
        if not self.storage.os_account_taken(acct):
            self.storage.set_os_user(user_id, acct)

    def _daemon_info(self) -> Dict[str, bool]:
        """Is the unlock service reachable, and is it the current (face-model 2) version?"""
        import socket as sock
        try:
            s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect("/tmp/facelock.sock")
            s.sendall(json.dumps({"action": "ping"}).encode())
            data = s.recv(4096).decode() or "{}"
            s.close()
            resp = json.loads(data)
            return {"alive": True, "current": bool(resp.get("result")) and bool(resp.get("ready", True))}
        except Exception:
            return {"alive": False, "current": False}

    def _new_user_id(self, name: str) -> str:
        """Internal ID from the name (e.g. "Ada Lovelace" -> ada_lovelace), unique among profiles."""
        base = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_") or "user"
        taken = {u[0] for u in self.storage.get_all_users()}
        candidate, n = base, 2
        while candidate in taken:
            candidate, n = f"{base}_{n}", n + 1
        return candidate

    def enroll_finish(self, user_id: str, name: str, passphrase: str = "", keep_existing: bool = False) -> Dict:
        session = self._enroll
        if session is None:
            return {"ok": False, "msg": "No enrollment in progress"}
        if not session.can_finish:
            return {"ok": False, "msg": "Keep moving your head slowly until the ring fills in"}
        template = session.build_template()
        if not keep_existing and not user_id:
            user_id = self._new_user_id(name)
        if keep_existing:
            # Re-scan: replace only the face template; the stored name, ID and passphrase stay.
            current = next((u for u in self.storage.get_all_users() if u[0] == user_id), None)
            if current is None:
                return {"ok": False, "msg": "That profile no longer exists"}
            name, password = current[1], None
        else:
            password = passphrase or "MasterKey123"
        ok = self.engine.enroll_template(user_id, name, "MasterKey123", template, password)
        if ok:
            self._enroll = None
            self._ensure_os_link(user_id)
        return {
            "ok": ok, "userId": user_id, "templates": len(template), "poses": template.coverage(),
            "msg": f"'{name}' enrolled from {len(template)} captures" if ok else "Enrollment failed",
        }

    def enroll_cancel(self) -> Dict:
        self._enroll = None
        return {"ok": True}

    def enroll_user(self, user_id: str, name: str, secret: str) -> Dict:
        """Single-frame enrollment, kept for scripts. The dashboard uses the guided flow."""
        if not self.camera.is_opened(): self.camera.open()
        ret, frame = self.camera.read_frame()
        if not ret or frame is None: return {"ok": False, "msg": "Camera capture failed"}
        ok = self.engine.enroll_user(user_id, name, "MasterKey123", frame, secret or "MasterKey123")
        return {"ok": ok, "msg": f"'{name}' enrolled" if ok else "Enrollment failed"}

    # ---- account + security checkup ----------------------------------------------------

    def account_get(self) -> Dict:
        out = self.account.public()
        out["checkup"] = self._checkup(out)
        out["google_status"] = self._google.status()
        return out

    def _checkup(self, acct: Dict) -> List[Dict[str, Any]]:
        sec = self.settings.security
        users = self.get_users()
        usable = [u for u in users if not u["needsReenroll"]]
        best = max((u["poseCoverage"] for u in usable), default=0)
        no_pw = [u for u in usable if not self.storage.get_password_hash(u["userId"])]
        acct_name = self._os_account()
        link_user = self.storage.find_user_by_os_account(acct_name)
        svc = self._daemon_info()
        items = [
            {"id": "face", "title": "Face profile", "page": "enrollment",
             "ok": bool(usable) and best >= 7,
             "detail": ("Enrolled from %d of 9 angles" % best) if usable else "No usable face profile yet"
                       if not users else "Older profile, enroll again"},
            {"id": "liveness", "title": "Liveness check", "page": "settings", "ok": sec.liveness_required,
             "detail": "Blocks flat photos and frozen video" if sec.liveness_required else "Turned off"},
            {"id": "fallback", "title": "Fallback passphrase", "page": "enrollment", "ok": bool(usable) and not no_pw,
             "detail": "Set for every profile" if usable and not no_pw else "Add one so you are never locked out"},
            {"id": "strict", "title": "Match strictness", "page": "settings", "ok": sec.matching_threshold >= 0.36,
             "detail": "Balanced or stricter" if sec.matching_threshold >= 0.36 else "Set low, easier for others to pass"},
            {"id": "link", "title": "Lock screen & protected apps", "page": "enrollment",
             "ok": bool(usable) and bool(link_user),
             "detail": (f"Your face unlocks the '{acct_name}' account" if link_user
                        else "No face profile is linked to this computer account yet")},
            {"id": "service", "title": "Unlock service", "page": "overview", "ok": svc["alive"] and svc["current"],
             "detail": ("Running and up to date" if svc["alive"] and svc["current"] else
                        "Running old code. Restart it: sudo systemctl restart facelock" if svc["alive"] else
                        "Not running. Start it: sudo systemctl start facelock")},
            {"id": "google", "title": "Google account", "page": "account", "ok": bool(acct.get("google")),
             "detail": acct["google"]["email"] if acct.get("google") else "Optional: link to personalise FaceLock"},
        ]
        return items

    def account_set_name(self, name: str) -> Dict:
        self.account.set_local_name(name or "")
        return {"ok": True}

    def account_save_client(self, client_id: str, client_secret: str = "") -> Dict:
        cid = (client_id or "").strip()
        if cid and not cid.endswith(".apps.googleusercontent.com"):
            return {"ok": False, "msg": "That doesn't look like a Google client ID (…apps.googleusercontent.com)"}
        self.account.set_client(cid, client_secret or None)
        return {"ok": True, "msg": "Google client saved"}

    def account_google_begin(self) -> Dict:
        try:
            self._google.begin()
            return {"ok": True}
        except GoogleOAuthError as e:
            return {"ok": False, "msg": str(e)}

    def account_google_status(self) -> Dict:
        return {"ok": True, **self._google.status(), "profile": self.account.public()["google"]}

    def account_google_cancel(self) -> Dict:
        self._google.cancel()
        return {"ok": True}

    def account_signout(self) -> Dict:
        self._google.sign_out()
        return {"ok": True}

    # ---- live perception + test unlock --------------------------------------------------

    def perception_tick(self) -> Dict:
        ret, frame = self.camera.read_frame() if self.camera.is_opened() else (False, None)
        if not ret or frame is None:
            return {"ok": False}
        h, w = frame.shape[:2]
        out = {"ok": True, "frame": self._encode(frame), "size": [w, h],
               "luma": round(mean_luma(frame)), "faces": []}
        for f in self.detector.detect(frame)[:3]:
            q = assess_face(self.detector.last_frame_used, f)
            x, y, bw, bh = f.bbox
            out["faces"].append({
                "box": [x / w, y / h, bw / w, bh / h], "score": round(f.score, 2),
                "yaw": round(f.yaw), "pitch": round(f.pitch), "roll": round(f.roll),
                "quality": "good" if q.ok else q.hint,
                "landmarks": [[float(px) / w, float(py) / h] for px, py in f.landmarks],
            })
        return out

    def verify_begin(self, user_id: str) -> Dict:
        if not self.camera.is_opened() and not self.camera.open():
            return {"ok": False, "msg": "Camera unavailable"}
        self._camera_active = True

        def frames():
            while True:
                ret, frame = self.camera.read_frame()
                yield frame if ret else None

        self._verify_user = user_id
        self._verify = self.engine.iter_authentication(
            user_id, "MasterKey123", frames(), timeout=self.settings.security.auth_timeout_seconds
        )
        return {"ok": True}

    def verify_tick(self) -> Dict:
        if self._verify is None:
            return {"ok": False, "done": True}
        try:
            p = next(self._verify)
        except StopIteration:
            self._verify = None
            return {"ok": False, "done": True}
        out = {"ok": True, "hint": p.hint, "score": round(p.score, 3), "matches": p.matches,
               "threshold": round(p.result.threshold if p.result and p.result.threshold
                                  else self.settings.security.matching_threshold, 3),
               "done": p.done, "success": bool(p.result and p.result.ok),
               "reason": p.result.reason if p.result else "", "box": None, "frame": None}
        if p.frame is not None:
            h, w = p.frame.shape[:2]
            out["frame"] = self._encode(p.frame)
            if p.face is not None:
                x, y, bw, bh = p.face.bbox
                out["box"] = [x / w, y / h, bw / w, bh / h]
        if p.done:
            self._verify = None
        return out

    @staticmethod
    def _encode(frame, max_w: int = 640) -> str:
        h, w = frame.shape[:2]
        if w > max_w:
            frame = cv2.resize(frame, (max_w, int(h * max_w / w)), interpolation=cv2.INTER_AREA)
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
        return f"data:image/jpeg;base64,{base64.b64encode(buf).decode('ascii')}"

    def _daemon_alive(self) -> bool:
        import socket as sock
        try:
            s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect("/tmp/facelock.sock")
            s.close()
            return True
        except Exception:
            return False

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
                            apps.append({"name": n, "cmd": c, "icon": ic, "kw": kw, "iconName": cp['Desktop Entry'].get('Icon', '')})
                except Exception: pass
        apps.sort(key=lambda x: x['name'].lower())
        return apps

    def get_app_icons(self, names: List[str]) -> Dict[str, Any]:
        """Real application icons as data URIs, keyed by the requested name (None if not found)."""
        out: Dict[str, Any] = {}
        for n in (names or [])[:120]:
            n = str(n or "")
            base = os.path.basename(n.split()[0]) if n and not os.path.isabs(n) and " " in n else n
            out[n] = self._icons.data_uri(n, base, base.lower())
        return out

    def get_protected_apps(self) -> List[Dict[str, Any]]:
        return getattr(self.settings, "protected_apps", [])

    def add_protected_app(self, name: str, cmd: str, icon: str, icon_name: str = "") -> Dict[str, Any]:
        aid = f"app_{len(self.get_protected_apps()) + 1}"
        apps = list(self.get_protected_apps()) + [{"id": aid, "name": name, "cmd": cmd, "icon": icon or "app", "icon_name": icon_name or ""}]
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
        return self._encode(frame)

    def _start_daemon(self):
        import socket as sock
        try: s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM); s.connect("/tmp/facelock.sock"); s.close()
        except Exception: subprocess.Popen([sys.executable, str(Path(__file__).resolve().parent.parent / "Service" / "auth" / "auth_service.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
