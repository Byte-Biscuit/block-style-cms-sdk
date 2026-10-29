"""Smoke checks: tool registration and handlers via a mock client."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from block_style_cms_sdk.models import (
    ChannelItem,
    FromMarkdownPayload,
    ImageMetaInfo,
    LocaleInfo,
)

from block_style_cms_mcp.server import create_server
from block_style_cms_mcp.tools import TOOL_NAMES


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.content.list_locales.return_value = [
        LocaleInfo(
            code="en-US",
            name="English",
            nativeName="English",
            englishName="English",
            flag="US",
        )
    ]
    client.content.list_channels.return_value = [
        ChannelItem(id="1", type="tag", href="/tags/demo", tag="demo")
    ]
    client.media.upload_image_file.return_value = ImageMetaInfo(
        filename="abc.png",
        originalName="cover.png",
        size=10,
        width=1,
        height=1,
        mimeType="image/png",
        uploadedAt="2026-01-01T00:00:00Z",
        fullUrl="/images/abc.png",
    )
    client.articles.publish_from_markdown.return_value = FromMarkdownPayload(
        id="art-1",
        slug="hello",
        locale="en-US",
    )
    return client


def _tools(server: Any) -> dict[str, Any]:
    return dict(server._tool_manager._tools)  # noqa: SLF001


def test_registers_expected_tools() -> None:
    names = set(_tools(create_server(_mock_client())))
    assert names == set(TOOL_NAMES)


def test_list_locales_calls_sdk() -> None:
    client = _mock_client()
    tool = _tools(create_server(client))["list_locales"]
    out = tool.fn()
    assert out[0]["code"] == "en-US"
    client.content.list_locales.assert_called_once()


def test_list_channels_calls_sdk() -> None:
    client = _mock_client()
    tool = _tools(create_server(client))["list_channels"]
    out = tool.fn()
    assert out[0]["tag"] == "demo"
    client.content.list_channels.assert_called_once()


def test_upload_image_calls_sdk() -> None:
    client = _mock_client()
    tool = _tools(create_server(client))["upload_image"]
    out = tool.fn(file_path="/tmp/cover.png", quality=80)
    assert out["filename"] == "abc.png"
    kwargs = client.media.upload_image_file.call_args
    assert kwargs.args[0] == "/tmp/cover.png"
    opts = kwargs.args[1]
    assert opts.quality == 80


def test_publish_from_markdown_calls_sdk() -> None:
    client = _mock_client()
    tool = _tools(create_server(client))["publish_from_markdown"]
    out = tool.fn(
        title="Hello",
        slug="hello",
        language="en-US",
        assets_dir="/tmp/assets",
        md_content="# Hi",
    )
    assert out["id"] == "art-1"
    kwargs = client.articles.publish_from_markdown.call_args.kwargs
    assert kwargs["slug"] == "hello"
    assert kwargs["md_content"] == "# Hi"
    assert kwargs["assets_dir"] == "/tmp/assets"
