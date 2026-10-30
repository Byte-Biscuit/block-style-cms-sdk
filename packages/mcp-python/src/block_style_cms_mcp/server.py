"""stdio MCP server wrapping BlockStyleCmsClient."""

from __future__ import annotations

from typing import Any

from block_style_cms_sdk import BlockStyleCmsClient
from block_style_cms_sdk.models import ArticleListPublishedFilter, ImageUploadOptions
from mcp.server.mcpserver import MCPServer

from .config import Settings, load_settings
from .tools import (
    TOOL_DELETE_ARTICLE,
    TOOL_DELETE_ARTICLE_BY_SLUG,
    TOOL_DELETE_IMAGE,
    TOOL_GET_ARTICLE,
    TOOL_GET_ARTICLE_BY_SLUG,
    TOOL_LIST_ARTICLES,
    TOOL_LIST_CHANNELS,
    TOOL_LIST_LOCALES,
    TOOL_PUBLISH_FROM_MARKDOWN,
    TOOL_SET_ARTICLE_PUBLISHED,
    TOOL_UPDATE_ARTICLE_METADATA,
    TOOL_UPDATE_FROM_MARKDOWN,
    TOOL_UPLOAD_IMAGE,
)


def create_server(
    client: BlockStyleCmsClient,
    *,
    name: str = "block-style-cms",
) -> MCPServer:
    """Build an MCP server bound to an existing SDK client (injectable for tests)."""
    mcp = MCPServer(name)

    @mcp.tool(name=TOOL_LIST_LOCALES)
    def list_locales() -> list[dict[str, Any]]:
        """List supported article locales from the CMS."""
        return [loc.model_dump() for loc in client.content.list_locales()]

    @mcp.tool(name=TOOL_LIST_CHANNELS)
    def list_channels() -> list[dict[str, Any]]:
        """List site channels from CMS settings."""
        return [ch.model_dump() for ch in client.content.list_channels()]

    @mcp.tool(name=TOOL_UPLOAD_IMAGE)
    def upload_image(
        file_path: str,
        quality: int | None = None,
        max_width: int | None = None,
        max_height: int | None = None,
        enable_webp: bool | None = None,
    ) -> dict[str, Any]:
        """Upload a local image file to the CMS media library.

        file_path must be readable from this MCP process (usually the host workspace).
        """
        opts: ImageUploadOptions | None = None
        if any(v is not None for v in (quality, max_width, max_height, enable_webp)):
            opts = ImageUploadOptions(
                quality=quality,
                maxWidth=max_width,
                maxHeight=max_height,
                enableWebP=enable_webp,
            )
        meta = client.media.upload_image_file(file_path, opts)
        return meta.model_dump()

    @mcp.tool(name=TOOL_DELETE_IMAGE)
    def delete_image(filename: str) -> Any:
        """Delete an image from the CMS media library by filename."""
        return client.media.delete_image(filename)

    @mcp.tool(name=TOOL_PUBLISH_FROM_MARKDOWN)
    def publish_from_markdown(
        title: str,
        slug: str,
        language: str,
        assets_dir: str,
        md_content: str | None = None,
        md_file: str | None = None,
        summary: str = "",
        tags: list[str] | None = None,
        keywords: list[str] | None = None,
        cover: str = "",
        cover_file: str | None = None,
        published: bool = False,
        locale_param: str | None = None,
    ) -> dict[str, Any]:
        """Publish an article from markdown, uploading relative local images.

        language is a site language tag (e.g. zh-CN, en-US, ja-JP); call
        list_locales first for values this CMS accepts. Provide md_content or
        md_file. assets_dir is required to resolve relative image paths. Paths
        are relative to the MCP process working directory / host workspace.
        """
        result = client.articles.publish_from_markdown(
            title=title,
            slug=slug,
            language=language,
            assets_dir=assets_dir,
            md_content=md_content,
            md_file=md_file,
            summary=summary,
            tags=tags,
            keywords=keywords,
            cover=cover,
            cover_file=cover_file,
            published=published,
            locale_param=locale_param,
        )
        return result.model_dump()

    @mcp.tool(name=TOOL_UPDATE_FROM_MARKDOWN)
    def update_from_markdown(
        id: str,
        title: str,
        slug: str,
        language: str,
        assets_dir: str,
        md_content: str | None = None,
        md_file: str | None = None,
        summary: str = "",
        tags: list[str] | None = None,
        keywords: list[str] | None = None,
        cover: str = "",
        cover_file: str | None = None,
        published: bool = False,
        locale_param: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing article from markdown (requires id).

        Prefer editing mdContent from get_article so images stay absolute http(s)
        URLs and uploads are skipped. Only relative local paths are uploaded.
        """
        result = client.articles.update_from_markdown(
            id=id,
            title=title,
            slug=slug,
            language=language,
            assets_dir=assets_dir,
            md_content=md_content,
            md_file=md_file,
            summary=summary,
            tags=tags,
            keywords=keywords,
            cover=cover,
            cover_file=cover_file,
            published=published,
            locale_param=locale_param,
        )
        return result.model_dump()

    @mcp.tool(name=TOOL_GET_ARTICLE)
    def get_article(
        slug: str,
        id: str,
        include_md_content: bool = False,
    ) -> dict[str, Any]:
        """Get full article by slug and id (BlockNote content by default).

        Set include_md_content=true to also receive mdContent export.
        """
        return client.articles.get(
            slug, id, include_md_content=include_md_content
        ).model_dump()

    @mcp.tool(name=TOOL_GET_ARTICLE_BY_SLUG)
    def get_article_by_slug(
        slug: str,
        locale: str,
        include_md_content: bool = False,
    ) -> dict[str, Any]:
        """Get full article by slug and locale (BlockNote content by default).

        Set include_md_content=true to also receive mdContent export.
        """
        return client.articles.get_by_slug(
            slug, locale, include_md_content=include_md_content
        ).model_dump()

    @mcp.tool(name=TOOL_LIST_ARTICLES)
    def list_articles(
        locale: str | None = None,
        tag: str | None = None,
        search_term: str | None = None,
        published: ArticleListPublishedFilter | None = None,
        page_index: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """List article metadata with optional filters.

        published is a CMS status filter token, not a boolean:
        "published" | "draft" | "all". Do not pass "true"/"false"
        (the API rejects them). Omit or use "all" for no status filter.
        This is unrelated to set_article_published / create-time
        published:bool fields.
        """
        return client.articles.list(
            locale=locale,
            tag=tag,
            search_term=search_term,
            published=published,
            page_index=page_index,
            page_size=page_size,
        ).model_dump()

    @mcp.tool(name=TOOL_UPDATE_ARTICLE_METADATA)
    def update_article_metadata(
        id: str,
        slug: str,
        title: str,
        locale: str,
        summary: str = "",
        tags: list[str] | None = None,
        keywords: list[str] | None = None,
        image: str = "",
        published: bool | None = None,
        locale_param: str | None = None,
    ) -> dict[str, Any]:
        """Update article metadata without replacing content blocks."""
        fields: dict[str, Any] = {
            "id": id,
            "slug": slug,
            "title": title,
            "locale": locale,
            "summary": summary,
            "tags": tags or [],
            "keywords": keywords or [],
            "image": image,
        }
        if published is not None:
            fields["published"] = published
        if locale_param:
            fields["__locale__"] = locale_param
        return client.articles.update_metadata(**fields)

    @mcp.tool(name=TOOL_SET_ARTICLE_PUBLISHED)
    def set_article_published(
        id: str,
        slug: str,
        published: bool,
        locale: str | None = None,
        locale_param: str | None = None,
    ) -> dict[str, Any]:
        """Publish or unpublish an article (loads current metadata first)."""
        return client.articles.set_published(
            id=id,
            slug=slug,
            published=published,
            locale=locale,
            locale_param=locale_param,
        )

    @mcp.tool(name=TOOL_DELETE_ARTICLE)
    def delete_article(slug: str, id: str) -> dict[str, Any]:
        """Delete an article by slug and id."""
        return client.articles.delete(slug, id)

    @mcp.tool(name=TOOL_DELETE_ARTICLE_BY_SLUG)
    def delete_article_by_slug(slug: str, locale: str) -> dict[str, Any]:
        """Delete an article by slug and locale."""
        return client.articles.delete_by_slug(slug, locale)

    return mcp


def build_client(settings: Settings) -> BlockStyleCmsClient:
    return BlockStyleCmsClient(
        base_url=settings.base_url,
        api_key=settings.api_key,
        auth_style=settings.auth_style,
    )


def main() -> None:
    settings = load_settings()
    client = build_client(settings)
    try:
        create_server(client).run()
    finally:
        client.close()


if __name__ == "__main__":
    main()
