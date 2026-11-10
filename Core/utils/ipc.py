"""Local IPC between the FaceLock service and its clients.

* POSIX: a UNIX domain socket (default ``/tmp/facelock.sock``), unchanged.
* Windows: Python's Windows build has no ``AF_UNIX``, so the service listens on
  ``127.0.0.1`` and publishes ``endpoint.json`` (port + secret token) in the
  user's FaceLock data directory. Clients read that file and send the token with
  every request; the service rejects requests without it.

An address is either a socket path, ``tcp://host:port`` (port 0 = pick one), or
``auto`` (resolve through ``endpoint.json``).
"""

import hmac
import json
import os
import secrets
import socket
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

IS_WINDOWS = os.name == "nt"
POSIX_DEFAULT_SOCKET = "/tmp/facelock.sock"
ENDPOINT_FILE = "endpoint.json"
LOOPBACK = "127.0.0.1"


def default_address() -> str:
    return os.environ.get("FACELOCK_SOCKET") or ("auto" if IS_WINDOWS else POSIX_DEFAULT_SOCKET)


def uses_tcp(address: str) -> bool:
    return address == "auto" or address.startswith("tcp://")


def endpoint_dir() -> Path:
    override = os.environ.get("FACELOCK_DATA_DIR")
    if override:
        return Path(override)
    from Core.config.settings import get_default_data_dir
    return get_default_data_dir()


def _split_tcp(address: str) -> Tuple[str, int]:
    rest = address[len("tcp://"):]
    host, _, port = rest.rpartition(":")
    return (host or LOOPBACK), int(port or 0)


def read_endpoint(data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    try:
        return json.loads((Path(data_dir) if data_dir else endpoint_dir()).joinpath(ENDPOINT_FILE).read_text("utf-8"))
    except (OSError, ValueError):
        return None


def write_endpoint(data_dir: Path, host: str, port: int, token: str) -> Path:
    from Core.utils.fs_security import restrict_to_owner
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / ENDPOINT_FILE
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"host": host, "port": port, "token": token, "pid": os.getpid()}, f)
    restrict_to_owner(path)
    return path


def remove_endpoint(data_dir: Path) -> None:
    try:
        (Path(data_dir) / ENDPOINT_FILE).unlink()
    except OSError:
        pass


def bind_server(address: str, data_dir: Optional[Path] = None) -> Tuple[socket.socket, str, Optional[str]]:
    """Create a listening socket. Returns ``(socket, resolved_address, token)``.

    ``token`` is None for UNIX sockets (protected by file permissions) and a fresh
    random secret for TCP.
    """
    if uses_tcp(address):
        host, port = (LOOPBACK, 0) if address == "auto" else _split_tcp(address)
        if host not in (LOOPBACK, "localhost"):
            raise ValueError("FaceLock only listens on the loopback interface.")
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # Windows: stop another process sharing the port
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        srv.bind((LOOPBACK, port))
        srv.listen(5)
        real_port = srv.getsockname()[1]
        token = secrets.token_urlsafe(32)
        write_endpoint(data_dir or endpoint_dir(), LOOPBACK, real_port, token)
        return srv, f"tcp://{LOOPBACK}:{real_port}", token

    if os.path.exists(address):
        try:
            os.unlink(address)
        except OSError:
            pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # POSIX only
    srv.bind(address)
    try:
        os.chmod(address, 0o666)  # PAM helpers run as other users
    except OSError:
        pass
    srv.listen(5)
    return srv, address, None


def token_ok(expected: Optional[str], given: Any) -> bool:
    if not expected:
        return True
    return isinstance(given, str) and hmac.compare_digest(expected, given)


def open_client(
    address: Optional[str] = None, token: Optional[str] = None, timeout: float = 10.0,
    data_dir: Optional[Path] = None,
) -> Tuple[socket.socket, Optional[str]]:
    """Connect to the service. Returns ``(connected_socket, token_to_send)``."""
    addr = address or default_address()
    if uses_tcp(addr):
        ep = read_endpoint(data_dir)
        if addr == "auto":
            if not ep:
                raise FileNotFoundError("FaceLock service endpoint not found; is the service running?")
            host, port, tok = ep.get("host", LOOPBACK), int(ep["port"]), token or ep.get("token")
        else:
            host, port = _split_tcp(addr)
            tok = token or os.environ.get("FACELOCK_TOKEN") or (ep.get("token") if ep and int(ep.get("port", -1)) == port else None)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
        except Exception:
            sock.close()
            raise
        return sock, tok
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(addr)
    except Exception:
        sock.close()
        raise
    return sock, None


def probe(address: Optional[str] = None, timeout: float = 0.5) -> bool:
    """True if something is listening at the address."""
    try:
        sock, _ = open_client(address, timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False
