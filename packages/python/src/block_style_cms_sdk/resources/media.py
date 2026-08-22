from __future__ import annotations

from pathlib import Path

from ..client import HttpClient
from ..models import ImageMetaInfo, ImageUploadOptions


class MediaResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def upload_image(
        self,
        file_bytes: bytes,
        filename: str,
        options: ImageUploadOptions | None = None,
    ) -> ImageMetaInfo:
        return self._http.upload_image(file_bytes, filename, options)

    def upload_image_file(
        self,
        file_path: str | Path,
        options: ImageUploadOptions | None = None,
    ) -> ImageMetaInfo:
        return self._http.upload_image_file(file_path, options)
