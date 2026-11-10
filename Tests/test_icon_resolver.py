"""Application icon lookup."""

import base64

from Core.utils.icon_resolver import IconResolver

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def _put(base, rel, data=PNG):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def test_prefers_scalable_then_largest_png(tmp_path):
    _put(tmp_path, "hicolor/16x16/apps/foo.png")
    big = _put(tmp_path, "hicolor/128x128/apps/foo.png")
    r = IconResolver([str(tmp_path)], pixmaps=[])
    assert r.find("foo") == str(big)
    svg = _put(tmp_path, "hicolor/scalable/apps/foo.svg", b"<svg/>")
    assert r.find("foo") == str(svg) or IconResolver([str(tmp_path)], []).find("foo") == str(svg)


def test_supports_category_first_layout_and_pixmaps(tmp_path):
    a = _put(tmp_path / "icons", "breeze/apps/48/bar.svg", b"<svg/>")
    r = IconResolver([str(tmp_path / "icons")], pixmaps=[str(tmp_path / "pix")])
    assert r.find("bar") == str(a)
    px = _put(tmp_path / "pix", "baz.png")
    assert r.find("baz") == str(px)


def test_absolute_path_and_data_uri(tmp_path):
    p = _put(tmp_path, "x/app.png")
    r = IconResolver([], [])
    assert r.find(str(p)) == str(p)
    uri = r.data_uri("nothing", str(p))
    assert uri.startswith("data:image/png;base64,") and base64.b64decode(uri.split(",", 1)[1]) == PNG


def test_misses_and_unsafe_names(tmp_path):
    r = IconResolver([str(tmp_path)], [])
    assert r.find("missing") is None and r.data_uri("missing") is None
    assert r.find("../../etc/passwd") is None and r.find("") is None
    assert r.find("/etc/passwd") is None  # absolute but not an image


def test_oversized_icons_are_skipped(tmp_path):
    _put(tmp_path, "hicolor/512x512/apps/huge.png", b"0" * 500_000)
    assert IconResolver([str(tmp_path)], []).find("huge") is None
