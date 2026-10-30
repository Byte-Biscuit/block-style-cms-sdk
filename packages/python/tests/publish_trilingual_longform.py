"""Publish three long articles (zh-CN / zh-TW / en-US) from a temp folder.

- Generates MiniMax illustrations into ``assets/`` under a temp work dir
- One article published, two drafts
- Does **not** delete articles after success

  set -a && source ../../.env && set +a
  uv run python tests/publish_trilingual_longform.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

from block_style_cms_sdk import BlockStyleCmsClient

REPORT_PATH = Path(__file__).resolve().parent / "trilingual_longform_report.json"

# One published, two drafts
ARTICLES: list[dict[str, Any]] = [
    {
        "language": "zh-CN",
        "published": False,
        "slug_suffix": "zh-cn",
        "title": "块式 CMS 长文联调：从本地资源到发布流水线",
        "summary": "用本地临时目录与插图资产，验证简体中文长文创建与草稿状态。",
        "tags": ["sdk-loop", "zh-CN", "longform"],
        "keywords": ["块式CMS", "Markdown", "插图"],
    },
    {
        "language": "zh-TW",
        "published": False,
        "slug_suffix": "zh-tw",
        "title": "塊式 CMS 長文聯調：從本地資源到發佈流水線",
        "summary": "以本地暫存目錄與插圖資產，驗證繁體中文長文建立與草稿狀態。",
        "tags": ["sdk-loop", "zh-TW", "longform"],
        "keywords": ["塊式CMS", "Markdown", "插圖"],
    },
    {
        "language": "en-US",
        "published": True,
        "slug_suffix": "en-us",
        "title": "Block Style CMS Long-form Loop: Local Assets to Publish",
        "summary": (
            "Validate English long-form create with local temp assets; "
            "this locale is published."
        ),
        "tags": ["sdk-loop", "en-US", "longform"],
        "keywords": ["block-style-cms", "markdown", "illustrations"],
    },
]

IMAGE_PROMPTS = [
    (
        "hero",
        "Wide editorial illustration of a modern content management workspace, "
        "soft blue and cream, flat design, no text, no logos",
        "16:9",
    ),
    (
        "pipeline",
        "Isometric diagram of a document flowing through upload, review, and publish "
        "stages, clean vector style, pastel colors, no text",
        "1:1",
    ),
    (
        "media",
        "Flat illustration of image assets organized in folders next to a markdown "
        "document, minimal, blue accents, no text",
        "1:1",
    ),
    (
        "locale",
        "Simple globe with three language speech bubbles abstract shapes, "
        "friendly flat design, no readable letters",
        "1:1",
    ),
]


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip("'\"")
        os.environ.setdefault(key, val)


def _mmx_generate(out_dir: Path, prefix: str, prompt: str, aspect: str) -> Path:
    out = subprocess.run(
        [
            "mmx",
            "image",
            "generate",
            "--prompt",
            prompt,
            "--aspect-ratio",
            aspect,
            "--out-dir",
            str(out_dir),
            "--out-prefix",
            prefix,
            "--non-interactive",
            "--output",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    paths: list[str] = []
    text = out.stdout.strip()
    try:
        start = text.find("{")
        if start >= 0:
            payload = json.loads(text[start:])
            paths.extend(str(x) for x in (payload.get("saved") or []))
    except json.JSONDecodeError:
        pass
    if not paths:
        paths = [str(p) for p in sorted(out_dir.glob(f"{prefix}*")) if p.is_file()]
    if not paths:
        raise RuntimeError(
            f"mmx failed for {prefix}: stdout={out.stdout!r} stderr={out.stderr!r}"
        )
    path = Path(paths[0])
    if not path.is_file():
        raise RuntimeError(f"mmx output missing: {path}")
    return path


def _md_zh_cn(stamp: str) -> str:
    return f"""# 块式 CMS 长文联调报告

> 生成时间戳：`{stamp}` · 语言：简体中文 · 状态：草稿

