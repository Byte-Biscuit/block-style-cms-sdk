import { describe, expect, it } from "vitest";
import { mimeTypeFromFilename } from "../src/client.js";

describe("mimeTypeFromFilename", () => {
    it("maps common image extensions", () => {
        expect(mimeTypeFromFilename("a.png")).toBe("image/png");
        expect(mimeTypeFromFilename("b.jpg")).toBe("image/jpeg");
        expect(mimeTypeFromFilename("c.jpeg")).toBe("image/jpeg");
        expect(mimeTypeFromFilename("d.webp")).toBe("image/webp");
        expect(mimeTypeFromFilename("e.gif")).toBe("image/gif");
        expect(mimeTypeFromFilename("f.svg")).toBe("image/svg+xml");
    });
});
