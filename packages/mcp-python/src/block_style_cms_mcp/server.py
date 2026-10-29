"""stdio MCP server wrapping BlockStyleCmsClient."""

from __future__ import annotations

from typing import Any

from block_style_cms_sdk import BlockStyleCmsClient
from block_style_cms_sdk.models import ImageUploadOptions
from mcp.server.mcpserver import MCPServer

from .config import Settings, load_settings
from .tools import (
    TOOL_LIST_CHANNELS,
    TOOL_LIST_LOCALES,
    TOOL_PUBLISH_FROM_MARKDOWN,
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
