/** Types aligned with spec/openapi.yaml */

/** Site-configured language tag (e.g. zh-CN, en-US, ja-JP). Use listLocales(). */
export type Locale = string;

export type ApiResult<T = unknown> = {
    code: number;
    message: string;
    payload: T;
    tt?: number;
};

export type ImageUploadOptions = {
    quality?: number;
    maxWidth?: number;
    maxHeight?: number;
    enableWebP?: boolean;
};

export type ImageMetaInfo = {
    filename: string;
    originalName: string;
    size: number;
    width: number;
    height: number;
    mimeType: string;
    uploadedAt: string;
    fullUrl?: string;
    title?: string;
    description?: string;
    tags?: string[];
    altText?: string;
};

export type FromMarkdownRequest = {
    title: string;
    slug: string;
    summary?: string;
    tags?: string[];
    keywords?: string[];
    language: Locale;
    mdContent?: string;
    "md-content"?: string;
    cover?: string;
    published?: boolean;
    __locale__?: string;
};

export type FromMarkdownPayload = {
    id: string;
    slug: string;
    locale: Locale;
};

export type ChannelItemType = "tag" | "page";

export type ChannelItem = {
    id: string;
    type: ChannelItemType;
    href: string;
    tag?: string;
    icon?: string;
};

export type LocaleInfo = {
    code: Locale;
    name: string;
    nativeName: string;
    englishName: string;
    flag: string;
};

export type ClientOptions = {
    /** CMS origin, e.g. https://cms.example.com */
    baseUrl: string;
    /** API token (bsc_...) */
    apiKey: string;
    /** Prefer Bearer instead of x-api-key */
    authStyle?: "api-key" | "bearer";
    /** fetch timeout hint — not enforced by undici by default */
    maxRetries?: number;
};

export type PublishFromMarkdownInput = {
    title: string;
    slug: string;
    summary?: string;
    tags?: string[];
    keywords?: string[];
    language: Locale;
    /** Inline markdown body */
    mdContent?: string;
    /** Path to a .md file (alternative to mdContent) */
    mdFile?: string;
    /**
     * Directory used to resolve relative image paths in the markdown
     * (e.g. "./posts/assets"). Required.
     */
    assetsDir: string;
    /** Cover as already-hosted URL or /images/... */
    cover?: string;
    /** Local cover file path — uploaded first */
    coverFile?: string;
    published?: boolean;
    __locale__?: string;
};
