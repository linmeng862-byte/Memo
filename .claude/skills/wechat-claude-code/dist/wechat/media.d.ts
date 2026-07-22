import type { MessageItem } from './types.js';
/**
 * Download a CDN image, decrypt it, and return a base64 data URI.
 * Returns null on failure.
 */
export declare function downloadImage(item: MessageItem): Promise<string | null>;
export declare function extractText(item: MessageItem): string;
/**
 * Find the first IMAGE type item in a list.
 */
export declare function extractFirstImageUrl(items?: MessageItem[]): MessageItem | undefined;
/**
 * Find the first FILE type item in a list.
 */
export declare function extractFirstFileItem(items?: MessageItem[]): MessageItem | undefined;
/**
 * Download a CDN file, decrypt it, and save to a temp directory.
 * Returns the local file path, or null on failure.
 */
export declare function downloadFile(item: MessageItem): Promise<string | null>;
