import pytest

from block_style_cms_mcp.config import (
    ENV_API_KEY,
    ENV_AUTH_STYLE,
    ENV_BASE_URL,
    load_settings,
)


def test_load_settings_ok() -> None:
    s = load_settings(
        {
            ENV_BASE_URL: " https://cms.example.com/ ",
            ENV_API_KEY: " bsc_token ",
        }
    )
    assert s.base_url == "https://cms.example.com/"
    assert s.api_key == "bsc_token"
    assert s.auth_style == "api-key"


def test_load_settings_bearer() -> None:
    s = load_settings(
        {
            ENV_BASE_URL: "https://cms.example.com",
            ENV_API_KEY: "tok",
            ENV_AUTH_STYLE: "bearer",
        }
    )
    assert s.auth_style == "bearer"


def test_missing_both() -> None:
    with pytest.raises(SystemExit) as ei:
        load_settings({})
    msg = str(ei.value)
    assert ENV_BASE_URL in msg
    assert ENV_API_KEY in msg
    assert "MCP host config" in msg


def test_missing_api_key_only() -> None:
    with pytest.raises(SystemExit) as ei:
        load_settings({ENV_BASE_URL: "https://cms.example.com"})
    msg = str(ei.value)
    assert ENV_API_KEY in msg
    # only list missing vars before the guidance sentence
    missing_part = msg.split(".")[0]
    assert ENV_BASE_URL not in missing_part


def test_invalid_auth_style() -> None:
    with pytest.raises(SystemExit) as ei:
        load_settings(
            {
                ENV_BASE_URL: "https://cms.example.com",
                ENV_API_KEY: "tok",
                ENV_AUTH_STYLE: "basic",
            }
        )
    assert ENV_AUTH_STYLE in str(ei.value)