## 背景

Block Style CMS 把 Markdown 与本地资源目录打通：相对路径图片会先上传到媒体库，再改写为站点内的 `/images/...` 路径，最后提交 `from-markdown` 创建文章。本次联调刻意加长正文，并插入多张由 MiniMax 生成、保存在临时目录 `assets/` 下的插图，以贴近真实写作场景。

![工作区示意](./assets/hero.jpg)

## 本地临时目录约定

发布前目录结构类似：

```text
/tmp/bsc-longform-xxxx/
  article.zh-CN.md
  assets/
    hero.jpg
    pipeline.jpg
    media.jpg
    locale.jpg
```

SDK 调用时传入 `md_file`（或 `md_content`）与 `assets_dir`。相对引用如 `./assets/hero.jpg` 会在上传后被改写。

## 发布流水线

1. **生成插图**：用 MiniMax CLI（`mmx image generate`）落盘到 `assets/`。
2. **组装 Markdown**：章节、列表、引用、代码与多图混排。
3. **调用 SDK**：`publish_from_markdown(..., language="zh-CN", published=False)`。
4. **校验**：`get` / `get_by_slug` 核对标题、封面与块数量。

![流水线示意](./assets/pipeline.jpg)

### 为何草稿也要跑通

草稿（`published=false`）仍会写入文章表与内容块，只是前台可能不可见。联调应覆盖草稿与已发布两种状态，避免「只有发布路径才测过」的盲区。

## 媒体与相对路径

插图全部来自本地临时文件夹，而不是远程 URL。这样可以验证：

- 多图上传顺序与失败回滚（缺文件应抛 `MissingAssetsError`）
- WebP/压缩等媒体处理选项是否与预期一致
- 正文内多处引用同一资源时的改写是否稳定

![媒体目录示意](./assets/media.jpg)

### 示例代码

```python
from block_style_cms_sdk import BlockStyleCmsClient

client = BlockStyleCmsClient(base_url=base_url, api_key=api_key)
client.articles.publish_from_markdown(
    title="……",
    slug="sdk-longform-…-zh-cn",
    language="zh-CN",
    md_file="article.zh-CN.md",
    assets_dir="assets",
    cover_file="assets/hero.jpg",
    published=False,
)
```

## 多语言站点

同一套插图资产可复用于简体、繁体与英文；差异主要在文案与 `language` / `locale`。站点支持的语言列表应以 `list_locales` 为准，而不是客户端写死枚举。

![多语言示意](./assets/locale.jpg)

## 验收清单

- [x] 正文足够长，包含多级标题与说明段落
- [x] 至少三张正文插图 + 一张封面候选
- [x] 从临时目录发布，不依赖仓库内 samples
- [x] 简体中文为草稿
- [ ] 测毕删除 —— **按需求保留文章**

## 结尾

若你在后台看到本篇，说明「本地临时目录 + MiniMax 插图 + 简体草稿」路径已打通。可继续对照繁体与英文姊妹篇检查一致性。
"""


def _md_zh_tw(stamp: str) -> str:
    return f"""# 塊式 CMS 長文聯調報告

> 產生時間戳：`{stamp}` · 語言：繁體中文 · 狀態：草稿

## 背景

Block Style CMS 將 Markdown 與本地資源目錄串接：相對路徑圖片會先上傳至媒體庫，再改寫為站點內的 `/images/...`，最後透過 `from-markdown` 建立文章。本次刻意加長正文，並插入多張由 MiniMax 產生、存放於暫存目錄 `assets/` 的插圖。

![工作區示意](./assets/hero.jpg)

## 本地暫存目錄

```text
/tmp/bsc-longform-xxxx/
  article.zh-TW.md
  assets/
    hero.jpg
    pipeline.jpg
    media.jpg
    locale.jpg
```

呼叫 SDK 時提供 `md_file` 與 `assets_dir`。相對路徑如 `./assets/pipeline.jpg` 會在上傳後被改寫。

