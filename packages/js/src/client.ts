import { readFile } from "node:fs/promises";
import path from "node:path";
import type {
    ApiResult,
    Article,
    ArticleListPayload,
    ArticleListQuery,
    ClientOptions,
    FromMarkdownPayload,
    FromMarkdownRequest,
    ImageMetaInfo,
    ImageUploadOptions,
    UpdateFromMarkdownRequest,
    UpdateMetadataInput,
} from "./types.js";

export class ApiError extends Error {
    readonly code: number;
    readonly payload: unknown;

    constructor(message: string, code: number, payload: unknown = {}) {
        super(message);
        this.name = "ApiError";
        this.code = code;
        this.payload = payload;
    }
}

function joinUrl(base: string, pathname: string): string {
    const b = base.replace(/\/+$/, "");
    const p = pathname.startsWith("/") ? pathname : `/${pathname}`;
    return `${b}${p}`;
}

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Infer image MIME from filename (Node Buffer uploads default to octet-stream). */
export function mimeTypeFromFilename(filename: string): string {
    switch (path.extname(filename).toLowerCase()) {
        case ".jpg":
        case ".jpeg":
            return "image/jpeg";
        case ".png":
            return "image/png";
        case ".webp":
            return "image/webp";
        case ".gif":
            return "image/gif";
        case ".svg":
            return "image/svg+xml";
        default:
            return "application/octet-stream";
    }
}

export class HttpClient {
    readonly baseUrl: string;
    readonly apiKey: string;
    readonly authStyle: "api-key" | "bearer";
    readonly maxRetries: number;

    constructor(options: ClientOptions) {
        if (!options.baseUrl?.trim()) {
            throw new Error("baseUrl is required");
        }
        if (!options.apiKey?.trim()) {
            throw new Error("apiKey is required");
        }
        this.baseUrl = options.baseUrl.trim();
        this.apiKey = options.apiKey.trim();
        this.authStyle = options.authStyle ?? "api-key";
        this.maxRetries = options.maxRetries ?? 2;
    }

    private authHeaders(): Record<string, string> {
        if (this.authStyle === "bearer") {
            return { Authorization: `Bearer ${this.apiKey}` };
        }
        return { "x-api-key": this.apiKey };
    }

