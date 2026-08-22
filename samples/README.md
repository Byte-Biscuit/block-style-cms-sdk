# Sample markdown fixture

Shared by Python and JavaScript SDK tests and by [Block Style CMS](https://github.com/Byte-Biscuit/block-style-cms) import validation. Paths are relative to the repository root.

## Markdown content in `article.md`

Besides the six image `src` forms below, `article.md` includes common syntax for CMS conversion checks:

| Element | Example in fixture |
|---------|-------------------|
| Headings | `#`, `##`, `###` |
| Inline | **bold**, *italic*, ***bold italic***, ~~strikethrough~~, `inline code`, links |
| Horizontal rule | `---` |
| Unordered list | nested bullets |
| Ordered list | numbered steps |
| Blockquote | `>` multi-line quote |
| Code fence | ` ```python ` block |
| Mermaid | ` ```mermaid ` flowchart |

```
samples/
  article.md          # six image src forms
  assets/
    relative-dot.png  # ./assets/relative-dot.png
    relative.png      # assets/relative.png
    html-img.jpg      # <img src="html-img.jpg">
```

## Resolving from tests

| SDK | Path |
|-----|------|
| Python | `Path(__file__).resolve().parents[3] / "samples"` from `packages/python/tests/` |
| Node.js | `path.resolve(import.meta.dirname, "../../..", "samples")` from `packages/js/test/` |

## Six image sources in `article.md`

| # | Type | Example src | Expected SDK behavior |
|---|------|-------------|------------------------|
| 1 | HTTPS URL | `https://upload.wikimedia.org/...` | Skipped (not collected, not rewritten) |
| 2 | CMS path | `/images/sample-already-uploaded.webp` | Skipped |
| 3 | Absolute path | `/tmp/block-style-cms-sdk/sample-abs.png` | Skipped |
| 4 | Relative `./` | `./assets/relative-dot.png` | Collected, resolved under `assets/`, rewritten on upload |
| 5 | Relative | `assets/relative.png` | Collected, resolved under `assets/`, rewritten on upload |
| 6 | HTML `<img>` | `html-img.jpg` | Collected, resolved under `assets/`, rewritten on upload |

`collect_relative_image_srcs` should return exactly:

```text
./assets/relative-dot.png
assets/relative.png
html-img.jpg
```

(sorted)

## Local asset sources (Wikimedia Commons)

| File | Source | License |
|------|--------|---------|
| `assets/relative-dot.png` | [PNG transparency demonstration](https://commons.wikimedia.org/wiki/File:PNG_transparency_demonstration_1.png) | Public domain |
| `assets/relative.png` | Same as `relative-dot.png` (duplicate bytes; distinct path for fixture) | Public domain |
| `assets/html-img.jpg` | [Cat03.jpg](https://commons.wikimedia.org/wiki/File:Cat03.jpg) | Public domain |

Remote URL in section 1: [Fronalpstock](https://commons.wikimedia.org/wiki/File:Fronalpstock_big.jpg) (CC BY-SA 3.0). Use the direct Commons file URL (not `/thumb/…`); thumb URLs often return HTTP 400 when hotlinked.

Sections 2 and 3 are **expected to show broken images** in the browser preview:

| Section | Why it breaks |
|---------|----------------|
| 2. `/images/sample-already-uploaded.webp` | Placeholder path — file was never uploaded to CMS |
| 3. `/tmp/block-style-cms-sdk/sample-abs.png` | Absolute filesystem path — browsers cannot load server-local files |

Sections 4–6 (relative uploads) should display after publish. If `/images/*.webp` still fail, check CMS `Content-Type` is `image/webp` (not `image / webp`).

## Remote API check (JavaScript)

```bash
cd packages/js
BSC_BASE_URL=https://your-cms.example.com \
BSC_API_KEY=bsc_... \
npm run publish:sample
```

Requires Node 18+. Same optional env as Python: `BSC_TEST_SLUG`, `BSC_CLEANUP`, `BSC_LOG_LEVEL`.

## Remote API check (Python)

Submit `article.md` to a live CMS and verify BlockNote blocks after conversion:

```bash
cd packages/python
BSC_BASE_URL=https://your-cms.example.com \
BSC_API_KEY=bsc_... \
uv run python tests/publish_sample_article.py
```

Optional env:

| Variable | Purpose |
|----------|---------|
| `BSC_TEST_SLUG` | Fixed slug (default `sdk-sample-<unix_ts>`) |
| `BSC_CLEANUP=1` | Delete the draft article after assertions |
| `BSC_LOG_LEVEL` | Log level: `DEBUG`, `INFO`, `WARNING` (default `INFO`) |

The script checks create response (`id`, `slug`, `locale`), fetches `GET /api/m/articles/{slug}/{id}`, and asserts block types (heading, lists, quote, code, mermaid, images) plus six image `src` forms in `enhancedImage` blocks.

Local-only image path checks (no network): `uv run python tests/test_sample_article.py`
