# Block Style CMS SDK

Official Node.js and Python client for [Block Style CMS](https://github.com/Byte-Biscuit/block-style-cms). Publish Markdown articles (including local images) and read site metadata — without calling the Admin API by hand.

## Packages

- [Node.js (`@block-style-cms/sdk`)](packages/js/README.md)
- [Python (`block-style-cms-sdk`)](packages/python/README.md)

API contract: [`spec/openapi.yaml`](spec/openapi.yaml)

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