## 發佈流水線

1. 以 MiniMax 產生插圖並寫入 `assets/`。
2. 組裝含章節、清單、引用、程式碼與多圖的 Markdown。
3. `publish_from_markdown(..., language="zh-TW", published=False)`。
4. 以 `get` / `get_by_slug` 驗證標題與區塊。

![流水線示意](./assets/pipeline.jpg)

### 草稿的意義

草稿仍會持久化內容，只是前台未必公開。聯調需同時覆蓋草稿與已發佈，避免只測到單一狀態。

## 媒體資產

所有插圖皆來自本地暫存資料夾。重點驗證多圖上傳、缺檔錯誤，以及路徑改寫的穩定性。

![媒體目錄示意](./assets/media.jpg)

### 範例

```python
client.articles.publish_from_markdown(
    title="……",
    slug="sdk-longform-…-zh-tw",
    language="zh-TW",
    md_file="article.zh-TW.md",
    assets_dir="assets",
    cover_file="assets/hero.jpg",
    published=False,
)
```

## 多語系

同一套插圖可共用；文案與 `language` 依語系調整。允許的語言以 `list_locales` 為準。

![多語系示意](./assets/locale.jpg)

## 驗收

- [x] 長文結構完整
- [x] 多張插圖位於 `assets/`
- [x] 自暫存目錄發佈
- [x] 繁體中文為草稿並保留

本篇用於確認繁體路徑與簡體、英文姊妹篇並列存在。
"""


def _md_en_us(stamp: str) -> str:
    return f"""# Block Style CMS Long-form Integration Report

> Timestamp: `{stamp}` · Locale: English (en-US) · Status: **published**

## Background

Block Style CMS connects Markdown authoring with a local asset directory: relative images are uploaded to the media library, rewritten to `/images/...`, then submitted through `from-markdown`. This fixture deliberately uses a long body and several MiniMax-generated illustrations stored under a temporary `assets/` folder.

![Workspace sketch](./assets/hero.jpg)

## Temporary folder layout

```text
/tmp/bsc-longform-xxxx/
  article.en-US.md
  assets/
    hero.jpg
    pipeline.jpg
    media.jpg
    locale.jpg
```

Call the SDK with `md_file` and `assets_dir`. References such as `./assets/media.jpg` are rewritten after upload.

## Publish pipeline

1. Generate illustrations with MiniMax (`mmx image generate`) into `assets/`.
2. Assemble Markdown with headings, lists, quotes, code, and inline figures.
3. Call `publish_from_markdown(..., language="en-US", published=True)`.
4. Verify with `get` / `get_by_slug` and list search.

![Pipeline sketch](./assets/pipeline.jpg)

### Why this locale is published

Among the three sister articles, only the English one is published. Simplified and Traditional Chinese remain drafts so both states are exercised in one run.

## Media handling

All figures come from the local temp tree—not remote URLs—so the run validates multi-image upload, rewrite stability, and cover selection from the same asset set.

![Media folder sketch](./assets/media.jpg)

### Sample call

```python
client.articles.publish_from_markdown(
    title="Block Style CMS Long-form Loop: Local Assets to Publish",
    slug="sdk-longform-…-en-us",
    language="en-US",
    md_file="article.en-US.md",
    assets_dir="assets",
    cover_file="assets/hero.jpg",
    published=True,
)
```

## Locales

Reuse the same illustrations across locales; change copy and `language` only. Discover allowed codes via `list_locales` rather than hard-coding enums in clients.

![Locale sketch](./assets/locale.jpg)

## Acceptance

- [x] Long-form structure with multiple sections
- [x] Multiple illustrations under `assets/`
- [x] Published from a temporary directory
- [x] English article published and retained (no cleanup delete)

