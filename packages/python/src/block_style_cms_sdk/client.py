from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Literal

import httpx

from .models import (
    ApiResult,
    Article,
    ArticleListPayload,
    ArticleListPublishedFilter,
    FromMarkdownPayload,
    FromMarkdownRequest,
    ImageMetaInfo,
    ImageUploadOptions,
    UpdateFromMarkdownRequest,
)

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, message: str, code: int, payload: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.payload = payload if payload is not None else {}


class HttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        auth_style: Literal["api-key", "bearer"] = "api-key",
        max_retries: int = 2,
        timeout: float = 60.0,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("base_url is required")
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        self.base_url = base_url.strip().rstrip("/")
        self.api_key = api_key.strip()
        self.auth_style = auth_style
        self.max_retries = max_retries
        self._client = httpx.Client(timeout=timeout)
        logger.debug(
            "HttpClient base_url=%s auth_style=%s max_retries=%d timeout=%s",
            self.base_url,
            auth_style,
            max_retries,
            timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _auth_headers(self) -> dict[str, str]:
        if self.auth_style == "bearer":
            return {"Authorization": f"Bearer {self.api_key}"}
        return {"x-api-key": self.api_key}

    def request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResult:
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        hdrs = {**self._auth_headers(), **(headers or {})}
        last_error: Exception | None = None
        attempts = self.max_retries + 1

        for attempt in range(attempts):
            logger.debug("%s %s (attempt %d/%d)", method, url, attempt + 1, attempts)
            try:
                res = self._client.request(
                    method,
                    url,
                    json=json,
                    data=data,
                    files=files,
                    headers=hdrs,
                )
                body = res.json()
                result = ApiResult.model_validate(body)
                if res.status_code >= 500 or result.code >= 500:
                    if attempt < self.max_retries:
                        logger.warning(
                            "server error %s %s: HTTP %s code=%s "
                            "(attempt %d), retrying",
                            method,
                            url,
                            res.status_code,
                            result.code,
                            attempt + 1,
                        )
                        time.sleep(0.2 * (attempt + 1))
                        continue
                if not res.is_success or result.code != 200:
                    logger.error(
                        "API error %s %s: HTTP %s code=%s message=%s",
                        method,
                        url,
                        res.status_code,
                        result.code,
                        result.message,
                    )
                    raise ApiError(
                        result.message or f"HTTP {res.status_code}",
                        result.code or res.status_code,
                        result.payload,
                    )
                logger.debug(
                    "%s %s -> HTTP %s code=%s message=%s",
                    method,
                    url,
                    res.status_code,
                    result.code,
                    result.message,
                )
                return result
            except ApiError:
                raise
            except Exception as err:  # noqa: BLE001 — retry network blips
                last_error = err
                if attempt < self.max_retries:
                    logger.warning(
                        "request failed %s %s (attempt %d/%d): %s",
                        method,
                        url,
                        attempt + 1,
                        attempts,
                        err,
                    )
                    time.sleep(0.2 * (attempt + 1))
                    continue
                logger.error(
                    "request failed %s %s after %d attempts: %s",
                    method,
                    url,
                    attempts,
                    err,
                )
                raise
        assert last_error is not None
        raise last_error

    def upload_image(
        self,
        file_bytes: bytes,
        filename: str,
        options: ImageUploadOptions | None = None,
    ) -> ImageMetaInfo:
        logger.info("uploading image %s (%d bytes)", filename, len(file_bytes))
        files = {"file": (filename, file_bytes)}
        data = None
        if options is not None:
            data = {
                "options": options.model_dump_json(exclude_none=True),
            }
        result = self.request_json(
            "POST",
            "/api/m/images",
            data=data,
            files=files,
        )
        meta = ImageMetaInfo.model_validate(result.payload)
        logger.info("uploaded image %s -> /images/%s", filename, meta.filename)
        return meta

    def upload_image_file(
        self,
        file_path: str | Path,
        options: ImageUploadOptions | None = None,
    ) -> ImageMetaInfo:
        path = Path(file_path)
        logger.debug("reading image file %s", path)
        return self.upload_image(path.read_bytes(), path.name, options)

    def create_article_from_markdown(
        self, body: FromMarkdownRequest
    ) -> FromMarkdownPayload:
        logger.info(
            "creating article from markdown slug=%s language=%s published=%s",
            body.slug,
            body.language,
            body.published,
        )
        payload = body.model_dump(by_alias=True, exclude_none=True)
        result = self.request_json(
            "POST",
            "/api/m/articles/from-markdown",
            json=payload,
        )
        article = FromMarkdownPayload.model_validate(result.payload)
        logger.info(
            "created article id=%s slug=%s locale=%s",
            article.id,
            article.slug,
            article.locale,
        )
        return article

    def update_article_from_markdown(
        self, body: UpdateFromMarkdownRequest
    ) -> FromMarkdownPayload:
        logger.info(
            "updating article from markdown id=%s slug=%s",
            body.id,
            body.slug,
        )
        payload = body.model_dump(by_alias=True, exclude_none=True)
        result = self.request_json(
            "PUT",
            "/api/m/articles/from-markdown",
            json=payload,
        )
        return FromMarkdownPayload.model_validate(result.payload)

    def get_article(
        self,
        slug: str,
        id: str,
        *,
        include_md_content: bool = False,
    ) -> Article:
        path = f"/api/m/articles/{slug}/{id}"
        if include_md_content:
            path = f"{path}?includeMdContent=true"
        result = self.request_json("GET", path)
        return Article.model_validate(result.payload)

    def get_article_by_slug(
        self,
        slug: str,
        locale: str,
        *,
        include_md_content: bool = False,
    ) -> Article:
        from urllib.parse import urlencode

        q: dict[str, str] = {"locale": locale}
        if include_md_content:
            q["includeMdContent"] = "true"
        result = self.request_json(
            "GET",
            f"/api/m/articles/by-slug/{slug}?{urlencode(q)}",
        )
        return Article.model_validate(result.payload)

    def list_articles(
        self,
        *,
        locale: str | None = None,
        tag: str | None = None,
        search_term: str | None = None,
        published: ArticleListPublishedFilter | None = None,
        page_index: int | None = None,
        page_size: int | None = None,
    ) -> ArticleListPayload:
        """GET /api/m/articles with optional filters.

        ``published`` must be one of ``\"published\"`` | ``\"draft\"`` | ``\"all\"``
        (CMS query enum). It is **not** a boolean — ``\"true\"`` / ``\"false\"`` fail.
        Omit the argument (or pass ``\"all\"``) to include every status.
        """
        from urllib.parse import urlencode

        # CMS validates query strictly: pageIndex/pageSize must be present
        # (OpenAPI defaults are not applied server-side).
        q: dict[str, str] = {
            "pageIndex": str(1 if page_index is None else page_index),
            "pageSize": str(10 if page_size is None else page_size),
        }
        if locale:
            q["locale"] = locale
        if tag:
            q["tag"] = tag
        if search_term:
            q["searchTerm"] = search_term
        if published:
            q["published"] = published
        path = f"/api/m/articles?{urlencode(q)}"
        result = self.request_json("GET", path)
        return ArticleListPayload.model_validate(result.payload)

    def update_article(self, body: dict[str, Any]) -> dict[str, Any]:
        result = self.request_json("PUT", "/api/m/articles", json=body)
        return result.payload if isinstance(result.payload, dict) else {}

    def delete_article(self, slug: str, id: str) -> dict[str, Any]:
        result = self.request_json("DELETE", f"/api/m/articles/{slug}/{id}")
        return result.payload if isinstance(result.payload, dict) else {}

    def delete_article_by_slug(self, slug: str, locale: str) -> dict[str, Any]:
        result = self.request_json(
            "DELETE",
            f"/api/m/articles/by-slug/{slug}?locale={locale}",
        )
        return result.payload if isinstance(result.payload, dict) else {}

    def delete_image(self, filename: str) -> Any:
        result = self.request_json("DELETE", f"/api/m/images/{filename}")
        return result.payload


class BlockStyleCmsClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        auth_style: Literal["api-key", "bearer"] = "api-key",
        max_retries: int = 2,
        timeout: float = 60.0,
    ) -> None:
        from .resources.articles import ArticlesResource
        from .resources.content import ContentResource
        from .resources.media import MediaResource

        self.http = HttpClient(
            base_url=base_url,
            api_key=api_key,
            auth_style=auth_style,
            max_retries=max_retries,
            timeout=timeout,
        )
        self.media = MediaResource(self.http)
        self.articles = ArticlesResource(self.http)
        self.content = ContentResource(self.http)

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> BlockStyleCmsClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
