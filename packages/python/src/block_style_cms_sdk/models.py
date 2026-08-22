from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Locale = Literal["zh-CN", "zh-TW", "en-US"]


class ApiResult(BaseModel):
    code: int
    message: str
    payload: Any = Field(default_factory=dict)
    tt: float | None = None


class ImageUploadOptions(BaseModel):
    quality: int | None = None
    maxWidth: int | None = None
    maxHeight: int | None = None
    enableWebP: bool | None = None


class ImageMetaInfo(BaseModel):
    filename: str
    originalName: str
    size: int
    width: int
    height: int
    mimeType: str
    uploadedAt: str
    fullUrl: str | None = None
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    altText: str | None = None


class FromMarkdownRequest(BaseModel):
    title: str
    slug: str
    language: Locale
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    mdContent: str | None = None
    cover: str = ""
    published: bool = False
    locale_param: str | None = Field(default=None, alias="__locale__")

    model_config = {"populate_by_name": True}


class FromMarkdownPayload(BaseModel):
    id: str
    slug: str
    locale: Locale
