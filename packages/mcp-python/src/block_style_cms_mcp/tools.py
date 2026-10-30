"""Tool names (schemas come from MCPServer handler signatures)."""

from __future__ import annotations

# Public MCP tool names (snake_case; stable contract).
TOOL_LIST_LOCALES = "list_locales"
TOOL_LIST_CHANNELS = "list_channels"
TOOL_UPLOAD_IMAGE = "upload_image"
TOOL_DELETE_IMAGE = "delete_image"
TOOL_PUBLISH_FROM_MARKDOWN = "publish_from_markdown"
TOOL_UPDATE_FROM_MARKDOWN = "update_from_markdown"
TOOL_GET_ARTICLE = "get_article"
TOOL_GET_ARTICLE_BY_SLUG = "get_article_by_slug"
TOOL_LIST_ARTICLES = "list_articles"
TOOL_UPDATE_ARTICLE_METADATA = "update_article_metadata"
TOOL_SET_ARTICLE_PUBLISHED = "set_article_published"
TOOL_DELETE_ARTICLE = "delete_article"
TOOL_DELETE_ARTICLE_BY_SLUG = "delete_article_by_slug"

TOOL_NAMES = (
    TOOL_LIST_LOCALES,
    TOOL_LIST_CHANNELS,
    TOOL_UPLOAD_IMAGE,
    TOOL_DELETE_IMAGE,
    TOOL_PUBLISH_FROM_MARKDOWN,
    TOOL_UPDATE_FROM_MARKDOWN,
    TOOL_GET_ARTICLE,
    TOOL_GET_ARTICLE_BY_SLUG,
    TOOL_LIST_ARTICLES,
    TOOL_UPDATE_ARTICLE_METADATA,
    TOOL_SET_ARTICLE_PUBLISHED,
    TOOL_DELETE_ARTICLE,
    TOOL_DELETE_ARTICLE_BY_SLUG,
)
