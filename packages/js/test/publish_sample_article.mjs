/**
 * Publish samples/article.md to a live CMS and verify converted blocks.
 *
 * Run (from packages/js):
 *
 *   BSC_BASE_URL=https://cms.example.com BSC_API_KEY=bsc_... \
 *     npm run publish:sample
 */

import { access } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { BlockStyleCmsClient } from "../dist/index.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SAMPLES = path.resolve(__dirname, "../../..", "samples");
const ARTICLE = path.join(SAMPLES, "article.md");
const ASSETS = path.join(SAMPLES, "assets");

const TITLE = "Markdown rendering fixture";
const LANGUAGE = "en-US";
const SUMMARY = "SDK sample for CMS markdown conversion and image handling.";
const TAGS = ["sdk-fixture"];

const CMS_SRC = "/images/sample-already-uploaded.webp";
const ABS_SRC = "/tmp/block-style-cms-sdk/sample-abs.png";

const REQUIRED_BLOCK_TYPES = new Set([
    "heading",
    "paragraph",
    "bulletListItem",
    "numberedListItem",
    "quote",
    "codeBlock",
    "mermaid",
    "enhancedImage",
]);

const LOG_LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"];

function env(name) {
    return (process.env[name] ?? "").trim();
}

function logLevel() {
    const level = (env("BSC_LOG_LEVEL") || "INFO").toUpperCase();
    return LOG_LEVELS.includes(level) ? level : "INFO";
}

function shouldLog(level) {
    return LOG_LEVELS.indexOf(level) >= LOG_LEVELS.indexOf(logLevel());
}

function log(level, message, ...args) {
    if (!shouldLog(level)) return;
    const time = new Date().toTimeString().slice(0, 8);
    const line = `${time} ${level} publish_sample_article: ${message}`;
    if (level === "ERROR") {
        console.error(line, ...args);
    } else if (level === "WARN") {
        console.warn(line, ...args);
    } else {
        console.log(line, ...args);
    }
}

function flattenTypes(blocks) {
    const found = new Set();
    const walk = (nodes) => {
        for (const node of nodes) {
            if (node.type) found.add(node.type);
            if (node.children?.length) walk(node.children);
        }
    };
    walk(blocks);
    return found;
}

function enhancedImages(blocks) {
    const images = [];
    const walk = (nodes) => {
        for (const node of nodes) {
            if (node.type === "enhancedImage" && node.props) {
                images.push(node.props);
            }
            if (node.children?.length) walk(node.children);
        }
    };
    walk(blocks);
    return images;
}

function findBlock(blocks, blockType) {
    for (const node of blocks) {
        if (node.type === blockType) return node;
        if (node.children?.length) {
            const found = findBlock(node.children, blockType);
            if (found) return found;
        }
    }
    return undefined;
}

function codeText(block) {
    return (block.content ?? [])
        .filter((item) => item.type === "text")
        .map((item) => item.text ?? "")
        .join("");
}

function assertOk(condition, message) {
    if (!condition) throw new Error(message);
}

function verifyArticleContent(content) {
    const types = flattenTypes(content);
    log("DEBUG", "block types: %s", [...types].sort().join(", "));

    const missing = [...REQUIRED_BLOCK_TYPES].filter((t) => !types.has(t));
    assertOk(missing.length === 0, `missing block types: ${missing.sort()}`);

    const images = enhancedImages(content);
    log("INFO", "found %d enhancedImage block(s)", images.length);
    assertOk(
        images.length >= 6,
        `expected >= 6 enhancedImage blocks, got ${images.length}`
    );

    const srcs = images.map((img) => String(img.src ?? ""));
    log("DEBUG", "image srcs: %s", JSON.stringify(srcs));

    assertOk(
        srcs.some((s) => s.startsWith("https://upload.wikimedia.org/")),
        "missing https image"
    );
    assertOk(
        srcs.some((s) => s === CMS_SRC),
        "missing CMS /images/ placeholder"
    );
    assertOk(
        srcs.some((s) => s.includes(ABS_SRC)),
        "missing absolute-path image"
    );
    assertOk(
        srcs.filter((s) => s.startsWith("/images/")).length >= 4,
        `expected >= 4 /images/ srcs, got ${JSON.stringify(srcs)}`
    );

    const code = findBlock(content, "codeBlock");
    assertOk(code, "codeBlock not found");
    assertOk(
        code.props?.language === "python",
        `expected python code block, got ${String(code.props?.language)}`
    );
    assertOk(
        codeText(code).includes("BlockStyleCmsClient"),
        "code block missing BlockStyleCmsClient"
    );

    const mermaid = findBlock(content, "mermaid");
    assertOk(mermaid, "mermaid block not found");
    const mermaidCode = String(mermaid.props?.code ?? "");
    assertOk(
        mermaidCode.includes("flowchart LR"),
        `mermaid missing flowchart LR: ${mermaidCode}`
    );
}

async function pathExists(p) {
    try {
        await access(p);
        return true;
    } catch {
        return false;
    }
}

const BASE_URL = "http://192.168.62.62:3000";
const API_KEY =
    "bsc_YVHDGLNFGWtEyxHiPDBPOlTQtvnLWGFXqFKQjgPHyAqxUlfGbhbzCMLBPzzCFLFN";

async function main() {
    const baseUrl = BASE_URL;
    const apiKey = API_KEY;

    assertOk(await pathExists(ARTICLE), `missing ${ARTICLE}`);
    assertOk(await pathExists(ASSETS), `missing ${ASSETS}`);

    const slug =
        env("BSC_TEST_SLUG") || `sdk-sample-${Math.floor(Date.now() / 1000)}`;
    const cleanup = env("BSC_CLEANUP") === "1";

    log("INFO", "base_url=%s slug=%s cleanup=%s", baseUrl, slug, cleanup);
    log("INFO", "publishing %s (assets=%s)", ARTICLE, ASSETS);

    const client = new BlockStyleCmsClient({ baseUrl, apiKey });

    const created = await client.articles.publishFromMarkdown({
        title: TITLE,
        slug,
        summary: SUMMARY,
        tags: TAGS,
        language: LANGUAGE,
        mdFile: ARTICLE,
        assetsDir: ASSETS,
        published: false,
    });

    assertOk(created.id, "created.id is empty");
    assertOk(created.slug === slug, `slug mismatch: ${created.slug}`);
    assertOk(
        created.locale === LANGUAGE,
        `locale mismatch: ${created.locale}`
    );
    log(
        "INFO",
        "created article id=%s slug=%s locale=%s",
        created.id,
        created.slug,
        created.locale
    );

    const fetchPath = `/api/m/articles/${slug}/${created.id}`;
    log("INFO", "fetching %s", fetchPath);
    const result = await client.http.requestJson("GET", fetchPath);
    assertOk(result.code === 200, `fetch failed: ${result.message}`);

    const article = result.payload;
    assertOk(article.title === TITLE, `title mismatch: ${article.title}`);
    const content = article.content;
    assertOk(
        Array.isArray(content) && content.length > 0,
        "empty article content"
    );
    log("INFO", "verifying %d top-level block(s)", content.length);
    verifyArticleContent(content);

    if (cleanup) {
        log("INFO", "deleting article id=%s", created.id);
        await client.http.requestJson("DELETE", fetchPath);
    }

    log(
        "INFO",
        "publish_sample_article: ok slug=%s id=%s%s",
        slug,
        created.id,
        cleanup ? " (deleted)" : ""
    );
}

main().catch((err) => {
    log("ERROR", "%s", err instanceof Error ? err.message : String(err));
    process.exit(1);
});
