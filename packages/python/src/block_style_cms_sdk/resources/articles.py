from __future__ import annotations

import logging
from pathlib import Path

from ..client import HttpClient
from ..markdown.images import (
    collect_relative_image_srcs,
    rewrite_all_image_srcs,
)
from ..models import FromMarkdownPayload, FromMarkdownRequest, Locale

logger = logging.getLogger(__name__)


class MissingAssetsError(Exception):
    def __init__(self, paths: list[str]) -> None:
        super().__init__(f"Missing local image files: {', '.join(paths)}")
        self.paths = paths


def _resolve_existing_image(assets_dir: Path, src: str) -> Path | None:
    cleaned = src[2:] if src.startswith("./") else src
    under_assets = cleaned[7:] if cleaned.startswith("assets/") else cleaned
    candidates = [
        (assets_dir / under_assets).resolve(),
        (assets_dir / cleaned).resolve(),
        (assets_dir / Path(cleaned).name).resolve(),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


class ArticlesResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def publish_from_markdown(
        self,
        *,
        title: str,
        slug: str,
        language: Locale,
        assets_dir: str | Path,
        summary: str = "",
        tags: list[str] | None = None,
        keywords: list[str] | None = None,
        md_content: str | None = None,
        md_file: str | Path | None = None,
        cover: str = "",
        cover_file: str | Path | None = None,
        published: bool = False,
        locale_param: str | None = None,
    ) -> FromMarkdownPayload:
        if not str(assets_dir).strip():
            raise ValueError("assets_dir is required")
        if not md_content and not md_file:
            raise ValueError("md_content or md_file is required")

        source = md_file if md_content is None else "<md_content>"
        logger.info(
            "publish_from_markdown slug=%s language=%s source=%s assets_dir=%s",
            slug,
            language,
            source,
            assets_dir,
        )

        md = (
            md_content
            if md_content is not None
            else Path(md_file).read_text(  # type: ignore[arg-type]
                encoding="utf-8"
            )
        )

        assets = Path(assets_dir)
        mapping: dict[str, str] = {}
        missing: list[str] = []
        relative_srcs = collect_relative_image_srcs(md)
        logger.debug("relative image srcs: %s", relative_srcs)

        for src in relative_srcs:
            local = _resolve_existing_image(assets, src)
            if local is None:
                missing.append(src)
                logger.warning("missing local image for src=%s in %s", src, assets)
                continue
            logger.debug("uploading local image src=%s file=%s", src, local)
            meta = self._http.upload_image_file(local)
            mapping[src] = f"/images/{meta.filename}"
            logger.info("mapped image src=%s -> /images/%s", src, meta.filename)

        if missing:
            logger.error("missing local image files: %s", missing)
            raise MissingAssetsError(missing)

        md = rewrite_all_image_srcs(md, mapping)
        logger.debug("rewrote %d relative image src(s) in markdown", len(mapping))

        cover_url = cover
        if cover_file is not None:
            logger.info("uploading cover file %s", cover_file)
            meta = self._http.upload_image_file(cover_file)
            cover_url = meta.fullUrl or f"/images/{meta.filename}"
            logger.info("cover -> %s", cover_url)

        payload: dict = {
            "title": title,
            "slug": slug,
            "language": language,
            "summary": summary,
            "tags": tags or [],
            "keywords": keywords or [],
            "mdContent": md,
            "cover": cover_url,
            "published": published,
        }
        if locale_param:
            payload["__locale__"] = locale_param
        body = FromMarkdownRequest.model_validate(payload)
        return self._http.create_article_from_markdown(body)
