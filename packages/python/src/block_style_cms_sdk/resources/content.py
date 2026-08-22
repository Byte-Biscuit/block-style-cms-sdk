from __future__ import annotations

from ..client import HttpClient
from ..models import ChannelItem, LocaleInfo


class ContentResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_channels(self) -> list[ChannelItem]:
        result = self._http.request_json("GET", "/api/m/channels")
        payload = result.payload
        if not isinstance(payload, list):
            raise TypeError(f"expected list payload, got {type(payload).__name__}")
        return [ChannelItem.model_validate(item) for item in payload]

    def list_locales(self) -> list[LocaleInfo]:
        result = self._http.request_json("GET", "/api/m/locales")
        payload = result.payload
        if not isinstance(payload, list):
            raise TypeError(f"expected list payload, got {type(payload).__name__}")
        return [LocaleInfo.model_validate(item) for item in payload]
