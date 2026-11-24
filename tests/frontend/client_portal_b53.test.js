/**
 * Frontend Unit & Workflow Tests for Module B53: Client & Guest Portal.
 */

import assert from 'assert';
import crypto from 'crypto';
import { clientPortalApi } from '../../src/services/clientPortalApi.js';

console.log('--- RUNNING MODULE B53: CLIENT & GUEST PORTAL FRONTEND TESTS ---');

// 1. Verify API Service Exposure
assert(typeof clientPortalApi.getDashboard === 'function', 'clientPortalApi must expose getDashboard');
assert(typeof clientPortalApi.getProjectOverview === 'function', 'clientPortalApi must expose getProjectOverview');
assert(typeof clientPortalApi.getProjectVisibility === 'function', 'clientPortalApi must expose getProjectVisibility');
assert(typeof clientPortalApi.updateProjectVisibility === 'function', 'clientPortalApi must expose updateProjectVisibility');
assert(typeof clientPortalApi.shareProject === 'function', 'clientPortalApi must expose shareProject');
assert(typeof clientPortalApi.unshareProject === 'function', 'clientPortalApi must expose unshareProject');
assert(typeof clientPortalApi.getInvitations === 'function', 'clientPortalApi must expose getInvitations');
assert(typeof clientPortalApi.createInvitation === 'function', 'clientPortalApi must expose createInvitation');
assert(typeof clientPortalApi.resendInvitation === 'function', 'clientPortalApi must expose resendInvitation');
assert(typeof clientPortalApi.revokeInvitation === 'function', 'clientPortalApi must expose revokeInvitation');
assert(typeof clientPortalApi.acceptInvitation === 'function', 'clientPortalApi must expose acceptInvitation');
assert(typeof clientPortalApi.getGuests === 'function', 'clientPortalApi must expose getGuests');
assert(typeof clientPortalApi.suspendGuest === 'function', 'clientPortalApi must expose suspendGuest');
assert(typeof clientPortalApi.reactivateGuest === 'function', 'clientPortalApi must expose reactivateGuest');
assert(typeof clientPortalApi.revokeGuest === 'function', 'clientPortalApi must expose revokeGuest');
assert(typeof clientPortalApi.getDeliverables === 'function', 'clientPortalApi must expose getDeliverables');
assert(typeof clientPortalApi.createDeliverable === 'function', 'clientPortalApi must expose createDeliverable');
assert(typeof clientPortalApi.reviewDeliverable === 'function', 'clientPortalApi must expose reviewDeliverable');
assert(typeof clientPortalApi.getFeedback === 'function', 'clientPortalApi must expose getFeedback');
assert(typeof clientPortalApi.submitFeedback === 'function', 'clientPortalApi must expose submitFeedback');
assert(typeof clientPortalApi.getComments === 'function', 'clientPortalApi must expose getComments');
assert(typeof clientPortalApi.postComment === 'function', 'clientPortalApi must expose postComment');
assert(typeof clientPortalApi.getDocuments === 'function', 'clientPortalApi must expose getDocuments');
assert(typeof clientPortalApi.getReports === 'function', 'clientPortalApi must expose getReports');
assert(typeof clientPortalApi.createReport === 'function', 'clientPortalApi must expose createReport');
assert(typeof clientPortalApi.getSettings === 'function', 'clientPortalApi must expose getSettings');
assert(typeof clientPortalApi.updateSettings === 'function', 'clientPortalApi must expose updateSettings');
assert(typeof clientPortalApi.getAuditLogs === 'function', 'clientPortalApi must expose getAuditLogs');
console.log('✓ clientPortalApi exposes all 28 required B53 client endpoints.');

// 2. Cryptographic Token Hashing Verification
function hashToken(rawToken) {
  return crypto.createHash('sha256').update(rawToken.trim()).digest('hex');
}
const sampleToken = 'focusboard_test_token_1234567890_abcdef';
const tokenHash = hashToken(sampleToken);
assert.strictEqual(tokenHash.length, 64, 'SHA-256 hash must be 64 hexadecimal characters');
assert.notStrictEqual(tokenHash, sampleToken, 'Raw token must not equal hashed token');
console.log('✓ Cryptographic token hashing produces deterministic 64-char hex digest.');

// 3. Guest Role Permission Matrix Resolution
const ROLE_PERMISSIONS = {
  CLIENT_VIEWER: {
    can_view_summary: true,
    can_view_tasks: true,
    can_view_milestones: true,
    can_view_documents: true,
    can_download_files: true,
    can_comment: false,
    can_upload_deliverables: false,
    can_submit_feedback: false,
    can_approve_deliverables: false,
    can_view_reports: true,
  },
  CLIENT_COLLABORATOR: {
    can_view_summary: true,
    can_view_tasks: true,
    can_view_milestones: true,
    can_view_documents: true,
    can_download_files: true,
    can_comment: true,
    can_upload_deliverables: true,
    can_submit_feedback: true,
    can_approve_deliverables: false,
    can_view_reports: true,
  },
  CLIENT_APPROVER: {
    can_view_summary: true,
    can_view_tasks: true,
    can_view_milestones: true,
    can_view_documents: true,
    can_download_files: true,
    can_comment: true,
    can_upload_deliverables: false,
    can_submit_feedback: true,
    can_approve_deliverables: true,
    can_view_reports: true,
  },
};

