from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..client import HttpClient
from ..markdown.images import (
    collect_relative_image_srcs,
    rewrite_all_image_srcs,
)
from ..models import (
    Article,
    ArticleListPayload,
    ArticleListPublishedFilter,
    FromMarkdownPayload,
    FromMarkdownRequest,
    Locale,
    UpdateFromMarkdownRequest,
)

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

    def _prepare_markdown(
        self,
        *,
        assets_dir: str | Path,
        md_content: str | None,
        md_file: str | Path | None,
        cover: str,
        cover_file: str | Path | None,
    ) -> tuple[str, str]:
        if not str(assets_dir).strip():
            raise ValueError("assets_dir is required")
        if not md_content and not md_file:
            raise ValueError("md_content or md_file is required")

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
        for src in collect_relative_image_srcs(md):
            local = _resolve_existing_image(assets, src)
            if local is None:
                missing.append(src)
                continue
            meta = self._http.upload_image_file(local)
            mapping[src] = f"/images/{meta.filename}"

        if missing:
            raise MissingAssetsError(missing)

        md = rewrite_all_image_srcs(md, mapping)

        cover_url = cover
        if cover_file is not None:
            meta = self._http.upload_image_file(cover_file)
            cover_url = meta.fullUrl or f"/images/{meta.filename}"

        return md, cover_url

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
        md, cover_url = self._prepare_markdown(
            assets_dir=assets_dir,
            md_content=md_content,
            md_file=md_file,
            cover=cover,
            cover_file=cover_file,
        )
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

    def update_from_markdown(
        self,
        *,
        id: str,
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
        if not str(id).strip():
            raise ValueError("id is required")
        md, cover_url = self._prepare_markdown(
            assets_dir=assets_dir,
            md_content=md_content,
            md_file=md_file,
            cover=cover,
            cover_file=cover_file,
        )
        payload: dict = {
            "id": id,
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
        body = UpdateFromMarkdownRequest.model_validate(payload)
        return self._http.update_article_from_markdown(body)

    def get(
        self,
        slug: str,
        id: str,
        *,
        include_md_content: bool = False,
    ) -> Article:
        return self._http.get_article(
            slug, id, include_md_content=include_md_content
        )

    def get_by_slug(
        self,
        slug: str,
        locale: Locale,
        *,
        include_md_content: bool = False,
    ) -> Article:
        return self._http.get_article_by_slug(
            slug, locale, include_md_content=include_md_content
        )

    def list(
        self,
        *,
        locale: str | None = None,
        tag: str | None = None,
        search_term: str | None = None,
        published: ArticleListPublishedFilter | None = None,
        page_index: int | None = None,
        page_size: int | None = None,
    ) -> ArticleListPayload:
        """List article metadata.

        ``published`` is a CMS status filter token, **not** a boolean:
        ``\"published\"`` | ``\"draft\"`` | ``\"all\"``.
        Do not pass ``\"true\"`` / ``\"false\"`` — the API rejects them.
        Omit or use ``\"all\"`` for no status filter.
        """
        return self._http.list_articles(
            locale=locale,
            tag=tag,
            search_term=search_term,
            published=published,
            page_index=page_index,
            page_size=page_size,
        )

    def update_metadata(self, **fields: Any) -> dict[str, Any]:
        return self._http.update_article(fields)

    def set_published(
        self,
        *,
        id: str,
        slug: str,
        published: bool,
        locale: Locale | None = None,
        locale_param: str | None = None,
    ) -> dict[str, Any]:
        article = self._http.get_article(slug, id)
        body: dict[str, Any] = {
            "id": id,
            "slug": slug,
            "title": article.title,
            "summary": article.summary or "",
            "tags": article.tags or [],
            "keywords": article.keywords or [],
            "locale": locale or article.locale,
            "image": article.image or "",
            "published": published,
        }
        if locale_param:
            body["__locale__"] = locale_param
        return self._http.update_article(body)

    def delete(self, slug: str, id: str) -> dict[str, Any]:
        return self._http.delete_article(slug, id)

    def delete_by_slug(self, slug: str, locale: Locale) -> dict[str, Any]:
        return self._http.delete_article_by_slug(slug, locale)
