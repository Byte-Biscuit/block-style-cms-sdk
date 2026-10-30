# `@block-style-cms/sdk`

Node.js / TypeScript SDK for [Block Style CMS](https://github.com/Byte-Biscuit/block-style-cms).

## Install

```bash
npm install @block-style-cms/sdk
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

## Article closed loop

After create, prefer editing exported markdown so images stay as absolute `http(s)` URLs and are not re-uploaded:

```ts
const article = await client.articles.get(slug, id, {
  includeMdContent: true,
});
// article.mdContent — edit, then:
await client.articles.updateFromMarkdown({
  id,
  title: article.title,
  slug,
  language: article.locale,
  mdContent: article.mdContent + "\n\nEdit.\n",
  assetsDir: "./posts/assets",
  published: false,
});
await client.articles.setPublished({ id, slug, published: true });
await client.articles.delete(slug, id);
```

Also: `getBySlug`, `list`, `updateMetadata`, `deleteBySlug`, `media.deleteImage`.  
Design notes: [`docs/`](../../docs/README.md).

## Content metadata

Before publishing, discover site configuration:

- `GET /api/m/locales` — site-supported article languages (deployment-specific)
- `GET /api/m/channels` — site channels from CMS settings

```ts
const locales = await client.content.listLocales();
const channels = await client.content.listChannels();
```

List filter `published` is a status token — `"published" | "draft" | "all"` — **not** a boolean. Do not pass `"true"` / `"false"`.

```ts
await client.articles.list({ published: "published", pageSize: 20 });
```

## Develop

From the monorepo root:

```bash
npm install
npm run build:js
```

Remote API check with the shared sample fixture ([`samples/`](../../samples/)):

```bash
cd packages/js
BSC_BASE_URL=https://your-cms.example.com \
BSC_API_KEY=bsc_... \
npm run publish:sample
```

## Release

1. Bump `version` in [`package.json`](package.json).
2. Tag `js-vX.Y.Z`, push, and **Publish** a GitHub Release for that tag.
3. GitHub Actions publishes to npm (requires `NPM_TOKEN` secret).

Example: version `0.0.1` → tag `js-v0.0.1` → GitHub Release → npm.
