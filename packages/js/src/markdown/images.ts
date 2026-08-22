import path from "node:path";

const MD_IMAGE_RE = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
const HTML_IMG_RE = /<img\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi;

export function isSkippableImageSrc(src: string): boolean {
    const s = src.trim();
    if (!s) return false;
    if (s.startsWith("/images/")) return true;
    if (/^https?:\/\//i.test(s)) return true;
    return false;
}

export function isRelativeImageSrc(src: string): boolean {
    const s = src.trim();
    if (!s) return true;
    if (isSkippableImageSrc(s)) return false;
    if (s.startsWith("/")) return false;
    return true;
}

/** Collect unique relative image sources from markdown. */
export function collectRelativeImageSrcs(md: string): string[] {
    const found = new Set<string>();
    for (const re of [MD_IMAGE_RE, HTML_IMG_RE]) {
        re.lastIndex = 0;
        let match: RegExpExecArray | null;
        while ((match = re.exec(md)) !== null) {
            const src = (match[2] ?? match[1] ?? "").trim();
            if (isRelativeImageSrc(src)) found.add(src);
        }
    }
    return [...found];
}

/**
 * Resolve a relative md image path against assetsDir.
 * Strips a leading `./` or `assets/` prefix when the file lives directly under assetsDir.
 */
export function resolveImagePath(assetsDir: string, src: string): string {
    const cleaned = src.replace(/^\.\//, "");
    const underAssets = cleaned.replace(/^assets\//, "");
    const candidates = [
        path.resolve(assetsDir, underAssets),
        path.resolve(assetsDir, cleaned),
        path.resolve(assetsDir, path.basename(cleaned)),
    ];
    return candidates[0];
}

export function rewriteImageSrc(
    md: string,
    fromSrc: string,
    toSrc: string
): string {
    const escaped = fromSrc.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const mdRe = new RegExp(
        `(!\\[[^\\]]*\\]\\()${escaped}((?:\\s+"[^"]*")?\\))`,
        "g"
    );
    let out = md.replace(mdRe, `$1${toSrc}$2`);
    const htmlRe = new RegExp(
        `(<img\\b[^>]*\\bsrc=["'])${escaped}(["'])`,
        "gi"
    );
    out = out.replace(htmlRe, `$1${toSrc}$2`);
    return out;
}

export function rewriteAllImageSrcs(
    md: string,
    mapping: Map<string, string>
): string {
    let out = md;
    for (const [from, to] of mapping) {
        out = rewriteImageSrc(out, from, to);
    }
    return out;
}
