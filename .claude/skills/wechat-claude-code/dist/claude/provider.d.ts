export interface QueryOptions {
    prompt: string;
    cwd: string;
    resume?: string;
    model?: string;
    systemPrompt?: string;
    images?: Array<{
        type: "image";
        source: {
            type: "base64";
            media_type: string;
            data: string;
        };
    }>;
    /** Called each time an assistant text chunk is produced (e.g. before/after tool calls). */
    onText?: (text: string) => Promise<void> | void;
    /** Called when an assistant turn ends, with its stop_reason
     *  ('tool_use' | 'end_turn' | 'max_tokens' | 'stop_sequence' | 'pause_turn' | ...).
     *  Use to decide whether the turn's text is interstitial or final answer. */
    onTurnEnd?: (stopReason: string) => Promise<void> | void;
    /** Optional abort controller to cancel the query (e.g. when user sends a new message). */
    abortController?: AbortController;
}
export interface QueryResult {
    text: string;
    sessionId: string;
    error?: string;
}
export interface StreamParserState {
    sessionId: string;
    textParts: string[];
    errorMessage?: string;
    trackingSkill: boolean;
    skillInputAccum: string;
}
export interface StreamParserCallbacks {
    onText?: (text: string) => void;
    onTurnEnd?: (stopReason: string) => void;
}
export declare function handleStreamLine(line: string, state: StreamParserState, callbacks: StreamParserCallbacks): void;
export declare function claudeQuery(options: QueryOptions): Promise<QueryResult>;