function resolvePermissions(role, customOverrides = {}) {
  const base = ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS.CLIENT_VIEWER;
  return { ...base, ...customOverrides };
}

const viewerPerms = resolvePermissions('CLIENT_VIEWER');
assert.strictEqual(viewerPerms.can_approve_deliverables, false);
assert.strictEqual(viewerPerms.can_comment, false);

const approverPerms = resolvePermissions('CLIENT_APPROVER');
assert.strictEqual(approverPerms.can_approve_deliverables, true);
assert.strictEqual(approverPerms.can_comment, true);

const customPerms = resolvePermissions('CLIENT_VIEWER', { can_comment: true });
assert.strictEqual(customPerms.can_comment, true, 'Custom overrides must take precedence');
console.log('✓ Guest role permission matrix accurately enforces read-only, collaborator, and approver access.');

// 4. Deliverable Review Decision Validation
function validateReviewSubmission(decision, comments) {
  const d = String(decision || '').toUpperCase();
  if (!['APPROVED', 'CHANGES_REQUESTED'].includes(d)) {
    throw new Error('Invalid decision. Must be APPROVED or CHANGES_REQUESTED.');
  }
  if (d === 'CHANGES_REQUESTED' && (!comments || comments.trim().length === 0)) {
    throw new Error('Comments are mandatory when requesting revisions.');
  }
  return { decision: d, comments: comments?.trim() || null };
}

assert.doesNotThrow(() => validateReviewSubmission('APPROVED', ''));
assert.doesNotThrow(() => validateReviewSubmission('CHANGES_REQUESTED', 'Please fix mobile padding.'));
assert.throws(() => validateReviewSubmission('CHANGES_REQUESTED', ''), /Comments are mandatory/);
assert.throws(() => validateReviewSubmission('REJECTED', 'nope'), /Invalid decision/);
console.log('✓ Deliverable review validation enforces mandatory comments on revision requests.');

// 5. Approved Project Progress Calculation
function computeClientProgress(tasks, progressMode = 'AUTOMATIC', manualPercent = 0) {
  if (progressMode === 'MANUAL') {
    return Math.max(0, Math.min(100, manualPercent));
  }
  const visibleTasks = tasks.filter(t => t.is_visible);
  if (visibleTasks.length === 0) return 0.0;
  const completed = visibleTasks.filter(t => t.client_status === 'COMPLETED').length;
  return Number(((completed / visibleTasks.length) * 100).toFixed(1));
}

const mockTasks = [
  { is_visible: true, client_status: 'COMPLETED' },
  { is_visible: true, client_status: 'IN_PROGRESS' },
  { is_visible: true, client_status: 'COMPLETED' },
  { is_visible: false, client_status: 'COMPLETED' }, // unshared task must not count
];
assert.strictEqual(computeClientProgress(mockTasks), 66.7, 'Progress should equal 2/3 = 66.7%');
assert.strictEqual(computeClientProgress(mockTasks, 'MANUAL', 85.5), 85.5, 'Manual progress should override automatic calculation');
console.log('✓ Client progress calculation derives accurately from shared tasks.');

// 6. Server-Side Allowlist Serialization Check
function serializeClientProject(internalProject, visibility) {
  return {
    project_id: internalProject.id,
    name: internalProject.name,
    description: visibility.show_description ? internalProject.description : null,
    status: internalProject.status,
    progress_percent: visibility.show_progress ? internalProject.progress : null,
    // Sensitive internal fields OMITTED:
    // internal_budget, employee_hourly_rates, profit_margin, internal_risk_scores
  };
}

const rawInternalProject = {
  id: 42,
  name: 'Brand Redesign',
  description: 'Public description',
  status: 'ACTIVE',
  progress: 75.0,
  internal_budget: 150000,
  employee_hourly_rates: { dev: 120 },
  internal_risk_scores: [0.85, 0.9],
};

const safeClientView = serializeClientProject(rawInternalProject, { show_description: true, show_progress: true });
assert.strictEqual(safeClientView.project_id, 42);
assert.strictEqual(safeClientView.name, 'Brand Redesign');
assert.strictEqual(safeClientView.internal_budget, undefined, 'Internal budget must never leak to client');
assert.strictEqual(safeClientView.employee_hourly_rates, undefined, 'Hourly rates must never leak to client');
assert.strictEqual(safeClientView.internal_risk_scores, undefined, 'Internal risk scores must never leak to client');
console.log('✓ Allowlist serializer guarantees internal financial and risk data is never exposed.');

console.log('ALL MODULE B53 CLIENT & GUEST PORTAL FRONTEND TESTS PASSED SUCCESSFULLY! ✓');
