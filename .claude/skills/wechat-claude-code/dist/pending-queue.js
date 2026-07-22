import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { DATA_DIR } from './constants.js';
import { logger } from './logger.js';
const QUEUE_DIR = join(DATA_DIR, 'pending-queue');
function queuePath(accountId) {
    return join(QUEUE_DIR, `${accountId}.json`);
}
function ensureDir() {
    if (!existsSync(QUEUE_DIR)) {
        mkdirSync(QUEUE_DIR, { recursive: true });
    }
}
export function loadPendingQueue(accountId) {
    try {
        const path = queuePath(accountId);
        if (!existsSync(path))
            return [];
        const raw = readFileSync(path, 'utf-8');
        const data = JSON.parse(raw);
        return Array.isArray(data) ? data : [];
    }
    catch (err) {
        logger.warn('Failed to load pending queue', {
            accountId,
            error: err instanceof Error ? err.message : String(err),
        });
        return [];
    }
}
export function savePendingQueue(accountId, items) {
    try {
        ensureDir();
        writeFileSync(queuePath(accountId), JSON.stringify(items, null, 2), 'utf-8');
    }
    catch (err) {
        logger.warn('Failed to save pending queue', {
            accountId,
            error: err instanceof Error ? err.message : String(err),
        });
    }
}
export function appendPending(accountId, item) {
    const items = loadPendingQueue(accountId);
    items.push(item);
    savePendingQueue(accountId, items);
    return items;
}
export function clearPending(accountId) {
    savePendingQueue(accountId, []);
}
export function hasPending(accountId) {
    return loadPendingQueue(accountId).length > 0;
}
