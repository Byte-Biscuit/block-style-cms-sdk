"""Sample article image checks — run: python tests/test_sample_article.py"""

from __future__ import annotations

import logging
from pathlib import Path

from block_style_cms_sdk.markdown.images import (
    collect_relative_image_srcs,
    is_relative_image_src,
    is_skippable_image_src,
    resolve_image_path,
    rewrite_all_image_srcs,
)

logger = logging.getLogger(__name__)

SAMPLES = Path(__file__).resolve().parents[3] / "samples"
ARTICLE = SAMPLES / "article.md"
ASSETS = SAMPLES / "assets"

URL_SRC = (
    "https://upload.wikimedia.org/wikipedia/commons/3/3f/"
    "Fronalpstock_big.jpg"
)
CMS_SRC = "/images/sample-already-uploaded.webp"
ABS_SRC = "/tmp/block-style-cms-sdk/sample-abs.png"
REL_DOT = "./assets/relative-dot.png"
REL = "assets/relative.png"
HTML_REL = "html-img.jpg"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("checking sample paths under %s", SAMPLES)
    assert ARTICLE.is_file()
    for name in ("relative-dot.png", "relative.png", "html-img.jpg"):
        assert (ASSETS / name).is_file(), name

    md = ARTICLE.read_text(encoding="utf-8")
    relative = collect_relative_image_srcs(md)
    logger.info("relative image srcs: %s", relative)
    assert relative == [REL_DOT, REL, HTML_REL]

    assert is_skippable_image_src(URL_SRC)
    assert is_skippable_image_src(CMS_SRC)
    assert not is_skippable_image_src(ABS_SRC)
    assert not is_relative_image_src(URL_SRC)
    assert not is_relative_image_src(CMS_SRC)
    assert not is_relative_image_src(ABS_SRC)

    for src, name in (
        (REL_DOT, "relative-dot.png"),
        (REL, "relative.png"),
        (HTML_REL, "html-img.jpg"),
    ):
        resolved = resolve_image_path(ASSETS, src)
        assert resolved.is_file(), src
        assert resolved.name == name, src

    out = rewrite_all_image_srcs(
        md,
        {
            REL_DOT: "/images/relative-dot.webp",
            REL: "/images/relative.webp",
            HTML_REL: "/images/html-img.webp",
        },
    )
    assert URL_SRC in out
    assert CMS_SRC in out
    assert ABS_SRC in out
    assert "/images/relative-dot.webp" in out
    assert "/images/relative.webp" in out
    assert "/images/html-img.webp" in out
    assert REL_DOT not in out
    assert REL not in out
    assert 'src="html-img.jpg"' not in out

    logger.info("test_sample_article: ok")


if __name__ == "__main__":
    main()
