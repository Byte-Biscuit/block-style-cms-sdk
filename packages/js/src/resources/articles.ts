import { access } from "node:fs/promises";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { HttpClient } from "../client.js";
import {
    collectRelativeImageSrcs,
    resolveImagePath,
    rewriteAllImageSrcs,
} from "../markdown/images.js";
import type {
    FromMarkdownPayload,
    PublishFromMarkdownInput,
} from "../types.js";

export class MissingAssetsError extends Error {
    readonly paths: string[];

    constructor(paths: string[]) {
        super(`Missing local image files: ${paths.join(", ")}`);
        this.name = "MissingAssetsError";
        this.paths = paths;
    }
}

async function fileExists(p: string): Promise<boolean> {
    try {
        await access(p);
        return true;
    } catch {
        return false;
    }
}

async function resolveExistingImage(
    assetsDir: string,
    src: string
): Promise<string | null> {
    const cleaned = src.replace(/^\.\//, "");
    const underAssets = cleaned.replace(/^assets\//, "");
    const candidates = [
        path.resolve(assetsDir, underAssets),
        path.resolve(assetsDir, cleaned),
        path.resolve(assetsDir, path.basename(cleaned)),
        resolveImagePath(assetsDir, src),
    ];
    for (const c of candidates) {
        if (await fileExists(c)) return c;
    }
    return null;
}

export class ArticlesResource {
    constructor(private readonly http: HttpClient) {}

    async publishFromMarkdown(
        input: PublishFromMarkdownInput
    ): Promise<FromMarkdownPayload> {
        if (!input.assetsDir?.trim()) {
            throw new Error("assetsDir is required");
        }
        if (!input.mdContent && !input.mdFile) {
            throw new Error("mdContent or mdFile is required");
        }

        let md =
            input.mdContent ??
            (await readFile(input.mdFile as string, "utf8"));

        const relativeSrcs = collectRelativeImageSrcs(md);
        const mapping = new Map<string, string>();
        const missing: string[] = [];

        for (const src of relativeSrcs) {
            const local = await resolveExistingImage(input.assetsDir, src);
            if (!local) {
                missing.push(src);
                continue;
            }
            const meta = await this.http.uploadImageFile(local);
            mapping.set(src, `/images/${meta.filename}`);
        }

        if (missing.length > 0) {
            throw new MissingAssetsError(missing);
        }

        md = rewriteAllImageSrcs(md, mapping);

        let cover = input.cover ?? "";
        if (input.coverFile) {
            const meta = await this.http.uploadImageFile(input.coverFile);
            cover = meta.fullUrl ?? `/images/${meta.filename}`;
        }

        return this.http.createArticleFromMarkdown({
            title: input.title,
            slug: input.slug,
            summary: input.summary ?? "",
            tags: input.tags ?? [],
            keywords: input.keywords ?? [],
            language: input.language,
            mdContent: md,
            cover,
            published: input.published ?? false,
            __locale__: input.__locale__,
        });
    }
}
