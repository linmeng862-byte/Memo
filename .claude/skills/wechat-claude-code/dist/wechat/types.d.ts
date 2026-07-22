export declare enum MessageType {
    USER = 1,
    BOT = 2
}
export declare enum MessageItemType {
    TEXT = 1,
    IMAGE = 2,
    VOICE = 3,
    FILE = 4,
    VIDEO = 5
}
export declare enum MessageState {
    NEW = 0,
    GENERATING = 1,
    FINISH = 2
}
export interface CDNMedia {
    aes_key: string;
    encrypt_query_param: string;
    cdn_url?: string;
}
export interface TextItem {
    text: string;
}
export interface ImageItem {
    cdn_media?: CDNMedia;
    /** Alternative field name used by some API versions */
    aeskey?: string;
    media?: {
        encrypt_query_param: string;
        aes_key?: string;
        encrypt_type?: number;
    };
    url?: string;
    mid_size?: number;
    hd_size?: number;
}
export interface VoiceItem {
    media?: CDNMedia;
    /** 语音转文字内容 */
    text?: string;
}
export interface FileItem {
    cdn_media?: CDNMedia;
    media?: {
        encrypt_query_param: string;
        aes_key?: string;
        encrypt_type?: number;
    };
    file_name?: string;
    len?: string;
}
export interface VideoItem {
    cdn_media: CDNMedia;
}
export interface MessageItem {
    type: MessageItemType;
    text_item?: TextItem;
    image_item?: ImageItem;
    voice_item?: VoiceItem;
    file_item?: FileItem;
    video_item?: VideoItem;
}
export interface WeixinMessage {
    seq?: number;
    message_id?: number;
    from_user_id?: string;
    to_user_id?: string;
    create_time_ms?: number;
    message_type?: MessageType;
    message_state?: MessageState;
    item_list?: MessageItem[];
    context_token?: string;
}
export interface GetUpdatesReq {
    get_updates_buf?: string;
}
export interface GetUpdatesResp {
    ret?: number;
    retmsg?: string;
    sync_buf: string;
    get_updates_buf: string;
    msgs?: WeixinMessage[];
}
export interface OutboundMessage {
    from_user_id: string;
    to_user_id: string;
    client_id: string;
    message_type: MessageType;
    message_state: MessageState;
    context_token: string;
    item_list: MessageItem[];
}
export interface SendMessageReq {
    msg: OutboundMessage;
}
export declare const TypingStatus: {
    readonly TYPING: 1;
    readonly CANCEL: 2;
};
export interface SendTypingReq {
    ilink_user_id: string;
    typing_ticket: string;
    status: number;
}
export interface GetConfigResp {
    ret?: number;
    errmsg?: string;
    typing_ticket?: string;
}
export declare const UploadMediaType: {
    readonly IMAGE: 1;
    readonly VIDEO: 2;
    readonly FILE: 3;
    readonly VOICE: 4;
};
export interface GetUploadUrlReq {
    filekey: string;
    media_type: number;
    to_user_id: string;
    rawsize: number;
    rawfilemd5: string;
    filesize: number;
    no_need_thumb: boolean;
    aeskey: string;
    base_info: {
        channel_version: string;
        bot_agent: string;
    };
}
export interface GetUploadUrlResp {
    ret?: number;
    upload_param?: string;
    upload_full_url?: string;
}
