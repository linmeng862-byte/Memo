export type SessionState = 'idle' | 'processing';
export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
}
export interface Session {
    sdkSessionId?: string;
    previousSdkSessionId?: string;
    workingDirectory: string;
    model?: string;
    state: SessionState;
    chatHistory: ChatMessage[];
    maxHistoryLength?: number;
}
export declare function createSessionStore(): {
    load: (accountId: string) => Session;
    save: (accountId: string, session: Session) => void;
    clear: (accountId: string, currentSession?: Session) => Session;
    addChatMessage: (session: Session, role: "user" | "assistant", content: string) => void;
    getChatHistoryText: (session: Session, limit?: number) => string;
};
