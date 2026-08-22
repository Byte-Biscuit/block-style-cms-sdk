import type { HttpClient } from "../client.js";
import type { ChannelItem, LocaleInfo } from "../types.js";

export class ContentResource {
    constructor(private readonly http: HttpClient) {}

    async listChannels(): Promise<ChannelItem[]> {
        const result = await this.http.requestJson<ChannelItem[]>(
            "GET",
            "/api/m/channels"
        );
        return result.payload;
    }

    async listLocales(): Promise<LocaleInfo[]> {
        const result = await this.http.requestJson<LocaleInfo[]>(
            "GET",
            "/api/m/locales"
        );
        return result.payload;
    }
}
