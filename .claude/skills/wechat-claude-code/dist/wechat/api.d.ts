import type { GetUpdatesResp, SendMessageReq, GetUploadUrlResp, SendTypingReq, GetConfigResp } from './types.js';
export declare class WeChatApi {
    private readonly token;
    private readonly baseUrl;
    private readonly uin;
    private readonly nextSendTime;
    private static readonly MIN_SEND_INTERVAL;
    private static readonly RATE_LIMIT_COOLDOWN_MS;
    private static readonly CIRCUIT_THRESHOLD;
    private static readonly CIRCUIT_WINDOW_MS;
    private static readonly CIRCUIT_OPEN_MS;
    private readonly _rateLimitEvents;
    private _circuitUntil;
    private static readonly STALE_SESSION_PAUSE_MS;
    constructor(token: string, baseUrl?: string);
    private headers;
    private request;
    /** Long-poll for new messages. Timeout 35s for long-polling. */
    getUpdates(buf?: string): Promise<GetUpdatesResp>;
    /** Send a message to a user. Per-user rate limited, retries on rate-limit (ret: -2). */
    sendMessage(req: SendMessageReq): Promise<void>;
    /** True while the breaker is open (sends should fail fast). */
    private _isCircuitOpen;
    /** Record a rate-limit event and open the breaker if threshold is met. */
    private _tripCircuit;
    /** Fetch bot config (includes typing_ticket). */
    getConfig(ilinkUserId: string, contextToken?: string): Promise<GetConfigResp>;
    /** Send a typing indicator to a user. */
    sendTyping(req: SendTypingReq): Promise<void>;
    /** Get a presigned upload URL for media files. */
    getUploadUrl(req: import('./types.js').GetUploadUrlReq): Promise<GetUploadUrlResp>;
}
