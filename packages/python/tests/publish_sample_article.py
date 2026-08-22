"""Publish samples/article.md to a live CMS and verify converted blocks.

Run (from packages/python):

  BSC_BASE_URL=https://cms.example.com BSC_API_KEY=bsc_... \\
    uv run python tests/publish_sample_article.py

Optional:
  BSC_TEST_SLUG=my-fixture-slug   # default: sdk-sample-<unix_ts>
  BSC_CLEANUP=1                   # DELETE article after checks
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from block_style_cms_sdk import BlockStyleCmsClient

logger = logging.getLogger(__name__)

SAMPLES = Path(__file__).resolve().parents[3] / "samples"
ARTICLE = SAMPLES / "article.md"
ASSETS = SAMPLES / "assets"

TITLE = "Markdown rendering fixture"
LANGUAGE = "en-US"
SUMMARY = "SDK sample for CMS markdown conversion and image handling."
TAGS = ["sdk-fixture"]

CMS_SRC = "/images/sample-already-uploaded.webp"
ABS_SRC = "/tmp/block-style-cms-sdk/sample-abs.png"

REQUIRED_BLOCK_TYPES = {
    "heading",
    "paragraph",
    "bulletListItem",
    "numberedListItem",
    "quote",
    "codeBlock",
    "mermaid",
    "enhancedImage",
}


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _configure_logging() -> None:
    level_name = _env("BSC_LOG_LEVEL") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _flatten_types(blocks: list[Any]) -> set[str]:
    found: set[str] = set()

    def walk(nodes: list[Any]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            block_type = node.get("type")
            if isinstance(block_type, str):
                found.add(block_type)
            children = node.get("children")
            if isinstance(children, list):
                walk(children)

    walk(blocks)
    return found


def _enhanced_images(blocks: list[Any]) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []

    def walk(nodes: list[Any]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("type") == "enhancedImage":
                props = node.get("props")
                if isinstance(props, dict):
                    images.append(props)
            children = node.get("children")
            if isinstance(children, list):
                walk(children)

    walk(blocks)
    return images


def _find_block(blocks: list[Any], block_type: str) -> dict[str, Any] | None:
    for node in blocks:
        if isinstance(node, dict) and node.get("type") == block_type:
            return node
        children = node.get("children") if isinstance(node, dict) else None
        if isinstance(children, list):
            found = _find_block(children, block_type)
            if found is not None:
                return found
    return None


def _code_text(block: dict[str, Any]) -> str:
    content = block.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "".join(parts)


def _verify_article_content(content: list[Any]) -> None:
    types = _flatten_types(content)
    logger.debug("block types: %s", sorted(types))
    missing = REQUIRED_BLOCK_TYPES - types
    assert not missing, f"missing block types: {sorted(missing)}"

    images = _enhanced_images(content)
    logger.info("found %d enhancedImage block(s)", len(images))
    assert len(images) >= 6, f"expected >= 6 enhancedImage blocks, got {len(images)}"

    srcs = [str(img.get("src", "")) for img in images]
    logger.debug("image srcs: %s", srcs)
    assert any(s.startswith("https://upload.wikimedia.org/") for s in srcs), "missing https image"
    assert any(s == CMS_SRC for s in srcs), "missing CMS /images/ placeholder"
    assert any(ABS_SRC in s for s in srcs), "missing absolute-path image"
    assert sum(s.startswith("/images/") for s in srcs) >= 4, srcs

    code = _find_block(content, "codeBlock")
    assert code is not None, "codeBlock not found"
    assert code.get("props", {}).get("language") == "python", code
    assert "BlockStyleCmsClient" in _code_text(code)

    mermaid = _find_block(content, "mermaid")
    assert mermaid is not None, "mermaid block not found"
    mermaid_code = str(mermaid.get("props", {}).get("code", ""))
    assert "flowchart LR" in mermaid_code, mermaid_code


def main() -> None:
    _configure_logging()

    base_url = _env("BSC_BASE_URL")
    api_key = _env("BSC_API_KEY")
    if not base_url or not api_key:
        logger.error("Set BSC_BASE_URL and BSC_API_KEY to run the remote API check.")
        sys.exit(1)

    assert ARTICLE.is_file(), ARTICLE
    assert ASSETS.is_dir(), ASSETS

    slug = _env("BSC_TEST_SLUG") or f"sdk-sample-{int(time.time())}"
    cleanup = _env("BSC_CLEANUP") == "1"

    logger.info("base_url=%s slug=%s cleanup=%s", base_url, slug, cleanup)
    logger.info("publishing %s (assets=%s)", ARTICLE, ASSETS)

    with BlockStyleCmsClient(base_url=base_url, api_key=api_key) as client:
        created = client.articles.publish_from_markdown(
            title=TITLE,
            slug=slug,
            summary=SUMMARY,
            tags=TAGS,
            language=LANGUAGE,
            md_file=ARTICLE,
            assets_dir=ASSETS,
            published=False,
        )
        assert created.id, created
        assert created.slug == slug, created
        assert created.locale == LANGUAGE, created
        logger.info(
            "created article id=%s slug=%s locale=%s",
            created.id,
            created.slug,
            created.locale,
        )

        fetch_path = f"/api/m/articles/{slug}/{created.id}"
        logger.info("fetching %s", fetch_path)
        result = client.http.request_json("GET", fetch_path)
        assert result.code == 200, result
        article = result.payload
        assert isinstance(article, dict), article
        assert article.get("title") == TITLE, article.get("title")
        content = article.get("content")
        assert isinstance(content, list) and content, "empty article content"
        logger.info("verifying %d top-level block(s)", len(content))
        _verify_article_content(content)

        if cleanup:
            logger.info("deleting article id=%s", created.id)
            client.http.request_json("DELETE", fetch_path)

    logger.info(
        "publish_sample_article: ok slug=%s id=%s%s",
        slug,
        created.id,
        " (deleted)" if cleanup else "",
    )


if __name__ == "__main__":
    os.environ["BSC_BASE_URL"] = "http://192.168.62.62:3000"
    os.environ["BSC_API_KEY"] = (
        "bsc_YVHDGLNFGWtEyxHiPDBPOlTQtvnLWGFXqFKQjgPHyAqxUlfGbhbzCMLBPzzCFLFN"
    )
    main()
