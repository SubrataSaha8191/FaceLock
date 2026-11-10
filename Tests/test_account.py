"""Google sign-in flow (PKCE, loopback redirect) and the local account store."""

import base64
import hashlib
import json
import os
import stat
import time
import urllib.parse
import urllib.request

import pytest

from Core.account import AccountStore, GoogleOAuthError, GoogleSignIn, make_pkce
from Core.account.google_oauth import build_auth_url


def test_pkce_challenge_matches_verifier():
    p = make_pkce()
    expect = base64.urlsafe_b64encode(hashlib.sha256(p["verifier"].encode()).digest()).rstrip(b"=").decode()
    assert p["challenge"] == expect and 43 <= len(p["verifier"]) <= 128


def test_auth_url_has_required_params():
    q = urllib.parse.parse_qs(urllib.parse.urlparse(build_auth_url("cid", "http://127.0.0.1:1/callback", "st", "ch")).query)
    assert q["client_id"] == ["cid"] and q["code_challenge_method"] == ["S256"] and q["state"] == ["st"]
    assert "openid" in q["scope"][0] and q["response_type"] == ["code"]


def test_store_is_private_and_never_exposes_secret(tmp_path):
    s = AccountStore(tmp_path)
    s.set_client("cid.apps.googleusercontent.com", "shh")
    s.set_local_name("Ada")
    if os.name != "nt":
        assert stat.S_IMODE(os.stat(s.path).st_mode) == 0o600
    # Windows has no POSIX modes; restrict_to_owner() applies an owner-only ACL there (best effort).
    pub = s.public()
    assert pub["hasClient"] and pub["hasSecret"] and "shh" not in json.dumps(pub)
    assert pub["localName"] == "Ada"


def _wait(g, phase, t=5):
    end = time.time() + t
    while time.time() < end and g.status()["phase"] != phase:
        time.sleep(0.02)
    return g.status()


def _run(tmp_path, callback_query):
    store = AccountStore(tmp_path)
    store.set_client("cid", "sec")
    seen = {}

    def post(url, form):
        seen["form"] = form
        return {"access_token": "tok"}

    def get(url, bearer):
        seen["bearer"] = bearer
        return {"sub": "1", "name": "Ada L", "email": "ada@example.com", "picture": "", "given_name": "Ada"}

    g = GoogleSignIn(store, post, get, open_browser=lambda url: None)
    info = g.begin(timeout=5)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(info["url"]).query)
    redirect, state = q["redirect_uri"][0], q["state"][0]
    cb = callback_query(state)
    try:
        urllib.request.urlopen(f"{redirect}?{cb}", timeout=3).read()
    except Exception:
        pass
    return g, store, seen, q


def test_full_flow_links_profile_and_keeps_no_tokens(tmp_path):
    g, store, seen, q = _run(tmp_path, lambda st: f"code=abc&state={st}")
    assert _wait(g, "done")["phase"] == "done"
    assert seen["form"]["code"] == "abc" and seen["form"]["client_secret"] == "sec"
    assert seen["form"]["code_verifier"] and seen["bearer"] == "tok"
    assert store.public()["google"]["email"] == "ada@example.com"
    assert "tok" not in store.path.read_text()


def test_wrong_state_is_rejected(tmp_path):
    g, store, seen, _ = _run(tmp_path, lambda st: "code=abc&state=forged")
    assert _wait(g, "error")["phase"] == "error"
    assert "form" not in seen and store.public()["google"] is None


def test_user_denied(tmp_path):
    g, _, _, _ = _run(tmp_path, lambda st: f"error=access_denied&state={st}")
    assert _wait(g, "error")["phase"] == "error"


def test_requires_client_id(tmp_path):
    with pytest.raises(GoogleOAuthError):
        GoogleSignIn(AccountStore(tmp_path), open_browser=lambda u: None).begin()


def test_sign_out(tmp_path):
    g, store, _, _ = _run(tmp_path, lambda st: f"code=abc&state={st}")
    _wait(g, "done"); g.sign_out()
    assert store.public()["google"] is None
