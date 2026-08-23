# block-style-cms-sdk

Python SDK for [Block Style CMS](https://github.com/Byte-Biscuit/block-style-cms).

## Install

```bash
pip install block-style-cms-sdk
# or: uv add block-style-cms-sdk
```

## Auth

Create an API token in the CMS admin UI. Pass it when constructing the client:

- Header: `x-api-key: <token>` (default), or
- `Authorization: Bearer <token>`

## Publish from Markdown

1. Collect relative images from markdown (e.g. `./assets/foo.png`)
2. Resolve files under the required `assetsDir`
3. Upload via `POST /api/m/images`
4. Rewrite paths to `/images/{filename}`
5. Submit via `POST /api/m/articles/from-markdown`

```python
from block_style_cms_sdk import BlockStyleCmsClient

client = BlockStyleCmsClient(
    base_url="https://cms.example.com",
    api_key="bsc_...",
)

client.articles.publish_from_markdown(
    title="Hello",
    slug="hello-article-slug",
    summary="A short summary of at least ten chars",
    tags=["demo"],
    language="en-US",
    md_file="./posts/hello.md",
    assets_dir="./posts/assets",
    published=False,
)
```

## Content metadata

Before publishing, discover site configuration:

- `GET /api/m/locales` — supported article languages (`zh-CN`, `zh-TW`, `en-US`)
- `GET /api/m/channels` — site channels from CMS settings

```python
locales = client.content.list_locales()
channels = client.content.list_channels()
```

## Develop

From `packages/python`:

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format .
```

Remote API check with the shared sample fixture ([`samples/`](../../samples/)):

```bash
cd packages/python
BSC_BASE_URL=https://your-cms.example.com \
BSC_API_KEY=bsc_... \
uv run python tests/publish_sample_article.py
```

## Release

1. Bump `version` in [`pyproject.toml`](pyproject.toml).
2. Tag `py-vX.Y.Z`, push, and **Publish** a GitHub Release for that tag.
3. GitHub Actions uploads to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC; no `PYPI_TOKEN` secret).

Example: version `0.0.1` → tag `py-v0.0.1` → GitHub Release → PyPI.
