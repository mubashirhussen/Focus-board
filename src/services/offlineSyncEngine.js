import { offlineStorage } from '../utils/indexedDB.js';
import { taskApi } from './taskApi.js';

class OfflineSyncEngine {
  constructor() {
    this.isOnline =
      typeof navigator !== 'undefined' && typeof navigator.onLine === 'boolean'
        ? navigator.onLine
        : true;
    this.listeners = new Set();
    this.init();
  }

  init() {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      this.isOnline = true;
      this.notify();
      this.syncPendingMutations();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.notify();
    });
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    this.listeners.forEach((fn) => fn(this.isOnline));
  }

  async queueOperation(type, payload) {
    await offlineStorage.enqueueSync({ type, payload });
    this.notify();
  }

  async syncPendingMutations() {
    if (!this.isOnline) return;

    const queue = await offlineStorage.getSyncQueue();
    if (queue.length === 0) return;

    console.info(`[SyncEngine] Processing ${queue.length} pending offline mutations...`);

    for (const item of queue) {
      try {
        if (item.type === 'CREATE_TASK') {
          await taskApi.createTask(item.payload);
        } else if (item.type === 'UPDATE_TASK') {
          await taskApi.updateTask(item.payload.id, item.payload);
        } else if (item.type === 'DELETE_TASK') {
          await taskApi.deleteTask(item.payload.id);
        }
      } catch (err) {
        console.warn(`[SyncEngine] Failed to process ${item.type}:`, err);
      }
    }

    await offlineStorage.clearSyncQueue();
    this.notify();
    console.info('[SyncEngine] Offline sync completed.');
  }
}

export const syncEngine = new OfflineSyncEngine();
