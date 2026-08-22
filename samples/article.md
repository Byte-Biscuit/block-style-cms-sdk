# Markdown rendering fixture

Neutral sample for [Block Style CMS](https://github.com/Byte-Biscuit/block-style-cms) import checks. Covers common block and inline syntax plus six image `src` forms.

## Headings and inline text

This paragraph mixes **bold**, *italic*, ***bold italic***, ~~strikethrough~~, and `inline code`. A [link to the CMS repo](https://github.com/Byte-Biscuit/block-style-cms) should survive conversion.

### Third-level heading

Plain paragraph after a subheading. Use `publish_from_markdown` with `assets_dir` pointing at `samples/assets`.

---

## Unordered list

- First item with **emphasis**
- Second item with `code`
  - Nested bullet
  - Another nested bullet
- Third item

## Ordered list

1. Step one: collect relative images
2. Step two: upload via `POST /api/m/images`
3. Step three: rewrite paths to `/images/{filename}`

## Blockquote

> Structured content should stay readable after import.
> Block quotes can span multiple lines.

## Fenced code block

```python
from block_style_cms_sdk import BlockStyleCmsClient

client = BlockStyleCmsClient(
    base_url="https://cms.example.com",
    api_key="bsc_...",
)
client.articles.publish_from_markdown(
    title="Fixture",
    slug="markdown-rendering-fixture",
    summary="Sample for CMS markdown conversion",
    language="en-US",
    md_file="./samples/article.md",
    assets_dir="./samples/assets",
)
```

## Mermaid diagram

```mermaid
flowchart LR
  md[article.md] --> parse[CMS markdown parser]
  parse --> blocks[BlockNote blocks]
  blocks --> publish[Published article]
```

---

## Image sources (six forms)

Each subsection uses one `src` type for SDK image-path handling.

### 1. HTTPS URL

![Alpine landscape](https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg)

### 2. CMS uploaded path

![Already on CMS](/images/sample-already-uploaded.webp)

### 3. Absolute filesystem path

![Absolute path sample](/tmp/block-style-cms-sdk/sample-abs.png)

### 4. Relative path with `./`

![Dot-relative PNG](./assets/relative-dot.png)

### 5. Relative path without `./`

![Assets-relative PNG](assets/relative.png)

### 6. HTML img tag

<img src="html-img.jpg" alt="HTML img relative JPEG" />