If this page is visible on the public site (depending on CMS front-end rules for `published`), the English publish path is confirmed.
"""


MD_BUILDERS = {
    "zh-CN": _md_zh_cn,
    "zh-TW": _md_zh_tw,
    "en-US": _md_en_us,
}


def main() -> int:
    _load_dotenv()
    base_url = os.environ.get("BSC_BASE_URL", "").strip()
    api_key = os.environ.get("BSC_API_KEY", "").strip()
    report: dict[str, Any] = {
        "base_url": base_url,
        "ok": False,
        "work_dir": None,
        "images": [],
        "articles": [],
        "steps": [],
    }
    if not base_url or not api_key:
        report["error"] = "BSC_BASE_URL and BSC_API_KEY required"
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    stamp = str(int(time.time()))
    work = Path(tempfile.mkdtemp(prefix="bsc-longform-"))
    assets = work / "assets"
    assets.mkdir(parents=True)
    report["work_dir"] = str(work)
    report["stamp"] = stamp

    client = BlockStyleCmsClient(base_url=base_url, api_key=api_key)
    try:
        t0 = time.time()
        for prefix, prompt, aspect in IMAGE_PROMPTS:
            path = _mmx_generate(assets, prefix, prompt, aspect)
            # normalize extension in markdown refs: always ./assets/{prefix}.jpg
            # by copying/renaming to stable name
            stable = assets / f"{prefix}.jpg"
            if path.resolve() != stable.resolve():
                stable.write_bytes(path.read_bytes())
            report["images"].append(
                {"prefix": prefix, "path": str(stable), "bytes": stable.stat().st_size}
            )
            report["steps"].append(
                {
                    "name": f"mmx_{prefix}",
                    "ok": True,
                    "seconds": round(time.time() - t0, 3),
                }
            )
            t0 = time.time()

        hero = assets / "hero.jpg"
        for spec in ARTICLES:
            lang = spec["language"]
            md_name = f"article.{lang}.md"
            md_path = work / md_name
            md_path.write_text(MD_BUILDERS[lang](stamp), encoding="utf-8")
            slug = f"sdk-longform-{stamp}-{spec['slug_suffix']}"
            step_t0 = time.time()
            try:
                created = client.articles.publish_from_markdown(
                    title=spec["title"],
                    slug=slug,
                    language=lang,
                    summary=spec["summary"],
                    tags=spec["tags"],
                    keywords=spec["keywords"],
                    md_file=md_path,
                    assets_dir=assets,
                    cover_file=hero,
                    published=bool(spec["published"]),
                )
                fetched = client.articles.get(slug, created.id)
                entry = {
                    "ok": True,
                    "language": lang,
                    "published_requested": bool(spec["published"]),
                    "published_actual": fetched.published,
                    "slug": created.slug,
                    "id": created.id,
                    "locale": created.locale,
                    "title": fetched.title,
                    "blocks": len(fetched.content or []),
                    "image": fetched.image,
                    "md_file": str(md_path),
                    "seconds": round(time.time() - step_t0, 3),
                }
                report["articles"].append(entry)
                report["steps"].append(
                    {"name": f"publish_{lang}", "ok": True, "result": entry}
                )
            except Exception as exc:  # noqa: BLE001
                entry = {
                    "ok": False,
                    "language": lang,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                    "seconds": round(time.time() - step_t0, 3),
                }
                report["articles"].append(entry)
                report["steps"].append({"name": f"publish_{lang}", **entry})
                raise

        pubs = [a for a in report["articles"] if a.get("published_actual")]
        drafts = [
            a
            for a in report["articles"]
            if a.get("ok") and not a.get("published_actual")
        ]
        report["summary"] = {
            "total": len(report["articles"]),
            "published_count": len(pubs),
            "draft_count": len(drafts),
            "retained": True,
            "note": "Articles were NOT deleted after publish",
        }
        report["ok"] = (
            len(report["articles"]) == 3
            and all(a.get("ok") for a in report["articles"])
            and len(pubs) == 1
            and len(drafts) == 2
        )
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["fatal"] = f"{type(exc).__name__}: {exc}"
    finally:
        client.close()
        REPORT_PATH.write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
