import assert from 'node:assert';
import { syncEngine } from '../../src/services/offlineSyncEngine.js';
import { offlineStorage } from '../../src/utils/indexedDB.js';

console.log('--- RUNNING OFFLINE & STATE SYNCHRONIZATION TESTS ---');

// 1. Initial Sync Engine State
{
  assert.ok(syncEngine, 'syncEngine service must be instantiated');
  assert.strictEqual(typeof syncEngine.queueOperation, 'function', 'Must provide queueOperation');
  assert.strictEqual(typeof syncEngine.syncPendingMutations, 'function', 'Must provide syncPendingMutations');
  assert.strictEqual(typeof syncEngine.subscribe, 'function', 'Must provide subscribe');
  console.log('✓ Offline sync engine API surface validated.');
}

// 2. Action Enqueue and Queue Retention
{
  await offlineStorage.clearSyncQueue();
  await syncEngine.queueOperation('CREATE_TASK', { id: 'offline-task-1', title: 'Draft Strategy Offline', priority: 'High' });
  const queue = await offlineStorage.getSyncQueue();
  assert.ok(queue.length >= 1, 'Queue must contain the enqueued action');
  const enqueued = queue[queue.length - 1];
  assert.strictEqual(enqueued.type, 'CREATE_TASK');
  assert.strictEqual(enqueued.payload.title, 'Draft Strategy Offline');
  console.log('✓ Action enqueueing and queue inspection verified.');
}

// 3. Online Subscription Listener
{
  let notifiedStatus = null;
  const unsubscribe = syncEngine.subscribe((isOnline) => {
    notifiedStatus = isOnline;
  });

  assert.strictEqual(typeof unsubscribe, 'function', 'Subscribe must return unsubscribe cleanup function');
  syncEngine.notify();
  assert.strictEqual(typeof notifiedStatus, 'boolean');
  unsubscribe();
  console.log('✓ Subscriber listener registration and cleanup verified.');
}

console.log('--- ALL OFFLINE & STATE SYNCHRONIZATION TESTS PASSED ---');
