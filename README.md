# Block Style CMS SDK

Monorepo with Node.js (`@block-style-cms/sdk`) and Python (`block-style-cms-sdk`) clients for [Block Style CMS](https://github.com).

**API contract:** [`spec/openapi.yaml`](spec/openapi.yaml) is the source of truth.

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

### Node.js

```bash
npm install @block-style-cms/sdk
```

```ts
import { BlockStyleCmsClient } from "@block-style-cms/sdk";

const client = new BlockStyleCmsClient({
  baseUrl: "https://cms.example.com",
  apiKey: process.env.BSC_API_KEY!,
});

await client.articles.publishFromMarkdown({
  title: "Hello",
  slug: "hello-article-slug",
  summary: "A short summary of at least ten chars",
  tags: ["demo"],
  language: "en-US",
  mdFile: "./posts/hello.md",
  assetsDir: "./posts/assets",
  published: false,
});
```

### Python

```bash
pip install block-style-cms-sdk
# or: uv add block-style-cms-sdk
```

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

## Packages

| Package | Path | Registry |
|---------|------|----------|
| `@block-style-cms/sdk` | `packages/js` | npm |
| `block-style-cms-sdk` | `packages/python` | PyPI |

## Develop

```bash
# JS
npm install
npm run build:js
npm run test:js

# Python (from packages/python)
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Release

- Tag `js-v*` → `.github/workflows/js-release.yml` (needs `NPM_TOKEN`)
- Tag `py-v*` → `.github/workflows/python-release.yml` (needs `PYPI_TOKEN`)
