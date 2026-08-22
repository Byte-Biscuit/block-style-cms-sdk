from __future__ import annotations

import re
from pathlib import Path

_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HTML_IMG_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.I)


def is_skippable_image_src(src: str) -> bool:
    s = src.strip()
    if not s:
        return False
    if s.startswith("/images/"):
        return True
    if re.match(r"^https?://", s, re.I):
        return True
    return False


def is_relative_image_src(src: str) -> bool:
    s = src.strip()
    if not s:
        return True
    if is_skippable_image_src(s):
        return False
    if s.startswith("/"):
        return False
    return True


def collect_relative_image_srcs(md: str) -> list[str]:
    found: set[str] = set()
    for match in _MD_IMAGE_RE.finditer(md):
        src = match.group(2).strip()
        if is_relative_image_src(src):
            found.add(src)
    for match in _HTML_IMG_RE.finditer(md):
        src = match.group(1).strip()
        if is_relative_image_src(src):
            found.add(src)
    return sorted(found)


def resolve_image_path(assets_dir: str | Path, src: str) -> Path:
    cleaned = src[2:] if src.startswith("./") else src
    under_assets = cleaned[7:] if cleaned.startswith("assets/") else cleaned
    return (Path(assets_dir) / under_assets).resolve()


def rewrite_image_src(md: str, from_src: str, to_src: str) -> str:
    escaped = re.escape(from_src)
    md_re = re.compile(rf"(!\[[^\]]*\]\(){escaped}((?:\s+\"[^\"]*\")?\))")
    out = md_re.sub(rf"\g<1>{to_src}\g<2>", md)
    html_re = re.compile(
        rf"(<img\b[^>]*\bsrc=[\"']){escaped}([\"'])",
        re.I,
    )
    return html_re.sub(rf"\g<1>{to_src}\g<2>", out)


def rewrite_all_image_srcs(md: str, mapping: dict[str, str]) -> str:
    out = md
    for from_src, to_src in mapping.items():
        out = rewrite_image_src(out, from_src, to_src)
    return out
