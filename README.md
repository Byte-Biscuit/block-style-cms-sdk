# Block Style CMS SDK

Official Node.js and Python client for [Block Style CMS](https://github.com/Byte-Biscuit/block-style-cms). Publish Markdown articles (including local images) and read site metadata — without calling the Admin API by hand.

## Packages

- [Node.js (`@block-style-cms/sdk`)](packages/js/README.md)
- [Python (`block-style-cms-sdk`)](packages/python/README.md)
- [MCP server (`block-style-cms-mcp`, Python)](packages/mcp-python/README.md)

API contract: [`spec/openapi.yaml`](spec/openapi.yaml)

## MCP (Python)

stdio MCP server wrapping the Python SDK. Tools: `list_locales`, `list_channels`, `upload_image`, `publish_from_markdown`.

**Credentials live in the MCP host `env` block** (not tool args, not the repo):

| Parameter | Env var |
|-----------|---------|
| CMS base URL | `BSC_BASE_URL` |
| API token | `BSC_API_KEY` |
| Auth style (optional) | `BSC_AUTH_STYLE` (`api-key` \| `bearer`) |

Cursor example:

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

See [packages/mcp-python/README.md](packages/mcp-python/README.md) for local `uv run` setup and tool details.

## Develop

```bash
# JS
npm install
npm run build:js

# Python SDK (from packages/python)
uv sync --extra dev
uv run ruff check .
uv run ruff format .

# MCP server (from packages/mcp-python)
uv sync --extra dev
uv run pytest
```
