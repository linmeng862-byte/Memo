import { WeChatApi } from './api.js';
export interface UploadedMedia {
    mediaType: 'image' | 'file';
    encryptQueryParam: string;
    aesKeyHex: string;
    fileName: string;
    fileSize: number;
    rawSize: number;
}
export declare function isImageFile(filePath: string): boolean;
export declare function uploadFile(api: WeChatApi, toUserId: string, filePath: string): Promise<UploadedMedia>;
