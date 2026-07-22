export interface PendingItem {
    text: string;
    role: 'interstitial' | 'final';
    queuedAt: number;
}
export declare function loadPendingQueue(accountId: string): PendingItem[];
export declare function savePendingQueue(accountId: string, items: PendingItem[]): void;
export declare function appendPending(accountId: string, item: PendingItem): PendingItem[];
export declare function clearPending(accountId: string): void;
export declare function hasPending(accountId: string): boolean;
