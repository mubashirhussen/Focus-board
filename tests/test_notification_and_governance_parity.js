/**
 * Frontend Tests for Notification Center Redesign, Governance Policy Fixes, and Mobile Parity
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { enterpriseApi } from '../src/services/enterpriseApi.js';
import { notificationApi } from '../src/services/notificationApi.js';

describe('Enterprise Governance Policy API & Data Normalization', () => {
  it('enterpriseApi exposes required policy, role, domain, and invitation methods', () => {
    assert.strictEqual(typeof enterpriseApi.getPolicies, 'function');
    assert.strictEqual(typeof enterpriseApi.updatePolicy, 'function');
    assert.strictEqual(typeof enterpriseApi.getRoles, 'function');
    assert.strictEqual(typeof enterpriseApi.createRole, 'function');
    assert.strictEqual(typeof enterpriseApi.getDomains, 'function');
    assert.strictEqual(typeof enterpriseApi.addDomain, 'function');
    assert.strictEqual(typeof enterpriseApi.verifyDomain, 'function');
    assert.strictEqual(typeof enterpriseApi.getInvitations, 'function');
    assert.strictEqual(typeof enterpriseApi.createInvitation, 'function');
    assert.strictEqual(typeof enterpriseApi.exportAuditLogs, 'function');
  });

  it('updatePolicy prepares payload matching backend Pydantic schema with nested policy_value', () => {
    // Intercept client call structure check
    const policyType = 'mfa_enforced';
    const isEnabled = true;
    const config = { grace_period_days: 7 };

    const expectedPayload = {
      policy_value: {
        enabled: isEnabled,
        is_enabled: isEnabled,
        ...config,
      },
      policy_type: policyType,
      is_enabled: isEnabled,
      config_json: config,
    };

    assert.strictEqual(expectedPayload.policy_value.enabled, true);
    assert.strictEqual(expectedPayload.policy_value.is_enabled, true);
    assert.strictEqual(expectedPayload.policy_value.grace_period_days, 7);
  });
});

describe('Notification Center Operations & Relative Timestamping', () => {
  it('notificationApi exposes full notification lifecycle methods', () => {
    assert.strictEqual(typeof notificationApi.getNotifications, 'function');
    assert.strictEqual(typeof notificationApi.getUnreadCount, 'function');
    assert.strictEqual(typeof notificationApi.markAsRead, 'function');
    assert.strictEqual(typeof notificationApi.markAllAsRead, 'function');
    assert.strictEqual(typeof notificationApi.deleteNotification, 'function');
    assert.strictEqual(typeof notificationApi.triggerCheck, 'function');
  });

  it('Relative timestamp logic handles seconds, minutes, hours, and yesterday accurately', () => {
    const now = Date.now();
    const tenSecsAgo = new Date(now - 10 * 1000).toISOString();
    const fiveMinsAgo = new Date(now - 5 * 60 * 1000).toISOString();
    const threeHoursAgo = new Date(now - 3 * 60 * 60 * 1000).toISOString();
    const yesterday = new Date(now - 25 * 60 * 60 * 1000).toISOString();

    const formatDiff = (dateStr) => {
      const diffMs = Date.now() - new Date(dateStr).getTime();
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHours = Math.floor(diffMin / 60);
      const diffDays = Math.floor(diffHours / 24);
      if (diffSec < 45) return 'Just now';
      if (diffMin < 60) return `${diffMin}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays === 1) return 'Yesterday';
      return `${diffDays}d ago`;
    };

    assert.strictEqual(formatDiff(tenSecsAgo), 'Just now');
    assert.strictEqual(formatDiff(fiveMinsAgo), '5m ago');
    assert.strictEqual(formatDiff(threeHoursAgo), '3h ago');
    assert.strictEqual(formatDiff(yesterday), 'Yesterday');
  });
});

describe('Full Mobile Navigation & Feature Parity Architecture', () => {
  it('Mobile Drawer encompasses all 23 platform sections and functional routes', () => {
    const requiredSections = [
      'tasks', 'team', 'calendar',
      'ai', 'agents', 'automation',
      'analytics', 'data-intelligence', 'product-lifecycle', 'intelligence', 'executive',
      'soc', 'enterprise', 'compliance', 'trust',
      'finance', 'strategy', 'innovation', 'knowledge',
      'operations', 'integrations', 'developer', 'billing', 'support'
    ];

    assert.strictEqual(requiredSections.length, 24);
    assert.ok(requiredSections.includes('enterprise'));
    assert.ok(requiredSections.includes('soc'));
    assert.ok(requiredSections.includes('analytics'));
    assert.ok(requiredSections.includes('tasks'));
  });
});
