import { WeChatApi } from './api.js';
export declare function createSender(api: WeChatApi, botAccountId: string): {
    sendText: (toUserId: string, contextToken: string, text: string) => Promise<void>;
    startTyping: (toUserId: string, contextToken: string) => () => void;
    sendFile: (toUserId: string, contextToken: string, filePath: string) => Promise<void>;
};
