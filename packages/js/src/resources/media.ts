import type { HttpClient } from "../client.js";
import type { ImageMetaInfo, ImageUploadOptions } from "../types.js";

export class MediaResource {
    constructor(private readonly http: HttpClient) {}

    uploadImage(
        file: Blob | Buffer | Uint8Array,
        filename: string,
        options?: ImageUploadOptions
    ): Promise<ImageMetaInfo> {
        return this.http.uploadImage(file, filename, options);
    }

    uploadImageFile(
        filePath: string,
        options?: ImageUploadOptions
    ): Promise<ImageMetaInfo> {
        return this.http.uploadImageFile(filePath, options);
    }
}
