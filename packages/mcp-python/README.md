# block-style-cms-mcp

Python [MCP](https://modelcontextprotocol.io/) server for [Block Style CMS](https://github.com/Byte-Biscuit/block-style-cms). Thin stdio wrapper around [`block-style-cms-sdk`](../python).

## Credentials (where they live)

CMS **base URL** and **API token** are **not** tool arguments. Put them in the MCP host config `env` block (e.g. Cursor `mcp.json` / Settings → MCP):

| Parameter | Env var | Required |
|-----------|---------|----------|
| CMS base URL | `BSC_BASE_URL` | yes |
| API token | `BSC_API_KEY` | yes |
| Auth style `api-key` or `bearer` | `BSC_AUTH_STYLE` | no (default `api-key`) |

Do not commit real tokens. Do not pass them as tool inputs (they would land in chat logs).

### Cursor example

```json
{
  "mcpServers": {
    "block-style-cms": {
      "command": "uvx",
      "args": ["block-style-cms-mcp"],
      "env": {
        "BSC_BASE_URL": "https://cms.example.com",
        "BSC_API_KEY": "your-api-token"
      }
    }
  }
}
```

Local checkout (before PyPI):

```json
{
  "mcpServers": {
    "block-style-cms": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/packages/mcp-python",
        "block-style-cms-mcp"
      ],
      "env": {
        "BSC_BASE_URL": "https://cms.example.com",
        "BSC_API_KEY": "your-api-token"
      }
    }
  }
}
```

## Tools

| Tool | Purpose |
|------|---------|
| `list_locales` | Supported article languages |
| `list_channels` | Site channels |
| `upload_image` | Upload a local image (`file_path` + optional processing options) |
| `publish_from_markdown` | Publish markdown (uploads relative images under `assets_dir`) |

Path arguments (`md_file`, `assets_dir`, `file_path`, `cover_file`) must be readable by the MCP process (typically paths under the host workspace).

## Develop

```bash
cd packages/mcp-python
uv sync --extra dev
uv run ruff check .
uv run pytest
```

## Release

1. Bump `version` in `pyproject.toml`.
2. Tag `mcp-py-vX.Y.Z`, push, and publish a GitHub Release when a workflow is added.
