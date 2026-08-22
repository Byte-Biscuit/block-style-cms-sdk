import { describe, expect, it } from "vitest";
import {
    collectRelativeImageSrcs,
    isRelativeImageSrc,
    isSkippableImageSrc,
    rewriteAllImageSrcs,
    rewriteImageSrc,
} from "../src/markdown/images.js";

describe("image src helpers", () => {
    it("detects skippable and relative srcs", () => {
        expect(isSkippableImageSrc("/images/a.webp")).toBe(true);
        expect(isSkippableImageSrc("https://cdn.example/a.png")).toBe(true);
        expect(isRelativeImageSrc("./assets/x.png")).toBe(true);
        expect(isRelativeImageSrc("assets/x.png")).toBe(true);
        expect(isRelativeImageSrc("/images/x.webp")).toBe(false);
    });

    it("collects relative markdown and html images", () => {
        const md = `
![a](./assets/a.png)
![b](/images/b.webp)
![c](https://cdn.example/c.png)
<img src="assets/d.jpg" />
`;
        expect(collectRelativeImageSrcs(md).sort()).toEqual([
            "./assets/a.png",
            "assets/d.jpg",
        ]);
    });

    it("rewrites markdown image src", () => {
        const md = "before ![alt](./assets/a.png) after";
        expect(rewriteImageSrc(md, "./assets/a.png", "/images/a.webp")).toBe(
            "before ![alt](/images/a.webp) after"
        );
    });

    it("rewrites all mapped srcs", () => {
        const md = "![a](./assets/a.png) and ![b](assets/b.png)";
        const out = rewriteAllImageSrcs(
            md,
            new Map([
                ["./assets/a.png", "/images/a.webp"],
                ["assets/b.png", "/images/b.webp"],
            ])
        );
        expect(out).toContain("/images/a.webp");
        expect(out).toContain("/images/b.webp");
        expect(out).not.toContain("./assets/");
    });
});
