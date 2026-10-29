"""Tool names (schemas come from MCPServer handler signatures)."""

from __future__ import annotations

# Public MCP tool names (snake_case; stable contract).
TOOL_LIST_LOCALES = "list_locales"
TOOL_LIST_CHANNELS = "list_channels"
TOOL_UPLOAD_IMAGE = "upload_image"
TOOL_PUBLISH_FROM_MARKDOWN = "publish_from_markdown"

TOOL_NAMES = (
    TOOL_LIST_LOCALES,
    TOOL_LIST_CHANNELS,
    TOOL_UPLOAD_IMAGE,
    TOOL_PUBLISH_FROM_MARKDOWN,
)