    async requestJson<T>(
        method: string,
        pathname: string,
        init: {
            body?: BodyInit | null;
            headers?: Record<string, string>;
            json?: unknown;
        } = {}
    ): Promise<ApiResult<T>> {
        const headers: Record<string, string> = {
            ...this.authHeaders(),
            ...init.headers,
        };
        let body = init.body ?? null;
        if (init.json !== undefined) {
            headers["Content-Type"] = "application/json";
            body = JSON.stringify(init.json);
        }

        let lastError: unknown;
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const res = await fetch(joinUrl(this.baseUrl, pathname), {
                    method,
                    headers,
                    body,
                });
                const data = (await res.json()) as ApiResult<T>;
                if (!res.ok || data.code !== 200) {
                    const retryable =
                        res.status >= 500 || data.code >= 500;
                    if (retryable && attempt < this.maxRetries) {
                        await sleep(200 * (attempt + 1));
                        continue;
                    }
                    throw new ApiError(
                        data.message || `HTTP ${res.status}`,
                        data.code ?? res.status,
                        data.payload
                    );
                }
                return data;
            } catch (err) {
                lastError = err;
                if (err instanceof ApiError) throw err;
                if (attempt < this.maxRetries) {
                    await sleep(200 * (attempt + 1));
                    continue;
                }
                throw err;
            }
        }
        throw lastError instanceof Error
            ? lastError
            : new Error(String(lastError));
    }

    async uploadImage(
        file: Blob | Buffer | Uint8Array,
        filename: string,
        options?: ImageUploadOptions
    ): Promise<ImageMetaInfo> {
        const form = new FormData();
        const blob =
            file instanceof Blob
                ? file
                : new Blob([Uint8Array.from(file as Uint8Array)], {
                      type: mimeTypeFromFilename(filename),
                  });
        form.append("file", blob, filename);
        if (options) {
            form.append("options", JSON.stringify(options));
        }
        const result = await this.requestJson<ImageMetaInfo>(
            "POST",
            "/api/m/images",
            { body: form }
        );
        return result.payload;
    }

    async uploadImageFile(
        filePath: string,
        options?: ImageUploadOptions
    ): Promise<ImageMetaInfo> {
        const buf = await readFile(filePath);
        return this.uploadImage(buf, path.basename(filePath), options);
    }

    async createArticleFromMarkdown(
        body: FromMarkdownRequest
    ): Promise<FromMarkdownPayload> {
        const result = await this.requestJson<FromMarkdownPayload>(
            "POST",
            "/api/m/articles/from-markdown",
            { json: body }
        );
        return result.payload;
    }

    async updateArticleFromMarkdown(
        body: UpdateFromMarkdownRequest
    ): Promise<FromMarkdownPayload> {
        const result = await this.requestJson<FromMarkdownPayload>(
            "PUT",
            "/api/m/articles/from-markdown",
            { json: body }
        );
        return result.payload;
    }

    async getArticle(
        slug: string,
        id: string,
        options: { includeMdContent?: boolean } = {}
    ): Promise<Article> {
        const q = new URLSearchParams();
        if (options.includeMdContent) q.set("includeMdContent", "true");
        const qs = q.toString();
        const path = `/api/m/articles/${encodeURIComponent(slug)}/${encodeURIComponent(id)}`;
        const result = await this.requestJson<Article>(
            "GET",
            qs ? `${path}?${qs}` : path
        );
        return result.payload;
    }

    async getArticleBySlug(
        slug: string,
        locale: string,
        options: { includeMdContent?: boolean } = {}
    ): Promise<Article> {
        const q = new URLSearchParams({ locale });
        if (options.includeMdContent) q.set("includeMdContent", "true");
        const result = await this.requestJson<Article>(
            "GET",
            `/api/m/articles/by-slug/${encodeURIComponent(slug)}?${q}`
        );
        return result.payload;
    }

    /**
     * List article metadata. `query.published` must be
     * `"published" | "draft" | "all"` (CMS enum), not a boolean string.
     */
    async listArticles(
        query: ArticleListQuery = {}
    ): Promise<ArticleListPayload> {
        // CMS validates query strictly: pageIndex/pageSize must be present.
        const q = new URLSearchParams({
            pageIndex: String(query.pageIndex ?? 1),
            pageSize: String(query.pageSize ?? 10),
        });
        if (query.locale) q.set("locale", query.locale);
        if (query.tag) q.set("tag", query.tag);
        if (query.searchTerm) q.set("searchTerm", query.searchTerm);
        if (query.published) q.set("published", query.published);
        const result = await this.requestJson<ArticleListPayload>(
            "GET",
            `/api/m/articles?${q}`
        );
        return result.payload;
    }

    async updateArticle(
        body: UpdateMetadataInput & { content?: unknown[] }
    ): Promise<{ slug: string; language: string }> {
        const result = await this.requestJson<{
            slug: string;
            language: string;
        }>("PUT", "/api/m/articles", { json: body });
        return result.payload;
    }

    async deleteArticle(
        slug: string,
        id: string
    ): Promise<{ slug: string; id: string }> {
        const result = await this.requestJson<{ slug: string; id: string }>(
            "DELETE",
            `/api/m/articles/${encodeURIComponent(slug)}/${encodeURIComponent(id)}`
        );
        return result.payload;
    }

    async deleteArticleBySlug(
        slug: string,
        locale: string
    ): Promise<{ slug: string; id: string; locale: string }> {
        const q = new URLSearchParams({ locale });
        const result = await this.requestJson<{
            slug: string;
            id: string;
            locale: string;
        }>(
            "DELETE",
            `/api/m/articles/by-slug/${encodeURIComponent(slug)}?${q}`
        );
        return result.payload;
    }

    async deleteImage(filename: string): Promise<unknown> {
        const result = await this.requestJson<unknown>(
            "DELETE",
            `/api/m/images/${encodeURIComponent(filename)}`
        );
        return result.payload;
    }
}
