"""Google sign-in for desktop apps: OAuth 2.0 authorization-code flow with PKCE.

The app opens the system browser, listens for the redirect on 127.0.0.1 (random
port), exchanges the code for tokens, reads the basic profile, and then discards
the tokens. Signing in only links an identity for display; it never unlocks
anything and is not used for face authentication.

Needs an OAuth client of type "Desktop app" from Google Cloud Console.
"""

import base64
import hashlib
import http.server
import json
import secrets
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from typing import Any, Callable, Dict, Optional

from Core.account.store import AccountStore

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SCOPES = "openid email profile"

_DONE_PAGE = """<!doctype html><meta charset=utf-8><title>FaceLock</title>
<body style="font-family:system-ui,sans-serif;display:grid;place-items:center;height:100vh;margin:0;background:#f8fafd;color:#1f1f1f">
<div style="text-align:center;max-width:360px"><div style="font-size:48px">{icon}</div>
<h2 style="margin:8px 0">{title}</h2><p style="color:#5f6368">{body}</p></div></body>"""


class GoogleOAuthError(RuntimeError):
    pass


def make_pkce() -> Dict[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return {"verifier": verifier, "challenge": challenge}


def build_auth_url(client_id: str, redirect_uri: str, state: str, challenge: str) -> str:
    q = {
        "client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": SCOPES, "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256", "access_type": "online", "prompt": "select_account",
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(q)


def _http_post_form(url: str, data: Dict[str, str]) -> Dict[str, Any]:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def _http_get_json(url: str, bearer: str) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


class GoogleSignIn:
    """One sign-in attempt at a time; poll :meth:`status` from the UI."""

    def __init__(
        self,
        store: AccountStore,
        post_form: Callable[[str, Dict[str, str]], Dict[str, Any]] = _http_post_form,
        get_json: Callable[[str, str], Dict[str, Any]] = _http_get_json,
        open_browser: Callable[[str], Any] = webbrowser.open,
    ):
        self.store = store
        self._post, self._get, self._open = post_form, get_json, open_browser
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {"phase": "idle", "message": ""}
        self._server: Optional[http.server.HTTPServer] = None

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def _set(self, phase: str, message: str = "") -> None:
        with self._lock:
            self._state = {"phase": phase, "message": message}

    def cancel(self) -> None:
        if self._server:
            threading.Thread(target=self._server.shutdown, daemon=True).start()
        self._set("idle")

    def begin(self, timeout: float = 180.0) -> Dict[str, Any]:
        client = self.store.client()
        if not client["client_id"]:
            raise GoogleOAuthError("Add your Google OAuth client ID first.")
        if self.status()["phase"] == "waiting":
            self.cancel()

        pkce, state = make_pkce(), secrets.token_urlsafe(24)
        result: Dict[str, str] = {}
        done = threading.Event()

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):  # silence
                pass

            def do_GET(self):
                url = urllib.parse.urlparse(self.path)
                if url.path != "/callback":
                    self.send_response(404); self.end_headers(); return
                q = urllib.parse.parse_qs(url.query)
                ok = q.get("state", [""])[0] == state and "code" in q
                if ok:
                    result["code"] = q["code"][0]
                else:
                    result["error"] = q.get("error", ["Sign-in was cancelled or the response was invalid."])[0]
                page = _DONE_PAGE.format(
                    icon="✅" if ok else "⚠️",
                    title="You're signed in" if ok else "Sign-in didn't finish",
                    body="You can close this tab and return to FaceLock." if ok else "Return to FaceLock and try again.",
                )
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
                self.wfile.write(page.encode())
                done.set()

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self._server = server
        redirect = f"http://127.0.0.1:{server.server_address[1]}/callback"
        url = build_auth_url(client["client_id"], redirect, state, pkce["challenge"])
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self._set("waiting", "Finish signing in in your browser")

        def worker():
            try:
                if not done.wait(timeout):
                    raise GoogleOAuthError("Sign-in timed out.")
                if "code" not in result:
                    raise GoogleOAuthError(result.get("error", "Sign-in failed."))
                form = {
                    "code": result["code"], "client_id": client["client_id"], "redirect_uri": redirect,
                    "grant_type": "authorization_code", "code_verifier": pkce["verifier"],
                }
                if client["client_secret"]:
                    form["client_secret"] = client["client_secret"]
                tokens = self._post(TOKEN_URL, form)
                profile = self._get(USERINFO_URL, tokens["access_token"])
                self.store.set_profile(profile)  # tokens are dropped here, never persisted
                self._set("done", profile.get("name") or profile.get("email", ""))
            except GoogleOAuthError as e:
                self._set("error", str(e))
            except Exception as e:  # network / HTTP errors
                self._set("error", f"Google sign-in failed: {e}")
            finally:
                threading.Thread(target=server.shutdown, daemon=True).start()

        threading.Thread(target=worker, daemon=True).start()
        try:
            self._open(url)
        except Exception:
            pass
        return {"url": url}

    def sign_out(self) -> None:
        self.store.set_profile(None)
        self._set("idle")
