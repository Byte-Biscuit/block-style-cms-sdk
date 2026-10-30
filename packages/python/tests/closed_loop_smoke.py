"""Closed-loop smoke against a live CMS: MiniMax image → upload → create →
update markdown → update metadata → get/list → cleanup delete.

  BSC_BASE_URL=... BSC_API_KEY=... uv run python tests/closed_loop_smoke.py

Optional: BSC_CLEANUP=0 to keep the article; BSC_LANGUAGE=en-US
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from block_style_cms_sdk import BlockStyleCmsClient

ROOT = Path(__file__).resolve().parents[3]
SAMPLES_ASSETS = ROOT / "samples" / "assets"
WORKDIR = Path(__file__).resolve().parent / "_closed_loop_work"
REPORT_PATH = Path(__file__).resolve().parent / "closed_loop_report.json"


def _step(report: dict[str, Any], name: str, fn: Any) -> Any:
    entry: dict[str, Any] = {"name": name, "ok": False}
    t0 = time.time()
    try:
        result = fn()
        entry["ok"] = True
        entry["result"] = result
        return result
    except Exception as exc:  # noqa: BLE001
        entry["error"] = f"{type(exc).__name__}: {exc}"
        entry["traceback"] = traceback.format_exc()
        raise
    finally:
        entry["seconds"] = round(time.time() - t0, 3)
        report["steps"].append(entry)


def main() -> int:
    base_url = os.environ.get("BSC_BASE_URL", "").strip()
    api_key = os.environ.get("BSC_API_KEY", "").strip()
    language = os.environ.get("BSC_LANGUAGE", "en-US").strip()
    cleanup = os.environ.get("BSC_CLEANUP", "1").strip() != "0"

    report: dict[str, Any] = {
        "base_url": base_url,
        "language": language,
        "cleanup": cleanup,
        "steps": [],
        "ok": False,
    }

    if not base_url or not api_key:
        report["error"] = "BSC_BASE_URL and BSC_API_KEY are required"
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    if WORKDIR.exists():
        shutil.rmtree(WORKDIR)
    WORKDIR.mkdir(parents=True)
    slug = f"sdk-loop-{int(time.time())}"
    report["slug"] = slug

    client = BlockStyleCmsClient(base_url=base_url, api_key=api_key)
    article_id: str | None = None
    uploaded_filenames: list[str] = []

    try:
        def gen_image() -> dict[str, Any]:
            out = subprocess.run(
                [
                    "mmx",
                    "image",
                    "generate",
                    "--prompt",
                    "Simple flat illustration of a CMS document icon, "
                    "blue and white, clean minimal, no text",
                    "--aspect-ratio",
                    "1:1",
                    "--out-dir",
                    str(WORKDIR),
                    "--out-prefix",
                    "mmx-cover",
                    "--non-interactive",
                    "--output",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            paths: list[str] = []
            # Prefer JSON {"saved":[...]} when present
            text = out.stdout.strip()
            try:
                start = text.find("{")
                if start >= 0:
                    payload = json.loads(text[start:])
                    saved = payload.get("saved") or []
                    paths.extend(str(x) for x in saved)
            except json.JSONDecodeError:
                pass
            if not paths:
                paths = [
                    str(p)
                    for p in sorted(WORKDIR.glob("mmx-cover*"))
                    if p.is_file()
                ]
            if not paths:
                raise RuntimeError(
                    f"mmx produced no files; stdout={out.stdout!r} "
                    f"stderr={out.stderr!r}"
                )
            p = Path(paths[0])
            if not p.is_file():
                raise RuntimeError(f"mmx path not a file: {p}")
            return {"path": str(p), "size": p.stat().st_size}

        mmx = _step(report, "minimax_image_generate", gen_image)
        mmx_path = Path(mmx["path"])

        def upload_mmx() -> dict[str, Any]:
            meta = client.media.upload_image_file(mmx_path)
            uploaded_filenames.append(meta.filename)
            return {
                "filename": meta.filename,
                "fullUrl": meta.fullUrl,
                "width": meta.width,
                "height": meta.height,
                "mimeType": meta.mimeType,
            }

        cover_meta = _step(report, "upload_minimax_image", upload_mmx)

        def upload_sample() -> dict[str, Any]:
            sample = SAMPLES_ASSETS / "relative-dot.png"
            meta = client.media.upload_image_file(sample)
            uploaded_filenames.append(meta.filename)
            return {"filename": meta.filename, "fullUrl": meta.fullUrl}

        _step(report, "upload_sample_image", upload_sample)

        # Local relative image for publish_from_markdown rewrite path
        local_asset = WORKDIR / "inline.png"
        shutil.copy(SAMPLES_ASSETS / "relative.png", local_asset)

        md_create = (
            f"# Closed loop create\n\n"
            f"Generated cover used as article cover.\n\n"
            f"![inline](./inline.png)\n\n"
            f"Slug `{slug}`.\n"
        )

        def create() -> dict[str, Any]:
            nonlocal article_id
            created = client.articles.publish_from_markdown(
                title="SDK Closed Loop Create",
                slug=slug,
                language=language,
                summary="Initial summary for closed-loop smoke.",
                tags=["sdk-loop", "smoke"],
                keywords=["sdk", "closed-loop"],
                md_content=md_create,
                assets_dir=WORKDIR,
                cover_file=mmx_path,
                published=False,
            )
            article_id = created.id
            return {
                "id": created.id,
                "slug": created.slug,
                "locale": created.locale,
            }

        created = _step(report, "create_article_from_markdown", create)

        def get_after_create() -> dict[str, Any]:
            art = client.articles.get(slug, created["id"])
            return {
                "title": art.title,
                "summary": art.summary,
                "tags": art.tags,
                "published": art.published,
                "image": art.image,
                "blocks": len(art.content or []),
            }

        _step(report, "get_article", get_after_create)

        md_update = (
            f"# Closed loop UPDATED\n\n"
            f"Body rewritten via update_from_markdown.\n\n"
            f"![inline](./inline.png)\n\n"
            f"Cover still from MiniMax upload: `{cover_meta['filename']}`.\n"
        )

        def update_md() -> dict[str, Any]:
            updated = client.articles.update_from_markdown(
                id=created["id"],
                title="SDK Closed Loop Updated",
                slug=slug,
                language=language,
                summary="Summary after markdown update.",
                tags=["sdk-loop", "smoke", "updated"],
                keywords=["sdk", "update"],
                md_content=md_update,
                assets_dir=WORKDIR,
                cover=cover_meta.get("fullUrl")
                or f"/images/{cover_meta['filename']}",
                published=False,
            )
            return {
                "id": updated.id,
                "slug": updated.slug,
                "locale": updated.locale,
            }

        _step(report, "update_article_from_markdown", update_md)

        def update_meta() -> dict[str, Any]:
            payload = client.articles.update_metadata(
                id=created["id"],
                slug=slug,
                title="SDK Closed Loop Meta",
                summary="Metadata-only update summary.",
                tags=["sdk-loop", "meta"],
                keywords=["metadata"],
                locale=language,
                image=cover_meta.get("fullUrl")
                or f"/images/{cover_meta['filename']}",
                published=False,
            )
            return payload if isinstance(payload, dict) else {"payload": payload}

        _step(report, "update_article_metadata", update_meta)

        def publish_toggle() -> dict[str, Any]:
            client.articles.set_published(
                id=created["id"],
                slug=slug,
                published=True,
                locale=language,
            )
            art = client.articles.get(slug, created["id"])
            return {"published": art.published, "title": art.title}

        _step(report, "set_published_true", publish_toggle)

        def list_and_by_slug() -> dict[str, Any]:
            listing = client.articles.list(
                locale=language,
                search_term="Meta",
                page_index=1,
                page_size=20,
            )
            by_slug = client.articles.get_by_slug(slug, language)
            return {
                "list_total": listing.total,
                "list_hit": any(a.slug == slug for a in listing.data),
                "by_slug_title": by_slug.title,
                "by_slug_published": by_slug.published,
            }

        _step(report, "list_and_get_by_slug", list_and_by_slug)

        if cleanup:

            def delete_article() -> dict[str, Any]:
                return client.articles.delete(slug, created["id"])

            _step(report, "delete_article", delete_article)

        report["ok"] = all(s.get("ok") for s in report["steps"])
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["fatal"] = f"{type(exc).__name__}: {exc}"
        if cleanup and article_id:
            try:
                client.articles.delete(slug, article_id)
                report["cleanup_after_failure"] = True
            except Exception as cleanup_exc:  # noqa: BLE001
                report["cleanup_after_failure"] = str(cleanup_exc)
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
