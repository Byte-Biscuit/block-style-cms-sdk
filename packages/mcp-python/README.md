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
| `upload_image` | Upload local image |
| `delete_image` | Delete library image by filename |
| `publish_from_markdown` | Create article from markdown |
| `update_from_markdown` | Update article from markdown (`id` required) |
| `get_article` | Get by slug + id (optional `include_md_content`) |
| `get_article_by_slug` | Get by slug + locale (optional `include_md_content`) |
| `list_articles` | List metadata with filters (`published` query: `published` \| `draft` \| `all`, **not** `true`/`false`) |
| `update_article_metadata` | Metadata-only update |
| `set_article_published` | Publish / unpublish |
| `delete_article` | Delete by slug + id |
| `delete_article_by_slug` | Delete by slug + locale |

Article closed-loop design: see repo [`docs/`](../../docs/README.md).

Path arguments (`md_file`, `assets_dir`, `file_path`, `cover_file`) must be readable by the MCP process (typically paths under the host workspace).

`list_articles.published` accepts only `published` | `draft` | `all` (CMS query enum). Boolean strings fail. Create/update and `set_article_published` still use a real boolean for the article’s published flag.

## Develop

```bash
cd packages/mcp-python
uv sync --extra dev
uv run ruff check .
uv run pytest
```

## Release

1. Ensure the required `block-style-cms-sdk` version is already on PyPI.
2. Bump `version` in `pyproject.toml` (and keep the SDK dependency pin in sync).
3. Tag `mcp-py-vX.Y.Z`, push, and **Publish** a GitHub Release for that tag.
4. GitHub Actions uploads to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC; GitHub Environment **`pypi-mcp`**, separate from the SDK’s `pypi` environment).

Example: version `0.0.3` → tag `mcp-py-v0.0.3` → GitHub Release → PyPI.

Setup checklist:

1. GitHub → Settings → Environments → create **`pypi-mcp`**.
2. Deployment branches and tags: allow tag pattern **`mcp-py-v*`** (optionally branch `master` for manual dry-runs).
3. On PyPI, register a Trusted Publisher for project `block-style-cms-mcp` pointing at workflow `mcp-python-release.yml` (and environment name `pypi-mcp` if the form asks for it).
