from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# Site-configured language tag (BCP 47–style). Not a fixed enum — see list_locales.
Locale = str


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


ChannelItemType = Literal["tag", "page"]


class ChannelItem(BaseModel):
    id: str
    type: ChannelItemType
    href: str
    tag: str | None = None
    icon: str | None = None


class LocaleInfo(BaseModel):
    code: Locale
    name: str
    nativeName: str
    englishName: str
    flag: str
