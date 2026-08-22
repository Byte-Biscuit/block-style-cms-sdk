import { HttpClient } from "./client.js";
import { ArticlesResource } from "./resources/articles.js";
import { MediaResource } from "./resources/media.js";
import type { ClientOptions } from "./types.js";

export class BlockStyleCmsClient {
    readonly http: HttpClient;
    readonly media: MediaResource;
    readonly articles: ArticlesResource;

    constructor(options: ClientOptions) {
        this.http = new HttpClient(options);
        this.media = new MediaResource(this.http);
        this.articles = new ArticlesResource(this.http);
    }
}

export { ApiError, HttpClient, mimeTypeFromFilename } from "./client.js";
export { MissingAssetsError } from "./resources/articles.js";
export {
    collectRelativeImageSrcs,
    isRelativeImageSrc,
    isSkippableImageSrc,
    rewriteAllImageSrcs,
    rewriteImageSrc,
    resolveImagePath,
} from "./markdown/images.js";
export type * from "./types.js";
