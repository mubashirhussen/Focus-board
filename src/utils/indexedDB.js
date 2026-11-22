// IndexedDB wrapper for offline task persistence and mutation queue
const DB_NAME = 'focusboard_offline_db';
const DB_VERSION = 1;

const inMemoryStorage = {
  tasks: [],
  syncQueue: [],
};

function openDB() {
  if (typeof indexedDB === 'undefined') {
    return Promise.resolve(null);
  }
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('tasks')) {
        db.createObjectStore('tasks', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('sync_queue')) {
        db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export const offlineStorage = {
  async saveTasks(tasks) {
    try {
      const db = await openDB();
      if (!db) {
        inMemoryStorage.tasks = [...tasks];
        return true;
      }
      const tx = db.transaction('tasks', 'readwrite');
      const store = tx.objectStore('tasks');
      store.clear();
      tasks.forEach((t) => store.put(t));
      return new Promise((resolve) => { tx.oncomplete = () => resolve(true); });
    } catch (err) {
      console.warn('Failed to save to IndexedDB:', err);
      return false;
    }
  },

  async getTasks() {
    try {
      const db = await openDB();
      if (!db) {
        return [...inMemoryStorage.tasks];
      }
      const tx = db.transaction('tasks', 'readonly');
      const store = tx.objectStore('tasks');
      const req = store.getAll();
      return new Promise((resolve) => {
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    } catch (err) {
      return [];
    }
  },

  async enqueueSync(operation) {
    try {
      const db = await openDB();
      if (!db) {
        inMemoryStorage.syncQueue.push({ ...operation, timestamp: Date.now() });
        return true;
      }
      const tx = db.transaction('sync_queue', 'readwrite');
      const store = tx.objectStore('sync_queue');
      store.add({ ...operation, timestamp: Date.now() });
      return new Promise((resolve) => { tx.oncomplete = () => resolve(true); });
    } catch (err) {
      console.warn('Failed to queue offline operation:', err);
      return false;
    }
  },

  async getSyncQueue() {
    try {
      const db = await openDB();
      if (!db) {
        return [...inMemoryStorage.syncQueue];
      }
      const tx = db.transaction('sync_queue', 'readonly');
      const store = tx.objectStore('sync_queue');
      const req = store.getAll();
      return new Promise((resolve) => {
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    } catch (err) {
      return [];
    }
  },

  async clearSyncQueue() {
    try {
      const db = await openDB();
      if (!db) {
        inMemoryStorage.syncQueue = [];
        return true;
      }
      const tx = db.transaction('sync_queue', 'readwrite');
      tx.objectStore('sync_queue').clear();
      return new Promise((resolve) => { tx.oncomplete = () => resolve(true); });
    } catch (err) {
      return false;
    }
  },
};
