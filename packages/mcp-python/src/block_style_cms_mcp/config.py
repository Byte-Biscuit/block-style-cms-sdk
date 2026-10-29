"""Load CMS credentials from host-injected environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

AuthStyle = Literal["api-key", "bearer"]

ENV_BASE_URL = "BSC_BASE_URL"
ENV_API_KEY = "BSC_API_KEY"
ENV_AUTH_STYLE = "BSC_AUTH_STYLE"


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    auth_style: AuthStyle = "api-key"


def load_settings(
    environ: dict[str, str] | None = None,
) -> Settings:
    """Read BSC_* env vars. Raises SystemExit with a clear message if missing."""
    env = environ if environ is not None else os.environ
    missing: list[str] = []
    base_url = (env.get(ENV_BASE_URL) or "").strip()
    api_key = (env.get(ENV_API_KEY) or "").strip()
    if not base_url:
        missing.append(ENV_BASE_URL)
    if not api_key:
        missing.append(ENV_API_KEY)
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Missing required environment variable(s): {names}. "
            "Set them in the MCP host config env block "
            "(e.g. Cursor mcp.json), not as tool arguments."
        )

    raw_style = (env.get(ENV_AUTH_STYLE) or "api-key").strip().lower()
    if raw_style not in ("api-key", "bearer"):
        raise SystemExit(
            f"Invalid {ENV_AUTH_STYLE}={raw_style!r}; expected 'api-key' or 'bearer'."
        )
    return Settings(
        base_url=base_url,
        api_key=api_key,
        auth_style=raw_style,  # type: ignore[arg-type]
    )
